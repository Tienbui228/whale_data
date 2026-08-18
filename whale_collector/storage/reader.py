"""Point-in-time correct parquet reader with deduplication."""

from pathlib import Path
from typing import Optional

import pandas as pd
import structlog

from whale_collector.storage.paths import METRIC_DIRS, funding_partition_path
from whale_collector.storage.dedup import DEDUP_KEY
from whale_collector.timeutil import HOUR_MS

log = structlog.get_logger()


def _collect_partition_paths(metric: str) -> list[Path]:
    """Find all existing partition files for a metric."""
    metric_dir = METRIC_DIRS.get(metric)
    if not metric_dir or not metric_dir.exists():
        return []
    if metric == "funding_8h":
        pattern = "month=*/part-0.parquet"
    else:
        pattern = "date=*/part-0.parquet"
    return sorted(metric_dir.glob(pattern))


def read_pit(
    metric: str,
    *,
    symbols: Optional[list[str]] = None,
    start_ts_ms: int,
    end_ts_ms: int,
    fetched_before_ts_ms: Optional[int] = None,
) -> pd.DataFrame:
    """Load data for [start_ts_ms, end_ts_ms), deduped by max(fetched_at_ms).

    Args:
        metric: storage metric key (e.g. 'klines_1h')
        symbols: optional filter; None = all symbols
        start_ts_ms: inclusive window start (UTC ms)
        end_ts_ms: exclusive window end (UTC ms)
        fetched_before_ts_ms: exclude rows fetched after this time (PIT);
                              defaults to end_ts_ms + HOUR_MS

    Returns:
        DataFrame sorted by (symbol, as_of_ts_ms), deduplicated.
    """
    if fetched_before_ts_ms is None:
        fetched_before_ts_ms = end_ts_ms + HOUR_MS

    paths = _collect_partition_paths(metric)
    if not paths:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for p in paths:
        try:
            df = pd.read_parquet(p)
            frames.append(df)
        except Exception as exc:
            log.warning("read_partition_failed", path=str(p), error=str(exc))

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Filter to time window
    df = df[(df["as_of_ts_ms"] >= start_ts_ms) & (df["as_of_ts_ms"] < end_ts_ms)]

    # Filter by symbol
    if symbols is not None:
        df = df[df["symbol"].isin(set(symbols))]

    # PIT correctness: exclude rows fetched after cutoff
    df = df[df["fetched_at_ms"] <= fetched_before_ts_ms]

    if df.empty:
        return df.reset_index(drop=True)

    # Dedup: keep row with MAX fetched_at_ms per DEDUP_KEY (see whale_collector/storage/dedup.py)
    df = (
        df.sort_values("fetched_at_ms")
        .drop_duplicates(subset=DEDUP_KEY, keep="last")
        .sort_values(DEDUP_KEY)
        .reset_index(drop=True)
    )

    return df


def read_latest_universe(n_latest: int = 1) -> Optional[pd.DataFrame]:
    """Read the most recent universe snapshot(s)."""
    from whale_collector.storage.paths import list_universe_snapshots

    paths = list_universe_snapshots()
    if not paths:
        return None
    selected = paths[-n_latest:]
    frames = [pd.read_parquet(p) for p in selected if p.exists()]
    if not frames:
        return None
    return (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["symbol"], keep="last")
    )

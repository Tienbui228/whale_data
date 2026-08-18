"""Parquet writer with idempotent-append semantics."""

import asyncio
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from whale_collector.config import COMPRESSION, COMPRESSION_LEVEL
from whale_collector.storage.paths import partition_path, funding_partition_path
from whale_collector.storage.dedup import DEDUP_KEY

log = structlog.get_logger()

# Per-partition asyncio locks prevent concurrent write races within a run
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(path: Path) -> asyncio.Lock:
    key = str(path)
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


def _sync_append(df: pd.DataFrame, path: Path, compression: str, level: int) -> None:
    """Append with dedup-on-write on DEDUP_KEY (chặn OI-dup ×2 tại nguồn).

    Verified by _probe_oi_dup_v1v2v3_20260818:
      - as_of_ts_ms là BAR-TIME (V1c) — dup rows có key + data fields IDENTICAL,
        chỉ fetched_at_ms khác → keep="last" giữ bản fetch mới nhất, không mất data.
      - lookback_h=2 trong collect_hourly GIỮ NGUYÊN (robustness chống miss-run,
        L-49); overlap chặn ở dedup-on-write, KHÔNG ở cắt lookback.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
        if "fetched_at_ms" in df.columns:
            df = df.sort_values("fetched_at_ms")
        df = df.drop_duplicates(subset=DEDUP_KEY, keep="last")
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression=compression, compression_level=level)


def _sync_overwrite(df: pd.DataFrame, path: Path, compression: str, level: int) -> None:
    """Overwrite the file (for universe snapshots)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression=compression, compression_level=level)


async def write_parquet_partition(
    df: pd.DataFrame,
    metric: str,
    as_of_date: str,
    *,
    compression: str = COMPRESSION,
    compression_level: int = COMPRESSION_LEVEL,
) -> Path:
    """Append df rows to partition file (date or month partitioned).

    For funding_8h: as_of_date[:7] is used as the month key.
    Concurrent writes to same partition are serialized via asyncio.Lock.
    """
    if df.empty:
        return Path()

    if metric == "funding_8h":
        path = funding_partition_path(as_of_date[:7])
    else:
        path = partition_path(metric, as_of_date)

    lock = _get_lock(path)
    async with lock:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, _sync_append, df, path, compression, compression_level
        )

    log.debug("partition_appended", metric=metric, date=as_of_date, rows=len(df))
    return path


async def write_dataframe_direct(
    df: pd.DataFrame,
    path: Path,
    *,
    overwrite: bool = False,
    compression: str = COMPRESSION,
    compression_level: int = COMPRESSION_LEVEL,
) -> None:
    """Write df to an arbitrary path. Used for universe snapshots and meta files."""
    if df.empty:
        return
    lock = _get_lock(path)
    async with lock:
        loop = asyncio.get_running_loop()
        fn = _sync_overwrite if overwrite else _sync_append
        await loop.run_in_executor(None, fn, df, path, compression, compression_level)

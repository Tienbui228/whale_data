"""Partition path resolvers for all metric datasets."""

from pathlib import Path

from whale_collector.config import RAW_DIR

METRIC_DIRS: dict[str, Path] = {
    "klines_1h":        RAW_DIR / "klines_1h",
    "oi_hist_1h":       RAW_DIR / "oi_hist_1h",
    "top_pos_1h":       RAW_DIR / "top_pos_1h",
    "top_acct_1h":      RAW_DIR / "top_acct_1h",
    "retail_global_1h": RAW_DIR / "retail_global_1h",
    "taker_ratio_1h":   RAW_DIR / "taker_ratio_1h",
    "funding_8h":       RAW_DIR / "funding_8h",
    "btc_market_1h":    RAW_DIR / "btc_market_1h",
    "universe":         RAW_DIR / "universe",
    # W2: daily-period (1d) metrics
    "oi_hist_1d":       RAW_DIR / "oi_hist_1d",
    "top_pos_1d":       RAW_DIR / "top_pos_1d",
    "top_acct_1d":      RAW_DIR / "top_acct_1d",
    "retail_global_1d": RAW_DIR / "retail_global_1d",
    "taker_ratio_1d":   RAW_DIR / "taker_ratio_1d",
}


def partition_path(metric: str, as_of_date_str: str) -> Path:
    """Return path: raw/{metric}/date=YYYY-MM-DD/part-0.parquet"""
    return METRIC_DIRS[metric] / f"date={as_of_date_str}" / "part-0.parquet"


def funding_partition_path(month_str: str) -> Path:
    """Return path: raw/funding_8h/month=YYYY-MM/part-0.parquet"""
    return METRIC_DIRS["funding_8h"] / f"month={month_str}" / "part-0.parquet"


def universe_partition_path(date_str: str) -> Path:
    """Return path: raw/universe/date=YYYY-MM-DD/snapshot.parquet"""
    return METRIC_DIRS["universe"] / f"date={date_str}" / "snapshot.parquet"


def list_universe_snapshots() -> list[Path]:
    """Return all universe snapshot files sorted by date."""
    base = METRIC_DIRS["universe"]
    if not base.exists():
        return []
    return sorted(base.glob("date=*/snapshot.parquet"))

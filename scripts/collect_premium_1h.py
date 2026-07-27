#!/usr/bin/env python3
"""W3: Premium index hourly collector.

Fetches /fapi/v1/premiumIndex once per run -- returns ALL symbols in a single call
(weight=1, general pool). Filters to universe_master active symbols.

Storage: data/raw/premium_1h/symbol=XXXX/YYYY-MM-DD.parquet
Cron: integrated into collect_hourly.py (called as a sub-step after standard metrics)

Schema:
    symbol, as_of_ts_ms, mark_price, index_price, last_funding_rate,
    next_funding_time_ms, interest_rate, time_ms, fetched_at_ms, schema_version

Usage:
    python scripts/collect_premium_1h.py
    python scripts/collect_premium_1h.py --dry-run
    python scripts/collect_premium_1h.py --symbols BTCUSDT,ETHUSDT
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, LOGS_DIR, RAW_DIR, MASTER_PATH,
    RATE_LIMIT_WEIGHT_PER_MIN, SCHEMA_VERSION, COMPRESSION, COMPRESSION_LEVEL,
    EXCLUDED_SYMBOLS,
)
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import now_ms, ms_to_date_str
from whale_collector.universe_master import load_master, get_active_symbols

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

PREMIUM_DIR: Path = RAW_DIR / "premium_1h"

_PREMIUM_COLS = [
    "symbol",
    "as_of_ts_ms",
    "mark_price",
    "index_price",
    "last_funding_rate",
    "next_funding_time_ms",  # ms epoch — Binance nextFundingTime is already in ms
    "interest_rate",
    "time_ms",
    "fetched_at_ms",
    "schema_version",
]

# Endpoint: one call returns ALL symbols
_PREMIUM_INDEX_PATH = "/fapi/v1/premiumIndex"
_PREMIUM_WEIGHT = 1  # general pool, weight=1


def _partition_path(symbol: str, date_str: str) -> Path:
    """raw/premium_1h/symbol=XXXX/YYYY-MM-DD.parquet"""
    return PREMIUM_DIR / f"symbol={symbol}" / f"{date_str}.parquet"


def _sync_write(df: pd.DataFrame, path: Path) -> None:
    """Append-only write: read existing + concat + atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        # Deduplicate on (symbol, as_of_ts_ms)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="last")
        df = combined
    tmp = path.with_suffix(".tmp.parquet")
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, tmp, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL)
    os.replace(tmp, path)


def parse_premium_index(data: list, fetched_at_ms: int) -> pd.DataFrame:
    """Parse /fapi/v1/premiumIndex batch response.

    Returns DataFrame with all returned symbols.
    Fields: symbol, markPrice, indexPrice, lastFundingRate,
            nextFundingTime, interestRate, time
    """
    if not data:
        return pd.DataFrame(columns=_PREMIUM_COLS)

    rows = []
    for item in data:
        sym = item.get("symbol", "")
        if not sym:
            continue
        rows.append({
            "symbol":            sym,
            "as_of_ts_ms":       int(item.get("time", fetched_at_ms)),
            "mark_price":        float(item.get("markPrice", 0) or 0),
            "index_price":       float(item.get("indexPrice", 0) or 0),
            "last_funding_rate": float(item.get("lastFundingRate", 0) or 0),
            "next_funding_time_ms": int(item.get("nextFundingTime", 0) or 0),
            "interest_rate":     float(item.get("interestRate", 0) or 0),
            "time_ms":           int(item.get("time", fetched_at_ms)),
            "fetched_at_ms":     int(fetched_at_ms),
            "schema_version":    int(SCHEMA_VERSION),
        })

    df = pd.DataFrame(rows, columns=_PREMIUM_COLS)
    df["as_of_ts_ms"] = df["as_of_ts_ms"].astype("int64")
    df["next_funding_time_ms"] = df["next_funding_time_ms"].astype("int64")
    df["time_ms"] = df["time_ms"].astype("int64")
    df["fetched_at_ms"] = df["fetched_at_ms"].astype("int64")
    df["mark_price"] = df["mark_price"].astype("float64")
    df["index_price"] = df["index_price"].astype("float64")
    df["last_funding_rate"] = df["last_funding_rate"].astype("float64")
    df["interest_rate"] = df["interest_rate"].astype("float64")
    df["schema_version"] = df["schema_version"].astype("int32")
    return df


async def run_collect_premium(
    *,
    symbols_override: Optional[list[str]] = None,
    dry_run: bool = False,
) -> int:
    """Fetch premium index (1 API call) and write per-symbol partitions.

    Returns exit code: 0=success, 1=error.
    """
    fetched_at_ms = now_ms()
    log.info("premium_1h_start", ts_ms=fetched_at_ms)

    # --- Dirs ---
    PREMIUM_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    # --- Universe ---
    if not MASTER_PATH.exists():
        log.error("universe_master_not_found")
        return 1
    master = load_master(MASTER_PATH)
    if master.empty:
        log.error("universe_master_empty")
        return 1

    active_syms: set[str] = set(
        symbols_override
        if symbols_override
        else [s for s in get_active_symbols(master) if s not in EXCLUDED_SYMBOLS]
    )
    log.info("premium_1h_universe", active_syms=len(active_syms))

    if dry_run:
        log.info("dry_run_complete", would_write_for=len(active_syms))
        return 0

    # --- Single API call --- weight=1, general pool
    # NOTE: /fapi/v1/premiumIndex (no symbol param) = ALL symbols in 1 call
    fetch_logger = FetchLogger()
    limiter = RateLimiter(max_weight_per_min=RATE_LIMIT_WEIGHT_PER_MIN)

    async with BinanceClient(limiter, fetch_logger) as client:
        log.info("premium_1h_fetch", endpoint=_PREMIUM_INDEX_PATH, weight=_PREMIUM_WEIGHT,
                 note="1_call_per_hour_all_symbols")
        try:
            # This is THE SINGLE CALL per hourly run that retrieves all symbols at once
            data = await client.get(_PREMIUM_INDEX_PATH, params={}, weight=_PREMIUM_WEIGHT)
        except Exception as exc:
            log.error("premium_1h_fetch_failed", error=str(exc))
            return 1

    log.info("premium_1h_raw_count", total_from_api=len(data))

    # --- Parse ---
    df_all = parse_premium_index(data, fetched_at_ms)
    if df_all.empty:
        log.warning("premium_1h_empty_parse")
        return 0

    # --- Filter to active universe only ---
    df_filtered = df_all[df_all["symbol"].isin(active_syms)].copy()
    log.info("premium_1h_filtered", in_universe=len(df_filtered), total_api=len(df_all))

    if df_filtered.empty:
        log.warning("premium_1h_no_universe_overlap")
        return 0

    # --- Write per symbol, partitioned by date ---
    df_filtered["_date"] = df_filtered["as_of_ts_ms"].apply(ms_to_date_str)

    loop = asyncio.get_running_loop()
    write_tasks = []
    for (sym, date_str), grp in df_filtered.groupby(["symbol", "_date"]):
        g = grp.drop(columns=["_date"]).copy()
        path = _partition_path(str(sym), str(date_str))
        write_tasks.append((g, path))

    written = 0
    errors = 0
    for g, path in write_tasks:
        try:
            await loop.run_in_executor(None, _sync_write, g, path)
            written += 1
        except Exception as exc:
            log.error("premium_1h_write_error", path=str(path), error=str(exc))
            errors += 1

    fetch_logger.flush(META_DIR / "fetch_log_premium_1h.parquet")
    log.info("premium_1h_complete",
             symbols_written=written,
             errors=errors,
             rows=len(df_filtered))
    return 0 if errors == 0 else 1


@app.command()
def main(
    dry_run: bool = typer.Option(False, help="Validate only -- no API calls or writes"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override"),
) -> None:
    """W3: Collect premium index snapshot hourly for full universe (1 API call/run)."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    code = asyncio.run(run_collect_premium(
        symbols_override=sym_list,
        dry_run=dry_run,
    ))
    raise typer.Exit(code)


if __name__ == "__main__":
    app()

#!/usr/bin/env python3
"""W2: Daily-period metric collector (oi_hist_1d, top_pos_1d, top_acct_1d,
retail_global_1d, taker_ratio_1d).

Same /futures/data/* endpoints as 1h but with period='1d' and limit=500.
Cron schedule: 00:35 UTC daily (after daily candle closes at 00:00; 5-min guard).

Usage:
    python scripts/collect_daily_metrics.py
    python scripts/collect_daily_metrics.py --days-back 7
    python scripts/collect_daily_metrics.py --symbols BANKUSDT,BTCUSDT --days-back 3
    python scripts/collect_daily_metrics.py --dry-run
"""

from __future__ import annotations

import asyncio
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
import typer

# Ensure package root is on path when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, LOGS_DIR, RATE_LIMIT_WEIGHT_PER_MIN, SEMAPHORE_SIZE,
    EXCLUDED_SYMBOLS, MASTER_PATH, SCHEMA_VERSION,
    RAW_DIR, COMPRESSION, COMPRESSION_LEVEL,
)
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import now_ms, ms_to_date_str, days_back_ms, today_str, DAY_MS, HOUR_MS
from whale_collector.binance.endpoints import PATHS
from whale_collector.binance.parsers import (
    parse_top_pos, parse_top_acct, parse_retail, parse_taker_ratio,
    _empty, _enforce_int64, _enforce_float64,
)
from whale_collector.universe_master import load_master, get_active_symbols

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

# ---------------------------------------------------------------------------
# Storage dirs for 1d metrics
# ---------------------------------------------------------------------------

DAILY_METRIC_DIRS: dict[str, Path] = {
    "oi_hist_1d":       RAW_DIR / "oi_hist_1d",
    "top_pos_1d":       RAW_DIR / "top_pos_1d",
    "top_acct_1d":      RAW_DIR / "top_acct_1d",
    "retail_global_1d": RAW_DIR / "retail_global_1d",
    "taker_ratio_1d":   RAW_DIR / "taker_ratio_1d",
}

# Per-partition asyncio locks (prevent concurrent write races)
_partition_locks: dict[str, asyncio.Lock] = {}


def _get_partition_lock(path: Path) -> asyncio.Lock:
    key = str(path)
    if key not in _partition_locks:
        _partition_locks[key] = asyncio.Lock()
    return _partition_locks[key]


def _daily_partition_path(metric: str, as_of_date_str: str) -> Path:
    """raw/{metric}/date=YYYY-MM-DD/part-0.parquet"""
    return DAILY_METRIC_DIRS[metric] / f"date={as_of_date_str}" / "part-0.parquet"


def _sync_append(df: pd.DataFrame, path: Path) -> None:
    """Append-only write. Reads existing + concat + write (same as writer.py)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL)


async def _write_daily_partition(df: pd.DataFrame, metric: str, date_str: str) -> None:
    """Write df to 1d partition, serialising concurrent writers per path."""
    if df.empty:
        return
    path = _daily_partition_path(metric, date_str)
    lock = _get_partition_lock(path)
    async with lock:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_append, df, path)


# ---------------------------------------------------------------------------
# 1d-specific parser for oi_hist (has extra CMCCirculatingSupply field)
# ---------------------------------------------------------------------------

_OI_HIST_1D_COLS = [
    "symbol",
    "as_of_ts_ms",
    "sum_open_interest",
    "sum_open_interest_value",
    "cmc_circulating_supply",
    "fetched_at_ms",
    "schema_version",
]


def parse_oi_hist_1d(data: list, symbol: str, fetched_at_ms: int) -> pd.DataFrame:
    """Parse open interest history response for period=1d.

    1d response has an extra CMCCirculatingSupply field absent in 1h.
    """
    if not data:
        return _empty(_OI_HIST_1D_COLS)

    rows = []
    for item in data:
        rows.append({
            "symbol":                   symbol,
            "as_of_ts_ms":              int(item["timestamp"]),
            "sum_open_interest":        float(item["sumOpenInterest"]),
            "sum_open_interest_value":  float(item["sumOpenInterestValue"]),
            "cmc_circulating_supply":   float(item.get("CMCCirculatingSupply") or 0),
            "fetched_at_ms":            int(fetched_at_ms),
            "schema_version":           int(SCHEMA_VERSION),
        })

    df = pd.DataFrame(rows, columns=_OI_HIST_1D_COLS)
    df = _enforce_int64(df, ["as_of_ts_ms", "fetched_at_ms"])
    df = _enforce_float64(df, ["sum_open_interest", "sum_open_interest_value", "cmc_circulating_supply"])
    df["schema_version"] = df["schema_version"].astype("int32")
    return df


# ---------------------------------------------------------------------------
# Metric configs for 1d collection
# ---------------------------------------------------------------------------

DAILY_METRICS: list[dict] = [
    {
        "key":          "oi_hist_1d",
        "path":         PATHS["oi_hist"],
        "parser":       parse_oi_hist_1d,
        "weight":       1,
        "limit":        500,
        "extra_params": {"period": "1d"},
        "ts_field":     "timestamp",
    },
    {
        "key":          "top_pos_1d",
        "path":         PATHS["top_pos"],
        "parser":       parse_top_pos,
        "weight":       1,
        "limit":        500,
        "extra_params": {"period": "1d"},
        "ts_field":     "timestamp",
    },
    {
        "key":          "top_acct_1d",
        "path":         PATHS["top_acct"],
        "parser":       parse_top_acct,
        "weight":       1,
        "limit":        500,
        "extra_params": {"period": "1d"},
        "ts_field":     "timestamp",
    },
    {
        "key":          "retail_global_1d",
        "path":         PATHS["retail"],
        "parser":       parse_retail,
        "weight":       1,
        "limit":        500,
        "extra_params": {"period": "1d"},
        "ts_field":     "timestamp",
    },
    {
        "key":          "taker_ratio_1d",
        "path":         PATHS["taker"],
        "parser":       parse_taker_ratio,
        "weight":       1,
        "limit":        500,
        "extra_params": {"period": "1d"},
        "ts_field":     "timestamp",
    },
]


# ---------------------------------------------------------------------------
# Pagination (endTime cursor — same logic as backfill_30d.py for /futures/data/*)
# ---------------------------------------------------------------------------

async def _paginate_daily(
    client: BinanceClient,
    mc: dict,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> list:
    """Walk endTime backward for /futures/data/* period=1d.

    Aligns start_ms down to nearest DAY_MS boundary (API rejects mid-day startTime).
    Returns items in chronological order (oldest first).
    """
    aligned_start = (start_ms // DAY_MS) * DAY_MS
    limit = mc["limit"]
    ts_step = DAY_MS

    max_pages = math.ceil((end_ms - aligned_start) / ts_step / limit) + 2
    segments: list[list] = []
    cur_end = end_ms
    prev_cur_end = cur_end + 1

    for _page in range(max_pages):
        if cur_end <= aligned_start:
            break
        if cur_end >= prev_cur_end:
            log.error("daily_paginate_endtime_not_decreasing",
                      metric=mc["key"], symbol=symbol,
                      cur_end=cur_end, prev_end=prev_cur_end)
            break

        params = {
            "symbol": symbol,
            "startTime": aligned_start,
            "endTime": cur_end,
            "limit": limit,
            **mc["extra_params"],
        }

        try:
            data = await client.get(mc["path"], params, weight=mc["weight"])
        except Exception as exc:
            log.error("daily_paginate_fetch_error", metric=mc["key"], symbol=symbol,
                      page=_page + 1, error=str(exc))
            break

        if not data:
            # Retry once before accepting empty as data edge
            await asyncio.sleep(2)
            try:
                data = await client.get(mc["path"], params, weight=mc["weight"])
            except Exception as exc:
                log.error("daily_paginate_fetch_error_retry", metric=mc["key"], symbol=symbol,
                          page=_page + 1, error=str(exc))
                break
            if not data:
                break

        segments.append(data)

        if len(data) < limit:
            break

        prev_cur_end = cur_end
        oldest_ts = min(int(x[mc["ts_field"]]) for x in data)
        cur_end = oldest_ts - ts_step

    else:
        log.error("daily_paginate_max_pages", metric=mc["key"], symbol=symbol, max_pages=max_pages)

    # Segments collected newest→oldest; reverse to chronological order
    all_items: list = []
    for seg in reversed(segments):
        all_items.extend(seg)
    return all_items


# ---------------------------------------------------------------------------
# Per-symbol collection + write
# ---------------------------------------------------------------------------

async def _collect_symbol_daily(
    client: BinanceClient,
    mc: dict,
    symbol: str,
    start_ms: int,
    end_ms: int,
    sem: asyncio.Semaphore,
    fetched_at_ms: int,
) -> tuple[str, int, Optional[str]]:
    """Fetch one 1d metric for one symbol and write to storage.
    Returns (symbol, rows_written, error_message|None).
    """
    async with sem:
        try:
            data = await _paginate_daily(client, mc, symbol, start_ms, end_ms)
        except ValueError as exc:
            return symbol, 0, f"bad_symbol: {exc}"
        except Exception as exc:
            return symbol, 0, f"{type(exc).__name__}: {exc}"

        if not data:
            return symbol, 0, None

        try:
            df = mc["parser"](data, symbol, fetched_at_ms)
        except Exception as exc:
            return symbol, 0, f"parse_error: {type(exc).__name__}: {exc}"

        if df.empty:
            return symbol, 0, None

        df["_date"] = df["as_of_ts_ms"].apply(ms_to_date_str)
        try:
            for date_str, group in df.groupby("_date"):
                g = group.drop(columns=["_date"])
                await _write_daily_partition(g, mc["key"], str(date_str))
        except Exception as exc:
            return symbol, 0, f"write_error: {type(exc).__name__}: {exc}"

        return symbol, len(df), None


# ---------------------------------------------------------------------------
# Main collection coroutine
# ---------------------------------------------------------------------------

async def run_collect_daily_metrics(
    *,
    days_back: int = 1,
    symbols_override: Optional[list[str]] = None,
    metrics_override: Optional[list[str]] = None,
    dry_run: bool = False,
    skip_guard: bool = False,
) -> int:
    """Collect 1d-period metrics. Returns exit code (0=success, 1=error)."""
    # --- Closed-candle guard ---
    # Daily candle closes at 00:00 UTC; collect only after 00:05 UTC buffer.
    now_utc = datetime.now(timezone.utc)
    if not skip_guard:
        if now_utc.hour == 0 and now_utc.minute < 5:
            log.info("daily_closed_candle_guard",
                     reason="called before 00:05 UTC; daily candle not yet settled",
                     utc_time=now_utc.strftime("%H:%M"))
            return 0

    log.info("daily_metrics_start", days_back=days_back, utc=now_utc.strftime("%Y-%m-%d %H:%M"))

    # --- Setup dirs ---
    for d in DAILY_METRIC_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Universe ---
    if not MASTER_PATH.exists():
        log.error("universe_master_not_found",
                  hint="Run: python scripts/seed_universe_master.py")
        return 1

    master = load_master(MASTER_PATH)
    if master.empty:
        log.error("universe_master_empty")
        return 1

    symbols: list[str] = (
        symbols_override
        if symbols_override
        else [s for s in get_active_symbols(master) if s not in EXCLUDED_SYMBOLS]
    )
    log.info("daily_metrics_universe", total=len(symbols))

    if dry_run:
        log.info("dry_run_complete", symbols=len(symbols))
        return 0

    # --- Time window ---
    now = now_ms()
    # Cap: /futures/data/* rejects startTime >= 30d ago (-1130); hard cap at 29d
    max_lookback_ms = 29 * DAY_MS
    requested_ms = days_back * DAY_MS
    start_ms = now - min(requested_ms, max_lookback_ms)
    end_ms = now

    log.info("daily_metrics_window",
             start=ms_to_date_str(start_ms),
             end=ms_to_date_str(end_ms),
             days=days_back)

    # --- Rate limiters (separate pools per W1 API facts) ---
    fetch_logger = FetchLogger()
    general_limiter = RateLimiter(max_weight_per_min=RATE_LIMIT_WEIGHT_PER_MIN)
    futures_data_limiter = RateLimiter(max_weight_per_min=500)
    sem = asyncio.Semaphore(SEMAPHORE_SIZE)

    # --- Filter metrics ---
    metrics_to_run = [
        mc for mc in DAILY_METRICS
        if metrics_override is None or mc["key"] in metrics_override
    ]
    log.info("daily_metrics_plan", metrics=[mc["key"] for mc in metrics_to_run])

    async with BinanceClient(
        general_limiter, fetch_logger,
        futures_data_limiter=futures_data_limiter,
    ) as client:
        for mc in metrics_to_run:
            log.info("daily_metric_start", metric=mc["key"], symbols=len(symbols))

            tasks = [
                _collect_symbol_daily(client, mc, sym, start_ms, end_ms, sem, now)
                for sym in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_rows = 0
            errors: list[str] = []
            for res in results:
                if isinstance(res, Exception):
                    errors.append(str(res))
                    continue
                sym_r, rows_r, err_r = res
                total_rows += rows_r
                if err_r:
                    errors.append(f"{sym_r}: {err_r}")
                    log.warning("daily_symbol_error", metric=mc["key"],
                                symbol=sym_r, error=err_r)

            log.info("daily_metric_done",
                     metric=mc["key"],
                     total_rows=total_rows,
                     errors=len(errors))

    fetch_logger.flush(META_DIR / "fetch_log_daily_metrics.parquet")
    log.info("daily_metrics_complete")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.command()
def main(
    days_back: int = typer.Option(1, help="Days of 1d candles to collect (default 1 = yesterday)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override"),
    metrics: Optional[str] = typer.Option(None, help="Comma-separated metric keys to run"),
    dry_run: bool = typer.Option(False, help="Validate only — no API calls or writes"),
    skip_guard: bool = typer.Option(False, help="Skip the 00:05 UTC closed-candle guard"),
) -> None:
    """W2: Collect daily-period (1d) whale metrics for all active symbols."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    metric_list = [m.strip() for m in metrics.split(",")] if metrics else None

    exit_code = asyncio.run(run_collect_daily_metrics(
        days_back=days_back,
        symbols_override=sym_list,
        metrics_override=metric_list,
        dry_run=dry_run,
        skip_guard=skip_guard,
    ))
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()

#!/usr/bin/env python3
"""E3: Binance Spot klines 1d collector — px/vol/takerBUY_spot cho toàn universe.

Schema spot_klines_1d:
    symbol, date_str, open, high, low, close,
    base_vol, quote_vol, n_trades,
    taker_buy_base_vol, taker_buy_quote_vol, taker_buy_pct,
    venue, taker_abstain, fetched_at_ms, schema_version

taker_abstain=True khi:
  (a) symbol không có spot trên Binance (400) → venue='no_spot'
  (b) klines[9] ≈ klines[5] (BSC taker bug, ratio≈1.0) → venue='binance_spot_bsc'
  (c) collect_alpha_spot.py ghi qua cùng store với source tag riêng

Cron: 01:05 UTC daily (sau daily candle đóng 00:00 UTC + 5 phút guard).

Usage:
    python scripts/collect_spot_daily.py
    python scripts/collect_spot_daily.py --days-back 3
    python scripts/collect_spot_daily.py --symbols BANKUSDT,TAGUSDT
    python scripts/collect_spot_daily.py --dry-run
"""

from __future__ import annotations

import asyncio
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, LOGS_DIR, SEMAPHORE_SIZE, EXCLUDED_SYMBOLS,
    MASTER_PATH, SCHEMA_VERSION, RAW_DIR, COMPRESSION, COMPRESSION_LEVEL,
)
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import now_ms, ms_to_date_str, DAY_MS, HOUR_MS
from whale_collector.universe_master import load_master, get_active_symbols
from whale_collector.storage.paths import spot_klines_partition_path

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

SPOT_BASE = "https://api.binance.com"
SPOT_KLINES_PATH = "/api/v3/klines"
# Spot REQUEST_WEIGHT limit: 6000/min (conservative budget)
SPOT_RATE_LIMIT = 1200

# BSC guard threshold: if taker_buy_base / base_vol > this → broken taker
_BSC_TAKER_RATIO_THRESHOLD = 0.9985

_SPOT_KLINES_COLS = [
    "symbol", "date_str",
    "open", "high", "low", "close",
    "base_vol", "quote_vol", "n_trades",
    "taker_buy_base_vol", "taker_buy_quote_vol", "taker_buy_pct",
    "venue", "taker_abstain",
    "fetched_at_ms", "schema_version",
]

_partition_locks: dict[str, asyncio.Lock] = {}


def _get_lock(path: Path) -> asyncio.Lock:
    key = str(path)
    if key not in _partition_locks:
        _partition_locks[key] = asyncio.Lock()
    return _partition_locks[key]


def _sync_append(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        path, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL,
    )


async def _write_spot_partition(df: pd.DataFrame, date_str: str) -> None:
    if df.empty:
        return
    path = spot_klines_partition_path(date_str)
    lock = _get_lock(path)
    async with lock:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_append, df, path)


def _make_abstain_row(symbol: str, date_str: str, venue: str, fetched_at: int) -> pd.DataFrame:
    """Row for 400/no-spot symbols — price fields NaN, taker_abstain=True."""
    return pd.DataFrame([{
        "symbol": symbol, "date_str": date_str,
        "open": float("nan"), "high": float("nan"),
        "low": float("nan"), "close": float("nan"),
        "base_vol": float("nan"), "quote_vol": float("nan"),
        "n_trades": 0,
        "taker_buy_base_vol": float("nan"),
        "taker_buy_quote_vol": float("nan"),
        "taker_buy_pct": float("nan"),
        "venue": venue, "taker_abstain": True,
        "fetched_at_ms": fetched_at, "schema_version": SCHEMA_VERSION,
    }], columns=_SPOT_KLINES_COLS)


def _parse_spot_kline_row(k: list, symbol: str, date_str: str, fetched_at: int) -> pd.DataFrame:
    """Parse one daily kline item. Sets taker_abstain=True if BSC guard fires."""
    open_ = float(k[1]); high = float(k[2]); low = float(k[3]); close = float(k[4])
    base_vol = float(k[5]); quote_vol = float(k[7])
    n_trades = int(k[8])
    taker_base = float(k[9]); taker_quote = float(k[10])

    taker_pct = taker_quote / quote_vol if quote_vol > 0 else float("nan")

    # BSC guard: taker_buy_base_vol ≈ base_volume → 100% taker = broken API field
    bsc_broken = (base_vol > 0 and taker_base / base_vol >= _BSC_TAKER_RATIO_THRESHOLD)
    if bsc_broken:
        taker_base = float("nan"); taker_quote = float("nan"); taker_pct = float("nan")
        venue = "binance_spot_bsc"
        taker_abstain = True
    else:
        venue = "binance_spot"
        taker_abstain = False

    return pd.DataFrame([{
        "symbol": symbol, "date_str": date_str,
        "open": open_, "high": high, "low": low, "close": close,
        "base_vol": base_vol, "quote_vol": quote_vol, "n_trades": n_trades,
        "taker_buy_base_vol": taker_base,
        "taker_buy_quote_vol": taker_quote,
        "taker_buy_pct": taker_pct,
        "venue": venue, "taker_abstain": taker_abstain,
        "fetched_at_ms": fetched_at, "schema_version": SCHEMA_VERSION,
    }], columns=_SPOT_KLINES_COLS)


async def _collect_spot_symbol(
    client: BinanceClient,
    symbol: str,
    start_ms: int,
    end_ms: int,
    sem: asyncio.Semaphore,
    fetched_at: int,
) -> tuple[str, int, Optional[str]]:
    """Fetch spot klines 1d for one symbol, write to partition. Returns (sym, rows, err)."""
    async with sem:
        date_str = ms_to_date_str(start_ms)
        try:
            data = await client.get(SPOT_KLINES_PATH, {
                "symbol": symbol, "interval": "1d",
                "startTime": start_ms, "endTime": end_ms - 1, "limit": 1,
            }, weight=2)
        except ValueError:
            # 400 → symbol not listed on Binance spot
            df = _make_abstain_row(symbol, date_str, "no_spot", fetched_at)
            await _write_spot_partition(df, date_str)
            return symbol, 1, None
        except Exception as exc:
            return symbol, 0, f"{type(exc).__name__}: {exc}"

        if not data:
            df = _make_abstain_row(symbol, date_str, "no_data", fetched_at)
            await _write_spot_partition(df, date_str)
            return symbol, 1, None

        df = _parse_spot_kline_row(data[0], symbol, date_str, fetched_at)
        await _write_spot_partition(df, date_str)
        return symbol, 1, None


async def run_spot_daily(
    *,
    days_back: int = 1,
    symbols_override: Optional[list[str]] = None,
    dry_run: bool = False,
    skip_guard: bool = False,
) -> int:
    now_utc = datetime.now(timezone.utc)
    if not skip_guard:
        if now_utc.hour == 0 and now_utc.minute < 5:
            log.info("spot_daily_guard", reason="before 00:05 UTC, candle not settled")
            return 0

    log.info("spot_daily_start", days_back=days_back, utc=now_utc.strftime("%Y-%m-%d %H:%M"))

    if not MASTER_PATH.exists():
        log.error("universe_master_not_found")
        return 1

    master = load_master(MASTER_PATH)
    symbols: list[str] = (
        symbols_override
        if symbols_override
        else [s for s in get_active_symbols(master) if s not in EXCLUDED_SYMBOLS]
    )
    log.info("spot_daily_universe", total=len(symbols))

    if dry_run:
        log.info("dry_run_complete", symbols=len(symbols))
        return 0

    now = now_ms()
    fetch_logger = FetchLogger()
    limiter = RateLimiter(max_weight_per_min=SPOT_RATE_LIMIT)
    sem = asyncio.Semaphore(SEMAPHORE_SIZE)

    total_ok = 0; total_err = 0

    async with BinanceClient(limiter, fetch_logger, base_url=SPOT_BASE) as client:
        for day_offset in range(days_back - 1, -1, -1):
            day_start = ((now // DAY_MS) - 1 - day_offset) * DAY_MS
            day_end = day_start + DAY_MS
            date_str = ms_to_date_str(day_start)
            log.info("spot_daily_day", date=date_str, symbols=len(symbols))

            tasks = [
                _collect_spot_symbol(client, sym, day_start, day_end, sem, now)
                for sym in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            day_ok = 0; day_err = 0
            for res in results:
                if isinstance(res, Exception):
                    day_err += 1
                    continue
                sym_r, rows_r, err_r = res
                day_ok += rows_r
                if err_r:
                    day_err += 1
                    log.warning("spot_symbol_error", date=date_str, symbol=sym_r, error=err_r)

            log.info("spot_daily_day_done", date=date_str, ok=day_ok, errors=day_err)
            total_ok += day_ok; total_err += day_err

    fetch_logger.flush(META_DIR / "fetch_log_spot_daily.parquet")
    log.info("spot_daily_complete", total_ok=total_ok, total_err=total_err)
    return 0 if total_err == 0 else 1


@app.command()
def main(
    days_back: int = typer.Option(1, help="Số ngày cần collect (default=1 = hôm qua)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override"),
    dry_run: bool = typer.Option(False, help="Validate only — no API calls"),
    skip_guard: bool = typer.Option(False, help="Skip 00:05 UTC guard"),
) -> None:
    """E3: Collect Binance spot daily klines for all active symbols."""
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ])
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    exit_code = asyncio.run(run_spot_daily(
        days_back=days_back,
        symbols_override=sym_list,
        dry_run=dry_run,
        skip_guard=skip_guard,
    ))
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()

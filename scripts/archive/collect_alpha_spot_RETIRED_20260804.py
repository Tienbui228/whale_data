#!/usr/bin/env python3
"""E3-alpha: Spot klines cho BSC-native tokens — price/vol ONLY, taker=ABSTAIN.

BSC tokens có Binance spot listing nhưng klines[9] (taker_buy_base_vol) == klines[5]
(base_volume) do API quirk của BSC bridge → taker data là 100% garbage.

GUARD: script này KHÔNG ĐỌC klines[9] hoặc klines[10] trong bất kỳ trường hợp nào.
       Các fields taker_buy_* được set NaN; taker_abstain=True; venue='binance_spot_bsc'.

Source symbols: data/config/alpha_bsc_symbols.txt (output của _probe_alpha_taker.py)
Store: CÙNG spot_klines_1d partition với collect_spot_daily.py (date-keyed, dedup theo
       symbol+date_str khi đọc).

Cron: chạy SAU collect_spot_daily.py cùng ngày (01:10 UTC hoặc theo operator lệnh).

Usage:
    python scripts/collect_alpha_spot.py
    python scripts/collect_alpha_spot.py --symbols BABYUSDT,ALPACAUSDT
    python scripts/collect_alpha_spot.py --dry-run
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, SEMAPHORE_SIZE, SCHEMA_VERSION,
    RAW_DIR, COMPRESSION, COMPRESSION_LEVEL,
)
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import now_ms, ms_to_date_str, DAY_MS
from whale_collector.storage.paths import spot_klines_partition_path
from whale_collector.alert import telegram_error
from scripts.collect_spot_daily import (
    _SPOT_KLINES_COLS, _get_lock, _sync_append, _write_spot_partition,
    SPOT_BASE, SPOT_KLINES_PATH, SPOT_RATE_LIMIT,
)

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

ALPHA_CONFIG = RAW_DIR.parent / "config" / "alpha_bsc_symbols.txt"


def _load_alpha_symbols(path: Path) -> list[str]:
    if not path.exists():
        msg = (f"alpha_config_missing: {path} not found. "
               "Run: python _probe_alpha_taker_20260803.py --write-config")
        log.error("alpha_config_missing", path=str(path),
                  hint="Run: python _probe_alpha_taker_20260803.py --write-config")
        telegram_error(msg)
        raise SystemExit(1)
    # Filter comment lines (reject-log section starts with #)
    syms = [
        l.strip().upper()
        for l in path.read_text().splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    log.info("alpha_symbols_loaded", count=len(syms), path=str(path))
    return syms


def _parse_alpha_kline_row(k: list, symbol: str, date_str: str, fetched_at: int) -> pd.DataFrame:
    """Parse spot kline — price/vol ONLY.

    # GUARD: DO NOT read klines[9] (taker_buy_base_vol) or klines[10]
    # (taker_buy_quote_vol). For BSC-bridged tokens these fields always equal
    # klines[5]/klines[7] (100% taker buy = broken API field). Reading them would
    # silently poison the taker_buy_pct column in every downstream join.
    """
    open_ = float(k[1]); high = float(k[2]); low = float(k[3]); close = float(k[4])
    base_vol = float(k[5]); quote_vol = float(k[7]); n_trades = int(k[8])
    # klines[9] and klines[10] intentionally NOT read — see guard above

    return pd.DataFrame([{
        "symbol": symbol, "date_str": date_str,
        "open": open_, "high": high, "low": low, "close": close,
        "base_vol": base_vol, "quote_vol": quote_vol, "n_trades": n_trades,
        "taker_buy_base_vol": float("nan"),   # GUARD: never read for BSC tokens
        "taker_buy_quote_vol": float("nan"),  # GUARD: never read for BSC tokens
        "taker_buy_pct": float("nan"),        # GUARD: never read for BSC tokens
        "venue": "binance_spot_bsc",
        "taker_abstain": True,
        "fetched_at_ms": fetched_at, "schema_version": SCHEMA_VERSION,
    }], columns=_SPOT_KLINES_COLS)


async def _collect_alpha_symbol(
    client: BinanceClient,
    symbol: str,
    day_start: int,
    day_end: int,
    sem: asyncio.Semaphore,
    fetched_at: int,
) -> tuple[str, int, Optional[str]]:
    async with sem:
        date_str = ms_to_date_str(day_start)
        try:
            data = await client.get(SPOT_KLINES_PATH, {
                "symbol": symbol, "interval": "1d",
                "startTime": day_start, "endTime": day_end - 1, "limit": 1,
            }, weight=2)
        except ValueError:
            # 400 — symbol not listed (config may be stale)
            log.warning("alpha_symbol_no_spot", symbol=symbol, date=date_str)
            return symbol, 0, f"no_spot_400"
        except Exception as exc:
            return symbol, 0, f"{type(exc).__name__}: {exc}"

        if not data:
            return symbol, 0, "empty_response"

        df = _parse_alpha_kline_row(data[0], symbol, date_str, fetched_at)
        await _write_spot_partition(df, date_str)
        return symbol, 1, None


async def run_alpha_spot(
    *,
    days_back: int = 1,
    symbols_override: Optional[list[str]] = None,
    dry_run: bool = False,
    skip_guard: bool = False,
) -> int:
    now_utc = datetime.now(timezone.utc)
    if not skip_guard and now_utc.hour == 0 and now_utc.minute < 5:
        log.info("alpha_spot_guard", reason="before 00:05 UTC")
        return 0

    symbols = symbols_override or _load_alpha_symbols(ALPHA_CONFIG)
    if not symbols:
        log.info("alpha_spot_no_symbols", hint="Empty alpha_bsc_symbols.txt — nothing to do")
        return 0

    log.info("alpha_spot_start", symbols=len(symbols), days_back=days_back)

    if dry_run:
        log.info("dry_run_complete", symbols=symbols)
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
            log.info("alpha_spot_day", date=date_str, symbols=len(symbols))

            tasks = [
                _collect_alpha_symbol(client, sym, day_start, day_end, sem, now)
                for sym in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            day_ok = 0; day_err = 0
            for res in results:
                if isinstance(res, Exception):
                    day_err += 1; continue
                _, rows_r, err_r = res
                day_ok += rows_r
                if err_r:
                    day_err += 1

            log.info("alpha_spot_day_done", date=date_str, ok=day_ok, errors=day_err)
            total_ok += day_ok; total_err += day_err

    fetch_logger.flush(META_DIR / "fetch_log_alpha_spot.parquet")
    log.info("alpha_spot_complete", total_ok=total_ok, total_err=total_err)
    return 0


@app.command()
def main(
    days_back: int = typer.Option(1, help="Số ngày collect (default=1 = hôm qua)"),
    symbols: Optional[str] = typer.Option(None, help="Override symbols (comma-separated)"),
    dry_run: bool = typer.Option(False, help="Validate only — no API calls"),
    skip_guard: bool = typer.Option(False, help="Skip 00:05 UTC guard"),
) -> None:
    """E3-alpha: Collect spot price/vol (NO taker) for BSC-native tokens."""
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ])
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    exit_code = asyncio.run(run_alpha_spot(
        days_back=days_back,
        symbols_override=sym_list,
        dry_run=dry_run,
        skip_guard=skip_guard,
    ))
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()

#!/usr/bin/env python3
"""Phase 2 hourly collector: klines, OI, position ratios, taker volume."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer

# Ensure package root is on path when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import META_DIR, RATE_LIMIT_WEIGHT_PER_MIN, SEMAPHORE_SIZE, EXCLUDED_SYMBOLS, MASTER_PATH
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import now_ms, HOUR_MS
from whale_collector.universe_master import load_master, get_active_symbols
from scripts.backfill_30d import HOURLY_METRICS, BTC_METRIC, _collect_symbol

log = structlog.get_logger()
app = typer.Typer(add_completion=False)


async def run_hourly(
    *,
    lookback_h: int = 2,
    symbols_override: Optional[list[str]] = None,
) -> int:
    """Main hourly collection coroutine. Returns exit code (0=success, 1=error)."""
    now = now_ms()
    start_ms = now - lookback_h * HOUR_MS
    # Truncate to the last completed hour boundary so the currently-forming bar
    # (open_time = current hour) is never written as a partial capture.
    end_ms = (now // HOUR_MS) * HOUR_MS - 1

    # Load active symbols from universe_master.csv
    master = load_master(MASTER_PATH)
    if master.empty:
        log.error("universe_master_empty",
                  hint="Run: python scripts/seed_universe_master.py")
        return 1

    symbols: list[str] = (
        symbols_override if symbols_override
        else [s for s in get_active_symbols(master) if s not in EXCLUDED_SYMBOLS]
    )
    log.info("hourly_start", symbols=len(symbols), lookback_h=lookback_h)

    fetch_logger = FetchLogger()
    limiter = RateLimiter(max_weight_per_min=RATE_LIMIT_WEIGHT_PER_MIN)
    sem = asyncio.Semaphore(SEMAPHORE_SIZE)

    async with BinanceClient(limiter, fetch_logger) as client:
        # BTC first
        btc_sym, btc_rows, btc_err = await _collect_symbol(
            client, BTC_METRIC, "BTCUSDT", start_ms, end_ms, sem, now
        )
        if btc_err:
            log.warning("btc_error", error=btc_err)
        else:
            log.info("btc_done", rows=btc_rows)

        # All metrics sequential, symbols concurrent
        for mc in HOURLY_METRICS:
            tasks = [
                _collect_symbol(client, mc, sym, start_ms, end_ms, sem, now)
                for sym in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            errors = sum(
                1 for r in results
                if isinstance(r, Exception) or (isinstance(r, tuple) and r[2])
            )
            rows = sum(r[1] for r in results if isinstance(r, tuple))

            # Log per-symbol errors at warning level
            for r in results:
                if isinstance(r, tuple) and r[2]:
                    log.warning("symbol_error", metric=mc.key, symbol=r[0], error=r[2])

            log.info("metric_done", metric=mc.key, rows=rows, errors=errors)

    fetch_logger.flush(META_DIR / "fetch_log.parquet")
    log.info("hourly_complete")
    return 0


@app.command()
def main(
    lookback_h: int = typer.Option(2, help="Hours to look back (default 2 for overlap safety)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override"),
) -> None:
    """Hourly incremental collector."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    code = asyncio.run(run_hourly(lookback_h=lookback_h, symbols_override=sym_list))
    raise typer.Exit(code)


if __name__ == "__main__":
    app()

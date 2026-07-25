#!/usr/bin/env python3
"""Daily universe refresh: update universe_master.csv + write snapshot parquet.

Changes from pre-W1:
  - Universe = all exchangeInfo TRADING USDT-PERP (no CoinGecko cap filter)
  - universe_master.csv is updated with union append-only logic
  - Auto-backfill hook: new symbols get immediate 30d backfill
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import aiohttp
import pandas as pd
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, COINGECKO_API_KEY, EXCLUDED_SYMBOLS,
    MASTER_PATH, FRESHWATCH_PATH,
    RATE_LIMIT_WEIGHT_PER_MIN, SEMAPHORE_SIZE,
)
from whale_collector.timeutil import now_ms, ms_to_date_str, today_str, days_back_ms
from whale_collector.universe import select_universe
from whale_collector.universe_master import (
    load_master, save_master,
    append_new_symbols, apply_delisted_72h, reactivate_returned,
    load_freshwatch_symbols,
)
from whale_collector.storage.writer import write_dataframe_direct
from whale_collector.storage.paths import universe_partition_path
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from scripts.backfill_30d import HOURLY_METRICS, FUNDING_METRIC, _collect_symbol

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

_CANARY_SYMBOLS = [
    "TUTUSDT", "BULLAUSDT", "PARTIUSDT", "ESPORTSUSDT", "CLOUSDT", "BANKUSDT",
]


async def _run_backfill_for_new_symbols(
    new_syms: set[str],
    fw_syms: set[str],
) -> None:
    """Immediate 30d backfill for newly-detected symbols.

    Priority: canary-6 first, freshwatch next, rest last.
    Does NOT call run_backfill() — uses _collect_symbol directly to avoid
    double universe-fetch, retention probe, and full audit overhead.
    """
    if not new_syms:
        return

    canary = [s for s in _CANARY_SYMBOLS if s in new_syms]
    fw_only = [s for s in sorted(new_syms) if s in fw_syms and s not in set(canary)]
    rest = sorted(new_syms - set(canary) - fw_syms)
    ordered = canary + fw_only + rest

    log.info("new_symbol_backfill_start", total=len(ordered),
             canary=len(canary), freshwatch=len(fw_only), rest=len(rest))

    now = now_ms()
    start_ms = days_back_ms(30, from_ms=now)
    end_ms = now

    fetch_logger = FetchLogger()
    limiter = RateLimiter(max_weight_per_min=RATE_LIMIT_WEIGHT_PER_MIN)
    sem = asyncio.Semaphore(SEMAPHORE_SIZE)
    total_rows = 0

    async with BinanceClient(limiter, fetch_logger) as client:
        for mc in HOURLY_METRICS:
            tasks = [
                _collect_symbol(client, mc, sym, start_ms, end_ms, sem, now)
                for sym in ordered
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, tuple):
                    sym_r, rows_r, err_r = res
                    total_rows += rows_r
                    if err_r:
                        log.warning("backfill_symbol_error", metric=mc.key,
                                    symbol=sym_r, error=err_r)

        # Funding rates
        f_tasks = [
            _collect_symbol(client, FUNDING_METRIC, sym, start_ms, end_ms, sem, now)
            for sym in ordered
        ]
        f_results = await asyncio.gather(*f_tasks, return_exceptions=True)
        for res in f_results:
            if isinstance(res, tuple):
                total_rows += res[1]
                if res[2]:
                    log.warning("backfill_funding_error", symbol=res[0], error=res[2])

    fetch_logger.flush(META_DIR / "fetch_log_newlistings.parquet")
    log.info("new_symbol_backfill_done", symbols=len(ordered), total_rows=total_rows)


async def run_daily() -> int:
    """Main daily refresh coroutine. Returns exit code (0=success, 1=error)."""
    log.info("daily_start")

    # Guard: master must be seeded first
    if not MASTER_PATH.exists():
        log.error("universe_master_not_found",
                  hint="Run: python scripts/seed_universe_master.py")
        return 1

    today = today_str()

    async with aiohttp.ClientSession() as session:
        # One HTTP call to exchangeInfo; reused by master update below
        snapshot_df, exchange_info_raw = await select_universe(
            session=session,
            coingecko_api_key=COINGECKO_API_KEY,
        )

    if snapshot_df.empty:
        log.error("universe_empty")
        return 1

    # Write daily snapshot (for collect_hourly + backtest backward compat)
    snap_path = universe_partition_path(today)
    await write_dataframe_direct(snapshot_df, snap_path, overwrite=True)
    log.info("universe_written", path=str(snap_path), n=len(snapshot_df))

    # Extract TRADING symbols for master logic
    trading_syms = {s for s, v in exchange_info_raw.items() if v["status"] == "TRADING"}

    # Load freshwatch tag set (fail-tolerant)
    try:
        fw_syms = load_freshwatch_symbols(FRESHWATCH_PATH)
    except Exception as exc:
        log.warning("freshwatch_load_failed", error=str(exc))
        fw_syms = set()

    # Update universe_master.csv
    master = load_master(MASTER_PATH)

    # 1. Reactivate delisted symbols that returned to exchangeInfo TRADING
    master, reactivated = reactivate_returned(master, trading_syms, today)

    # 2. Update last_seen + apply 72h delist rule
    master, newly_delisted = apply_delisted_72h(master, trading_syms, today)

    # 3. Detect brand-new symbols (in exchangeInfo but never in master)
    known_syms = set(master["symbol"])
    new_syms = trading_syms - known_syms - EXCLUDED_SYMBOLS

    # 4. Build freshwatch notes for new symbols
    notes = {s: "freshwatch" for s in new_syms if s in fw_syms}

    # 5. Append new symbols
    master = append_new_symbols(master, new_syms, today, source="exchangeinfo", notes=notes)

    # 6. Persist
    save_master(master, MASTER_PATH)

    log.info("universe_master_updated",
             new_symbols=len(new_syms),
             newly_delisted=len(newly_delisted),
             reactivated=len(reactivated),
             total_active=int((master["status"] == "active").sum()))

    if reactivated:
        log.info("universe_reactivated", symbols=sorted(reactivated))
    if newly_delisted:
        log.info("universe_delisted", symbols=sorted(newly_delisted))
    if new_syms:
        log.info("universe_added", symbols=sorted(new_syms))

    # 7. Auto-backfill for newly added symbols
    if new_syms:
        await _run_backfill_for_new_symbols(new_syms, fw_syms)

    log.info("daily_complete", n_symbols=len(snapshot_df))
    return 0


@app.command()
def main() -> None:
    """Daily universe refresh + universe_master update."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    raise typer.Exit(asyncio.run(run_daily()))


if __name__ == "__main__":
    app()

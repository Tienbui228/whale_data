#!/usr/bin/env python3
"""W1 seed script: create data/config/universe_master.csv from 3 sources.

Sources (union, dedup by symbol):
  (a) All TRADING USDT-PERP from Binance exchangeInfo (live, today)
  (b) 394 historical symbols from symbols_in_store.txt
  (c) FreshWatch list from data/config/freshwatch_symbols.txt (note tag)

Rules:
  - Historical NOT in current exchangeInfo → status=delisted immediately (no 72h wait)
  - EXCLUDED_SYMBOLS → status=excluded (visible in master, not silently dropped)
  - freshwatch symbols tagged with note=freshwatch in master

Gate (a) output: print counts by source × status.

Usage:
    python scripts/seed_universe_master.py
    python scripts/seed_universe_master.py --force    # overwrite existing master
    python scripts/seed_universe_master.py --dry-run  # print plan, no write
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import aiohttp
import pandas as pd
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import EXCLUDED_SYMBOLS, MASTER_PATH, FRESHWATCH_PATH
from whale_collector.timeutil import today_str
from whale_collector.universe import fetch_exchange_info
from whale_collector.universe_master import (
    MASTER_COLS, save_master, load_freshwatch_symbols,
)

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

HISTORICAL_TXT = Path(__file__).parent.parent / "symbols_in_store.txt"


def load_historical_symbols(path: Path) -> set[str]:
    """Read symbols_in_store.txt; skip header/comment lines, keep all USDT symbols.

    Includes non-ASCII symbols (e.g. Chinese-char Binance perps) — these are real
    trading pairs that appear in exchangeInfo and must not be silently dropped.
    """
    syms: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or not s.endswith("USDT"):
                continue
            syms.add(s)
    return syms


async def _fetch_ei() -> dict[str, dict]:
    async with aiohttp.ClientSession() as session:
        return await fetch_exchange_info(session)


def seed_main(force: bool, dry_run: bool) -> None:
    if MASTER_PATH.exists() and not force and not dry_run:
        print(f"Master already exists: {MASTER_PATH}")
        print("Re-run with --force to overwrite.")
        raise typer.Exit(1)

    today = today_str()
    print(f"Seeding universe_master.csv  date={today}", flush=True)

    # --- Source (a): live exchangeInfo ---
    print("Fetching Binance exchangeInfo...", flush=True)
    exchange_info = asyncio.run(_fetch_ei())
    trading_syms = {s for s, v in exchange_info.items() if v["status"] == "TRADING"}
    all_ei_syms = set(exchange_info.keys())
    print(f"  exchangeInfo TRADING: {len(trading_syms)}", flush=True)

    # --- Source (b): 394 historical (includes non-ASCII Binance perps) ---
    historical = load_historical_symbols(HISTORICAL_TXT)
    print(f"  Historical store:     {len(historical)}", flush=True)

    # --- Source (c): freshwatch tag ---
    fw_syms = load_freshwatch_symbols(FRESHWATCH_PATH)
    print(f"  FreshWatch symbols:   {len(fw_syms)}", flush=True)

    rows: list[dict] = []

    # EXCLUDED_SYMBOLS → status=excluded
    for sym in sorted(EXCLUDED_SYMBOLS):
        rows.append({
            "symbol": sym,
            "added_date": today,
            "source": "seed",
            "status": "excluded",
            "note": "excluded_config",
            "last_seen_exchangeinfo": today if sym in all_ei_syms else "",
        })

    # Historical symbols (minus excluded)
    known_excluded = EXCLUDED_SYMBOLS
    for sym in sorted(historical - known_excluded):
        if sym in trading_syms:
            status = "active"
            last_seen = today
        elif sym in all_ei_syms:
            status = "delisted"
            last_seen = today
        else:
            status = "delisted"
            last_seen = ""  # never seen in current exchangeInfo
        rows.append({
            "symbol": sym,
            "added_date": today,
            "source": "seed",
            "status": status,
            "note": "freshwatch" if sym in fw_syms else "",
            "last_seen_exchangeinfo": last_seen,
        })

    # New from current exchangeInfo (not in historical, not excluded)
    already_known = historical | known_excluded
    for sym in sorted(trading_syms - already_known):
        rows.append({
            "symbol": sym,
            "added_date": today,
            "source": "exchangeinfo",
            "status": "active",
            "note": "freshwatch" if sym in fw_syms else "",
            "last_seen_exchangeinfo": today,
        })

    df = pd.DataFrame(rows, columns=MASTER_COLS)

    # --- Gate (a): counts by source × status ---
    print("\n=== Gate (a): universe_master seed counts ===")
    for (src, stat), grp in df.groupby(["source", "status"]):
        print(f"  {src:<14} / {stat:<10} : {len(grp)}")
    print(f"  {'TOTAL':<14}   {'':10}  {len(df)}")
    active_n = (df["status"] == "active").sum()
    delisted_n = (df["status"] == "delisted").sum()
    excluded_n = (df["status"] == "excluded").sum()
    fw_tagged = (df["note"] == "freshwatch").sum()
    print(f"\n  active={active_n}  delisted={delisted_n}  excluded={excluded_n}  fw_tagged={fw_tagged}")

    if dry_run:
        print("\n[dry-run] master NOT written.")
        return

    save_master(df, MASTER_PATH)
    print(f"\nWritten -> {MASTER_PATH}")
    print("Seed complete. Run collect_daily.py to verify auto-union logic.")


@app.command()
def main(
    force: bool = typer.Option(False, help="Overwrite existing master"),
    dry_run: bool = typer.Option(False, help="Print plan only, no write"),
) -> None:
    """W1 seed: create universe_master.csv from exchangeInfo + historical + freshwatch."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    seed_main(force=force, dry_run=dry_run)


if __name__ == "__main__":
    app()

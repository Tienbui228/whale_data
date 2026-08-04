#!/usr/bin/env python3
"""E3-alpha-v2: Binance Alpha klines 1d collector — price/vol ONLY, taker=ABSTAIN.

Ported from: Check onchain fresh wallets/_s3_v2.py (section 6 fetch logic).

Endpoint:  https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines
Symbol:    {alpha_id}USDT  (e.g. ALPHA_223USDT for IDOL)
Venue:     binance_alpha   (replaces deprecated binance_spot_bsc)

Guard: klines[9] == klines[5] always on Alpha (taker=total vol, broken field).
       taker_buy_* set NaN; taker_abstain=True; see guard comment in _parse_row.

Config:    data/config/alpha_id_map.json  →  {futures_base: alpha_id}
Missing config → ERROR + exit≠0 + Telegram alert (L-44 rule: no silent no-op).

Throttle:  0.4s between calls; exponential backoff on 4xx/5xx (WAF risk).
Store:     raw/spot_klines_1d/ (same partition schema as collect_spot_daily).

Cron:      02:00 UTC daily (after collect_spot_daily 01:05 UTC).
Usage:
    python scripts/collect_alpha_daily.py
    python scripts/collect_alpha_daily.py --dry-run
    python scripts/collect_alpha_daily.py --days-back 3
    python scripts/collect_alpha_daily.py --symbols IDOL,TAG
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
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
    META_DIR, SCHEMA_VERSION, COMPRESSION, COMPRESSION_LEVEL,
)
from whale_collector.timeutil import now_ms, ms_to_date_str, DAY_MS
from whale_collector.storage.paths import spot_klines_partition_path
from whale_collector.alert import telegram_error

# Column schema — mirrors collect_spot_daily._SPOT_KLINES_COLS exactly.
# Inline here to avoid importing collect_spot_daily (which loads aiohttp).
_SPOT_KLINES_COLS = [
    "symbol", "date_str",
    "open", "high", "low", "close",
    "base_vol", "quote_vol", "n_trades",
    "taker_buy_base_vol", "taker_buy_quote_vol", "taker_buy_pct",
    "venue", "taker_abstain",
    "fetched_at_ms", "schema_version",
]



log = structlog.get_logger()
app = typer.Typer(add_completion=False)

BAPI_BASE        = "https://www.binance.com"
BAPI_KLINES_PATH = "/bapi/defi/v1/public/alpha-trade/klines"
UA               = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
ALPHA_MAP_PATH   = Path(__file__).parent.parent / "data" / "config" / "alpha_id_map.json"

_CALL_SLEEP   = 0.4   # between each symbol call
_RETRY_SLEEP  = 5.0   # base sleep on 429/503
_MAX_RETRIES  = 3


def _load_alpha_map(path: Path) -> dict[str, str]:
    if not path.exists():
        msg = (f"alpha_map_missing: {path} not found. "
               "Run: python _task_write_alpha_config_20260804.py")
        log.error("alpha_map_missing", path=str(path))
        telegram_error(msg)
        raise SystemExit(1)
    mapping = json.loads(path.read_text(encoding="utf-8"))
    log.info("alpha_map_loaded", count=len(mapping))
    return mapping


def _bapi_get(path: str, params: dict) -> tuple[Optional[list], int]:
    """Fetch bapi endpoint with retry on 429/503. Returns (klines_list, status)."""
    qs  = urllib.parse.urlencode(params)
    url = f"{BAPI_BASE}{path}?{qs}"
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = json.loads(r.read().decode())
                arr = raw if isinstance(raw, list) else (
                    raw.get("data", []) if isinstance(raw, dict) else [])
                return arr, 200
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (429, 503) and attempt < _MAX_RETRIES - 1:
                sleep_t = _RETRY_SLEEP * (2 ** attempt)
                log.warning("alpha_rate_limited", code=code, sleep=sleep_t)
                time.sleep(sleep_t)
            else:
                return None, code
        except Exception as exc:
            log.warning("alpha_fetch_error", exc=str(exc), attempt=attempt)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_SLEEP)
            else:
                return None, 0
    return None, 0


def _parse_alpha_row(k: list, symbol: str, date_str: str, fetched_at: int) -> pd.DataFrame:
    """Parse one daily Alpha kline.

    # GUARD: DO NOT read klines[9] (taker_buy_base_vol) on Alpha endpoint.
    # klines[9] == klines[5] always (100% taker = broken Alpha API field).
    # Reading it would silently poison taker_buy_pct in all downstream joins.
    """
    open_  = float(k[1]); high  = float(k[2])
    low    = float(k[3]); close = float(k[4])
    base_vol  = float(k[5] or 0)
    quote_vol = float(k[7] or 0)
    try:
        n_trades = int(k[8])
    except (IndexError, ValueError, TypeError):
        n_trades = 0
    # Compute avg_px = quote_vol / base_vol (fallback to close if zero)
    avg_px = quote_vol / base_vol if base_vol > 0 else close

    return pd.DataFrame([{
        "symbol": symbol, "date_str": date_str,
        "open": open_, "high": high, "low": low, "close": avg_px,
        "base_vol": base_vol, "quote_vol": quote_vol, "n_trades": n_trades,
        "taker_buy_base_vol":  float("nan"),  # GUARD: never read on Alpha
        "taker_buy_quote_vol": float("nan"),  # GUARD: never read on Alpha
        "taker_buy_pct":       float("nan"),  # GUARD: never read on Alpha
        "venue": "binance_alpha",
        "taker_abstain": True,
        "fetched_at_ms": fetched_at,
        "schema_version": SCHEMA_VERSION,
    }], columns=_SPOT_KLINES_COLS)


def _write_partition(df: pd.DataFrame, date_str: str) -> None:
    if df.empty:
        return
    path = spot_klines_partition_path(date_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        # Remove old binance_alpha rows for symbols we're about to write (dedup)
        syms = set(df["symbol"])
        existing = existing[~((existing["venue"] == "binance_alpha") &
                              (existing["symbol"].isin(syms)))]
        df = pd.concat([existing, df], ignore_index=True)
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        path, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL,
    )


def run_alpha_daily(
    *,
    days_back: int = 1,
    symbols_override: Optional[list[str]] = None,
    dry_run: bool = False,
) -> int:
    alpha_map = _load_alpha_map(ALPHA_MAP_PATH)

    if symbols_override:
        work = {s: alpha_map[s] for s in symbols_override if s in alpha_map}
        missing = [s for s in symbols_override if s not in alpha_map]
        if missing:
            log.warning("alpha_symbols_not_in_map", missing=missing)
    else:
        work = alpha_map

    if not work:
        log.error("alpha_daily_no_symbols")
        return 1

    log.info("alpha_daily_start", symbols=len(work), days_back=days_back, dry_run=dry_run)

    if dry_run:
        log.info("dry_run_symbols", symbols=list(work.keys())[:10])
        return 0

    t_now   = now_ms()
    total_ok  = 0; total_err = 0

    for day_offset in range(days_back - 1, -1, -1):
        day_start = ((t_now // DAY_MS) - 1 - day_offset) * DAY_MS
        day_end   = day_start + DAY_MS
        date_str  = ms_to_date_str(day_start)
        log.info("alpha_daily_day", date=date_str, symbols=len(work))
        day_ok = 0; day_err = 0

        for sym, alpha_id in work.items():
            ticker = f"{alpha_id}USDT"
            arr, status = _bapi_get(BAPI_KLINES_PATH, {
                "symbol": ticker, "interval": "1d",
                "startTime": day_start, "endTime": day_end - 1, "limit": 1,
            })
            if status != 200:
                log.warning("alpha_fetch_error", symbol=sym, alpha_id=alpha_id,
                            date=date_str, status=status)
                day_err += 1
                time.sleep(_CALL_SLEEP)
                continue
            if not arr:
                # status=200, empty response = no Alpha trading on this day (normal)
                log.debug("alpha_no_trading", symbol=sym, date=date_str)
                time.sleep(_CALL_SLEEP)
                continue

            k = arr[0]
            close_time_ms = int(k[6]) if len(k) > 6 else 0
            if close_time_ms > t_now:
                log.debug("alpha_candle_open", symbol=sym, date=date_str)
                day_ok += 0
                time.sleep(_CALL_SLEEP)
                continue

            df = _parse_alpha_row(k, sym, date_str, t_now)
            _write_partition(df, date_str)
            day_ok += 1
            time.sleep(_CALL_SLEEP)

        log.info("alpha_daily_day_done", date=date_str, ok=day_ok, errors=day_err)
        total_ok += day_ok; total_err += day_err

    log.info("alpha_daily_complete", total_ok=total_ok, total_err=total_err)

    if total_err > 0:
        log.warning("alpha_daily_errors", total_err=total_err, total_ok=total_ok)
    if total_ok == 0 and total_err > 0:
        telegram_error(f"collect_alpha_daily: 0 rows written, {total_err} errors (all HTTP fail)")
        return 1
    return 0


@app.command()
def main(
    days_back:  int            = typer.Option(1, help="Ngày collect (default=1=hôm qua)"),
    symbols:    Optional[str]  = typer.Option(None, help="Override symbols (comma-separated)"),
    dry_run:    bool           = typer.Option(False, help="Validate only — no API calls"),
) -> None:
    """E3-alpha-v2: Collect Binance Alpha price/vol (NO taker) cho toàn u50 universe."""
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ])
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    code = run_alpha_daily(
        days_back=days_back,
        symbols_override=sym_list,
        dry_run=dry_run,
    )
    raise typer.Exit(code)


if __name__ == "__main__":
    app()

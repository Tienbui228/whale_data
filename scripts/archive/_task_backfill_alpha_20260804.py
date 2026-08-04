#!/usr/bin/env python3
"""TASK: Backfill full Alpha klines history — 137 u50 symbols.

Fetch limit=1000 per symbol (bapi/alpha, 1d candles) → ghi raw/spot_klines_1d/.
Chỉ ghi nến đóng (close_time_ms <= now_ms).
Dedup trên (symbol, date_str) khi append vào partition có sẵn.

Throttle: 0.5s per symbol, 3s sau mỗi 20 symbols (WAF safe).
Log tiến độ mỗi 10 symbols.
Archive sau khi chạy xong (án một lần).
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

sys.path.insert(0, str(Path(__file__).parent))

from whale_collector.config import SCHEMA_VERSION, COMPRESSION, COMPRESSION_LEVEL
from whale_collector.timeutil import ms_to_date_str
from whale_collector.storage.paths import spot_klines_partition_path

log = structlog.get_logger()
structlog.configure(processors=[
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.dev.ConsoleRenderer(),
])

BAPI_BASE   = "https://www.binance.com"
KLINES_PATH = "/bapi/defi/v1/public/alpha-trade/klines"
UA          = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MAP_PATH    = Path(__file__).parent / "data" / "config" / "alpha_id_map.json"

_SPOT_KLINES_COLS = [
    "symbol", "date_str", "open", "high", "low", "close",
    "base_vol", "quote_vol", "n_trades",
    "taker_buy_base_vol", "taker_buy_quote_vol", "taker_buy_pct",
    "venue", "taker_abstain", "fetched_at_ms", "schema_version",
]


def bget(path, params):
    qs  = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{BAPI_BASE}{path}?{qs}", headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = json.loads(r.read().decode())
                return (raw if isinstance(raw, list)
                        else raw.get("data", []) if isinstance(raw, dict) else []), 200
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1))
            else:
                return None, e.code
        except Exception as ex:
            if attempt < 2:
                time.sleep(5)
            else:
                return None, str(ex)
    return None, 0


def parse_klines(arr, sym, now_ms, fetched_at):
    """Parse full history array. Skip open candle (close_time > now_ms)."""
    rows = []
    for k in arr:
        if not isinstance(k, (list, tuple)) or len(k) < 8:
            continue
        try:
            open_ms    = int(k[0])
            close_ms   = int(k[6]) if len(k) > 6 else open_ms + 86_400_000 - 1
            if close_ms > now_ms:
                continue  # open candle — skip
            date_str = ms_to_date_str(open_ms)
            open_  = float(k[1]); high = float(k[2])
            low    = float(k[3]); close = float(k[4])
            bv     = float(k[5] or 0)
            qv     = float(k[7] or 0)
            try:    n_trades = int(k[8])
            except: n_trades = 0
            avg_px = qv / bv if bv > 0 else close
            rows.append({
                "symbol": sym, "date_str": date_str,
                "open": open_, "high": high, "low": low, "close": avg_px,
                "base_vol": bv, "quote_vol": qv, "n_trades": n_trades,
                "taker_buy_base_vol":  float("nan"),
                "taker_buy_quote_vol": float("nan"),
                "taker_buy_pct":       float("nan"),
                "venue": "binance_alpha", "taker_abstain": True,
                "fetched_at_ms": fetched_at, "schema_version": SCHEMA_VERSION,
            })
        except Exception:
            pass
    return rows


def write_partition_dedup(rows_by_date: dict[str, list[dict]]) -> tuple[int, int]:
    """Write/append rows grouped by date_str. Dedup on (symbol, date_str)."""
    written = 0; partitions = 0
    for date_str, rows in sorted(rows_by_date.items()):
        df_new = pd.DataFrame(rows, columns=_SPOT_KLINES_COLS)
        path = spot_klines_partition_path(date_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = pd.read_parquet(path)
            # Dedup: remove rows for symbols we're about to write
            syms_in_new = set(df_new["symbol"])
            existing = existing[~existing["symbol"].isin(syms_in_new)]
            df_new = pd.concat([existing, df_new], ignore_index=True)
        pq.write_table(
            pa.Table.from_pandas(df_new, preserve_index=False),
            path, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL,
        )
        written += len(rows)
        partitions += 1
    return written, partitions


# ── MAIN ──────────────────────────────────────────────────────────────────────

alpha_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))
log.info("backfill_start", symbols=len(alpha_map))

now_ms     = int(datetime.now(timezone.utc).timestamp() * 1000)
fetched_at = now_ms

# Collect all candles across all symbols, group by date
rows_by_date: dict[str, list[dict]] = defaultdict(list)
total_syms   = len(alpha_map)
sym_ok = 0; sym_fail = 0
all_rows = 0

for i, (sym, alpha_id) in enumerate(sorted(alpha_map.items()), 1):
    ticker = f"{alpha_id}USDT"
    arr, status = bget(KLINES_PATH, {"symbol": ticker, "interval": "1d", "limit": 1000})

    if status != 200 or not arr:
        log.warning("backfill_fetch_fail", symbol=sym, alpha_id=alpha_id, status=status)
        sym_fail += 1
    else:
        rows = parse_klines(arr, sym, now_ms, fetched_at)
        for r in rows:
            rows_by_date[r["date_str"]].append(r)
        all_rows += len(rows)
        sym_ok += 1
        if i % 10 == 0 or i == total_syms:
            log.info("backfill_progress",
                     done=i, total=total_syms, ok=sym_ok, fail=sym_fail,
                     candles_so_far=all_rows, dates=len(rows_by_date))

    time.sleep(0.5)
    if i % 20 == 0:
        log.info("backfill_pause_20", i=i)
        time.sleep(3)

log.info("backfill_fetch_done", ok=sym_ok, fail=sym_fail,
         total_candles=all_rows, date_partitions=len(rows_by_date))

# Write all partitions
log.info("backfill_writing", partitions=len(rows_by_date))
written, parts = write_partition_dedup(rows_by_date)
log.info("backfill_complete", rows_written=written, partitions_written=parts,
         sym_fail=sym_fail)

# Sample verification: print 3 rows from 2 recent partitions
import sys
dates_sorted = sorted(rows_by_date.keys())[-3:]
print("\n=== SAMPLE VERIFICATION (3 rows × 3 recent dates) ===")
for ds in dates_sorted:
    path = spot_klines_partition_path(ds)
    df = pd.read_parquet(path)
    alpha_rows = df[df["venue"] == "binance_alpha"]
    sample = alpha_rows[["symbol","date_str","close","quote_vol","venue"]].head(3)
    print(f"\nPartition {ds}: {len(alpha_rows)} alpha rows total")
    print(sample.to_string(index=False))

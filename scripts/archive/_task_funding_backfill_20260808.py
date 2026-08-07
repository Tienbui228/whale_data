#!/usr/bin/env python3
"""Backfill VPS funding_8h store từ fapi fundingRate historical.
Chiến lược: 1 fapi call per symbol×month, insert missing rows, nhãn source=fapi_backfill.
Chạy script trên VPS, chỉ copy text result về local.
"""
import sys, subprocess, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"

def ssh_run(cmd, timeout=300, label=""):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

# Build backfill script on VPS
backfill_script = r"""
import pandas as pd, json, time, sys
from datetime import datetime, timezone, timedelta
import urllib.request, urllib.error

BASE = "/root/Data_back_test/whale_data"
PARQ_DIR = BASE + "/data/raw/funding_8h"
INTERVALS_JSON = BASE + "/data/config/funding_intervals.json"

with open(INTERVALS_JSON) as f:
    iv_raw = json.load(f)

def get_interval_h(sym):
    v = iv_raw.get(sym)
    if v is None:
        return 8
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, dict):
        return int(v.get("interval_h", v.get("interval", 8)))
    return 8

def day_ms(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    s = int(dt.timestamp() * 1000)
    return s, s + 86_400_000- 1

def settlement_ts_expected(date_str, ih):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    base = int(dt.timestamp() * 1000)
    step = ih * 3600 * 1000
    return set(base + i * step for i in range(24 // ih))

def iter_dates(start, end):
    d = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    e = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    while d <= e:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)

def fapi_funding(sym, start_ms, end_ms, retries=3):
    url = (f"https://fapi.binance.com/fapi/v1/fundingRate?"
           f"symbol={sym}&startTime={start_ms}&endTime={end_ms}&limit=1000")
    for attempt in range(retries):
        try:
            resp = urllib.request.urlopen(url, timeout=20)
            import json as _json
            return _json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return None
    return None

# Load monthly parquets
dfs = {}
for m in ["2026-07", "2026-08"]:
    path = f"{PARQ_DIR}/month={m}/part-0.parquet"
    try:
        dfs[m] = pd.read_parquet(path)
    except Exception as e:
        print(f"WARN {path}: {e}", file=sys.stderr)

# All symbols
all_syms = sorted(set(s for df in dfs.values() for s in df['symbol'].unique()))

# Process per symbol: find gaps, fetch fapi, collect new rows
total_inserted = 0
total_gap_syms = 0
new_rows_all = {"2026-07": [], "2026-08": []}

now_ms = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000)

LOG_INTERVAL = 50  # print every N symbols

for i, sym in enumerate(all_syms):
    ih = get_interval_h(sym)
    exp = 24 // ih
    sym_gaps = {}  # date -> set of missing ts

    for m_str, df in dfs.items():
        start_d = m_str + "-01"
        # end: last day of data or today
        sub_sym = df[df['symbol'] == sym]
        if len(sub_sym) == 0:
            continue

        for d in iter_dates(start_d, "2026-08-08"):
            if d[:7] != m_str:
                continue
            s, e = day_ms(d)
            sub = sub_sym[(sub_sym['as_of_ts_ms'] >= s) & (sub_sym['as_of_ts_ms'] <= e)]
            if len(sub) == 0:
                continue
            exp_ts = settlement_ts_expected(d, ih)
            actual_ts = set(sub['as_of_ts_ms'].unique())
            missing = exp_ts - actual_ts
            if missing:
                sym_gaps[d] = missing

    if not sym_gaps:
        continue

    total_gap_syms += 1
    # Fetch from fapi for the full range (Jul 01 → Aug 08)
    range_start_ms, _ = day_ms("2026-07-01")
    _, range_end_ms = day_ms("2026-08-08")
    fapi_data = fapi_funding(sym, range_start_ms, range_end_ms)
    if fapi_data is None:
        print(f"  WARN: fapi failed for {sym}")
        continue

    # Build set of fapi settlement timestamps
    fapi_ts_map = {int(r["fundingTime"]): r for r in fapi_data}

    # Insert missing rows
    for d, missing_ts in sym_gaps.items():
        m_str = d[:7]
        for ts in missing_ts:
            if ts not in fapi_ts_map:
                continue  # fapi doesn't have this (symbol may not have existed yet)
            r = fapi_ts_map[ts]
            row = {
                "symbol": sym,
                "as_of_ts_ms": ts,
                "funding_rate": float(r["fundingRate"]),
                "mark_price": float(r.get("markPrice", float("nan"))),
                "fetched_at_ms": now_ms,
                "schema_version": 1,
                "source": "fapi_backfill",
            }
            new_rows_all[m_str].append(row)
            total_inserted += 1

    if (i + 1) % LOG_INTERVAL == 0:
        print(f"  Progress: {i+1}/{len(all_syms)} syms, {total_inserted} rows queued", flush=True)
    time.sleep(0.05)  # polite rate limit

print(f"  Fetch complete: {total_gap_syms} syms had gaps, {total_inserted} backfill rows")

# Write to parquet (append + dedup)
import pyarrow as pa, pyarrow.parquet as pq

saved = 0
for m_str, new_rows in new_rows_all.items():
    if not new_rows:
        continue
    path = f"{PARQ_DIR}/month={m_str}/part-0.parquet"
    df_new = pd.DataFrame(new_rows)
    df_old = dfs[m_str]

    # Add 'source' column to old if missing
    if 'source' not in df_old.columns:
        df_old = df_old.copy()
        df_old['source'] = "collector"

    df_combined = pd.concat([df_old, df_new], ignore_index=True)
    # Dedup on (symbol, as_of_ts_ms): keep 'fapi_backfill' over 'collector' for same ts
    df_combined = df_combined.sort_values("source", ascending=False)  # fapi_backfill < collector alpha
    df_combined = df_combined.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
    df_combined = df_combined.sort_values(["symbol", "as_of_ts_ms"]).reset_index(drop=True)

    df_combined.to_parquet(path, index=False)
    saved += len(new_rows)
    print(f"  Wrote {len(new_rows)} new rows to {path} (total {len(df_combined)})")

print(f"BACKFILL DONE: {saved} rows inserted")
"""

print("=== Writing backfill script to VPS ===")
out0, err0, rc0 = ssh_run(
    "cat > /tmp/funding_backfill.py << 'XBFILL'\n" + backfill_script + "\nXBFILL"
)
print(f"  write rc={rc0} {err0[:80] if err0 else 'ok'}")

print("\n=== Running backfill on VPS (may take 5-10 min for 526 symbols) ===")
print("  (polite 50ms delay per symbol, ~526 fapi calls)")
out, err, rc = ssh_run(
    "python3 /tmp/funding_backfill.py 2>&1 | tee /tmp/funding_backfill_log.txt",
    timeout=600,
    label="backfill"
)
print(out[-3000:] if len(out) > 3000 else out)
if rc != 0:
    print(f"  stderr: {err[:400]}")

# Write log locally
report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "docs", "reports", "_funding_backfill_20260808.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(out)
print(f"\n  Full log: {report_path}")

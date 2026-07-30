#!/usr/bin/env python3
"""B4: BULLA 07-20 topLSR_pos canonical từ VPS store + so sánh twelve_cases nếu có."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess, tempfile, os

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

probe = r'''
import pandas as pd
from pathlib import Path

DATA = Path("/root/Data_back_test/whale_data/data")

print("=== B4: BULLA 07-20 topLSR_pos từ mọi nguồn có trong store ===\n")

# SOURCE 1: freshwatch_daily export CSV (derived_1h)
csv = DATA / "export" / "freshwatch_daily_2026-07.csv"
if csv.exists():
    df = pd.read_csv(csv)
    bulla = df[(df["symbol"] == "BULLAUSDT") & (df["date"] == "2026-07-20")]
    if not bulla.empty:
        row = bulla.iloc[0]
        print(f"[S1] freshwatch_daily_2026-07.csv (derived_1h):")
        print(f"  lsr_pos_r  = {row['lsr_pos_r']}")
        print(f"  lsr_acc_r  = {row['lsr_acc_r']}")
        print(f"  src_ratio  = {row['src_ratio']}")
        print(f"  low_conf   = {row.get('low_conf', 'N/A')}")
        print(f"  fn         = {row.get('fn', 'N/A')}")
    else:
        print("[S1] freshwatch_daily: BULLA 07-20 NOT FOUND")
else:
    print(f"[S1] CSV not found: {csv}")

# SOURCE 2: top_pos_1h — keep-last of 07-20 (last entry = closest to 23:xx UTC)
p20 = DATA / "raw" / "top_pos_1h" / "date=2026-07-20" / "part-0.parquet"
if p20.exists():
    df20 = pd.read_parquet(p20)
    b20 = df20[df20["symbol"] == "BULLAUSDT"].sort_values("as_of_ts_ms")
    if not b20.empty:
        last = b20.iloc[-1]
        import datetime
        ts_utc = datetime.datetime.utcfromtimestamp(last["as_of_ts_ms"] / 1000)
        print(f"\n[S2] top_pos_1h date=2026-07-20 keep-last:")
        print(f"  long_short_ratio (topLSR_pos) = {last['long_short_ratio']:.4f}")
        print(f"  long_account                  = {last['long_account']:.4f}")
        print(f"  short_account                 = {last['short_account']:.4f}")
        print(f"  as_of_ts_ms = {last['as_of_ts_ms']} ({ts_utc} UTC)")
        print(f"  Row count 07-20: {len(b20)}")
        # Also show all rows for that day
        print(f"  All rows: as_of_ts_ms range [{b20['as_of_ts_ms'].min()} .. {b20['as_of_ts_ms'].max()}]")
    else:
        print("\n[S2] top_pos_1h 07-20: BULLA not found")
else:
    print(f"\n[S2] top_pos_1h date=2026-07-20 not found at {p20}")

# SOURCE 3: top_pos_1h — first entry of 07-21 (= snapshot AT 00:00 UTC 21/07)
TS_00UTC_21 = 1753056000000
p21 = DATA / "raw" / "top_pos_1h" / "date=2026-07-21" / "part-0.parquet"
if p21.exists():
    df21 = pd.read_parquet(p21)
    b21 = df21[df21["symbol"] == "BULLAUSDT"].sort_values("as_of_ts_ms")
    if not b21.empty:
        # Exact match at 00:00 UTC
        snap = b21[b21["as_of_ts_ms"] == TS_00UTC_21]
        first = b21.iloc[0]
        import datetime
        ts_first = datetime.datetime.utcfromtimestamp(first["as_of_ts_ms"] / 1000)
        print(f"\n[S3] top_pos_1h date=2026-07-21 first entry ({ts_first} UTC):")
        print(f"  long_short_ratio = {first['long_short_ratio']:.4f}")
        if not snap.empty:
            print(f"  Exact 00:00 UTC match: long_short_ratio = {snap.iloc[0]['long_short_ratio']:.4f}")
        else:
            print(f"  No exact match at TS={TS_00UTC_21} (first entry differs)")
else:
    print(f"\n[S3] top_pos_1h date=2026-07-21 not found")

# SOURCE 4: top_pos_1d (daily native) — should have a single row per symbol
p1d_20 = DATA / "raw" / "top_pos_1d" / "date=2026-07-20" / "part-0.parquet"
p1d_21 = DATA / "raw" / "top_pos_1d" / "date=2026-07-21" / "part-0.parquet"
for label, pp in [("07-20", p1d_20), ("07-21", p1d_21)]:
    if pp.exists():
        df_d = pd.read_parquet(pp)
        b_d = df_d[df_d["symbol"] == "BULLAUSDT"]
        if not b_d.empty:
            print(f"\n[S4] top_pos_1d {label}: {b_d[['symbol','long_short_ratio','long_account','short_account']].to_string()}")
        else:
            print(f"\n[S4] top_pos_1d {label}: BULLA not found in parquet")
    else:
        print(f"\n[S4] top_pos_1d {label}: not available")

# Show top_pos_1d available dates
top1d = DATA / "raw" / "top_pos_1d"
if top1d.exists():
    dates = sorted([d.name for d in top1d.iterdir() if d.is_dir()])
    print(f"\n[S4] top_pos_1d available dates: {dates}")

print("\n=== VERDICT ===")
print("native_1d (S4) for 07-20: see above")
print("derived_1h (S1): lsr_pos_r from freshwatch_daily CSV (see above)")
print("raw 1h last-of-day (S2): see above")
print("raw 1h first-of-21 (S3): see above")
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(probe)
    tmp = f.name

r = subprocess.run(
    ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", tmp,
     "root@5.223.67.21:/tmp/probe_b4_bulla.py"],
    capture_output=True
)
os.unlink(tmp)
print(f"SCP: {'OK' if r.returncode == 0 else r.stderr.decode()}")

result = subprocess.run(
    ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST,
     "cd /root/Data_back_test/whale_data && python3 /tmp/probe_b4_bulla.py 2>&1"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])

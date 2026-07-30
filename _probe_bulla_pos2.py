#!/usr/bin/env python3
"""Probe top_pos_1h 00:00 UTC 21/07 for BULLA (dedup keep-last of 07-20 daily)."""
import sys, io, subprocess, tempfile, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

probe = '''
import pandas as pd
from pathlib import Path

DATA = Path("/root/Data_back_test/whale_data/data/raw")
TS_00UTC_21 = 1753056000000  # 2026-07-21 00:00:00 UTC

# top_pos_1h date=2026-07-20 and date=2026-07-21
for date_str in ["2026-07-20", "2026-07-21"]:
    p = DATA / "top_pos_1h" / f"date={date_str}" / "part-0.parquet"
    if not p.exists():
        print(f"{date_str}: no parquet")
        continue
    df = pd.read_parquet(p)
    bulla = df[df["symbol"] == "BULLAUSDT"].copy()
    print(f"\\n{date_str}: {len(bulla)} rows, cols={list(bulla.columns)}")
    # as_of_ts_ms is the canonical snapshot timestamp
    col_ts = "as_of_ts_ms"
    if col_ts not in bulla.columns:
        col_ts = [c for c in bulla.columns if "ts" in c.lower() or "time" in c.lower()][0]
    bulla = bulla.sort_values(col_ts)
    print(bulla[[col_ts, "long_short_ratio", "long_account", "short_account"]].tail(5).to_string())

# dedup keep-last of day 07-20: all top_pos_1h rows for 07-20, take max(as_of_ts_ms)
p20 = DATA / "top_pos_1h" / "date=2026-07-20" / "part-0.parquet"
if p20.exists():
    df20 = pd.read_parquet(p20)
    bulla20 = df20[df20["symbol"] == "BULLAUSDT"].sort_values("as_of_ts_ms")
    last_row = bulla20.tail(1)
    print(f"\\n=== BULLA 07-20 dedup keep-last (top_pos_1h) ===")
    print(f"  as_of_ts_ms: {last_row['as_of_ts_ms'].values[0]}")
    print(f"  long_short_ratio (topLSR_pos): {last_row['long_short_ratio'].values[0]:.4f}")
    print(f"  long_account: {last_row['long_account'].values[0]:.4f}")
    print(f"  short_account: {last_row['short_account'].values[0]:.4f}")
    import datetime
    ts = int(last_row["as_of_ts_ms"].values[0])
    print(f"  timestamp UTC: {datetime.datetime.utcfromtimestamp(ts/1000)}")
    # Also check row closest to 00:00 UTC 21/07
    snap = bulla20[bulla20["as_of_ts_ms"] == TS_00UTC_21]
    if not snap.empty:
        print(f"\\n  Snapshot at exactly 00:00 UTC 21/07: long_short_ratio={snap['long_short_ratio'].values[0]:.4f}")
    else:
        print(f"\\n  No exact match for 00:00 UTC 21/07 in date=2026-07-20 partition")
        # Try date=2026-07-21
        p21 = DATA / "top_pos_1h" / "date=2026-07-21" / "part-0.parquet"
        if p21.exists():
            df21 = pd.read_parquet(p21)
            bulla21 = df21[df21["symbol"] == "BULLAUSDT"].sort_values("as_of_ts_ms")
            snap21 = bulla21[bulla21["as_of_ts_ms"] == TS_00UTC_21]
            if not snap21.empty:
                print(f"  Found in date=2026-07-21: long_short_ratio={snap21['long_short_ratio'].values[0]:.4f}")
            else:
                first = bulla21.head(1)
                print(f"  First entry in date=2026-07-21: ts={first['as_of_ts_ms'].values[0]}, "
                      f"lsr={first['long_short_ratio'].values[0]:.4f}")
'''

# Write and SCP probe
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(probe)
    tmp = f.name

r = subprocess.run(
    ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", tmp, "root@5.223.67.21:/tmp/probe_bulla3.py"],
    capture_output=True
)
os.unlink(tmp)
print(f"SCP: {'OK' if r.returncode == 0 else r.stderr.decode()}")

result = subprocess.run(
    ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST,
     "cd /root/Data_back_test/whale_data && python3 /tmp/probe_bulla3.py 2>&1"],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])

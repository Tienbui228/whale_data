#!/usr/bin/env python3
"""Probe: (1) VPS data/raw/ store list — check available 1h stores for 24-26/07.
          (2) Check if other stores (klines_1h, oi_1h, taker_1h, funding_1h) exist.
"""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

REPO = Path(__file__).resolve().parent
VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# 1. List all stores under data/raw/
print("=== VPS data/raw/ — store list ===")
out, _ = ssh(f"ls {BASE}/data/raw/")
print(out)

print()

# 2. For each interesting store, check if 24-26/07 partition exists + row count
stores_to_check = [
    "klines_1h", "klines_4h", "klines_1d",
    "taker_1h", "taker_long_short_1h",
    "oi_1h", "oi_snapshots",
    "funding_1h", "funding_snapshots",
    "top_pos_1d",
]

print("=== Store x date check ===")
for store in stores_to_check:
    for d in ["2026-07-24", "2026-07-25", "2026-07-26"]:
        path = f"{BASE}/data/raw/{store}/date={d}"
        out2, _ = ssh(f"ls {path}/ 2>/dev/null | wc -l")
        if out2.strip() != "0":
            # Get a sample to see columns
            out3, _ = ssh(
                f"python3 -c \""
                f"import glob, pandas as pd; "
                f"files=glob.glob('{path}/*.parquet'); "
                f"df=pd.concat([pd.read_parquet(f) for f in files[:1]]) if files else pd.DataFrame(); "
                f"print(list(df.columns)[:10], 'rows:', len(df))\"",
                timeout=30,
            )
            print(f"  {store}/{d}: {out2.strip()} files | {out3[:120]}")

print()
print("=== DỪNG — xem cột nào có cho regen ===")

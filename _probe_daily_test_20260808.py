#!/usr/bin/env python3
"""Probe Việc 3.5: test gom_scan --daily offline.

Steps:
1. SCP freshwatch CSVs from VPS → local scratch/fw_csv_test/
2. Run gom_scan --daily --store scratch/fw_csv_test/ --date 2026-08-06
3. Run same for 2026-08-05
4. Paste output 2-3 interesting tokens
"""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import os

VPS      = "root@5.223.67.21"
VPS_CSV  = "/root/Data_back_test/whale_data/data/export/"
REPO     = Path(__file__).resolve().parent
LOCAL_CSV = REPO / "scratch" / "fw_csv_test"
GOM      = REPO / "scripts" / "gom_scan.py"

# ── Step 1: SCP freshwatch CSVs from VPS ─────────────────────────────────────
print("=== Step 1: SCP freshwatch_daily CSVs from VPS ===")
LOCAL_CSV.mkdir(parents=True, exist_ok=True)

scp_args = [
    "scp",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=10",
    f"{VPS}:{VPS_CSV}freshwatch_daily_2026-07.csv",
    f"{VPS}:{VPS_CSV}freshwatch_daily_2026-08.csv",
    str(LOCAL_CSV) + "/",
]
r = subprocess.run(scp_args, capture_output=True, encoding="utf-8", errors="replace", timeout=60)
print(f"SCP rc={r.returncode}")
if r.stderr:
    print("SCP stderr:", r.stderr[:300])

# List what we got
local_files = list(LOCAL_CSV.glob("*.csv"))
print(f"Local CSV files: {[f.name for f in local_files]}")
if not local_files:
    print("ERROR: no CSV files downloaded — check VPS path or SSH key")
    sys.exit(1)

# Quick shape check
import pandas as pd
for csv_path in sorted(local_files):
    df = pd.read_csv(csv_path)
    print(f"  {csv_path.name}: {len(df)} rows, {df['symbol'].nunique()} symbols, "
          f"dates {df['date'].min()} → {df['date'].max()}")

# ── Step 2: Run gom_scan --daily for 2 dates ──────────────────────────────────
for target in ["2026-08-05", "2026-08-06"]:
    print(f"\n{'='*70}")
    print(f"=== gom_scan --daily --date {target} ===")
    print(f"{'='*70}")

    cmd = [
        sys.executable, str(GOM),
        "--daily",
        "--store", str(LOCAL_CSV),
        "--date", target,
    ]
    r2 = subprocess.run(
        cmd, capture_output=True, encoding="utf-8", errors="replace",
        timeout=120,
        cwd=str(REPO),
    )
    output = r2.stdout + (f"\n[STDERR]: {r2.stderr[:500]}" if r2.stderr.strip() else "")
    print(output[:6000])  # cap to 6K per run
    if r2.returncode != 0:
        print(f"\n!! exit code {r2.returncode}")

# ── Step 3: Targeted output for 2-3 interesting tokens ────────────────────────
print(f"\n{'='*70}")
print("=== Targeted: BANK + TAG + TUT --date 2026-08-06 ===")
print(f"{'='*70}")

for tok in ["BANK", "TAG", "TUT"]:
    print(f"\n--- {tok} ---")
    cmd3 = [
        sys.executable, str(GOM),
        "--daily",
        "--store", str(LOCAL_CSV),
        "--date", "2026-08-06",
        "--token", tok,
    ]
    r3 = subprocess.run(
        cmd3, capture_output=True, encoding="utf-8", errors="replace",
        timeout=60, cwd=str(REPO),
    )
    out3 = r3.stdout + (f"\n[STDERR]: {r3.stderr[:200]}" if r3.stderr.strip() else "")
    print(out3[:3000])
    if r3.returncode != 0:
        print(f"!! exit code {r3.returncode}")

print("\n=== probe done ===")

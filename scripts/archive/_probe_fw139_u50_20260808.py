#!/usr/bin/env python3
# Item 5: NỢ 5 — diff fw139 vs u50_universe.csv + table; NỢ 4 — 2 tables
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# Find u50_universe.csv on VPS or locally
print("=== Search for u50_universe files ===")
out, _ = ssh(f"find {BASE} -name 'u50*' -o -name '*universe*' 2>/dev/null | head -20")
print(out)

print()
# Check local
import subprocess as sp
r = sp.run(["dir", "/b", "/s", "u50*"], capture_output=True, text=True, shell=True,
           cwd="D:\\Data back test\\whale_data")
print("Local u50* files:", r.stdout[:500])
r2 = sp.run(["dir", "/b", "/s", "*universe*"], capture_output=True, text=True, shell=True,
            cwd="D:\\Data back test\\whale_data")
print("Local *universe* files:", r2.stdout[:500])

print()
# Check freshwatch_symbols.txt locally (might exist)
import os
local_paths = [
    "D:\\Data back test\\whale_data\\data\\config\\freshwatch_symbols.txt",
    "D:\\Data back test\\whale_data\\scratch\\freshwatch_symbols.txt",
]
for lp in local_paths:
    if os.path.exists(lp):
        with open(lp, encoding="utf-8") as f:
            lines = f.readlines()
        print(f"Found local: {lp} ({len(lines)} lines)")
        print(f"  First 5: {[l.strip() for l in lines[:5]]}")
    else:
        print(f"Not found: {lp}")

# Check line 324 of run_gom_daily.py (label to update)
print()
print("=== Label location in run_gom_daily.py ===")
out2, _ = ssh(f"grep -n 'fw137\\|fw139\\|fw@\\|fw_count\\|Universe' {BASE}/scripts/run_gom_daily.py | head -10")
print(out2)

#!/usr/bin/env python3
"""Live test: run gom_scan --daily on VPS against 2026-08-06 (last full export date)."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
REPO = Path(__file__).resolve().parent

def ssh(cmd, timeout=180):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

print("=== VPS gom_scan --daily test run (date=2026-08-06) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1",
    timeout=180,
)
print(out[:4000])
if err:
    print("STDERR:", err[:500])

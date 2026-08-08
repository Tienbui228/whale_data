#!/usr/bin/env python3
"""Dry-run run_gom_daily.py on VPS: full scan → format → send Telegram.
Validates entire pipeline before natural 01:25 UTC cron fire."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

print("=== Dry-run: run_gom_daily.py (full pipeline + Telegram) ===")
print("NOTE: This sends a REAL Telegram message for D-1 verification.\n")

out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1",
    timeout=300,
)

print(out[:6000])
if err:
    print("\n--- STDERR ---")
    print(err[:500])

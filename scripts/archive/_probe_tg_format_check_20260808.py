#!/usr/bin/env python3
"""Check Telegram message format after S-MISSING fix."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS,
     f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=300,
)
# Print last portion (stdout of run_gom_daily prints the scan stdout)
# The TG message is sent to Telegram; we reconstruct it from the log + scan output
out = r.stdout or r.stderr
# Find the TG-relevant portion
lines = out.splitlines()
# Look for tg_send indicator in stderr or the scan output sections
print("=== full output (last 50 lines) ===")
print("\n".join(lines[-50:]))

#!/usr/bin/env python3
"""Fix GOM cron timing: 01:00 → 01:25 UTC."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
REPO = Path(__file__).resolve().parent

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# Use sed directly on VPS to change 0 1 * * * run_gom → 25 1 * * * run_gom
# More reliable than file-based replace
print("=== Updating cron via sed ===")
# Read, sed-replace, write back atomically
sed_cmd = (
    f"(crontab -l 2>/dev/null | "
    f"sed 's|^0 1 \\* \\* \\* cd {BASE} && python3 scripts/run_gom_daily.py|"
    f"25 1 * * * cd {BASE} \\&\\& python3 scripts/run_gom_daily.py|') | "
    f"crontab -"
)
out, err = ssh(sed_cmd)
print(f"sed result: '{out}' err='{err}'")

# Verify
final, _ = ssh("crontab -l")
print("\nAll cron entries (relevant):")
for line in (final or "").splitlines():
    if "1 * * *" in line or "GOM" in line:
        print(f"  {line}")

# Confirm GOM line
gom_lines = [l for l in (final or "").splitlines() if "run_gom" in l and not l.startswith("#")]
if gom_lines:
    line = gom_lines[0]
    time_field = line.split()[1]  # minute field
    print(f"\nGOM cron minute field: {line.split()[0]}  (expected: 25)")
    if line.strip().startswith("25 1"):
        print("✓ Cron updated to 01:25 UTC")
    else:
        print(f"⚠ Unexpected time: {line[:40]}")
else:
    print("No GOM run_gom line found!")

#!/usr/bin/env python3
"""Fix GOM cron: move from 01:00 → 01:25 UTC (after export 01:20, before universe 01:30)."""
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

def scp(local, remote, timeout=20):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", str(local), f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", timeout=timeout,
    )
    return r.returncode == 0

# Read current crontab
cur, _ = ssh("crontab -l 2>/dev/null")
print("Current crontab (GOM line):")
for line in (cur or "").splitlines():
    if "run_gom" in line or "GOM daily" in line:
        print(f"  {line}")

# Replace 01:00 GOM line with 01:25
OLD_LINE = (
    f"0 1 * * * cd {BASE} && "
    f"python3 scripts/run_gom_daily.py "
    f">> {BASE}/data/logs/gom_daily.log 2>&1"
)
NEW_LINE = (
    f"25 1 * * * cd {BASE} && "
    f"python3 scripts/run_gom_daily.py "
    f">> {BASE}/data/logs/gom_daily.log 2>&1"
)

if OLD_LINE not in (cur or ""):
    print("WARNING: exact old cron line not found — may have already been changed")
    for l in (cur or "").splitlines():
        if "run_gom" in l:
            print(f"  Current: {l}")

new_cron = (cur or "").replace(OLD_LINE, NEW_LINE)

tmp = REPO / "_tmp_crontab2.txt"
tmp.write_text(new_cron, encoding="utf-8", newline="\n")
scp(tmp, "/tmp/_gom_crontab2.txt")

out, err = ssh("crontab /tmp/_gom_crontab2.txt && echo 'crontab updated'")
print(out or err)
tmp.unlink(missing_ok=True)

# Verify
final, _ = ssh("crontab -l")
print("\nFinal crontab (GOM line):")
for line in (final or "").splitlines():
    if "run_gom" in line or "GOM daily" in line:
        print(f"  {line}")

print("\nTiming: 01:25 UTC — 5 min after export (01:20), 5 min before universe refresh (01:30)")

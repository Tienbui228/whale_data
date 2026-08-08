#!/usr/bin/env python3
# Item 6: case_daily 2-day silence — check scheduler + logs
import sys, subprocess, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Check locally: any case_daily or scheduler logs
print("=== Local: search for case_daily / scheduler ===")
checks = [
    "D:\\Data back test\\whale_data\\data\\logs",
    "D:\\Data back test\\whale_data\\scripts",
]
for d in checks:
    if os.path.exists(d):
        files = [f for f in os.listdir(d) if "case" in f.lower() or "scheduler" in f.lower() or "daily" in f.lower()]
        print(f"{d}: {files[:20]}")

# Check scripts directory for case_daily script
r = subprocess.run(["dir", "/b", "/s", "*case_daily*"], capture_output=True, text=True, shell=True,
                   cwd="D:\\Data back test\\whale_data")
print("*case_daily* files:", r.stdout[:500] or "NONE")

r2 = subprocess.run(["dir", "/b", "/s", "collect_daily*"], capture_output=True, text=True, shell=True,
                    cwd="D:\\Data back test\\whale_data")
print("collect_daily* files:", r2.stdout[:500] or "NONE")

# Check scripts/collect_daily.py modification time
from pathlib import Path
collect_daily = Path("D:\\Data back test\\whale_data\\scripts\\collect_daily.py")
if collect_daily.exists():
    import time
    print(f"\ncollect_daily.py mtime: {time.strftime('%Y-%m-%d %H:%M', time.localtime(collect_daily.stat().st_mtime))}")
    print(f"  size: {collect_daily.stat().st_size} bytes")

# Check if there's a case_daily.log
log_dir = Path("D:\\Data back test\\whale_data\\data\\logs")
if log_dir.exists():
    logs = sorted(log_dir.iterdir())
    print(f"\nLogs in data/logs/: {[l.name for l in logs]}")

# Check VPS for case_daily related things
VPS = "root@5.223.67.21"

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

print()
print("=== VPS: search for case_daily script ===")
out, _ = ssh("find /root/Data_back_test/whale_data -name '*case_daily*' 2>/dev/null")
print(out or "NONE")

print()
print("=== VPS: crontab mention of case ===")
out2, _ = ssh("crontab -l 2>/dev/null | grep -i 'case\\|daily.py\\|append'")
print(out2 or "NONE")

print()
print("=== VPS: daily.log last 20 lines ===")
out3, _ = ssh("tail -20 /root/Data_back_test/whale_data/data/logs/daily.log 2>/dev/null")
print(out3)

print()
print("=== VPS: collect_daily.py last run ===")
out4, _ = ssh("stat -c '%y' /root/Data_back_test/whale_data/scripts/collect_daily.py 2>/dev/null")
print(out4)

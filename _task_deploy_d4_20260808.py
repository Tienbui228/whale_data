#!/usr/bin/env python3
# Deploy D4 updated gom_scan + run_gom_daily to VPS
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if r.returncode != 0:
        print(f"SCP FAIL {local}: {r.stderr[:200]}")
    return r.returncode == 0

ok1 = scp(r"D:\Data back test\whale_data\scripts\gom_scan.py",
          f"{BASE}/scripts/gom_scan.py")
ok2 = scp(r"D:\Data back test\whale_data\scripts\run_gom_daily.py",
          f"{BASE}/scripts/run_gom_daily.py")
ok3 = scp(r"D:\Data back test\whale_data\scripts\fw_loader_utils.py",
          f"{BASE}/scripts/fw_loader_utils.py")
print(f"gom_scan: {'OK' if ok1 else 'FAIL'}")
print(f"run_gom_daily: {'OK' if ok2 else 'FAIL'}")
print(f"fw_loader_utils: {'OK' if ok3 else 'FAIL'}")

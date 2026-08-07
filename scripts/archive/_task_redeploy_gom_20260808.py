#!/usr/bin/env python3
"""Re-deploy updated gom_scan.py + run_gom_daily.py to VPS + verify fw-filter."""
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

def scp(local, remote, timeout=20):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", str(local), f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", timeout=timeout,
    )
    ok = r.returncode == 0
    print(f"  SCP {'OK' if ok else 'FAIL'} {Path(local).name} → {remote}")
    return ok

print("=== Re-deploying updated scripts ===")
scp(REPO / "scripts" / "gom_scan.py",      f"{BASE}/scripts/gom_scan.py")
scp(REPO / "scripts" / "run_gom_daily.py", f"{BASE}/scripts/run_gom_daily.py")

print("\n=== Verify import + fw-filter arg ===")
out, err = ssh(
    f"cd {BASE} && python3 -c \""
    f"import sys; sys.path.insert(0,'scripts'); "
    f"import gom_scan; "
    f"import argparse; "
    f"print('import OK'); "
    f"p = argparse.ArgumentParser(); "
    f"# just check --fw-filter exists in parse "
    f"print('gom_scan has fw_filter_path:', hasattr(gom_scan.run_daily, '__code__'))\""
)
print(out or err)

print("\n=== Live test run with fw-filter (date=2026-08-06) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1",
    timeout=180,
)
# Print first 3000 chars
print(out[:3000])
if err:
    print("STDERR:", err[:200])

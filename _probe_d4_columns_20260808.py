#!/usr/bin/env python3
# D4 verify: push updated gom_scan + run_gom_daily, run --daily 2026-08-07, check STAT lines
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
        print(f"SCP FAIL: {r.stderr[:200]}")
    return r.returncode == 0

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

print("Pushing gom_scan.py + run_gom_daily.py...")
ok1 = scp(r"D:\Data back test\whale_data\scripts\gom_scan.py",
          f"{BASE}/scripts/gom_scan.py")
ok2 = scp(r"D:\Data back test\whale_data\scripts\run_gom_daily.py",
          f"{BASE}/scripts/run_gom_daily.py")
if not (ok1 and ok2):
    sys.exit(1)

print("Running --daily 2026-08-07 (capture stdout only, not TG)...")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily 2026-08-07 2>&1 | grep -A2 'GOM-C'",
    timeout=300,
)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("--- STDERR ---")
    print(err[:600])

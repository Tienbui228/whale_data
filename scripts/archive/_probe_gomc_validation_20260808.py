#!/usr/bin/env python3
# GOM-C data validation outer runner -- SCP inner script to VPS and run it.
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
LOCAL_INNER = r"D:\Data back test\whale_data\_vps_gomc_validation.py"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if r.returncode != 0:
        print(f"SCP FAILED: {r.stderr[:200]}")
    return r.returncode == 0

def ssh(cmd, timeout=420):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

print("Deploying _vps_gomc_validation.py to VPS...")
ok = scp(LOCAL_INNER, f"{BASE}/_vps_gomc_validation.py")
if not ok:
    sys.exit(1)

print("Running on VPS (may take ~2min)...")
out, err = ssh(f"python3 {BASE}/_vps_gomc_validation.py 2>&1", timeout=420)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("\n--- STDERR ---")
    print(err[:1200])

#!/usr/bin/env python3
# Test GOM-C beta: deploy updated gom_scan.py + run_gom_daily.py to VPS, run daily scan.
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

LOCAL_SCRIPTS = r"D:\Data back test\whale_data\scripts"

print("Deploying gom_scan.py + run_gom_daily.py...")
ok1 = scp(f"{LOCAL_SCRIPTS}/gom_scan.py", f"{BASE}/scripts/gom_scan.py")
ok2 = scp(f"{LOCAL_SCRIPTS}/run_gom_daily.py", f"{BASE}/scripts/run_gom_daily.py")
if not (ok1 and ok2):
    sys.exit(1)
print("Deploy OK")

print("\nRunning --daily scan (GOM-C beta test)...")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily "
    f"--store data/export --fw-filter data/config/freshwatch_symbols.txt "
    f"--date 2026-08-07 2>&1",
    timeout=300,
)
print(out[-4000:] if len(out) > 4000 else out)  # last 4k chars
if err and ("Error" in err or "Traceback" in err):
    print("\n--- STDERR ---")
    print(err[:800])

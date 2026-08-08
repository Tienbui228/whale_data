#!/usr/bin/env python3
# D2: GOM-C beta triage pack -- COOKIE / CYS / TST (14d data + condition trace)
# Output to docs/reports/gom_c_triage_20260808.txt on VPS, then copy here.
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if r.returncode != 0: print(f"SCP FAIL: {r.stderr[:200]}")
    return r.returncode == 0

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

LOCAL_INNER = r"D:\Data back test\whale_data\_triage_inner.py"

print("Deploying triage inner script...")
ok = scp(LOCAL_INNER, f"{BASE}/_triage_inner.py")
if not ok:
    sys.exit(1)
out, err = ssh(
    f"python3 {BASE}/_triage_inner.py 2>&1 | tee {BASE}/docs/reports/gom_c_triage_20260808.txt",
    timeout=300,
)
print(out[-6000:] if len(out) > 6000 else out)
if err and ("Error" in err or "Traceback" in err):
    print("--- STDERR ---")
    print(err[:800])

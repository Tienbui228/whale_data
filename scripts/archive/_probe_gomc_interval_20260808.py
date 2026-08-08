#!/usr/bin/env python3
# D1.2: SCP interval check probe to VPS and run it.
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
LOCAL = r"D:\Data back test\whale_data\_probe_interval_inner.py"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if r.returncode != 0: print(f"SCP FAIL: {r.stderr[:200]}")
    return r.returncode == 0

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

scp(LOCAL, f"{BASE}/_probe_interval_inner.py")
out, err = ssh(f"python3 {BASE}/_probe_interval_inner.py 2>&1", timeout=120)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print(err[:600])

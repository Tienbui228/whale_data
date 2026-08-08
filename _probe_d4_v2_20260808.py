#!/usr/bin/env python3
# D4 verify v2: capture tail of gom_scan output to check STAT lines
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily --date 2026-08-07 --store {BASE}/data/export 2>&1 | tail -30",
    timeout=300,
)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("--- STDERR ---")
    print(err[:800])

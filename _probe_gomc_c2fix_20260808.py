#!/usr/bin/env python3
# Verify C2 2×neutral + TST 14d cooldown: expect 8 fires + 1 ⏸ (TST)
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

print("Pushing gom_scan.py + run_gom_daily.py...")
ok1 = scp(r"D:\Data back test\whale_data\scripts\gom_scan.py",
          f"{BASE}/scripts/gom_scan.py")
ok2 = scp(r"D:\Data back test\whale_data\scripts\run_gom_daily.py",
          f"{BASE}/scripts/run_gom_daily.py")
print(f"  gom_scan: {'OK' if ok1 else 'FAIL'}  run_gom_daily: {'OK' if ok2 else 'FAIL'}")

# Quick sanity: verify /4 is in deployed file
out, _ = ssh(f"grep -n 'interval_h / 4' {BASE}/scripts/gom_scan.py | head -5")
print(f"C2 /4 check: {out or '(NOT FOUND — fix not applied!)'}")

print("\nRunning --daily 2026-08-07...")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily --date 2026-08-07 "
    f"--store {BASE}/data/export 2>&1 | grep -E 'GOM-C'",
    timeout=300,
)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("STDERR:", err[:400])

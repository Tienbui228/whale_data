#!/usr/bin/env python3
"""Deploy S-MISSING split fix (gom_scan.py + run_gom_daily.py) + verify output."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
LOCAL = r"D:\Data back test\whale_data"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if r.returncode != 0:
        print(f"SCP FAIL: {r.stderr}")
    else:
        print(f"SCP OK: {local} -> {remote}")

def ssh(cmd, timeout=180):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# === Deploy ===
print("=== Deploying gom_scan.py + run_gom_daily.py ===")
scp(f"{LOCAL}\\scripts\\gom_scan.py", f"{BASE}/scripts/gom_scan.py")
scp(f"{LOCAL}\\scripts\\run_gom_daily.py", f"{BASE}/scripts/run_gom_daily.py")

# === Verify: run gom_scan --daily, check S-MISSING section ===
print("\n=== Verify: gom_scan --daily S-MISSING output ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily --store data/export --date 2026-08-07 "
    f"--fw-filter data/config/freshwatch_symbols.txt 2>&1 | grep -E 'S-MISSING|OPEN|open /' | head -20",
    timeout=180,
)
print(out)
if err:
    print("ERR:", err[:300])

# === Verify: run run_gom_daily.py to check Telegram message format ===
print("\n=== Verify: run_gom_daily.py full output (first 100 lines) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1 | head -40",
    timeout=300,
)
print(out)
if err:
    print("ERR:", err[:300])

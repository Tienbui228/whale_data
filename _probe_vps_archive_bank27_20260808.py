#!/usr/bin/env python3
"""Probe VPS /root/archive/ for BANK 27/07 vol — compare with current CSV.
READ-ONLY: no writes to any file.
"""
import sys, subprocess, os
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"
SSH_KEY = None  # use default (~/.ssh/id_rsa or agent)

def ssh(cmd, timeout=20):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    if SSH_KEY:
        args += ["-i", SSH_KEY]
    args += [VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

print("=== VPS ARCHIVE: BANK 27/07 vol ===")
print()

# 1. Check if archive dir exists
out, err, rc = ssh("ls -la /root/archive/ 2>/dev/null | head -20")
if rc != 0:
    print(f"  ERROR connecting to VPS: {err}")
    print("  Cannot verify VPS archive. Manual SSH required:")
    print(f"  ssh {VPS} 'ls -la /root/archive/ | grep freshwatch'")
    print(f"  ssh {VPS} \"grep 'BANKUSDT.*2026-07-27\\|2026-07-27.*BANKUSDT' /root/archive/freshwatch_daily_2026-07.csv\"")
    sys.exit(0)

print("  /root/archive/ contents:")
for ln in out.splitlines():
    print(f"    {ln}")

# 2. Check freshwatch CSV in archive
out2, err2, rc2 = ssh("ls -la /root/archive/freshwatch_daily_2026-07.csv /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv 2>/dev/null")
print()
print("  CSV file timestamps (VPS):")
for ln in out2.splitlines():
    print(f"    {ln}")

# 3. BANK 27/07 from ARCHIVE CSV
out3, err3, rc3 = ssh(
    "awk -F, 'NR==1{print;next} ($0 ~ /BANKUSDT/ || $0 ~ /^BANK,/) && $0 ~ /2026-07-27/{print}' "
    "/root/archive/freshwatch_daily_2026-07.csv 2>/dev/null | head -5"
)
print()
print("  BANK 27/07 from ARCHIVE CSV:")
if out3:
    for ln in out3.splitlines():
        print(f"    {ln}")
else:
    print(f"  (empty or file missing: {err3})")

# 4. BANK 27/07 from CURRENT EXPORT CSV
out4, err4, rc4 = ssh(
    "awk -F, 'NR==1{print;next} ($0 ~ /BANKUSDT/ || $0 ~ /^BANK,/) && $0 ~ /2026-07-27/{print}' "
    "/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv 2>/dev/null | head -5"
)
print()
print("  BANK 27/07 from CURRENT VPS export CSV:")
if out4:
    for ln in out4.splitlines():
        print(f"    {ln}")
else:
    print(f"  (empty: {err4})")

# 5. Check VPS export log for 27/07
out5, err5, rc5 = ssh(
    "grep -i '2026-07-27\\|07-27' /root/Data_back_test/whale_data/data/export/export.log 2>/dev/null | tail -20"
)
print()
print("  VPS export.log entries for 07-27:")
if out5:
    for ln in out5.splitlines():
        print(f"    {ln}")
else:
    print(f"  (no log or no match: {err5})")

# 6. Check structlog entries in VPS logs
out6, err6, rc6 = ssh(
    "find /root/Data_back_test/whale_data -name '*.log' -newer /root/archive 2>/dev/null | head -10"
)
print()
print("  Log files newer than /root/archive:")
if out6:
    for ln in out6.splitlines():
        print(f"    {ln}")
else:
    print(f"  (none or error: {err6})")

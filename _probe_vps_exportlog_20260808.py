#!/usr/bin/env python3
"""Read VPS freshwatch_export.log for 27/07 entries + full timeline.
READ-ONLY.
"""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=30):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

LOG = "/root/Data_back_test/whale_data/data/logs/freshwatch_export.log"

print("=== VPS freshwatch_export.log ===")
print()

# 1. File size and tail
out, err, rc = ssh(f"wc -l {LOG} && tail -5 {LOG}")
print(f"  Log file: {LOG}")
print(f"  {out or err}")
print()

# 2. Entries for 2026-07-27
out2, err2, rc2 = ssh(f"grep '2026-07-27\\|07-27' {LOG} | head -20")
print(f"  Entries mentioning 07-27:")
if out2:
    for ln in out2.splitlines():
        print(f"    {ln}")
else:
    print(f"    (none: {err2})")
print()

# 3. First write of freshwatch_daily_2026-07 (creation)
out3, err3, rc3 = ssh(f"grep -n 'freshwatch_daily_2026-07\\|2026-07\\|month_written\\|new_rows' {LOG} | head -30")
print(f"  CSV creation / new_rows entries:")
if out3:
    for ln in out3.splitlines():
        print(f"    {ln}")
else:
    print(f"    (none: {err3})")
print()

# 4. Timestamps of force-regen entries
out4, err4, rc4 = ssh(f"grep -i 'force\\|regen\\|strip\\|rebuild' {LOG} | head -20")
print(f"  Force-regen log entries:")
if out4:
    for ln in out4.splitlines():
        print(f"    {ln}")
else:
    print(f"    (none: {err4})")
print()

# 5. Full July export timeline (date_written entries)
out5, err5, rc5 = ssh(f"grep 'date\\|export_date\\|written\\|rows' {LOG} | grep -i '07-2[4-9]\\|07-3\\|export_month_written' | head -30")
print(f"  Date-specific log entries 07-24→07-31:")
if out5:
    for ln in out5.splitlines():
        print(f"    {ln}")
else:
    print(f"    (none: {err5})")
print()

# 6. Early July log (when was first write?)
out6, err6, rc6 = ssh(f"head -30 {LOG}")
print(f"  First 30 lines of export log (oldest entries):")
if out6:
    for ln in out6.splitlines():
        print(f"    {ln}")
else:
    print(f"    ({err6})")

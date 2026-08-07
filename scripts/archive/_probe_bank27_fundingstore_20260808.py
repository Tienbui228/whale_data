#!/usr/bin/env python3
"""Check funding_8h raw store on VPS for BANK 27/07.
Xác nhận: store hiện tại có đủ 6 intervals chưa? → phân xử case (a) vs (b).
Also check 26/07 and 05/08 trio.
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

BASE = "/root/Data_back_test/whale_data"
STORE = f"{BASE}/data/raw/funding_8h"

print("=" * 68)
print("A — Structure of funding_8h store")
print("=" * 68)
out, err, rc = ssh(f"ls -la {STORE}/ 2>/dev/null | head -20")
for ln in (out or err).splitlines():
    print(f"  {ln}")

print()
print("=" * 68)
print("B — BANKUSDT 27/07: rows in funding_8h store (count + values)")
print("=" * 68)
# Check if store is partitioned by date or symbol
out2, err2, rc2 = ssh(
    f"find {STORE} -name '*BANK*' -o -name '*2026-07-27*' 2>/dev/null | head -20"
)
if out2:
    for ln in out2.splitlines():
        print(f"  {ln}")
else:
    print(f"  (no BANK/27-07 files: {err2})")

print()
# Try parquet read if Python3 + pandas available
out3, err3, rc3 = ssh(
    "python3 -c \""
    "import os, glob; "
    "store='/root/Data_back_test/whale_data/data/raw/funding_8h'; "
    "files=glob.glob(store+'/**', recursive=True); "
    "print('total_files:', len([f for f in files if os.path.isfile(f)])); "
    "[print(f) for f in sorted(files)[:30] if os.path.isfile(f)]"
    "\""
)
if out3:
    print("  Store files:")
    for ln in out3.splitlines():
        print(f"    {ln}")
else:
    print(f"  (python3 error: {err3[:200]})")

print()
print("=" * 68)
print("C — funding.log: entries for BANKUSDT 2026-07-27")
print("=" * 68)
FLOG = f"{BASE}/data/logs/funding.log"
out4, err4, rc4 = ssh(f"grep -i 'BANK\\|27\\|2026-07-27' {FLOG} 2>/dev/null | head -20")
if out4:
    for ln in out4.splitlines():
        print(f"  {ln}")
else:
    print(f"  (no match or no file: {err4})")

print()
print("=" * 68)
print("D — funding_intervals.json: structure peek")
print("=" * 68)
FJ = f"{BASE}/data/config/funding_intervals.json"
out5, err5, rc5 = ssh(f"python3 -c \""
    "import json; "
    "d=json.load(open('/root/Data_back_test/whale_data/data/config/funding_intervals.json')); "
    "keys=list(d.keys()) if isinstance(d,dict) else type(d).__name__; "
    "print('type:', type(d).__name__); "
    "print('keys[:5]:', list(d.keys())[:5] if isinstance(d,dict) else 'N/A'); "
    "# if list of records:"
    "first=d[0] if isinstance(d,list) else next(iter(d.values())); "
    "print('sample:', str(first)[:200])"
    "\"")
if out5:
    for ln in out5.splitlines():
        print(f"  {ln}")
else:
    print(f"  (error: {err5[:300]})")

print()
print("=" * 68)
print("E — funding_intervals.json: BANK entries for 2026-07-27")
print("=" * 68)
out6, err6, rc6 = ssh(
    "python3 -c \""
    "import json; "
    "d=json.load(open('/root/Data_back_test/whale_data/data/config/funding_intervals.json')); "
    "# Count total and find BANK 27/07"
    "total=len(d) if isinstance(d,list) else sum(len(v) for v in d.values()); "
    "print('total_intervals:', total); "
    "if isinstance(d,list):"
    "  bank27=[x for x in d if 'BANK' in str(x.get('symbol','')) and '2026-07-27' in str(x.get('date',''))];"
    "  print('BANK 27/07 entries:', len(bank27));"
    "  [print(x) for x in bank27[:10]]"
    "elif isinstance(d,dict):"
    "  for k,v in d.items():"
    "    if 'BANK' in k:"
    "      print('key:', k, 'entries:', len(v) if hasattr(v,'__len__') else v)"
    "\""
)
if out6:
    for ln in out6.splitlines():
        print(f"  {ln}")
else:
    print(f"  (error: {err6[:300]})")

print()
print("=" * 68)
print("F — First entry in funding.log (when collector started)")
print("=" * 68)
out7, err7, rc7 = ssh(f"head -5 {FLOG} 2>/dev/null")
if out7:
    for ln in out7.splitlines():
        print(f"  {ln}")
else:
    print(f"  (no file: {err7})")

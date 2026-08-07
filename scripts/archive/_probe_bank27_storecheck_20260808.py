#!/usr/bin/env python3
"""Phân xử mâu thuẫn 2.1 vs 2.2: BANK 27/07 fn=1 origin.
Hai câu hỏi:
  Q1: Store VPS hôm nay có bao nhiêu funding_8h records cho BANKUSDT 2026-07-27?
  Q2: Export log dòng chính xác timestamp cho 27/07 là gì?
READ-ONLY.
"""
import sys, subprocess, json

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
LOG  = f"{BASE}/data/logs/freshwatch_export.log"

print("=" * 68)
print("Q1a — Export log: dòng chính xác liên quan 27/07 (kèm timestamp)")
print("=" * 68)
out, err, rc = ssh(f"grep -n '2026-07-27\\|07-27' {LOG}")
if out:
    for ln in out.splitlines():
        print(f"  {ln}")
else:
    print(f"  (no match: {err})")

print()
print("=" * 68)
print("Q1b — Export log: full block cho export_date 2026-07-27")
print("      (grep từ dòng 'export_date' đến newline trước dòng tiếp theo)")
print("=" * 68)
out2, err2, rc2 = ssh(
    f"grep -A5 'export_date.*2026-07-27\\|date.*2026-07-27' {LOG} | head -30"
)
if out2:
    for ln in out2.splitlines():
        print(f"  {ln}")
else:
    print(f"  (no match: {err2})")

print()
print("=" * 68)
print("Q2 — VPS local funding store: db / parquet / sqlite / json for BANKUSDT")
print("=" * 68)

# Check if there's a local DB or store for funding rates
out3, err3, rc3 = ssh(
    f"find {BASE}/data -name '*.db' -o -name '*.sqlite' -o -name 'funding*' "
    f"-o -name '*rate*' 2>/dev/null | head -20"
)
if out3:
    for ln in out3.splitlines():
        print(f"  {ln}")
else:
    print(f"  (none: {err3})")

print()
print("=" * 68)
print("Q2b — Xem cấu trúc data/ trên VPS")
print("=" * 68)
out4, err4, rc4 = ssh(f"ls -la {BASE}/data/ 2>/dev/null")
if out4:
    for ln in out4.splitlines():
        print(f"  {ln}")
else:
    print(f"  ({err4})")

print()
print("=" * 68)
print("Q3 — Fapi funding rate BANKUSDT 27/07: count trực tiếp")
print("     (Binance fundingRate historical — available nếu Binance giữ lịch sử)")
print("=" * 68)

# Query Binance fapi for BANKUSDT funding rates on 2026-07-27
# startTime = 2026-07-27 00:00:00 UTC = 1753574400000
# endTime   = 2026-07-27 23:59:59 UTC = 1753660799000
fapi_cmd = (
    "python3 -c \""
    "import urllib.request, json; "
    "url='https://fapi.binance.com/fapi/v1/fundingRate?"
    "symbol=BANKUSDT&startTime=1753574400000&endTime=1753660799000&limit=10'; "
    "resp=urllib.request.urlopen(url,timeout=15); "
    "data=json.loads(resp.read()); "
    "print(f'count={len(data)}'); "
    "[print(f'  {d[\\\"fundingTime\\\"]//1000} rate={d[\\\"fundingRate\\\"]}') for d in data]"
    "\""
)
out5, err5, rc5 = ssh(fapi_cmd, timeout=25)
if out5:
    for ln in out5.splitlines():
        print(f"  {ln}")
else:
    print(f"  (error: {err5[:200]})")

print()
print("=" * 68)
print("Q4 — Fapi klines BANKUSDT 27/07 1h: count rows (confirms full-day vol)")
print("=" * 68)

klines_cmd = (
    "python3 -c \""
    "import urllib.request, json; "
    "url='https://fapi.binance.com/fapi/v1/klines?"
    "symbol=BANKUSDT&interval=1h"
    "&startTime=1753574400000&endTime=1753660799000&limit=30'; "
    "resp=urllib.request.urlopen(url,timeout=15); "
    "data=json.loads(resp.read()); "
    "vol=sum(float(r[7]) for r in data); "
    "print(f'rows={len(data)} total_vol_quote={vol:.0f}'); "
    "[print(f'  {r[0]//1000} v={r[7]:.0f}') for r in data[:6]]"
    "\""
)
out6, err6, rc6 = ssh(klines_cmd, timeout=25)
if out6:
    for ln in out6.splitlines():
        print(f"  {ln}")
    if len(out6.splitlines()) < 5:
        print(f"  (stderr: {err6[:100]})")
else:
    print(f"  (error: {err6[:200]})")

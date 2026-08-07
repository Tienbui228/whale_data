#!/usr/bin/env python3
"""Đọc export_freshwatch_daily.py trên VPS: tìm cách tính fn (funding_n).
Cũng kiểm tra store BANK 27/07 vs fapi timestamps trực tiếp.
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
        r = subprocess.run(args, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

BASE = "/root/Data_back_test/whale_data"
SCRIPT = f"{BASE}/scripts/export_freshwatch_daily.py"

print("=== A: Locate funding_n / fn calculation in exporter ===")
out, err, rc = ssh(f"grep -n 'funding_n\\|fn\\|settle\\|count\\|interval' {SCRIPT} | head -40")
for ln in out.splitlines():
    print(f"  {ln}")

print()
print("=== B: Lines around 'funding' keyword ===")
out2, err2, rc2 = ssh(f"grep -n 'funding' {SCRIPT} | head -30")
for ln in out2.splitlines():
    print(f"  {ln}")

print()
print("=== C: Exact fn calculation (context) ===")
# Get the function or block that computes fn
out3, err3, rc3 = ssh(f"grep -n 'funding_n\\|fn =' {SCRIPT} | head -20")
for ln in out3.splitlines():
    line_num = ln.split(":")[0].strip()
    if line_num.isdigit():
        n = int(line_num)
        lo = max(1, n - 3)
        hi = n + 5
        ctx, _, _ = ssh(f"sed -n '{lo},{hi}p' {SCRIPT}")
        print(f"  --- line {line_num} ---")
        for cl in ctx.splitlines():
            print(f"    {cl}")

print()
print("=== D: How does exporter query funding store? ===")
# Look for parquet read or store access patterns
out4, err4, rc4 = ssh(f"grep -n 'parquet\\|read_parquet\\|funding_8h\\|load_funding\\|get_funding' {SCRIPT} | head -20")
for ln in out4.splitlines():
    print(f"  {ln}")

print()
print("=== E: BANK 27/07 — store timestamps vs fapi (debug backfill) ===")
debug_py = (
    "import pandas as pd, urllib.request, json\n"
    "from datetime import datetime, timezone\n"
    "\n"
    "df = pd.read_parquet('/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-07/part-0.parquet')\n"
    "# 2026-07-27 range\n"
    "s = int(datetime(2026,7,27,tzinfo=timezone.utc).timestamp() * 1000)\n"
    "e = s + 86400000 - 1\n"
    "sub = df[(df['symbol']=='BANKUSDT') & (df['as_of_ts_ms']>=s) & (df['as_of_ts_ms']<=e)]\n"
    "print('Store as_of_ts_ms for BANK 27/07 (' + str(len(sub)) + ' rows):')\n"
    "[print('  ' + str(t) + ' = ' + datetime.utcfromtimestamp(t/1000).strftime('%H:%M UTC')) for t in sorted(sub['as_of_ts_ms'].unique())]\n"
    "\n"
    "# fapi fundingRate for BANK 27/07\n"
    "url = f'https://fapi.binance.com/fapi/v1/fundingRate?symbol=BANKUSDT&startTime={s}&endTime={e}&limit=20'\n"
    "resp = urllib.request.urlopen(url, timeout=15)\n"
    "data = json.loads(resp.read())\n"
    "print('fapi fundingTime (' + str(len(data)) + ' records):')\n"
    "[print('  ' + str(r['fundingTime']) + ' = ' + datetime.utcfromtimestamp(r['fundingTime']/1000).strftime('%H:%M UTC') + ' rate=' + r['fundingRate']) for r in data]\n"
    "\n"
    "# Compare\n"
    "store_ts = set(sub['as_of_ts_ms'].unique())\n"
    "fapi_ts = set(r['fundingTime'] for r in data)\n"
    "print('In fapi but NOT in store:', sorted(fapi_ts - store_ts))\n"
    "print('In store but NOT in fapi:', sorted(store_ts - fapi_ts))\n"
)

write_out, _, _ = ssh("cat > /tmp/debug_fn.py << 'XENDF'\n" + debug_py + "\nXENDF")
out5, err5, rc5 = ssh("python3 /tmp/debug_fn.py 2>/dev/null", timeout=30)
for ln in out5.splitlines():
    print(f"  {ln}")
if err5 and rc5 != 0:
    print(f"  err: {err5[:200]}")

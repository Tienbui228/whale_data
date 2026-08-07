#!/usr/bin/env python3
"""Probe BR 24-26/07 missing from CSV: check native_1d store on VPS.
READ-ONLY.
"""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

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

br_script = """
import pandas as pd, glob, os
from datetime import datetime, timezone

RAW = '/root/Data_back_test/whale_data/data/raw'

# Check native_1d parquet for BR 24-26/07
for d in ['2026-07-24', '2026-07-25', '2026-07-26']:
    pattern = RAW + '/*/date=' + d + '/*.parquet'
    files = glob.glob(pattern)
    br_found = False
    for f in files:
        try:
            df = pd.read_parquet(f)
            sym_col = next((c for c in df.columns if c.lower() in ('symbol','sym')), None)
            if sym_col:
                if 'BRUSDT' in df[sym_col].values or 'BR' in df[sym_col].values:
                    print('  Found BR in: ' + f + ' (' + str(len(df)) + ' rows)')
                    br_found = True
        except:
            pass
    if not br_found:
        print('  BR NOT found in any store for ' + d)
        # List what stores have that date
        stores = set(f.split('/date=')[0].split('/')[-1] for f in files if '/date=' in f)
        print('    Available stores: ' + str(list(stores)[:10]))

# Check: is BRUSDT in the CSV for dates before and after the gap?
df_csv = pd.read_csv('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv', low_memory=False)
br_csv = df_csv[df_csv['symbol'] == 'BRUSDT'].sort_values('date')
print()
print('BRUSDT dates in CSV (all): ' + str(sorted(br_csv['date'].tolist())))
"""

ssh("cat > /tmp/probe_br.py << 'BREOF'\n" + br_script + "\nBREOF")
print("=== BR 24-26/07: store check ===")
out, err, rc = ssh("python3 /tmp/probe_br.py 2>&1")
print(out or err)

# Also check the regen log for BR specifically
print("\n=== Export log for BR 24-26/07 (last regen run) ===")
LOG = BASE + "/data/logs/freshwatch_export.log"
out2, err2, rc2 = ssh(f"grep 'BRUSDT\\|BR' {LOG} | tail -20")
print(out2 or err2 or "(no BR entries in export log)")

# Check if BR klines exist for those dates
print("\n=== BR klines availability (fapi check) ===")
fapi_br = """
import urllib.request, json
from datetime import datetime, timezone

for d in ['2026-07-24', '2026-07-25', '2026-07-26', '2026-07-27']:
    dt = datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    s = int(dt.timestamp() * 1000)
    e = s + 86400000 - 1
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol=BRUSDT&interval=1d&startTime={s}&endTime={e}&limit=5'
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())
        if data:
            r = data[0]
            print(d + ': vol_quote=' + str(r[7]) + ' open=' + str(r[1]))
        else:
            print(d + ': NO klines data')
    except Exception as ex:
        print(d + ': ERROR ' + str(ex))
"""
ssh("cat > /tmp/probe_br_fapi.py << 'BFEOF'\n" + fapi_br + "\nBFEOF")
out3, err3, rc3 = ssh("python3 /tmp/probe_br_fapi.py 2>&1", timeout=30)
print(out3 or err3)

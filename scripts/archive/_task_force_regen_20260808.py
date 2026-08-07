#!/usr/bin/env python3
"""Verify post-regen results. Chạy trên VPS via heredoc."""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

verify_script = """
import pandas as pd

base = '/root/Data_back_test/whale_data/data/export'
checks_jul = [
    ('BANKUSDT', '2026-07-26'), ('BANKUSDT', '2026-07-27'),
    ('BRUSDT', '2026-07-24'), ('BRUSDT', '2026-07-25'), ('BRUSDT', '2026-07-26'),
    ('TAGUSDT', '2026-07-27'),
]
checks_aug = [
    ('BANKUSDT', '2026-08-05'), ('IDOLUSDT', '2026-08-05'), ('XPINUSDT', '2026-08-05'),
]

for fpath, pairs in [
    (base + '/freshwatch_daily_2026-07.csv', checks_jul),
    (base + '/freshwatch_daily_2026-08.csv', checks_aug),
]:
    try:
        df = pd.read_csv(fpath, low_memory=False)
    except Exception as e:
        print('ERROR: ' + fpath + ' ' + str(e))
        continue
    for sym, d in pairs:
        row = df[(df['symbol'] == sym) & (df['date'].astype(str) == d)]
        if len(row) == 0:
            print('  MISSING: ' + sym + ' ' + d)
        else:
            fn  = row['funding_n'].iloc[0]
            vol = row['vol_quote'].iloc[0]
            ok  = row['data_ok'].iloc[0] if 'data_ok' in df.columns else '?'
            print('  ' + sym + ' ' + d + ': fn=' + str(fn) + ' vol=' + str(int(vol)) + ' data_ok=' + str(ok))
"""

bank_script = """
import json, pandas as pd
from datetime import datetime, timezone

iv = json.load(open('/root/Data_back_test/whale_data/data/config/funding_intervals.json'))
print('Config interval_h: BANKUSDT=' + str(iv.get('BANKUSDT')) + ' TAGUSDT=' + str(iv.get('TAGUSDT')))

df = pd.read_parquet('/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-07/part-0.parquet')
bank = df[df['symbol'] == 'BANKUSDT']
print('BANKUSDT Jul store total rows: ' + str(len(bank)))
for d in ['2026-07-01', '2026-07-20', '2026-07-26', '2026-07-27']:
    dt = datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    s = int(dt.timestamp() * 1000)
    sub = bank[(bank['as_of_ts_ms'] >= s) & (bank['as_of_ts_ms'] < s + 86400000)]
    ut = len(sub['as_of_ts_ms'].unique())
    print('  ' + d + ': ' + str(ut) + ' unique_ts in store -> fn would be ' + str(ut))
"""

# Write scripts to VPS and run
ssh("cat > /tmp/v_regen.py << 'VEOF'\n" + verify_script + "\nVEOF")
ssh("cat > /tmp/v_bank.py << 'BEOF'\n" + bank_script + "\nBEOF")

print("=== VERIFY: fn + vol post-regen ===")
out, err, rc = ssh("python3 /tmp/v_regen.py 2>&1")
print(out or err)

print("\n=== BANKUSDT: interval config vs actual store ===")
out2, err2, rc2 = ssh("python3 /tmp/v_bank.py 2>&1")
print(out2 or err2)

# Step 3: full fn<expected audit, but check against ACTUAL intervals (not from config)
# Because config says BANK=1h (1h interval) but historical data was 4h
# Filter only rows where data_ok=True (exclude data_bad) and check if fn=1 specifically
print("\n=== CRITICAL: rows with fn=1 in CSV (potential born-wrong) ===")
fn1_script = """
import pandas as pd

rows_fn1 = []
for fpath in [
    '/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv',
    '/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv',
]:
    try:
        df = pd.read_csv(fpath, low_memory=False)
    except:
        continue
    ok_col = 'data_ok' if 'data_ok' in df.columns else None
    sub = df[df['funding_n'] == 1]
    if ok_col:
        sub = sub[sub[ok_col] == True]
    for _, r in sub.iterrows():
        rows_fn1.append((r['symbol'], str(r['date']), r['vol_quote']))

print('fn=1 AND data_ok=True rows: ' + str(len(rows_fn1)))
for sym, d, vol in sorted(rows_fn1, key=lambda x: x[1]):
    print('  ' + sym + ' ' + d + ' vol=' + str(int(vol)))
"""
ssh("cat > /tmp/v_fn1.py << 'FN1EOF'\n" + fn1_script + "\nFN1EOF")
out3, err3, rc3 = ssh("python3 /tmp/v_fn1.py 2>&1")
print(out3 or err3)

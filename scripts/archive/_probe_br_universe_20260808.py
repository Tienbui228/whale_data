#!/usr/bin/env python3
"""Quick check: BR in universe snapshot + 1d stores for 07-24 to 07-26. READ-ONLY."""
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

chk = """
import pandas as pd, os, glob

RAW = '/root/Data_back_test/whale_data/data/raw'

for d in ['2026-07-24', '2026-07-25', '2026-07-26']:
    print('--- ' + d + ' ---')
    # Universe snapshot
    up = RAW + '/universe/date=' + d + '/snapshot.parquet'
    if os.path.exists(up):
        udf = pd.read_parquet(up)
        sym_col = next((c for c in udf.columns if c.lower() in ('symbol','sym')), None)
        if sym_col:
            br_in = 'BRUSDT' in udf[sym_col].values
            print('  universe: ' + str(len(udf)) + ' rows, BRUSDT=' + str(br_in))

    # 1d stores: check if BR present
    for store in ['oi_hist_1d', 'taker_ratio_1d', 'top_acct_1d', 'top_pos_1d', 'retail_global_1d']:
        p = RAW + '/' + store + '/date=' + d
        if not os.path.exists(p):
            print('  ' + store + ': NO PARTITION')
            continue
        files = glob.glob(p + '/*.parquet')
        if not files:
            print('  ' + store + ': NO FILES')
            continue
        df = pd.read_parquet(files[0])
        sym_col = next((c for c in df.columns if c.lower() in ('symbol','sym')), None)
        if sym_col:
            br_in = 'BRUSDT' in df[sym_col].values or 'BR' in df[sym_col].values
            n = len(df)
            print('  ' + store + ': ' + str(n) + ' rows, BRUSDT=' + str(br_in))
        else:
            print('  ' + store + ': ' + str(len(df)) + ' rows (no sym col: ' + str(list(df.columns)[:3]) + ')')

    # klines_1h: count BR rows
    p1h = RAW + '/klines_1h/date=' + d
    if os.path.exists(p1h):
        files = glob.glob(p1h + '/*.parquet')
        if files:
            df1h = pd.read_parquet(files[0])
            sym_col = next((c for c in df1h.columns if c.lower() in ('symbol','sym')), None)
            if sym_col:
                br_rows = len(df1h[df1h[sym_col] == 'BRUSDT'])
                print('  klines_1h: BRUSDT=' + str(br_rows) + ' rows (total=' + str(len(df1h)) + ')')
"""
ssh("cat > /tmp/br_univ.py << 'BEOF'\n" + chk + "\nBEOF")
out, err, rc = ssh("python3 /tmp/br_univ.py 2>&1")
print(out or err)

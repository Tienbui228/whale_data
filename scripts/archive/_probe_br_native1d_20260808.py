#!/usr/bin/env python3
"""Check native_1d store for BR 24-26/07. Xác định có thể backfill không."""
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

native_script = """
import os, glob, pandas as pd

RAW = '/root/Data_back_test/whale_data/data/raw'

# List all store types in raw/
stores = [d for d in os.listdir(RAW) if os.path.isdir(os.path.join(RAW, d))]
print('All stores in raw/: ' + str(sorted(stores)))

# Check which stores have date=2026-07-24 partitions
print()
print('Stores with date=2026-07-24:')
for s in sorted(stores):
    p = os.path.join(RAW, s, 'date=2026-07-24')
    if os.path.exists(p):
        files = glob.glob(p + '/*.parquet')
        print('  ' + s + ': ' + str(len(files)) + ' parquet files')

# Check native_1d specifically (or similar)
print()
for candidate in ['native_1d', 'klines_1d', 'futures_klines_1d', 'perp_klines_1d']:
    p = os.path.join(RAW, candidate)
    if os.path.exists(p):
        print('Found store: ' + candidate)
        dates = sorted([d.replace('date=','') for d in os.listdir(p) if d.startswith('date=')])
        print('  dates: ' + str(dates[:5]) + '...' + str(dates[-3:]) if dates else '  (no date partitions)')
        # Check for BR
        for d in ['2026-07-24', '2026-07-25', '2026-07-26', '2026-07-27']:
            dp = os.path.join(p, 'date='+d)
            if os.path.exists(dp):
                files = glob.glob(dp+'/*.parquet')
                if files:
                    df = pd.read_parquet(files[0])
                    sym_col = next((c for c in df.columns if c.lower() in ('symbol','sym')), None)
                    br_in = 'BRUSDT' in df[sym_col].values if sym_col else '?'
                    print('  ' + d + ': ' + str(len(df)) + ' rows, BRUSDT=' + str(br_in))
                else:
                    print('  ' + d + ': no parquet')
            else:
                print('  ' + d + ': no partition')
"""

ssh("cat > /tmp/probe_native.py << 'NNEOF'\n" + native_script + "\nNNEOF")
out, err, rc = ssh("python3 /tmp/probe_native.py 2>&1")
print(out or err)

# Also check what exporter reads (from src=native_1d) — look in export script
print()
print("=== Export script: native_1d read path ===")
out2, err2, rc2 = ssh(
    f"grep -n 'native_1d\\|_build_native\\|native.*parquet\\|klines_1d' "
    f"{BASE}/scripts/export_freshwatch_daily.py | head -20"
)
print(out2 or err2)

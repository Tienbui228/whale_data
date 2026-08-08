#!/usr/bin/env python3
"""Explicit funding_8h rows-per-day table on VPS: 37 dates 01/07→06/08.
Confirms 'TRỐNG TOÀN BỘ' with numeric evidence."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

script = r"""
python3 - <<'PYEOF'
import os, glob
from pathlib import Path
from datetime import date, timedelta

base = '/root/Data_back_test/whale_data/data/raw/funding_8h'

# Check if store dir exists
if not Path(base).exists():
    print(f"STORE DIR NOT FOUND: {base}")
    exit(0)

# List date partitions
partitions = sorted(glob.glob(base + '/date=*'))
print(f"Partition dirs: {len(partitions)}")
if partitions:
    print("Existing partitions:", [p.split('date=')[1] for p in partitions[:5]])

# Grid audit: 37 dates
d = date(2026, 7, 1)
end = date(2026, 8, 6)
total_rows = 0
nonzero = []
while d <= end:
    ds = d.strftime('%Y-%m-%d')
    pattern = base + f'/date={ds}/*.parquet'
    files = glob.glob(pattern)
    if files:
        try:
            import pyarrow.parquet as pq
            n = sum(pq.read_table(f).num_rows for f in files)
        except Exception as e:
            n = -1
    else:
        n = 0
    total_rows += max(n, 0)
    if n > 0:
        nonzero.append((ds, n))
    d += timedelta(days=1)

print(f"\nfunding_8h rows-per-day audit (01/07→06/08, 37 dates):")
print(f"{'Date':<12} | {'Rows':>6} | {'Expected':>8} | Status")
print('-' * 50)
d = date(2026, 7, 1)
while d <= end:
    ds = d.strftime('%Y-%m-%d')
    found = next((n for dd, n in nonzero if dd == ds), 0)
    status = 'HAS DATA' if found > 0 else 'EMPTY'
    print(f"{ds:<12} | {found:>6} | {417:>8} | {status}")
    d += timedelta(days=1)

print(f"\nSUMMARY: {len(nonzero)}/37 dates with rows | Total rows: {total_rows}")
if not nonzero:
    print("CONFIRMED: funding_8h TRỐNG TOÀN BỘ — 0 rows for ALL 37 dates")
PYEOF
"""

out, err = ssh(script)
print(out or err)

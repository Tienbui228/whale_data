#!/usr/bin/env python3
"""Trace BR OI timestamp + whale_collector OI aggregation method."""
import csv, pathlib, json, os
from datetime import datetime, timezone

WHALE_DIR = pathlib.Path('/root/Data_back_test/whale_data')
BOT_DIR = pathlib.Path('/root/binance_bot_signals')

# 1. Check pending_2026-07-29.csv for BRUSDT row
pending_f = BOT_DIR / 'data' / 'pending' / 'pending_2026-07-29.csv'
if pending_f.exists():
    rows = list(csv.DictReader(pending_f.open(encoding='utf-8')))
    br = [r for r in rows if r.get('symbol','').upper() in ('BRUSDT','BR')]
    print(f"=== pending_2026-07-29.csv: {len(rows)} total rows, {len(br)} BRUSDT ===")
    for r in br[:2]:
        print(f"  {r}")
else:
    print("pending_2026-07-29.csv not found in bot dir")

# 2. Check if whale_data has pending/raw for BRUSDT
whale_pending = WHALE_DIR / 'data' / 'pending'
if whale_pending.exists():
    for f in sorted(whale_pending.glob('*2026-07-2[789]*'))[:5]:
        mtime = datetime.fromtimestamp(os.path.getmtime(str(f)), tz=timezone.utc)
        print(f"\n  {f.name} mtime={mtime.strftime('%Y-%m-%d %H:%M UTC')}")
        rows = list(csv.DictReader(f.open(encoding='utf-8')))
        br = [r for r in rows if r.get('symbol','').upper() == 'BRUSDT']
        for r in br[:1]:
            print(f"    BRUSDT: {r}")

# 3. Check the whale_collector/storage/reader.py for oi_usd field derivation
reader = WHALE_DIR / 'whale_collector' / 'storage' / 'reader.py'
if reader.exists():
    lines = reader.read_text(errors='replace').splitlines()
    print("\n=== reader.py: oi_usd / openInterest references ===")
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in ['oi_usd', 'open_interest', 'sumOpenInterest', 'oi_hist']):
            print(f"  line {i}: {line.rstrip()[:120]}")

# 4. Check what time the export CSV for Jul 29 was generated
export_f = WHALE_DIR / 'data' / 'export' / 'freshwatch_daily_2026-07.csv'
mtime = datetime.fromtimestamp(os.path.getmtime(str(export_f)), tz=timezone.utc)
print(f"\n=== export CSV mtime: {mtime.strftime('%Y-%m-%d %H:%M:%S UTC')} ===")

# 5. Check whale_collector binance reader for OI hist period
bc_dir = WHALE_DIR / 'whale_collector' / 'binance'
for pyf in sorted(bc_dir.glob('*.py')):
    lines = pyf.read_text(errors='replace').splitlines()
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in ['period', 'interval', 'oi_hist', 'openInterestHist', 'sum_open_interest']):
            print(f"  {pyf.name} line {i}: {line.rstrip()[:120]}")

# 6. Check build_features or script for oi_usd aggregation
for pyf in [WHALE_DIR / 'build_features.py', WHALE_DIR / 'scripts' / 'collect_funding.py']:
    if pyf.exists():
        lines = pyf.read_text(errors='replace').splitlines()
        print(f"\n=== {pyf.name}: oi_usd lines ===")
        for i, line in enumerate(lines, 1):
            if 'oi_usd' in line or 'sum_open_interest' in line:
                print(f"  line {i}: {line.rstrip()[:120]}")

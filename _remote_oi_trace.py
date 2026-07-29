#!/usr/bin/env python3
"""Trace BR OI provenance: export pipeline methodology + timestamp."""
import csv, pathlib, json

WHALE_DIR = pathlib.Path('/root/Data_back_test/whale_data')
BOT_DIR = pathlib.Path('/root/binance_bot_signals')

# 1. Check export CSV for BR Jul 29 raw row + any timestamp columns
f = WHALE_DIR / 'data' / 'export' / 'freshwatch_daily_2026-07.csv'
rows = list(csv.DictReader(f.open(encoding='utf-8')))
br_rows = [r for r in rows if r['symbol'] == 'BRUSDT' and r['date'] >= '2026-07-25']
print("=== EXPORT freshwatch_daily_2026-07.csv BRUSDT Jul25-29 ===")
cols = list(br_rows[0].keys()) if br_rows else []
print("Columns:", cols)
for r in br_rows:
    print(f"  {r['date']}: oi_usd={r['oi_usd']}, src_ratio={r['src_ratio']}, data_ok={r['data_ok']}, low_conf={r['low_conf']}, funding_n={r['funding_n']}")

# 2. Check whale_collector storage for any OI raw file with timestamps
import os
oi_files = []
for root, dirs, files in os.walk(WHALE_DIR / 'data'):
    for fn in files:
        if 'br' in fn.lower() or 'oi' in fn.lower():
            full = pathlib.Path(root) / fn
            oi_files.append((str(full.relative_to(WHALE_DIR)), os.path.getmtime(str(full))))
oi_files.sort(key=lambda x: x[1], reverse=True)
print("\n=== OI/BR related data files (newest first) ===")
for fn, mt in oi_files[:15]:
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(mt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"  {dt}  {fn}")

# 3. Check if there's a raw OI collection file for BRUSDT Jul 29
# Look in pending or storage
pending_dir = BOT_DIR / 'data' / 'pending'
if pending_dir.exists():
    pending = sorted(pending_dir.glob('pending_2026-07-29*.csv'))
    print(f"\n=== pending_2026-07-29 files ({len(pending)}) ===")
    for pf in pending[:3]:
        print(f"  {pf.name}")
        # Check for BRUSDT row
        try:
            rows_p = list(csv.DictReader(pf.open(encoding='utf-8')))
            br_p = [r for r in rows_p if r.get('symbol','').upper() in ('BRUSDT','BR')]
            for r in br_p[:2]:
                print(f"    {r}")
        except:
            pass

# 4. whale_collector source code: how oi_usd is populated
wc = WHALE_DIR / 'whale_collector' / 'binance'
if wc.exists():
    for pyf in sorted(wc.glob('*.py')):
        print(f"\n=== {pyf.name}: grep oi_usd ===")
        for ln, line in enumerate(pyf.read_text(errors='replace').splitlines(), 1):
            if 'oi_usd' in line.lower() or 'openInterest' in line or 'open_interest' in line:
                print(f"  line {ln}: {line.strip()[:120]}")

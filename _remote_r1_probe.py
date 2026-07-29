#!/usr/bin/env python3
"""Remote script: probe R1 join — both sides. Upload and run via paramiko."""
import csv, sys
from pathlib import Path

WHALE = Path('/root/Data_back_test/whale_data')
EXPORT_DIR = WHALE / 'data' / 'export'
LEDGER_DIR = WHALE / 'data' / 'ledger'

print("=== SIDE A: EXPORT (freshwatch_daily) ===")
export_files = sorted(EXPORT_DIR.glob('freshwatch_daily_*.csv'))
print(f"Found {len(export_files)} export files:")
for f in export_files:
    print(f"  {f.name}  {f.stat().st_size:,} bytes")

exp_path = EXPORT_DIR / 'freshwatch_daily_2026-07.csv'
if not exp_path.exists():
    print("July export MISSING — abort")
    sys.exit(1)

with open(exp_path, 'r', newline='', encoding='utf-8', errors='replace') as fh:
    reader = csv.DictReader(fh)
    cols = reader.fieldnames or []
    all_rows = list(reader)

print(f"\nExport columns ({len(cols)}): {cols[:8]}")
print(f"Export total rows: {len(all_rows)}")

# Key: how does export store symbol? Check first 3 rows
print("\n--- Export sample: first 3 rows (symbol + date) ---")
for r in all_rows[:3]:
    print(f"  symbol={repr(r.get('symbol','?'))} date={repr(r.get('date','?'))}")

# Find TAG rows (exact and partial)
for sym_key in ['TAG', 'TAGUSDT']:
    hits = [r for r in all_rows if r.get('symbol','') == sym_key]
    print(f"\nExact symbol=='{sym_key}': {len(hits)} rows")
    for r in hits[:3]:
        print(f"  symbol={repr(r['symbol'])} date={repr(r.get('date','?'))} px_avg={r.get('px_avg','?')}")

tag_any = [r for r in all_rows if 'TAG' in r.get('symbol','').upper()]
print(f"\nPartial 'TAG' in symbol (any case): {len(tag_any)} rows, unique: {sorted(set(r['symbol'] for r in tag_any))}")

# Build export_data like ledger_daily.py does
by_symbol = {}
for row in all_rows:
    sym = (row.get("symbol") or "").strip().upper()
    if not sym:
        continue
    if sym not in by_symbol:
        by_symbol[sym] = []
    by_symbol[sym].append(dict(row))

print(f"\nexport_data keys sample (first 10): {sorted(by_symbol.keys())[:10]}")
print(f"'TAG' in export_data: {'TAG' in by_symbol}")
print(f"'TAGUSDT' in export_data: {'TAGUSDT' in by_symbol}")
if 'TAG' in by_symbol:
    r = by_symbol['TAG'][-1]
    print(f"  Latest TAG row: date={r.get('date','?')} symbol={r.get('symbol','?')}")
if 'TAGUSDT' in by_symbol:
    r = by_symbol['TAGUSDT'][-1]
    print(f"  Latest TAGUSDT row: date={r.get('date','?')} symbol={r.get('symbol','?')}")

print("\n=== SIDE B: LEDGER DIR ===")
for f in sorted(LEDGER_DIR.iterdir()):
    size = f.stat().st_size if f.is_file() else 0
    print(f"  {f.name}  {size:,} bytes")

print("\n=== SIDE C: LEDGER (ledger_v2.xlsx) ===")
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(LEDGER_DIR / 'ledger_v2.xlsx'), read_only=True, data_only=True)
    print(f"Sheets: {wb.sheetnames}")
    # Check Zone B sheet for symbol format
    for sh_name in wb.sheetnames:
        ws = wb[sh_name]
        print(f"\n  Sheet '{sh_name}': {ws.max_row}r x {ws.max_column}c")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 5:
                break
            if any(v is not None for v in row):
                print(f"    {row[:8]}")
except Exception as e:
    print(f"openpyxl error: {e}")

print("\n=== SIDE D: ledger_daily.log — join diagnostic ===")
log = WHALE / 'ledger_daily.log'
if log.exists():
    lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"Total lines: {len(lines)}")
    # Find key messages
    hits = [l for l in lines if any(x in l for x in ['no export data', 'loaded', 'symbols', 'TAG', 'Zone A', 'skipped'])]
    print(f"\nKey messages ({len(hits)} hits):")
    for l in hits[-30:]:
        print(f"  {l}")
    print("\nLast 20 lines of log:")
    for l in lines[-20:]:
        print(f"  {l}")
else:
    print("ledger_daily.log not found")

print("\n=== SIDE E: 3 pairs symbol+date raw from each side ===")
print("--- Export side (3 pairs, latest date): ---")
for sym_key in (['TAG', 'TAGUSDT'] if 'TAG' in by_symbol or 'TAGUSDT' in by_symbol else list(by_symbol.keys())[:2]):
    rows = by_symbol.get(sym_key, [])
    for r in rows[-2:]:
        print(f"  EXPORT key='{sym_key}' symbol_raw={repr(r.get('symbol','?'))} date={repr(r.get('date','?'))}")

# Show 3 pairs from ledger (what the join looks for)
print("\n--- Ledger side (what sym_upper would be): ---")
# Read ledger_v2.xlsx Zone B to get symbol+date format
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(LEDGER_DIR / 'ledger_v2.xlsx'), read_only=True, data_only=True)
    for sh_name in wb.sheetnames:
        ws = wb[sh_name]
        # Find header
        header = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            vals = [str(v).lower() if v is not None else '' for v in row]
            if 'symbol' in vals and ('date' in vals or 'entry_date' in vals or 'signal_date' in vals):
                header = [str(v) if v is not None else '' for v in row]
                sym_idx = vals.index('symbol')
                date_idx = vals.index('date') if 'date' in vals else (vals.index('entry_date') if 'entry_date' in vals else -1)
                print(f"\n  Sheet '{sh_name}' header at row {i+1}: symbol@col{sym_idx} date@col{date_idx}")
                # Print next 5 data rows
                for j, r2 in enumerate(ws.iter_rows(values_only=True, min_row=i+2)):
                    if j >= 5:
                        break
                    sym_val = r2[sym_idx] if r2 and sym_idx < len(r2) else '?'
                    date_val = r2[date_idx] if date_idx >= 0 and r2 and date_idx < len(r2) else '?'
                    if sym_val and str(sym_val).strip():
                        print(f"    LEDGER symbol_raw={repr(sym_val)} date_raw={repr(date_val)}")
                break
except Exception as e:
    print(f"  openpyxl error: {e}")

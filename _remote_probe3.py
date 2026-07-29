#!/usr/bin/env python3
"""Remote probe 3 — upload và chạy trên VPS.
  A. Symbol thực trong ledger_v2.xlsx CAMPAIGNS sheet
  B. Export TAG/BR Jul 01–28 (dữ liệu backfill T3)
  C. Export PARTI/EVAA/CLO/BLUAI Jul 19–29 (T5 cooldown packet)
  D. ledger_daily.py lines 880-930 (R3 section)
"""
import csv, sys
from pathlib import Path

WHALE = Path('/root/Data_back_test/whale_data')
EXPORT_CSV = WHALE / 'data' / 'export' / 'freshwatch_daily_2026-07.csv'
LEDGER_XLSX = WHALE / 'data' / 'ledger' / 'ledger_v2.xlsx'

print("=" * 60)
print("A. LEDGER CAMPAIGNS — actual symbols")
print("=" * 60)
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(LEDGER_XLSX), read_only=True, data_only=True)
    print(f"Sheets: {wb.sheetnames}")
    if 'CAMPAIGNS' in wb.sheetnames:
        ws = wb['CAMPAIGNS']
        header = [c for c in next(ws.iter_rows(max_row=1, values_only=True))]
        print(f"Header: {header[:10]}")
        # Find symbol and t0_date column index
        h_lower = [str(v).lower() if v else '' for v in header]
        sym_idx = h_lower.index('symbol') if 'symbol' in h_lower else -1
        date_idx = h_lower.index('t0_date') if 't0_date' in h_lower else -1
        print(f"sym_idx={sym_idx} date_idx={date_idx}")
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
            if i > 35:
                break
            sym = row[sym_idx] if sym_idx >= 0 and row and sym_idx < len(row) else None
            date = row[date_idx] if date_idx >= 0 and row and date_idx < len(row) else '?'
            if sym and str(sym).strip():
                print(f"  row {i+2}: sym={repr(str(sym).strip())} t0_date={repr(str(date))}")
    else:
        print("CAMPAIGNS sheet not found")
        for sh in wb.sheetnames:
            ws = wb[sh]
            print(f"\nSheet '{sh}' first 3 rows:")
            for j, row in enumerate(ws.iter_rows(max_row=3, values_only=True)):
                print(f"  {row[:8]}")
except Exception as e:
    print(f"openpyxl error: {e}")

print("\n" + "=" * 60)
print("B. EXPORT TAG+BR Jul 01–28 (backfill T3)")
print("=" * 60)
if EXPORT_CSV.exists():
    rows = list(csv.DictReader(open(str(EXPORT_CSV), 'r', errors='replace')))
    print(f"Total rows: {len(rows)}")
    cols = list(rows[0].keys()) if rows else []
    print(f"Columns: {cols}")
    for sym in ['TAGUSDT', 'BRUSDT']:
        sym_rows = [r for r in rows if r.get('symbol', '') == sym
                    and '2026-07-01' <= r.get('date', '') <= '2026-07-28']
        print(f"\n{sym}: {len(sym_rows)} rows (Jul 01-28)")
        for r in sym_rows:
            print(dict(r))
else:
    print(f"EXPORT_CSV MISSING: {EXPORT_CSV}")

print("\n" + "=" * 60)
print("C. EXPORT PARTI/EVAA/CLO/BLUAI Jul 19–29")
print("=" * 60)
if EXPORT_CSV.exists():
    rows = list(csv.DictReader(open(str(EXPORT_CSV), 'r', errors='replace')))
    for sym in ['PARTIUSDT', 'EVAAUSDT', 'CLOUSDT', 'BLUAIUSDT']:
        sym_rows = [r for r in rows if r.get('symbol', '') == sym
                    and '2026-07-19' <= r.get('date', '') <= '2026-07-29']
        print(f"\n{sym}: {len(sym_rows)} rows (Jul 19-29)")
        for r in sym_rows:
            print(dict(r))

print("\n" + "=" * 60)
print("D. ledger_daily.py lines 875-930")
print("=" * 60)
ld = WHALE / 'ledger_daily.py'
if ld.exists():
    all_lines = ld.read_text(errors='replace').splitlines()
    for i, line in enumerate(all_lines[874:930], start=875):
        print(f"{i:4d}: {line}")
else:
    print("ledger_daily.py MISSING")

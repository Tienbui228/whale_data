#!/usr/bin/env python3
"""Probe Zone-A-agg: đọc CAMPAIGNS tab của ledger_v2.xlsx,
tìm TAG rows, hiểu boundary (00:00 UTC hay keep-last hay avg)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from pathlib import Path

LEDGER = Path(r"D:\Check onchain fresh wallets\data\ledger\ledger_v2.xlsx")
print(f"Ledger: {LEDGER}, exists={LEDGER.exists()}")

wb = openpyxl.load_workbook(str(LEDGER), read_only=True, data_only=True)
print(f"Sheets: {wb.sheetnames}")

# Find CAMPAIGNS sheet (or similar)
target_sheets = [s for s in wb.sheetnames if any(k in s.upper() for k in ["CAMPAIGN","ZONE","LSR","RATIO"])]
print(f"Candidate sheets: {target_sheets}")

# Read first relevant sheet
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        continue
    print(f"\n=== Sheet: {sheet_name} ({len(rows)} rows) ===")
    print(f"Header: {rows[0]}")
    # Find TAG rows (any row with TAGUSDT or TAG in it)
    tag_rows = [r for r in rows[1:] if any(
        isinstance(c, str) and "TAG" in c.upper() for c in r if c is not None
    )]
    if tag_rows:
        print(f"TAG rows found ({len(tag_rows)}):")
        for r in tag_rows[:10]:
            print(f"  {r}")
    else:
        print("(no TAG rows)")

wb.close()

# Also check the most recent backup for reference
BACKUP = Path(r"D:\Check onchain fresh wallets\data\ledger\backups\ledger_v2_20260730_084919.xlsx")
if BACKUP.exists():
    print(f"\n=== BACKUP {BACKUP.name} ===")
    wb2 = openpyxl.load_workbook(str(BACKUP), read_only=True, data_only=True)
    print(f"Sheets: {wb2.sheetnames}")
    for sheet_name in wb2.sheetnames:
        ws = wb2[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        tag_rows = [r for r in rows[1:] if any(
            isinstance(c, str) and "TAG" in c.upper() for c in r if c is not None
        )]
        if tag_rows:
            print(f"\n  Sheet [{sheet_name}] TAG rows:")
            print(f"  Header: {rows[0]}")
            for r in tag_rows[:10]:
                print(f"    {r}")
    wb2.close()

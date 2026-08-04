#!/usr/bin/env python3
"""Probe: đọc cấu trúc CASE_BANK.xlsx để làm template CASE_CLO."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from pathlib import Path

BANK = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_BANK.xlsx")
TAG  = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_TAG.xlsx")

for fpath in [BANK, TAG]:
    print(f"\n{'='*60}")
    print(f"FILE: {fpath.name}")
    wb = openpyxl.load_workbook(fpath, data_only=True)
    print(f"Sheets: {wb.sheetnames}")
    for shname in wb.sheetnames:
        ws = wb[shname]
        print(f"\n--- Sheet: {shname} ({ws.max_row}r × {ws.max_column}c) ---")
        # Print first 6 rows
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 8: break
            print(f"  R{i+1}: {list(row)}")

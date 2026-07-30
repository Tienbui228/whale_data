#!/usr/bin/env python3
"""Probe actual LESSONS sheet structure to fix L-39 append."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from pathlib import Path

CASE_INDEX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
wb = openpyxl.load_workbook(str(CASE_INDEX), read_only=True, data_only=True)
ws = wb["LESSONS"]

rows = list(ws.iter_rows(values_only=True))
print(f"Total rows (incl header): {len(rows)}")
print(f"Row 0 (title/header): {rows[0]}")
print()

# Show rows 35-last (to see L-35..L-39)
print("=== Last 8 rows ===")
for i, r in enumerate(rows[-8:], start=len(rows)-7):
    print(f"Row {i}: {r}")

wb.close()

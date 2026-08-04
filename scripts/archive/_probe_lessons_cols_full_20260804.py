#!/usr/bin/env python3
"""Probe: full LESSONS sheet column structure."""
import io, sys
import openpyxl
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
wb = openpyxl.load_workbook(CASE_DIR / "CASE_INDEX.xlsx")
ws = wb["LESSONS"]

print(f"Max row: {ws.max_row}, Max col: {ws.max_column}")

# Print all columns for first 3 rows
print("\n=== Rows 1-3 (all cols) ===")
for r in range(1, 4):
    for c in range(1, ws.max_column+1):
        v = ws.cell(r, c).value
        if v:
            print(f"  R{r}C{c}: {str(v)[:120]}")

# Print all columns for rows 5-7 (L-05, L-06, L-07)
print("\n=== Rows 6-8 (L-05, L-06, L-07 — all cols) ===")
for r in range(6, 9):
    print(f"\nRow {r}:")
    for c in range(1, ws.max_column+1):
        v = ws.cell(r, c).value
        if v is not None:
            print(f"  C{c}: {str(v)[:150]}")

# Print last 2 rows (all cols)
print("\n=== Last 2 rows ===")
for r in range(ws.max_row-1, ws.max_row+1):
    print(f"\nRow {r}:")
    for c in range(1, ws.max_column+1):
        v = ws.cell(r, c).value
        if v is not None:
            print(f"  C{c}: {str(v)[:150]}")

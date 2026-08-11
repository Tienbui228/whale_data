"""Probe LESSONS sheet structure in CASE_INDEX."""
import sys, io, openpyxl
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

wb = openpyxl.load_workbook(Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx"))
ws = wb["LESSONS"]

print(f"max_row={ws.max_row}, max_col={ws.max_column}")
print("First 5 rows, all columns:")
for r in range(1, min(6, ws.max_row + 1)):
    row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
    print(f"  Row {r}: {row_vals}")

print("\nLast 3 non-empty rows:")
for r in range(max(1, ws.max_row - 3), ws.max_row + 1):
    row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
    if any(v for v in row_vals):
        print(f"  Row {r}: {row_vals}")

#!/usr/bin/env python3
"""Quick header dump for COOKIE/BROCCOLIF3B/KOMA to confirm schema."""
from pathlib import Path
import openpyxl

CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")

for fname in ["CASE_COOKIE.xlsx", "CASE_BROCCOLIF3B.xlsx", "CASE_KOMA.xlsx"]:
    fpath = CASE_DIR / fname
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    wb = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
    ws = wb["DAILY"]
    for row_idx in range(1, 4):  # rows 1-3 (2 header rows + first data row)
        row_vals = []
        for c in range(1, 50):
            v = ws.cell(row_idx, c).value
            row_vals.append(v)
        print(f"  Row {row_idx}: {row_vals[:32]}")
    # Show last 5 data rows
    max_row = ws.max_row
    print(f"  max_row={max_row}")
    print(f"  Last 3 rows (max_row-2 to max_row):")
    for row_idx in range(max(3, max_row - 2), max_row + 1):
        row_vals = [ws.cell(row_idx, c).value for c in range(1, 33)]
        print(f"  Row {row_idx}: {row_vals}")
    wb.close()

print("\nDUNG.")

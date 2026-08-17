"""Quick check: rows 1-3 of CASE_AIN DAILY to understand header structure."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

path = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_AIN.xlsx")
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb["DAILY"]

print(f"max_row={ws.max_row}, max_col={ws.max_column}")
print("\nRow 1 (all):")
for i, c in enumerate(next(ws.iter_rows(min_row=1, max_row=1)), 1):
    if c.value is not None:
        print(f"  col{i:2d}: {repr(c.value)}")

print("\nRow 2 (first 50 cols):")
for i, c in enumerate(next(ws.iter_rows(min_row=2, max_row=2)), 1):
    if c.value is not None:
        print(f"  col{i:2d}: {repr(c.value)}")

print("\nRow 3 (data row 1):")
r3 = list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]
print(f"  {r3[:15]} ...")

print("\nRow 4 (data row 2):")
r4 = list(ws.iter_rows(min_row=4, max_row=4, values_only=True))[0]
print(f"  {r4[:15]} ...")

# Col 31-35 specifically in row 2
print("\nRow 2 col28-40:")
r2 = list(ws.iter_rows(min_row=2, max_row=2, values_only=True))[0]
for i in range(27, 40):
    if i < len(r2):
        print(f"  col{i+1:2d}: {repr(r2[i])}")

wb.close()

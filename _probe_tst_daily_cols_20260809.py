"""Map CASE_TST DAILY column headers and check GOM status."""
import openpyxl
from pathlib import Path

path = Path("docs/case_files/CASE_TST.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
ws = wb["DAILY"]

rows = list(ws.iter_rows(values_only=True))
print(f"Total rows: {len(rows)}")
print()
print("Row 1 (section headers):")
for i, v in enumerate(rows[0]):
    if v: print(f"  col{i}: {v}")
print()
print("Row 2 (column headers):")
for i, v in enumerate(rows[1]):
    if v: print(f"  col{i}: {v}")
print()

# First data row
print("Row 3 (first data):")
print(" ", rows[2])
print()

# Date range
dates = [r[0] for r in rows[2:] if r[0]]
print(f"Date range: {dates[0]} → {dates[-1]} ({len(dates)} rows)")
print()

# GOM columns
gom_col_start = None
for i, v in enumerate(rows[0]):
    if v and "GOM" in str(v):
        gom_col_start = i
        break
print(f"GOM section starts at col {gom_col_start}")
if gom_col_start:
    gom_headers = [(i, rows[1][i]) for i in range(gom_col_start, min(gom_col_start+8, len(rows[1])))]
    print("GOM headers:", gom_headers)
    print()
    print("GOM values last 10 rows:")
    for r in rows[-10:]:
        print(f"  {r[0]}: {r[gom_col_start:gom_col_start+8]}")

wb.close()

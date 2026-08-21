"""Read LESSONS sheet schema + last 3 rows structure."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["LESSONS"]

# Row 4 is header
print("=== Row 4 header (schema) ===")
for c in range(1, ws.max_column+1):
    v = ws.cell(4, c).value
    print(f"  col {c}: {v!r}")

# Row 52-55 (L-49 to L-BUG) — see how rows are structured
print("\n=== Rows 52-55 (L-49, L-50, L-51, L-BUG) full content ===")
for r in range(52, 56):
    print(f"\nRow {r}:")
    for c in range(1, ws.max_column+1):
        v = ws.cell(r, c).value
        if v is not None:
            print(f"  col {c}: {str(v)[:200]}")

# also print row 51 (L-48) for reference
print("\n=== Row 51 (L-48) full ===")
for c in range(1, ws.max_column+1):
    v = ws.cell(51, c).value
    if v is not None:
        print(f"  col {c}: {str(v)[:200]}")

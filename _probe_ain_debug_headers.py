"""Debug: print CASE_AIN.xlsx headers and sample row."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
case_path = ROOT / "docs" / "case_files" / "CASE_AIN.xlsx"
wb = openpyxl.load_workbook(case_path, read_only=True, data_only=True)
ws = wb["DAILY"]
all_rows = list(ws.iter_rows(values_only=True))
print(f"Total rows: {len(all_rows)}")
print(f"\nRow 0 (category labels, first 10):\n{all_rows[0][:10]}")
print(f"\nRow 1 (HDR_LABELS, first 20):\n{all_rows[1][:20]}")
print(f"\nRow 2 (first data row, first 20):\n{all_rows[2][:20]}")
# Find close and vol columns
headers = list(all_rows[1])
for i, h in enumerate(headers):
    if h and ("close" in str(h).lower() or "vol" in str(h).lower()):
        print(f"  col {i}: header='{h}' val='{all_rows[2][i]}'")

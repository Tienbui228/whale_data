"""
_probe_apr_headers_20260811.py
Read CASE_APR.xlsx DAILY: column names, last row, row count.
machine: local
"""
import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")
CASE_APR = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"

def log(s=""): print(s)

log("=== CASE_APR.xlsx DAILY HEADERS ===")
wb = openpyxl.load_workbook(CASE_APR, data_only=True, read_only=True)
log(f"Sheets: {wb.sheetnames}")

sh = wb["DAILY"]
all_rows = list(sh.iter_rows(values_only=True))
log(f"Total rows (incl headers): {len(all_rows)}")
log(f"Row 0 (section labels): {list(all_rows[0])[:10]}...")
log(f"Row 1 (column names): {list(all_rows[1])}")
log(f"Data rows: {len(all_rows) - 2}")

hdr = list(all_rows[1])
log(f"\n=== ALL 50 COLUMNS (idx: name) ===")
for i, h in enumerate(hdr):
    log(f"  [{i:02d}] {h}")

log(f"\n=== LAST 3 DATA ROWS ===")
for row in all_rows[-3:]:
    log(f"  {list(row)[:6]}  ...")

log(f"\n=== FIRST DATA ROW ===")
log(f"  {list(all_rows[2])[:6]}")

# Find date column index
date_idx = None
for i, h in enumerate(hdr):
    if h and "date" in str(h).lower():
        date_idx = i
        break
if date_idx is not None:
    log(f"\nDate col index: {date_idx} ({hdr[date_idx]})")
    log(f"First date: {all_rows[2][date_idx]}")
    log(f"Last date:  {all_rows[-1][date_idx]}")

wb.close()
log("\n[DONE]")

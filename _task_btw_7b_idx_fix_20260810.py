"""_task_btw_7b_idx_fix_20260810.py — fix token + loai fields in CASE_INDEX row 21."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
XLSX_IDX = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"

wb = openpyxl.load_workbook(XLSX_IDX)
ws = wb.active

# Find header row
hdr_idx = None; headers = []
for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
    if str(row[0] or "").lower().strip() == "file":
        hdr_idx = i; headers = [str(c or "").strip() for c in row]; break

print(f"Headers: {headers}")

# Find BTW row (CASE_BTW.xlsx)
for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
    if str(row[0] or "").strip() == "CASE_BTW.xlsx":
        print(f"Found BTW at row {i}: {list(row)}")
        # Update token (col 2 = headers[1] = "token")
        # Update loai (col 4 = headers[3] = "loai")
        # Update action_class (col 5 = headers[4] = "action_class")
        ws.cell(row=i, column=2, value="BTW")
        ws.cell(row=i, column=4, value="BLOWOFF2.0 echo; 3-cond trigger 0/3; OI UNCALIBRATED; GOM-C 14d pre-cool")
        ws.cell(row=i, column=5, value="WATCH (án tích refresh)")
        print(f"  Updated row {i}")
        break

wb.save(XLSX_IDX)
print("Saved CASE_INDEX.xlsx")

# Verify
for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
    if i > hdr_idx and row[0]: print(f"  Row {i}: {list(row[:6])}")

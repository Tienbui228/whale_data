"""Dump first 2 rows of DAILY sheet for each CASE file to reveal actual header names."""
from __future__ import annotations
import sys, io
from pathlib import Path
import openpyxl
from openpyxl.cell.cell import MergedCell

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")

# Check a few representative files
targets = ["CASE_ZBT.xlsx", "CASE_HEI.xlsx", "CASE_FF.xlsx", "CASE_BROCCOLIF3B.xlsx"]

for name in targets:
    xlsx = CASE_DIR / name
    if not xlsx.exists():
        print(f"{name}: NOT FOUND"); continue
    wb = openpyxl.load_workbook(str(xlsx), data_only=True, read_only=True)
    if "DAILY" not in wb.sheetnames:
        print(f"{name}: NO DAILY SHEET"); wb.close(); continue
    ws = wb["DAILY"]
    print(f"\n=== {name} — DAILY rows 1-3 ===")
    for ri, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if ri > 3:
            break
        vals = [str(v)[:20] if v is not None else "(null)" for v in row[:25]]
        print(f"  row{ri}: {vals}")
    wb.close()

"""Dump full row2 headers (all cols) from key CASE files."""
from __future__ import annotations
import sys, io
from pathlib import Path
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")

targets = ["CASE_ZBT.xlsx", "CASE_HEI.xlsx", "CASE_FF.xlsx", "CASE_BANANAS31.xlsx"]

for name in targets:
    xlsx = CASE_DIR / name
    if not xlsx.exists():
        continue
    wb = openpyxl.load_workbook(str(xlsx), data_only=True, read_only=True)
    ws = wb["DAILY"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    # Find row with 'date'
    hrow = None
    for i, row in enumerate(rows[:5]):
        if any(str(v).startswith("date") for v in row if v):
            hrow = row; break
    if hrow is None:
        print(f"{name}: no header row found"); continue
    print(f"\n=== {name} ===")
    for ci, v in enumerate(hrow):
        if v is not None:
            print(f"  col{ci+1:>3}: {v}")

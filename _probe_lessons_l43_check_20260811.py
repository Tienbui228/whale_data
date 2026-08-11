"""Check L-43 through L-54 existence in CASE_INDEX LESSONS sheet."""
import sys, io, openpyxl
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

wb = openpyxl.load_workbook(Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx"))
ws = wb["LESSONS"]

print("Rows 40-54 (L-40 onward):")
for r in range(40, min(ws.max_row + 1, 58)):
    id_val = ws.cell(row=r, column=1).value
    date_val = ws.cell(row=r, column=2).value
    case_val = ws.cell(row=r, column=3).value
    bai_hoc = ws.cell(row=r, column=4).value
    if id_val or bai_hoc:
        snippet = str(bai_hoc or "")[:80] if bai_hoc else "(empty)"
        print(f"  Row {r:2d}: id={id_val!r:10} date={str(date_val)[:12]} | {snippet}")
    else:
        print(f"  Row {r:2d}: EMPTY")

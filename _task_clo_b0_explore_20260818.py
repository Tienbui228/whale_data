"""_task_clo_b0_explore_20260818.py — B0 backup + explore CLO structure."""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES   = ROOT / "docs" / "case_files"

src = CASES / "CASE_CLO.xlsx"
dst = SCRATCH / "CASE_CLO_bak_pre_refresh_20260818.xlsx"
if not dst.exists():
    shutil.copy2(src, dst)
print(f"BACKUP: {dst} ({dst.stat().st_size} B)")

wb = openpyxl.load_workbook(src, data_only=True)
print(f"Sheets: {wb.sheetnames}")

ws = wb["DAILY"]
row1 = [c.value for c in ws[1]]
row2 = [c.value for c in ws[2]]
print(f"\nDAILY dims: {ws.dimensions}, cols: {len(row2)}")

print(f"\nFull col map (col#, section, field):")
for i, (s, f) in enumerate(zip(row1, row2), start=1):
    print(f"  col {i:2d}: section={s!r}  field={f!r}")

# Data range
dates = []
for r in range(3, ws.max_row+1):
    d = ws.cell(r, 1).value
    if d:
        dates.append((r, str(d)[:10]))
print(f"\nDAILY: {len(dates)} rows, first={dates[0]}, last={dates[-1]}")

# Sample last 10 rows across ALL cols to see data
print(f"\nLast 5 rows (all cols):")
last5 = dates[-5:]
for r_num, d_str in last5:
    row_vals = [ws.cell(r_num, i).value for i in range(1, len(row2)+1)]
    non_null = [(i, row1[i-1], row2[i-1], v) for i, v in enumerate(row_vals, start=1) if v is not None]
    print(f"\n  === row {r_num} ({d_str}) ===")
    for i, sec, fld, v in non_null:
        print(f"    col {i:2d} [{sec}][{fld}] = {v}")

# CASE sheet
if "CASE" in wb.sheetnames:
    print(f"\n=== CASE sheet ===")
    ws_case = wb["CASE"]
    for r in range(1, ws_case.max_row+1):
        row_v = [c.value for c in ws_case[r]]
        if any(v is not None for v in row_v):
            print(f"  r{r}: {row_v[:8]}")

# EVENTS
if "EVENTS" in wb.sheetnames:
    ws_ev = wb["EVENTS"]
    print(f"\n=== EVENTS: dims={ws_ev.dimensions} max_row={ws_ev.max_row} ===")
    for r in range(1, min(ws_ev.max_row+1, 20)):
        print(f"  r{r}: {[c.value for c in ws_ev[r]]}")

if "UNLOCK" in wb.sheetnames:
    ws_ul = wb["UNLOCK"]
    print(f"\n=== UNLOCK dims={ws_ul.dimensions} ===")
    print(f"  r1: {[c.value for c in ws_ul[1]]}")

print("\n[DONE]")

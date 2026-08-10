"""Check ZBT last 35 rows of DAILY to see f_avg and LSR column data."""
from __future__ import annotations
import sys, io
from pathlib import Path
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_ZBT.xlsx")
wb = openpyxl.load_workbook(str(XLSX), data_only=True, read_only=True)
ws = wb["DAILY"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

# Find header row
hrow_idx = None
for i, row in enumerate(rows[:5]):
    if any(str(v) == "date" for v in row if v):
        hrow_idx = i; break

headers = {v: ci for ci, v in enumerate(rows[hrow_idx]) if v}
print(f"Header row index: {hrow_idx}")
print(f"Headers: {list(headers.keys())}")

data_rows = [r for r in rows[hrow_idx+1:] if r[0] not in (None, "")]
print(f"Total data rows: {len(data_rows)}")

# Show last 35 rows: date, px_avg, f_avg, lsr_pos_r (cols 2,6,15)
col_date = headers.get("date", 0)
col_px   = headers.get("px_avg", 1)
col_favg = headers.get("f_avg", 5)
col_fn   = headers.get("f_n", 8)
col_lsr  = headers.get("lsr_pos_r", 14)

print(f"\n{'date':<14} {'px_avg':<14} {'f_avg':<12} {'f_n':<8} {'lsr_pos_r'}")
for r in data_rows[-35:]:
    print(f"  {str(r[col_date]):<14} {str(r[col_px])[:12]:<14} {str(r[col_favg])[:10]:<12} {str(r[col_fn]):<8} {str(r[col_lsr])}")

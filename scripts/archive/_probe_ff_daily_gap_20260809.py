"""Find when CASE_FF DAILY stopped getting PERP klines data."""
import openpyxl
from pathlib import Path
from datetime import date

path = Path("docs/case_files/CASE_FF.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
ws = wb["DAILY"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

data = rows[2:]  # skip 2 header rows

# Find last row with non-None px_avg (col1)
last_with_px = None
first_none_px = None
for r in data:
    if not r[0]:
        continue
    px = r[1]  # px_avg
    d_val = r[0]
    if isinstance(d_val, date) or hasattr(d_val, 'strftime'):
        d_str = d_val.strftime("%Y-%m-%d")
    else:
        d_str = str(d_val)[:10]

    if px is not None:
        last_with_px = d_str
        first_none_px = None  # reset
    elif first_none_px is None:
        first_none_px = d_str

print(f"Total data rows: {len([r for r in data if r[0]])}")
print(f"Last row with px_avg: {last_with_px}")
print(f"First row with px_avg=None: {first_none_px}")

# Count rows with None vs not None for px_avg
none_count = sum(1 for r in data if r[0] and r[1] is None)
ok_count = sum(1 for r in data if r[0] and r[1] is not None)
print(f"Rows with px_avg: {ok_count}, without: {none_count}")

# Show the transition zone
in_transition = False
for r in data:
    if not r[0]:
        continue
    d_val = r[0]
    if isinstance(d_val, date) or hasattr(d_val, 'strftime'):
        d_str = d_val.strftime("%Y-%m-%d")
    else:
        d_str = str(d_val)[:10]

    if d_str >= "2026-05-20" and d_str <= "2026-06-10":
        print(f"  {d_str}: px={r[1]}, vol={r[6]}, f_avg={r[8]}")

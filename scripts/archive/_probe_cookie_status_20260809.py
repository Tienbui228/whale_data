"""Check CASE_COOKIE DAILY status."""
import openpyxl
from pathlib import Path
from datetime import date

path = Path("docs/case_files/CASE_COOKIE.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
ws = wb["DAILY"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

data = rows[2:]

def ds(r):
    v = r[0]
    if v is None: return None
    if isinstance(v, date) or hasattr(v, 'strftime'):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10]

data_rows = [r for r in data if r[0]]
print(f"COOKIE DAILY rows: {len(data_rows)}")
print(f"Date range: {ds(data_rows[0])} to {ds(data_rows[-1])}")
print()

# Check klines columns (1-7) and gom columns (37-39)
none_px = sum(1 for r in data_rows if r[1] is None)
ok_px = sum(1 for r in data_rows if r[1] is not None)
gom_a_fires = sum(1 for r in data_rows if len(r)>37 and str(r[37]).upper()=='TRUE')

print(f"px_avg populated: {ok_px}, None: {none_px}")
print(f"GOM-A fire: {gom_a_fires}")

# Last 5 rows
print("Last 5:")
for r in data_rows[-5:]:
    pos_r = r[26] if len(r)>26 else None
    gLSR = r[28] if len(r)>28 else None
    gom_a = r[37] if len(r)>37 else None
    print(f"  {ds(r)}: px={r[1]} vol={r[6]} pos_r={pos_r} gLSR={gLSR} gom_A={gom_a}")

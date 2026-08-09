"""Check FF DAILY GOM screen columns and alpha vol columns."""
import openpyxl
from pathlib import Path
from datetime import date

path = Path("docs/case_files/CASE_FF.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
ws = wb["DAILY"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

# Header rows
print("Row 1 sections (non-None):")
for i, v in enumerate(rows[0]):
    if v:
        try: print(f"  col{i}: {v}")
        except: print(f"  col{i}: [encode-err]")
print()
print("Row 2 cols:")
for i, v in enumerate(rows[1]):
    if v:
        try: print(f"  col{i}: {v}")
        except: print(f"  col{i}: [encode-err]")
print()

data = rows[2:]

def d_str(r):
    v = r[0]
    if v is None: return None
    if isinstance(v, date) or hasattr(v, 'strftime'):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10]

# Find GOM columns from row 1 (section headers)
for i, v in enumerate(rows[0]):
    if v and "GOM" in str(v):
        print(f"GOM section at col {i}")
for i, v in enumerate(rows[0]):
    if v and "ALPHA" in str(v):
        print(f"ALPHA section at col {i}")

# Last 10 rows with key columns
print()
print("Last 10 data rows (key cols):")
for r in data[-10:]:
    ds = d_str(r)
    if not ds: continue
    # Try to show: date, pos_r(26), acc_r(27), gLSR(28), alpha_vol(34), gom_A(37), gom_B(38)
    pos_r = r[26] if len(r)>26 else None
    acc_r = r[27] if len(r)>27 else None
    gLSR  = r[28] if len(r)>28 else None
    alpha_v = r[34] if len(r)>34 else None
    gom_a = r[37] if len(r)>37 else None
    gom_b = r[38] if len(r)>38 else None
    print(f"  {ds}: pos_r={pos_r} acc_r={acc_r} gLSR={gLSR} alpha_vol={alpha_v} gom_A={gom_a} gom_B={gom_b}")

# Count GOM fire days
gom_a_true = sum(1 for r in data if r[0] and len(r)>37 and str(r[37]).upper()=='TRUE')
gom_b_true = sum(1 for r in data if r[0] and len(r)>38 and str(r[38]).upper()=='TRUE')
print(f"\nGOM-A fire: {gom_a_true}")
print(f"GOM-B fire: {gom_b_true}")
print(f"Total data rows: {len([r for r in data if r[0]])}")

# First and last non-None gom_A
print("\nGOM-A fire dates:")
for r in data:
    if r[0] and len(r)>37 and str(r[37]).upper()=='TRUE':
        print(f"  {d_str(r)}: gom_A={r[37]}, pos_r={r[26] if len(r)>26 else None}")

"""R3: Merge TST LSR backfill into CASE_TST DAILY sheet.
Fills cols: pos_r(26), acc_r(27), gLSR(28), taker_lsr(29), div_raw(21), div_avg3(22)
for rows 07-11 to 08-09 where currently None.
Also re-computes div_avg3 for affected window.

data-source: scratch/tst_lsr_backfill_20260809.csv (from VPS parquet stores)
machine: local
date-range: 2026-07-10 to 2026-08-09
code-commit: (pre-commit, task script)
"""
import openpyxl
import csv
from pathlib import Path
from datetime import date
import math

CASE_PATH = Path("docs/case_files/CASE_TST.xlsx")
CSV_PATH = Path("scratch/tst_lsr_backfill_20260809.csv")

# Load backfill CSV into dict keyed by date string
backfill = {}
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        d = row["date"].strip()
        def fv(k):
            v = row.get(k, "").strip()
            return float(v) if v and v.lower() not in ("nan", "", "none") else None
        backfill[d] = {
            "pos_r":     fv("pos_r"),
            "acc_r":     fv("acc_r"),
            "gLSR":      fv("gLSR"),
            "taker_lsr": fv("taker_lsr"),
            "div_raw":   fv("div_raw"),
            "oi_usd_store": fv("oi_usd_store"),
        }

print(f"Backfill dates: {sorted(backfill)[:3]} ... {sorted(backfill)[-3:]}")
print(f"Total backfill entries: {len(backfill)}")

# Open workbook
wb = openpyxl.load_workbook(CASE_PATH)
ws = wb["DAILY"]

# Column mapping (1-indexed for openpyxl)
# Row 1 = section headers, Row 2 = col headers, Row 3+ = data
COL = {
    "date":      1,   # col0
    "oi_usd":    13,  # col12
    "div_raw":   22,  # col21
    "div_avg3":  23,  # col22
    "pos_r":     27,  # col26
    "acc_r":     28,  # col27
    "gLSR":      29,  # col28
    "taker_lsr": 30,  # col29
}

# Build {date_str: row_index} map for data rows (starting at row 3)
date_row_map = {}
for row in ws.iter_rows(min_row=3, max_col=1, values_only=False):
    cell = row[0]
    if cell.value is None:
        continue
    d_val = cell.value
    if isinstance(d_val, (date,)) or hasattr(d_val, 'strftime'):
        d_str = d_val.strftime("%Y-%m-%d")
    else:
        d_str = str(d_val)[:10]
    date_row_map[d_str] = cell.row

print(f"Excel date rows: {len(date_row_map)}, last 3: {sorted(date_row_map)[-3:]}")

updates = 0
skipped_missing = 0
skipped_existing = 0

for d_str, vals in sorted(backfill.items()):
    if d_str not in date_row_map:
        skipped_missing += 1
        continue

    row_i = date_row_map[d_str]
    changed = False

    for col_name, bf_key in [("pos_r", "pos_r"), ("acc_r", "acc_r"), ("gLSR", "gLSR"), ("taker_lsr", "taker_lsr")]:
        col_i = COL[col_name]
        existing = ws.cell(row=row_i, column=col_i).value
        new_val = vals[bf_key]
        if existing is None and new_val is not None:
            ws.cell(row=row_i, column=col_i).value = round(new_val, 4)
            changed = True

    # div_raw (computed from pos_r/acc_r)
    pos_r_final = ws.cell(row=row_i, column=COL["pos_r"]).value
    acc_r_final = ws.cell(row=row_i, column=COL["acc_r"]).value
    if pos_r_final is not None and acc_r_final is not None and acc_r_final > 0:
        dr = round(pos_r_final / acc_r_final, 4)
        if ws.cell(row=row_i, column=COL["div_raw"]).value is None:
            ws.cell(row=row_i, column=COL["div_raw"]).value = dr
            changed = True

    if changed:
        updates += 1

print(f"Updated: {updates} rows")
print(f"Skipped (date not in Excel): {skipped_missing}")

# Recompute div_avg3 for all rows that have div_raw (rolling 3-day mean)
# Collect all div_raw values in row order
all_dates_sorted = sorted(date_row_map.items())
div_raw_by_row = []
for d_str, row_i in all_dates_sorted:
    dr = ws.cell(row=row_i, column=COL["div_raw"]).value
    div_raw_by_row.append((d_str, row_i, dr))

avg3_updates = 0
for i, (d_str, row_i, dr) in enumerate(div_raw_by_row):
    if dr is None:
        continue
    window = [v for _, _, v in div_raw_by_row[max(0, i-2):i+1] if v is not None]
    if not window:
        continue
    new_avg3 = round(sum(window) / len(window), 4)
    existing_avg3 = ws.cell(row=row_i, column=COL["div_avg3"]).value
    if existing_avg3 is None or abs((existing_avg3 or 0) - new_avg3) > 0.0001:
        ws.cell(row=row_i, column=COL["div_avg3"]).value = new_avg3
        avg3_updates += 1

print(f"div_avg3 updated: {avg3_updates} rows")

wb.save(CASE_PATH)
print(f"Saved: {CASE_PATH}")
print()

# Verify last 10 updated rows
print("Verification — last 10 rows with LSR data:")
for d_str, row_i in sorted(date_row_map.items())[-20:]:
    pos_r = ws.cell(row=row_i, column=COL["pos_r"]).value
    acc_r = ws.cell(row=row_i, column=COL["acc_r"]).value
    glsr = ws.cell(row=row_i, column=COL["gLSR"]).value
    div_r = ws.cell(row=row_i, column=COL["div_raw"]).value
    if pos_r is not None:
        print(f"  {d_str}: pos_r={pos_r} acc_r={acc_r} gLSR={glsr} div_raw={div_r}")

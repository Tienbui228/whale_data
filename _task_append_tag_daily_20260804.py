#!/usr/bin/env python3
"""Task: Append CASE_TAG.xlsx DAILY — fix 30/07 + append 01-03/08.

30/07 row (row 32): px/vol/taker/OI missing — freshwatch has data.
01-03/08: entirely missing rows — append from freshwatch.
04/08: partial day — skip, ghi PENDING.

Source: freshwatch_daily_2026-08.csv
"""
import csv, io, sys
from pathlib import Path
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
XLSX    = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_TAG.xlsx")

# ─── Load freshwatch TAG ───────────────────────────────────────────────────────
tag_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "TAGUSDT":
            tag_rows[r["date"]] = r

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

print("Available dates:", sorted(tag_rows.keys())[-10:])

# ─── Open XLSX ─────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLSX)
ws = wb["DAILY"]

print(f"Current max_row: {ws.max_row}")

# Map row numbers to dates (scan column A)
date_to_row = {}
for row in ws.iter_rows(min_row=3, values_only=False):
    if row[0].value and isinstance(row[0].value, str) and row[0].value.startswith("2026"):
        date_to_row[row[0].value] = row[0].row

print(f"Last date in DAILY: {max(date_to_row.keys())}")
print(f"Row for 2026-07-30: {date_to_row.get('2026-07-30', 'NOT FOUND')}")

# ─── Fix row 30/07 (row 32) — fill missing numeric cols ──────────────────────
# Unmerge A32:L32 before writing (openpyxl can't write to merged slave cells)
for mr in list(ws.merged_cells.ranges):
    if mr.min_row == 32 and mr.max_row == 32:
        print(f"Unmerging {mr}")
        ws.unmerge_cells(str(mr))

row_30 = date_to_row.get("2026-07-30")
if row_30:
    r = tag_rows.get("2026-07-30", {})
    px   = gv(r, "px_avg")
    vol  = gv(r, "vol_quote")
    tk   = gv(r, "taker_buy_pct")
    fav  = gv(r, "funding_avg")
    fmin = gv(r, "funding_min")
    fmax = gv(r, "funding_max")
    fn   = gv(r, "funding_n")
    oi   = gv(r, "oi_usd")

    # Only write if currently empty
    if ws.cell(row_30, 2).value is None:
        ws.cell(row_30, 2, px)
    if ws.cell(row_30, 4).value is None:
        ws.cell(row_30, 4, vol)
    if ws.cell(row_30, 5).value is None:
        ws.cell(row_30, 5, tk)
    if ws.cell(row_30, 6).value is None:
        ws.cell(row_30, 6, fav)
    if ws.cell(row_30, 7).value is None:
        ws.cell(row_30, 7, fmin)
    if ws.cell(row_30, 8).value is None:
        ws.cell(row_30, 8, fmax)
    if ws.cell(row_30, 9).value is None and fn:
        ws.cell(row_30, 9, int(fn))
    if ws.cell(row_30, 12).value is None:
        ws.cell(row_30, 12, oi)
    # Fill formula for ret_1d (C=col 3)
    if ws.cell(row_30, 3).value is None:
        ws.cell(row_30, 3, f"=IFERROR(B{row_30}/B{row_30-1}-1,\"\")")
    # funding_regime (col 10, J)
    if fav is not None and abs(fav - 0.00005) < 0.000005:
        ws.cell(row_30, 10, "PINNED")

    print(f"Fixed row {row_30} (2026-07-30): px={px}, vol={vol}, oi={oi}")
else:
    print("Row 30/07 not found in DAILY!")

# ─── Append 01/08, 02/08, 03/08 ──────────────────────────────────────────────
next_row = ws.max_row + 1

dates_to_append = ["2026-08-01", "2026-08-02", "2026-08-03"]

for d in dates_to_append:
    if d in date_to_row:
        print(f"  {d} already exists at row {date_to_row[d]}, skipping")
        continue
    r = tag_rows.get(d, {})
    if not r:
        print(f"  {d}: no freshwatch data, skip")
        continue

    px   = gv(r, "px_avg")
    vol  = gv(r, "vol_quote")
    tk   = gv(r, "taker_buy_pct")
    fav  = gv(r, "funding_avg")
    fmin = gv(r, "funding_min")
    fmax = gv(r, "funding_max")
    fn   = gv(r, "funding_n")
    oi   = gv(r, "oi_usd")
    pr   = gv(r, "lsr_pos_r")
    ar   = gv(r, "lsr_acc_r")
    gl   = gv(r, "lsr_global_r")

    n = next_row
    ws.cell(n, 1,  d)
    ws.cell(n, 2,  px)
    ws.cell(n, 3,  f"=IFERROR(B{n}/B{n-1}-1,\"\")")
    ws.cell(n, 4,  vol)
    ws.cell(n, 5,  tk)
    ws.cell(n, 6,  fav)
    ws.cell(n, 7,  fmin)
    ws.cell(n, 8,  fmax)
    if fn: ws.cell(n, 9, int(fn))
    regime = "PINNED" if (fav is not None and abs(fav - 0.00005) < 0.000005) else None
    if regime: ws.cell(n, 10, regime)
    ws.cell(n, 12, oi)
    ws.cell(n, 13, f"=IFERROR(L{n}/MEDIAN(L{max(3,n-14)}:L{n-1}),\"\")")
    ws.cell(n, 15, pr)
    ws.cell(n, 16, ar)
    ws.cell(n, 17, gl)
    ws.cell(n, 18, f"=IFERROR(O{n}/P{n},\"\")")
    ws.cell(n, 19, f"=IFERROR(AVERAGE(R{max(3,n-2)}:R{n}),\"\")")
    ws.cell(n, 20, f"=IFERROR(Q{n}/Q{max(3,n-5)},\"\")")
    ws.cell(n, 21, f"=IFERROR(O{n}/O{max(3,n-3)}-1,\"\")")
    ws.cell(n, 22, f"=IFERROR(P{n}/P{max(3,n-3)}-1,\"\")")

    px_s = f"{px:.6f}" if px else "?"
    oi_s = f"{oi/1e6:.2f}" if oi else "?"
    print(f"  Appended {d} at row {n}: px={px_s}, OI={oi_s}M, gLSR={gl}")
    next_row += 1

wb.save(XLSX)
print(f"\nSaved: {XLSX}")
print(f"New max_row: {ws.max_row}")

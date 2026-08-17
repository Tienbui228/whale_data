#!/usr/bin/env python3
"""
Backfill APR DAILY cols 27/28/29 (pos_r/acc_r/gLSR) and col 8 (taker) from export CSV.

Root cause: build_case.py wrote o/h/l/c/vol correctly but did NOT write LSR cols.
Taker (col8) also missing for 08-10 to 08-16.
Export has APRUSDT with lsr_pos_r/acc_r/lsr_global_r for Jul-Aug 2026.

Strategy: only overwrite cells that are currently None — do not touch correctly-filled cells.
validate_written_pack checks last 30 rows; July+August export covers that window.

Run: python _probe_apr_backfill_lsr_20260817.py
"""
import csv
import sys
import io
import math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import openpyxl
from openpyxl.cell.cell import MergedCell

sys.path.insert(0, str(Path(__file__).parent))
from scripts.case_guard import validate_written_pack

WHALE      = Path(r"D:\Data back test\whale_data")
CASE_DIR   = WHALE / "docs" / "case_files"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
FIRST_DATA_ROW = 3
SYM = "APRUSDT"
APR_PATH = CASE_DIR / "CASE_APR.xlsx"

# Load export for APR
export = {}
for ym in ["2026-08", "2026-07", "2026-06"]:
    p = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
    if not p.exists(): continue
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["symbol"] == SYM:
                export[row["date"]] = row

print(f"[export] {SYM}: {len(export)} rows  ({min(export) if export else '—'} → {max(export) if export else '—'})")

def _flt(v):
    if v is None or str(v).strip() == "": return None
    try:
        x = float(v); return None if math.isnan(x) else x
    except (ValueError, TypeError): return None


wb = openpyxl.load_workbook(str(APR_PATH), data_only=False)
ws = wb["DAILY"]
max_row = ws.max_row

# Scan and patch
n_lsr_written   = 0
n_taker_written = 0
n_no_export     = 0
details = []

for r in range(FIRST_DATA_ROW, max_row + 1):
    date_v = ws.cell(r, 1).value
    if not date_v or not isinstance(date_v, str): continue
    csv_row = export.get(str(date_v))
    if csv_row is None:
        n_no_export += 1
        continue

    changed = []

    # Write taker (col8) only if currently None
    if ws.cell(r, 8).value is None:
        tak_raw = _flt(csv_row.get("taker_buy_pct", ""))
        if tak_raw is not None:
            ws.cell(r, 8).value = round(tak_raw * 100, 6)  # fraction → percent
            changed.append(f"col8_taker={ws.cell(r,8).value:.2f}%")
            n_taker_written += 1

    # Write pos_r (col27) only if currently None
    pos_wrote = False
    if ws.cell(r, 27).value is None:
        pos_v = _flt(csv_row.get("lsr_pos_r", ""))
        if pos_v is not None:
            ws.cell(r, 27).value = pos_v
            changed.append(f"pos_r={pos_v:.4f}")
            n_lsr_written += 1
            pos_wrote = True

    # Write acc_r (col28)
    if ws.cell(r, 28).value is None:
        acc_v = _flt(csv_row.get("lsr_acc_r", ""))
        if acc_v is not None:
            ws.cell(r, 28).value = acc_v
            if not pos_wrote: n_lsr_written += 1
            changed.append(f"acc_r={acc_v:.4f}")

    # Write gLSR (col29)
    if ws.cell(r, 29).value is None:
        gls_v = _flt(csv_row.get("lsr_global_r", ""))
        if gls_v is not None:
            ws.cell(r, 29).value = gls_v
            changed.append(f"gLSR={gls_v:.4f}")

    if changed:
        details.append((date_v, r, changed))

print(f"\n[patch] rows with export data: {len(export) - n_no_export}  /  no export: {n_no_export}")
print(f"  lsr rows written (pos_r+): {n_lsr_written}")
print(f"  taker rows written:        {n_taker_written}")

if details:
    print(f"\n  Sample changes (last 15):")
    print(f"  {'date':>12}  {'row':>5}  changes")
    for date_v, r, ch in details[-15:]:
        print(f"  {date_v:>12}  {r:>5}  {', '.join(ch)}")

wb.save(str(APR_PATH))
print(f"\n[save] {APR_PATH.name}")

try:
    validate_written_pack(APR_PATH)
    print(f"[validate] PASS ✓")
except RuntimeError as e:
    print(f"[validate] FAIL:\n  {e}")

# Spot-check: print last 5 rows with all patched cols
print(f"\n[verify] Last 5 data rows after patch:")
wb2 = openpyxl.load_workbook(str(APR_PATH), data_only=True, read_only=True)
ws2 = wb2["DAILY"]
mr2 = ws2.max_row
print(f"  {'date':>12}  {'col8_taker':>12}  {'col27_pos':>10}  {'col28_acc':>10}  {'col29_gLSR':>10}")
for r in range(max(3, mr2 - 4), mr2 + 1):
    d  = ws2.cell(r, 1).value
    t  = ws2.cell(r, 8).value
    p  = ws2.cell(r, 27).value
    a  = ws2.cell(r, 28).value
    g  = ws2.cell(r, 29).value
    def f(v): return f"{v:.4f}" if isinstance(v, (int,float)) else "—"
    tv = f"{t:.2f}%" if isinstance(t, (int,float)) else "—"
    print(f"  {str(d):>12}  {tv:>12}  {f(p):>10}  {f(a):>10}  {f(g):>10}")
wb2.close()
print("\nDUNG.")

#!/usr/bin/env python3
"""H4: Update CASE_BANK.xlsx — machine-verified data from H1/H2/H3 probes.

Adds probe-verified rows to CASE sheet (bottom).
Fills T+14 row in OUTCOME sheet (machine columns only).
Leaves: verdict, on-chain, nhận định for operator.

Source: _probe_bank_h1h2h3_20260804.py (04/08/2026)
"""
import io, sys
from pathlib import Path
import openpyxl
from openpyxl.styles import PatternFill, Font

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_BANK.xlsx")

wb = openpyxl.load_workbook(XLSX)

# ─── CASE sheet — append machine-verified block ───────────────────────────────
ws_case = wb["CASE"]

# Find last used row
last_row = ws_case.max_row
while last_row > 0 and all(ws_case.cell(last_row, c).value is None for c in range(1, 5)):
    last_row -= 1

next_row = last_row + 2  # blank separator

header_fill = PatternFill("solid", fgColor="D4A843")  # amber
header_font = Font(bold=True)

def append_section_header(ws, row, text):
    cell = ws.cell(row, 1, text)
    cell.fill = header_fill
    cell.font = header_font

def append_kv(ws, row, key, val):
    ws.cell(row, 1, key)
    ws.cell(row, 2, str(val))

append_section_header(ws_case, next_row, "=== PROBE-VERIFIED — H1/H2/H3 (04/08/2026) ===")
next_row += 1

machine_rows = [
    ("px_T0 probe-verified",         "0.03773 (freshwatch 10/07 px_avg)"),
    ("px_max [1h spike native]",     "0.67205 USDT — 27/07 06:00 UTC (fapi 1h high, vol 299M USDT)"),
    ("px_max [daily avg basis]",     "0.37632 USDT — 26/07 freshwatch avg (truoc da dung lam px_max)"),
    ("px_max [close basis]",         "0.41958 USDT — 27/07 close (fapi 1h)"),
    ("markup T0→spike_high",         "+1681% (0.03773→0.67205)"),
    ("markup T0→daily_avg_max",      "+897% (0.03773→0.37632)"),
    ("OI PRE range (25/06-09/07)",   "4.31M→4.73M FLAT — khong xay duoc truoc markup"),
    ("OI MARKUP peak (19/07)",       "26.56M USD (tu 4.47M T0: +22M trong 9 ngay)"),
    ("MM_build_VWAP",                "0.03943 USDT (daily 25/06-12/07 approx)"),
    ("MM_exit_VWAP",                 "0.19710 USDT (1h klines 19-21/07, pos_r sap window)"),
    ("MM_multiple_thuc",             "5.00x (+400%) = exit_VWAP / build_VWAP"),
    ("MM_funding_PnL_PRE_MARKUP",    "$26K-$43K total (27/06-19/07, 3-5M long, khong dang ke)"),
    ("gLSR_min_POST",                "0.390 — 20/07 (ngay sau pos_r crash)"),
    ("gLSR_slope_flip_sustained",    "28/07 (sau spike 27/07) — da tang lien tuc len 1.726 ngay 03/08)"),
    ("pos_r_flat_window",            "1.30-1.36 (23-27/07) — khi px tang 0.247→0.376 (+42.7%)"),
    ("pos_r_crash_window",           "19-20/07: 1.61→1.09 (MM phan phoi trong khi px van tang)"),
    ("SOURCE",                       "_probe_bank_h1h2h3_20260804.py run 04/08/2026"),
]

for key, val in machine_rows:
    append_kv(ws_case, next_row, key, val)
    next_row += 1

print(f"[CASE] Appended {len(machine_rows)} machine-verified rows from row {last_row + 2}")

# ─── OUTCOME sheet — fill T+14 (machine columns) ─────────────────────────────
ws_out = wb["OUTCOME"]

# Find T+14 row
t14_row = None
for row in ws_out.iter_rows():
    if row[0].value == "T+14":
        t14_row = row[0].row
        break

if t14_row:
    # px (col C=3), ret_pct (col D=4), oi_usd (col F=6), gLSR (col G=7), dien_bien (col H=8)
    ws_out.cell(t14_row, 3, 0.28339)       # px — freshwatch 24/07 px_avg
    ws_out.cell(t14_row, 4, "+651.1%")      # ret_pct from T0 (0.03773)
    ws_out.cell(t14_row, 5, "peak→down")    # drawup_drawdown: peaked ~26/07, declining by 24/07
    ws_out.cell(t14_row, 6, 51.12e6)       # oi_usd = 51.12M
    ws_out.cell(t14_row, 7, 0.500)          # gLSR
    ws_out.cell(t14_row, 8, "px van cao (24/07 avg 0.283), OI 51M, gLSR 0.500 — POST dang sap")
    print(f"[OUTCOME] T+14 (row {t14_row}) updated: px=0.28339, ret=+651.1%, OI=51.12M, gLSR=0.500")
else:
    print("[OUTCOME] T+14 row NOT FOUND — check sheet")

# Leave T+30 (09/08) and T+60 blank — still in future

wb.save(XLSX)
print(f"\nSaved: {XLSX}")
print("H4 DONE — operator phan: verdict_check cot I, T+30/T+60 khi den han.")

#!/usr/bin/env python3
"""Check export CSV for APRUSDT: does lsr_pos_r/acc_r/global_r exist?
Also check col15 in CASE_APR for rows 08-10→08-16 (did old EXPORT_COL_MAP write LSR to col15?)
"""
import csv
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
CASE_DIR   = Path(r"D:\Data back test\whale_data\docs\case_files")
SYM = "APRUSDT"

# [A] Check freshwatch_daily export for APRUSDT
print("[A] APRUSDT in freshwatch_daily export (last 20 rows)")
apr_rows = []
for ym in ["2026-08", "2026-07"]:
    p = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
    if not p.exists(): print(f"  missing: {p}"); continue
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["symbol"] == SYM:
                apr_rows.append(row)

apr_rows.sort(key=lambda r: r["date"])
print(f"  Found {len(apr_rows)} rows for {SYM}")
if apr_rows:
    # Print header keys
    print(f"  Fields: {list(apr_rows[0].keys())}")
    print(f"\n  Last 10 rows: date / px_avg / oi_usd / lsr_pos_r / lsr_acc_r / lsr_global_r / taker_buy_pct / vol_quote")
    for r in apr_rows[-10:]:
        print(f"    {r['date']}  px={r.get('px_avg','?'):>10}  "
              f"oi={r.get('oi_usd','?'):>14}  "
              f"pos={r.get('lsr_pos_r','?'):>8}  "
              f"acc={r.get('lsr_acc_r','?'):>8}  "
              f"gLSR={r.get('lsr_global_r','?'):>8}  "
              f"tak={r.get('taker_buy_pct','?'):>8}  "
              f"vol={r.get('vol_quote','?'):>14}")
else:
    print(f"  ** APRUSDT NOT FOUND in freshwatch_daily export **")
    print(f"  → APR is not in freshwatch perp universe → LSR akan selalu kosong")

# [B] Check CASE_APR cols 14-17 (data_ok/low_conf area) and col 4-6 (h/l/c area)
# to see if old EXPORT_COL_MAP wrote LSR to col15, vol to col4, taker to col5
print("\n[B] CASE_APR.xlsx — col4/5/6/7/8/15/16/17 for last 10 rows")
wb = openpyxl.load_workbook(str(CASE_DIR / "CASE_APR.xlsx"), data_only=True, read_only=True)
ws = wb["DAILY"]
max_row = ws.max_row
print(f"  {'date':>12}  {'c4_h':>12}  {'c5_l':>12}  {'c6_c':>12}  {'c7_vol':>14}  {'c8_tak':>10}  {'c15_dok':>10}  {'c16_lc':>10}  {'c17_ret':>10}")
for r in range(max(3, max_row - 9), max_row + 1):
    c1 = ws.cell(r, 1).value
    c4 = ws.cell(r, 4).value
    c5 = ws.cell(r, 5).value
    c6 = ws.cell(r, 6).value
    c7 = ws.cell(r, 7).value
    c8 = ws.cell(r, 8).value
    c15 = ws.cell(r, 15).value
    c16 = ws.cell(r, 16).value
    c17 = ws.cell(r, 17).value
    def f(v, w=12):
        if isinstance(v, float): return f"{v:.4g}"
        return str(v)[:w] if v is not None else "—"
    print(f"  {str(c1):>12}  {f(c4):>12}  {f(c5):>12}  {f(c6):>12}  {f(c7):>14}  "
          f"{f(c8):>10}  {f(c15):>10}  {f(c16):>10}  {f(c17):>10}")
wb.close()

# [C] Check freshwatch_symbols.txt for APR
fw_path = Path(r"D:\Data back test\whale_data\data\config\freshwatch_symbols.txt")
fw_set = set(l.strip() for l in fw_path.read_text(encoding="utf-8").splitlines() if l.strip())
print(f"\n[C] 'APRUSDT' in freshwatch_symbols.txt: {'APRUSDT' in fw_set}")
print(f"    'APR' in freshwatch_symbols.txt:      {'APR' in fw_set}")

print("\nDUNG.")

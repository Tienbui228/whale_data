#!/usr/bin/env python3
"""A4 probe: BANK pre-29/07 DAILY vol + taker rows vs CSV — gather facts for analysis note."""
import sys, csv
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import openpyxl

CASE_DIR   = Path(__file__).parent / "docs" / "case_files"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")

def load_csv(symbol):
    rows = {}
    for ym in ("2026-05","2026-06","2026-07","2026-08"):
        p = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("symbol","").upper() != symbol.upper():
                    continue
                d = r.get("date","")
                if d:
                    rows[d] = r
    return rows

def flt(v):
    try: return float(v)
    except: return None

for wb_name, symbol in [("CASE_BANK.xlsx","BANKUSDT"), ("CASE_BR.xlsx","BRUSDT")]:
    path = CASE_DIR / wb_name
    csv_data = load_csv(symbol)
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb["DAILY"]

    print(f"\n{'='*76}")
    print(f"{wb_name}  symbol={symbol}")
    print(f"  {'date':<12} {'xl_taker':>10} {'csv_taker':>10} {'taker_d':>10}  "
          f"{'xl_vol':>18} {'csv_vol':>18} {'vol_d%':>8}  note")
    print(f"  {'-'*110}")

    frac_count = 0
    for row in ws.iter_rows(min_row=3, values_only=True):
        date_v  = row[0] if len(row) > 0 else None
        taker_v = row[4] if len(row) > 4 else None
        vol_v   = row[3] if len(row) > 3 else None
        if date_v is None:
            continue
        date_s = date_v.strftime("%Y-%m-%d") if isinstance(date_v, datetime) else str(date_v)[:10]
        if not date_s or date_s == "None":
            continue

        is_frac = isinstance(taker_v, (int, float)) and 0 < taker_v < 1.0
        if is_frac:
            frac_count += 1

        cv = csv_data.get(date_s, {})
        ct   = flt(cv.get("taker_buy_pct"))
        cvol = flt(cv.get("vol_quote"))

        taker_d = abs(taker_v - ct) if (isinstance(taker_v,(int,float)) and ct is not None) else None
        vol_d_pct = abs(vol_v/cvol - 1)*100 if (isinstance(vol_v,(int,float)) and cvol and cvol>0 and vol_v is not None) else None

        note = ""
        if isinstance(vol_v,(int,float)):
            if vol_v == round(vol_v, -6) and vol_v >= 1e6:
                note = "ROUND_1M"
            if vol_v == 1_900_000_000:
                note = "PLACEHOLDER_1.9B"

        t_s  = f"{taker_v:.6f}" if isinstance(taker_v,(int,float)) else str(taker_v)
        ct_s = f"{ct:.6f}"     if ct is not None else "N/A"
        td_s = f"{taker_d:.6f}" if taker_d is not None else "N/A"
        v_s  = f"{vol_v:,.0f}" if isinstance(vol_v,(int,float)) else str(vol_v)
        cv_s = f"{cvol:,.0f}"  if cvol is not None else "N/A"
        vd_s = f"{vol_d_pct:.2f}%" if vol_d_pct is not None else "N/A"

        frac_tag = " ← FRAC" if is_frac else ""
        print(f"  {date_s:<12} {t_s:>10} {ct_s:>10} {td_s:>10}  "
              f"{v_s:>18} {cv_s:>18} {vd_s:>8}  {note}{frac_tag}")

    wb.close()
    print(f"\n  Total fraction rows (0<taker<1): {frac_count}")

#!/usr/bin/env python3
"""A1: 15 samples BANK+BR taker vs freshwatch CSV — exact delta, verdict.
   7 samples BANK (30 frac rows), 8 samples BR (60 frac rows) = 15 total.
"""
import sys, csv, math
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import openpyxl

CASE_DIR   = Path(__file__).parent / "docs" / "case_files"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
CHECKS = [
    ("CASE_BANK.xlsx", "BANKUSDT", 7),
    ("CASE_BR.xlsx",   "BRUSDT",   8),
]

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
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

any_fail = False
total_samples = 0

for wb_name, symbol, n_samples in CHECKS:
    path = CASE_DIR / wb_name
    csv_data = load_csv(symbol)

    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb["DAILY"]
    frac_rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        date_v  = row[0] if len(row) > 0 else None
        taker_v = row[4] if len(row) > 4 else None
        if date_v is None or not isinstance(taker_v, (int, float)):
            continue
        date_s = date_v.strftime("%Y-%m-%d") if isinstance(date_v, datetime) else str(date_v)[:10]
        if not (0 < taker_v < 1.0):
            continue
        frac_rows.append((date_s, taker_v))
    wb.close()

    n = len(frac_rows)
    # Evenly-spaced indices
    if n <= n_samples:
        idxs = list(range(n))
    else:
        step = (n - 1) / (n_samples - 1)
        idxs = [round(i * step) for i in range(n_samples)]
    samples = [frac_rows[i] for i in idxs]

    print(f"\n{'='*76}")
    print(f"{wb_name}  symbol={symbol}  total_frac={n}  samples={len(samples)}")
    print(f"{'='*76}")
    print(f"  {'date':<12} {'xlsx_taker':>14} {'csv_taker':>14}  {'delta':>12}  verdict")
    print(f"  {'-'*70}")

    wb_pass = True
    for d, t in samples:
        cv = csv_data.get(d, {})
        ct = flt(cv.get("taker_buy_pct")) if cv else None

        if ct is None:
            verdict = "CSV_N/A"
            wb_pass = False; any_fail = True
            delta_s = "N/A"
        else:
            delta = abs(t - ct)
            delta_s = f"{delta:.8f}"
            if delta == 0.0:
                verdict = "OK exact"
            elif delta < 0.0001:
                verdict = f"OK Δ<0.0001"
            elif delta < 0.001:
                verdict = f"WARN Δ<0.001"
            else:
                verdict = f"LỆCH Δ={delta:.6f}"
                wb_pass = False; any_fail = True

        ct_s = f"{ct:.8f}" if ct is not None else "N/A"
        print(f"  {d:<12} {t:>14.8f} {ct_s:>14}  {delta_s:>12}  {verdict}")
        total_samples += 1

    print(f"  → {wb_name}: {'PASS' if wb_pass else 'FAIL'}")

print(f"\n{'='*76}")
print(f"TOTAL samples: {total_samples}  OVERALL: {'ALL PASS' if not any_fail else 'CÓ FAIL'}")

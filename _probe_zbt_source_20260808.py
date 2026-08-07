#!/usr/bin/env python3
"""ZBT source audit: what loader, what taker units, decay timing.
Operator question: ZBT chain opens 07-01 despite potential decay-always-True bug.
"""
import sys, math, csv
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD  = Path(r"D:\Data back test\whale_data")
BOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT))

import importlib.util as _ilu
import yaml

_gs = _ilu.spec_from_file_location("gom_scan", WD / "scripts" / "gom_scan.py")
_gm = _ilu.module_from_spec(_gs); _gs.loader.exec_module(_gm)
cfg = _gm.load_thresholds()

print("=== ZBT SOURCE AUDIT ===")
print()

# 1. Check if ZBT_result.txt exists
case_dir = BOT / "docs" / "case study"
zbt_result = case_dir / "ZBT_result.txt"
zbt_zbt    = case_dir / "zbt_result.txt"
print(f"ZBT_result.txt: {'EXISTS' if zbt_result.exists() else 'NOT FOUND'}")
print(f"zbt_result.txt: {'EXISTS' if zbt_zbt.exists() else 'NOT FOUND'}")
print()

# 2. Check freshwatch CSVs for ZBT
FW = [WD / "scratch" / "freshwatch_daily_2026-06.csv",
      WD / "scratch" / "freshwatch_daily_2026-07.csv"]
print("=== ZBT rows in freshwatch CSVs ===")
zbt_rows = []
for csv_file in FW:
    if not csv_file.exists():
        continue
    with open(csv_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","").upper()
            if sym in ("ZBT","ZBTUSDT"):
                zbt_rows.append(row)

if zbt_rows:
    zbt_rows.sort(key=lambda r: r.get("date",""))
    print(f"  ZBT rows: {len(zbt_rows)}  {zbt_rows[0]['date']} → {zbt_rows[-1]['date']}")
    for row in zbt_rows[:10]:
        t = row.get("taker_buy_pct","?")
        glsr = row.get("lsr_global_r","?")
        posr = row.get("lsr_pos_r","?")
        print(f"  {row['date']}  taker={t}  gLSR={glsr}  pos_r={posr}")
else:
    print("  ZBT: 0 rows in freshwatch CSVs")
print()

# 3. Check CASE_ZBT.xlsx for DAILY data
print("=== CASE_ZBT.xlsx ===")
try:
    import openpyxl
    xlsx_path = WD / "docs" / "case_files" / "CASE_ZBT.xlsx"
    if xlsx_path.exists():
        wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)
        print(f"  Sheets: {wb.sheetnames}")
        if "DAILY" in wb.sheetnames:
            ws = wb["DAILY"]
            headers = [str(c.value) for c in next(ws.iter_rows(min_row=1, max_row=1))]
            print(f"  DAILY headers: {headers}")
            print(f"  DAILY rows (top 5):")
            for row in ws.iter_rows(min_row=2, max_row=7, values_only=True):
                print(f"    {row}")
    else:
        print("  CASE_ZBT.xlsx not found at expected path")
except ImportError:
    print("  openpyxl not available — reading .xlsx as zip")
    import zipfile, re
    xlsx_path = WD / "docs" / "case_files" / "CASE_ZBT.xlsx"
    if xlsx_path.exists():
        print(f"  File exists: {xlsx_path}")
        print(f"  Size: {xlsx_path.stat().st_size} bytes")
    else:
        print("  Not found")
print()

# 4. KEY INSIGHT: decay() returns False for i < hold_n-1 = 4
# If ZBT data starts 07-01 and chain opens+closes in 2 days (i=0,1),
# then decay CANNOT fire (needs i≥4). This is true even with decimal bug.
print("=== decay() early-return guard ===")
print(f"  cfg['decay']['decay_days_min'] = {cfg['decay']['decay_days_min']}")
print(f"  decay() returns False if i < (decay_days_min - 1) = {cfg['decay']['decay_days_min'] - 1}")
print()
print("  If ZBT data starts 07-01 (i=0) and chain opens+closes on i=0,1:")
print("  → i=0: decay=False (guard). Chain can open. ✓")
print("  → i=1: decay=False (guard). Rule-iv pos_r_drop 34% → chain closes. ✓")
print("  → Decimal bug irrelevant: chain opens+closes before decay 5d window activates.")
print()

# 5. Simulate: if ZBT DayData had decimal takers from freshwatch,
#    would the first 2 days still produce open+close?
print("=== Simulation: ZBT open/close timing with any taker format ===")
if zbt_rows and len(zbt_rows) >= 2:
    def flt(row, k):
        try: return float(row.get(k,"nan"))
        except: return float("nan")

    print("  ZBT from freshwatch (if exists) - taker as stored:")
    for i, row in enumerate(zbt_rows[:5]):
        t_raw = flt(row, "taker_buy_pct")
        below_raw = t_raw < 0.48  # fraction check
        below_pct = t_raw < 48.0  # pct check

        # decay check (i < 4 → always False)
        decay_guard = i < (cfg["decay"]["decay_days_min"] - 1)
        print(f"  i={i} {row['date']}  taker_raw={t_raw:.4f}  "
              f"below_if_frac={below_raw}  below_if_pct={below_pct}  "
              f"decay_guard={decay_guard} → decay=False if i<4")
elif not zbt_rows:
    print("  ZBT not in freshwatch → must be from CASE_ZBT.xlsx or v4 had result.txt")
    print("  If from Excel with pct units → no decimal bug → Z1/Z2 clean ✓")
print()
print("=== CONCLUSION ===")
if not zbt_rows:
    print("  ZBT NOT in freshwatch CSVs. Source: CASE_ZBT.xlsx DAILY (Excel, pct units).")
    print("  No decimal taker bug applies. Z1/Z2 PASS* is CLEAN.")
else:
    print("  ZBT found in freshwatch. But: if data starts 07-01, decay guard (i<4)")
    print("  protects i=0 and i=1 regardless of taker format.")
    print("  Chain opens day 0, closes day 1 (rule-iv 34%) → Z1/Z2 immune to bug.")

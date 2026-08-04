#!/usr/bin/env python3
"""Probe BR scratch data + CASE_BR structure + R5/R6."""
import csv, io, sys
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── scratch/BR_daily.csv ──────────────────────────────────────────────────────
scratch = Path(r"D:\Data back test\whale_data\scratch\BR_daily.csv")
print("=== scratch/BR_daily.csv ===")
if scratch.exists():
    df = pd.read_csv(scratch)
    print(f"Rows: {len(df)}, Cols: {list(df.columns)}")
    print(df.to_string())
else:
    print("NOT FOUND")

# ── CASE_BR exists? ────────────────────────────────────────────────────────────
print("\n=== CASE files for BR ===")
case_dir = Path(r"D:\Data back test\whale_data\docs\case_files")
br_files = list(case_dir.glob("*BR*")) + list(case_dir.glob("*br*"))
print(f"BR case files: {br_files}")

# ── VPS tape: check if BR tape is on VPS ──────────────────────────────────────
print("\n=== VPS tape check (via SSH) ===")
import subprocess
try:
    result = subprocess.run(
        ['ssh', 'root@5.223.67.21',
         'ls /root/Data_back_test/whale_data/data/raw/tape/ 2>/dev/null | head -20; '
         'find /root/Data_back_test/whale_data/data/raw/tape/ -name "*.parquet" 2>/dev/null | grep -i br | head -10'],
        capture_output=True, text=True, timeout=15
    )
    print(result.stdout or "(no output)")
    if result.stderr: print("stderr:", result.stderr[:200])
except Exception as e:
    print(f"SSH error: {e}")

# ── R5: IDOL comparison framework ────────────────────────────────────────────
print("\n=== R5 — IDOL vs BR so khuôn ===")
# Load IDOL freshwatch for comparison reference
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
idol_rows = {}
br_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        sym = r.get("symbol","")
        if sym == "IDOLUSDT": idol_rows[r["date"]] = r
        if sym == "BRUSDT": br_rows[r["date"]] = r

def gv(r, k):
    v = r.get(k,"")
    if v in ("",None): return None
    try: return float(v)
    except: return None

# IDOL pre-ignition profile (around Jun-Jul 2025, case open)
# IDOL case: T0 = ? — check CASE_IDOL if exists
idol_case = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_IDOL.xlsx")
import openpyxl
idol_t0 = None
if idol_case.exists():
    wb = openpyxl.load_workbook(idol_case)
    if "CASE" in wb.sheetnames:
        ws = wb["CASE"]
        for row in ws.iter_rows():
            if row[0].value and "T0" in str(row[0].value):
                print(f"IDOL T0 row: {[c.value for c in row[:5]]}")
                idol_t0 = row[1].value if len(row) > 1 else None
                break
    if "DAILY" in wb.sheetnames:
        ws = wb["DAILY"]
        # Get last few rows
        for r in range(max(3, ws.max_row-5), ws.max_row+1):
            d = ws.cell(r,1).value
            gl = ws.cell(r,17).value  # gLSR col Q
            pr = ws.cell(r,15).value  # pos_r col O
            ar = ws.cell(r,16).value  # acc_r col P
            oi = ws.cell(r,12).value  # oi_usd col L
            px = ws.cell(r,2).value   # px_avg col B
            if d:
                print(f"  IDOL {d}: px={px}, gLSR={gl}, pos_r={pr}, acc_r={ar}, OI={oi}")

# BR current state
print("\nBR current (03/08 - latest):")
r03 = br_rows.get("2026-08-03", {})
print(f"  px={gv(r03,'px_avg'):.6f}, gLSR={gv(r03,'lsr_global_r'):.4f}, pos_r={gv(r03,'lsr_pos_r'):.3f}, acc_r={gv(r03,'lsr_acc_r'):.3f}, OI={gv(r03,'oi_usd')/1e6:.3f}M" if gv(r03,'px_avg') else "  no data")

# IDOL at pre-ignition (check months before case)
print("\nIDOL recent dates (for comparison):")
for d in sorted(idol_rows)[-10:]:
    r = idol_rows[d]
    px = gv(r,'px_avg')
    gl = gv(r,'lsr_global_r')
    pr = gv(r,'lsr_pos_r')
    ar = gv(r,'lsr_acc_r')
    oi = gv(r,'oi_usd')
    fn = gv(r,'funding_n')
    if px:
        oi_s = f"{oi/1e6:.3f}M" if oi else "—"
        print(f"  {d}: px={px:.5f}, gLSR={gl:.4f if gl else '—'}, pos_r={pr:.3f if pr else '—'}, acc_r={ar:.3f if ar else '—'}, OI={oi_s}, fn={int(fn) if fn else '—'}")

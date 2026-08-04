#!/usr/bin/env python3
"""Probe: collect MM-ECON data for all campaigns.

For each token: OI series, pos_r series, px series, vol — to compute:
- OI_base (pre-markup), OI_peak (at pos_r collapse), OI_multiple
- exit_VWAP (vol-weighted px during pos_r crash window)
- px_multiple (px_max / px_T0)
- Build window dates
"""
import csv, io, json, sys
from pathlib import Path
import pandas as pd
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# ── Load all freshwatch data ──────────────────────────────────────────────────
all_fw = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        sym = r.get("symbol", "")
        if sym not in all_fw:
            all_fw[sym] = {}
        all_fw[sym][r["date"]] = r

tokens_fw = sorted(all_fw.keys())
print(f"Tokens in freshwatch: {len(tokens_fw)}")
print(f"All symbols: {tokens_fw}")

# ── Campaigns of interest ──────────────────────────────────────────────────────
campaigns = {
    # symbol: {T0, markup_start, pos_collapse_window, notes}
    "AKUSDT":     {"name":"AKE",     "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "BANKUSDT":   {"name":"BANK",    "T0":"2026-07-10", "markup_start":"2026-07-10", "collapse":"2026-07-19"},
    "IDOLUSDT":   {"name":"IDOL",    "T0":"2026-07-04", "markup_start":"2026-07-04", "collapse":"?"},
    "TUTUSDT":    {"name":"TUT",     "T0":"2026-07-22", "markup_start":"2026-07-22", "collapse":"ongoing"},
    "ESPORTSUSDT":{"name":"ESPORTS", "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "CLOUSDT":    {"name":"CLO",     "T0":"?",          "markup_start":"?",   "collapse":"?"},
    # M2 extended
    "BASUSDT":    {"name":"BAS",     "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "TAGUSDT":    {"name":"TAG",     "T0":"2026-07-10", "markup_start":"2026-07-10", "collapse":"ongoing"},
    "POWERUSDT":  {"name":"POWER",   "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "BASEDUSDT":  {"name":"BASED",   "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "BULLAUSDT":  {"name":"BULLA",   "T0":"?",          "markup_start":"?",   "collapse":"?"},
    "BTWUSDT":    {"name":"BTW",     "T0":"?",          "markup_start":"?",   "collapse":"?"},
}

# ── For each token: get full series ──────────────────────────────────────────
print(f"\n{'='*70}")
print("TOKEN DATA SUMMARY")
print(f"{'='*70}")

for sym, meta in campaigns.items():
    rows = all_fw.get(sym, {})
    if not rows:
        print(f"\n{meta['name']:8} ({sym}): NOT IN FRESHWATCH")
        continue

    dates = sorted(rows.keys())
    print(f"\n{meta['name']:8} ({sym}): {len(rows)} rows ({dates[0]} → {dates[-1]})")

    # Get px, OI, pos_r series
    series = []
    for d in dates:
        r = rows[d]
        series.append({
            'd': d,
            'px': gv(r,'px_avg'),
            'vol': gv(r,'vol_quote'),
            'oi': gv(r,'oi_usd'),
            'pr': gv(r,'lsr_pos_r'),
            'ar': gv(r,'lsr_acc_r'),
            'gl': gv(r,'lsr_global_r'),
            'fav': gv(r,'funding_avg'),
            'fn': gv(r,'funding_n'),
        })

    # OI stats
    oi_vals = [(x['d'], x['oi']) for x in series if x['oi']]
    if oi_vals:
        oi_min = min(oi_vals, key=lambda x: x[1])
        oi_max = max(oi_vals, key=lambda x: x[1])
        print(f"  OI: min={oi_min[1]/1e6:.3f}M ({oi_min[0]}) → max={oi_max[1]/1e6:.3f}M ({oi_max[0]})")
        oi_mult = oi_max[1]/oi_min[1]
        print(f"  OI_multiple (min→max): {oi_mult:.2f}×")

    # pos_r stats + min (pos_r collapse = local min after peak)
    pr_vals = [(x['d'], x['pr']) for x in series if x['pr']]
    if pr_vals:
        pr_min = min(pr_vals, key=lambda x: x[1])
        pr_max = max(pr_vals, key=lambda x: x[1])
        print(f"  pos_r: min={pr_min[1]:.3f} ({pr_min[0]}) max={pr_max[1]:.3f} ({pr_max[0]})")

    # gLSR stats
    gl_vals = [(x['d'], x['gl']) for x in series if x['gl']]
    if gl_vals:
        gl_min = min(gl_vals, key=lambda x: x[1])
        gl_max = max(gl_vals, key=lambda x: x[1])
        print(f"  gLSR: min={gl_min[1]:.4f} ({gl_min[0]}) max={gl_max[1]:.4f} ({gl_max[0]})")

    # px stats
    px_vals = [(x['d'], x['px']) for x in series if x['px']]
    if px_vals:
        px_min = min(px_vals, key=lambda x: x[1])
        px_max = max(px_vals, key=lambda x: x[1])
        print(f"  px: min={px_min[1]:.6f} ({px_min[0]}) max={px_max[1]:.6f} ({px_max[0]})")
        px_mult_total = px_max[1]/px_min[1]
        print(f"  px_multiple (min→max overall): {px_mult_total:.1f}×")

    # Large pos_r drops (potential collapse windows)
    drops = []
    for i in range(1, len(series)):
        if series[i]['pr'] and series[i-1]['pr']:
            drop = (series[i]['pr'] - series[i-1]['pr']) / series[i-1]['pr']
            if drop < -0.10:  # >10% drop
                drops.append((series[i]['d'], series[i-1]['pr'], series[i]['pr'], drop))
    if drops:
        print(f"  Large pos_r drops (>10%/d):")
        for d, p0, p1, dr in drops[:5]:
            print(f"    {d}: {p0:.3f}→{p1:.3f} ({dr*100:+.1f}%)")

    # Vol peak
    vol_vals = [(x['d'], x['vol']) for x in series if x['vol']]
    if vol_vals:
        vol_max = max(vol_vals, key=lambda x: x[1])
        print(f"  Vol peak: {vol_max[1]/1e6:.1f}M ({vol_max[0]})")

    # Full series (compact)
    print(f"  Full series (last 20):")
    for x in series[-20:]:
        px_s  = f"{x['px']:.5f}" if x['px'] else "—"
        oi_s  = f"{x['oi']/1e6:.2f}M" if x['oi'] else "—"
        pr_s  = f"{x['pr']:.3f}" if x['pr'] else "—"
        gl_s  = f"{x['gl']:.4f}" if x['gl'] else "—"
        vol_s = f"{x['vol']/1e6:.1f}M" if x['vol'] else "—"
        fav_s = f"{x['fav']:.5f}" if x['fav'] else "—"
        print(f"    {x['d']}: px={px_s} OI={oi_s} pos_r={pr_s} gLSR={gl_s} vol={vol_s} f={fav_s}")

# ── CASE files available ───────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("CASE FILES AVAILABLE")
case_files = sorted(CASE_DIR.glob("CASE_*.xlsx"))
print(f"Files: {[f.name for f in case_files]}")

# Read CASE_BANK OUTCOME for known MM numbers
bank_case = CASE_DIR / "CASE_BANK.xlsx"
if bank_case.exists():
    print(f"\nCASE_BANK OUTCOME sheet:")
    wb = openpyxl.load_workbook(bank_case)
    if "OUTCOME" in wb.sheetnames:
        ws = wb["OUTCOME"]
        for r in range(1, ws.max_row+1):
            a, b, c = ws.cell(r,1).value, ws.cell(r,2).value, ws.cell(r,3).value
            if a: print(f"  {a} | {b} | {c}")

# Check CASE_IDOL
idol_case = CASE_DIR / "CASE_IDOL.xlsx"
if idol_case.exists():
    print(f"\nCASE_IDOL OUTCOME sheet:")
    wb = openpyxl.load_workbook(idol_case)
    if "OUTCOME" in wb.sheetnames:
        ws = wb["OUTCOME"]
        for r in range(1, min(ws.max_row+1, 30)):
            a, b = ws.cell(r,1).value, ws.cell(r,2).value
            if a: print(f"  {a} | {b}")
    # Also check DAILY for T0 date
    if "DAILY" in wb.sheetnames:
        ws = wb["DAILY"]
        print(f"  IDOL DAILY: max_row={ws.max_row}")
        for r in range(3, 6):
            print(f"    row {r}: date={ws.cell(r,1).value}, px={ws.cell(r,2).value}, gLSR={ws.cell(r,17).value}")

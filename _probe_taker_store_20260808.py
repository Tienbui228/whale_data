#!/usr/bin/env python3
"""Probe: taker_buy_pct units in freshwatch daily CSV (the store that --daily will consume).
Reports min/max/sample for 5 symbols × 7 most recent days.
"""
import sys, csv, math
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD = Path(r"D:\Data back test\whale_data")
FW = [
    WD / "scratch" / "freshwatch_daily_2026-06.csv",
    WD / "scratch" / "freshwatch_daily_2026-07.csv",
]

PROBE_SYMS = ["PARTI", "TAG", "AKE", "BANK", "BULLA"]

print("=== TAKER_BUY_PCT in freshwatch CSV (the --daily store) ===")
print()

# Load all rows for probe symbols
rows_by_sym = defaultdict(list)
for csv_file in FW:
    if not csv_file.exists():
        print(f"  MISSING: {csv_file}")
        continue
    with open(csv_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol", "").upper().replace("USDT", "")
            if sym in PROBE_SYMS:
                rows_by_sym[sym].append(row)

print(f"  {'Symbol':>8}  {'N_rows':>7}  {'min_raw':>10}  {'max_raw':>10}  {'scale?':>8}")
print(f"  {'-'*8}  {'-'*7}  {'-'*10}  {'-'*10}  {'-'*8}")
all_raw_vals = []
for sym in PROBE_SYMS:
    rows = sorted(rows_by_sym[sym], key=lambda r: r.get("date", ""))
    vals = []
    for r in rows:
        try:
            v = float(r.get("taker_buy_pct", "nan"))
            if not math.isnan(v):
                vals.append(v)
                all_raw_vals.append(v)
        except (ValueError, TypeError):
            pass
    if vals:
        mx, mn = max(vals), min(vals)
        scale = "FRACTION" if mx <= 1.0 else ("PCT" if mx <= 100.0 else "UNKNOWN")
        print(f"  {sym:>8}  {len(vals):>7}  {mn:>10.5f}  {mx:>10.5f}  {scale:>8}")
    else:
        print(f"  {sym:>8}  {'0':>7}  {'N/A':>10}  {'N/A':>10}  {'NO DATA':>8}")

print()
# Last 7 dates across all symbols
print("=== Last 7 days per symbol (raw taker_buy_pct) ===")
for sym in PROBE_SYMS:
    rows = sorted(rows_by_sym[sym], key=lambda r: r.get("date", ""))[-7:]
    if not rows:
        print(f"  {sym}: no data")
        continue
    print(f"  {sym}:")
    for r in rows:
        t = r.get("taker_buy_pct", "?")
        try:
            tv = float(t)
            flag = "FRAC" if tv <= 1.0 else "PCT"
        except (ValueError, TypeError):
            tv = float("nan")
            flag = "?"
        print(f"    {r.get('date','?')}  taker_raw={t:>10}  → {flag}")

print()
print("=== GLOBAL summary (all probe symbols, all dates) ===")
if all_raw_vals:
    print(f"  N={len(all_raw_vals)}  min={min(all_raw_vals):.6f}  max={max(all_raw_vals):.6f}")
    pct_le1 = sum(1 for v in all_raw_vals if v <= 1.0)
    print(f"  Values ≤ 1.0: {pct_le1}/{len(all_raw_vals)}  ({100*pct_le1/len(all_raw_vals):.0f}%)")
    if max(all_raw_vals) <= 1.0:
        print("  CONCLUSION: ALL fraction format → gom_scan --daily must apply ×100 when loaded")
    elif min(all_raw_vals) > 1.0:
        print("  CONCLUSION: ALL percentage format → no conversion needed")
    else:
        print("  CONCLUSION: MIXED — taker scale inconsistent in CSV, RAISE required")
else:
    print("  No data found for probe symbols")

print()
print("=== gom_scan.py --daily status ===")
gs = WD / "scripts" / "gom_scan.py"
txt = gs.read_text(encoding="utf-8", errors="replace")
if "not yet implemented" in txt:
    # Find the line
    for i, line in enumerate(txt.splitlines()):
        if "not yet implemented" in line:
            print(f"  L{i+1}: {line.strip()}")
    print("  → --daily is NOT DEPLOYED. Tripwire must be in the loader when implemented.")
else:
    print("  --daily appears to have an implementation — check source.")

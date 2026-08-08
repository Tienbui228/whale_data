#!/usr/bin/env python3
# D1.2: Verify funding interval for 4 GOM-C beta fires + check C2_quiet with normalization.
import sys, math, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path("/root/Data_back_test/whale_data")
CONFIG_DIR = REPO / "data" / "config"

intervals_path = CONFIG_DIR / "funding_intervals.json"
if intervals_path.exists():
    intervals = json.load(open(str(intervals_path)))
else:
    intervals = {}
    print("WARNING: funding_intervals.json not found!")

BETA_FIRES = ["COOKIEUSDT", "CYSUSDT", "TSTUSDT", "TUTUSDT"]
BASE_NAMES = ["COOKIE", "CYS", "TST", "TUT"]

print("D1.2 -- Funding interval check for GOM-C beta fires (2026-08-07)")
print("=" * 70)
print(f"  {'Token':<12} {'interval_h':>10} {'f_avg_raw':>12} {'f_avg_8h_eq':>14} {'C2_raw':>8} {'C2_norm':>8} note")
print(f"  {'-'*80}")

sys.path.insert(0, str(REPO / "scripts"))
from fw_loader_utils import load_fw_csvs, taker_scale_check_df

STORE = REPO / "data" / "export"
df = load_fw_csvs(STORE, "2026-08-07", lookback_days=2)
df = taker_scale_check_df(df)
df_day = df[df["date"].astype(str) == "2026-08-07"] if not df.empty else df

C2_THR_8H = 1e-4

for sym, tok in zip(BETA_FIRES, BASE_NAMES):
    interval_h = intervals.get(sym, 8)
    row = df_day[df_day["symbol"] == sym]
    if row.empty:
        print(f"  {tok:<12} {interval_h:>10}h  no data for 2026-08-07")
        continue
    f_avg = float(row.iloc[0].get("funding_avg", math.nan))
    if math.isnan(f_avg):
        print(f"  {tok:<12} {interval_h:>10}h  funding_avg=NaN")
        continue
    f_8h_eq = f_avg * interval_h / 8
    c2_raw  = f_avg <= C2_THR_8H
    c2_norm = f_8h_eq <= C2_THR_8H
    note = ""
    if interval_h != 8:
        note = f"<-INTERVAL {interval_h}h"
        if c2_raw != c2_norm:
            note += " *** MISCLASSIFIED"
    print(f"  {tok:<12} {interval_h:>10}h {f_avg:>12.7f} {f_8h_eq:>14.7f} {str(c2_raw):>8} {str(c2_norm):>8} {note}")

print()
print("Note: C2_THR = 1e-4 (per 8h settlement)")
print("      f_avg_8h_eq = f_avg * interval_h / 8")
print("      MISCLASSIFIED = raw fire differs from normalized fire")

print()
print("All fw137 tokens with non-8h intervals:")
fw_path = CONFIG_DIR / "freshwatch_symbols.txt"
if fw_path.exists():
    fw_syms = [l.strip() for l in open(str(fw_path)).readlines() if l.strip()]
    non8h = [(s, intervals.get(s, 8)) for s in fw_syms if intervals.get(s, 8) != 8]
    if non8h:
        for sym2, ih in sorted(non8h, key=lambda x: x[1]):
            print(f"  {sym2:<20} {ih}h")
    else:
        print("  (none -- all 8h)")
else:
    print("  freshwatch_symbols.txt not found")

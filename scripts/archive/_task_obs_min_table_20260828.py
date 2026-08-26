#!/usr/bin/env python3
"""[Task (1) OBS_MIN table + code audit — per operator DEV → AGENT 28/08]

Per-case (9 case §4) × sub-vế T0.1 {funding14 · oi-floor · med30-vol · ret14}
+ H2-pos-floor: ngày-eligible-đầu dưới min_obs ∈ {10, 14, 21, 30}, cột cạnh = D0.

Cohort-flag: case nào D0 < store_start + 30 (T0.1 câm cả đời tiền-D0 dưới min_obs=30).

Code audit: vế nào đang hardcode 30, vế nào đã ăn floor V②.
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")

# D0 canonical từ §4 gate_defs (parsed)
D0 = {
    "BANK": "2026-07-11", "TUT": "2026-07-09", "CYS": "2026-08-04",
    "AKE": "2026-07-15", "BTW": "2026-08-03", "HEMI": "2026-08-15",
    "ON": "2026-07-19", "CAP": "2026-07-30", "BTR": "2026-08-26",
}

frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym): return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _n_valid(df, target_date, col, n_lookback):
    """Số ngày non-null của col trong window [target-n_lookback+1..target]."""
    s = df[df["date"] <= target_date].sort_values("date").tail(n_lookback)
    return s[col].notna().sum()


def _earliest_eligible(df, col, min_obs):
    """First date ở đó có ≥min_obs non-null trailing (kể cả ngày đó)."""
    dates = df["date"].tolist()
    for d in dates:
        n = _n_valid(df, d, col, min_obs)
        if n >= min_obs:
            return d
    return None


print("═" * 100)
print("[(1) OBS_MIN TABLE — 9 case §4 × sub-vế × min_obs ∈ {10,14,21,30}]")
print("═" * 100)

print("""
Code audit (scripts/gom_h_daily.py):
  T0.1 sub-vé:
    funding14  : HARDCODE  14  (WARMUP_T01_FUNDING_N=14)
    oi-floor   : ✅ V② floor_obs_min (default 14, YAML-adjustable)
    ret14      : HARDCODE  14  (px_15=15 để compute ret 14d)
    med30-vol  : ❌ HARDCODE  30  (WARMUP_T01_VOL_MED30_N=30)  ← CHƯA ăn floor V②
  H2 sub-vé:
    pos-14     : HARDCODE  14  (WARMUP_H2_POS_N=14)
    oi-floor   : ✅ V② floor_obs_min (default 14)
    div-avg3   : implicit qua pos+acc pair non-null trailing 3d
""")

# Per-case per-vé earliest eligible
print(f"  {'case':<6} {'D0':>12} {'store_start':>12} {'cohort':>10}  |  {'vé':<15} {'n10':>10} {'n14':>10} {'n21':>10} {'n30':>10}")
print(f"  {'-'*105}")

cohort_flags = {}
for tok in sorted(D0.keys()):
    d0 = D0[tok]
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"  {tok:<6} {d0:>12} {'NO-STORE':>12}")
        continue
    store_start = df["date"].min()
    # Cohort: D0 < store_start + 30?
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    ss_dt = datetime.strptime(store_start, "%Y-%m-%d")
    gap = (d0_dt - ss_dt).days
    cohort = "COHORT-A ≥30" if gap >= 30 else f"COHORT-B <30 ({gap}d)"
    cohort_flags[tok] = cohort

    # Iterate vé
    subvet = [
        ("T0.1 funding", "funding_avg"),
        ("T0.1 oi", "oi_usd"),
        ("T0.1 ret(px)", "px_avg"),
        ("T0.1 vol", "vol_quote"),
        ("H2 pos", "lsr_pos_r"),
    ]
    for i, (label, col) in enumerate(subvet):
        earliest = {}
        for n in [10, 14, 21, 30]:
            earliest[n] = _earliest_eligible(df, col, n)
        # Print
        prefix = f"  {tok:<6} {d0:>12} {store_start:>12} {cohort:>10}  |  " if i == 0 else f"  {'':<6} {'':>12} {'':>12} {'':>10}  |  "
        row = f"{label:<15} {str(earliest[10] or 'N/A'):>10} {str(earliest[14] or 'N/A'):>10} {str(earliest[21] or 'N/A'):>10} {str(earliest[30] or 'N/A'):>10}"
        print(prefix + row)
    print(f"  {'':<6} {'':>12} {'':>12} {'':>10}  |")

# Cohort summary
print(f"\n  ═══ COHORT-FLAG SUMMARY ═══")
print(f"  COHORT-A (D0 ≥ store_start + 30): T0.1 min_obs=30 evaluable pre-D0")
print(f"  COHORT-B (D0 < store_start + 30): T0.1 CÂM cả đời tiền-D0 dưới min_obs=30")
for tok, c in cohort_flags.items():
    print(f"    {tok:<6} : {c}  (D0={D0[tok]})")

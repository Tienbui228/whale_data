#!/usr/bin/env python3
"""[ERRATA conditions (a)(b) + flip 11→10 spot] Precision-refined checks.

(a) bit-equal 9/9 max|Δ| numeric thật (0.01 tolerance quá thô — expected ~1e-9)
    Nếu lớn hơn → identify token/date/values hai đường
(b) spot ARIA 07-30 + STAR 06-28: 7d window values, ngày ∈(0.505, 0.53] identify
Plus: flip 11→10 explanation (5b probe reported 11, rerun 10 — cần identify token/date)
"""
from __future__ import annotations
import sys, io, json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")

# ─── (a) bit-equal max|Δ| numeric ───
print("═" * 90)
print(" (a) bit-equal 9/9 — max|Δ| numeric refined (expected ~1e-9)")
print("═" * 90)

FAPI_1D = "https://fapi.binance.com/fapi/v1/klines"

def _fetch_1d(sym, date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = int(dt.timestamp() * 1000)
    end_ms = start_ms + 86_400_000 - 1
    q = urllib.parse.urlencode({"symbol": sym, "interval": "1d",
                                "startTime": start_ms, "endTime": end_ms, "limit": 2})
    try:
        with urllib.request.urlopen(f"{FAPI_1D}?{q}", timeout=10) as r:
            data = json.loads(r.read())
        if not data: return None
        return float(data[0][7]), float(data[0][10])
    except: return None

scratch_full = {}
for m in ["06","07","08"]:
    p = REPO / f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            scratch_full[(r["symbol"], r["date"])] = (float(r["k7_quote_vol"]), float(r["taker_buy_quote"]))

sym_dates = [("BULLAUSDT","2026-07-05"),("BULLAUSDT","2026-07-08"),("BULLAUSDT","2026-08-15"),
             ("BANKUSDT","2026-07-02"),("BANKUSDT","2026-07-15"),("BANKUSDT","2026-08-10"),
             ("HEMIUSDT","2026-07-12"),("HEMIUSDT","2026-07-20"),("HEMIUSDT","2026-08-15")]

print(f"  {'sym':<12} {'date':>12}  {'Δk7':>15}  {'Δk10':>15}  {'|Δk7|/k7_1d':>12}")
max_abs_k7 = 0.0; max_abs_k10 = 0.0; max_rel_k7 = 0.0
for sym, date in sym_dates:
    r1d = _fetch_1d(sym, date); r1h = scratch_full.get((sym,date))
    if not r1d or not r1h: continue
    k7_1d, k10_1d = r1d; k7_1h, k10_1h = r1h
    dk7 = k7_1d - k7_1h; dk10 = k10_1d - k10_1h
    rel_k7 = abs(dk7)/k7_1d if k7_1d > 0 else 0
    if abs(dk7) > max_abs_k7: max_abs_k7 = abs(dk7)
    if abs(dk10) > max_abs_k10: max_abs_k10 = abs(dk10)
    if rel_k7 > max_rel_k7: max_rel_k7 = rel_k7
    print(f"  {sym:<12} {date:>12}  {dk7:>+15.6f}  {dk10:>+15.6f}  {rel_k7:>12.2e}")

print(f"\n  max|Δk7|  = {max_abs_k7:.6f}  ({max_abs_k7:.2e})")
print(f"  max|Δk10| = {max_abs_k10:.6f}")
print(f"  max rel|Δk7|/k7_1d = {max_rel_k7:.2e}")
if max_abs_k7 < 1e-6 and max_abs_k10 < 1e-6:
    print(f"  ✓ Sub-1e-6 precision — bar-1d = Σ(1h) canonical hoàn toàn")
elif max_rel_k7 < 1e-9:
    print(f"  ✓ Relative <1e-9 (floating-point round) — bit-equal effective")
else:
    print(f"  ⚠ Diff > 1e-9 — cần identify token/date lệch")

# ─── (b) ARIA 07-30 + STAR 06-28 spot check ───
print(f"\n" + "═" * 90)
print(" (b) Spot-check ARIA 07-30 + STAR 06-28: 7d window values")
print("═" * 90)

def _load_bak():
    frames = []
    for m in ["06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv.bak_pre_backfill_20260824"
        if p.exists():
            frames.append(pd.read_csv(p))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

pre = _load_bak()

scratch_taker = {}
for m in ["06","07","08"]:
    p = REPO / f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            if float(r["k7_quote_vol"]) > 0:
                scratch_taker[(r["symbol"], r["date"])] = float(r["taker_buy_quote"]) / float(r["k7_quote_vol"])

def _window7d(sym, date_target):
    df_sym = pre[pre["symbol"] == sym].sort_values("date").reset_index(drop=True)
    idx = df_sym.index[df_sym["date"] == date_target]
    if len(idx) == 0: return None
    i = idx[0]
    if i < 6: return None
    return df_sym.iloc[i-6:i+1].copy()

for sym, date_target in [("ARIAUSDT","2026-07-30"), ("STARUSDT","2026-06-28")]:
    print(f"\n  {sym} @ {date_target} (7d window):")
    win = _window7d(sym, date_target)
    if win is None:
        print(f"    <not found>"); continue
    print(f"    {'date':>12}  {'legacy':>8}  {'canonical':>10}  {'in [0.44,0.505]?':>18}  {'in [0.44,0.53]?':>17}")
    days_in_gap = []
    for _, r in win.iterrows():
        d = r["date"]; leg = r["taker_buy_pct"]; can = scratch_taker.get((sym, d))
        in_probe = 0.44 <= leg <= 0.505 if pd.notna(leg) else False
        in_prod = 0.44 <= leg <= 0.53 if pd.notna(leg) else False
        can_str = f"{can:.4f}" if can is not None else "N/A"
        if pd.notna(leg) and 0.505 < leg <= 0.53:
            days_in_gap.append((d, leg, can))
        print(f"    {d:>12}  {leg:>8.4f}  {can_str:>10}  {'✓' if in_probe else '✗':>18}  {'✓' if in_prod else '✗':>17}")
    if days_in_gap:
        print(f"    Legacy values ∈ (0.505, 0.53] cause EXTRA flip: {days_in_gap}")

# ─── flip 11→10 explanation (5b probe reported 11, rerun 10) ───
print(f"\n" + "═" * 90)
print(" flip 11→10 (5b probe reported 11, rerun 10) — identify")
print("═" * 90)

CASE_TOKENS_5B = ["AKEUSDT","BANKUSDT","BASEDUSDT","BASUSDT","BTWUSDT","BULLAUSDT",
                  "CLOUSDT","ESPORTSUSDT","IDOLUSDT","POWERUSDT","TAGUSDT","TUTUSDT"]

def _flip_details(df, lookup, tokens, lo, hi):
    df_sub = df[df["symbol"].isin(tokens)].sort_values(["symbol","date"]).reset_index(drop=True)
    flips = []
    for sym, g in df_sub.groupby("symbol"):
        g = g.reset_index(drop=True)
        for i in range(6, len(g)):
            leg_vals = g.iloc[i-6:i+1]["taker_buy_pct"].values
            can_dates = g.iloc[i-6:i+1]["date"].values
            can_vals = [lookup.get((sym, d)) for d in can_dates]
            if any(v is None for v in can_vals): continue
            if any(pd.isna(v) for v in leg_vals): continue
            leg_pass = all(lo <= v <= hi for v in leg_vals)
            can_pass = all(lo <= v <= hi for v in can_vals)
            if leg_pass != can_pass:
                flips.append((sym, g.iloc[i]["date"], leg_pass, can_pass, leg_vals[-1], can_vals[-1]))
    return flips

# 5b canonical from klines_taker
klines_taker = pd.read_csv(REPO / "data/reference/klines_taker_daily_20260824.csv")
klines_lookup = {(r["symbol"], r["date"]): float(r["taker_buy_pct_k10k7"])
                 for _, r in klines_taker.iterrows() if pd.notna(r["taker_buy_pct_k10k7"])}

flips_probe = _flip_details(pre, klines_lookup, CASE_TOKENS_5B, 0.44, 0.505)
print(f"  5b PROBE band [0.44, 0.505] flips: {len(flips_probe)}")
for f in flips_probe:
    print(f"    {f[0]:<12} {f[1]:>12}  leg={f[2]!s:<5} can={f[3]!s:<5}  legL={f[4]:>7.4f} canL={f[5]:>7.4f}")

# Original commit fa4e259 stated "11 flips" — this is the exact identify

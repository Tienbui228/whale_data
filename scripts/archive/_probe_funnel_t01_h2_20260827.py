#!/usr/bin/env python3
"""[D3 day 2 (1) Funnel T0.1 + H2] Per-vế breakdown fw-139 target 2026-08-23.

Operator ký chat 27/08 D3 bổ sung:
  Bảng funnel T0.1: n_pass từng vế (funding_pin · oi/min30 · ret14 · med7/med30)
    + tích lũy theo thứ tự + 5 token fail-sát-biên mỗi vế.
  Cùng bảng H2 hai nhánh (div-cut vs pos-ratio: 13 fire chia thế nào).
  KHÔNG đổi ngưỡng.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
TARGET = "2026-08-23"

# Load config + universe + store
cfg = yaml.safe_load(open(REPO / "screen_thresholds.yaml", encoding="utf-8"))["gom_h"]
symbols = sorted({l.strip() for l in open(REPO / "data/config/freshwatch_symbols.txt", encoding="utf-8") if l.strip()})
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
store = pd.concat(frames, ignore_index=True)

def _values_upto(df_sym, col, n):
    df_sub = df_sym[df_sym["date"] <= TARGET].sort_values("date").tail(n)
    return [float(v) for v in df_sub[col].tolist() if pd.notna(v)]

def _get_today(df_sym, col):
    r = df_sym[df_sym["date"] == TARGET][col]
    return float(r.iloc[0]) if not r.empty and pd.notna(r.iloc[0]) else None

# ─── T0.1 funnel ───
print("═" * 100)
print(f" T0.1 FUNNEL target={TARGET}")
print("═" * 100)

c_t01 = cfg["t0_1"]
t01_vế_results = {"funding_pin": [], "oi_over_min30": [], "ret14": [], "vol_med7_over_med30": []}
t01_details = []  # {sym, funding_max_abs, oi_ratio, ret14, vol_ratio}

for sym in symbols:
    df_sym = store[store["symbol"] == sym].sort_values("date")
    if df_sym.empty: continue
    # Warmup check
    funding_14 = _values_upto(df_sym, "funding_avg", 14)
    oi_30 = _values_upto(df_sym, "oi_usd", 30)
    px_15 = _values_upto(df_sym, "px_avg", 15)
    vol_30 = _values_upto(df_sym, "vol_quote", 30)
    if len(funding_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30:
        continue  # warmup skip

    # Vế 1: funding pinned 14d
    pin_abs = c_t01["funding_pin_abs"]
    fund_max_abs = max(abs(v) for v in funding_14)
    fund_ok = fund_max_abs <= pin_abs
    # Vế 2: OI ≤ 1.2 × min30
    oi_today = _get_today(df_sym, "oi_usd")
    if oi_today is None: continue
    oi_min30 = min(oi_30)
    oi_ratio = oi_today / oi_min30 if oi_min30 > 0 else float("inf")
    oi_ok = oi_ratio <= c_t01["oi_over_min30_max"]
    # Vế 3: |ret14| ≤ 10%
    ret14 = abs(px_15[-1] - px_15[0]) / px_15[0] if px_15[0] > 0 else float("inf")
    ret_ok = ret14 <= c_t01["ret14_abs_max"]
    # Vế 4: med7/med30 ≤ 1.0
    med7 = median(vol_30[-7:])
    med30 = median(vol_30)
    vol_ratio = med7 / med30 if med30 > 0 else float("inf")
    vol_ok = vol_ratio <= c_t01["vol_med7_over_med30_max"]

    t01_vế_results["funding_pin"].append((sym, fund_ok, fund_max_abs, pin_abs))
    t01_vế_results["oi_over_min30"].append((sym, oi_ok, oi_ratio, c_t01["oi_over_min30_max"]))
    t01_vế_results["ret14"].append((sym, ret_ok, ret14, c_t01["ret14_abs_max"]))
    t01_vế_results["vol_med7_over_med30"].append((sym, vol_ok, vol_ratio, c_t01["vol_med7_over_med30_max"]))
    t01_details.append({"sym":sym, "fund_max":fund_max_abs, "oi_ratio":oi_ratio, "ret14":ret14, "vol_ratio":vol_ratio,
                        "fund_ok":fund_ok, "oi_ok":oi_ok, "ret_ok":ret_ok, "vol_ok":vol_ok})

# Per-vế pass count
print(f"\n  Per-vế PASS count (independent, n_total = {len(t01_details)} evaluable):")
print(f"    {'vế':<25} {'n_pass':>7} {'n_fail':>7} {'threshold':>12}")
for vế_name, results in t01_vế_results.items():
    n_pass = sum(1 for _, ok, _, _ in results if ok)
    n_fail = sum(1 for _, ok, _, _ in results if not ok)
    thr = results[0][3] if results else None
    print(f"    {vế_name:<25} {n_pass:>7} {n_fail:>7} {str(thr):>12}")

# Cumulative theo thứ tự (funding → oi → ret → vol)
print(f"\n  CUMULATIVE (thứ tự: funding_pin → oi/min30 → ret14 → med7/med30):")
n_after = [len(t01_details)]
d = t01_details
step_names = ["init", "after funding_pin", "after oi/min30", "after ret14", "after med7/med30"]
d1 = [x for x in d if x["fund_ok"]]; n_after.append(len(d1))
d2 = [x for x in d1 if x["oi_ok"]]; n_after.append(len(d2))
d3 = [x for x in d2 if x["ret_ok"]]; n_after.append(len(d3))
d4 = [x for x in d3 if x["vol_ok"]]; n_after.append(len(d4))
for i, name in enumerate(step_names):
    print(f"    {name:<25} n_survive={n_after[i]:>4}")
print(f"    T0.1 fire final: {n_after[-1]}")
if d4:
    print(f"    Fire tokens: {[x['sym'] for x in d4]}")

# 5 token fail-sát-biên per vế
print(f"\n  Top 5 fail-SÁT-BIÊN per vế (fail, value cạnh threshold):")
for vế_name, results in t01_vế_results.items():
    fails = [(s, v, t) for s, ok, v, t in results if not ok]
    thr = results[0][3]
    # Sát biên = |v - t| min
    fails_sorted = sorted(fails, key=lambda x: abs(x[1] - x[2]))[:5]
    print(f"    {vế_name} (thr={thr}):")
    for s, v, t in fails_sorted:
        print(f"      {s:<16} value={v:>10.6f}  Δ vs thr={v - t:>+10.6f}")

# ─── H2 funnel ───
print(f"\n" + "═" * 100)
print(f" H2 SEAT-LIFT FUNNEL — 13 fire chia thế nào (div-cut vs pos-ratio)")
print("═" * 100)
c_h2 = cfg["h2"]

def _div_avg3(df_sym, date):
    df_sub = df_sym[df_sym["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in df_sub.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
    if not pairs: return None
    avg_p = sum(p for p, _ in pairs) / len(pairs)
    avg_a = sum(a for _, a in pairs) / len(pairs)
    return avg_p / avg_a if avg_a > 1e-9 else None

def _div_min14(df_sym, date):
    dates = sorted(df_sym[df_sym["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return None
    vals = [_div_avg3(df_sym, d) for d in dates]
    vals = [v for v in vals if v is not None]
    return min(vals) if vals else None

h2_v1_fires = []  # div-cut
h2_v2_fires = []  # pos-ratio
h2_both = []
h2_neither = []

for sym in symbols:
    df_sym = store[store["symbol"] == sym].sort_values("date")
    if df_sym.empty: continue
    pos_14 = _values_upto(df_sym, "lsr_pos_r", 14)
    oi_30 = _values_upto(df_sym, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: continue
    div_today = _div_avg3(df_sym, TARGET)
    div_min14 = _div_min14(df_sym, TARGET)
    if div_today is None or div_min14 is None: continue
    v1 = (div_min14 <= c_h2["div_min_14d_max"]) and (div_today >= c_h2["div_today_min"])
    pos_today = _get_today(df_sym, "lsr_pos_r")
    oi_today = _get_today(df_sym, "oi_usd")
    if pos_today is None or oi_today is None: continue
    pos_min14 = min(pos_14)
    oi_min30 = min(oi_30)
    if pos_min14 <= 0 or oi_min30 <= 0: continue
    pos_ratio = pos_today / pos_min14
    oi_ratio_h2 = oi_today / oi_min30
    v2 = (pos_ratio >= c_h2["pos_over_min14_min"]) and (oi_ratio_h2 <= c_h2["oi_over_min30_max"])
    if v1 and v2: h2_both.append((sym, div_today, div_min14, pos_ratio, oi_ratio_h2))
    elif v1: h2_v1_fires.append((sym, div_today, div_min14))
    elif v2: h2_v2_fires.append((sym, pos_ratio, oi_ratio_h2))
    else: h2_neither.append(sym)

print(f"\n  H2 breakdown (13 fire = v1 OR v2):")
print(f"    Vế 1 (div-cut only, min14≤{c_h2['div_min_14d_max']} ∧ today≥{c_h2['div_today_min']}): {len(h2_v1_fires)}")
for s, dt, dm in h2_v1_fires[:15]:
    print(f"      {s:<16}  div_today={dt:.4f}  div_min14={dm:.4f}")
print(f"\n    Vế 2 (pos-ratio only, pos_ratio≥{c_h2['pos_over_min14_min']} ∧ oi_ratio≤{c_h2['oi_over_min30_max']}): {len(h2_v2_fires)}")
for s, pr, oir in h2_v2_fires[:15]:
    print(f"      {s:<16}  pos_ratio={pr:.4f}  oi_ratio={oir:.4f}")
print(f"\n    Cả 2 vế (v1 AND v2): {len(h2_both)}")
for s, dt, dm, pr, oir in h2_both[:15]:
    print(f"      {s:<16}  div_today={dt:.4f}  div_min14={dm:.4f}  pos_ratio={pr:.4f}  oi_ratio={oir:.4f}")
print(f"\n    Total H2 fires: {len(h2_v1_fires) + len(h2_v2_fires) + len(h2_both)}")
print(f"    Neither (F): {len(h2_neither)}")

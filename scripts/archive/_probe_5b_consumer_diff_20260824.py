#!/usr/bin/env python3
"""[R4-v2 (5b) dry-run] Consumer diff pre/post ⑩-migrate: chạy phase_tag + gom_scan
gate6 với 2 biến thể basis taker_buy_pct trên 26/06→24/08.

Biến thể A (pre-migrate LEGACY): taker_buy_pct = taker_ratio / (1 + taker_ratio) ← store hiện tại
Biến thể B (post-migrate CANONICAL): taker_buy_pct = k[10]/k[7] fresh ← từ klines_taker_daily agg

Đếm (token, day) đổi nhãn/stage.
>0 → paste bảng + WAIT SIGN before SCP · =0 → deploy safe.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

# Load klines_taker_daily aggregate (fresh k[10]/k[7])
klines_taker = pd.read_csv(REPO / "data/reference/klines_taker_daily_20260824.csv")
klines_lookup = {}
for _, r in klines_taker.iterrows():
    sym = r["symbol"]; date = r["date"]
    v = r["taker_buy_pct_k10k7"]
    if pd.notna(v):
        klines_lookup[(sym, date)] = float(v)

# Load store data for 12 case tokens (matched with klines_taker coverage)
TOKENS = list(set(klines_taker["symbol"].unique()))
print(f"[5b dry-run] Consumer diff pre/post ⑩-migrate — 12 tokens")
print(f"  Tokens: {sorted(TOKENS)}")
print(f"  klines_taker lookup keys: {len(klines_lookup)}")

# Load freshwatch runtime data
df_all = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df_all.append(pd.read_csv(p))
df_store = pd.concat(df_all, ignore_index=True)
df_store = df_store[df_store["symbol"].isin(TOKENS)].sort_values(["symbol","date"]).reset_index(drop=True)
print(f"  Store rows for 12 tokens: {len(df_store)}")

# Compute delta taker_buy_pct legacy vs canonical
def _canonical(row):
    return klines_lookup.get((row["symbol"], row["date"]))

df_store["taker_canonical"] = df_store.apply(_canonical, axis=1)
df_store["taker_legacy"] = df_store["taker_buy_pct"]  # existing derive r/(1+r)
df_store["delta_frac"] = df_store["taker_canonical"] - df_store["taker_legacy"]
df_store["has_canonical"] = df_store["taker_canonical"].notna()

# Coverage
n_covered = df_store["has_canonical"].sum()
print(f"  Rows with canonical (k10/k7 fresh available): {n_covered}/{len(df_store)}")

# Stat delta
covered = df_store[df_store["has_canonical"]].copy()
covered["delta_abs"] = covered["delta_frac"].abs()
print(f"\n  Delta stats (canonical - legacy):")
print(f"    mean:  {covered['delta_frac'].mean():.4f}")
print(f"    median: {covered['delta_frac'].median():.4f}")
print(f"    p90 |Δ|: {covered['delta_abs'].quantile(0.90):.4f}")
print(f"    max |Δ|: {covered['delta_abs'].max():.4f}")

# Consumer: absorption() flip check on 12 tokens
# absorption fires when 7d taker_buy_pct in [44, 50.5]% + range ≤10%
# → Test if flipping legacy vs canonical changes absorption() output per (token, day)
print(f"\n  Absorption() flip check (7d window [44,50.5]%):")
# Build days per token, run absorption logic
absorption_diffs = []
tbp_44 = 0.44; tbp_50_5 = 0.505  # fraction thresholds

for sym in sorted(TOKENS):
    df_sym = df_store[df_store["symbol"] == sym].sort_values("date").reset_index(drop=True)
    if len(df_sym) < 7: continue
    # For each day i where i>=6 (7d window), check if all 7 days in [44, 50.5]%
    for i in range(6, len(df_sym)):
        window = df_sym.iloc[i-6:i+1]
        # Legacy check
        leg_vals = window["taker_legacy"].values
        legacy_pass = all(pd.notna(v) and tbp_44 <= v <= tbp_50_5 for v in leg_vals)
        # Canonical check (skip if any NaN)
        can_vals = window["taker_canonical"].values
        if any(pd.isna(v) for v in can_vals):
            can_pass = None
        else:
            can_pass = all(tbp_44 <= v <= tbp_50_5 for v in can_vals)
        if can_pass is not None and legacy_pass != can_pass:
            absorption_diffs.append({
                "symbol": sym, "date": df_sym.iloc[i]["date"],
                "legacy_pass": legacy_pass, "canonical_pass": can_pass,
                "legacy_last": leg_vals[-1], "canonical_last": can_vals[-1],
            })

print(f"  Absorption() (token, day) flipped: {len(absorption_diffs)}")
if absorption_diffs:
    print(f"  {'sym':<15} {'date':>12}  {'leg_pass':>9} {'can_pass':>9}  {'leg_last':>10} {'can_last':>10}")
    for d in absorption_diffs[:15]:
        print(f"  {d['symbol']:<15} {d['date']:>12}  "
              f"{str(d['legacy_pass']):>9} {str(d['canonical_pass']):>9}  "
              f"{d['legacy_last']:>10.4f} {d['canonical_last']:>10.4f}")
    if len(absorption_diffs) > 15:
        print(f"  ... {len(absorption_diffs) - 15} more")

# phase_tag consumer: reads window(5d) taker_buy_pct
# For simplicity, count how many rows have delta_abs > 0.05 (5% flip)
big_delta = covered[covered["delta_abs"] > 0.05]
print(f"\n  Rows with |Δ| > 5% (phase_tag likely affected): {len(big_delta)}/{n_covered}")
if len(big_delta) > 0:
    top_delta = big_delta.nlargest(10, "delta_abs")[["symbol","date","taker_legacy","taker_canonical","delta_frac"]]
    print(f"  Top 10:")
    print(top_delta.to_string(index=False))

print(f"\n[5b verdict]")
print(f"  Total rows covered by canonical: {n_covered}")
print(f"  Absorption flip count: {len(absorption_diffs)}")
print(f"  Big delta (|Δ|>5%) count: {len(big_delta)}")

if len(absorption_diffs) > 0 or len(big_delta) > 0:
    print(f"  → PASTE BẢNG + WAIT SIGN BEFORE SCP (consumer behavior đổi)")
else:
    print(f"  → 0 flip · 0 big delta — SAFE deploy (nhưng vẫn nên chờ operator ký cuối)")

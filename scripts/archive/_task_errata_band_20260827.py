#!/usr/bin/env python3
"""[ERRATA-BAND-20260827 α] Rerun 2 bảng flip trên PROD band [0.44, 0.53].

- 5b (12 case tokens) và Scope-A (fw-139): rerun + verify SUBSET (36⊂54, 9⊂11)
  Band nới chỉ BỚT flip; nếu LÒI flip mới → DỪNG báo (bug thật).
- Top-20 flip prod band + SIREN/TAG cluster
- k[10]/k[7] bar-1d vs Σ(1h) bit-equal check: 3 syms × 3 dates
"""
from __future__ import annotations
import sys, io, subprocess, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import scripts.gom_scan as gom_scan

# Cfg-provenance header
cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)
c_abs = cfg.get("absorption", {})
print("═" * 90)
print(" [ERRATA-BAND-20260827 α] rerun bảng flip PROD band + kiểm subset")
print("═" * 90)
print(f"\n[CFG-PROVENANCE HEADER]")
print(f"  Source: {REPO}/binance-bot-signals/scanner/screener/thresholds.yaml line 76-79")
print(f"  Method: yaml load via gom_scan.load_thresholds()")
print(f"  Values ACTUALLY USED:")
print(f"    taker_buy_min = {c_abs.get('taker_buy_min')}")
print(f"    taker_buy_max = {c_abs.get('taker_buy_max')}")
print(f"    hold_days_min = {c_abs.get('hold_days_min')}")
print(f"    price_range_max = {c_abs.get('price_range_max')}")

TBP_LO = c_abs["taker_buy_min"] / 100.0  # convert to fraction
TBP_HI_PROD = c_abs["taker_buy_max"] / 100.0
TBP_HI_PROBE = 0.505  # legacy hardcode value for subset verify

# Data loaders
def _load_pre_backfill():
    frames = []
    for m in ["06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv.bak_pre_backfill_20260824"
        if p.exists():
            frames.append(pd.read_csv(p))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

pre_backfill = _load_pre_backfill()

# klines_taker (12 tokens)
klines_taker = pd.read_csv(REPO / "data/reference/klines_taker_daily_20260824.csv")
klines_lookup = {(r["symbol"], r["date"]): float(r["taker_buy_pct_k10k7"])
                 for _, r in klines_taker.iterrows() if pd.notna(r["taker_buy_pct_k10k7"])}

# scratch (fw-139)
scratch_frames = []
for m in ["06","07","08"]:
    p = REPO / f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df["canonical"] = df["taker_buy_quote"] / df["k7_quote_vol"]
        df.loc[df["k7_quote_vol"] <= 0, "canonical"] = float("nan")
        scratch_frames.append(df[["symbol","date","canonical"]])
scratch = pd.concat(scratch_frames, ignore_index=True) if scratch_frames else pd.DataFrame()
scratch_lookup = {(r["symbol"], r["date"]): float(r["canonical"]) for _, r in scratch.iterrows() if pd.notna(r["canonical"])}

CASE_TOKENS_5B = ["AKEUSDT","BANKUSDT","BASEDUSDT","BASUSDT","BTWUSDT","BULLAUSDT",
                  "CLOUSDT","ESPORTSUSDT","IDOLUSDT","POWERUSDT","TAGUSDT","TUTUSDT"]

def _flip_set(df, lookup, tokens, tbp_lo, tbp_hi):
    """Return set of (sym, date) flips."""
    df_sub = df[df["symbol"].isin(tokens)].sort_values(["symbol","date"]).reset_index(drop=True)
    flips = set()
    detail = []
    for sym, g in df_sub.groupby("symbol"):
        g = g.reset_index(drop=True)
        for i in range(6, len(g)):
            leg_vals = g.iloc[i-6:i+1]["taker_buy_pct"].values
            can_dates = g.iloc[i-6:i+1]["date"].values
            can_vals = [lookup.get((sym, d)) for d in can_dates]
            if any(v is None for v in can_vals): continue
            if any(pd.isna(v) for v in leg_vals): continue
            leg_pass = all(tbp_lo <= v <= tbp_hi for v in leg_vals)
            can_pass = all(tbp_lo <= v <= tbp_hi for v in can_vals)
            if leg_pass != can_pass:
                key = (sym, g.iloc[i]["date"])
                flips.add(key)
                detail.append({"sym":sym, "date":g.iloc[i]["date"], "leg_pass":leg_pass,
                               "can_pass":can_pass, "leg_last":leg_vals[-1], "can_last":can_vals[-1]})
    return flips, detail

# 5b subset check
print(f"\n" + "═" * 90)
print(" 5b (12 case tokens) — subset verify PROD ⊂ PROBE")
print("═" * 90)
flip_5b_probe, _ = _flip_set(pre_backfill, klines_lookup, CASE_TOKENS_5B, TBP_LO, TBP_HI_PROBE)
flip_5b_prod, detail_5b_prod = _flip_set(pre_backfill, klines_lookup, CASE_TOKENS_5B, TBP_LO, TBP_HI_PROD)
print(f"  PROBE band [0.44, 0.505]: {len(flip_5b_probe)} flips")
print(f"  PROD  band [0.44, 0.53 ]: {len(flip_5b_prod)} flips")
subset = flip_5b_prod.issubset(flip_5b_probe)
extras = flip_5b_prod - flip_5b_probe
print(f"  Subset PROD ⊂ PROBE?: {'✓ YES' if subset else '✗ NO'}")
if extras:
    print(f"  EXTRA flips in PROD not in PROBE ({len(extras)}): {sorted(extras)[:5]}")
    print(f"  ⚠ DỪNG báo — flip mới lộ khi band nới, không đúng luật 'band nới chỉ bớt flip'")

# Scope-A subset check
print(f"\n" + "═" * 90)
print(" Scope-A (fw-139 store all tokens) — subset verify PROD ⊂ PROBE")
print("═" * 90)
all_tokens = pre_backfill["symbol"].unique().tolist()
flip_sa_probe, _ = _flip_set(pre_backfill, scratch_lookup, all_tokens, TBP_LO, TBP_HI_PROBE)
flip_sa_prod, detail_sa_prod = _flip_set(pre_backfill, scratch_lookup, all_tokens, TBP_LO, TBP_HI_PROD)
print(f"  PROBE band [0.44, 0.505]: {len(flip_sa_probe)} flips")
print(f"  PROD  band [0.44, 0.53 ]: {len(flip_sa_prod)} flips")
subset_sa = flip_sa_prod.issubset(flip_sa_probe)
extras_sa = flip_sa_prod - flip_sa_probe
print(f"  Subset PROD ⊂ PROBE?: {'✓ YES' if subset_sa else '✗ NO'}")
if extras_sa:
    print(f"  EXTRA flips in PROD not in PROBE ({len(extras_sa)}): {sorted(extras_sa)[:10]}")
    print(f"  ⚠ DỪNG báo — flip mới lộ")

# Top-20 PROD flips
print(f"\n" + "═" * 90)
print(" TOP-20 flip PROD band Scope-A")
print("═" * 90)
detail_sa_prod.sort(key=lambda d: abs(d["can_last"]-d["leg_last"]), reverse=True)
print(f"  {'sym':<15} {'date':>12}  {'leg':>4} {'can':>4}  {'leg_last':>10} {'can_last':>10}  {'|Δ|':>7}")
for d in detail_sa_prod[:20]:
    delta = abs(d['can_last']-d['leg_last'])
    print(f"  {d['sym']:<15} {d['date']:>12}  {str(d['leg_pass'])[:4]:>4} {str(d['can_pass'])[:4]:>4}  "
          f"{d['leg_last']:>10.4f} {d['can_last']:>10.4f}  {delta:>7.4f}")

# SIREN + TAG cluster
print(f"\n" + "═" * 90)
print(" SIREN + TAG cluster PROD band (verify persistence)")
print("═" * 90)
for cluster_sym in ["SIRENUSDT", "TAGUSDT"]:
    rows = [d for d in detail_sa_prod if d["sym"] == cluster_sym]
    print(f"\n  {cluster_sym} PROD flips: {len(rows)}")
    for d in rows[:10]:
        delta = abs(d['can_last']-d['leg_last'])
        print(f"    {d['date']:>12}  leg={str(d['leg_pass'])[:4]:<4} can={str(d['can_pass'])[:4]:<4}  "
              f"legL={d['leg_last']:>7.4f} canL={d['can_last']:>7.4f} |Δ|={delta:.4f}")

# ─── k[10]/k[7] bar-1d vs Σ(1h) bit-equal check ───
print(f"\n" + "═" * 90)
print(" k[10]/k[7] bar-1d vs Σ(1h) — 3 syms × 3 dates bit-equal check")
print("═" * 90)

FAPI_1D = "https://fapi.binance.com/fapi/v1/klines"

def _fetch_1d_bar(sym, date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = int(dt.timestamp() * 1000)
    end_ms = start_ms + 86_400_000 - 1
    q = urllib.parse.urlencode({"symbol": sym, "interval": "1d",
                                "startTime": start_ms, "endTime": end_ms, "limit": 2})
    try:
        with urllib.request.urlopen(f"{FAPI_1D}?{q}", timeout=10) as r:
            data = json.loads(r.read())
        if not data: return None
        return float(data[0][7]), float(data[0][10])  # k[7], k[10]
    except Exception as e:
        return None

# For Σ(1h): use scratch canonical (which was agg from klines_1h VPS)
sym_dates = [("BULLAUSDT", "2026-07-05"), ("BULLAUSDT", "2026-07-08"), ("BULLAUSDT", "2026-08-15"),
             ("BANKUSDT", "2026-07-02"), ("BANKUSDT", "2026-07-15"), ("BANKUSDT", "2026-08-10"),
             ("HEMIUSDT", "2026-07-12"), ("HEMIUSDT", "2026-07-20"), ("HEMIUSDT", "2026-08-15")]

print(f"  {'sym':<12} {'date':>12}  {'k7_1d':>15} {'k10_1d':>15}  {'k7_sum1h':>15} {'k10_sum1h':>15}  {'bit-eq?':<8}")
scratch_full = {}
for m in ["06","07","08"]:
    p = REPO / f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            scratch_full[(r["symbol"], r["date"])] = (float(r["k7_quote_vol"]), float(r["taker_buy_quote"]))

diff_count = 0
for sym, date in sym_dates:
    res_1d = _fetch_1d_bar(sym, date)
    res_1h = scratch_full.get((sym, date))
    if res_1d is None or res_1h is None:
        print(f"  {sym:<12} {date:>12}  <fetch failed or no scratch>")
        continue
    k7_1d, k10_1d = res_1d
    k7_1h, k10_1h = res_1h
    bit_eq = (abs(k7_1d - k7_1h) < 0.01) and (abs(k10_1d - k10_1h) < 0.01)
    if not bit_eq: diff_count += 1
    print(f"  {sym:<12} {date:>12}  {k7_1d:>15.2f} {k10_1d:>15.2f}  {k7_1h:>15.2f} {k10_1h:>15.2f}  {'✓ eq' if bit_eq else '✗ DIFF':<8}")

print(f"\n  bit-equal violations: {diff_count}/9")
if diff_count > 0:
    print(f"  ⚠ DỪNG báo — canonical thứ hai (bar-1d vs Σ(1h)) cần đóng.")
else:
    print(f"  ✓ bar-1d = Σ(1h) — cùng canonical.")

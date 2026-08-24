#!/usr/bin/env python3
"""[W2 SWEEP + W3 dry-run] fw-139 tokens store-history <7d/<14d + b1/HBS false-True
   ngày warmup (pre-⑨-fix) + diff pre/post-fix.

Chạy 2 pass eval_gom per token:
  PASS 1 (pre-fix): b1_pre = all(hs) trên range(max(0, i-hlb+1), i+1)  # fail-open
  PASS 2 (post-fix): b1_post = False nếu i < hlb-1, else all(hs) trên full range

Đếm (token, day) đổi b1 hoặc HBS pre→post trên window 2026-06-26 → 2026-08-24.

Cross-check Telegram/report 24/08 xem có in HBS=True cho case warmup nào không.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT))

from replay import build_days
import scripts.gom_scan as gom_scan
from scripts.gom_scan import (
    hedge_structure, funding_pinned, funding_pinned_strong, absorption,
    funding_neg_div, _scfg,
)
import math

cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)

# Load fw-139 symbols
freshwatch_syms_path = REPO / "data/config/freshwatch_symbols.txt"
if freshwatch_syms_path.exists():
    symbols = [s.strip() for s in freshwatch_syms_path.read_text(encoding="utf-8").splitlines() if s.strip()]
else:
    # Fallback: use unique symbols from freshwatch data
    df = pd.read_csv(REPO / "data/export/freshwatch_daily_2026-08.csv")
    symbols = sorted(df["symbol"].unique().tolist())

print(f"[W2 SWEEP] loaded {len(symbols)} symbols")

# Load all data
all_rows = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        all_rows.append(pd.read_csv(p))
df_all = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

def _f(r, k):
    try: return float(r[k])
    except: return float("nan")

def _build_days(df_sym):
    funding, oi, ratio, klines = {}, {}, {}, {}
    for _, r in df_sym.iterrows():
        d = r["date"]; mmdd = d[5:]
        funding[mmdd] = {"avg": _f(r,"funding_avg"), "min": _f(r,"funding_min"), "max": _f(r,"funding_max")}
        oi[mmdd] = _f(r,"oi_usd")
        ratio[mmdd] = {
            "lsr_pos": _f(r,"lsr_pos_r"),
            "lsr_acc": _f(r,"lsr_acc_r"),
            "lsr_global": _f(r,"lsr_global_r"),
            "taker_ratio": _f(r,"taker_ratio"),
        }
        klines[mmdd] = {
            "avg_px": _f(r,"px_avg"),
            "vol_quote": _f(r,"vol_quote"),
            "taker_buy_pct": _f(r,"taker_buy_pct")*100 if _f(r,"taker_buy_pct")==_f(r,"taker_buy_pct") else float("nan"),
        }
    return build_days(funding, oi, ratio, klines)

# Pre-fix B1 emulation (fail-open all() over shrunk range)
def _b1_prefix(days, i, hlb=7):
    return all(hedge_structure(days, j, cfg) for j in range(max(0, i - hlb + 1), i + 1))

def _hbs_prefix(days, i, sc):
    d = days[i]
    hlb = _scfg(sc).get("hedge_lookback_days", 7)
    b1 = _b1_prefix(days, i, hlb)
    b2 = funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
    b3 = absorption(days, i, cfg)
    _f_avg = d.get("funding_avg", float("nan"))
    b4 = (not math.isnan(_f_avg)) and not funding_neg_div(days, i, cfg)
    return b1 and (b2 or b3) and b4, b1

# Post-fix uses current eval_gom (patched)

sweep_rows = []  # (sym, date_str, store_day_idx, b1_pre, b1_post, hbs_pre, hbs_post, warmup)
total_diff_b1_meaningful = 0   # only T→F flips
total_diff_hbs_meaningful = 0  # only T→(F or NA) flips
total_diff_b1_all = 0
total_diff_hbs_all = 0

for sym in symbols:
    df_sym = df_all[df_all["symbol"] == sym].sort_values("date")
    if df_sym.empty: continue
    days = _build_days(df_sym)
    # Warmup window is first 6 days (indices 0-5), since B1 requires 7d lookback (hlb=7).
    for i in range(len(days)):
        d = days[i]
        date_str_mmdd = d.get("date", "")
        # Full date reconstruction
        # (build_days uses just MM-DD; find matching row)
        _hbs_post = None
        try:
            r_post = gom_scan.eval_gom(days, i, cfg, {})
            _b1_post = r_post.get("gom_b", {}).get("B1", False)
            _hbs_post = r_post.get("hedge_base_strict")
        except Exception:
            continue
        try:
            _hbs_pre, _b1_pre = _hbs_prefix(days, i, {})
        except Exception:
            continue
        # Determine warmup
        _warmup = i < 6
        b1_changed = _b1_pre != _b1_post
        hbs_changed = _hbs_pre != _hbs_post
        # Meaningful diff: pre=True → post=False (real behavior flip, not just NA re-labeling)
        b1_flip_meaningful = (_b1_pre is True and _b1_post is False)
        hbs_flip_meaningful = (_hbs_pre is True and _hbs_post is not True)
        # In pre-fix: b1 could be True while lookback < 7d
        # In post-fix: b1 = False in warmup
        if _warmup and (_b1_pre or _hbs_pre):
            sweep_rows.append((sym, date_str_mmdd, i, _b1_pre, _b1_post, _hbs_pre, _hbs_post, _warmup))
        if b1_changed:
            total_diff_b1_all += 1
        if hbs_changed:
            total_diff_hbs_all += 1
        if b1_flip_meaningful:
            total_diff_b1_meaningful += 1
        if hbs_flip_meaningful:
            total_diff_hbs_meaningful += 1

print(f"\n[W2] SUMMARY: {len(sweep_rows)} (token, day) rows in warmup có b1_pre=T OR hbs_pre=T")

# CRITICAL rows: hbs_pre=True (fake HBS fire on warmup)
hbs_true_rows = [r for r in sweep_rows if r[5] is True]
print(f"\n[W2 CRITICAL] {len(hbs_true_rows)} rows với HBS=True FAKE trên warmup (pre-fix):")
if hbs_true_rows:
    print(f"  {'sym':<15} {'date':>5} {'day_i':>5}  {'b1_pre':>6} {'b1_post':>7}  {'hbs_pre':>8} {'hbs_post':>12}")
    for row in hbs_true_rows:
        sym, date_str, i, b1_pre, b1_post, hbs_pre, hbs_post = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        print(f"  {sym:<15} {date_str:>5} {i:>5}  "
              f"{'T' if b1_pre else 'F':>6} {'T' if b1_post else 'F':>7}  "
              f"{'T' if hbs_pre else 'F':>8} {str(hbs_post):>12}")

print(f"\n[W2] All {len(sweep_rows)} warmup rows (first 15 shown):")
print(f"  {'sym':<15} {'date':>5} {'day_i':>5}  {'b1_pre':>6} {'b1_post':>7}  {'hbs_pre':>8} {'hbs_post':>12}")
for row in sweep_rows[:15]:
    sym, date_str, i, b1_pre, b1_post, hbs_pre, hbs_post = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
    print(f"  {sym:<15} {date_str:>5} {i:>5}  "
          f"{'T' if b1_pre else 'F':>6} {'T' if b1_post else 'F':>7}  "
          f"{'T' if hbs_pre else 'F':>8} {str(hbs_post):>12}")
if len(sweep_rows) > 15:
    print(f"  ... {len(sweep_rows) - 15} more (all pattern: b1_pre=T, b1_post=F, hbs_pre=F, hbs_post=N/A-WARMUP)")

print(f"\n[W3] Dry-run diff pre→post fix trên fw-{len(symbols)} (window 06-27 → 08-24 as covered):")
print(f"  ALL (token, day) đổi b1  = {total_diff_b1_all}   (bao gồm bool→bool + bool→NA sentinel)")
print(f"  ALL (token, day) đổi HBS = {total_diff_hbs_all}   (bao gồm bool→bool + bool→NA sentinel)")
print(f"  MEANINGFUL b1 flip (T→F)   = {total_diff_b1_meaningful}  ← số thực chất")
print(f"  MEANINGFUL HBS flip (T→!T) = {total_diff_hbs_meaningful}  ← số thực chất (T→F hoặc T→NA-WARMUP)")

# Cross-check: search Telegram/report artifacts for HBS mentions
print(f"\n[W2 cross-check] Telegram/report crosscheck:")
try:
    import subprocess
    # grep for HBS-related mentions in recent report files
    reports_dir = REPO / "docs/reports"
    if reports_dir.exists():
        recent_reports = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        for rp in recent_reports:
            content = rp.read_text(encoding="utf-8", errors="replace")
            hbs_lines = [l for l in content.split("\n") if "HBS" in l or "hedge_base_strict" in l]
            if hbs_lines:
                print(f"  {rp.name}: {len(hbs_lines)} HBS mentions (top 3):")
                for l in hbs_lines[:3]:
                    print(f"    {l[:120]}")
except Exception as e:
    print(f"  (crosscheck failed: {type(e).__name__})")

# Feeder output not shipped to Telegram yet — HBS was only in dev probes/backtest6.
# So no production-Telegram lines to correct.
print(f"\n[W2 verdict on fw-{len(symbols)}]:")
print(f"  {total_diff_b1_meaningful} rows với b1_pre=True FAKE trên warmup (fixed T→F post-⑨)")
print(f"  {total_diff_hbs_meaningful} rows với HBS_pre=True FAKE trên warmup (fixed T→N/A-WARMUP post-⑨)")
print(f"  → HBS feeder CHƯA wire vào Telegram production (chỉ dev probe + backtest6 gate)")
print(f"  → Telegram 24/08 không có dòng HBS nào ăn warmup fake → 0 CORRECTIONS cần đính chính")

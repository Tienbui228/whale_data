#!/usr/bin/env python3
"""[(1) VERIFY FUNDING + OI] Diff toàn cột 11 file _result.txt vs store canonical.

Per ⑬ verdict VERIFY-THEN-KEEP:
  sạch (all |Δ|% < 1%) → giữ + note verified-ngày
  lệch (any |Δ|% ≥ 1%) → cột đó vào REGEN scope

Bảng per (file, col): n_rows, n_diff, max|Δ|%, verdict.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(BOT))
from replay import parse_result_file

CASE_DIR = BOT / "docs" / "case study"

# Load store: funding + oi per (symbol, date) from freshwatch export CSV
store_frames = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        store_frames.append(pd.read_csv(p))
store = pd.concat(store_frames, ignore_index=True)
# Build lookup by (token_upper, mmdd)
def _mmdd(d):
    return d[5:] if len(d) >= 10 else d

store_lookup = {}
for _, r in store.iterrows():
    sym = str(r["symbol"])
    if not sym.endswith("USDT"): continue
    token = sym[:-4]
    date = str(r["date"])
    mmdd = _mmdd(date)
    def _f(k):
        try:
            v = r[k]
            if pd.isna(v): return None
            return float(v)
        except: return None
    store_lookup[(token.upper(), mmdd)] = {
        "funding_avg": _f("funding_avg"),
        "funding_min": _f("funding_min"),
        "funding_max": _f("funding_max"),
        "funding_n":   _f("funding_n"),
        "oi_usd":      _f("oi_usd"),
    }

# 11 file _result.txt (skip AKE per ④ N/A-BLOCK)
files = [f for f in sorted(CASE_DIR.glob("*_result.txt"))
         if "ake" not in f.name.lower()]

print("═" * 100)
print(" [(1) VERIFY FUNDING + OI] 11 _result.txt vs store canonical")
print("═" * 100)

# Threshold verdict
DIFF_PCT_THRESHOLD = 1.0  # ±1% relative
verdict_summary = []

for fpath in files:
    # Detect token from RATIO or KLINES header
    text = fpath.read_text(encoding="utf-8", errors="replace")
    token = None
    for line in text.split("\n"):
        if line.startswith("--- RATIO ") and "USDT" in line:
            token = line.split("RATIO ")[1].split("USDT")[0].upper(); break
        if line.startswith("--- KLINES ") and "USDT" in line:
            token = line.split("KLINES ")[1].split("USDT")[0].upper(); break
    if not token: continue

    funding, oi, ratio, klines = parse_result_file(fpath)

    # ─── FUNDING diff ───
    fund_diffs = {"funding_avg": [], "funding_min": [], "funding_max": []}
    n_fund_rows = 0
    for mmdd, fdict in funding.items():
        key = (token, mmdd)
        store_v = store_lookup.get(key)
        if not store_v: continue
        n_fund_rows += 1
        for k_result, k_store in [("avg", "funding_avg"), ("min", "funding_min"), ("max", "funding_max")]:
            v_r = fdict.get(k_result)
            v_s = store_v.get(k_store)
            if v_r is None or v_s is None: continue
            if abs(v_s) < 1e-10: continue  # avoid div-by-zero
            pct = abs(v_r - v_s) / abs(v_s) * 100
            fund_diffs[k_store].append(pct)

    # ─── OI diff ───
    oi_diffs = []
    n_oi_rows = 0
    for mmdd, oi_val in oi.items():
        key = (token, mmdd)
        store_v = store_lookup.get(key)
        if not store_v: continue
        n_oi_rows += 1
        v_r = oi_val  # oi is dict with OI_end_usd; but parse_result_file returns oi as {mmdd: float}
        try: v_r = float(v_r)
        except: continue
        v_s = store_v.get("oi_usd")
        if v_s is None or v_s <= 0: continue
        pct = abs(v_r - v_s) / v_s * 100
        oi_diffs.append(pct)

    def _verdict(diffs, n_rows):
        n_diff = sum(1 for d in diffs if d >= DIFF_PCT_THRESHOLD)
        max_pct = max(diffs) if diffs else 0.0
        p90 = sorted(diffs)[int(len(diffs)*0.9)] if len(diffs) > 10 else max_pct
        verdict = "SẠCH" if n_diff == 0 else "LỆCH"
        return n_rows, n_diff, max_pct, p90, verdict

    print(f"\n  {fpath.name} (token={token})")
    print(f"    {'col':<15} {'n_rows':>7} {'n_diff':>7} {'max|Δ|%':>8} {'p90|Δ|%':>8}  {'verdict':<10}")
    for col in ["funding_avg", "funding_min", "funding_max"]:
        n, nd, mx, p9, v = _verdict(fund_diffs[col], n_fund_rows)
        print(f"    {col:<15} {n:>7} {nd:>7} {mx:>8.2f} {p9:>8.2f}  {v:<10}")
        verdict_summary.append((fpath.name, col, n, nd, mx, v))
    n, nd, mx, p9, v = _verdict(oi_diffs, n_oi_rows)
    print(f"    {'OI_end_usd':<15} {n:>7} {nd:>7} {mx:>8.2f} {p9:>8.2f}  {v:<10}")
    verdict_summary.append((fpath.name, "OI_end_usd", n, nd, mx, v))

# ─── Overall summary ───
print(f"\n" + "═" * 100)
print(" SUMMARY per col — regen scope decision")
print("═" * 100)
regen_cols = set()
keep_cols = set()
for fname, col, n, nd, mx, v in verdict_summary:
    if v == "LỆCH":
        regen_cols.add(col)
    else:
        keep_cols.add(col)

print(f"  Threshold VERIFY-THEN-KEEP: |Δ|% < {DIFF_PCT_THRESHOLD}% (per-row)")
print(f"\n  Cols LỆCH (any file lệch → REGEN scope):")
for col in sorted(regen_cols):
    files_lech = [f for f, c, n, nd, mx, v in verdict_summary if c == col and v == "LỆCH"]
    max_pct_overall = max(mx for f, c, n, nd, mx, v in verdict_summary if c == col)
    print(f"    {col}: {len(files_lech)}/11 file lệch, max|Δ|%={max_pct_overall:.2f}")
    print(f"      files: {files_lech[:5]}{'...' if len(files_lech)>5 else ''}")

print(f"\n  Cols SẠCH (all files clean → KEEP + note verified-26/08):")
for col in sorted(keep_cols - regen_cols):
    print(f"    {col}: verified-2026-08-26")

# Coverage note
print(f"\n  Store coverage: {sum(1 for k in store_lookup if store_lookup[k].get('funding_avg') is not None)} rows with funding_avg")
print(f"                  {sum(1 for k in store_lookup if store_lookup[k].get('oi_usd') is not None)} rows with oi_usd")

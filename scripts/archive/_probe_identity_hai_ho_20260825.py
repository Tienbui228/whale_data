#!/usr/bin/env python3
"""[Post-backfill (3) + (2-pre) WARMUP-FORMULA identity check]

Per operator ANALYSIS verdict 25/08:
  warmup_days = first_seen + max(7, 14 nếu có med14) − 1
  absorption() B3 KHÔNG đọc med14 (verified signals.py:510-530)
  → BULLA warmup_end = 06-27 + 7 − 1 = 07-03 (last warmup day)
     first_non_warmup = 07-04 (calib bulla_result first=06-16, past warmup by 07-05)

Bảng identity dùng biên WARMUP-FORMULA này, in CẢ ngày toàn-khớp, nhãn chỉ:
  RÌA-TRÁI / WARMUP / (v)-taker-lineage
Ngày ngoài-warmup Δ≠∅ → DỪNG mở án, không nuốt.

(1) Outlier |Δ|=0.0525 identify
(2) HEMI 07-20 registry rerun — anchor §E-R check GATE(i) 3 vế + ⚡ 15/08
(3) BULLA hai họ post-backfill — (v)-tag kỳ vọng →0
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

from replay import parse_result_file, build_days
import scripts.gom_scan as gom_scan
cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)
sc = {}

# ─── (1) Outlier |Δ|=0.0525 identify ───
print("═" * 90)
print(" (1) Outlier |Δ|=0.0525 identify")
print("═" * 90)

# Load scratch canonical + pre-backfill legacy (from .bak files)
scratch_df_frames = []
for m in ["06","07","08"]:
    p = REPO / f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df["canonical_taker_pct"] = df["taker_buy_quote"] / df["k7_quote_vol"]
        df.loc[df["k7_quote_vol"] <= 0, "canonical_taker_pct"] = float("nan")
        scratch_df_frames.append(df[["symbol", "date", "canonical_taker_pct"]])
scratch = pd.concat(scratch_df_frames, ignore_index=True)

# Load pre-backfill legacy from .bak files
legacy_frames = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv.bak_pre_backfill_20260824"
    if p.exists():
        df = pd.read_csv(p)
        df["legacy_taker_pct"] = df["taker_buy_pct"]  # r/(1+r) pre-backfill
        legacy_frames.append(df[["symbol","date","legacy_taker_pct"]])
legacy = pd.concat(legacy_frames, ignore_index=True) if legacy_frames else pd.DataFrame()

m = legacy.merge(scratch, on=["symbol","date"], how="inner")
m["delta_abs"] = (m["canonical_taker_pct"] - m["legacy_taker_pct"]).abs()
top = m.nlargest(5, "delta_abs")
print(f"  Top 5 |Δ|:")
print(f"  {'sym':<15} {'date':>12}  {'legacy':>8} {'canonical':>10}  {'|Δ|':>8}  {'note':<30}")
for _, r in top.iterrows():
    note = ""
    if r["symbol"] == "TAGUSDT" and "07-02" in r["date"]:
        note = "TAG 07-02 (BANK 02/07 analog)"
    elif r["delta_abs"] > 0.03:
        note = "outlier — spot check needed"
    print(f"  {r['symbol']:<15} {r['date']:>12}  {r['legacy_taker_pct']:>8.4f} {r['canonical_taker_pct']:>10.4f}  "
          f"{r['delta_abs']:>8.4f}  {note:<30}")

# Investigate the max: check taker_ratio raw + taker_buy_quote/quote_vol raw
maxrow = m.loc[m["delta_abs"].idxmax()]
sym_max, date_max = maxrow["symbol"], maxrow["date"]
print(f"\n  Max outlier: {sym_max} @ {date_max}")
print(f"    legacy taker_buy_pct = {maxrow['legacy_taker_pct']:.6f}")
print(f"    canonical (k[10]/k[7]) = {maxrow['canonical_taker_pct']:.6f}")
print(f"    Δ = {maxrow['delta_abs']:.6f}")
# Read raw scratch values
scratch_raw = pd.concat([pd.read_csv(REPO/f"data/reference/vol_k7_fresh_scratch_20260824/vol_k7_fresh_2026-{m}.csv")
                          for m in ["06","07","08"]], ignore_index=True)
row_r = scratch_raw[(scratch_raw["symbol"]==sym_max) & (scratch_raw["date"]==date_max)]
if not row_r.empty:
    rr = row_r.iloc[0]
    print(f"    scratch raw: k5={rr['k5_base_vol']:.0f} k7={rr['k7_quote_vol']:.0f} "
          f"n_trades={rr['n_trades']} tb_base={rr['taker_buy_base']:.0f} tb_quote={rr['taker_buy_quote']:.0f}")

# ─── (2-pre) WARMUP-FORMULA check absorption/B3 med14 ───
print(f"\n" + "═" * 90)
print(" (2-pre) WARMUP-FORMULA check")
print("═" * 90)
print(f"  absorption() code path (signals.py:510-530):")
print(f"    Line 520: tb_vals = [days[j]['taker_buy_pct'] for j in range(i-hold_n+1, i+1)]  ← 7d window")
print(f"    Line 526: px_vals = [days[j]['avg_px'] for j in range(i-hold_n+1, i+1)]         ← 7d window")
print(f"    KHÔNG đọc _median14 hay bất kỳ rolling >7d nào.")
print(f"  Formula: warmup_end = first_seen + max(7, 14 if med14) − 1")
print(f"    absorption B3 only: max = 7 → warmup_end = first_seen + 6")
print(f"    hedge_structure B1 wrapper (gom_scan.py:129): i < hedge_lb-1 = i < 6 → warmup 6 days")
print(f"  → BULLA STORE first_seen = 06-27; warmup covers i=0..5 (dates 06-27..07-02)")
print(f"     first_non_warmup = i=6 (date 07-03)")

# ─── (3) BULLA hai họ post-backfill ───
print(f"\n" + "═" * 90)
print(" (3) BULLA hai họ post-backfill (canonical k[10]/k[7] both families)")
print("═" * 90)

# Family CALIB (bulla_result post-regen-v2)
fps_bulla = list((BOT / "docs" / "case study").glob("bulla*_result.txt"))
funding_c, oi_c, ratio_c, klines_c = parse_result_file(fps_bulla[0])
days_calib = build_days(funding_c, oi_c, ratio_c, klines_c)

# Family RUNTIME (store post-backfill)
rows_store = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[df["symbol"] == "BULLAUSDT"].sort_values("date")
        for _, r in df.iterrows(): rows_store.append(r)

def _f(r, k):
    try: return float(r[k])
    except: return float("nan")

funding_r, oi_r, ratio_r, klines_r = {}, {}, {}, {}
for r in rows_store:
    d = r["date"]; mmdd = d[5:]
    funding_r[mmdd] = {"avg": _f(r,"funding_avg"), "min": _f(r,"funding_min"), "max": _f(r,"funding_max")}
    oi_r[mmdd] = _f(r,"oi_usd")
    ratio_r[mmdd] = {"lsr_pos": _f(r,"lsr_pos_r"), "lsr_acc": _f(r,"lsr_acc_r"),
                     "lsr_global": _f(r,"lsr_global_r"), "taker_ratio": _f(r,"taker_ratio")}
    klines_r[mmdd] = {"avg_px": _f(r,"px_avg"), "vol_quote": _f(r,"vol_quote"),
                      "taker_buy_pct": _f(r,"taker_buy_pct")*100 if _f(r,"taker_buy_pct")==_f(r,"taker_buy_pct") else float("nan")}
days_runtime = build_days(funding_r, oi_r, ratio_r, klines_r)

def _hbs_map(days):
    m = {}
    for i in range(len(days)):
        d = days[i]
        mmdd = d.get("date","")
        if len(mmdd) == 10: mmdd = mmdd[5:]
        if not mmdd: continue
        try: r = gom_scan.eval_gom(days, i, cfg, sc)
        except Exception: continue
        gb = r.get("gom_b", {})
        m[mmdd] = (r.get("hedge_base_strict"), gb)
    return m

hbs_calib = _hbs_map(days_calib)
hbs_runtime = _hbs_map(days_runtime)

# WARMUP boundaries
RUNTIME_WARMUP_LAST = "07-02"  # BULLA store first=06-27, warmup i=0..5 = 06-27..07-02
CALIB_WARMUP_LAST = "06-22"    # bulla_result first=06-16, warmup i=0..5 = 06-16..06-22

print(f"  Runtime warmup last day (BULLA store first=06-27): {RUNTIME_WARMUP_LAST}")
print(f"  Calib warmup last day (bulla_result first=06-16): {CALIB_WARMUP_LAST}")
print()
print(f"  {'date':>6}  {'HBS_c':>6} {'HBS_r':>6}  {'B1c/r':>7} {'B3c/r':>7}  {'nhãn':<30}")
print(f"  " + "─" * 78)

def _fmt(v):
    if v is True: return "T"
    if v is False: return "F"
    if v == "N/A-WARMUP": return "WARM"
    return "-"

label_counts = {"SAME": 0, "WARMUP": 0, "RÌA-TRÁI": 0, "(v)-taker-lineage": 0, "KHÁC": 0}
khac_rows = []

for date in sorted(set(hbs_calib.keys()) | set(hbs_runtime.keys())):
    if not ("06-25" <= date <= "07-20"): continue
    c = hbs_calib.get(date, (None, {}))
    r = hbs_runtime.get(date, (None, {}))
    hbs_c, gb_c = c[0], c[1] or {}
    hbs_r, gb_r = r[0], r[1] or {}
    b1_c = gb_c.get("B1"); b1_r = gb_r.get("B1")
    b3_c = gb_c.get("B3"); b3_r = gb_r.get("B3")
    same = (hbs_c == hbs_r)
    if same:
        label = "SAME"; label_counts["SAME"] += 1
    else:
        if hbs_r == "N/A-WARMUP" or hbs_c == "N/A-WARMUP" or date <= RUNTIME_WARMUP_LAST:
            label = "WARMUP"; label_counts["WARMUP"] += 1
        elif date <= "07-03":  # RÌA-TRÁI = ngày đầu post-warmup
            label = "RÌA-TRÁI"; label_counts["RÌA-TRÁI"] += 1
        else:
            # Post-warmup, post-rìa-trái → check B3-only-flip (v)-tag
            other_diff = (b1_c != b1_r) or (gb_c.get("B2") != gb_r.get("B2")) or (gb_c.get("B4") != gb_r.get("B4"))
            b3_diff = (b3_c != b3_r)
            if b3_diff and not other_diff:
                label = "(v)-taker-lineage"; label_counts["(v)-taker-lineage"] += 1
            else:
                label = "KHÁC ★"; label_counts["KHÁC"] += 1
                khac_rows.append((date, hbs_c, hbs_r, gb_c, gb_r))
    b1_str = f"{str(b1_c)[:1]}/{str(b1_r)[:1]}"
    b3_str = f"{str(b3_c)[:1]}/{str(b3_r)[:1]}"
    print(f"  {date:>6}  {_fmt(hbs_c):>6} {_fmt(hbs_r):>6}  {b1_str:>7} {b3_str:>7}  {label:<30}")

print()
print(f"  Summary: SAME={label_counts['SAME']} · WARMUP={label_counts['WARMUP']} · "
      f"RÌA-TRÁI={label_counts['RÌA-TRÁI']} · (v)-taker-lineage={label_counts['(v)-taker-lineage']} · "
      f"KHÁC={label_counts['KHÁC']}")

if label_counts["KHÁC"] > 0:
    print(f"\n  ✗ KHÁC = {label_counts['KHÁC']} — DỪNG mở án (không nuốt)")
    for d, hc, hr, gc, gr in khac_rows:
        print(f"    {d}: calib HBS={hc} (B1={gc.get('B1')} B3={gc.get('B3')}) vs runtime HBS={hr} (B1={gr.get('B1')} B3={gr.get('B3')})")
elif label_counts["(v)-taker-lineage"] == 0:
    print(f"\n  ✓ (v)-taker-lineage=0 hội tụ. Residual chỉ WARMUP/RÌA-TRÁI. R6-⑫ prep enable.")
else:
    print(f"\n  △ (v)-taker-lineage vẫn {label_counts['(v)-taker-lineage']} — chưa hội tụ full")

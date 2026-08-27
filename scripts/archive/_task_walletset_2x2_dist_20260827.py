#!/usr/bin/env python3
"""[WALLETSET 2×2 distributions · KÝ-27/08 · display-only, chờ operator ngưỡng]

Trình PHÂN BỐ 3 metric cho operator điền ngưỡng:
  (i)  |Δbal| — kho OUT-step 1d (%|Δbal|/prev, chỉ Δ<0). Reuse 0.50 đã ký?
  (ii) Δholders/ngày — signed. Nhiễu-nền phẳng vs "lớn" theo tail?
  (iii) stress — vol≥3×med14 ∨ ret≤−5%? Distribution 2 vế.

Universe: fw-139 (data/config/freshwatch_symbols.txt)
Window: 30d rolling ending target=2026-08-25 → 2026-07-26..2026-08-25

Sources:
  · data/raw/nansen_snapshots/{ingest_date}.json — exchange_balance_tokens, exchange_holders
  · data/raw/spot_klines_1d/date={D}/*.parquet — close, base_vol
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td
from statistics import median
import glob

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

REPO = Path("/root/Data_back_test/whale_data") if sys.platform != "win32" else Path("D:/Data back test/whale_data")
SNAPSHOTS_DIR = REPO / "data/raw/nansen_snapshots"
SYMBOLS_TXT = REPO / "data/config/freshwatch_symbols.txt"
SPOT_DIR = REPO / "data/raw/spot_klines_1d"

TARGET_END = _date(2026, 8, 25)
WINDOW_DAYS = 30

symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
tokens = [s[:-4] if s.endswith("USDT") else s for s in symbols]
print(f"# fw-{len(symbols)} · window {TARGET_END - _td(days=WINDOW_DAYS-1)} .. {TARGET_END}")

# ─── Load balance + holders series ───
BAL = {}
HOLDERS = {}
snap_dates = []
for p in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    ingest = p.stem
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception: continue
    if not isinstance(d, dict): continue
    snap_dates.append(ingest)
    for r in d.get("rows", []):
        if not r: continue
        sym = (r.get("symbol") or "").upper()
        if not sym: continue
        bal = r.get("exchange_balance_tokens")
        hol = r.get("exchange_holders")
        if bal is not None:
            try: BAL.setdefault(sym, {})[ingest] = float(bal)
            except: pass
        if hol is not None:
            try: HOLDERS.setdefault(sym, {})[ingest] = int(hol)
            except: pass

print(f"# snapshots loaded: {len(snap_dates)}")

# ─── (i) OUT-step distribution: |Δbal|/prev when Δ<0, per (token, day) ───
# bal_date = ingest_date - 1 (T-1 UTC semantic per spec §5)
out_step_pcts = []  # signed pct (negative)
for tok in tokens:
    series = BAL.get(tok, {})
    for ingest in sorted(series.keys()):
        d_ingest = _date.fromisoformat(ingest)
        bal_date = d_ingest - _td(days=1)
        if bal_date < TARGET_END - _td(days=WINDOW_DAYS-1) or bal_date > TARGET_END: continue
        prev_ingest = (d_ingest - _td(days=1)).isoformat()
        if prev_ingest not in series: continue
        b_now = series[ingest]; b_prev = series[prev_ingest]
        if b_prev <= 0: continue
        pct = (b_now - b_prev) / b_prev
        if pct < 0:  # OUT-step only
            out_step_pcts.append(pct * 100)  # store as %

print(f"\n═══ (i) OUT-STEP |Δbal|/prev distribution — 1d, fw-{len(tokens)} × ~{WINDOW_DAYS}d window ═══")
print(f"n_samples: {len(out_step_pcts)} out-steps observed")
if out_step_pcts:
    abs_pcts = [abs(p) for p in out_step_pcts]
    abs_pcts.sort()
    # Percentiles
    def pctl(arr, p):
        if not arr: return None
        i = int(len(arr) * p / 100)
        return arr[min(i, len(arr)-1)]
    print(f"  |Δbal| percentiles: p50={pctl(abs_pcts,50):.2f}% · p75={pctl(abs_pcts,75):.2f}% · p90={pctl(abs_pcts,90):.2f}% · p95={pctl(abs_pcts,95):.2f}% · p99={pctl(abs_pcts,99):.2f}% · max={abs_pcts[-1]:.2f}%")
    # Bucket distribution
    buckets = [(0,5),(5,10),(10,20),(20,50),(50,80),(80,100)]
    print(f"  bucket counts (|Δbal| %):")
    for lo, hi in buckets:
        c = sum(1 for p in abs_pcts if lo <= p < hi)
        print(f"    [{lo:>3}, {hi:>3})%: {c:>4} ({c/len(abs_pcts)*100:.1f}%)")
    # ≥50% (VERIFY-WALLETSET ký threshold)
    c50 = sum(1 for p in abs_pcts if p >= 50)
    c30 = sum(1 for p in abs_pcts if p >= 30)
    c20 = sum(1 for p in abs_pcts if p >= 20)
    print(f"  ≥20% : {c20:>4} ({c20/len(abs_pcts)*100:.1f}% of out-steps)")
    print(f"  ≥30% : {c30:>4} ({c30/len(abs_pcts)*100:.1f}%)")
    print(f"  ≥50% (VERIFY-WALLETSET ký): {c50:>4} ({c50/len(abs_pcts)*100:.1f}%)")

# ─── (ii) Δholders distribution ───
holder_deltas = []
for tok in tokens:
    series = HOLDERS.get(tok, {})
    for ingest in sorted(series.keys()):
        d_ingest = _date.fromisoformat(ingest)
        bal_date = d_ingest - _td(days=1)
        if bal_date < TARGET_END - _td(days=WINDOW_DAYS-1) or bal_date > TARGET_END: continue
        prev_ingest = (d_ingest - _td(days=1)).isoformat()
        if prev_ingest not in series: continue
        d_holders = series[ingest] - series[prev_ingest]
        holder_deltas.append(d_holders)

print(f"\n═══ (ii) Δholders/ngày distribution — signed, fw-{len(tokens)} × ~{WINDOW_DAYS}d ═══")
print(f"n_samples: {len(holder_deltas)}")
if holder_deltas:
    abs_d = sorted([abs(d) for d in holder_deltas])
    print(f"  |Δholders| percentiles: p50={pctl(abs_d,50)} · p75={pctl(abs_d,75)} · p90={pctl(abs_d,90)} · p95={pctl(abs_d,95)} · p99={pctl(abs_d,99)} · max={abs_d[-1]}")
    # Bucket
    buckets_h = [(0,1),(1,2),(2,3),(3,5),(5,10),(10,20),(20,50),(50,999)]
    print(f"  bucket counts (|Δholders|):")
    for lo, hi in buckets_h:
        c = sum(1 for d in abs_d if lo <= d < hi)
        if c > 0: print(f"    [{lo:>3}, {hi:>3}): {c:>4} ({c/len(abs_d)*100:.1f}%)")
    # Signed breakdown
    n_zero = sum(1 for d in holder_deltas if d == 0)
    n_pos = sum(1 for d in holder_deltas if d > 0)
    n_neg = sum(1 for d in holder_deltas if d < 0)
    print(f"  signed: Δ=0 (phẳng): {n_zero} ({n_zero/len(holder_deltas)*100:.1f}%) · Δ>0: {n_pos} ({n_pos/len(holder_deltas)*100:.1f}%) · Δ<0: {n_neg} ({n_neg/len(holder_deltas)*100:.1f}%)")
    # Tail (|Δ|≥2, ≥3, ≥5)
    for thr in [1, 2, 3, 5]:
        c = sum(1 for d in abs_d if d >= thr)
        print(f"  |Δholders|≥{thr}: {c} ({c/len(abs_d)*100:.1f}%)")

# ─── (iii) STRESS distribution: vol≥3×med14 ∨ ret1d≤−5% ───
vol_ratios = []  # vol / med14
ret_1d = []
for tok in tokens:
    sym = tok + "USDT"
    # Collect vol series 60d for percentile
    day_frames = []
    d0 = TARGET_END - _td(days=WINDOW_DAYS + 20)  # extra 20d for med14 rolling
    d1 = TARGET_END
    cur = d0
    vols_per_day = {}
    closes_per_day = {}
    while cur <= d1:
        p = SPOT_DIR / f"date={cur.isoformat()}"
        try:
            if p.exists():
                df = pd.read_parquet(p)
                r = df[df["symbol"] == sym]
                if not r.empty:
                    vols_per_day[cur.isoformat()] = float(r.iloc[0]["base_vol"])
                    closes_per_day[cur.isoformat()] = float(r.iloc[0]["close"])
        except Exception: pass
        cur += _td(days=1)
    # For each day in target window, compute vol/med14 + ret1d
    for i in range(WINDOW_DAYS):
        d = TARGET_END - _td(days=WINDOW_DAYS - 1 - i)
        d_str = d.isoformat()
        if d_str not in vols_per_day: continue
        # med14 = median of vol[d-14..d-1]
        prev_vols = [vols_per_day[(d - _td(days=k)).isoformat()] for k in range(1, 15)
                     if (d - _td(days=k)).isoformat() in vols_per_day]
        if len(prev_vols) < 14: continue
        m14 = median(prev_vols)
        if m14 > 0:
            vol_ratios.append(vols_per_day[d_str] / m14)
        # ret1d
        d_prev = (d - _td(days=1)).isoformat()
        if d_prev in closes_per_day and closes_per_day[d_prev] > 0:
            ret = (closes_per_day[d_str] - closes_per_day[d_prev]) / closes_per_day[d_prev]
            ret_1d.append(ret * 100)  # store as %

print(f"\n═══ (iii) STRESS distribution — vol/med14 + ret1d, fw-{len(tokens)} × {WINDOW_DAYS}d ═══")
print(f"n_vol_samples: {len(vol_ratios)} · n_ret_samples: {len(ret_1d)}")
if vol_ratios:
    vr = sorted(vol_ratios)
    print(f"  vol/med14 percentiles: p50={pctl(vr,50):.2f}× · p75={pctl(vr,75):.2f}× · p90={pctl(vr,90):.2f}× · p95={pctl(vr,95):.2f}× · p99={pctl(vr,99):.2f}× · max={vr[-1]:.2f}×")
    # Bucket
    buckets_v = [(0,1),(1,2),(2,3),(3,5),(5,10),(10,20),(20,100)]
    print(f"  bucket counts (vol/med14):")
    for lo, hi in buckets_v:
        c = sum(1 for r in vr if lo <= r < hi)
        if c > 0: print(f"    [{lo:>3}, {hi:>3})×: {c:>4} ({c/len(vr)*100:.1f}%)")
    for thr in [2, 3, 5, 10]:
        c = sum(1 for r in vr if r >= thr)
        print(f"  vol/med14≥{thr}×: {c} ({c/len(vr)*100:.1f}%)")
if ret_1d:
    rs = sorted(ret_1d)
    print(f"\n  ret1d percentiles: p1={pctl(rs,1):.2f}% · p5={pctl(rs,5):.2f}% · p10={pctl(rs,10):.2f}% · p50={pctl(rs,50):.2f}% · p90={pctl(rs,90):.2f}% · p95={pctl(rs,95):.2f}% · p99={pctl(rs,99):.2f}%")
    # Distribution of ret ≤ -X%
    for thr in [-3, -5, -8, -10, -15, -20]:
        c = sum(1 for r in rs if r <= thr)
        print(f"  ret1d≤{thr}%: {c} ({c/len(rs)*100:.1f}%)")

# Combined stress: vol≥3× AND ret≤-5%
if vol_ratios and ret_1d:
    # Need per (token, day) pairing — recompute
    stress_pairs = []
    for tok in tokens:
        sym = tok + "USDT"
        vols_per_day = {}
        closes_per_day = {}
        cur = TARGET_END - _td(days=WINDOW_DAYS + 20)
        while cur <= TARGET_END:
            p = SPOT_DIR / f"date={cur.isoformat()}"
            try:
                if p.exists():
                    df = pd.read_parquet(p)
                    r = df[df["symbol"] == sym]
                    if not r.empty:
                        vols_per_day[cur.isoformat()] = float(r.iloc[0]["base_vol"])
                        closes_per_day[cur.isoformat()] = float(r.iloc[0]["close"])
            except Exception: pass
            cur += _td(days=1)
        for i in range(WINDOW_DAYS):
            d = TARGET_END - _td(days=WINDOW_DAYS - 1 - i)
            d_str = d.isoformat()
            if d_str not in vols_per_day: continue
            prev_vols = [vols_per_day[(d - _td(days=k)).isoformat()] for k in range(1, 15)
                         if (d - _td(days=k)).isoformat() in vols_per_day]
            if len(prev_vols) < 14: continue
            m14 = median(prev_vols)
            if m14 <= 0: continue
            vr = vols_per_day[d_str] / m14
            d_prev = (d - _td(days=1)).isoformat()
            if d_prev not in closes_per_day or closes_per_day[d_prev] <= 0: continue
            r1d = (closes_per_day[d_str] - closes_per_day[d_prev]) / closes_per_day[d_prev] * 100
            stress_pairs.append((tok, d_str, vr, r1d))
    n = len(stress_pairs)
    n_vol3 = sum(1 for _,_,v,_ in stress_pairs if v >= 3)
    n_ret5 = sum(1 for _,_,_,r in stress_pairs if r <= -5)
    n_vol3_or_ret5 = sum(1 for _,_,v,r in stress_pairs if v >= 3 or r <= -5)
    n_vol3_and_ret5 = sum(1 for _,_,v,r in stress_pairs if v >= 3 and r <= -5)
    print(f"\n  Combined stress (vol≥3× ∨ ret≤-5%) — n_pairs={n}:")
    print(f"    vol≥3×:              {n_vol3} ({n_vol3/n*100:.1f}%)")
    print(f"    ret≤-5%:             {n_ret5} ({n_ret5/n*100:.1f}%)")
    print(f"    vol≥3× ∨ ret≤-5%:    {n_vol3_or_ret5} ({n_vol3_or_ret5/n*100:.1f}%)")
    print(f"    vol≥3× ∧ ret≤-5%:    {n_vol3_and_ret5} ({n_vol3_and_ret5/n*100:.1f}%)")

print("\n═══ ĐỀ XUẤT NGƯỠNG (chờ operator điền) ═══")
print("  (i)   |Δbal|: [ ]% (tái dùng 0.50 = 50%? · phân bố trên)")
print("  (ii)  Δholders: [ ]|Δholders|≥? · signed/abs?")
print("  (iii) stress: vol/med14≥[ ]× ∨ ret1d≤[ ]%")
print("  Sau khi có ngưỡng → matrix 2×2 auto-tag: CONCENTRATED · BROAD-QUIET · BROAD-STRESS")

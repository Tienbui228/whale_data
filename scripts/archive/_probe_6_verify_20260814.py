"""
Phase 6 diagnostic — verify h1/h2 computation là per-hour, không phải daily aggregate.
Trace:
  [1] BANK 2026-07-05 (build): danh sách giờ + ret + taker_pct + phân nhóm + h1
  [2] BANANAS31 2026-07-10 (negative): same trace, verify NaN reason
  [3] h2_oiw BANK sample day: ΔOI⁺ per hour + join ret + formula direction

Run on VPS: python3 _probe_6_verify_20260814.py
"""

import sys, json
from pathlib import Path
from datetime import date

import pandas as pd

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

MS = 3_600_000

funding: dict = {}
fp = REPO / "data" / "config" / "funding_intervals.json"
if fp.exists():
    with open(fp) as f:
        funding = json.load(f)

def settle_hrs(sym):
    iv = funding.get(sym, 8)
    if iv <= 1:
        return set()
    return {h for h in range(0, 24, iv)}

def load_klines(dt, sym):
    pq = RAW / "klines_1h" / f"date={dt}" / "part-0.parquet"
    df = pd.read_parquet(pq)
    df = df[df["symbol"] == sym].copy()
    df = df.drop_duplicates(subset=["symbol","as_of_ts_ms"], keep="first")
    df = df.sort_values("as_of_ts_ms").reset_index(drop=True)
    df["hour_utc"] = (df["as_of_ts_ms"] // MS) % 24
    df["ret"]      = (df["close"] - df["open"]) / df["open"].clip(lower=1e-12)
    df["tbuy_pct"] = df["taker_buy_base_vol"] / df["base_volume"].clip(lower=1e-12)
    df["rng"]      = df["high"] - df["low"]
    return df

def load_oi(dt, sym):
    pq = RAW / "oi_hist_1h" / f"date={dt}" / "part-0.parquet"
    if not pq.exists():
        return pd.DataFrame()
    df = pd.read_parquet(pq)
    df = df[df["symbol"] == sym].copy()
    df = df.drop_duplicates(subset=["symbol","as_of_ts_ms"], keep="first")
    df = df.sort_values("as_of_ts_ms").reset_index(drop=True)
    df["hour_utc"] = (df["as_of_ts_ms"] // MS) % 24
    df["delta_oi"] = df["sum_open_interest"].diff()
    df["doi_pos"]  = df["delta_oi"].clip(lower=0.0)
    return df

SEP = "=" * 90

# ─────────────────────────────────────────────────────────────────────────────────
# [1] BANK 2026-07-05
# ─────────────────────────────────────────────────────────────────────────────────
print(SEP)
print("[1] BANK 2026-07-05 — h1_skew hourly trace")
print(SEP)

sym, dt = "BANKUSDT", "2026-07-05"
iv = funding.get(sym, 8)
excl = settle_hrs(sym)
print(f"  symbol={sym}  interval_h={iv}  settle_hours_excl={sorted(excl)}")
print()

df = load_klines(dt, sym)
print(f"  Total rows after dedup: {len(df)}  (should be ≤24)")
print()
print(f"  {'hour':>5} {'open':>10} {'close':>10} {'ret%':>7} {'tbuy_vol':>12} "
      f"{'vol':>12} {'tbuy%':>7} {'excl':>6} {'group':>8}")
print(f"  {'─'*5} {'─'*10} {'─'*10} {'─'*7} {'─'*12} {'─'*12} {'─'*7} {'─'*6} {'─'*8}")

for _, row in df.iterrows():
    h = int(row["hour_utc"])
    excl_tag = "SETTLE" if h in excl else ""
    ret_pct  = row["ret"] * 100
    tbuy_pct = row["tbuy_pct"] * 100

    grp = ""
    if excl_tag == "":
        if row["ret"] < 0:
            grp = "NEG_HR"
        elif row["ret"] > 0:
            grp = "POS_HR"
        else:
            grp = "ZERO"

    print(f"  {h:>5} {row['open']:>10.5f} {row['close']:>10.5f} {ret_pct:>+7.3f}% "
          f"{row['taker_buy_base_vol']:>12.2f} {row['base_volume']:>12.2f} "
          f"{tbuy_pct:>7.2f}% {excl_tag:>6} {grp:>8}")

# Filter
df_h1 = df[~df["hour_utc"].isin(excl)].copy()
neg_h = df_h1[df_h1["ret"] < 0]
pos_h = df_h1[df_h1["ret"] > 0]

print()
print(f"  After excluding settle hours ({sorted(excl)}): {len(df_h1)} rows")
print(f"  ret < 0 group: n={len(neg_h)}")
print(f"    hours: {sorted(neg_h['hour_utc'].tolist())}")
if len(neg_h) > 0:
    print(f"    tbuy% values: {[f'{v*100:.2f}' for v in neg_h['tbuy_pct'].tolist()]}")
    print(f"    mean(tbuy% | ret<0) = {neg_h['tbuy_pct'].mean()*100:.4f}%")

print(f"  ret > 0 group: n={len(pos_h)}")
print(f"    hours: {sorted(pos_h['hour_utc'].tolist())}")
if len(pos_h) > 0:
    print(f"    tbuy% values: {[f'{v*100:.2f}' for v in pos_h['tbuy_pct'].tolist()]}")
    print(f"    mean(tbuy% | ret>0) = {pos_h['tbuy_pct'].mean()*100:.4f}%")

if len(neg_h) >= 5 and len(pos_h) >= 5:
    h1 = neg_h["tbuy_pct"].mean() - pos_h["tbuy_pct"].mean()
    print(f"\n  h1_skew = {neg_h['tbuy_pct'].mean()*100:.4f}% − {pos_h['tbuy_pct'].mean()*100:.4f}%"
          f" = {h1*100:+.4f}%  (raw={h1:.6f})")
    print(f"  → MATCHES stored h1_skew=+0.0198 ? (stored×1={0.0198:.4f} vs computed={h1:.4f})")
else:
    print(f"\n  h1_skew = NaN (neg_n={len(neg_h)}, pos_n={len(pos_h)}, need ≥5 each)")

# ─────────────────────────────────────────────────────────────────────────────────
# [2] BANANAS31 2026-07-10
# ─────────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("[2] BANANAS31 2026-07-10 — h1_skew hourly trace (stored=NaN)")
print(SEP)

sym2, dt2 = "BANANAS31USDT", "2026-07-10"
iv2 = funding.get(sym2, 8)
excl2 = settle_hrs(sym2)
print(f"  symbol={sym2}  interval_h={iv2}  settle_hours_excl={sorted(excl2)}")
print()

df2 = load_klines(dt2, sym2)
print(f"  Total rows after dedup: {len(df2)}")
print()
print(f"  {'hour':>5} {'open':>10} {'close':>10} {'ret%':>7} {'tbuy_vol':>12} "
      f"{'vol':>12} {'tbuy%':>7} {'excl':>6} {'group':>8}")
print(f"  {'─'*5} {'─'*10} {'─'*10} {'─'*7} {'─'*12} {'─'*12} {'─'*7} {'─'*6} {'─'*8}")

for _, row in df2.iterrows():
    h = int(row["hour_utc"])
    excl_tag = "SETTLE" if h in excl2 else ""
    ret_pct  = row["ret"] * 100
    tbuy_pct = row["tbuy_pct"] * 100
    grp = ""
    if excl_tag == "":
        if row["ret"] < 0:
            grp = "NEG_HR"
        elif row["ret"] > 0:
            grp = "POS_HR"
        else:
            grp = "ZERO"
    print(f"  {h:>5} {row['open']:>10.5f} {row['close']:>10.5f} {ret_pct:>+7.3f}% "
          f"{row['taker_buy_base_vol']:>12.2f} {row['base_volume']:>12.2f} "
          f"{tbuy_pct:>7.2f}% {excl_tag:>6} {grp:>8}")

df2_h1 = df2[~df2["hour_utc"].isin(excl2)].copy()
neg2 = df2_h1[df2_h1["ret"] < 0]
pos2 = df2_h1[df2_h1["ret"] > 0]

print()
print(f"  After excl settle: {len(df2_h1)} rows")
print(f"  ret<0: n={len(neg2)}  ret>0: n={len(pos2)}")
if len(neg2) < 5 or len(pos2) < 5:
    print(f"  → NaN reason: {'neg_n<5' if len(neg2)<5 else 'pos_n<5'}")
if len(neg2) > 0:
    print(f"  hours_neg: {sorted(neg2['hour_utc'].tolist())}")
    print(f"  tbuy% neg: {[f'{v*100:.2f}' for v in neg2['tbuy_pct'].tolist()]}")
if len(pos2) > 0:
    print(f"  hours_pos: {sorted(pos2['hour_utc'].tolist())}")
    print(f"  tbuy% pos: {[f'{v*100:.2f}' for v in pos2['tbuy_pct'].tolist()]}")

if len(neg2) >= 5 and len(pos2) >= 5:
    h1_2 = neg2["tbuy_pct"].mean() - pos2["tbuy_pct"].mean()
    print(f"  h1_skew = {h1_2:.6f}")
else:
    print(f"  → h1_skew = NaN confirmed")

# ─────────────────────────────────────────────────────────────────────────────────
# [3] h2_oiw direction — BANK 2026-07-12 (h2=0.787 stored)
# ─────────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("[3] h2_oiw direction — BANK 2026-07-12 (stored h2=0.787)")
print(SEP)
print("  Formula: h2 = Σ ΔOI⁺(giờ ret≤0) / Σ ΔOI⁺(mọi giờ)")
print("  High h2 → OI tăng chủ yếu vào giờ GIÁ GIẢM (= gom vào yếu = accumulation)")
print("  Low h2  → OI tăng chủ yếu vào giờ GIÁ TĂNG (= mua đà = FOMO / pump)\n")

sym3, dt3 = "BANKUSDT", "2026-07-12"
df3_k = load_klines(dt3, sym3)
df3_o = load_oi(dt3, sym3)

print(f"  klines rows: {len(df3_k)}  OI rows: {len(df3_o)}")
print()

if df3_o.empty:
    print("  OI MISSING for this day — pick different date")
else:
    # Build the join table (same logic as compute_symbol)
    sk_hr = df3_k[["hour_utc","ret"]].set_index("hour_utc")
    so_hr = df3_o.dropna(subset=["delta_oi"])[["hour_utc","doi_pos"]].set_index("hour_utc")
    merged = so_hr.join(sk_hr, how="inner")

    print(f"  OI interval_h for join (unique hours in OI): {sorted(df3_o['hour_utc'].unique())}")
    print()
    print(f"  {'hour':>5} {'OI_usd':>14} {'delta_OI':>12} {'DOI+':>10} {'ret%':>7} {'dir':>8}")
    print(f"  {'─'*5} {'─'*14} {'─'*12} {'─'*10} {'─'*7} {'─'*8}")

    for h in sorted(df3_o["hour_utc"].unique()):
        oi_row = df3_o[df3_o["hour_utc"] == h].iloc[-1]
        k_row  = df3_k[df3_k["hour_utc"] == h]
        if k_row.empty:
            ret_pct, dir_s = float("nan"), "?"
        else:
            ret_pct = k_row.iloc[0]["ret"] * 100
            dir_s   = "NEG_HR" if ret_pct < 0 else ("POS_HR" if ret_pct > 0 else "ZERO")
        doi = oi_row["doi_pos"] if not pd.isna(oi_row["doi_pos"]) else 0.0
        d_oi = oi_row["delta_oi"] if not pd.isna(oi_row["delta_oi"]) else float("nan")
        oi_val = oi_row["sum_open_interest"]
        print(f"  {h:>5} {oi_val:>14,.0f} {d_oi:>12,.0f} {doi:>10,.0f} {ret_pct:>+7.3f}% {dir_s:>8}")

    sum_all = float(merged["doi_pos"].sum())
    sum_neg = float(merged.loc[merged["ret"] <= 0, "doi_pos"].sum())
    h2_calc = sum_neg / sum_all if sum_all > 0 else float("nan")

    print()
    print(f"  Σ ΔOI⁺ (mọi giờ)  = {sum_all:,.0f}")
    print(f"  Σ ΔOI⁺ (ret≤0 hr) = {sum_neg:,.0f}")
    print(f"  h2_oiw = {sum_neg:,.0f} / {sum_all:,.0f} = {h2_calc:.4f}")
    print(f"  Stored h2=0.7866 vs computed={h2_calc:.4f}  → {'MATCH' if abs(h2_calc - 0.7866) < 0.001 else 'MISMATCH!'}")
    print()
    print(f"  DIRECTION CHECK:")
    print(f"  h2=0.79 → ~79% of OI increase happened on ret≤0 hours (price-down hours)")
    print(f"  = OI grows when PRICE DROPS = smart money ABSORBING sells = ACCUMULATION signal")
    print()
    print(f"  But BANK build window median h2=0.411 (41% of OI+ on down-hours)")
    print(f"  → 59% of OI builds on UP-hours during build window")
    print(f"  → Price grinds UP while OI builds on UP-hours = price-led OI = FOMO / trend-follow?")
    print(f"  → OR: grind means mostly green hours, so RATIO naturally tilts to green-hour OI")

    # Also show neg_hours vs pos_hours count
    neg_hr_count = int((df3_k["ret"] < 0).sum())
    pos_hr_count = int((df3_k["ret"] > 0).sum())
    print()
    print(f"  Hours with ret<0: {neg_hr_count}   Hours with ret>0: {pos_hr_count}  "
          f"(this ratio affects h2 base rate)")

print()
print("=" * 90)
print("DONE — paste [1][2][3] to operator. DỪNG.")

"""
Probe [7] — BANK 2026-07-12: trace n_neg/n_pos mâu thuẫn.
Probe [B] trước: n_neg=14 n_pos=9. Commit sample: n_neg=12 n_pos=11.
Tổng 23 khớp, phân bố đổi. Mục tiêu:
  [1] Mỗi giờ trong klines: ret, phân loại (≤0 / >0)
  [2] Mỗi giờ trong OI (sau dedup): doi_pos, có duplicate hour_utc không?
  [3] Merged DataFrame toàn bộ row — xem cartesian product?
  [4] n_neg, n_pos, rate_neg, rate_pos, h2r chính thức.

Run on VPS: python3 _probe_7_bank_jul12_trace_20260815.py
"""

import sys, math
from pathlib import Path
import pandas as pd

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"
sys.path.insert(0, str(REPO))

MS  = 3_600_000
SYM = "BANKUSDT"
DT  = "2026-07-12"

SEP = "=" * 80
print(SEP)
print(f"[7] BANK {DT} — n_neg/n_pos trace dứt điểm")
print(SEP)

# ── Load + dedup ───────────────────────────────────────────────────────────────
df_k_raw = pd.read_parquet(RAW / "klines_1h" / f"date={DT}" / "part-0.parquet")
df_k_raw = df_k_raw[df_k_raw["symbol"] == SYM].copy()
print(f"\n[klines] raw rows: {len(df_k_raw)}")

df_k = df_k_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
df_k = df_k.sort_values("as_of_ts_ms").reset_index(drop=True)
df_k["hour_utc"] = (df_k["as_of_ts_ms"] // MS) % 24
df_k["ret"]      = (df_k["close"] - df_k["open"]) / df_k["open"].clip(lower=1e-12)
print(f"[klines] after dedup(symbol,as_of_ts_ms): {len(df_k)} rows")

df_o_raw = pd.read_parquet(RAW / "oi_hist_1h" / f"date={DT}" / "part-0.parquet")
df_o_raw = df_o_raw[df_o_raw["symbol"] == SYM].copy()
print(f"[OI]     raw rows: {len(df_o_raw)}")

df_o = df_o_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
df_o = df_o.sort_values("as_of_ts_ms").reset_index(drop=True)
df_o["hour_utc"] = (df_o["as_of_ts_ms"] // MS) % 24
df_o["delta_oi"] = df_o["sum_open_interest"].diff()
df_o["doi_pos"]  = df_o["delta_oi"].clip(lower=0.0)
print(f"[OI]     after dedup(symbol,as_of_ts_ms): {len(df_o)} rows")

# ── [1] Klines per-hour ────────────────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[1] Klines per hour — ret + phân loại")
print(f"  {'hr':>4} {'as_of_ts_ms':>16} {'open':>10} {'close':>10} {'ret%':>8} {'group':>10}")
print(f"  {'──':>4} {'─'*16} {'─'*10} {'─'*10} {'─'*8} {'─'*10}")
for _, row in df_k.iterrows():
    h   = int(row["hour_utc"])
    ret = row["ret"]
    grp = "NEG(≤0)" if ret <= 0 else "POS(>0)"
    print(f"  {h:>4} {int(row['as_of_ts_ms']):>16} {row['open']:>10.5f} {row['close']:>10.5f} "
          f"{ret*100:>+8.3f}% {grp:>10}")
dup_k_hours = df_k["hour_utc"].duplicated().sum()
print(f"\n  Duplicate hour_utc trong klines: {dup_k_hours}")

# ── [2] OI per-hour ────────────────────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[2] OI per hour — doi_pos + duplicate hour_utc check")
print(f"  {'hr':>4} {'as_of_ts_ms':>16} {'oi_usd':>14} {'delta_oi':>12} {'doi_pos':>12}")
print(f"  {'──':>4} {'─'*16} {'─'*14} {'─'*12} {'─'*12}")
df_o_valid = df_o.dropna(subset=["delta_oi"])
for _, row in df_o.iterrows():
    h = int(row["hour_utc"])
    doi = row["doi_pos"] if not pd.isna(row["doi_pos"]) else float("nan")
    d   = row["delta_oi"] if not pd.isna(row["delta_oi"]) else float("nan")
    print(f"  {h:>4} {int(row['as_of_ts_ms']):>16} {row['sum_open_interest']:>14,.0f} "
          f"{d:>12,.0f} {doi:>12,.0f}")
dup_o_hours = df_o_valid["hour_utc"].duplicated().sum()
print(f"\n  Duplicate hour_utc trong OI (sau dropna delta_oi): {dup_o_hours}")
if dup_o_hours > 0:
    print("  *** CÓ DUPLICATE hour_utc trong OI → join sẽ cartesian product ***")
    dup_hrs = df_o_valid[df_o_valid["hour_utc"].duplicated(keep=False)]["hour_utc"].unique()
    print(f"  Duplicate hours: {sorted(dup_hrs)}")

# ── [3] Merged DataFrame đầy đủ ───────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[3] Merged DataFrame (so_hr.join(sk_hr, inner)) — toàn bộ row")

sk_hr  = df_k[["hour_utc", "ret"]].set_index("hour_utc")
so_hr  = df_o_valid[["hour_utc", "doi_pos"]].set_index("hour_utc")
merged = so_hr.join(sk_hr, how="inner")

print(f"  Merged rows: {len(merged)}  (sk_hr unique hours={df_k['hour_utc'].nunique()}, "
      f"so_hr rows={len(so_hr)})")
print()
print(f"  {'idx(hr)':>8} {'doi_pos':>12} {'ret%':>8} {'group':>10}")
print(f"  {'─'*8} {'─'*12} {'─'*8} {'─'*10}")
for h, row in merged.iterrows():
    doi = row["doi_pos"]
    ret = row["ret"]
    grp = "NEG(≤0)" if ret <= 0 else "POS(>0)"
    print(f"  {h:>8} {doi:>12,.0f} {ret*100:>+8.3f}% {grp:>10}")

# ── [4] n, Σ, rate, h2r ────────────────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[4] n / Σ ΔOI⁺ / rate / h2r chính thức")

neg_mask = merged["ret"] <= 0
pos_mask = merged["ret"] > 0
n_neg    = int(neg_mask.sum())
n_pos    = int(pos_mask.sum())
sum_neg  = float(merged.loc[neg_mask, "doi_pos"].sum())
sum_pos  = float(merged.loc[pos_mask, "doi_pos"].sum())
sum_all  = float(merged["doi_pos"].sum())
h2_share = sum_neg / sum_all if sum_all > 0 else float("nan")

print(f"\n  n_neg (ret≤0): {n_neg}")
print(f"  n_pos (ret>0): {n_pos}")
print(f"  Σ ΔOI⁺ (neg): {sum_neg:>16,.0f}")
print(f"  Σ ΔOI⁺ (pos): {sum_pos:>16,.0f}")
print(f"  Σ ΔOI⁺ (all): {sum_all:>16,.0f}")
print(f"  h2_old_share: {h2_share:.6f}")

if n_neg >= 5 and n_pos >= 5 and sum_neg > 0 and sum_pos > 0:
    rate_neg = sum_neg / n_neg
    rate_pos = sum_pos / n_pos
    h2r      = rate_neg / rate_pos
    h2r_log  = math.log(h2r)
    print(f"\n  rate_neg = {sum_neg:,.0f} / {n_neg} = {rate_neg:>14,.2f}")
    print(f"  rate_pos = {sum_pos:,.0f} / {n_pos} = {rate_pos:>14,.2f}")
    print(f"\n  h2r      = {rate_neg:,.2f} / {rate_pos:,.2f} = {h2r:.6f}")
    print(f"  h2r_log  = ln({h2r:.6f}) = {h2r_log:.6f}")
    print(f"  rate_neg_usd_hr = {rate_neg:,.2f}")
else:
    print(f"\n  GUARD triggered → NaN (n_neg={n_neg}, n_pos={n_pos})")

print()
print(SEP)
print("VERDICT:")
print(f"  n_neg={n_neg}  n_pos={n_pos}  tổng={n_neg+n_pos}")
print("  Probe[B]-trước đếm: n_neg=14 n_pos=9  → đúng hay sai?")
print("  Commit sample paste: n_neg=12 n_pos=11 → đúng hay sai?")
print("  Bảng [3] là nguồn sự thật. DỪNG.")
print(SEP)

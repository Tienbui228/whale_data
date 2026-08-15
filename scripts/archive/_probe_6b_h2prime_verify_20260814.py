"""
Probe [B] — verify h2′ rate-normalized ĐÚNG công thức, không phải share-based đội tên.
Case: BANK 2026-07-12 (h2_old=0.7866 đã trace _probe_6_verify_20260814.py).
h2′ PHẢI khác h2_old nếu normalize đúng.

Công thức tại điểm dùng (scripts/compute_h_daily.py :: compute_h2_prime):
  rate_neg = mean(ΔOI⁺ | giờ ret≤0)  =  Σ ΔOI⁺(red) / n_red_hrs
  rate_pos = mean(ΔOI⁺ | giờ ret>0)  =  Σ ΔOI⁺(green) / n_green_hrs
  h2_prime = rate_neg − rate_pos      ← KHÔNG phải share, KHÔNG phải ratio

Run on VPS: python3 _probe_6b_h2prime_verify_20260814.py
"""

import sys, json
from pathlib import Path
import pandas as pd

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts.compute_h_daily import compute_h2_prime

MS = 3_600_000
funding: dict = {}
fp = REPO / "data" / "config" / "funding_intervals.json"
if fp.exists():
    with open(fp) as f:
        funding = json.load(f)

SYM, DT = "BANKUSDT", "2026-07-12"
H2_OLD  = 0.7866   # share-based từ _probe_6_verify_20260814.py

print("=" * 80)
print(f"[B] h2′ verify — {SYM} {DT}")
print("=" * 80)
print(f"\n  Công thức tại điểm dùng (compute_h2_prime):")
print(f"    rate_neg = Σ ΔOI⁺(ret≤0) / n_neg_hrs")
print(f"    rate_pos = Σ ΔOI⁺(ret>0) / n_pos_hrs")
print(f"    h2_prime = rate_neg − rate_pos   [KHÔNG phải share [0,1], KHÔNG phải ratio]")
print()

# Load raw klines + OI
df_k = pd.read_parquet(RAW / "klines_1h" / f"date={DT}" / "part-0.parquet")
df_k = df_k[df_k["symbol"] == SYM].copy()
df_k = df_k.drop_duplicates(subset=["symbol","as_of_ts_ms"], keep="first")
df_k = df_k.sort_values("as_of_ts_ms").reset_index(drop=True)
df_k["hour_utc"] = (df_k["as_of_ts_ms"] // MS) % 24
df_k["ret"]      = (df_k["close"] - df_k["open"]) / df_k["open"].clip(lower=1e-12)

df_o_raw = pd.read_parquet(RAW / "oi_hist_1h" / f"date={DT}" / "part-0.parquet")
df_o_raw = df_o_raw[df_o_raw["symbol"] == SYM].copy()
df_o_raw = df_o_raw.drop_duplicates(subset=["symbol","as_of_ts_ms"], keep="first")
df_o_raw = df_o_raw.sort_values("as_of_ts_ms").reset_index(drop=True)

# ── Manual trace (same logic as compute_h2_prime) ─────────────────────────────────
df_o = df_o_raw.copy()
df_o["hour_utc"] = (df_o["as_of_ts_ms"] // MS) % 24
df_o["delta_oi"] = df_o["sum_open_interest"].diff()
df_o["doi_pos"]  = df_o["delta_oi"].clip(lower=0.0)

sk_hr  = df_k[["hour_utc","ret"]].set_index("hour_utc")
so_hr  = df_o.dropna(subset=["delta_oi"])[["hour_utc","doi_pos"]].set_index("hour_utc")
merged = so_hr.join(sk_hr, how="inner")

neg_mask = merged["ret"] <= 0
pos_mask = merged["ret"] > 0

print(f"  {'hr':>4} {'ΔOI⁺':>14} {'ret%':>7} {'group':>10}")
print(f"  {'──':>4} {'─'*14} {'─'*7} {'─'*10}")
for h in sorted(merged.index):
    doi = merged.loc[h, "doi_pos"]
    ret = merged.loc[h, "ret"]
    grp = "NEG_HR(≤0)" if ret <= 0 else "POS_HR(>0)"
    print(f"  {h:>4} {doi:>14,.0f} {ret*100:>+7.3f}% {grp:>10}")

n_neg    = int(neg_mask.sum())
n_pos    = int(pos_mask.sum())
sum_neg  = float(merged.loc[neg_mask, "doi_pos"].sum())
sum_pos  = float(merged.loc[pos_mask, "doi_pos"].sum())
sum_all  = float(merged["doi_pos"].sum())

rate_neg = sum_neg / n_neg
rate_pos = sum_pos / n_pos
h2p      = rate_neg - rate_pos
h2_share = sum_neg / sum_all

print()
print(f"  ── RED hours (ret≤0):   n={n_neg}   Σ ΔOI⁺ = {sum_neg:>14,.0f}")
print(f"  ── GREEN hours (ret>0): n={n_pos}   Σ ΔOI⁺ = {sum_pos:>14,.0f}")
print(f"  ── ALL (joined):               Σ ΔOI⁺ = {sum_all:>14,.0f}")
print()
print(f"  rate_neg = {sum_neg:,.0f} / {n_neg} = {rate_neg:>14,.2f}  [USD-OI per red hour]")
print(f"  rate_pos = {sum_pos:,.0f} / {n_pos} = {rate_pos:>14,.2f}  [USD-OI per green hour]")
print()
print(f"  h2_prime = rate_neg − rate_pos")
print(f"           = {rate_neg:,.2f} − {rate_pos:,.2f}")
print(f"           = {h2p:+,.2f}  [USD-OI / hour differential]")
print()
print(f"  h2_old  (share-based) = {sum_neg:,.0f} / {sum_all:,.0f} = {h2_share:.4f}")
print(f"  MATCH h2_old={H2_OLD}: {abs(h2_share - H2_OLD) < 1e-3}  ← đây là bản cũ")
print()
print(f"  h2_prime ({h2p:+,.2f})  ≠  h2_old ({H2_OLD})  →  NORMALIZE THẬT ✓")
print(f"  h2_prime UNIT: USD-OI per hour (NOT dimensionless share)")
print(f"  h2_prime > 0 → OI grows {rate_neg/rate_pos:.2f}× faster per red hour vs green hour")
print()

# ── Call module function on raw df_o ─────────────────────────────────────────────
print("  Module call compute_h2_prime(raw_data):")
res = compute_h2_prime(SYM, df_k, df_o_raw, funding.get(SYM, 8))
print(f"    h2_prime={res['h2p']:+,.2f}   n_neg={res['n_neg']}  n_pos={res['n_pos']}")
match = abs(res["h2p"] - h2p) < 1.0
print(f"    MATCH trace: {match}  (diff={res['h2p']-h2p:.2f})")

print()
print("=" * 80)
verdict = "PASS" if (h2p != H2_OLD and abs(h2_share - H2_OLD) < 1e-3 and match) else "FAIL"
print(f"VERDICT: {verdict}")
print("  h2_share reproduces h2_old → cũ đúng trace")
print("  h2_prime ≠ h2_old → rate-normalize THẬT, không phải share đội tên")
print("DỪNG — paste kết quả.")

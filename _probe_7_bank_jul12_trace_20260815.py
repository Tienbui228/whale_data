"""
Probe [7] v2 — BANK 2026-07-12: n_neg/n_pos mâu thuẫn + cartesian forensic.
Target: xác định h2r=2.370 là số ĐÚNG hay RÁC (cartesian product từ dup hour_utc).

[1] Klines per hour: ret + phân loại
[2] OI per hour: doi_pos rows
[3] Merged DataFrame toàn bộ row (join kết quả thực tế)
[4] OI FORENSIC: mọi row sau dedup as_of_ts_ms — as_of_ts_ms raw + hour_utc floor.
    Tìm 2 row: khác as_of_ts_ms NHƯNG cùng hour_utc.
[5] KLINES FORENSIC: cùng cách — cùng hour_utc nhưng khác as_of_ts_ms?

Kết luận: h2r ĐÚNG hay RÁC.
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
print(f"[7] BANK {DT} — n_neg/n_pos + cartesian forensic")
print(SEP)

# ── Load raw ───────────────────────────────────────────────────────────────────
df_k_raw = pd.read_parquet(RAW / "klines_1h" / f"date={DT}" / "part-0.parquet")
df_k_raw = df_k_raw[df_k_raw["symbol"] == SYM].copy()

df_o_raw = pd.read_parquet(RAW / "oi_hist_1h" / f"date={DT}" / "part-0.parquet")
df_o_raw = df_o_raw[df_o_raw["symbol"] == SYM].copy()

print(f"\n  raw klines rows: {len(df_k_raw)}  |  raw OI rows: {len(df_o_raw)}")

# ── Dedup (as_of_ts_ms) ────────────────────────────────────────────────────────
df_k = df_k_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
df_k = df_k.sort_values("as_of_ts_ms").reset_index(drop=True)
df_k["hour_utc"] = (df_k["as_of_ts_ms"] // MS) % 24
df_k["ret"]      = (df_k["close"] - df_k["open"]) / df_k["open"].clip(lower=1e-12)

df_o = df_o_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
df_o = df_o.sort_values("as_of_ts_ms").reset_index(drop=True)
df_o["hour_utc"] = (df_o["as_of_ts_ms"] // MS) % 24
df_o["delta_oi"] = df_o["sum_open_interest"].diff()
df_o["doi_pos"]  = df_o["delta_oi"].clip(lower=0.0)

print(f"  after dedup(as_of_ts_ms): klines={len(df_k)}  OI={len(df_o)}")

# ── [1] Klines per hour ────────────────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[1] Klines — ret per hour + phân loại")
print(f"  {'hr':>4} {'as_of_ts_ms':>16} {'open':>10} {'close':>10} {'ret%':>8} {'group':>9}")
print(f"  {'──':>4} {'─'*16} {'─'*10} {'─'*10} {'─'*8} {'─'*9}")
for _, row in df_k.iterrows():
    h   = int(row["hour_utc"])
    ret = row["ret"]
    grp = "NEG(≤0)" if ret <= 0 else "POS(>0)"
    print(f"  {h:>4} {int(row['as_of_ts_ms']):>16} {row['open']:>10.5f} {row['close']:>10.5f}"
          f" {ret*100:>+8.3f}% {grp:>9}")
neg_k = (df_k["ret"] <= 0).sum()
pos_k = (df_k["ret"] > 0).sum()
zer_k = (df_k["ret"] == 0).sum()
print(f"\n  Klines đếm: NEG(≤0)={neg_k}  POS(>0)={pos_k}  ret==0 chính xác={zer_k}")

# ── [2] OI per hour ────────────────────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[2] OI — doi_pos per hour (sau dedup as_of_ts_ms)")
print(f"  {'hr':>4} {'as_of_ts_ms':>16} {'oi_usd':>14} {'delta_oi':>12} {'doi_pos':>12}")
print(f"  {'──':>4} {'─'*16} {'─'*14} {'─'*12} {'─'*12}")
for _, row in df_o.iterrows():
    h   = int(row["hour_utc"])
    doi = row["doi_pos"] if not pd.isna(row["doi_pos"]) else float("nan")
    d   = row["delta_oi"] if not pd.isna(row["delta_oi"]) else float("nan")
    print(f"  {h:>4} {int(row['as_of_ts_ms']):>16} {row['sum_open_interest']:>14,.0f}"
          f" {d:>12,.0f} {doi:>12,.0f}")

# ── [3] Merged DataFrame đầy đủ ───────────────────────────────────────────────
print(f"\n{'─'*80}")
print("[3] Merged DataFrame (so_hr.join(sk_hr, inner)) — toàn bộ row")

df_o_valid = df_o.dropna(subset=["delta_oi"])
sk_hr  = df_k[["hour_utc", "ret"]].set_index("hour_utc")
so_hr  = df_o_valid[["hour_utc", "doi_pos"]].set_index("hour_utc")
merged = so_hr.join(sk_hr, how="inner")

print(f"  sk_hr rows (klines): {len(sk_hr)}  |  so_hr rows (OI valid): {len(so_hr)}")
print(f"  merged rows THỰC TẾ: {len(merged)}  ← nếu > max(sk,so) → cartesian xảy ra")
print()
print(f"  {'idx(hr)':>8} {'doi_pos':>12} {'ret%':>8} {'group':>9}")
print(f"  {'─'*8} {'─'*12} {'─'*8} {'─'*9}")
for h, row in merged.iterrows():
    doi = row["doi_pos"]
    ret = row["ret"]
    grp = "NEG(≤0)" if ret <= 0 else "POS(>0)"
    print(f"  {h:>8} {doi:>12,.0f} {ret*100:>+8.3f}% {grp:>9}")

neg_mask = merged["ret"] <= 0
pos_mask = merged["ret"] > 0
n_neg    = int(neg_mask.sum())
n_pos    = int(pos_mask.sum())
print(f"\n  Merged count: n_neg={n_neg}  n_pos={n_pos}  total={n_neg+n_pos}")

# ── [4] OI FORENSIC: dup hour_utc sau dedup as_of_ts_ms ───────────────────────
print(f"\n{'─'*80}")
print("[4] OI FORENSIC — duplicate hour_utc sau dedup as_of_ts_ms?")
print(f"  (dedup chỉ đuổi trùng as_of_ts_ms — 2 ts KHÁC giờ nhưng CÙNG floor = dup hour)")
print()
print(f"  {'hr':>4} {'as_of_ts_ms_raw':>18} {'ms_trong_giờ':>14} {'note':>20}")
print(f"  {'──':>4} {'─'*18} {'─'*14} {'─'*20}")
for _, row in df_o.iterrows():
    h    = int(row["hour_utc"])
    ts   = int(row["as_of_ts_ms"])
    ms_r = ts % MS   # milliseconds within the hour
    note = "<<< KHÔNG phải đầu giờ!" if ms_r != 0 else "đầu giờ OK"
    print(f"  {h:>4} {ts:>18} {ms_r:>14} {note:>20}")

dup_oi_hours = df_o["hour_utc"].duplicated(keep=False)
n_dup = dup_oi_hours.sum()
if n_dup > 0:
    dup_hrs = sorted(df_o.loc[dup_oi_hours, "hour_utc"].unique())
    print(f"\n  *** CÓ {n_dup} row với hour_utc trùng nhau: {dup_hrs}")
    print(f"  *** CARTESIAN XÁC NHẬN → h2r=2.370 tính trên Σ nhiễm → RÁC")
    print(f"  *** FIX: dedup thêm tầng hour_utc TRƯỚC set_index (keep last = giá trị cuối giờ)")
else:
    print(f"\n  hour_utc OI: tất cả unique ({df_o['hour_utc'].nunique()} giờ) — KHÔNG cartesian từ OI")

# ── [5] KLINES FORENSIC: dup hour_utc sau dedup as_of_ts_ms ───────────────────
print(f"\n{'─'*80}")
print("[5] KLINES FORENSIC — duplicate hour_utc sau dedup as_of_ts_ms?")
print()
print(f"  {'hr':>4} {'as_of_ts_ms_raw':>18} {'ms_trong_giờ':>14} {'note':>20}")
print(f"  {'──':>4} {'─'*18} {'─'*14} {'─'*20}")
for _, row in df_k.iterrows():
    h    = int(row["hour_utc"])
    ts   = int(row["as_of_ts_ms"])
    ms_r = ts % MS
    note = "<<< KHÔNG phải đầu giờ!" if ms_r != 0 else "đầu giờ OK"
    print(f"  {h:>4} {ts:>18} {ms_r:>14} {note:>20}")

dup_k_hours = df_k["hour_utc"].duplicated(keep=False)
n_dup_k = dup_k_hours.sum()
if n_dup_k > 0:
    dup_hrs_k = sorted(df_k.loc[dup_k_hours, "hour_utc"].unique())
    print(f"\n  *** CÓ {n_dup_k} row klines dup hour_utc: {dup_hrs_k}")
    print(f"  *** join đôi cả hai phía = nhân bốn cho giờ đó")
else:
    print(f"\n  hour_utc klines: tất cả unique ({df_k['hour_utc'].nunique()} giờ) — OK")

# ── VERDICT ────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("VERDICT:")
if n_dup > 0 or n_dup_k > 0:
    print("  h2r=2.370 = SỐ RÁC — cartesian product từ dup hour_utc trong store")
    print("  FIX CẦN: dedup floor-to-hour (keep='last') TRƯỚC set_index trong compute_h2_prime()")
    print("  KHÔNG đóng — sửa loader, tính lại, commit mới.")
else:
    print("  KHÔNG cartesian — OI và klines đều unique per hour_utc")
    print("  h2r=2.370 là số ĐÚNG. Lệch n_neg/n_pos do lý do khác (xem [1][3]).")
    print("  [B]-probe 14/9 vs commit 12/11 = đếm/ret==0 nhầm — [3] là nguồn sự thật.")

sum_neg_m = float(merged.loc[neg_mask, "doi_pos"].sum())
sum_pos_m = float(merged.loc[pos_mask, "doi_pos"].sum())
if n_neg >= 5 and n_pos >= 5 and sum_neg_m > 0 and sum_pos_m > 0:
    rate_neg = sum_neg_m / n_neg
    rate_pos = sum_pos_m / n_pos
    h2r      = rate_neg / rate_pos
    h2r_log  = math.log(h2r)
    print(f"\n  FINAL (từ merged thực tế):")
    print(f"  n_neg={n_neg}  Σ_neg={sum_neg_m:,.0f}  rate_neg={rate_neg:,.2f}")
    print(f"  n_pos={n_pos}  Σ_pos={sum_pos_m:,.0f}  rate_pos={rate_pos:,.2f}")
    print(f"  h2r={h2r:.6f}  h2r_log={h2r_log:.6f}")
print(SEP)
print("DỪNG — paste [1]-[5] + VERDICT.")

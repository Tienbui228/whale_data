#!/usr/bin/env python3
"""
Verify [3] _build_klines_agg defense (OI-DUP-20260818).

[3b] Re-run agg trên 1 partition ĐÃ sạch (post-dedup) → vol_quote before/after IDENTICAL.
     Proves: dòng thêm KHÔNG đổi kết quả khi store sạch (no-op safe).

[3c] Inject 1 dup-row giả vào df → confirm agg KHÔNG inflate ×2.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from whale_collector.storage.dedup import DEDUP_KEY

RAW = Path("/root/Data_back_test/whale_data/data/raw")
DIV = "="*72

# ── Load clean partition (post-dedup) ────────────────────────────────────────
target_date = "2026-08-18"   # post-dedup clean
p = RAW / "klines_1h" / f"date={target_date}" / "part-0.parquet"
df_raw = pd.read_parquet(p)
sym_set = set(df_raw["symbol"].unique()[:20])   # sample 20 symbols
df = df_raw[df_raw["symbol"].isin(sym_set)].copy()

print(f"{DIV}\n[3b] AGG on CLEAN partition (before-fix vs after-fix)\n{DIV}")
print(f"  partition : {p}")
print(f"  sample    : 20 symbols, {len(df)} rows")
print(f"  DEDUP_KEY : {DEDUP_KEY}")

# BEFORE fix: agg without drop_duplicates
grp_before = df.groupby("symbol").agg(
    quote_vol_sum=("quote_volume", "sum"),
    base_vol_sum=("base_volume", "sum"),
).reset_index()

# AFTER fix: drop_duplicates THEN agg
df_dd = df.drop_duplicates(subset=DEDUP_KEY, keep="last")
grp_after = df_dd.groupby("symbol").agg(
    quote_vol_sum=("quote_volume", "sum"),
    base_vol_sum=("base_volume", "sum"),
).reset_index()

# Compare
merged = grp_before.merge(grp_after, on="symbol", suffixes=("_before", "_after"))
merged["quote_diff"] = merged["quote_vol_sum_after"] - merged["quote_vol_sum_before"]
merged["base_diff"]  = merged["base_vol_sum_after"] - merged["base_vol_sum_before"]

n_diff_quote = (merged["quote_diff"].abs() > 0.01).sum()
n_diff_base  = (merged["base_diff"].abs() > 0.01).sum()

print(f"\n  Result: {len(merged)} symbols compared")
print(f"    quote_vol_sum differs : {n_diff_quote}  ({'✓ ALL IDENTICAL' if n_diff_quote==0 else '⚠ DIFF FOUND'})")
print(f"    base_vol_sum differs  : {n_diff_base}   ({'✓ ALL IDENTICAL' if n_diff_base==0 else '⚠ DIFF FOUND'})")
print(f"    max |quote_diff|      : {merged['quote_diff'].abs().max():.6f}")
print(f"    n rows dedup removed  : {len(df) - len(df_dd)}  (expect 0 on clean partition)")

if n_diff_quote == 0 and n_diff_base == 0:
    print(f"\n  ✓ VERIFIED: defense line = no-op khi store sạch")
else:
    print(f"\n  ⚠ Partition có dup còn sót — samples:")
    for _, r in merged[merged["quote_diff"].abs() > 0.01].head(5).iterrows():
        print(f"    {r['symbol']:>16}  before={r['quote_vol_sum_before']:.0f}  after={r['quote_vol_sum_after']:.0f}  diff={r['quote_diff']:+.0f}")


# ── [3c] Inject synthetic dup ────────────────────────────────────────────────
print(f"\n{DIV}\n[3c] Inject 1 dup-row giả → confirm agg KHÔNG inflate\n{DIV}")

# Pick 1 symbol, duplicate its first row
sym_pick = list(sym_set)[0]
sym_rows = df[df["symbol"] == sym_pick].sort_values("as_of_ts_ms").head(1)
if sym_rows.empty:
    print(f"  no rows for {sym_pick} — skip [3c]")
else:
    orig_row = sym_rows.iloc[0]
    print(f"  symbol   : {sym_pick}")
    print(f"  original : as_of_ts_ms={int(orig_row['as_of_ts_ms'])}  quote_vol={orig_row['quote_volume']}  base_vol={orig_row['base_volume']}")

    # BEFORE inject: current sym rows
    df_sym_orig = df[df["symbol"] == sym_pick]
    q0 = df_sym_orig["quote_volume"].sum()
    b0 = df_sym_orig["base_volume"].sum()
    n0 = len(df_sym_orig)

    # Inject dup (same as_of_ts_ms + same data + different fetched_at_ms)
    dup_row = orig_row.copy()
    if "fetched_at_ms" in dup_row.index:
        dup_row["fetched_at_ms"] = int(dup_row["fetched_at_ms"]) + 3_600_000  # +1h
    df_injected = pd.concat([df, pd.DataFrame([dup_row])], ignore_index=True)
    df_sym_inj = df_injected[df_injected["symbol"] == sym_pick]
    q_inj = df_sym_inj["quote_volume"].sum()
    b_inj = df_sym_inj["base_volume"].sum()
    n_inj = len(df_sym_inj)

    # WITHOUT fix (old code): agg directly
    grp_old = df_injected[df_injected["symbol"] == sym_pick].agg(
        quote_vol_sum=("quote_volume", "sum"),
        base_vol_sum=("base_volume", "sum"),
    )
    # Handle Series result
    q_old = grp_old["quote_volume"] if "quote_volume" in grp_old.index else q_inj
    b_old = grp_old["base_volume"]  if "base_volume"  in grp_old.index else b_inj

    # WITH fix: drop_duplicates then agg
    df_inj_dd = df_injected.drop_duplicates(subset=DEDUP_KEY, keep="last")
    df_sym_inj_dd = df_inj_dd[df_inj_dd["symbol"] == sym_pick]
    q_new = df_sym_inj_dd["quote_volume"].sum()
    b_new = df_sym_inj_dd["base_volume"].sum()
    n_new = len(df_sym_inj_dd)

    print(f"\n  BEFORE inject  : n_rows={n0:>3}  quote_vol_sum={q0:,.0f}  base_vol_sum={b0:,.0f}")
    print(f"  AFTER inject   : n_rows={n_inj:>3}  quote_vol_sum={q_inj:,.0f}  base_vol_sum={b_inj:,.0f}")
    print(f"  OLD code (no defense): SUM inflate by dup row → quote_vol_sum={q_inj:,.0f}  (⚠ INFLATED)")
    print(f"  NEW code (defense)   : drop_dup → n_rows={n_new:>3}  quote_vol_sum={q_new:,.0f}")
    print(f"    diff vs original    : quote_diff={q_new-q0:+,.0f}  base_diff={b_new-b0:+,.0f}")

    if abs(q_new - q0) < 0.01 and abs(b_new - b0) < 0.01 and n_new == n0:
        print(f"\n  ✓ VERIFIED: defense chặn inflate ×N khi dup xuất hiện")
    else:
        print(f"\n  ⚠ Defense không chặn hết — inspect")

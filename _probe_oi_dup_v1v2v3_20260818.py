#!/usr/bin/env python3
"""
Verify V1-V3 for OI-dup fix. READ-ONLY, không sửa/commit.

V1(c) DATA: 1 bar bị ghi 2× — in đầy đủ 2 dòng, so as_of_ts_ms vs fetched_at_ms.
V2       : columns + dtype schema per metric (oi/taker/klines). Xác nhận key hiện diện.
V3       : grep net_k3/net_oi/oi_delta downstream; trace path read_pit vs raw.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import pandas as pd

RAW = Path("/root/Data_back_test/whale_data/data/raw")
DIV = "=" * 72

# ─── V1(c) — DATA CONFIRM as_of_ts_ms is BAR-TIME ───────────────────────────
print(f"{DIV}\n[V1c] DATA — read raw parquet oi_hist_1h, 1 symbol có dup\n{DIV}")

# Pick BANKUSDT 2026-08-12 (confirmed dup in earlier forensic — max=3, dup-ratio 2.00)
target_date = "2026-08-12"
target_sym  = "BANKUSDT"
p = RAW / "oi_hist_1h" / f"date={target_date}" / "part-0.parquet"
df = pd.read_parquet(p)
sym_df = df[df["symbol"] == target_sym].sort_values(["as_of_ts_ms", "fetched_at_ms"])
print(f"  file    : {p}")
print(f"  columns : {list(sym_df.columns)}")
print(f"  n rows  : {len(sym_df)} (raw, no dedup)")

# Find a dup: same as_of_ts_ms → 2+ rows
counts = sym_df.groupby("as_of_ts_ms").size()
dup_ts = counts[counts >= 2].index[:3].tolist()
if not dup_ts:
    print("  NO DUP found in this partition — try another")
else:
    print(f"  dup as_of_ts_ms found: {len(counts[counts>=2])} bar-times ≥2 copies")
    print(f"  sample first 3 dup timestamps: {dup_ts}")

    for t in dup_ts[:1]:  # inspect first
        rows = sym_df[sym_df["as_of_ts_ms"] == t]
        print(f"\n  ── inspect as_of_ts_ms={t} ({pd.to_datetime(t, unit='ms', utc=True)}) — n_copies={len(rows)} ──")
        for i, (_, r) in enumerate(rows.iterrows()):
            print(f"    copy #{i+1}:")
            for c in sym_df.columns:
                v = r[c]
                if c in ("as_of_ts_ms", "fetched_at_ms"):
                    dt = pd.to_datetime(int(v), unit='ms', utc=True)
                    print(f"      {c:>26} = {int(v):>15}  ({dt})")
                else:
                    print(f"      {c:>26} = {v}")

        # Same-value comparison across copies
        print(f"\n    ANALYSIS:")
        for c in sym_df.columns:
            vals = rows[c].tolist()
            all_same = all(str(v) == str(vals[0]) for v in vals)
            print(f"      {c:>26} : {'SAME' if all_same else 'DIFF'} {vals}")

# ─── V2 — Columns schema per metric ─────────────────────────────────────────
print(f"\n{DIV}\n[V2] Schema check: oi_hist_1h · taker_ratio_1h · klines_1h\n{DIV}")

for metric in ("oi_hist_1h", "taker_ratio_1h", "klines_1h"):
    metric_dir = RAW / metric
    p_files = sorted(metric_dir.glob("date=*/part-0.parquet"))
    if not p_files:
        print(f"\n  [{metric}] NO partitions")
        continue
    sample = p_files[-1]  # latest partition
    d = pd.read_parquet(sample)
    print(f"\n  ── {metric}  (sample: {sample.parent.name})")
    print(f"    n rows            : {len(d):,}")
    print(f"    columns + dtypes  :")
    for c in d.columns:
        print(f"      {c:>28} : {d[c].dtype}")
    has_key = ("symbol" in d.columns) and ("as_of_ts_ms" in d.columns)
    print(f"    ['symbol','as_of_ts_ms'] present? {has_key}")

# ─── V3 — net_k3 downstream path ────────────────────────────────────────────
print(f"\n{DIV}\n[V3] net_k3 downstream path — read_pit vs raw?\n{DIV}")
print("  (grep + code trace ở section riêng ngoài probe này — file _probe_dayk3_20260815.py)")

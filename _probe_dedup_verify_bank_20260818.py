#!/usr/bin/env python3
"""Verify BANKUSDT partition 2026-08-18 sau collect_hourly manual — không dup?"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import pandas as pd

RAW = Path("/root/Data_back_test/whale_data/data/raw")
DIV = "="*72

for metric in ("oi_hist_1h", "taker_ratio_1h", "klines_1h"):
    p = RAW / metric / "date=2026-08-18" / "part-0.parquet"
    if not p.exists():
        print(f"[{metric}] partition missing"); continue
    df = pd.read_parquet(p)
    sym = df[df["symbol"] == "BANKUSDT"]
    counts = sym.groupby(["symbol", "as_of_ts_ms"]).size()
    max_n = int(counts.max()) if len(counts) else 0
    n_dup = int((counts > 1).sum())
    print(f"\n{DIV}\n[{metric}] BANKUSDT 2026-08-18\n{DIV}")
    print(f"  n rows                  : {len(sym)}")
    print(f"  unique (symbol,ts) pairs: {len(counts)}")
    print(f"  n_dup pairs (>1 copy)   : {n_dup}")
    print(f"  max_copies              : {max_n}")
    if max_n > 1:
        dup_ts = counts[counts>1].index[:3]
        print(f"  ⚠ DUP FOUND — sample: {list(dup_ts)}")
    else:
        print(f"  ✓ CLEAN — writer dedup-on-write hoạt động đúng")

    # Show last 3 bars fetched_at_ms range
    if "fetched_at_ms" in sym.columns and len(sym):
        s = sym.sort_values("as_of_ts_ms").tail(3)
        print(f"\n  Last 3 bars (as_of_ts_ms → fetched_at_ms):")
        for _, r in s.iterrows():
            ts = pd.to_datetime(int(r["as_of_ts_ms"]), unit='ms', utc=True)
            ft = pd.to_datetime(int(r["fetched_at_ms"]), unit='ms', utc=True)
            print(f"    bar={ts}  fetch={ft}")

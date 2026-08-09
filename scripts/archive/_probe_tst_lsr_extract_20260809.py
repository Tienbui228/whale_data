"""Pull TST LSR/OI data from VPS parquet stores, output merge-ready CSV."""
import pandas as pd
from pathlib import Path
import math
import csv
import sys

BASE = Path("data/raw")
SYM = "TSTUSDT"
OUT = Path("scratch/tst_lsr_backfill_20260809.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

def read_metric_for_sym(metric, sym):
    """Read all date-partitioned parquet for one symbol, return sorted DataFrame."""
    files = sorted((BASE / metric).glob("date=*/part-0.parquet"))
    rows = []
    for f in files:
        date_str = f.parent.name.replace("date=", "")
        try:
            df = pd.read_parquet(f)
            if "symbol" not in df.columns:
                continue
            sub = df[df["symbol"] == sym].copy()
            if len(sub) == 0:
                continue
            # Take last row if multiple (dedup by keeping latest as_of_ts_ms)
            if "as_of_ts_ms" in sub.columns:
                sub = sub.sort_values("as_of_ts_ms").iloc[[-1]]
            sub["_date"] = date_str
            rows.append(sub)
        except Exception as e:
            print(f"  WARN {metric}/{date_str}: {e}", file=sys.stderr)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows).drop_duplicates(subset=["_date"]).set_index("_date").sort_index()

print("Reading OI data...")
oi = read_metric_for_sym("oi_hist_1d", SYM)
print(f"  oi_hist_1d: {len(oi)} dates, cols={list(oi.columns)[:5]}")

print("Reading top_pos data...")
top_pos = read_metric_for_sym("top_pos_1d", SYM)
print(f"  top_pos_1d: {len(top_pos)} dates, cols={list(top_pos.columns)[:5]}")

print("Reading top_acct data...")
top_acct = read_metric_for_sym("top_acct_1d", SYM)
print(f"  top_acct_1d: {len(top_acct)} dates, cols={list(top_acct.columns)[:5]}")

print("Reading retail_global data...")
retail = read_metric_for_sym("retail_global_1d", SYM)
print(f"  retail_global_1d: {len(retail)} dates, cols={list(retail.columns)[:5]}")

print("Reading taker_ratio data...")
taker = read_metric_for_sym("taker_ratio_1d", SYM)
print(f"  taker_ratio_1d: {len(taker)} dates, cols={list(taker.columns)[:5]}")

# Build merge table
# pos_r = top_pos "long_short_ratio" or similar, acc_r = top_acct same
# gLSR = retail "longShortRatio" or similar, taker_lsr = taker buy_sell_ratio
print()
print("top_pos cols:", list(top_pos.columns) if len(top_pos) else "EMPTY")
print("top_acct cols:", list(top_acct.columns) if len(top_acct) else "EMPTY")
print("retail cols:", list(retail.columns) if len(retail) else "EMPTY")
print("taker cols:", list(taker.columns) if len(taker) else "EMPTY")
print("oi cols:", list(oi.columns) if len(oi) else "EMPTY")

# Sample row from each
for name, df in [("top_pos", top_pos), ("top_acct", top_acct), ("retail", retail), ("taker", taker)]:
    if len(df):
        print(f"\n{name} sample:", df.iloc[0].to_dict())

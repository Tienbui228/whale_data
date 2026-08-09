"""R2: Verify TST backfill — count per metric, first/last date for TSTUSDT."""
import pandas as pd
from pathlib import Path

BASE = Path("data/raw")
METRICS = ["oi_hist_1d", "top_pos_1d", "top_acct_1d", "retail_global_1d", "taker_ratio_1d"]
SYM = "TSTUSDT"

print(f"R2 TST backfill verify — {SYM}")
print("=" * 60)

for metric in METRICS:
    metric_dir = BASE / metric
    files = sorted(metric_dir.glob("date=*/part-0.parquet"))
    rows_sym = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            if "symbol" in df.columns:
                sub = df[df["symbol"] == SYM]
            else:
                sub = df[df.index == SYM] if df.index.name == "symbol" else pd.DataFrame()
            if len(sub) > 0:
                date_str = f.parent.name.replace("date=", "")
                rows_sym.append((date_str, len(sub)))
        except Exception as e:
            print(f"  ERROR {f}: {e}")
    if rows_sym:
        rows_sym.sort()
        first_d, last_d = rows_sym[0][0], rows_sym[-1][0]
        total = sum(r[1] for r in rows_sym)
        print(f"  {metric}: {len(rows_sym)} dates, {total} rows, first={first_d}, last={last_d}")
    else:
        print(f"  {metric}: 0 rows found for {SYM}")

print()
print("Sample oi_hist_1d earliest rows:")
oi_files = sorted((BASE / "oi_hist_1d").glob("date=*/part-0.parquet"))
for f in oi_files[:5]:
    try:
        df = pd.read_parquet(f)
        if "symbol" in df.columns:
            sub = df[df["symbol"] == SYM]
            if len(sub) > 0:
                print(f"  {f.parent.name}: {sub[['sumOpenInterest','sumOpenInterestValue']].to_string(index=False)}")
    except Exception as e:
        print(f"  {f}: {e}")

"""Build TST LSR merge CSV from VPS parquet stores. Output to scratch/."""
import pandas as pd
from pathlib import Path
import sys, math

BASE = Path("data/raw")
SYM = "TSTUSDT"
OUT = Path("scratch/tst_lsr_backfill_20260809.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

def read_metric(metric, sym, val_col, alias):
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
            if "as_of_ts_ms" in sub.columns:
                sub = sub.sort_values("as_of_ts_ms").iloc[[-1]]
            rows.append({"date": date_str, alias: sub.iloc[0][val_col]})
        except Exception as e:
            print(f"  WARN {metric}/{date_str}: {e}", file=sys.stderr)
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()

pos_df = read_metric("top_pos_1d", SYM, "long_short_ratio", "pos_r")
acc_df = read_metric("top_acct_1d", SYM, "long_short_ratio", "acc_r")
gls_df = read_metric("retail_global_1d", SYM, "long_short_ratio", "gLSR")
tkr_df = read_metric("taker_ratio_1d", SYM, "buy_sell_ratio", "taker_lsr")
oi_df = read_metric("oi_hist_1d", SYM, "sum_open_interest_value", "oi_usd_store")

merged = pos_df.join(acc_df, how="outer").join(gls_df, how="outer").join(tkr_df, how="outer").join(oi_df, how="outer")
merged = merged.sort_index().reset_index().rename(columns={"index": "date"})

# Derived cols
merged["div_raw"] = merged.apply(
    lambda r: round(r["pos_r"] / r["acc_r"], 4) if pd.notna(r["pos_r"]) and pd.notna(r["acc_r"]) and r["acc_r"] > 0 else None,
    axis=1)

# div_avg3: rolling 3-day mean of pos_r/acc_r series
dates_sorted = merged.sort_values("date")
div_raw_series = dates_sorted["div_raw"].values
div_avg3 = []
for i in range(len(div_raw_series)):
    window = [v for v in div_raw_series[max(0, i-2):i+1] if v is not None and not (isinstance(v, float) and math.isnan(v))]
    div_avg3.append(round(sum(window)/len(window), 4) if window else None)
dates_sorted = dates_sorted.copy()
dates_sorted["div_avg3"] = div_avg3
merged = dates_sorted

merged.to_csv(OUT, index=False)
print(f"Written: {OUT} ({len(merged)} rows)")
print(merged[["date","pos_r","acc_r","gLSR","taker_lsr","div_raw","oi_usd_store"]].to_string(index=False))

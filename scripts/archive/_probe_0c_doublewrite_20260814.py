"""
PHASE 0c: Điều tra 48 vs 24 rows/ngày trong store 1h.
Token: BANKUSDT (48), AKEUSDT (24). Metric: taker_ratio_1h. Ngày: 2026-06-30.
Run trên VPS: python3 _probe_0c_doublewrite_20260814.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"

METRIC = "taker_ratio_1h"
DATE   = "2026-06-30"

def load_day(sym: str) -> pd.DataFrame:
    pq = RAW / METRIC / f"date={DATE}" / "part-0.parquet"
    df = pd.read_parquet(pq)
    return df[df["symbol"] == sym].copy()

def analyze(sym: str):
    df = load_day(sym)
    print(f"\n{'='*70}")
    print(f"TOKEN: {sym}  metric={METRIC}  date={DATE}  rows={len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Detect timestamp column
    ts_col = None
    for c in ["as_of_ts_ms", "timestamp", "open_time", "ts", "time", "closeTime", "openTime"]:
        if c in df.columns:
            ts_col = c
            break
    if ts_col is None:
        print("NO TIMESTAMP COLUMN FOUND — aborting")
        return

    df = df.sort_values(ts_col).reset_index(drop=True)

    # Print all rows: timestamp as UTC + raw value
    val_cols = [c for c in df.columns if c not in ["symbol", ts_col, "date"]]
    print(f"{'row':>4}  {'ts_raw':>15}  {'UTC hour':>12}  " + "  ".join(f"{c:>10}" for c in val_cols[:3]))
    print("-" * 80)
    for i, row in df.iterrows():
        ts_raw = row[ts_col]
        try:
            ts_ms = int(ts_raw)
            dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            utc_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            utc_str = str(ts_raw)[:16]
            ts_ms = -1
        vals = "  ".join(f"{row[c]:>10.4f}" if isinstance(row[c], float) else f"{str(row[c]):>10}" for c in val_cols[:3])
        print(f"{i:>4}  {ts_ms:>15}  {utc_str:>12}  {vals}")

    # Duplicate analysis
    print()
    ts_ms_series = df[ts_col].astype(int)
    hours_floored = (ts_ms_series // 3_600_000) * 3_600_000  # floor to hour
    distinct_ts   = df[ts_col].nunique()
    distinct_hours = hours_floored.nunique()
    exact_dups    = len(df) - distinct_ts
    hour_dups     = len(df) - distinct_hours

    print(f"DISTINCT exact timestamps : {distinct_ts}")
    print(f"DISTINCT hours (floored)  : {distinct_hours}")
    print(f"Exact duplicates          : {exact_dups}")
    print(f"Hour-level dups           : {hour_dups}")

    if exact_dups > 0:
        dup_ts = df[df[ts_col].duplicated(keep=False)][ts_col].unique()[:5]
        print(f"Sample dup timestamps     : {list(dup_ts)}")

    if hour_dups > 0:
        hour_counts = df.groupby(hours_floored).size()
        over2 = hour_counts[hour_counts > 1]
        print(f"Hours with >1 row (first 5):")
        for ts_h, cnt in over2.head(5).items():
            dt_h = datetime.fromtimestamp(ts_h / 1000, tz=timezone.utc)
            print(f"  {dt_h.strftime('%H:00 UTC')} → {cnt} rows")

    return distinct_hours

print("\n" + "="*70)
print("PHASE 0c — Double-write investigation")
print("="*70)

results = {}
for sym in ["BANKUSDT", "AKEUSDT"]:
    dh = analyze(sym)
    if dh is not None:
        results[sym] = dh

# Also quick distinct-hour count for TUT and CYS on same date
print(f"\n{'='*70}")
print(f"DISTINCT HOURS SUMMARY — {METRIC} {DATE}")
print("-"*40)
for sym in ["BANKUSDT", "TUTUSDT", "CYSUSDT", "AKEUSDT"]:
    try:
        df = load_day(sym)
        ts_col = next((c for c in ["as_of_ts_ms","timestamp","open_time","ts","time"] if c in df.columns), None)
        if ts_col:
            ts_ms = df[ts_col].astype(int)
            distinct_h = (ts_ms // 3_600_000).nunique()
            print(f"  {sym:>12}  total_rows={len(df):>3}  distinct_hours={distinct_h:>2}")
        else:
            print(f"  {sym:>12}  NO TS COL")
    except Exception as e:
        print(f"  {sym:>12}  ERROR: {e}")

print("\nDONE")

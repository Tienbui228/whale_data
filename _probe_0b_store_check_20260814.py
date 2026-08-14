"""
PHASE 0b [2]: Kiểm store 1h cho 4 positive case gate §H5:
BANK 06-29→07-14 · TUT 06-26→07-12 · AKE (trước 07-08) · CYS

Output: ngày đầu/cuối có data + gaps + count rows/ngày mẫu
Run trên VPS: python3 _probe_0b_store_check_20260814.py
"""
import sys
from pathlib import Path
import pandas as pd

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"

TARGETS = {
    "BANKUSDT": ("2026-06-29", "2026-07-14"),
    "TUTUSDT":  ("2026-06-26", "2026-07-12"),
    "AKEUSDT":  ("2026-06-01", "2026-07-08"),  # "trước 07-08"
    "CYSUSDT":  ("2026-06-01", "2026-08-14"),  # full window
}

METRICS = ["oi_hist_1h", "top_pos_1h", "top_acct_1h", "taker_ratio_1h"]

def check_metric(metric: str, sym: str, window_start: str, window_end: str):
    mdir = RAW / metric
    if not mdir.exists():
        print(f"  {metric}: DIR NOT FOUND")
        return

    # All available date dirs
    all_dates = sorted(d.name.replace("date=", "") for d in mdir.iterdir() if d.name.startswith("date="))
    if not all_dates:
        print(f"  {metric}: EMPTY STORE")
        return

    # Check which dates have this symbol
    sym_dates = []
    for dt in all_dates:
        pq = mdir / f"date={dt}" / "part-0.parquet"
        if not pq.exists():
            continue
        try:
            df = pd.read_parquet(pq, columns=["symbol"])
            if sym in df["symbol"].values:
                sym_dates.append(dt)
        except Exception as e:
            pass

    if not sym_dates:
        print(f"  {metric}: {sym} NOT IN ANY DATE")
        return

    # Coverage
    first = sym_dates[0]
    last  = sym_dates[-1]

    # Gaps
    from datetime import date, timedelta
    start_dt = date.fromisoformat(first)
    end_dt   = date.fromisoformat(last)
    expected = [(start_dt + timedelta(days=i)).isoformat()
                for i in range((end_dt - start_dt).days + 1)]
    gaps = [d for d in expected if d not in sym_dates]

    # Row counts for sample days in window
    sample_days = [d for d in sym_dates if window_start <= d <= window_end][:3]
    samples = {}
    for sd in sample_days:
        pq = mdir / f"date={sd}" / "part-0.parquet"
        try:
            df = pd.read_parquet(pq)
            rows = len(df[df["symbol"] == sym])
            samples[sd] = rows
        except:
            samples[sd] = "ERR"

    win_dates = [d for d in sym_dates if window_start <= d <= window_end]

    print(f"  {metric}:")
    print(f"    store:  {first} → {last}  ({len(sym_dates)} days)")
    print(f"    window {window_start}→{window_end}: {len(win_dates)} days")
    print(f"    gaps:   {gaps[:10] if gaps else 'NONE'}" + (" ..." if len(gaps) > 10 else ""))
    print(f"    sample rows/day: {samples}")

print("=" * 80)
for sym, (ws, we) in TARGETS.items():
    print(f"\n{'─'*60}")
    print(f"TOKEN: {sym}  (window {ws} → {we})")
    for metric in METRICS:
        check_metric(metric, sym, ws, we)

print("\n" + "=" * 80)
print("DONE")

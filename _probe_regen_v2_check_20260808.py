#!/usr/bin/env python3
"""Quick check: which 6 symbols still have funding_n=NaN in regen v2."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parent
FW137_DIR = REPO / "scratch" / "fw137_test"
jul_csv = FW137_DIR / "freshwatch_daily_2026-07.csv"

df = pd.read_csv(jul_csv)
rows = df[df["date"].isin(["2026-07-24", "2026-07-25", "2026-07-26"])]
missing_fn = rows[rows["funding_n"].isna() | (rows["funding_n"] == 0)]
print(f"Rows with funding_n null/zero in 24-26/07: {len(missing_fn)}")
print(missing_fn[["date", "symbol", "funding_n", "oi_usd", "lsr_global_r"]].to_string())

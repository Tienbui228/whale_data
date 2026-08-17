"""Check existing GUA/APR scratch CSVs to find last date and what needs fetching."""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
DATE_TARGET = "20260817"

for sym in ["gua", "apr"]:
    print(f"\n{'='*50}")
    print(f"{sym.upper()} scratch CSVs:")
    for tag in ["20260810", "20260811", "20260812", "20260813", "20260815", "20260817"]:
        for suffix in ["perp", "funding", "oi_hist", "lsr_raw"]:
            p = SCRATCH / f"{sym}_{suffix}_{tag}.csv"
            if p.exists():
                rows = list(csv.DictReader(open(p, encoding="utf-8")))
                last = rows[-1].get("date", rows[-1].get(list(rows[-1].keys())[0], "?")) if rows else "EMPTY"
                print(f"  {p.name}: {len(rows)} rows, last={last}")

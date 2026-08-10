"""Check BANANAS31 alpha klines coverage inside date-partitioned parquet store.

data-source: data/raw/spot_klines_1d (local + VPS)
machine: local
date-range: all available → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"

print("=== BANANAS31 alpha klines — parquet store check ===\n")

try:
    import pandas as pd
    import pyarrow.parquet as pq

    # Read all parquet files, check for BANANAS31 or BANANAS31USDT
    date_dirs = sorted(STORE.glob("date=*/"))
    print(f"Date dirs: {len(date_dirs)} | {date_dirs[0].name if date_dirs else '?'} → {date_dirs[-1].name if date_dirs else '?'}")

    # Sample first file to see schema
    first_pq = list(date_dirs[0].glob("*.parquet"))[0] if date_dirs else None
    if first_pq:
        schema = pq.read_schema(first_pq)
        print(f"Schema cols: {schema.names}")

    # Scan all parquets for BANANAS31
    found_dates = []
    found_rows_total = 0
    sym_col = None

    for d in date_dirs:
        pq_files = list(d.glob("*.parquet"))
        if not pq_files:
            continue
        try:
            df = pd.read_parquet(pq_files[0])
            # Determine symbol column
            if sym_col is None:
                candidates = [c for c in df.columns if "sym" in c.lower() or "token" in c.lower()]
                sym_col = candidates[0] if candidates else None

            if sym_col:
                mask = df[sym_col].str.contains("BANANAS31", na=False)
            else:
                # Try to find by any string column
                str_cols = df.select_dtypes(include="object").columns
                mask = pd.Series([False] * len(df), index=df.index)
                for sc in str_cols:
                    mask = mask | df[sc].str.contains("BANANAS31", na=False)

            sub = df[mask]
            if not sub.empty:
                found_dates.append(d.name.replace("date=", ""))
                found_rows_total += len(sub)
        except Exception as e:
            pass  # skip unreadable

    if found_dates:
        found_dates.sort()
        print(f"\nBANANAS31 found in {len(found_dates)} dates: {found_dates[0]} → {found_dates[-1]}")
        print(f"Total rows: {found_rows_total}")
        # Check gaps
        from datetime import datetime, timedelta
        gaps = []
        cur = datetime.strptime(found_dates[0], "%Y-%m-%d")
        for d in found_dates[1:]:
            nxt = datetime.strptime(d, "%Y-%m-%d")
            if (nxt - cur).days > 1:
                gaps.append((cur.strftime("%Y-%m-%d"), d))
            cur = nxt
        if gaps:
            print(f"Gaps: {gaps}")
        else:
            print("Gaps: NONE ✓")
    else:
        print("\nBANANAS31 NOT FOUND in any parquet file")
        # Show what symbols ARE in the parquet
        if date_dirs:
            df_sample = pd.read_parquet(list(date_dirs[-1].glob("*.parquet"))[0])
            print(f"Sample file ({date_dirs[-1].name}) symbols: {df_sample[sym_col].unique()[:10] if sym_col else df_sample.head(2)}")

except ImportError as e:
    print(f"pandas/pyarrow not available: {e}")
    print("Manual check via VPS SSH:")
    # Check on VPS
    r = subprocess.run(
        ["ssh", "root@5.223.67.21",
         "python3 -c \""
         "import pandas as pd; "
         "from pathlib import Path; "
         "store=Path('/root/Data_back_test/whale_data/data/raw/spot_klines_1d'); "
         "dates=sorted(store.glob('date=*/')); "
         "found=[]; "
         "[found.append(d.name) or None for d in dates for f in d.glob('*.parquet') "
         "for df in [pd.read_parquet(f)] "
         "if any('BANANAS31' in str(v) for col in df.select_dtypes('object').columns for v in df[col])]; "
         "print(f'Found in {len(found)} dates'); "
         "print(found[:5] if found else 'NONE')\""],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
    )
    print(r.stdout or r.stderr)
except Exception as e:
    print(f"Error: {e}")

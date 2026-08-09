"""Check FF klines coverage in spot_klines_1d store and identify the '74 days treo' gap."""
import pandas as pd
from pathlib import Path
import openpyxl

BASE = Path("data/raw/spot_klines_1d")
SYM = "FF"

# Check local spot_klines store
files = sorted(BASE.glob("date=*/part-0.parquet"))
ff_dates = []
for f in files:
    df = pd.read_parquet(f)
    if "symbol" in df.columns:
        sub = df[df["symbol"] == SYM]
        if len(sub):
            ff_dates.append(f.parent.name.replace("date=", ""))

print(f"FF in spot_klines_1d: {len(ff_dates)} dates")
if ff_dates:
    print(f"  First: {ff_dates[0]}, Last: {ff_dates[-1]}")
    for d in ff_dates:
        print(f"  {d}")
else:
    print("  No data")

print()

# Check CASE_FF.xlsx DAILY sheet
ff_xlsx = Path("docs/case_files/CASE_FF.xlsx")
if ff_xlsx.exists():
    wb = openpyxl.load_workbook(ff_xlsx, read_only=True)
    print("CASE_FF sheets:", wb.sheetnames)
    if "DAILY" in wb.sheetnames:
        ws = wb["DAILY"]
        rows = list(ws.iter_rows(values_only=True))
        print(f"DAILY rows: {len(rows)}")
        print(f"Header row 2: {rows[1][:10] if len(rows)>1 else 'N/A'}")
        data_rows = [r for r in rows[2:] if r[0]]
        print(f"Data rows: {len(data_rows)}")
        if data_rows:
            print(f"Date range: {data_rows[0][0]} to {data_rows[-1][0]}")
            # Check alpha vol column (col34 if same structure)
            print("Last 5 rows (first 12 cols):")
            for r in data_rows[-5:]:
                print(f"  {r[:12]}")
    wb.close()

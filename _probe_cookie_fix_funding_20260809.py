"""Fix: regenerate cookie_funding CSV as raw records (fundingRate column)"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"

fund_json = SCRATCH / f"cookie_funding_{DATE_TAG}.json"
fund_raw_csv = SCRATCH / f"cookie_funding_{DATE_TAG}.csv"

data = json.loads(fund_json.read_text(encoding="utf-8"))
print(f"Raw records: {len(data)}")
print(f"Sample keys: {list(data[0].keys())}")

# Overwrite CSV with raw records preserving fundingRate column
with open(fund_raw_csv, "w", newline="", encoding="utf-8") as f:
    # Preserve all original fields
    fieldnames = list(data[0].keys())
    if "date" not in fieldnames:
        # Add date column derived from fundingTime
        fieldnames = ["date"] + fieldnames
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in data:
        ts = int(r.get("fundingTime", 0))
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        row = dict(r)
        row["date"] = dt
        w.writerow(row)

print(f"Written raw CSV: {fund_raw_csv.name} ({fund_raw_csv.stat().st_size:,} bytes)")
print("Done")

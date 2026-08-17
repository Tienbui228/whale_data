"""Merge old ain_funding_20260813.csv + new ain_funding_20260817.csv → complete history."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import csv

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

old_path = SCRATCH / "ain_funding_20260813.csv"
new_path = SCRATCH / "ain_funding_20260817.csv"
out_path = SCRATCH / "ain_funding_20260817.csv"  # overwrite new with merged

rows = {}

for p in [old_path, new_path]:
    if not p.exists():
        print(f"MISSING: {p.name}")
        continue
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row.get("time_ms") or row.get("fundingTime", "")
            if key:
                rows[key] = row

merged = sorted(rows.values(), key=lambda r: int(r.get("time_ms") or r.get("fundingTime", 0)))
print(f"Old: {old_path.name if old_path.exists() else 'MISSING'}")
print(f"New: {new_path.name}")
print(f"Merged total: {len(merged)} entries")
if merged:
    print(f"Range: {merged[0].get('date','')} → {merged[-1].get('date','')}")

fieldnames = ["date","time_ms","fundingRate"]
with open(out_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in merged:
        # normalise key names
        out_r = {
            "date":        r.get("date", ""),
            "time_ms":     r.get("time_ms") or r.get("fundingTime", ""),
            "fundingRate": r.get("fundingRate", ""),
        }
        w.writerow(out_r)

print(f"Written: {out_path.name}")

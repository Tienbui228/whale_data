"""Append Aug13-17 funding entries to ain_funding_20260817.csv."""
import sys, io, json, csv, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

def fetch_json(url, params=None):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def to_ms(d_str):
    return int(datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

def ms_to_date(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# Read existing merged CSV
fund_path = SCRATCH / "ain_funding_20260817.csv"
existing = {}
with open(fund_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        existing[row["time_ms"]] = row

print(f"Existing entries: {len(existing)}, last date: {max(r['date'] for r in existing.values())}")

# Fetch Aug13-17 specifically
start = to_ms("2026-08-13")
end   = to_ms("2026-08-17") + 86400000
data  = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": "AINUSDT", "startTime": start, "endTime": end, "limit": 200})

added = 0
for item in data:
    ts    = int(item.get("fundingTime", 0))
    d_str = ms_to_date(ts)
    key   = str(ts)
    if key not in existing:
        existing[key] = {"date": d_str, "time_ms": key, "fundingRate": item.get("fundingRate","")}
        added += 1

print(f"New entries added: {added}")
print(f"Total after merge: {len(existing)}")

merged = sorted(existing.values(), key=lambda r: int(r["time_ms"]))
if merged:
    print(f"Range: {merged[0]['date']} → {merged[-1]['date']}")

with open(fund_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","time_ms","fundingRate"])
    w.writeheader()
    for r in merged:
        w.writerow({"date": r["date"], "time_ms": r["time_ms"], "fundingRate": r["fundingRate"]})

print(f"Written: {fund_path.name} ({len(merged)} entries)")

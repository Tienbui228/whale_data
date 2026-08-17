"""Check what fapi returns for AIN funding Aug13-17."""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import datetime, timezone

def fetch_json(url, params=None):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def to_ms(d_str):
    return int(datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

def ms_to_dt(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# Fetch last 50 funding entries
data = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                  {"symbol": "AINUSDT", "limit": 50})
if isinstance(data, list):
    print(f"Total returned: {len(data)}")
    print("Last 20 entries:")
    for item in data[-20:]:
        ts = int(item.get("fundingTime", 0))
        print(f"  {ms_to_dt(ts)}  rate={item.get('fundingRate','')}")
else:
    print(f"Error: {data}")

# Fetch specifically Aug13-17
print("\nFetch with startTime=Aug13:")
start = to_ms("2026-08-13")
end   = to_ms("2026-08-17") + 86400000
data2 = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": "AINUSDT", "startTime": start, "endTime": end, "limit": 200})
if isinstance(data2, list):
    print(f"Aug13-17 entries: {len(data2)}")
    for item in data2:
        ts = int(item.get("fundingTime", 0))
        print(f"  {ms_to_dt(ts)}  rate={item.get('fundingRate','')}")
else:
    print(f"Error: {data2}")

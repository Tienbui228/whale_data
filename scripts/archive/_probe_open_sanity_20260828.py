#!/usr/bin/env python3
"""[R3 SANITY OPEN 07-27 close D0..D+5 raw fapi k[4] fresh]

Operator relay (2) 28/08 cho parenthetical "OPEN không có trong census 63".
Verify: OPEN 07-27 CÓ trong census 63 (grep confirmed 3 OPEN rows: 07-16, 07-17, 07-27).
Vậy paste OPEN 07-27 close D0..D+5.
"""
from __future__ import annotations
import sys, io, json, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FAPI = "https://fapi.binance.com/fapi/v1/klines"
sym = "OPENUSDT"
d0 = "2026-07-27"
d0_dt = datetime.strptime(d0, "%Y-%m-%d")
start_ms = int(d0_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
end_dt = d0_dt + timedelta(days=6)
end_ms = int(end_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

url = FAPI + "?" + urllib.parse.urlencode({
    "symbol": sym, "interval": "1d", "startTime": start_ms, "endTime": end_ms, "limit": 10
})
print(f"[fapi] {url}\n")
with urllib.request.urlopen(url, timeout=15) as r:
    data = json.loads(r.read().decode("utf-8"))

print(f"[SANITY OPEN 07-27 close D0..D+5 raw fapi k[4] fresh]")
if not data:
    print("  N/A-NO-KLINES")
else:
    for k in data[:6]:
        dt = datetime.fromtimestamp(k[0]/1000, tz=timezone.utc).date()
        close = float(k[4])
        days_since = (dt - d0_dt.date()).days
        print(f"  {dt.strftime('%Y-%m-%d')} (D+{days_since}) : close={close:.8g}")

"""B1 probe: fetch AGT raw 4-endpoint LSR + OI data, identify pos_r/acc_r mapping,
confirm bar 1h cuối D-2 (2026-08-10 00:00 UTC boundary) tồn tại.
data-source: Binance /futures/data endpoints (public)
machine: local
date-range: 2026-08-12 (fetch now = intraday)
code-commit: see git log
DỪNG sau khi paste RAW — chờ operator duyệt trước B2.
"""
import sys, io, json, requests
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYM = "AGTUSDT"

# D-2 = 2026-08-10
# D-2 00:00 UTC in ms
D2_start_ms = int(datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
D2_end_ms   = int(datetime(2026, 8, 10, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)

BASE = "https://fapi.binance.com"

ENDPOINTS = {
    "topLongShortPositionRatio": f"{BASE}/futures/data/topLongShortPositionRatio",
    "topLongShortAccountRatio":  f"{BASE}/futures/data/topLongShortAccountRatio",
    "globalLongShortAccountRatio": f"{BASE}/futures/data/globalLongShortAccountRatio",
    "openInterestHist":          f"{BASE}/futures/data/openInterestHist",
}

def fetch_lsr(url, sym, period="1h", limit=5):
    r = requests.get(url, params={"symbol": sym, "period": period, "limit": limit}, timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_oi_hist(sym, period="1h", limit=5):
    r = requests.get(ENDPOINTS["openInterestHist"],
                     params={"symbol": sym, "period": period, "limit": limit, "contractType": "PERPETUAL"},
                     timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_oi_now(sym):
    r = requests.get(f"{BASE}/fapi/v1/openInterest", params={"symbol": sym}, timeout=15)
    r.raise_for_status()
    return r.json()

print(f"=== B1 probe AGT — {datetime.now(timezone.utc).isoformat()} UTC ===")
print(f"Symbol: {SYM}")
print(f"D-2 = 2026-08-10, D2_start_ms={D2_start_ms}, D2_end_ms={D2_end_ms}")
print()

# --- 1. topLongShortPositionRatio (pos_r candidate) ---
print("=== 1. topLongShortPositionRatio (period=1h, limit=5 recent) ===")
try:
    pos_data = fetch_lsr(ENDPOINTS["topLongShortPositionRatio"], SYM, period="1h", limit=5)
    for row in pos_data:
        ts_ms = row.get("timestamp", row.get("time", "?"))
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
        print(f"  ts={ts_str}  longShortRatio={row.get('longShortRatio')}  longAccount={row.get('longAccount')}  shortAccount={row.get('shortAccount')}")
    print(f"  Keys: {list(pos_data[0].keys()) if pos_data else 'empty'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# --- 2. topLongShortAccountRatio (acc_r candidate) ---
print("=== 2. topLongShortAccountRatio (period=1h, limit=5 recent) ===")
try:
    acc_data = fetch_lsr(ENDPOINTS["topLongShortAccountRatio"], SYM, period="1h", limit=5)
    for row in acc_data:
        ts_ms = row.get("timestamp", row.get("time", "?"))
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
        print(f"  ts={ts_str}  longShortRatio={row.get('longShortRatio')}  longAccount={row.get('longAccount')}  shortAccount={row.get('shortAccount')}")
    print(f"  Keys: {list(acc_data[0].keys()) if acc_data else 'empty'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# --- 3. globalLongShortAccountRatio (gLSR) ---
print("=== 3. globalLongShortAccountRatio (period=1h, limit=5 recent) ===")
try:
    glsr_data = fetch_lsr(ENDPOINTS["globalLongShortAccountRatio"], SYM, period="1h", limit=5)
    for row in glsr_data:
        ts_ms = row.get("timestamp", row.get("time", "?"))
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
        print(f"  ts={ts_str}  longShortRatio={row.get('longShortRatio')}  longAccount={row.get('longAccount')}  shortAccount={row.get('shortAccount')}")
    print(f"  Keys: {list(glsr_data[0].keys()) if glsr_data else 'empty'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# --- 4. openInterestHist (period=1h, limit=5 recent) ---
print("=== 4. openInterestHist (period=1h, limit=5 recent) ===")
try:
    oih_data = fetch_oi_hist(SYM, period="1h", limit=5)
    for row in oih_data:
        ts_ms = row.get("timestamp", row.get("time", "?"))
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
        print(f"  ts={ts_str}  sumOpenInterest={row.get('sumOpenInterest')}  sumOpenInterestValue={row.get('sumOpenInterestValue')}")
    print(f"  Keys: {list(oih_data[0].keys()) if oih_data else 'empty'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# --- 5. /fapi/v1/openInterest now ---
print("=== 5. /fapi/v1/openInterest (now) ===")
try:
    oi_now = fetch_oi_now(SYM)
    print(f"  openInterest={oi_now.get('openInterest')}  time={oi_now.get('time')}")
    ts_ms = oi_now.get("time")
    if ts_ms:
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat()
        print(f"  time_utc={ts_str}")
    print(f"  Full: {json.dumps(oi_now)}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# --- 6. D-2 boundary probe: fetch bars AROUND 2026-08-10 00:00 UTC ---
# Need bar 1h CUỐI D-2 = bar closing at 23:00 UTC on 2026-08-10 (open 22:00, close 23:00)
# = timestamp 2026-08-10 23:00:00 UTC (bar start time)
# For 1h bars: bar at T = opens at T, closes at T+1h
# "cuối ngày D-2" = bar opening at 23:00 UTC 2026-08-10, ts = D2_end_ms - 1h

D2_23h_ms = int(datetime(2026, 8, 10, 23, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
D2_22h_ms = int(datetime(2026, 8, 10, 22, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

print("=== 6. D-2 boundary: last bar of 2026-08-10 (1h, near 23:00 UTC) ===")
print(f"  Target D-2 23:00 UTC ms = {D2_23h_ms}")

for ep_name, ep_url in [
    ("topLongShortPositionRatio", ENDPOINTS["topLongShortPositionRatio"]),
    ("topLongShortAccountRatio",  ENDPOINTS["topLongShortAccountRatio"]),
]:
    print(f"\n  --- {ep_name} startTime around D-2 22:00 UTC ---")
    try:
        r = requests.get(ep_url, params={
            "symbol": SYM, "period": "1h", "limit": 3,
            "startTime": D2_22h_ms
        }, timeout=15)
        r.raise_for_status()
        data = r.json()
        for row in data:
            ts_ms = row.get("timestamp", row.get("time", "?"))
            ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
            print(f"    ts={ts_str} ({ts_ms})  longShortRatio={row.get('longShortRatio')}")
    except Exception as e:
        print(f"    ERROR: {e}")

# OI hist D-2 23:00
print(f"\n  --- openInterestHist startTime around D-2 22:00 UTC ---")
try:
    r = requests.get(ENDPOINTS["openInterestHist"], params={
        "symbol": SYM, "period": "1h", "limit": 3,
        "startTime": D2_22h_ms, "contractType": "PERPETUAL"
    }, timeout=15)
    r.raise_for_status()
    data = r.json()
    for row in data:
        ts_ms = row.get("timestamp", row.get("time", "?"))
        ts_str = datetime.fromtimestamp(int(ts_ms)/1000, tz=timezone.utc).isoformat() if str(ts_ms).isdigit() else "?"
        print(f"    ts={ts_str} ({ts_ms})  sumOpenInterest={row.get('sumOpenInterest')}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=== 7. MAPPING ASSESSMENT ===")
print("  pos_r = topLongShortPositionRatio → longShortRatio field")
print("  acc_r = topLongShortAccountRatio  → longShortRatio field")
print("  gLSR  = globalLongShortAccountRatio → longShortRatio field")
print("  oi_token = openInterestHist → sumOpenInterest field")
print()
print("  div_raw_prov = pos_r / acc_r = (topLong/shortPosition ratio) / (topLong/shortAccount ratio)")
print()
print("DỪNG — chờ operator duyệt trước B2.")

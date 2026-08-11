"""Re-test D-2 boundary: verify if startTime+endTime epoch-ms works for historical LSR fetch.
PART 1: Show exact params old probe sent (confirm epoch ms, not ISO string).
PART 2: Fetch with startTime+endTime bracketing 2026-08-08 12:00-13:00 UTC (3 days ago).
PART 3: Fetch with startTime+endTime bracketing 2026-08-09 00:00-01:00 UTC (true D-2 for T2 on 2026-08-11).
data-source: Binance /futures/data endpoints (public, no auth)
machine: local
date-range: 2026-08-12
code-commit: see git log
"""
import sys, io, json, requests
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYM  = "AGTUSDT"
BASE = "https://fapi.binance.com"
EP_POS = f"{BASE}/futures/data/topLongShortPositionRatio"
EP_ACC = f"{BASE}/futures/data/topLongShortAccountRatio"
EP_OIH = f"{BASE}/futures/data/openInterestHist"

def fetch_ep(url, params):
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json(), r.url  # r.url = actual request URL with encoded params

def ts_str(ms):
    try:
        return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).isoformat()
    except Exception:
        return str(ms)

# ── Epoch MS reference points ──────────────────────────────────────────────
# From previous probe output: D2_start_ms = 1786320000000 = 2026-08-10 00:00 UTC
OLD_START_MS   = 1786320000000 + 22*3600*1000  # 2026-08-10 22:00 UTC = 1786399200000 (old probe's startTime)

# 3-days-ago test: 2026-08-08 12:00-13:00 UTC
HIST_START_MS  = 1786147200000 + 12*3600*1000  # 1786190400000 = 2026-08-08 12:00 UTC
HIST_END_MS    = HIST_START_MS + 3600*1000      # 1786194000000 = 2026-08-08 13:00 UTC

# True D-2 for T2 on 2026-08-11: D-2 = 2026-08-09
D2_TRUE_START  = 1786233600000                  # 2026-08-09 00:00 UTC
D2_TRUE_END    = D2_TRUE_START + 3600*1000      # 2026-08-09 01:00 UTC

now_utc = datetime.now(timezone.utc).isoformat()
print(f"=== B1b re-test D-2 boundary — {now_utc} ===")
print()

# ── PART 1: Reconstruct old probe request ─────────────────────────────────
print("=== PART 1: Old probe — actual params sent ===")
print(f"  D2_22h_ms value  : {OLD_START_MS}  ({ts_str(OLD_START_MS)})")
print(f"  Python type      : {type(OLD_START_MS).__name__}  → requests encodes as decimal string in URL")
print(f"  Reconstructed URL: {EP_POS}?symbol={SYM}&period=1h&limit=3&startTime={OLD_START_MS}")
print(f"  Conclusion: startTime was sent as epoch ms integer — NOT ISO string")
print()

# ── PART 2: Historical fetch — 2026-08-08 12:00-13:00 UTC ────────────────
print("=== PART 2: Historical fetch — 2026-08-08 12:00-13:00 UTC (3 days ago) ===")
print(f"  startTime={HIST_START_MS} ({ts_str(HIST_START_MS)})")
print(f"  endTime  ={HIST_END_MS}   ({ts_str(HIST_END_MS)})")
print()

for ep_name, ep_url in [("topLongShortPositionRatio", EP_POS), ("topLongShortAccountRatio", EP_ACC)]:
    params = {"symbol": SYM, "period": "1h", "startTime": HIST_START_MS, "endTime": HIST_END_MS, "limit": 3}
    try:
        data, url_used = fetch_ep(ep_url, params)
        print(f"  {ep_name}:")
        print(f"    Actual URL: {url_used}")
        if data:
            for row in data:
                ts_ms = row.get("timestamp", row.get("time", "?"))
                match = "✓ MATCH" if str(ts_ms) == str(HIST_START_MS) else "✗ NOT 12:00"
                print(f"    ts={ts_str(ts_ms)} ({ts_ms})  ratio={row.get('longShortRatio')}  {match}")
        else:
            print(f"    EMPTY: {json.dumps(data)}")
    except Exception as e:
        print(f"  {ep_name}: ERROR {e}")
    print()

print("  openInterestHist:")
params_oi = {"symbol": SYM, "period": "1h", "startTime": HIST_START_MS, "endTime": HIST_END_MS,
             "limit": 3, "contractType": "PERPETUAL"}
try:
    data, url_used = fetch_ep(EP_OIH, params_oi)
    print(f"    Actual URL: {url_used}")
    if data:
        for row in data:
            ts_ms = row.get("timestamp", row.get("time", "?"))
            match = "✓ MATCH" if str(ts_ms) == str(HIST_START_MS) else "✗ NOT 12:00"
            print(f"    ts={ts_str(ts_ms)} ({ts_ms})  sumOI={row.get('sumOpenInterest')}  {match}")
    else:
        print(f"    EMPTY: {json.dumps(data)}")
except Exception as e:
    print(f"    ERROR: {e}")
print()

# ── PART 3: True D-2 fetch — 2026-08-09 00:00-01:00 UTC ─────────────────
print("=== PART 3: True D-2 (v2 canonical boundary) — 2026-08-09 00:00-01:00 UTC ===")
print(f"  startTime={D2_TRUE_START} ({ts_str(D2_TRUE_START)})")
print(f"  endTime  ={D2_TRUE_END}   ({ts_str(D2_TRUE_END)})")
print()

for ep_name, ep_url in [("topLongShortPositionRatio", EP_POS), ("topLongShortAccountRatio", EP_ACC)]:
    params = {"symbol": SYM, "period": "1h", "startTime": D2_TRUE_START, "endTime": D2_TRUE_END, "limit": 2}
    try:
        data, url_used = fetch_ep(ep_url, params)
        print(f"  {ep_name}:")
        print(f"    Actual URL: {url_used}")
        if data:
            for row in data:
                ts_ms = row.get("timestamp", row.get("time", "?"))
                match = "✓ MATCH D-2 00:00" if str(ts_ms) == str(D2_TRUE_START) else "✗ MISMATCH"
                print(f"    ts={ts_str(ts_ms)} ({ts_ms})  ratio={row.get('longShortRatio')}  {match}")
        else:
            print(f"    EMPTY: {json.dumps(data)}")
    except Exception as e:
        print(f"  {ep_name}: ERROR {e}")
    print()

print("  openInterestHist:")
params_oi2 = {"symbol": SYM, "period": "1h", "startTime": D2_TRUE_START, "endTime": D2_TRUE_END,
              "limit": 2, "contractType": "PERPETUAL"}
try:
    data, url_used = fetch_ep(EP_OIH, params_oi2)
    print(f"    Actual URL: {url_used}")
    if data:
        for row in data:
            ts_ms = row.get("timestamp", row.get("time", "?"))
            match = "✓ MATCH D-2 00:00" if str(ts_ms) == str(D2_TRUE_START) else "✗ MISMATCH"
            print(f"    ts={ts_str(ts_ms)} ({ts_ms})  sumOI={row.get('sumOpenInterest')}  {match}")
    else:
        print(f"    EMPTY: {json.dumps(data)}")
except Exception as e:
    print(f"    ERROR: {e}")
print()

print("=== VERDICT GUIDE ===")
print("  PART2 bars @ 12:00 UTC 2026-08-08 → startTime/endTime WORK, old probe bug was OTHER cause")
print("  PART2 returns recent bars OR empty → API ignores startTime regardless of format")
print("  Architecture: PHƯƠNG ÁN A (T1 store) confirmed regardless of verdict.")

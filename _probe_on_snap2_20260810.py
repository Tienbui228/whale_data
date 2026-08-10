"""
_probe_on_snap2_20260810.py
N-5 snap2: compare vs snap1 (09:02 UTC), gate >=13:02 UTC.
data-source: fapi.binance.com depth (public)
machine: local scratch
date: 2026-08-10
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"; SYM_LOWER = "on"
FAPI = "https://fapi.binance.com"
GATE_UTC = "13:02"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"ON SNAP2  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# Gate check
gate_h, gate_m = map(int, GATE_UTC.split(":"))
gate_ok = (NOW.hour > gate_h) or (NOW.hour == gate_h and NOW.minute >= gate_m)
if not gate_ok:
    log(f"  Gate NOT MET: current={NOW.strftime('%H:%M')} UTC, gate={GATE_UTC} UTC")
    log(f"  Reschedule needed — exit")
    sys.exit(0)

log(f"  Gate PASSED — collecting snap2")

# Load snap1
snap1_path = SCRATCH / f"{SYM_LOWER}_depth_snap1_{DATE_TAG}.json"
if not snap1_path.exists():
    log(f"  ERROR: snap1 not found at {snap1_path}"); sys.exit(1)
with open(snap1_path, encoding="utf-8") as f:
    snap1 = json.load(f)
log(f"  Snap1: {snap1['time']} mid={snap1['mid']:.7f} ratio={snap1['ratio']} {snap1['bias']}")

# Fetch snap2 depth
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:70]}: {e}"); return None

depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=20")
if not depth:
    log("  Depth fetch failed"); sys.exit(1)

bids = [(float(b[0]), float(b[1])) for b in depth.get("bids", [])]
asks = [(float(a[0]), float(a[1])) for a in depth.get("asks", [])]

mid2 = (bids[0][0] + asks[0][0]) / 2
bid2_usd = sum(p * q for p, q in bids if p >= mid2 * 0.98)
ask2_usd = sum(p * q for p, q in asks if p <= mid2 * 1.02)
ratio2 = round(bid2_usd / ask2_usd, 4) if ask2_usd > 0 else None
bias2 = "BID-HEAVY" if (ratio2 and ratio2 > 1.1) else ("ASK-HEAVY" if (ratio2 and ratio2 < 0.9) else "BALANCED")

mid1 = snap1["mid"]
price_chg = (mid2 - mid1) / mid1 * 100 if mid1 else None
ratio_chg = round(ratio2 - snap1["ratio"], 4) if (ratio2 and snap1["ratio"]) else None

log(f"\n  SNAP1 → SNAP2 comparison:")
log(f"  {'Metric':<20} {'Snap1':>14} {'Snap2':>14} {'Delta':>10}")
log(f"  {'-'*20} {'-'*14} {'-'*14} {'-'*10}")
log(f"  {'mid':<20} {snap1['mid']:>14.7f} {mid2:>14.7f} {price_chg:>+9.2f}%")
log(f"  {'bid2_usd':<20} ${snap1['bid2_usd']:>13,.0f} ${bid2_usd:>13,.0f} {''}")
log(f"  {'ask2_usd':<20} ${snap1['ask2_usd']:>13,.0f} ${ask2_usd:>13,.0f} {''}")
log(f"  {'ratio':<20} {snap1['ratio']:>14.4f} {ratio2 or 'N/A':>14} {ratio_chg or '':>10}")
log(f"  {'bias':<20} {snap1['bias']:>14} {bias2:>14} {''}")

if ratio_chg:
    trend = "BID strengthening" if ratio_chg > 0 else "ASK strengthening"
    log(f"\n  Trend: {trend} (ratio {'increased' if ratio_chg > 0 else 'decreased'} {abs(ratio_chg):.4f})")

# Live ticker
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"\n  Live: price={ticker.get('lastPrice')} 24h_pct={float(ticker.get('priceChangePercent',0)):+.2f}% vol=${float(ticker.get('quoteVolume',0)):,.0f}")

# Save snap2
snap2_data = {
    "snap": 2, "symbol": SYM,
    "time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
    "time_ts": int(NOW.timestamp()),
    "mid": mid2, "bid2_usd": round(bid2_usd, 2), "ask2_usd": round(ask2_usd, 2),
    "ratio": ratio2, "bias": bias2,
    "snap1_ref": {"time": snap1["time"], "mid": mid1, "ratio": snap1["ratio"]},
    "delta_mid_pct": round(price_chg, 4) if price_chg else None,
    "delta_ratio": ratio_chg,
}
out_snap2 = SCRATCH / f"{SYM_LOWER}_depth_snap2_{DATE_TAG}.json"
with open(out_snap2, "w", encoding="utf-8") as f:
    json.dump(snap2_data, f, ensure_ascii=False, indent=2)
log(f"\n  Saved: {out_snap2.name}")
log(f"\n[ON SNAP2 DONE]")

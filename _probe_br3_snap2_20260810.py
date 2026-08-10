"""
_probe_br3_snap2_20260810.py
BR3-5 Depth snap #2 — BROCCOLIF3BUSDT. Compare vs snap1.
Snap1: 00:45 UTC, mid=0.0069345, ratio=1.585 BID-HEAVY
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BROCCOLIF3BUSDT"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BR3 SNAP #2  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# ── Snap1 reference ───────────────────────────────────────────────────────
snap1 = json.loads((SCRATCH / f"br3_depth_snap1_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"\n  Snap1 ref: time={snap1['time']} mid={snap1['mid']} ratio={snap1['ratio']:.3f}")
log(f"             bid2=${snap1['bid2_usd']:,.0f}  ask2=${snap1['ask2_usd']:,.0f}")

# ── Order book depth ───────────────────────────────────────────────────────
log(f"\n=== Snap #2 order book ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: depth fetch failed"); sys.exit(1)

bids = [[float(p), float(q)] for p,q in depth["bids"]]
asks = [[float(p), float(q)] for p,q in depth["asks"]]

best_bid = bids[0][0]; best_ask = asks[0][0]
mid = (best_bid + best_ask) / 2
spread_pct = (best_ask - best_bid) / mid * 100

def bid_depth(pct):
    limit = mid * (1 - pct/100)
    return sum(p*q for p,q in bids if p >= limit)

def ask_depth(pct):
    limit = mid * (1 + pct/100)
    return sum(p*q for p,q in asks if p <= limit)

bands = [0.5, 1.0, 2.0, 5.0]
log(f"  Mid: {mid:.7f}  Spread: {spread_pct:.4f}%")
log(f"  {'Band':>6}  {'Bid $':>14}  {'Ask $':>14}  {'Ratio B/A':>10}")
log(f"  {'-'*6}  {'-'*14}  {'-'*14}  {'-'*10}")
for pct in bands:
    b = bid_depth(pct); a = ask_depth(pct)
    r = b/a if a > 0 else float('inf')
    log(f"  {pct:>5.1f}%  ${b:>13,.0f}  ${a:>13,.0f}  {r:>10.3f}")

bid2 = bid_depth(2); ask2 = ask_depth(2)
ratio2 = bid2/ask2 if ask2 > 0 else None
bid5 = bid_depth(5); ask5 = ask_depth(5)
ratio5 = bid5/ask5 if ask5 > 0 else None

# ── Compare snap1 vs snap2 ────────────────────────────────────────────────
log(f"\n=== Snap1 vs Snap2 comparison ===")
log(f"  {'Metric':<20} {'Snap1':>15} {'Snap2':>15} {'Change':>12}")
log(f"  {'-'*20} {'-'*15} {'-'*15} {'-'*12}")
log(f"  {'mid':<20} {snap1['mid']:>15.7f} {mid:>15.7f} {(mid-snap1['mid'])/snap1['mid']*100:>+11.3f}%")
log(f"  {'bid2_usd':<20} {snap1['bid2_usd']:>15,.0f} {bid2:>15,.0f} {(bid2-snap1['bid2_usd'])/snap1['bid2_usd']*100:>+11.1f}%")
log(f"  {'ask2_usd':<20} {snap1['ask2_usd']:>15,.0f} {ask2:>15,.0f} {(ask2-snap1['ask2_usd'])/snap1['ask2_usd']*100:>+11.1f}%")
log(f"  {'ratio_2pct':<20} {snap1['ratio']:>15.3f} {ratio2:>15.3f} {ratio2-snap1['ratio']:>+11.3f}")

bias = "BID-HEAVY" if (ratio2 or 0) > 1.2 else ("ASK-HEAVY" if (ratio2 or 0) < 0.8 else "BALANCED")
log(f"\n  Snap2 bias: {bias}  (ratio={ratio2:.3f})")

# Depth trend verdict
if ratio2 > snap1['ratio']:
    trend = "BID strengthening (buyer support gia tang)"
elif ratio2 < snap1['ratio'] * 0.7:
    trend = "BID weakening significantly"
else:
    trend = "Depth stable"
log(f"  Depth trend: {trend}")

# ── Ticker ────────────────────────────────────────────────────────────────
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"\n  Ticker: lastPrice={ticker.get('lastPrice')} 24h_pct={float(ticker.get('priceChangePercent',0)):+.2f}% vol=${float(ticker.get('quoteVolume',0)):,.0f}")

# ── Save ──────────────────────────────────────────────────────────────────
snap2 = {
    "snap": 2, "symbol": SYM,
    "time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
    "mid": mid, "spread_pct": spread_pct,
    "bid2_usd": bid2, "ask2_usd": ask2, "ratio": ratio2,
    "bid5_usd": bid5, "ask5_usd": ask5, "ratio5": ratio5,
    "vs_snap1": {
        "mid_chg_pct": round((mid-snap1['mid'])/snap1['mid']*100, 4),
        "bid2_chg_pct": round((bid2-snap1['bid2_usd'])/snap1['bid2_usd']*100, 2),
        "ask2_chg_pct": round((ask2-snap1['ask2_usd'])/snap1['ask2_usd']*100, 2),
        "ratio_delta": round(ratio2 - snap1['ratio'], 4),
    },
    "bias": bias, "trend": trend,
}
out = SCRATCH / f"br3_depth_snap2_{DATE_TAG}.json"
out.write_text(json.dumps(snap2, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")
log(f"\n[BR3 SNAP2 DONE]")

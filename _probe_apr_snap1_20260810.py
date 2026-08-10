"""
_probe_apr_snap1_20260810.py
A-5: Depth snap #1 — APRUSDT. Record time for snap #2 gate (≥4h after).
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-5 DEPTH SNAP #1  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# ── Order book depth ───────────────────────────────────────────────────────
log(f"\n=== Order book depth (limit=500) ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: depth fetch failed"); sys.exit(1)

bids = [[float(p), float(q)] for p,q in depth["bids"]]
asks = [[float(p), float(q)] for p,q in depth["asks"]]

best_bid = bids[0][0]; best_ask = asks[0][0]
mid = (best_bid + best_ask) / 2
spread_pct = (best_ask - best_bid) / mid * 100

log(f"  Best bid: {best_bid:.6f}")
log(f"  Best ask: {best_ask:.6f}")
log(f"  Mid: {mid:.6f}")
log(f"  Spread: {spread_pct:.4f}%")

# Aggregate by depth bands
def agg_side(orders, mid, pct_list):
    result = {}
    for pct in pct_list:
        limit_bid = mid * (1 - pct/100)
        limit_ask = mid * (1 + pct/100)
        # For bids: price >= limit_bid
        total = sum(p*q for p,q in orders if
                    (orders[0][0] > mid/2 and p >= limit_bid) or  # bid side
                    (orders[0][0] < mid*2 and p <= limit_ask))     # ask side
        result[pct] = total
    return result

# Bids within X% of mid
def bid_depth(pct):
    limit = mid * (1 - pct/100)
    return sum(p*q for p,q in bids if p >= limit)

def ask_depth(pct):
    limit = mid * (1 + pct/100)
    return sum(p*q for p,q in asks if p <= limit)

bands = [0.5, 1.0, 2.0, 5.0]
log(f"\n  Depth by band:")
log(f"  {'Band':>6}  {'Bid $':>14}  {'Ask $':>14}  {'Ratio B/A':>10}")
log(f"  {'-'*6}  {'-'*14}  {'-'*14}  {'-'*10}")
for pct in bands:
    b = bid_depth(pct); a = ask_depth(pct)
    r = b/a if a > 0 else float('inf')
    log(f"  {pct:>5.1f}%  ${b:>13,.0f}  ${a:>13,.0f}  {r:>10.3f}")

# ±2% as canonical
bid2 = bid_depth(2); ask2 = ask_depth(2)
ratio_2 = bid2/ask2 if ask2 > 0 else None
# ±5%
bid5 = bid_depth(5); ask5 = ask_depth(5)
ratio_5 = bid5/ask5 if ask5 > 0 else None

log(f"\n  CANONICAL ±2%: bid=${bid2:,.0f}  ask=${ask2:,.0f}  ratio={ratio_2:.3f}")
log(f"  CANONICAL ±5%: bid=${bid5:,.0f}  ask=${ask5:,.0f}  ratio={ratio_5:.3f}")

bias = "BID-HEAVY (support)" if (ratio_2 or 0) > 1.2 else ("ASK-HEAVY (resistance)" if (ratio_2 or 0) < 0.8 else "BALANCED")
log(f"  Depth bias: {bias}")

# ── Current ticker ─────────────────────────────────────────────────────────
log(f"\n=== Current ticker ===")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"  lastPrice: {ticker.get('lastPrice')}")
    log(f"  24h change: {float(ticker.get('priceChangePercent',0)):.2f}%")
    log(f"  24h vol: ${float(ticker.get('quoteVolume',0)):,.0f}")
    log(f"  24h count: {ticker.get('count')} trades")

# ── Save snap ──────────────────────────────────────────────────────────────
snap = {
    "symbol": SYM,
    "snap_time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
    "snap_ts": NOW.isoformat(),
    "mid": mid,
    "spread_pct": spread_pct,
    "bid_2pct": bid2,
    "ask_2pct": ask2,
    "ratio_2pct": ratio_2,
    "bid_5pct": bid5,
    "ask_5pct": ask5,
    "ratio_5pct": ratio_5,
    "bias": bias,
    "snap2_gate": "≥04h after snap1 = " + NOW.strftime("%Y-%m-%d") + " " +
                  f"{NOW.hour+4:02d}:{NOW.minute:02d} UTC",
}
out = SCRATCH / f"apr_snap1_{DATE_TAG}.json"
out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
log(f"\n  Snap #1 saved: {out.name}")
log(f"  SNAP #2 GATE: ≥{snap['snap2_gate']}")
log(f"\n[A-5 SNAP1 DONE]")

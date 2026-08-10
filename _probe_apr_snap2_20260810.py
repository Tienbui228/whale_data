"""
_probe_apr_snap2_20260810.py
APR snap #2 — APRUSDT. Compare vs snap1 (03:42 UTC, mid=0.19755, ratio=1.638 BID-HEAVY).
Gate ≥07:42 UTC (4h after snap1).
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
log(f"APR SNAP #2  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# Snap1 reference
snap1 = json.loads((SCRATCH / f"apr_snap1_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"\n  Snap1 ref: {snap1['snap_time']}")
log(f"    mid={snap1['mid']}  spread={snap1['spread_pct']:.4f}%")
log(f"    bid2=${snap1['bid_2pct']:,.0f}  ask2=${snap1['ask_2pct']:,.0f}  ratio={snap1['ratio_2pct']:.3f}")
log(f"    bias: {snap1['bias']}")

# Order book snap2
log(f"\n=== Snap #2 ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: depth fetch failed"); sys.exit(1)

bids = [[float(p), float(q)] for p,q in depth["bids"]]
asks = [[float(p), float(q)] for p,q in depth["asks"]]
best_bid = bids[0][0]; best_ask = asks[0][0]
mid = (best_bid + best_ask) / 2
spread_pct = (best_ask - best_bid) / mid * 100

def bid_usd(pct): return sum(p*q for p,q in bids if p >= mid*(1-pct/100))
def ask_usd(pct): return sum(p*q for p,q in asks if p <= mid*(1+pct/100))

log(f"  mid={mid:.7f}  spread={spread_pct:.4f}%")
log(f"  best_bid={best_bid}  best_ask={best_ask}")
log(f"  {'Band':>6}  {'Bid $':>14}  {'Ask $':>14}  {'Ratio':>8}")
log(f"  {'-'*6}  {'-'*14}  {'-'*14}  {'-'*8}")
for pct in [0.5, 1.0, 2.0, 5.0]:
    b = bid_usd(pct); a = ask_usd(pct)
    r = b/a if a>0 else float('inf')
    log(f"  {pct:>5.1f}%  ${b:>13,.0f}  ${a:>13,.0f}  {r:>8.3f}")

bid2 = bid_usd(2); ask2 = ask_usd(2); ratio2 = bid2/ask2 if ask2>0 else None
bid5 = bid_usd(5); ask5 = ask_usd(5); ratio5 = bid5/ask5 if ask5>0 else None

bias = "BID-HEAVY" if (ratio2 or 0)>1.2 else ("ASK-HEAVY" if (ratio2 or 0)<0.8 else "BALANCED")
log(f"\n  Bias (±2%): {bias}  ratio={ratio2:.3f}")

# Compare snap1 vs snap2
log(f"\n=== Snap1 vs Snap2 ===")
def chg(new, old): return (new-old)/old*100 if old else 0
log(f"  {'Metric':<20} {'Snap1':>12} {'Snap2':>12} {'Δ%':>10}")
log(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
log(f"  {'mid':<20} {snap1['mid']:>12.5f} {mid:>12.5f} {chg(mid,snap1['mid']):>+9.3f}%")
log(f"  {'bid2_usd':<20} {snap1['bid_2pct']:>12,.0f} {bid2:>12,.0f} {chg(bid2,snap1['bid_2pct']):>+9.1f}%")
log(f"  {'ask2_usd':<20} {snap1['ask_2pct']:>12,.0f} {ask2:>12,.0f} {chg(ask2,snap1['ask_2pct']):>+9.1f}%")
log(f"  {'ratio_2pct':<20} {snap1['ratio_2pct']:>12.3f} {ratio2:>12.3f} {ratio2-snap1['ratio_2pct']:>+10.3f}")

if ratio2 > snap1['ratio_2pct']: trend = "BID strengthening"
elif ratio2 < snap1['ratio_2pct']*0.7: trend = "BID weakening significantly"
else: trend = "Depth stable"
log(f"\n  Depth trend: {trend}")

# Ticker
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"\n  Ticker: last={ticker.get('lastPrice')} 24h={float(ticker.get('priceChangePercent',0)):+.2f}% vol=${float(ticker.get('quoteVolume',0)):,.0f}")

# Save
snap2 = {
    "snap": 2, "symbol": SYM,
    "time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
    "mid": mid, "spread_pct": spread_pct,
    "bid_2pct": bid2, "ask_2pct": ask2, "ratio_2pct": ratio2,
    "bid_5pct": bid5, "ask_5pct": ask5, "ratio_5pct": ratio5,
    "bias": bias, "trend": trend,
    "vs_snap1": {
        "mid_chg_pct": round(chg(mid,snap1['mid']), 4),
        "bid2_chg_pct": round(chg(bid2,snap1['bid_2pct']), 2),
        "ask2_chg_pct": round(chg(ask2,snap1['ask_2pct']), 2),
        "ratio_delta": round(ratio2 - snap1['ratio_2pct'], 4),
    },
}
out = SCRATCH / f"apr_snap2_{DATE_TAG}.json"
out.write_text(json.dumps(snap2, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")
log(f"\n[APR SNAP2 DONE]")

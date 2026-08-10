"""
_probe_btw_snap2_20260810.py
BTW snap #2 — BTWUSDT. Compare vs snap1 (08:01 UTC, mid=0.19879, ratio=1.249 BID-HEAVY).
Gate ≥12:01 UTC (4h after snap1).
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BTW SNAP #2  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# Snap1 reference
snap1 = json.loads((SCRATCH / f"btw_depth_snap1_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"\n  Snap1 ref: {snap1['time']}")
log(f"    mid={snap1['mid']:.7f}  spread={snap1['spread_pct']:.4f}%")
log(f"    bid2=${snap1['bid2_usd']:,.0f}  ask2=${snap1['ask2_usd']:,.0f}  ratio={snap1['ratio']:.3f}")
log(f"    bias: {snap1['bias']}")

# Check gate
snap1_ts = snap1.get("time_ts", 0)
elapsed_h = (NOW.timestamp() - snap1_ts) / 3600 if snap1_ts else None
if elapsed_h and elapsed_h < 4.0:
    log(f"\n  WARNING: only {elapsed_h:.2f}h since snap1 (gate = 4h). Collecting anyway.")
else:
    log(f"\n  Gate check: {elapsed_h:.2f}h elapsed — PASS" if elapsed_h else "  Gate check: OK")

# Order book
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
bid05 = bid_usd(0.5); ask05 = ask_usd(0.5)

bias = "BID-HEAVY" if (ratio2 or 0)>1.2 else ("ASK-HEAVY" if (ratio2 or 0)<0.8 else "BALANCED")
log(f"\n  Bias (±2%): {bias}  ratio={ratio2:.3f}")

# Wall detection
bids5 = [[p,q] for p,q in bids if p >= mid*0.95]
asks5 = [[p,q] for p,q in asks if p <= mid*1.05]
top_bid = max(bids5, key=lambda x: x[0]*x[1]) if bids5 else None
top_ask = max(asks5, key=lambda x: x[0]*x[1]) if asks5 else None
if top_bid: log(f"  Top bid wall: ${top_bid[0]:.6f} × {top_bid[1]:.0f} = ${top_bid[0]*top_bid[1]:,.0f}")
if top_ask: log(f"  Top ask wall: ${top_ask[0]:.6f} × {top_ask[1]:.0f} = ${top_ask[0]*top_ask[1]:,.0f}")

# Compare
log(f"\n=== Snap1 vs Snap2 ===")
def chg(new, old): return (new-old)/old*100 if old else 0
log(f"  {'Metric':<20} {'Snap1':>12} {'Snap2':>12} {'Δ%':>10}")
log(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
log(f"  {'mid':<20} {snap1['mid']:>12.7f} {mid:>12.7f} {chg(mid,snap1['mid']):>+9.3f}%")
log(f"  {'bid2_usd':<20} {snap1['bid2_usd']:>12,.0f} {bid2:>12,.0f} {chg(bid2,snap1['bid2_usd']):>+9.1f}%")
log(f"  {'ask2_usd':<20} {snap1['ask2_usd']:>12,.0f} {ask2:>12,.0f} {chg(ask2,snap1['ask2_usd']):>+9.1f}%")
log(f"  {'ratio_2pct':<20} {snap1['ratio']:>12.3f} {ratio2:>12.3f} {ratio2-snap1['ratio']:>+10.3f}")

if ratio2 > snap1['ratio']: trend = "BID strengthening"
elif ratio2 < snap1['ratio']*0.7: trend = "BID weakening significantly"
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
    "time_ts": NOW.timestamp(),
    "mid": mid, "spread_pct": spread_pct,
    "bid2_usd": bid2, "ask2_usd": ask2, "ratio": ratio2,
    "bid5_usd": bid5, "ask5_usd": ask5, "ratio5": ratio5,
    "bias": bias, "trend": trend,
    "top_bid_wall_usd": top_bid[0]*top_bid[1] if top_bid else None,
    "top_ask_wall_usd": top_ask[0]*top_ask[1] if top_ask else None,
    "vs_snap1": {
        "mid_chg_pct": round(chg(mid,snap1['mid']), 4),
        "bid2_chg_pct": round(chg(bid2,snap1['bid2_usd']), 2),
        "ask2_chg_pct": round(chg(ask2,snap1['ask2_usd']), 2),
        "ratio_delta": round(ratio2 - snap1['ratio'], 4),
    },
}
out = SCRATCH / f"btw_depth_snap2_{DATE_TAG}.json"
out.write_text(json.dumps(snap2, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")
log(f"\n[BTW SNAP2 DONE]")

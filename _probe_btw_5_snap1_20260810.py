"""
_probe_btw_5_snap1_20260810.py
W-5: Depth snap #1 + ticker + venue audit — BTWUSDT.
Snap2 gate = this_time + 4h.
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
log(f"W-5 SNAP #1  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── 1. Venue audit ────────────────────────────────────────────────────────────
log("\n=== 1. Venue audit ===")
log(f"  Perp: BTWUSDT on Binance FAPI — CONFIRMED (67 klines collected)")
log(f"  Spot: NO spot pair (WARN CSV missing in build, spot klines N/A)")
log(f"  Alpha: ALPHA_778 (BSC, 10B supply, 2.71B circ, 45.2K holders)")
log(f"  Contract: 0x444045b0ee1ee319a660a5e3d604ca0ffa35acaa (BSC)")
log(f"  Alpha listing: 2026-03-02  Perp onboard: 2026-06-04")
log(f"  Vol source: perp only (spot=N/A, alpha_taker=ABSTAIN)")
log(f"  On-chain outflow: ABSTAIN (Nansen LOCKED, BscScan = CẦN OPERATOR)")

# ── 2. Ticker ─────────────────────────────────────────────────────────────────
log("\n=== 2. Ticker (live) ===")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"  lastPrice: {ticker.get('lastPrice')}")
    log(f"  24h pct:   {float(ticker.get('priceChangePercent',0)):+.2f}%")
    log(f"  24h vol:   ${float(ticker.get('quoteVolume',0)):,.0f}")
    log(f"  highPrice: {ticker.get('highPrice')}  lowPrice: {ticker.get('lowPrice')}")
    log(f"  openPrice: {ticker.get('openPrice')}")

# ── 3. Premium / funding ──────────────────────────────────────────────────────
log("\n=== 3. Current funding ===")
pm = fetch_json(f"{FAPI}/fapi/v1/premiumIndex?symbol={SYM}")
if pm:
    log(f"  markPrice: {pm.get('markPrice')}")
    log(f"  lastFundingRate: {pm.get('lastFundingRate')}")
    log(f"  nextFundingTime: {datetime.fromtimestamp(int(pm.get('nextFundingTime',0))/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

# ── 4. Order book depth snap #1 ───────────────────────────────────────────────
log("\n=== 4. Depth snap #1 ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: depth fetch failed")
    sys.exit(1)

bids = [[float(p), float(q)] for p,q in depth["bids"]]
asks = [[float(p), float(q)] for p,q in depth["asks"]]
best_bid = bids[0][0]; best_ask = asks[0][0]
mid = (best_bid + best_ask) / 2
spread_pct = (best_ask - best_bid) / mid * 100

def bid_depth(pct): return sum(p*q for p,q in bids if p >= mid*(1-pct/100))
def ask_depth(pct): return sum(p*q for p,q in asks if p <= mid*(1+pct/100))

bands = [0.5, 1.0, 2.0, 5.0]
log(f"  Mid: {mid:.7f}  Spread: {spread_pct:.4f}%")
log(f"  best_bid: {best_bid}  best_ask: {best_ask}")
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
bid05 = bid_depth(0.5); ask05 = ask_depth(0.5)

bias = "BID-HEAVY" if (ratio2 or 0) > 1.2 else ("ASK-HEAVY" if (ratio2 or 0) < 0.8 else "BALANCED")
log(f"\n  Bias (±2%): {bias}  (ratio={ratio2:.3f})")

# Wall detection
# Find largest single level bid within 5%
bids5 = [[p,q] for p,q in bids if p >= mid*0.95]
asks5 = [[p,q] for p,q in asks if p <= mid*1.05]
top_bid = max(bids5, key=lambda x: x[0]*x[1]) if bids5 else None
top_ask = max(asks5, key=lambda x: x[0]*x[1]) if asks5 else None
if top_bid: log(f"  Top bid wall: ${top_bid[0]:.6f} × {top_bid[1]:.0f} = ${top_bid[0]*top_bid[1]:,.0f}")
if top_ask: log(f"  Top ask wall: ${top_ask[0]:.6f} × {top_ask[1]:.0f} = ${top_ask[0]*top_ask[1]:,.0f}")

# Save snap1
snap1 = {
    "snap": 1, "symbol": SYM,
    "time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
    "time_ts": NOW.timestamp(),
    "mid": mid, "spread_pct": spread_pct,
    "bid05_usd": bid05, "ask05_usd": ask05,
    "bid2_usd": bid2, "ask2_usd": ask2, "ratio": ratio2,
    "bid5_usd": bid5, "ask5_usd": ask5, "ratio5": ratio5,
    "bias": bias,
    "top_bid_wall_usd": top_bid[0]*top_bid[1] if top_bid else None,
    "top_ask_wall_usd": top_ask[0]*top_ask[1] if top_ask else None,
}
out1 = SCRATCH / f"btw_depth_snap1_{DATE_TAG}.json"
out1.write_text(json.dumps(snap1, indent=2), encoding="utf-8")
log(f"\n  Saved: {out1.name}")
log(f"  Snap2 gate: ≥ {(NOW.replace(minute=(NOW.minute+0))).strftime('%H:%M')} + 4h = collect after {NOW.hour+4:02d}:{NOW.minute:02d} UTC")

log(f"\n[W-5 SNAP1 DONE]")

"""
_probe_on_5_depth_20260810.py
N-5: Depth snap1 + venue audit (perp/spot/alpha).
ONUSDT. Saves snap1 JSON for snap2 comparison later.
data-source: fapi.binance.com + bapi.binance.com (public endpoints)
machine: local scratch
date: 2026-08-10
"""
import sys, io, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"
SYM_LOWER = "on"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-5 DEPTH SNAP1 ONUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# ── 1. Perp depth snap1 ───────────────────────────────────────────────────────
log("\n=== 1. Perp depth snap1 ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=20")
snap1_data = {}

if depth:
    bids = [(float(b[0]), float(b[1])) for b in depth.get("bids", [])]
    asks = [(float(a[0]), float(a[1])) for a in depth.get("asks", [])]

    if bids and asks:
        mid = (bids[0][0] + asks[0][0]) / 2
        # bid depth $2 = top-2% of mid
        bid_usd_2 = sum(p * q for p, q in bids if p >= mid * 0.98)
        ask_usd_2 = sum(p * q for p, q in asks if p <= mid * 1.02)
        ratio = round(bid_usd_2 / ask_usd_2, 4) if ask_usd_2 > 0 else None
        bias = "BID-HEAVY" if (ratio and ratio > 1.1) else ("ASK-HEAVY" if (ratio and ratio < 0.9) else "BALANCED")

        log(f"  mid: {mid:.7f}")
        log(f"  bid±2%: ${bid_usd_2:,.0f}  ask±2%: ${ask_usd_2:,.0f}")
        log(f"  ratio: {ratio}  bias: {bias}")

        log(f"\n  Top 5 bids:")
        for p, q in bids[:5]:
            log(f"    {p:.7f}  qty={q:,.0f}  usd=${p*q:,.0f}")
        log(f"  Top 5 asks:")
        for p, q in asks[:5]:
            log(f"    {p:.7f}  qty={q:,.0f}  usd=${p*q:,.0f}")

        snap1_data = {
            "snap": 1, "symbol": SYM,
            "time": NOW.strftime("%Y-%m-%d %H:%M UTC"),
            "time_ts": int(NOW.timestamp()),
            "mid": mid,
            "bid2_usd": round(bid_usd_2, 2),
            "ask2_usd": round(ask_usd_2, 2),
            "ratio": ratio,
            "bias": bias,
            "bids_top5": [[b[0], b[1]] for b in bids[:5]],
            "asks_top5": [[a[0], a[1]] for a in asks[:5]],
        }
        out_snap = SCRATCH / f"{SYM_LOWER}_depth_snap1_{DATE_TAG}.json"
        with open(out_snap, "w", encoding="utf-8") as f:
            json.dump(snap1_data, f, ensure_ascii=False, indent=2)
        log(f"\n  Saved: {out_snap.name}")
else:
    log("  depth fetch failed")

# ── 2. Live ticker ────────────────────────────────────────────────────────────
log("\n=== 2. Live ticker (perp) ===")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"  lastPrice: {ticker.get('lastPrice')}")
    log(f"  24h pct:   {float(ticker.get('priceChangePercent',0)):+.2f}%")
    log(f"  24h vol:   ${float(ticker.get('quoteVolume',0)):,.0f}")
    log(f"  24h high:  {ticker.get('highPrice')}  low: {ticker.get('lowPrice')}")

# ── 3. Spot venue check ───────────────────────────────────────────────────────
log("\n=== 3. Spot venue audit ===")
# ON has no spot on Binance (perp only, confirmed N-0)
spot_ticker = fetch_json(f"{SAPI}/api/v3/ticker/24hr?symbol=ONUSDT")
if spot_ticker and "lastPrice" in spot_ticker:
    log(f"  SPOT found: lastPrice={spot_ticker.get('lastPrice')} vol=${float(spot_ticker.get('quoteVolume',0)):,.0f}")
else:
    log(f"  Spot ONUSDT: NOT FOUND on Binance spot (perp-only, confirmed)")

# ── 4. Alpha spot price check ────────────────────────────────────────────────
log("\n=== 4. Alpha spot (bapi) ===")
ALPHA_TICKER_URL = "https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines?symbol=ON&interval=1d&limit=1"
alpha_tick = fetch_json(ALPHA_TICKER_URL)
if alpha_tick:
    if isinstance(alpha_tick, list) and alpha_tick:
        k = alpha_tick[0]
        log(f"  Alpha 1d last: o={k[1]} h={k[2]} l={k[3]} c={k[4]} vol={k[5]}")
    else:
        log(f"  Alpha resp: {str(alpha_tick)[:200]}")
else:
    log(f"  Alpha ticker: no data")

# ── 5. Premium Index / basis ──────────────────────────────────────────────────
log("\n=== 5. Premium Index / basis ===")
pm = fetch_json(f"{FAPI}/fapi/v1/premiumIndex?symbol={SYM}")
if pm:
    mark = float(pm.get("markPrice", 0))
    idx  = float(pm.get("indexPrice", 0))
    fr   = float(pm.get("lastFundingRate", 0))
    basis = (mark - idx) / idx * 100 if idx > 0 else None
    log(f"  mark={mark:.7f}  index={idx:.7f}")
    log(f"  basis: {basis:+.4f}%" if basis else "  basis: N/A")
    log(f"  lastFundingRate: {fr:.6f}")
    next_ft = int(pm.get("nextFundingTime", 0))
    log(f"  nextFunding: {datetime.fromtimestamp(next_ft/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

log(f"\n[N-5 DONE]")
log(f"  snap1 saved → snap2 gate: ≥4h after {NOW.strftime('%H:%M UTC')} = "
    f"{datetime.fromtimestamp(NOW.timestamp()+14400, tz=timezone.utc).strftime('%H:%M UTC')}")

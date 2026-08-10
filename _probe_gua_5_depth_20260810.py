"""
_probe_gua_5_depth_20260810.py
G-5 SNAP1: Depth snapshot — GUAUSDT perp.
Bid±2% / Ask±2% ratio. Saves JSON for snap2 compare.
data-source: fapi.binance.com/fapi/v1/depth (public, no auth)
machine: local
date: 2026-08-10
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "GUAUSDT"
SYM_LOWER = "gua"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-5 DEPTH SNAP1 GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── Fetch depth ────────────────────────────────────────────────────────────────
log(f"\n=== Depth snapshot GUAUSDT ===")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: could not fetch depth"); sys.exit(1)

bids = [(float(p), float(q)) for p, q in depth["bids"]]
asks = [(float(p), float(q)) for p, q in depth["asks"]]
if not bids or not asks:
    log("  ERROR: empty book"); sys.exit(1)

mid = (bids[0][0] + asks[0][0]) / 2
bid_lo = mid * 0.98; ask_hi = mid * 1.02

bid_vol = sum(p*q for p, q in bids if p >= bid_lo)
ask_vol = sum(p*q for p, q in asks if p <= ask_hi)
ratio = bid_vol / ask_vol if ask_vol > 0 else None

if ratio and ratio > 1.1:   wall_side = "BID-HEAVY"
elif ratio and ratio < 0.9: wall_side = "ASK-HEAVY"
else:                        wall_side = "BALANCED"

snap_time = NOW.strftime("%Y-%m-%d %H:%M UTC")
log(f"  mid:      ${mid:.7f}")
log(f"  bid±2%:   ${bid_vol:,.0f}")
log(f"  ask±2%:   ${ask_vol:,.0f}")
log(f"  ratio:    {ratio:.4f}")
log(f"  wall:     {wall_side}")
log(f"  snap_time: {snap_time}")

# Context: live pump status
log(f"\n  Context: Token pumping +54.92% today (Aug10, real-time)")
log(f"  Live funding (last 3h): 0.001101 EXTREME HOT")
log(f"  Crowd: gLSR=2.87 VERY BULL, div_avg3=0.41 BEAR (smart shorts vs retail longs)")

# ── Save snap1 ────────────────────────────────────────────────────────────────
snap1 = {
    "symbol": SYM, "snap": 1, "date": DATE_TAG,
    "snap_time": snap_time,
    "mid": mid, "bid_vol": bid_vol, "ask_vol": ask_vol,
    "ratio": ratio, "wall": wall_side,
    "best_bid": bids[0][0], "best_ask": asks[0][0],
    "bid_levels": len(bids), "ask_levels": len(asks),
    "gate_snap2_utc": "15:50",
}
out = SCRATCH / f"{SYM_LOWER}_depth_snap1_{DATE_TAG}.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(snap1, f, indent=2)
log(f"\n  Saved: {out.name}")
log(f"  Gate snap2: ≥15:50 UTC (2h from snap1)")
log(f"\n[G-5 SNAP1 DONE] → schedule snap2 wakeup ≥15:50 UTC")

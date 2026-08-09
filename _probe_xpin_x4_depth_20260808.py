"""
_probe_xpin_x4_depth_20260808.py
X-4: Depth snap ±2% XPINUSDT. Save to scratch/xpin_depth_snap1_20260808.json.
Also: alpha_id check + LSR FAPI status summary.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-4 DEPTH SNAP  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M %Z')}")
log(f"Snap timestamp: {NOW_UTC.isoformat()}")

# ── Depth orderbook ────────────────────────────────────────────────────────────
BASE_FAPI = "https://fapi.binance.com"
SYM = "XPINUSDT"
DATE_TAG = "20260808"

url_book = f"{BASE_FAPI}/fapi/v1/depth?symbol={SYM}&limit=1000"
try:
    with urllib.request.urlopen(url_book, timeout=15) as r:
        book = json.loads(r.read())
    bids = [(float(p), float(q)) for p, q in book.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in book.get("asks", [])]
    log(f"  Order book: {len(bids)} bids, {len(asks)} asks")
except Exception as e:
    log(f"  ERROR fetching orderbook: {e}")
    sys.exit(1)

# Mid price
best_bid = bids[0][0] if bids else 0
best_ask = asks[0][0] if asks else 0
mid = (best_bid + best_ask) / 2
log(f"  Best bid: {best_bid}, Best ask: {best_ask}, Mid: {mid:.8f}")

# ±2% depth
threshold_low  = mid * 0.98
threshold_high = mid * 1.02

bid2_usd  = sum(p * q for p, q in bids if p >= threshold_low)
ask2_usd  = sum(p * q for p, q in asks if p <= threshold_high)
depth_ratio = bid2_usd / ask2_usd if ask2_usd > 0 else None

# Walls (largest single level ±5%)
bid5_levels = [(p, q, p*q) for p, q in bids if p >= mid*0.95]
ask5_levels = [(p, q, p*q) for p, q in asks if p <= mid*1.05]

bid_wall = max(bid5_levels, key=lambda x: x[2]) if bid5_levels else (None, None, None)
ask_wall = max(ask5_levels, key=lambda x: x[2]) if ask5_levels else (None, None, None)

log(f"\n  ── DEPTH ±2% ──")
log(f"  Mid:         {mid:.8f}")
log(f"  Bid ±2%:    ${bid2_usd:,.0f}")
log(f"  Ask ±2%:    ${ask2_usd:,.0f}")
log(f"  Ratio (bid/ask): {depth_ratio:.4f}" if depth_ratio else "  Ratio: N/A")
log(f"  Bid wall: px={bid_wall[0]}, usd=${bid_wall[2]:,.0f}" if bid_wall[0] else "  Bid wall: N/A")
log(f"  Ask wall: px={ask_wall[0]}, usd=${ask_wall[2]:,.0f}" if ask_wall[0] else "  Ask wall: N/A")

# Save snap
snap = {
    "sym": SYM,
    "snap_time": NOW_UTC.isoformat(),
    "snap_label": "snap1",
    "mid": mid,
    "best_bid": best_bid,
    "best_ask": best_ask,
    "bid2pct_usd": round(bid2_usd, 0),
    "ask2pct_usd": round(ask2_usd, 0),
    "depth_ratio": round(depth_ratio, 4) if depth_ratio else None,
    "bid_wall_px": bid_wall[0],
    "bid_wall_usd": round(bid_wall[2], 0) if bid_wall[2] else None,
    "ask_wall_px": ask_wall[0],
    "ask_wall_usd": round(ask_wall[2], 0) if ask_wall[2] else None,
}

out_path = SCRATCH / f"xpin_depth_snap1_{DATE_TAG}.json"
out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
log(f"\n  Saved: {out_path.name}")

# ── BAPI alpha check ──────────────────────────────────────────────────────────
log("\n=== ALPHA STATUS (from alpha_id_map) ===")
ALPHA_MAP = ROOT / "data" / "config" / "alpha_id_map.json"
if ALPHA_MAP.exists():
    alpha_map = json.loads(ALPHA_MAP.read_text(encoding="utf-8"))
    alpha_id = alpha_map.get("XPIN", "NOT_IN_MAP")
    log(f"  alpha_id_map: XPIN → {alpha_id}")
else:
    log("  alpha_id_map not found")

# BAPI token list check (cached or fresh)
bapi_path = SCRATCH / f"xpin_bapi_{DATE_TAG}.json"
if bapi_path.exists():
    bapi = json.loads(bapi_path.read_text(encoding="utf-8"))
    log(f"  BAPI cache: {bapi_path.name}")
else:
    log("  Fetching BAPI token list...")
    try:
        url_tl = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
        req = urllib.request.Request(url_tl, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            tl_data = json.loads(r.read())
        tokens = tl_data.get("data", {}).get("tokenList", [])
        xpin_tokens = [t for t in tokens if t.get("tokenSymbol","").upper()=="XPIN"
                       or (t.get("alphaId","") or "").upper()=="ALPHA_334"]
        bapi = xpin_tokens[0] if xpin_tokens else {}
        bapi_path.write_text(json.dumps(bapi, indent=2), encoding="utf-8")
        log(f"  BAPI fetched: {len(tokens)} total tokens, XPIN match: {len(xpin_tokens)}")
    except Exception as e:
        log(f"  BAPI ERROR: {e}")
        bapi = {}

if bapi:
    log(f"  alphaId:     {bapi.get('alphaId','?')}")
    log(f"  contract:    {bapi.get('contractAddress','?')}")
    log(f"  tokenSymbol: {bapi.get('tokenSymbol','?')}")
    log(f"  fullyDelisted: {bapi.get('fullyDelisted','?')}")
    supply_fields = {k: bapi.get(k) for k in ("totalSupply","circulatingSupply","holders") if bapi.get(k)}
    log(f"  supply/holders: {supply_fields}")
else:
    log("  XPIN not found in BAPI token list")

# ── Summary ───────────────────────────────────────────────────────────────────
log(f"\n=== X-4 SNAP #1 SUMMARY ===")
log(f"  Time:    {NOW_UTC.strftime('%H:%M:%S UTC')}")
log(f"  Mid:     {mid:.8f}")
log(f"  Bid±2%:  ${bid2_usd:,.0f}")
log(f"  Ask±2%:  ${ask2_usd:,.0f}")
log(f"  Ratio:   {depth_ratio:.4f}" if depth_ratio else "  Ratio:   N/A")
log(f"  Snap #2: needed ≥{NOW_UTC.strftime('%H')}:{int(NOW_UTC.strftime('%M'))+0:02d} +4h = ~{(int(NOW_UTC.strftime('%H'))+4)%24:02d}:{NOW_UTC.strftime('%M')} UTC")
log(f"\n[X-4 SNAP DONE]")

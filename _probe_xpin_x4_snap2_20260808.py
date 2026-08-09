"""
_probe_xpin_x4_snap2_20260808.py
X-4: Depth snap #2 XPINUSDT — lần 2 (≥4h sau snap #1 lúc 09:18 UTC).
Cần chạy ≥13:18 UTC 08/08/2026.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-4 DEPTH SNAP #2  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M:%S UTC')}")

# Verify timing
snap1_time = datetime(2026, 8, 8, 9, 18, 3, tzinfo=timezone.utc)
elapsed_h = (NOW_UTC - snap1_time).total_seconds() / 3600
if elapsed_h < 4.0:
    log(f"  WARNING: only {elapsed_h:.2f}h since snap #1 — need ≥4h. Proceeding anyway (caller verified).")
else:
    log(f"  OK: {elapsed_h:.2f}h since snap #1 ✓")

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
    log(f"  ERROR: {e}"); sys.exit(1)

best_bid = bids[0][0] if bids else 0
best_ask = asks[0][0] if asks else 0
mid = (best_bid + best_ask) / 2
threshold_low  = mid * 0.98
threshold_high = mid * 1.02

bid2_usd  = sum(p * q for p, q in bids if p >= threshold_low)
ask2_usd  = sum(p * q for p, q in asks if p <= threshold_high)
depth_ratio = bid2_usd / ask2_usd if ask2_usd > 0 else None

bid5 = [(p, q, p*q) for p, q in bids if p >= mid*0.95]
ask5 = [(p, q, p*q) for p, q in asks if p <= mid*1.05]
bid_wall = max(bid5, key=lambda x: x[2]) if bid5 else (None, None, None)
ask_wall = max(ask5, key=lambda x: x[2]) if ask5 else (None, None, None)

log(f"\n  ── DEPTH ±2% SNAP #2 ──")
log(f"  Mid:         {mid:.8f}")
log(f"  Bid ±2%:    ${bid2_usd:,.0f}")
log(f"  Ask ±2%:    ${ask2_usd:,.0f}")
log(f"  Ratio (bid/ask): {depth_ratio:.4f}" if depth_ratio else "  Ratio: N/A")
log(f"  Bid wall: px={bid_wall[0]}, usd=${bid_wall[2]:,.0f}" if bid_wall[0] else "  Bid wall: N/A")
log(f"  Ask wall: px={ask_wall[0]}, usd=${ask_wall[2]:,.0f}" if ask_wall[0] else "  Ask wall: N/A")

snap = {
    "sym": SYM,
    "snap_time": NOW_UTC.isoformat(),
    "snap_label": "snap2",
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

out_path = SCRATCH / f"xpin_depth_snap2_{DATE_TAG}.json"
out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
log(f"\n  Saved: {out_path.name}")

# Load snap1 for comparison
snap1_path = SCRATCH / f"xpin_depth_snap1_{DATE_TAG}.json"
if snap1_path.exists():
    s1 = json.loads(snap1_path.read_text(encoding="utf-8"))
    log(f"\n  ── COMPARISON snap1 vs snap2 ──")
    log(f"  Snap #1 ({s1['snap_time'][:16]}): mid={s1['mid']:.8f} bid2=${s1['bid2pct_usd']:,.0f} ask2=${s1['ask2pct_usd']:,.0f} ratio={s1['depth_ratio']}")
    log(f"  Snap #2 ({NOW_UTC.strftime('%Y-%m-%dT%H:%M')}): mid={mid:.8f} bid2=${bid2_usd:,.0f} ask2=${ask2_usd:,.0f} ratio={depth_ratio:.4f}" if depth_ratio else "")
    mid_chg = (mid - s1['mid'])/s1['mid']*100
    log(f"  Mid change: {mid_chg:+.2f}%")
    log(f"  Time gap: {elapsed_h:.2f}h")

log(f"\n[X-4 SNAP #2 DONE]")

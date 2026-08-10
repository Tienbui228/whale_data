"""
_probe_koma_snap1_20260810.py — depth snap #1 for KOMAUSDT
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
SYM_PERP = "KOMAUSDT"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"KOMA DEPTH SNAP#1  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR: {e}"); return None

FAPI = "https://fapi.binance.com"
depth_data = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM_PERP}&limit=1000")
snap_time = datetime.now(timezone.utc)

if depth_data:
    bids = [(float(p), float(q)) for p,q in depth_data.get("bids",[])]
    asks = [(float(p), float(q)) for p,q in depth_data.get("asks",[])]
    bid_top = bids[0][0]; ask_top = asks[0][0]
    mid = (bid_top + ask_top) / 2
    spread = (ask_top - bid_top) / mid * 100
    bid2_full = sum(p*q for p,q in bids)
    ask2_full = sum(p*q for p,q in asks)
    ratio_full = bid2_full/ask2_full if ask2_full > 0 else None
    log(f"  Time:    {snap_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"  mid:     ${mid:.8f}")
    log(f"  bid_top: ${bid_top:.8f} ask_top: ${ask_top:.8f}")
    log(f"  spread:  {spread:.3f}%")
    log(f"  bid2(full): ${bid2_full:,.0f}")
    log(f"  ask2(full): ${ask2_full:,.0f}")
    log(f"  ratio:   {ratio_full:.4f}")
    log(f"\n  Depth buckets:")
    for pct_b in [0.01, 0.02, 0.05]:
        bb = sum(p*q for p,q in bids if p >= mid*(1-pct_b))
        ab = sum(p*q for p,q in asks if p <= mid*(1+pct_b))
        rb = bb/ab if ab > 0 else None
        rb_str = f"{rb:.3f}" if rb else "N/A"
        log(f"    +-{int(pct_b*100)}%: bid=${bb:,.0f} ask=${ab:,.0f} ratio={rb_str}")
    snap = {
        "symbol": SYM_PERP, "time": snap_time.isoformat(), "mid": mid,
        "bid_top": bid_top, "ask_top": ask_top, "spread_pct": spread,
        "bid2_full_usd": bid2_full, "ask2_full_usd": ask2_full, "ratio_full": ratio_full,
        "buckets": {
            "1pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.99), "ask": sum(p*q for p,q in asks if p<=mid*1.01)},
            "2pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.98), "ask": sum(p*q for p,q in asks if p<=mid*1.02)},
            "5pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.95), "ask": sum(p*q for p,q in asks if p<=mid*1.05)},
        }
    }
    (SCRATCH / f"koma_depth_snap1_{DATE_TAG}.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
    snap2_gate = datetime.fromtimestamp(snap_time.timestamp()+4*3600, tz=timezone.utc)
    log(f"\n  Saved: koma_depth_snap1_{DATE_TAG}.json")
    log(f"  SNAP #2 GATE: >='{snap2_gate.strftime('%Y-%m-%d %H:%M UTC')}'")
else:
    log("  FAILED")

log(f"\n[SNAP#1 DONE]")

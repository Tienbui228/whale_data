"""FF depth snap #2 — collected 2026-08-09 (gate ≥16:07 UTC 08-08 satisfied)"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
SYM = "FFUSDT"
NOW = datetime.now(timezone.utc)
print(f"FF SNAP #2  |  {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")

url = f"https://fapi.binance.com/fapi/v1/depth?symbol={SYM}&limit=1000"
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        raw = json.loads(r.read())
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

bids = [(float(p), float(q)) for p,q in raw.get("bids",[])]
asks = [(float(p), float(q)) for p,q in raw.get("asks",[])]

if not bids or not asks:
    print("Empty orderbook")
    sys.exit(1)

mid = (bids[0][0] + asks[0][0]) / 2
bid2 = sum(p*q for p,q in bids)
ask2 = sum(p*q for p,q in asks)
ratio = bid2/ask2 if ask2 > 0 else None
spread_pct = (asks[0][0] - bids[0][0]) / mid * 100

print(f"  mid:       ${mid:.6f}")
print(f"  bid_top:   ${bids[0][0]:.6f}")
print(f"  ask_top:   ${asks[0][0]:.6f}")
print(f"  spread:    {spread_pct:.3f}%")
print(f"  bid2(USD): ${bid2:,.0f}")
print(f"  ask2(USD): ${ask2:,.0f}")
print(f"  ratio:     {ratio:.4f}" if ratio else "  ratio: N/A")

# Depth buckets
for pct in [0.01, 0.02, 0.05]:
    bid_b = sum(p*q for p,q in bids if p >= mid*(1-pct))
    ask_b = sum(p*q for p,q in asks if p <= mid*(1+pct))
    r_b = bid_b/ask_b if ask_b > 0 else None
    print(f"  ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=${ask_b:,.0f} ratio={r_b:.3f}" if r_b else f"  ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=0")

# Load snap #1
snap1_file = SCRATCH / "ff_depth_snap1_20260808.json"
snap1 = json.loads(snap1_file.read_text(encoding="utf-8")) if snap1_file.exists() else {}

snap2 = {
    "snap": 2, "time": NOW.isoformat(),
    "symbol": SYM,
    "mid": mid, "bid_top": bids[0][0], "ask_top": asks[0][0],
    "spread_pct": spread_pct,
    "bid2_usd": bid2, "ask2_usd": ask2, "ratio": ratio,
    "bids_len": len(bids), "asks_len": len(asks)
}
out = SCRATCH / "ff_depth_snap2_20260808.json"
out.write_text(json.dumps(snap2, indent=2), encoding="utf-8")
print(f"\n  Saved: {out.name}")

# Delta vs snap1
if snap1:
    print(f"\n  === DELTA vs SNAP #1 ===")
    print(f"  Snap #1 time: {snap1.get('snap_time','?')}")
    print(f"  Snap #2 time: {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    mid1 = snap1.get("mid",0)
    bid1 = snap1.get("bid2pct_usd", snap1.get("bid2_usd",0))
    ask1 = snap1.get("ask2pct_usd", snap1.get("ask2_usd",0))
    r1 = snap1.get("depth_ratio", snap1.get("ratio",0))
    print(f"  mid:    ${mid1:.6f} → ${mid:.6f}  ({(mid/mid1-1)*100:+.2f}%)")
    print(f"  bid2:   ${bid1:,.0f} → ${bid2:,.0f}  ({(bid2/bid1-1)*100:+.1f}%)" if bid1 else "  bid2: N/A")
    print(f"  ask2:   ${ask1:,.0f} → ${ask2:,.0f}  ({(ask2/ask1-1)*100:+.1f}%)" if ask1 else "  ask2: N/A")
    print(f"  ratio:  {r1:.4f} → {ratio:.4f}  ({'bid↑' if ratio > r1 else 'bid↓'})")

print(f"\n[FF SNAP #2 DONE]")

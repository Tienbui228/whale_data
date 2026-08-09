import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
NOW_UTC = datetime.now(timezone.utc)
print(f"AGT SNAP #2  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M:%S UTC')}")
SYM = "AGTUSDT"
url = f"https://fapi.binance.com/fapi/v1/depth?symbol={SYM}&limit=1000"
with urllib.request.urlopen(url, timeout=15) as r:
    book = json.loads(r.read())
bids = [(float(p), float(q)) for p,q in book["bids"]]
asks = [(float(p), float(q)) for p,q in book["asks"]]
best_bid = bids[0][0]; best_ask = asks[0][0]; mid = (best_bid+best_ask)/2
bid2 = sum(p*q for p,q in bids if p >= mid*0.98)
ask2 = sum(p*q for p,q in asks if p <= mid*1.02)
ratio = bid2/ask2 if ask2 > 0 else None
snap = {"sym":SYM,"snap_time":NOW_UTC.isoformat(),"snap_label":"snap2","mid":mid,"bid2pct_usd":round(bid2,0),"ask2pct_usd":round(ask2,0),"depth_ratio":round(ratio,4) if ratio else None}
out = SCRATCH / "agt_depth_snap2_20260808.json"
out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
print(f"  mid={mid:.8f} bid2=${bid2:,.0f} ask2=${ask2:,.0f} ratio={ratio:.4f}" if ratio else "no ratio")
print(f"  Saved: {out.name}")

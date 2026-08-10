"""
_probe_gua_snap2_20260810.py
G-5 SNAP2: Depth compare vs snap1. Gate: ≥15:50 UTC.
data-source: fapi.binance.com/fapi/v1/depth
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
SYM = "GUAUSDT"; SYM_LOWER = "gua"
FAPI = "https://fapi.binance.com"
GATE_UTC = "15:50"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-5 SNAP2 GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

gate_h, gate_m = map(int, GATE_UTC.split(":"))
gate_ok = (NOW.hour > gate_h) or (NOW.hour == gate_h and NOW.minute >= gate_m)
if not gate_ok:
    log(f"  Gate NOT MET (need ≥{GATE_UTC} UTC, now {NOW.hour:02d}:{NOW.minute:02d} UTC)")
    log(f"  Exiting — re-run after {GATE_UTC} UTC")
    sys.exit(0)

log(f"  Gate OK ≥{GATE_UTC} UTC")

# Load snap1
snap1_path = SCRATCH / f"{SYM_LOWER}_depth_snap1_{DATE_TAG}.json"
with open(snap1_path, encoding="utf-8") as f:
    snap1 = json.load(f)
log(f"\n  Snap1: {snap1['snap_time']} | mid=${snap1['mid']:.7f} | ratio={snap1['ratio']:.4f} | {snap1['wall']}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM}&limit=500")
if not depth:
    log("  ERROR: depth fetch failed"); sys.exit(1)

bids = [(float(p), float(q)) for p, q in depth["bids"]]
asks = [(float(p), float(q)) for p, q in depth["asks"]]
mid = (bids[0][0] + asks[0][0]) / 2
bid_lo = mid * 0.98; ask_hi = mid * 1.02
bid_vol = sum(p*q for p, q in bids if p >= bid_lo)
ask_vol = sum(p*q for p, q in asks if p <= ask_hi)
ratio = bid_vol / ask_vol if ask_vol > 0 else None
wall = "BID-HEAVY" if (ratio and ratio > 1.1) else ("ASK-HEAVY" if (ratio and ratio < 0.9) else "BALANCED")

snap_time = NOW.strftime("%Y-%m-%d %H:%M UTC")
log(f"\n  Snap2: {snap_time}")
log(f"  mid:      ${mid:.7f}  (was ${snap1['mid']:.7f}, Δ={((mid-snap1['mid'])/snap1['mid']*100):+.2f}%)")
log(f"  bid±2%:   ${bid_vol:,.0f}  (was ${snap1['bid_vol']:,.0f})")
log(f"  ask±2%:   ${ask_vol:,.0f}  (was ${snap1['ask_vol']:,.0f})")
log(f"  ratio:    {ratio:.4f}  (was {snap1['ratio']:.4f})")
log(f"  wall:     {wall}  (was {snap1['wall']})")
log(f"  FLIP: {'YES !' if wall != snap1['wall'] else 'no'}")

snap2 = {
    "symbol": SYM, "snap": 2, "date": DATE_TAG,
    "snap_time": snap_time,
    "mid": mid, "bid_vol": bid_vol, "ask_vol": ask_vol,
    "ratio": ratio, "wall": wall,
    "snap1_mid": snap1["mid"], "snap1_ratio": snap1["ratio"],
    "mid_delta_pct": round((mid - snap1["mid"]) / snap1["mid"] * 100, 4) if snap1["mid"] else None,
    "ratio_delta": round(ratio - snap1["ratio"], 4) if (ratio and snap1["ratio"]) else None,
    "flip": (wall != snap1["wall"]),
}
out = SCRATCH / f"{SYM_LOWER}_depth_snap2_{DATE_TAG}.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(snap2, f, indent=2)
log(f"\n  Saved: {out.name}")
log(f"\n[G-5 SNAP2 DONE]")

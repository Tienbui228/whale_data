#!/usr/bin/env python3
"""[GATE-ANOMALY] GUA isolated-market check — READ-ONLY paste raw."""
import sys, io, json, urllib.request
from datetime import datetime, timezone

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode())

DIV = "═" * 78

# ─── [1] currencies flags
print(f"{DIV}\n[1] Gate /api/v4/spot/currencies/GUA — deposit/withdraw/trade flags\n{DIV}")
cur = get("https://api.gateio.ws/api/v4/spot/currencies/GUA")
for k in ["currency","name","delisted","withdraw_disabled","withdraw_delayed",
          "deposit_disabled","trade_disabled","fixed_rate","chain"]:
    print(f"  {k:>20}: {cur.get(k)!r}")
print(f"\n  chains[]:")
for c in cur.get("chains", []):
    print(f"    name={c.get('name')!r} withdraw_disabled={c.get('withdraw_disabled')!r} "
          f"deposit_disabled={c.get('deposit_disabled')!r} "
          f"disabled={c.get('disabled')!r} "
          f"addr={c.get('addr','')[:12]}...")

# pair flags
print(f"\n  pair /api/v4/spot/currency_pairs/GUA_USDT:")
pair = get("https://api.gateio.ws/api/v4/spot/currency_pairs/GUA_USDT")
for k in ["id","base","quote","trade_status","sell_start","buy_start",
          "min_base_amount","min_quote_amount","fee"]:
    print(f"    {k:>18}: {pair.get(k)!r}")

# ─── [2] orderbook depth ±2%
print(f"\n{DIV}\n[2] Orderbook GUA_USDT — depth ±2% around mid\n{DIV}")
ob = get("https://api.gateio.ws/api/v4/spot/order_book?currency_pair=GUA_USDT&limit=100")
bids = [(float(p), float(q)) for p, q in ob.get("bids", [])]
asks = [(float(p), float(q)) for p, q in ob.get("asks", [])]
if bids and asks:
    best_bid = bids[0][0]; best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2
    spread = (best_ask - best_bid) / mid * 100
    print(f"  best_bid={best_bid:.6f}  best_ask={best_ask:.6f}  mid={mid:.6f}  spread={spread:.3f}%")
    print(f"  raw bid[0..5]:")
    for p, q in bids[:5]:
        print(f"    px={p:.6f}  qty={q:.2f}  notional=${p*q:,.2f}")
    print(f"  raw ask[0..5]:")
    for p, q in asks[:5]:
        print(f"    px={p:.6f}  qty={q:.2f}  notional=${p*q:,.2f}")
    lo = mid * 0.98; hi = mid * 1.02
    bid_depth_usd = sum(p*q for p, q in bids if p >= lo)
    ask_depth_usd = sum(p*q for p, q in asks if p <= hi)
    bid_n_levels  = sum(1 for p, _ in bids if p >= lo)
    ask_n_levels  = sum(1 for p, _ in asks if p <= hi)
    print(f"\n  ±2% window: [{lo:.6f}, {hi:.6f}]")
    print(f"    bid side depth (≥{lo:.6f}): {bid_n_levels} levels · ${bid_depth_usd:,.2f}")
    print(f"    ask side depth (≤{hi:.6f}): {ask_n_levels} levels · ${ask_depth_usd:,.2f}")
    print(f"    total ±2% depth: ${bid_depth_usd + ask_depth_usd:,.2f}")
else:
    print("  EMPTY orderbook (no bids/asks)")

# ─── [3] recent 20 trades
print(f"\n{DIV}\n[3] Recent 20 trades GUA_USDT — sanity\n{DIV}")
trs = get("https://api.gateio.ws/api/v4/spot/trades?currency_pair=GUA_USDT&limit=20")
print(f"  n_trades: {len(trs)}")
if trs:
    ts0 = int(float(trs[0].get("create_time")))
    tsN = int(float(trs[-1].get("create_time")))
    dt0 = datetime.fromtimestamp(ts0, tz=timezone.utc).isoformat()
    dtN = datetime.fromtimestamp(tsN, tz=timezone.utc).isoformat()
    print(f"  first (newest): {dt0}")
    print(f"  last  (oldest): {dtN}")
    span_s = ts0 - tsN
    print(f"  time span: {span_s}s ≈ {span_s/60:.1f} min · {span_s/3600:.1f}h · {span_s/86400:.1f}d")
    print(f"\n  raw:")
    print(f"  {'idx':>3}  {'time_utc':>19}  {'side':>4}  {'px':>10}  {'qty':>12}  {'notional':>10}")
    for i, t in enumerate(trs):
        ts = int(float(t.get("create_time")))
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        side = t.get("side", "?")
        px = float(t.get("price", 0))
        qty = float(t.get("amount", 0))
        print(f"  {i:>3}  {dt:>19}  {side:>4}  {px:>10.6f}  {qty:>12.2f}  ${px*qty:>8.2f}")
    total_usd = sum(float(t["price"]) * float(t["amount"]) for t in trs)
    print(f"\n  Σ notional 20 trades: ${total_usd:,.2f}")

print(f"\n{DIV}\nDONE. Verdict paste kèm interpret.\n{DIV}")

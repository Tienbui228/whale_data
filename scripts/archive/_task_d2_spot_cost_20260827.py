"""(D2) SPOT-COLLECTOR COST · fw-139 vs Binance spot listing · trình số only."""
from __future__ import annotations
import sys, io, json, urllib.request
from pathlib import Path

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
from gom_h_daily import _load_universe

symbols = _load_universe()  # e.g. ["ABCUSDT", ...]

# Fetch spot exchangeInfo
try:
    req = urllib.request.Request("https://api.binance.com/api/v3/exchangeInfo",
                                 headers={"User-Agent": "spot-cost/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        info = json.loads(resp.read().decode())
    spot_symbols = {s["symbol"] for s in info.get("symbols", []) if s.get("status") == "TRADING"}
except Exception as e:
    print(f"[FAIL] spot exchangeInfo fetch: {e}")
    sys.exit(1)

print("═" * 100)
print("[D2 SPOT-COLLECTOR COST · fw-139 vs Binance spot listing]")
print("═" * 100)
print(f"fw-139 universe: {len(symbols)} symbols")
print(f"Binance spot TRADING symbols: {len(spot_symbols)}")
print()

on_spot = [s for s in symbols if s in spot_symbols]
off_spot = [s for s in symbols if s not in spot_symbols]

print(f"fw-139 CÓ Binance spot listing: {len(on_spot)}")
print(f"fw-139 KHÔNG có Binance spot listing: {len(off_spot)} (scope-note)")
print()
print("[COST TRỌN GÓI]")
print(f"  Endpoint: GET /api/v3/klines?symbol=<S>&interval=1d&limit=<L>")
print(f"  Native taker fields: k[9]=taker_buy_base_asset_vol · k[10]=taker_buy_quote_asset_vol")
print(f"  Doctrine compliance: spot-collect 19/08 (native field, KHÔNG forward-poll)")
print()
print(f"  Daily poll: {len(on_spot)} call/day (1 call per token · limit 500 candles)")
print(f"  Backfill 60d one-time: {len(on_spot)} call (limit 1000 candles đủ)")
print(f"  Rate limit Binance spot: 1200 req/min (weight 1 mỗi call)")
print(f"  {len(on_spot)} call << 1200/min trần → trong-trần rộng rãi")
print()
print(f"[Off-spot list ({len(off_spot)} tokens) — scope-note cho operator]")
for i, s in enumerate(off_spot):
    print(f"  {s}", end="  " if (i+1) % 6 else "\n")
if off_spot and len(off_spot) % 6: print()
print()
print(f"[VERDICT]")
if len(on_spot) < 200:
    print(f"  {len(on_spot)} daily call · << 1200/min trần ops → TRONG TRẦN, không cần scope-cut")
    print(f"  (backfill 60d one-time = {len(on_spot)} call bulk, cùng scope · complete <1 min)")
else:
    print(f"  {len(on_spot)} daily call · sát trần → cần scope-cut hoặc rate-limit gate")
print(f"  Quyết định scope: chờ operator ký (đây chỉ trình số).")

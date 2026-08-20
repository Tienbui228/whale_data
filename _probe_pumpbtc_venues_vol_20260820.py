"""_probe_pumpbtc_venues_vol_20260820.py — fetch 24h vol từ ALL 3 spot venues confirmed.
Gate + MEXC + Bitget → so vol lớn nhất.
"""
import sys, io, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def fetch_json(url, params=None, timeout=15):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

SYM = "PUMPBTC"

results = {}

# Gate
print("=== Gate ===")
d = fetch_json("https://api.gateio.ws/api/v4/spot/tickers", {"currency_pair": f"{SYM}_USDT"})
time.sleep(0.3)
if isinstance(d, list) and d:
    r = d[0]
    vol_usd = float(r.get("quote_volume") or 0)
    base_vol = float(r.get("base_volume") or 0)
    last = float(r.get("last") or 0)
    results["gate"] = {"vol_usd": vol_usd, "base_vol": base_vol, "last": last, "raw": r}
    print(f"  last={last}  base_vol={base_vol}  quote_volume(USD)={vol_usd:,.2f}")
    print(f"  raw keys: {list(r.keys())}")

# MEXC
print("\n=== MEXC ===")
d = fetch_json("https://api.mexc.com/api/v3/ticker/24hr", {"symbol": f"{SYM}USDT"})
time.sleep(0.3)
if isinstance(d, dict) and "quoteVolume" in d:
    vol_usd = float(d.get("quoteVolume") or 0)
    base_vol = float(d.get("volume") or 0)
    last = float(d.get("lastPrice") or 0)
    results["mexc"] = {"vol_usd": vol_usd, "base_vol": base_vol, "last": last, "raw": d}
    print(f"  last={last}  volume(base)={base_vol}  quoteVolume(USD)={vol_usd:,.2f}")

# Bitget — 3 endpoints try
print("\n=== Bitget ===")
d = fetch_json("https://api.bitget.com/api/v2/spot/market/tickers", {"symbol": f"{SYM}USDT"})
time.sleep(0.3)
if isinstance(d, dict) and str(d.get("code")) == "00000":
    lst = d.get("data", [])
    if lst:
        r = lst[0]
        # try different field names
        vol_usd_candidates = {
            "usdtVolume": r.get("usdtVolume"),
            "quoteVolume": r.get("quoteVolume"),
            "usdtVol": r.get("usdtVol"),
        }
        # Bitget v2 ticker: usdtVolume is quote vol
        vol_usd = float(r.get("usdtVolume") or r.get("quoteVolume") or 0)
        base_vol = float(r.get("baseVolume") or 0)
        last = float(r.get("lastPr") or r.get("close") or 0)
        results["bitget"] = {"vol_usd": vol_usd, "base_vol": base_vol, "last": last, "raw": r}
        print(f"  last={last}  baseVolume={base_vol}  usdtVolume(USD)={vol_usd:,.2f}")
        print(f"  vol_usd candidates: {vol_usd_candidates}")
        print(f"  raw keys: {list(r.keys())}")
else:
    print(f"  err: {d}")

# COMPARE
print("\n" + "="*60)
print("VOL COMPARISON (24h USD)")
print("="*60)
ranked = sorted(results.items(), key=lambda x: x[1]["vol_usd"], reverse=True)
for v_name, v_data in ranked:
    print(f"  {v_name:<10}: ${v_data['vol_usd']:>14,.2f}  · last=${v_data['last']}")

if ranked:
    winner = ranked[0][0]
    print(f"\n  → VENUE LỚN NHẤT (24h): **{winner}** with ${ranked[0][1]['vol_usd']:,.2f}")

# Price-band check
print("\n" + "="*60)
print("PRICE-BAND CHECK vs perp (±20% tolerance)")
print("="*60)
# perp last price from fapi ticker
d = fetch_json("https://fapi.binance.com/fapi/v1/ticker/price", {"symbol": f"{SYM}USDT"})
time.sleep(0.3)
if isinstance(d, dict) and d.get("price"):
    perp_last = float(d["price"])
    print(f"  perp last: ${perp_last}")
    for v_name, v_data in ranked:
        dev = abs(v_data["last"] - perp_last) / perp_last * 100
        verdict = "✓ PASS" if dev < 20 else "❌ FAIL (dừng cột, báo)"
        print(f"  {v_name:<10}: ${v_data['last']}  dev={dev:.2f}%  {verdict}")

print("\n[DONE]")

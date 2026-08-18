"""_probe_taker_alpha_20260818.py — VPS read-only probe.
[1] Verify spot CEX pair for GUA on Binance
[2] Mổ payload Alpha klines schema — field-by-field
[3/4] Depend on [2]: propose taker extraction OR L-48 amendment
"""
import sys, json, urllib.request, time
from datetime import datetime, timezone

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

def hr(label):
    print("\n" + "="*70 + f"\n{label}\n" + "="*70)

# ═══════════════════════════════════════════════════════════════════════
# [1] VERIFY spot CEX pair for GUA
# ═══════════════════════════════════════════════════════════════════════
hr("[1] Binance SPOT exchangeInfo — check GUA / SUPERFORTUNE presence")

info = fetch_json("https://api.binance.com/api/v3/exchangeInfo")
if "_error" in info:
    print(f"  ERROR: {info['_error']}")
    sys.exit(1)

symbols = info.get("symbols", [])
print(f"  Total spot symbols on Binance: {len(symbols)}")

# search for GUA / SUPERFORTUNE and variants
patterns = ["GUA", "SUPERFORTUNE"]
matches = []
for s in symbols:
    sym  = s.get("symbol", "")
    base = s.get("baseAsset", "")
    quot = s.get("quoteAsset", "")
    for p in patterns:
        if p in sym or p in base:
            matches.append({
                "symbol": sym, "base": base, "quote": quot,
                "status": s.get("status"), "isSpot": s.get("isSpotTradingAllowed"),
            })
            break

if matches:
    print(f"  MATCHES ({len(matches)}):")
    for m in matches:
        print(f"    {m}")
else:
    print("  → NO SPOT PAIR containing 'GUA' or 'SUPERFORTUNE' on Binance spot")

# Also check exact 'GUA' base asset (in case another token named GUA exists)
gua_exact = [s for s in symbols if s.get("baseAsset") == "GUA"]
print(f"\n  Exact base='GUA' matches: {len(gua_exact)}")
for s in gua_exact:
    print(f"    {s.get('symbol')} · base={s.get('baseAsset')} · quote={s.get('quoteAsset')} · status={s.get('status')}")

# Verdict
if not matches and not gua_exact:
    print("\n  VERDICT [1]: GUA (SUPERFORTUNE) does NOT have CEX spot pair on Binance.")
    print("               Alpha-only listing. taker_spot_pct = N/A-STRUCTURAL (not data-gap).")
elif gua_exact:
    print(f"\n  VERDICT [1]: GUA base found on spot: {[s.get('symbol') for s in gua_exact]}")
    print("               If different project — noise. If same → taker_spot AVAILABLE.")

time.sleep(0.5)

# ═══════════════════════════════════════════════════════════════════════
# [2] MỔ Alpha klines payload — field-by-field
# ═══════════════════════════════════════════════════════════════════════
hr("[2] Alpha klines payload — schema forensic (GUA=ALPHA_483)")

alpha_id = "ALPHA_483"
ticker   = f"{alpha_id}USDT"

# Fetch 3 days (Aug15-Aug17)
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines",
               {"symbol": ticker, "interval": "1d", "limit": 3})
time.sleep(0.5)

if isinstance(d, dict) and "_error" in d:
    print(f"  ERROR: {d['_error']}")
    sys.exit(2)

data = d.get("data") if isinstance(d, dict) else d
if not data:
    print(f"  No data. Full response keys: {d.keys() if isinstance(d, dict) else type(d)}")
    print(f"  Response: {json.dumps(d)[:500]}")
    sys.exit(2)

print(f"\n  Response type: {type(data).__name__}, length: {len(data)}")

# [2a] Paste raw + count fields for element[0]
print(f"\n  [2a] RAW element[0]:")
print(f"    {json.dumps(data[0])}")
print(f"    fields count: {len(data[0])}")

print(f"\n  [2a-2] RAW element[1]:")
print(f"    {json.dumps(data[1])}")
print(f"    fields count: {len(data[1])}")

print(f"\n  [2a-3] RAW element[2]:")
print(f"    {json.dumps(data[2])}")
print(f"    fields count: {len(data[2])}")

# [2b] Infer labels from VALUES (not position)
print(f"\n  [2b] Field-by-field VALUE-based label inference (element[0]):")
k0 = data[0]
for i, v in enumerate(k0):
    try:
        f = float(v)
    except:
        f = None
    hint = ""
    if isinstance(v, str) and len(v) == 13 and v.isdigit():
        try:
            dt = datetime.fromtimestamp(int(v)/1000, tz=timezone.utc)
            hint = f"→ TIMESTAMP MS {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        except: pass
    elif f is not None:
        if 0.001 < f < 1000:      hint = "→ likely PRICE"
        elif 1e3 < f < 1e10:      hint = "→ likely VOLUME (base or quote)"
        elif f == int(f) and f < 1e6: hint = "→ likely COUNT/INT"
        elif f == 0:              hint = "→ ZERO"
    print(f"    k[{i}] = {v!r}  ({type(v).__name__})  {hint}")

# [2c] Look for taker-buy-like fields
print(f"\n  [2c] Taker-buy field detection via CROSS-VALUE math:")
# In api/v3 klines: k[7]=quote_asset_vol, k[9]=taker_buy_base, k[10]=taker_buy_quote, k[11]=ignore
# But Alpha may differ. Try to find pair where value1 <= value2 (taker <= total) and ratio in [0,1].

candidate_vols = {}
for i, v in enumerate(k0):
    try:
        f = float(v)
        if f > 1000:  # likely volume
            candidate_vols[i] = f
    except:
        pass
print(f"    Volume-like fields (>1000): {candidate_vols}")

# Check for pairs where one is smaller (potential taker-buy fraction)
if len(candidate_vols) >= 2:
    idxs = sorted(candidate_vols.keys())
    print(f"    Pair analysis (taker/total ratio candidates):")
    for i, ia in enumerate(idxs):
        for ib in idxs[i+1:]:
            va, vb = candidate_vols[ia], candidate_vols[ib]
            if va == vb:
                print(f"    k[{ia}]={va:.2f} == k[{ib}]={vb:.2f}  ← EQUAL (broken field like L-48 rule)")
            else:
                small, big = min(va, vb), max(va, vb)
                ratio = small/big
                if 0.1 < ratio < 1.0:
                    print(f"    k[{ia}]={va:.2f} vs k[{ib}]={vb:.2f}  ratio={ratio:.4f} → possible taker/total")
                elif ratio < 0.001:
                    print(f"    k[{ia}]={va:.2f} vs k[{ib}]={vb:.2f}  ratio={ratio:.6f} → different-unit (base vs quote)")

# Standard positions probe (like api/v3):
print(f"\n  [2c-2] Standard spot-klines positions check for element[0]:")
print(f"    if standard schema: k[7]=quote_vol · k[10]=taker_buy_quote_vol")
if len(k0) >= 11:
    q  = k0[7]; tq = k0[10]; tb = k0[9]; bv = k0[5]
    print(f"    k[5]  (base_vol maybe)         = {bv}")
    print(f"    k[7]  (quote_vol maybe)        = {q}")
    print(f"    k[9]  (taker_buy_base maybe)   = {tb}")
    print(f"    k[10] (taker_buy_quote maybe)  = {tq}")
    try:
        fq  = float(q); ftq = float(tq); ftb = float(tb); fbv = float(bv)
        # equal-field check (L-48 rule)
        eq_5_9   = fbv == ftb
        eq_7_10  = fq  == ftq
        eq_9_5   = ftb == fbv
        print(f"    L-48 broken-field check: k[9]==k[5]={eq_5_9} · k[10]==k[7]={eq_7_10}")
        if not eq_7_10 and fq > 0:
            taker_pct = ftq / fq * 100
            print(f"    IF valid: taker_alpha% = k[10]/k[7]*100 = {taker_pct:.4f}%  ← would need scale check")
        else:
            print(f"    → k[10] mirrors k[7] (or invalid) — TAKER FIELD BROKEN in Alpha payload")
    except Exception as e:
        print(f"    parse err: {e}")

# [2c-3] SANITY: verify quote_vol matches expected $234K/$107K
print(f"\n  [2c-3] SANITY total_quote_vol vs known Aug15/16 vols:")
for k in data:
    ts = int(k[0]) if k else 0
    dstr = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    if len(k) >= 8:
        print(f"    {dstr}: k[7]={k[7]}  (expected: Aug15≈$234K, Aug16≈$107K)")

# ═══════════════════════════════════════════════════════════════════════
# [2d] alternate endpoints: aggTrades / trades
# ═══════════════════════════════════════════════════════════════════════
hr("[2d] Alpha alternate endpoints — aggTrades / trades probe")

alt_endpoints = [
    "https://www.binance.com/bapi/defi/v1/public/alpha-trade/aggTrades",
    "https://www.binance.com/bapi/defi/v1/public/alpha-trade/trades",
    "https://www.binance.com/bapi/defi/v1/public/alpha-trade/historicalTrades",
]
for ep in alt_endpoints:
    print(f"\n  Trying: {ep}")
    d = fetch_json(ep, {"symbol": ticker, "limit": 3})
    time.sleep(0.3)
    if isinstance(d, dict) and "_error" in d:
        print(f"    ERROR: {d['_error']}")
        continue
    if isinstance(d, dict) and d.get("code") not in (None, "000000", 0):
        print(f"    API code={d.get('code')} msg={d.get('message','')[:200]}")
        continue
    payload = d.get("data") if isinstance(d, dict) else d
    if payload:
        print(f"    SUCCESS ({len(payload)} rows). Schema of first row:")
        print(f"      {json.dumps(payload[0])}")
        # Check for isBuyerMaker flag
        if isinstance(payload[0], dict):
            has_bm = "isBuyerMaker" in payload[0] or "m" in payload[0]
            print(f"      isBuyerMaker/m flag present: {has_bm}")
    else:
        print(f"    empty payload. keys={d.keys() if isinstance(d, dict) else 'N/A'}")

# Try fapi trade endpoints as reference
print(f"\n  Reference: does GUAUSDT PERP trades endpoint exist?")
d = fetch_json("https://fapi.binance.com/fapi/v1/aggTrades",
               {"symbol": "GUAUSDT", "limit": 3})
time.sleep(0.3)
if isinstance(d, list) and d:
    print(f"    fapi GUAUSDT aggTrades: {len(d)} rows returned. Schema:")
    print(f"      {json.dumps(d[0])}")
    print(f"      → PERP has aggTrades with isBuyerMaker='m' flag. Not applicable to spot Alpha.")

print("\n[DONE PROBE - see verdict + proposal or L-48 draft above/below]")

"""
_probe_apr_p0_venue_20260811.py
P-0: APR venue/spot/chain investigation.
data-source: Binance api/v3, fapi, bapi, CoinGecko, Gate.io, Bybit, OKX, GeckoTerminal
machine: local scratch
date-range: 2026-08-13 (spot check)
code-commit: TBD
"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

def log(s=""): print(s, flush=True)

SESS = requests.Session()
SESS.headers.update({"User-Agent": "Mozilla/5.0"})

def get(url, params=None, timeout=15):
    try:
        r = SESS.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e)}

# ── P-0a: Binance SPOT exchangeInfo ──────────────────────────────────────────
log("=== P-0a: Binance SPOT (api.binance.com) ===")
spot_info = get("https://api.binance.com/api/v3/exchangeInfo")
if "_error" in spot_info:
    log(f"  ERROR: {spot_info['_error']}")
else:
    apr_pairs = [s for s in spot_info.get("symbols", [])
                 if "APR" in s.get("symbol", "")]
    log(f"  APR* pairs found: {len(apr_pairs)}")
    for p in apr_pairs:
        log(f"    {p['symbol']} status={p.get('status')} quoteAsset={p.get('quoteAsset')}")
    if not apr_pairs:
        log("  → NO APR spot pair on Binance")

# ── P-0b: Binance PERP info ───────────────────────────────────────────────────
log("\n=== P-0b: Binance PERP fapi (existing perp check) ===")
perp = get("https://fapi.binance.com/fapi/v1/exchangeInfo")
if "_error" in perp:
    log(f"  ERROR: {perp['_error']}")
else:
    apr_perp = [s for s in perp.get("symbols", [])
                if "APR" in s.get("symbol", "")]
    for p in apr_perp:
        log(f"  {p['symbol']} status={p.get('status')} underlyingType={p.get('underlyingType')}")
        log(f"    underlyingSubType={p.get('underlyingSubType')} onboardDate={p.get('onboardDate')}")
        log(f"    settlePrecision={p.get('settlePrecision')} contractType={p.get('contractType')}")

# ── P-0c: CoinGecko — identify APR / aPriori chain ───────────────────────────
log("\n=== P-0c: CoinGecko (chain ID + contract) ===")
# Search by ticker
cg_search = get("https://api.coingecko.com/api/v3/search", {"query": "aPriori"})
if "_error" in cg_search:
    log(f"  CoinGecko search error: {cg_search['_error']}")
else:
    coins = cg_search.get("coins", [])[:5]
    log(f"  Top CoinGecko results for 'aPriori':")
    for c in coins:
        log(f"    id={c.get('id')} symbol={c.get('symbol')} name={c.get('name')}")

# Try direct coin lookup
for cg_id in ["apriori", "apr", "apriori-apr"]:
    cg_coin = get(f"https://api.coingecko.com/api/v3/coins/{cg_id}")
    if "_error" not in cg_coin and "id" in cg_coin:
        log(f"\n  CoinGecko id={cg_id}: name={cg_coin.get('name')}")
        log(f"    symbol={cg_coin.get('symbol')}")
        platforms = cg_coin.get("detail_platforms", cg_coin.get("platforms", {}))
        log(f"    platforms: {json.dumps(platforms, indent=4)}")
        mc = cg_coin.get("market_data", {})
        log(f"    market_cap_rank={cg_coin.get('market_cap_rank')}")
        break
    time.sleep(0.5)

# ── P-0d: Gate.io spot ───────────────────────────────────────────────────────
log("\n=== P-0d: Gate.io SPOT ===")
gate = get("https://api.gateio.ws/api/v4/spot/currency_pairs")
if "_error" in gate:
    log(f"  ERROR: {gate['_error']}")
else:
    apr_gate = [p for p in gate if "APR" in p.get("id", "").upper()]
    log(f"  APR pairs on Gate: {len(apr_gate)}")
    for p in apr_gate[:5]:
        log(f"    {p.get('id')} base={p.get('base')} quote={p.get('quote')} trade_status={p.get('trade_status')}")

# ── P-0e: Bybit spot ─────────────────────────────────────────────────────────
log("\n=== P-0e: Bybit SPOT ===")
bybit = get("https://api.bybit.com/v5/market/instruments-info",
            {"category": "spot", "baseCoin": "APR"})
if "_error" in bybit:
    log(f"  ERROR: {bybit['_error']}")
else:
    items = bybit.get("result", {}).get("list", [])
    log(f"  APR spot on Bybit: {len(items)}")
    for it in items:
        log(f"    symbol={it.get('symbol')} status={it.get('status')}")

# ── P-0f: OKX spot ───────────────────────────────────────────────────────────
log("\n=== P-0f: OKX SPOT ===")
okx = get("https://www.okx.com/api/v5/public/instruments",
          {"instType": "SPOT", "instId": "APR-USDT"})
if "_error" in okx:
    log(f"  ERROR: {okx['_error']}")
else:
    data = okx.get("data", [])
    log(f"  APR-USDT on OKX: found={len(data)}")
    for d in data:
        log(f"    instId={d.get('instId')} state={d.get('state')}")
# Also check APR-USDC
okx2 = get("https://www.okx.com/api/v5/public/instruments",
           {"instType": "SPOT", "instId": "APR-USDC"})
if "_error" not in okx2:
    data2 = okx2.get("data", [])
    for d in data2:
        log(f"    instId={d.get('instId')} state={d.get('state')}")

# ── P-0g: GeckoTerminal DEX pools ────────────────────────────────────────────
log("\n=== P-0g: GeckoTerminal DEX (APR pools) ===")
gt = get("https://api.geckoterminal.com/api/v2/search/pools",
         {"query": "APR", "page": 1},
         timeout=20)
if "_error" in gt:
    log(f"  ERROR: {gt['_error']}")
else:
    pools = gt.get("data", [])
    log(f"  DEX pools matching APR: {len(pools)}")
    for p in pools[:5]:
        attrs = p.get("attributes", {})
        rels = p.get("relationships", {})
        net = rels.get("network", {}).get("data", {}).get("id", "?")
        dex = rels.get("dex", {}).get("data", {}).get("id", "?")
        log(f"    name={attrs.get('name')} network={net} dex={dex}")
        log(f"      liq=${attrs.get('reserve_in_usd','?')} vol24h=${attrs.get('volume_usd',{}).get('h24','?')}")
        log(f"      addr={attrs.get('address','?')[:20]}...")
        ba = attrs.get("base_token_price_usd", "?")
        log(f"      base_price=${ba}")

# ── P-0h: Binance bapi alpha token list (re-check) ───────────────────────────
log("\n=== P-0h: Binance bapi alpha token list re-check ===")
bapi = get("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list",
           timeout=20)
if "_error" in bapi:
    log(f"  ERROR: {bapi['_error']}")
else:
    tokens = bapi.get("data", {}).get("content", []) if isinstance(bapi.get("data"), dict) else bapi.get("data", [])
    if isinstance(tokens, list):
        apr_tokens = [t for t in tokens if "APR" in str(t.get("symbol","")).upper()]
        log(f"  APR tokens in bapi alpha: {len(apr_tokens)}")
        for t in apr_tokens:
            log(f"    symbol={t.get('symbol')} name={t.get('name')} chain={t.get('chain','?')} contract={t.get('contract','?')}")
    else:
        log(f"  Unexpected data type: {type(tokens)}")

# Save result summary
result = {
    "date": "2026-08-13",
    "notes": "P-0 venue/spot/chain investigation for APR (aPriori)"
}
out_path = SCRATCH / "apr_p0_venue_20260811.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
log(f"\n[P-0 DONE] Output: {out_path.name}")

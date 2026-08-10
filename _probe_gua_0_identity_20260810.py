"""
_probe_gua_0_identity_20260810.py
G-0: Định danh GUAUSDT — grep exchangeInfo biến thể, metadata, contract verify BAPI.
data-source: fapi.binance.com + bapi alpha token list
machine: local scratch D:\Data back test\whale_data\scratch
date: 2026-08-10
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "GUAUSDT"
SYM_LOWER = "gua"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-0 IDENTITY GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  data-source: fapi.binance.com/exchangeInfo + bapi alpha token list (public)")
log(f"  machine: local scratch {SCRATCH}")
log(f"  date: {NOW.strftime('%Y-%m-%d')} UTC")

def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# ── 1. Grep exchangeInfo for GUA variants ────────────────────────────────────
log("\n=== 1. FAPI exchangeInfo — grep GUA variants ===")
ei = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
if not ei:
    log("  exchangeInfo fetch failed"); ei = {"symbols": []}

all_syms = ei.get("symbols", [])
log(f"  Total perp symbols: {len(all_syms)}")

# Search variants
variants_found = []
SEARCH_TERMS = ["GUA", "GUARD", "IGU", "AGUA"]
for s in all_syms:
    sym = s.get("symbol", "")
    base = s.get("baseAsset", "")
    for term in SEARCH_TERMS:
        if term in sym.upper() or term in base.upper():
            variants_found.append({
                "symbol": sym, "baseAsset": base, "quoteAsset": s.get("quoteAsset"),
                "status": s.get("status"), "contractType": s.get("contractType"),
                "onboardDate": s.get("onboardDate"),
                "underlyingSubType": s.get("underlyingSubType", []),
            })
            break

log(f"\n  Variants found ({len(variants_found)}):")
for v in variants_found:
    ob = datetime.fromtimestamp(v["onboardDate"]/1000, tz=timezone.utc).strftime("%Y-%m-%d") if v.get("onboardDate") else "N/A"
    log(f"    {v['symbol']:<20} base={v['baseAsset']:<8} status={v['status']:<10} type={v['underlyingSubType']} onboard={ob}")

# Lock GUAUSDT
target = next((s for s in all_syms if s.get("symbol") == SYM), None)
if target:
    ob = datetime.fromtimestamp(target["onboardDate"]/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if target.get("onboardDate") else "N/A"
    log(f"\n  LOCKED: {SYM}")
    log(f"    baseAsset:  {target.get('baseAsset')}")
    log(f"    quoteAsset: {target.get('quoteAsset')}")
    log(f"    status:     {target.get('status')}")
    log(f"    contractType: {target.get('contractType')}")
    log(f"    onboardDate: {ob}")
    log(f"    underlyingSubType: {target.get('underlyingSubType')}")
    log(f"    pricePrecision: {target.get('pricePrecision')}")
    log(f"    quantityPrecision: {target.get('quantityPrecision')}")
    START_MS = target.get("onboardDate", 0)
else:
    log(f"\n  ERROR: {SYM} not found in exchangeInfo")
    START_MS = 0

# ── 2. Alpha ID map lookup ─────────────────────────────────────────────────────
log("\n=== 2. Alpha ID map ===")
alpha_map = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_id = None
if alpha_map.exists():
    try:
        with open(alpha_map, encoding="utf-8-sig", errors="replace") as f:
            amap = json.load(f)
        base = target.get("baseAsset", "GUA") if target else "GUA"
        alpha_id = amap.get(base)
        log(f"  Alpha ID for {base}: {alpha_id or 'NOT FOUND'}")
        # Also check variants
        for k, v in amap.items():
            if "GUA" in k.upper():
                log(f"  Map entry: {k} → {v}")
    except Exception as e:
        log(f"  alpha_id_map error: {e}")

# ── 3. BAPI alpha token list — contract + supply ───────────────────────────────
log("\n=== 3. BAPI alpha token list — contract + supply ===")
ALPHA_LIST_URL = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
token_list = fetch_json(ALPHA_LIST_URL)
contract_addr = None; token_meta = {}

if token_list:
    items = token_list.get("data", [])
    log(f"  Alpha token list: {len(items)} tokens")
    base_asset = target.get("baseAsset", "GUA") if target else "GUA"
    for item in items:
        sym_item = (item.get("symbol") or item.get("tokenSymbol") or "").upper()
        aid = str(item.get("alphaId") or item.get("id") or "")
        name = item.get("name", "")
        if sym_item == base_asset.upper() or (alpha_id and f"ALPHA_{aid}" == alpha_id):
            contract_addr = (item.get("contractAddress") or item.get("address") or
                             item.get("tokenAddress") or "")
            token_meta = item
            log(f"  MATCH: sym={sym_item} id={aid} name={name}")
            log(f"    contract: {contract_addr}")
            log(f"    chainId:  {item.get('chainId')}")
            log(f"    totalSupply: {item.get('totalSupply') or item.get('total_supply') or 'N/A'}")
            log(f"    Full: {json.dumps(item, ensure_ascii=False)[:600]}")
            break
    if not contract_addr:
        log(f"  {base_asset} NOT FOUND in alpha token list")
        # Fuzzy: look for anything containing GUA
        for item in items:
            s2 = (item.get("symbol") or "").upper()
            n2 = (item.get("name") or "").upper()
            if "GUA" in s2 or "GUA" in n2:
                log(f"  Fuzzy match: sym={s2} name={n2} id={item.get('alphaId')} contract={item.get('contractAddress','')}")

# ── 4. FreshWatch presence ─────────────────────────────────────────────────────
log("\n=== 4. FreshWatch daily CSVs ===")
import csv
fw_hits = []
for fw in sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv")):
    try:
        with open(fw, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("symbol","").upper() == SYM:
                    fw_hits.append(row)
    except: pass
log(f"  {SYM} rows in FW: {len(fw_hits)}")
if fw_hits:
    dates = sorted(r.get("date","")[:10] for r in fw_hits)
    log(f"  Range: {dates[0]} → {dates[-1]}")
    log(f"  Last 3:")
    for r in fw_hits[-3:]:
        log(f"    {r.get('date','')[:10]}: pos_r={r.get('lsr_pos_r','')} "
            f"acc_r={r.get('lsr_acc_r','')} glsr={r.get('lsr_global_r','')}")

# ── 5. Spot SAPI check ─────────────────────────────────────────────────────────
log("\n=== 5. Spot check (SAPI) ===")
spot = fetch_json(f"{SAPI}/api/v3/ticker/24hr?symbol={SYM}")
if spot and "lastPrice" in spot:
    log(f"  Spot {SYM}: lastPrice={spot.get('lastPrice')} vol=${float(spot.get('quoteVolume',0)):,.0f}")
else:
    log(f"  Spot {SYM}: NOT FOUND (perp-only or different quote)")

# Check GUAUSDT on spot BAPI
bapi_price = fetch_json(f"https://www.binance.com/bapi/asset/v1/public/asset/asset/get-all-asset")
# Don't parse full, just note
log(f"  BAPI asset check: skipped (too large)")

# ── 6. Ticker live ─────────────────────────────────────────────────────────────
log("\n=== 6. Ticker live (perp) ===")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"  lastPrice: {ticker.get('lastPrice')}")
    log(f"  24h pct:   {float(ticker.get('priceChangePercent',0)):+.2f}%")
    log(f"  24h vol:   ${float(ticker.get('quoteVolume',0)):,.0f}")
    log(f"  24h high:  {ticker.get('highPrice')}  low: {ticker.get('lowPrice')}")
    log(f"  openPrice: {ticker.get('openPrice')}")

# ── 7. Disambiguation table ────────────────────────────────────────────────────
log("\n=== 7. DISAMBIGUATION TABLE ===")
log(f"  {'Symbol':<20} {'Base':<8} {'Note'}")
log(f"  {'-'*20} {'-'*8} {'-'*30}")
for v in variants_found:
    note = "→ LOCKED" if v["symbol"] == SYM else ("different base" if v["baseAsset"] != "GUA" else "variant")
    log(f"  {v['symbol']:<20} {v['baseAsset']:<8} {note}")
if not variants_found:
    log(f"  (no variants found — GUAUSDT unique)")

# ── 8. Save metadata ───────────────────────────────────────────────────────────
meta = {
    "symbol": SYM,
    "baseAsset": target.get("baseAsset") if target else "GUA",
    "onboardDate_ms": START_MS,
    "onboardDate": datetime.fromtimestamp(START_MS/1000, tz=timezone.utc).strftime("%Y-%m-%d") if START_MS else "N/A",
    "alpha_id": alpha_id,
    "contract": contract_addr,
    "fw_rows": len(fw_hits),
    "token_meta": token_meta,
}
out = SCRATCH / f"{SYM_LOWER}_perp_info_{DATE_TAG}.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
log(f"\n  Saved: {out.name}")
log(f"  START_MS: {START_MS}")
log(f"  Onboard: {meta['onboardDate']}")
log(f"  Alpha ID: {alpha_id}")
log(f"  Contract: {contract_addr or 'N/A'}")
log(f"  FW rows: {len(fw_hits)}")
log(f"\n[G-0 DONE]")

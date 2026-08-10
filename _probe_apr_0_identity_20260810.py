"""
_probe_apr_0_identity_20260810.py
A-0: Identity lock — APRUSDT. Check APRS/APRIL variants.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
TARGET  = "APRUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-0 IDENTITY LOCK  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

FAPI = "https://fapi.binance.com"

# ── 1. exchangeInfo — all APR* symbols ───────────────────────────────────
log("\n=== 1. FAPI exchangeInfo — all APR* symbols ===")
info = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
apr_syms = {}
if info:
    for s in info.get("symbols", []):
        sym = s.get("symbol","").upper()
        if sym.startswith("APR"):
            apr_syms[sym] = s

log(f"  All APR* perp symbols: {list(apr_syms.keys())}")
for sym in apr_syms:
    s = apr_syms[sym]
    onb = s.get("onboardDate")
    onb_dt = datetime.fromtimestamp(int(onb)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if onb else "N/A"
    log(f"  {sym}:")
    log(f"    status:       {s.get('status')}")
    log(f"    onboardDate:  {onb} ({onb_dt})")
    log(f"    contractType: {s.get('contractType')}")
    log(f"    baseAsset:    {s.get('baseAsset')}")
    log(f"    quoteAsset:   {s.get('quoteAsset')}")

target_info = apr_syms.get("APRUSDT", {})
out = SCRATCH / f"apr_perp_info_{DATE_TAG}.json"
out.write_text(json.dumps(target_info, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")

# ── 2. alpha_id_map — APR + variants ─────────────────────────────────────
log("\n=== 2. alpha_id_map lookup ===")
map_path = ROOT / "data" / "config" / "alpha_id_map.json"
apr_alpha_id = None
variants_found = {}
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    for sym, aid in amap.items():
        su = sym.upper()
        if su == "APR":
            apr_alpha_id = aid
            log(f"  APR (exact) → alphaId={aid}")
        elif su.startswith("APR") or "APRIL" in su or "APRS" in su:
            variants_found[sym] = aid
            log(f"  Variant: {sym} → {aid}")
    if not apr_alpha_id and not variants_found:
        log(f"  No APR* in alpha_id_map")
    # disambiguation table if variants exist
    if variants_found:
        log(f"\n  ── Disambiguation table ──")
        log(f"  {'Symbol':<20s} {'alphaId':<15s} {'note'}")
        if apr_alpha_id:
            log(f"  {'APR':<20s} {apr_alpha_id:<15s} TARGET")
        for sym, aid in variants_found.items():
            log(f"  {sym:<20s} {aid:<15s} VARIANT")
else:
    log(f"  alpha_id_map not found: {map_path}")

# ── 3. BAPI token list ────────────────────────────────────────────────────
log("\n=== 3. BAPI token list — APR search ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
apr_tok = None
apr_variants_tok = []
if bapi_data:
    raw = bapi_data.get("data", [])
    token_list = raw if isinstance(raw, list) else raw.get("tokenList", raw.get("list", []))
    log(f"  Total tokens: {len(token_list)}")
    for t in token_list:
        sym = t.get("tokenSymbol","").upper()
        aid = t.get("alphaId","")
        if sym == "APR" or (apr_alpha_id and aid == apr_alpha_id):
            apr_tok = t
            log(f"  APR exact: sym={sym} alphaId={aid} fullyDelisted={t.get('fullyDelisted')}")
        elif sym.startswith("APR") and sym != "APR":
            apr_variants_tok.append(t)
            log(f"  APR variant in BAPI: {sym} alphaId={aid} fullyDelisted={t.get('fullyDelisted')}")
        elif "APRIL" in sym:
            apr_variants_tok.append(t)
            log(f"  APRIL in BAPI: {sym} alphaId={aid}")

    if apr_tok:
        log(f"\n  APR token detail:")
        for k in ["alphaId","tokenSymbol","contractAddress","totalSupply","circulatingSupply",
                  "holders","fullyDelisted","offsell","offline","listingTime","price","marketCap"]:
            log(f"    {k}: {apr_tok.get(k)}")
        bapi_out = SCRATCH / f"apr_bapi_{DATE_TAG}.json"
        bapi_out.write_text(json.dumps(apr_tok, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"  Saved: {bapi_out.name}")
    else:
        log(f"  APR not found in BAPI (sym=APR or alphaId={apr_alpha_id})")
        bapi_out = SCRATCH / f"apr_bapi_{DATE_TAG}.json"
        bapi_out.write_text(json.dumps({"note":"not_found_in_bapi","symbol":"APR","alpha_id":apr_alpha_id}, indent=2), encoding="utf-8")

    if apr_variants_tok:
        log(f"\n  APR variant tokens detail:")
        for tv in apr_variants_tok[:3]:
            log(f"    {tv.get('tokenSymbol')}: alphaId={tv.get('alphaId')} contract={str(tv.get('contractAddress',''))[:30]} fullyDelisted={tv.get('fullyDelisted')}")

# ── 4. Contract cross-verify ──────────────────────────────────────────────
log("\n=== 4. Contract cross-verify ===")
if apr_tok:
    log(f"  APR contract: {apr_tok.get('contractAddress','N/A')}")
for vt in apr_variants_tok:
    vc = vt.get('contractAddress','')
    ac = apr_tok.get('contractAddress','') if apr_tok else ''
    same = (vc.lower() == ac.lower()) if (vc and ac) else False
    log(f"  {vt.get('tokenSymbol')} contract: {vc[:30]}... SAME_AS_APR: {'YES — CRITICAL' if same else 'NO — distinct'}")

# ── 5. PASS/FAIL ─────────────────────────────────────────────────────────
log("\n=== A-0 PASS/FAIL GATE ===")
gate_perp   = "APRUSDT" in apr_syms
gate_status = apr_syms.get("APRUSDT",{}).get("status") == "TRADING"
gate_alpha  = apr_tok is not None

log(f"  G1 APRUSDT in exchangeInfo: {'PASS' if gate_perp else 'FAIL'}")
log(f"  G2 Status=TRADING: {'PASS' if gate_status else 'FAIL'}")
log(f"  G3 Alpha token in BAPI: {'PASS' if gate_alpha else 'FAIL — not Alpha'}")
log(f"  G4 Variants disambiguation: {len(variants_found)} variants in map, {len(apr_variants_tok)} in BAPI")

overall = gate_perp and gate_status
log(f"\n  OVERALL A-0: {'PASS — proceed' if overall else 'FAIL — STOP'}")

summary = {
    "apr_symbol_perp":  "APRUSDT",
    "apr_alpha_id":     apr_alpha_id,
    "apr_contract":     apr_tok.get("contractAddress") if apr_tok else None,
    "apr_totalSupply":  apr_tok.get("totalSupply") if apr_tok else None,
    "apr_holders":      apr_tok.get("holders") if apr_tok else None,
    "apr_fullyDelisted":apr_tok.get("fullyDelisted") if apr_tok else None,
    "apr_listingTime":  apr_tok.get("listingTime") if apr_tok else None,
    "apr_price":        apr_tok.get("price") if apr_tok else None,
    "apr_marketCap":    apr_tok.get("marketCap") if apr_tok else None,
    "variants_map":     variants_found,
    "variants_bapi":    [v.get("tokenSymbol") for v in apr_variants_tok],
    "gate_pass":        overall,
    "onboard_date":     datetime.fromtimestamp(
        int(target_info.get("onboardDate",0))/1000, tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC") if target_info.get("onboardDate") else None,
}
out3 = SCRATCH / f"apr_identity_{DATE_TAG}.json"
out3.write_text(json.dumps(summary, indent=2), encoding="utf-8")
log(f"\n  Identity summary: {out3.name}")
log(f"\n[A-0 DONE]")

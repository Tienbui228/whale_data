"""
_probe_koma_0_identity_20260810.py
K-0: Identity lock — KOMAUSDT. Check KOMAINU variants.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
TARGET  = "KOMAUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-0 IDENTITY LOCK  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"

# ── 1. exchangeInfo — all KOMA* symbols ──────────────────────────────────
log("\n=== 1. FAPI exchangeInfo — all KOMA symbols ===")
info = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
koma_syms = {}
if info:
    for s in info.get("symbols", []):
        sym = s.get("symbol","").upper()
        if sym.startswith("KOMA"):
            koma_syms[sym] = s

log(f"  All KOMA* perp symbols: {list(koma_syms.keys())}")

for sym in koma_syms:
    s = koma_syms[sym]
    onb = s.get("onboardDate")
    onb_dt = datetime.fromtimestamp(int(onb)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if onb else "N/A"
    log(f"  {sym}:")
    log(f"    status:       {s.get('status')}")
    log(f"    onboardDate:  {onb} ({onb_dt})")
    log(f"    contractType: {s.get('contractType')}")
    log(f"    baseAsset:    {s.get('baseAsset')}")
    log(f"    quoteAsset:   {s.get('quoteAsset')}")

# Save perp info for KOMAUSDT
target_info = koma_syms.get("KOMAUSDT", {})
out = SCRATCH / f"koma_perp_info_{DATE_TAG}.json"
out.write_text(json.dumps(target_info, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")

# ── 2. alpha_id_map — exact + fuzzy KOMA search ───────────────────────────
log("\n=== 2. alpha_id_map lookup ===")
map_path = ROOT / "data" / "config" / "alpha_id_map.json"
koma_alpha_id = None
variants_found = {}
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    # Exact match
    for sym, aid in amap.items():
        if sym.upper() == "KOMA":
            koma_alpha_id = aid
            log(f"  KOMA (exact) → alphaId={aid}")
    # Fuzzy — any key containing KOMA
    for sym, aid in amap.items():
        if "KOMA" in sym.upper() and sym.upper() != "KOMA":
            variants_found[sym] = aid
            log(f"  Fuzzy KOMA variant: {sym} → {aid}")
    if not koma_alpha_id and not variants_found:
        log(f"  No KOMA entries in alpha_id_map")
    # Also check KOMAINU specifically
    for sym, aid in amap.items():
        if "KOMAINU" in sym.upper():
            log(f"  KOMAINU found: {sym} → {aid}")
else:
    log(f"  alpha_id_map not found: {map_path}")

# ── 3. BAPI — search all KOMA tokens ─────────────────────────────────────
log("\n=== 3. BAPI token list — KOMA search ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
koma_tok = None
komainu_tok = None
if bapi_data:
    raw = bapi_data.get("data", [])
    token_list = raw if isinstance(raw, list) else raw.get("tokenList", raw.get("list", []))
    log(f"  Total tokens: {len(token_list)}")
    for t in token_list:
        sym = t.get("tokenSymbol","").upper()
        aid = t.get("alphaId","")
        if sym == "KOMA" or (koma_alpha_id and aid == koma_alpha_id):
            koma_tok = t
            log(f"  KOMA exact: {sym} alphaId={aid} fullyDelisted={t.get('fullyDelisted')}")
        if "KOMAINU" in sym:
            komainu_tok = t
            log(f"  KOMAINU found: {sym} alphaId={aid} fullyDelisted={t.get('fullyDelisted')}")
        elif "KOMA" in sym and sym != "KOMA":
            log(f"  KOMA variant: {sym} alphaId={aid}")

    if koma_tok:
        log(f"\n  KOMA token detail:")
        for k in ["alphaId","tokenSymbol","contractAddress","totalSupply","circulatingSupply",
                  "holders","fullyDelisted","offsell","offline","listingTime","price","marketCap"]:
            log(f"    {k}: {koma_tok.get(k)}")
        bapi_out = SCRATCH / f"koma_bapi_{DATE_TAG}.json"
        bapi_out.write_text(json.dumps(koma_tok, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"  Saved: {bapi_out.name}")
    else:
        log(f"  KOMA not found in BAPI by exact symbol or alphaId={koma_alpha_id}")
        bapi_out = SCRATCH / f"koma_bapi_{DATE_TAG}.json"
        bapi_out.write_text(json.dumps({"note":"not_found","query":"KOMA","alpha_id":koma_alpha_id}, indent=2), encoding="utf-8")

    if komainu_tok:
        log(f"\n  KOMAINU token detail:")
        for k in ["alphaId","tokenSymbol","contractAddress","fullyDelisted","listingTime","marketCap"]:
            log(f"    {k}: {komainu_tok.get(k)}")

# ── 4. Contract cross-verify (if both found) ──────────────────────────────
log("\n=== 4. Contract cross-verify ===")
if koma_tok:
    log(f"  KOMA contract: {koma_tok.get('contractAddress','N/A')}")
if komainu_tok:
    log(f"  KOMAINU contract: {komainu_tok.get('contractAddress','N/A')}")
if koma_tok and komainu_tok:
    c1 = koma_tok.get("contractAddress","")
    c2 = komainu_tok.get("contractAddress","")
    log(f"  Contracts DIFFERENT: {'YES ✓' if c1.lower() != c2.lower() else 'SAME — CRITICAL ERROR'}")

# ── 5. PASS/FAIL gate ─────────────────────────────────────────────────────
log("\n=== K-0 PASS/FAIL GATE ===")
gate_perp   = "KOMAUSDT" in koma_syms
gate_status = koma_syms.get("KOMAUSDT",{}).get("status") == "TRADING"
gate_alpha  = koma_tok is not None

log(f"  G1 KOMAUSDT in exchangeInfo: {'PASS' if gate_perp else 'FAIL'}")
log(f"  G2 Status=TRADING: {'PASS' if gate_status else 'FAIL'}")
log(f"  G3 Alpha token in BAPI: {'PASS' if gate_alpha else 'FAIL — not Alpha listed'}")
log(f"  G4 KOMAINU disambiguation: {'checked — see above' if komainu_tok or variants_found else 'no KOMAINU found'}")

overall = gate_perp and gate_status
log(f"\n  OVERALL K-0: {'PASS — proceed' if overall else 'FAIL — STOP'}")

summary = {
    "koma_symbol_perp":  "KOMAUSDT",
    "koma_alpha_id":     koma_alpha_id,
    "koma_contract":     koma_tok.get("contractAddress") if koma_tok else None,
    "koma_totalSupply":  koma_tok.get("totalSupply") if koma_tok else None,
    "koma_holders":      koma_tok.get("holders") if koma_tok else None,
    "koma_fullyDelisted":koma_tok.get("fullyDelisted") if koma_tok else None,
    "koma_listingTime":  koma_tok.get("listingTime") if koma_tok else None,
    "koma_price":        koma_tok.get("price") if koma_tok else None,
    "koma_marketCap":    koma_tok.get("marketCap") if koma_tok else None,
    "komainu_found":     komainu_tok is not None,
    "komainu_contract":  komainu_tok.get("contractAddress") if komainu_tok else None,
    "variants_found":    variants_found,
    "gate_pass":         overall,
    "onboard_date":      datetime.fromtimestamp(
        int(target_info.get("onboardDate",0))/1000, tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC") if target_info.get("onboardDate") else None,
}
out3 = SCRATCH / f"koma_identity_{DATE_TAG}.json"
out3.write_text(json.dumps(summary, indent=2), encoding="utf-8")
log(f"\n  Identity summary: {out3.name}")
log(f"\n[K-0 DONE]")

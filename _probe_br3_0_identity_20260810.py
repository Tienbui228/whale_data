"""
_probe_br3_0_identity_20260810.py
BR3-0: Identity lock — BROCCOLIF3BUSDT vs BROCCOLI714USDT disambiguation.
PASS gate before proceeding.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BR3-0 IDENTITY LOCK  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR fetching {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"

# ── 1. exchangeInfo — paste both broccoli symbols side by side ────────────────
log("\n=== 1. FAPI exchangeInfo — BOTH BROCCOLI symbols ===")
info = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
syms = {}
if info:
    for s in info.get("symbols", []):
        if "BROCCOLI" in s.get("symbol","").upper():
            syms[s["symbol"]] = s

log(f"  All BROCCOLI perp symbols found: {list(syms.keys())}")

for sym in ["BROCCOLIF3BUSDT", "BROCCOLI714USDT"]:
    s = syms.get(sym, {})
    if s:
        onb = s.get("onboardDate")
        onb_dt = datetime.fromtimestamp(int(onb)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if onb else "N/A"
        deliv = s.get("deliveryDate")
        deliv_str = "N/A"
        if deliv:
            try:
                deliv_str = datetime.fromtimestamp(int(deliv)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            except: pass
        log(f"  {sym}:")
        log(f"    status:       {s.get('status')}")
        log(f"    onboardDate:  {onb} ({onb_dt})")
        log(f"    deliveryDate: {deliv} ({deliv_str})")
        log(f"    contractType: {s.get('contractType')}")
        log(f"    marginType:   {s.get('marginType')}")
        log(f"    quoteAsset:   {s.get('quoteAsset')}")
        log(f"    baseAsset:    {s.get('baseAsset')}")
    else:
        log(f"  {sym}: NOT FOUND in exchangeInfo")

# Save perp info for target
target_info = syms.get("BROCCOLIF3BUSDT", {})
out = SCRATCH / f"br3_perp_info_{DATE_TAG}.json"
out.write_text(json.dumps(target_info, indent=2), encoding="utf-8")
log(f"\n  Saved: {out.name}")

# ── 2. alpha_id_map lookup — exact string match ───────────────────────────────
log("\n=== 2. alpha_id_map lookup ===")
map_path = ROOT / "data" / "config" / "alpha_id_map.json"
br3_alpha_id = None
br714_alpha_id = None
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    # Exact string match — no fuzzy
    for sym, aid in amap.items():
        if sym.upper() == "BROCCOLIF3B":
            br3_alpha_id = aid
            log(f"  BROCCOLIF3B → {aid}")
        if sym.upper() == "BROCCOLI714":
            br714_alpha_id = aid
            log(f"  BROCCOLI714  → {aid}")
    if not br3_alpha_id:
        log(f"  BROCCOLIF3B: NOT FOUND in alpha_id_map")
        # Try case-insensitive
        for sym, aid in amap.items():
            if "BROCCOLIF3B" in sym.upper():
                log(f"  Fuzzy match: {sym} → {aid}")
    if not br714_alpha_id:
        log(f"  BROCCOLI714: NOT FOUND in alpha_id_map")
        for sym, aid in amap.items():
            if "BROCCOLI714" in sym.upper():
                log(f"  Fuzzy match: {sym} → {aid}")
else:
    log(f"  alpha_id_map not found at {map_path}")

# ── 3. BAPI — fetch both tokens, verify contract + supply ────────────────────
log("\n=== 3. BAPI token list — cross-verify by alphaId ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
br3_tok = None
br714_tok = None
if bapi_data:
    raw = bapi_data.get("data", [])
    token_list = raw if isinstance(raw, list) else raw.get("tokenList", raw.get("list", []))
    log(f"  Total tokens in BAPI: {len(token_list)}")
    for t in token_list:
        sym = t.get("tokenSymbol","").upper()
        aid = t.get("alphaId","")
        if sym == "BROCCOLIF3B" or (br3_alpha_id and aid == br3_alpha_id):
            br3_tok = t
        if sym == "BROCCOLI714" or (br714_alpha_id and aid == br714_alpha_id):
            br714_tok = t

    log(f"\n  BROCCOLIF3B token:")
    if br3_tok:
        for k in ["alphaId","tokenSymbol","contractAddress","totalSupply","circulatingSupply",
                  "holders","fullyDelisted","offsell","offline","listingTime","price","marketCap"]:
            log(f"    {k}: {br3_tok.get(k)}")
        out2 = SCRATCH / f"br3_bapi_{DATE_TAG}.json"
        out2.write_text(json.dumps(br3_tok, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"  Saved: {out2.name}")
    else:
        log(f"    NOT FOUND by symbol=BROCCOLIF3B or alphaId={br3_alpha_id}")
        # Try partial match
        for t in token_list:
            if "BROCCOLI" in t.get("tokenSymbol","").upper():
                log(f"    Candidate: {t.get('tokenSymbol')} alphaId={t.get('alphaId')} contract={t.get('contractAddress','')[:20]}")

    log(f"\n  BROCCOLI714 token:")
    if br714_tok:
        for k in ["alphaId","tokenSymbol","contractAddress","totalSupply","fullyDelisted","listingTime"]:
            log(f"    {k}: {br714_tok.get(k)}")
    else:
        log(f"    NOT FOUND by symbol=BROCCOLI714 or alphaId={br714_alpha_id}")
        for t in token_list:
            if "BROCCOLI" in t.get("tokenSymbol","").upper():
                log(f"    Candidate: {t.get('tokenSymbol')} alphaId={t.get('alphaId')}")

# ── 4. Contract cross-verify ──────────────────────────────────────────────────
log("\n=== 4. CONTRACT CROSS-VERIFY ===")
if br3_tok and br714_tok:
    c3 = br3_tok.get("contractAddress","")
    c714 = br714_tok.get("contractAddress","")
    log(f"  BROCCOLIF3B contract: {c3}")
    log(f"  BROCCOLI714 contract: {c714}")
    log(f"  Contracts DIFFERENT: {'YES ✓' if c3.lower() != c714.lower() else 'SAME — CRITICAL ERROR'}")
elif br3_tok:
    log(f"  BROCCOLIF3B contract: {br3_tok.get('contractAddress')}")
    log(f"  BROCCOLI714: not found for comparison")

# ── 5. PASS/FAIL gate ─────────────────────────────────────────────────────────
log("\n=== BR3-0 PASS/FAIL GATE ===")
gate_perp   = "BROCCOLIF3BUSDT" in syms
gate_alpha  = br3_tok is not None
gate_no_mix = True  # will be False if contracts same

if br3_tok and br714_tok:
    gate_no_mix = br3_tok.get("contractAddress","").lower() != br714_tok.get("contractAddress","").lower()

log(f"  G1 Perp symbol verified (BROCCOLIF3BUSDT in exchangeInfo): {'PASS' if gate_perp else 'FAIL'}")
log(f"  G2 Alpha token found in BAPI: {'PASS' if gate_alpha else 'FAIL — need manual check'}")
log(f"  G3 Contract != BROCCOLI714: {'PASS' if gate_no_mix else 'FAIL — CRITICAL'}")
log(f"  G4 BROCCOLI714 also identified (not confused): {'PASS' if br714_tok or br714_alpha_id else 'WARN — 714 not found, may not exist'}")

overall = gate_perp  # minimum gate
log(f"\n  OVERALL BR3-0: {'PASS — proceed' if overall else 'FAIL — STOP'}")

# Save summary
summary = {
    "br3_symbol_perp": "BROCCOLIF3BUSDT",
    "br3_alpha_id": br3_alpha_id,
    "br3_contract": br3_tok.get("contractAddress") if br3_tok else None,
    "br3_totalSupply": br3_tok.get("totalSupply") if br3_tok else None,
    "br3_holders": br3_tok.get("holders") if br3_tok else None,
    "br3_fullyDelisted": br3_tok.get("fullyDelisted") if br3_tok else None,
    "br3_listingTime": br3_tok.get("listingTime") if br3_tok else None,
    "br714_alpha_id": br714_alpha_id,
    "br714_contract": br714_tok.get("contractAddress") if br714_tok else None,
    "gate_pass": overall,
}
out3 = SCRATCH / f"br3_identity_{DATE_TAG}.json"
out3.write_text(json.dumps(summary, indent=2), encoding="utf-8")
log(f"\n  Identity summary saved: {out3.name}")
log(f"\n[BR3-0 DONE]")

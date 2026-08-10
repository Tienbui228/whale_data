"""
_probe_on_0_identity_20260810.py
N-0: Định danh ONUSDT — grep ALL "ON" symbols từ exchangeInfo, lock baseAsset=ON.
Rủi ro nhầm: ONT, ONE, ONG, ONDO, PONTON, OMNI... cần bảng phân biệt.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
TARGET_SYM = "ONUSDT"
TARGET_BASE = "ON"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-0 IDENTITY ONUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── 1. FAPI exchangeInfo — grep tất cả symbols chứa "ON" ─────────────────────
log("\n=== 1. FAPI — tất cả perp symbols chứa 'ON' ===")
info = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
on_symbols = []
target_info = {}
if info:
    for s in info.get("symbols", []):
        sym = s.get("symbol", "")
        base = s.get("baseAsset", "")
        # grep: symbol OR baseAsset contains "ON" (case-insensitive, standalone check)
        if "ON" in sym.upper() or "ON" in base.upper():
            on_symbols.append({
                "symbol": sym,
                "baseAsset": base,
                "quoteAsset": s.get("quoteAsset",""),
                "status": s.get("status",""),
                "contractType": s.get("contractType",""),
                "onboardDate": s.get("onboardDate",""),
            })
        if sym == TARGET_SYM:
            target_info = s

log(f"\n  All FAPI perp symbols with 'ON':")
log(f"  {'Symbol':<22} {'Base':<10} {'Status':<12} {'ContractType':<16} {'Onboard'}")
log(f"  {'-'*22} {'-'*10} {'-'*12} {'-'*16} {'-'*12}")
for s in sorted(on_symbols, key=lambda x: x["symbol"]):
    ob = s["onboardDate"]
    ob_d = datetime.fromtimestamp(int(ob)/1000, tz=timezone.utc).strftime("%Y-%m-%d") if ob else "N/A"
    mark = " ← TARGET" if s["symbol"] == TARGET_SYM else ""
    log(f"  {s['symbol']:<22} {s['baseAsset']:<10} {s['status']:<12} {s['contractType']:<16} {ob_d}{mark}")

log(f"\n  Total 'ON' symbols: {len(on_symbols)}")

# ── 2. Target lock: ONUSDT ────────────────────────────────────────────────────
log(f"\n=== 2. Target lock: {TARGET_SYM} ===")
if not target_info:
    log(f"  ERROR: {TARGET_SYM} NOT FOUND in FAPI exchangeInfo!"); sys.exit(1)

onb_ms = int(target_info.get("onboardDate", 0))
onb_d = datetime.fromtimestamp(onb_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if onb_ms else "N/A"
log(f"  symbol:       {target_info.get('symbol')}")
log(f"  baseAsset:    {target_info.get('baseAsset')}  ← LOCKED (must be 'ON' only)")
log(f"  quoteAsset:   {target_info.get('quoteAsset')}")
log(f"  status:       {target_info.get('status')}")
log(f"  contractType: {target_info.get('contractType')}")
log(f"  onboardDate:  {onb_ms} ({onb_d})")

# pricePrecision + tickSize
for flt in target_info.get("filters", []):
    if flt.get("filterType") == "PRICE_FILTER":
        log(f"  tickSize:     {flt.get('tickSize')}")
    if flt.get("filterType") == "LOT_SIZE":
        log(f"  stepSize:     {flt.get('stepSize')}")

# Save perp_info
(SCRATCH/f"on_perp_info_{DATE_TAG}.json").write_text(
    json.dumps(target_info, indent=2), encoding="utf-8")
log(f"  Saved: on_perp_info_{DATE_TAG}.json")

# ── 3. BAPI Alpha token detail ─────────────────────────────────────────────────
log(f"\n=== 3. BAPI Alpha token detail ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
on_tok = None
if bapi_data:
    raw = bapi_data.get("data", [])
    token_list = raw if isinstance(raw, list) else raw.get("tokenList", raw.get("list", []))
    # Search for baseAsset=ON exactly
    for t in token_list:
        sym = t.get("tokenSymbol", "").upper()
        if sym == TARGET_BASE:
            on_tok = t; break

if on_tok:
    log(f"  Found: sym={on_tok.get('tokenSymbol')} alphaId={on_tok.get('alphaId')}")
    for k in ["contractAddress", "totalSupply", "circulatingSupply", "holders",
              "fullyDelisted", "listingTime", "price", "marketCap", "offSell", "offline"]:
        log(f"    {k}: {on_tok.get(k)}")
    (SCRATCH/f"on_bapi_{DATE_TAG}.json").write_text(
        json.dumps(on_tok, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  Saved: on_bapi_{DATE_TAG}.json")
else:
    log(f"  ON not found in BAPI alpha list (may be perp-only, not Alpha token)")
    (SCRATCH/f"on_bapi_{DATE_TAG}.json").write_text(
        json.dumps({"note":"not_found","symbol":TARGET_BASE}, indent=2), encoding="utf-8")

# ── 4. Alpha ID map ────────────────────────────────────────────────────────────
log(f"\n=== 4. Alpha ID map ===")
alpha_map_p = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_id = None
if alpha_map_p.exists():
    amap = json.loads(alpha_map_p.read_text(encoding="utf-8"))
    alpha_id = amap.get(TARGET_BASE)
    log(f"  ON alpha_id from map: {alpha_id}")
    # Also check if "ONUSDT" in map
    log(f"  ONUSDT in map: {amap.get('ONUSDT')}")
else:
    log(f"  alpha_id_map.json not found")

# ── 5. Spot check ─────────────────────────────────────────────────────────────
log(f"\n=== 5. Spot check ===")
spot = fetch_json(f"{SAPI}/api/v3/klines?symbol={TARGET_SYM}&interval=1d&limit=5")
if spot and len(spot) > 0:
    log(f"  Spot AVAILABLE: {len(spot)} rows, last close={spot[-1][4]}")
else:
    log(f"  Spot: N/A (no {TARGET_SYM} spot pair)")

# Also check ONBTC or ONBUSD
for spot_alt in ["ONBTC", "ONETH", "ONBNB"]:
    s2 = fetch_json(f"{SAPI}/api/v3/klines?symbol={spot_alt}&interval=1d&limit=3")
    if s2: log(f"  {spot_alt}: AVAILABLE {len(s2)} rows")

# ── 6. gom_state ───────────────────────────────────────────────────────────────
log(f"\n=== 6. gom_state.json — ON ===")
state_p = ROOT / "data" / "gom_state.json"
if state_p.exists():
    state = json.loads(state_p.read_text(encoding="utf-8"))
    on_st = state.get("ON", state.get("ONUSDT", {}))
    log(json.dumps(on_st, indent=2, default=str) if on_st else "  ON not in gom_state")
else:
    log(f"  gom_state.json not found")

# ── 7. FreshWatch count ────────────────────────────────────────────────────────
log(f"\n=== 7. FreshWatch ON rows ===")
import csv
fw_count = 0; fw_dates = []
for fw_csv in sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == TARGET_SYM:
                fw_count += 1; fw_dates.append(row.get("date","")[:10])
log(f"  {TARGET_SYM} rows in freshwatch (scratch): {fw_count}")
if fw_dates: log(f"  Date range: {min(fw_dates)} → {max(fw_dates)}")

# ── 8. agent_log grep ON ──────────────────────────────────────────────────────
log(f"\n=== 8. agent_log — ON key mentions ===")
agent_log = ROOT / "agent_log.md"
if agent_log.exists():
    lines = agent_log.read_text(encoding="utf-8").splitlines()
    # Word-boundary grep for " ON " (not ONDO, ONT, etc.)
    key_lines = [(i+1, l) for i,l in enumerate(lines)
                 if " ON " in f" {l} " and any(kw in l for kw in
                    ["ONUSDT","baseAsset=ON","ON perp","gom","fire","DQ","SUPP","decay","stage"])]
    for n,l in key_lines[:15]:
        log(f"  L{n}: {l[:120]}")
    if not key_lines:
        log(f"  (no key ON mentions found)")

# ── Summary ────────────────────────────────────────────────────────────────────
log(f"\n=== IDENTITY LOCK ===")
log(f"  TARGET_SYM = ONUSDT")
log(f"  baseAsset  = ON  (locked — distinct from ONT/ONE/ONG/ONDO)")
log(f"  status     = {target_info.get('status')}")
log(f"  onboard    = {onb_d}")
log(f"  alpha_id   = {alpha_id or on_tok.get('alphaId') if on_tok else 'N/A'}")

log(f"\n[N-0 DONE]")

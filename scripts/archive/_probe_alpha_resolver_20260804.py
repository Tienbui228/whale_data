#!/usr/bin/env python3
"""PROBE: Alpha resolver — token-list endpoint → full u50_universe coverage.

Bước 1: Test /bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list
Bước 2: Join 137 u50_universe symbols → alpha_id (via bsc_address → contractAddress)
Bước 3: Verify 12/12 CALIB_ALPHA match
Bước 4: Spot-check klines depth (earliest date) trên 3 tokens

Output: docs/reports/_probe_alpha_resolver_20260804.md
KHÔNG sửa code, KHÔNG ghi store.
"""
import csv, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = __import__("io").TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)

WHALE  = Path(r"D:\Data back test\whale_data")
U50    = Path(r"D:\Check onchain fresh wallets\u50_universe.csv")
OUT    = WHALE / "docs" / "reports" / "_probe_alpha_resolver_20260804.md"
BASE   = "https://www.binance.com"
UA     = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

CALIB_ALPHA = {
    "AKE": "ALPHA_331", "CLO": "ALPHA_429", "ESPORTS": "ALPHA_283",
    "BTW": "ALPHA_778", "POWER": "ALPHA_487", "BASED": "ALPHA_837",
    "BAS": "ALPHA_328", "TAG": "ALPHA_233", "IDOL": "ALPHA_223",
    "TUT": "ALPHA_117", "BULLA": "ALPHA_240", "BANK": "ALPHA_146",
}

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def bget(path, params=None):
    qs  = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{BASE}{path}{qs}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()), r.status
    except urllib.error.HTTPError as e:
        try: body = e.read().decode()[:300]
        except: body = ""
        return body, e.code
    except Exception as ex:
        return None, str(ex)

def flatten(raw):
    if isinstance(raw, list): return raw
    if isinstance(raw, dict):
        d = raw.get("data", raw)
        if isinstance(d, list): return d
        if isinstance(d, dict):
            return d.get("list") or d.get("tokens") or []
    return []

emit("# PROBE: Alpha Resolver — token-list + u50 full coverage")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit("")

# ─── BƯỚC 1: Token-list endpoint ──────────────────────────────────────────────
emit("## Bước 1: Token-list endpoint")
emit("")
TOKEN_LIST_PATH = "/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
emit(f"URL: `{BASE}{TOKEN_LIST_PATH}`")

raw, status = bget(TOKEN_LIST_PATH)
emit(f"Status: {status}")

if status != 200:
    emit(f"**FAIL** — {raw}")
    emit(""); emit("Blocker vẫn còn — CẦN OPERATOR DevTools."); emit("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nOutput: {OUT}"); sys.exit(1)

tokens_all = flatten(raw)
emit(f"Total Alpha tokens returned: {len(tokens_all)}")
if tokens_all:
    sample = tokens_all[0]
    emit(f"Sample keys: {list(sample.keys())[:10]}")
    emit(f"Sample entry: {json.dumps({k: sample[k] for k in list(sample.keys())[:8]})[:300]}")
emit("")

# Index by BSC contractAddress
alpha_by_addr = {}
for t in tokens_all:
    if str(t.get("chainId")) == "56":
        addr = (t.get("contractAddress") or "").lower().strip()
        if addr:
            alpha_by_addr[addr] = t
emit(f"BSC tokens (chainId=56) with contractAddress: {len(alpha_by_addr)}")
emit("")

# ─── BƯỚC 2: Join u50_universe ────────────────────────────────────────────────
emit("## Bước 2: u50_universe join → alpha_id resolver")
emit("")

rows = list(csv.DictReader(open(U50, encoding="utf-8-sig")))
emit(f"u50_universe: {len(rows)} symbols")
emit("")
emit(f"| {'symbol':<10} | {'bsc_address':<45} | {'alpha_id':<13} | status |")
emit(f"|{'-'*12}|{'-'*47}|{'-'*15}|{'-'*10}|")

resolver = {}   # futures_base -> alpha_id
fail_list = []
ok_list = []

for r in rows:
    sym  = r["futures_base"]
    bsc  = (r.get("bsc_address") or "").lower().strip()
    t    = alpha_by_addr.get(bsc) if bsc else None
    if not t:
        status_s = "NO_MATCH"
        fail_list.append(sym)
        emit(f"| {sym:<10} | {(bsc or 'MISSING'):<45} | {'':13} | {status_s} |")
    else:
        alpha_id = t.get("alphaId") or t.get("alpha_id") or ""
        if alpha_id:
            resolver[sym] = alpha_id
            ok_list.append(sym)
            emit(f"| {sym:<10} | {bsc:<45} | {alpha_id:<13} | OK |")
        else:
            fail_list.append(sym)
            emit(f"| {sym:<10} | {bsc:<45} | NO_ALPHAID | FAIL |")

emit("")
emit(f"**OK (alpha_id found): {len(ok_list)}**")
emit(f"**FAIL (no match): {len(fail_list)}**")
emit("")
if fail_list:
    emit(f"FAIL list: {fail_list[:50]}")
emit("")

# ─── BƯỚC 3: Verify CALIB_ALPHA 12/12 ─────────────────────────────────────────
emit("## Bước 3: CALIB_ALPHA 12/12 verification")
emit("")
emit(f"| symbol | CALIB_expected | resolver_got | match |")
emit(f"|--------|----------------|--------------|-------|")

match_count = 0
for sym, expected in sorted(CALIB_ALPHA.items()):
    got = resolver.get(sym, "MISSING")
    ok  = "✓" if got == expected else "✗ MISMATCH"
    if got == expected:
        match_count += 1
    emit(f"| {sym:<6} | {expected:<14} | {got:<12} | {ok} |")

emit("")
emit(f"Match: {match_count}/12 — {'PASS ✓' if match_count == 12 else 'FAIL ✗'}")
if match_count == 12:
    emit("→ CALIB_ALPHA dict có thể retire (resolver tự động thay thế)")
emit("")

# ─── BƯỚC 4: Klines depth check (3 sample tokens) ────────────────────────────
emit("## Bước 4: Klines depth check (earliest date)")
emit("")

DEPTH_SAMPLES = []
for sym in ["BLUAI", "IDOL", "TAG"]:
    if sym in resolver:
        DEPTH_SAMPLES.append((sym, resolver[sym]))
if not DEPTH_SAMPLES:
    # fallback to first 3 ok
    DEPTH_SAMPLES = [(s, resolver[s]) for s in ok_list[:3]]

emit(f"| symbol | alpha_id | earliest_date | n_candles | latest_date |")
emit(f"|--------|----------|---------------|-----------|-------------|")

for sym, alpha_id in DEPTH_SAMPLES:
    ticker_sym = f"{alpha_id}USDT"
    # Fetch with large limit to get max history
    data, st = bget("/bapi/defi/v1/public/alpha-trade/klines",
                    {"symbol": ticker_sym, "interval": "1d", "limit": 1000})
    if st != 200 or not data:
        emit(f"| {sym} | {alpha_id} | FAIL({st}) | - | - |")
        continue
    arr = data if isinstance(data, list) else flatten(data)
    if not arr:
        emit(f"| {sym} | {alpha_id} | EMPTY | 0 | - |")
        continue
    try:
        def ts_to_date(ms): return datetime.fromtimestamp(int(ms)//1000, timezone.utc).strftime("%Y-%m-%d")
        earliest = ts_to_date(arr[0][0])
        latest   = ts_to_date(arr[-1][0])
        emit(f"| {sym} | {alpha_id} | {earliest} | {len(arr)} | {latest} |")
    except Exception as ex:
        emit(f"| {sym} | {alpha_id} | parse_err({ex}) | {len(arr)} | - |")
    time.sleep(0.5)

emit("")

# ─── SUMMARY ──────────────────────────────────────────────────────────────────
emit("## Summary")
emit("")
emit(f"- Token-list endpoint: **{'OK' if status == 200 else 'FAIL'}**")
emit(f"- BSC tokens indexed: {len(alpha_by_addr)}")
emit(f"- u50_universe coverage: {len(ok_list)}/{len(rows)} resolved")
emit(f"- CALIB_ALPHA verify: {match_count}/12")
emit(f"- FAIL (no alpha listing): {len(fail_list)} — {fail_list[:20]}")
emit("")
emit("### Resolver dict (toàn bộ)")
emit("")
emit("```python")
emit("ALPHA_ID_MAP = {")
for sym in sorted(resolver):
    emit(f'    "{sym}": "{resolver[sym]}",')
emit("}")
emit("```")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

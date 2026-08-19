#!/usr/bin/env python3
"""[F1/F2/F3/F4] GUA identity forensics — READ-ONLY.

F1: trace lookup chain, verify contract match at map creation.
F2: price triangle 15-17/08 bapi alpha ALPHA_483 vs Gate GUA_USDT vs perp GUAUSDT.
F3: check circular: is Alpha $234K (15/08) via same lookup as F1?
F4: sweep fw-139 ratio px_alpha/px_perp.
"""
import sys, io, json, urllib.request, urllib.parse, time, math, csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
U50 = Path(r"D:\Check onchain fresh wallets\u50_universe.csv")
ALPHA_MAP = REPO / "data" / "config" / "alpha_id_map.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def bapi_get(path, params):
    qs = urllib.parse.urlencode(params)
    url = f"https://www.binance.com{path}?{qs}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = json.loads(r.read().decode())
    return raw

def bapi_alpha_klines(alpha_id, day_start_ms, day_end_ms):
    """Fetch 1-day alpha kline."""
    try:
        arr = bapi_get("/bapi/defi/v1/public/alpha-trade/klines",
            {"symbol": f"{alpha_id}USDT", "interval": "1d",
             "startTime": day_start_ms, "endTime": day_end_ms - 1, "limit": 1})
        if isinstance(arr, dict): arr = arr.get("data", [])
        return arr
    except Exception as e:
        return f"ERR: {e}"

def gate_klines(pair, day_start_s, day_end_s):
    url = f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={pair}&interval=1d&from={day_start_s}&to={day_end_s}"
    try:
        return json.load(urllib.request.urlopen(url, timeout=15))
    except Exception as e:
        return f"ERR: {e}"

def perp_klines(sym, day_start_ms, day_end_ms):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&startTime={day_start_ms}&endTime={day_end_ms-1}&limit=1"
    try:
        return json.load(urllib.request.urlopen(url, timeout=15))
    except Exception as e:
        return f"ERR: {e}"

DIV = "═" * 78

# ============================================================================
# F1 — LOOKUP CHAIN
# ============================================================================
print(f"{DIV}\n[F1] LOOKUP CHAIN — GUA → ALPHA_483 forensic\n{DIV}")

# a) Read alpha_id_map.json
alpha_map = json.loads(ALPHA_MAP.read_text(encoding="utf-8"))
print(f"\n[F1.a] alpha_id_map.json: {len(alpha_map)} entries")
print(f"       key='GUA' → value={alpha_map.get('GUA', 'MISSING')!r}")
print(f"       lookup uses KEY (symbol string) — unique_field=NO (symbol collision possible)")

# b) Read u50_universe.csv row for GUA
u50_rows = list(csv.DictReader(open(U50, encoding="utf-8-sig")))
gua_u50 = next((r for r in u50_rows if r["futures_base"] == "GUA"), None)
print(f"\n[F1.b] u50_universe.csv GUA row:")
if gua_u50:
    for k, v in gua_u50.items():
        print(f"       {k}: {v}")
    u50_contract = (gua_u50.get("bsc_address") or "").lower().strip()
    print(f"       → u50 bsc_address canonical = {u50_contract}")

# c) Query Alpha bapi wallet endpoint to see full alpha token record for GUA / ALPHA_483
print(f"\n[F1.c] bapi wallet-direct alpha token-list — look up alphaId=ALPHA_483:")
raw = bapi_get("/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
tokens_all = raw if isinstance(raw, list) else raw.get("data", [])
if isinstance(tokens_all, dict):
    tokens_all = tokens_all.get("list") or tokens_all.get("tokens") or []
print(f"       total tokens: {len(tokens_all)}")

# find by alphaId
alpha_483 = [t for t in tokens_all if str(t.get("alphaId")) == "ALPHA_483"]
print(f"       matches alphaId==ALPHA_483: {len(alpha_483)}")
for t in alpha_483[:3]:
    print(f"         {json.dumps({k: t.get(k) for k in ['alphaId','symbol','name','chainId','contractAddress','tokenId']}, ensure_ascii=False)}")

# find by contract address u50 GUA
if gua_u50:
    ct = (gua_u50.get("bsc_address") or "").lower().strip()
    hits_ct = [t for t in tokens_all if (t.get("contractAddress") or "").lower() == ct]
    print(f"       matches contract={ct[:10]}...: {len(hits_ct)}")
    for t in hits_ct[:3]:
        print(f"         {json.dumps({k: t.get(k) for k in ['alphaId','symbol','name','chainId','contractAddress']}, ensure_ascii=False)}")

# also find by symbol='GUA' (multi-hit test)
hits_sym = [t for t in tokens_all if (t.get("symbol") or "").upper() == "GUA"]
print(f"       matches symbol=='GUA': {len(hits_sym)} (collision test)")
for t in hits_sym[:5]:
    print(f"         {json.dumps({k: t.get(k) for k in ['alphaId','symbol','name','chainId','contractAddress']}, ensure_ascii=False)}")

# ============================================================================
# F2 — TRIANGLE PRICES 15-17/08
# ============================================================================
print(f"\n{DIV}\n[F2] TAM GIÁC GIÁ 15-17/08 (bapi alpha / Gate / perp)\n{DIV}")

dates = ["2026-08-15", "2026-08-16", "2026-08-17"]
alpha_id = alpha_map.get("GUA")

for d in dates:
    ds_ms = int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)
    de_ms = ds_ms + 86400000
    ds_s  = ds_ms // 1000
    de_s  = de_ms // 1000

    print(f"\n  ── {d} ──")

    # ① bapi alpha ALPHA_483
    if alpha_id:
        arr = bapi_alpha_klines(alpha_id, ds_ms, de_ms)
        if isinstance(arr, str):
            print(f"    ① Alpha {alpha_id}USDT: {arr}")
        elif arr:
            k = arr[0]
            # [openTime, open, high, low, close, base_vol, closeTime, quote_vol, n_trades, taker_buy_base, taker_buy_quote, ignore]
            close = float(k[4]); base_vol = float(k[5] or 0); quote_vol = float(k[7] or 0)
            avg_px = quote_vol / base_vol if base_vol > 0 else close
            print(f"    ① Alpha {alpha_id}USDT: close={close:.6f} avg_px={avg_px:.6f} base_vol={base_vol:.0f} quote_vol=${quote_vol:,.0f}")
        else:
            print(f"    ① Alpha {alpha_id}USDT: (empty response)")

    # ② Gate GUA_USDT
    g = gate_klines("GUA_USDT", ds_s, de_s)
    if isinstance(g, str):
        print(f"    ② Gate GUA_USDT: {g}")
    elif g:
        # Format: [ts, quote_vol, close, high, low, open, base_vol, complete]
        c = g[0]
        close_g = float(c[2]); qv_g = float(c[1]); bv_g = float(c[6])
        print(f"    ② Gate GUA_USDT: close={close_g:.6f} qv=${qv_g:,.0f} bv={bv_g:.0f}")

    # ③ perp GUAUSDT
    p = perp_klines("GUAUSDT", ds_ms, de_ms)
    if isinstance(p, str):
        print(f"    ③ Perp GUAUSDT: {p}")
    elif p:
        # [openTime, open, high, low, close, base_vol, closeTime, quote_vol, n_trades, taker_buy_base, taker_buy_quote, ignore]
        k = p[0]
        close_p = float(k[4]); qv_p = float(k[7])
        print(f"    ③ Perp GUAUSDT: close={close_p:.6f} quote_vol=${qv_p:,.0f}")

    time.sleep(0.4)

# ============================================================================
# F3 — CIRCULAR CHECK (Alpha $234K khớp sổ)
# ============================================================================
print(f"\n{DIV}\n[F3] CIRCULAR CHECK — Alpha $234K (15/08) via cùng lookup?\n{DIV}")
print("""
  Đường thu $234K (theo _gua_refresh_20260818.md line 85, 98):
    - Report: 'Sổ có vol Aug16 = $234,378 (khớp handover 17/08)'
    - Line 98: 'vol_alpha = "alpha_klines_bapi:107060"'
  Đường collect: collect_alpha_daily.py line 176 alpha_map[symbol]=alpha_id
                  → bapi_klines(symbol=f"{alpha_id}USDT")
  Đường 'khớp sổ 18/08': handover 17/08 nói $234K = KHÔNG rõ nguồn khác hay không
""")
# Actually re-fetch Alpha ALPHA_483USDT 08-16 to confirm $234K figure
d_2 = "2026-08-16"
ds_ms = int(datetime.fromisoformat(d_2).replace(tzinfo=timezone.utc).timestamp() * 1000)
de_ms = ds_ms + 86400000
arr = bapi_alpha_klines(alpha_id, ds_ms, de_ms)
if isinstance(arr, list) and arr:
    k = arr[0]
    qv = float(k[7] or 0); bv = float(k[5] or 0)
    print(f"  [refetch Alpha ALPHA_483USDT 2026-08-16] quote_vol=${qv:,.0f}  base_vol={bv:.0f}")
    if abs(qv - 234378) / 234378 < 0.03:
        print(f"    → KHỚP $234K report (diff <3%)")
        print(f"    → VÒNG TRÒN: '$234K khớp sổ' = A khớp A (cùng lookup ALPHA_483, cùng bapi)")
    else:
        print(f"    → LỆCH ${abs(qv-234378):,.0f} — số cũ không tái tạo được")

# ============================================================================
# F4 — SWEEP fw-139 RATIO px_alpha/px_perp
# ============================================================================
print(f"\n{DIV}\n[F4] SWEEP fw-139 — ratio px_alpha / px_perp (independent evidence)\n{DIV}")
print("  Reading 1 recent day: 2026-08-17")
target_d = "2026-08-17"
ds_ms = int(datetime.fromisoformat(target_d).replace(tzinfo=timezone.utc).timestamp() * 1000)
de_ms = ds_ms + 86400000

print(f"\n  {'symbol':>10}  {'alphaId':>10}  {'px_alpha':>10}  {'px_perp':>10}  {'ratio':>8}  {'flag':>10}")
print("  " + "-" * 78)

results = []
for sym in sorted(alpha_map.keys()):
    aid = alpha_map[sym]
    # alpha price
    arr = bapi_alpha_klines(aid, ds_ms, de_ms)
    if isinstance(arr, list) and arr:
        k = arr[0]
        bv = float(k[5] or 0); qv = float(k[7] or 0); cl = float(k[4] or 0)
        px_a = qv / bv if bv > 0 else cl
    else:
        px_a = float("nan")
    # perp price
    try:
        p = perp_klines(f"{sym}USDT", ds_ms, de_ms)
        px_p = float(p[0][4]) if (isinstance(p, list) and p) else float("nan")
    except:
        px_p = float("nan")
    ratio = px_a / px_p if (not math.isnan(px_a) and not math.isnan(px_p) and px_p > 0) else float("nan")
    flag = "OUT" if (not math.isnan(ratio) and (ratio < 0.8 or ratio > 1.25)) else ("OK" if not math.isnan(ratio) else "?")
    if math.isnan(px_a) and math.isnan(px_p):
        flag = "SKIP-noA-noP"
    elif math.isnan(px_a):
        flag = "no-alpha"
    elif math.isnan(px_p):
        flag = "no-perp"
    results.append({"sym": sym, "aid": aid, "px_a": px_a, "px_p": px_p, "ratio": ratio, "flag": flag})
    time.sleep(0.35)

# Print flagged only + summary
out_of_band = [r for r in results if r["flag"] == "OUT"]
ok_band     = [r for r in results if r["flag"] == "OK"]
no_alpha    = [r for r in results if r["flag"] == "no-alpha"]
no_perp     = [r for r in results if r["flag"] == "no-perp"]

print(f"\n  === SUMMARY ===")
print(f"  total tokens in alpha_map : {len(results)}")
print(f"  OK (ratio ∈ [0.8, 1.25])  : {len(ok_band)}")
print(f"  OUT of band               : {len(out_of_band)}")
print(f"  no-alpha (empty klines)   : {len(no_alpha)}")
print(f"  no-perp  (delist/no futu) : {len(no_perp)}")

print(f"\n  === FLAGGED OUT-OF-BAND (ratio ∉ [0.8, 1.25]) — nghi collision ===")
for r in out_of_band:
    print(f"    {r['sym']:>10}  {r['aid']:>10}  {r['px_a']:>10.5f}  {r['px_p']:>10.5f}  {r['ratio']:>8.3f}")

print(f"\n  === NO-ALPHA (empty klines) — có thể delisted alpha ===")
for r in no_alpha[:20]:
    print(f"    {r['sym']:>10}  {r['aid']:>10}  px_perp={r['px_p']:.5f}")

print(f"\n  === NO-PERP (no futures/delisted) ===")
for r in no_perp[:20]:
    print(f"    {r['sym']:>10}  {r['aid']:>10}  px_alpha={r['px_a']:.5f}")

# Save results JSON to /tmp
out_json = Path("/tmp/gua_forensics_20260819/f4_sweep.json")
out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"\n  [saved] {out_json} ({len(results)} rows)")

print(f"\n{DIV}\nDONE F1-F4. F5-F6 = paper (no code).\n{DIV}")

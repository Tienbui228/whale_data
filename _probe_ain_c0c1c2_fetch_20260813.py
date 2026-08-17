"""
_probe_ain_c0c1c2_fetch_20260813.py
AI-0 identity + AI-1 LSR/OI persist + AI-2 klines+events AINUSDT.
data-source : fapi.binance.com / bapi / exchangeInfo / GeckoTerminal / Gate.io
machine     : local
date-range  : full history → 2026-08-12 (L-21 skip 13/08)
code-commit : TBD
"""
import sys, io, json, csv, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260813"
SYM   = "AINUSDT"
BASE  = "AIN"
LOWER = "ain"
L21   = "2026-08-12"

def log(s=""): print(s, flush=True)

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

def fetch_paginated_klines(symbol, interval, start_ms, end_ms, limit=1000):
    rows = []
    cur = start_ms
    while cur < end_ms:
        url = (f"https://fapi.binance.com/fapi/v1/klines"
               f"?symbol={symbol}&interval={interval}&startTime={cur}&endTime={end_ms}&limit={limit}")
        data = fetch_json(url)
        if isinstance(data, dict) and "_error" in data:
            log(f"  klines error: {data['_error']}"); break
        if not data: break
        rows.extend(data)
        if len(data) < limit: break
        cur = data[-1][0] + 1
        time.sleep(0.15)
    return rows

def fetch_paginated_funding(symbol, start_ms, end_ms, limit=1000):
    rows = []
    cur = start_ms
    while cur < end_ms:
        url = (f"https://fapi.binance.com/fapi/v1/fundingRate"
               f"?symbol={symbol}&startTime={cur}&endTime={end_ms}&limit={limit}")
        data = fetch_json(url)
        if isinstance(data, dict) and "_error" in data:
            log(f"  funding error: {data['_error']}"); break
        if not data: break
        rows.extend(data)
        if len(data) < limit: break
        cur = data[-1]["fundingTime"] + 1
        time.sleep(0.15)
    return rows

def ms_to_date(ms): return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
def date_to_ms(ds):
    return int(datetime.strptime(ds, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
def sf(v, d=None):
    try: return float(v) if v not in (None, "", "None", "nan") else d
    except: return d

log("="*70)
log(f"AIN FETCH — AI-0/AI-1/AI-2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("="*70)

# ── AI-0a. IDENTITY ───────────────────────────────────────────────────────────
log("\n── AI-0a. IDENTITY ──")

exinfo = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
ain_info = {}
if "symbols" in exinfo:
    for s in exinfo["symbols"]:
        if s.get("symbol") == SYM:
            ain_info = s; break
if ain_info:
    ob_ms = ain_info.get("onboardDate", 0) or 0
    ob_str = ms_to_date(ob_ms) if ob_ms else "UNKNOWN"
    log(f"  AINUSDT perp: onboardDate={ob_str}, status={ain_info.get('status')}")
    log(f"    contractType={ain_info.get('contractType')}, marginAsset={ain_info.get('marginAsset')}")
    log(f"    underlyingType={ain_info.get('underlyingType')}, underlyingSubType={ain_info.get('underlyingSubType')}")
    pinfo = {"symbol": SYM, "onboardDate": ob_ms, "onboardDate_str": ob_str,
             "status": ain_info.get("status"), "contractType": ain_info.get("contractType"),
             "marginAsset": ain_info.get("marginAsset"),
             "underlyingType": ain_info.get("underlyingType"),
             "underlyingSubType": ain_info.get("underlyingSubType")}
    (SCRATCH / f"ain_perp_info_{DATE_TAG}.json").write_text(json.dumps(pinfo, indent=2), encoding="utf-8")
    log(f"  Saved: ain_perp_info_{DATE_TAG}.json")
else:
    log("  WARN: AINUSDT not found in exchangeInfo")

# BAPI alpha token list
log("\n  Fetching BAPI alpha token list for AIN...")
bapi_list = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list")
ain_bapi = {}
if "data" in bapi_list:
    # Search AIN, AINU, AI variants
    candidates = []
    for tk in bapi_list["data"]:
        sym_b = (tk.get("tokenSymbol") or "").upper()
        if sym_b in ("AIN", "AINUSDT") or sym_b.startswith("AIN"):
            candidates.append(tk)
    log(f"  BAPI candidates matching AIN*: {[t.get('tokenSymbol') for t in candidates]}")
    for tk in candidates:
        if (tk.get("tokenSymbol") or "").upper() == BASE:
            ain_bapi = tk; break
    if not ain_bapi and candidates:
        ain_bapi = candidates[0]

if ain_bapi:
    log(f"  AIN bapi: tokenSymbol={ain_bapi.get('tokenSymbol')}, name={ain_bapi.get('tokenName')}")
    log(f"    contract={ain_bapi.get('contractAddress','')[:20]}...")
    log(f"    totalSupply={ain_bapi.get('totalSupply')}, circ={ain_bapi.get('circulatingSupply')}")
    log(f"    listingTime={ain_bapi.get('listingTime')}, fullyDelisted={ain_bapi.get('fullyDelisted')}")
    (SCRATCH / f"ain_bapi_{DATE_TAG}.json").write_text(json.dumps(ain_bapi, indent=2), encoding="utf-8")
else:
    log("  WARN: AIN not found in BAPI alpha list — saving empty")
    (SCRATCH / f"ain_bapi_{DATE_TAG}.json").write_text(json.dumps({"_note": "AIN not in alpha list", "tokenSymbol": "AIN"}, indent=2), encoding="utf-8")

# AI-0b: Name disambiguation
log("\n── AI-0b. NAME DISAMBIGUATION ──")
log("  Checking for AIN / AI / AINU / AINS variants in fapi...")
variants = []
if "symbols" in exinfo:
    for s in exinfo["symbols"]:
        sym = s.get("symbol","")
        if ("AIN" in sym or sym.startswith("AI") and len(sym) <= 8) and "USDT" in sym:
            variants.append({"symbol": sym, "status": s.get("status"),
                              "underlyingSubType": s.get("underlyingSubType")})
log(f"  fapi variants: {[v['symbol'] for v in variants]}")
for v in variants:
    log(f"    {v['symbol']}: status={v['status']}, subType={v['underlyingSubType']}")

# Binance spot check
log("\n  Checking Binance spot AINUSDT...")
spot_info = fetch_json("https://api.binance.com/api/v3/exchangeInfo?symbol=AINUSDT")
has_spot = "symbols" in spot_info and len(spot_info.get("symbols", [])) > 0
log(f"  AINUSDT Binance spot: {'EXISTS' if has_spot else 'NOT FOUND'}")
if has_spot:
    s0 = spot_info["symbols"][0]
    log(f"    status={s0.get('status')}, isSpotTradingAllowed={s0.get('isSpotTradingAllowed')}")

# Gate.io
log("\n  Checking Gate.io AIN_USDT...")
gate = fetch_json("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=AIN_USDT")
if isinstance(gate, list) and gate:
    log(f"  Gate AIN_USDT: last={gate[0].get('last')}, vol24h=${float(gate[0].get('quote_volume',0)):,.0f}")
else:
    log(f"  Gate AIN_USDT: {gate}")

# CoinGecko chain search
log("\n  CoinGecko search AIN...")
cg = fetch_json("https://api.coingecko.com/api/v3/search?query=AIN")
if "_error" in cg:
    log(f"  CoinGecko error: {cg['_error']}")
else:
    coins = cg.get("coins", [])[:5]
    for c in coins:
        log(f"    {c.get('symbol','?').upper():8} {c.get('name','?')[:30]:30} id={c.get('id','?')}")

# GeckoTerminal
log("\n  GeckoTerminal search AIN...")
gt = fetch_json("https://api.geckoterminal.com/api/v2/search/pools?query=AIN")
if "_error" in gt:
    log(f"  GT error: {gt['_error']}")
else:
    pools = gt.get("data", [])[:5]
    log(f"  GT pools found: {len(gt.get('data',[]))}")
    for p in pools:
        attr = p.get("attributes", {})
        net = p.get("relationships", {}).get("network", {}).get("data", {}).get("id", "?")
        log(f"    {attr.get('name','?'):25} net={net:10} vol24=${float(attr.get('volume_usd',{}).get('h24',0) or 0):,.0f}")

# ── AI-0b: Alerts grep ────────────────────────────────────────────────────────
log("\n── AI-0c. GREP ALERTS (word-boundary AIN) ──")
agent_log = ROOT / "agent_log.md"
ain_hits = []
if agent_log.exists():
    import re
    lines = agent_log.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        if re.search(r'\bAIN\b', line.upper()):
            ain_hits.append((i+1, line.strip()[:100]))
log(f"  agent_log AIN hits: {len(ain_hits)}")
for ln, text in ain_hits[:15]:
    log(f"    L{ln}: {text}")

# gom reports
for rpt in sorted((ROOT / "docs" / "reports").glob("*gom*"))[:5]:
    try:
        import re
        txt = rpt.read_text(encoding="utf-8", errors="replace")
        hits = [l.strip()[:80] for l in txt.splitlines() if re.search(r'\bAIN\b', l)]
        if hits:
            log(f"  {rpt.name}:")
            for h in hits[:5]: log(f"    {h}")
    except: pass

# gom_state.json
gs_path = ROOT / "data" / "logs" / "gom_state.json"
if gs_path.exists():
    try:
        gs = json.loads(gs_path.read_text(encoding="utf-8"))
        log(f"  gom_state[AINUSDT]: {gs.get(SYM, 'not found')}")
    except: pass
else:
    log("  gom_state.json: not found locally (VPS canonical)")

# ── AI-1. LSR + OI PERSIST ────────────────────────────────────────────────────
log("\n── AI-1. LSR + OI PERSIST (4 endpoints + OI hist 30d) ──")
END_MS = date_to_ms("2026-08-13")

for label, endpoint, outkey in [
    ("pos", "topLongShortPositionRatio", "pos"),
    ("acc", "topLongShortAccountRatio", "acc"),
    ("glb", "globalLongShortAccountRatio", "glb"),
    ("taker", "takerlongshortRatio", "taker"),
]:
    url = f"https://fapi.binance.com/futures/data/{endpoint}?symbol={SYM}&period=1d&limit=30"
    data = fetch_json(url)
    if isinstance(data, list):
        log(f"  LSR {label}: {len(data)} rows, {ms_to_date(int(data[0]['timestamp']))} → {ms_to_date(int(data[-1]['timestamp']))}")
        (SCRATCH / f"ain_lsr_{label}_{DATE_TAG}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        log(f"  LSR {label} ERROR: {data}")

# Merge LSR into CSV
lsr_files = {
    "pos": json.loads((SCRATCH / f"ain_lsr_pos_{DATE_TAG}.json").read_text(encoding="utf-8")) if (SCRATCH / f"ain_lsr_pos_{DATE_TAG}.json").exists() else [],
    "acc": json.loads((SCRATCH / f"ain_lsr_acc_{DATE_TAG}.json").read_text(encoding="utf-8")) if (SCRATCH / f"ain_lsr_acc_{DATE_TAG}.json").exists() else [],
    "glb": json.loads((SCRATCH / f"ain_lsr_glb_{DATE_TAG}.json").read_text(encoding="utf-8")) if (SCRATCH / f"ain_lsr_glb_{DATE_TAG}.json").exists() else [],
    "taker": json.loads((SCRATCH / f"ain_lsr_taker_{DATE_TAG}.json").read_text(encoding="utf-8")) if (SCRATCH / f"ain_lsr_taker_{DATE_TAG}.json").exists() else [],
}
pos_d = {ms_to_date(int(r["timestamp"])): float(r.get("longShortRatio", 1)) for r in lsr_files["pos"]}
acc_d = {ms_to_date(int(r["timestamp"])): float(r.get("longShortRatio", 1)) for r in lsr_files["acc"]}
glb_d = {ms_to_date(int(r["timestamp"])): float(r.get("longShortRatio", 1)) for r in lsr_files["glb"]}
tk_d  = {ms_to_date(int(r["timestamp"])): float(r.get("buySellRatio", 1)) for r in lsr_files["taker"]}

all_lsr_dates = sorted(set(list(pos_d) + list(acc_d) + list(glb_d)))
lsr_csv = SCRATCH / f"ain_lsr_raw_{DATE_TAG}.csv"
with open(lsr_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","pos_r","acc_r","gLSR","taker_lsr","_src"])
    for dt in all_lsr_dates:
        if dt > L21: continue
        w.writerow([dt,
                    round(pos_d[dt], 4) if dt in pos_d else "",
                    round(acc_d[dt], 4) if dt in acc_d else "",
                    round(glb_d[dt], 4) if dt in glb_d else "",
                    round(tk_d[dt], 4) if dt in tk_d else "",
                    "fapi_LSR_30d"])
log(f"  LSR CSV: {lsr_csv.name} ({len(all_lsr_dates)} dates)")

# OI hist 30d
oi_url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=30"
oi_hist = fetch_json(oi_url)
if isinstance(oi_hist, list):
    log(f"  OI hist: {len(oi_hist)} rows, {ms_to_date(int(oi_hist[0]['timestamp']))} → {ms_to_date(int(oi_hist[-1]['timestamp']))}")
    (SCRATCH / f"ain_oi_hist_{DATE_TAG}.json").write_text(json.dumps(oi_hist, indent=2), encoding="utf-8")
else:
    log(f"  OI hist ERROR: {oi_hist}")
    oi_hist = []

oi_csv = SCRATCH / f"ain_oi_hist_{DATE_TAG}.csv"
with open(oi_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","oi_usd","oi_token","timestamp"])
    for r in oi_hist:
        dt = ms_to_date(int(r["timestamp"]))
        if dt > L21: continue
        w.writerow([dt, r.get("sumOpenInterestValue"), r.get("sumOpenInterest"), r["timestamp"]])
log(f"  OI CSV: {oi_csv.name}")

# Current OI snapshot
oi_snap = fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={SYM}")
log(f"  OI snapshot: {oi_snap}")

# AI-1 bonus: register watchlist 1h collect
watchlist_path = ROOT / "data" / "config" / "watchlist_1h.txt"
if watchlist_path.exists():
    current = watchlist_path.read_text(encoding="utf-8").strip().splitlines()
    if SYM not in current:
        current.append(SYM)
        watchlist_path.write_text("\n".join(current) + "\n", encoding="utf-8")
        log(f"  Watchlist 1h: Added {SYM} → {watchlist_path}")
    else:
        log(f"  Watchlist 1h: {SYM} already present")
else:
    log(f"  WARN: watchlist_1h.txt not found at {watchlist_path} — skip register")

# ── AI-2. KLINES + FUNDING ────────────────────────────────────────────────────
log("\n── AI-2. KLINES + FUNDING ──")

START_MS = date_to_ms("2026-01-01")
END_MS_K = date_to_ms("2026-08-13")

log("  Fetching fapi klines 1d full history...")
klines = fetch_paginated_klines(SYM, "1d", START_MS, END_MS_K)
log(f"  Klines raw: {len(klines)} rows")

perp_path = SCRATCH / f"ain_perp_{DATE_TAG}.csv"
prev_c = None
with open(perp_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","open","high","low","close","vol_quote_usd","taker_buy_pct","taker_buy_vol","ret_1d","open_ms"])
    for k in klines:
        dt = ms_to_date(int(k[0]))
        if dt > L21: continue
        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_q = float(k[7]); tb_quot = float(k[10])
        taker_pct = round(tb_quot/vol_q*100, 4) if vol_q > 0 else None
        ret_1d = round((c - prev_c)/prev_c*100, 6) if prev_c and prev_c > 0 else None
        prev_c = c
        w.writerow([dt, o, h, l, c, round(vol_q, 2), taker_pct, round(tb_quot, 2), ret_1d, k[0]])
log(f"  Perp CSV: {perp_path.name}")

rows_p = list(csv.DictReader(open(perp_path, encoding="utf-8")))
if rows_p:
    log(f"  Date range: {rows_p[0]['date']} → {rows_p[-1]['date']}")
    log(f"\n  VERIFY-TAY 5 dòng cuối:")
    log(f"  {'date':12} {'open':10} {'high':10} {'low':10} {'close':10} {'vol_q_usd':14} {'taker%':7} {'ret_1d':8}")
    for r in rows_p[-5:]:
        log(f"  {r['date']:12} {r['open']:10} {r['high']:10} {r['low']:10} "
            f"{r['close']:10} {r['vol_quote_usd']:14} {r.get('taker_buy_pct','?'):7} {r.get('ret_1d','?'):8}")

# Spot klines
log("\n  Checking Binance spot AINUSDT klines...")
spot_klines_url = f"https://api.binance.com/api/v3/klines?symbol=AINUSDT&interval=1d&startTime={START_MS}&endTime={END_MS_K}&limit=1000"
spot_data = fetch_json(spot_klines_url)
spot_path = SCRATCH / f"ain_spot_{DATE_TAG}.csv"
if isinstance(spot_data, list) and spot_data:
    log(f"  Binance spot klines: {len(spot_data)} rows")
    with open(spot_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date","open","high","low","close","vol_spot_usd","taker_spot_pct"])
        for k in spot_data:
            dt = ms_to_date(int(k[0]))
            if dt > L21: continue
            vol_q = float(k[7]); tb_quot = float(k[10]) if len(k)>10 else 0
            tpct = round(tb_quot/vol_q*100, 4) if vol_q > 0 else None
            w.writerow([dt, k[1], k[2], k[3], k[4], round(vol_q, 2), tpct])
else:
    log(f"  Binance spot AINUSDT: {spot_data}")
    with open(spot_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["date","open","high","low","close","vol_spot_usd","taker_spot_pct"])

# Funding
log("\n  Fetching funding rate full history...")
fund_raw = fetch_paginated_funding(SYM, START_MS, END_MS_K)
log(f"  Funding raw: {len(fund_raw)} entries")
fund_path = SCRATCH / f"ain_funding_{DATE_TAG}.csv"
with open(fund_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","fundingRate","fundingTime"])
    for fr in fund_raw:
        dt = ms_to_date(int(fr.get("fundingTime", 0)))
        if dt > L21: continue
        w.writerow([dt, fr.get("fundingRate"), fr.get("fundingTime")])
log(f"  Funding CSV: {fund_path.name}")

# ── AI-2. EVENTS SCAN ─────────────────────────────────────────────────────────
log("\n── AI-2. EVENTS SCAN ──")

closes = [sf(r["close"]) for r in rows_p]
vols   = [sf(r["vol_quote_usd"]) for r in rows_p]
rets   = [sf(r.get("ret_1d")) for r in rows_p]
dates  = [r["date"] for r in rows_p]
N = len(rows_p)

def med14(vals, i):
    w = [v for v in vals[max(0,i-14):i] if v is not None]
    if len(w) < 7: return None
    s = sorted(w); n = len(s)
    return (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]

# Events |ret|>10%
log(f"\n  Events |ret|>10%:")
log(f"  {'date':12} {'ret%':8} {'vol':14} {'vol_vs_m':8} {'close':10}")
events_10pct = []
for i, r in enumerate(rows_p):
    ret = sf(r.get("ret_1d"))
    if ret and abs(ret) > 10.0:
        vm = med14(vols, i); vs = vols[i]
        vvm = round(vs/vm, 2) if (vs and vm) else None
        events_10pct.append((r["date"], ret, vs, vvm, sf(r["close"])))
        log(f"  {r['date']:12} {ret:8.2f}% ${vs:>13,.0f} {str(vvm):8} {sf(r['close']):10.6f}")

# PROVEN_PUMP check: any +100% within 7 calendar days
log(f"\n  PROVEN_PUMP check (+100%/≤7d in-window pumps):")
proven_pumps = []
for i in range(N):
    if closes[i] is None: continue
    # Check rolling 7-day max gain from closes[i] to closes[i+7]
    for j in range(i+1, min(i+8, N)):
        if closes[j] is None: continue
        gain = (closes[j] - closes[i])/closes[i]*100
        if gain >= 100:
            proven_pumps.append((dates[i], dates[j], round(gain, 1), closes[i], closes[j]))
            break  # one per start
# Deduplicate by end date
seen = set()
proven_unique = []
for pp in proven_pumps:
    if pp[1] not in seen:
        proven_unique.append(pp)
        seen.add(pp[1])
if proven_unique:
    log(f"  PROVEN_PUMP: YES")
    for pp in proven_unique[:10]:
        log(f"    {pp[0]} → {pp[1]}: +{pp[2]:.1f}% (${pp[3]:.4f} → ${pp[4]:.4f})")
else:
    log(f"  PROVEN_PUMP: NO (no +100% within 7 days found)")

# Events vol>=8× med14
log(f"\n  Events vol>=8× med14:")
for i, r in enumerate(rows_p):
    vm = med14(vols, i); vs = vols[i]
    if vs and vm and vs >= 8*vm:
        ret = sf(r.get("ret_1d")); vvm = round(vs/vm, 2)
        log(f"  {r['date']:12} {vvm:6.1f}× {'?' if ret is None else f'{ret:+.2f}%':8} close={sf(r['close']):.5f}")

# ATH/ATL
valid_closes = [(dates[i], closes[i]) for i in range(N) if closes[i]]
if valid_closes:
    ath_d, ath_v = max(valid_closes, key=lambda x: x[1])
    atl_d, atl_v = min(valid_closes, key=lambda x: x[1])
    last_d, last_v = valid_closes[-1]
    log(f"\n  ATH: ${ath_v:.6f} on {ath_d}")
    log(f"  ATL: ${atl_v:.6f} on {atl_d}")
    log(f"  Latest: ${last_v:.6f} on {last_d}")
    log(f"  Drawdown from ATH: {round((last_v-ath_v)/ath_v*100,1)}%")
    # Deposit window Aug04-Aug12
    aug04_data = [(dates[i], closes[i], rets[i]) for i in range(N) if dates[i] >= "2026-08-04"]
    if aug04_data:
        aug04_c = sf(rows_p[dates.index("2026-08-04")]["close"]) if "2026-08-04" in dates else None
        log(f"\n  Cửa sổ nạp Aug04→Aug12:")
        log(f"  {'date':12} {'close':10} {'ret_1d':8}")
        for d, c, r_v in aug04_data:
            log(f"  {d:12} {c:10.5f} {str(round(r_v,2) if r_v else '?'):8}")
        if aug04_c:
            ret_cumul = (last_v - aug04_c)/aug04_c*100
            days_red = sum(1 for _,_,rv in aug04_data if rv is not None and rv < 0)
            days_grn = sum(1 for _,_,rv in aug04_data if rv is not None and rv > 0)
            log(f"\n  Cửa sổ nạp ret cộng dồn: {ret_cumul:+.1f}%")
            log(f"  Days red/green: {days_red}/{days_grn}")

# Depth snapshot
log("\n  Fetching depth...")
depth = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={SYM}&limit=20")
if "_error" not in depth and "bids" in depth:
    bids = [(float(b[0]), float(b[1])) for b in depth["bids"][:5]]
    asks = [(float(a[0]), float(a[1])) for a in depth["asks"][:5]]
    if bids and asks:
        mid = (bids[0][0] + asks[0][0])/2
        bid_2p = sum(q*p for p,q in bids if p >= mid*0.98)
        ask_2p = sum(q*p for p,q in asks if p <= mid*1.02)
        log(f"  Depth mid=${mid:.5f}")
        log(f"    Bid ±2%: ${bid_2p:,.0f}  Ask ±2%: ${ask_2p:,.0f}")
        (SCRATCH / f"ain_depth_{DATE_TAG}.json").write_text(
            json.dumps({"mid":mid,"bid_2pct_usd":bid_2p,"ask_2pct_usd":ask_2p,
                        "bids":bids,"asks":asks}, indent=2), encoding="utf-8")

# 24h ticker
ticker = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={SYM}")
if "_error" not in ticker:
    log(f"\n  24h ticker: last=${ticker.get('lastPrice')}, vol=${float(ticker.get('quoteVolume',0) or 0):,.0f}")
    log(f"    high=${ticker.get('highPrice')}, low=${ticker.get('lowPrice')}")

log("\n[DONE] AI-0/AI-1/AI-2 fetch complete")
log("Next: python build_case.py AINUSDT 20260813")

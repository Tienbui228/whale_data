"""
_probe_cys_c0c1c2_fetch_20260813.py
C-0 identity + C-1 LSR/OI persist + C-2 klines+funding CYSUSDT.
data-source : fapi.binance.com / bapi / GeckoTerminal / exchangeInfo
machine     : local
date-range  : full history → 2026-08-12 (L-21 skip hôm nay 13/08)
code-commit : TBD
"""
import sys, io, json, csv, time, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260813"
SYM  = "CYSUSDT"
BASE = "CYS"
LOWER = "cys"
TODAY_STR = "2026-08-13"
L21_CUTOFF = "2026-08-12"  # last closed day (L-21: skip today partial)

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
            log(f"  klines error at {cur}: {data['_error']}")
            break
        if not data: break
        rows.extend(data)
        if len(data) < limit: break
        cur = data[-1][0] + 1
        time.sleep(0.2)
    return rows

def fetch_paginated_funding(symbol, start_ms, end_ms, limit=1000):
    rows = []
    cur = start_ms
    while cur < end_ms:
        url = (f"https://fapi.binance.com/fapi/v1/fundingRate"
               f"?symbol={symbol}&startTime={cur}&endTime={end_ms}&limit={limit}")
        data = fetch_json(url)
        if isinstance(data, dict) and "_error" in data:
            log(f"  funding error: {data['_error']}")
            break
        if not data: break
        rows.extend(data)
        if len(data) < limit: break
        cur = data[-1]["fundingTime"] + 1
        time.sleep(0.2)
    return rows

def ms_to_date(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")

def date_to_ms(ds):
    dt = datetime.strptime(ds, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

# ─────────────────────────────────────────────────────────────────────────────
log("=" * 70)
log(f"CYS FETCH — C-0/C-1/C-2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── C-0a. ĐỊNH DANH ────────────────────────────────────────────────────────────
log("\n── C-0a. IDENTITY ──")

# fapi exchangeInfo
log("  Fetching fapi exchangeInfo for CYSUSDT...")
exinfo = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
cys_info = {}
if "symbols" in exinfo:
    for s in exinfo["symbols"]:
        if s.get("symbol") == SYM:
            cys_info = s
            break
if cys_info:
    onboard_ms = cys_info.get("onboardDate", 0) or 0
    onboard_str = ms_to_date(onboard_ms) if onboard_ms else "UNKNOWN"
    log(f"  CYSUSDT perp: onboardDate={onboard_str}, status={cys_info.get('status')}")
    log(f"    contractType={cys_info.get('contractType')}, marginAsset={cys_info.get('marginAsset')}")
    log(f"    underlyingType={cys_info.get('underlyingType')}, underlyingSubType={cys_info.get('underlyingSubType')}")
    pinfo_out = {
        "symbol": SYM,
        "onboardDate": onboard_ms,
        "onboardDate_str": onboard_str,
        "status": cys_info.get("status"),
        "contractType": cys_info.get("contractType"),
        "marginAsset": cys_info.get("marginAsset"),
        "underlyingType": cys_info.get("underlyingType"),
        "underlyingSubType": cys_info.get("underlyingSubType"),
    }
    pinfo_path = SCRATCH / f"cys_perp_info_{DATE_TAG}.json"
    pinfo_path.write_text(json.dumps(pinfo_out, indent=2), encoding="utf-8")
    log(f"  Saved: {pinfo_path.name}")
else:
    log("  WARN: CYSUSDT not found in exchangeInfo")

# BAPI Alpha token list — search for CYS
log("\n  Fetching BAPI alpha token list for CYS...")
bapi_list = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list")
cys_bapi = {}
if "data" in bapi_list:
    for tk in bapi_list["data"]:
        sym_bapi = (tk.get("tokenSymbol") or "").upper()
        if sym_bapi == BASE or sym_bapi == SYM:
            cys_bapi = tk
            break
if cys_bapi:
    log(f"  CYS bapi: tokenSymbol={cys_bapi.get('tokenSymbol')}")
    log(f"    name={cys_bapi.get('tokenName')}")
    log(f"    contractAddress={cys_bapi.get('contractAddress','')[:20]}...")
    log(f"    totalSupply={cys_bapi.get('totalSupply')}, circ={cys_bapi.get('circulatingSupply')}")
    log(f"    listingTime={cys_bapi.get('listingTime')}, fullyDelisted={cys_bapi.get('fullyDelisted')}")
    bapi_path = SCRATCH / f"cys_bapi_{DATE_TAG}.json"
    bapi_path.write_text(json.dumps(cys_bapi, indent=2), encoding="utf-8")
    log(f"  Saved: {bapi_path.name}")
else:
    log("  WARN: CYS not found in BAPI alpha list — saving empty")
    bapi_path = SCRATCH / f"cys_bapi_{DATE_TAG}.json"
    bapi_path.write_text(json.dumps({"_note": "CYS not in alpha list", "tokenSymbol": "CYS"}, indent=2), encoding="utf-8")

# Binance spot — check CYSUSDT pair
log("\n  Checking Binance spot for CYSUSDT...")
spot_info = fetch_json("https://api.binance.com/api/v3/exchangeInfo?symbol=CYSUSDT")
has_cys_spot = "symbols" in spot_info and len(spot_info.get("symbols", [])) > 0
log(f"  CYSUSDT Binance spot: {'EXISTS' if has_cys_spot else 'NOT FOUND'}")
if has_cys_spot:
    s0 = spot_info["symbols"][0]
    log(f"    status={s0.get('status')}, isSpotTradingAllowed={s0.get('isSpotTradingAllowed')}")

# Gate.io spot check
log("  Checking Gate.io CYSUSDT...")
gate = fetch_json("https://api.gateio.ws/api/v4/spot/tickers?currency_pair=CYS_USDT")
if isinstance(gate, list) and gate:
    log(f"  Gate CYS_USDT: last={gate[0].get('last')}, vol24h={gate[0].get('quote_volume')}")
else:
    log(f"  Gate CYS_USDT: {gate}")

# GeckoTerminal — search CYS
log("  GeckoTerminal search CYS...")
gecko = fetch_json("https://api.geckoterminal.com/api/v2/search/pools?query=CYS&network=solana")
if "_error" in gecko:
    log(f"  GeckoTerminal error: {gecko['_error']}")
else:
    pools = gecko.get("data", [])
    log(f"  GeckoTerminal Solana pools: {len(pools)}")
    for p in pools[:3]:
        attr = p.get("attributes", {})
        log(f"    {attr.get('name','?')} addr={attr.get('address','?')[:12]}... vol24={attr.get('volume_usd',{}).get('h24','?')}")

# ── C-0b. GREP ALERTS ─────────────────────────────────────────────────────────
log("\n── C-0b. GREP ALERTS ──")
# Search agent_log.md for CYS mentions
agent_log = ROOT / "agent_log.md"
cys_log_hits = []
if agent_log.exists():
    lines = agent_log.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        if "CYS" in line.upper() and ("alert" in line.lower() or "gom" in line.lower() or "fire" in line.lower() or "Q1" in line.lower()):
            cys_log_hits.append((i+1, line.strip()[:120]))
log(f"  agent_log CYS alert/gom hits: {len(cys_log_hits)}")
for ln, text in cys_log_hits[:10]:
    log(f"    L{ln}: {text}")

# Search gom_scan output files
gom_reports = list((ROOT / "docs" / "reports").glob("*gom*"))
cys_gom_hits = []
for rpt in gom_reports:
    try:
        txt = rpt.read_text(encoding="utf-8", errors="replace")
        if "CYS" in txt.upper():
            for ln, line in enumerate(txt.splitlines(), 1):
                if "CYS" in line.upper():
                    cys_gom_hits.append((rpt.name, ln, line.strip()[:100]))
    except: pass
log(f"  gom_scan report CYS hits: {len(cys_gom_hits)}")
for fname, ln, text in cys_gom_hits[:10]:
    log(f"    {fname}:{ln}: {text}")

# Search gom_state.json
gom_state = ROOT / "data" / "logs" / "gom_state.json"
if gom_state.exists():
    try:
        gs = json.loads(gom_state.read_text(encoding="utf-8"))
        cys_state = gs.get(SYM, {})
        log(f"  gom_state.json CYS: {cys_state}")
    except Exception as e:
        log(f"  gom_state.json read error: {e}")
else:
    log("  gom_state.json not found locally (VPS canonical)")

# Check triage report
triage_path = ROOT / "docs" / "reports" / "gom_c_triage_20260808.txt"
if triage_path.exists():
    txt = triage_path.read_text(encoding="utf-8", errors="replace")
    cys_lines = [l.strip() for l in txt.splitlines() if "CYS" in l.upper()]
    log(f"  gom_c_triage_20260808.txt CYS lines: {len(cys_lines)}")
    for l in cys_lines[:10]:
        log(f"    {l}")

# ── C-1. LSR + OI PERSIST (4 endpoints + OI hist 30d) ─────────────────────────
log("\n── C-1. LSR + OI PERSIST ──")
END_MS = date_to_ms("2026-08-13")  # exclusive end

# C-1a. LSR Position Ratio (pos/short ratio per account)
log("  Fetching LSR pos ratio (topLongShortPositionRatio)...")
lsr_pos_url = (f"https://fapi.binance.com/futures/data/topLongShortPositionRatio"
               f"?symbol={SYM}&period=1d&limit=30")
lsr_pos = fetch_json(lsr_pos_url)
if isinstance(lsr_pos, list):
    log(f"  LSR pos: {len(lsr_pos)} rows, from {ms_to_date(int(lsr_pos[0]['timestamp']))} to {ms_to_date(int(lsr_pos[-1]['timestamp']))}")
elif "_error" in lsr_pos:
    log(f"  LSR pos ERROR: {lsr_pos['_error']}")
    lsr_pos = []
else:
    log(f"  LSR pos unexpected: {lsr_pos}")
    lsr_pos = []

# C-1b. LSR Account Ratio (acc ratio)
log("  Fetching LSR acc ratio (topLongShortAccountRatio)...")
lsr_acc_url = (f"https://fapi.binance.com/futures/data/topLongShortAccountRatio"
               f"?symbol={SYM}&period=1d&limit=30")
lsr_acc = fetch_json(lsr_acc_url)
if isinstance(lsr_acc, list):
    log(f"  LSR acc: {len(lsr_acc)} rows, from {ms_to_date(int(lsr_acc[0]['timestamp']))} to {ms_to_date(int(lsr_acc[-1]['timestamp']))}")
elif "_error" in lsr_acc:
    log(f"  LSR acc ERROR: {lsr_acc['_error']}")
    lsr_acc = []
else:
    lsr_acc = []

# C-1c. Global LSR
log("  Fetching global LSR (globalLongShortAccountRatio)...")
lsr_glb_url = (f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
               f"?symbol={SYM}&period=1d&limit=30")
lsr_glb = fetch_json(lsr_glb_url)
if isinstance(lsr_glb, list):
    log(f"  LSR global: {len(lsr_glb)} rows, from {ms_to_date(int(lsr_glb[0]['timestamp']))} to {ms_to_date(int(lsr_glb[-1]['timestamp']))}")
elif "_error" in lsr_glb:
    log(f"  LSR global ERROR: {lsr_glb['_error']}")
    lsr_glb = []
else:
    lsr_glb = []

# C-1d. Taker Buy/Sell Vol ratio
log("  Fetching taker buy/sell ratio (takerlongshortRatio)...")
taker_url = (f"https://fapi.binance.com/futures/data/takerlongshortRatio"
             f"?symbol={SYM}&period=1d&limit=30")
taker_lsr_raw = fetch_json(taker_url)
if isinstance(taker_lsr_raw, list):
    log(f"  Taker ratio: {len(taker_lsr_raw)} rows")
elif "_error" in taker_lsr_raw:
    log(f"  Taker ERROR: {taker_lsr_raw['_error']}")
    taker_lsr_raw = []
else:
    taker_lsr_raw = []

# Merge into lsr_raw CSV — parse loop
lsr_pos_d = {}
for r in lsr_pos:
    dt = ms_to_date(int(r["timestamp"]))
    # topLongShortPositionRatio returns longShortRatio = long/short
    ratio = float(r.get("longShortRatio", 0))
    lsr_pos_d[dt] = ratio

lsr_acc_d = {}
for r in lsr_acc:
    dt = ms_to_date(int(r["timestamp"]))
    ratio = float(r.get("longShortRatio", 0))
    lsr_acc_d[dt] = ratio

lsr_glb_d = {}
for r in lsr_glb:
    dt = ms_to_date(int(r["timestamp"]))
    ratio = float(r.get("longShortRatio", 0))
    lsr_glb_d[dt] = ratio

taker_d = {}
for r in taker_lsr_raw:
    dt = ms_to_date(int(r["timestamp"]))
    taker_d[dt] = float(r.get("buySellRatio", 1))

all_lsr_dates = sorted(set(list(lsr_pos_d) + list(lsr_acc_d) + list(lsr_glb_d)))
lsr_raw_path = SCRATCH / f"cys_lsr_raw_{DATE_TAG}.csv"
with open(lsr_raw_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","pos_r","acc_r","gLSR","taker_lsr","_src"])
    for dt in all_lsr_dates:
        if dt > L21_CUTOFF: continue
        w.writerow([dt,
                    round(lsr_pos_d.get(dt, float("nan")), 4) if dt in lsr_pos_d else "",
                    round(lsr_acc_d.get(dt, float("nan")), 4) if dt in lsr_acc_d else "",
                    round(lsr_glb_d.get(dt, float("nan")), 4) if dt in lsr_glb_d else "",
                    round(taker_d.get(dt, float("nan")), 4) if dt in taker_d else "",
                    "fapi_LSR_30d"])
log(f"  LSR CSV saved: {lsr_raw_path.name} ({len(all_lsr_dates)} dates)")

# C-1e. OI hist 30d
log("\n  Fetching OI hist (30d)...")
oi_hist_url = (f"https://fapi.binance.com/futures/data/openInterestHist"
               f"?symbol={SYM}&period=1d&limit=30")
oi_hist = fetch_json(oi_hist_url)
if isinstance(oi_hist, list):
    log(f"  OI hist: {len(oi_hist)} rows, {ms_to_date(int(oi_hist[0]['timestamp']))} → {ms_to_date(int(oi_hist[-1]['timestamp']))}")
elif "_error" in oi_hist:
    log(f"  OI hist ERROR: {oi_hist['_error']}")
    oi_hist = []
else:
    oi_hist = []

oi_raw_path = SCRATCH / f"cys_oi_hist_{DATE_TAG}.csv"
with open(oi_raw_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","oi_usd","oi_token","timestamp"])
    for r in oi_hist:
        dt = ms_to_date(int(r["timestamp"]))
        if dt > L21_CUTOFF: continue
        w.writerow([dt, r.get("sumOpenInterestValue"), r.get("sumOpenInterest"), r["timestamp"]])
log(f"  OI CSV saved: {oi_raw_path.name}")

# Also save raw JSONs
(SCRATCH / f"cys_lsr_pos_{DATE_TAG}.json").write_text(json.dumps(lsr_pos, indent=2), encoding="utf-8")
(SCRATCH / f"cys_lsr_acc_{DATE_TAG}.json").write_text(json.dumps(lsr_acc, indent=2), encoding="utf-8")
(SCRATCH / f"cys_lsr_glb_{DATE_TAG}.json").write_text(json.dumps(lsr_glb, indent=2), encoding="utf-8")
(SCRATCH / f"cys_oi_hist_{DATE_TAG}.json").write_text(json.dumps(oi_hist, indent=2), encoding="utf-8")
log(f"  Raw JSONs saved: lsr_pos/acc/glb/oi_hist")

# ── C-2. KLINES + FUNDING ─────────────────────────────────────────────────────
log("\n── C-2. KLINES + FUNDING ──")

# C-2a. Perp klines 1d — full history
log("  Fetching fapi klines 1d full history...")
# CYS listed ~Jun01 based on store; use Jan01 2026 as safe start
START_MS = date_to_ms("2026-01-01")
END_MS_K = date_to_ms("2026-08-13")  # exclusive

klines_raw = fetch_paginated_klines(SYM, "1d", START_MS, END_MS_K)
log(f"  Klines raw: {len(klines_raw)} rows")

# Build perp CSV
perp_path = SCRATCH / f"cys_perp_{DATE_TAG}.csv"
with open(perp_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","open","high","low","close","vol_quote_usd","taker_buy_pct","taker_buy_vol","ret_1d","open_ms"])
    prev_close = None
    for k in klines_raw:
        dt = ms_to_date(int(k[0]))
        if dt > L21_CUTOFF: continue
        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_q = float(k[7])  # quote asset volume
        tb_vol = float(k[9]) # taker buy base vol
        tb_quot = float(k[10]) # taker buy quote vol
        total_vol = float(k[5])
        taker_pct = round(float(tb_quot)/vol_q*100, 4) if vol_q > 0 else None
        ret_1d = round((c - prev_close)/prev_close*100, 6) if prev_close and prev_close > 0 else None
        prev_close = c
        w.writerow([dt, o, h, l, c, round(vol_q, 2), taker_pct, round(tb_quot, 2), ret_1d, k[0]])
log(f"  Perp CSV saved: {perp_path.name} ({len(klines_raw)} rows)")

# Verify: show last 5 rows
klines_dates = []
with open(perp_path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
klines_dates = [r["date"] for r in rows]
log(f"  Date range: {klines_dates[0] if klines_dates else '?'} → {klines_dates[-1] if klines_dates else '?'}")
log(f"\n  VERIFY-TAY 5 dòng cuối:")
log(f"  {'date':12} {'open':10} {'high':10} {'low':10} {'close':10} {'vol_q_usd':14} {'taker%':7} {'ret_1d':8}")
for r in rows[-5:]:
    log(f"  {r['date']:12} {r['open']:10} {r['high']:10} {r['low']:10} "
        f"{r['close']:10} {r['vol_quote_usd']:14} {r.get('taker_buy_pct','?'):7} {r.get('ret_1d','?'):8}")

# C-2b. Spot klines (Binance spot CYSUSDT if exists)
log("\n  Fetching Binance spot klines CYSUSDT...")
spot_klines = []
try:
    spot_url = (f"https://api.binance.com/api/v3/klines"
                f"?symbol=CYSUSDT&interval=1d&startTime={START_MS}&endTime={END_MS_K}&limit=1000")
    spot_data = fetch_json(spot_url)
    if isinstance(spot_data, list):
        spot_klines = spot_data
        log(f"  Binance spot klines: {len(spot_klines)} rows")
    else:
        log(f"  Binance spot: {spot_data}")
except Exception as e:
    log(f"  Binance spot error: {e}")

spot_path = SCRATCH / f"cys_spot_{DATE_TAG}.csv"
if spot_klines:
    with open(spot_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date","open","high","low","close","vol_spot_usd","taker_spot_pct"])
        for k in spot_klines:
            dt = ms_to_date(int(k[0]))
            if dt > L21_CUTOFF: continue
            vol_q = float(k[7])
            tb_quot = float(k[10]) if len(k) > 10 else 0
            taker_pct = round(tb_quot/vol_q*100, 4) if vol_q > 0 else None
            w.writerow([dt, k[1], k[2], k[3], k[4], round(vol_q, 2), taker_pct])
    log(f"  Spot CSV saved: {spot_path.name}")
else:
    # empty CSV
    with open(spot_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["date","open","high","low","close","vol_spot_usd","taker_spot_pct"])
    log(f"  Spot CSV empty (no Binance spot): {spot_path.name}")

# C-2c. Funding — full history
log("\n  Fetching fapi funding rate full history...")
FUND_START_MS = date_to_ms("2026-01-01")
fund_raw = fetch_paginated_funding(SYM, FUND_START_MS, END_MS_K)
log(f"  Funding raw: {len(fund_raw)} entries")

fund_path = SCRATCH / f"cys_funding_{DATE_TAG}.csv"
with open(fund_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date","fundingRate","fundingTime"])
    for fr in fund_raw:
        dt = ms_to_date(int(fr.get("fundingTime", fr.get("time", 0))))
        if dt > L21_CUTOFF: continue
        w.writerow([dt, fr.get("fundingRate"), fr.get("fundingTime")])
log(f"  Funding CSV saved: {fund_path.name}")

# C-2d. Current OI snapshot
log("\n  Fetching current OI snapshot...")
oi_snap = fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={SYM}")
log(f"  OI snapshot: {oi_snap}")

# C-2e. Current ticker (depth/price)
ticker = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={SYM}")
if "_error" not in ticker:
    log(f"\n  24h ticker: last={ticker.get('lastPrice')}, vol={ticker.get('quoteVolume')}")
    log(f"    high={ticker.get('highPrice')}, low={ticker.get('lowPrice')}")
    log(f"    fundingRate={ticker.get('lastFundingRate')}, nextFundingTime={ticker.get('nextFundingTime')}")

# Depth ±2%
log("\n  Fetching depth (limit=20)...")
depth = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={SYM}&limit=20")
if "_error" not in depth and "bids" in depth:
    bids = [(float(b[0]), float(b[1])) for b in depth["bids"][:5]]
    asks = [(float(a[0]), float(a[1])) for a in depth["asks"][:5]]
    if bids:
        mid = (bids[0][0] + asks[0][0]) / 2
        bid_2pct = sum(q*p for p,q in bids if p >= mid*0.98)
        ask_2pct = sum(q*p for p,q in asks if p <= mid*1.02)
        log(f"  Depth mid={mid:.4f}")
        log(f"    Bid ±2% depth: ${bid_2pct:,.0f}")
        log(f"    Ask ±2% depth: ${ask_2pct:,.0f}")
        depth_snap = {"mid": mid, "bid_2pct_usd": bid_2pct, "ask_2pct_usd": ask_2pct,
                      "bids": bids, "asks": asks, "timestamp": datetime.now(timezone.utc).isoformat()}
        (SCRATCH / f"cys_depth_{DATE_TAG}.json").write_text(json.dumps(depth_snap, indent=2), encoding="utf-8")

# C-2f. Events scan — |ret|>10% and vol>=8× med14
log("\n── C-2. EVENTS SCAN ──")
perp_rows = list(csv.DictReader(open(perp_path, encoding="utf-8")))

def safe_f(v, d=None):
    try: return float(v) if v not in (None, "", "None", "nan") else d
    except: return d

closes = [safe_f(r["close"]) for r in perp_rows]
vols   = [safe_f(r["vol_quote_usd"]) for r in perp_rows]
rets   = [safe_f(r.get("ret_1d")) for r in perp_rows]

# rolling med14
def med14(vals, i):
    w = [v for v in vals[max(0,i-14):i] if v is not None]
    if len(w) < 7: return None
    s = sorted(w)
    n = len(s)
    return (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]

log(f"\n  Events |ret|>10%:")
log(f"  {'date':12} {'ret%':8} {'vol':14} {'vol_vs_m':8} {'close':10}")
events_ret10 = []
for i, r in enumerate(perp_rows):
    ret = safe_f(r.get("ret_1d"))
    if ret is None: continue
    if abs(ret) > 10.0:
        vm = med14(vols, i)
        vs = vols[i]
        vvm = round(vs/vm, 2) if (vs and vm) else None
        events_ret10.append((r["date"], ret, vs, vvm, safe_f(r["close"])))
        log(f"  {r['date']:12} {ret:8.2f}% ${vs:>13,.0f} {str(vvm):8} {safe_f(r['close']):10.6f}")

log(f"\n  Events vol>=8× med14 (with ret):")
events_vol8x = []
for i, r in enumerate(perp_rows):
    vm = med14(vols, i)
    vs = vols[i]
    if vs and vm and vs >= 8*vm:
        ret = safe_f(r.get("ret_1d"))
        vvm = round(vs/vm, 2)
        events_vol8x.append((r["date"], vvm, ret, safe_f(r["close"])))
        log(f"  {r['date']:12} {vvm:6.1f}× {'?' if ret is None else f'{ret:+.2f}%':8} {safe_f(r['close']):10.6f}")

# ATH + drawdown
valid_closes = [(r["date"], safe_f(r["close"])) for r in perp_rows if safe_f(r["close"])]
if valid_closes:
    ath_date, ath_px = max(valid_closes, key=lambda x: x[1])
    last_date, last_px = valid_closes[-1]
    dd = round((last_px - ath_px)/ath_px*100, 2)
    log(f"\n  ATH: {ath_px:.6f} on {ath_date}")
    log(f"  Latest: {last_px:.6f} on {last_date}")
    log(f"  Drawdown from ATH: {dd}%")

# Pump cluster summary
log("\n  Pump cluster summary (|ret|>10%):")
for dt, ret, vol, vvm, c in events_ret10:
    marker = "PUMP" if ret > 0 else "DUMP"
    log(f"    {dt}: {marker} {ret:+.1f}% vol=${vol:,.0f} ({vvm}× med14) c={c:.5f}")

log("\n[DONE] C-0/C-1/C-2 fetch complete. Check scratch/ for CSVs + JSONs.")
log("Next step: build_case.py CYSUSDT 20260813")

"""
_probe_cookie_c2_collect_20260809.py
COOKIE C-2: Collect perp klines + funding + OI + spot + BAPI + perp_info
"""
import sys, io, json, csv, urllib.request, urllib.parse, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"
SYM_PERP = "COOKIEUSDT"
SYM_BASE = "COOKIE"
ALPHA_ID = "ALPHA_33"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-2 COLLECT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR fetching {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"
API  = "https://api.binance.com"

# ── 1. Perp klines (1d, trọn đời) ────────────────────────────────────────────
log("\n=== perp klines 1d (full history) ===")
all_klines = []
end_ms = int(NOW.timestamp() * 1000)
# Fetch back 1000 bars at a time
while True:
    url = f"{FAPI}/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1000&endTime={end_ms}"
    data = fetch_json(url)
    if not data:
        break
    # Filter: only complete candles (openTime < today 00:00 UTC)
    today_start = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    today_ms = int(today_start.timestamp() * 1000)
    complete = [k for k in data if int(k[0]) < today_ms]
    all_klines = complete + all_klines
    if len(data) < 1000 or int(data[0][0]) <= 0:
        break
    end_ms = int(data[0][0]) - 1
    time.sleep(0.1)

# Dedup by open time
seen = set()
deduped = []
for k in all_klines:
    if k[0] not in seen:
        seen.add(k[0])
        deduped.append(k)
deduped.sort(key=lambda x: x[0])

log(f"  Raw klines: {len(deduped)} rows")
if deduped:
    d0 = datetime.fromtimestamp(int(deduped[0][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(deduped[-1][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    # Save JSON
    out = SCRATCH / f"cookie_perp_klines_{DATE_TAG}.json"
    out.write_text(json.dumps(deduped), encoding="utf-8")
    log(f"  Saved JSON: {out.name}")

    # Convert to CSV
    rows = []
    for k in deduped:
        dt = datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        o,h,l,c = float(k[1]),float(k[2]),float(k[3]),float(k[4])
        vol_q = float(k[7])  # quote volume
        taker_q = float(k[10])  # taker buy quote vol
        taker_pct = taker_q/vol_q if vol_q > 0 else None
        rows.append({"date":dt,"open":o,"high":h,"low":l,"close":c,
                     "vol_quote_usd":vol_q,"taker_pct":taker_pct})
    out_csv = SCRATCH / f"cookie_perp_{DATE_TAG}.csv"
    with open(out_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","open","high","low","close","vol_quote_usd","taker_pct"])
        w.writeheader()
        w.writerows(rows)
    log(f"  Saved CSV: {out_csv.name} ({out_csv.stat().st_size:,} bytes)")
    # Show last 5
    log("  Last 5 rows:")
    for r in rows[-5:]:
        log(f"    {r['date']} c={r['close']:.6f} vol=${r['vol_quote_usd']:,.0f} taker={r.get('taker_pct',0):.2%}")

# ── 2. Funding rate (full history) ────────────────────────────────────────────
log("\n=== funding history ===")
fund_all = []
end_ms2 = int(NOW.timestamp() * 1000)
for _ in range(20):
    url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM_PERP}&limit=1000&endTime={end_ms2}"
    data = fetch_json(url)
    if not data:
        break
    fund_all = data + fund_all
    if len(data) < 1000:
        break
    end_ms2 = int(data[0]["fundingTime"]) - 1
    time.sleep(0.1)

# Dedup
seen_f = set()
fund_deduped = []
for r in fund_all:
    k = r["fundingTime"]
    if k not in seen_f:
        seen_f.add(k)
        fund_deduped.append(r)
fund_deduped.sort(key=lambda x: x["fundingTime"])
log(f"  Records: {len(fund_deduped)}")
if fund_deduped:
    d0 = datetime.fromtimestamp(int(fund_deduped[0]["fundingTime"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(fund_deduped[-1]["fundingTime"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    rates = [float(r["fundingRate"]) for r in fund_deduped]
    log(f"  min={min(rates):.6f}  max={max(rates):.6f}  neg_count={sum(1 for r in rates if r<0)}")
    out = SCRATCH / f"cookie_funding_{DATE_TAG}.json"
    out.write_text(json.dumps(fund_deduped), encoding="utf-8")
    log(f"  Saved: {out.name}")

# ── 3. OI hist (30d) ─────────────────────────────────────────────────────────
log("\n=== OI historical 30d ===")
url = f"{FAPI}/futures/data/openInterestHist?symbol={SYM_PERP}&period=1d&limit=30"
oi_data = fetch_json(url)
if oi_data:
    log(f"  Records: {len(oi_data)}")
    d0 = datetime.fromtimestamp(int(oi_data[0]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(oi_data[-1]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    log(f"  First OI: ${float(oi_data[0].get('sumOpenInterestValue',0)):,.0f}")
    log(f"  Last OI:  ${float(oi_data[-1].get('sumOpenInterestValue',0)):,.0f}")
    out = SCRATCH / f"cookie_oi_hist_{DATE_TAG}.json"
    out.write_text(json.dumps(oi_data), encoding="utf-8")
    log(f"  Saved: {out.name}")

# ── 4. Spot klines ────────────────────────────────────────────────────────────
log("\n=== spot klines (COOKIEUSDT) ===")
url = f"{API}/api/v3/klines?symbol={SYM_PERP}&interval=1d&limit=1000"
spot_data = fetch_json(url)
if spot_data:
    today_ms = int(datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()*1000)
    spot_complete = [k for k in spot_data if int(k[0]) < today_ms]
    log(f"  Spot rows: {len(spot_complete)}")
    if spot_complete:
        d0 = datetime.fromtimestamp(int(spot_complete[0][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        d1 = datetime.fromtimestamp(int(spot_complete[-1][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Range: {d0} → {d1}")
        spot_rows = []
        for k in spot_complete:
            dt = datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
            vol_q = float(k[7])
            taker_q = float(k[10])
            taker_pct = taker_q/vol_q if vol_q > 0 else None
            spot_rows.append({"date":dt,"open":float(k[1]),"high":float(k[2]),"low":float(k[3]),"close":float(k[4]),
                               "vol_quote_usd":vol_q,"taker_pct":taker_pct})
        out = SCRATCH / f"cookie_spot_{DATE_TAG}.csv"
        with open(out,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date","open","high","low","close","vol_quote_usd","taker_pct"])
            w.writeheader()
            w.writerows(spot_rows)
        log(f"  Saved: {out.name} ({out.stat().st_size:,} bytes)")
        log(f"  Last 3 rows:")
        for r in spot_rows[-3:]:
            log(f"    {r['date']} c={r['close']:.6f} vol=${r['vol_quote_usd']:,.0f} taker={r.get('taker_pct',0):.2%}")
else:
    log("  ERROR or no spot pair")

# ── 5. BAPI token info ────────────────────────────────────────────────────────
log("\n=== BAPI token info ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
if bapi_data:
    raw = bapi_data.get("data", [])
    if isinstance(raw, list):
        token_list = raw
    else:
        token_list = raw.get("tokenList", raw.get("list", []))
    cookie_tok = None
    for t in token_list:
        aid = t.get("alphaId","")
        sym = t.get("tokenSymbol","")
        if aid == ALPHA_ID or sym.upper() == SYM_BASE:
            cookie_tok = t
            break
    if cookie_tok:
        log(f"  alphaId:         {cookie_tok.get('alphaId')}")
        log(f"  tokenSymbol:     {cookie_tok.get('tokenSymbol')}")
        log(f"  contractAddress: {cookie_tok.get('contractAddress')}")
        log(f"  totalSupply:     {cookie_tok.get('totalSupply')}")
        log(f"  holders:         {cookie_tok.get('holders')}")
        log(f"  fullyDelisted:   {cookie_tok.get('fullyDelisted')}")
        log(f"  offsell:         {cookie_tok.get('offsell')}")
        log(f"  offline:         {cookie_tok.get('offline')}")
        log(f"  listingTime:     {cookie_tok.get('listingTime')}")
        out = SCRATCH / f"cookie_bapi_{DATE_TAG}.json"
        out.write_text(json.dumps(cookie_tok, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"  Saved: {out.name}")
    else:
        log(f"  COOKIE (ALPHA_33) not found in BAPI list ({len(token_list)} tokens total)")

# ── 6. FAPI perp info ────────────────────────────────────────────────────────
log("\n=== FAPI perp info ===")
url = f"{FAPI}/fapi/v1/exchangeInfo"
info = fetch_json(url)
if info:
    syms = {s["symbol"]: s for s in info.get("symbols",[])}
    si = syms.get(SYM_PERP, {})
    if si:
        log(f"  status:      {si.get('status')}")
        log(f"  onboardDate: {si.get('onboardDate')}")
        if si.get("onboardDate"):
            onb = datetime.fromtimestamp(int(si["onboardDate"])/1000,tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            log(f"  onboard:     {onb}")
        log(f"  deliveryDate:{si.get('deliveryDate')}")
        log(f"  marginType:  {si.get('marginType')}")
        out = SCRATCH / f"cookie_perp_info_{DATE_TAG}.json"
        out.write_text(json.dumps(si, indent=2), encoding="utf-8")
        log(f"  Saved: {out.name}")
    else:
        log(f"  {SYM_PERP} not found in exchangeInfo")

log(f"\n[C-2 COLLECT DONE]")

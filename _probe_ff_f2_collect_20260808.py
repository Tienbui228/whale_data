"""
_probe_ff_f2_collect_20260808.py
F-2: Klines trọn đời + funding + OI hist 30d + spot + alpha.
"""
import sys, io, json, csv, urllib.request, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-2 COLLECT  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

SYM_PERP = "FFUSDT"
SYM_SPOT = "FFUSDT"  # no spot pair expected
BASE_FAPI = "https://fapi.binance.com"
BASE_API  = "https://api.binance.com"

def safe_get(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

# ── Perp exchange info ───────────────────────────────────────────────────────
log("\n=== PERP EXCHANGE INFO ===")
ei, err = safe_get(f"{BASE_FAPI}/fapi/v1/exchangeInfo")
ff_info = None
if ei:
    for s in ei.get("symbols", []):
        if s.get("symbol") == SYM_PERP:
            ff_info = s
            break
if ff_info:
    onboard_ms = ff_info.get("onboardDate", 0)
    onboard_dt = datetime.utcfromtimestamp(onboard_ms/1000).strftime("%Y-%m-%d") if onboard_ms else "?"
    log(f"  Symbol:       {ff_info['symbol']}")
    log(f"  Status:       {ff_info.get('status')}")
    log(f"  contractType: {ff_info.get('contractType')}")
    log(f"  onboardDate:  {onboard_dt}")
    log(f"  pricePrecision: {ff_info.get('pricePrecision')}")
    log(f"  quantityPrecision: {ff_info.get('quantityPrecision')}")
    ei_path = SCRATCH / f"ff_perp_info_{DATE_TAG}.json"
    ei_path.write_text(json.dumps(ff_info, indent=2), encoding="utf-8")
    log(f"  Saved: {ei_path.name}")
else:
    log(f"  ERROR: {err}")
    onboard_dt = "2026-01-01"  # fallback estimate

# ── Perp klines (trọn đời) ───────────────────────────────────────────────────
log("\n=== PERP KLINES 1D (ALL TIME) ===")
# Fetch in batches (limit 1500 per call)
all_klines = []
end_ms = int(NOW_UTC.timestamp() * 1000)
start_ms = 0  # from listing

# Two-pass: first without start to get earliest
url_first = f"{BASE_FAPI}/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1500&endTime={end_ms}"
kl, err = safe_get(url_first)
if err:
    log(f"  ERROR: {err}")
else:
    log(f"  Batch: {len(kl)} candles from {datetime.utcfromtimestamp(kl[0][0]/1000).strftime('%Y-%m-%d') if kl else '?'}")
    all_klines = kl

# If 1500 rows, need more batches (unlikely for FF which listed recently)
if len(all_klines) == 1500:
    # Need earlier data
    more_end = all_klines[0][0] - 1
    url_more = f"{BASE_FAPI}/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1500&endTime={more_end}"
    kl2, _ = safe_get(url_more)
    if kl2:
        all_klines = kl2 + all_klines
        log(f"  Extended: {len(all_klines)} total candles")

# L-21: trim today (partial)
today_str = NOW_UTC.strftime("%Y-%m-%d")
raw_klines = []
for k in all_klines:
    dt_str = datetime.utcfromtimestamp(k[0]/1000).strftime("%Y-%m-%d")
    if dt_str >= today_str:
        continue
    raw_klines.append({
        "date": dt_str,
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "vol_perp_usd": float(k[7]),   # quote vol
        "taker_buy_pct": float(k[9])/float(k[7]) if float(k[7])>0 else float("nan"),
        "n_trades": int(k[8]),
    })

log(f"  After L-21 trim: {len(raw_klines)} rows")
if raw_klines:
    log(f"  Range: {raw_klines[0]['date']} → {raw_klines[-1]['date']}")
    log(f"  Latest close: {raw_klines[-1]['close']:.8f}")
    log(f"  ATH: {max(r['high'] for r in raw_klines):.8f}")
    log(f"  ATL: {min(r['low'] for r in raw_klines):.8f}")

kl_path = SCRATCH / f"ff_perp_klines_{DATE_TAG}.json"
kl_path.write_text(json.dumps({r["date"]: r for r in raw_klines}, indent=2), encoding="utf-8")
log(f"  Saved: {kl_path.name}")

# CSV version
csv_path = SCRATCH / f"ff_perp_{DATE_TAG}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    if raw_klines:
        w = csv.DictWriter(f, fieldnames=raw_klines[0].keys())
        w.writeheader(); w.writerows(raw_klines)
log(f"  Saved: {csv_path.name}")

# ── Funding (trọn đời) ───────────────────────────────────────────────────────
log("\n=== FUNDING (ALL TIME) ===")
all_funding = []
end_ms_f = int(NOW_UTC.timestamp() * 1000)
while True:
    url_f = f"{BASE_FAPI}/fapi/v1/fundingRate?symbol={SYM_PERP}&limit=1000&endTime={end_ms_f}"
    fdata, err = safe_get(url_f)
    if err or not fdata:
        log(f"  Batch error: {err}"); break
    all_funding = fdata + all_funding
    if len(fdata) < 1000:
        break
    end_ms_f = fdata[0]["fundingTime"] - 1

log(f"  Total funding records: {len(all_funding)}")
if all_funding:
    rates = [float(r["fundingRate"]) for r in all_funding]
    log(f"  Range: {datetime.utcfromtimestamp(all_funding[0]['fundingTime']/1000).strftime('%Y-%m-%d')} → {datetime.utcfromtimestamp(all_funding[-1]['fundingTime']/1000).strftime('%Y-%m-%d')}")
    log(f"  Min rate: {min(rates):.6f}  Max: {max(rates):.6f}  Mean: {sum(rates)/len(rates):.6f}")
    neg = sum(1 for r in rates if r < 0)
    log(f"  Negative records: {neg}/{len(rates)} ({neg/len(rates)*100:.1f}%)")

fund_path = SCRATCH / f"ff_funding_{DATE_TAG}.json"
fund_path.write_text(json.dumps(all_funding, indent=2), encoding="utf-8")
log(f"  Saved: {fund_path.name}")

# ── OI hist 30d ──────────────────────────────────────────────────────────────
log("\n=== OI HIST (30d, 1d) ===")
url_oi = f"{BASE_FAPI}/futures/data/openInterestHist?symbol={SYM_PERP}&period=1d&limit=30"
oi_data, err = safe_get(url_oi)
if err:
    log(f"  ERROR: {err}")
    oi_data = []
else:
    log(f"  {len(oi_data)} records")
    if oi_data:
        oi_vals = [float(r["sumOpenInterestValue"]) for r in oi_data]
        log(f"  OI range: ${min(oi_vals):,.0f} → ${max(oi_vals):,.0f}")
        log(f"  Latest: {datetime.utcfromtimestamp(oi_data[-1]['timestamp']/1000).strftime('%Y-%m-%d')} OI=${float(oi_data[-1]['sumOpenInterestValue']):,.0f}")

oi_path = SCRATCH / f"ff_oi_hist_{DATE_TAG}.json"
oi_path.write_text(json.dumps(oi_data or [], indent=2), encoding="utf-8")
log(f"  Saved: {oi_path.name}")

# ── Spot check (FFUSDT on spot) ───────────────────────────────────────────────
log("\n=== SPOT PAIR CHECK ===")
sp_data, err = safe_get(f"{BASE_API}/api/v3/exchangeInfo?symbol=FFUSDT")
if err and "Invalid symbol" in str(err):
    log("  FFUSDT spot: NO PAIR (HTTP 400 — permanent, expected)")
    spot_exists = False
elif err:
    log(f"  ERROR: {err}")
    spot_exists = False
else:
    syms = sp_data.get("symbols", []) if sp_data else []
    ff_spot = [s for s in syms if s.get("symbol") == "FFUSDT"]
    if ff_spot:
        log(f"  FFUSDT spot: EXISTS, status={ff_spot[0].get('status')}")
        spot_exists = True
    else:
        log("  FFUSDT spot: NOT FOUND")
        spot_exists = False

# ── Alpha klines ─────────────────────────────────────────────────────────────
log("\n=== ALPHA KLINES (store) ===")
ALPHA_DIR = ROOT / "data" / "raw" / "spot_klines_1d"
alpha_ff = list(ALPHA_DIR.glob(f"**/FFUSDT_*.parquet")) if ALPHA_DIR.exists() else []
log(f"  Alpha store partitions for FF: {len(alpha_ff)}")
if alpha_ff:
    alpha_ff.sort()
    log(f"  First: {alpha_ff[0].name}  Last: {alpha_ff[-1].name}")

# Check alpha_id_map
am_path = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_id = None
if am_path.exists():
    am = json.loads(am_path.read_text(encoding="utf-8"))
    alpha_id = am.get("FF")
    log(f"  alpha_id_map: FF → {alpha_id}")

# Try alpha endpoint if alpha_id known
if alpha_id:
    log(f"\n  Fetching alpha klines for {alpha_id}...")
    url_alpha = (f"https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"
                 f"?alphaId={alpha_id}&interval=1d&limit=30")
    alpha_kl, err = safe_get(url_alpha)
    if err:
        log(f"  Alpha API error: {err[:80]}")
    elif alpha_kl:
        klines = alpha_kl.get("data", []) if isinstance(alpha_kl, dict) else alpha_kl
        if isinstance(klines, list) and klines:
            log(f"  Alpha klines: {len(klines)} candles")
            last = klines[-1]
            log(f"  Latest: {last}")
        else:
            log(f"  Alpha klines: unexpected structure {str(alpha_kl)[:200]}")

# ── BAPI token info ───────────────────────────────────────────────────────────
log("\n=== BAPI TOKEN INFO ===")
bapi_path = SCRATCH / f"ff_bapi_{DATE_TAG}.json"
if bapi_path.exists():
    bapi = json.loads(bapi_path.read_text(encoding="utf-8"))
    log(f"  Using cached bapi")
else:
    url_tl = ("https://www.binance.com/bapi/defi/v1/public/wallet-direct/"
               "buw/wallet/cex/alpha/all/token/list")
    tl_data, err = safe_get(url_tl)
    bapi = {}
    if err:
        log(f"  Token list ERROR: {err[:80]}")
    else:
        raw_list = tl_data.get("data", []) if tl_data else []
        tokens = raw_list if isinstance(raw_list, list) else raw_list.get("tokenList", [])
        matches = [t for t in tokens
                   if t.get("tokenSymbol","").upper()=="FF"
                   or str(t.get("alphaId","")).upper()==(alpha_id or "")
                   or t.get("symbol","").upper()=="FF"]
        bapi = matches[0] if matches else {}
        log(f"  Token list: {len(tokens)} tokens, FF matches: {len(matches)}")
        bapi_path.write_text(json.dumps(bapi, indent=2), encoding="utf-8")

if bapi:
    log(f"  alphaId:         {bapi.get('alphaId','?')}")
    log(f"  symbol:          {bapi.get('tokenSymbol','?')}")
    log(f"  contractAddress: {bapi.get('contractAddress','?')}")
    log(f"  totalSupply:     {bapi.get('totalSupply','?')}")
    log(f"  holders:         {bapi.get('holders','?')}")
    log(f"  fullyDelisted:   {bapi.get('fullyDelisted','?')}")
else:
    log("  BAPI FF not found in token list")

log("\n[F-2 DONE]")

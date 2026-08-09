"""
_probe_xpin_x2_collect_20260808.py
X-2: Collect XPIN perp klines, funding, OI for 08-01→08-07.
Spot: GeckoTerminal attempt for 08-06/08-07.
Check freshwatch Aug columns for XPIN.
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-2 COLLECT  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

BASE_FAPI  = "https://fapi.binance.com"
BASE_FUTDT = "https://fapi.binance.com/futures"
SYM = "XPINUSDT"
DATE_TAG = "20260808"

def safe_get(url, timeout=15):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

def dt_to_ms(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

# ── 1. Check freshwatch Aug columns ──────────────────────────────────────────
log("\n=== FRESHWATCH AUG COLUMNS FOR XPIN ===")
fw_aug = VPS_EXPORT / "freshwatch_daily_2026-08.csv"
if fw_aug.exists():
    with open(fw_aug, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        xpin_rows = [r for r in reader if r.get("symbol","").upper() == SYM]
    log(f"  Headers ({len(headers)}): {headers}")
    log(f"  XPIN rows: {len(xpin_rows)}")
    for r in xpin_rows:
        dt = r.get("date","?")
        non_null = {k: v for k,v in r.items() if v not in (None,"","nan","NaN") and k not in ("symbol","date")}
        log(f"  {dt}: {non_null}")
else:
    log("  NOT FOUND")

# ── 2. Perp klines 08-01 → 08-07 ─────────────────────────────────────────────
log("\n=== PERP KLINES 08-01→08-07 ===")
start_ms = dt_to_ms("2026-07-07")   # 30d back for OI context
end_ms   = dt_to_ms("2026-08-08")   # exclusive end (07 closes at 00:00 08-08)
url = (f"{BASE_FAPI}/fapi/v1/klines?symbol={SYM}&interval=1d"
       f"&startTime={start_ms}&endTime={end_ms}&limit=35")
data, err = safe_get(url)
if err:
    log(f"  ERROR: {err}")
    klines = []
else:
    klines = data
    log(f"  {len(klines)} candles")

KCOLS = ["open_time","open","high","low","close","vol_base",
         "close_time","vol_quote","n_trades","taker_vol_base","taker_vol_quote","ignore"]
klines_by_date = {}
for row in klines:
    if len(row) < 12:
        continue
    d = dict(zip(KCOLS, row))
    ts_ms = int(d["open_time"])
    dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    klines_by_date[dt] = {
        "date": dt,
        "px_open":  float(d["open"]),
        "px_high":  float(d["high"]),
        "px_low":   float(d["low"]),
        "px_close": float(d["close"]),
        "vol_perp_usd": round(float(d["vol_quote"]), 0),
        "taker_vol_usd": round(float(d["taker_vol_quote"]), 0),
    }
    taker_pct = float(d["taker_vol_quote"]) / float(d["vol_quote"]) if float(d["vol_quote"]) > 0 else None
    klines_by_date[dt]["taker_buy_pct"] = round(taker_pct, 5) if taker_pct else None
    klines_by_date[dt]["px_avg"] = round((float(d["open"])+float(d["close"]))/2, 8)

log(f"  Last rows:")
for dt in sorted(klines_by_date.keys())[-7:]:
    r = klines_by_date[dt]
    log(f"  {dt}: open={r['px_open']} close={r['px_close']} vol=${r['vol_perp_usd']:,.0f} taker={r.get('taker_buy_pct','?')}")

# Save klines
klines_out = SCRATCH / f"xpin_perp_klines_{DATE_TAG}.json"
klines_out.write_text(json.dumps(klines_by_date, indent=2), encoding="utf-8")
log(f"  Saved: {klines_out.name}")

# ── 3. Funding 08-01→08-08 ────────────────────────────────────────────────────
log("\n=== FUNDING 08-01→08-08 ===")
fund_start = dt_to_ms("2026-08-01")
fund_end   = dt_to_ms("2026-08-08") + 8*3600*1000  # a bit past end
url_fund = (f"{BASE_FAPI}/fapi/v1/fundingRate?symbol={SYM}"
            f"&startTime={fund_start}&limit=50")
fund_data, err = safe_get(url_fund)
if err:
    log(f"  ERROR: {err}")
    fund_data = []
else:
    log(f"  {len(fund_data)} funding records")

# Group by date
fund_by_date = {}
for r in fund_data or []:
    ts_ms = int(r.get("fundingTime", 0))
    dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    rate = float(r.get("fundingRate", 0))
    if dt not in fund_by_date:
        fund_by_date[dt] = []
    fund_by_date[dt].append(rate)

log("  Daily funding summary:")
for dt in sorted(fund_by_date.keys()):
    rates = fund_by_date[dt]
    f_avg = sum(rates)/len(rates)
    log(f"  {dt}: n={len(rates)} f_avg={f_avg:.6f} f_min={min(rates):.6f} f_max={max(rates):.6f}")

fund_out = SCRATCH / f"xpin_funding_{DATE_TAG}.json"
fund_out.write_text(json.dumps(fund_data or [], indent=2), encoding="utf-8")
log(f"  Saved: {fund_out.name}")

# ── 4. OI history 30d ─────────────────────────────────────────────────────────
log("\n=== OI HISTORY 30d ===")
url_oi = (f"{BASE_FAPI}/futures/data/openInterestHist?symbol={SYM}"
          f"&period=1d&limit=30")
oi_data, err = safe_get(url_oi)
if err:
    log(f"  ERROR: {err}")
    oi_data = []
else:
    log(f"  {len(oi_data)} OI records")

oi_by_date = {}
for r in oi_data or []:
    ts_ms = int(r.get("timestamp", 0))
    dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    oi_usd = float(r.get("sumOpenInterestValue", 0))
    oi_tok = float(r.get("sumOpenInterest", 0))
    oi_by_date[dt] = {"oi_usd": round(oi_usd, 0), "oi_token": round(oi_tok, 2)}

log("  Last 10 OI rows:")
for dt in sorted(oi_by_date.keys())[-10:]:
    r = oi_by_date[dt]
    log(f"  {dt}: oi_usd=${r['oi_usd']:,.0f}  oi_token={r['oi_token']:,.0f}")

oi_out = SCRATCH / f"xpin_oi_hist_{DATE_TAG}.json"
oi_out.write_text(json.dumps(oi_by_date, indent=2), encoding="utf-8")
log(f"  Saved: {oi_out.name}")

# ── 5. GeckoTerminal spot vol for XPIN (PancakeSwapV3 pool) ──────────────────
log("\n=== GECKO TERMINAL SPOT (BSC DEX) ===")
# Pool from CASE sheet: 0x08de…4a4
# GeckoTerminal OHLCV API
POOL_ADDR = "0x08dec60e24bd34d27e1e14b1b75b8374be8094a4"
NETWORK = "bsc"
url_gt = (f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{POOL_ADDR}"
          f"/ohlcv/day?limit=10")
req = urllib.request.Request(url_gt, headers={"Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        gt_data = json.loads(r.read())
    ohlcv = gt_data.get("data",{}).get("attributes",{}).get("ohlcv_list",[])
    log(f"  {len(ohlcv)} records from GeckoTerminal")
    spot_by_date = {}
    for row in ohlcv:
        # [timestamp, open, high, low, close, vol_usd]
        if len(row) < 6: continue
        ts = int(row[0])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        spot_by_date[dt] = {
            "vol_spot_usd": round(float(row[5]), 0),
            "px_close_spot": round(float(row[4]), 8),
        }
    log("  Last 5 spot rows:")
    for dt in sorted(spot_by_date.keys())[-5:]:
        r = spot_by_date[dt]
        log(f"  {dt}: vol_spot=${r['vol_spot_usd']:,.0f}  px={r['px_close_spot']}")
    spot_out = SCRATCH / f"xpin_spot_gt_{DATE_TAG}.json"
    spot_out.write_text(json.dumps(spot_by_date, indent=2), encoding="utf-8")
    log(f"  Saved: {spot_out.name}")
except Exception as e:
    log(f"  GeckoTerminal ERROR: {e}")
    log("  Spot vol 08-06/08-07 = MISSING (GeckoTerminal unavailable)")
    spot_by_date = {}

log("\n[X-2 COLLECT DONE]")

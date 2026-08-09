"""
_probe_agt_b0_prep_20260808.py
A-2: Klines + Funding + OI + BAPI metadata for AGTUSDT.
Klines: perp (1d lifetime) + spot (1d if pair exists).
BAPI: token details → contract/supply/holders/listing/fullyDelisted.
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260808"
SYM_PERP = "AGTUSDT"
SYM_BASE = "AGT"

def log(s=""): print(s)
def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"A-2 B0 PREP  {SYM_BASE}  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── 1. FAPI exchangeInfo — onboard date + contract details ────────────────────
log("\n--- FAPI exchangeInfo ---")
ei = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
agt_info = None
if "_error" not in ei:
    for sym in ei.get("symbols", []):
        if sym.get("symbol") == SYM_PERP:
            agt_info = sym
            break
if agt_info:
    onboard_ms = agt_info.get("onboardDate", 0)
    onboard_dt = datetime.fromtimestamp(onboard_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  AGTUSDT perp found: onboardDate={onboard_dt} ({onboard_ms})")
    log(f"  status={agt_info.get('status')} pricePrecision={agt_info.get('pricePrecision')}")
    log(f"  contractType={agt_info.get('contractType')} marginAsset={agt_info.get('marginAsset')}")
    # Save onboard date
    (SCRATCH / f"agt_perp_info_{DATE_TAG}.json").write_text(
        json.dumps(agt_info, indent=2), encoding="utf-8")
else:
    log(f"  AGTUSDT not found in exchangeInfo or error: {str(ei)[:100]}")
    onboard_dt = "UNKNOWN"

# ── 2. BAPI token list — contract, supply, holders, listing ──────────────────
log("\n--- BAPI alpha token list ---")
bapi = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list")
agt_bapi = None
if "_error" not in bapi:
    tokens = bapi.get("data", bapi) if isinstance(bapi, dict) else bapi
    if isinstance(tokens, list):
        for t in tokens:
            # alphaId or symbol match
            if str(t.get("alphaId","")) == "191" or str(t.get("alphaId","")) == "ALPHA_191":
                agt_bapi = t; break
            if t.get("symbol","").upper() == SYM_BASE or t.get("tokenSymbol","").upper() == SYM_BASE:
                agt_bapi = t; break
    elif isinstance(tokens, dict) and "data" in tokens:
        for t in tokens["data"]:
            if str(t.get("alphaId","")) == "191":
                agt_bapi = t; break
            if t.get("symbol","").upper() == SYM_BASE:
                agt_bapi = t; break

if agt_bapi:
    log(f"  AGT BAPI record found:")
    for k, v in agt_bapi.items():
        log(f"    {k}: {v}")
    (SCRATCH / f"agt_bapi_{DATE_TAG}.json").write_text(
        json.dumps(agt_bapi, indent=2), encoding="utf-8")
else:
    log(f"  AGT not found in BAPI token list. Response type: {type(bapi)}")
    if isinstance(bapi, dict):
        log(f"  Keys: {list(bapi.keys())[:10]}")
    elif isinstance(bapi, list):
        log(f"  List len: {len(bapi)}, first item keys: {list(bapi[0].keys())[:10] if bapi else []}")
    log(f"  → Saving raw response for manual check")
    (SCRATCH / f"agt_bapi_raw_{DATE_TAG}.json").write_text(
        json.dumps(bapi if not isinstance(bapi, dict) or "_error" not in bapi else {}, indent=2),
        encoding="utf-8")

# ── 3. Perp klines (lifetime, 1d) ─────────────────────────────────────────────
log("\n--- Perp klines ---")
PERP_COLS = ["open_time","open","high","low","close","volume","close_time",
             "quote_vol","n_trades","taker_buy_vol","taker_buy_quote_vol","ignore"]

all_perp = []
# Binance max limit=1500 per call, go back via endTime pagination
end_time = None
iterations = 0
while True:
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1500"
    if end_time:
        url += f"&endTime={end_time}"
    data = fetch_json(url)
    if "_error" in data or not isinstance(data, list) or len(data) == 0:
        log(f"  Perp klines fetch stopped: {data if '_error' in (data if isinstance(data, dict) else {}) else 'empty'}")
        break
    all_perp = data + all_perp  # prepend (older data)
    if len(data) < 1500:
        break  # got everything
    end_time = int(data[0]["open_time"]) - 1
    iterations += 1
    if iterations > 5: break  # safety

log(f"  Total perp klines: {len(all_perp)} rows")
if all_perp:
    oldest = datetime.fromtimestamp(int(all_perp[0]["open_time"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    newest = datetime.fromtimestamp(int(all_perp[-1]["open_time"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Perp range: {oldest} → {newest}")

# Save raw perp CSV
perp_out = SCRATCH / f"agt_perp_raw_{DATE_TAG}.csv"
with open(perp_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=PERP_COLS)
    w.writeheader()
    for row in all_perp:
        w.writerow(dict(zip(PERP_COLS, row)))
log(f"  Saved raw: {perp_out.name}")

# ── 4. Spot klines ─────────────────────────────────────────────────────────────
log("\n--- Spot klines ---")
spot_url = f"https://api.binance.com/api/v3/klines?symbol={SYM_PERP}&interval=1d&limit=1000"
spot_data = fetch_json(spot_url)
if isinstance(spot_data, list) and len(spot_data) > 0:
    log(f"  Spot klines: {len(spot_data)} rows")
    spot_out = SCRATCH / f"agt_spot_raw_{DATE_TAG}.csv"
    with open(spot_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PERP_COLS)
        w.writeheader()
        for row in spot_data:
            w.writerow(dict(zip(PERP_COLS, row)))
    oldest_s = datetime.fromtimestamp(int(spot_data[0][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    newest_s = datetime.fromtimestamp(int(spot_data[-1][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Spot range: {oldest_s} → {newest_s}")
    log(f"  Saved: {spot_out.name}")
elif isinstance(spot_data, dict) and "_error" in spot_data:
    log(f"  Spot error: {spot_data['_error']}")
else:
    log(f"  Spot: no data or unexpected format: {str(spot_data)[:100]}")

# ── 5. Funding hist ────────────────────────────────────────────────────────────
log("\n--- Funding history ---")
fund_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={SYM_PERP}&limit=1000"
fund_data = fetch_json(fund_url)
if isinstance(fund_data, list):
    log(f"  Funding records: {len(fund_data)}")
    if fund_data:
        oldest_f = datetime.fromtimestamp(int(fund_data[0].get("fundingTime",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        newest_f = datetime.fromtimestamp(int(fund_data[-1].get("fundingTime",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Funding range: {oldest_f} → {newest_f}")
        log(f"  Last 3: {[(r.get('fundingTime',''), r.get('fundingRate','')) for r in fund_data[-3:]]}")
    fund_out = SCRATCH / f"agt_funding_{DATE_TAG}.json"
    fund_out.write_text(json.dumps(fund_data, indent=2), encoding="utf-8")
    log(f"  Saved: {fund_out.name}")
else:
    log(f"  Funding error: {str(fund_data)[:150]}")

# ── 6. OI hist (30d) ──────────────────────────────────────────────────────────
log("\n--- OI hist ---")
oi_url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={SYM_PERP}&period=1d&limit=30"
oi_data = fetch_json(oi_url)
if isinstance(oi_data, list):
    log(f"  OI records: {len(oi_data)}")
    if oi_data:
        oldest_o = datetime.fromtimestamp(int(oi_data[0].get("timestamp",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        newest_o = datetime.fromtimestamp(int(oi_data[-1].get("timestamp",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  OI range: {oldest_o} → {newest_o}")
        log(f"  Last OI: {oi_data[-1]}")
    oi_out = SCRATCH / f"agt_oi_hist_{DATE_TAG}.json"
    oi_out.write_text(json.dumps(oi_data, indent=2), encoding="utf-8")
    log(f"  Saved: {oi_out.name}")
else:
    log(f"  OI error: {str(oi_data)[:150]}")

# ── 7. Spot check BAPI for FAPI data availability ──────────────────────────────
log("\n--- Quick spot check (api/v3 ticker) ---")
ticker = fetch_json(f"https://api.binance.com/api/v3/ticker/24hr?symbol={SYM_PERP}")
if "_error" not in ticker:
    log(f"  Spot ticker: lastPrice={ticker.get('lastPrice')} vol24h={ticker.get('quoteVolume')} "
        f"priceChange%={ticker.get('priceChangePercent')}")
else:
    log(f"  Spot ticker: {ticker['_error']}")

# ── 8. Summary ────────────────────────────────────────────────────────────────
log("\n--- Summary ---")
log(f"  Perp klines: {len(all_perp)} rows")
log(f"  BAPI AGT found: {'YES' if agt_bapi else 'NO'}")
log(f"  Perp onboard: {onboard_dt}")
log(f"  Files in scratch/agt_*_{DATE_TAG}.*:")
for p in sorted(SCRATCH.glob(f"agt_*_{DATE_TAG}.*")):
    log(f"    {p.name}")

log(f"\n[B0 PREP DONE]")

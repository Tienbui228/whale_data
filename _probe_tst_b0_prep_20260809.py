"""
_probe_tst_b0_prep_20260809.py
T-0/T-2: Basic info — symbol verify, listing dates, klines meta, OI hist,
funding hist trọn đời, Alpha ID, freshwatch universe check.
"""
import sys, io, json, csv, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

SYMBOL  = "TSTUSDT"
SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
ROOT    = Path(r"D:\Data back test\whale_data")

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TST B-0 PREP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

# ── 1. Perp exchange info ─────────────────────────────────────────────────────
log("\n--- Perp exchange info ---")
ei = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo", timeout=30)
tst_perp = None
if isinstance(ei, dict) and "symbols" in ei:
    for s in ei["symbols"]:
        if s.get("symbol") == SYMBOL:
            tst_perp = s
            break
if tst_perp:
    log(f"  symbol: {tst_perp.get('symbol')}")
    log(f"  status: {tst_perp.get('status')}")
    log(f"  contractType: {tst_perp.get('contractType')}")
    log(f"  onboardDate: {datetime.fromtimestamp(tst_perp.get('onboardDate',0)/1000, tz=timezone.utc).strftime('%Y-%m-%d') if tst_perp.get('onboardDate') else 'N/A'}")
    log(f"  deliveryDate: {tst_perp.get('deliveryDate')}")
    log(f"  underlyingType: {tst_perp.get('underlyingType')}")
    log(f"  pricePrecision: {tst_perp.get('pricePrecision')}")
else:
    log(f"  ERROR or not found: {str(ei)[:200]}")

time.sleep(0.3)

# ── 2. Perp klines — oldest nến (list start) ─────────────────────────────────
log("\n--- Perp klines oldest (listing date) ---")
kl_old = fetch_json(f"{FAPI}/fapi/v1/klines?symbol={SYMBOL}&interval=1d&limit=3&startTime=0")
if isinstance(kl_old, list) and kl_old:
    first_k = kl_old[0]
    log(f"  First kline open_time: {datetime.fromtimestamp(first_k[0]/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log(f"  open={first_k[1]} high={first_k[2]} low={first_k[3]} close={first_k[4]} vol={first_k[5]}")
else:
    log(f"  ERROR: {kl_old}")

# Latest klines (last 7 days)
log("\n--- Perp klines latest 7 days ---")
kl_latest = fetch_json(f"{FAPI}/fapi/v1/klines?symbol={SYMBOL}&interval=1d&limit=7")
perp_last = None
if isinstance(kl_latest, list) and kl_latest:
    log(f"  Records: {len(kl_latest)}")
    for k in kl_latest:
        d = datetime.fromtimestamp(k[0]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"    {d}: o={k[1]} h={k[2]} l={k[3]} c={k[4]} vol={k[5]} trades={k[8]} taker_vol={k[9]}")
    perp_last = kl_latest[-1]
else:
    log(f"  ERROR: {kl_latest}")

# Count total klines
kl_all = fetch_json(f"{FAPI}/fapi/v1/klines?symbol={SYMBOL}&interval=1d&limit=1500&startTime=0")
if isinstance(kl_all, list):
    log(f"  Total klines (limit 1500): {len(kl_all)}")
    if kl_all:
        first_d = datetime.fromtimestamp(kl_all[0][0]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        last_d  = datetime.fromtimestamp(kl_all[-1][0]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Date range: {first_d} → {last_d}")
        # Save all perp klines
        out_perp = SCRATCH / "tst_perp_20260809.csv"
        with open(out_perp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["open_time","open","high","low","close","volume","close_time","quote_vol","trades","taker_buy_vol","taker_buy_quote_vol","ignore"])
            w.writerows(kl_all)
        log(f"  Saved perp klines: {out_perp}")

time.sleep(0.3)

# ── 3. Spot klines ────────────────────────────────────────────────────────────
log("\n--- Spot klines ---")
spot_all = fetch_json(f"{SAPI}/api/v3/klines?symbol={SYMBOL}&interval=1d&limit=1500&startTime=0")
if isinstance(spot_all, list):
    log(f"  Spot klines: {len(spot_all)}")
    if spot_all:
        first_s = datetime.fromtimestamp(spot_all[0][0]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        last_s  = datetime.fromtimestamp(spot_all[-1][0]/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Date range: {first_s} → {last_s}")
        out_spot = SCRATCH / "tst_spot_20260809.csv"
        with open(out_spot, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["open_time","open","high","low","close","volume","close_time","quote_vol","trades","taker_buy_vol","taker_buy_quote_vol","ignore"])
            w.writerows(spot_all)
        log(f"  Saved spot klines: {out_spot}")
        log(f"  Latest spot: {spot_all[-1][4]} (close)")
else:
    log(f"  ERROR or no spot pair: {str(spot_all)[:200]}")

time.sleep(0.3)

# ── 4. Current price + markPrice ─────────────────────────────────────────────
log("\n--- Current prices ---")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYMBOL}")
if isinstance(ticker, dict) and "lastPrice" in ticker:
    log(f"  lastPrice: {ticker['lastPrice']}")
    log(f"  priceChangePercent: {ticker['priceChangePercent']}%")
    log(f"  volume (24h): {ticker['volume']}")
    log(f"  quoteVolume (24h): {ticker['quoteVolume']}")
    log(f"  highPrice: {ticker['highPrice']}")
    log(f"  lowPrice: {ticker['lowPrice']}")
else:
    log(f"  ERROR: {ticker}")

time.sleep(0.3)

# ── 5. OI hist 30d ───────────────────────────────────────────────────────────
log("\n--- OI hist 30d ---")
oi_hist = fetch_json(f"{FAPI}/futures/data/openInterestHist?symbol={SYMBOL}&period=1d&limit=30")
if isinstance(oi_hist, list):
    log(f"  OI records: {len(oi_hist)}")
    if oi_hist:
        log(f"  Oldest: {datetime.fromtimestamp(int(oi_hist[0]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Newest: {datetime.fromtimestamp(int(oi_hist[-1]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        latest_oi = oi_hist[-1]
        log(f"  Latest: sumOpenInterest={latest_oi.get('sumOpenInterest','?')} sumOpenInterestValue={latest_oi.get('sumOpenInterestValue','?')}")
    out_oi = SCRATCH / "tst_oi_hist_20260809.json"
    out_oi.write_text(json.dumps(oi_hist), encoding="utf-8")
    log(f"  Saved: {out_oi}")
else:
    log(f"  ERROR: {oi_hist}")

time.sleep(0.3)

# ── 6. OI current ────────────────────────────────────────────────────────────
log("\n--- OI current ---")
oi_now = fetch_json(f"{FAPI}/fapi/v1/openInterest?symbol={SYMBOL}")
if isinstance(oi_now, dict):
    log(f"  openInterest: {oi_now.get('openInterest','?')} (tokens)")
else:
    log(f"  ERROR: {oi_now}")

time.sleep(0.3)

# ── 7. Funding hist — trọn đời (500 per call, page) ─────────────────────────
log("\n--- Funding hist trọn đời ---")
all_fn = []
end_time = int(NOW.timestamp() * 1000)
max_pages = 20
page = 0
while page < max_pages:
    url_fn = f"{FAPI}/fapi/v1/fundingRate?symbol={SYMBOL}&limit=1000&endTime={end_time}"
    batch = fetch_json(url_fn)
    if not isinstance(batch, list) or not batch:
        break
    # Prepend (batches come newest first when we page backward)
    all_fn = batch + all_fn
    oldest_ts = int(batch[0]["fundingTime"])
    end_time  = oldest_ts - 1
    if len(batch) < 1000:
        break
    page += 1
    time.sleep(0.2)
if all_fn:
    log(f"  Total funding records: {len(all_fn)}")
    first_fn = datetime.fromtimestamp(int(all_fn[0]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    last_fn  = datetime.fromtimestamp(int(all_fn[-1]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    log(f"  Date range: {first_fn} → {last_fn}")
    # Last few rates
    for fn in all_fn[-4:]:
        dt = datetime.fromtimestamp(int(fn["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        log(f"    {dt}: {fn.get('fundingRate','?')}")
    out_fn = SCRATCH / "tst_funding_20260809.json"
    out_fn.write_text(json.dumps(all_fn), encoding="utf-8")
    log(f"  Saved: {out_fn}")
else:
    log(f"  No funding data")

time.sleep(0.3)

# ── 8. Alpha ID check ─────────────────────────────────────────────────────────
log("\n--- Alpha ID check ---")
alpha_map = ROOT / "data" / "config" / "alpha_id_map.json"
if alpha_map.exists():
    amap = json.loads(alpha_map.read_text(encoding="utf-8"))
    tst_alpha = None
    for sym, info in amap.items():
        if sym == "TSTUSDT" or sym == "TST" or (isinstance(info, dict) and info.get("symbol","").upper() in ["TST","TSTUSDT"]):
            tst_alpha = (sym, info)
            break
    if tst_alpha:
        log(f"  FOUND: {tst_alpha}")
    else:
        log(f"  TST not in alpha_id_map.json (not an Alpha token or map incomplete)")
        log(f"  Total symbols in map: {len(amap)}")
else:
    log(f"  alpha_id_map.json not found at {alpha_map}")

time.sleep(0.2)

# ── 9. BAPI Alpha token list — search TST ────────────────────────────────────
log("\n--- BAPI Alpha token list (search TST) ---")
bapi_list = fetch_json(
    "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list",
    timeout=30)
tst_bapi = None
if isinstance(bapi_list, dict):
    tokens = bapi_list.get("data", bapi_list.get("result", []))
    if isinstance(tokens, list):
        for t in tokens:
            sym = str(t.get("symbol","") or t.get("tokenSymbol","") or "").upper()
            if sym in ["TST", "TSTUSDT"]:
                tst_bapi = t
                break
        log(f"  Total BAPI tokens: {len(tokens)}")
    if tst_bapi:
        log(f"  TST found in BAPI Alpha list:")
        for k, v in tst_bapi.items():
            log(f"    {k}: {v}")
    else:
        log(f"  TST NOT in BAPI Alpha list")
else:
    log(f"  BAPI error: {str(bapi_list)[:200]}")

# ── 10. freshwatch universe check ────────────────────────────────────────────
log("\n--- freshwatch universe check (TST in 137?) ---")
fw_sym_file = ROOT / "data" / "config" / "freshwatch_symbols.txt"
if fw_sym_file.exists():
    syms = fw_sym_file.read_text(encoding="utf-8").splitlines()
    tst_in_fw = any("TST" in s.upper() for s in syms)
    log(f"  freshwatch_symbols.txt: {len(syms)} symbols, TST in list: {tst_in_fw}")
    if tst_in_fw:
        matches = [s for s in syms if "TST" in s.upper()]
        log(f"  TST entries: {matches}")
else:
    log(f"  freshwatch_symbols.txt not found at {fw_sym_file}")

# Check freshwatch CSVs for TST
for tag in ["2026-07", "2026-06", "2026-08"]:
    fw_csv = SCRATCH / f"freshwatch_daily_{tag}.csv"
    if fw_csv.exists():
        with open(fw_csv, encoding="utf-8") as f:
            rows_tst = [r for r in csv.DictReader(f)
                        if "TST" in (r.get("symbol","") or r.get("Symbol","")).upper()]
        log(f"  freshwatch_{tag}: {len(rows_tst)} TST rows")
        if rows_tst:
            log(f"    Columns: {list(rows_tst[0].keys())}")
            log(f"    Last row: {rows_tst[-1]}")
    else:
        log(f"  freshwatch_{tag}.csv: not in scratch")

# ── 11. gom_scan / CASE cross-ref quick check ────────────────────────────────
log("\n--- Quick cross-ref: gom_scan / case files / agent_log ---")
for label, fpath in [
    ("gom_gate6_full_20260808.txt", ROOT / "docs" / "reports" / "gom_gate6_full_20260808.txt"),
    ("CASE_INDEX.xlsx", None),
    ("agent_log.md", ROOT / "agent_log.md"),
]:
    if fpath and fpath.exists():
        txt = fpath.read_text(encoding="utf-8", errors="replace")
        if "TST" in txt.upper():
            lines = [l for l in txt.split("\n") if "TST" in l.upper()][:5]
            log(f"  {label}: TST found ({len(lines)} lines) — {lines[0][:80]}")
        else:
            log(f"  {label}: TST not found (checked, clean)")
    elif fpath:
        log(f"  {label}: not found")

log(f"\n[B-0 DONE]")

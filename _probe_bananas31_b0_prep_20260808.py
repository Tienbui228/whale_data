"""
_probe_bananas31_b0_prep_20260808.py
B-0/B-1 prep: check alpha_id_map, symbol info, LSR persist (TIME-SENSITIVE FIRST).
"""
import sys, io, json, csv, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYMBOL = "BANANAS31USDT"
SYM_BASE = "BANANAS31"
SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("="*70)
log(f"BANANAS31 PREP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("="*70)

# ── 1. Alpha ID map check ─────────────────────────────────────────────────────
alpha_map_path = Path(r"D:\Data back test\whale_data\data\config\alpha_id_map.json")
alpha_id = None
alpha_info = {}
if alpha_map_path.exists():
    try:
        with open(alpha_map_path, encoding="utf-8-sig") as f:
            alpha_map = json.load(f)
        for k, v in alpha_map.items():
            if "BANANA" in k.upper() or "BANANA" in str(v).upper():
                log(f"  alpha_map key match: {k} -> {v}")
                alpha_id = v
                alpha_info = {"key": k, "val": v}
        if not alpha_id:
            log(f"  alpha_map: BANANAS31 NOT FOUND — checking all keys with 31...")
            for k, v in alpha_map.items():
                if "31" in k:
                    log(f"    {k} -> {v}")
    except Exception as e:
        log(f"  alpha_map read error: {e}")
else:
    log(f"  alpha_map NOT FOUND: {alpha_map_path}")

# ── 2. Perp symbol info ───────────────────────────────────────────────────────
log(f"\n  Checking fapi exchangeInfo for {SYMBOL}...")
ei = fetch_json(f"https://fapi.binance.com/fapi/v1/exchangeInfo")
sym_info = {}
if isinstance(ei, dict) and "symbols" in ei:
    for s in ei["symbols"]:
        if s.get("symbol") == SYMBOL:
            sym_info = s
            break
if sym_info:
    log(f"  perp: found. onboardDate={sym_info.get('onboardDate')} "
        f"deliveryDate={sym_info.get('deliveryDate')} "
        f"underlyingType={sym_info.get('underlyingType')} "
        f"status={sym_info.get('status')}")
    log(f"  contractType={sym_info.get('contractType')} "
        f"marginAsset={sym_info.get('marginAsset')}")
else:
    log(f"  perp: NOT FOUND in fapi exchangeInfo — CRITICAL")

# ── 3. Spot pair check ────────────────────────────────────────────────────────
log(f"\n  Checking spot pair {SYMBOL}...")
spot_ei = fetch_json(f"https://api.binance.com/api/v3/exchangeInfo?symbol={SYMBOL}")
spot_info = {}
if isinstance(spot_ei, dict) and "symbols" in spot_ei:
    spot_info = spot_ei["symbols"][0] if spot_ei["symbols"] else {}
    log(f"  spot: found. status={spot_info.get('status')} "
        f"isSpotTradingAllowed={spot_info.get('isSpotTradingAllowed')}")
elif "_error" in spot_ei:
    log(f"  spot: {spot_ei['_error']}")
else:
    log(f"  spot: NOT FOUND or error")

# ── 4. LSR PERSIST (TIME-SENSITIVE — run first) ────────────────────────────────
log(f"\n--- LSR PERSIST (TIME-SENSITIVE) ---")
lsr_endpoints = [
    ("topLongShortPositionRatio", "longShortRatio", "pos_r_raw"),
    ("topLongShortAccountRatio",  "longShortRatio", "acc_r_raw"),
    ("globalLongShortAccountRatio","longShortRatio","glsr_raw"),
    ("takerlongshortRatio",       "buySellRatio",   "taker_lsr_raw"),
]

lsr_by_date = defaultdict(dict)
for ep, ratio_key, field in lsr_endpoints:
    url = (f"https://fapi.binance.com/futures/data/{ep}"
           f"?symbol={SYMBOL}&period=1d&limit=30")
    raw = fetch_json(url)
    if isinstance(raw, list) and raw:
        for r in raw:
            ts = r.get("timestamp")
            if ts:
                dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
                v = r.get(ratio_key)
                if v is not None:
                    lsr_by_date[dt][field] = float(v)
        log(f"  {ep}: {len(raw)} rows, range={raw[0].get('timestamp')} - {raw[-1].get('timestamp')}")
    else:
        log(f"  {ep}: ERROR or empty: {raw}")

# Write LSR CSV
lsr_path = SCRATCH / f"bananas31_lsr_raw_{NOW.strftime('%Y%m%d')}.csv"
lsr_rows_sorted = sorted(lsr_by_date.items())
if lsr_rows_sorted:
    fields = ["date", "pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw"]
    with open(lsr_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for dt, vals in lsr_rows_sorted:
            w.writerow({"date": dt, **{k: vals.get(k, "") for k in fields[1:]}})
    log(f"  LSR persisted: {lsr_path} ({len(lsr_rows_sorted)} rows)")
    log(f"  Range: {lsr_rows_sorted[0][0]} → {lsr_rows_sorted[-1][0]}")
    log(f"  Sample last 3:")
    for dt, v in lsr_rows_sorted[-3:]:
        log(f"    {dt}: pos_r={v.get('pos_r_raw','?')} acc_r={v.get('acc_r_raw','?')} "
            f"gLSR={v.get('glsr_raw','?')} tkls={v.get('taker_lsr_raw','?')}")
else:
    log(f"  LSR: NO DATA — check symbol {SYMBOL}")

# ── 5. OI hist 30d ────────────────────────────────────────────────────────────
log(f"\n  OI hist 30d...")
oih = fetch_json(f"https://fapi.binance.com/futures/data/openInterestHist"
                 f"?symbol={SYMBOL}&period=1d&limit=30")
oi_path = SCRATCH / f"bananas31_oi_hist_{NOW.strftime('%Y%m%d')}.csv"
if isinstance(oih, list) and oih:
    with open(oi_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "oi_token", "oi_usd", "ts_ms"])
        w.writeheader()
        for o in oih:
            ts = o.get("timestamp")
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d") if ts else ""
            w.writerow({"date": dt, "oi_token": o.get("sumOpenInterest",""),
                        "oi_usd": o.get("sumOpenInterestValue",""), "ts_ms": ts})
    log(f"  OI: {len(oih)} rows persisted -> {oi_path}")
    log(f"  OI range: {oih[0].get('timestamp')} -> {oih[-1].get('timestamp')}")
else:
    log(f"  OI hist: ERROR: {oih}")

# ── 6. Funding history ────────────────────────────────────────────────────────
log(f"\n  Funding rates (limit=1000)...")
fund = fetch_json(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={SYMBOL}&limit=1000")
fund_path = SCRATCH / f"bananas31_funding_{NOW.strftime('%Y%m%d')}.csv"
if isinstance(fund, list) and fund:
    with open(fund_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "fundingTime", "fundingRate"])
        w.writeheader()
        for fr in fund:
            ts = fr.get("fundingTime")
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d") if ts else ""
            w.writerow({"date": dt, "fundingTime": ts, "fundingRate": fr.get("fundingRate","")})
    log(f"  Funding: {len(fund)} rows -> {fund_path}")
    dates = set()
    for fr in fund:
        ts = fr.get("fundingTime")
        if ts:
            dates.add(datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d"))
    log(f"  Funding date range: {min(dates)} → {max(dates)} ({len(dates)} days)")
else:
    log(f"  Funding: ERROR: {fund}")

# ── 7. Perp klines — paginated ────────────────────────────────────────────────
log(f"\n  Perp klines (paginated from listing)...")
onboard_ts = sym_info.get("onboardDate") if sym_info else None
if onboard_ts:
    start_ts = int(onboard_ts)
else:
    # Fallback: start from 2024-01-01
    start_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
log(f"  Start ts: {start_ts} ({datetime.fromtimestamp(start_ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')})")

perp_rows_all = []
ts_cur = start_ts
end_ts = int(datetime(2026, 8, 7, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
while ts_cur < end_ts:
    url = (f"https://fapi.binance.com/fapi/v1/klines"
           f"?symbol={SYMBOL}&interval=1d&startTime={ts_cur}&limit=500")
    raw = fetch_json(url)
    if not isinstance(raw, list) or not raw:
        log(f"  klines fetch error at ts={ts_cur}: {raw}")
        break
    for k in raw:
        dt = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        vol_q = float(k[7]); taker_q = float(k[10])
        perp_rows_all.append({
            "date": dt, "o": k[1], "h": k[2], "l": k[3], "c": k[4],
            "vol_quote_usd": vol_q,
            "taker_pct": round(taker_q/vol_q*100, 4) if vol_q else None,
            "open_ts": k[0], "close_ts": k[6],
        })
    ts_cur = int(raw[-1][0]) + 86_400_000
    if len(raw) < 500:
        break

# Compute ret_1d
for i in range(1, len(perp_rows_all)):
    c_prev = float(perp_rows_all[i-1]["c"]) if perp_rows_all[i-1]["c"] else None
    c_cur  = float(perp_rows_all[i]["c"])   if perp_rows_all[i]["c"]   else None
    if c_prev and c_cur and c_prev > 0:
        perp_rows_all[i]["ret_1d"] = round((c_cur - c_prev) / c_prev * 100, 4)
    else:
        perp_rows_all[i]["ret_1d"] = None
perp_rows_all[0]["ret_1d"] = None

perp_path = SCRATCH / f"bananas31_perp_{NOW.strftime('%Y%m%d')}.csv"
if perp_rows_all:
    fields = ["date","o","h","l","c","vol_quote_usd","taker_pct","ret_1d","open_ts","close_ts"]
    with open(perp_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(perp_rows_all)
    log(f"  Perp klines: {len(perp_rows_all)} rows -> {perp_path}")
    log(f"  Range: {perp_rows_all[0]['date']} → {perp_rows_all[-1]['date']}")
    log(f"  px_listing_close={perp_rows_all[0]['c']} px_latest={perp_rows_all[-1]['c']}")
    log(f"  px_max={max(float(r['h']) for r in perp_rows_all):.6f} "
        f"px_min={min(float(r['l']) for r in perp_rows_all if r['l']):.6f}")
else:
    log(f"  Perp klines: NO DATA")

# ── 8. Spot klines ────────────────────────────────────────────────────────────
log(f"\n  Spot klines (same window)...")
spot_rows_all = []
ts_cur = start_ts
while ts_cur < end_ts:
    url = (f"https://api.binance.com/api/v3/klines"
           f"?symbol={SYMBOL}&interval=1d&startTime={ts_cur}&limit=500")
    raw = fetch_json(url)
    if not isinstance(raw, list) or not raw:
        log(f"  spot klines: error/empty at ts={ts_cur}: {raw}")
        break
    for k in raw:
        dt = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        vol_q = float(k[7]); taker_q = float(k[10])
        spot_rows_all.append({
            "date": dt,
            "vol_spot_usd": vol_q,
            "taker_spot_pct": round(taker_q/vol_q*100, 4) if vol_q else None,
        })
    ts_cur = int(raw[-1][0]) + 86_400_000
    if len(raw) < 500:
        break

spot_path = SCRATCH / f"bananas31_spot_{NOW.strftime('%Y%m%d')}.csv"
if spot_rows_all:
    with open(spot_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","vol_spot_usd","taker_spot_pct"])
        w.writeheader()
        w.writerows(spot_rows_all)
    log(f"  Spot klines: {len(spot_rows_all)} rows -> {spot_path}")
else:
    log(f"  Spot klines: NO DATA (pair may not exist on spot)")

# ── 9. Current live data ──────────────────────────────────────────────────────
log(f"\n  Live snapshots...")
ticker = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={SYMBOL}")
oi_live = fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={SYMBOL}")
px_live = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}")
log(f"  px_live: {px_live.get('price','?')}")
log(f"  OI_token: {oi_live.get('openInterest','?')}")
log(f"  24h vol: {ticker.get('quoteVolume','?')}")
log(f"  24h high: {ticker.get('highPrice','?')} low: {ticker.get('lowPrice','?')}")

# ── 10. Depth snapshot #1 ─────────────────────────────────────────────────────
log(f"\n  Depth snapshot #1 ({NOW.strftime('%Y-%m-%d %H:%M UTC')})...")
depth = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={SYMBOL}&limit=500")
px_mid = float(px_live.get("price", 0))
if px_mid and isinstance(depth, dict):
    pct_band = 0.02
    bids = [(float(p), float(q)) for p, q in depth.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in depth.get("asks", [])]
    bid_2pct = sum(p*q for p,q in bids if p >= px_mid*(1-pct_band))
    ask_2pct = sum(p*q for p,q in asks if p <= px_mid*(1+pct_band))
    log(f"  Depth ±2%: Bid=${bid_2pct:,.0f}  Ask=${ask_2pct:,.0f}  px_mid={px_mid}")
    log(f"  Snapshot #1 timestamp: {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"  [Need snapshot #2 >= {(NOW).strftime('%H:%M')} + 4h = L-23 compliance]")
else:
    log(f"  Depth: error or no price {depth}")

log(f"\n[B-0/B-1 PREP DONE]")
log(f"  LSR: {lsr_path}")
log(f"  OI hist: {oi_path}")
log(f"  Funding: {fund_path}")
log(f"  Perp: {perp_path}")
log(f"  Spot: {spot_path}")
log(f"  alpha_id: {alpha_id if alpha_id else 'NOT FOUND'}")

"""
HEI cold-start pack — H0 (identity/listing) + H1 (perp daily, LSR persist KHẨN CẤP).
LSR chỉ giữ 30 ngày — chạy ĐẦU TIÊN.
Output: scratch/hei_h0h1_raw_20260808.txt + scratch/hei_lsr_raw_20260808.csv
"""
import sys, io, json, csv, time, math
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(r"D:\Data back test\whale_data\scratch")
OUT_DIR.mkdir(exist_ok=True)
LOG_F   = OUT_DIR / "hei_h0h1_raw_20260808.txt"
LSR_F   = OUT_DIR / "hei_lsr_raw_20260808.csv"

def ts_ms(dt_str):
    """ISO date string → ms timestamp UTC 00:00"""
    dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def now_ms():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

lines = []
def log(s=""):
    print(s)
    lines.append(s)

log("=" * 70)
log(f"HEI COLD-START — H0 + H1  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# H0 — IDENTITY + LISTING DATES
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════╗")
log("║  H0 — IDENTITY + LISTING     ║")
log("╚══════════════════════════════╝")

# H0a — Perp listing: fapi klines 1d, startTime=0 limit=1 để lấy nến đầu tiên
log()
log("── H0a: Perp listing date (fapi klines 1d first candle) ──")
url_perp_first = "https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&startTime=0&limit=1"
d = fetch_json(url_perp_first)
if "_error" in d:
    log(f"  PERP LISTING: ERROR — {d['_error']}")
    perp_first_ts  = None
    perp_list_date = None
else:
    if isinstance(d, list) and len(d) > 0:
        perp_first_ts  = d[0][0]
        perp_list_date = datetime.fromtimestamp(perp_first_ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Perp listing date : {perp_list_date}  (open_ts={perp_first_ts})")
        # Also get last candle for window count
        url_perp_last = "https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&limit=1"
        dlast = fetch_json(url_perp_last)
        if isinstance(dlast, list) and len(dlast) > 0:
            last_open = dlast[0][0]
            last_date = datetime.fromtimestamp(last_open/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            window_d  = round((last_open - perp_first_ts) / 86400000) + 1
            log(f"  Last candle open  : {last_date}")
            log(f"  Window (days)     : {window_d}d")
            if window_d < 29:
                log(f"  ⚠ WINDOW < 29d — lấy TOÀN BỘ full history ({window_d}d)")
            else:
                log(f"  Window ≥ 29d — đủ điều kiện")
    else:
        log(f"  PERP NOT FOUND or empty: {d}")
        perp_first_ts  = None
        perp_list_date = None

# H0a — Spot listing: api/v3 klines 1d startTime=0 limit=1
log()
log("── H0a: Spot listing date (api/v3 klines 1d) ──")
url_spot_first = "https://api.binance.com/api/v3/klines?symbol=HEIUSDT&interval=1d&startTime=0&limit=1"
ds = fetch_json(url_spot_first)
if "_error" in ds:
    log(f"  SPOT LISTING: ERROR — {ds['_error']}")
    spot_list_date = None
elif isinstance(ds, list) and len(ds) > 0:
    spot_first_ts  = ds[0][0]
    spot_list_date = datetime.fromtimestamp(spot_first_ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Spot listing date : {spot_list_date}  (open_ts={spot_first_ts})")
else:
    log(f"  Spot pair HEIUSDT: NOT FOUND on Binance spot")
    spot_list_date = None

# H0a — Alpha ID check (already confirmed NOT in alpha_id_map.json)
log()
log("── H0a: Alpha ID ──")
alpha_map = Path(r"D:\Data back test\whale_data\data\config\alpha_id_map.json")
if alpha_map.exists():
    with open(alpha_map, encoding="utf-8") as f:
        amap = json.load(f)
    hei_keys = [k for k in amap if "HEI" in k.upper()]
    if hei_keys:
        log(f"  HEI found in alpha_id_map: {hei_keys}")
        for k in hei_keys:
            log(f"    {k}: {amap[k]}")
    else:
        log("  HEI: NOT in alpha_id_map.json")
        log("  → Alpha collect: N/A (no alpha_id). Alpha layer = ABSTAIN.")
else:
    log(f"  alpha_id_map.json NOT FOUND at {alpha_map}")

# H0b — Contract address: try exchangeInfo fapi
log()
log("── H0b: Contract info (fapi exchangeInfo) ──")
url_ei = "https://fapi.binance.com/fapi/v1/exchangeInfo"
ei = fetch_json(url_ei)
hei_info = None
if "_error" not in ei:
    syms = ei.get("symbols", [])
    for s in syms:
        if s.get("symbol") == "HEIUSDT":
            hei_info = s
            break
if hei_info:
    log(f"  baseAsset        : {hei_info.get('baseAsset')}")
    log(f"  quoteAsset       : {hei_info.get('quoteAsset')}")
    log(f"  contractType     : {hei_info.get('contractType')}")
    log(f"  deliveryDate     : {hei_info.get('deliveryDate')}")
    log(f"  onboardDate      : {hei_info.get('onboardDate')}")
    onboard_ms = hei_info.get("onboardDate")
    if onboard_ms:
        onboard_dt = datetime.fromtimestamp(onboard_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  onboardDate (UTC): {onboard_dt}")
    log(f"  status           : {hei_info.get('status')}")
    log(f"  quantityPrecision: {hei_info.get('quantityPrecision')}")
    log(f"  underlyingType   : {hei_info.get('underlyingType')}")
    log(f"  underlyingSubType: {hei_info.get('underlyingSubType')}")
    # marginAsset
    log(f"  marginAsset      : {hei_info.get('marginAsset')}")
else:
    log("  HEIUSDT not found in fapi exchangeInfo or fetch error")

# H0c — spot exchangeInfo for contract details
log()
log("── H0c: Spot exchangeInfo (for chain/address) ──")
url_sei = "https://api.binance.com/api/v3/exchangeInfo?symbol=HEIUSDT"
sei = fetch_json(url_sei)
if "_error" in sei:
    log(f"  Spot exchangeInfo: {sei['_error']}")
elif "symbols" in sei:
    for s in sei["symbols"]:
        if s.get("symbol") == "HEIUSDT":
            log(f"  baseAsset: {s.get('baseAsset')}")
            log(f"  status   : {s.get('status')}")
            log(f"  orderTypes: {s.get('orderTypes')}")
else:
    log(f"  Response: {str(sei)[:200]}")

# ═══════════════════════════════════════════════════════════════════════════
# H1 — PERP DAILY: LSR 4 ENDPOINTS (KHẨN CẤP — 30d only)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════════════════════╗")
log("║  H1 — PERP DAILY: LSR PERSIST (KHẨN CẤP — 30d retention only)       ║")
log("╚══════════════════════════════════════════════════════════════════════╝")

# Determine window: from perp listing or 30d ago, whichever is more recent
from datetime import timedelta
today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
cutoff_30d = today_utc - timedelta(days=30)

if perp_first_ts:
    listing_dt = datetime.fromtimestamp(perp_first_ts/1000, tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    window_start = max(listing_dt, cutoff_30d)
else:
    window_start = cutoff_30d

window_start_ms = int(window_start.timestamp() * 1000)
# Cutoff: yesterday 00:00 UTC (L-21: today not closed)
yesterday = today_utc - timedelta(days=1)
window_end_ms   = int(yesterday.timestamp() * 1000) + 86399999  # end of yesterday

log(f"  Window : {window_start.strftime('%Y-%m-%d')} → {yesterday.strftime('%Y-%m-%d')} (L-21: today not closed)")
log(f"  Reason : LSR 30d retention — persist NGAY")

def fetch_lsr(endpoint_name, url_base, symbol="HEIUSDT", period="1d", limit=30):
    """Fetch LSR endpoint, return list of dicts."""
    url = f"{url_base}?symbol={symbol}&period={period}&limit={limit}"
    d = fetch_json(url)
    if "_error" in d:
        log(f"  {endpoint_name}: ERROR — {d['_error']}")
        return []
    if isinstance(d, list):
        log(f"  {endpoint_name}: {len(d)} rows")
        return d
    log(f"  {endpoint_name}: unexpected response {str(d)[:100]}")
    return []

log()
log("── H1a: topLongShortPositionRatio (pos_r = longShortRatio) ──")
pos_data = fetch_lsr("topLSPosition",
    "https://fapi.binance.com/futures/data/topLongShortPositionRatio")

log()
log("── H1b: topLongShortAccountRatio (acc_r) ──")
acc_data = fetch_lsr("topLSAccount",
    "https://fapi.binance.com/futures/data/topLongShortAccountRatio")

log()
log("── H1c: globalLongShortAccountRatio (gLSR) ──")
gls_data = fetch_lsr("globalLSAccount",
    "https://fapi.binance.com/futures/data/globalLongShortAccountRatio")

log()
log("── H1d: takerlongshortRatio (taker buy/sell ratio) ──")
tkr_data = fetch_lsr("takerLSRatio",
    "https://fapi.binance.com/futures/data/takerlongshortRatio")

# Build date-keyed dict for each
def to_dict(rows, key="timestamp"):
    out = {}
    for r in rows:
        ts = r.get(key) or r.get("time") or r.get("t")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            out[dt] = r
    return out

pos_d  = to_dict(pos_data)
acc_d  = to_dict(acc_data)
gls_d  = to_dict(gls_data)
tkr_d  = to_dict(tkr_data)

all_dates = sorted(set(list(pos_d) + list(acc_d) + list(gls_d) + list(tkr_d)))
log()
log(f"  Combined dates: {len(all_dates)} ({all_dates[0] if all_dates else 'N/A'} → {all_dates[-1] if all_dates else 'N/A'})")

# Persist LSR raw to CSV
def share_to_ratio(s):
    """s = longAccount proportion 0→1 → ratio = s/(1-s)"""
    try:
        sv = float(s)
        if 0 < sv < 1:
            return round(sv / (1 - sv), 6)
        return sv  # already a ratio if >1
    except:
        return None

lsr_rows = []
for dt in all_dates:
    row = {"date": dt}
    p = pos_d.get(dt, {})
    a = acc_d.get(dt, {})
    g = gls_d.get(dt, {})
    t = tkr_d.get(dt, {})
    # pos_r: topLongShortPositionRatio longShortRatio field
    row["pos_r_raw"]  = p.get("longShortRatio")
    row["pos_long"]   = p.get("longAccount")
    row["pos_short"]  = p.get("shortAccount")
    # acc_r: topLongShortAccountRatio
    row["acc_r_raw"]  = a.get("longShortRatio")
    row["acc_long"]   = a.get("longAccount")
    row["acc_short"]  = a.get("shortAccount")
    # gLSR: globalLongShortAccountRatio
    row["glsr_raw"]   = g.get("longShortRatio")
    row["glsr_long"]  = g.get("longAccount")
    row["glsr_short"] = g.get("shortAccount")
    # taker buy/sell ratio
    row["taker_lsr_raw"] = t.get("buySellRatio")
    row["taker_buy_vol"] = t.get("buyVol")
    row["taker_sell_vol"]= t.get("sellVol")
    # Convert shares to ratio (unbounded) if needed
    # pos/acc/glsr: check if <1 (share) or >1 (ratio already)
    for fld in ["pos_r_raw", "acc_r_raw", "glsr_raw"]:
        v = row[fld]
        if v is not None:
            try:
                fv = float(v)
                if 0 < fv < 1:
                    row[fld + "_note"] = f"share→ratio={share_to_ratio(fv)}"
            except:
                pass
    lsr_rows.append(row)

# Write CSV
if lsr_rows:
    fieldnames = list(lsr_rows[0].keys())
    with open(LSR_F, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(lsr_rows)
    log(f"\n  LSR raw persisted → {LSR_F.name} ({len(lsr_rows)} rows)")
else:
    log("\n  WARN: no LSR rows to save")

# Print LSR table
log()
log("── H1 LSR TABLE ──")
log(f"  {'date':<12} {'pos_r':>8} {'acc_r':>8} {'gLSR':>8} {'tkr_ls':>8}")
log(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
for row in lsr_rows:
    ps = f"{float(row['pos_r_raw']):.4f}" if row['pos_r_raw'] else "—"
    ac = f"{float(row['acc_r_raw']):.4f}" if row['acc_r_raw'] else "—"
    gl = f"{float(row['glsr_raw']):.4f}"  if row['glsr_raw']  else "—"
    tk = f"{float(row['taker_lsr_raw']):.4f}" if row['taker_lsr_raw'] else "—"
    log(f"  {row['date']:<12} {ps:>8} {ac:>8} {gl:>8} {tk:>8}")

# ═══════════════════════════════════════════════════════════════════════════
# H1 — PERP DAILY: Main data (klines-based for px/vol/taker + oi + funding)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════════════════════╗")
log("║  H1 — PERP DAILY: Main data (px/vol/taker/funding/OI)               ║")
log("╚══════════════════════════════════════════════════════════════════════╝")

# klines perp 1d full
log()
log("── Perp klines 1d (fapi) ──")
if perp_first_ts:
    kl_url = f"https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&startTime={perp_first_ts}&limit=500"
else:
    kl_url = "https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&limit=500"
kl = fetch_json(kl_url)
perp_klines = []
if "_error" not in kl and isinstance(kl, list):
    # Filter: exclude today (L-21 not closed)
    today_ms = int(today_utc.timestamp() * 1000)
    for k in kl:
        if int(k[0]) < today_ms:
            dt = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            perp_klines.append({
                "date": dt,
                "open_ts": k[0],
                "o": float(k[1]),
                "h": float(k[2]),
                "l": float(k[3]),
                "c": float(k[4]),
                "vol_base": float(k[5]),
                "close_ts": k[6],
                "vol_quote": float(k[7]),  # vol_perp_usd
                "n_trades": k[8],
                "taker_base": float(k[9]),
                "taker_quote": float(k[10]),  # takerBuyQuoteVol (USDT)
            })
    log(f"  Perp klines: {len(perp_klines)} days ({perp_klines[0]['date'] if perp_klines else '—'} → {perp_klines[-1]['date'] if perp_klines else '—'})")
else:
    log(f"  Perp klines ERROR: {kl}")

# Funding history — get all available (limit=1000 to maximize)
log()
log("── Funding history (fapi fundingRate) ──")
fund_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=HEIUSDT&limit=1000"
fund_raw = fetch_json(fund_url)
fund_rows = []
if isinstance(fund_raw, list):
    log(f"  Funding rows raw: {len(fund_raw)}")
    for f_ in fund_raw:
        ts = f_.get("fundingTime")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc)
            fund_rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "hhmm": dt.strftime("%H:%M"),
                "fundingTime_ms": ts,
                "fundingRate": f_.get("fundingRate"),
                "markPrice": f_.get("markPrice"),
            })
else:
    log(f"  Funding ERROR: {fund_raw}")

# Infer fn per day (count settlements per day) and f_avg/min/max
from collections import defaultdict
fund_by_day = defaultdict(list)
for fr in fund_rows:
    fund_by_day[fr["date"]].append(float(fr["fundingRate"]) if fr["fundingRate"] else 0.0)

log(f"  Days with funding: {len(fund_by_day)}")
# Detect interval: check first day count
first_fund_day = sorted(fund_by_day.keys())[0] if fund_by_day else None
if first_fund_day:
    count0 = len(fund_by_day[first_fund_day])
    interval = "8h" if count0 <= 3 else "4h"
    log(f"  Settlement interval (detected): {interval} ({count0} settlements on {first_fund_day})")
    log(f"  fn per day expected: {'3' if interval=='8h' else '6'}")

# OI current snapshot
log()
log("── OI snapshot (fapi openInterest) ──")
oi_url = "https://fapi.binance.com/fapi/v1/openInterest?symbol=HEIUSDT"
oi_snap = fetch_json(oi_url)
if "_error" not in oi_snap:
    oi_tokens = float(oi_snap.get("openInterest", 0))
    oi_time   = oi_snap.get("time")
    oi_ts_str = datetime.fromtimestamp(int(oi_time)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if oi_time else "?"
    log(f"  OI tokens  : {oi_tokens:,.0f}")
    log(f"  Timestamp  : {oi_ts_str}")
    if perp_klines:
        last_close = perp_klines[-1]["c"]
        oi_usd = oi_tokens * last_close
        log(f"  OI USD     : ${oi_usd:,.0f} (× last close {last_close})")
else:
    log(f"  OI ERROR: {oi_snap}")

# premiumIndex / mark
log()
log("── premiumIndex (mark/index/funding) ──")
prem_url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=HEIUSDT"
prem = fetch_json(prem_url)
if "_error" not in prem:
    log(f"  markPrice          : {prem.get('markPrice')}")
    log(f"  indexPrice         : {prem.get('indexPrice')}")
    log(f"  lastFundingRate    : {prem.get('lastFundingRate')}")
    log(f"  nextFundingTime    : {datetime.fromtimestamp(int(prem.get('nextFundingTime',0))/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log(f"  estimatedSettlePrice: {prem.get('estimatedSettlePrice')}")
else:
    log(f"  premiumIndex ERROR: {prem}")

# Print klines table
log()
log("── H1 PERP KLINES TABLE (px/vol/taker) ──")
log(f"  {'date':<12} {'open':>9} {'high':>9} {'low':>9} {'close':>9} {'vol_usd':>14} {'taker%':>7}")
log(f"  {'-'*12} {'-'*9} {'-'*9} {'-'*9} {'-'*9} {'-'*14} {'-'*7}")
for k in perp_klines[-40:]:  # last 40 rows
    tpct = k['taker_quote'] / k['vol_quote'] * 100 if k['vol_quote'] > 0 else 0
    log(f"  {k['date']:<12} {k['o']:>9.6f} {k['h']:>9.6f} {k['l']:>9.6f} {k['c']:>9.6f} {k['vol_quote']:>14,.0f} {tpct:>6.1f}%")

# Print funding table (last 30 rows)
log()
log("── H1 FUNDING TABLE (last 30 settlements) ──")
log(f"  {'date':<12} {'time':>6} {'rate':>12} {'markPrice':>12}")
log(f"  {'-'*12} {'-'*6} {'-'*12} {'-'*12}")
for fr in fund_rows[-30:]:
    log(f"  {fr['date']:<12} {fr['hhmm']:>6} {float(fr['fundingRate'] or 0):>12.6f} {fr['markPrice'] or '—':>12}")

# fn per day table
log()
log("── H1 fn PER DAY ──")
log(f"  {'date':<12} {'fn':>4} {'f_avg':>12} {'f_min':>12} {'f_max':>12} {'flag':>10}")
log(f"  {'-'*12} {'-'*4} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
for dt in sorted(fund_by_day.keys()):
    rates = fund_by_day[dt]
    fn = len(rates)
    favg = sum(rates)/fn
    fmin = min(rates)
    fmax = max(rates)
    flag = "SUSPECT" if fn < 6 else ("OK" if fn >= 6 else "")
    # For 8h interval, fn=3 is normal
    if first_fund_day and interval == "8h" and fn == 3:
        flag = "OK(8h)"
    elif first_fund_day and interval == "4h" and fn < 6:
        flag = "SUSPECT"
    log(f"  {dt:<12} {fn:>4} {favg:>12.6f} {fmin:>12.6f} {fmax:>12.6f} {flag:>10}")

# Write log
with open(LOG_F, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
log(f"\n[H0+H1 DONE] → {LOG_F.name}")

"""
HEI cold-start pack — H2 (klines full), H3 (derived + GOM screen), H4 (spot).
Output: scratch/hei_h2h4_raw_20260808.txt + scratch/hei_perp_full_20260808.csv
        scratch/hei_spot_full_20260808.csv
"""
import sys, io, json, csv, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(r"D:\Data back test\whale_data\scratch")
LOG_F   = OUT_DIR / "hei_h2h4_raw_20260808.txt"
PERP_F  = OUT_DIR / "hei_perp_full_20260808.csv"
SPOT_F  = OUT_DIR / "hei_spot_full_20260808.csv"

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

today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today_utc - timedelta(days=1)
today_ms  = int(today_utc.timestamp() * 1000)

log("=" * 70)
log(f"HEI H2+H3+H4  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# H2 — PERP KLINES FULL WINDOW (paginate to get all 541 days)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H2 — PERP KLINES 1d FULL WINDOW (paginate)          ║")
log("╚══════════════════════════════════════════════════════╝")

perp_listing_ms = 1739404800000  # 2025-02-13
all_perp_klines = []

# Page 1: from listing, limit 500
url1 = f"https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&startTime={perp_listing_ms}&limit=500"
d1 = fetch_json(url1)
if isinstance(d1, list):
    # Filter out today
    page1 = [k for k in d1 if int(k[0]) < today_ms]
    all_perp_klines.extend(page1)
    log(f"  Page 1: {len(page1)} rows, last = {datetime.fromtimestamp(page1[-1][0]/1000,tz=timezone.utc).strftime('%Y-%m-%d') if page1 else '?'}")
    # Page 2: from last+1 day
    if page1:
        next_start = int(page1[-1][0]) + 86400000
        url2 = f"https://fapi.binance.com/fapi/v1/klines?symbol=HEIUSDT&interval=1d&startTime={next_start}&limit=200"
        d2 = fetch_json(url2)
        if isinstance(d2, list):
            page2 = [k for k in d2 if int(k[0]) < today_ms]
            all_perp_klines.extend(page2)
            log(f"  Page 2: {len(page2)} rows, last = {datetime.fromtimestamp(page2[-1][0]/1000,tz=timezone.utc).strftime('%Y-%m-%d') if page2 else '?'}")
else:
    log(f"  ERROR page1: {d1}")

log(f"  TOTAL perp klines: {len(all_perp_klines)}")

# Parse
def parse_klines(raw_list, source="fapi"):
    rows = []
    for k in raw_list:
        dt = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        qv = float(k[7])
        tq = float(k[10])
        rows.append({
            "date": dt,
            "open_ts_ms": k[0],
            "o": float(k[1]),
            "h": float(k[2]),
            "l": float(k[3]),
            "c": float(k[4]),
            "vol_base": float(k[5]),
            "vol_quote_usd": qv,
            "n_trades": int(k[8]),
            "taker_buy_quote": tq,
            "taker_pct": round(tq/qv*100, 4) if qv > 0 else None,
            "px_avg": round((float(k[2])+float(k[3])+float(k[4]))/3, 8),  # (H+L+C)/3 typical
            "ret_1d": None,  # fill later
            "source": source,
        })
    return rows

perp_rows = parse_klines(all_perp_klines, "fapi_1d")

# Fill ret_1d
for i in range(1, len(perp_rows)):
    c_prev = perp_rows[i-1]["c"]
    c_cur  = perp_rows[i]["c"]
    if c_prev and c_prev > 0:
        perp_rows[i]["ret_1d"] = round((c_cur - c_prev) / c_prev * 100, 4)

log(f"  Date range: {perp_rows[0]['date']} → {perp_rows[-1]['date']}")

# Save
with open(PERP_F, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(perp_rows[0].keys()))
    w.writeheader()
    w.writerows(perp_rows)
log(f"  Saved: {PERP_F.name}")

# Summary stats
closes = [r["c"] for r in perp_rows]
vols   = [r["vol_quote_usd"] for r in perp_rows]
log()
log("── H2 Highlights ──")
log(f"  px_min : {min(closes):.6f}  ({perp_rows[closes.index(min(closes))]['date']})")
log(f"  px_max : {max(closes):.6f}  ({perp_rows[closes.index(max(closes))]['date']})")
log(f"  px_last: {closes[-1]:.6f}  ({perp_rows[-1]['date']})")
log(f"  vol_max: ${max(vols):,.0f}  ({perp_rows[vols.index(max(vols))]['date']})")
log(f"  vol_avg: ${sum(vols)/len(vols):,.0f}")

# Days |ret|>10%
big_moves = [(r["date"], round(r["ret_1d"],2)) for r in perp_rows if r.get("ret_1d") and abs(r["ret_1d"]) > 10]
log(f"\n  Days |ret|>10% ({len(big_moves)} days):")
for d_, r_ in big_moves[-20:]:
    log(f"    {d_}: {r_:+.1f}%")

# Days vol ≥ 3× med14 (bait probe candidates)
# Compute rolling med14
def med14_series(rows, field):
    result = [None]*14
    for i in range(14, len(rows)):
        window = [rows[j][field] for j in range(i-14, i)]
        window_sorted = sorted(window)
        med = (window_sorted[6]+window_sorted[7])/2
        result.append(med)
    return result

vol_series  = [r["vol_quote_usd"] for r in perp_rows]
med14_vols  = med14_series(perp_rows, "vol_quote_usd")
bait8x = []
for i, (r, med) in enumerate(zip(perp_rows, med14_vols)):
    if med and r["vol_quote_usd"] >= 8 * med:
        bait8x.append((r["date"], r["vol_quote_usd"], med, r["vol_quote_usd"]/med))
log(f"\n  Vol ≥8× med14 candidates (bait-probe L-15) — {len(bait8x)} days:")
for d_, v_, m_, x_ in bait8x:
    log(f"    {d_}: vol=${v_:,.0f}  med14=${m_:,.0f}  ratio={x_:.1f}×")

# Print last 45 rows
log()
log("── H2 PERP KLINES TABLE (last 45 rows) ──")
log(f"  {'date':<12} {'open':>9} {'high':>9} {'low':>9} {'close':>9} {'vol_usd':>14} {'taker%':>7} {'ret%':>7}")
log(f"  {'-'*12} {'-'*9} {'-'*9} {'-'*9} {'-'*9} {'-'*14} {'-'*7} {'-'*7}")
for r in perp_rows[-45:]:
    ret_s = f"{r['ret_1d']:+.1f}%" if r.get("ret_1d") else "  —"
    tp_s  = f"{r['taker_pct']:.1f}%" if r.get("taker_pct") else "  —"
    log(f"  {r['date']:<12} {r['o']:>9.5f} {r['h']:>9.5f} {r['l']:>9.5f} {r['c']:>9.5f} {r['vol_quote_usd']:>14,.0f} {tp_s:>7} {ret_s:>7}")

# ═══════════════════════════════════════════════════════════════════════════
# H4 — SPOT KLINES (api/v3)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H4 — SPOT KLINES 1d (api/v3)                        ║")
log("╚══════════════════════════════════════════════════════╝")

spot_listing_ms = 1739404800000  # 2025-02-13 same as perp
all_spot = []

# Page 1
url_s1 = f"https://api.binance.com/api/v3/klines?symbol=HEIUSDT&interval=1d&startTime={spot_listing_ms}&limit=500"
ds1 = fetch_json(url_s1)
if isinstance(ds1, list):
    p1 = [k for k in ds1 if int(k[0]) < today_ms]
    all_spot.extend(p1)
    log(f"  Spot page 1: {len(p1)} rows")
    if p1:
        next_s = int(p1[-1][0]) + 86400000
        url_s2 = f"https://api.binance.com/api/v3/klines?symbol=HEIUSDT&interval=1d&startTime={next_s}&limit=200"
        ds2 = fetch_json(url_s2)
        if isinstance(ds2, list):
            p2 = [k for k in ds2 if int(k[0]) < today_ms]
            all_spot.extend(p2)
            log(f"  Spot page 2: {len(p2)} rows")
else:
    log(f"  Spot ERROR: {ds1}")

spot_rows = []
for k in all_spot:
    dt  = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    qv  = float(k[7])
    tq  = float(k[10])  # takerBuyQuoteAssetVolume (USDT)
    spot_rows.append({
        "date": dt,
        "o": float(k[1]),
        "h": float(k[2]),
        "l": float(k[3]),
        "c": float(k[4]),
        "vol_spot_usd": qv,
        "taker_spot_pct": round(tq/qv*100, 4) if qv > 0 else None,
        "venue": "binance_spot",
        "source": "api/v3/klines k[10]/k[7]",
    })

log(f"  Total spot rows: {len(spot_rows)} ({spot_rows[0]['date'] if spot_rows else '?'} → {spot_rows[-1]['date'] if spot_rows else '?'})")

# Guard L-29 (spot/perp >3× → suspect)
perp_by_date = {r["date"]: r for r in perp_rows}
spot_l29_flags = []
for sr in spot_rows:
    pr = perp_by_date.get(sr["date"])
    if pr and pr["vol_quote_usd"] > 0:
        ratio = sr["vol_spot_usd"] / pr["vol_quote_usd"]
        sr["spot_perp_ratio"] = round(ratio, 4)
        if ratio > 3:
            sr["l29_flag"] = "ABSTAIN_VOL_SPOT"
            spot_l29_flags.append((sr["date"], ratio))
        else:
            sr["l29_flag"] = ""
    else:
        sr["spot_perp_ratio"] = None
        sr["l29_flag"] = ""

if spot_l29_flags:
    log(f"\n  L-29 flags (spot/perp >3×): {len(spot_l29_flags)}")
    for d_, r_ in spot_l29_flags[-10:]:
        log(f"    {d_}: {r_:.2f}×")
else:
    log("  L-29: no flags (spot/perp <3× all days)")

# Save spot CSV
with open(SPOT_F, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(spot_rows[0].keys()))
    w.writeheader()
    w.writerows(spot_rows)
log(f"  Saved: {SPOT_F.name}")

# H4b — depth snapshot: bids/asks ±2%
log()
log("── H4b: Order book depth ±2% (snapshot) ──")
depth_url = "https://api.binance.com/api/v3/depth?symbol=HEIUSDT&limit=500"
dep = fetch_json(depth_url)
snap_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
if "_error" not in dep:
    bids = dep.get("bids", [])
    asks = dep.get("asks", [])
    # Get last price from spot or mark
    last_px_raw = fetch_json("https://api.binance.com/api/v3/ticker/price?symbol=HEIUSDT")
    last_px = float(last_px_raw.get("price", 0)) if "_error" not in last_px_raw else 0
    log(f"  Snapshot time : {snap_time}")
    log(f"  Last price    : {last_px}")
    low2  = last_px * 0.98
    high2 = last_px * 1.02
    # bid depth within 2%
    bid_depth = sum(float(b[0])*float(b[1]) for b in bids if float(b[0]) >= low2)
    ask_depth = sum(float(a[0])*float(a[1]) for a in asks if float(a[0]) <= high2)
    log(f"  Bid depth ±2%  : ${bid_depth:,.0f} USDT")
    log(f"  Ask depth ±2%  : ${ask_depth:,.0f} USDT")
    log(f"  Bid/Ask ratio  : {(bid_depth/ask_depth if ask_depth else 0):.3f}")
    log(f"  Bids total (limit 500): {len(bids)}")
    log(f"  Asks total (limit 500): {len(asks)}")
    log(f"  NOTE: One snapshot only (need ≥2 shots ≥4h apart for L-23 compliance)")
else:
    log(f"  Depth ERROR: {dep}")

# Alpha layer
log()
log("── H4c: Alpha Layer ──")
log("  alpha_id: NOT in alpha_id_map.json (searched 'HEI')")
log("  Alpha layer = ABSTAIN (no alpha_id → no alpha klines to collect)")
log("  Taker alpha: BANNED regardless (k[9]==k[5] semantically broken)")

# ═══════════════════════════════════════════════════════════════════════════
# H3 — DERIVED (per day)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H3 — DERIVED METRICS                                ║")
log("╚══════════════════════════════════════════════════════╝")

# Load LSR from CSV we already saved
LSR_F = OUT_DIR / "hei_lsr_raw_20260808.csv"
lsr_by_date = {}
if LSR_F.exists():
    with open(LSR_F, encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            lsr_by_date[row["date"]] = row

# Load funding by day from H1 data (rebuild from file or recompute)
# We'll read from the log or re-fetch minimal version
# Since we have fund_rows in memory: re-fetch a summary
fund_url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=HEIUSDT&limit=1000"
fund_raw2 = fetch_json(fund_url)
fund_by_day2 = defaultdict(list)
if isinstance(fund_raw2, list):
    for fr in fund_raw2:
        ts = fr.get("fundingTime")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            fund_by_day2[dt].append(float(fr.get("fundingRate", 0)))

# Build combined DAILY rows (recent 30d where LSR available = join)
spot_by_date = {r["date"]: r for r in spot_rows}

# Key derived fields per day
derived_rows = []
# PIN band for funding
PIN_LO = 4e-5; PIN_HI = 6e-5

def in_pin(rate):
    return PIN_LO <= rate <= PIN_HI

for r in perp_rows:
    dt   = r["date"]
    lsr  = lsr_by_date.get(dt, {})
    sp   = spot_by_date.get(dt, {})
    fday = fund_by_day2.get(dt, [])

    pos_r = float(lsr.get("pos_r_raw", 0) or 0)
    acc_r = float(lsr.get("acc_r_raw", 0) or 0)
    glsr  = float(lsr.get("glsr_raw", 0)  or 0)
    tkls  = float(lsr.get("taker_lsr_raw", 0) or 0)

    fn    = len(fday)
    f_avg = sum(fday)/fn if fday else None
    f_min = min(fday) if fday else None
    f_max = max(fday) if fday else None
    # pin_streak: count consecutive days where all settlements in PIN band
    # (compute below after full table)
    # For now: pin_day = all settlements in PIN?
    pin_day = all(in_pin(f) for f in fday) if fday else None

    # div_raw: divergence = pos_r * gLSR (proxy for L-vs-S interaction)
    div_raw = round(pos_r * glsr, 4) if pos_r and glsr else None

    row = {
        "date": dt,
        # PERP MACHINE
        "px_avg":       r["px_avg"],
        "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"],
        "vol_perp_usd": r["vol_quote_usd"],
        "taker_buy_pct": r["taker_pct"],
        "ret_1d":       r["ret_1d"],
        "fn":           fn if fn > 0 else None,
        "f_avg":        round(f_avg, 8) if f_avg is not None else None,
        "f_min":        round(f_min, 8) if f_min is not None else None,
        "f_max":        round(f_max, 8) if f_max is not None else None,
        "pin_day":      pin_day,
        "data_ok":      fn >= 6 if fn > 0 else False,
        "low_conf":     fn < 6 if fn > 0 else True,
        # CROWD
        "pos_r":        pos_r if pos_r > 0 else None,
        "acc_r":        acc_r if acc_r > 0 else None,
        "gLSR":         glsr  if glsr  > 0 else None,
        "taker_lsr":    tkls  if tkls  > 0 else None,
        "div_raw":      div_raw,
        # SPOT
        "vol_spot_usd": sp.get("vol_spot_usd"),
        "taker_spot_pct": sp.get("taker_spot_pct"),
        "spot_perp_ratio": sp.get("spot_perp_ratio"),
        "l29_flag":     sp.get("l29_flag", ""),
        # ALPHA
        "vol_alpha":    "ABSTAIN(no_alpha_id)",
        "taker_alpha":  "BANNED",
    }
    derived_rows.append(row)

# Fill pin_streak (rolling streak of consecutive pin_day=True)
streak = 0
for i, r in enumerate(derived_rows):
    if r["pin_day"] is True:
        streak += 1
    elif r["pin_day"] is False:
        streak = 0
    # If None (no funding data), don't reset (gap → reset)
    elif r["pin_day"] is None:
        streak = 0  # gap = reset
    r["pin_streak"] = streak

# Fill oi_vs_med14, div_avg3, glsr_slope_5d, d_pos_3d, d_acc_3d
# OI: we only have current snapshot, not history → fill daily OI from... need OI hist
# Binance fapi openInterestHist endpoint (note: prev probe showed 404)
log()
log("── H3: OI historical (fapi openInterestHist) ──")
oi_hist_url = "https://fapi.binance.com/futures/data/openInterestHist?symbol=HEIUSDT&period=1d&limit=30"
oih = fetch_json(oi_hist_url)
oi_by_date = {}
if "_error" not in oih and isinstance(oih, list):
    log(f"  OI hist rows: {len(oih)}")
    for o in oih:
        ts = o.get("timestamp")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            oi_by_date[dt] = {
                "oi_usd": float(o.get("sumOpenInterestValue", 0)),
                "oi_token": float(o.get("sumOpenInterest", 0)),
            }
    if oi_by_date:
        dates_ = sorted(oi_by_date.keys())
        log(f"  OI hist range: {dates_[0]} → {dates_[-1]}")
else:
    log(f"  OI hist: {oih if isinstance(oih, dict) else str(oih)[:100]}")

# Add OI to derived_rows
for r in derived_rows:
    oi = oi_by_date.get(r["date"])
    if oi:
        r["oi_usd"]   = oi["oi_usd"]
        r["oi_token"] = oi["oi_token"]
    else:
        r["oi_usd"]   = None
        r["oi_token"] = None

# OI vs med14
oi_vals = [r.get("oi_usd") for r in derived_rows]
oi_med14 = [None]*14
for i in range(14, len(derived_rows)):
    window = [v for v in oi_vals[i-14:i] if v is not None]
    if len(window) >= 7:
        window_s = sorted(window)
        n = len(window_s)
        med = (window_s[n//2-1]+window_s[n//2])/2 if n%2==0 else window_s[n//2]
        oi_med14.append(med)
    else:
        oi_med14.append(None)

for i, r in enumerate(derived_rows):
    r["oi_vs_med14"] = round(r["oi_usd"]/oi_med14[i], 3) if (r.get("oi_usd") and oi_med14[i]) else None

# div_avg3
for i in range(2, len(derived_rows)):
    divs = [derived_rows[j]["div_raw"] for j in range(i-2, i+1) if derived_rows[j]["div_raw"] is not None]
    derived_rows[i]["div_avg3"] = round(sum(divs)/len(divs), 4) if len(divs) == 3 else None

# glsr_slope_5d (gLSR[i] / gLSR[i-5])
for i in range(5, len(derived_rows)):
    g_now  = derived_rows[i]["gLSR"]
    g_prev = derived_rows[i-5]["gLSR"]
    if g_now and g_prev and g_prev > 0:
        derived_rows[i]["glsr_slope_5d"] = round((g_now - g_prev) / g_prev * 100, 2)
    else:
        derived_rows[i]["glsr_slope_5d"] = None

# d_pos_3d (pos_r change over 3 days)
for i in range(3, len(derived_rows)):
    p_now  = derived_rows[i]["pos_r"]
    p_prev = derived_rows[i-3]["pos_r"]
    if p_now and p_prev and p_prev > 0:
        derived_rows[i]["d_pos_3d"] = round((p_now - p_prev) / p_prev * 100, 2)
    else:
        derived_rows[i]["d_pos_3d"] = None

# d_acc_3d
for i in range(3, len(derived_rows)):
    a_now  = derived_rows[i]["acc_r"]
    a_prev = derived_rows[i-3]["acc_r"]
    if a_now and a_prev and a_prev > 0:
        derived_rows[i]["d_acc_3d"] = round((a_now - a_prev) / a_prev * 100, 2)
    else:
        derived_rows[i]["d_acc_3d"] = None

# ── GOM-A/B SCREEN (NHÃN BẮT BUỘC — chưa ký, screen-tier only) ──────────────
log()
log("── H3: GOM-A/B Screen (gom_detect_spec v1.1 CHƯA KÝ — SCREEN-tier tham chiếu offline) ──")

# GOM-A conditions (A1-A5):
# A1: vol_perp ≥ 3× med14
# A2: gLSR_slope_5d < 0 (gLSR decreasing)
# A3: pos_r > 1.5
# A4: funding avg ≥ pin floor (f_avg ≥ 4e-5)
# A5: taker_buy ≥ 45%
# GOM-B (B1-B4):
# B1: pos_r persist ≥7 consecutive days (>1.5)
# B2: funding pin (f_avg in [4e-5,6e-5] and pin_day)
# B3: absorption (vol_perp ≥ 3× med14 on red day, taker≥50%)
# B4: OI ignore (OI ≥ 1.5× floor)

vol_med14 = med14_series(derived_rows, "vol_perp_usd")

# B1: rolling pos_r persist ≥7d
pos_r_persist = [0]*len(derived_rows)
cnt = 0
for i, r in enumerate(derived_rows):
    if r["pos_r"] and r["pos_r"] > 1.5:
        cnt += 1
    else:
        cnt = 0
    pos_r_persist[i] = cnt

gom_screen_rows = []
for i, r in enumerate(derived_rows):
    dt = r["date"]
    med14_v = vol_med14[i]
    vol_3x  = (r["vol_perp_usd"] / med14_v >= 3) if (med14_v and med14_v > 0) else False
    vol_8x  = (r["vol_perp_usd"] / med14_v >= 8) if (med14_v and med14_v > 0) else False

    # GOM-A
    A1 = vol_3x
    A2 = (r.get("glsr_slope_5d") is not None and r["glsr_slope_5d"] < 0)
    A3 = (r["pos_r"] is not None and r["pos_r"] > 1.5)
    A4 = (r["f_avg"] is not None and r["f_avg"] >= PIN_LO)
    A5 = (r["taker_buy_pct"] is not None and r["taker_buy_pct"] >= 45)
    gom_a = A1 and A2 and A3 and A4 and A5

    # GOM-B
    B1 = (pos_r_persist[i] >= 7)
    B2 = (r["pin_day"] is True)
    # B3: vol ≥ 3× + red day (ret_1d < 0) + taker ≥ 50%
    B3 = (vol_3x and r.get("ret_1d") is not None and r["ret_1d"] < 0
          and r["taker_buy_pct"] is not None and r["taker_buy_pct"] >= 50)
    # B4: OI ≥ 1.5× min OI in window (simplified: oi_vs_med14 ≥ 1.5)
    B4 = (r.get("oi_vs_med14") is not None and r["oi_vs_med14"] >= 1.5)
    gom_b = B1 and (B2 or B3) and B4

    r["gom_A1"]=A1; r["gom_A2"]=A2; r["gom_A3"]=A3; r["gom_A4"]=A4; r["gom_A5"]=A5
    r["gom_A_screen"]=gom_a
    r["gom_B1"]=B1; r["gom_B2"]=B2; r["gom_B3"]=B3; r["gom_B4"]=B4
    r["gom_B_screen"]=gom_b
    r["vol_vs_med14"] = round(r["vol_perp_usd"]/med14_v, 2) if (med14_v and med14_v > 0) else None

    if gom_a or gom_b:
        gom_screen_rows.append(r)

log(f"  GOM-A screen fires: {sum(1 for r in derived_rows if r.get('gom_A_screen'))}")
log(f"  GOM-B screen fires: {sum(1 for r in derived_rows if r.get('gom_B_screen'))}")
log()
log("  NHÃN BẮT BUỘC: 'gom_detect_spec v1.1 CHƯA KÝ — SCREEN-tier tham chiếu offline, không phải signal chính thức'")

# Print GOM screen fires
if gom_screen_rows:
    log()
    log("  GOM screen fire dates:")
    for r in gom_screen_rows:
        log(f"    {r['date']}: A={r['gom_A_screen']} (A1={r['gom_A1']},A2={r['gom_A2']},A3={r['gom_A3']},A4={r['gom_A4']},A5={r['gom_A5']}) "
            f"B={r['gom_B_screen']} (B1={r['gom_B1']},B2={r['gom_B2']},B3={r['gom_B3']},B4={r['gom_B4']})")

# Print last 35 days of derived table
log()
log("── H3 DERIVED TABLE (recent 35 rows, where LSR available) ──")
log(f"  {'date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'fn':>4} {'f_avg':>10} {'pin':>4} {'streak':>6} {'div_raw':>8} {'d_pos3d':>8}")
log(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*7} {'-'*4} {'-'*10} {'-'*4} {'-'*6} {'-'*8} {'-'*8}")
for r in derived_rows[-35:]:
    ps = f"{r['pos_r']:.4f}"   if r.get("pos_r") else "  —"
    ac = f"{r['acc_r']:.4f}"   if r.get("acc_r") else "  —"
    gl = f"{r['gLSR']:.4f}"    if r.get("gLSR")  else "  —"
    fn_s = str(r["fn"]) if r["fn"] else "—"
    fa_s = f"{r['f_avg']:.6f}" if r["f_avg"] is not None else "     —"
    pin_s = "PIN" if r["pin_day"] is True else ("  ✗" if r["pin_day"] is False else "  —")
    str_s = str(r["pin_streak"])
    dv_s = f"{r['div_raw']:.4f}" if r.get("div_raw") else "   —"
    dp_s = f"{r['d_pos_3d']:+.1f}%" if r.get("d_pos_3d") else "   —"
    log(f"  {r['date']:<12} {ps:>7} {ac:>7} {gl:>7} {fn_s:>4} {fa_s:>10} {pin_s:>4} {str_s:>6} {dv_s:>8} {dp_s:>8}")

# Spot table last 45 rows
log()
log("── H4 SPOT TABLE (last 45 rows) ──")
log(f"  {'date':<12} {'vol_spot_usd':>14} {'taker_spot%':>12} {'sp/perp':>8} {'L29':>10}")
log(f"  {'-'*12} {'-'*14} {'-'*12} {'-'*8} {'-'*10}")
for r in spot_rows[-45:]:
    ts_s = f"{r['taker_spot_pct']:.1f}%" if r.get("taker_spot_pct") else "   —"
    sp_s = f"{r['spot_perp_ratio']:.3f}x" if r.get("spot_perp_ratio") else "  —"
    l29  = r.get("l29_flag","")
    log(f"  {r['date']:<12} {r['vol_spot_usd']:>14,.0f} {ts_s:>12} {sp_s:>8} {l29:>10}")

# Write final log
with open(LOG_F, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
log(f"\n[H2+H3+H4 DONE] → {LOG_F.name}")

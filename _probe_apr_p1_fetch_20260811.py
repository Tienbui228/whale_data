"""
_probe_apr_p1_fetch_20260811.py
P-1: Fetch APRUSDT klines/LSR/OI/funding for Aug 10-12 2026.
Also reads all existing DAILY data for analytics prep (P-2→P-5).
data-source: fapi.binance.com, freshwatch local store
machine: local scratch
date-range: 2026-08-10 → 2026-08-12
code-commit: TBD
"""
import sys, io, json, math, statistics, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests, openpyxl
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE    = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"

def log(s=""): print(s, flush=True)
SESS = requests.Session()
SESS.headers.update({"User-Agent": "Mozilla/5.0"})

def get(url, params=None, timeout=15):
    try:
        r = SESS.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e)}

# ── Read existing DAILY (for rolling computations) ───────────────────────────
log("=== LOAD EXISTING DAILY ===")
wb = openpyxl.load_workbook(CASE, data_only=True, read_only=True)
sh = wb["DAILY"]
all_rows = list(sh.iter_rows(values_only=True))
hdr = list(all_rows[1])
data_rows = [list(r) for r in all_rows[2:]]
wb.close()

col_map = {str(h).lower().strip(): i for i, h in enumerate(hdr) if h}

def gcol(row, *keys):
    for k in keys:
        kl = k.lower().strip()
        if kl in col_map:
            v = row[col_map[kl]]
            if v is not None: return v
    for k in keys:
        kl = k.lower().strip()
        for ck, ci in col_map.items():
            if kl in ck:
                v = row[ci]
                if v is not None: return v
    return None

last_date = str(data_rows[-1][0]) if data_rows else "?"
log(f"  DAILY rows loaded: {len(data_rows)} | last date: {last_date}")

# ── Fetch new klines (last 10 rows for safety) ───────────────────────────────
log("\n=== FETCH klines (1d, last 10) ===")
klines_raw = get("https://fapi.binance.com/fapi/v1/klines",
                 {"symbol": "APRUSDT", "interval": "1d", "limit": 10})
if "_error" in klines_raw:
    log(f"  ERROR klines: {klines_raw['_error']}")
    klines_new = {}
else:
    # Each kline: [open_time, o, h, l, c, vol, close_time, quote_vol, trades, taker_buy_vol, taker_buy_quote_vol, ignore]
    klines_new = {}
    today_ts = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    for k in klines_raw:
        ts_ms = k[0]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d_str = dt.strftime("%Y-%m-%d")
        if dt >= today_ts:
            log(f"  L-21 skip partial candle: {d_str}")
            continue
        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_q = float(k[7])   # quote volume = vol in USDT
        tb_q  = float(k[10])  # taker buy quote volume
        total_q_safe = vol_q if vol_q > 0 else float("nan")
        taker_pct = tb_q / total_q_safe * 100 if not math.isnan(total_q_safe) else None
        klines_new[d_str] = {
            "o": o, "h": h, "l": l, "c": c,
            "vol_perp_usd": vol_q,
            "taker_buy_pct": taker_pct,
            "px_avg": (h + l + c) / 3,
        }
        log(f"  {d_str}: o={o} h={h} l={l} c={c} vol=${vol_q:,.0f} taker={taker_pct:.1f}%")

# ── Fetch funding (recent 100 entries) ───────────────────────────────────────
log("\n=== FETCH funding rates ===")
funding_raw = get("https://fapi.binance.com/fapi/v1/fundingRate",
                  {"symbol": "APRUSDT", "limit": 100})
if "_error" in funding_raw:
    log(f"  ERROR funding: {funding_raw['_error']}")
    funding_by_date = {}
else:
    # Each: {symbol, fundingTime, fundingRate, markPrice}
    funding_by_date = {}
    for fr in funding_raw:
        dt = datetime.fromtimestamp(fr["fundingTime"]/1000, tz=timezone.utc)
        d_str = dt.strftime("%Y-%m-%d")
        if d_str not in funding_by_date:
            funding_by_date[d_str] = []
        funding_by_date[d_str].append(float(fr["fundingRate"]))
    # Show last 7 days
    for d in sorted(funding_by_date.keys())[-7:]:
        rates = funding_by_date[d]
        f_avg = sum(rates) / len(rates)
        log(f"  {d}: n={len(rates)} f_avg={f_avg:.6f} f_min={min(rates):.6f} f_max={max(rates):.6f}")

# ── Fetch OI history ──────────────────────────────────────────────────────────
log("\n=== FETCH OI history ===")
oi_raw = get("https://fapi.binance.com/futures/data/openInterestHist",
             {"symbol": "APRUSDT", "period": "1d", "limit": 10})
if "_error" in oi_raw:
    log(f"  ERROR OI: {oi_raw['_error']}")
    oi_by_date = {}
else:
    oi_by_date = {}
    for row in oi_raw:
        dt = datetime.fromtimestamp(row["timestamp"]/1000, tz=timezone.utc)
        d_str = dt.strftime("%Y-%m-%d")
        oi_by_date[d_str] = {
            "oi_token": float(row["sumOpenInterest"]),
            "oi_usd":   float(row["sumOpenInterestValue"]),
        }
        log(f"  {d_str}: oi_usd=${float(row['sumOpenInterestValue']):,.0f} oi_token={float(row['sumOpenInterest']):,.0f}")

# ── Fetch LSR (3 endpoints) ───────────────────────────────────────────────────
log("\n=== FETCH LSR ===")
lsr_endpoints = {
    "globalLSR": "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
    "topPos":    "https://fapi.binance.com/futures/data/topLongShortPositionRatio",
    "topAcc":    "https://fapi.binance.com/futures/data/topLongShortAccountRatio",
    "taker":     "https://fapi.binance.com/futures/data/takerlongshortRatio",
}
lsr_data = {}  # date -> {pos_r, acc_r, gLSR, taker_lsr}
for name, url in lsr_endpoints.items():
    resp = get(url, {"symbol": "APRUSDT", "period": "1d", "limit": 10})
    if "_error" in resp:
        log(f"  {name}: ERROR {resp['_error']}")
    else:
        log(f"  {name}: {len(resp)} rows")
        for row in resp[-5:]:
            dt = datetime.fromtimestamp(row["timestamp"]/1000, tz=timezone.utc)
            d_str = dt.strftime("%Y-%m-%d")
            if d_str not in lsr_data:
                lsr_data[d_str] = {}
            if name == "topPos":
                try:
                    v = float(row.get("longShortRatio", row.get("longShortPositionRatio", "nan")))
                    lsr_data[d_str]["pos_r"] = v
                    log(f"    topPos {d_str}: pos_r={v:.4f}")
                except: pass
            elif name == "topAcc":
                try:
                    v = float(row.get("longShortRatio", row.get("longShortAccountRatio", "nan")))
                    lsr_data[d_str]["acc_r"] = v
                    log(f"    topAcc {d_str}: acc_r={v:.4f}")
                except: pass
            elif name == "globalLSR":
                try:
                    v = float(row.get("longShortRatio", "nan"))
                    lsr_data[d_str]["gLSR"] = v
                    log(f"    gLSR   {d_str}: gLSR={v:.4f}")
                except: pass
            elif name == "taker":
                try:
                    v = float(row.get("buySellRatio", "nan"))
                    lsr_data[d_str]["taker_lsr"] = v
                    log(f"    taker  {d_str}: taker_lsr={v:.4f}")
                except: pass

# ── Bybit spot check (filter correctly) ──────────────────────────────────────
log("\n=== BYBIT APR SPOT CHECK ===")
bybit_apr = get("https://api.bybit.com/v5/market/tickers",
                {"category": "spot", "symbol": "APRUSDT"})
if "_error" in bybit_apr:
    log(f"  ERROR: {bybit_apr['_error']}")
else:
    blist = bybit_apr.get("result", {}).get("list", [])
    if blist:
        for item in blist:
            log(f"  FOUND Bybit APR spot: {item}")
    else:
        log("  No APRUSDT on Bybit spot")

# ── GeckoTerminal BSC pool detail ────────────────────────────────────────────
log("\n=== GECKO BSC APR/BNB POOL DETAIL ===")
# BSC PancakeSwap pool: 0xff84bf0ab4772bfa39... (truncated from P-0)
# Get APR token on BSC
gt_bsc = get("https://api.geckoterminal.com/api/v2/networks/bsc/tokens/0x299ad4299da5b2b93fba4c96967b040c7f611099",
             timeout=20)
if "_error" in gt_bsc:
    log(f"  ERROR: {gt_bsc['_error']}")
else:
    attrs = gt_bsc.get("data", {}).get("attributes", {})
    log(f"  BSC token: {attrs.get('name')} ({attrs.get('symbol')})")
    log(f"  Price USD: {attrs.get('price_usd')}")
    log(f"  Market cap: {attrs.get('market_cap_usd')}")
    log(f"  FDV: {attrs.get('fdv_usd')}")
    log(f"  Vol 24h: {attrs.get('volume_usd', {})}")

# ── Summary: dates to append ──────────────────────────────────────────────────
log("\n=== DATES TO APPEND TO DAILY ===")
existing_dates = set(str(r[0]) for r in data_rows)
need_dates = []
for d_str in ["2026-08-10", "2026-08-11", "2026-08-12"]:
    if d_str in existing_dates:
        log(f"  {d_str}: ALREADY EXISTS — skip")
    elif d_str not in klines_new:
        log(f"  {d_str}: NO KLINES DATA — partial or missing")
    else:
        need_dates.append(d_str)
        log(f"  {d_str}: NEED TO APPEND ✓")

# ── Build new rows ─────────────────────────────────────────────────────────────
log("\n=== BUILD NEW ROWS ===")

# Get rolling data from existing DAILY for computations
def get_col_arr(col_key, n=None):
    vals = []
    for r in data_rows:
        v = gcol(r, col_key)
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            vals.append(None)
    return vals[-n:] if n else vals

close_arr    = get_col_arr("c")
oi_arr       = get_col_arr("oi_usd")
vol_arr      = get_col_arr("vol_perp_usd")
pos_r_arr    = get_col_arr("pos_r")
acc_r_arr    = get_col_arr("acc_r")
glsr_arr     = get_col_arr("glsr")
f_avg_arr    = get_col_arr("f_avg")
taker_arr    = get_col_arr("taker_buy_pct (k[10]/k[7])")
ret_arr      = get_col_arr("ret_1d (close-to-close)")
dws_arr      = [r[col_map.get("dist_wall_streak (consec days)", 45)] for r in data_rows]
dwc_arr      = [r[col_map.get("dist_wall_cumul_ret (%)", 46)] for r in data_rows]
pin_str_arr  = get_col_arr("pin_streak")

def safe_median(arr):
    clean = [v for v in arr if v is not None and not math.isnan(v)]
    return statistics.median(clean) if clean else None

def safe_mean(arr):
    clean = [v for v in arr if v is not None and not math.isnan(v)]
    return sum(clean)/len(clean) if clean else None

new_rows_built = []

for d_str in need_dates:
    kl = klines_new.get(d_str, {})
    fn_row = funding_by_date.get(d_str, [])
    oi_row = oi_by_date.get(d_str, {})
    lsr_row = lsr_data.get(d_str, {})

    o      = kl.get("o")
    h      = kl.get("h")
    l      = kl.get("l")
    c      = kl.get("c")
    vol_p  = kl.get("vol_perp_usd")
    tk_pct = kl.get("taker_buy_pct")
    px_avg = kl.get("px_avg")

    # Funding
    f_avg_v = sum(fn_row) / len(fn_row) if fn_row else None
    f_min_v = min(fn_row) if fn_row else None
    f_max_v = max(fn_row) if fn_row else None
    fn_v    = len(fn_row)
    data_ok = 1 if fn_v >= 6 else 0
    low_c   = 1 if fn_v < 6 else 0

    # OI
    oi_usd_v   = oi_row.get("oi_usd")
    oi_token_v = oi_row.get("oi_token")

    # LSR
    pos_r_v    = lsr_row.get("pos_r")
    acc_r_v    = lsr_row.get("acc_r")
    gLSR_v     = lsr_row.get("gLSR")
    taker_lsr_v = lsr_row.get("taker_lsr")

    # Derived
    # Append current values for rolling
    close_arr.append(c)
    oi_arr.append(oi_usd_v)
    vol_arr.append(vol_p)
    pos_r_arr.append(pos_r_v)
    acc_r_arr.append(acc_r_v)
    glsr_arr.append(gLSR_v)
    f_avg_arr.append(f_avg_v)
    taker_arr.append(tk_pct)

    # ret_1d
    prev_c = close_arr[-2] if len(close_arr) >= 2 else None
    ret_1d_v = None
    if prev_c and c:
        try:
            ret_1d_v = (float(c) - float(prev_c)) / float(prev_c) * 100
        except: pass

    # oi_vs_med14
    oi_med14 = safe_median([v for v in oi_arr[-15:-1] if v is not None])
    oi_vs_med14 = oi_usd_v / oi_med14 if (oi_med14 and oi_usd_v) else None

    # vol_vs_med14
    vol_med14 = safe_median([v for v in vol_arr[-15:-1] if v is not None])
    vol_vs_med14 = vol_p / vol_med14 if (vol_med14 and vol_p) else None

    # div_raw
    div_raw_v = None
    if pos_r_v and acc_r_v and acc_r_v != 0:
        try: div_raw_v = float(pos_r_v) / float(acc_r_v)
        except: pass

    # div_avg3
    pos3 = [v for v in pos_r_arr[-3:] if v is not None]
    acc3 = [v for v in acc_r_arr[-3:] if v is not None]
    div_avg3_v = None
    if len(pos3) >= 2 and len(acc3) >= 2:
        div_avg3_v = (sum(pos3)/len(pos3)) / (sum(acc3)/len(acc3))

    # glsr_slope_5d
    glsr5 = [v for v in glsr_arr[-6:-1] if v is not None]
    glsr_slope_v = None
    if len(glsr5) >= 1 and glsr_arr[-1] is not None:
        if glsr5[0] and glsr5[0] != 0:
            try: glsr_slope_v = float(glsr_arr[-1]) / float(glsr5[0])
            except: pass

    # d_pos_3d, d_acc_3d
    pos3d_arr = [v for v in pos_r_arr[-4:-1] if v is not None]
    d_pos_3d_v = None
    if pos3d_arr and pos_r_v:
        try: d_pos_3d_v = (float(pos_r_v) - float(pos3d_arr[0])) / float(pos3d_arr[0]) * 100
        except: pass
    acc3d_arr = [v for v in acc_r_arr[-4:-1] if v is not None]
    d_acc_3d_v = None
    if acc3d_arr and acc_r_v:
        try: d_acc_3d_v = (float(acc_r_v) - float(acc3d_arr[0])) / float(acc3d_arr[0]) * 100
        except: pass

    # pin_streak + pin_day
    pin_day_v = 1 if (f_avg_v is not None and 4e-5 <= f_avg_v <= 6e-5) else 0
    prev_pin_str = pin_str_arr[-1] if pin_str_arr else 0
    try:
        prev_pin_n = float(prev_pin_str) if prev_pin_str is not None else 0
    except: prev_pin_n = 0
    pin_streak_v = prev_pin_n + 1 if pin_day_v == 1 else 0
    pin_str_arr.append(pin_streak_v)

    # oi_cycle_pos (30d rolling)
    oi_30 = [v for v in oi_arr[-31:] if v is not None]
    oi_cycle_v = None
    if len(oi_30) >= 2:
        mn, mx = min(oi_30), max(oi_30)
        if mx > mn:
            oi_cycle_v = (oi_usd_v - mn) / (mx - mn) if oi_usd_v else None

    # flag_neg_div: f_avg <= -2e-4 AND range3d <= 7%
    # range3d = (max - min) of last 3 closes / open
    ret3 = [v for v in ret_arr[-3:] if v is not None]
    range3d = abs(sum(v for v in ret3 if v)) if ret3 else 999
    ret_arr.append(ret_1d_v)
    flag_neg_div_v = 1 if (f_avg_v is not None and f_avg_v <= -2e-4 and range3d <= 7) else 0

    # flag_dist_wall_day: taker >= 50 AND ret < 0
    flag_dist_v = 0
    if tk_pct is not None and ret_1d_v is not None:
        flag_dist_v = 1 if (tk_pct >= 50 and ret_1d_v < 0) else 0

    # dist_wall_streak + cumul_ret
    try: prev_dws = float(dws_arr[-1]) if dws_arr and dws_arr[-1] is not None else 0
    except: prev_dws = 0
    try: prev_dwc = float(dwc_arr[-1]) if dwc_arr and dwc_arr[-1] is not None else 0
    except: prev_dwc = 0
    if flag_dist_v == 1:
        dws_v = prev_dws + 1
        dwc_v = (prev_dwc if prev_dws > 0 else 0) + (ret_1d_v or 0)
    else:
        dws_v = 0
        dwc_v = 0
    dws_arr.append(dws_v)
    dwc_arr.append(dwc_v)

    # flag_decay_day: taker < 45
    flag_decay_v = 1 if (tk_pct is not None and tk_pct < 45) else 0

    # flag_hedge_struct: div_avg3 <= 0.5
    flag_hedge_v = 1 if (div_avg3_v is not None and div_avg3_v <= 0.5) else 0

    # flag_knife_crowd: gLSR↑ AND ret < -3%
    prev_glsr = glsr_arr[-2] if len(glsr_arr) >= 2 else None
    glsr_rising = (gLSR_v is not None and prev_glsr is not None and gLSR_v > prev_glsr)
    flag_knife_v = 1 if (glsr_rising and ret_1d_v is not None and ret_1d_v < -3) else 0

    row50 = [None] * 50
    row50[0]  = d_str
    row50[1]  = px_avg
    row50[2]  = o
    row50[3]  = h
    row50[4]  = l
    row50[5]  = c
    row50[6]  = vol_p
    row50[7]  = tk_pct
    row50[8]  = f_avg_v
    row50[9]  = f_min_v
    row50[10] = f_max_v
    row50[11] = fn_v
    row50[12] = oi_usd_v
    row50[13] = oi_token_v
    row50[14] = data_ok
    row50[15] = low_c
    row50[16] = ret_1d_v
    row50[17] = pin_streak_v
    row50[18] = pin_day_v
    row50[19] = oi_vs_med14
    row50[20] = vol_vs_med14
    row50[21] = div_raw_v
    row50[22] = div_avg3_v
    row50[23] = glsr_slope_v
    row50[24] = d_pos_3d_v
    row50[25] = d_acc_3d_v
    row50[26] = pos_r_v
    row50[27] = acc_r_v
    row50[28] = gLSR_v
    row50[29] = taker_lsr_v
    row50[30] = None   # vol_spot_usd (no Binance spot; DEX noted in note)
    row50[31] = None   # taker_spot_pct
    row50[32] = None   # spot_perp_ratio
    row50[33] = None   # l29_flag
    row50[34] = None   # vol_alpha (check later)
    row50[35] = None   # taker_alpha
    row50[36] = "CoinGecko/BSC+ETH+Monad"  # on_chain_source
    row50[37] = None   # gom_A_screen
    row50[38] = None   # gom_B_screen
    row50[39] = None   # gom_note
    row50[40] = "fapi.binance.com klines 1d"
    row50[41] = "fapi.binance.com topPos/topAcc/global/taker"
    row50[42] = oi_cycle_v
    row50[43] = flag_neg_div_v
    row50[44] = flag_dist_v
    row50[45] = dws_v
    row50[46] = dwc_v
    row50[47] = flag_decay_v
    row50[48] = flag_hedge_v
    row50[49] = flag_knife_v

    new_rows_built.append(row50)

    def _fmt(v, fmt=".4f"):
        if v is None: return "N/A"
        try: return format(float(v), fmt)
        except: return str(v)

    log(f"  {d_str}:")
    log(f"    c={_fmt(c)} ret={_fmt(ret_1d_v,'%')} vol=${_fmt(vol_p,'.0f')}")
    log(f"    pos_r={_fmt(pos_r_v)} acc_r={_fmt(acc_r_v)} gLSR={_fmt(gLSR_v)}")
    log(f"    div_avg3={_fmt(div_avg3_v)} oi_vs_med14={_fmt(oi_vs_med14)}")
    log(f"    f_avg={_fmt(f_avg_v)} fn={fn_v} data_ok={data_ok}")
    log(f"    oi_usd=${_fmt(oi_usd_v,'.0f')} oi_cycle={_fmt(oi_cycle_v)}")
    log(f"    flag_neg_div={flag_neg_div_v} flag_dist={flag_dist_v} flag_decay={flag_decay_v}")
    log(f"    flag_hedge={flag_hedge_v} flag_knife={flag_knife_v}")

# ── Save to scratch for append task ──────────────────────────────────────────
out = {
    "need_dates": need_dates,
    "new_rows":   new_rows_built,
    "hdr":        hdr,
    "existing_count": len(data_rows),
}
out_path = SCRATCH / "apr_p1_newrows_20260811.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
log(f"\n[P-1 DONE] {len(new_rows_built)} new rows built → {out_path.name}")
log(f"Dates: {need_dates}")

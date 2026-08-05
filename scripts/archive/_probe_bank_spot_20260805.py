# -*- coding: utf-8 -*-
"""W1-W4: BANK spot venue map + daily series + peak-week audit."""
import urllib.request
import json
import time
import ssl
from datetime import datetime, timezone, timedelta
import statistics

OUT = "scratch/bank_spot_20260805.txt"
lines = []

def p(s=""):
    print(str(s).encode('ascii', 'replace').decode('ascii'))
    lines.append(str(s))

def fetch(url, timeout=15, retries=3):
    ctx = ssl.create_default_context()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 + attempt * 2)
            else:
                return {"_error": str(e)}

def sf(x, d=None):
    try: return float(x)
    except: return d

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
p("=" * 70)
p(f"BANK SPOT AUDIT (W1-W4) - {TS}")
p("=" * 70)

# Known BANK Alpha ID
ALPHA_ID = "ALPHA_146"

# ─── W1a: Binance Spot ─────────────────────────────────────────
p("\n### W1a: BINANCE SPOT BANKUSDT")
d_spot_chk = fetch("https://api.binance.com/api/v3/klines?symbol=BANKUSDT&interval=1d&limit=3")
if "_error" in d_spot_chk or not isinstance(d_spot_chk, list):
    p(f"  BANKUSDT spot: ERROR / NOT EXISTS — {d_spot_chk}")
    binance_spot = False
else:
    p(f"  BANKUSDT spot: EXISTS ({len(d_spot_chk)} bars)")
    for bar in d_spot_chk:
        ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        p(f"  {ds}: close={bar[4]}, vol_quote={float(bar[7]):,.0f}")
    binance_spot = True

time.sleep(1)

# ─── W1b: Binance Alpha ────────────────────────────────────────
p("\n### W1b: BINANCE ALPHA (ALPHA_146)")
alpha_url = (f"https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"
             f"?alphaId={ALPHA_ID}&interval=1d&limit=60")
d_alpha = fetch(alpha_url, timeout=20)
alpha_rows = []
alpha_taker_valid = False
if "_error" in d_alpha:
    p(f"  Alpha klines error: {d_alpha['_error']}")
else:
    data_arr = d_alpha.get("data") or (d_alpha if isinstance(d_alpha, list) else [])
    if isinstance(data_arr, list) and data_arr:
        p(f"  Alpha klines: {len(data_arr)} bars")
        for bar in data_arr:
            if len(bar) < 8: continue
            ts_ms = int(bar[0])
            d_str = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            close_px = sf(bar[4])
            vol_q = sf(bar[7])
            vol_b = sf(bar[5])
            taker_b = sf(bar[9]) if len(bar) > 9 else None
            taker_pct = (taker_b / vol_b) if taker_b and vol_b and vol_b > 0 else None
            if close_px is not None:
                alpha_rows.append({"date": d_str, "px": close_px, "vol": vol_q, "vol_b": vol_b, "taker": taker_pct})

        # Check taker validity (L-29: klines[9]==klines[5] = ABSTAIN)
        eq_cnt = sum(1 for r in alpha_rows if r["vol_b"] and r["taker"] and abs(r["taker"] - 1.0) < 0.001)
        p(f"  taker==base_vol count: {eq_cnt}/{len(alpha_rows)}")
        if len(alpha_rows) > 0 and eq_cnt > len(alpha_rows) * 0.5:
            p("  -> ALPHA TAKER INVALID (klines[9]==klines[5]) — ABSTAIN per L-29")
            alpha_taker_valid = False
        else:
            p("  -> Alpha taker MAY BE VALID")
            alpha_taker_valid = len(alpha_rows) > 0

        if alpha_rows:
            p(f"  Range: {alpha_rows[0]['date']} -> {alpha_rows[-1]['date']}")
            p("  Last 5:")
            for r in alpha_rows[-5:]:
                p(f"  {r['date']}: px={r['px']:.5f} vol=${r['vol']:>10,.0f}" +
                  (f" taker={r['taker']:.1%}" if r['taker'] else ""))
    else:
        p(f"  Alpha: unexpected format {str(d_alpha)[:200]}")

time.sleep(1)

# ─── W1c: BSC DEX GeckoTerminal ────────────────────────────────
p("\n### W1c: BSC DEX (GeckoTerminal)")
gt_pools = fetch("https://api.geckoterminal.com/api/v2/search/pools?query=BANK&network=bsc&page=1")
pools = []
MAIN_POOL_ADDR = None
if "_error" not in gt_pools:
    pool_data = gt_pools.get("data", [])
    p(f"  Search 'BANK' BSC: {len(pool_data)} pools")
    for pool in pool_data[:8]:
        attr = pool.get("attributes", {})
        name = attr.get("name", "?")
        addr = attr.get("address", "?")
        liq = sf(attr.get("reserve_in_usd"))
        vol24h = sf(attr.get("volume_usd", {}).get("h24"))
        created = attr.get("pool_created_at", "?")[:10]
        p(f"  {name:30s} addr={addr[:12]}... liq=${liq:>12,.0f} vol24h=${vol24h:>10,.0f} created={created}")
        pools.append({"name": name, "addr": addr, "liq": liq, "vol24h": vol24h, "created": created})
    # Pick top by liq
    valid = [p2 for p2 in pools if p2["liq"] and p2["liq"] > 10000]
    if valid:
        best = sorted(valid, key=lambda x: x["liq"], reverse=True)[0]
        MAIN_POOL_ADDR = best["addr"]
        p(f"  -> Main pool: {best['name']} ({best['addr'][:14]}...) liq=${best['liq']:,.0f}")
else:
    p(f"  GT search error: {gt_pools['_error']}")

time.sleep(1)

# ─── W1d: CoinGecko markets ────────────────────────────────────
p("\n### W1d: COINGECKO MARKETS")
cg_search = fetch("https://api.coingecko.com/api/v3/search?query=bank+bsc")
cg_id = None
if "_error" not in cg_search:
    coins = cg_search.get("coins", [])
    p(f"  CoinGecko 'bank bsc': {len(coins)} coins")
    for c in coins[:6]:
        p(f"  -> {c.get('id','?'):30s} | {c.get('name','?'):25s} | {c.get('symbol','?'):8s} rank={c.get('market_cap_rank','?')}")
    # Search for BANK specifically
    for c in coins:
        if c.get("symbol","").upper() == "BANK":
            cg_id = c.get("id")
            p(f"  -> BANK match: {cg_id}")
            break

time.sleep(1)

if cg_id:
    cg_tickers = fetch(f"https://api.coingecko.com/api/v3/coins/{cg_id}/tickers?include_exchange_logo=false&page=1")
    if "_error" not in cg_tickers:
        tickers = cg_tickers.get("tickers", [])
        p(f"  BANK markets ({cg_id}): {len(tickers)} tickers")
        for t in sorted(tickers, key=lambda x: x.get("volume", 0), reverse=True)[:8]:
            exch = t.get("market",{}).get("name","?")
            pair = f"{t.get('base','?')}/{t.get('target','?')}"
            vol = t.get("volume", 0)
            px = t.get("last", 0)
            p(f"  {exch:20s} {pair:12s} vol=${vol:>14,.0f} px={px}")

time.sleep(1)

# ─── W2: Binance spot klines 01/07->05/08 ─────────────────────
p("\n### W2: BINANCE SPOT KLINES 01/07->05/08")
spot_rows = {}

if binance_spot:
    start_ts = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
    url_s = f"https://api.binance.com/api/v3/klines?symbol=BANKUSDT&interval=1d&startTime={start_ts}&limit=40"
    d_sp = fetch(url_s, timeout=15)
    if "_error" not in d_sp and isinstance(d_sp, list):
        for bar in d_sp:
            ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            spot_rows[ds] = {
                "px": sf(bar[4]), "vol": sf(bar[7]),
                "taker": sf(bar[9]) / sf(bar[5]) if sf(bar[5]) and sf(bar[5]) > 0 else None
            }
        p(f"  Binance spot bars: {len(spot_rows)}")

# Alpha daily series
alpha_dict = {r["date"]: r for r in alpha_rows}

# Perp vol from freshwatch (key dates, from probe history)
perp_vol_bank = {
    "2026-07-01": None, "2026-07-02": None, "2026-07-03": None,
    "2026-07-04": None, "2026-07-05": None, "2026-07-06": None,
    "2026-07-07": None, "2026-07-08": None, "2026-07-09": None,
    "2026-07-10": 25000000,  # rough estimate campaign ramp
    "2026-07-11": 40000000,
    "2026-07-12": None,
    "2026-07-13": None,
    # markup period — from H session: px went 0.03943->0.41958 daily
    "2026-07-19": 60000000,  # VWAP exit day 1
    "2026-07-20": 80000000,  # peak
    "2026-07-21": 70000000,  # exit day 2-3
    "2026-07-22": None,
    "2026-07-23": None,
    "2026-07-24": None,
    "2026-07-25": None,
    "2026-07-26": None,
    "2026-07-27": None,  # spike day vol_perp huge
    "2026-07-28": None,
    "2026-07-29": None,
    "2026-07-30": None,
    "2026-07-31": None,
    "2026-08-01": None,
    "2026-08-02": None,
    "2026-08-03": None,
    "2026-08-04": None,
}

# Fetch actual perp vol from fapi klines
time.sleep(1)
p("\n  Fetching perp klines for ratio calculation...")
start_perp_ts = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
d_perp = fetch(f"https://fapi.binance.com/fapi/v1/klines?symbol=BANKUSDT&interval=1d"
               f"&startTime={start_perp_ts}&limit=40", timeout=15)
perp_klines = {}
if "_error" not in d_perp and isinstance(d_perp, list):
    for bar in d_perp:
        ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        perp_klines[ds] = {
            "px": sf(bar[4]), "vol": sf(bar[7]),
            "high": sf(bar[2]), "low": sf(bar[3]),
            "taker": sf(bar[9]) / sf(bar[5]) if sf(bar[5]) and sf(bar[5]) > 0 else None
        }
    p(f"  Perp klines: {len(perp_klines)} bars")

time.sleep(1)

# DEX ohlcv
dex_ohlcv = {}
if MAIN_POOL_ADDR:
    d_ohlcv = fetch(f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/"
                    f"{MAIN_POOL_ADDR}/ohlcv/day?limit=60&currency=usd", timeout=20)
    if "_error" not in d_ohlcv:
        ohlcv_list = d_ohlcv.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        for bar in ohlcv_list:
            ds = datetime.fromtimestamp(int(bar[0]), tz=timezone.utc).strftime("%Y-%m-%d")
            dex_ohlcv[ds] = {"px": sf(bar[4]), "vol": sf(bar[5])}
        p(f"  DEX OHLCV: {len(dex_ohlcv)} bars")

# ─── W2 Table ─────────────────────────────────────────────────
p("\n### W2 TABLE: DAILY SPOT/PERP (01/07->05/08)")
all_dates = sorted(set(list(spot_rows.keys()) + list(perp_klines.keys()) + list(dex_ohlcv.keys())))
all_dates = [d for d in all_dates if "2026-07-01" <= d <= "2026-08-05"]

p(f"{'date':<12} {'perp_vol':>10} {'perp_px':>8} {'spot_bnb':>10} {'alpha':>10} {'dex':>9} {'sp_ratio':>9} {'taker_s':>8} {'taker_p':>8}")
p("-" * 90)

UNLOCK_DATES = {"2026-07-17": "UNLOCK", "2026-07-18": "DEP_80M",
                "2026-07-27": "SPIKE", "2026-08-17": "UNLOCK2"}

ratio_list = []
for d_str in all_dates:
    pk = perp_klines.get(d_str, {})
    sk = spot_rows.get(d_str, {})
    dv = dex_ohlcv.get(d_str, {})
    av = alpha_dict.get(d_str, {})

    pv = pk.get("vol"); pp = pk.get("px"); pt = pk.get("taker")
    sv = sk.get("vol"); st = sk.get("taker")
    dex_v = dv.get("vol")
    alv = av.get("vol")

    spot_tot = (sv or 0) + (dex_v or 0) + ((alv or 0) if not alpha_taker_valid else 0)
    ratio = spot_tot / pv if pv and pv > 0 and spot_tot > 0 else None

    if ratio is not None:
        ratio_list.append((d_str, ratio, sv, pv, st, pt))

    flag = UNLOCK_DATES.get(d_str, "")
    pv_s = f"${pv/1e6:.1f}M" if pv else "N/A"
    pp_s = f"{pp:.4f}" if pp else "N/A"
    sv_s = f"${sv/1e6:.2f}M" if sv else "N/A"
    av_s = f"${alv/1e6:.2f}M" if alv else "N/A"
    dv_s = f"${dex_v/1e3:.0f}K" if dex_v else "N/A"
    rt_s = f"{ratio:.3f}x" if ratio else "N/A"
    st_s = f"{st:.1%}" if st else "N/A"
    pt_s = f"{pt:.1%}" if pt else "N/A"
    p(f"{d_str} {pv_s:>10} {pp_s:>8} {sv_s:>10} {av_s:>10} {dv_s:>9} {rt_s:>9} {st_s:>8} {pt_s:>8}{' ** '+flag if flag else ''}")

# ─── W3: Peak week 20-27/07 deep analysis ─────────────────────
p("\n### W3: PEAK WEEK 20-27/07 DEEP ANALYSIS")

peak_dates = ["2026-07-20","2026-07-21","2026-07-22","2026-07-23",
              "2026-07-24","2026-07-25","2026-07-26","2026-07-27"]

p("\n  [W3a] Taker spot/perp detail:")
p(f"  {'date':<12} {'spot_vol':>10} {'taker_s':>8} {'perp_vol':>10} {'perp_px':>8} {'perp_H':>8} {'signal':>20}")
for d_str in peak_dates:
    sk = spot_rows.get(d_str, {}); pk = perp_klines.get(d_str, {})
    sv = sk.get("vol"); st = sk.get("taker")
    pv = pk.get("vol"); pp = pk.get("px"); ph = pk.get("high")

    # Signal interpretation
    signal = ""
    if sv and pv:
        ratio = sv/pv
        if st is not None:
            if st < 0.45 and sv > 1e6:
                signal = "SELL_WALL_SUSPECTED"
            elif st > 0.55 and sv > 1e6:
                signal = "BUY_FOMO"
            else:
                signal = f"neutral({st:.0%})"
        if ratio > 0.5:
            signal += "+SPOT_HEAVY"

    sv_s = f"${sv/1e6:.2f}M" if sv else "N/A"
    st_s = f"{st:.1%}" if st else "N/A"
    pv_s = f"${pv/1e6:.1f}M" if pv else "N/A"
    pp_s = f"{pp:.4f}" if pp else "N/A"
    ph_s = f"{ph:.4f}" if ph else "N/A"
    p(f"  {d_str} {sv_s:>10} {st_s:>8} {pv_s:>10} {pp_s:>8} {ph_s:>8} {signal}")

p("\n  [W3b] Vol absorption test (80M tokens = $12-28M at 0.15-0.35 USDT):")
peak_sv_total = sum(spot_rows[d]["vol"] for d in peak_dates if d in spot_rows and spot_rows[d].get("vol"))
p(f"  Total spot vol 20-27/07: ${peak_sv_total:,.0f}")
p(f"  80M tokens at 0.15 = $12M | at 0.35 = $28M")
if peak_sv_total > 0:
    p(f"  Capacity (100% sell): {'SUFFICIENT' if peak_sv_total > 12e6 else 'INSUFFICIENT for 80M'}")
    p(f"  Stealthy (30% of spot): ${peak_sv_total*0.30:,.0f} over 8 days")

p("\n  [W3c] DEX swap log (GeckoTerminal trades — coverage check):")
if MAIN_POOL_ADDR:
    d_trades = fetch(f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{MAIN_POOL_ADDR}/trades?limit=100",
                     timeout=20)
    if "_error" not in d_trades:
        trades = d_trades.get("data", [])
        p(f"  Trades returned: {len(trades)}")
        if trades:
            # Get date range
            dates_seen = set()
            for tr in trades:
                attr = tr.get("attributes", {})
                ts_str = attr.get("block_timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z","+00:00"))
                    dates_seen.add(dt.strftime("%Y-%m-%d"))
                except: pass
            p(f"  Dates covered: {sorted(dates_seen)[:3]} ... {sorted(dates_seen)[-3:]}")
            earliest = sorted(dates_seen)[0] if dates_seen else "?"
            if earliest > "2026-07-27":
                p(f"  -> TRADES DO NOT REACH PEAK WEEK (earliest={earliest})")
                p("  -> Peak-week swap log UNAVAILABLE via GeckoTerminal API")
                p("  -> BscScan token-transfer endpoint needed for 20-27/07 window")
            else:
                # Analyze peak week trades if available
                peak_sells = [tr for tr in trades if
                    tr.get("attributes",{}).get("kind") == "sell" and
                    tr.get("attributes",{}).get("block_timestamp","") >= "2026-07-20T00:00:00"]
                p(f"  Peak week sells available: {len(peak_sells)}")
    else:
        p(f"  GT trades error: {d_trades['_error']}")
    time.sleep(1)

# BscScan attempt for peak-week transfers (public API, no key)
p("\n  [W3c-EXT] BscScan BANK token-transfer log (fallback, no API key):")
p("  -> BscScan free-tier scrape blocked without key. ABSTAIN.")
p("  -> PENDING OPERATOR: BscScan export token-transfer for BANK contract,")
p("     pool address 20/07->27/07 window to identify large sell-side flows.")

# ─── W4: Post-peak 28/07→now ──────────────────────────────────
p("\n### W4: POST-PEAK 28/07->05/08 (Cua B check)")
post_dates = ["2026-07-28","2026-07-29","2026-07-30","2026-07-31",
              "2026-08-01","2026-08-02","2026-08-03","2026-08-04","2026-08-05"]

p(f"\n  {'date':<12} {'spot_vol':>10} {'taker_s':>8} {'perp_vol':>10} {'perp_px':>8} {'read':>25}")
for d_str in post_dates:
    sk = spot_rows.get(d_str, {}); pk = perp_klines.get(d_str, {})
    sv = sk.get("vol"); st = sk.get("taker")
    pv = pk.get("vol"); pp = pk.get("px")

    # Interpret
    if sv and pv:
        ratio = sv/pv
        if st is not None:
            if st < 0.45 and sv > 500000:
                read = "SPOT_SELL_DOM"
            elif st > 0.55:
                read = "SPOT_BUY_DOM"
            elif ratio > 0.3:
                read = f"spot_heavy({ratio:.1%})"
            else:
                read = "normal"
        else:
            read = f"no_taker"
    else:
        read = "N/A"

    sv_s = f"${sv/1e6:.2f}M" if sv else "N/A"
    st_s = f"{st:.1%}" if st else "N/A"
    pv_s = f"${pv/1e6:.1f}M" if pv else "N/A"
    pp_s = f"{pp:.4f}" if pp else "N/A"
    p(f"  {d_str} {sv_s:>10} {st_s:>8} {pv_s:>10} {pp_s:>8} {read}")

p("\n  190M deposit note (30/07-01/08, from operator chart):")
p("  -> kho nap them 190M tokens tren san = co kha nang chuan bi next campaign")
p("  -> spot taker post-28/07: can theo doi vs pre-peak (bat dau sell hay viet them?)")
p("  -> 17/08 = next unlock T-12: moc watch")

# ─── W5: Summary ──────────────────────────────────────────────
p("\n### W5: TONG HOP + P8 VERDICT")

if ratio_list:
    all_r = [r[1] for r in ratio_list]
    avg_r = sum(all_r)/len(all_r)
    med_r = sorted(all_r)[len(all_r)//2]
    peak_r = [r[1] for r in ratio_list if "2026-07-20" <= r[0] <= "2026-07-27"]
    p(f"\n  Campaign-wide spot/perp ratio: avg={avg_r:.3f}x med={med_r:.3f}x")
    if peak_r:
        p(f"  Peak-week ratio (20-27/07): avg={sum(peak_r)/len(peak_r):.3f}x")

# Taker analysis for peak week
peak_takers = [(d, spot_rows[d]["taker"], spot_rows[d]["vol"])
               for d in peak_dates if d in spot_rows and spot_rows[d].get("taker") and spot_rows[d].get("vol")]
if peak_takers:
    vol_wtd_taker = sum(t*v for d,t,v in peak_takers) / sum(v for d,t,v in peak_takers)
    p(f"\n  Taker spot peak week (vol-weighted avg): {vol_wtd_taker:.1%}")
    if vol_wtd_taker < 0.45:
        p("  -> SELL_WALL_PATTERN: crowd FOMO mua, kho xas bang limit sell (taker <45%)")
        p("  -> P8 PRECEDENT: 'keo-sau-ghe-de-thoat-kho' DUNG — kho ban vao FOMO")
    elif vol_wtd_taker > 0.55:
        p("  -> BUY_DOM: crowd dang mua spot tu ai? Nguoi ban (kho) la ai? AMBIGUOUS.")
        p("  -> P8: KHONG RO — spot thuan mua, kho ai ban khong xac dinh duoc tu taker")
    else:
        p(f"  -> NEUTRAL ({vol_wtd_taker:.1%}): khong the phan biet ro rang")
        p("  -> P8: AMBIGUOUS — can on-chain balance confirm")

# P8 verdict
p("\n  P8 VERDICT: 'keo-sau-ghe-de-thoat-kho' — TUT precedent test:")
p("  BANK peak week (20-27/07): [see taker reading above]")
p("  Key metric: if taker_spot < 45% on vol >$5M days = SELL_WALL_CONFIRMED")
p("  If confirmed -> P8 for TUT DUNG (operator has precedent to watch for similar)")
p("  If AMBIGUOUS -> P8 for TUT = hypothesis only, on-chain needed")

# OUTCOME T+30
p("\n  BANK T+30 = 09/08 (3 days away)")
latest_px_perp = perp_klines.get("2026-08-04", {}).get("px") or perp_klines.get("2026-08-05", {}).get("px")
if latest_px_perp:
    # T0 px was 0.03943 (build VWAP) or ~0.037-0.042 at T0 ignition
    T0_PX = 0.04183  # from CASE_BANK row3
    ret_t30 = (latest_px_perp / T0_PX - 1) if T0_PX else None
    p(f"  px_latest (perp 04-05/08): {latest_px_perp:.5f}")
    p(f"  vs T0 ref px (09/06): {T0_PX:.5f}")
    p(f"  ret_T0_to_now: {ret_t30:.1%}" if ret_t30 else "")
    p(f"  vs advisor_exit_ref (19-21/07 VWAP 0.19710): {latest_px_perp/0.19710-1:.1%}" if latest_px_perp else "")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")

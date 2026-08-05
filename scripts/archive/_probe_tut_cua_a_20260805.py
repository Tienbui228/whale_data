# -*- coding: utf-8 -*-
"""S1-S3: TUT spot venue map + daily series + Cua A audit."""
import urllib.request
import urllib.parse
import json
import time
import ssl
from datetime import datetime, timezone, timedelta

OUT = "scratch/tut_cua_a_20260805.txt"
lines = []

def p(s=""):
    print(s)
    lines.append(s)

def fetch(url, timeout=15, retries=3):
    ctx = ssl.create_default_context()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 + attempt * 2)
            else:
                return {"_error": str(e)}

def safe_float(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
p("=" * 70)
p(f"TUT CUA A AUDIT - {TS}")
p("=" * 70)

# ─────────────────────────────────────────────────────────────────
# S1a: Binance SPOT - does TUTUSDT exist?
# ─────────────────────────────────────────────────────────────────
p("\n### S1a: BINANCE SPOT")
try:
    d = fetch("https://api.binance.com/api/v3/klines?symbol=TUTUSDT&interval=1d&limit=3")
    if "_error" in d or isinstance(d, dict):
        p(f"  Binance spot TUTUSDT: ERROR - {d.get('_error','unknown')}")
        p("  -> KHONG CO Binance spot listing cho TUT")
        binance_spot = False
    else:
        p(f"  Binance spot TUTUSDT: EXISTS ({len(d)} bars)")
        if d:
            last = d[-1]
            p(f"  Last bar: date={datetime.fromtimestamp(last[0]/1000,tz=timezone.utc).date()}, "
              f"close={last[4]}, vol_quote={float(last[7]):.0f}")
        binance_spot = True
except Exception as e:
    p(f"  Binance spot error: {e}")
    binance_spot = False

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S1b: Binance Alpha - ALPHA_117 klines
# ─────────────────────────────────────────────────────────────────
p("\n### S1b: BINANCE ALPHA (ALPHA_117)")
ALPHA_ID = "ALPHA_117"

# Try Alpha klines - 60 days
alpha_url = ("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"
             f"?alphaId={ALPHA_ID}&interval=1d&limit=60")
d_alpha = fetch(alpha_url, timeout=20)

alpha_rows = []
if "_error" in d_alpha:
    p(f"  Alpha klines error: {d_alpha['_error']}")
else:
    data_arr = d_alpha.get("data") or d_alpha
    if isinstance(data_arr, list):
        p(f"  Alpha klines: {len(data_arr)} bars")
        # klines format: [open_time, open, high, low, close, vol_base, close_time, vol_quote, ...]
        for bar in data_arr[-5:]:
            if len(bar) >= 8:
                ts_ms = int(bar[0])
                d_str = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
                close_px = safe_float(bar[4])
                vol_q = safe_float(bar[7])
                vol_b = safe_float(bar[5])
                # taker: bar[9]=taker_buy_base, bar[10]=taker_buy_quote
                taker_b = safe_float(bar[9]) if len(bar) > 9 else None
                taker_pct = (taker_b / vol_b) if taker_b and vol_b and vol_b > 0 else None
                p(f"  {d_str}: px={close_px}, vol_quote=${vol_q:.0f}" +
                  (f", taker={taker_pct:.1%}" if taker_pct else ""))
                alpha_rows.append({"date": d_str, "px": close_px, "vol_quote": vol_q,
                                   "vol_base": vol_b, "taker_pct": taker_pct})
        # Build full alpha series
        alpha_rows = []
        for bar in data_arr:
            if len(bar) >= 8:
                ts_ms = int(bar[0])
                d_str = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
                close_px = safe_float(bar[4])
                vol_q = safe_float(bar[7])
                vol_b = safe_float(bar[5])
                taker_b = safe_float(bar[9]) if len(bar) > 9 else None
                taker_pct = (taker_b / vol_b) if taker_b and vol_b and vol_b > 0 else None
                if close_px is not None and vol_q is not None:
                    alpha_rows.append({"date": d_str, "px": close_px, "vol_quote": vol_q,
                                       "vol_base": vol_b, "taker_pct": taker_pct})
        # Check taker validity - Alpha rule L-29: taker unreliable
        # klines[9]==klines[5] test
        taker_equal_count = sum(1 for r in alpha_rows if r["vol_base"] and r["taker_pct"] and
                                 abs(r["taker_pct"] - 1.0) < 0.001)
        p(f"  Alpha taker==vol_base count: {taker_equal_count}/{len(alpha_rows)}")
        if taker_equal_count > len(alpha_rows) * 0.5:
            p("  -> ALPHA TAKER INVALID (klines[9]==klines[5] pattern) - ABSTAIN per L-29")
            alpha_taker_valid = False
        else:
            p(f"  -> Alpha taker appears valid (spot trading data)")
            alpha_taker_valid = True
        p(f"  First date: {alpha_rows[0]['date'] if alpha_rows else 'N/A'}")
        p(f"  Last date:  {alpha_rows[-1]['date'] if alpha_rows else 'N/A'}")
    else:
        p(f"  Alpha klines: unexpected format - {str(d_alpha)[:200]}")

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S1c: BSC DEX - GeckoTerminal pool search
# ─────────────────────────────────────────────────────────────────
p("\n### S1c: BSC DEX (GeckoTerminal)")

# Search pools
gt_search = fetch("https://api.geckoterminal.com/api/v2/search/pools?query=TUT&network=bsc&page=1")
pools = []
if "_error" not in gt_search:
    pool_data = gt_search.get("data", [])
    p(f"  GeckoTerminal pool search 'TUT' on BSC: {len(pool_data)} results")
    for pool in pool_data[:8]:
        attr = pool.get("attributes", {})
        name = attr.get("name", "?")
        addr = attr.get("address", "?")
        liq = safe_float(attr.get("reserve_in_usd"))
        vol24h = safe_float(attr.get("volume_usd", {}).get("h24"))
        created = attr.get("pool_created_at", "?")
        p(f"  Pool: {name} | addr={addr[:12]}... | liq=${liq:,.0f} | vol24h=${vol24h:,.0f} | created={created[:10] if created else '?'}")
        pools.append({
            "name": name, "addr": addr,
            "liq": liq, "vol24h": vol24h, "created": created
        })
else:
    p(f"  GeckoTerminal error: {gt_search['_error']}")

# Identify main pool
MAIN_POOL_ADDR = None
for pool in pools:
    if pool["liq"] and pool["liq"] > 500000:
        if MAIN_POOL_ADDR is None or pool["vol24h"] > pools[0].get("vol24h", 0):
            MAIN_POOL_ADDR = pool["addr"]
            p(f"  -> Main pool selected: {pool['name']} ({pool['addr'][:12]}...)")
            break

if not MAIN_POOL_ADDR and pools:
    MAIN_POOL_ADDR = pools[0]["addr"]
    p(f"  -> Using first pool: {pools[0]['name']}")

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S1d: CoinGecko markets - CEX listings
# ─────────────────────────────────────────────────────────────────
p("\n### S1d: COINGECKO MARKETS (CEX check)")

# Search for TUT on CoinGecko
cg_search = fetch("https://api.coingecko.com/api/v3/search?query=tut")
cg_coin_id = None
if "_error" not in cg_search:
    coins = cg_search.get("coins", [])
    p(f"  CoinGecko search 'tut': {len(coins)} coins found")
    for coin in coins[:5]:
        p(f"  -> {coin.get('id','?')} | {coin.get('name','?')} | {coin.get('symbol','?')} | market_cap_rank={coin.get('market_cap_rank','?')}")
    # Try to find BSC meme TUT
    for coin in coins:
        if coin.get("symbol", "").upper() == "TUT":
            cg_coin_id = coin.get("id")
            p(f"  -> TUT match: id={cg_coin_id}")
            break
else:
    p(f"  CoinGecko search error: {cg_search['_error']}")

time.sleep(1)

# Get markets for TUT if found
if cg_coin_id:
    cg_markets = fetch(f"https://api.coingecko.com/api/v3/coins/{cg_coin_id}/tickers?include_exchange_logo=false&page=1")
    if "_error" not in cg_markets:
        tickers = cg_markets.get("tickers", [])
        p(f"\n  TUT markets ({cg_coin_id}): {len(tickers)} tickers")
        for t in sorted(tickers, key=lambda x: x.get("volume", 0), reverse=True)[:10]:
            exch = t.get("market", {}).get("name", "?")
            pair = f"{t.get('base','?')}/{t.get('target','?')}"
            vol24h = t.get("volume", 0)
            px = t.get("last", 0)
            trust = t.get("trust_score", "?")
            p(f"  {exch:20s} {pair:12s} vol=${vol24h:>12,.0f} px={px} trust={trust}")
    else:
        p(f"  CoinGecko tickers error: {cg_markets['_error']}")
else:
    p("  No CoinGecko ID found for TUT - checking tickers via pool token")

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S2: Daily spot series from BSC DEX (GeckoTerminal OHLCV)
# ─────────────────────────────────────────────────────────────────
p("\n### S2: DAILY SPOT SERIES (GeckoTerminal OHLCV)")

dex_ohlcv = []
if MAIN_POOL_ADDR:
    gt_ohlcv_url = (f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/"
                    f"{MAIN_POOL_ADDR}/ohlcv/day?limit=60&currency=usd")
    d_ohlcv = fetch(gt_ohlcv_url, timeout=20)

    if "_error" not in d_ohlcv:
        ohlcv_data = d_ohlcv.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        p(f"  DEX OHLCV bars: {len(ohlcv_data)}")

        # Parse: [timestamp_sec, open, high, low, close, vol_usd]
        for bar in ohlcv_data:
            ts_sec = int(bar[0])
            d_str = datetime.fromtimestamp(ts_sec, tz=timezone.utc).strftime("%Y-%m-%d")
            o, h, l, c = safe_float(bar[1]), safe_float(bar[2]), safe_float(bar[3]), safe_float(bar[4])
            vol = safe_float(bar[5])
            dex_ohlcv.append({"date": d_str, "o": o, "h": h, "l": l, "c": c, "vol_usd": vol})

        dex_ohlcv.sort(key=lambda x: x["date"])
        p(f"  Date range: {dex_ohlcv[0]['date'] if dex_ohlcv else 'N/A'} -> {dex_ohlcv[-1]['date'] if dex_ohlcv else 'N/A'}")
        if dex_ohlcv:
            p(f"  Last 5 rows:")
            for row in dex_ohlcv[-5:]:
                p(f"  {row['date']}: px={row['c']:.5f} vol_dex=${row['vol_usd']:>10,.0f}")
    else:
        p(f"  GeckoTerminal OHLCV error: {d_ohlcv['_error']}")

time.sleep(1)

# Alpha daily series (already fetched)
p(f"\n  Alpha OHLCV ({ALPHA_ID}): {len(alpha_rows)} bars")
if alpha_rows:
    for row in alpha_rows[-5:]:
        p(f"  {row['date']}: px={row['px']:.5f} vol_alpha=${row['vol_quote']:>10,.0f}" +
          (f" taker={row['taker_pct']:.1%}" if row['taker_pct'] else ""))

# Freshwatch perp series (from earlier known data - hardcode key points)
perp_vol = {
    "2026-07-09": 9368282, "2026-07-10": 4985976, "2026-07-11": 42160637,
    "2026-07-12": 14714506, "2026-07-13": 6385355, "2026-07-14": 3913234,
    "2026-07-15": 4691117, "2026-07-16": 4130509, "2026-07-17": 3842080,
    "2026-07-18": 2797311, "2026-07-19": 1986039, "2026-07-20": 7229116,
    "2026-07-21": 15798077, "2026-07-22": 7489592, "2026-07-23": 4028569,
    "2026-07-27": 1525599, "2026-07-28": 2429507, "2026-07-29": 2232808,
    "2026-07-30": 1129865, "2026-07-31": 2392917,
    "2026-08-01": 9821947, "2026-08-02": 3062632, "2026-08-03": 17947839,
    "2026-08-04": 33252326,
}

p("\n### S1a-EXT: BINANCE SPOT KLINES (01/07->05/08)")
# Fetch full spot klines for campaign window
time.sleep(1)
spot_start = int(__import__('datetime').datetime(2026, 7, 1, tzinfo=__import__('datetime').timezone.utc).timestamp() * 1000)
spot_klines_url = f"https://api.binance.com/api/v3/klines?symbol=TUTUSDT&interval=1d&startTime={spot_start}&limit=40"
d_spot = fetch(spot_klines_url, timeout=15)
spot_rows = {}
if "_error" not in d_spot and isinstance(d_spot, list):
    for bar in d_spot:
        ts = int(bar[0])
        d_str = __import__('datetime').datetime.fromtimestamp(ts/1000, tz=__import__('datetime').timezone.utc).strftime("%Y-%m-%d")
        px_s = float(bar[4])
        vol_q_s = float(bar[7])
        base_s = float(bar[5])
        taker_b_s = float(bar[9])
        taker_pct_s = taker_b_s / base_s if base_s > 0 else None
        spot_rows[d_str] = {"px": px_s, "vol": vol_q_s, "taker": taker_pct_s}
    p(f"  Binance spot TUTUSDT klines: {len(spot_rows)} bars")
    if spot_rows:
        for d_str in sorted(spot_rows.keys())[-5:]:
            r = spot_rows[d_str]
            tk_s = f" taker={r['taker']:.1%}" if r['taker'] else ""
            p(f"  {d_str}: px={r['px']:.5f} vol=${r['vol']:>10,.0f}{tk_s}")
else:
    p(f"  Binance spot klines error: {d_spot.get('_error','?') if isinstance(d_spot,dict) else d_spot}")

p("\n### S2: SPOT/PERP RATIO TABLE (01/07->05/08)")
p(f"{'date':<12} {'perp_vol':>12} {'spot_bnb':>12} {'dex_bsc':>12} {'spot_tot':>12} {'s/p_ratio':>10} {'taker_s':>8}")
p("-" * 80)

# Build combined table
dex_dict = {r["date"]: r["vol_usd"] for r in dex_ohlcv}

all_dates_s2 = sorted(set(list(perp_vol.keys()) + list(dex_dict.keys()) + list(spot_rows.keys())))
# Filter to 01/07 onward
all_dates_s2 = [d for d in all_dates_s2 if d >= "2026-07-01"]

ratio_list = []
for d_str in all_dates_s2:
    pv = perp_vol.get(d_str)
    dv = dex_dict.get(d_str)
    sv = spot_rows.get(d_str, {}).get("vol")
    stk = spot_rows.get(d_str, {}).get("taker")
    spot_tot = (sv or 0) + (dv or 0)
    ratio = spot_tot / pv if pv and pv > 0 and spot_tot > 0 else None
    ratio_list.append((d_str, pv, dv, sv, spot_tot, ratio))

    pv_s = f"${pv/1e6:.2f}M" if pv else "N/A"
    sv_s = f"${sv/1e6:.2f}M" if sv else "N/A"
    dv_s = f"${dv/1e6:.2f}M" if dv else "N/A"
    st_s = f"${spot_tot/1e6:.2f}M" if spot_tot > 0 else "N/A"
    r_s = f"{ratio:.3f}x" if ratio else "N/A"
    tk_s = f"{stk:.1%}" if stk else "N/A"
    p(f"{d_str:<12} {pv_s:>12} {sv_s:>12} {dv_s:>12} {st_s:>12} {r_s:>10} {tk_s:>8}")

if ratio_list:
    valid_ratios = [r[5] for r in ratio_list if r[5] is not None]
    if valid_ratios:
        avg_r = sum(valid_ratios) / len(valid_ratios)
        med_r = sorted(valid_ratios)[len(valid_ratios)//2]
        p(f"\n  avg spot/perp ratio: {avg_r:.3f}x | median: {med_r:.3f}x")
        if avg_r < 0.1:
            p("  -> AKE-test: SPOT CANG GAN (ratio <<1) - spot KHONG phai chu dong")
        elif avg_r > 0.5:
            p("  -> AKE-test: SPOT CO THIT (ratio >0.5) - spot co the la venue chinh")
        else:
            p(f"  -> AKE-test: SPOT TRUNG BINH ({avg_r:.2f}x) - theo doi")

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S3a: DEX trades - sell-side audit
# ─────────────────────────────────────────────────────────────────
p("\n### S3a: DEX TRADES (sell-side audit)")

if MAIN_POOL_ADDR:
    gt_trades_url = (f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/"
                     f"{MAIN_POOL_ADDR}/trades?limit=100")
    d_trades = fetch(gt_trades_url, timeout=20)

    sells_by_day = {}
    buys_by_day = {}
    large_sells = []

    if "_error" not in d_trades:
        trades = d_trades.get("data", [])
        p(f"  Recent trades: {len(trades)}")

        for tr in trades:
            attr = tr.get("attributes", {})
            kind = attr.get("kind", "?")  # "buy" or "sell"
            ts_str = attr.get("block_timestamp", "")
            vol_usd = safe_float(attr.get("volume_in_usd"))
            price = safe_float(attr.get("price_from_in_usd"))

            # Parse date
            try:
                ts_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                d_str = ts_dt.strftime("%Y-%m-%d")
            except Exception:
                d_str = "unknown"

            if kind == "sell":
                sells_by_day[d_str] = sells_by_day.get(d_str, 0) + (vol_usd or 0)
                if vol_usd and vol_usd > 5000:
                    large_sells.append({"date": d_str, "vol_usd": vol_usd, "px": price})
            elif kind == "buy":
                buys_by_day[d_str] = buys_by_day.get(d_str, 0) + (vol_usd or 0)

        # Sell-side pattern
        all_trade_dates = sorted(set(list(sells_by_day.keys()) + list(buys_by_day.keys())))
        p(f"\n  Sells/Buys by day (recent {len(all_trade_dates)} days):")
        p(f"  {'date':<12} {'sell_vol':>12} {'buy_vol':>12} {'s/b ratio':>10}")
        for d_str in all_trade_dates[-14:]:
            sv = sells_by_day.get(d_str, 0)
            bv = buys_by_day.get(d_str, 0)
            sb_r = sv / bv if bv > 0 else None
            r_s = f"{sb_r:.2f}" if sb_r else "-"
            p(f"  {d_str:<12} ${sv:>10,.0f} ${bv:>10,.0f} {r_s:>10}")

        p(f"\n  Large sells (>$5k) in window:")
        large_sells.sort(key=lambda x: x["date"])
        for ls in large_sells[-20:]:
            p(f"  {ls['date']}: vol=${ls['vol_usd']:,.0f}, px={ls['px']}")

        # Distribution pattern check
        if len(sells_by_day) > 5:
            sell_vals = [v for v in sells_by_day.values() if v > 0]
            sell_vals.sort()
            avg_sell = sum(sell_vals)/len(sell_vals)
            # Check uniformity: std/mean
            import statistics
            if len(sell_vals) > 2:
                std_sell = statistics.stdev(sell_vals)
                cv = std_sell / avg_sell if avg_sell > 0 else None
                p(f"\n  Sell-side uniformity: avg=${avg_sell:,.0f}/day, CV={cv:.2f}" if cv else "")
                if cv and cv < 0.5:
                    p("  -> LOW CV (uniform sells) = organized distribution pattern suspected")
                elif cv and cv > 1.5:
                    p("  -> HIGH CV (lumpy sells) = likely retail/organic")
                else:
                    p(f"  -> MODERATE CV = mixed signal")
    else:
        p(f"  GeckoTerminal trades error: {d_trades['_error']}")

time.sleep(1)

# ─────────────────────────────────────────────────────────────────
# S3b: Cửa A capacity estimate
# ─────────────────────────────────────────────────────────────────
p("\n### S3b: CUA A CAPACITY (27 ngay 09/07->05/08)")

# Pool liquidity and vol data
main_pool_liq = None
main_pool_vol24h = None
for pool in pools:
    if pool["addr"] == MAIN_POOL_ADDR:
        main_pool_liq = pool["liq"]
        main_pool_vol24h = pool["vol24h"]
        break

if not main_pool_liq and pools:
    main_pool_liq = pools[0]["liq"] if pools else None
    main_pool_vol24h = pools[0]["vol24h"] if pools else None

p(f"  Pool liq snapshot: ${main_pool_liq:,.0f}" if main_pool_liq else "  Pool liq: N/A")
p(f"  Pool vol24h: ${main_pool_vol24h:,.0f}" if main_pool_vol24h else "  Pool vol24h: N/A")

# Average daily DEX vol from S2
if dex_ohlcv:
    # Use campaign window 09/07 onward
    campaign_dex = [r for r in dex_ohlcv if r["date"] >= "2026-07-09"]
    if campaign_dex:
        avg_dex = sum(r["vol_usd"] for r in campaign_dex) / len(campaign_dex)
        median_dex_vals = sorted([r["vol_usd"] for r in campaign_dex])
        med_dex = median_dex_vals[len(median_dex_vals)//2]
        p(f"\n  DEX vol in campaign (09/07->05/08):")
        p(f"    N days:      {len(campaign_dex)}")
        p(f"    avg/day:     ${avg_dex:,.0f}")
        p(f"    median/day:  ${med_dex:,.0f}")
        total_dex_campaign = sum(r["vol_usd"] for r in campaign_dex)
        p(f"    total:       ${total_dex_campaign:,.0f}")

        # Stealthy sell capacity: 10-30% of daily vol
        sell_cap_low = avg_dex * 0.10
        sell_cap_mid = avg_dex * 0.20
        sell_cap_high = avg_dex * 0.30

        p(f"\n  Stealthy sell capacity (10-30% of avg daily vol):")
        p(f"    10% (conservative): ${sell_cap_low:,.0f}/day")
        p(f"    20% (mid):          ${sell_cap_mid:,.0f}/day")
        p(f"    30% (aggressive):   ${sell_cap_high:,.0f}/day")

        # What if 50% of total DEX vol = sells (2-sided market)?
        sell_realside = total_dex_campaign * 0.50
        p(f"\n  If 50% of total DEX vol = actual sells:")
        p(f"    Total possible sell vol: ${sell_realside:,.0f}")
        p(f"    At px_avg ~0.015 USDT:   {sell_realside/0.015:,.0f} tokens")

        # 27 day estimate
        days = 27
        p(f"\n  27-day campaign estimate (capacity, not actual):")
        p(f"    Low  (10%): ${sell_cap_low*days:,.0f} ({sell_cap_low*days/0.015:,.0f} tokens at avg 0.015)")
        p(f"    Mid  (20%): ${sell_cap_mid*days:,.0f} ({sell_cap_mid*days/0.015:,.0f} tokens at avg 0.015)")
        p(f"    High (30%): ${sell_cap_high*days:,.0f} ({sell_cap_high*days/0.015:,.0f} tokens at avg 0.015)")
        p(f"    Total DEX 50%: ${sell_realside:,.0f} ({sell_realside/0.015:,.0f} tokens)")

# Alpha vol (if available and valid)
if alpha_rows:
    campaign_alpha = [r for r in alpha_rows if r["date"] >= "2026-07-09"]
    if campaign_alpha:
        avg_alpha = sum(r["vol_quote"] for r in campaign_alpha) / len(campaign_alpha)
        total_alpha = sum(r["vol_quote"] for r in campaign_alpha)
        p(f"\n  Alpha venue (ALPHA_117) in campaign:")
        p(f"    N days:    {len(campaign_alpha)}")
        p(f"    avg/day:   ${avg_alpha:,.0f}")
        p(f"    total:     ${total_alpha:,.0f}")
        p(f"    Note: {'TAKER INVALID (ABSTAIN)' if not alpha_taker_valid else 'taker valid'}")

p("\n### S3c: EXCHANGE BALANCE")
p("  PENDING OPERATOR - Nansen LOCKED")
p("  Can: 30D exchange balance chart TUT (Nansen hoac BscScan token holder snapshot)")
p("  Key question: kho tren san TANG hay GIAM tu 09/07?")
p("  -> TANG = nap them de dan (campaign support)")
p("  -> PHANG = ban noi san vo hinh / chua ban")
p("  -> GIAM MANH = da rut/relocate (phan phoi xong)")

# ─────────────────────────────────────────────────────────────────
# S4: Tong ket / verdict update
# ─────────────────────────────────────────────────────────────────
p("\n### S4: VERDICT V4 UPDATE")

if dex_ohlcv and campaign_dex:
    total_spot_campaign = total_dex_campaign + (total_alpha if alpha_rows and campaign_alpha else 0)
    perp_total = sum(perp_vol.values())
    p(f"\n  Tong vol campaign (09/07->04/08):")
    p(f"    Perp total:    ${perp_total:,.0f}")
    p(f"    DEX total:     ${total_dex_campaign:,.0f}")
    p(f"    Alpha total:   ${total_alpha:,.0f}" if alpha_rows and campaign_alpha else "    Alpha total:   N/A")
    p(f"    Spot total:    ${total_spot_campaign:,.0f}")
    p(f"    Spot/Perp:     {total_spot_campaign/perp_total:.3f}x")

    if total_spot_campaign / perp_total < 0.05:
        p("  -> SPOT RAN = spot vol khong dang ke vs perp (AKE-test FAIL)")
        p("     Kho CHUA xay qua spot o muc dang ke trong campaign window")
        p("     Monetize chinh = PERP only (~15-20% da exit)")
    elif total_spot_campaign / perp_total > 0.3:
        p("  -> SPOT CO THIT = spot venue la chinh")
        p("     Kiem tra them: spot vol buy-dominated hay sell-dominated?")
    else:
        r = total_spot_campaign/perp_total
        p(f"  -> SPOT TRUNG BINH ({r:.2f}x) = can them on-chain de phan xet")

# Write output
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")

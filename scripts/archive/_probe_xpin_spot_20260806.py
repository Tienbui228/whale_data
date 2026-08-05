# _probe_xpin_spot_20260806.py
# XS1-XS4: XPIN SPOT/DEX/ALPHA AUDIT
# Sources: GeckoTerminal API, Binance Alpha API, CoinGecko tickers, local store
# Output: scratch/xpin_spot_20260806.txt

import urllib.request, json, time, os, statistics
from datetime import datetime, timezone

CONTRACT = "0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6"
ALPHA_ID = "ALPHA_334"
CG_ID = "xpin-network"
OUT = r"D:\Data back test\whale_data\scratch\xpin_spot_20260806.txt"
STORE_ROOT = r"D:\Data back test\whale_data\data\raw\spot_klines_1d"

lines = []
def p(s):
    s2 = str(s).encode('ascii','replace').decode('ascii')
    print(s2)
    lines.append(s2)

def fetch(url, retries=3, delay=1.2):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent":"Mozilla/5.0",
                "Accept":"application/json"
            })
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read())
        except Exception as e:
            if i < retries-1: time.sleep(delay)
            else: return {"_error": str(e)}

p("="*72)
p("XPIN SPOT/DEX/ALPHA AUDIT - 2026-08-06")
p("="*72)

# ═══════════════════════════════════════════════════════════════════
# [XS1a] GECKOTERMINAL — all BSC pools for XPIN contract
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS1a] GECKOTERMINAL — ALL BSC POOLS FOR XPIN CONTRACT")
url_pools = f"https://api.geckoterminal.com/api/v2/networks/bsc/tokens/{CONTRACT}/pools?page=1"
raw_pools = fetch(url_pools)
pools = []
if isinstance(raw_pools, dict) and "data" in raw_pools:
    for pool in raw_pools["data"]:
        attr = pool.get("attributes", {})
        pool_id = pool.get("id","")   # e.g. "bsc_0x..."
        addr = pool_id.replace("bsc_","")
        name = attr.get("name","?")
        liq = attr.get("reserve_in_usd") or 0
        v24 = attr.get("volume_usd",{}).get("h24") or 0
        v7d = attr.get("volume_usd",{}).get("d7") or 0
        v30d = attr.get("volume_usd",{}).get("d30") or 0
        created = attr.get("pool_created_at","?")
        price_usd = attr.get("base_token_price_usd","?")
        tx_h24 = attr.get("transactions",{}).get("h24",{})
        buys_h24 = tx_h24.get("buys",0)
        sells_h24 = tx_h24.get("sells",0)
        pools.append({
            "addr":addr, "name":name,
            "liq":float(liq), "v24":float(v24), "v7d":float(v7d), "v30d":float(v30d),
            "created":created, "px_usd":price_usd,
            "buys_24h":buys_h24, "sells_24h":sells_h24
        })
    p(f"  Found {len(pools)} pools on BSC")
    for pl in pools:
        p(f"  {pl['name']:<35} liq=${pl['liq']:>10,.0f} v24=${pl['v24']:>10,.0f} "
          f"v7d=${pl['v7d']:>10,.0f} v30d=${pl['v30d']:>10,.0f}")
        p(f"    addr={pl['addr']}  created={pl['created']}  buys24={pl['buys_24h']} sells24={pl['sells_24h']}")
else:
    p(f"  ERROR or no data: {raw_pools}")

# Sort by liquidity
if pools:
    main_pool = sorted(pools, key=lambda x: x["liq"], reverse=True)[0]
    p(f"\n  MAIN POOL: {main_pool['name']} addr={main_pool['addr']}")
    p(f"  Liq=${main_pool['liq']:,.0f} | v24=${main_pool['v24']:,.0f} | v7d=${main_pool['v7d']:,.0f} | v30d=${main_pool['v30d']:,.0f}")
    p(f"  Created: {main_pool['created']}")
    # vol/liq ratio
    ratio_24h = main_pool['v24']/main_pool['liq'] if main_pool['liq']>0 else None
    p(f"  vol/liq ratio (24h): {ratio_24h:.3f}" if ratio_24h else "  vol/liq: N/A")
else:
    main_pool = None

# Pool detail endpoint for full address
time.sleep(1)
p("\n  [XS1a-detail] Pool attribute detail:")
if main_pool:
    url_detail = f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{main_pool['addr']}"
    det = fetch(url_detail)
    if isinstance(det, dict) and "data" in det:
        attr = det["data"]["attributes"]
        p(f"  base_token: {attr.get('base_token_price_usd','?')} USD")
        p(f"  fee_tier: {attr.get('pool_fee','?')}")
        p(f"  tx count 24h: buys={attr.get('transactions',{}).get('h24',{}).get('buys','?')} sells={attr.get('transactions',{}).get('h24',{}).get('sells','?')}")
        p(f"  tx count 7d:  buys={attr.get('transactions',{}).get('d7',{}).get('buys','?')} sells={attr.get('transactions',{}).get('d7',{}).get('sells','?')}")
    else:
        p(f"  ERROR: {det}")

# ═══════════════════════════════════════════════════════════════════
# [XS1b] ALPHA ALPHA_334 — store + endpoint
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS1b] BINANCE ALPHA ALPHA_334 — STORE + KLINES")

# Local store check
p("  Local store check:")
found_alpha = []
for root, dirs, files in os.walk(STORE_ROOT):
    for f in files:
        if "xpin" in f.lower() or "XPIN" in f:
            found_alpha.append(os.path.join(root, f))
p(f"  Files with 'XPIN' in store: {len(found_alpha)}")
for f in found_alpha[:5]:
    p(f"    {f}")

# Check alpha_id_map
map_path = r"D:\Data back test\whale_data\data\config\alpha_id_map.json"
if os.path.exists(map_path):
    with open(map_path, encoding="utf-8") as fh:
        id_map = json.load(fh)
    xpin_entry = {k:v for k,v in id_map.items() if "XPIN" in k}
    p(f"  alpha_id_map XPIN entries: {xpin_entry}")
else:
    p("  alpha_id_map.json NOT FOUND")

# Alpha klines endpoint
p("  Fetching Alpha klines (daily, limit=365)...")
time.sleep(0.8)
url_alpha = f"https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines?coinId={ALPHA_ID}&interval=1d&limit=365"
raw_alpha = fetch(url_alpha)
alpha_bars = []
if isinstance(raw_alpha, dict) and "data" in raw_alpha and raw_alpha["data"]:
    data_a = raw_alpha["data"]
    p(f"  Alpha bars received: {len(data_a)}")
    for bar in data_a:
        ts_ms = bar[0]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        o,h,l,c = float(bar[1]),float(bar[2]),float(bar[3]),float(bar[4])
        vol_token = float(bar[5])   # base volume (tokens)
        vol_usd   = float(bar[7])   # quote volume
        # bar[9]=taker base, bar[10]=taker quote
        try:
            taker_base = float(bar[9]); taker_vol = float(bar[10])
            taker_pct = taker_base/vol_token if vol_token>0 else None
        except:
            taker_pct = None
        alpha_bars.append({"date":d,"o":o,"h":h,"l":l,"c":c,"vol_usd":vol_usd,"taker":taker_pct})
    p(f"  Alpha range: {alpha_bars[0]['date']} -> {alpha_bars[-1]['date']}")
    # summary stats
    vols = [b["vol_usd"] for b in alpha_bars if b["vol_usd"]>0]
    if vols:
        p(f"  Alpha vol_usd: avg=${statistics.mean(vols):,.0f} max=${max(vols):,.0f} min=${min(vols):,.0f}")
    # taker check — note: Alpha klines[9]==klines[5] means taker=ABSTAIN
    sample = alpha_bars[-1]
    tk_s = "ABSTAIN (Alpha)" if sample['taker'] is None or abs((sample['taker'] or 0)-1)<0.01 else f"{sample['taker']:.1%}"
    p(f"  Latest bar {sample['date']}: px=${sample['c']:.6f} vol_usd=${sample['vol_usd']:,.0f} taker={tk_s}")
elif isinstance(raw_alpha, dict) and "code" in raw_alpha:
    p(f"  Alpha API response code: {raw_alpha.get('code')} msg: {raw_alpha.get('message','')}")
    p(f"  Alpha klines: ENDPOINT ERROR")
    alpha_bars = []
else:
    p(f"  Alpha klines result: {str(raw_alpha)[:200]}")
    alpha_bars = []

# Build alpha dict for XS2 merge
alpha_dict = {b["date"]: b for b in alpha_bars}

# ═══════════════════════════════════════════════════════════════════
# [XS1c] CEX WASH TEST — CoinGecko tickers
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS1c] CEX WASH TEST — COINGECKO TICKERS")
time.sleep(1)
url_tickers = f"https://api.coingecko.com/api/v3/coins/{CG_ID}/tickers?include_exchange_logo=false&page=1&depth=true"
raw_tickers = fetch(url_tickers)
if isinstance(raw_tickers, dict) and "tickers" in raw_tickers:
    tickers = raw_tickers["tickers"]
    p(f"  Total tickers: {len(tickers)}")
    p(f"  {'Exchange':<22} {'Pair':<12} {'vol24_USD':>15} {'liq_usd':>12} {'vol/liq':>8} {'spread':>8} {'trust':>6} {'flag'}")
    for tk in sorted(tickers, key=lambda x: x.get("converted_volume",{}).get("usd",0), reverse=True)[:15]:
        exch = tk.get("market",{}).get("name","?")[:20]
        pair = (tk.get("base","")+"/"+ tk.get("target",""))[:11]
        vol_usd = tk.get("converted_volume",{}).get("usd",0) or 0
        bid_ask = tk.get("bid_ask_spread_percentage") or 0
        trust = tk.get("trust_score") or "?"
        liq = tk.get("cost_to_move_up_usd") or tk.get("cost_to_move_down_usd") or 0
        # vol/liq ratio
        vol_liq = vol_usd/liq if liq>0 else None
        # anomaly flag
        flag = ""
        if vol_usd > 5_000_000 and (vol_liq is None or vol_liq > 20): flag = "SUSPECT"
        if vol_usd > 50_000_000 and (vol_liq is None or vol_liq > 50): flag = "HIGH-SUSPECT"
        if trust == "green": flag = flag or "OK"
        vl_str = f"{vol_liq:.1f}" if vol_liq else "N/A"
        p(f"  {exch:<22} {pair:<12} ${vol_usd:>14,.0f} ${liq:>11,.0f} {vl_str:>8} {bid_ask:>7.2f}% {str(trust):>6} {flag}")
else:
    p(f"  ERROR: {raw_tickers}")

# ═══════════════════════════════════════════════════════════════════
# [XS2] GECKOTERMINAL OHLCV DAILY — main pool
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS2] GECKOTERMINAL DAILY OHLCV — MAIN POOL")
dex_bars = []
if main_pool:
    time.sleep(1.2)
    url_ohlcv = f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{main_pool['addr']}/ohlcv/day?limit=365&currency=usd&token=base"
    raw_ohlcv = fetch(url_ohlcv)
    if isinstance(raw_ohlcv, dict) and "data" in raw_ohlcv:
        ohlcv_list = raw_ohlcv["data"].get("attributes",{}).get("ohlcv_list",[])
        p(f"  Bars received: {len(ohlcv_list)}")
        for bar in reversed(ohlcv_list):  # GT returns newest first
            ts = bar[0]
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            d = dt.strftime("%Y-%m-%d")
            o,h,l,c = float(bar[1]),float(bar[2]),float(bar[3]),float(bar[4])
            vol_usd = float(bar[5])
            dex_bars.append({"date":d,"o_dex":o,"h_dex":h,"l_dex":l,"c_dex":c,"vol_dex":vol_usd})
        if dex_bars:
            p(f"  DEX range: {dex_bars[0]['date']} -> {dex_bars[-1]['date']}")
    else:
        p(f"  ERROR ohlcv: {raw_ohlcv}")

# Build DEX dict
dex_dict = {b["date"]: b for b in dex_bars}

# Fetch perp klines for comparison
p("\n  Fetching perp klines for px comparison...")
time.sleep(0.8)
url_perp = "https://fapi.binance.com/fapi/v1/klines?symbol=XPINUSDT&interval=1d&limit=400"
raw_perp = fetch(url_perp)
perp_dict = {}
if isinstance(raw_perp, list):
    for b in raw_perp:
        ts_ms = b[0]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        perp_dict[d] = {"c_perp":float(b[4]),"vol_perp":float(b[7]),"taker_perp":float(b[10])/float(b[7]) if float(b[7])>0 else None}

# ─── XS2 Pivot: combined DEX + Perp + Alpha daily ───
# Key windows: Campaign1 (Oct 16-26), Fail (Jul 10-11), peak-div (Jul 17), crowd (Jul 22-Aug5)
WINDOWS = {
    "campaign1": ("2025-10-16","2025-10-27"),
    "campaign2": ("2025-12-19","2025-12-24"),
    "fail_ignition": ("2026-07-08","2026-07-13"),
    "peak_div": ("2026-07-15","2026-07-19"),
    "crowd_surge": ("2026-07-22","2026-08-05"),
}

p("\n  [XS2] DAILY PIVOT — DEX vol + px vs perp + Alpha vol")
p(f"  Key: vol_dex=GeckoTerminal pool USD | vol_alpha=Alpha klines USD | c_dex=pool close | c_perp=fapi close")
p(f"  Note: DEX pool created 2025-08-20 → pool coverage starts then")
p(f"  {'date':<12} {'vol_dex':>10} {'vol_alpha':>10} {'vol_perp':>12} {'dex/perp':>9} {'c_dex':>10} {'c_perp':>10} {'px_gap%':>8} {'window'}")
p("  " + "-"*95)

# Find all dates covered
all_dates = sorted(set(list(dex_dict.keys()) + list(alpha_dict.keys()) + list(perp_dict.keys())))
# Filter to reasonable range (pool creation onward)
all_dates = [d for d in all_dates if d >= "2025-08-20"]

def in_window(d):
    for name, (start, end) in WINDOWS.items():
        if start <= d <= end: return name
    return ""

def fmt_vol(v):
    if v is None: return "    ---"
    if v >= 1e6: return f"{v/1e6:>6.2f}M"
    if v >= 1e3: return f"{v/1e3:>6.1f}K"
    return f"{v:>7.0f}"

# Print all rows (but compress quiet periods)
prev_window = ""
quiet_streak = 0
for d in all_dates:
    dex = dex_dict.get(d,{})
    alpha = alpha_dict.get(d,{})
    perp = perp_dict.get(d,{})
    vd = dex.get("vol_dex")
    va = alpha.get("vol_usd")
    vp = perp.get("vol_perp")
    cd = dex.get("c_dex")
    cp = perp.get("c_perp")
    win = in_window(d)
    px_gap = ((cd/cp-1)*100) if (cd and cp and cp>0) else None
    dex_perp = vd/vp if (vd and vp and vp>0) else None

    # always print window rows; compress quiet (no dex + no alpha vol)
    is_notable = bool(win) or (vd and vd>50000) or (va and va>100000)
    if not is_notable:
        quiet_streak += 1
        if quiet_streak == 1:
            p(f"  ... quiet rows (DEX vol<$50K, Alpha vol<$100K) ...")
        continue
    quiet_streak = 0

    px_gap_s = f"{px_gap:+.2f}%" if px_gap is not None else "     ---"
    dex_perp_s = f"{dex_perp:.4f}" if dex_perp is not None else "      ---"
    va_s = fmt_vol(va)
    vd_s = fmt_vol(vd)
    vp_s = fmt_vol(vp)
    win_s = f"[{win}]" if win else ""
    p(f"  {d:<12} {vd_s:>10} {va_s:>10} {vp_s:>12} {dex_perp_s:>9} {str(cd or '---'):>10} {str(cp or '---'):>10} {px_gap_s:>8} {win_s}")

# Window summaries
p("\n  [XS2] WINDOW SUMMARIES:")
for wname, (ws, we) in WINDOWS.items():
    w_dates = [d for d in all_dates if ws <= d <= we]
    w_vd = [dex_dict[d]["vol_dex"] for d in w_dates if d in dex_dict and dex_dict[d].get("vol_dex")]
    w_va = [alpha_dict[d]["vol_usd"] for d in w_dates if d in alpha_dict and alpha_dict[d].get("vol_usd")]
    w_vp = [perp_dict[d]["vol_perp"] for d in w_dates if d in perp_dict and perp_dict[d].get("vol_perp")]
    total_dex = sum(w_vd)
    total_alpha = sum(w_va)
    total_perp = sum(w_vp)
    dex_ratio = total_dex/total_perp if total_perp>0 else None
    alpha_ratio = total_alpha/total_perp if total_perp>0 else None
    p(f"  [{wname}] {ws} to {we}: {len(w_dates)} days")
    p(f"    DEX total=${total_dex:,.0f} Alpha=${total_alpha:,.0f} Perp=${total_perp:,.0f}")
    if total_perp>0:
        p(f"    DEX/perp ratio={dex_ratio:.4f}" if dex_ratio else "    DEX/perp: N/A")
        p(f"    Alpha/perp ratio={alpha_ratio:.4f}" if alpha_ratio else "    Alpha/perp: N/A")

# ═══════════════════════════════════════════════════════════════════
# [XS3a] CROWD SURGE CHECK: DEX/Alpha vol expansion last 14d
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS3a] CROWD SURGE: DEX/ALPHA VOL Jul22→Aug05 vs prior period")
crowd_dates = [d for d in all_dates if "2026-07-22" <= d <= "2026-08-05"]
prior_dates = [d for d in all_dates if "2026-07-08" <= d <= "2026-07-21"]

def window_stats(dates, label):
    vd_list = [dex_dict[d].get("vol_dex",0) for d in dates if d in dex_dict]
    va_list = [alpha_dict[d].get("vol_usd",0) for d in dates if d in alpha_dict]
    vp_list = [perp_dict[d].get("vol_perp",0) for d in dates if d in perp_dict]
    n = len(dates)
    p(f"  {label} ({n} days):")
    p(f"    DEX avg/day=${sum(vd_list)/max(n,1):,.0f} total=${sum(vd_list):,.0f}")
    p(f"    Alpha avg/day=${sum(va_list)/max(n,1):,.0f} total=${sum(va_list):,.0f}")
    p(f"    Perp avg/day=${sum(vp_list)/max(n,1):,.0f} total=${sum(vp_list):,.0f}")
    return sum(vd_list)/max(n,1), sum(va_list)/max(n,1), sum(vp_list)/max(n,1)

prior_dex, prior_alpha, prior_perp = window_stats(prior_dates, "Prior (Jul08-Jul21)")
crowd_dex, crowd_alpha, crowd_perp = window_stats(crowd_dates, "Crowd surge (Jul22-Aug05)")

if prior_dex>0: p(f"  DEX vol change: {crowd_dex/prior_dex:.2f}x")
if prior_alpha>0: p(f"  Alpha vol change: {crowd_alpha/prior_alpha:.2f}x")
if prior_perp>0: p(f"  Perp vol change: {crowd_perp/prior_perp:.2f}x")

# ═══════════════════════════════════════════════════════════════════
# [XS3b] RECENT TRADES — GeckoTerminal (last ~1-2 days)
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS3b] RECENT TRADES — GECKOTERMINAL (last ~24-48h)")
if main_pool:
    time.sleep(1)
    url_trades = f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{main_pool['addr']}/trades?trade_volume_in_usd_greater_than=0"
    raw_trades = fetch(url_trades)
    if isinstance(raw_trades, dict) and "data" in raw_trades:
        trades = raw_trades["data"]
        p(f"  Trades returned: {len(trades)}")
        buys=[]; sells=[]
        for tr in trades:
            attr = tr.get("attributes",{})
            kind = attr.get("kind","?")
            usd = float(attr.get("volume_in_usd",0) or 0)
            ts = attr.get("block_timestamp","?")
            sender = attr.get("tx_from_address","?")
            if kind == "buy": buys.append({"usd":usd,"ts":ts,"sender":sender})
            else: sells.append({"usd":usd,"ts":ts,"sender":sender})
        total_buy = sum(t["usd"] for t in buys)
        total_sell = sum(t["usd"] for t in sells)
        p(f"  Buys: {len(buys)} trades = ${total_buy:,.0f}")
        p(f"  Sells: {len(sells)} trades = ${total_sell:,.0f}")
        p(f"  Buy/sell ratio: {total_buy/(total_sell+0.01):.2f}")
        if buys or sells:
            p(f"\n  Top 10 trades by size:")
            all_t = [(t["usd"], t["ts"], "BUY", t["sender"]) for t in buys] + \
                    [(t["usd"], t["ts"], "SELL", t["sender"]) for t in sells]
            for usd, ts, kind, sender in sorted(all_t, key=lambda x: -x[0])[:10]:
                p(f"    {kind:<5} ${usd:>8,.0f}  {ts[:19] if ts else '?'}  {str(sender)[:10]}...")
        # Large wallet detection
        wallet_vol = {}
        for tr in trades:
            attr = tr.get("attributes",{})
            sender = attr.get("tx_from_address","?")
            usd = float(attr.get("volume_in_usd",0) or 0)
            kind = attr.get("kind","?")
            if sender not in wallet_vol: wallet_vol[sender] = {"buy":0,"sell":0}
            wallet_vol[sender][kind] = wallet_vol[sender].get(kind,0) + usd
        p(f"\n  Top wallets by total vol:")
        for w, vols in sorted(wallet_vol.items(), key=lambda x: -(x[1].get("buy",0)+x[1].get("sell",0)))[:5]:
            total = vols.get("buy",0)+vols.get("sell",0)
            p(f"    {str(w)[:12]}... buy=${vols.get('buy',0):,.0f} sell=${vols.get('sell',0):,.0f} total=${total:,.0f}")
    else:
        p(f"  Trades error: {raw_trades}")

# ═══════════════════════════════════════════════════════════════════
# [XS3c] FAILED IGNITION Jul 10-11 AUTOPSY — DEX contribution
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS3c] FAILED IGNITION Jul10-11 AUTOPSY — DEX/Alpha vs Perp")
for d in ["2026-07-09","2026-07-10","2026-07-11","2026-07-12","2026-07-13"]:
    dex = dex_dict.get(d,{})
    alpha = alpha_dict.get(d,{})
    perp = perp_dict.get(d,{})
    vd = dex.get("vol_dex")
    va = alpha.get("vol_usd")
    vp = perp.get("vol_perp")
    cd = dex.get("c_dex")
    cp = perp.get("c_perp")
    px_gap = ((cd/cp-1)*100) if (cd and cp and cp>0) else None
    label = ""
    if d == "2026-07-10": label = "<-- pre-ignition"
    if d == "2026-07-11": label = "<-- FAIL ignition ($207M perp)"
    if vd and vp:
        pg_s = f"{px_gap:+.2f}%" if px_gap is not None else "---"
        p(f"  {d}: DEX=${vd:>9,.0f} Alpha=${(va or 0):>9,.0f} Perp=${vp:>12,.0f}  "
          f"dex/perp={vd/vp:.5f} px_gap={pg_s}  {label}")
    else:
        p(f"  {d}: DEX={vd} Alpha={va} Perp={vp}  {label}")

# ═══════════════════════════════════════════════════════════════════
# [XS1c-b] DETECTION FLOOR: kho X% supply vs DEX vol
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS1d] DETECTION FLOOR (kho_vol_ratio) — DEX/Alpha scenario")
p("  Circulating supply (Alpha): 48,074,534,161 tokens")
p("  Total supply: 100,000,000,000 tokens")
p("  Current px: ~$0.00155")
p("  PENDING OPERATOR: actual kho size (BscScan)")
p("")
p("  Scenario A — kho = 5% of circulating = 2.4B tokens @ $0.00155 = $3.72M")
for scenario_name, kho_tokens, kho_label in [
    ("5% circ", 2_403_726_708, "2.4B tokens"),
    ("10% circ", 4_807_453_416, "4.8B tokens"),
    ("1% total", 1_000_000_000, "1B tokens"),
    ("5% total", 5_000_000_000, "5B tokens"),
]:
    kho_usd = kho_tokens * 0.00155
    # DEX vol reference
    recent_dex_dates = [d for d in all_dates if "2026-07-22" <= d <= "2026-08-05"]
    recent_dex_vols = [dex_dict[d]["vol_dex"] for d in recent_dex_dates if d in dex_dict and dex_dict[d].get("vol_dex")]
    avg_dex_vol = sum(recent_dex_vols)/len(recent_dex_vols) if recent_dex_vols else 100000
    recent_alpha_vols = [alpha_dict[d]["vol_usd"] for d in recent_dex_dates if d in alpha_dict and alpha_dict[d].get("vol_usd")]
    avg_alpha_vol = sum(recent_alpha_vols)/len(recent_alpha_vols) if recent_alpha_vols else 50000
    total_spot_day = avg_dex_vol + avg_alpha_vol
    ratio = kho_usd / total_spot_day
    p(f"  {scenario_name} ({kho_label}) = ${kho_usd:,.0f}")
    p(f"    vs avg_dex=${avg_dex_vol:,.0f}/day + avg_alpha=${avg_alpha_vol:,.0f}/day = ${total_spot_day:,.0f}/day")
    p(f"    kho_vol_ratio = {ratio:.1f}x daily spot — DETECTABLE if selling >1d")

# ═══════════════════════════════════════════════════════════════════
# [XS1c-final] VENUE MAP + DETECTION FLOOR SUMMARY
# ═══════════════════════════════════════════════════════════════════
p("\n### [XS1-FINAL] VENUE MAP AUDIT SUMMARY")
p("  Venue              | Vol/day est   | Vol/liq | Trust | Verdict")
p("  -------------------+---------------+---------+-------+--------")
if pools:
    for pl in sorted(pools, key=lambda x: -x["liq"]):
        v24 = pl["v24"]
        liq = pl["liq"]
        ratio = v24/liq if liq>0 else None
        r_s = f"{ratio:.2f}" if ratio else "N/A"
        p(f"  BSC DEX {pl['name'][:20]:<20} | ${v24:>10,.0f} | {r_s:>7} | DEX | {'OK' if liq>100000 else 'TINY'}")

p("  ALPHA_334 (Alpha)             | see above    | N/A     | Alpha | Store check above")
p("  BitMart (CG #1)               | $1.1B        | UNKNOWN | ?     | SUSPECT (see XS1c)")
p("  Gate/MEXC/KuCoin              | $37-104M     | UNKNOWN | ?     | WATCH")
p("  ETH DEX (Uniswap 3 pools)     | $0           | N/A     | DEX   | LOCKED/FAKE liq")
p("  Solana pools                  | $0-8/day     | N/A     | DEX   | DIFFERENT TOKEN")

# ═══════════════════════════════════════════════════════════════════
# WRITE OUTPUT
# ═══════════════════════════════════════════════════════════════════
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")

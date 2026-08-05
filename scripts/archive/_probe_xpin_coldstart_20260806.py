# -*- coding: utf-8 -*-
"""XPIN cold-start: X0 identity, X1 venue map, X2 full series, X3 analysis seed."""
import urllib.request, json, ssl, time, subprocess, os
from datetime import datetime, timezone, timedelta

OUT = "scratch/xpin_coldstart_20260806.txt"
lines = []

def p(s=""):
    print(str(s).encode('ascii', 'replace').decode('ascii'))
    lines.append(str(s))

def fetch(url, timeout=18, retries=3):
    ctx = ssl.create_default_context()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries-1: time.sleep(2+attempt*2)
            else: return {"_error": str(e)}

def sf(x, d=None):
    try: return float(x)
    except: return d

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
p("=" * 72)
p(f"XPIN COLD-START PACK - {TS}")
p("=" * 72)

# ─── X0: IDENTITY ─────────────────────────────────────────────────
p("\n### [X0] CĂNCƯỚC — IDENTITY")

# X0a: Binance perp exchange info
p("\n  [X0a] Binance FAPI exchange info for XPIN:")
d_ei = fetch("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=25)
xpin_info = None
if "_error" not in d_ei:
    syms = d_ei.get("symbols", [])
    for s in syms:
        if s.get("symbol") == "XPINUSDT":
            xpin_info = s
            break
    if xpin_info:
        p(f"  FOUND: XPINUSDT perp")
        p(f"  onboardDate: {xpin_info.get('onboardDate')}")
        p(f"  contractType: {xpin_info.get('contractType')}")
        p(f"  status: {xpin_info.get('status')}")
        p(f"  settleCurrency: {xpin_info.get('settleCurrency')}")
        onboard_ts = xpin_info.get("onboardDate")
        if onboard_ts:
            onboard_dt = datetime.fromtimestamp(int(onboard_ts)/1000, tz=timezone.utc)
            age_d = (datetime.now(timezone.utc) - onboard_dt).days
            p(f"  onboard_datetime: {onboard_dt.strftime('%Y-%m-%d %H:%M UTC')}")
            p(f"  age_days: {age_d}d (guard §5: <14d = block all signals)")
    else:
        p("  NOT FOUND: XPINUSDT perp not in Binance FAPI")
else:
    p(f"  fapi exchangeInfo error: {d_ei.get('_error')}")

time.sleep(1)

# X0b: Binance spot info
p("\n  [X0b] Binance Spot (SAPI) for XPINUSDT:")
d_spot_ei = fetch("https://api.binance.com/api/v3/exchangeInfo?symbol=XPINUSDT", timeout=15)
if "_error" not in d_spot_ei:
    spot_syms = d_spot_ei.get("symbols", [])
    if spot_syms:
        sp = spot_syms[0]
        p(f"  FOUND: XPINUSDT spot | status={sp.get('status')}")
        p(f"  baseAsset={sp.get('baseAsset')} quoteAsset={sp.get('quoteAsset')}")
    else:
        p("  NOT FOUND: XPINUSDT spot")
else:
    p(f"  Spot info: {d_spot_ei.get('_error','not found')}")

time.sleep(1)

# X0c: CoinGecko search
p("\n  [X0c] CoinGecko search 'xpin':")
cg_s = fetch("https://api.coingecko.com/api/v3/search?query=xpin", timeout=15)
cg_id = None
if "_error" not in cg_s:
    coins = cg_s.get("coins", [])
    p(f"  Results: {len(coins)}")
    for c in coins[:6]:
        p(f"  -> {c.get('id','?'):30s} | {c.get('name','?'):25s} | {c.get('symbol','?')}")
        if c.get("symbol","").upper() == "XPIN":
            cg_id = c.get("id")
            p(f"  *** XPIN match: id={cg_id}")

time.sleep(1)

# X0d: CoinGecko coin detail
if cg_id:
    p(f"\n  [X0d] CoinGecko /coins/{cg_id}:")
    cg_c = fetch(f"https://api.coingecko.com/api/v3/coins/{cg_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false", timeout=20)
    if "_error" not in cg_c:
        md = cg_c.get("market_data", {})
        mc  = md.get("market_cap",{}).get("usd")
        fdv = md.get("fully_diluted_valuation",{}).get("usd")
        px  = md.get("current_price",{}).get("usd")
        total_s = md.get("total_supply")
        circ_s  = md.get("circulating_supply")
        platforms = cg_c.get("asset_platform_id","?")
        contract  = cg_c.get("contract_address","?")
        genesis   = cg_c.get("genesis_date","?")
        chains    = cg_c.get("detail_platforms",{})
        p(f"  name={cg_c.get('name')} symbol={cg_c.get('symbol')}")
        p(f"  px=${px} MC=${mc:,.0f} FDV=${fdv:,.0f}" if mc else "  MC/FDV unavailable")
        p(f"  total_supply={total_s:,.0f} circulating={circ_s:,.0f}" if total_s else "")
        p(f"  platform={platforms} contract={contract}")
        p(f"  genesis_date={genesis}")
        p(f"  chains_detail: {list(chains.keys())}")
        for ch, v in chains.items():
            p(f"    {ch}: {v.get('contract_address','?')}")

time.sleep(1)

# ─── X1: VENUE MAP ────────────────────────────────────────────────
p("\n### [X1] VENUE MAP")

# X1a: Binance spot klines check
p("\n  [X1a] Binance Spot klines XPINUSDT:")
d_sp_k = fetch("https://api.binance.com/api/v3/klines?symbol=XPINUSDT&interval=1d&limit=5", timeout=15)
if "_error" not in d_sp_k and isinstance(d_sp_k, list) and d_sp_k:
    p(f"  EXISTS: {len(d_sp_k)} bars")
    for bar in d_sp_k[-3:]:
        ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        tb = sf(bar[9]); bb = sf(bar[5])
        tk = tb/bb if (tb and bb and bb>0) else None
        p(f"  {ds}: C={bar[4]} vol=${sf(bar[7]):,.0f} taker={tk:.1%}" if tk else f"  {ds}: {bar[4]}")
else:
    p(f"  NOT EXISTS or error: {d_sp_k}")

time.sleep(1)

# X1b: Binance Alpha (try common XPIN alpha ID)
p("\n  [X1b] Binance Alpha — search XPIN:")
# Try to find from token list
alpha_list = fetch("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", timeout=20)
xpin_alpha_id = None
if "_error" not in alpha_list:
    tokens = alpha_list.get("data", {}).get("tokenList", []) if isinstance(alpha_list.get("data"), dict) else []
    if not tokens:
        tokens = alpha_list.get("data", []) if isinstance(alpha_list.get("data"), list) else []
    p(f"  Alpha token list: {len(tokens)} tokens")
    for t in tokens:
        sym = str(t.get("symbol","")).upper()
        if "XPIN" in sym:
            xpin_alpha_id = t.get("id") or t.get("alphaId")
            p(f"  FOUND: {t}")
    if not xpin_alpha_id:
        p("  XPIN not found in Alpha list")
else:
    p(f"  Alpha list error: {alpha_list.get('_error','?')}")

time.sleep(1)

# X1c: GeckoTerminal search BSC + ETH
p("\n  [X1c] GeckoTerminal DEX search 'XPIN':")
for network in ["bsc", "eth", "solana"]:
    gt = fetch(f"https://api.geckoterminal.com/api/v2/search/pools?query=XPIN&network={network}&page=1", timeout=15)
    if "_error" not in gt:
        pools = gt.get("data", [])
        p(f"  [{network}] {len(pools)} pools")
        for pool in pools[:4]:
            attr = pool.get("attributes",{})
            name = attr.get("name","?")
            addr = attr.get("address","?")
            liq  = sf(attr.get("reserve_in_usd"))
            v24  = sf(attr.get("volume_usd",{}).get("h24"))
            cre  = attr.get("pool_created_at","?")[:10]
            p(f"    {name:28s} liq=${liq:>10,.0f} v24=${v24:>9,.0f} addr={addr[:12]}... created={cre}")
    else:
        p(f"  [{network}] error: {gt.get('_error','?')}")
    time.sleep(0.5)

time.sleep(1)

# X1d: CoinGecko tickers
if cg_id:
    p(f"\n  [X1d] CoinGecko tickers (markets) for {cg_id}:")
    tickers = fetch(f"https://api.coingecko.com/api/v3/coins/{cg_id}/tickers?page=1", timeout=15)
    if "_error" not in tickers:
        tk_list = tickers.get("tickers",[])
        p(f"  {len(tk_list)} tickers")
        for t in sorted(tk_list, key=lambda x: x.get("volume",0), reverse=True)[:8]:
            exch = t.get("market",{}).get("name","?")
            pair = f"{t.get('base','?')}/{t.get('target','?')}"
            vol  = t.get("volume",0); px = t.get("last",0)
            trust = t.get("trust_score","?")
            p(f"  {exch:22s} {pair:12s} vol=${vol:>14,.0f} px={px:.6f} trust={trust}")

time.sleep(1)

# ─── X2: FULL DATA SERIES ─────────────────────────────────────────
p("\n### [X2] FULL DATA SERIES")

# X2a: fapi klines — fetch max available (1000 bars = ~2.7y at 1d)
p("\n  [X2a] FAPI 1d klines (max 1000 bars):")
klines = []
d_k = fetch("https://fapi.binance.com/fapi/v1/klines?symbol=XPINUSDT&interval=1d&limit=1000", timeout=25)
if "_error" not in d_k and isinstance(d_k, list):
    klines = d_k
    p(f"  Total bars: {len(klines)}")
    if klines:
        first_dt = datetime.fromtimestamp(int(klines[0][0])/1000, tz=timezone.utc)
        last_dt  = datetime.fromtimestamp(int(klines[-1][0])/1000, tz=timezone.utc)
        p(f"  Range: {first_dt.strftime('%Y-%m-%d')} -> {last_dt.strftime('%Y-%m-%d')}")
        p(f"  Total days: {(last_dt - first_dt).days}")
else:
    p(f"  Klines error: {d_k}")

time.sleep(1)

# X2b: funding history (last 1000 intervals = ~167d at 4h/interval)
p("\n  [X2b] Funding rate history (max 1000 intervals):")
funding = []
d_f = fetch("https://fapi.binance.com/fapi/v1/fundingRate?symbol=XPINUSDT&limit=1000", timeout=20)
if "_error" not in d_f and isinstance(d_f, list):
    funding = d_f
    p(f"  Total funding intervals: {len(funding)}")
    if funding:
        f_first = datetime.fromtimestamp(int(funding[0].get("fundingTime",0))/1000, tz=timezone.utc)
        f_last  = datetime.fromtimestamp(int(funding[-1].get("fundingTime",0))/1000, tz=timezone.utc)
        p(f"  Range: {f_first.strftime('%Y-%m-%d %H:00')} -> {f_last.strftime('%Y-%m-%d %H:00')}")
        rates = [sf(x.get("fundingRate")) for x in funding if sf(x.get("fundingRate")) is not None]
        PIN = 5e-5
        pin_cnt = sum(1 for r in rates if abs(r - PIN) < 5e-6)
        p(f"  Rate range: min={min(rates):.5f} max={max(rates):.5f} avg={sum(rates)/len(rates):.5f}")
        p(f"  PIN (5e-5 ±5e-6) count: {pin_cnt}/{len(rates)} ({pin_cnt/len(rates):.1%})")
else:
    p(f"  Funding error: {d_f}")

time.sleep(1)

# X2c: OI history (last 90d at 1d)
p("\n  [X2c] OI history (1d, 90 bars):")
d_oi = fetch("https://fapi.binance.com/futures/data/openInterestHist?symbol=XPINUSDT&period=1d&limit=90", timeout=15)
oi_hist = []
if "_error" not in d_oi and isinstance(d_oi, list):
    oi_hist = d_oi
    p(f"  OI bars: {len(oi_hist)}")
    if oi_hist:
        oi_vals = [sf(x.get("sumOpenInterestValue")) for x in oi_hist if sf(x.get("sumOpenInterestValue"))]
        p(f"  OI range: min=${min(oi_vals)/1e6:.3f}M max=${max(oi_vals)/1e6:.3f}M latest=${oi_vals[-1]/1e6:.3f}M")
else:
    p(f"  OI error: {d_oi}")

time.sleep(1)

# X2d: LSR daily
p("\n  [X2d] gLSR + pos_r daily (30d):")
d_glsr = fetch("https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=XPINUSDT&period=1d&limit=30", timeout=15)
glsr_hist = []
if "_error" not in d_glsr and isinstance(d_glsr, list):
    glsr_hist = d_glsr
    p(f"  gLSR bars: {len(glsr_hist)}")
    if glsr_hist:
        gs = [sf(x.get("longShortRatio")) for x in glsr_hist if sf(x.get("longShortRatio"))]
        p(f"  gLSR range: min={min(gs):.3f} max={max(gs):.3f} latest={gs[-1]:.3f}")

d_pos = fetch("https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=XPINUSDT&period=1d&limit=30", timeout=15)
pos_hist = []
if "_error" not in d_pos and isinstance(d_pos, list):
    pos_hist = d_pos
    if pos_hist:
        ps = [sf(x.get("longShortRatio")) for x in pos_hist if sf(x.get("longShortRatio"))]
        p(f"  pos_r range: min={min(ps):.3f} max={max(ps):.3f} latest={ps[-1]:.3f}")

d_acc = fetch("https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=XPINUSDT&period=1d&limit=30", timeout=15)
acc_hist = []
if "_error" not in d_acc and isinstance(d_acc, list):
    acc_hist = d_acc
    if acc_hist:
        acs = [sf(x.get("longShortRatio")) for x in acc_hist if sf(x.get("longShortRatio"))]
        p(f"  acc_r range: min={min(acs):.3f} max={max(acs):.3f} latest={acs[-1]:.3f}")

time.sleep(1)

# X2e: VPS freshwatch check
p("\n  [X2e] VPS freshwatch check (universe + date range):")
try:
    r_vps = subprocess.run(
        ["ssh", "root@5.223.67.21",
         "grep -c 'XPIN' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv 2>/dev/null; "
         "grep -c 'XPIN' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv 2>/dev/null; "
         "grep 'XPIN' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv 2>/dev/null | head -5"],
        capture_output=True, text=True, timeout=20)
    p(f"  VPS output:\n  {r_vps.stdout.strip()}")
except Exception as e:
    p(f"  VPS error: {e}")

time.sleep(1)

# X2f: local backup store check
p("\n  [X2f] Local backup store check:")
local_paths = [
    "D:/Data back test/whale_data/data/raw",
    "D:/Check onchain fresh wallets/u50_data",
]
for lp in local_paths:
    if os.path.exists(lp):
        p(f"  Checking {lp}:")
        import glob
        xpin_files = glob.glob(f"{lp}/**/*XPIN*", recursive=True)
        p(f"    XPIN files: {len(xpin_files)}")
        if xpin_files:
            for f in xpin_files[:3]: p(f"    {f}")
    else:
        p(f"  {lp}: NOT EXISTS")

# ─── X3: SIDEWAY ANATOMY ─────────────────────────────────────────
p("\n### [X3] GIẢI PHẪU SIDEWAY (computed from klines + funding)")

if klines:
    # Parse klines
    bars = []
    for bar in klines:
        dt = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc)
        o,h,l,c = sf(bar[1]),sf(bar[2]),sf(bar[3]),sf(bar[4])
        v = sf(bar[7]);  tb = sf(bar[9]); bb = sf(bar[5])
        tk = tb/bb if (tb and bb and bb>0) else None
        bars.append({"dt":dt,"d":dt.strftime("%Y-%m-%d"),"o":o,"h":h,"l":l,"c":c,"v":v,"tk":tk})

    # ① Range
    p("\n  [①] SIDEWAY RANGE:")
    all_dates = [b["d"] for b in bars]
    all_c = [b["c"] for b in bars if b["c"]]
    if all_c:
        recent_14 = [b for b in bars[-14:] if b["c"]]
        recent_30 = [b for b in bars[-30:] if b["c"]]
        all_H = max(b["h"] for b in bars if b["h"])
        all_L = min(b["l"] for b in bars if b["l"])
        r14_H = max(b["h"] for b in recent_14)
        r14_L = min(b["l"] for b in recent_14)
        r30_H = max(b["h"] for b in recent_30)
        r30_L = min(b["l"] for b in recent_30)
        p(f"  All-time H={all_H:.6f} L={all_L:.6f} range={all_H/all_L-1:.1%}")
        p(f"  30d range: H={r30_H:.6f} L={r30_L:.6f} band={r30_H/r30_L-1:.1%}")
        p(f"  14d range: H={r14_H:.6f} L={r14_L:.6f} band={r14_H/r14_L-1:.1%}")
        # Check narrowing
        monthly_bands = []
        for i in range(0, len(bars), 7):
            chunk = bars[i:i+7]
            if len(chunk) >= 3:
                ch = max(b["h"] for b in chunk if b["h"])
                cl = min(b["l"] for b in chunk if b["l"])
                monthly_bands.append((chunk[0]["d"], ch/cl-1))
        if len(monthly_bands) >= 3:
            p(f"  Weekly band trend (last 5 weeks):")
            for (d,band) in monthly_bands[-5:]:
                p(f"    {d}: {band:.1%}")

    # Print full daily table (last 30d)
    p(f"\n  Full kline table (last 30d):")
    p(f"  {'date':<12} {'O':>8} {'H':>8} {'L':>8} {'C':>8} {'vol_$':>10} {'taker':>7} {'ret_1d':>7}")
    prev_c = None
    bars_30 = bars[-30:]
    for b in bars_30:
        ret = (b["c"]/prev_c - 1) if (prev_c and b["c"] and prev_c>0) else None
        vol_s = f"${b['v']/1e6:.2f}M"
        tk_s = f"{b['tk']:.1%}" if b['tk'] else 'N/A'
        ret_s = f"{ret:.1%}" if ret else ''
        p(f"  {b['d']:<12} {b['o']:>8.5f} {b['h']:>8.5f} {b['l']:>8.5f} {b['c']:>8.5f} "
          f"{vol_s:>10} {tk_s:>7} {ret_s:>7}")
        prev_c = b["c"]

    # ② Funding analysis over window
    p("\n  [②] FUNDING REGIME (full history):")
    if funding:
        PIN = 5e-5
        EPS = 5e-6
        # compute streaks
        streak = 0; max_streak = 0; streak_start = None; max_streak_start = None
        breaks = []
        for item in funding:
            ts = int(item.get("fundingTime",0))
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:00")
            r = sf(item.get("fundingRate"))
            if r is None: continue
            if abs(r - PIN) < EPS:
                if streak == 0: streak_start = dt
                streak += 1
                if streak > max_streak:
                    max_streak = streak
                    max_streak_start = streak_start
            else:
                if streak > 0:
                    breaks.append({"end": dt, "rate": r, "streak_before": streak})
                streak = 0

        p(f"  PIN (5e-5) count: {sum(1 for x in funding if sf(x.get('fundingRate')) and abs(sf(x.get('fundingRate'))-PIN)<EPS)}/{len(funding)}")
        p(f"  Max consecutive PIN streak: {max_streak} intervals ({max_streak*4/24:.1f}d) starting {max_streak_start}")
        p(f"  PIN streak currently: {streak} intervals")
        p(f"  Break events (last 10):")
        for br in breaks[-10:]:
            p(f"    broke at {br['end']}: f={br['rate']:.5f} (after {br['streak_before']} PIN)")

        # Last 20 funding intervals
        p(f"\n  Last 20 funding intervals:")
        for item in funding[-20:]:
            ts = int(item.get("fundingTime",0))
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%m-%d %H:00")
            r = sf(item.get("fundingRate"))
            tag = " [PIN]" if r and abs(r-PIN)<EPS else ""
            p(f"    {dt}: f={r:.5f}{tag}" if r is not None else f"    {dt}: err")

    # ③ Absorption (taker 44-50.5% with stable price)
    p("\n  [③] ABSORPTION ANALYSIS:")
    if bars:
        abs_days = [(b["d"], b["tk"], b["c"]) for b in bars
                    if b["tk"] and 0.44 <= b["tk"] <= 0.505 and b["c"]]
        p(f"  Days taker 44-50.5%: {len(abs_days)}/{len(bars)} ({len(abs_days)/len(bars):.0%})")
        # Check consecutive absorption streaks
        streak_abs = 0; max_abs = 0
        for b in bars:
            if b["tk"] and 0.44 <= b["tk"] <= 0.505:
                streak_abs += 1
                max_abs = max(max_abs, streak_abs)
            else:
                streak_abs = 0
        p(f"  Max consecutive absorption days: {max_abs}")
        p(f"  Current streak: {streak_abs}")

    # ④ div structure (need gLSR + pos_r + acc_r by date)
    p("\n  [④] DIV STRUCTURE (pos_r/acc_r):")
    if pos_hist and acc_hist:
        pos_d = {datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d"):
                 sf(x.get("longShortRatio")) for x in pos_hist}
        acc_d = {datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d"):
                 sf(x.get("longShortRatio")) for x in acc_hist}
        divs = [(d, pos_d[d]/acc_d[d]) for d in sorted(pos_d) if d in acc_d and acc_d[d] and pos_d[d]]
        if divs:
            dv = [v for d,v in divs]
            p(f"  div range: min={min(dv):.3f} max={max(dv):.3f} latest={dv[-1]:.3f}")
            p(f"  Interpretation:")
            p(f"    div>=1.5 -> Structure A (lsr_accum) = mm holding big perp longs vs accounts")
            p(f"    div<=0.5 -> Structure B (hedge) = POWER-khuon: perp longs nho but account long")
            p(f"    div~1.0  -> No clear structure = L-07 (con moi, sideway vo chu)")
            latest_div = dv[-1]
            if latest_div >= 1.5:
                p(f"  CURRENT ({latest_div:.3f}): STRUCTURE A — accumulated longs concentrated")
            elif latest_div <= 0.5:
                p(f"  CURRENT ({latest_div:.3f}): STRUCTURE B — POWER-khuon / hedge structure")
            else:
                p(f"  CURRENT ({latest_div:.3f}): NEUTRAL / weak structure — watch for change")
            p(f"\n  div table (last 14d):")
            for (d,v) in divs[-14:]:
                pr = pos_d.get(d); ar = acc_d.get(d)
                p(f"    {d}: pos_r={pr:.3f} acc_r={ar:.3f} div={v:.3f}" if (pr and ar) else f"    {d}: div={v:.3f}")

    # ⑤ gLSR + slope
    p("\n  [⑤] gLSR + SLOPE:")
    if glsr_hist:
        glsr_d = {datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d"):
                  sf(x.get("longShortRatio")) for x in glsr_hist}
        gs_vals = [(d, glsr_d[d]) for d in sorted(glsr_d) if glsr_d[d]]
        if gs_vals:
            gv = [v for d,v in gs_vals]
            p(f"  gLSR range (30d): min={min(gv):.3f} max={max(gv):.3f} latest={gv[-1]:.3f}")
            # simple slope last 5d
            if len(gv) >= 5:
                slope5 = (gv[-1] - gv[-5]) / 5
                p(f"  gLSR slope 5d: {slope5:+.4f}/day")
            p(f"\n  gLSR table (last 14d):")
            for (d,v) in gs_vals[-14:]:
                lp = sf(next((x.get("longAccount") for x in glsr_hist
                              if datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")==d), None))
                p(f"    {d}: gLSR={v:.3f} long={lp:.1%}" if lp else f"    {d}: gLSR={v:.3f}")

    # ⑥ OI analysis
    p("\n  [⑥] OI ANALYSIS:")
    if oi_hist:
        oi_dates = []
        for item in oi_hist:
            ts = int(item.get("timestamp",0))
            d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            v = sf(item.get("sumOpenInterestValue"))
            if v: oi_dates.append((d,v))
        if oi_dates:
            ov = [v for d,v in oi_dates]
            p(f"  OI min=${min(ov)/1e6:.3f}M max=${max(ov)/1e6:.3f}M latest=${ov[-1]/1e6:.3f}M")
            p(f"  OI floor (min): ${min(ov)/1e6:.3f}M at {[d for d,v in oi_dates if v==min(ov)][0]}")
            # Bait-probe events: OI spike >50% in 1d then reversal
            p(f"\n  OI table (last 14d):")
            for (d,v) in oi_dates[-14:]:
                p(f"    {d}: OI=${v/1e6:.3f}M")
            # Ignition attempts: vol spikes
            p(f"\n  [⑦] BAIT-PROBE scan (vol >=8x avg):")
            vol_vals = [b["v"] for b in bars if b["v"] and b["v"]>0]
            if vol_vals:
                avg_vol = sum(vol_vals)/len(vol_vals)
                p(f"  avg_vol (all time): ${avg_vol/1e6:.2f}M")
                probes = [(b["d"], b["v"], b["h"]/b["l"]-1 if b["l"] else 0)
                          for b in bars if b["v"] and b["v"] >= avg_vol*8]
                p(f"  vol >=8x avg days: {len(probes)}")
                for pd, pv, pr in probes[-10:]:
                    p(f"    {pd}: vol=${pv/1e6:.1f}M ({pv/avg_vol:.0f}x) range={pr:.1%}")

# ─── Full OI + LSR tables ─────────────────────────────────────────
p("\n  Full OI+gLSR+pos_r table (last 30d):")
p(f"  {'date':<12} {'OI_USD':>10} {'gLSR':>6} {'pos_r':>6} {'acc_r':>6} {'div':>6}")
oi_d = {}; gs_d2 = {}; ps_d = {}; ac_d = {}
if oi_hist:
    for x in oi_hist:
        d = datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_d[d] = sf(x.get("sumOpenInterestValue"))
if glsr_hist:
    for x in glsr_hist:
        d = datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        gs_d2[d] = sf(x.get("longShortRatio"))
if pos_hist:
    for x in pos_hist:
        d = datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        ps_d[d] = sf(x.get("longShortRatio"))
if acc_hist:
    for x in acc_hist:
        d = datetime.fromtimestamp(int(x["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        ac_d[d] = sf(x.get("longShortRatio"))

all_d = sorted(set(list(oi_d.keys())+list(gs_d2.keys())+list(ps_d.keys())))[-30:]
for d in all_d:
    oi_v = oi_d.get(d); gs_v = gs_d2.get(d); ps_v = ps_d.get(d); ac_v = ac_d.get(d)
    div_v = (ps_v/ac_v) if (ps_v and ac_v and ac_v>0) else None
    p(f"  {d:<12} {f'${oi_v/1e6:.3f}M':>10} {f'{gs_v:.3f}' if gs_v else 'N/A':>6} "
      f"{f'{ps_v:.3f}' if ps_v else 'N/A':>6} {f'{ac_v:.3f}' if ac_v else 'N/A':>6} "
      f"{f'{div_v:.3f}' if div_v else 'N/A':>6}")

# X4: major events
p("\n### [X4] MAJOR EVENTS (vol/price outliers all history):")
if bars:
    vol_vals2 = [b["v"] for b in bars if b["v"] and b["v"]>0]
    avg_v = sum(vol_vals2)/len(vol_vals2) if vol_vals2 else 1
    med_v = sorted(vol_vals2)[len(vol_vals2)//2] if vol_vals2 else 1
    p(f"  avg_vol={avg_v/1e6:.2f}M med_vol={med_v/1e6:.2f}M")
    events = [(b["d"], b["v"], b["c"], b["h"]/b["l"]-1 if b["l"] else 0,
               b["c"]/bars[i-1]["c"]-1 if i>0 and bars[i-1]["c"] else None)
              for i,b in enumerate(bars) if b["v"] and b["v"] >= avg_v*3]
    events_price = [(b["d"], b["v"], b["c"], abs(b["h"]/b["l"]-1) if b["l"] else 0)
                    for b in bars if b["h"] and b["l"] and b["l"]>0 and b["h"]/b["l"]>1.15]
    all_events = sorted(set(events + events_price), key=lambda x: x[0])
    p(f"  Events (vol>=3x avg OR intraday range>=15%): {len(all_events)}")
    for (d, v, c, rng, ret) in events[:30]:
        p(f"  {d}: vol=${v/1e6:.2f}M ({v/avg_v:.1f}x) C={c:.5f} range={rng:.1%} ret={f'{ret:.1%}' if ret else 'N/A'}")

# ─── SAVE ─────────────────────────────────────────────────────────
with open(OUT, "w", encoding="utf-8") as fout:
    fout.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")

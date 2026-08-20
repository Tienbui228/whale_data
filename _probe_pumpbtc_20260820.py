"""_probe_pumpbtc_20260820.py — PUMPBTC identity + full readout.
Discipline: L-51 4-step · L-52 venue sweep · L-53/54 STATIC-SEAT · anti-collision.
Read-only. Nến đóng L-21: D-1 = 2026-08-19. Window 60d cuối (or from listing if shorter).
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
from statistics import median

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
EXPORT = ROOT / "data" / "export"

SYM = "PUMPBTC"
TICKER = "PUMPBTCUSDT"
END = "2026-08-19"
END_DT = _date.fromisoformat(END)
START_HINT = (END_DT - timedelta(days=60)).isoformat()

def fetch_json(url, params=None, timeout=15):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}
def to_ms(d): return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
def safe_float(v):
    if v in (None,"","None"): return None
    try: return float(v)
    except: return None
def hr(t): print("\n" + "="*70 + f"\n{t}\n" + "="*70)

# ═══════════════════════════════════════════════════════════════════════
# P0.① fapi + ANTI-COLLISION check
# ═══════════════════════════════════════════════════════════════════════
hr("[P0.① PERP fapi + anti-collision (PUMP-family)]")
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
time.sleep(0.3)
if isinstance(d, dict):
    pump_family = [s for s in d.get("symbols",[]) if "PUMP" in s.get("symbol","")]
    print(f"  PUMP-family fapi symbols: {len(pump_family)}")
    for s in pump_family:
        print(f"    {s.get('symbol')} · status={s.get('status')} · base={s.get('baseAsset')} · quote={s.get('quoteAsset')} · onboard={s.get('onboardDate')}")
    perp_meta = next((s for s in pump_family if s.get("symbol") == TICKER), None)
    if perp_meta:
        onboard_ms = perp_meta.get("onboardDate")
        onboard_d = ms_to_date(onboard_ms) if onboard_ms else "?"
        tick = next((f.get('tickSize') for f in perp_meta.get('filters',[]) if f.get('filterType')=='PRICE_FILTER'), '?')
        print(f"\n  TARGET PUMPBTCUSDT: status={perp_meta.get('status')} onboard={onboard_d} tickSize={tick}")
        PERP_START = onboard_d if onboard_d > START_HINT else START_HINT
        print(f"    → window start: {PERP_START} (max of onboard or END-60d)")
    else:
        print(f"\n  TARGET PUMPBTCUSDT: NOT FOUND")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════
# P0.② CONTRACT
# ═══════════════════════════════════════════════════════════════════════
hr("[P0.② CONTRACT — operator feed required]")
print("  Contract 0x + chain: UNVERIFIED (chờ operator relay)")
print("  → mọi alpha/venue map [UNVERIFIED] cho tới khi contract confirmed")

# ═══════════════════════════════════════════════════════════════════════
# P0.③ Alpha bapi + mirror check
# ═══════════════════════════════════════════════════════════════════════
hr("[P0.③ Alpha bapi (symbol-string, ⚠ F1 risk)]")
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
time.sleep(0.3)
alpha_hits = []
if isinstance(d, dict) and "data" in d:
    # Check PUMPBTC + PUMP separately (anti-collision)
    for tok in d.get("data") or []:
        sym_up = str(tok.get("symbol","")).upper()
        if "PUMP" in sym_up:
            alpha_hits.append(tok)
if not alpha_hits:
    print("  Alpha bapi: 0 PUMP-family match")
else:
    print(f"  Alpha PUMP-family entries: {len(alpha_hits)}")
    for tok in alpha_hits:
        print(f"    symbol={tok.get('symbol')} alphaId={tok.get('alphaId')} name={tok.get('name')} "
              f"fullyDelisted={tok.get('fullyDelisted')} offline={tok.get('offline')} "
              f"chain={tok.get('chainName')} contract={tok.get('contractAddress')}")

# Mirror check for any PUMPBTC-matching alpha
pumpbtc_alpha = next((t for t in alpha_hits if str(t.get("symbol","")).upper() == "PUMPBTC"), None)
if pumpbtc_alpha:
    aid = pumpbtc_alpha.get("alphaId")
    print(f"\n  [Mirror check] Alpha klines schema for {aid}USDT (last 3 days):")
    d = fetch_json("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines",
                   {"symbol": f"{aid}USDT", "interval":"1d", "limit":3})
    time.sleep(0.3)
    if isinstance(d, dict) and "data" in d and d["data"]:
        for k in d["data"][:3]:
            bv = float(k[5]); tv = float(k[9]) if len(k)>=10 else None
            q = float(k[7]); tq = float(k[10]) if len(k)>=11 else None
            mirror = (bv==tv and q==tq)
            print(f"    {ms_to_date(int(k[0]))}: k[5]={bv} k[9]={tv} bit-eq={bv==tv if tv else '-'}  "
                  f"k[7]={q} k[10]={tq} bit-eq={q==tq if tq else '-'} mirror={mirror}")
    else:
        print(f"    (Alpha klines returned empty/error)")
else:
    print("\n  No Alpha PUMPBTC to mirror-check")

# ═══════════════════════════════════════════════════════════════════════
# P0.④ Venue sweep L-52 + price-band ±20%
# ═══════════════════════════════════════════════════════════════════════
hr("[P0.④ VENUE SWEEP — 7 venues + deposit/withdraw flags]")

def bybit_probe(sym):
    d = fetch_json("https://api.bybit.com/v5/market/instruments-info",
                   {"category":"spot","symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        lst = d.get("result",{}).get("list",[])
        if lst: return lst[0]
    return None

def okx_probe(sym):
    d = fetch_json("https://www.okx.com/api/v5/public/instruments",
                   {"instType":"SPOT","instId":f"{sym}-USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "0":
        lst = d.get("data",[])
        if lst: return lst[0]
    return None

def gate_probe(sym):
    d = fetch_json(f"https://api.gateio.ws/api/v4/spot/currency_pairs/{sym}_USDT")
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("id"): return d
    return None

def kucoin_probe(sym):
    d = fetch_json(f"https://api.kucoin.com/api/v1/symbols/{sym}-USDT")
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "200000" and d.get("data"):
        return d.get("data")
    return None

def mexc_probe(sym):
    d = fetch_json("https://api.mexc.com/api/v3/exchangeInfo", {"symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("symbols"):
        return d["symbols"][0]
    return None

def bitget_probe(sym):
    d = fetch_json("https://api.bitget.com/api/v2/spot/public/symbols", {"symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "00000":
        lst = d.get("data",[])
        if lst: return lst[0]
    return None

def bnc_probe(sym):
    d = fetch_json("https://api.binance.com/api/v3/exchangeInfo", {})
    time.sleep(0.3)
    if isinstance(d, dict) and "symbols" in d:
        m = [s for s in d["symbols"] if s.get("baseAsset")==sym]
        if m: return m[0]
    return None

venues = {}
probes = [("binance_spot", bnc_probe),("bybit", bybit_probe),("okx", okx_probe),
          ("gate", gate_probe),("kucoin", kucoin_probe),("mexc", mexc_probe),("bitget", bitget_probe)]
for name, fn in probes:
    r = fn(SYM)
    venues[name] = r
    print(f"\n  {name}: {'FOUND' if r else 'NOT_FOUND'}")
    if r:
        for k in ["symbol","baseAsset","baseCoin","quoteAsset","quoteCoin","status","state","trade_status","enableTrading"]:
            if k in r:
                print(f"    {k}: {r.get(k)}")

# Deposit/withdraw flags (Gate)
if venues.get("gate"):
    d = fetch_json("https://api.gateio.ws/api/v4/wallet/currency_chains", {"currency": SYM})
    time.sleep(0.3)
    if isinstance(d, list) and d:
        print(f"\n  Gate wallet/currency_chains {SYM}:")
        for ch in d:
            print(f"    chain={ch.get('chain')} name={ch.get('name_cn')} "
                  f"deposit_disabled={ch.get('is_deposit_disabled')} "
                  f"withdraw_disabled={ch.get('is_withdraw_disabled')}")

# ═══════════════════════════════════════════════════════════════════════
# P1 — PERP FULL
# ═══════════════════════════════════════════════════════════════════════
hr(f"[P1 PERP FULL {PERP_START} → {END}]")
s_ms = to_ms(PERP_START); e_ms = to_ms(END) + 86400000 - 1

d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol":TICKER,"interval":"1d","startTime":s_ms,"endTime":e_ms,"limit":100})
time.sleep(0.3)
perp = {}
for k in d if isinstance(d, list) else []:
    d_str = ms_to_date(int(k[0]))
    if d_str < PERP_START or d_str > END: continue
    vol_q = float(k[7]); taker_q = float(k[10])
    perp[d_str] = {
        "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
        "vol_quote_usd": round(vol_q, 2),
        "taker_buy_pct": round(taker_q/vol_q*100, 4) if vol_q > 0 else None,
    }
print(f"  perp days: {len(perp)}, range={min(perp)}→{max(perp)}")

# funding
fund_all = []; cur = s_ms
while cur <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol":TICKER,"startTime":cur,"endTime":e_ms,"limit":1000})
    time.sleep(0.3)
    if not isinstance(d, list) or not d: break
    fund_all.extend(d)
    last = int(d[-1]["fundingTime"])
    if last <= cur or last >= e_ms: break
    cur = last + 1
fund_by_d = {}
for it in fund_all:
    ts = int(it["fundingTime"]); d_str = ms_to_date(ts)
    if PERP_START <= d_str <= END:
        fund_by_d.setdefault(d_str, []).append({"ts": ts, "fr": float(it["fundingRate"])})
print(f"  funding: {len(fund_by_d)} days, {sum(len(v) for v in fund_by_d.values())} entries")
# interval verify
anom = []
for d_str in sorted(fund_by_d):
    tss = sorted(x["ts"] for x in fund_by_d[d_str])
    if len(tss) >= 2:
        intervals = [(tss[i]-tss[i-1])/3600000 for i in range(1,len(tss))]
        med = median(intervals)
        if abs(med - 4) > 0.5 and abs(med - 8) > 0.5:
            anom.append((d_str, med))
if anom:
    print(f"  ⚠ interval anomalies: {anom[:5]}")
else:
    print(f"  L-41 interval verified: 4h × 6/day majority ✓")

# OI (30d limit)
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol":TICKER,"period":"1d","limit":30})
time.sleep(0.3)
oi_by_d = {}
seen = set()
for it in d if isinstance(d, list) else []:
    ts = int(it["timestamp"]); d_str = ms_to_date(ts)
    key = (d_str, str(ts))
    if key in seen: continue
    seen.add(key)
    oi_by_d[d_str] = {
        "oi_usd": float(it["sumOpenInterestValue"] or 0),
        "oi_token": float(it["sumOpenInterest"] or 0),
    }
print(f"  OI: {len(oi_by_d)} days (30d limit)")

# LSR freshwatch
lsr_fw = {}
in_fw139 = False
FW139 = ROOT / "scratch" / "freshwatch_symbols.txt"
if FW139.exists():
    with open(FW139, encoding="utf-8", errors="ignore") as f:
        fw139_set = set(l.strip().upper() for l in f if l.strip())
    in_fw139 = TICKER in fw139_set
print(f"  PUMPBTCUSDT in fw-139: {in_fw139}")

for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = safe_float(row.get("lsr_pos_r"))
            if not d_str or not pr: continue
            lsr_fw[d_str] = {
                "pos_r": pr, "acc_r": safe_float(row.get("lsr_acc_r")),
                "gLSR": safe_float(row.get("lsr_global_r")),
                "taker_lsr": safe_float(row.get("taker_ratio")),
            }
print(f"  freshwatch LSR: {len(lsr_fw)} days" +
      (f", range={min(lsr_fw)}→{max(lsr_fw)}" if lsr_fw else ""))

# fapi 3-endpoint fallback
def fetch_ep(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol":TICKER,"period":"1d","limit":30})
    time.sleep(0.3)
    by_d = {}
    for it in d if isinstance(d, list) else []:
        ts = int(it["timestamp"]); by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d
lsr_top_pos = fetch_ep("topLongShortPositionRatio")
lsr_top_acc = fetch_ep("topLongShortAccountRatio")
lsr_glo     = fetch_ep("globalLongShortAccountRatio")
print(f"  fapi topPos {len(lsr_top_pos)}d · topAcc {len(lsr_top_acc)}d · global {len(lsr_glo)}d")

# ═══════════════════════════════════════════════════════════════════════
# taker scale
tk_samples = [perp[d]["taker_buy_pct"] for d in perp if perp[d]["taker_buy_pct"] is not None]
if tk_samples:
    mn, mx = min(tk_samples), max(tk_samples)
    scale = "percent" if mn > 1.0 else "fraction" if mx <= 1.5 else "mixed"
    print(f"  TAKER SCALE: range {mn:.2f}-{mx:.2f} = {scale} ✓" if scale=="percent" else f"  TAKER SCALE: {scale} range {mn}-{mx}")

# ═══════════════════════════════════════════════════════════════════════
# Build per-day table (30d cuối for readout focus)
# ═══════════════════════════════════════════════════════════════════════
hr(f"[P1 PER-DAY TABLE last 30d]")
start_30d = (END_DT - timedelta(days=29)).isoformat()
d0 = _date.fromisoformat(start_30d); d1 = END_DT
days = []; cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)

table = []
prev_c = None
for d_str in days:
    p = perp.get(d_str, {})
    if not p:
        table.append({"date": d_str, "_miss": True}); continue
    c = p["c"]
    frs = [x["fr"] for x in fund_by_d.get(d_str,[])]
    fn = len(frs); f_avg = round(sum(frs)/fn, 8) if fn else None
    pin = f_avg is not None and 4e-5 <= f_avg <= 6e-5
    oi_r = oi_by_d.get(d_str, {})
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r, acc_r, gl = fw["pos_r"], fw["acc_r"], fw["gLSR"]; src = "fw"
    else:
        pos_r = lsr_top_pos.get(d_str); acc_r = lsr_top_acc.get(d_str); gl = lsr_glo.get(d_str)
        src = "fapi" if pos_r else "-"
    ret = round((c-prev_c)/prev_c*100, 2) if (c and prev_c) else None
    prev_c = c if c else prev_c
    div = round(pos_r/acc_r, 3) if (pos_r and acc_r) else None
    table.append({"date": d_str, "c": c, "ret": ret, "vol": p["vol_quote_usd"],
                  "oi": oi_r.get("oi_usd"), "f_avg": f_avg, "fn": fn, "pin": pin,
                  "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl, "div": div,
                  "taker": p["taker_buy_pct"], "src": src})
# div_avg3
for i, r in enumerate(table):
    if i < 2 or r.get("_miss"): continue
    p3 = [table[j].get("pos_r") for j in range(i-2, i+1) if table[j].get("pos_r")]
    a3 = [table[j].get("acc_r") for j in range(i-2, i+1) if table[j].get("acc_r")]
    if len(p3)==3 and len(a3)==3:
        aa = sum(a3)/3
        r["div3"] = round((sum(p3)/3)/aa, 4) if aa else None

# Print
print(f"  {'date':<11} {'c':>10} {'ret%':>6} {'vol':>10} {'oi':>10} {'f_avg':>10} {'fn':>3} "
      f"{'pin':>4} {'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'div':>6} {'div3':>6} {'tk%':>6} {'src':>4}")
def fmt(v, w, prec=2): return f"{v:>{w}.{prec}f}" if v is not None else " "*w
for r in table:
    if r.get("_miss"): print(f"  {r['date']:<11}  (missing perp)"); continue
    print(f"  {r['date']:<11} {fmt(r['c'],10,6)} {fmt(r['ret'],6,2)} "
          f"{fmt(r['vol'],10,0)} {fmt(r['oi'],10,0)} {fmt(r['f_avg'],10,6)} "
          f"{str(r['fn'] or ''):>3} {str(r['pin']):>4} "
          f"{fmt(r['pos_r'],6,3)} {fmt(r['acc_r'],6,3)} {fmt(r['gLSR'],6,3)} "
          f"{fmt(r['div'],6,3)} {fmt(r.get('div3'),6,3)} {fmt(r['taker'],6,2)} {r['src']:>4}")

# ═══════════════════════════════════════════════════════════════════════
# P2 CHÂN HÀNG: pick venue-lớn-nhất via 24h ticker vol
# ═══════════════════════════════════════════════════════════════════════
hr("[P2 CHÂN HÀNG — venue-lớn-nhất chosen by 24h vol]")

def venue_vol_24h(venue, sym):
    try:
        if venue == "bybit":
            d = fetch_json("https://api.bybit.com/v5/market/tickers", {"category":"spot","symbol":f"{sym}USDT"})
            time.sleep(0.3)
            if d.get("retCode")==0 and d["result"]["list"]:
                r = d["result"]["list"][0]
                return float(r.get("turnover24h") or 0), r
        elif venue == "gate":
            d = fetch_json(f"https://api.gateio.ws/api/v4/spot/tickers", {"currency_pair":f"{sym}_USDT"})
            time.sleep(0.3)
            if isinstance(d, list) and d:
                r = d[0]
                return float(r.get("quote_volume") or 0), r
        elif venue == "mexc":
            d = fetch_json("https://api.mexc.com/api/v3/ticker/24hr", {"symbol":f"{sym}USDT"})
            time.sleep(0.3)
            if isinstance(d, dict) and d.get("quoteVolume"):
                return float(d["quoteVolume"]), d
        elif venue == "okx":
            d = fetch_json("https://www.okx.com/api/v5/market/ticker", {"instId":f"{sym}-USDT"})
            time.sleep(0.3)
            if str(d.get("code"))=="0" and d.get("data"):
                r = d["data"][0]
                return float(r.get("volCcy24h") or 0), r
        elif venue == "kucoin":
            d = fetch_json("https://api.kucoin.com/api/v1/market/stats", {"symbol":f"{sym}-USDT"})
            time.sleep(0.3)
            if str(d.get("code"))=="200000" and d.get("data"):
                return float(d["data"].get("volValue") or 0), d["data"]
    except: pass
    return 0, None

vol_by_venue = {}
for v_name in ["bybit","gate","kucoin","mexc","okx"]:
    if venues.get(v_name):
        vol, raw = venue_vol_24h(v_name, SYM)
        vol_by_venue[v_name] = vol
        print(f"  {v_name}: 24h vol_usd = ${vol:,.0f}")

if vol_by_venue:
    winner = max(vol_by_venue, key=vol_by_venue.get)
    print(f"\n  → VENUE LỚN NHẤT: **{winner}** with 24h vol ${vol_by_venue[winner]:,.0f}")
else:
    winner = None
    print(f"\n  → NO SPOT VENUE VOL AVAILABLE")

# Price-band check ±20% vs perp
if winner and perp:
    perp_last = table[-1]["c"] if table and not table[-1].get("_miss") else None
    # get winner price
    def get_price(v, sym):
        try:
            if v == "bybit":
                d = fetch_json("https://api.bybit.com/v5/market/tickers", {"category":"spot","symbol":f"{sym}USDT"})
                if d.get("retCode")==0 and d["result"]["list"]:
                    return float(d["result"]["list"][0].get("lastPrice") or 0)
            elif v == "gate":
                d = fetch_json(f"https://api.gateio.ws/api/v4/spot/tickers", {"currency_pair":f"{sym}_USDT"})
                if isinstance(d, list) and d:
                    return float(d[0].get("last") or 0)
            elif v == "mexc":
                d = fetch_json("https://api.mexc.com/api/v3/ticker/price", {"symbol":f"{sym}USDT"})
                if isinstance(d, dict) and d.get("price"):
                    return float(d["price"])
            elif v == "okx":
                d = fetch_json("https://www.okx.com/api/v5/market/ticker", {"instId":f"{sym}-USDT"})
                if str(d.get("code"))=="0" and d.get("data"):
                    return float(d["data"][0].get("last") or 0)
            elif v == "kucoin":
                d = fetch_json("https://api.kucoin.com/api/v1/market/orderbook/level1", {"symbol":f"{sym}-USDT"})
                if str(d.get("code"))=="200000" and d.get("data"):
                    return float(d["data"].get("price") or 0)
        except: pass
        return 0
    winner_px = get_price(winner, SYM)
    time.sleep(0.3)
    if perp_last and winner_px:
        dev = abs(winner_px - perp_last) / perp_last * 100
        print(f"\n  PRICE-BAND CHECK vs perp: perp={perp_last} · {winner}={winner_px} · deviation={dev:.2f}%")
        print(f"  Tolerance ±20%: {'✓ PASS' if dev < 20 else '❌ FAIL — DỪNG cột, báo ngay'}")

# ═══════════════════════════════════════════════════════════════════════
# P3(a) PHASE-TAG cross-check via VPS
# ═══════════════════════════════════════════════════════════════════════
hr("[P3(a) PHASE-TAG CSV grep PUMPBTC]")
import subprocess
try:
    r = subprocess.run(["ssh","root@5.223.67.21",
                        "find /root/Data_back_test/whale_data -maxdepth 6 -iname 'phase_tag_daily*.csv' 2>/dev/null | head -5"],
                       capture_output=True, text=True, timeout=30)
    print(f"  phase_tag CSVs on VPS:")
    print(f"  {r.stdout}")
    if r.stdout.strip():
        latest = r.stdout.strip().split("\n")[0]
        r2 = subprocess.run(["ssh","root@5.223.67.21", f"grep -i PUMPBTC {latest} | tail -10"],
                            capture_output=True, text=True, timeout=30)
        print(f"  PUMPBTC rows in {latest}:")
        print(r2.stdout if r2.stdout else "  (0 rows — machine không chấm)")
except Exception as e:
    print(f"  VPS err: {e}")

# ═══════════════════════════════════════════════════════════════════════
# P3(d) watchlist_log + unhedge_registry grep
# ═══════════════════════════════════════════════════════════════════════
hr("[P3(d) watchlist_log + unhedge_registry grep PUMPBTC]")
try:
    r = subprocess.run(["ssh","root@5.223.67.21",
                        "grep -i PUMPBTC /root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv | tail -20"],
                       capture_output=True, text=True, timeout=30)
    print(f"  watchlist_log 2026-08 PUMPBTC rows:")
    if r.stdout:
        print(r.stdout)
    else:
        print("  (0 rows)")
except Exception as e:
    print(f"  VPS err: {e}")

# Local unhedge_registry
reg_csv = ROOT / "data" / "registry" / "unhedge_registry_fw139_20260820.csv"
if reg_csv.exists():
    print(f"\n  unhedge_registry_fw139_20260820.csv PUMPBTC rows:")
    with open(reg_csv, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if "PUMPBTC" in r.get("symbol","").upper()]
    if rows:
        for r in rows:
            print(f"    {r}")
    else:
        print(f"    (0 rows in registry)")

# ═══════════════════════════════════════════════════════════════════════
# P3(b) oi_cycle_pos
# ═══════════════════════════════════════════════════════════════════════
hr("[P3(b) oi_cycle_pos]")
oi_vals = [r["oi"] for r in table if not r.get("_miss") and r.get("oi")]
if oi_vals:
    mn, mx = min(oi_vals), max(oi_vals)
    cur_oi = table[-1]["oi"] if table and not table[-1].get("_miss") else None
    if cur_oi and mx > mn:
        cyc = (cur_oi - mn)/(mx - mn)
        print(f"  OI 30d: min=${mn:,.0f} max=${mx:,.0f} · current=${cur_oi:,.0f} · cycle_pos={cyc:.4f}")

# ═══════════════════════════════════════════════════════════════════════
# P3(f) STATIC-SEAT check
# ═══════════════════════════════════════════════════════════════════════
hr("[P3(f) STATIC-SEAT check (L-53 calib)]")
pos_vals = [r["pos_r"] for r in table[-14:] if not r.get("_miss") and r.get("pos_r")]
oi_vals14 = [r["oi"] for r in table[-14:] if not r.get("_miss") and r.get("oi")]
pin_days = sum(1 for r in table[-14:] if r.get("pin"))
if pos_vals:
    avg14 = sum(pos_vals)/len(pos_vals)
    mn14 = min(pos_vals)
    print(f"  avg14(pos_r) = {avg14:.3f} · min14(pos_r) = {mn14:.3f}")
    print(f"  Criteria: pos_r ≥ 2.5-3 bền ≥14d · OI ≤ $5M · funding pin ·  kho lớn")
    print(f"    pos_r ≥ 2.5 bền: {'✓' if mn14 >= 2.5 else '✗ (min ' + str(mn14) + ')'}")
    if oi_vals14:
        avg_oi = sum(oi_vals14)/len(oi_vals14)
        print(f"    avg14(OI) = ${avg_oi:,.0f} · {'✓ (≤$5M)' if avg_oi <= 5e6 else '✗ (>$5M)'}")
    print(f"    pin days last14 = {pin_days}/14 · {'✓' if pin_days >= 10 else '✗'}")

# ═══════════════════════════════════════════════════════════════════════
# Save scratch
# ═══════════════════════════════════════════════════════════════════════
hr("[SAVE scratch]")
def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

write_csv(SCRATCH / "pumpbtc_perp_20260820.csv",
          [{"date": d, **v} for d, v in sorted(perp.items())],
          ["date","o","h","l","c","vol_quote_usd","taker_buy_pct"])
print(f"  Written: pumpbtc_perp_20260820.csv ({len(perp)} rows)")

print("\n[DONE probe]")

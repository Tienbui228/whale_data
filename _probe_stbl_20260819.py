"""_probe_stbl_20260819.py — STBL identity + full readout probe.
S0 IDENTITY (L-51 4-step, contract UNVERIFIED tag if operator missing)
S1 PERP full + LSR + funding + taker
S2 venue sweep (Bybit/OKX/Gate + api/v3 spot + Alpha bapi + deposit/withdraw flags)
S3 4 answers
S4 request operator on-chain
Read-only. Nến đóng L-21: D-1 = 2026-08-18. Window 60d cuối trước D-1.
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
from statistics import median

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
EXPORT   = ROOT / "data" / "export"

SYM     = "STBL"
TICKER  = "STBLUSDT"
END     = "2026-08-18"
# start = min(listing, END-60d)
END_DT  = _date.fromisoformat(END)
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

def hr(t): print("\n" + "="*70 + f"\n{t}\n" + "="*70)

# ═══════════════════════════════════════════════════════════════════════
# S0 — IDENTITY (Step-0 L-51 discipline)
# ═══════════════════════════════════════════════════════════════════════
hr("[S0.① PERP fapi exchangeInfo]")
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
time.sleep(0.3)
perp_meta = None
if isinstance(d, dict):
    perp_meta = next((s for s in d.get("symbols",[]) if s.get("symbol")==TICKER), None)
if perp_meta:
    onboard_ms = perp_meta.get("onboardDate")
    onboard_d  = ms_to_date(onboard_ms) if onboard_ms else "?"
    print(f"  PERP STBLUSDT: status={perp_meta.get('status')} onboardDate={onboard_ms} ({onboard_d})")
    print(f"    baseAsset={perp_meta.get('baseAsset')} quoteAsset={perp_meta.get('quoteAsset')}")
    tick = next((f.get('tickSize') for f in perp_meta.get('filters',[]) if f.get('filterType')=='PRICE_FILTER'), '?')
    print(f"    tickSize={tick}")
    PERP_START = onboard_d if onboard_d > START_HINT else START_HINT
    print(f"    → window start: {PERP_START} (max of onboard or END-60d)")
else:
    print(f"  PERP STBLUSDT: NOT FOUND on fapi")
    print(f"  → abort S1 (no perp)")
    PERP_START = None

hr("[S0.② CONTRACT (operator feed required)]")
print("  Contract 0x + chain: UNVERIFIED (operator chưa relay).")
print("  → mọi mapping alpha/venue mang nhãn UNVERIFIED (symbol-string match KHÔNG dùng bài F1 GUA)")
print("  → CẦN OPERATOR: paste 0x + chain trong follow-up (BSC/ETH/SOL/…)")

hr("[S0.③ Alpha bapi map]")
# WARNING: symbol-string match is F1 vulnerability. We probe but tag UNVERIFIED.
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
time.sleep(0.3)
alpha_matches = []
if isinstance(d, dict) and "data" in d:
    for tok in (d.get("data") or []):
        if str(tok.get("symbol","")).upper() == "STBL":
            alpha_matches.append(tok)
if not alpha_matches:
    print(f"  Alpha bapi: 0 entry match symbol='STBL'")
    print(f"  → Alpha map: NOT FOUND (KHÔNG có ALPHA_id cho STBL trên bapi)")
else:
    for tok in alpha_matches:
        print(f"  alphaId={tok.get('alphaId')} name={tok.get('name')} "
              f"fullyDelisted={tok.get('fullyDelisted')} offline={tok.get('offline')} "
              f"chain={tok.get('chainName')} contract={tok.get('contractAddress')}")
    print(f"  ⚠ Symbol-string match — UNVERIFIED cho tới khi operator confirm contract khớp")

hr("[S0.④ VENUE SWEEP L-52 — Bybit/OKX/Gate/Binance-spot + deposit/withdraw flags]")

def bybit_instr(sym):
    d = fetch_json("https://api.bybit.com/v5/market/instruments-info",
                   {"category":"spot","symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        lst = d.get("result",{}).get("list",[])
        if lst:
            r = lst[0]
            return {"venue":"bybit", "status": r.get("status"), "innovation": r.get("innovation"),
                    "launchTime": r.get("launchTime"), "raw": r}
    return None

def okx_instr(sym):
    d = fetch_json("https://www.okx.com/api/v5/public/instruments",
                   {"instType":"SPOT","instId":f"{sym}-USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "0":
        lst = d.get("data",[])
        if lst:
            r = lst[0]
            return {"venue":"okx","status":r.get("state"),"listTime":r.get("listTime"),"raw":r}
    return None

def gate_instr(sym):
    d = fetch_json(f"https://api.gateio.ws/api/v4/spot/currency_pairs/{sym}_USDT")
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("id"):
        return {"venue":"gate","status":d.get("trade_status"),"raw":d}
    return None

def kucoin_instr(sym):
    d = fetch_json(f"https://api.kucoin.com/api/v1/symbols/{sym}-USDT")
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "200000" and d.get("data"):
        r = d.get("data")
        return {"venue":"kucoin","status":"enabled" if r.get("enableTrading") else "disabled","raw":r}
    return None

def mexc_instr(sym):
    d = fetch_json("https://api.mexc.com/api/v3/exchangeInfo", {"symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("symbols"):
        r = d["symbols"][0]
        return {"venue":"mexc","status":r.get("status"),"raw":r}
    return None

def bitget_instr(sym):
    d = fetch_json("https://api.bitget.com/api/v2/spot/public/symbols",
                   {"symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "00000":
        lst = d.get("data",[])
        if lst:
            r = lst[0]
            return {"venue":"bitget","status":r.get("status"),"raw":r}
    return None

def bnc_spot_instr(sym):
    # api.binance.com blocked from local — will note ATTEMPT and rely on VPS follow-up
    d = fetch_json("https://api.binance.com/api/v3/exchangeInfo", {})
    time.sleep(0.3)
    if isinstance(d, dict) and "symbols" in d:
        matches = [s for s in d["symbols"] if s.get("baseAsset")==sym]
        if matches:
            r = matches[0]
            return {"venue":"binance_spot","status":r.get("status"),"raw":r}
        return {"venue":"binance_spot","status":"NOT_FOUND","raw":None}
    return {"venue":"binance_spot","status":f"ERR:{d.get('_error','?')}","raw":None}

venues = {}
for name, fn in [("binance_spot",bnc_spot_instr),("bybit",bybit_instr),
                 ("okx",okx_instr),("gate",gate_instr),
                 ("kucoin",kucoin_instr),("mexc",mexc_instr),("bitget",bitget_instr)]:
    print(f"\n  Trying: {name}")
    r = fn(SYM)
    venues[name] = r
    if r:
        print(f"    ✓ status={r.get('status')} · rest keys: {list(r.get('raw',{}).keys())[:10] if r.get('raw') else '-'}")
    else:
        print(f"    ✗ NOT FOUND / no pair")

# Deposit/withdraw flags — via capital/config/getall (requires auth) OR public status?
# Public endpoint: /sapi/v1/capital/config/getall requires auth.
# Fallback: check what each venue exposes public: status field in instruments-info might reflect trading only.
print(f"\n  DEPOSIT/WITHDRAW FLAGS — publicly available via:")
print(f"    - Bybit: /v5/asset/coin/query-info (public? — try)")
print(f"    - MEXC:  /api/v3/capital/config/getall (requires SIGNED)")
print(f"    - Gate:  /wallet/currency_chains?currency=X (public)")

# Try Gate withdrawStatus (public)
d = fetch_json("https://api.gateio.ws/api/v4/wallet/currency_chains", {"currency":SYM})
time.sleep(0.3)
if isinstance(d, list) and d:
    print(f"\n  Gate wallet/currency_chains {SYM}:")
    for chain_info in d:
        print(f"    chain={chain_info.get('chain')} name={chain_info.get('name_cn')} "
              f"withdraw_disabled={chain_info.get('is_withdraw_disabled')} "
              f"deposit_disabled={chain_info.get('is_deposit_disabled')}")
elif isinstance(d, dict) and d.get("_error"):
    print(f"  Gate chains {SYM}: {d['_error']}")

# ═══════════════════════════════════════════════════════════════════════
# S1 — PERP FULL (klines/funding/OI/LSR/taker)
# ═══════════════════════════════════════════════════════════════════════
if not perp_meta:
    print("\n[S1 aborted — no perp]")
    sys.exit(0)

hr(f"[S1 PERP FULL {PERP_START} → {END}]")
s_ms = to_ms(PERP_START); e_ms = to_ms(END) + 86400000 - 1

d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval": "1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 100})
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

# Funding paginate
fund_all = []; cur = s_ms
while cur <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": TICKER, "startTime": cur, "endTime": e_ms, "limit": 1000})
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
print(f"  funding days: {len(fund_by_d)}, entries: {sum(len(v) for v in fund_by_d.values())}")

# OI 30d
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period": "1d", "limit": 30})
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
print(f"  OI: {len(oi_by_d)} days")

# LSR: freshwatch store first, fallback fapi
lsr_fw = {}
for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = None
            try: pr = float(row.get("lsr_pos_r") or 0)
            except: pass
            if not d_str or not pr: continue
            lsr_fw[d_str] = {
                "pos_r": pr,
                "acc_r": float(row.get("lsr_acc_r") or 0) or None,
                "gLSR":  float(row.get("lsr_global_r") or 0) or None,
                "taker_lsr": float(row.get("taker_ratio") or 0) or None,
                "src": "freshwatch_store",
            }
print(f"  freshwatch LSR STBL: {len(lsr_fw)} days" + (f", range={min(lsr_fw)}→{max(lsr_fw)}" if lsr_fw else ""))

# fallback fapi LSR
def fetch_ep(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol": TICKER, "period":"1d", "limit": 30})
    time.sleep(0.3)
    by_d = {}
    for it in d if isinstance(d, list) else []:
        ts = int(it["timestamp"])
        by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d
lsr_top_pos = fetch_ep("topLongShortPositionRatio")
lsr_top_acc = fetch_ep("topLongShortAccountRatio")
lsr_glo     = fetch_ep("globalLongShortAccountRatio")
print(f"  fapi topPos {len(lsr_top_pos)}d, topAcc {len(lsr_top_acc)}d, global {len(lsr_glo)}d")

# ═══════════════════════════════════════════════════════════════════════
# S2 — CHÂN HÀNG (fetch klines from each venue found)
# ═══════════════════════════════════════════════════════════════════════
hr("[S2 CHÂN HÀNG — venue klines fetch + identity-check L-51 4-step]")

def bybit_klines(sym, s_ms, e_ms):
    d = fetch_json("https://api.bybit.com/v5/market/kline",
                   {"category":"spot","symbol":f"{sym}USDT","interval":"D",
                    "start":s_ms,"end":e_ms,"limit":200})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        return d.get("result",{}).get("list",[])
    return None

def gate_klines(sym, s_ms, e_ms):
    d = fetch_json("https://api.gateio.ws/api/v4/spot/candlesticks",
                   {"currency_pair":f"{sym}_USDT","interval":"1d",
                    "from": s_ms//1000, "to": e_ms//1000, "limit": 100})
    time.sleep(0.3)
    if isinstance(d, list): return d
    return None

venue_data = {}
if venues.get("bybit"):
    print("  → bybit klines fetch (30d)")
    s2_ms = to_ms((END_DT - timedelta(days=30)).isoformat())
    e2_ms = to_ms(END) + 86400000 - 1
    rows = bybit_klines(SYM, s2_ms, e2_ms)
    if rows:
        # [startTime, o, h, l, c, volume, turnover]
        by_d = {}
        for r in rows:
            ts = int(r[0]); d_str = ms_to_date(ts)
            by_d[d_str] = {
                "o": float(r[1]), "c": float(r[4]),
                "base_vol": float(r[5]), "turnover_usd": float(r[6]),
            }
        venue_data["bybit"] = by_d
        print(f"    bybit: {len(by_d)} days, sample last: {list(sorted(by_d.items()))[-1] if by_d else 'none'}")
        # identity check 3 sample: bit-equal
        sample = sorted(by_d.keys())[:3]
        for s in sample:
            r = by_d[s]
            bv = r["base_vol"]; tv = r["turnover_usd"]
            print(f"    identity {s}: bv={bv} tv={tv} bit-eq={bv==tv} implied={tv/bv if bv else '-'} c={r['c']}")

if venues.get("gate"):
    print("\n  → gate klines fetch (30d)")
    s2_ms = to_ms((END_DT - timedelta(days=30)).isoformat())
    e2_ms = to_ms(END) + 86400000 - 1
    rows = gate_klines(SYM, s2_ms, e2_ms)
    if rows:
        # Gate klines schema: [timestamp, volume_usd, close, high, low, open, base_vol, is_closed]
        # Actually Gate returns: [t, v, c, h, l, o, a, b] where v=quote_vol
        by_d = {}
        for r in rows:
            ts = int(r[0]) * 1000
            d_str = ms_to_date(ts)
            by_d[d_str] = {
                "o": float(r[5]), "c": float(r[2]),
                "vol_quote_usd": float(r[1]),
                "base_vol": float(r[6]) if len(r) > 6 else None,
            }
        venue_data["gate"] = by_d
        print(f"    gate: {len(by_d)} days, sample last: {list(sorted(by_d.items()))[-1] if by_d else 'none'}")
        sample = sorted(by_d.keys())[:3]
        for s in sample:
            r = by_d[s]
            print(f"    identity {s}: vol_q={r['vol_quote_usd']} base_vol={r.get('base_vol')} c={r['c']}")

# ═══════════════════════════════════════════════════════════════════════
# S3 — build per-day table (last 30d for readout) + baseline
# ═══════════════════════════════════════════════════════════════════════
hr("[S3 PER-DAY TABLE + baseline]")

# focus last 30d for readout
start_30d = (END_DT - timedelta(days=29)).isoformat()
days = []
cur = _date.fromisoformat(start_30d)
while cur <= END_DT:
    days.append(cur.isoformat()); cur += timedelta(days=1)

table = []
prev_c = None
for d_str in days:
    p = perp.get(d_str, {})
    if not p:
        table.append({"date": d_str, "_missing": True})
        continue
    frs = [x["fr"] for x in fund_by_d.get(d_str, [])]
    fn = len(frs)
    f_avg = round(sum(frs)/fn, 8) if fn else None
    pin_day = f_avg is not None and 4e-5 <= f_avg <= 6e-5
    oi = oi_by_d.get(d_str, {})
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r, acc_r, gl, src = fw["pos_r"], fw["acc_r"], fw["gLSR"], "freshwatch_store"
    else:
        pos_r = lsr_top_pos.get(d_str); acc_r = lsr_top_acc.get(d_str); gl = lsr_glo.get(d_str)
        src = "fapi_LSR_30d"
    c = p["c"]
    ret_1d = round((c - prev_c)/prev_c*100, 4) if (c and prev_c) else None
    prev_c = c if c else prev_c
    div_raw = round(pos_r/acc_r, 4) if (pos_r and acc_r) else None
    table.append({
        "date": d_str, "c": c, "ret_1d": ret_1d, "vol": p.get("vol_quote_usd"),
        "oi_usd": oi.get("oi_usd"),
        "f_avg": f_avg, "fn": fn, "pin_day": pin_day,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl,
        "div_raw": div_raw, "taker": p.get("taker_buy_pct"),
        "src_lsr": src,
    })

# div_avg3
for i, r in enumerate(table):
    if i < 2 or r.get("_missing"): continue
    p3 = [table[j].get("pos_r") for j in range(i-2,i+1) if table[j].get("pos_r")]
    a3 = [table[j].get("acc_r") for j in range(i-2,i+1) if table[j].get("acc_r")]
    if len(p3)==3 and len(a3)==3:
        aa = sum(a3)/3
        r["div_avg3"] = round((sum(p3)/3)/aa, 4) if aa else None

print(f"\n  {'date':<11} {'c':>9} {'ret%':>6} {'vol':>10} {'oi':>10} {'f_avg':>10} {'fn':>3} {'pin':>4} "
      f"{'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'div':>6} {'div3':>6} {'tk%':>6} {'src':>18}")
def fmt(v, w, prec=2): return f"{v:>{w}.{prec}f}" if v is not None else " "*w
for r in table:
    if r.get("_missing"):
        print(f"  {r['date']:<11}  (missing perp)")
        continue
    print(f"  {r['date']:<11} {fmt(r['c'],9,6)} {fmt(r['ret_1d'],6,2)} "
          f"{fmt(r['vol'],10,0)} {fmt(r['oi_usd'],10,0)} {fmt(r['f_avg'],10,6)} "
          f"{str(r['fn'] or ''):>3} {str(r['pin_day']):>4} "
          f"{fmt(r['pos_r'],6,3)} {fmt(r['acc_r'],6,3)} {fmt(r['gLSR'],6,3)} "
          f"{fmt(r['div_raw'],6,3)} {fmt(r.get('div_avg3'),6,3)} {fmt(r['taker'],6,2)} "
          f"{str(r['src_lsr']):>18}")

# oi_cycle_pos (min/max 30d)
oi_vals = [r["oi_usd"] for r in table if not r.get("_missing") and r["oi_usd"]]
if oi_vals:
    mn, mx = min(oi_vals), max(oi_vals)
    cur_oi = table[-1]["oi_usd"] if table and not table[-1].get("_missing") else None
    cyc = (cur_oi - mn)/(mx - mn) if (cur_oi and mx > mn) else None
    print(f"\n  OI 30d: min=${mn:,.0f} max=${mx:,.0f} · current=${cur_oi:,.0f} · cycle_pos={cyc:.4f}" if cyc is not None else "")

# baseline nền T7 spot per venue (using 20-31/07 if avail else earlier 12d window)
nen_days = [d for d in days if "2026-07-20" <= d <= "2026-08-01"]
for v, by_d in venue_data.items():
    vols = []
    for d in nen_days:
        r = by_d.get(d)
        if r:
            v_val = r.get("turnover_usd") or r.get("vol_quote_usd")
            if v_val: vols.append(v_val)
    if vols:
        print(f"\n  Nền T7 {v} (Jul20-Aug01): n={len(vols)} median=${median(vols):,.0f} "
              f"range=${min(vols):,.0f}..${max(vols):,.0f}")

# ═══════════════════════════════════════════════════════════════════════
# SAVE scratch data
# ═══════════════════════════════════════════════════════════════════════
hr("[SAVE scratch]")
csv_path = SCRATCH / "stbl_perp_60d_20260819.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","vol_quote_usd","taker_buy_pct"])
    w.writeheader()
    for d_str in sorted(perp): w.writerow({"date":d_str, **perp[d_str]})
print(f"  Written: {csv_path.name} ({len(perp)} rows)")

for v, by_d in venue_data.items():
    p = SCRATCH / f"stbl_{v}_spot_20260819.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        keys = list(by_d[list(by_d.keys())[0]].keys()) if by_d else []
        w = csv.DictWriter(f, fieldnames=["date"] + keys)
        w.writeheader()
        for d_str in sorted(by_d): w.writerow({"date": d_str, **by_d[d_str]})
    print(f"  Written: {p.name} ({len(by_d)} rows)")

print("\n[DONE probe]")

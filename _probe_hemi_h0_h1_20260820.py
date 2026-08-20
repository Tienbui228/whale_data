"""_probe_hemi_h0_h1_20260820.py — HEMI H0 identity + H1 perp full 01/07-19/08.
Discipline: L-51 4-step, L-52 venue sweep, price-band check bài SUPERFORTUNE, L-48 mirror check.
Read-only. Save scratch CSVs for downstream tasks.
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
from statistics import median

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
EXPORT   = ROOT / "data" / "export"

SYM     = "HEMI"
TICKER  = "HEMIUSDT"
START   = "2026-07-01"
END     = "2026-08-19"  # D-1 nến đóng

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
# H0 — IDENTITY
# ═══════════════════════════════════════════════════════════════════════
hr("[H0.① PERP fapi exchangeInfo]")
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
time.sleep(0.3)
perp_meta = None
if isinstance(d, dict):
    perp_meta = next((s for s in d.get("symbols",[]) if s.get("symbol")==TICKER), None)
if perp_meta:
    onboard_ms = perp_meta.get("onboardDate")
    onboard_d  = ms_to_date(onboard_ms) if onboard_ms else "?"
    print(f"  PERP HEMIUSDT: status={perp_meta.get('status')} onboard={onboard_ms} ({onboard_d})")
    tick = next((f.get('tickSize') for f in perp_meta.get('filters',[]) if f.get('filterType')=='PRICE_FILTER'), '?')
    print(f"    tickSize={tick} baseAsset={perp_meta.get('baseAsset')} quote={perp_meta.get('quoteAsset')}")
else:
    print("  PERP HEMIUSDT: NOT FOUND — abort")
    sys.exit(1)

hr("[H0.② CONTRACT — operator feed required]")
print("  Contract 0x + chain: UNVERIFIED (chờ operator relay từ tracker)")
print("  → Alpha map + venue price-band verify PHẢI dùng contract, KHÔNG dùng symbol-string (bài F1 GUA)")

hr("[H0.③ Alpha bapi (symbol-match, ⚠ UNVERIFIED)]")
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
time.sleep(0.3)
alpha_hits = []
if isinstance(d, dict) and "data" in d:
    for tok in d.get("data") or []:
        if str(tok.get("symbol","")).upper() == "HEMI":
            alpha_hits.append(tok)
if not alpha_hits:
    print("  Alpha bapi: 0 entry match symbol='HEMI'")
else:
    for tok in alpha_hits:
        print(f"  alphaId={tok.get('alphaId')} name={tok.get('name')} "
              f"fullyDelisted={tok.get('fullyDelisted')} offline={tok.get('offline')} "
              f"chain={tok.get('chainName')} contract={tok.get('contractAddress')}")
    print("  ⚠ SYMBOL-STRING match — UNVERIFIED cho tới khi operator confirm contract khớp (bài F1 GUA)")

hr("[H0.④ VENUE SWEEP L-52 — 7 venues + van flags]")

def venue_probe(venue_name, url, parse_fn):
    d = fetch_json(url[0], url[1])
    time.sleep(0.3)
    return parse_fn(d)

def bybit_pf(d):
    if isinstance(d, dict) and d.get("retCode") == 0:
        lst = d.get("result",{}).get("list",[])
        if lst: return lst[0]
    return None
def okx_pf(d):
    if isinstance(d, dict) and str(d.get("code")) == "0":
        lst = d.get("data",[])
        if lst: return lst[0]
    return None
def gate_pf(d):
    if isinstance(d, dict) and d.get("id"): return d
    return None
def kucoin_pf(d):
    if isinstance(d, dict) and str(d.get("code")) == "200000" and d.get("data"):
        return d.get("data")
    return None
def mexc_pf(d):
    if isinstance(d, dict) and d.get("symbols"):
        return d["symbols"][0]
    return None
def bitget_pf(d):
    if isinstance(d, dict) and str(d.get("code")) == "00000":
        lst = d.get("data",[])
        if lst: return lst[0]
    return None
def bnc_pf(d):
    if isinstance(d, dict) and "symbols" in d:
        m = [s for s in d["symbols"] if s.get("baseAsset")=="HEMI"]
        if m: return m[0]
        return {"status":"NOT_FOUND"}
    return None

venues = {}
probes = [
    ("binance_spot", ("https://api.binance.com/api/v3/exchangeInfo", {}), bnc_pf),
    ("bybit",   ("https://api.bybit.com/v5/market/instruments-info", {"category":"spot","symbol":f"{SYM}USDT"}), bybit_pf),
    ("okx",     ("https://www.okx.com/api/v5/public/instruments", {"instType":"SPOT","instId":f"{SYM}-USDT"}), okx_pf),
    ("gate",    (f"https://api.gateio.ws/api/v4/spot/currency_pairs/{SYM}_USDT", {}), gate_pf),
    ("kucoin",  (f"https://api.kucoin.com/api/v1/symbols/{SYM}-USDT", {}), kucoin_pf),
    ("mexc",    ("https://api.mexc.com/api/v3/exchangeInfo", {"symbol":f"{SYM}USDT"}), mexc_pf),
    ("bitget",  ("https://api.bitget.com/api/v2/spot/public/symbols", {"symbol":f"{SYM}USDT"}), bitget_pf),
]
for name, url, fn in probes:
    r = venue_probe(name, url, fn)
    venues[name] = r
    print(f"\n  {name}: {'FOUND' if r and r.get('status') != 'NOT_FOUND' else 'NOT_FOUND'}")
    if r and r.get('status') != 'NOT_FOUND':
        keys_show = ["symbol","baseCoin","baseAsset","quoteCoin","quoteAsset","status","state","trade_status","enableTrading"]
        rel = {k: r.get(k) for k in keys_show if k in r}
        print(f"    {rel}")

# Gate deposit/withdraw flags
d = fetch_json("https://api.gateio.ws/api/v4/wallet/currency_chains", {"currency": SYM})
time.sleep(0.3)
if isinstance(d, list) and d:
    print(f"\n  Gate wallet/currency_chains {SYM}:")
    for ch in d:
        print(f"    chain={ch.get('chain')} name={ch.get('name_cn')} "
              f"deposit_disabled={ch.get('is_deposit_disabled')} "
              f"withdraw_disabled={ch.get('is_withdraw_disabled')}")

# ═══════════════════════════════════════════════════════════════════════
# H1 — PERP FULL 01/07-19/08
# ═══════════════════════════════════════════════════════════════════════
hr(f"[H1 PERP FULL {START} → {END}]")

s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1

# klines
d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval":"1d", "startTime": s_ms, "endTime": e_ms, "limit": 100})
time.sleep(0.3)
perp = {}
for k in d if isinstance(d, list) else []:
    d_str = ms_to_date(int(k[0]))
    if d_str < START or d_str > END: continue
    vol_q = float(k[7]); taker_q = float(k[10])
    perp[d_str] = {
        "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
        "vol_quote_usd": round(vol_q, 2),
        "taker_buy_pct": round(taker_q/vol_q*100, 4) if vol_q > 0 else None,
    }
print(f"  perp days: {len(perp)}, range={min(perp)}→{max(perp)}")

# funding paginate
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
    if START <= d_str <= END:
        fund_by_d.setdefault(d_str, []).append({"ts": ts, "fr": float(it["fundingRate"])})
print(f"  funding days: {len(fund_by_d)}, entries: {sum(len(v) for v in fund_by_d.values())}")

# OI (30d limit)
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period":"1d", "limit": 30})
time.sleep(0.3)
oi_by_d = {}
seen = set()
for it in d if isinstance(d, list) else []:
    ts = int(it["timestamp"]); d_str = ms_to_date(ts)
    key = (d_str, str(ts))
    if key in seen: continue
    seen.add(key)
    oi_by_d[d_str] = {"oi_usd": float(it["sumOpenInterestValue"] or 0),
                      "oi_token": float(it["sumOpenInterest"] or 0)}
print(f"  OI: {len(oi_by_d)} days (30d limit, covers Jul21-Aug19)")

# LSR freshwatch (fw-139)
lsr_fw = {}
for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = safe_float(row.get("lsr_pos_r"))
            if not d_str or not pr: continue
            lsr_fw[d_str] = {
                "pos_r": pr,
                "acc_r": safe_float(row.get("lsr_acc_r")),
                "gLSR":  safe_float(row.get("lsr_global_r")),
                "taker_lsr": safe_float(row.get("taker_ratio")),
                "src": "freshwatch_store",
            }
print(f"  freshwatch LSR: {len(lsr_fw)} days" +
      (f", range={min(lsr_fw)}→{max(lsr_fw)}" if lsr_fw else ""))

# fapi 3 endpoint fallback
def fetch_ep(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol": TICKER, "period":"1d", "limit": 30})
    time.sleep(0.3)
    by_d = {}
    for it in d if isinstance(d, list) else []:
        ts = int(it["timestamp"]); by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d
lsr_top_pos = fetch_ep("topLongShortPositionRatio")
lsr_top_acc = fetch_ep("topLongShortAccountRatio")
lsr_glo     = fetch_ep("globalLongShortAccountRatio")

# Save scratch
def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

write_csv(SCRATCH / "hemi_perp_20260820.csv",
          [{"date": d, **v} for d, v in sorted(perp.items())],
          ["date","o","h","l","c","vol_quote_usd","taker_buy_pct"])
print(f"\n  Written: hemi_perp_20260820.csv ({len(perp)} rows)")

fund_flat = []
for d_str in sorted(fund_by_d):
    for e in fund_by_d[d_str]:
        fund_flat.append({"date": d_str, "time_ms": e["ts"], "fundingRate": e["fr"]})
write_csv(SCRATCH / "hemi_funding_20260820.csv", fund_flat, ["date","time_ms","fundingRate"])
print(f"  Written: hemi_funding_20260820.csv ({len(fund_flat)} entries)")

write_csv(SCRATCH / "hemi_oi_20260820.csv",
          [{"date": d, **v} for d, v in sorted(oi_by_d.items())],
          ["date","oi_usd","oi_token"])
print(f"  Written: hemi_oi_20260820.csv ({len(oi_by_d)} rows)")

write_csv(SCRATCH / "hemi_lsr_freshwatch_20260820.csv",
          [{"date": d, **v} for d, v in sorted(lsr_fw.items())],
          ["date","pos_r","acc_r","gLSR","taker_lsr","src"])
print(f"  Written: hemi_lsr_freshwatch_20260820.csv ({len(lsr_fw)} rows)")

# lsr fapi (combined)
lsr_fapi_combined = {}
for d in set(list(lsr_top_pos.keys()) + list(lsr_top_acc.keys()) + list(lsr_glo.keys())):
    lsr_fapi_combined[d] = {
        "pos_r": lsr_top_pos.get(d),
        "acc_r": lsr_top_acc.get(d),
        "gLSR":  lsr_glo.get(d),
    }
write_csv(SCRATCH / "hemi_lsr_fapi_20260820.csv",
          [{"date": d, **v} for d, v in sorted(lsr_fapi_combined.items())],
          ["date","pos_r","acc_r","gLSR"])
print(f"  Written: hemi_lsr_fapi_20260820.csv ({len(lsr_fapi_combined)} rows)")

# quick summary + taker scale check
taker_samples = [perp[d]["taker_buy_pct"] for d in perp if perp[d]["taker_buy_pct"] is not None]
mn, mx = min(taker_samples), max(taker_samples)
print(f"\n  TAKER SCALE: range {mn:.2f}-{mx:.2f} → {'percent' if mn > 1.0 else 'fraction OR mixed'} ✓")

# Print per-day table 30d cuối
print(f"\n  === PER-DAY TABLE Jul21→Aug19 (30 rows, LSR + PERP) ===")
print(f"  {'date':<11} {'c':>10} {'ret%':>7} {'vol':>10} {'oi':>10} {'f_avg':>10} {'fn':>3} "
      f"{'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'div':>6} {'tk%':>6} {'src':>18}")
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
days = []; cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)
prev_c = None
for d_str in days:
    p = perp.get(d_str)
    if not p: continue
    c = p["c"]
    frs = [x["fr"] for x in fund_by_d.get(d_str,[])]
    fn = len(frs); f_avg = round(sum(frs)/fn, 8) if fn else None
    oi = oi_by_d.get(d_str, {}).get("oi_usd")
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r, acc_r, gl, src = fw["pos_r"], fw["acc_r"], fw["gLSR"], "fw"
    else:
        pos_r = lsr_top_pos.get(d_str); acc_r = lsr_top_acc.get(d_str); gl = lsr_glo.get(d_str)
        src = "fapi" if pos_r else "-"
    ret_1d = round((c-prev_c)/prev_c*100, 2) if (c and prev_c) else None
    prev_c = c if c else prev_c
    div = round(pos_r/acc_r, 3) if (pos_r and acc_r) else None
    def fmt(v, w, prec=2): return f"{v:>{w}.{prec}f}" if v is not None else " "*w
    print(f"  {d_str:<11} {fmt(c,10,5)} {fmt(ret_1d,7,2)} {fmt(p['vol_quote_usd'],10,0)} "
          f"{fmt(oi,10,0)} {fmt(f_avg,10,6)} {str(fn or ''):>3} "
          f"{fmt(pos_r,6,3)} {fmt(acc_r,6,3)} {fmt(gl,6,3)} {fmt(div,6,3)} "
          f"{fmt(p['taker_buy_pct'],6,2)} {src:>18}")

print("\n[DONE H0+H1]")

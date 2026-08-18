"""_task_clo_b1_fetch_20260818.py
B1: Fetch fapi perp/funding/OI Aug04-Aug17 for CLOUSDT.
Fetch LSR canonical schema (Fix B from án E).
Also probe: is CLO on api/v3 spot? on Alpha?
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

SYM     = "CLO"
TICKER  = "CLOUSDT"
NEW_TAG = "20260818"

# window for append: Aug04-Aug17 (14 days)
START = "2026-08-04"
END   = "2026-08-17"

def fetch_json(url, params=None, timeout=20):
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

# ── SPOT / ALPHA verify ─────────────────────────────────────────────────
print("="*70)
print("[SPOT/ALPHA verify — CLO listing structure]")
print("="*70)

# NOTE: api.binance.com may be geo-blocked from Windows — use bapi (works local)
# Try bapi alpha token list first
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
time.sleep(0.3)
alpha_meta = None
if isinstance(d, dict) and "data" in d:
    for tok in (d.get("data") or []):
        if str(tok.get("symbol","")).upper() == "CLO":
            alpha_meta = tok; break
if alpha_meta:
    print(f"  Alpha entry FOUND: alphaId={alpha_meta.get('alphaId')} name={alpha_meta.get('name')} "
          f"fullyDelisted={alpha_meta.get('fullyDelisted')} offline={alpha_meta.get('offline')}")
else:
    print(f"  Alpha entry: NOT in list (CLO not an Alpha token)")

# fapi symbols (perp) — check CLOUSDT
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo", {})
time.sleep(0.3)
if isinstance(d, dict) and "symbols" in d:
    clo_perp = [s for s in d["symbols"] if s.get("symbol")=="CLOUSDT"]
    if clo_perp:
        s = clo_perp[0]
        print(f"  PERP CLOUSDT: status={s.get('status')} onboardDate={s.get('onboardDate')}")
    else:
        print(f"  PERP CLOUSDT: NOT FOUND")

# ── perp klines Aug04-Aug17 ─────────────────────────────────────────────
print("\n" + "="*70)
print(f"[PERP klines {START} → {END}]")
print("="*70)
s_ms = to_ms(START)
e_ms = to_ms(END) + 86400000 - 1
d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval": "1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 30})
time.sleep(0.3)
perp_rows = []
if isinstance(d, list):
    for k in d:
        d_str = ms_to_date(int(k[0]))
        if d_str < START or d_str > END: continue
        vol_q = float(k[7])
        taker_q = float(k[10])
        taker_pct = round(taker_q/vol_q*100, 4) if vol_q > 0 else 50.0
        perp_rows.append({
            "date": d_str,
            "open":  float(k[1]),
            "high":  float(k[2]),
            "low":   float(k[3]),
            "close": float(k[4]),
            "vol_quote_usd": round(vol_q, 2),
            "taker_buy_pct": taker_pct,
            "taker_buy_vol": round(taker_q, 2),
        })
print(f"  perp rows fetched: {len(perp_rows)}")
for r in perp_rows:
    print(f"    {r['date']}: o={r['open']} c={r['close']} vol_usd={r['vol_quote_usd']:.0f} tk={r['taker_buy_pct']:.2f}%")

# ── funding Aug04-Aug17 ─────────────────────────────────────────────────
print("\n" + "="*70)
print(f"[FUNDING {START} → {END}]")
print("="*70)
# Binance funding history: paginate by startTime, max 1000 per call
fund_all = []
cur_start = s_ms
while cur_start <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": TICKER, "startTime": cur_start,
                    "endTime": e_ms, "limit": 1000})
    time.sleep(0.3)
    if not isinstance(d, list) or not d: break
    fund_all.extend(d)
    last_ts = int(d[-1].get("fundingTime", 0))
    if last_ts <= cur_start: break
    cur_start = last_ts + 1
    if last_ts >= e_ms: break

# unique + assign to date
fund_by_date = {}
for it in fund_all:
    ts = int(it.get("fundingTime", 0))
    d_str = ms_to_date(ts)
    if d_str < START or d_str > END: continue
    fund_by_date.setdefault(d_str, []).append({"time_ms": ts, "fr": float(it.get("fundingRate",0))})
print(f"  funding total entries: {sum(len(v) for v in fund_by_date.values())}, "
      f"days covered: {len(fund_by_date)}")
for d_str in sorted(fund_by_date):
    entries = fund_by_date[d_str]
    frs = [e["fr"] for e in entries]
    fn = len(entries)
    f_avg = round(sum(frs)/fn, 8)
    # interval detect
    if fn >= 2:
        tss = sorted(e["time_ms"] for e in entries)
        intervals = [(tss[i]-tss[i-1])/3600000 for i in range(1,len(tss))]
        med = sorted(intervals)[len(intervals)//2]
    else:
        med = None
    print(f"    {d_str}: fn={fn} f_avg={f_avg} f_min={min(frs)} f_max={max(frs)} interval_med={med}h")

# ── OI Aug04-Aug17 (last 30d limit — must fetch fresh) ──────────────────
print("\n" + "="*70)
print(f"[OI hist last 30d, filter {START}→{END}]")
print("="*70)
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period":"1d", "limit": 30})
time.sleep(0.3)
oi_rows = []
if isinstance(d, list):
    seen = set()
    for it in d:
        ts = int(it.get("timestamp", 0))
        d_str = ms_to_date(ts)
        key = (d_str, str(ts))
        if key in seen: continue
        seen.add(key)
        oi_rows.append({
            "date": d_str, "timestamp": str(ts),
            "oi_usd": float(it.get("sumOpenInterestValue", 0) or 0),
            "oi_token": float(it.get("sumOpenInterest", 0) or 0),
        })
oi_in_window = [r for r in oi_rows if START <= r["date"] <= END]
print(f"  OI raw: {len(oi_rows)}, in-window: {len(oi_in_window)}")
for r in oi_in_window:
    print(f"    {r['date']}: oi_usd={r['oi_usd']:.0f} oi_token={r['oi_token']:.0f}")

# ── LSR canonical schema (Fix B) ────────────────────────────────────────
print("\n" + "="*70)
print(f"[LSR canonical last 30d]")
print("="*70)
d = fetch_json("https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
               {"symbol": TICKER, "period":"1d", "limit": 30})
time.sleep(0.3)
lsr_rows = []
if isinstance(d, list):
    for it in d:
        ts = int(it.get("timestamp", 0))
        d_str = ms_to_date(ts)
        ratio = float(it.get("longShortRatio", 0) or 0)
        long_frac = float(it.get("longAccount", 0) or 0)
        short_frac= float(it.get("shortAccount", 0) or 0)
        lsr_rows.append({
            "date": d_str,
            "pos_r_raw":     "",
            "acc_r_raw":     round(ratio, 4),
            "glsr_raw":      round(ratio, 4),
            "taker_lsr_raw": "",
            "_src": "fapi_LSR_30d",
        })
print(f"  LSR rows: {len(lsr_rows)}, range: {lsr_rows[0]['date']}→{lsr_rows[-1]['date']}")

# ── INTRADAY 18/08 snapshot ─────────────────────────────────────────────
print("\n" + "="*70)
print(f"[INTRADAY 18/08 snapshot]")
print("="*70)
now_utc = datetime.now(timezone.utc)
print(f"  snapshot at: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

# fapi 24h ticker
d = fetch_json("https://fapi.binance.com/fapi/v1/ticker/24hr", {"symbol": TICKER})
time.sleep(0.3)
if isinstance(d, dict) and "lastPrice" in d:
    print(f"  24h ticker: last={d['lastPrice']} open24h={d['openPrice']} "
          f"chg%={d['priceChangePercent']} vol_quote={d['quoteVolume']}")
    intraday_price = d["lastPrice"]
    intraday_open  = d["openPrice"]
    intraday_chg   = d["priceChangePercent"]
    intraday_vol   = d["quoteVolume"]
else:
    print(f"  Ticker error: {d}")
    intraday_price = intraday_open = intraday_chg = intraday_vol = None

# current OI (single snapshot)
d = fetch_json("https://fapi.binance.com/fapi/v1/openInterest", {"symbol": TICKER})
time.sleep(0.3)
if isinstance(d, dict) and "openInterest" in d:
    oi_now_tok = float(d["openInterest"])
    px_now = float(intraday_price) if intraday_price else None
    oi_now_usd = oi_now_tok * px_now if px_now else None
    print(f"  OI now: token={oi_now_tok:.0f} px={px_now} usd={oi_now_usd:.0f}" if oi_now_usd else
          f"  OI now: token={oi_now_tok:.0f}")
else:
    print(f"  OI now error: {d}")

# funding recent
d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
               {"symbol": TICKER, "limit": 3})
time.sleep(0.3)
if isinstance(d, list) and d:
    print(f"  Recent funding entries:")
    for it in d:
        ts = int(it.get("fundingTime", 0))
        print(f"    {ms_to_date(ts)} @ {datetime.fromtimestamp(ts/1000,tz=timezone.utc).strftime('%H:%M UTC')}: "
              f"fr={it.get('fundingRate')}")

# ── WRITE scratch CSVs ─────────────────────────────────────────────────
def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

if perp_rows:
    write_csv(SCRATCH / f"clo_perp_aug04_17_{NEW_TAG}.csv", perp_rows,
              ["date","open","high","low","close","vol_quote_usd","taker_buy_pct","taker_buy_vol"])
    print(f"\n  Written: clo_perp_aug04_17_{NEW_TAG}.csv ({len(perp_rows)} rows)")

fund_flat = []
for d_str in sorted(fund_by_date):
    for e in fund_by_date[d_str]:
        fund_flat.append({"date": d_str, "time_ms": e["time_ms"], "fundingRate": e["fr"]})
if fund_flat:
    write_csv(SCRATCH / f"clo_funding_aug04_17_{NEW_TAG}.csv", fund_flat,
              ["date","time_ms","fundingRate"])
    print(f"  Written: clo_funding_aug04_17_{NEW_TAG}.csv ({len(fund_flat)} entries)")

if oi_rows:
    write_csv(SCRATCH / f"clo_oi_hist_{NEW_TAG}.csv", oi_rows,
              ["date","timestamp","oi_usd","oi_token"])
    print(f"  Written: clo_oi_hist_{NEW_TAG}.csv ({len(oi_rows)} rows)")

if lsr_rows:
    write_csv(SCRATCH / f"clo_lsr_raw_{NEW_TAG}.csv", lsr_rows,
              ["date","pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw","_src"])
    print(f"  Written: clo_lsr_raw_{NEW_TAG}.csv ({len(lsr_rows)} rows)")

print("\n[DONE B1 fetch]")

"""
_probe_on_2_collect_20260810.py
N-2: Klines full lifetime + funding — ONUSDT.
Onboard: 2025-10-24. Perp only (no spot pair). Alpha: ALPHA_444 (may not be BSC).
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"
SYM_LOWER = "on"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-2 COLLECT ONUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# Onboard: 2025-10-24 08:30 UTC
START_MS = 1761294600000
start_d = datetime.fromtimestamp(START_MS/1000, tz=timezone.utc).strftime("%Y-%m-%d")
log(f"  Start: {start_d} (onboard)")

# ── 1. Perp klines full lifetime ──────────────────────────────────────────────
log(f"\n=== 1. Perp klines 1d — full history from {start_d} ===")
all_klines = []
end_ms = None; page = 0
while True:
    url = f"{FAPI}/fapi/v1/klines?symbol={SYM}&interval=1d&limit=1500"
    url += f"&startTime={START_MS}" if page == 0 else f"&startTime={end_ms+1}"
    batch = fetch_json(url)
    if not batch: log(f"  batch {page}: error"); break
    all_klines.extend(batch)
    log(f"  batch {page}: {len(batch)} rows → total {len(all_klines)}")
    if len(batch) < 1500: break
    end_ms = int(batch[-1][0]); page += 1; time.sleep(0.2)

log(f"  Total: {len(all_klines)}")
if all_klines:
    t0 = datetime.fromtimestamp(int(all_klines[0][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    t1 = datetime.fromtimestamp(int(all_klines[-1][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {t0} → {t1}")
    log(f"  Last 5:")
    for k in all_klines[-5:]:
        ts = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        qv = float(k[7]); tb = float(k[9]); vol_b = float(k[5])
        tp = round(tb/vol_b*100, 2) if vol_b > 0 else 0
        log(f"    {ts}: o={k[1]} h={k[2]} l={k[3]} c={k[4]} vol_usd=${qv:,.0f} taker={tp:.1f}%")
    out_k = SCRATCH / f"{SYM_LOWER}_klines_{DATE_TAG}.csv"
    fields = ["open_time","open","high","low","close","volume","close_time","quote_vol",
              "trades","taker_buy_base","taker_buy_quote","ignore"]
    with open(out_k, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fields); w.writerows(all_klines)
    log(f"  Saved: {out_k.name} ({out_k.stat().st_size:,} bytes)")

    # Quick stats
    closes = [float(k[4]) for k in all_klines]
    highs  = [float(k[2]) for k in all_klines]
    lows   = [float(k[3]) for k in all_klines]
    vols   = [float(k[7]) for k in all_klines]
    ath = max(highs); atl = min(lows); last_c = closes[-1]
    ath_d = datetime.fromtimestamp(int(all_klines[highs.index(ath)][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"\n  ATH: ${ath:.6f} ({ath_d})")
    log(f"  ATL: ${atl:.6f}")
    log(f"  Last close: ${last_c:.6f}")
    log(f"  Drawdown from ATH: {(last_c-ath)/ath*100:.2f}%")
    log(f"  Recovery from ATL: {(last_c-atl)/atl*100:.2f}%")
    med_vol = sorted(vols)[len(vols)//2]
    log(f"  Median daily vol: ${med_vol:,.0f}")

    # EVENTS: |ret|>10% + vol≥8×med14
    log(f"\n  === KEY EVENTS (|ret|>10% or vol≥8×med14) ===")
    for i in range(1, len(all_klines)):
        d = datetime.fromtimestamp(int(all_klines[i][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        c_prev = float(all_klines[i-1][4]); c = float(all_klines[i][4])
        ret = (c - c_prev)/c_prev*100 if c_prev else 0
        qv = float(all_klines[i][7])
        # med14 at this point
        vol_window = [float(all_klines[j][7]) for j in range(max(0,i-14),i)]
        med14 = sorted(vol_window)[len(vol_window)//2] if vol_window else 0
        vol_vs_m = round(qv/med14, 2) if med14 > 0 else None
        if abs(ret) > 10 or (vol_vs_m and vol_vs_m >= 8):
            tb = float(all_klines[i][9]); vb = float(all_klines[i][5])
            tp = round(tb/vb*100, 1) if vb > 0 else 0
            log(f"    {d}: ret={ret:+.2f}%  vol=${qv:,.0f}  vol_vs_m={vol_vs_m}x  taker={tp}%")

# ── 2. Funding rate ───────────────────────────────────────────────────────────
log(f"\n=== 2. Funding rate history ===")
fund_all = []
url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={START_MS}"
batch = fetch_json(url)
if batch:
    fund_all.extend(batch)
    log(f"  Page 1: {len(batch)} rows")
    if len(batch) == 1000:
        last_t = int(batch[-1]["fundingTime"])
        batch2 = fetch_json(f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={last_t+1}")
        if batch2:
            fund_all.extend(batch2)
            log(f"  Page 2: {len(batch2)} rows")

if fund_all:
    t0f = datetime.fromtimestamp(int(fund_all[0]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    t1f = datetime.fromtimestamp(int(fund_all[-1]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {t0f} → {t1f}  Total: {len(fund_all)}")
    log(f"  Last 9 (3 days):")
    for r in fund_all[-9:]:
        ts = datetime.fromtimestamp(int(r["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        log(f"    {ts}: {float(r.get('fundingRate',0)):.6f}")
    out_f = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"
    with open(out_f, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","fundingTime","fundingRate","markPrice"])
        w.writeheader()
        for r in fund_all:
            w.writerow({k: r.get(k,"") for k in ["symbol","fundingTime","fundingRate","markPrice"]})
    log(f"  Saved: {out_f.name} ({out_f.stat().st_size:,} bytes, {len(fund_all)} rows)")

# ── 3. Alpha store check ──────────────────────────────────────────────────────
log(f"\n=== 3. Alpha store check (ALPHA_444) ===")
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
if alpha_store.exists():
    try:
        import pandas as pd
        cnt = 0
        for p in alpha_store.rglob("*.parquet"):
            try:
                df = pd.read_parquet(p, columns=["symbol"])
                c = (df["symbol"] == "ON").sum()
                if c > 0: cnt += c
            except: pass
        log(f"  Alpha 'ON' in local store: {cnt} rows")
    except Exception as e:
        log(f"  Alpha store check: {e}")
else:
    log(f"  Alpha store not found")

# ── 4. Ticker live ────────────────────────────────────────────────────────────
log(f"\n=== 4. Ticker live ===")
ticker = fetch_json(f"{FAPI}/fapi/v1/ticker/24hr?symbol={SYM}")
if ticker:
    log(f"  lastPrice: {ticker.get('lastPrice')}")
    log(f"  24h pct:   {float(ticker.get('priceChangePercent',0)):+.2f}%")
    log(f"  24h vol:   ${float(ticker.get('quoteVolume',0)):,.0f}")
    log(f"  24h high:  {ticker.get('highPrice')}  low: {ticker.get('lowPrice')}")
    log(f"  open24h:   {ticker.get('openPrice')}")

log(f"\n[N-2 DONE]")

"""
_probe_apr_2_collect_20260810.py
A-2: Collect klines (perp) + funding + spot check — APRUSDT.
APR = standard perp (NOT Alpha). taker from klines[9] valid.
LSR all 404 → no LSR CSVs for this symbol.
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-2 COLLECT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── 1. Perp klines — full history 1d ──────────────────────────────────────
log(f"\n=== 1. Perp klines 1d — full history ===")
# Onboard: 2025-10-23. startTime in ms
START_MS = int(datetime(2025, 10, 23, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
all_klines = []
end_ms = None
page = 0
while True:
    url = f"{FAPI}/fapi/v1/klines?symbol={SYM}&interval=1d&limit=1500"
    if page == 0:
        url += f"&startTime={START_MS}"
    else:
        url += f"&startTime={end_ms+1}"
    batch = fetch_json(url)
    if not batch:
        log(f"  batch {page}: error"); break
    all_klines.extend(batch)
    log(f"  batch {page}: {len(batch)} rows → total {len(all_klines)}")
    if len(batch) < 1500:
        break
    end_ms = int(batch[-1][0])
    page += 1
    time.sleep(0.2)

log(f"  Total klines: {len(all_klines)}")
if all_klines:
    t0 = datetime.fromtimestamp(int(all_klines[0][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    t1 = datetime.fromtimestamp(int(all_klines[-1][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {t0} → {t1}")
    log(f"  Last 3:")
    for k in all_klines[-3:]:
        ts = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        o,h,l,c,v = k[1],k[2],k[3],k[4],k[5]
        qv = float(k[7])  # quote vol
        tk_buy = float(k[9])  # taker buy base
        tk_pct = float(k[9])/float(k[5])*100 if float(k[5])>0 else 0
        log(f"  {ts}: o={o} h={h} l={l} c={c} vol_q=${qv:,.0f} taker={tk_pct:.1f}%")

    # Save CSV
    out1 = SCRATCH / f"apr_klines_{DATE_TAG}.csv"
    fields = ["open_time","open","high","low","close","volume","close_time","quote_vol",
              "trades","taker_buy_base","taker_buy_quote","ignore"]
    with open(out1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        w.writerows(all_klines)
    log(f"  Saved: {out1.name} ({out1.stat().st_size:,} bytes, {len(all_klines)} rows)")

# ── 2. Funding rate history ────────────────────────────────────────────────
log(f"\n=== 2. Funding rate history ===")
fund_url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={START_MS}"
funding = fetch_json(fund_url)
log(f"  raw count: {len(funding) if funding else 'ERROR'}")
if funding:
    t0f = datetime.fromtimestamp(int(funding[0]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    t1f = datetime.fromtimestamp(int(funding[-1]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {t0f} → {t1f}")
    log(f"  Last 6:")
    for r in funding[-6:]:
        ts = datetime.fromtimestamp(int(r["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        fr = float(r.get("fundingRate", 0))
        log(f"    {ts}: fundingRate={fr:.6f}")

    # Get page 2 if needed
    if len(funding) == 1000:
        last_t = int(funding[-1]["fundingTime"])
        fund_url2 = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={last_t+1}"
        funding2 = fetch_json(fund_url2)
        if funding2:
            funding.extend(funding2)
            log(f"  Page 2: +{len(funding2)} rows → total {len(funding)}")

    out2 = SCRATCH / f"apr_funding_{DATE_TAG}.csv"
    with open(out2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","fundingTime","fundingRate","markPrice"])
        w.writeheader()
        for r in funding:
            w.writerow({k: r.get(k,"") for k in ["symbol","fundingTime","fundingRate","markPrice"]})
    log(f"  Saved: {out2.name} ({out2.stat().st_size:,} bytes, {len(funding)} rows)")

    # Daily avg funding
    log(f"\n  Daily f_avg (last 10 days):")
    day_fr = {}
    for r in funding:
        d = datetime.fromtimestamp(int(r["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        fr = float(r.get("fundingRate", 0))
        day_fr.setdefault(d, []).append(fr)
    for d in sorted(day_fr.keys())[-10:]:
        avg = sum(day_fr[d])/len(day_fr[d])
        log(f"    {d}: f_avg={avg:.6f} (n={len(day_fr[d])})")

# ── 3. Spot klines check ─────────────────────────────────────────────────
log(f"\n=== 3. Spot klines check ===")
spot_url = f"{SAPI}/api/v3/klines?symbol={SYM}&interval=1d&limit=5"
spot = fetch_json(spot_url)
if spot and len(spot) > 0:
    log(f"  Spot available: {len(spot)} rows")
    k = spot[-1]
    ts = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Latest: {ts} close={k[4]} vol={float(k[7]):,.0f}")
    # full history
    spot_all_url = f"{SAPI}/api/v3/klines?symbol={SYM}&interval=1d&limit=1500&startTime={START_MS}"
    spot_all = fetch_json(spot_all_url)
    log(f"  Full spot: {len(spot_all) if spot_all else 0} rows")
    if spot_all:
        out3 = SCRATCH / f"apr_spot_{DATE_TAG}.csv"
        fields = ["open_time","open","high","low","close","volume","close_time","quote_vol",
                  "trades","taker_buy_base","taker_buy_quote","ignore"]
        with open(out3, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(fields)
            w.writerows(spot_all)
        log(f"  Saved: {out3.name} ({out3.stat().st_size:,} bytes)")
else:
    log(f"  Spot: N/A (404 or no data)")

# ── 4. Current OI + mark price ────────────────────────────────────────────
log(f"\n=== 4. Current OI + mark price ===")
oi_now = fetch_json(f"{FAPI}/fapi/v1/openInterest?symbol={SYM}")
mp_now = fetch_json(f"{FAPI}/fapi/v1/premiumIndex?symbol={SYM}")
if oi_now:
    oi_v = float(oi_now.get("openInterest", 0))
    log(f"  OI now: {oi_v:,.0f} contracts")
if mp_now:
    log(f"  markPrice: {mp_now.get('markPrice')} lastFundingRate: {mp_now.get('lastFundingRate')}")

# ── 5. Venue top check ────────────────────────────────────────────────────
log(f"\n=== 5. Venue top — check Bitget / other venues (L-30) ===")
# Check Binance volume vs expected (can't call non-Binance APIs)
log(f"  NOTE: Cross-venue check (Bitget/Gate/etc.) requires operator or CEX API key")
log(f"  Binance APRUSDT is the target venue for this case")

log(f"\n[A-2 DONE]")

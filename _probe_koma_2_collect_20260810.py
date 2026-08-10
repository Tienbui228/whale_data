"""
_probe_koma_2_collect_20260810.py
K-2: Klines full life + funding full + spot + input check for build_case.py
KOMAUSDT — listing 2024-12-10
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_PERP = "KOMAUSDT"
SYM_BASE = "KOMA"
SYM_LOWER = "koma"
SYM_SPOT = "KOMAUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-2 COLLECT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"
API  = "https://api.binance.com"

today_start = datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
today_ms = int(today_start.timestamp()*1000)
end_ms   = int(NOW.timestamp()*1000)

# ── 1. Perp klines 1d (full history) ─────────────────────────────────────
log("\n=== 1. Perp klines 1d (full history) ===")
all_klines = []
cur_end = end_ms
while True:
    url = f"{FAPI}/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1000&endTime={cur_end}"
    data = fetch_json(url)
    if not data: break
    complete = [k for k in data if int(k[0]) < today_ms]
    all_klines = complete + all_klines
    if len(data) < 1000 or int(data[0][0]) <= 0: break
    cur_end = int(data[0][0]) - 1
    time.sleep(0.1)

seen = set(); deduped = []
for k in all_klines:
    if k[0] not in seen:
        seen.add(k[0]); deduped.append(k)
deduped.sort(key=lambda x: x[0])
log(f"  Raw klines: {len(deduped)} rows")
if deduped:
    d0 = datetime.fromtimestamp(int(deduped[0][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(deduped[-1][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    rows_perp = []
    for k in deduped:
        dt = datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        o,h,l,c = float(k[1]),float(k[2]),float(k[3]),float(k[4])
        vol_q = float(k[7]); taker_q = float(k[10])
        taker_pct = taker_q/vol_q if vol_q > 0 else None
        rows_perp.append({"date":dt,"open":o,"high":h,"low":l,"close":c,
                     "vol_quote_usd":vol_q,"taker_pct":taker_pct})
    out_csv = SCRATCH / f"koma_perp_{DATE_TAG}.csv"
    with open(out_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","open","high","low","close","vol_quote_usd","taker_pct"])
        w.writeheader(); w.writerows(rows_perp)
    log(f"  CSV: {out_csv.name} ({out_csv.stat().st_size:,} bytes)")
    log(f"  Last 5:")
    for r in rows_perp[-5:]:
        log(f"    {r['date']} c={r['close']:.6f} vol=${r['vol_quote_usd']:,.0f} taker={r.get('taker_pct') or 'N/A'}")
    # vol spike analysis (top 5)
    med_vol = sorted([r['vol_quote_usd'] for r in rows_perp])[len(rows_perp)//2]
    log(f"\n  Vol spike check (≥8× median={med_vol:,.0f}):")
    spikes = [(r['date'],r['vol_quote_usd'],r['close']) for r in rows_perp if r['vol_quote_usd'] >= 8*med_vol]
    for dt,vol,c in sorted(spikes, key=lambda x:-x[1])[:10]:
        log(f"    {dt}: vol=${vol:,.0f} ({vol/med_vol:.1f}×) close={c:.6f}")

# ── 2. Funding rate (full history) ────────────────────────────────────────
log("\n=== 2. Funding history ===")
fund_all = []
end_ms2 = end_ms
for _ in range(30):
    url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM_PERP}&limit=1000&endTime={end_ms2}"
    data = fetch_json(url)
    if not data: break
    fund_all = data + fund_all
    if len(data) < 1000: break
    end_ms2 = int(data[0]["fundingTime"]) - 1
    time.sleep(0.1)

seen_f = set(); fund_deduped = []
for r in fund_all:
    k = r["fundingTime"]
    if k not in seen_f:
        seen_f.add(k); fund_deduped.append(r)
fund_deduped.sort(key=lambda x: x["fundingTime"])
log(f"  Records: {len(fund_deduped)}")
if fund_deduped:
    d0 = datetime.fromtimestamp(int(fund_deduped[0]["fundingTime"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(fund_deduped[-1]["fundingTime"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    rates = [float(r["fundingRate"]) for r in fund_deduped]
    log(f"  min={min(rates):.6f}  max={max(rates):.6f}  neg_count={sum(1 for r in rates if r<0)}")
    fund_json = SCRATCH / f"koma_funding_{DATE_TAG}.json"
    fund_json.write_text(json.dumps(fund_deduped), encoding="utf-8")
    fund_csv = SCRATCH / f"koma_funding_{DATE_TAG}.csv"
    fieldnames = list(fund_deduped[0].keys())
    if "date" not in fieldnames:
        fieldnames = ["date"] + fieldnames
    with open(fund_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in fund_deduped:
            ts = int(r.get("fundingTime",0))
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            row = dict(r); row["date"] = dt
            w.writerow(row)
    log(f"  Saved: {fund_json.name}, {fund_csv.name}")

# ── 3. OI hist — already in K-1 ──────────────────────────────────────────
log("\n=== 3. OI hist → already in K-1 ===")
oi_csv = SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv"
log(f"  {oi_csv.name}: exists={oi_csv.exists()}")

# ── 4. Spot klines ────────────────────────────────────────────────────────
log("\n=== 4. Spot klines ===")
spot_data = fetch_json(f"{API}/api/v3/klines?symbol={SYM_SPOT}&interval=1d&limit=1000")
if spot_data:
    spot_complete = [k for k in spot_data if int(k[0]) < today_ms]
    log(f"  Spot rows: {len(spot_complete)}")
    if spot_complete:
        d0 = datetime.fromtimestamp(int(spot_complete[0][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        d1 = datetime.fromtimestamp(int(spot_complete[-1][0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Range: {d0} → {d1}")
        spot_rows = []
        for k in spot_complete:
            dt = datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
            vol_q = float(k[7]); taker_q = float(k[10])
            taker_pct = taker_q/vol_q if vol_q > 0 else None
            spot_rows.append({"date":dt,"open":float(k[1]),"high":float(k[2]),"low":float(k[3]),
                               "close":float(k[4]),"vol_quote_usd":vol_q,"taker_pct":taker_pct})
        spot_csv = SCRATCH / f"koma_spot_{DATE_TAG}.csv"
        with open(spot_csv,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date","open","high","low","close","vol_quote_usd","taker_pct"])
            w.writeheader(); w.writerows(spot_rows)
        log(f"  CSV: {spot_csv.name} ({spot_csv.stat().st_size:,} bytes)")
        log(f"  Last 3:")
        for r in spot_rows[-3:]:
            log(f"    {r['date']} c={r['close']:.6f} vol=${r['vol_quote_usd']:,.0f} taker={r.get('taker_pct') or 'N/A'}")
else:
    log(f"  Spot: no data (HTTP 400 or pair not on spot)")
    spot_csv = SCRATCH / f"koma_spot_{DATE_TAG}.csv"
    with open(spot_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","open","high","low","close","vol_quote_usd","taker_pct"])
        w.writeheader()
    log(f"  Empty spot CSV created: {spot_csv.name}")

# ── 5. Input check ────────────────────────────────────────────────────────
log("\n=== 5. Input check for build_case.py ===")
required = [
    SCRATCH / f"koma_perp_{DATE_TAG}.csv",
    SCRATCH / f"koma_lsr_raw_{DATE_TAG}.csv",
    SCRATCH / f"koma_funding_{DATE_TAG}.csv",
    SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv",
    SCRATCH / f"koma_spot_{DATE_TAG}.csv",
    SCRATCH / f"koma_bapi_{DATE_TAG}.json",
    SCRATCH / f"koma_perp_info_{DATE_TAG}.json",
]
all_ok = True
for p in required:
    ok = p.exists() and p.stat().st_size > 0
    log(f"  {'OK' if ok else 'MISSING'} {p.name} ({p.stat().st_size if p.exists() else 0:,} bytes)")
    if not ok: all_ok = False
log(f"\n  All inputs ready: {'YES' if all_ok else 'NO — fix before build'}")
log(f"\n[K-2 COLLECT DONE]")

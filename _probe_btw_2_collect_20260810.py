"""
_probe_btw_2_collect_20260810.py
W-2: Collect klines (perp + Alpha) + funding — BTWUSDT.
BTW = ALPHA_778. taker from Alpha klines = ABSTAIN. Perp taker valid.
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
SYM_BASE = "BTW"
SYM_LOWER = "btw"
ALPHA_ID = "ALPHA_778"
FAPI = "https://fapi.binance.com"
SAPI = "https://api.binance.com"
BAPI = "https://www.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"W-2 COLLECT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── 0. exchangeInfo ───────────────────────────────────────────────────────
log(f"\n=== 0. FAPI exchangeInfo ===")
info = fetch_json(f"{FAPI}/fapi/v1/exchangeInfo")
btw_info = {}
if info:
    for s in info.get("symbols",[]):
        if s.get("symbol") == SYM:
            btw_info = s
            onb_ms = s.get("onboardDate",0)
            onb = datetime.fromtimestamp(int(onb_ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if onb_ms else "N/A"
            log(f"  status={s.get('status')} onboardDate={onb_ms} ({onb})")
            log(f"  baseAsset={s.get('baseAsset')} contractType={s.get('contractType')}")
            # Save
            (SCRATCH/f"{SYM_LOWER}_perp_info_{DATE_TAG}.json").write_text(
                json.dumps(s, indent=2), encoding="utf-8")
            break

# Determine start time
onb_ms = int(btw_info.get("onboardDate", 0))
if onb_ms:
    START_MS = onb_ms
    start_d = datetime.fromtimestamp(onb_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Perp listed: {start_d}")
else:
    # Fallback: use Jun 1 2026 (before blowoff)
    START_MS = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
    log(f"  onboardDate unknown — starting from 2026-05-01")

# ── 1. Perp klines ────────────────────────────────────────────────────────
log(f"\n=== 1. Perp klines 1d — full history ===")
all_klines = []
end_ms = None; page = 0
while True:
    url = f"{FAPI}/fapi/v1/klines?symbol={SYM}&interval=1d&limit=1500"
    url += f"&startTime={START_MS}" if page==0 else f"&startTime={end_ms+1}"
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
        tp = round(tb/vol_b*100,2) if vol_b>0 else 0
        log(f"    {ts}: o={k[1]} h={k[2]} l={k[3]} c={k[4]} vol_usd=${qv:,.0f} taker={tp:.1f}%")
    out_k = SCRATCH / f"btw_klines_{DATE_TAG}.csv"
    fields = ["open_time","open","high","low","close","volume","close_time","quote_vol",
              "trades","taker_buy_base","taker_buy_quote","ignore"]
    with open(out_k, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fields); w.writerows(all_klines)
    log(f"  Saved: {out_k.name} ({out_k.stat().st_size:,} bytes)")

# ── 2. Funding rate ───────────────────────────────────────────────────────
log(f"\n=== 2. Funding rate history ===")
fund_all = []
for start_t in [START_MS]:
    url = f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={start_t}"
    batch = fetch_json(url)
    if batch:
        fund_all.extend(batch)
        log(f"  Page 1: {len(batch)} rows")
        if len(batch) == 1000:
            last_t = int(batch[-1]["fundingTime"])
            batch2 = fetch_json(f"{FAPI}/fapi/v1/fundingRate?symbol={SYM}&limit=1000&startTime={last_t+1}")
            if batch2:
                fund_all.extend(batch2)
                log(f"  Page 2: {len(batch2)} rows → total {len(fund_all)}")

if fund_all:
    t0f = datetime.fromtimestamp(int(fund_all[0]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    t1f = datetime.fromtimestamp(int(fund_all[-1]["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {t0f} → {t1f}")
    log(f"  Last 9 (3 days):")
    for r in fund_all[-9:]:
        ts = datetime.fromtimestamp(int(r["fundingTime"])/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        log(f"    {ts}: {float(r.get('fundingRate',0)):.6f}")
    out_f = SCRATCH / f"btw_funding_{DATE_TAG}.csv"
    with open(out_f, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","fundingTime","fundingRate","markPrice"])
        w.writeheader()
        for r in fund_all:
            w.writerow({k: r.get(k,"") for k in ["symbol","fundingTime","fundingRate","markPrice"]})
    log(f"  Saved: {out_f.name} ({out_f.stat().st_size:,} bytes, {len(fund_all)} rows)")

# ── 3. Alpha klines ───────────────────────────────────────────────────────
log(f"\n=== 3. Alpha klines (ALPHA_778) ===")
# Lookup alpha_id_map
alpha_map_p = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_numeric_id = None
if alpha_map_p.exists():
    amap = json.loads(alpha_map_p.read_text(encoding="utf-8"))
    alpha_numeric_id = amap.get(SYM_BASE)
    log(f"  alpha_id from map: {alpha_numeric_id}")

# Try alpha klines endpoint
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
if alpha_store.exists():
    try:
        import pandas as pd
        cnt = 0
        for p in alpha_store.rglob("*.parquet"):
            try:
                df = pd.read_parquet(p, columns=["symbol"])
                c = (df["symbol"] == SYM_BASE).sum()
                if c > 0: cnt += c
            except: pass
        log(f"  Alpha in local store: {cnt} rows")
    except Exception as e:
        log(f"  Alpha store check: {e}")
else:
    log(f"  Alpha local store not found")

# ── 4. Spot check ─────────────────────────────────────────────────────────
log(f"\n=== 4. Spot check ===")
spot = fetch_json(f"{SAPI}/api/v3/klines?symbol={SYM}&interval=1d&limit=5")
if spot and len(spot)>0:
    log(f"  Spot available: {len(spot)} rows latest close={spot[-1][4]}")
else:
    log(f"  Spot: N/A (no spot pair)")

# ── 5. BAPI token detail ──────────────────────────────────────────────────
log(f"\n=== 5. BAPI Alpha token detail ===")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_data = fetch_json(bapi_url, timeout=30)
btw_tok = None
if bapi_data:
    raw = bapi_data.get("data",[])
    token_list = raw if isinstance(raw,list) else raw.get("tokenList", raw.get("list",[]))
    for t in token_list:
        sym = t.get("tokenSymbol","").upper()
        aid = t.get("alphaId","")
        if sym == SYM_BASE or (alpha_numeric_id and aid == alpha_numeric_id):
            btw_tok = t; break
if btw_tok:
    log(f"  Found: sym={btw_tok.get('tokenSymbol')} alphaId={btw_tok.get('alphaId')}")
    for k in ["contractAddress","totalSupply","circulatingSupply","holders",
              "fullyDelisted","listingTime","price","marketCap"]:
        log(f"    {k}: {btw_tok.get(k)}")
    (SCRATCH/f"{SYM_LOWER}_bapi_{DATE_TAG}.json").write_text(
        json.dumps(btw_tok, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  Saved: btw_bapi_{DATE_TAG}.json")
else:
    log(f"  BTW not found in BAPI token list")
    (SCRATCH/f"{SYM_LOWER}_bapi_{DATE_TAG}.json").write_text(
        json.dumps({"note":"not_found","symbol":SYM_BASE}, indent=2), encoding="utf-8")

log(f"\n[W-2 DONE]")

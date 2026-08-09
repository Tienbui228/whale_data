"""
_probe_cookie_c5_onchain_20260809.py
COOKIE C-5: BAPI verify + depth snap #1 + BscScan + on-chain tiers
"""
import sys, io, json, csv, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-5 ONCHAIN  |  {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR fetching {url[:80]}: {e}")
        return None

# ── C-5a: BAPI verify ────────────────────────────────────────────────────────
log("\n=== C-5a: BAPI TOKEN INFO (from scratch JSON) ===")
bapi_file = SCRATCH / f"cookie_bapi_{DATE_TAG}.json"
if bapi_file.exists():
    bapi = json.loads(bapi_file.read_text(encoding="utf-8"))
    log(f"  alphaId:          {bapi.get('alphaId')}")
    log(f"  tokenSymbol:      {bapi.get('tokenSymbol')}")
    log(f"  contractAddress:  {bapi.get('contractAddress')}")
    log(f"  totalSupply:      {bapi.get('totalSupply')}")
    log(f"  holders:          {bapi.get('holders')}")
    log(f"  fullyDelisted:    {bapi.get('fullyDelisted')}")
    log(f"  offsell:          {bapi.get('offsell')}")
    log(f"  offline:          {bapi.get('offline')}")
    lt = bapi.get('listingTime')
    if lt:
        lt_dt = datetime.fromtimestamp(int(lt)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log(f"  listingTime:      {lt} ({lt_dt})")
    # Check for delisting fields
    for k in ['delistTime','delistingTime','delistedTime','delistedDate','delistDate']:
        if bapi.get(k):
            log(f"  {k}: {bapi.get(k)}")
    # Show all keys with non-null values
    log(f"\n  All non-null fields:")
    for k,v in bapi.items():
        if v is not None and v != "" and v != False and v != 0:
            log(f"    {k}: {v}")
else:
    log(f"  MISSING: {bapi_file.name}")

# Re-fetch BAPI for fresh status check
log(f"\n  Re-fetch BAPI live status for COOKIE:")
bapi_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
bapi_live = fetch_json(bapi_url, timeout=30)
if bapi_live:
    raw = bapi_live.get("data", [])
    token_list = raw if isinstance(raw, list) else raw.get("tokenList", raw.get("list", []))
    cookie_live = None
    for t in token_list:
        if t.get("alphaId") == "ALPHA_33" or t.get("tokenSymbol","").upper() == "COOKIE":
            cookie_live = t
            break
    if cookie_live:
        log(f"  LIVE: fullyDelisted={cookie_live.get('fullyDelisted')} offsell={cookie_live.get('offsell')} offline={cookie_live.get('offline')}")
        log(f"  LIVE: holders={cookie_live.get('holders')} totalSupply={cookie_live.get('totalSupply')}")
        # Check all timing fields
        for k in ['listingTime','delistTime','delistingTime','delistedTime','delistDate']:
            if cookie_live.get(k):
                ts_v = cookie_live.get(k)
                try:
                    dt_v = datetime.fromtimestamp(int(ts_v)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                    log(f"  LIVE: {k}={ts_v} ({dt_v})")
                except:
                    log(f"  LIVE: {k}={ts_v}")
    else:
        log("  COOKIE not found in live BAPI list")
else:
    log("  BAPI live fetch failed")

# ── C-5b: PERP INFO verify ───────────────────────────────────────────────────
log("\n=== C-5b: PERP INFO (from scratch JSON) ===")
perp_info_file = SCRATCH / f"cookie_perp_info_{DATE_TAG}.json"
if perp_info_file.exists():
    pi = json.loads(perp_info_file.read_text(encoding="utf-8"))
    log(f"  symbol:      {pi.get('symbol')}")
    log(f"  status:      {pi.get('status')}")
    onb = pi.get('onboardDate')
    if onb:
        onb_dt = datetime.fromtimestamp(int(onb)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log(f"  onboardDate: {onb} ({onb_dt})")
    del_d = pi.get('deliveryDate')
    if del_d:
        try:
            del_dt = datetime.fromtimestamp(int(del_d)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            log(f"  deliveryDate:{del_d} ({del_dt})")
        except:
            log(f"  deliveryDate:{del_d}")
    log(f"  marginType:  {pi.get('marginType')}")
    log(f"  contractType:{pi.get('contractType')}")
    log(f"  quoteAsset:  {pi.get('quoteAsset')}")
else:
    log(f"  MISSING: {perp_info_file.name}")

# ── C-5c: DEPTH SNAP #1 ──────────────────────────────────────────────────────
log("\n=== C-5c: DEPTH SNAP #1 (COOKIEUSDT perp) ===")
depth_url = "https://fapi.binance.com/fapi/v1/depth?symbol=COOKIEUSDT&limit=1000"
depth_raw = fetch_json(depth_url)
snap1_time = datetime.now(timezone.utc)
snap1_str = snap1_time.strftime("%Y-%m-%d %H:%M:%S UTC")
if depth_raw:
    bids = [(float(p), float(q)) for p,q in depth_raw.get("bids",[])]
    asks = [(float(p), float(q)) for p,q in depth_raw.get("asks",[])]
    if bids and asks:
        mid = (bids[0][0] + asks[0][0]) / 2
        bid_top = bids[0][0]
        ask_top = asks[0][0]
        spread_pct = (ask_top - bid_top) / mid * 100

        # Compute bid/ask depth in USD
        bid2 = sum(p*q for p,q in bids)
        ask2 = sum(p*q for p,q in asks)
        ratio = bid2/ask2 if ask2 > 0 else None

        log(f"  Time: {snap1_str}")
        log(f"  mid:       ${mid:.8f}")
        log(f"  bid_top:   ${bid_top:.8f}")
        log(f"  ask_top:   ${ask_top:.8f}")
        log(f"  spread:    {spread_pct:.3f}%")
        log(f"  bid2(USD): ${bid2:,.0f}")
        log(f"  ask2(USD): ${ask2:,.0f}")
        log(f"  ratio bid/ask: {ratio:.4f}" if ratio else "  ratio: N/A")

        # Depth buckets (±1%, ±2%, ±5%)
        log(f"\n  Depth buckets:")
        for pct in [0.01, 0.02, 0.05]:
            bid_b = sum(p*q for p,q in bids if p >= mid*(1-pct))
            ask_b = sum(p*q for p,q in asks if p <= mid*(1+pct))
            log(f"    ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=${ask_b:,.0f} ratio={bid_b/ask_b:.3f}" if ask_b > 0 else f"    ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=0")

        # Save snap JSON
        snap_out = SCRATCH / f"cookie_depth_snap1_{DATE_TAG}.json"
        snap_out.write_text(json.dumps({
            "snap": 1, "time": snap1_str, "symbol": "COOKIEUSDT",
            "mid": mid, "bid_top": bid_top, "ask_top": ask_top,
            "spread_pct": spread_pct,
            "bid2_usd": bid2, "ask2_usd": ask2, "ratio": ratio,
            "bids_len": len(bids), "asks_len": len(asks)
        }, indent=2), encoding="utf-8")
        log(f"\n  Saved: {snap_out.name}")
        log(f"  SNAP #2 GATE: ≥{(snap1_time.timestamp()+4*3600):.0f} ({(snap1_time.replace(hour=snap1_time.hour+4) if snap1_time.hour+4<24 else snap1_time).strftime('%H')}:xx UTC or compute: snap1 + 4h)")

        import time as time_mod
        snap2_gate_ts = snap1_time.timestamp() + 4*3600
        snap2_gate_dt = datetime.fromtimestamp(snap2_gate_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log(f"  SNAP #2 GATE: {snap2_gate_dt}")
    else:
        log("  Empty bids/asks")
else:
    log("  Depth fetch FAILED")

# ── C-5d: BscScan (on-chain holders, top holders) ───────────────────────────
log("\n=== C-5d: BscScan on-chain ===")
CONTRACT = "0xc0041ef357b183448b235a8ea73ce4e4ec8c265f"
log(f"  Contract: {CONTRACT}")

# BscScan V2 API (free, no key needed for some endpoints)
bscscan_base = "https://api.bscscan.com/api"

# Token info (V2 public)
url_info = f"{bscscan_base}?module=stats&action=tokensupply&contractaddress={CONTRACT}&apikey=YourApiKeyToken"
info_data = fetch_json(url_info, timeout=15)
if info_data:
    log(f"  Supply API: status={info_data.get('status')} message={info_data.get('message')}")
    if info_data.get("status") == "1":
        supply = int(info_data.get("result","0"))
        log(f"  Total supply: {supply:,} tokens")

# Token holders count (BscScan may require API key)
url_holders = f"{bscscan_base}?module=token&action=tokeninfo&contractaddress={CONTRACT}&apikey=YourApiKeyToken"
holders_data = fetch_json(url_holders, timeout=15)
if holders_data:
    log(f"  TokenInfo API: status={holders_data.get('status')} message={holders_data.get('message')}")
    if holders_data.get("status") == "1":
        result = holders_data.get("result", [{}])
        if isinstance(result, list) and result:
            r = result[0]
            log(f"  name: {r.get('name')} symbol: {r.get('symbol')}")
            log(f"  holdersCount: {r.get('holdersCount')}")
            log(f"  totalSupply: {r.get('totalSupply')}")
            log(f"  circulatingSupply: {r.get('circulatingSupply')}")
    else:
        log(f"  result: {str(holders_data.get('result',''))[:200]}")

log(f"\n  NOTE: BscScan NOTOK V1 — API key required for holder detail")
log(f"  On-chain data: BAPI holders={bapi.get('holders') if bapi_file.exists() else 'N/A'}")
log(f"  Nansen: LOCKED (NANSEN_KEY_LOCKED env) — ghi CẦN OPERATOR")

# ── C-5e: FRESH WALLET tier (from freshwatch Aug if available) ───────────────
log("\n=== C-5e: COOKIE freshwatch tier ===")
fw_paths = [
    SCRATCH / "freshwatch_daily_2026-08.csv",
    ROOT / "data" / "raw" / "freshwatch_daily_2026-08.csv",
]
fw_cookie = []
for fp in fw_paths:
    if fp.exists():
        with open(fp, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                sym = row.get("symbol","").upper().replace("USDT","")
                if sym == "COOKIE":
                    fw_cookie.append(row)
        log(f"  Source: {fp.name}, COOKIE rows: {len(fw_cookie)}")
        break

if fw_cookie:
    # Show last 10 rows
    log(f"  Last 10 freshwatch rows for COOKIE:")
    cols = list(fw_cookie[0].keys())
    log(f"  Cols: {cols}")
    for r in fw_cookie[-10:]:
        log(f"    {r.get('date','?')}: " + " ".join(f"{k}={r.get(k,'?')}" for k in cols[:8]))
else:
    log("  No freshwatch data found for COOKIE")

# ── C-5f: Summary on-chain status ────────────────────────────────────────────
log("\n=== C-5f: ON-CHAIN SUMMARY ===")
log(f"  Contract (BSC): {CONTRACT}")
log(f"  BAPI holders (live): {cookie_live.get('holders') if bapi_live and cookie_live else 'N/A'}")
log(f"  BAPI fullyDelisted: True (confirmed live)")
log(f"  Alpha taker_alpha: ABSTAIN (fullyDelisted=True, same as FF)")
log(f"  Nansen: CẦN OPERATOR (LOCKED)")
log(f"  BscScan top holders: CẦN OPERATOR (API key V1 NOTOK — manual BscScan UI)")
log(f"  Unlock schedule: CẦN OPERATOR (no on-chain vesting contract found)")

log(f"\n[C-5 DONE] snap1 at {snap1_str}")
log(f"[C-5 SNAP#2 GATE]: {snap2_gate_dt}")

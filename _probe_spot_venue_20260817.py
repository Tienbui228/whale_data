"""
_probe_spot_venue_20260817.py
S-0→S-3: store probe + venue discovery + wash test + DEX fallback for APR
Tokens: AIN (ALPHA_260), GUA (ALPHA_483), APR (not in alpha_id_map → CEX/DEX only)
"""
import sys, io, json, urllib.request, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
STORE   = ROOT / "data" / "raw" / "spot_klines_1d"
OUT     = ROOT / "scratch" / "spot_venue_discovery_20260817.json"

TOKENS = {
    "AIN": {"alpha_id": "ALPHA_260", "sym": "AIN"},
    "GUA": {"alpha_id": "ALPHA_483", "sym": "GUA"},
    "APR": {"alpha_id": None,        "sym": "APR"},
}

# ─────────────────────────────────────────────────────────────────────────────
def fetch_json(url, params=None, timeout=15):
    if params:
        qs = "&".join(f"{k}={v}" for k,v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# S-0: PROBE STORE
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("S-0: PROBE spot_klines_1d store")
print("=" * 60)

store_results = {}  # sym -> {dates: [...], rows: int, last_date: str}

if not STORE.exists():
    print(f"  STORE NOT FOUND: {STORE}")
else:
    # List date= partitions
    date_dirs = sorted([d for d in STORE.iterdir() if d.is_dir() and d.name.startswith("date=")])
    print(f"  Total date partitions: {len(date_dirs)}")
    if date_dirs:
        first = date_dirs[0].name.replace("date=", "")
        last  = date_dirs[-1].name.replace("date=", "")
        print(f"  Range: {first} → {last}")

    # Try to read last few parquet files for AIN/GUA
    try:
        import pandas as pd
        # First: print actual columns from a recent parquet
        for dd in reversed(date_dirs[-5:]):
            pq = dd / "part-0.parquet"
            if pq.exists():
                df_sample = pd.read_parquet(pq)
                print(f"  Sample parquet cols ({dd.name}): {list(df_sample.columns)}")
                print(f"  Sample values (row 0): {dict(df_sample.iloc[0])}")
                break

        for sym, meta in TOKENS.items():
            alpha_id = meta["alpha_id"]
            if alpha_id is None:
                store_results[sym] = {"rows": 0, "last_date": None, "note": "not in alpha store"}
                continue

            rows_found = []
            for dd in date_dirs:
                pq = dd / "part-0.parquet"
                if not pq.exists():
                    continue
                df = pd.read_parquet(pq)
                # Try different column names for alpha_id
                if "alpha_id" in df.columns:
                    sub = df[df["alpha_id"] == alpha_id]
                elif "symbol" in df.columns:
                    # Try both formats: 'AINUSDT' and 'AIN'
                    sub = df[df["symbol"].isin([f"{sym}USDT", sym])]
                elif "ticker" in df.columns:
                    sub = df[df["ticker"] == sym]
                else:
                    # Unknown schema
                    print(f"  [{dd.name}] UNKNOWN cols: {list(df.columns)[:10]}")
                    break
                if len(sub) > 0:
                    rows_found.append(dd.name.replace("date=", ""))

            store_results[sym] = {
                "rows": len(rows_found),
                "last_date": rows_found[-1] if rows_found else None,
                "first_date": rows_found[0] if rows_found else None,
            }
            print(f"  {sym} ({alpha_id}): {len(rows_found)} date-rows, "
                  f"last={rows_found[-1] if rows_found else 'NONE'}")

    except ImportError:
        print("  pandas not available — reading parquet columns via pyarrow")
        try:
            import pyarrow.parquet as pq_lib
            # Just check columns from one parquet
            sample_pq = date_dirs[-1] / "part-0.parquet"
            if sample_pq.exists():
                tbl = pq_lib.read_table(str(sample_pq))
                cols = tbl.schema.names
                print(f"  Parquet columns: {cols}")
                for sym, meta in TOKENS.items():
                    alpha_id = meta["alpha_id"]
                    if alpha_id is None:
                        store_results[sym] = {"rows": 0, "last_date": None, "note": "not in alpha store"}
                        continue
                    # Count rows matching alpha_id
                    if "alpha_id" in cols:
                        import pyarrow.compute as pc
                        mask = pc.equal(tbl["alpha_id"], alpha_id)
                        n = pc.sum(mask).as_py()
                        print(f"  {sym}: {n} rows in last partition")
        except Exception as e2:
            print(f"  pyarrow error: {e2}")
    except Exception as e:
        print(f"  Store read error: {e}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# S-1: VENUE DISCOVERY — 6 CEX tickers
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("S-1: VENUE DISCOVERY — 6 CEX 24h ticker")
print("=" * 60)

def get_binance_spot(sym):
    d = fetch_json(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT")
    if "_error" in d or "code" in d:
        return None, str(d.get("_error", d.get("msg", "err")))
    vol = float(d.get("quoteVolume", 0))
    return vol, "ok"

def get_bybit_spot(sym):
    d = fetch_json(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={sym}USDT")
    if "_error" in d:
        return None, d["_error"]
    # BYBIT TRAP: HTTP 200 retCode=10001 = pair doesn't exist
    rc = d.get("retCode", 0)
    if rc != 0:
        return None, f"retCode={rc}"
    items = d.get("result", {}).get("list", [])
    if not items:
        return None, "no list"
    vol = float(items[0].get("turnover24h", 0))  # turnover24h = quote vol USDT
    return vol, "ok"

def get_gate_spot(sym):
    d = fetch_json(f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={sym}_USDT")
    if "_error" in d:
        return None, d["_error"]
    if not isinstance(d, list) or len(d) == 0:
        return None, "empty"
    vol = float(d[0].get("quote_volume", 0))  # gate: quote_volume = USDT
    return vol, "ok"

def get_bitget_spot(sym):
    d = fetch_json(f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={sym}USDT")
    if "_error" in d:
        return None, d["_error"]
    items = d.get("data", [])
    if not items:
        return None, "no data"
    item = items[0]
    # usdtVol preferred, fallback quoteVol
    vol = float(item.get("usdtVol", item.get("quoteVol", 0)))
    return vol, "ok"

def get_mexc_spot(sym):
    d = fetch_json(f"https://api.mexc.com/api/v3/ticker/24hr?symbol={sym}USDT")
    if "_error" in d or "code" in d:
        return None, str(d.get("_error", d.get("msg", "err")))
    vol = float(d.get("quoteVolume", 0))
    return vol, "ok"

def get_kucoin_spot(sym):
    d = fetch_json(f"https://api.kucoin.com/api/v1/market/stats?symbol={sym}-USDT")
    if "_error" in d:
        return None, d["_error"]
    if d.get("code") != "200000":
        return None, f"code={d.get('code')}"
    data = d.get("data", {})
    raw = data.get("volValue")
    if raw is None:
        return None, "volValue=None (pair absent?)"
    vol = float(raw)
    return vol, "ok"

venue_results = {}  # sym -> {venue: vol_usd, ...}

for sym in TOKENS:
    print(f"\n  ── {sym} ──")
    have = {}
    errors = {}

    v, s = get_binance_spot(sym)
    if v: have["binance"] = v
    else: errors["binance"] = s
    time.sleep(0.2)

    v, s = get_bybit_spot(sym)
    if v: have["bybit"] = v
    else: errors["bybit"] = s
    time.sleep(0.2)

    v, s = get_gate_spot(sym)
    if v: have["gate"] = v
    else: errors["gate"] = s
    time.sleep(0.2)

    v, s = get_bitget_spot(sym)
    if v: have["bitget"] = v
    else: errors["bitget"] = s
    time.sleep(0.2)

    v, s = get_mexc_spot(sym)
    if v: have["mexc"] = v
    else: errors["mexc"] = s
    time.sleep(0.2)

    v, s = get_kucoin_spot(sym)
    if v: have["kucoin"] = v
    else: errors["kucoin"] = s
    time.sleep(0.2)

    # Print table
    for venue in ["binance","bybit","gate","bitget","mexc","kucoin"]:
        if venue in have:
            print(f"    {venue:10s} {have[venue]:>15,.0f} USD")
        else:
            print(f"    {venue:10s} {'ABSENT':>15s}  ({errors.get(venue,'')})")

    top_venue = max(have, key=have.get) if have else None
    top_vol   = have[top_venue] if top_venue else 0
    print(f"  → TOP: {top_venue} vol={top_vol:,.0f}")

    venue_results[sym] = {
        "have": have,
        "errors": errors,
        "top_venue": top_venue,
        "top_vol_usd": top_vol,
    }

print()

# ─────────────────────────────────────────────────────────────────────────────
# S-2: WASH TEST — depth ±2% for top venue
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("S-2: WASH TEST — depth ±2%")
print("=" * 60)

def depth_binance(sym):
    d = fetch_json("https://api.binance.com/api/v3/depth", {"symbol": f"{sym}USDT", "limit": 20})
    if "_error" in d: return None
    bids = [(float(p), float(q)) for p, q in d.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in d.get("asks", [])]
    return bids, asks

def depth_bybit(sym):
    d = fetch_json("https://api.bybit.com/v5/market/orderbook",
                   {"category":"spot","symbol":f"{sym}USDT","limit":50})
    if "_error" in d: return None
    rc = d.get("retCode",0)
    if rc != 0: return None
    bids = [(float(p), float(q)) for p, q in d.get("result",{}).get("b",[])]
    asks = [(float(p), float(q)) for p, q in d.get("result",{}).get("a",[])]
    return bids, asks

def depth_gate(sym):
    d = fetch_json("https://api.gateio.ws/api/v4/spot/order_book",
                   {"currency_pair":f"{sym}_USDT","limit":20})
    if "_error" in d: return None
    bids = [(float(p), float(q)) for p, q in d.get("bids",[])]
    asks = [(float(p), float(q)) for p, q in d.get("asks",[])]
    return bids, asks

def depth_mexc(sym):
    d = fetch_json("https://api.mexc.com/api/v3/depth", {"symbol":f"{sym}USDT","limit":20})
    if "_error" in d: return None
    bids = [(float(p), float(q)) for p, q in d.get("bids",[])]
    asks = [(float(p), float(q)) for p, q in d.get("asks",[])]
    return bids, asks

def depth_kucoin(sym):
    d = fetch_json(f"https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol={sym}-USDT")
    if "_error" in d: return None
    if d.get("code") != "200000": return None
    data = d.get("data", {})
    bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in data.get("asks", [])]
    return bids, asks

def compute_depth_2pct(bids, asks):
    if not bids or not asks: return 0
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2
    depth_bid = sum(p*q for p,q in bids if p >= mid * 0.98)
    depth_ask = sum(p*q for p,q in asks if p <= mid * 1.02)
    return depth_bid + depth_ask

wash_results = {}

for sym, vdata in venue_results.items():
    top = vdata["top_venue"]
    top_vol = vdata["top_vol_usd"]

    if not top:
        print(f"  {sym}: no top venue — skip wash test")
        wash_results[sym] = {"depth2pct": 0, "ratio": None, "verdict": "SKIP"}
        continue

    depth_data = None
    if top == "binance":
        depth_data = depth_binance(sym)
    elif top == "bybit":
        depth_data = depth_bybit(sym)
    elif top == "gate":
        depth_data = depth_gate(sym)
    elif top in ("mexc",):
        depth_data = depth_mexc(sym)
    elif top == "kucoin":
        depth_data = depth_kucoin(sym)
    else:
        print(f"  {sym}: depth not implemented for {top} — skip")
        wash_results[sym] = {"depth2pct": 0, "ratio": None, "verdict": "SKIP"}
        continue

    time.sleep(0.3)

    if depth_data is None:
        print(f"  {sym}: depth fetch failed for {top}")
        wash_results[sym] = {"depth2pct": 0, "ratio": None, "verdict": "SKIP"}
        continue

    bids, asks = depth_data
    d2pct = compute_depth_2pct(bids, asks)

    ratio = top_vol / d2pct if d2pct > 0 else None
    if ratio is None:
        verdict = "SKIP"
    elif ratio < 5:
        verdict = "CLEAN"
    elif ratio < 20:
        verdict = "SUSPECT"
    else:
        verdict = "WASH"

    ratio_s = f"{ratio:.1f}" if ratio is not None else "N/A"
    print(f"  {sym}: top={top} vol={top_vol:,.0f} depth2%={d2pct:,.0f} ratio={ratio_s} → {verdict}")
    wash_results[sym] = {
        "top_venue": top,
        "depth2pct_usd": d2pct,
        "ratio": round(ratio, 2) if ratio else None,
        "verdict": verdict,
    }

print()

# ─────────────────────────────────────────────────────────────────────────────
# S-3: DEX FALLBACK — APR (not in CEX or CEX vol very low)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("S-3: DEX FALLBACK for APR")
print("=" * 60)

apr_data = {}

# Step 1: CoinGecko — find BSC contract for APR
print("  CoinGecko: searching APR contract on BSC...")
# Try direct coin search by symbol
cg_search = fetch_json("https://api.coingecko.com/api/v3/search?query=APR")
time.sleep(0.5)

apr_contract = None
if "_error" not in cg_search:
    coins = cg_search.get("coins", [])
    # Look for exact APR match
    for c in coins[:10]:
        print(f"    {c.get('id')} | {c.get('symbol','').upper()} | {c.get('name')}")
        if c.get("symbol","").upper() == "APR":
            # Fetch coin detail for platforms
            coin_id = c.get("id")
            detail = fetch_json(f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false")
            time.sleep(0.5)
            if "_error" not in detail:
                platforms = detail.get("platforms", {})
                bsc_addr = platforms.get("binance-smart-chain", "")
                eth_addr = platforms.get("ethereum", "")
                print(f"    APR platforms: BSC={bsc_addr or 'NONE'} ETH={eth_addr or 'NONE'}")
                if bsc_addr:
                    apr_contract = bsc_addr
                apr_data["coingecko_platforms"] = platforms
                apr_data["coingecko_id"] = coin_id
            break

# Step 2: DexScreener — query by symbol
print("  DexScreener: querying APR...")
ds = fetch_json("https://api.dexscreener.com/latest/dex/search?q=APR")
time.sleep(0.5)

if "_error" not in ds:
    pairs = ds.get("pairs", []) or []
    # Filter for APR/USDT or APR/WBNB on BSC, pick highest liquidity
    usdt_pairs = [p for p in pairs if p.get("baseToken",{}).get("symbol","").upper() == "APR"
                  and "bsc" in p.get("chainId","").lower()]
    if not usdt_pairs:
        usdt_pairs = [p for p in pairs if p.get("baseToken",{}).get("symbol","").upper() == "APR"]

    print(f"  DexScreener: {len(pairs)} total pairs, {len(usdt_pairs)} APR pairs")

    if usdt_pairs:
        # Sort by liquidity
        usdt_pairs.sort(key=lambda p: float(p.get("liquidity",{}).get("usd",0) or 0), reverse=True)
        top_pair = usdt_pairs[0]
        dex_vol24h = top_pair.get("volume",{}).get("h24", 0)
        dex_liq    = top_pair.get("liquidity",{}).get("usd", 0)
        dex_price  = top_pair.get("priceUsd","N/A")
        dex_chain  = top_pair.get("chainId","?")
        dex_dex    = top_pair.get("dexId","?")
        dex_pair   = top_pair.get("pairAddress","?")
        print(f"  TOP pair: {dex_chain}/{dex_dex} liq={dex_liq:,.0f} vol24h={dex_vol24h:,.0f} price={dex_price}")
        print(f"  Pair address: {dex_pair}")

        apr_data["dexscreener_top_pair"] = {
            "chain": dex_chain,
            "dex": dex_dex,
            "vol24h_usd": dex_vol24h,
            "liquidity_usd": dex_liq,
            "priceUsd": dex_price,
            "pairAddress": dex_pair,
        }

        # Wash test for DEX: vol / liquidity ratio
        if dex_liq and float(dex_liq) > 0:
            dex_ratio = float(dex_vol24h or 0) / float(dex_liq)
            print(f"  DEX wash proxy: vol/liq = {dex_ratio:.1f} (note: DEX double-counts, treat as informational)")
            apr_data["dex_wash_proxy_ratio"] = round(dex_ratio, 2)
    else:
        print("  DexScreener: no APR pairs found")

# If APR found on CEX too, show comparison
apr_cex = venue_results.get("APR", {})
if apr_cex.get("top_vol_usd", 0) > 0:
    print(f"  APR CEX top: {apr_cex['top_venue']} vol={apr_cex['top_vol_usd']:,.0f}")
    print(f"  Note: if CEX vol > DEX vol → use CEX as top_venue; DEX for reference only")

print()

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("SUMMARY — VENUE SELECTION")
print("=" * 60)

summary = {}
for sym in TOKENS:
    vdata = venue_results.get(sym, {})
    wdata = wash_results.get(sym, {})
    have  = vdata.get("have", {})

    top   = vdata.get("top_venue")
    vol   = vdata.get("top_vol_usd", 0)
    ratio = wdata.get("ratio")
    verdict = wdata.get("verdict","?")

    # Check if we need DEX fallback
    use_dex = (sym == "APR" and vol < 100_000) or top is None

    venue_final = top if not use_dex else "dex"
    wash_flag   = verdict in ("WASH", "SKIP") or use_dex

    print(f"  {sym}: venue={venue_final} vol24h={vol:,.0f} wash={verdict} ratio={ratio} "
          f"flag={wash_flag}")

    summary[sym] = {
        "venue_top_measurable": venue_final,
        "vol_spot_usd_24h": vol,
        "all_venues": have,
        "wash_ratio": ratio,
        "wash_verdict": verdict,
        "wash_suspect_flag": wash_flag,
        "taker_available": venue_final == "binance",
    }

# Save full output
result = {
    "run_date": "2026-08-17",
    "store": store_results,
    "venue_discovery": venue_results,
    "wash": wash_results,
    "apr_dex": apr_data,
    "summary": summary,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\nFull output: {OUT}")
print("[DONE S-0→S-3]")

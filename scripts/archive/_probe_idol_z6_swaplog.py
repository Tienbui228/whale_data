#!/usr/bin/env python3
"""Z6: PancakeSwap IDOL swap log 20/07→02/08.
Pool: IDOL/WBNB 0.01% BSC (GeckoTerminal confirmed, vol24h 03/08 ≈ $6.67M).
Nguồn: GeckoTerminal pool address → subgraph (GraphQL) / BscScan getLogs fallback.
Output: daily buy vol (IDOL + USD) + VWAP mua; cumulative buy curve vs 273M.
CAVEAT: taker = ví omnibus Binance — không tách user.
"""
import sys, io, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone as tz, timedelta

WHALE    = Path(r"D:\Data back test\whale_data")
OUT      = WHALE / "docs" / "reports" / "_probe_idol_z6_swaplog.txt"
CONTRACT = "0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07"   # IDOL token BSC
WBNB     = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"    # WBNB BSC

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def fetch(url, headers=None, timeout=15, method="GET", body=None):
    h = {"Accept": "application/json",
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if headers: h.update(headers)
    data_bytes = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, headers=h, method=method, data=data_bytes)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:    return json.loads(raw), r.status
            except: return raw.decode(errors="replace")[:400], r.status
    except urllib.error.HTTPError as e:
        try:    body_e = e.read().decode(errors="replace")[:200]
        except: body_e = ""
        return body_e, e.code
    except Exception as ex:
        return None, str(ex)

emit("=" * 75)
emit("PROBE idol_z6_swaplog —", datetime.now(tz.utc).strftime("%Y-%m-%d %H:%M UTC"))
emit(f"IDOL contract: {CONTRACT}")
emit("=" * 75)

WIN_START = datetime(2026, 7, 20, tzinfo=tz.utc)
WIN_END   = datetime(2026, 8, 3, tzinfo=tz.utc)   # exclusive (03/08 00:00)
start_ts  = int(WIN_START.timestamp())
end_ts    = int(WIN_END.timestamp())

# ── 1. Get full pool address ──────────────────────────────────────────────────
emit("\n[1] GeckoTerminal — pool address IDOL/WBNB:")
POOL_ADDRESS = None

gt_pools, s = fetch(
    f"https://api.geckoterminal.com/api/v2/networks/bsc/tokens/{CONTRACT}/pools?page=1",
    headers={"Accept": "application/json;version=20230302"})
if s == 200 and isinstance(gt_pools, dict):
    for p in gt_pools.get("data", []):
        attrs = p.get("attributes", {})
        pool_id = p.get("id","")  # format: "bsc_0x..."
        addr = pool_id.split("_")[-1] if "_" in pool_id else pool_id
        name  = attrs.get("name","")
        vol24 = attrs.get("volume_usd",{}).get("h24",0)
        emit(f"  {name!r:30}  addr={addr}  vol24h=${float(vol24 or 0):,.0f}")
        if "IDOL / WBNB" in name and "0.01%" in name and POOL_ADDRESS is None:
            POOL_ADDRESS = addr
            emit(f"  → POOL SELECTED: {POOL_ADDRESS}")
else:
    emit(f"  GeckoTerminal pools: status={s}")

if not POOL_ADDRESS:
    emit("  FALLBACK: sử dụng pool đã biết từ probe trước (address kết thúc 5fabca5559)")
    emit("  CẦN full address — skip BscScan getLogs, dùng subgraph với token address")

time.sleep(0.8)

# ── 2. Subgraph — swap events by pool ─────────────────────────────────────────
emit("\n[2] Subgraph GraphQL — swap events 20/07→02/08:")
swap_daily = {}   # {date_str: {buy_idol, sell_idol, buy_usd, sell_usd, n_buy, n_sell}}

SUBGRAPH_ENDPOINTS = [
    # Pancakeswap V3 BSC via various providers
    ("https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-bsc", "thegraph_v3"),
    ("https://api.goldsky.com/api/public/project_cl2rg5pp47j3t0ztlr3uf7wr/subgraphs/pancakeswap-v3-bsc/latest/gn", "goldsky_v3"),
    ("https://graph.pancakeswap.finance/v3/bsc", "pancake_official"),
]

# Query: swaps for IDOL token in the time window, batch by day
def make_gql_swaps(pool_addr_lower, ts_from, ts_to, skip=0):
    pool_filter = (f'pool: "{pool_addr_lower}",' if pool_addr_lower
                   else f'token0: "{CONTRACT}"')
    return json.dumps({"query": f"""{{
  swaps(
    first: 1000
    skip: {skip}
    orderBy: timestamp
    orderDirection: asc
    where: {{
      {pool_filter}
      timestamp_gte: {ts_from}
      timestamp_lte: {ts_to}
    }}
  ) {{
    timestamp
    amount0
    amount1
    amountUSD
    sqrtPriceX96
  }}
}}"""})

def make_gql_swaps_by_token(ts_from, ts_to, skip=0):
    """Fallback: query by token when pool address unknown."""
    return json.dumps({"query": f"""{{
  swaps(
    first: 1000
    skip: {skip}
    orderBy: timestamp
    orderDirection: asc
    where: {{
      token0: "{CONTRACT}"
      timestamp_gte: {ts_from}
      timestamp_lte: {ts_to}
    }}
  ) {{
    timestamp
    amount0
    amount1
    amountUSD
    pool {{ id }}
  }}
}}"""})

working_endpoint = None
for ep_url, ep_name in SUBGRAPH_ENDPOINTS:
    emit(f"\n  [{ep_name}] {ep_url[:60]}...")
    # First try a simple query to check connectivity
    test_q = json.dumps({"query": "{ _meta { block { number } } }"})
    d_test, s_test = fetch(ep_url, headers={"Content-Type": "application/json"},
                           method="POST", body=test_q, timeout=10)
    emit(f"    meta query: status={s_test}")
    if s_test == 200 and isinstance(d_test, dict):
        if "data" in d_test:
            block_num = d_test.get("data",{}).get("_meta",{}).get("block",{}).get("number","?")
            emit(f"    → ENDPOINT LIVE, latest block={block_num}")
            working_endpoint = (ep_url, ep_name)
            break
        else:
            emit(f"    Response: {str(d_test)[:100]}")
    elif isinstance(d_test, str):
        emit(f"    Response: {d_test[:100]}")
    time.sleep(0.5)

if working_endpoint:
    ep_url, ep_name = working_endpoint
    emit(f"\n  Fetching swaps via {ep_name}...")
    pool_lower = POOL_ADDRESS.lower() if POOL_ADDRESS else None

    # Fetch in daily chunks to avoid timeout / result size limits
    all_swaps = []
    day = WIN_START
    while day < WIN_END:
        day_end = day + timedelta(days=1)
        ts_from = int(day.timestamp())
        ts_to   = int(day_end.timestamp()) - 1

        skip = 0
        day_swaps = []
        while True:
            gql = (make_gql_swaps(pool_lower, ts_from, ts_to, skip) if pool_lower
                   else make_gql_swaps_by_token(ts_from, ts_to, skip))
            d, s = fetch(ep_url, headers={"Content-Type": "application/json"},
                         method="POST", body=gql, timeout=20)
            if s != 200 or not isinstance(d, dict):
                emit(f"    {day.strftime('%Y-%m-%d')}: status={s}")
                break
            swaps = d.get("data", {}).get("swaps", [])
            day_swaps.extend(swaps)
            if len(swaps) < 1000:
                break
            skip += 1000
            time.sleep(0.3)

        # Aggregate
        d_str = day.strftime("%Y-%m-%d")
        buy_idol = sell_idol = buy_usd = sell_usd = n_buy = n_sell = 0.0
        for sw in day_swaps:
            a0 = float(sw.get("amount0",0))   # IDOL (token0)
            a1 = float(sw.get("amount1",0))   # WBNB (token1)
            usd= float(sw.get("amountUSD",0) or 0)
            if a0 < 0:   # IDOL exits pool = BUY
                buy_idol  += abs(a0)
                buy_usd   += usd
                n_buy     += 1
            else:        # IDOL enters pool = SELL
                sell_idol += a0
                sell_usd  += usd
                n_sell    += 1

        swap_daily[d_str] = {
            "buy_idol": buy_idol, "sell_idol": sell_idol,
            "buy_usd": buy_usd, "sell_usd": sell_usd,
            "n_buy": n_buy, "n_sell": n_sell,
            "total": len(day_swaps)
        }
        if day_swaps:
            vwap_buy = buy_usd / buy_idol if buy_idol > 0 else 0
            emit(f"    {d_str}: {len(day_swaps):>5} swaps | buy={buy_idol/1e6:.2f}M IDOL "
                 f"${buy_usd/1e6:.3f}M | vwap_buy={vwap_buy:.6f}")
        else:
            emit(f"    {d_str}: 0 swaps")
        day += timedelta(days=1)
        time.sleep(0.2)

else:
    emit("\n  Tất cả subgraph endpoints KHÔNG ACCESSIBLE (network/DNS)")

# ── 3. BscScan getLogs fallback ───────────────────────────────────────────────
if not swap_daily and POOL_ADDRESS:
    emit("\n[3] BscScan getLogs fallback (Swap events):")
    # PancakeSwap V3 Swap topic
    SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

    # Get block numbers for date range
    def get_block(ts):
        url = (f"https://api.bscscan.com/api?module=block&action=getblocknobytime"
               f"&timestamp={ts}&closest=before")
        d, s = fetch(url)
        if s == 200 and isinstance(d, dict) and d.get("status") == "1":
            return int(d.get("result", 0))
        return None

    emit("  Getting block numbers for window...")
    blk_start = get_block(start_ts)
    blk_end   = get_block(end_ts)
    emit(f"  Block range: {blk_start} → {blk_end}")
    time.sleep(0.5)

    if blk_start and blk_end:
        # BscScan BSC ~3 sec/block → 14 days = ~400K blocks
        # getLogs max offset=10000 — need pagination
        # Use daily chunks
        day = WIN_START
        while day < WIN_END:
            day_end = day + timedelta(days=1)
            blk_from = get_block(int(day.timestamp()))
            blk_to   = get_block(int(day_end.timestamp()) - 1)
            time.sleep(0.3)

            if not blk_from or not blk_to:
                day += timedelta(days=1)
                continue

            d_str = day.strftime("%Y-%m-%d")
            url = (f"https://api.bscscan.com/api?module=logs&action=getLogs"
                   f"&address={POOL_ADDRESS}&topic0={SWAP_TOPIC}"
                   f"&fromBlock={blk_from}&toBlock={blk_to}&page=1&offset=1000")
            data, status = fetch(url)
            if status == 200 and isinstance(data, dict) and data.get("status") == "1":
                logs = data.get("result", [])
                emit(f"  {d_str}: {len(logs)} swap logs (may be truncated at 1000)")
                # Parse: data field = abi.encode(amount0, amount1, sqrtPriceX96, liquidity, tick)
                # First 64 chars = amount0 (int256), next 64 = amount1 (int256) — two's complement
                buy_idol = sell_idol = buy_usd = 0.0
                for log in logs:
                    data_hex = log.get("data","")[2:]  # strip 0x
                    if len(data_hex) < 128: continue
                    a0_hex = data_hex[0:64]; a1_hex = data_hex[64:128]
                    a0 = int(a0_hex, 16)
                    if a0 >= (1 << 255): a0 -= (1 << 256)  # two's complement
                    if a0 < 0:
                        buy_idol += abs(a0) / 1e18  # IDOL decimals = 18
                    else:
                        sell_idol += a0 / 1e18
                swap_daily[d_str] = {
                    "buy_idol": buy_idol, "sell_idol": sell_idol,
                    "n_buy": sum(1 for _ in logs), "total": len(logs)
                }
                emit(f"    buy={buy_idol:.2f}M IDOL (/{1e6:.0f}) | sell={sell_idol:.2f}M IDOL")
            else:
                emit(f"  {d_str}: status={status} {str(data)[:80]}")
            day += timedelta(days=1)
            time.sleep(0.5)

# ── 4. Tổng hợp kết quả ───────────────────────────────────────────────────────
emit("\n" + "=" * 75)
emit("KẾT QUẢ Z6 — Daily buy/sell + VWAP + cumulative")
emit("=" * 75)

# DEX daily vol từ GeckoTerminal (tổng, đã có từ A3 — dùng làm reference)
GT_VOL = {
    "2026-07-20": 1_531_800, "2026-07-21": 563_300, "2026-07-22": 454_300,
    "2026-07-23": 18_683_300,"2026-07-24": 4_809_300,"2026-07-25": 1_380_400,
    "2026-07-26": 641_900,   "2026-07-27": 9_834_000,"2026-07-28": 1_770_600,
    "2026-07-29": 1_126_900, "2026-07-30": 1_024_700,"2026-07-31": 1_434_500,
    "2026-08-01": 31_831_100,"2026-08-02": 7_319_100,
}
# DEX daily price (GeckoTerminal close)
GT_PX = {
    "2026-07-20": 0.015170,"2026-07-21": 0.014865,"2026-07-22": 0.015374,
    "2026-07-23": 0.015483,"2026-07-24": 0.015112,"2026-07-25": 0.014991,
    "2026-07-26": 0.014918,"2026-07-27": 0.017212,"2026-07-28": 0.016523,
    "2026-07-29": 0.015196,"2026-07-30": 0.015030,"2026-07-31": 0.016480,
    "2026-08-01": 0.024383,"2026-08-02": 0.023193,
}

if swap_daily:
    emit(f"\n  {'date':<12} {'buy_IDOL_M':>11} {'buy_USD_M':>10} {'sell_IDOL_M':>12} "
         f"{'vwap_buy':>10} {'n_swaps':>8}")
    emit("  " + "-" * 70)
    cum_buy_idol = 0.0
    cum_buy_usd  = 0.0
    for d in sorted(swap_daily):
        row = swap_daily[d]
        bi = row.get("buy_idol", 0)
        bu = row.get("buy_usd", 0)
        si = row.get("sell_idol", 0)
        n  = row.get("total", 0)
        vwap = bu / bi if bi > 0 else 0
        cum_buy_idol += bi
        cum_buy_usd  += bu
        flag = ""
        if bi >= 20e6: flag = "  ← BIG BUY"
        emit(f"  {d:<12} {bi/1e6:>11.3f}M {bu/1e6:>10.4f}M {si/1e6:>12.3f}M "
             f"{vwap:>10.6f} {n:>8}{flag}")

    emit(f"\n  Cumulative buy:  {cum_buy_idol/1e6:.3f}M IDOL = ${cum_buy_usd/1e6:.3f}M")
    avg_vwap = cum_buy_usd / cum_buy_idol if cum_buy_idol > 0 else 0
    emit(f"  VWAP buy (14d): ${avg_vwap:.6f}/IDOL")
    emit(f"\n  Đối chiếu 273M IDOL:")
    emit(f"  Cum buy {cum_buy_idol/1e6:.1f}M IDOL vs 273M (rút) → "
         f"{'ĐỦ' if cum_buy_idol >= 273e6 else f'THIẾU (cần {(273e6-cum_buy_idol)/1e6:.1f}M nữa)'}")
    emit(f"  Cost basis ước tính (nếu MM mua qua pool): VWAP ${avg_vwap:.6f}")
    emit(f"  Current px 02/08 close = {GT_PX.get('2026-08-02',0):.6f}")
    if avg_vwap > 0:
        pnl_pct = (GT_PX.get("2026-08-02",0) / avg_vwap - 1) * 100
        emit(f"  PnL estimate (02/08 close vs VWAP): {pnl_pct:+.1f}%")

else:
    emit("\n  Không lấy được swap log data — sử dụng GeckoTerminal daily vol làm proxy.")
    emit("\n  PROXY ESTIMATE (50/50 buy/sell split — KHÔNG CHÍNH XÁC):")
    emit(f"\n  {'date':<12} {'total_DEX_M':>12} {'est_buy_M':>10} {'px_close':>10} {'cum_buy_M':>12}")
    emit("  " + "-" * 60)
    cum_buy_idol = 0.0
    cum_buy_usd  = 0.0
    for d in sorted(GT_VOL):
        total_usd = GT_VOL[d]
        px = GT_PX.get(d, 0)
        total_idol = total_usd / px if px > 0 else 0
        # Assume 50/50: buy ≈ half of total IDOL volume
        est_buy_idol = total_idol * 0.5
        est_buy_usd  = total_usd * 0.5
        cum_buy_idol += est_buy_idol
        cum_buy_usd  += est_buy_usd
        emit(f"  {d:<12} {total_usd/1e6:>12.4f}M {est_buy_idol/1e6:>10.3f}M "
             f"{px:>10.6f} {cum_buy_idol/1e6:>12.3f}M")

    cum_vwap = cum_buy_usd / cum_buy_idol if cum_buy_idol > 0 else 0
    emit(f"\n  Cumulative buy est: {cum_buy_idol/1e6:.2f}M IDOL = ${cum_buy_usd/1e6:.2f}M")
    emit(f"  VWAP est: ${cum_vwap:.6f} (proxy, 50/50 split)")
    emit(f"  273M benchmark: cum_buy {cum_buy_idol/1e6:.1f}M → "
         f"{'ĐỦ (>273M)' if cum_buy_idol >= 273e6 else f'THIẾU ({(273e6-cum_buy_idol)/1e6:.1f}M gap)'}")
    emit("\n  CAVEAT PROXY: 50/50 split là giả định. Thực tế cần swap log để phân tách.")

emit("\n" + "=" * 75)
emit("CAVEAT — Taker = Binance omnibus:")
emit("  Swap events trên PancakeSwap BSC: caller là ví người dùng thực hoặc")
emit("  aggregator (1inch/ParaSwap). KHÔNG có ví Binance omnibus trong pool DEX.")
emit("  Nguyên nhân: Binance cầm IDOL on-chain trong ví custody riêng, không phải")
emit("  qua pool AMM trực tiếp. Người dùng mua/bán IDOL trên Binance bằng internal")
emit("  book — không tạo on-chain swap event.")
emit("  → Pool DEX swaps = thị trường OTC/DeFi, KHÔNG phản ánh Binance user orders.")
emit("  → VWAP từ pool ≠ Binance internal VWAP của 273M block.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

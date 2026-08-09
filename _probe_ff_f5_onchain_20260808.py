"""
_probe_ff_f5_onchain_20260808.py
F-5: Spot + Alpha + On-chain (contract, supply, holders, BscScan, depth).
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260808"
SYM = "FFUSDT"
SYM_B = "FF"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-5 ON-CHAIN  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_get(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

# ── Load cached BAPI ───────────────────────────────────────────────────────────
bapi_path = SCRATCH / f"ff_bapi_{DATE_TAG}.json"
bapi = json.loads(bapi_path.read_text(encoding="utf-8")) if bapi_path.exists() else {}

# ── X-5a: BAPI + alpha_id_map cross-check ─────────────────────────────────────
log("\n=== X-5a: BAPI ALPHA VERIFY ===")
am_path = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_map = json.loads(am_path.read_text(encoding="utf-8")) if am_path.exists() else {}
map_id = alpha_map.get(SYM_B, "NOT_IN_MAP")
ALPHA_ID = "ALPHA_398"
CONTRACT = "0xac23b90a79504865d52b49b327328411a23d4db2"

log(f"  alpha_id_map: FF → {map_id}")
log(f"  Expected ALPHA_ID: {ALPHA_ID}")
log(f"  Expected contract: {CONTRACT}")

if bapi:
    log(f"\n  BAPI data found:")
    log(f"    alphaId:         {bapi.get('alphaId','?')}")
    log(f"    tokenSymbol:     {bapi.get('tokenSymbol','?')}")
    log(f"    contractAddress: {bapi.get('contractAddress','?')}")
    log(f"    totalSupply:     {bapi.get('totalSupply','?')}")
    log(f"    holders:         {bapi.get('holders','?')}")
    log(f"    fullyDelisted:   {bapi.get('fullyDelisted','?')}")
    log(f"    offsell:         {bapi.get('offsell','?')}")
    log(f"    offline:         {bapi.get('offline','?')}")

    bapi_contract = bapi.get("contractAddress","?")
    id_match = bapi.get("alphaId","?") == ALPHA_ID or map_id == ALPHA_ID
    contract_match = bapi_contract.lower() == CONTRACT.lower()
    log(f"\n  alpha_id match: {'PASS' if id_match else 'MISMATCH'} (map={map_id}, bapi={bapi.get('alphaId')})")
    log(f"  contract match: {'PASS' if contract_match else 'MISMATCH'} (bapi={bapi_contract})")
    log(f"  fullyDelisted: {bapi.get('fullyDelisted')} — ALPHA_398 DELISTED FROM BINANCE ALPHA")
    log(f"  → Flag: DELISTED ALPHA — perp còn TRADING nhưng alpha program kết thúc")
else:
    log("  BAPI: không tìm thấy FF trong cache (xem f2 collect)")

# ── X-5b: BscScan 0-credit ────────────────────────────────────────────────────
log("\n=== X-5b: BscScan TOKEN INFO ===")
url_bsc = f"https://api.bscscan.com/api?module=token&action=tokeninfo&contractaddress={CONTRACT}&apikey=YourApiKeyToken"
bsc, err = safe_get(url_bsc)
if err:
    log(f"  BscScan error: {err[:80]}")
elif bsc:
    log(f"  status={bsc.get('status','?')} message={bsc.get('message','?')}")
    result = bsc.get("result","?")
    if bsc.get("status")=="1" and isinstance(result, list) and result:
        log(f"  Token info: {result[0]}")
    else:
        log(f"  NOTOK (no free key or deprecated)")

# BSC balance check (exchange hot wallets)
log("\n=== X-5b2: BscScan EXCHANGE BALANCE (spot check) ===")
log("  Câu hỏi F-0 audit: withdrawal cùng cửa sổ build (08-01→08-07)?")
log("  Binance BSC hot: 0x28C6c06298d514Db089934071355E5743bf21d60")
log("  Gate BSC: 0x0D0707963952f2fBA59dD06f2b425ace40b492Fe")
for label, addr in [("Binance BSC hot", "0x28C6c06298d514Db089934071355E5743bf21d60"),
                    ("Gate BSC", "0x0D0707963952f2fBA59dD06f2b425ace40b492Fe")]:
    url_bal = (f"https://api.bscscan.com/api?module=account&action=tokenbalance"
               f"&contractaddress={CONTRACT}&address={addr}&tag=latest&apikey=YourApiKeyToken")
    bal, err = safe_get(url_bal)
    if err:
        log(f"  {label}: ERROR {err[:60]}")
    elif bal:
        st = bal.get("status","?")
        res = bal.get("result","?")
        if st == "1":
            try:
                bal_tokens = float(res) / 1e18
                log(f"  {label}: {bal_tokens:,.0f} FF tokens")
            except:
                log(f"  {label}: {res}")
        else:
            log(f"  {label}: NOTOK status={st} msg={bal.get('message','?')}")

# ── X-5c: Operator checklist ──────────────────────────────────────────────────
log("\n=== X-5c: OPERATOR CHECKLIST ===")
log()
log("  1. DELISTED ALPHA FLAG")
log("     BAPI: fullyDelisted=True (ALPHA_398). Xác nhận:")
log("     (a) Ngày alpha program kết thúc? (check BAPI listingTime + delistDate)")
log("     (b) Tại sao FFUSDT perp còn TRADING dù alpha delisted?")
log("     (c) Có unlock event nào liên quan listing/delisting không?")
log("     Vì sao: delisted alpha thường = team không còn vesting => rủi ro dump thấp hơn,")
log("             nhưng cũng = liquidity retail giảm (ít người biết dự án).")
log()
log("  2. CONTRACT TRÊN BSC")
log(f"     Contract: {CONTRACT}")
log("     BscScan: token holders tab → top 10 holders → ai là holder lớn nhất?")
log("     Câu hỏi: Có whale wallet tích lũy trong cửa sổ 08-01→08-07 không?")
log()
log("  3. SPOT PAIR FFUSDT EXISTS")
log("     FF có spot pair (FFUSDT spot TRADING trên Binance).")
log("     Hỏi: Vol spot vs vol perp trong cửa sổ build?")
log("     Nếu spot vol >> perp vol → retail có thể gom qua spot thay perp.")
log("     Nếu perp vol >> spot vol → accumulation thiên về perp (institutional?).")
log()
log("  4. FUNDING ANALYSIS")
log("     500 records tất cả POSITIVE (min=0.000050, max=0.000119).")
log("     KHÔNG có funding âm = crowd KHÔNG reverse hoàn toàn.")
log("     Hỏi: Funding có tăng lên trong cửa sổ build (bull signal)?")
log("     Hay funding thấp flat (neutral)?")
log()
log("  5. NANSEN (LOCKED)")
log("     CẦN OPERATOR: on-chain wallet classification.")
log("     (a) Smart Money wallets đang hold FF không?")
log("     (b) Exchange flow net = deposit hay withdrawal (08-01→08-07)?")

# ── X-5d: Check UNLOCK sheet if exists ─────────────────────────────────────────
log("\n=== X-5d: UNLOCK SHEET ===")
log("  CASE_FF.xlsx chưa tồn tại — UNLOCK sheet sẽ được điền sau khi build.")
log("  Câu hỏi cần điền: có vesting contract FF trên BSC không?")

# ── X-5e: Depth snap #1 ───────────────────────────────────────────────────────
log("\n=== X-5e: DEPTH SNAP #1 ===")
BASE_FAPI = "https://fapi.binance.com"
url_book = f"{BASE_FAPI}/fapi/v1/depth?symbol={SYM}&limit=1000"
snap1_time = NOW_UTC
try:
    req = urllib.request.Request(url_book, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        book = json.loads(r.read())
    bids = [(float(p), float(q)) for p,q in book.get("bids",[])]
    asks = [(float(p), float(q)) for p,q in book.get("asks",[])]
    log(f"  Order book: {len(bids)} bids, {len(asks)} asks")

    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    mid = (best_bid + best_ask) / 2
    bid2_usd = sum(p*q for p,q in bids if p >= mid*0.98)
    ask2_usd = sum(p*q for p,q in asks if p <= mid*1.02)
    depth_ratio = bid2_usd/ask2_usd if ask2_usd > 0 else None

    bid5 = [(p,q,p*q) for p,q in bids if p >= mid*0.95]
    ask5 = [(p,q,p*q) for p,q in asks if p <= mid*1.05]
    bid_wall = max(bid5, key=lambda x:x[2]) if bid5 else (None,None,None)
    ask_wall = max(ask5, key=lambda x:x[2]) if ask5 else (None,None,None)

    log(f"\n  ── DEPTH ±2% SNAP #1 ──")
    log(f"  Time:        {snap1_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"  Mid:         {mid:.8f}")
    log(f"  Bid ±2%:    ${bid2_usd:,.0f}")
    log(f"  Ask ±2%:    ${ask2_usd:,.0f}")
    log(f"  Ratio (bid/ask): {depth_ratio:.4f}" if depth_ratio else "  Ratio: N/A")
    log(f"  Bid wall: px={bid_wall[0]}, usd=${bid_wall[2]:,.0f}" if bid_wall[0] else "  Bid wall: N/A")
    log(f"  Ask wall: px={ask_wall[0]}, usd=${ask_wall[2]:,.0f}" if ask_wall[0] else "  Ask wall: N/A")

    snap1 = {
        "sym": SYM, "snap_time": snap1_time.isoformat(), "snap_label": "snap1",
        "mid": mid, "best_bid": best_bid, "best_ask": best_ask,
        "bid2pct_usd": round(bid2_usd, 0), "ask2pct_usd": round(ask2_usd, 0),
        "depth_ratio": round(depth_ratio, 4) if depth_ratio else None,
        "bid_wall_px": bid_wall[0], "bid_wall_usd": round(bid_wall[2],0) if bid_wall[2] else None,
        "ask_wall_px": ask_wall[0], "ask_wall_usd": round(ask_wall[2],0) if ask_wall[2] else None,
    }
    snap1_path = SCRATCH / f"ff_depth_snap1_{DATE_TAG}.json"
    snap1_path.write_text(json.dumps(snap1, indent=2), encoding="utf-8")
    log(f"\n  Saved: {snap1_path.name}")
    log(f"  → Snap #2 cần ≥ {snap1_time.strftime('%H:%M')} + 4h = "
        f"{datetime.fromtimestamp(snap1_time.timestamp()+4*3600, tz=timezone.utc).strftime('%H:%M')} UTC")

except Exception as e:
    log(f"  Depth snap ERROR: {e}")

log("\n[F-5 DONE]")

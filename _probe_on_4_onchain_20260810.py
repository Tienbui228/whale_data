"""
_probe_on_4_onchain_20260810.py
N-4: On-chain — contract address, BscScan top holders, exchange balance check.
ONUSDT = ALPHA_444. Nansen LOCKED → CẦN OPERATOR.
data-source: bapi alpha token list + BscScan free API
machine: local scratch
date: 2026-08-10
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
ALPHA_ID = "ALPHA_444"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-4 ON-CHAIN ONUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  data-source: bapi.binance.com alpha token list + BscScan free API")
log(f"  machine: local scratch {SCRATCH}")
log(f"  NANSEN: LOCKED → CẦN OPERATOR for on-chain cluster analysis")

def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

# ── 1. Get contract address from alpha token list ─────────────────────────────
log("\n=== 1. Contract address (ALPHA_444 / ON) ===")
ALPHA_LIST_URL = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
token_list = fetch_json(ALPHA_LIST_URL)
contract_addr = None
token_meta = {}

if token_list:
    items = token_list.get("data", [])
    log(f"  Alpha token list: {len(items)} tokens")
    for item in items:
        sym = (item.get("symbol") or item.get("tokenSymbol") or "").upper()
        aid = item.get("alphaId") or item.get("id") or ""
        if sym == "ON" or str(aid) == "444" or "ALPHA_444" in str(aid):
            contract_addr = (item.get("contractAddress") or item.get("address") or
                             item.get("tokenAddress") or "")
            token_meta = item
            log(f"  FOUND: sym={sym} id={aid} contract={contract_addr}")
            log(f"  Full meta: {json.dumps(item, ensure_ascii=False)[:400]}")
            break
    if not contract_addr:
        # try numeric id 444
        for item in items:
            aid = str(item.get("alphaId") or item.get("id") or "")
            if aid == "444":
                contract_addr = (item.get("contractAddress") or item.get("address") or
                                 item.get("tokenAddress") or "")
                token_meta = item
                log(f"  FOUND by id=444: contract={contract_addr}")
                break
    if not contract_addr:
        log(f"  NOT FOUND in token list. Will try BscScan search.")
else:
    log(f"  alpha token list fetch failed")

# Save token meta
out_meta = SCRATCH / f"{SYM_LOWER}_token_meta_{DATE_TAG}.json"
with open(out_meta, "w", encoding="utf-8") as f:
    json.dump({"alpha_id": ALPHA_ID, "contract": contract_addr, "meta": token_meta}, f, ensure_ascii=False, indent=2)
log(f"  Saved: {out_meta.name}")

# ── 2. BscScan top holders ─────────────────────────────────────────────────────
log("\n=== 2. BscScan top holders ===")
BSCSCAN_API = "https://api.bscscan.com/api"

if contract_addr:
    log(f"  Contract: {contract_addr}")
    # BscScan free: token holder list (no key required for basic, but rate-limited)
    # endpoint: ?module=token&action=tokenholderlist&contractaddress=X&page=1&offset=20
    url_holders = (f"{BSCSCAN_API}?module=token&action=tokenholderlist"
                   f"&contractaddress={contract_addr}&page=1&offset=20")
    holders_resp = fetch_json(url_holders)
    if holders_resp:
        status = holders_resp.get("status"); msg = holders_resp.get("message","")
        log(f"  BscScan holders: status={status} msg={msg}")
        result = holders_resp.get("result", [])
        if isinstance(result, list) and result:
            log(f"  Top {len(result)} holders:")
            for i, h in enumerate(result[:20]):
                addr = h.get("TokenHolderAddress","")
                qty = h.get("TokenHolderQuantity","")
                log(f"    #{i+1}: {addr}  qty={qty}")
            out_h = SCRATCH / f"{SYM_LOWER}_holders_{DATE_TAG}.csv"
            with open(out_h, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["rank","address","quantity"])
                w.writeheader()
                for i, h in enumerate(result[:20]):
                    w.writerow({"rank": i+1,
                                "address": h.get("TokenHolderAddress",""),
                                "quantity": h.get("TokenHolderQuantity","")})
            log(f"  Saved: {out_h.name}")
        else:
            log(f"  No holder data (may need API key or rate limit): {str(result)[:200]}")

    # Token supply info
    url_supply = f"{BSCSCAN_API}?module=stats&action=tokensupply&contractaddress={contract_addr}"
    supply_resp = fetch_json(url_supply)
    if supply_resp and supply_resp.get("status") == "1":
        supply = supply_resp.get("result","")
        log(f"\n  Total supply: {supply}")

    # Transfer events last 30d (large txns from BscScan tokentx — free but limited)
    log(f"\n  BscScan tokentx (transfers, last 30 rows):")
    url_tx = (f"{BSCSCAN_API}?module=account&action=tokentx"
              f"&contractaddress={contract_addr}&page=1&offset=30&sort=desc")
    tx_resp = fetch_json(url_tx)
    if tx_resp:
        status_tx = tx_resp.get("status"); result_tx = tx_resp.get("result",[])
        log(f"  status={status_tx} count={len(result_tx) if isinstance(result_tx,list) else result_tx}")
        if isinstance(result_tx, list) and result_tx:
            log(f"  Recent transfers (last 5):")
            for tx in result_tx[:5]:
                ts_tx = datetime.fromtimestamp(int(tx.get("timeStamp",0)), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                val = tx.get("value","0")
                dec = int(tx.get("tokenDecimal","18"))
                try: val_f = int(val) / (10**dec)
                except: val_f = 0
                fr = tx.get("from","")[:10]; to = tx.get("to","")[:10]
                log(f"    {ts_tx}: {fr}→{to} qty={val_f:,.2f}")
else:
    log(f"  Contract address not found — skipping BscScan holder lookup")
    log(f"  CẦN OPERATOR: provide contract address for ON token on BSC")

# ── 3. Exchange balance note ───────────────────────────────────────────────────
log("\n=== 3. Exchange balance / CẦN OPERATOR ===")
log("  NANSEN LOCKED (NANSEN_KEY_LOCKED env) → on-chain cluster phân tích = CẦN OPERATOR")
log("  Alternatives checked:")
log("  a) BscScan top holders: listed above (nếu có contract addr)")
log("  b) Exchange balance trend: không có endpoint public → CẦN OPERATOR (Nansen/Dune)")
log("  c) Transfer clustering: CẦN OPERATOR (Nansen)")
log("")
log("  CẦN OPERATOR tasks:")
log("  1. Xác nhận contract address ON (BSC)")
log("  2. Nansen: exchange balance trend 30d — xem có netflow vào sàn không")
log("  3. Nansen/Dune: top 10 holders có phải entity sàn không")
log("  4. BscScan: verify top holders list — compare vs exchanges known addrs")

# ── 4. Alpha store — price/vol check ─────────────────────────────────────────
log("\n=== 4. Alpha store check (ON) ===")
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
alpha_rows = []
try:
    import pandas as pd
    for p in sorted(alpha_store.rglob("*.parquet")):
        try:
            df = pd.read_parquet(p)
            sub = df[df.get("symbol", pd.Series(dtype=str)) == "ON"] if "symbol" in df.columns else pd.DataFrame()
            if len(sub) > 0:
                for _, row in sub.iterrows():
                    d_col = next((c for c in ["date","open_time","ts"] if c in sub.columns), None)
                    d_val = str(row.get(d_col,""))[:10] if d_col else None
                    vol = float(row.get("quote_vol") or row.get("volume") or 0)
                    cl = float(row.get("close") or 0)
                    alpha_rows.append({"date": d_val, "close": cl, "vol_usd": vol})
        except: pass
    alpha_rows.sort(key=lambda x: x["date"] or "")
    log(f"  Alpha rows: {len(alpha_rows)}")
    if alpha_rows:
        log(f"  Range: {alpha_rows[0]['date']} → {alpha_rows[-1]['date']}")
        log(f"  Last 5:")
        for r in alpha_rows[-5:]:
            log(f"    {r['date']}: close={r['close']:.6f} vol=${r['vol_usd']:,.0f}")
except Exception as e:
    log(f"  Alpha store error: {e}")

log(f"\n[N-4 DONE]")

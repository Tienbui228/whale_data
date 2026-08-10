"""
_probe_gua_4_onchain_20260810.py
G-4: On-chain data — GUA/SUPERFORTUNE (BSC).
Contract: 0xa5c8e1513b6a08334b479fe4d71f1253259469be
Source: BscScan public endpoints (no auth). Nansen LOCKED → CẦN OPERATOR.
data-source: api.bscscan.com free endpoints
machine: local
date: 2026-08-10
"""
import sys, io, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_LOWER = "gua"
CONTRACT = "0xa5c8e1513b6a08334b479fe4d71f1253259469be"
BSCSCAN = "https://api.bscscan.com/api"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-4 ON-CHAIN GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  Contract: {CONTRACT} (BSC chainId=56)")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

# ── 1. Token info (BscScan stats endpoint) ────────────────────────────────────
log(f"\n=== 1. Token holder count (BscScan getTokenHolders) ===")
url_holders = f"{BSCSCAN}?module=token&action=tokenholderlist&contractaddress={CONTRACT}&page=1&offset=10"
data = fetch_json(url_holders)
if data:
    status = data.get("status"); msg = data.get("message",""); result = data.get("result",[])
    log(f"  status={status}, message={msg}")
    if isinstance(result, list) and result:
        log(f"  Top 10 holders:")
        for r in result[:10]:
            addr = r.get("TokenHolderAddress",""); qty = r.get("TokenHolderQuantity","")
            try: qty_f = float(qty); qty_s = f"{qty_f:,.0f}"
            except: qty_s = qty
            log(f"    {addr}: {qty_s}")
    elif isinstance(result, str):
        log(f"  result (str): {result[:200]}")
    else:
        log(f"  Empty result or error")
else:
    log(f"  ERROR: no response")

time.sleep(0.5)

# ── 2. Token total supply ─────────────────────────────────────────────────────
log(f"\n=== 2. Token total supply (BscScan tokensupply) ===")
url_supply = f"{BSCSCAN}?module=stats&action=tokensupply&contractaddress={CONTRACT}"
data2 = fetch_json(url_supply)
if data2:
    log(f"  status={data2.get('status')}, message={data2.get('message','')}")
    log(f"  totalSupply: {data2.get('result','N/A')}")

time.sleep(0.5)

# ── 3. Recent transfers (top 5 txns) ─────────────────────────────────────────
log(f"\n=== 3. Recent token transfers (last 5) ===")
url_txns = f"{BSCSCAN}?module=account&action=tokentx&contractaddress={CONTRACT}&page=1&offset=5&sort=desc"
data3 = fetch_json(url_txns)
if data3:
    status3 = data3.get("status"); msg3 = data3.get("message","")
    result3 = data3.get("result",[])
    log(f"  status={status3}, message={msg3}")
    if isinstance(result3, list) and result3:
        log(f"  Last 5 transfers:")
        for r in result3[:5]:
            ts = int(r.get("timeStamp",0))
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            frm = r.get("from","")[:12]; to = r.get("to","")[:12]
            val = r.get("value",""); deci = int(r.get("tokenDecimal","18") or "18")
            try: val_f = float(val) / (10**deci); val_s = f"{val_f:,.2f}"
            except: val_s = val[:20]
            log(f"    {dt}: {frm}→{to} qty={val_s}")
    elif isinstance(result3, str):
        log(f"  result (str): {result3[:200]}")
else:
    log(f"  ERROR: no response")

# ── 4. CẦN OPERATOR notes ─────────────────────────────────────────────────────
log(f"\n=== 4. CẦN OPERATOR (Nansen LOCKED) ===")
log(f"  Nansen: KHÔNG gọi — key LOCKED (CLAUDE.md tầng HUMAN)")
log(f"  Cần operator:")
log(f"    a) Top 50 holders + % supply tập trung — BscScan export CSV")
log(f"    b) Fresh wallet check: có ví <30d tuổi trong top20 không?")
log(f"    c) On-chain flow: BSC inflow/outflow 7d (Nansen required)")
log(f"    d) Cross-ref cụm ví: GUA holders vs ON/BTW/AGT holders?")
log(f"       → contract GUA: {CONTRACT}")
log(f"       → contract ON:  0x0e4f6209ed984b21edea43ace6e09559ed051d48")

# ── 5. Alpha listing context ──────────────────────────────────────────────────
log(f"\n=== 5. Alpha context (from G-0 meta) ===")
bapi_path = SCRATCH / f"{SYM_LOWER}_bapi_{DATE_TAG}.json"
if bapi_path.exists():
    with open(bapi_path, encoding="utf-8") as f:
        bapi = json.load(f)
    log(f"  alphaId: {bapi.get('alphaId')}")
    log(f"  chainId: {bapi.get('chainId')} (BSC)")
    log(f"  totalSupply: {bapi.get('totalSupply')}")
    log(f"  circulatingSupply: {bapi.get('circulatingSupply')}")
    log(f"  fullyDelisted: {bapi.get('fullyDelisted')}")
    log(f"  listingTime: {datetime.fromtimestamp(int(bapi.get('listingTime',0))/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
else:
    log(f"  bapi JSON not found: {bapi_path.name}")

log(f"\n[G-4 DONE]")
log(f"  On-chain: BscScan attempted (rate-limited, no key)")
log(f"  Nansen: LOCKED → CẦN OPERATOR")
log(f"  Fresh-wallet cross-ref: CẦN OPERATOR")

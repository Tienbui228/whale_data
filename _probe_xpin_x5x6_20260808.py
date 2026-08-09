"""
_probe_xpin_x5x6_20260808.py
X-5: On-chain contract verify (BAPI fix) + BscScan + X-6 cross-reference.
"""
import sys, io, json, urllib.request, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")
DATA_DIR = ROOT / "data"
CASE_DIR = ROOT / "docs" / "case_files"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-5/X-6  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

SYM = "XPIN"
PERP = "XPINUSDT"
CONTRACT = "0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6"
ALPHA_ID = "ALPHA_334"
DATE_TAG = "20260808"

def safe_get(url, headers=None, timeout=20):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

# ── X-5a: Contract verify BAPI ────────────────────────────────────────────────
log("\n=== X-5a: BAPI ALPHA CONTRACT VERIFY ===")
bapi_path = SCRATCH / f"xpin_bapi_{DATE_TAG}.json"
if bapi_path.exists():
    log(f"  Using cached {bapi_path.name}")
    bapi = json.loads(bapi_path.read_text(encoding="utf-8"))
else:
    url_tl = ("https://www.binance.com/bapi/defi/v1/public/wallet-direct/"
               "buw/wallet/cex/alpha/all/token/list")
    data, err = safe_get(url_tl)
    if err:
        log(f"  ERROR: {err}")
        bapi = {}
    else:
        # Structure: {"code":"000000","data":[...list of tokens...]}
        raw_list = data.get("data", [])
        if isinstance(raw_list, list):
            tokens = raw_list
        elif isinstance(raw_list, dict):
            tokens = raw_list.get("tokenList", [])
        else:
            tokens = []
        # Find XPIN
        xpin_match = [t for t in tokens
                      if (t.get("tokenSymbol","").upper() == "XPIN"
                          or str(t.get("alphaId","")).upper() == ALPHA_ID
                          or str(t.get("contractAddress","")).lower() == CONTRACT.lower())]
        bapi = xpin_match[0] if xpin_match else {}
        bapi_path.write_text(json.dumps(bapi, indent=2), encoding="utf-8")
        log(f"  Fetched {len(tokens)} tokens, XPIN match: {len(xpin_match)}")

log(f"  BAPI data: {json.dumps(bapi, indent=4) if bapi else 'NOT FOUND'}")

# Cross-check from alpha_id_map
alpha_map_path = DATA_DIR / "config" / "alpha_id_map.json"
if alpha_map_path.exists():
    alpha_map = json.loads(alpha_map_path.read_text(encoding="utf-8"))
    map_id = alpha_map.get("XPIN", "NOT_IN_MAP")
    log(f"\n  alpha_id_map: XPIN → {map_id}")
    match = map_id == ALPHA_ID
    log(f"  Cross-check: {'PASS' if match else 'MISMATCH'} (map={map_id}, case={ALPHA_ID})")

log(f"\n  Contract from CASE: {CONTRACT}")
bapi_contract = bapi.get("contractAddress", "?") if bapi else "?"
log(f"  Contract from BAPI: {bapi_contract}")
if bapi_contract.lower() == CONTRACT.lower():
    log("  CONTRACT VERIFY: PASS (BAPI ✓ alpha_id_map ✓)")
elif bapi_contract == "?":
    log("  CONTRACT VERIFY: PARTIAL (BAPI fail — only CASE/alpha_id_map)")
else:
    log(f"  CONTRACT VERIFY: MISMATCH — CASE={CONTRACT} BAPI={bapi_contract}")

# Supply/holders from BAPI
log(f"\n  Supply (BAPI): totalSupply={bapi.get('totalSupply','?')} circulatingSupply={bapi.get('circulatingSupply','?')}")
log(f"  Holders (BAPI): {bapi.get('holders','?')}")
log(f"  fullyDelisted: {bapi.get('fullyDelisted','?')}")

# ── X-5b: BscScan 0-credit ────────────────────────────────────────────────────
log("\n=== X-5b: BscScan TOKEN INFO ===")
# Try BscScan v2 API (no key needed for public token info)
url_bsc = f"https://api.bscscan.com/api?module=token&action=tokeninfo&contractaddress={CONTRACT}&apikey=YourApiKeyToken"
bsc_data, err = safe_get(url_bsc)
if err:
    log(f"  BscScan API error: {err}")
else:
    status = bsc_data.get("status","?") if bsc_data else "?"
    message = bsc_data.get("message","?") if bsc_data else "?"
    result  = bsc_data.get("result","?") if bsc_data else "?"
    log(f"  status={status} message={message}")
    if status == "1" and isinstance(result, list) and result:
        log(f"  Token info: {json.dumps(result[0], indent=4)}")
    else:
        log(f"  Result: {result}")
        log("  BscScan token info: NOTOK (no free API key or deprecated)")

# Try BscScan holder count (alternative)
url_holders = f"https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress={CONTRACT}&page=1&offset=5&apikey=YourApiKeyToken"
bsc_holders, err = safe_get(url_holders)
if bsc_holders:
    log(f"  Holder count query: status={bsc_holders.get('status','?')} message={bsc_holders.get('message','?')}")
    if bsc_holders.get("status") == "1":
        log(f"  Top holders: {bsc_holders.get('result','[]')[:2]}")

# ── X-5c: Operator checklist ──────────────────────────────────────────────────
log("\n=== X-5c: OPERATOR CHECKLIST ===")
log("  Mỗi mục = câu hỏi cụ thể + vì sao cần:")
log()
log("  1. UNLOCK SCHEDULE")
log("     Hỏi: Team vesting contract trên BSC — có trên BscScan không?")
log("     Contract: 0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6")
log("     Tìm 'internal txns' hoặc 'token transfer' từ địa chỉ vesting.")
log("     Vì sao: unlock event = potential supply shock — invalidates ignition window.")
log("     Nguồn đã thử: CASE_XPIN UNLOCK sheet (9 rows 'PENDING OPERATOR'), BSC API notok.")
log()
log("  2. TOP HOLDERS / KHO WALLET")
log("     Hỏi: Top 10 holders theo BscScan 'Token Holders' tab của contract trên.")
log("     → holder 1 & 2 thường là LP + team kho. Xác nhận:")
log("     (a) Địa chỉ kho wallet của team là gì?")
log("     (b) Kho wallet có di chuyển token từ sau ngày 08/08/2026 không?")
log("     Vì sao: movement từ kho → sàn = tín hiệu phân phối, invalidates WATCH.")
log()
log("  3. EXCHANGE BALANCE TREND (sàn Binance / Gate / KuCoin)")
log("     Hỏi: Số dư token XPIN tại địa chỉ hot wallet Binance/Gate trên BSC — tăng hay giảm?")
log("     Binance BSC hot wallet: 0x28C6c06298d514Db089934071355E5743bf21d60 (BSC)")
log("     Gate BSC: 0x0D0707963952f2fBA59dD06f2b425ace40b492Fe")
log("     So sánh ngày 08/08/2026 vs ngày cuối sổ (08/07/2026):")
log("     (a) Nếu balance tăng → withdrawal-accelerant (crowd distributing)?")
log("     (b) Nếu balance giảm → deposit-lớn rút ra DEX (không phân phối)?")
log("     Vì sao: trend sàn là leading indicator của OI divergence (crowd moved perp-only).")
log()
log("  4. BITMART WASH TRADING")
log("     Hỏi: Vào BitMart XPIN order book live — spread là bao nhiêu?")
log("     (a) Vol $1.61M vs liq $4.8K = 338x ratio → nếu spread >5% = wash confirmed.")
log("     (b) Kiểm tra lịch sử giao dịch: có thành viên thực không?")
log("     Vì sao: xác nhận wash → venue_top = BSC DEX (không phải BitMart). Ảnh hưởng")
log("             detection floor: nếu BitMart thực thì DEX vol nhỏ hơn tổng.")
log()
log("  5. NANSEN (LOCKED): on-chain wallet classification")
log("     Hỏi: (a) Smart Money wallets đang hold XPIN không?")
log("     (b) Exchange flow net (30d) = deposit hay withdrawal?")
log("     Vì sao cần: xác nhận P8 taker_detect — hiện tại ABSTAIN vì no kho_vol_ratio data.")

# ── X-5d: Unlock sheet ───────────────────────────────────────────────────────
log("\n=== X-5d: UNLOCK SHEET ===")
import openpyxl
wb = openpyxl.load_workbook(str(CASE_DIR / "CASE_XPIN.xlsx"), data_only=True)
ws_unlock = wb["UNLOCK"]
for r in ws_unlock.iter_rows(values_only=True):
    if any(v is not None for v in r):
        log(f"  {r}")
wb.close()

# ── X-6: CROSS-REFERENCE ────────────────────────────────────────────────────────
log("\n=== X-6: CROSS-REFERENCE ===")

# 6a: Freshwatch rows for XPIN
log("\n  --- Freshwatch (fw137/fw139) ---")
FW_FILES = [
    SCRATCH / "freshwatch_daily_2026-06.csv",
    SCRATCH / "freshwatch_daily_2026-07.csv",
    VPS_EXPORT / "freshwatch_daily_2026-08.csv",
]
fw_total = 0
for fw in FW_FILES:
    if not fw.exists(): continue
    with open(fw, encoding="utf-8") as f:
        cnt = sum(1 for r in csv.DictReader(f) if r.get("symbol","").upper() == PERP)
    log(f"  {fw.name}: {cnt} XPIN rows")
    fw_total += cnt
log(f"  Total FW rows: {fw_total} ({PERP})")

# 6b: check u50 rows / ledger / gom_scan output
log("\n  --- u50 / universe_master ---")
alpha_map_path = DATA_DIR / "config" / "alpha_id_map.json"
if alpha_map_path.exists():
    am = json.loads(alpha_map_path.read_text(encoding="utf-8"))
    log(f"  alpha_id_map XPIN: {am.get('XPIN','NOT_FOUND')}")
else:
    log("  alpha_id_map not found")

# 6c: Check gom_state for XPIN
gom_state_candidates = [
    VPS_EXPORT.parent / "state" / "gom_state.json",
    VPS_EXPORT.parent.parent / "state" / "gom_state.json",
    Path(r"D:\Check onchain fresh wallets") / "data" / "state" / "gom_state.json",
]
gom_state = None
for gsp in gom_state_candidates:
    if gsp.exists():
        gom_state = json.loads(gsp.read_text(encoding="utf-8"))
        log(f"\n  --- gom_state ({gsp.name}) ---")
        xpin_state = gom_state.get("XPINUSDT", gom_state.get("XPIN", {}))
        log(f"  XPIN state: {json.dumps(xpin_state, indent=4)}")
        break
if not gom_state:
    log("\n  --- gom_state: NOT FOUND in candidate paths ---")

# 6d: Check MM_BOOK / EVENTS in other case files
log("\n  --- EVENTS in other case files (grep XPIN) ---")
for xlsx in CASE_DIR.glob("CASE_*.xlsx"):
    if "XPIN" in xlsx.name: continue
    try:
        wb2 = openpyxl.load_workbook(str(xlsx), data_only=True)
        if "EVENTS" in wb2.sheetnames:
            ws_ev = wb2["EVENTS"]
            for r in range(2, ws_ev.max_row+1):
                for c in range(1, ws_ev.max_column+1):
                    v = str(ws_ev.cell(r,c).value or "")
                    if "XPIN" in v.upper():
                        log(f"  {xlsx.name} EVENTS row {r}: {[ws_ev.cell(r,cc).value for cc in range(1, ws_ev.max_column+1)]}")
                        break
        if "MM_PROFILE" in wb2.sheetnames:
            ws_mm = wb2["MM_PROFILE"]
            for r in range(1, ws_mm.max_row+1):
                for c in range(1, ws_mm.max_column+1):
                    v = str(ws_mm.cell(r,c).value or "")
                    if "XPIN" in v.upper():
                        log(f"  {xlsx.name} MM_PROFILE row {r}: {[ws_mm.cell(r,cc).value for cc in range(1, ws_mm.max_column+1)]}")
                        break
        wb2.close()
    except Exception as e:
        log(f"  {xlsx.name}: ERROR {e}")

# 6e: fresh-wallets log check
log("\n  --- Fresh-wallets log ---")
fw_log_path = Path(r"D:\Check onchain fresh wallets") / "data" / "log"
if fw_log_path.exists():
    logs = sorted(fw_log_path.glob("*.log"))[-3:]
    for logf in logs:
        try:
            content = logf.read_text(encoding="utf-8", errors="replace")
            if "XPIN" in content.upper():
                lines = [l for l in content.splitlines() if "XPIN" in l.upper()]
                log(f"  {logf.name}: {len(lines)} XPIN lines")
                for l in lines[:5]:
                    log(f"    {l}")
            else:
                log(f"  {logf.name}: no XPIN mention")
        except Exception as e:
            log(f"  {logf.name}: ERROR {e}")
else:
    log("  Log path not found")

log("\n[X-5/X-6 DONE]")

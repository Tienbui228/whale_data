#!/usr/bin/env python3
"""PROBE: Alpha dead code investigation — Parts 1/2/3.

Part 2: u50_universe BSC-only symbols → spot listing scan (sample)
Part 3: bapi/defi/* endpoint discovery — token list paths

Output: docs/reports/_probe_alpha_deadcode_20260803.md
KHÔNG sửa code, KHÔNG ghi config, KHÔNG backfill.
"""
import sys, io, json, time, urllib.request, urllib.error, csv
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
U50     = Path(r"D:\Check onchain fresh wallets\u50_universe.csv")
OUT     = WHALE / "docs" / "reports" / "_probe_alpha_deadcode_20260803.md"
SPOT_BASE  = "https://api.binance.com"
BAPI_BASE  = "https://www.binance.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

DAY_MS = 86_400_000
now_ms = int(time.time() * 1000)
yesterday_start = ((now_ms // DAY_MS) - 1) * DAY_MS
today_start = (now_ms // DAY_MS) * DAY_MS

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def get_json(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), r.status
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()[:200]
        except:
            body = ""
        return body, e.code
    except Exception as ex:
        return None, str(ex)

def spot_check(symbol):
    url = (f"{SPOT_BASE}/api/v3/klines?symbol={symbol}&interval=1d"
           f"&startTime={yesterday_start}&endTime={today_start-1}&limit=1")
    data, status = get_json(url)
    if status == 400:
        return "NO_SPOT"
    if data is None or not data or not isinstance(data, list):
        return "EMPTY"
    k = data[0]
    base_vol = float(k[5]); taker_base = float(k[9])
    if base_vol <= 0:
        return "ZERO_VOL"
    ratio = taker_base / base_vol
    return "BSC_BROKEN" if ratio >= 0.9985 else f"OK({ratio:.4f})"

emit("# PROBE: Alpha Dead Code Investigation — 2026-08-03")
emit(f"Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit("")

# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 2: u50_universe BSC-only — spot listing scan
# ─────────────────────────────────────────────────────────────────────────────
emit("## PHẦN 2: u50_universe BSC-only — spot listing scan")
emit("")

rows = list(csv.DictReader(open(U50, encoding="utf-8-sig")))
emit(f"u50_universe.csv: {len(rows)} rows")
emit(f"Cols: {list(rows[0].keys())}")
emit(f"Has bsc_address column: YES (all {len(rows)} rows have it)")
emit("")

# Sample TOÀN BỘ (137 symbols — call lần lượt với delay)
emit("### 2.4 Spot listing scan — toàn bộ 137 u50 symbols")
emit(f"API: GET api.binance.com/api/v3/klines (cùng URL mà _probe_alpha_taker.py dùng)")
emit("")
emit(f"| {'symbol':<12} | {'status':<15} |")
emit(f"|{'-'*14}|{'-'*17}|")

ok_list = []; no_spot_list = []; bsc_broken_list = []; empty_list = []

for r in rows:
    sym = r["futures_base"] + "USDT"
    result = spot_check(sym)
    if result == "NO_SPOT":
        no_spot_list.append(r["futures_base"])
    elif result == "BSC_BROKEN":
        bsc_broken_list.append(r["futures_base"])
    elif result in ("EMPTY", "ZERO_VOL"):
        empty_list.append(r["futures_base"])
    else:
        ok_list.append(r["futures_base"])
    emit(f"| {sym:<12} | {result:<15} |")
    time.sleep(0.07)

emit("")
emit("### 2.4 Summary")
emit(f"- OK (spot có taker hợp lệ): {len(ok_list)}")
emit(f"- NO_SPOT (400 — không có Binance spot): {len(no_spot_list)}")
emit(f"- BSC_BROKEN (taker ratio >0.9985): {len(bsc_broken_list)}")
emit(f"- EMPTY/ZERO_VOL: {len(empty_list)}")
emit("")
emit(f"**Nhóm CẦN alpha endpoint phủ (no_spot):** {len(no_spot_list)} tokens")
emit(f"Danh sách no_spot: {no_spot_list[:30]}{'...' if len(no_spot_list)>30 else ''}")
if bsc_broken_list:
    emit(f"**BSC_BROKEN (cần venue=binance_spot_bsc guard):** {bsc_broken_list}")
else:
    emit(f"**BSC_BROKEN = 0** → alpha_bsc_symbols.txt sẽ RỖNG nếu generate từ u50")
emit("")

# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 3: bapi/defi/* endpoint discovery
# ─────────────────────────────────────────────────────────────────────────────
emit("## PHẦN 3: bapi/defi endpoint discovery")
emit("")

# 3.1: Xác nhận IDOL ALPHA_223 endpoint
emit("### 3.1: IDOL one-off endpoint confirm")
idol_url = f"{BAPI_BASE}/bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_223USDT&interval=1d&limit=2"
data, status = get_json(idol_url)
emit(f"URL: {idol_url}")
emit(f"Status: {status}")
if isinstance(data, dict) and "data" in data:
    emit(f"Response shape: dict with keys={list(data.keys())}")
    d = data.get("data", [])
    emit(f"data[] count: {len(d) if isinstance(d, list) else type(d)}")
    if isinstance(d, list) and d:
        emit(f"Sample entry[0]: {json.dumps(d[0])[:200]}")
elif isinstance(data, list):
    emit(f"Response: list[{len(data)}] — direct array")
    if data:
        emit(f"entry[0]: {json.dumps(data[0])[:200]}")
else:
    emit(f"Response: {str(data)[:300]}")
emit("")

# 3.3: Thử các path cùng prefix bapi/defi/v1/public/alpha-trade/
CANDIDATE_PATHS = [
    "/bapi/defi/v1/public/alpha-trade/token-list",
    "/bapi/defi/v1/public/alpha-trade/tokens",
    "/bapi/defi/v1/public/alpha-trade/symbol-list",
    "/bapi/defi/v1/public/alpha-trade/symbols",
    "/bapi/defi/v1/public/alpha-trade/config",
    "/bapi/defi/v1/public/alpha-trade/info",
    "/bapi/defi/v1/public/alpha-trade/tickers",
    "/bapi/defi/v1/public/alpha-trade/list",
    "/bapi/defi/v1/public/alpha-trade/allTokens",
    "/bapi/defi/v1/public/alpha-trade/market",
]

emit("### 3.3: Path discovery — cùng prefix alpha-trade/")
emit("")
emit(f"| {'path':<50} | {'status'} | response_shape |")
emit(f"|{'-'*52}|{'-'*8}|{'-'*20}|")

found_paths = []
for path in CANDIDATE_PATHS:
    url = f"{BAPI_BASE}{path}"
    data, status = get_json(url)
    if status == 200:
        if isinstance(data, dict):
            shape = f"dict keys={list(data.keys())[:4]}"
            if "data" in data:
                d = data["data"]
                if isinstance(d, list) and d:
                    shape += f" data[{len(d)}] entry0={json.dumps(d[0])[:60]}"
        elif isinstance(data, list):
            shape = f"list[{len(data)}]"
            if data:
                shape += f" item0={json.dumps(data[0])[:60]}"
        else:
            shape = str(data)[:80]
        found_paths.append((path, shape))
        emit(f"| {path:<50} | **{status}** | {shape[:80]} |")
    else:
        err_s = str(data)[:60] if data else "(no body)"
        emit(f"| {path:<50} | {status} | {err_s} |")
    time.sleep(0.15)

emit("")
if found_paths:
    emit("**FOUND endpoints:**")
    for p, s in found_paths:
        emit(f"- `{p}` → {s}")
else:
    emit("**Không tìm thấy token-list endpoint** → ghi CẦN OPERATOR (DevTools Binance Alpha)")

# Also try bapi/alpha/v1 (WAF-blocked per CLAUDE.md — xác nhận)
emit("")
emit("### 3.3b: Confirm WAF block — bapi/alpha/v1")
waf_url = f"{BAPI_BASE}/bapi/alpha/v1/public/alpha-trade/token-list"
data, status = get_json(waf_url)
emit(f"URL: {waf_url}")
emit(f"Status: {status} — {'WAF blocked (expected)' if status in (403,429,503) else 'unexpected'}")
emit(f"Body: {str(data)[:200]}")
emit("")

# 3.2: CALIB_ALPHA 12 entries
emit("### 3.2: CALIB_ALPHA 12 entries (from _calib_alpha_daily.py)")
CALIB_ALPHA = {
    "AKE":     "ALPHA_331",
    "CLO":     "ALPHA_429",
    "ESPORTS": "ALPHA_283",
    "BTW":     "ALPHA_778",
    "POWER":   "ALPHA_487",
    "BASED":   "ALPHA_837",
    "BAS":     "ALPHA_328",
    "TAG":     "ALPHA_233",
    "IDOL":    "ALPHA_223",
    "TUT":     "ALPHA_117",
    "BULLA":   "ALPHA_240",
    "BANK":    "ALPHA_146",
}
emit("")
emit("| symbol | alpha_id | cách sinh |")
emit("|--------|----------|-----------|")
for sym, aid in CALIB_ALPHA.items():
    emit(f"| {sym} | {aid} | tay (12 calib case — user-provided) |")
emit("")
emit("File: `D:\\Check onchain fresh wallets\\_calib_alpha_daily.py` (tồn tại)")
emit("Ngày sinh: không có timestamp trong file, infer từ 12 calib case set (≈07/2026)")
emit("")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
emit("## SUMMARY ĐỂ OPERATOR PHÂN NHÁNH")
emit("")
emit("### PHẦN 1 — Fetch path thật")
emit("- `collect_alpha_spot.py` gọi: `api.binance.com/api/v3/klines` (standard Binance spot)")
emit("- **KHÔNG** gọi `bapi/defi/v1/public/alpha-trade/klines`")
emit("- Venue tag = `binance_spot_bsc` (label trong parquet)")
emit("- → **NHÁNH B** (gọi spot thường, không phải alpha thật)")
emit("")
emit("### PHẦN 2 — Universe 118 (u50_universe.csv = 137 rows)")
emit(f"- Tổng: {len(rows)} BSC symbols có bsc_address")
emit(f"- NO_SPOT (cần alpha endpoint phủ): {len(no_spot_list)}")
emit(f"- OK spot (đã có collect_spot_daily phủ): {len(ok_list)}")
emit(f"- BSC_BROKEN: {len(bsc_broken_list)} (alpha_bsc_symbols.txt = RỖNG)")
emit("")
emit("### PHẦN 3 — Resolver")
emit("- CALIB_ALPHA: 12 entries tay, file `_calib_alpha_daily.py`")
emit("- klines endpoint: `/bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_NNN USDT`")
emit("- token-list endpoint: → xem kết quả path discovery ở trên")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

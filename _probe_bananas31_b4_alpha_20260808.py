"""
_probe_bananas31_b4_alpha_20260808.py
B-4: Alpha store check (ALPHA_21) + alpha klines + depth #2.
"""
import sys, io, json, csv, urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYMBOL = "BANANAS31USDT"
ALPHA_ID = "ALPHA_21"
SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
ALPHA_STORE = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("="*70)
log(f"BANANAS31 B-4 ALPHA  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("="*70)

# ── 1. Alpha store check (local parquet) ──────────────────────────────────────
log("\n--- Alpha store check (local) ---")
alpha_venue_dir = ALPHA_STORE / "venue=binance_alpha"
alpha_sym_dir = None
if alpha_venue_dir.exists():
    # Look for symbol=BANANAS31 or related
    for d in alpha_venue_dir.iterdir():
        if d.is_dir() and "BANANA" in d.name.upper():
            alpha_sym_dir = d
            break
    if not alpha_sym_dir:
        log(f"  BANANAS31 NOT in binance_alpha store (no dir). Dirs available:")
        dirs = list(alpha_venue_dir.iterdir())[:10]
        for d in dirs:
            log(f"    {d.name}")
    else:
        partitions = list(alpha_sym_dir.glob("date=*/"))
        log(f"  Found: {alpha_sym_dir}")
        log(f"  Partitions: {len(partitions)}")
        if partitions:
            dates = sorted(p.name.replace("date=","") for p in partitions)
            log(f"  Date range: {dates[0]} → {dates[-1]}")
else:
    log(f"  Alpha store path not found: {alpha_venue_dir}")

# ── 2. Alpha token list — check status ────────────────────────────────────────
log("\n--- Alpha token status ---")
token_list_url = ("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw"
                  "/wallet/cex/alpha/all/token/list")
raw_list = fetch_json(token_list_url, timeout=30)
banana_status = None
if isinstance(raw_list, dict):
    data = raw_list.get("data", {})
    items = data if isinstance(data, list) else data.get("tokenList", data.get("list", []))
    if not isinstance(items, list):
        # Try different keys
        for key in ["data", "tokenList", "list", "items", "tokens"]:
            if key in raw_list and isinstance(raw_list[key], list):
                items = raw_list[key]; break
    for item in (items if isinstance(items, list) else []):
        name = str(item.get("tokenName","") or item.get("symbol","") or "")
        if "BANANA" in name.upper():
            banana_status = item
            log(f"  Found in token list: {item}")
            break
    if not banana_status:
        log(f"  BANANAS31 NOT found in alpha token list (may be delisted)")
        log(f"  Raw keys: {list(raw_list.keys()) if isinstance(raw_list, dict) else type(raw_list)}")
else:
    log(f"  Token list fetch error: {raw_list}")

# ── 3. Alpha klines via BAPI endpoint ────────────────────────────────────────
log("\n--- Alpha klines (BAPI) ---")
# From alpha_id_map, ALPHA_21 = BANANAS31
# Need to get the numeric alpha id for the kline endpoint
alpha_map_path = Path(r"D:\Data back test\whale_data\data\config\alpha_id_map.json")
alpha_num_id = None
if alpha_map_path.exists():
    try:
        with open(alpha_map_path, encoding="utf-8-sig") as f:
            alpha_map = json.load(f)
        for k, v in alpha_map.items():
            if "BANANA" in k.upper():
                alpha_num_id = v  # e.g. "ALPHA_21"
                break
    except Exception as e:
        log(f"  alpha_map read error: {e}")

# Try to get BANANAS31 recent alpha klines via bapi
# The endpoint uses a token ID number
# From the map: ALPHA_21 → numeric ID 21?
alpha_klines_url = ("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"
                    f"?alphaId=21&interval=1d&limit=30")
alpha_k = fetch_json(alpha_klines_url, timeout=30)
if isinstance(alpha_k, dict) and not alpha_k.get("_error"):
    klines = alpha_k.get("data", alpha_k)
    if isinstance(klines, list) and klines:
        log(f"  Alpha klines (alphaId=21): {len(klines)} rows")
        log(f"  Sample (last 3): vol, open, close per candle")
        for k in klines[-3:]:
            ts = k[0] if k else None
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "?"
            log(f"    {dt}: o={k[1]} c={k[4]} vol_token={k[5]} vol_quote={k[7]}")
        log(f"  TAKER: k[9]={klines[-1][9] if len(klines[-1])>9 else '?'} "
            f"k[5]={klines[-1][5] if len(klines[-1])>5 else '?'} "
            f"→ k[9]==k[5]? {klines[-1][9]==klines[-1][5] if len(klines[-1])>9 else '?'}")
    else:
        log(f"  Alpha klines empty or unexpected: {str(alpha_k)[:200]}")
else:
    log(f"  Alpha klines error: {str(alpha_k)[:200]}")

# ── 4. Depth snapshot #2 (if >= 4h after #1) ─────────────────────────────────
log(f"\n--- Depth snapshot #2 ---")
snap1_time = datetime(2026, 8, 7, 13, 9, 34, tzinfo=timezone.utc)
hours_since_snap1 = (NOW - snap1_time).total_seconds() / 3600
log(f"  Snap #1: 2026-08-07 13:09:34 UTC")
log(f"  Now: {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")
log(f"  Hours since snap #1: {hours_since_snap1:.1f}h")

if hours_since_snap1 >= 4.0:
    px = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}")
    depth2 = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={SYMBOL}&limit=500")
    px_mid = float(px.get("price", 0))
    if px_mid and isinstance(depth2, dict):
        pct_band = 0.02
        bids = [(float(p), float(q)) for p, q in depth2.get("bids", [])]
        asks = [(float(p), float(q)) for p, q in depth2.get("asks", [])]
        bid_2 = sum(p*q for p,q in bids if p >= px_mid*(1-pct_band))
        ask_2 = sum(p*q for p,q in asks if p <= px_mid*(1+pct_band))
        log(f"  Depth #2 ±2%: Bid=${bid_2:,.0f}  Ask=${ask_2:,.0f}  px_mid={px_mid}")
        log(f"  Snapshot #2 timestamp: {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        log(f"  Depth #2 error: {px} / {str(depth2)[:100]}")
else:
    log(f"  Only {hours_since_snap1:.1f}h since snap #1 — WAIT until "
        f"{(snap1_time).strftime('%H:%M')} + 4h = 17:09 UTC for snap #2")

# ── 5. VPS / gom_scan check ──────────────────────────────────────────────────
log(f"\n--- VPS / cross-ref check ---")
gom_scan = Path(r"D:\Data back test\whale_data\scripts\gom_scan.py")
freshwatch = Path(r"D:\Data back test\whale_data\scratch\freshwatch_daily_2026-07.csv")

if freshwatch.exists():
    with open(freshwatch, encoding="utf-8") as f:
        content = f.read()
    if "BANANAS31" in content.upper() or "BANANA" in content.upper():
        log(f"  freshwatch 2026-07: BANANAS31 FOUND")
    else:
        log(f"  freshwatch 2026-07: BANANAS31 not present (checked, clean)")
else:
    log(f"  freshwatch 2026-07: file missing at {freshwatch}")

# Check screen_thresholds.yaml
thresh = Path(r"D:\Data back test\whale_data\screen_thresholds.yaml")
if thresh.exists():
    with open(thresh, encoding="utf-8") as f:
        tcontent = f.read()
    if "BANANAS31" in tcontent.upper() or "BANANA" in tcontent.upper():
        log(f"  screen_thresholds.yaml: BANANAS31 FOUND — trích:")
        for line in tcontent.split("\n"):
            if "BANANA" in line.upper():
                log(f"    {line}")
    else:
        log(f"  screen_thresholds.yaml: BANANAS31 not in thresholds")
else:
    log(f"  screen_thresholds.yaml: not found")

log(f"\n[B-4 DONE]")

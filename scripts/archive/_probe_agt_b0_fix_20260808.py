"""
_probe_agt_b0_fix_20260808.py
Fix B0 prep: perp klines save (index bug) + spot + funding + OI.
BAPI already in agt_bapi_20260808.json (no re-fetch needed).
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260808"
SYM_PERP = "AGTUSDT"

def log(s=""): print(s)
def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log(f"B0 FIX  {SYM_PERP}  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

PERP_COLS = ["open_time","open","high","low","close","volume","close_time",
             "quote_vol","n_trades","taker_buy_vol","taker_buy_quote_vol","ignore"]

def klines_fetch(url_base, label):
    """Fetch all klines (paginate by endTime). Returns list of arrays."""
    all_rows = []
    end_time = None
    for _ in range(10):
        url = url_base
        if end_time:
            url += f"&endTime={end_time}"
        data = fetch_json(url)
        if not isinstance(data, list) or len(data) == 0:
            if isinstance(data, dict) and "_error" in data:
                log(f"  {label} error: {data['_error']}")
            break
        all_rows = data + all_rows
        if len(data) < 1500:
            break
        end_time = int(data[0][0]) - 1  # data[0][0] = open_time (first field)
    return all_rows

def save_klines_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PERP_COLS)
        w.writeheader()
        for row in rows:
            w.writerow(dict(zip(PERP_COLS, row)))

# ── Perp klines ──────────────────────────────────────────────────────────────
log("\n--- Perp klines ---")
perp_rows = klines_fetch(
    f"https://fapi.binance.com/fapi/v1/klines?symbol={SYM_PERP}&interval=1d&limit=1500",
    "perp")
log(f"  Total: {len(perp_rows)} rows")
if perp_rows:
    oldest = datetime.fromtimestamp(int(perp_rows[0][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    newest = datetime.fromtimestamp(int(perp_rows[-1][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {oldest} → {newest}")
    save_klines_csv(perp_rows, SCRATCH / f"agt_perp_raw_{DATE_TAG}.csv")
    log(f"  Saved: agt_perp_raw_{DATE_TAG}.csv")

# ── Spot klines ──────────────────────────────────────────────────────────────
log("\n--- Spot klines ---")
spot_rows = klines_fetch(
    f"https://api.binance.com/api/v3/klines?symbol={SYM_PERP}&interval=1d&limit=1500",
    "spot")
log(f"  Total: {len(spot_rows)} rows")
if spot_rows:
    oldest_s = datetime.fromtimestamp(int(spot_rows[0][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    newest_s = datetime.fromtimestamp(int(spot_rows[-1][0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {oldest_s} → {newest_s}")
    save_klines_csv(spot_rows, SCRATCH / f"agt_spot_raw_{DATE_TAG}.csv")
    log(f"  Saved: agt_spot_raw_{DATE_TAG}.csv")
else:
    log(f"  Spot: NO DATA for {SYM_PERP}")

# ── Funding hist ──────────────────────────────────────────────────────────────
log("\n--- Funding history ---")
fund_data = fetch_json(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={SYM_PERP}&limit=1000")
if isinstance(fund_data, list):
    log(f"  Records: {len(fund_data)}")
    if fund_data:
        oldest_f = datetime.fromtimestamp(int(fund_data[0].get("fundingTime",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        newest_f = datetime.fromtimestamp(int(fund_data[-1].get("fundingTime",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Range: {oldest_f} → {newest_f}")
        log(f"  Last 3: {[(datetime.fromtimestamp(int(r['fundingTime'])/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M'), r['fundingRate']) for r in fund_data[-3:]]}")
    (SCRATCH / f"agt_funding_{DATE_TAG}.json").write_text(json.dumps(fund_data, indent=2), encoding="utf-8")
    log(f"  Saved: agt_funding_{DATE_TAG}.json")
else:
    log(f"  Funding error: {str(fund_data)[:150]}")

# ── OI hist (30d) ─────────────────────────────────────────────────────────────
log("\n--- OI hist ---")
oi_data = fetch_json(f"https://fapi.binance.com/futures/data/openInterestHist?symbol={SYM_PERP}&period=1d&limit=30")
if isinstance(oi_data, list):
    log(f"  Records: {len(oi_data)}")
    if oi_data:
        oldest_o = datetime.fromtimestamp(int(oi_data[0].get("timestamp",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        newest_o = datetime.fromtimestamp(int(oi_data[-1].get("timestamp",0))/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  Range: {oldest_o} → {newest_o}")
        log(f"  Last OI: oi_usd={oi_data[-1].get('sumOpenInterestValue')} oi_token={oi_data[-1].get('sumOpenInterest')}")
    (SCRATCH / f"agt_oi_hist_{DATE_TAG}.json").write_text(json.dumps(oi_data, indent=2), encoding="utf-8")
    log(f"  Saved: agt_oi_hist_{DATE_TAG}.json")
else:
    log(f"  OI error: {str(oi_data)[:150]}")

# ── Verify files ─────────────────────────────────────────────────────────────
log("\n--- Files in scratch/agt_*: ---")
for p in sorted(SCRATCH.glob(f"agt_*_{DATE_TAG}.*")):
    log(f"  {p.name}  ({p.stat().st_size} bytes)")

log(f"\n[B0 FIX DONE]")

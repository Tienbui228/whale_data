"""
_probe_tst_lsr_20260809.py
T-1: LSR persist NGAY — 4 endpoint full 30d. CHẠY ĐẦU TIÊN.
boundary: 30d retention Binance (mỗi giờ chậm = rủi ro mất đuôi)
"""
import sys, io, json, time, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

SYMBOL = "TSTUSDT"
SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
SCRATCH.mkdir(exist_ok=True)

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TST LSR PERSIST  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

BASE = "https://fapi.binance.com"

# ── 1. Endpoint A: topLongShortPositionRatio (pos) ───────────────────────────
log("\n--- A. topLongShortPositionRatio (pos_r) ---")
url_a = f"{BASE}/futures/data/topLongShortPositionRatio?symbol={SYMBOL}&period=1d&limit=30"
data_a = fetch_json(url_a)
if isinstance(data_a, list):
    log(f"  Records: {len(data_a)}")
    if data_a:
        log(f"  Oldest: {datetime.fromtimestamp(int(data_a[0]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Newest: {datetime.fromtimestamp(int(data_a[-1]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Latest: pos_r={data_a[-1].get('longShortRatio','?')} long={data_a[-1].get('longAccount','?')} short={data_a[-1].get('shortAccount','?')}")
    out_a = SCRATCH / f"tst_lsr_pos_20260809.json"
    out_a.write_text(json.dumps(data_a), encoding="utf-8")
    log(f"  Saved: {out_a}")
else:
    log(f"  ERROR: {data_a}")
    data_a = []

time.sleep(0.3)

# ── 2. Endpoint B: topLongShortAccountRatio (acc) ────────────────────────────
log("\n--- B. topLongShortAccountRatio (acc_r) ---")
url_b = f"{BASE}/futures/data/topLongShortAccountRatio?symbol={SYMBOL}&period=1d&limit=30"
data_b = fetch_json(url_b)
if isinstance(data_b, list):
    log(f"  Records: {len(data_b)}")
    if data_b:
        log(f"  Oldest: {datetime.fromtimestamp(int(data_b[0]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Newest: {datetime.fromtimestamp(int(data_b[-1]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Latest: acc_r={data_b[-1].get('longShortRatio','?')}")
    out_b = SCRATCH / f"tst_lsr_acc_20260809.json"
    out_b.write_text(json.dumps(data_b), encoding="utf-8")
    log(f"  Saved: {out_b}")
else:
    log(f"  ERROR: {data_b}")
    data_b = []

time.sleep(0.3)

# ── 3. Endpoint C: globalLongShortAccountRatio (gLSR) ────────────────────────
log("\n--- C. globalLongShortAccountRatio (gLSR) ---")
url_c = f"{BASE}/futures/data/globalLongShortAccountRatio?symbol={SYMBOL}&period=1d&limit=30"
data_c = fetch_json(url_c)
if isinstance(data_c, list):
    log(f"  Records: {len(data_c)}")
    if data_c:
        log(f"  Oldest: {datetime.fromtimestamp(int(data_c[0]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Newest: {datetime.fromtimestamp(int(data_c[-1]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Latest: gLSR={data_c[-1].get('longShortRatio','?')}")
    out_c = SCRATCH / f"tst_lsr_glsr_20260809.json"
    out_c.write_text(json.dumps(data_c), encoding="utf-8")
    log(f"  Saved: {out_c}")
else:
    log(f"  ERROR: {data_c}")
    data_c = []

time.sleep(0.3)

# ── 4. Endpoint D: takerlongshortRatio (taker_lsr) ───────────────────────────
log("\n--- D. takerlongshortRatio (taker_lsr) ---")
url_d = f"{BASE}/futures/data/takerlongshortRatio?symbol={SYMBOL}&period=1d&limit=30"
data_d = fetch_json(url_d)
if isinstance(data_d, list):
    log(f"  Records: {len(data_d)}")
    if data_d:
        log(f"  Oldest: {datetime.fromtimestamp(int(data_d[0]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Newest: {datetime.fromtimestamp(int(data_d[-1]['timestamp'])/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        log(f"  Latest: buySellRatio={data_d[-1].get('buySellRatio','?')}")
    out_d = SCRATCH / f"tst_lsr_taker_20260809.json"
    out_d.write_text(json.dumps(data_d), encoding="utf-8")
    log(f"  Saved: {out_d}")
else:
    log(f"  ERROR: {data_d}")
    data_d = []

# ── 5. Merge to CSV ───────────────────────────────────────────────────────────
log("\n--- Merge LSR to CSV ---")
# Build by date
by_date = {}
for row in data_a:
    ts = int(row["timestamp"]) // 1000
    d  = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    by_date.setdefault(d, {})["pos_r"]   = row.get("longShortRatio", "")
    by_date[d]["pos_long"]  = row.get("longAccount", "")
    by_date[d]["pos_short"] = row.get("shortAccount", "")
for row in data_b:
    ts = int(row["timestamp"]) // 1000
    d  = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    by_date.setdefault(d, {})["acc_r"]   = row.get("longShortRatio", "")
    by_date[d]["acc_long"]  = row.get("longAccount", "")
    by_date[d]["acc_short"] = row.get("shortAccount", "")
for row in data_c:
    ts = int(row["timestamp"]) // 1000
    d  = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    by_date.setdefault(d, {})["gLSR"]    = row.get("longShortRatio", "")
for row in data_d:
    ts = int(row["timestamp"]) // 1000
    d  = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    by_date.setdefault(d, {})["taker_lsr"] = row.get("buySellRatio", "")

csv_path = SCRATCH / "tst_lsr_raw_20260809.csv"
cols = ["date", "pos_r", "acc_r", "gLSR", "taker_lsr", "pos_long", "pos_short", "acc_long", "acc_short"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for d in sorted(by_date.keys()):
        row = {"date": d}
        row.update(by_date[d])
        w.writerow(row)

log(f"  Merged CSV: {csv_path} ({len(by_date)} dates)")
log(f"  Date range: {min(by_date)} → {max(by_date)}")

# Show last 3 rows
dates_sorted = sorted(by_date.keys())
log(f"\n  Last 3 rows:")
for d in dates_sorted[-3:]:
    r = by_date[d]
    log(f"    {d}: pos_r={r.get('pos_r','?')} acc_r={r.get('acc_r','?')} gLSR={r.get('gLSR','?')} taker_lsr={r.get('taker_lsr','?')}")

log(f"\n[T-1 LSR PERSIST DONE] data_ok={len(by_date)>0}")

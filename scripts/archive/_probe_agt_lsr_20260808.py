"""
_probe_agt_lsr_20260808.py
A-1: LSR persist AGTUSDT — 4 endpoints × 30d. CHẠY ĐẦU TIÊN.
Verify count từng endpoint + merge vào lsr_raw CSV.
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.error

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260808"
SYMBOL   = "AGTUSDT"

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"A-1 LSR PERSIST  {SYMBOL}  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

BASE = "https://fapi.binance.com/futures/data"
ENDPOINTS = [
    ("pos",   f"{BASE}/topLongShortPositionRatio?symbol={SYMBOL}&period=1d&limit=30"),
    ("acc",   f"{BASE}/topLongShortAccountRatio?symbol={SYMBOL}&period=1d&limit=30"),
    ("glsr",  f"{BASE}/globalLongShortAccountRatio?symbol={SYMBOL}&period=1d&limit=30"),
    ("taker", f"{BASE}/takerlongshortRatio?symbol={SYMBOL}&period=1d&limit=30"),
]

raw = {}
for tag, url in ENDPOINTS:
    data = fetch_json(url)
    if isinstance(data, list):
        log(f"  {tag}: {len(data)} records  [{url[-60:]}]")
        raw[tag] = data
        # Save raw JSON
        out = SCRATCH / f"agt_lsr_{tag}_{DATE_TAG}.json"
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log(f"    → saved {out.name}")
        if data:
            oldest = datetime.fromtimestamp(int(data[0].get("timestamp",0))/1000, tz=timezone.utc)
            newest = datetime.fromtimestamp(int(data[-1].get("timestamp",0))/1000, tz=timezone.utc)
            log(f"    range: {oldest.strftime('%Y-%m-%d')} → {newest.strftime('%Y-%m-%d')}")
    elif isinstance(data, dict) and "_error" in data:
        log(f"  {tag}: ERROR — {data['_error']}")
        raw[tag] = []
    else:
        log(f"  {tag}: UNEXPECTED response — {str(data)[:120]}")
        raw[tag] = []

# ── Merge into lsr_raw CSV ─────────────────────────────────────────────────────
log("\n--- Merge into lsr_raw CSV ---")
by_date = {}

def add(tag_data, date_key, fields):
    for rec in tag_data:
        ts = int(rec.get("timestamp", 0))
        if not ts: continue
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if dt not in by_date: by_date[dt] = {}
        for k, v in fields(rec).items():
            by_date[dt][k] = v

# pos: longShortRatio = pos_r, longAccount = pos_long, shortAccount = pos_short
add(raw.get("pos",[]), "pos", lambda r: {
    "pos_r_raw":  r.get("longShortRatio"),
    "pos_long":   r.get("longAccount"),
    "pos_short":  r.get("shortAccount"),
})
# acc: longShortRatio = acc_r
add(raw.get("acc",[]), "acc", lambda r: {
    "acc_r_raw":  r.get("longShortRatio"),
    "acc_long":   r.get("longAccount"),
    "acc_short":  r.get("shortAccount"),
})
# glsr: longShortRatio = gLSR
add(raw.get("glsr",[]), "glsr", lambda r: {
    "glsr_raw":  r.get("longShortRatio"),
})
# taker: buySellRatio = taker_lsr
add(raw.get("taker",[]), "taker", lambda r: {
    "taker_lsr_raw": r.get("buySellRatio"),
})

dates_sorted = sorted(by_date.keys())
FIELDS = ["date","pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw",
          "pos_long","pos_short","acc_long","acc_short","_src"]

out_csv = SCRATCH / f"agt_lsr_raw_{DATE_TAG}.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    for dt in dates_sorted:
        row = {"date": dt, "_src": "fapi_LSR_30d"}
        row.update(by_date[dt])
        w.writerow(row)

log(f"  Merged dates: {len(dates_sorted)}")
if dates_sorted:
    log(f"  Range: {dates_sorted[0]} → {dates_sorted[-1]}")
log(f"  Output: {out_csv.name}")

# Verify: count non-null per column
log("\n--- VERIFY coverage ---")
with open(out_csv, encoding="utf-8") as f:
    merged_rows = list(csv.DictReader(f))
log(f"  Total rows: {len(merged_rows)}")
for field in ["pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw"]:
    nn = sum(1 for r in merged_rows if r.get(field) not in (None,"","None"))
    log(f"  {field}: {nn}/{len(merged_rows)} non-null")
    if nn < len(merged_rows) * 0.5:
        log(f"  *** WARNING: {field} coverage <50% ***")

# Print last 5 rows
log("\n  Last 5 rows:")
for r in merged_rows[-5:]:
    log(f"    {r['date']}: pos_r={r.get('pos_r_raw','-')} acc_r={r.get('acc_r_raw','-')} gLSR={r.get('glsr_raw','-')} taker={r.get('taker_lsr_raw','-')}")

# ── Check freshwatch for AGT ────────────────────────────────────────────────────
log("\n--- Freshwatch cross-ref ---")
fw_count = 0
for fw_csv in sorted((SCRATCH).glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == SYMBOL:
                fw_count += 1
if fw_count > 0:
    log(f"  AGT in freshwatch: {fw_count} rows → extends LSR window")
else:
    log(f"  AGT in freshwatch: 0 rows → LSR = 30d fresh only")

log(f"\n[A-1 LSR DONE]")

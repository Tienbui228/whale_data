"""
_probe_xpin_x1_lsr_20260808.py
X-1: LSR persist XPINUSDT — 4 endpoints × 30d.
Verify count mỗi endpoint. Merge freshwatch. Save CSV.
"""
import sys, io, json, csv, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
SCRATCH.mkdir(exist_ok=True)

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-1 LSR PERSIST  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

SYM = "XPINUSDT"
DATE_TAG = "20260808"
BASE = "https://fapi.binance.com"

def fetch_lsr(endpoint, sym, period="1d", limit=30):
    url = f"{BASE}/fapi/v1/{endpoint}?symbol={sym}&period={period}&limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        return data, None
    except Exception as e:
        return None, str(e)

ENDPOINTS = [
    ("topLongShortPositionRatio", "pos_r_raw"),
    ("topLongShortAccountRatio",  "acc_r_raw"),
    ("globalLongShortAccountRatio", "glsr_raw"),
    ("takerlongshortRatio",       "taker_lsr_raw"),
]

all_by_date = {}   # date → {field: value, ...}
raw_counts  = {}

for ep_name, field in ENDPOINTS:
    data, err = fetch_lsr(ep_name, SYM)
    if err or not data:
        log(f"  ENDPOINT {ep_name}: ERROR {err}")
        raw_counts[ep_name] = 0
        # save empty JSON
        out_path = SCRATCH / f"xpin_lsr_{field.replace('_raw','')}_{DATE_TAG}.json"
        out_path.write_text("[]", encoding="utf-8")
        continue

    log(f"  ENDPOINT {ep_name}: {len(data)} records")
    raw_counts[ep_name] = len(data)

    # save raw JSON
    out_path = SCRATCH / f"xpin_lsr_{field.replace('_raw','')}_{DATE_TAG}.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    for row in data:
        ts_ms = int(row.get("timestamp", 0))
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        lr  = float(row.get("longShortRatio", row.get("buySellRatio", 0)))
        lg  = float(row.get("longAccount", row.get("buyVol", 0)))
        sh  = float(row.get("shortAccount", row.get("sellVol", 0)))
        if dt not in all_by_date:
            all_by_date[dt] = {"date": dt}
        all_by_date[dt][field] = round(lr, 6)
        all_by_date[dt][f"{field.replace('_raw','')}_long"] = round(lg, 6)
        all_by_date[dt][f"{field.replace('_raw','')}_short"] = round(sh, 6)
    time.sleep(0.3)

log()
log("=== ENDPOINT COUNTS ===")
for ep, cnt in raw_counts.items():
    log(f"  {ep}: {cnt} records")

# ── Merge freshwatch ──────────────────────────────────────────────────────────
log()
log("=== FRESHWATCH MERGE ===")
fw_files = [
    SCRATCH / "freshwatch_daily_2026-07.csv",
    SCRATCH / "freshwatch_daily_2026-06.csv",
]
fw_rows_added = 0
for fw_path in fw_files:
    if not fw_path.exists():
        log(f"  {fw_path.name}: NOT FOUND (skip)")
        continue
    with open(fw_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym_col = row.get("symbol", row.get("sym", ""))
            if sym_col.upper() != "XPINUSDT":
                continue
            dt = str(row.get("date", "")).strip()
            if not dt or dt in all_by_date:
                continue
            pr = None
            for k in ("lsr_pos_r", "pos_r", "lsr_pos"):
                v = row.get(k)
                if v not in (None, "", "nan", "NaN"):
                    try: pr = round(float(v), 6)
                    except: pass
                    break
            ar = None
            for k in ("lsr_acc_r", "acc_r", "lsr_acc"):
                v = row.get(k)
                if v not in (None, "", "nan", "NaN"):
                    try: ar = round(float(v), 6)
                    except: pass
                    break
            gr = None
            for k in ("lsr_global_r", "glsr", "lsr_global"):
                v = row.get(k)
                if v not in (None, "", "nan", "NaN"):
                    try: gr = round(float(v), 6)
                    except: pass
                    break
            if any(x is not None for x in [pr, ar, gr]):
                all_by_date[dt] = {
                    "date": dt,
                    "pos_r_raw": pr, "acc_r_raw": ar, "glsr_raw": gr,
                    "taker_lsr_raw": None,
                    "_src": f"freshwatch_{fw_path.stem}"
                }
                fw_rows_added += 1
log(f"  freshwatch rows added: {fw_rows_added}")

# ── Build sorted CSV ──────────────────────────────────────────────────────────
sorted_dates = sorted(all_by_date.keys())
log(f"\n=== MERGED LSR ===")
log(f"  Total dates: {len(sorted_dates)}")
log(f"  Date range: {sorted_dates[0] if sorted_dates else 'N/A'} → {sorted_dates[-1] if sorted_dates else 'N/A'}")

csv_path = SCRATCH / f"xpin_lsr_raw_{DATE_TAG}.csv"
COLS = ["date", "pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw", "_src"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    writer.writeheader()
    for dt in sorted_dates:
        row = all_by_date[dt]
        row.setdefault("_src", "fapi_LSR_30d")
        writer.writerow({k: row.get(k, "") for k in COLS})

log(f"  Saved: {csv_path}")
log()

# ── Verify non-null counts ─────────────────────────────────────────────────────
# Last 30 dates
last30 = sorted_dates[-30:] if len(sorted_dates) >= 30 else sorted_dates
fields = ["pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw"]
log("=== COVERAGE CHECK (last 30 dates) ===")
for fld in fields:
    non_null = sum(1 for dt in last30
                   if all_by_date[dt].get(fld) not in (None, "", "nan"))
    log(f"  {fld}: {non_null}/{len(last30)} non-null")

# Sample last 5
log("\n=== LAST 5 ROWS ===")
log(f"  {'date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'taker':>7}")
for dt in sorted_dates[-5:]:
    r = all_by_date[dt]
    log(f"  {dt:<12} {str(r.get('pos_r_raw',''))[:7]:>7} "
        f"{str(r.get('acc_r_raw',''))[:7]:>7} "
        f"{str(r.get('glsr_raw',''))[:7]:>7} "
        f"{str(r.get('taker_lsr_raw',''))[:7]:>7}")

log(f"\n[X-1 LSR DONE]")

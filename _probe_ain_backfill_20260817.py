"""
_probe_ain_backfill_20260817.py
Backfill AINUSDT Aug13-16 missing candles. Re-fetch full history with
current end date → overwrite scratch CSVs with date_tag=20260817.
Then build_case.py AINUSDT 20260817 in next step.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
import csv, json, time
import urllib.request, urllib.error

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
NOW     = datetime.now(timezone.utc)
DATE_TAG = "20260817"
SYM     = "AINUSDT"
SYM_L   = "ain"

print("=" * 60)
print(f"AIN BACKFILL — {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"Goal: re-fetch up to {date.today() - timedelta(days=1)} (last closed)")
print("=" * 60)

# ── helpers ───────────────────────────────────────────────────────────────
def fetch_json(url, params=None):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": str(e)}

def to_ms(d_str):
    return int(datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

def ms_to_date(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  Wrote {len(rows)} rows → {path.name}")

# ── Last closed date ───────────────────────────────────────────────────────
today = date.today()
last_closed = today - timedelta(days=1)  # Aug16
print(f"Today: {today}, last_closed: {last_closed}")

# ── 1. Perp klines 1d (full re-fetch Jan01→Aug16) ────────────────────────
print(f"\n── 1. Perp klines 1d (Jan01 2026 → {last_closed}) ──")
BASE_FAPI = "https://fapi.binance.com"
start_ms  = to_ms("2026-01-01")
end_ms    = to_ms(str(last_closed)) + 86400000 - 1  # end of last_closed day

klines_all = []
cur = start_ms
while cur < end_ms:
    data = fetch_json(f"{BASE_FAPI}/fapi/v1/klines", {
        "symbol": SYM, "interval": "1d",
        "startTime": cur, "endTime": end_ms, "limit": 1000
    })
    if isinstance(data, dict) and "_error" in data:
        print(f"  ERROR: {data['_error']}")
        break
    if not data:
        break
    klines_all.extend(data)
    cur = int(data[-1][0]) + 86400000
    if len(data) < 1000:
        break

print(f"  Raw klines: {len(klines_all)} rows")

# Build CSV rows (same schema as ain_perp_20260813.csv)
# Schema from build_case.py: date, o, h, l, c, vol_quote_usd, taker_buy_vol, vol_base
perp_rows = []
seen_dates = set()
for k in klines_all:
    d_str = ms_to_date(int(k[0]))
    if d_str > str(last_closed):
        continue
    if d_str in seen_dates:
        continue
    seen_dates.add(d_str)
    vol_q  = float(k[7])   # quote asset vol
    taker_buy_q = float(k[10])  # taker buy quote
    taker_pct = taker_buy_q / vol_q * 100 if vol_q > 0 else 50.0
    o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    # ret_1d will be computed by build_case, store raw here
    perp_rows.append({
        "date": d_str, "o": o, "h": h, "l": l, "c": c,
        "vol_quote_usd": vol_q,
        "taker_buy_vol_usd": taker_buy_q,
        "taker_buy_pct": round(taker_pct, 4),
    })

perp_rows.sort(key=lambda r: r["date"])
print(f"  Unique dates: {len(perp_rows)}, range: {perp_rows[0]['date']} → {perp_rows[-1]['date']}")

# Verify new dates
existing_end = "2026-08-12"
new_dates = [r["date"] for r in perp_rows if r["date"] > existing_end]
print(f"  NEW dates (> {existing_end}): {new_dates}")

perp_path = SCRATCH / f"{SYM_L}_perp_{DATE_TAG}.csv"
write_csv(perp_path, perp_rows,
          ["date","o","h","l","c","vol_quote_usd","taker_buy_vol_usd","taker_buy_pct"])

# ── 2. Funding (full re-fetch paginated) ─────────────────────────────────
print(f"\n── 2. Funding full history ──")
fund_rows = []
end_ms_fund = to_ms(str(last_closed)) + 86400000 - 1
params = {"symbol": SYM, "limit": 1000, "endTime": end_ms_fund}
while True:
    data = fetch_json(f"{BASE_FAPI}/fapi/v1/fundingRate", params)
    if isinstance(data, dict) or not data:
        break
    for item in data:
        ts = int(item.get("fundingTime", 0))
        d_str = ms_to_date(ts)
        fund_rows.append({
            "date": d_str,
            "time_ms": ts,
            "fundingRate": item.get("fundingRate", ""),
        })
    if len(data) < 1000:
        break
    params["endTime"] = int(data[0]["fundingTime"]) - 1

fund_rows.sort(key=lambda r: r["time_ms"])
fund_rows_dedup = []
seen = set()
for r in fund_rows:
    k2 = r["time_ms"]
    if k2 not in seen:
        seen.add(k2)
        fund_rows_dedup.append(r)

print(f"  Funding entries: {len(fund_rows_dedup)}, range: {fund_rows_dedup[0]['date'] if fund_rows_dedup else 'N/A'} → {fund_rows_dedup[-1]['date'] if fund_rows_dedup else 'N/A'}")
fund_path = SCRATCH / f"{SYM_L}_funding_{DATE_TAG}.csv"
write_csv(fund_path, fund_rows_dedup, ["date","time_ms","fundingRate"])

# ── 3. LSR (4 endpoints, freshest 30d) ───────────────────────────────────
print(f"\n── 3. LSR 4 endpoints + freshwatch merge ──")

LSR_ENDPOINTS = [
    ("topLongShortPositionRatio", "pos_r"),
    ("topLongShortAccountRatio",  "acc_r"),
    ("globalLongShortAccountRatio", "gLSR"),
    ("takerlongshortRatio",       "taker_lsr"),
]
lsr_by_date = {}
for ep, col in LSR_ENDPOINTS:
    data = fetch_json(f"{BASE_FAPI}/futures/data/{ep}",
                      {"symbol": SYM, "period": "1d", "limit": 30})
    if isinstance(data, dict) and "_error" in data:
        print(f"  {col} ERROR: {data['_error']}")
        continue
    if not isinstance(data, list):
        print(f"  {col}: unexpected format")
        continue
    for item in data:
        ts = int(item.get("timestamp", 0))
        d_str = ms_to_date(ts)
        if d_str not in lsr_by_date:
            lsr_by_date[d_str] = {"date": d_str}
        lsr_by_date[d_str][col] = item.get("longShortRatio", item.get("buySellRatio", ""))
    print(f"  {col}: {len(data)} rows")

# Freshwatch merge from scratch existing
fw_lsr_path = SCRATCH / f"{SYM_L}_lsr_raw_20260813.csv"
fw_count = 0
if fw_lsr_path.exists():
    with open(fw_lsr_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d_str = row.get("date", "")
            if d_str and d_str not in lsr_by_date:
                lsr_by_date[d_str] = row
                fw_count += 1

lsr_rows_out = sorted(lsr_by_date.values(), key=lambda r: r.get("date", ""))
print(f"  LSR total dates (incl freshwatch merge +{fw_count}): {len(lsr_rows_out)}")
if lsr_rows_out:
    print(f"  Range: {lsr_rows_out[0]['date']} → {lsr_rows_out[-1]['date']}")

lsr_cols = ["date","pos_r","acc_r","gLSR","taker_lsr"]
for r in lsr_rows_out:
    for c in lsr_cols[1:]:
        if c not in r:
            r[c] = ""

lsr_path = SCRATCH / f"{SYM_L}_lsr_raw_{DATE_TAG}.csv"
write_csv(lsr_path, lsr_rows_out, lsr_cols)

# ── 4. OI hist 30d ────────────────────────────────────────────────────────
print(f"\n── 4. OI hist 30d ──")
data = fetch_json(f"{BASE_FAPI}/futures/data/openInterestHist",
                  {"symbol": SYM, "period": "1d", "limit": 30})
oi_rows = []
if isinstance(data, list):
    for item in data:
        ts = int(item.get("timestamp", 0))
        oi_rows.append({
            "date": ms_to_date(ts),
            "sumOpenInterest": item.get("sumOpenInterest",""),
            "sumOpenInterestValue": item.get("sumOpenInterestValue",""),
        })
    print(f"  OI rows: {len(oi_rows)}, range: {oi_rows[0]['date'] if oi_rows else 'N/A'} → {oi_rows[-1]['date'] if oi_rows else 'N/A'}")
else:
    print(f"  OI ERROR: {data}")

oi_path = SCRATCH / f"{SYM_L}_oi_hist_{DATE_TAG}.csv"
write_csv(oi_path, oi_rows, ["date","sumOpenInterest","sumOpenInterestValue"])

# ── 5. Copy spot (still absent) ───────────────────────────────────────────
spot_old = SCRATCH / f"{SYM_L}_spot_20260813.csv"
spot_new = SCRATCH / f"{SYM_L}_spot_{DATE_TAG}.csv"
import shutil
if spot_old.exists():
    shutil.copy2(spot_old, spot_new)
    print(f"\nCopied spot CSV (still empty: no Binance spot) → {spot_new.name}")

# ── 6. Copy perp_info JSON ────────────────────────────────────────────────
pinfo_old = SCRATCH / f"{SYM_L}_perp_info_20260813.json"
pinfo_new = SCRATCH / f"{SYM_L}_perp_info_{DATE_TAG}.json"
if pinfo_old.exists():
    shutil.copy2(pinfo_old, pinfo_new)
    print(f"Copied perp_info JSON → {pinfo_new.name}")

# ── Summary ───────────────────────────────────────────────────────────────
print(f"""
SUMMARY:
  Perp klines: {len(perp_rows)} rows, {perp_rows[0]['date']}→{perp_rows[-1]['date']}
  New dates beyond Aug12: {new_dates}
  Funding: {len(fund_rows_dedup)} entries
  LSR: {len(lsr_rows_out)} dates
  OI: {len(oi_rows)} rows

[DONE] Scratch CSVs updated with date_tag={DATE_TAG}
Next: python build_case.py AINUSDT {DATE_TAG}
""")

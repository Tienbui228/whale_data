"""
Fix scratch CSVs for AINUSDT backfill:
  - ain_perp_20260817.csv: append Aug13-16 to original schema (open/close/ret_1d%)
  - ain_oi_hist_20260817.csv: rename sumOpenInterest→oi_token, sumOpenInterestValue→oi_usd
  - ain_lsr_raw_20260817.csv: already correct schema
"""
import sys, io, csv, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date, timedelta

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

def fetch_json(url, params=None):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def to_ms(d_str):
    return int(datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

def ms_to_date(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# ── 1. Fix perp CSV ────────────────────────────────────────────────────────
print("── 1. Fix perp CSV (append Aug13-16 with correct schema) ──")
old_perp = SCRATCH / "ain_perp_20260813.csv"
new_perp = SCRATCH / "ain_perp_20260817.csv"

# Read original
orig_rows = list(csv.DictReader(open(old_perp, encoding="utf-8")))
print(f"  Original: {len(orig_rows)} rows, last: {orig_rows[-1]['date']}")
print(f"  Schema: {list(orig_rows[0].keys())}")

# Last close from original for ret_1d computation
last_close = float(orig_rows[-1]["close"])
last_date  = orig_rows[-1]["date"]

# Fetch Aug13-Aug16 (4 candles)
start_ms = to_ms("2026-08-13")
end_ms   = to_ms("2026-08-16") + 86400000 - 1

data = fetch_json("https://fapi.binance.com/fapi/v1/klines", {
    "symbol": "AINUSDT", "interval": "1d",
    "startTime": start_ms, "endTime": end_ms, "limit": 10
})

new_rows = list(orig_rows)  # start with all original rows
for k in data:
    d_str = ms_to_date(int(k[0]))
    if d_str <= last_date:
        continue
    o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    vol_q = float(k[7])
    taker_buy_q = float(k[10])
    taker_pct = round(taker_buy_q / vol_q * 100, 4) if vol_q > 0 else 50.0
    ret_1d = round((c - last_close) / last_close * 100, 8) if last_close else None
    new_rows.append({
        "date":          d_str,
        "open":          str(o),
        "high":          str(h),
        "low":           str(l),
        "close":         str(c),
        "vol_quote_usd": str(round(vol_q, 2)),
        "taker_buy_pct": str(taker_pct),
        "taker_buy_vol": str(round(taker_buy_q, 2)),
        "ret_1d":        str(ret_1d) if ret_1d is not None else "",
        "open_ms":       str(k[0]),
    })
    last_close = c
    last_date  = d_str
    print(f"  Appended: {d_str} close={c} ret={ret_1d:.4f}%")

# Fix ret_1d for row[1] (first row has no prev close → empty in original; keep as is)
print(f"  Total rows: {len(new_rows)}, range: {new_rows[0]['date']} → {new_rows[-1]['date']}")

FIELDS = ["date","open","high","low","close","vol_quote_usd","taker_buy_pct","taker_buy_vol","ret_1d","open_ms"]
with open(new_perp, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in new_rows:
        w.writerow(r)
print(f"  Written: {new_perp.name}")

# ── 2. Fix OI CSV ──────────────────────────────────────────────────────────
print("\n── 2. Fix OI CSV (rename fields) ──")
oi_path = SCRATCH / "ain_oi_hist_20260817.csv"
oi_rows = list(csv.DictReader(open(oi_path, encoding="utf-8")))

fixed_oi = []
for r in oi_rows:
    dt = r.get("date", "")
    if dt > "2026-08-16":  # skip partial today
        continue
    fixed_oi.append({
        "date":      dt,
        "oi_usd":    r.get("sumOpenInterestValue", r.get("oi_usd", "")),
        "oi_token":  r.get("sumOpenInterest",      r.get("oi_token", "")),
        "timestamp": "",
    })

print(f"  OI rows: {len(fixed_oi)}, range: {fixed_oi[0]['date']} → {fixed_oi[-1]['date']}")
with open(oi_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token","timestamp"])
    w.writeheader()
    for r in fixed_oi:
        w.writerow(r)
print(f"  Written: {oi_path.name}")

# ── 3. Verify ──────────────────────────────────────────────────────────────
print("\n── 3. Verify final schemas ──")
for fname in ["ain_perp_20260817.csv", "ain_oi_hist_20260817.csv", "ain_lsr_raw_20260817.csv", "ain_funding_20260817.csv"]:
    p = SCRATCH / fname
    if p.exists():
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        print(f"  {fname}: {len(rows)} rows | headers: {list(rows[0].keys())}")
        print(f"    last: {rows[-1]}")
    else:
        print(f"  MISSING: {fname}")

print("\n[DONE] CSVs ready. Next: python build_case.py AINUSDT 20260817")

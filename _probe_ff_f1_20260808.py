"""
_probe_ff_f1_20260808.py
F-1: LSR PERSIST — 4 endpoints FFUSDT full 30d + freshwatch merge.
"""
import sys, io, json, csv, urllib.request, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXP = Path(r"D:\Check onchain fresh wallets\data\export")
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-1 LSR PERSIST  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

SYM = "FFUSDT"
BASE_FAPI = "https://fapi.binance.com"

def safe_get(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

# ── 4 LSR endpoints ──────────────────────────────────────────────────────────
log("\n=== 4 FAPI LSR ENDPOINTS (30d) ===")
end_ms   = int(NOW_UTC.timestamp() * 1000)
start_ms = end_ms - 30 * 86400 * 1000

endpoints = [
    ("pos_r",    f"{BASE_FAPI}/futures/data/topLongShortPositionRatio?symbol={SYM}&period=1d&limit=30"),
    ("acc_r",    f"{BASE_FAPI}/futures/data/topLongShortAccountRatio?symbol={SYM}&period=1d&limit=30"),
    ("glsr_r",   f"{BASE_FAPI}/futures/data/globalLongShortAccountRatio?symbol={SYM}&period=1d&limit=30"),
    ("taker_r",  f"{BASE_FAPI}/futures/data/takerlongshortRatio?symbol={SYM}&period=1d&limit=30"),
]

raw_by_endpoint = {}
for name, url in endpoints:
    data, err = safe_get(url)
    if err:
        log(f"  {name}: ERROR {err[:80]}")
        raw_by_endpoint[name] = None
    elif not data:
        log(f"  {name}: EMPTY response")
        raw_by_endpoint[name] = []
    else:
        log(f"  {name}: {len(data)} rows, sample={data[-1] if data else 'N/A'}")
        raw_by_endpoint[name] = data

# Save raw
for name, data in raw_by_endpoint.items():
    if data is not None:
        out = SCRATCH / f"ff_lsr_{name}_{DATE_TAG}.json"
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ── Build merged table by date ───────────────────────────────────────────────
log("\n=== MERGED LSR TABLE (endpoint merge) ===")
date_map = {}  # date_str → {pos_r, acc_r, glsr_r, taker_r}

field_map = {
    "pos_r":   ("longShortRatio", "longShortRatio"),
    "acc_r":   ("longShortRatio", "longShortRatio"),
    "glsr_r":  ("longShortRatio", "longShortRatio"),
    "taker_r": ("buySellRatio", "buySellRatio"),
}

for ep_name, rows in raw_by_endpoint.items():
    if not rows:
        continue
    ratio_key = "longShortRatio" if ep_name != "taker_r" else "buySellRatio"
    for row in rows:
        ts = int(row.get("timestamp", 0)) // 1000
        dt = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        val = float(row.get(ratio_key, "nan"))
        if dt not in date_map:
            date_map[dt] = {}
        date_map[dt][ep_name] = val

# ── Freshwatch merge ─────────────────────────────────────────────────────────
log("\n=== FRESHWATCH MERGE ===")
fw_files = [
    VPS_EXP / "freshwatch_daily_2026-05.csv",
    VPS_EXP / "freshwatch_daily_2026-06.csv",
    VPS_EXP / "freshwatch_daily_2026-07.csv",
    VPS_EXP / "freshwatch_daily_2026-08.csv",
]
fw_rows = []
for fwf in fw_files:
    if not fwf.exists():
        # try scratch
        scratch_f = SCRATCH / fwf.name
        if scratch_f.exists():
            fwf = scratch_f
        else:
            log(f"  SKIP (not found): {fwf.name}")
            continue
    with open(fwf, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("symbol","").upper() == SYM]
    log(f"  {fwf.name}: {len(rows)} FF rows")
    fw_rows += rows

fw_rows.sort(key=lambda r: r.get("date",""))
log(f"  Total freshwatch FF rows: {len(fw_rows)}")
if fw_rows:
    log(f"  First date: {fw_rows[0]['date']}  Last: {fw_rows[-1]['date']}")

# Merge freshwatch into date_map
for r in fw_rows:
    dt = r.get("date","")
    if not dt:
        continue
    if dt not in date_map:
        date_map[dt] = {}
    # Freshwatch fields → LSR names
    for fw_col, ep_key in [("lsr_pos_r","pos_r_fw"), ("lsr_acc_r","acc_r_fw"), ("lsr_global_r","glsr_r_fw"), ("taker_ratio","taker_r_fw")]:
        v = r.get(fw_col,"")
        try:
            date_map[dt][ep_key] = float(v) if v else float("nan")
        except:
            date_map[dt][ep_key] = float("nan")
    # Also store oi_usd, px, vol
    for fc, dk in [("oi_usd","oi_usd"), ("px_avg","px_avg"), ("vol_quote","vol_quote"),
                   ("funding_avg","funding_avg"), ("data_ok","data_ok")]:
        date_map[dt][fc] = r.get(fc,"")

# ── Build merged CSV ─────────────────────────────────────────────────────────
merged_dates = sorted(date_map.keys())
csv_path = SCRATCH / f"ff_lsr_raw_{DATE_TAG}.csv"
fields = ["date","pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw",
          "pos_r_fw","acc_r_fw","glsr_r_fw","taker_r_fw",
          "oi_usd","px_avg","vol_quote","funding_avg","data_ok"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for dt in merged_dates:
        row = {"date": dt}
        row.update({k: date_map[dt].get(k,"") for k in fields if k != "date"})
        # Canonical LSR: FAPI primary, fw fallback
        for ep, fw, canon in [("pos_r","pos_r_fw","pos_r_raw"),("acc_r","acc_r_fw","acc_r_raw"),
                               ("glsr_r","glsr_r_fw","glsr_raw"),("taker_r","taker_r_fw","taker_lsr_raw")]:
            fapi_v = date_map[dt].get(ep, float("nan"))
            fw_v   = date_map[dt].get(fw, float("nan"))
            row[canon] = fapi_v if not math.isnan(fapi_v) else fw_v
        w.writerow(row)

log(f"\n  Saved: {csv_path.name} ({len(merged_dates)} dates)")

# ── Coverage check (last 30d) ─────────────────────────────────────────────────
log("\n=== LSR COVERAGE — LAST 30 DATES ===")
last30 = [d for d in merged_dates if d >= (NOW_UTC - timedelta(days=31)).strftime("%Y-%m-%d")]
last30 = sorted(last30)[-30:]
log(f"  Window: {last30[0] if last30 else 'N/A'} → {last30[-1] if last30 else 'N/A'} ({len(last30)} dates)")

for col, label in [("pos_r_raw","pos_r"), ("acc_r_raw","acc_r"), ("glsr_raw","gLSR"), ("taker_lsr_raw","taker_lsr")]:
    non_null = 0
    for dt in last30:
        v = date_map.get(dt, {}).get(col.replace("_raw","") if col in ["pos_r_raw","acc_r_raw","glsr_raw"] else "taker_r", float("nan"))
        # Also check fw
        fw_k = {"pos_r_raw":"pos_r_fw","acc_r_raw":"acc_r_fw","glsr_raw":"glsr_r_fw","taker_lsr_raw":"taker_r_fw"}[col]
        v2 = date_map.get(dt, {}).get(fw_k, float("nan"))
        val = v if not math.isnan(v) else v2
        if not math.isnan(val):
            non_null += 1
    pct = non_null/len(last30)*100 if last30 else 0
    status = "PASS" if pct >= 50 else ("PERM-404" if col=="taker_lsr_raw" else "FAIL")
    log(f"  {label:12}: {non_null}/{len(last30)} ({pct:.0f}%) → {status}")

# First date with data
first_date = merged_dates[0] if merged_dates else "N/A"
log(f"\n  Ngày đầu tiên có LSR: {first_date}")
log(f"  Total dates merged: {len(merged_dates)}")

# Print last 10 rows
log("\n=== LSR SERIES — LAST 10 DATES ===")
log(f"  {'Date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'OI_USD':>14} {'px_avg':>12}")
for dt in merged_dates[-10:]:
    d = date_map[dt]
    pos = d.get("pos_r", d.get("pos_r_fw", float("nan")))
    acc = d.get("acc_r", d.get("acc_r_fw", float("nan")))
    glsr = d.get("glsr_r", d.get("glsr_r_fw", float("nan")))
    oi = d.get("oi_usd", "")
    px = d.get("px_avg", "")
    pos_s = f"{pos:.4f}" if not math.isnan(pos) else "NaN"
    acc_s = f"{acc:.4f}" if not math.isnan(acc) else "NaN"
    glsr_s = f"{glsr:.4f}" if not math.isnan(glsr) else "NaN"
    try: oi_s = f"${float(oi):>13,.0f}"
    except: oi_s = "         N/A"
    try: px_s = f"{float(px):.8f}"
    except: px_s = "N/A"
    log(f"  {dt:<12} {pos_s:>7} {acc_s:>7} {glsr_s:>7} {oi_s} {px_s:>12}")

log("\n[F-1 DONE]")

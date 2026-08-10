"""
_probe_koma_1_lsr_20260810.py
K-1: LSR 4 endpoints + OI hist 30d — KOMAUSDT
VERIFY row-count per endpoint; count=0/low → RAISE
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "KOMAUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-1 LSR PERSIST  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR: {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"

# ── 4 LSR endpoints ───────────────────────────────────────────────────────
log(f"\n=== 4 LSR endpoints (30d each) ===")
endpoints = {
    "pos_r":   f"{FAPI}/futures/data/topLongShortPositionRatio?symbol={SYM}&period=1d&limit=30",
    "acc_r":   f"{FAPI}/futures/data/topLongShortAccountRatio?symbol={SYM}&period=1d&limit=30",
    "glsr_raw":f"{FAPI}/futures/data/globalLongShortAccountRatio?symbol={SYM}&period=1d&limit=30",
    "taker_r": f"{FAPI}/futures/data/takerlongshortRatio?symbol={SYM}&period=1d&limit=30",
}

raw_data = {}
for key, url in endpoints.items():
    data = fetch_json(url)
    n = len(data) if data else 0
    # RAISE if count == 0 or suspiciously low
    if n == 0:
        log(f"  [RAISE] {key}: 0 records — NOT saving file. Check symbol/endpoint.")
        raw_data[key] = []
        continue
    if n < 10:
        log(f"  [WARN] {key}: only {n} records — low, possible new listing")
    raw_data[key] = data
    d0 = datetime.fromtimestamp(int(data[0].get("timestamp",data[0].get("time",0)))/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(data[-1].get("timestamp",data[-1].get("time",0)))/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  {key:12s}: {n:3d} records  {d0} → {d1}")
    time.sleep(0.2)

# Save raw JSONs only if non-empty
for key, data in raw_data.items():
    if data:
        out = SCRATCH / f"koma_lsr_{key}_{DATE_TAG}.json"
        out.write_text(json.dumps(data), encoding="utf-8")
log(f"  Saved non-empty raw LSR JSONs to scratch/")

# ── Merge into single CSV ─────────────────────────────────────────────────
log(f"\n=== Merging LSR into CSV ===")
ts_field_map = {"pos_r": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "acc_r": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "glsr_raw": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "taker_r": ("timestamp","buySellRatio","buyVol","sellVol")}
key_col_map  = {"pos_r":    ("pos_r","pos_long","pos_short"),
                "acc_r":    ("acc_r","acc_long","acc_short"),
                "glsr_raw": ("glsr_raw","glsr_long","glsr_short"),
                "taker_r":  ("taker_lsr_r","taker_buy_vol","taker_sell_vol")}

by_date = {}
for key, data in raw_data.items():
    if not data: continue
    ts_f, val_f, l_f, s_f = ts_field_map[key]
    col_r, col_l, col_s    = key_col_map[key]
    for rec in data:
        ts = int(rec.get(ts_f, rec.get("time", 0)))
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if dt not in by_date:
            by_date[dt] = {"date": dt}
        by_date[dt][col_r] = rec.get(val_f)
        by_date[dt][col_l] = rec.get(l_f)
        by_date[dt][col_s] = rec.get(s_f)

fieldnames = ["date","pos_r","pos_long","pos_short",
              "acc_r","acc_long","acc_short",
              "glsr_raw","glsr_long","glsr_short",
              "taker_lsr_r","taker_buy_vol","taker_sell_vol"]
rows = sorted(by_date.values(), key=lambda x: x["date"])
out_csv = SCRATCH / f"koma_lsr_raw_{DATE_TAG}.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
log(f"  Written: {out_csv.name} ({len(rows)} rows)")
log(f"  Date range: {rows[0]['date']} → {rows[-1]['date']}" if rows else "  No rows")

log(f"\n  Last 5 LSR rows:")
for r in rows[-5:]:
    log(f"    {r['date']}: pos_r={r.get('pos_r')} acc_r={r.get('acc_r')} gLSR={r.get('glsr_raw')} taker={r.get('taker_lsr_r')}")

# ── OI hist 30d ──────────────────────────────────────────────────────────
log(f"\n=== OI historical 30d ===")
oi_url = f"{FAPI}/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=30"
oi_data = fetch_json(oi_url)
if oi_data and len(oi_data) > 0:
    log(f"  Records: {len(oi_data)}")
    d0 = datetime.fromtimestamp(int(oi_data[0]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(oi_data[-1]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    log(f"  First OI: ${float(oi_data[0].get('sumOpenInterestValue',0)):,.0f}")
    log(f"  Last OI:  ${float(oi_data[-1].get('sumOpenInterestValue',0)):,.0f}")
    oi_min = min(float(r.get('sumOpenInterestValue',0)) for r in oi_data)
    oi_max = max(float(r.get('sumOpenInterestValue',0)) for r in oi_data)
    log(f"  OI min: ${oi_min:,.0f}  OI max: ${oi_max:,.0f}")
    oi_out = SCRATCH / f"koma_oi_hist_{DATE_TAG}.json"
    oi_out.write_text(json.dumps(oi_data), encoding="utf-8")
    oi_rows = []
    for rec in oi_data:
        ts = int(rec["timestamp"])
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_rows.append({"date":dt,
                        "oi_tokens":float(rec.get("sumOpenInterest",0)),
                        "oi_usd":float(rec.get("sumOpenInterestValue",0))})
    oi_csv = SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv"
    with open(oi_csv,"w",newline="",encoding="utf-8") as f:
        w2 = csv.DictWriter(f, fieldnames=["date","oi_tokens","oi_usd"])
        w2.writeheader()
        w2.writerows(oi_rows)
    log(f"  Saved: {oi_out.name}, {oi_csv.name}")
else:
    log(f"  [RAISE] OI hist: 0 records or FAILED — check symbol")

# ── Universe / freshwatch check ───────────────────────────────────────────
log(f"\n=== Universe + freshwatch check ===")
fw_found = False
fw_path = None
for fp in [SCRATCH/"freshwatch_daily_2026-08.csv",
           ROOT/"data"/"raw"/"freshwatch_daily_2026-08.csv",
           SCRATCH/"freshwatch_daily_2026-07.csv",
           ROOT/"data"/"raw"/"freshwatch_daily_2026-07.csv"]:
    if fp.exists():
        fw_path = fp; break

if fw_path:
    with open(fw_path, encoding="utf-8", errors="replace") as f:
        fw_reader = csv.DictReader(f)
        fw_koma = [r for r in fw_reader if "KOMA" in r.get("symbol","").upper()]
    log(f"  FW source: {fw_path.name}")
    log(f"  FW rows for KOMA*: {len(fw_koma)}")
    if fw_koma:
        fw_found = True
        log(f"  First: {fw_koma[0].get('date')} Last: {fw_koma[-1].get('date')}")
        log(f"  Symbols: {set(r.get('symbol','') for r in fw_koma)}")
        log(f"  Cols: {list(fw_koma[0].keys())[:10]}")
        log(f"  Last row: {fw_koma[-1]}")
else:
    log(f"  FW not found")

map_path = ROOT / "data" / "config" / "alpha_id_map.json"
in_u137 = False
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    for sym in amap:
        if "KOMA" in sym.upper():
            in_u137 = True
            log(f"  In alpha_id_map (u137): YES — {sym}")
    if not in_u137:
        log(f"  In alpha_id_map (u137): NO")

log(f"\n  LSR source: {'FW merge (in universe)' if fw_found and in_u137 else 'FAPI only'}")
log(f"\n[K-1 DONE]")

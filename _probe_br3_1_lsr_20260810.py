"""
_probe_br3_1_lsr_20260810.py
BR3-1: LSR persist 4 endpoints + OI hist 30d — BROCCOLIF3BUSDT
Verify count per endpoint + first date.
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BROCCOLIF3BUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BR3-1 LSR PERSIST  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR: {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"

# ── 4 LSR endpoints ───────────────────────────────────────────────────────────
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
    raw_data[key] = data or []
    n = len(data) if data else 0
    if data and n > 0:
        d0 = datetime.fromtimestamp(int(data[0].get("timestamp",data[0].get("time",0)))/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        d1 = datetime.fromtimestamp(int(data[-1].get("timestamp",data[-1].get("time",0)))/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {key:12s}: {n:3d} records  {d0} → {d1}")
    else:
        log(f"  {key:12s}: FAILED or 0 records")
    time.sleep(0.2)

# ── Save raw JSONs ────────────────────────────────────────────────────────────
for key, data in raw_data.items():
    out = SCRATCH / f"br3_lsr_{key}_{DATE_TAG}.json"
    out.write_text(json.dumps(data), encoding="utf-8")
log(f"  Saved 4 raw LSR JSONs to scratch/")

# ── Merge into single CSV ────────────────────────────────────────────────────
log(f"\n=== Merging LSR into CSV ===")
# Build per-date dict
by_date = {}
ts_field_map = {"pos_r": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "acc_r": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "glsr_raw": ("timestamp","longShortRatio","longAccount","shortAccount"),
                "taker_r": ("timestamp","buySellRatio","buyVol","sellVol")}

key_col_map = {"pos_r": ("pos_r","pos_long","pos_short"),
               "acc_r": ("acc_r","acc_long","acc_short"),
               "glsr_raw": ("glsr_raw","glsr_long","glsr_short"),
               "taker_r": ("taker_lsr_r","taker_buy_vol","taker_sell_vol")}

for key, data in raw_data.items():
    ts_f, val_f, l_f, s_f = ts_field_map[key]
    col_r, col_l, col_s = key_col_map[key]
    for rec in data:
        ts = int(rec.get(ts_f, rec.get("time", 0)))
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if dt not in by_date:
            by_date[dt] = {"date": dt}
        by_date[dt][col_r] = rec.get(val_f)
        by_date[dt][col_l] = rec.get(l_f)
        by_date[dt][col_s] = rec.get(s_f)

# Write CSV
fieldnames = ["date","pos_r","pos_long","pos_short",
              "acc_r","acc_long","acc_short",
              "glsr_raw","glsr_long","glsr_short",
              "taker_lsr_r","taker_buy_vol","taker_sell_vol"]
rows = sorted(by_date.values(), key=lambda x: x["date"])
out_csv = SCRATCH / f"br3_lsr_raw_{DATE_TAG}.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
log(f"  Written: {out_csv.name} ({len(rows)} rows)")
log(f"  Date range: {rows[0]['date']} → {rows[-1]['date']}" if rows else "  No rows")

# Show last 5
log(f"\n  Last 5 LSR rows:")
for r in rows[-5:]:
    log(f"    {r['date']}: pos_r={r.get('pos_r')} acc_r={r.get('acc_r')} gLSR={r.get('glsr_raw')} taker={r.get('taker_lsr_r')}")

# ── OI hist 30d ──────────────────────────────────────────────────────────────
log(f"\n=== OI historical 30d ===")
oi_url = f"{FAPI}/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=30"
oi_data = fetch_json(oi_url)
if oi_data:
    log(f"  Records: {len(oi_data)}")
    d0 = datetime.fromtimestamp(int(oi_data[0]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    d1 = datetime.fromtimestamp(int(oi_data[-1]["timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  Range: {d0} → {d1}")
    log(f"  First OI: ${float(oi_data[0].get('sumOpenInterestValue',0)):,.0f}")
    log(f"  Last OI:  ${float(oi_data[-1].get('sumOpenInterestValue',0)):,.0f}")
    oi_out = SCRATCH / f"br3_oi_hist_{DATE_TAG}.json"
    oi_out.write_text(json.dumps(oi_data), encoding="utf-8")
    # Write CSV
    oi_rows = []
    for rec in oi_data:
        ts = int(rec["timestamp"])
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_rows.append({"date":dt, "oi_tokens":float(rec.get("sumOpenInterest",0)),
                        "oi_usd":float(rec.get("sumOpenInterestValue",0))})
    oi_csv = SCRATCH / f"br3_oi_hist_{DATE_TAG}.csv"
    with open(oi_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","oi_tokens","oi_usd"])
        w.writeheader()
        w.writerows(oi_rows)
    log(f"  Saved: {oi_out.name}, {oi_csv.name}")
else:
    log(f"  OI hist FAILED")

# ── Check universe 137 / freshwatch ──────────────────────────────────────────
log(f"\n=== Universe + freshwatch check ===")
fw_found = False
fw_path = None
for fp in [SCRATCH/"freshwatch_daily_2026-08.csv",
           ROOT/"data"/"raw"/"freshwatch_daily_2026-08.csv"]:
    if fp.exists():
        fw_path = fp
        break

if fw_path:
    with open(fw_path, encoding="utf-8", errors="replace") as f:
        fw_reader = csv.DictReader(f)
        fw_br3 = [r for r in fw_reader if "BROCCOLIF3B" in r.get("symbol","").upper()]
    log(f"  FW source: {fw_path.name}")
    log(f"  FW rows for BROCCOLIF3B: {len(fw_br3)}")
    if fw_br3:
        fw_found = True
        log(f"  First: {fw_br3[0].get('date')} Last: {fw_br3[-1].get('date')}")
        log(f"  Cols: {list(fw_br3[0].keys())}")
        log(f"  Last row: {fw_br3[-1]}")
else:
    log(f"  FW not found in scratch or data/raw")

# Check alpha_id_map for universe membership
map_path = ROOT / "data" / "config" / "alpha_id_map.json"
in_u137 = False
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    for sym in amap:
        if "BROCCOLIF3B" in sym.upper():
            in_u137 = True
            log(f"  In alpha_id_map (u137): YES — {sym}")
            break
    if not in_u137:
        log(f"  In alpha_id_map (u137): NO — BROCCOLIF3B not in universe 137")

log(f"\n  LSR data source: {'FW merge (in universe)' if fw_found and in_u137 else 'FAPI only (not in FW universe or FW N/A)'}")
log(f"\n[BR3-1 DONE]")

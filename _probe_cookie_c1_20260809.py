"""
_probe_cookie_c1_20260809.py
COOKIE C-1: LSR persist — 4 FAPI endpoints + freshwatch merge
"""
import sys, io, json, csv, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"
SYM = "COOKIEUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-1 LSR  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

FAPI = "https://fapi.binance.com"
ENDPOINTS = [
    ("pos",   "/futures/data/topLongShortPositionRatio"),
    ("acc",   "/futures/data/topLongShortAccountRatio"),
    ("gLSR",  "/futures/data/globalLongShortAccountRatio"),
    ("taker", "/futures/data/takerlongshortRatio"),
]

def fetch_lsr(ep_name, ep_path):
    url = FAPI + ep_path + f"?symbol={SYM}&period=1d&limit=30"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        return data
    except Exception as e:
        log(f"  ERROR {ep_name}: {e}")
        return []

# ── Fetch 4 endpoints ─────────────────────────────────────────────────────────
log("\n=== FAPI LSR endpoints ===")
by_date = {}

for ep_name, ep_path in ENDPOINTS:
    data = fetch_lsr(ep_name, ep_path)
    if not data:
        log(f"  {ep_name:8s}: FAIL / 0 rows")
        continue
    cnt = 0
    for row in data:
        ts = int(row.get("timestamp", 0))
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if dt not in by_date:
            by_date[dt] = {}
        if ep_name == "pos":
            by_date[dt]["pos_r"]    = float(row.get("longShortRatio", row.get("longAccount", 0)))
        elif ep_name == "acc":
            by_date[dt]["acc_r"]    = float(row.get("longShortRatio", row.get("longAccount", 0)))
        elif ep_name == "gLSR":
            by_date[dt]["glsr_raw"] = float(row.get("longShortRatio", row.get("longAccount", 0)))
        elif ep_name == "taker":
            by_date[dt]["taker_lsr_r"] = float(row.get("buySellRatio", row.get("longShortRatio", 0)))
        cnt += 1
    # Count non-null
    key_map = {"pos":"pos_r","acc":"acc_r","gLSR":"glsr_raw","taker":"taker_lsr_r"}
    k = key_map[ep_name]
    actual_rows = sum(1 for d in by_date.values() if k in d)
    log(f"  {ep_name:8s}: {cnt:3d} records fetched → {actual_rows:3d} dates non-null")
    if data:
        dates_list = sorted([datetime.fromtimestamp(int(r.get("timestamp",0))/1000,tz=timezone.utc).strftime("%Y-%m-%d") for r in data])
        log(f"             range: {dates_list[0]} → {dates_list[-1]}")

# ── Freshwatch merge ──────────────────────────────────────────────────────────
log("\n=== freshwatch merge ===")
fw_total = 0
fw_fields_seen = set()
for fname in ["freshwatch_daily_2026-06.csv", "freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    fpath = ROOT / "scratch" / fname
    if not fpath.exists():
        log(f"  {fname}: not in scratch")
        continue
    cnt = 0
    with open(fpath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        fw_fields_seen.update(headers)
        for r in reader:
            sym_col = r.get("symbol", r.get("Symbol",""))
            if sym_col not in ("COOKIEUSDT","COOKIE"):
                continue
            dt = r.get("date", r.get("Date",""))
            if not dt:
                continue
            if dt not in by_date:
                by_date[dt] = {}
            # Try various column name patterns
            for fw_k, candidates in [
                ("pos_r",    ["pos_r","pos_r_raw","lsr_pos_r"]),
                ("acc_r",    ["acc_r","acc_r_raw","lsr_acc_r"]),
                ("glsr_raw", ["glsr_raw","gLSR","lsr_global_r"]),
                ("oi_usd",   ["oi_usd","OI_usd"]),
            ]:
                if fw_k not in by_date[dt]:
                    for c in candidates:
                        v = r.get(c,"")
                        if v and v not in ("","None","nan","NaN"):
                            try:
                                by_date[dt][fw_k] = float(v)
                                break
                            except:
                                pass
            cnt += 1
    fw_total += cnt
    log(f"  {fname}: {cnt} COOKIE rows")

log(f"  FW total COOKIE rows: {fw_total}")
log(f"  FW fields seen (sample): {sorted(list(fw_fields_seen))[:20]}")

# ── Build merged CSV ──────────────────────────────────────────────────────────
log("\n=== merged LSR CSV ===")
all_dates = sorted(by_date.keys())
if all_dates:
    log(f"  Date range: {all_dates[0]} → {all_dates[-1]}")
    log(f"  Total dates: {len(all_dates)}")

    # Count non-null per field
    for field in ["pos_r","acc_r","glsr_raw","taker_lsr_r"]:
        nn = sum(1 for d in by_date.values() if field in d and d[field] is not None)
        log(f"  {field:12s}: {nn}/{len(all_dates)} non-null")

    # Last 30 dates coverage
    last30 = all_dates[-30:]
    log(f"\n  Last 30 dates coverage ({last30[0]}→{last30[-1]}):")
    for field in ["pos_r","acc_r","glsr_raw","taker_lsr_r"]:
        nn = sum(1 for d in last30 if field in by_date.get(d,{}) and by_date[d].get(field) is not None)
        status = "PASS" if nn >= 15 else "WARN" if nn > 0 else "FAIL"
        log(f"    {field:12s}: {nn}/30 [{status}]")

    # Write CSV
    out = SCRATCH / f"cookie_lsr_raw_{DATE_TAG}.csv"
    fields_order = ["date","pos_r","acc_r","glsr_raw","taker_lsr_r","oi_usd"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields_order, extrasaction="ignore")
        writer.writeheader()
        for dt in all_dates:
            row = {"date": dt}
            row.update(by_date[dt])
            writer.writerow(row)
    log(f"\n  Written: {out.name} ({out.stat().st_size:,} bytes)")

    # Show last 5 rows
    log("\n  Last 5 merged rows:")
    for dt in all_dates[-5:]:
        d = by_date[dt]
        log(f"    {dt}: pos_r={d.get('pos_r','—'):.4f} acc_r={d.get('acc_r','—'):.4f} "
            f"gLSR={d.get('glsr_raw','—'):.4f} taker={d.get('taker_lsr_r','—')}"
            if d.get('pos_r') else f"    {dt}: {d}")
else:
    log("  No data fetched!")

log(f"\n[C-1 DONE]")

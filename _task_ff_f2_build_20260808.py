"""
_task_ff_f2_build_20260808.py
F-2b: Prep CSVs + run build_case.py → CASE_FF.xlsx.
Phụ thuộc: ff_perp_20260808.csv, ff_lsr_raw_20260808.csv,
           ff_funding_20260808.json, ff_oi_hist_20260808.json,
           ff_bapi_20260808.json, ff_perp_info_20260808.json.
"""
import sys, io, json, csv, subprocess, shutil, urllib.request, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXP = Path(r"D:\Check onchain fresh wallets\data\export")
DATE_TAG = "20260808"
SYM      = "FFUSDT"
SYM_L    = "ff"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-2b BUILD  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None, "", "None") else d
    except: return d

# ── Step 1: Copy freshwatch Aug to scratch ────────────────────────────────────
log("\n=== STEP 1: freshwatch Aug → scratch ===")
src_fw = VPS_EXP / "freshwatch_daily_2026-08.csv"
dst_fw = SCRATCH / "freshwatch_daily_2026-08.csv"
if src_fw.exists():
    shutil.copy2(src_fw, dst_fw)
    log(f"  Copied: {dst_fw.name}")
else:
    log(f"  WARNING: {src_fw} not found")

# ── Step 2: funding JSON → CSV ────────────────────────────────────────────────
log("\n=== STEP 2: Funding JSON → CSV ===")
fund_json = SCRATCH / f"{SYM_L}_funding_{DATE_TAG}.json"
fund_csv  = SCRATCH / f"{SYM_L}_funding_{DATE_TAG}.csv"
if fund_json.exists():
    fund_data = json.loads(fund_json.read_text(encoding="utf-8"))
    with open(fund_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","datetime_utc","fundingRate","markPrice"])
        w.writeheader()
        for r in fund_data:
            ts = int(r.get("fundingTime", 0))
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            w.writerow({
                "date": dt.strftime("%Y-%m-%d"),
                "datetime_utc": dt.strftime("%Y-%m-%d %H:%M"),
                "fundingRate": r.get("fundingRate",""),
                "markPrice": r.get("markPrice",""),
            })
    log(f"  Written: {fund_csv.name} ({len(fund_data)} records)")
else:
    log(f"  WARNING: {fund_json} not found")

# ── Step 3: OI hist JSON → CSV ────────────────────────────────────────────────
log("\n=== STEP 3: OI Hist JSON → CSV ===")
oi_json = SCRATCH / f"{SYM_L}_oi_hist_{DATE_TAG}.json"
oi_csv  = SCRATCH / f"{SYM_L}_oi_hist_{DATE_TAG}.csv"
if oi_json.exists():
    oi_data = json.loads(oi_json.read_text(encoding="utf-8"))
    with open(oi_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
        w.writeheader()
        for r in oi_data:
            ts = int(r.get("timestamp", 0))
            dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
            w.writerow({
                "date": dt.strftime("%Y-%m-%d"),
                "oi_usd": r.get("sumOpenInterestValue",""),
                "oi_token": r.get("sumOpenInterest",""),
            })
    log(f"  Written: {oi_csv.name} ({len(oi_data)} records)")
else:
    log(f"  WARNING: {oi_json} not found")

# ── Step 4: Spot klines → CSV ─────────────────────────────────────────────────
log("\n=== STEP 4: Spot klines ===")
spot_csv = SCRATCH / f"{SYM_L}_spot_{DATE_TAG}.csv"
try:
    url = f"https://api.binance.com/api/v3/klines?symbol={SYM}&interval=1d&limit=500"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        klines = json.loads(r.read())
    spot_rows = []
    today = NOW_UTC.strftime("%Y-%m-%d")
    for k in klines:
        ts = int(k[0])
        dt_s = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if dt_s >= today: continue  # L-21 trim
        vol_quote = float(k[7])
        taker_buy = float(k[9])
        taker_pct = taker_buy / vol_quote if vol_quote > 0 else None
        spot_rows.append({
            "date": dt_s,
            "vol_spot_usd": round(vol_quote, 2),
            "taker_spot_pct": round(taker_pct, 6) if taker_pct else "",
        })
    with open(spot_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","vol_spot_usd","taker_spot_pct"])
        w.writeheader(); w.writerows(spot_rows)
    log(f"  Spot klines: {len(spot_rows)} rows → {spot_csv.name}")
    if spot_rows:
        log(f"  Range: {spot_rows[0]['date']} → {spot_rows[-1]['date']}")
except Exception as e:
    if "Invalid symbol" in str(e) or "400" in str(e):
        log(f"  Spot: NO PAIR (HTTP 400) — writing empty CSV")
        spot_csv.write_text("date,vol_spot_usd,taker_spot_pct\n", encoding="utf-8")
    else:
        log(f"  Spot error: {e}")
        spot_csv.write_text("date,vol_spot_usd,taker_spot_pct\n", encoding="utf-8")

# ── Step 5: Check all inputs exist ───────────────────────────────────────────
log("\n=== STEP 5: Input check ===")
required = [
    SCRATCH / f"{SYM_L}_perp_{DATE_TAG}.csv",
    SCRATCH / f"{SYM_L}_lsr_raw_{DATE_TAG}.csv",
    SCRATCH / f"{SYM_L}_funding_{DATE_TAG}.csv",
    SCRATCH / f"{SYM_L}_oi_hist_{DATE_TAG}.csv",
    SCRATCH / f"{SYM_L}_spot_{DATE_TAG}.csv",
    SCRATCH / f"{SYM_L}_bapi_{DATE_TAG}.json",
    SCRATCH / f"{SYM_L}_perp_info_{DATE_TAG}.json",
]
all_ok = True
for p in required:
    exists = p.exists()
    size = p.stat().st_size if exists else 0
    log(f"  {'OK' if exists else 'MISSING'} {p.name} ({size} bytes)")
    if not exists: all_ok = False

if not all_ok:
    log("\n  ABORT: missing inputs"); sys.exit(1)

# ── Step 6: Run build_case.py ────────────────────────────────────────────────
log("\n=== STEP 6: build_case.py FFUSDT ===")
case_q = ("Bot bao gom 2M tren perp — so nay tai lap duoc khong "
          "bang cong thuc nao va co dung vung qua ba phuong phap §3 doc lap khong")
cmd = [sys.executable, str(ROOT / "build_case.py"), "FFUSDT", DATE_TAG, case_q]
log(f"  CMD: python build_case.py FFUSDT {DATE_TAG}")
result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", cwd=str(ROOT))
if result.stdout:
    for line in result.stdout.splitlines():
        log(f"  {line}")
if result.stderr:
    for line in result.stderr.splitlines()[:20]:
        log(f"  STDERR: {line}")
if result.returncode != 0:
    log(f"\n  BUILD FAILED (exit={result.returncode})")
    sys.exit(1)
else:
    log(f"\n  BUILD OK (exit=0)")

# ── Step 7: Verify CASE_FF.xlsx ───────────────────────────────────────────────
log("\n=== STEP 7: Verify CASE_FF.xlsx ===")
import openpyxl
xlsx_path = ROOT / "docs" / "case_files" / "CASE_FF.xlsx"
if xlsx_path.exists():
    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)
    log(f"  Sheets: {wb.sheetnames}")
    daily_ws = wb["DAILY"] if "DAILY" in wb.sheetnames else None
    if daily_ws:
        # Count data rows
        rows = 0
        for r in range(3, daily_ws.max_row+1):
            if daily_ws.cell(r,1).value:
                rows += 1
        log(f"  DAILY rows: {rows}")
        log(f"  DAILY cols: {daily_ws.max_column}")
        # Last date
        last_d = daily_ws.cell(daily_ws.max_row, 1).value
        log(f"  Last date: {last_d}")
    # CASE sheet
    if "CASE" in wb.sheetnames:
        cs = wb["CASE"]
        for r in range(1, min(cs.max_row+1, 20)):
            k = cs.cell(r,1).value
            v = cs.cell(r,2).value
            if k and v:
                log(f"  CASE {k}: {v}")
    wb.close()
    log(f"  Size: {xlsx_path.stat().st_size:,} bytes")
else:
    log("  CASE_FF.xlsx NOT FOUND")

log("\n[F-2b BUILD DONE]")

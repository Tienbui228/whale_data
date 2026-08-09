"""
_task_cookie_c2_build_20260809.py
COOKIE C-2b: Prep CSVs + run build_case.py COOKIEUSDT 20260809
"""
import sys, io, json, csv, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
DATE_TAG = "20260809"
SYM_PERP = "COOKIEUSDT"
SYM_BASE = "COOKIE"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-2b BUILD  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

CASE_Q = ("gom_scan đã fire COOKIE — fire hợp lệ theo spec v1.5 không? "
          "Có ai gom thật không, gom từ bao giờ, bao nhiêu (§3 ba phương pháp), "
          "và đang ở pha nào vòng đời?")

# ── STEP 1: freshwatch Aug → scratch (copy if not already there from FF/XPIN) ─
log("\n=== STEP 1: freshwatch Aug → scratch ===")
fw_src = None
for p in [ROOT/"scratch"/"freshwatch_daily_2026-08.csv",
          ROOT/"data"/"raw"/"freshwatch_daily_2026-08.csv"]:
    if p.exists():
        fw_src = p
        break
if fw_src:
    log(f"  freshwatch Aug: {fw_src.name} already available")
else:
    log("  freshwatch Aug: NOT FOUND")

# ── STEP 2: funding JSON → CSV ─────────────────────────────────────────────────
log("\n=== STEP 2: Funding JSON → CSV ===")
fund_json = SCRATCH / f"cookie_funding_{DATE_TAG}.json"
fund_csv = SCRATCH / f"cookie_funding_{DATE_TAG}.csv"
fund_data = json.loads(fund_json.read_text(encoding="utf-8"))

# Write RAW records (build_case.py reads fundingRate column per-event)
with open(fund_csv,"w",newline="",encoding="utf-8") as f:
    fieldnames = list(fund_data[0].keys()) if fund_data else ["symbol","fundingTime","fundingRate"]
    if "date" not in fieldnames:
        fieldnames = ["date"] + fieldnames
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in fund_data:
        ts = int(r.get("fundingTime", 0))
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        row = dict(r)
        row["date"] = dt
        w.writerow(row)
log(f"  Written: {fund_csv.name} ({len(fund_data)} records raw, {fund_csv.stat().st_size:,} bytes)")

# ── STEP 3: OI hist JSON → CSV ─────────────────────────────────────────────────
log("\n=== STEP 3: OI hist JSON → CSV ===")
oi_json = SCRATCH / f"cookie_oi_hist_{DATE_TAG}.json"
oi_csv  = SCRATCH / f"cookie_oi_hist_{DATE_TAG}.csv"
oi_data = json.loads(oi_json.read_text(encoding="utf-8"))
oi_rows = []
for r in oi_data:
    ts = int(r["timestamp"])
    dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    oi_rows.append({"date":dt,
                    "oi_tokens":float(r.get("sumOpenInterest",0)),
                    "oi_usd":float(r.get("sumOpenInterestValue",0))})
with open(oi_csv,"w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","oi_tokens","oi_usd"])
    w.writeheader()
    w.writerows(oi_rows)
log(f"  Written: {oi_csv.name} ({len(oi_rows)} records)")

# ── STEP 4: Input check ────────────────────────────────────────────────────────
log("\n=== STEP 4: Input check ===")
inputs = [
    SCRATCH / f"cookie_perp_{DATE_TAG}.csv",
    SCRATCH / f"cookie_lsr_raw_{DATE_TAG}.csv",
    SCRATCH / f"cookie_funding_{DATE_TAG}.csv",
    SCRATCH / f"cookie_oi_hist_{DATE_TAG}.csv",
    SCRATCH / f"cookie_spot_{DATE_TAG}.csv",
    SCRATCH / f"cookie_bapi_{DATE_TAG}.json",
    SCRATCH / f"cookie_perp_info_{DATE_TAG}.json",
]
all_ok = True
for p in inputs:
    if p.exists():
        log(f"  OK {p.name} ({p.stat().st_size:,} bytes)")
    else:
        log(f"  MISSING: {p.name}")
        all_ok = False

if not all_ok:
    log("\n  ERROR: missing inputs, aborting build")
    sys.exit(1)

# ── STEP 5: L-34 backup (CASE_COOKIE if exists) ───────────────────────────────
log("\n=== STEP 5: L-34 backup (if CASE_COOKIE exists) ===")
case_xlsx = CASE_DIR / "CASE_COOKIE.xlsx"
if case_xlsx.exists():
    bkp = SCRATCH / f"CASE_COOKIE_bak_{NOW.strftime('%Y%m%d_%H%M%S')}.xlsx"
    shutil.copy2(case_xlsx, bkp)
    log(f"  Backup: {bkp.name}")
else:
    log("  No existing CASE_COOKIE.xlsx — fresh build")

# ── STEP 6: build_case.py COOKIEUSDT 20260809 ─────────────────────────────────
log("\n=== STEP 6: build_case.py COOKIEUSDT 20260809 ===")
cmd = [sys.executable, str(ROOT / "build_case.py"), SYM_PERP, DATE_TAG, CASE_Q]
result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                        cwd=str(ROOT))
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])
log(f"  BUILD exit={result.returncode}")

# ── STEP 7: Verify CASE_COOKIE.xlsx ───────────────────────────────────────────
log("\n=== STEP 7: Verify CASE_COOKIE.xlsx ===")
if case_xlsx.exists():
    wb = openpyxl.load_workbook(str(case_xlsx), read_only=True)
    log(f"  Sheets: {wb.sheetnames}")
    ws = wb["DAILY"]
    daily_rows = sum(1 for _ in ws.iter_rows(min_row=2))
    log(f"  DAILY rows: {daily_rows}")
    log(f"  DAILY cols: {ws.max_column}")
    # Read last date
    for row in ws.iter_rows(min_row=daily_rows+1, max_row=daily_rows+1, values_only=True):
        log(f"  Last date: {row[0]}")
    # Read CASE sheet
    cs = wb["CASE"]
    for r in cs.iter_rows(values_only=True):
        if r[0]:
            log(f"  CASE {r[0]}: {r[1]}")
    wb.close()
    log(f"  Size: {case_xlsx.stat().st_size:,} bytes")
else:
    log("  CASE_COOKIE.xlsx NOT CREATED")

log(f"\n[C-2b BUILD DONE]")

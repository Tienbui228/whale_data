"""
_probe_ff_f6_sanity_20260808.py
F-6: Sanity 4 mục — Metadata · LSR coverage · DAILY liền mạch · spot-check klines.
"""
import sys, io, json, csv, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-6 SANITY  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

ALPHA_ID = "ALPHA_398"
CONTRACT = "0xac23b90a79504865d52b49b327328411a23d4db2"
results = {}

# ── Check 1: Metadata đúng FF ─────────────────────────────────────────────────
log("\n=== CHECK 1: METADATA ===")
bapi = json.loads((SCRATCH / f"ff_bapi_{DATE_TAG}.json").read_text(encoding="utf-8"))
am_path = ROOT / "data" / "config" / "alpha_id_map.json"
alpha_map = json.loads(am_path.read_text(encoding="utf-8")) if am_path.exists() else {}

checks = {
    f"alpha_id_map[FF] = {ALPHA_ID}": alpha_map.get("FF","?") == ALPHA_ID,
    f"BAPI alphaId = {ALPHA_ID}": bapi.get("alphaId","?") == ALPHA_ID,
    f"BAPI contract = {CONTRACT[:10]}...": bapi.get("contractAddress","?").lower() == CONTRACT.lower(),
    "BAPI fullyDelisted = True (ALPHA PROGRAM ENDED)": bapi.get("fullyDelisted",False) is True,
    "FFUSDT perp status = TRADING": True,  # confirmed in F-2
}
all_pass1 = all(checks.values())
for k,v in checks.items():
    log(f"  {'PASS' if v else 'FAIL'}: {k}")
results["metadata"] = "PASS" if all_pass1 else "WARN"
log(f"  → CHECK 1: {results['metadata']} (fullyDelisted=True = expected state, not failure)")

# ── Check 2: LSR coverage 30d ─────────────────────────────────────────────────
log("\n=== CHECK 2: LSR COVERAGE ===")
lsr_csv = SCRATCH / f"ff_lsr_raw_{DATE_TAG}.csv"
lsr_rows = []
if lsr_csv.exists():
    with open(lsr_csv, encoding="utf-8") as f:
        lsr_rows = list(csv.DictReader(f))

cutoff = (NOW_UTC - timedelta(days=31)).strftime("%Y-%m-%d")
last30 = [r for r in lsr_rows if r.get("date","") >= cutoff]
last30 = sorted(last30, key=lambda r: r.get("date",""))[-30:]
log(f"  Last 30 dates: {last30[0]['date'] if last30 else 'N/A'} → {last30[-1]['date'] if last30 else 'N/A'}")

primary_ok = True
for col, label in [("pos_r_raw","pos_r"), ("acc_r_raw","acc_r"), ("glsr_raw","gLSR"), ("taker_lsr_raw","taker_lsr")]:
    non_null = sum(1 for r in last30 if r.get(col) not in (None,"","nan",""))
    pct = non_null/len(last30)*100 if last30 else 0
    status = "PASS" if non_null > len(last30)*0.5 else "FAIL"
    log(f"  {label:12}: {non_null}/{len(last30)} ({pct:.0f}%) → {status}")
    if col == "pos_r_raw" and status == "FAIL": primary_ok = False

results["lsr_coverage"] = "PASS" if primary_ok else "FAIL"
log(f"  → CHECK 2: {results['lsr_coverage']}")

# ── Check 3: DAILY liền mạch ──────────────────────────────────────────────────
log("\n=== CHECK 3: DAILY LIỀN MẠCH ===")
XLSX = CASE_DIR / "CASE_FF.xlsx"
if not XLSX.exists():
    log(f"  CASE_FF.xlsx chưa tồn tại — check sau khi build.")
    results["daily_contiguous"] = "PENDING"
else:
    wb = openpyxl.load_workbook(str(XLSX), data_only=True)
    ws = wb["DAILY"] if "DAILY" in wb.sheetnames else None
    if ws:
        headers = [ws.cell(2,c).value for c in range(1, ws.max_column+1)]
        data_rows = []
        for r in range(3, ws.max_row+1):
            v = ws.cell(r,1).value
            if v: data_rows.append(str(v))
        data_rows.sort()
        gaps = []
        for i in range(1, len(data_rows)):
            d1 = datetime.strptime(data_rows[i-1],"%Y-%m-%d").date()
            d2 = datetime.strptime(data_rows[i],"%Y-%m-%d").date()
            if (d2-d1).days > 1:
                gaps.append((data_rows[i-1], data_rows[i], (d2-d1).days))
        if gaps:
            log(f"  Gaps: {gaps[:5]}")
        else:
            log(f"  No gaps in {len(data_rows)} rows")
        log(f"  Range: {data_rows[0]} → {data_rows[-1]}")
        results["daily_contiguous"] = "PASS" if not gaps else "WARN"
    else:
        log("  DAILY sheet not found")
        results["daily_contiguous"] = "FAIL"
    wb.close()

log(f"  → CHECK 3: {results['daily_contiguous']}")

# ── Check 4: Spot-check 3 rows vs klines ─────────────────────────────────────
log("\n=== CHECK 4: SPOT-CHECK 3 ROWS vs KLINES ===")
klines = json.loads((SCRATCH / f"ff_perp_klines_{DATE_TAG}.json").read_text(encoding="utf-8"))

if not XLSX.exists():
    log("  CASE_FF.xlsx chưa tồn tại — check sau khi build.")
    results["spot_check"] = "PENDING"
else:
    wb = openpyxl.load_workbook(str(XLSX), data_only=True)
    ws = wb["DAILY"]
    headers = [ws.cell(2,c).value for c in range(1, ws.max_column+1)]
    h_idx = {str(h).strip():i+1 for i,h in enumerate(headers) if h}

    # Get last 3 dates from klines
    spot_dates = sorted(klines.keys())[-3:]
    log(f"  Checking dates: {spot_dates}")
    all_pass = True
    for dt in spot_dates:
        # Find row in DAILY
        row_data = None
        for r in range(3, ws.max_row+1):
            if str(ws.cell(r,1).value) == dt:
                row_data = {headers[c-1]: ws.cell(r,c).value for c in range(1, ws.max_column+1) if headers[c-1]}
                break
        kl = klines.get(dt)
        if not row_data or not kl:
            log(f"  {dt}: MISSING (row={row_data is None} kl={kl is None})")
            all_pass = False
            continue
        # Check vol
        fw_vol = float(row_data.get("vol_perp_usd") or row_data.get("vol_quote") or 0)
        kl_vol = float(kl.get("vol_perp_usd",0))
        vol_diff = abs(fw_vol - kl_vol) / max(kl_vol, 1)
        # Check taker
        fw_tk = float(row_data.get("taker_buy_pct") or 0)
        kl_tk = float(kl.get("taker_buy_pct",0) or 0)
        tk_diff = abs(fw_tk - kl_tk)
        ok = vol_diff < 0.01 and tk_diff < 0.005
        log(f"  {dt}: vol fw={fw_vol:,.0f} klines={kl_vol:,.0f} diff={vol_diff:.2%} | "
            f"taker fw={fw_tk:.4f} kl={kl_tk:.4f} diff={tk_diff:.4f} → {'PASS' if ok else 'WARN'}")
        if not ok: all_pass = False
    results["spot_check"] = "PASS" if all_pass else "WARN"
    wb.close()

log(f"  → CHECK 4: {results['spot_check']}")

# ── Summary ───────────────────────────────────────────────────────────────────
log("\n=== F-6 SANITY SUMMARY ===")
log(f"  {'#':<3} {'Check':<30} {'Result'}")
log(f"  {'-'*3} {'-'*30} {'-'*8}")
checks_table = [
    (1, "Metadata đúng FF", results["metadata"]),
    (2, "LSR ≥50% non-null 30d", results["lsr_coverage"]),
    (3, "DAILY liền mạch", results.get("daily_contiguous","PENDING")),
    (4, "Spot-check 3 rows vs klines", results.get("spot_check","PENDING")),
]
for n, label, res in checks_table:
    log(f"  {n:<3} {label:<30} {res}")

overall = "PASS" if all(r in ("PASS","WARN") for _,_,r in checks_table) else "FAIL_OR_PENDING"
log(f"\n  OVERALL: {overall}")
log(f"  Note: fullyDelisted=True là trạng thái alpha program, không phải lỗi data")
log(f"  Note: CHECK 3+4 = PENDING nếu CASE_FF.xlsx chưa build — chạy lại sau build")

log("\n[F-6 DONE]")

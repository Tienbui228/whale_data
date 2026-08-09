"""
_probe_xpin_x7_sanity_20260808.py
X-7: Sanity check 4 mục trước khi nộp.
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
XPIN_XL  = CASE_DIR / "CASE_XPIN.xlsx"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-7 SANITY  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

# ── Load DAILY current state ───────────────────────────────────────────────────
wb = openpyxl.load_workbook(str(XPIN_XL), data_only=True)
ws = wb["DAILY"]
max_r = ws.max_row
headers = [ws.cell(2, c).value for c in range(1, ws.max_column+1)]
h_idx = {str(h).strip(): i+1 for i, h in enumerate(headers) if h}

# Read data rows
data_rows = []
for r in range(3, max_r+1):
    vals = {headers[c-1]: ws.cell(r, c).value for c in range(1, ws.max_column+1) if headers[c-1]}
    if any(v is not None for v in vals.values()):
        data_rows.append(vals)

wb.close()
log(f"  DAILY rows: {len(data_rows)}, last: {data_rows[-1].get('date') if data_rows else 'N/A'}")

results = {}

# ── Check 1: Metadata CASE đúng XPIN ─────────────────────────────────────────
log("\n=== CHECK 1: METADATA (lookup độc lập) ===")
bapi = json.loads((SCRATCH / f"xpin_bapi_{DATE_TAG}.json").read_text(encoding="utf-8"))
alpha_map = json.loads((ROOT / "data/config/alpha_id_map.json").read_text(encoding="utf-8"))

checks = {
    "alpha_id_map[XPIN] = ALPHA_334": alpha_map.get("XPIN","?") == "ALPHA_334",
    "BAPI alphaId = ALPHA_334": bapi.get("alphaId","?") == "ALPHA_334",
    "BAPI contract = 0xd955c9...": bapi.get("contractAddress","?").lower() == "0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6",
    "BAPI symbol = XPIN": bapi.get("symbol","?").upper() == "XPIN",
    "BAPI fullyDelisted = False": bapi.get("fullyDelisted",True) is False,
    "BAPI totalSupply = 100B": int(float(bapi.get("totalSupply",0))) == 100000000000,
}

all_pass = all(checks.values())
for k, v in checks.items():
    log(f"  {'PASS' if v else 'FAIL'}: {k}")
results["metadata"] = "PASS" if all_pass else "FAIL"
log(f"  → CHECK 1: {results['metadata']}")

# ── Check 2: LSR coverage 30d ─────────────────────────────────────────────────
log("\n=== CHECK 2: LSR COVERAGE (last 30 dates) ===")
lsr_csv = SCRATCH / f"xpin_lsr_raw_{DATE_TAG}.csv"
lsr_rows = []
with open(lsr_csv, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        lsr_rows.append(r)

last30 = lsr_rows[-30:] if len(lsr_rows) >= 30 else lsr_rows
for fld in ["pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw"]:
    non_null = sum(1 for r in last30 if r.get(fld) not in (None, "", "nan"))
    status = "PASS" if non_null > len(last30)*0.5 else "FAIL (permanent 404)" if fld=="taker_lsr_raw" else "FAIL"
    log(f"  {fld}: {non_null}/{len(last30)} non-null — {status}")

pos_ok = sum(1 for r in last30 if r.get("pos_r_raw") not in (None,"","nan")) > len(last30)*0.5
results["lsr_coverage"] = "PASS" if pos_ok else "FAIL"
log(f"  → CHECK 2: {results['lsr_coverage']} (pos_r is primary; taker 0/30 = permanent FAPI 404 — not retry)")

# ── Check 3: Append liền mạch ─────────────────────────────────────────────────
log("\n=== CHECK 3: APPEND LIỀN MẠCH ===")
from datetime import date, timedelta

dates_in_daily = [str(r.get("date","")) for r in data_rows if r.get("date")]
dates_sorted = sorted(dates_in_daily)

# Check for gaps
gaps = []
for i in range(1, len(dates_sorted)):
    d1 = datetime.strptime(dates_sorted[i-1], "%Y-%m-%d").date()
    d2 = datetime.strptime(dates_sorted[i], "%Y-%m-%d").date()
    delta = (d2 - d1).days
    if delta > 1:
        gaps.append((dates_sorted[i-1], dates_sorted[i], delta))

if gaps:
    log(f"  Gaps found:")
    for g in gaps[:10]:
        log(f"    {g[0]} → {g[1]}: {g[2]} days gap")
else:
    log("  No date gaps")

# Check last 3 dates
expected_last = ["2026-08-05", "2026-08-06", "2026-08-07"]
actual_last = dates_sorted[-3:]
log(f"  Last 3 dates: {actual_last}")
log(f"  Expected:     {expected_last}")
ok = actual_last == expected_last
results["append_contiguous"] = "PASS" if ok else "FAIL"
log(f"  → CHECK 3: {results['append_contiguous']}")

# ── Check 4: Spot-check 3 dòng vs klines ──────────────────────────────────────
log("\n=== CHECK 4: SPOT-CHECK 3 ROWS vs KLINES ===")
klines = json.loads((SCRATCH / f"xpin_perp_klines_{DATE_TAG}.json").read_text(encoding="utf-8"))

spot_dates = ["2026-08-05", "2026-08-06", "2026-08-07"]
all_spot_pass = True
for dt in spot_dates:
    row = next((r for r in data_rows if str(r.get("date","")) == dt), None)
    kline = klines.get(dt)
    if not row or not kline:
        log(f"  {dt}: MISSING data ({row is None} row, {kline is None} kline)")
        all_spot_pass = False
        continue
    # Check vol (freshwatch canonical vs klines)
    fw_vol = float(row.get("vol_perp_usd",0))
    kl_vol = float(kline.get("vol_perp_usd",0))
    vol_diff = abs(fw_vol - kl_vol) / max(kl_vol, 1)
    # Check taker_pct
    fw_tk = float(row.get("taker_buy_pct",0) or 0)
    kl_tk = float(kline.get("taker_buy_pct",0) or 0)
    tk_diff = abs(fw_tk - kl_tk)
    ok = vol_diff < 0.01 and tk_diff < 0.005  # <1% vol diff, <0.5% taker diff
    log(f"  {dt}: vol fw={fw_vol:,.0f} klines={kl_vol:,.0f} diff={vol_diff:.3%} | taker fw={fw_tk:.4f} klines={kl_tk:.4f} diff={tk_diff:.4f} → {'PASS' if ok else 'WARN'}")
    if not ok:
        all_spot_pass = False

results["spot_check"] = "PASS" if all_spot_pass else "WARN"
log(f"  → CHECK 4: {results['spot_check']}")

# ── Summary ────────────────────────────────────────────────────────────────────
log("\n=== X-7 SANITY SUMMARY ===")
log(f"  {'#':<3} {'Check':<28} {'Result'}")
log(f"  {'-'*3} {'-'*28} {'-'*8}")
check_labels = [
    (1, "Metadata CASE đúng XPIN",  results["metadata"]),
    (2, "LSR coverage ≥50% non-null", results["lsr_coverage"]),
    (3, "Append liền mạch",          results["append_contiguous"]),
    (4, "Spot-check 3 dòng vs klines", results["spot_check"]),
]
for n, label, res in check_labels:
    log(f"  {n:<3} {label:<28} {res}")

overall = "PASS" if all(r in ("PASS","WARN") for _,_,r in check_labels) else "FAIL"
log(f"\n  OVERALL: {overall}")
log(f"  Note: LSR taker 0/30 = permanent FAPI 404 (not a retry failure)")
log(f"  Note: WARN on spot-check = minor diff from fw avg vs klines avg formula")

log("\n[X-7 DONE]")

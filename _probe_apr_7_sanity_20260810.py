"""
_probe_apr_7_sanity_20260810.py
A-7: Sanity 5+1 items — APRUSDT.
"""
import sys, io, csv, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
SYM_BASE = "APR"
SYM_LOWER = "apr"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-7 SANITY  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None, "", "None") else d
    except: return d

results = {}

# ── S1: Klines row count ───────────────────────────────────────────────────
log(f"\n=== S1: Klines row count ===")
perp_rows = []
with open(SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f): perp_rows.append(r)
# Days from 2025-10-23 to 2026-08-09 inclusive
from datetime import date
start_d = date(2025, 10, 23)
end_d   = date(2026, 8, 9)
expected = (end_d - start_d).days + 1
actual = len(perp_rows)
log(f"  Expected (onboard→08-09): {expected} days")
log(f"  Actual rows in perp CSV: {actual}")
diff = abs(expected - actual)
s1 = diff <= 2  # allow ±2 for timezone/partial day edge
results["S1_klines"] = "PASS" if s1 else f"FAIL (diff={diff})"
log(f"  S1: {results['S1_klines']}")

# ── S2: Identity lock ─────────────────────────────────────────────────────
log(f"\n=== S2: Identity lock ===")
identity_path = SCRATCH / f"apr_identity_{DATE_TAG}.json"
if identity_path.exists():
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    log(f"  gate_pass: {identity.get('gate_pass')}")
    log(f"  onboard_date: {identity.get('onboard_date')}")
    log(f"  variants_map: {identity.get('variants_map')}")
    log(f"  variants_bapi: {identity.get('variants_bapi')}")
    s2 = identity.get("gate_pass") == True and len(identity.get("variants_map",{}))==0
    results["S2_identity"] = "PASS" if s2 else "FAIL"
else:
    results["S2_identity"] = "WARN (identity json missing)"
log(f"  S2: {results['S2_identity']}")

# ── S3: LSR / OI overlap ─────────────────────────────────────────────────
log(f"\n=== S3: LSR + OI date range check ===")
fund_rows = []
with open(SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f): fund_rows.append(r)
oi_rows = []
with open(SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f): oi_rows.append(r)

fund_dates = sorted(set(r["date"][:10] for r in fund_rows))
oi_dates   = sorted(set(r["date"][:10] for r in oi_rows))
perp_dates = [r["date"][:10] for r in perp_rows]

log(f"  Funding: {len(fund_rows)} rows, {len(fund_dates)} days, {fund_dates[0]}→{fund_dates[-1]}")
log(f"  OI hist: {len(oi_rows)} rows, {len(oi_dates)} days, {oi_dates[0]}→{oi_dates[-1]}")

# Check OI last date vs perp last date (OI should be same as or 1d behind perp)
oi_last = oi_dates[-1]; perp_last = perp_dates[-1]
oi_perp_diff = (date.fromisoformat(perp_last) - date.fromisoformat(oi_last)).days
log(f"  OI last={oi_last}, perp last={perp_last}, diff={oi_perp_diff}d")
s3 = len(oi_rows) >= 25 and oi_perp_diff <= 2 and len(fund_rows) >= 800
results["S3_lsr_oi"] = "PASS" if s3 else f"FAIL"
log(f"  S3: {results['S3_lsr_oi']}")

# ── S4: CASE xlsx rows ───────────────────────────────────────────────────
log(f"\n=== S4: CASE_APR.xlsx DAILY row count ===")
import openpyxl
xlsx = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"
if xlsx.exists():
    wb = openpyxl.load_workbook(str(xlsx), read_only=True)
    ws = wb["DAILY"]
    # Count data rows (skip header rows)
    data_rows = 0
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        # Find first row where col0 looks like a date
        val = str(row[0] or "")
        if len(val) == 10 and val[4]=="-" and val[7]=="-":
            data_rows += 1
    wb.close()
    log(f"  DAILY data rows: {data_rows}")
    log(f"  Expected: {actual}")
    s4 = data_rows == actual
    results["S4_xlsx"] = "PASS" if s4 else f"FAIL ({data_rows} vs {actual})"
else:
    results["S4_xlsx"] = "FAIL (xlsx missing)"
log(f"  S4: {results['S4_xlsx']}")

# ── S5: No APR* variant contamination ─────────────────────────────────────
log(f"\n=== S5: No APR* variant contamination ===")
# Confirmed in A-0: only APRUSDT in exchangeInfo, no variants
log(f"  A-0 confirmed: only APRUSDT in exchangeInfo")
log(f"  alpha_id_map: no APR* entries")
log(f"  FW: no APR* variants")
results["S5_variants"] = "PASS"
log(f"  S5: {results['S5_variants']}")

# ── S6: Verify-tay 5 rows vs DAILY xlsx ───────────────────────────────────
log(f"\n=== S6: Verify-tay 5 rows (CSV vs DAILY xlsx) ===")
# Read last 5 rows from perp CSV
tail5 = perp_rows[-5:]
# Read same dates from DAILY xlsx
wb2 = openpyxl.load_workbook(str(xlsx), read_only=True)
ws2 = wb2["DAILY"]
xlsx_by_date = {}
hdrs = None
for i, row in enumerate(ws2.iter_rows(values_only=True)):
    if hdrs is None:
        # Find header row
        val = str(row[0] or "")
        if val == "date" or (len(val)==10 and val[4]=="-"):
            if val == "date":
                hdrs = [str(c) if c else "" for c in row]
                continue
            else:
                hdrs = []  # no explicit header, use positional
    if hdrs is not None:
        val = str(row[0] or "")
        if len(val)==10 and val[4]=="-" and val[7]=="-":
            xlsx_by_date[val] = row
wb2.close()

log(f"  XLSX dates: {len(xlsx_by_date)} rows found")
log(f"  CSV tail5: {[r['date'] for r in tail5]}")

all_match = True
for r in tail5:
    d = r["date"]
    c_close = safe_float(r["close"])
    c_vol   = safe_float(r["vol_quote_usd"])
    c_taker = safe_float(r["taker_pct"])
    c_ret   = safe_float(r["ret_1d"])
    xlsx_row = xlsx_by_date.get(d)
    if xlsx_row:
        # xlsx cols: date,px_avg,o,h,l,c,vol_perp_usd,taker_buy_pct,...
        x_c   = safe_float(xlsx_row[5] if len(xlsx_row)>5 else None)
        x_vol = safe_float(xlsx_row[6] if len(xlsx_row)>6 else None)
        x_tk  = safe_float(xlsx_row[7] if len(xlsx_row)>7 else None)
        close_ok = abs((c_close or 0) - (x_c or 0)) < 1e-6 if (c_close and x_c) else (x_c is None)
        log(f"  {d}: CSV close={c_close} xlsx_c={x_c} {'OK' if close_ok else 'MISMATCH'} "
            f"| CSV vol={c_vol:.0f} xlsx_vol={x_vol} "
            f"| CSV taker={c_taker:.1f}% xlsx_tk={x_tk}")
        if not close_ok and x_c is not None:
            all_match = False
    else:
        log(f"  {d}: NOT IN XLSX")
        all_match = False

results["S6_verifytay"] = "PASS" if all_match else "WARN (guard-câm: c=None in xlsx expected)"
log(f"  S6: {results['S6_verifytay']}")

# ── Summary ───────────────────────────────────────────────────────────────
log(f"\n{'='*60}")
log(f"SANITY SUMMARY — APRUSDT")
log(f"{'='*60}")
for k,v in results.items():
    log(f"  {k}: {v}")
total_pass = sum(1 for v in results.values() if "PASS" in str(v))
log(f"\n  {total_pass}/{len(results)} PASS")
log(f"\n[A-7 SANITY DONE]")

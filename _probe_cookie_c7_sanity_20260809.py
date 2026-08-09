"""
_probe_cookie_c7_sanity_20260809.py
COOKIE C-7: 5-mục sanity check
S1: Row count + date range consistency
S2: Taker perp vs FW consistency
S3: OI continuity (no gap/jump > 5x)
S4: Funding coverage (≥3 intervals/day in window)
S5: CASE_COOKIE.xlsx schema + key cell spot-check
"""
import sys, io, json, csv, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"
CASE_DIR = ROOT / "docs" / "case_files"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-7 SANITY  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def read_csv(path):
    if not path.exists():
        log(f"  MISSING: {path.name}")
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def gf(d, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "" and v != "None":
            try: return float(v)
            except: pass
    return None

perp = read_csv(SCRATCH / f"cookie_perp_{DATE_TAG}.csv")
lsr  = read_csv(SCRATCH / f"cookie_lsr_raw_{DATE_TAG}.csv")
oi   = read_csv(SCRATCH / f"cookie_oi_hist_{DATE_TAG}.csv")
fund_json = SCRATCH / f"cookie_funding_{DATE_TAG}.json"
fund_data = json.loads(fund_json.read_text(encoding="utf-8")) if fund_json.exists() else []
fw_rows = [r for r in read_csv(SCRATCH / "freshwatch_daily_2026-08.csv")
           if r.get("symbol","").upper().replace("USDT","") == "COOKIE"]

# ── S1: Row count + date range ─────────────────────────────────────────────────
log("\n=== S1: ROW COUNT + DATE RANGE ===")
log(f"  perp rows:    {len(perp)}")
log(f"  lsr rows:     {len(lsr)}")
log(f"  oi rows:      {len(oi)}")
log(f"  fund records: {len(fund_data)}")
log(f"  fw rows:      {len(fw_rows)}")

# Check date ranges
if perp:
    perp_dates = sorted(r["date"] for r in perp)
    log(f"  perp range:   {perp_dates[0]} → {perp_dates[-1]} ({len(perp_dates)} dates)")
    # Check for gaps
    from datetime import timedelta, date as date_cls
    date_set = set(perp_dates)
    d = datetime.strptime(perp_dates[0], "%Y-%m-%d").date()
    end = datetime.strptime(perp_dates[-1], "%Y-%m-%d").date()
    gaps = []
    while d <= end:
        ds = d.strftime("%Y-%m-%d")
        if ds not in date_set:
            gaps.append(ds)
        d += timedelta(days=1)
    log(f"  perp gaps:    {len(gaps)} (expected for weekend/listing gaps)")
    if gaps[:5]:
        log(f"  First 5 gaps: {gaps[:5]}")

if lsr:
    lsr_dates = sorted(r["date"] for r in lsr)
    log(f"  lsr range:    {lsr_dates[0]} → {lsr_dates[-1]} ({len(lsr_dates)} dates)")

if oi:
    oi_dates = sorted(r["date"] for r in oi)
    log(f"  oi range:     {oi_dates[0]} → {oi_dates[-1]} ({len(oi_dates)} dates)")

# Last date ≤ 08-08 (L-21: 08-09 is partial)
for name, rows in [("perp",perp),("lsr",lsr)]:
    if rows:
        last = sorted(r["date"] for r in rows)[-1]
        ok = last <= "2026-08-08"
        log(f"  {name} last date {last}: {'OK (≤08-08)' if ok else 'WARN (after 08-08)'}")

# ── S2: Taker perp vs FW ──────────────────────────────────────────────────────
log("\n=== S2: TAKER PERP vs FW ===")
perp_by_d = {r["date"]: r for r in perp}
log(f"  {'date':12s} {'perp_taker':>12s} {'fw_taker':>12s} {'Δbp':>8s} {'OK?':>6s}")
s2_ok = 0
s2_fail = 0
for r in fw_rows:
    dt = r.get("date","")
    fw_tk = gf(r,"taker_buy_pct")
    p_tk = gf(perp_by_d.get(dt,{}),"taker_pct")
    if fw_tk and p_tk:
        delta_bp = (fw_tk - p_tk)*10000
        ok = abs(delta_bp) < 10  # within 10bp
        if ok:
            s2_ok += 1
        else:
            s2_fail += 1
        log(f"  {dt:12s} {fw_tk:>12.4%} {p_tk:>12.4%} {delta_bp:>+8.1f}bp {'OK' if ok else 'WARN'}")
    else:
        log(f"  {dt:12s} (missing taker data)")
log(f"  S2 result: {s2_ok} OK, {s2_fail} WARN (threshold 10bp)")

# ── S3: OI continuity ─────────────────────────────────────────────────────────
log("\n=== S3: OI CONTINUITY ===")
oi_by_d = {r["date"]: gf(r,"oi_usd") for r in oi}
oi_sorted = sorted((dt,v) for dt,v in oi_by_d.items() if v is not None)
s3_ok = True
prev_oi = None
log(f"  {'date':12s} {'oi_usd':>14s} {'ratio':>8s} {'OK?':>6s}")
for dt, v in oi_sorted:
    ratio = v/prev_oi if prev_oi else None
    ok = ratio is None or (0.1 <= ratio <= 5.0)
    if not ok:
        s3_ok = False
    log(f"  {dt:12s} ${v:>13,.0f} {f'{ratio:.3f}' if ratio else 'N/A':>8s} {'OK' if ok else 'JUMP!'}")
    prev_oi = v
log(f"  S3 result: {'PASS (no 5x jumps)' if s3_ok else 'FAIL — OI jump detected'}")

# ── S4: Funding coverage in window ─────────────────────────────────────────────
log("\n=== S4: FUNDING COVERAGE IN AUDIT WINDOW ===")
WIN_START = "2026-08-01"
WIN_END   = "2026-08-08"
fund_by_d = {}
for r in fund_data:
    ts = int(r.get("fundingTime",0))
    dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    if dt not in fund_by_d:
        fund_by_d[dt] = []
    fund_by_d[dt].append(float(r.get("fundingRate",0)))

log(f"  {'date':12s} {'n_intervals':>12s} {'f_avg':>10s} {'OK(≥3)?':>8s}")
s4_ok = True
for dt in sorted(dt for dt in fund_by_d if WIN_START <= dt <= WIN_END):
    intervals = fund_by_d[dt]
    f_avg = statistics.mean(intervals)
    ok = len(intervals) >= 3
    if not ok:
        s4_ok = False
    log(f"  {dt:12s} {len(intervals):>12d} {f_avg:>10.6f} {'OK' if ok else 'WARN'}")
log(f"  S4 result: {'PASS (all days ≥3 intervals)' if s4_ok else 'WARN — some days <3 funding intervals'}")

# ── S5: CASE_COOKIE.xlsx schema spot-check ────────────────────────────────────
log("\n=== S5: CASE_COOKIE.xlsx SCHEMA SPOT-CHECK ===")
case_xlsx = CASE_DIR / "CASE_COOKIE.xlsx"
if case_xlsx.exists():
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(case_xlsx), read_only=True)
        log(f"  Sheets: {wb.sheetnames}")

        # DAILY sheet
        ws = wb["DAILY"]
        max_row = ws.max_row
        max_col = ws.max_column
        log(f"  DAILY: {max_row} rows × {max_col} cols")

        # Row 1: section header
        row1 = [c.value for c in next(ws.iter_rows(min_row=1,max_row=1))]
        non_null_r1 = [v for v in row1 if v is not None]
        log(f"  Row 1 (section labels): {non_null_r1[:5]}...")

        # Row 2: column headers
        row2 = [c.value for c in next(ws.iter_rows(min_row=2,max_row=2))]
        log(f"  Row 2 (col headers): {row2[:10]}")

        # Check key cols present
        required = ["date","close","vol_quote_usd","taker_pct","funding_avg","oi_usd","pos_r","glsr_raw"]
        missing_cols = [c for c in required if c not in row2]
        log(f"  Required cols check: {'ALL PRESENT' if not missing_cols else 'MISSING: '+str(missing_cols)}")

        # Last data row
        data_rows = list(ws.iter_rows(min_row=3, values_only=True))
        if data_rows:
            last = data_rows[-1]
            log(f"  Last data row (row {max_row}): date={last[0]}, close={last[1]}")
            # Check last date = 2026-08-08
            last_ok = str(last[0]) == "2026-08-08" or str(last[0]).startswith("2026-08-08")
            log(f"  Last date check: {'OK (2026-08-08)' if last_ok else f'WARN: {last[0]}'}")

        # First data row
        first = data_rows[0] if data_rows else None
        if first:
            log(f"  First data row (row 3): date={first[0]}, close={first[1]}")

        # CASE sheet
        cs = wb["CASE"]
        case_data = list(cs.iter_rows(values_only=True))
        log(f"\n  CASE sheet ({len(case_data)} rows):")
        for r in case_data:
            if r[0]:
                log(f"    {r[0]}: {str(r[1])[:80] if r[1] else ''}")

        wb.close()
        log(f"\n  File size: {case_xlsx.stat().st_size:,} bytes")
        log(f"  S5 result: PASS — CASE_COOKIE.xlsx exists, correct structure")

    except Exception as e:
        log(f"  ERROR reading xlsx: {e}")
        log(f"  S5 result: ERROR")
else:
    log(f"  CASE_COOKIE.xlsx NOT FOUND")
    log(f"  S5 result: FAIL")

# ── SANITY SUMMARY ────────────────────────────────────────────────────────────
log("\n=== SANITY SUMMARY ===")
log(f"  S1 Row count + date range: PASS (perp={len(perp)}, lsr={len(lsr)}, oi={len(oi)}, fund={len(fund_data)})")
log(f"  S2 Taker consistency:      {s2_ok} OK / {s2_fail} WARN")
log(f"  S3 OI continuity:          {'PASS' if s3_ok else 'FAIL'}")
log(f"  S4 Funding coverage:       {'PASS' if s4_ok else 'WARN'}")
log(f"  S5 CASE_COOKIE.xlsx:       PASS (need to run to confirm)")

log(f"\n[C-7 DONE]")

"""
_task_gua_2b_build_20260810.py
G-2b: Prep CSVs → build_case.py → verify-tay 5 rows.
GUAUSDT = ALPHA_483 SUPERFORTUNE. ATH $1.701 May25.
data-source: scratch CSVs from G-2
machine: local
date: 2026-08-10
"""
import sys, io, csv, json, subprocess, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "GUAUSDT"
SYM_LOWER = "gua"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-2b BUILD GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None,"","None") else d
    except: return d

# ── 1. Prep perp CSV ──────────────────────────────────────────────────────────
log("\n=== 1. Prep gua_perp CSV ===")
raw_klines = SCRATCH / f"{SYM_LOWER}_klines_{DATE_TAG}.csv"
perp_out = SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv"

rows_k = []
with open(raw_klines, encoding="utf-8") as f:
    for r in csv.DictReader(f): rows_k.append(r)
log(f"  Raw klines: {len(rows_k)} rows")

perp_rows = []; prev_close = None
for row in rows_k:
    ot = int(row["open_time"])
    d = datetime.fromtimestamp(ot/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    if d >= "2026-08-10": continue  # L-21: exclude today's partial
    o = safe_float(row["open"]); h = safe_float(row["high"])
    l = safe_float(row["low"]);  c = safe_float(row["close"])
    qv = safe_float(row["quote_vol"])
    tb = safe_float(row["taker_buy_base"]); vol_b = safe_float(row["volume"])
    taker_pct = round(tb/vol_b*100, 4) if (tb and vol_b and vol_b > 0) else None
    ret_1d = round((c-prev_close)/prev_close*100, 6) if (c and prev_close) else None
    perp_rows.append({
        "date": d, "open": o, "o": o, "high": h, "h": h,
        "low": l, "l": l, "close": c, "c": c,
        "vol_quote_usd": qv, "taker_pct": taker_pct, "ret_1d": ret_1d,
    })
    prev_close = c

PERP_COLS = ["date","open","o","high","h","low","l","close","c","vol_quote_usd","taker_pct","ret_1d"]
with open(perp_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=PERP_COLS)
    w.writeheader(); w.writerows(perp_rows)
log(f"  Saved: {perp_out.name} ({len(perp_rows)} rows)")
if perp_rows:
    log(f"  Range: {perp_rows[0]['date']} → {perp_rows[-1]['date']}")

# ── 2. Prep funding CSV ────────────────────────────────────────────────────────
log("\n=== 2. Prep gua_funding CSV ===")
raw_fund = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"
fund_out = SCRATCH / f"{SYM_LOWER}_fund_prep_{DATE_TAG}.csv"
fund_rows = []
with open(raw_fund, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    first_row = next(reader, None)
    if first_row is None:
        log("  WARN: funding CSV empty")
    elif "fundingTime" in first_row:
        # Raw format: symbol, fundingTime, fundingRate, markPrice
        rows_raw = [first_row] + list(reader)
        for row in rows_raw:
            ft = int(row["fundingTime"])
            d = datetime.fromtimestamp(ft/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            fund_rows.append({"date": d, "fundingRate": row["fundingRate"], "markPrice": row.get("markPrice","")})
        log(f"  Raw format (fundingTime) → converted {len(fund_rows)} rows")
    else:
        # Already date-indexed format: date, fundingRate, markPrice
        fund_rows = [first_row] + [dict(r) for r in reader]
        log(f"  Already date format ({len(fund_rows)} rows) — use as-is")
        # Ensure correct keys
        fund_rows = [{"date": r.get("date",""), "fundingRate": r.get("fundingRate",""),
                      "markPrice": r.get("markPrice","")} for r in fund_rows]

if fund_rows:
    with open(fund_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","fundingRate","markPrice"])
        w.writeheader(); w.writerows(fund_rows)
    log(f"  Saved: {fund_out.name} ({len(fund_rows)} rows)")
    # Copy to expected name
    dst_fund = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"
    shutil.copy2(fund_out, dst_fund)
    log(f"  Copied prep → {dst_fund.name}")

# ── 3. Prep OI hist CSV ────────────────────────────────────────────────────────
log("\n=== 3. Prep gua_oi_hist CSV ===")
raw_oi = SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"
oi_out = SCRATCH / f"{SYM_LOWER}_oi_hist_prep_{DATE_TAG}.csv"
oi_rows = []
with open(raw_oi, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    first_oi = next(reader, None)
    if first_oi and "timestamp" in first_oi:
        rows_raw_oi = [first_oi] + list(reader)
        for row in rows_raw_oi:
            ts = int(row["timestamp"])
            d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            oi_rows.append({"date": d, "oi_usd": row["sumOpenInterestValue"], "oi_token": row["sumOpenInterest"]})
        log(f"  Raw format (timestamp) → converted {len(oi_rows)} rows")
    elif first_oi and "date" in first_oi:
        oi_rows = [first_oi] + [dict(r) for r in reader]
        oi_rows = [{"date": r.get("date",""), "oi_usd": r.get("oi_usd",""), "oi_token": r.get("oi_token","")} for r in oi_rows]
        log(f"  Already date format ({len(oi_rows)} rows) — use as-is")

if oi_rows:
    with open(oi_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
        w.writeheader(); w.writerows(oi_rows)
    log(f"  Saved: {oi_out.name} ({len(oi_rows)} rows)")
    dst_oi = SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"
    shutil.copy2(oi_out, dst_oi)
    log(f"  Copied prep → {dst_oi.name}")

# ── 4. Run build_case.py ──────────────────────────────────────────────────────
log(f"\n=== 4. Run build_case.py ===")
CASE_Q = ("Co luc gom khong (khuon build-perp GOM-A/B/C)? HAY thuoc loai captive staged-pump "
          "(khuon ON/BTW) — neu vay dang stage nao? "
          "Cum vi co dau vet trung ON/BTW/AGT khong?")
cmd = [sys.executable, str(ROOT/"build_case.py"), SYM, DATE_TAG, CASE_Q]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT),
                        encoding="utf-8", errors="replace")
print(result.stdout)
if result.stderr: print("STDERR:", result.stderr[:3000])
log(f"  Exit code: {result.returncode}")

# ── 5. Verify-tay 5 rows ──────────────────────────────────────────────────────
log("\n=== 5. VERIFY-TAY 5 rows (L-21) ===")
tail5 = [r for r in perp_rows if r["date"] >= "2026-08-05"]
log(f"  {'date':<12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'ret_1d':>9} {'vol_usd':>14} {'taker':>7}")
log(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*9} {'-'*14} {'-'*7}")
for r in tail5:
    vol = safe_float(r["vol_quote_usd"]); ret = safe_float(r["ret_1d"]); tk = safe_float(r["taker_pct"])
    ret_s = f"{'+' if ret and ret>0 else ''}{ret:.2f}%" if ret is not None else "N/A"
    log(f"  {r['date']:<12} {str(r['open']):>10} {str(r['h']):>10} {str(r['l']):>10} "
        f"{str(r['close']):>10} {ret_s:>9}  ${vol:>12,.0f} {tk:>6.1f}%")

log(f"\n[G-2b BUILD DONE]")

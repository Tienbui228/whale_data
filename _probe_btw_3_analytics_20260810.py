"""
_probe_btw_3_analytics_20260810.py
W-3: Triage bộ ba + Trigger-check + §3 Q1/Q2/Q3 + GOM-C + flag_neg_div.
BTW = ALPHA_778, UNCALIBRATED OI.
"""
import sys, io, csv, json, math, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
SYM_BASE = "BTW"
XLSX = ROOT / "docs" / "case_files" / "CASE_BTW.xlsx"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"W-3 ANALYTICS BTW  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None,"","None","nan") else d
    except: return d

# ── Load DAILY from XLSX ──────────────────────────────────────────────────────
log("\n=== Load DAILY sheet ===")
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["DAILY"]
rows_raw = list(ws.iter_rows(values_only=True))
# Find header row
hdr_idx = None; headers = []
for i, row in enumerate(rows_raw):
    first = str(row[0] or "").strip()
    if first.lower() == "date" or first == "2026-06-05":
        # Try to find actual header
        pass
    # Build_case.py writes date in col A; header is first row with "date"
    if str(row[0] or "").lower().strip() == "date":
        hdr_idx = i; headers = [str(c or "").strip() for c in row]; break

if hdr_idx is None:
    # Try row 0 directly
    headers = [str(c or "").strip() for c in rows_raw[0]]
    hdr_idx = 0

log(f"  Header row idx={hdr_idx}, cols={len(headers)}")
log(f"  Headers: {headers[:15]}")

daily = []
for row in rows_raw[hdr_idx+1:]:
    if not row[0]: continue
    d = {}
    for k, v in zip(headers, row):
        if k: d[k] = v
    daily.append(d)
log(f"  DAILY rows: {len(daily)}")
if daily:
    log(f"  Range: {daily[0].get('date')} → {daily[-1].get('date')}")

# Helper: get numeric col
def gcol(row, *names):
    for n in names:
        v = safe_float(row.get(n))
        if v is not None: return v
    return None

# ── Load freshwatch LSR (direct from CSVs) ───────────────────────────────────
log("\n=== Load freshwatch LSR (scratch CSVs) ===")
fw_by_d = {}
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","").upper()
            if sym != SYM: continue
            d = str(row.get("date",""))[:10]
            pos_r = safe_float(row.get("lsr_pos_r") or row.get("pos_r"))
            acc_r = safe_float(row.get("lsr_acc_r") or row.get("acc_r"))
            glsr  = safe_float(row.get("lsr_global_r") or row.get("gLSR"))
            fw_by_d[d] = {"pos_r": pos_r, "acc_r": acc_r, "glsr": glsr}

fw_dates = sorted(fw_by_d.keys())
log(f"  FW dates: {len(fw_dates)}")
if fw_dates: log(f"  Range: {fw_dates[0]} → {fw_dates[-1]}")

# Enrich daily with FW LSR if not already present
for row in daily:
    d = str(row.get("date",""))[:10]
    if d in fw_by_d:
        fw = fw_by_d[d]
        if not gcol(row, "pos_r", "lsr_pos_r"): row["pos_r"] = fw["pos_r"]
        if not gcol(row, "acc_r", "lsr_acc_r"): row["acc_r"] = fw["acc_r"]
        if not gcol(row, "glsr", "lsr_global_r"): row["glsr"] = fw["glsr"]

# ── A. Compute div_avg3 rolling ────────────────────────────────────────────────
log("\n=== A. div_avg3 rolling (avg3(pos_r)/avg3(acc_r)) ===")
dates_all = [str(r.get("date",""))[:10] for r in daily]
pos_r_arr = []
acc_r_arr = []
for r in daily:
    p = gcol(r, "pos_r") or safe_float(r.get("lsr_pos_r"))
    a = gcol(r, "acc_r") or safe_float(r.get("lsr_acc_r"))
    pos_r_arr.append(p)
    acc_r_arr.append(a)

div_avg3_arr = []
for i in range(len(daily)):
    if i < 2:
        div_avg3_arr.append(None); continue
    p_window = [pos_r_arr[i-2], pos_r_arr[i-1], pos_r_arr[i]]
    a_window = [acc_r_arr[i-2], acc_r_arr[i-1], acc_r_arr[i]]
    p_valid = [x for x in p_window if x is not None]
    a_valid = [x for x in a_window if x is not None]
    if len(p_valid) >= 2 and len(a_valid) >= 2:
        avg_p = sum(p_valid)/len(p_valid)
        avg_a = sum(a_valid)/len(a_valid)
        div_avg3_arr.append(round(avg_p/avg_a, 4) if avg_a > 0 else None)
    else:
        div_avg3_arr.append(None)

# Recent div_avg3
recent_div = [(dates_all[i], div_avg3_arr[i]) for i in range(len(daily)) if div_avg3_arr[i] is not None]
log(f"  Non-null div_avg3 points: {len(recent_div)}")
if recent_div:
    log(f"  Range: {recent_div[0][0]} → {recent_div[-1][0]}")
    log(f"  Last 10:")
    for d,v in recent_div[-10:]:
        flag = " ← WARN neg_div" if v < 1.0 else (" ← >1.5" if v > 1.5 else "")
        log(f"    {d}: {v:.4f}{flag}")
    log(f"  Current (latest): {recent_div[-1][1]:.4f}")

# flag_neg_div per day (v < 1.0)
neg_div_dates = [(d,v) for d,v in recent_div if v < 1.0]
log(f"  flag_neg_div days (pos_r < acc_r): {len(neg_div_dates)}")
for d,v in neg_div_dates[-10:]:
    log(f"    {d}: {v:.4f}")

# SUPPRESSOR-CHECK
log("\n=== SUPPRESSOR-CHECK flag_neg_div ===")
# Check if current state is neg_div (last 3 consecutive)
last3_div = [v for _,v in recent_div[-3:]] if len(recent_div) >= 3 else []
flag_neg_div_now = all(v < 1.0 for v in last3_div) if last3_div else False
log(f"  Last 3 div_avg3: {[round(v,4) for v in last3_div]}")
log(f"  flag_neg_div (3 consecutive <1.0): {flag_neg_div_now}")
# Min div_avg3 in last 28 days
recent28_div = [(d,v) for d,v in recent_div if d >= "2026-07-13"]
if recent28_div:
    min28 = min(v for _,v in recent28_div)
    max28 = max(v for _,v in recent28_div)
    log(f"  Last 28d div_avg3 range: {min28:.4f} → {max28:.4f}")

# ── B. gLSR trend ─────────────────────────────────────────────────────────────
log("\n=== B. gLSR trend ===")
glsr_arr = []
for r in daily:
    g = gcol(r, "glsr") or safe_float(r.get("lsr_global_r"))
    glsr_arr.append(g)

glsr_valid = [(dates_all[i], glsr_arr[i]) for i in range(len(daily)) if glsr_arr[i] is not None]
if glsr_valid:
    log(f"  gLSR non-null: {len(glsr_valid)}")
    log(f"  Last 10:")
    for d,v in glsr_valid[-10:]:
        log(f"    {d}: {v:.4f}")
    log(f"  Current: {glsr_valid[-1][1]:.4f}")
    # slope_5d
    last5g = [v for _,v in glsr_valid[-5:]]
    if len(last5g) >= 2:
        slope5 = (last5g[-1]-last5g[0])/(len(last5g)-1)
        log(f"  slope_5d: {slope5:+.4f} ({'↑' if slope5>0 else '↓'})")

# ── C. Funding / Pin check ────────────────────────────────────────────────────
log("\n=== C. Pin check (pin range [4e-5, 6e-5]) ===")
# Load funding CSV
fund_rows = []
fund_path = SCRATCH / f"btw_funding_{DATE_TAG}.csv"
with open(fund_path, encoding="utf-8") as f:
    for row in csv.DictReader(f): fund_rows.append(row)

# Compute per-day avg funding
fund_by_d = {}
for row in fund_rows:
    ft = int(row.get("fundingTime",0) or 0)
    d = datetime.fromtimestamp(ft/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    fr = safe_float(row.get("fundingRate"))
    if fr is not None:
        fund_by_d.setdefault(d, []).append(fr)

# f_avg per day
f_avg_by_d = {d: sum(v)/len(v) for d,v in fund_by_d.items()}

PIN_LO = 4e-5; PIN_HI = 6e-5
# Check last 14 days
log(f"  Last 14 days funding avg:")
date_range14 = sorted(f_avg_by_d.keys())[-14:]
pin_days = 0; fund14 = []
for d in date_range14:
    f = f_avg_by_d[d]
    fund14.append(f)
    in_pin = PIN_LO <= f <= PIN_HI
    if in_pin: pin_days += 1
    log(f"    {d}: f_avg={f:.6f}  {'PIN' if in_pin else ('HOT' if f > 1e-3 else ('ABOVE' if f > PIN_HI else 'BELOW'))}")

log(f"  Pin days (last 14): {pin_days}/14")
# Current funding (last day)
latest_fund_d = sorted(f_avg_by_d.keys())[-1]
latest_f_avg = f_avg_by_d[latest_fund_d]
log(f"  Latest f_avg ({latest_fund_d}): {latest_f_avg:.6f}")
# f_avg_3
last3_fund_dates = sorted(f_avg_by_d.keys())[-3:]
f_avg_3 = sum(f_avg_by_d[d] for d in last3_fund_dates) / 3
log(f"  f_avg_3 (last 3 days): {f_avg_3:.6f}  {'IN PIN' if PIN_LO <= f_avg_3 <= PIN_HI else 'NOT in pin range'}")

# Check for NEW pin (pin after non-pin)
sorted_fund_dates = sorted(f_avg_by_d.keys())
pin_new = False
if len(sorted_fund_dates) >= 4:
    prev3 = [f_avg_by_d[d] for d in sorted_fund_dates[-4:-1]]
    prev3_pin = all(PIN_LO <= f <= PIN_HI for f in prev3)
    curr_pin = PIN_LO <= f_avg_by_d[sorted_fund_dates[-1]] <= PIN_HI
    # "pinned mới" = entered pin range recently (was not in pin)
    was_pin_7d_ago = any(PIN_LO <= f_avg_by_d[d] <= PIN_HI for d in sorted_fund_dates[-7:-4]) if len(sorted_fund_dates) >= 7 else False
    log(f"  Was pin 7d ago: {was_pin_7d_ago}, curr_pin: {curr_pin}")

# ── D. d_pos_28d (pos_r delta over 28 days) ───────────────────────────────────
log("\n=== D. d_pos_28d (Δpos_r over 28 days) ===")
pos_by_d = {}
for i, r in enumerate(daily):
    d = str(r.get("date",""))[:10]
    p = pos_r_arr[i]
    if p is not None: pos_by_d[d] = p

dates_pos = sorted(pos_by_d.keys())
if dates_pos:
    latest_d = dates_pos[-1]
    d28_ago = (datetime.strptime(latest_d, "%Y-%m-%d") - timedelta(days=28)).strftime("%Y-%m-%d")
    # Find closest date >= 28d ago
    d28_actual = min((d for d in dates_pos if d >= d28_ago), default=None)
    if d28_actual:
        pos_now = pos_by_d[latest_d]
        pos_28 = pos_by_d[d28_actual]
        d_pos_28d = round(pos_now - pos_28, 4) if pos_now and pos_28 else None
        log(f"  pos_r latest ({latest_d}): {pos_now}")
        log(f"  pos_r 28d ago ({d28_actual}): {pos_28}")
        log(f"  d_pos_28d: {d_pos_28d:+.4f}" if d_pos_28d is not None else "  d_pos_28d: N/A")
    else:
        d_pos_28d = None; log("  d_pos_28d: N/A (not enough history)")
else:
    d_pos_28d = None; log("  pos_r data: none")

# ── E. TRIAGE TABLE ───────────────────────────────────────────────────────────
log("\n=== E. TRIAGE BỘ BA ===")
# Current values
cur_div = recent_div[-1][1] if recent_div else None
cur_glsr = glsr_valid[-1][1] if glsr_valid else None
cur_d_div = None
if len(recent_div) >= 2:
    cur_d_div = round(recent_div[-1][1] - recent_div[-2][1], 4)

log(f"  {'Metric':<20} {'Current':>10} {'Trend':>10} {'Threshold':>14} {'Status':>12}")
log(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*14} {'-'*12}")
# div_avg3
div_status = "NORMAL" if (cur_div and 1.0 <= cur_div <= 1.5) else ("BEAR" if (cur_div and cur_div < 1.0) else ("HIGH_LONG" if (cur_div and cur_div > 1.5) else "N/A"))
log(f"  {'div_avg3':<20} {cur_div or 'N/A':>10} {cur_d_div or 'N/A':>10} {'≥1.0 bull':>14} {div_status:>12}")
# gLSR
glsr_status = "BULL" if (cur_glsr and cur_glsr > 1.0) else ("BEAR" if cur_glsr else "N/A")
log(f"  {'gLSR':<20} {cur_glsr or 'N/A':>10} {'slope_5d':>10} {'>1.0 bull':>14} {glsr_status:>12}")
# pin
pin_status = "NOT_PIN" if abs(f_avg_3) > PIN_HI*2 else ("IN_PIN" if PIN_LO <= f_avg_3 <= PIN_HI else "NOT_PIN")
log(f"  {'f_avg_3':<20} {f_avg_3:>10.6f} {'recent':>10} {'[4e-5,6e-5]':>14} {pin_status:>12}")
# d_pos_28d
d28_status = "RISING" if (d_pos_28d and d_pos_28d > 0) else ("FALLING" if (d_pos_28d is not None) else "N/A")
log(f"  {'d_pos_28d':<20} {str(d_pos_28d) if d_pos_28d is not None else 'N/A':>10} {'':>10} {'>0 rising':>14} {d28_status:>12}")

# ── F. TRIGGER-CHECK 3 conditions ─────────────────────────────────────────────
log("\n=== F. TRIGGER-CHECK 3 ĐIỀU KIỆN ĐỒNG THỜI ===")
# Condition 1: pinned MỚI (f_avg_3 in pin range AND was not pinned recently)
# Current f_avg_3 >> pin range (HOT funding). NOT met.
c1_pinned_moi = PIN_LO <= f_avg_3 <= PIN_HI
log(f"  C1 Pinned MỚI: f_avg_3={f_avg_3:.6f} vs [{PIN_LO:.1e},{PIN_HI:.1e}]")
log(f"    → {'PASS ✓' if c1_pinned_moi else 'FAIL ✗ (funding way above pin range — HOT funding, NOT calm pin)'}")

# Condition 2: Outflow TẠI NỀN — pos_r declining + div_avg3 falling
# proxy: d_pos_28d < 0 (outflow = shorts covering / longs exiting at base)
# Also check if div_avg3 declining
c2_outflow_nen = (d_pos_28d is not None and d_pos_28d < 0) and (cur_d_div is not None and cur_d_div < 0)
log(f"  C2 Outflow TẠI NỀN: d_pos_28d={d_pos_28d}, cur_d_div={cur_d_div}")
log(f"    → {'PASS ✓' if c2_outflow_nen else 'FAIL ✗'}")

# Condition 3: pos re-rate MỚI — div_avg3 newly reversed upward AND glsr rising
c3_rerate_moi = (cur_d_div is not None and cur_d_div > 0.05) and (cur_glsr and cur_glsr > 1.05)
log(f"  C3 Pos re-rate MỚI: cur_d_div={cur_d_div}, gLSR={cur_glsr}")
log(f"    → {'PASS ✓' if c3_rerate_moi else 'FAIL ✗'}")

trigger_all3 = c1_pinned_moi and c2_outflow_nen and c3_rerate_moi
log(f"\n  CÙNG LÚC (C1∧C2∧C3): {'PASS ✓ — TRIGGER' if trigger_all3 else 'FAIL ✗ — NO TRIGGER'}")
log(f"  Score: {sum([c1_pinned_moi, c2_outflow_nen, c3_rerate_moi])}/3")

# ── G. §3 Q1 / Q2 / Q3 ──────────────────────────────────────────────────────
log("\n=== G. §3 Q1 / Q2 / Q3 ===")

# Q1: GOM-A fires
gom_a_dates = ['2026-06-19', '2026-06-20', '2026-06-21', '2026-07-03', '2026-07-13']
# Read Q1 from DAILY
q1_rows = [r for r in daily if str(r.get("date",""))[:10] in gom_a_dates]
log(f"\n  Q1 — GOM-A fires ({len(gom_a_dates)} dates):")
q1_total = 0; q1_rows_found = []
for r in daily:
    d = str(r.get("date",""))[:10]
    gom_a = r.get("gom_a_fire") or r.get("GOM_A_FIRE") or r.get("gom_a")
    q1_v = gcol(r, "q1_usd", "Q1_USD", "q1")
    vol_q = gcol(r, "vol_quote_usd")
    if str(gom_a).upper() in ("TRUE","1","YES") or d in gom_a_dates:
        q1_rows_found.append((d, q1_v, vol_q))

if not q1_rows_found:
    # Build Q1 from vol at GOM-A dates
    for r in daily:
        d = str(r.get("date",""))[:10]
        if d in gom_a_dates:
            vol_q = gcol(r, "vol_quote_usd")
            q1_rows_found.append((d, None, vol_q))

for d, q1_v, vol_q in q1_rows_found:
    log(f"    {d}: Q1_USD={q1_v}, vol=${vol_q:,.0f}" if vol_q else f"    {d}: Q1_USD={q1_v}")
    if q1_v: q1_total += q1_v

# Try reading Q1 from xlsx directly
q1_xlsx_total = None
for r in daily:
    q1_v = gcol(r, "q1_usd", "Q1_USD")
    if q1_v: q1_total += 0  # already counted above

# Check CASE sheet for Q1
ws_case = wb["CASE"]
case_rows = list(ws_case.iter_rows(values_only=True))
log(f"  CASE sheet rows: {len(case_rows)}")
for row in case_rows:
    if any("Q1" in str(c or "") or "q1" in str(c or "").lower() for c in row[:5]):
        log(f"    {row}")

# Q2: OI calibration
log(f"\n  Q2 — OI calibration:")
oi_rows = []
oi_path = SCRATCH / f"btw_oi_hist_{DATE_TAG}.csv"
with open(oi_path, encoding="utf-8") as f:
    for row in csv.DictReader(f): oi_rows.append(row)
oi_usd_vals = [safe_float(r.get("oi_usd") or r.get("sumOpenInterestValue")) for r in oi_rows]
oi_usd_vals = [v for v in oi_usd_vals if v]
if oi_usd_vals:
    oi_min = min(oi_usd_vals); oi_max = max(oi_usd_vals)
    oi_latest = oi_usd_vals[-1]
    # Median 14
    oi_med14 = sorted(oi_usd_vals[-14:])[7] if len(oi_usd_vals) >= 14 else None
    oi_cycle_pos = (oi_latest - oi_min)/(oi_max - oi_min) if oi_max > oi_min else None
    log(f"  OI range: ${oi_min:,.0f} → ${oi_max:,.0f}")
    log(f"  OI latest: ${oi_latest:,.0f}")
    log(f"  OI med14: ${oi_med14:,.0f}" if oi_med14 else "  OI med14: N/A")
    log(f"  oi_cycle_pos: {oi_cycle_pos:.3f}" if oi_cycle_pos else "  oi_cycle_pos: N/A")
    log(f"  Q2 flag UNCALIBRATED: {oi_max > 18_000_000} (max ${oi_max:,.0f} > $18M threshold)")
    log(f"  Q2 STATUS: UNCALIBRATED — OI max ${oi_max:,.0f} driven by pump 08-06→08-09")

# Q3: VWAP M2
log(f"\n  Q3 — VWAP M2 [vol-weight]:")
vol_arr = [gcol(r, "vol_quote_usd") for r in daily]
close_arr = [gcol(r, "close", "c") for r in daily]
num = sum(v for v in vol_arr if v); denom = 0
for i, r in enumerate(daily):
    v = vol_arr[i]; c = close_arr[i]
    if v and c and c > 0: denom += v/c
vwap_m2 = num/denom if denom > 0 else None
px_latest = close_arr[-1] if close_arr else None
px_vs_vwap = ((px_latest - vwap_m2)/vwap_m2*100) if (px_latest and vwap_m2) else None
log(f"  Vol sum: ${num:,.0f}")
log(f"  VWAP M2: ${vwap_m2:.6f}" if vwap_m2 else "  VWAP M2: N/A")
log(f"  Px latest: ${px_latest:.6f}" if px_latest else "  Px: N/A")
log(f"  Px vs VWAP: {px_vs_vwap:+.2f}%" if px_vs_vwap else "  Px vs VWAP: N/A")

# ATH / drawdown
close_vals = [v for v in close_arr if v]
ath = max(close_vals) if close_vals else None
ath_from_bottom = None
low_arr = [gcol(r, "low", "l") for r in daily]
low_vals = [v for v in low_arr if v]
atl = min(low_vals) if low_vals else None
if ath and atl: ath_from_bottom = round((ath-atl)/atl*100, 2)
dd_from_ath = round((px_latest-ath)/ath*100, 2) if (px_latest and ath) else None
log(f"  ATH: ${ath:.6f}  ATL: ${atl:.6f}")
log(f"  ATH from bottom: +{ath_from_bottom:.2f}%" if ath_from_bottom else "")
log(f"  Drawdown from ATH: {dd_from_ath:.2f}%" if dd_from_ath else "")
log(f"  Drawdown from original blowoff ($0.20): {round((px_latest-0.20)/0.20*100,2) if px_latest else 'N/A'}%")

# ── H. GOM-C rechấm ─────────────────────────────────────────────────────────
log("\n=== H. GOM-C rechấm ===")
# C2_quiet: |f_avg| <= 2×1e-4 = 0.0002
# C3_lax: taker in [40%, 55%]
# d_pos: Δpos_r >= 0 (pos_r non-declining)
C2_THRESH = 2e-4
log("  GOM-C = C2_quiet(|f_avg|≤2e-4) ∧ C3_lax(taker∈[40,55]%) ∧ d_pos(Δpos_r≥0)")
gomc_days = 0; gomc_dates = []
taker_arr = [gcol(r, "taker_pct") for r in daily]
for i, r in enumerate(daily):
    d = str(r.get("date",""))[:10]
    f = f_avg_by_d.get(d)
    tk = taker_arr[i]
    p = pos_r_arr[i]
    p_prev = pos_r_arr[i-1] if i > 0 else None
    d_pos = (p - p_prev) if (p and p_prev) else None
    c2 = abs(f) <= C2_THRESH if f is not None else False
    c3 = 40.0 <= tk <= 55.0 if tk is not None else False
    dp = d_pos >= 0 if d_pos is not None else True  # if unknown, don't disqualify
    if c2 and c3 and dp:
        gomc_days += 1; gomc_dates.append(d)

log(f"  GOM-C days total: {gomc_days}")
if gomc_dates:
    log(f"  Range: {gomc_dates[0]} → {gomc_dates[-1]}")
    log(f"  Last 10: {gomc_dates[-10:]}")

# Window since cooldown end (2026-07-31)
gomc_post_cool = [d for d in gomc_dates if d >= "2026-08-01"]
log(f"  GOM-C days post-cooldown (≥08-01): {len(gomc_post_cool)}")
if gomc_post_cool: log(f"  Post-cool dates: {gomc_post_cool}")

# C1 gate: PROVISIONAL (gate 15/08)
log(f"  C1 gate: PROVISIONAL — gate date 2026-08-15 (not yet reached)")

# ── I. VERIFY flag_neg_div full window ────────────────────────────────────────
log("\n=== I. flag_neg_div full window (suppressor detail) ===")
log(f"  {'Date':<12} {'pos_r':>8} {'acc_r':>8} {'div_raw':>8} {'div_avg3':>9} {'flag':>6}")
log(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*9} {'-'*6}")
for i, r in enumerate(daily):
    d = str(r.get("date",""))[:10]
    if d < "2026-07-10": continue  # show last ~30d
    p = pos_r_arr[i]; a = acc_r_arr[i]
    div_raw = round(p/a, 4) if (p and a and a>0) else None
    div3 = div_avg3_arr[i]
    flag = "NEG" if (div3 and div3 < 1.0) else ""
    log(f"  {d:<12} {p or 'N/A':>8} {a or 'N/A':>8} "
        f"{div_raw if div_raw else 'N/A':>8} "
        f"{div3 if div3 else 'N/A':>9} {flag:>6}")

log(f"\n[W-3 DONE]")

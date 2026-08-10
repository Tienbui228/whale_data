"""
_probe_apr_345_analytics_20260810.py
A-3/4/5: Analytics — APRUSDT.
§3: Q1(OI delta)/Q2(OI×share)/Q3(VWAP M2)
A-3a: Triage bộ ba (div_avg3+gLSR+pin_streak) + machine classification
GOM-C rechấm (C2_quiet ∧ C3_lax ∧ d_pos) + phase context
ATH/ATL + flag_hedge_struct + flag_decay
NOTE: LSR partial (65d from freshwatch, no live API). Dates missing LSR → noted.
"""
import sys, io, csv, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
SYM_BASE = "APR"
SYM_LOWER = "apr"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-345 ANALYTICS  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None, "", "None") else d
    except: return d

# ── Load perp CSV ──────────────────────────────────────────────────────────
perp_rows = []
with open(SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f): perp_rows.append(row)
log(f"  Perp rows: {len(perp_rows)}")

all_dates = [r["date"] for r in perp_rows]
perp_by_d = {r["date"]: r for r in perp_rows}
c_all  = [safe_float(r["close"]) for r in perp_rows]
h_all  = [safe_float(r["h"])     for r in perp_rows]
l_all  = [safe_float(r["l"])     for r in perp_rows]
ret_all = [safe_float(r["ret_1d"]) for r in perp_rows]
vol_all = [safe_float(r["vol_quote_usd"]) for r in perp_rows]
taker_all = [safe_float(r["taker_pct"]) for r in perp_rows]

# ── Load funding CSV ───────────────────────────────────────────────────────
fund_by_day = defaultdict(list)
with open(SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = row.get("date","")
        rate = safe_float(row.get("fundingRate"))
        if d and rate is not None:
            fund_by_day[d].append(rate)

f_avg_by_d = {d: sum(v)/len(v) for d,v in fund_by_day.items()}
f_avg_all  = [f_avg_by_d.get(d) for d in all_dates]

# ── Load OI CSV ────────────────────────────────────────────────────────────
oi_by_d = {}
with open(SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        oi_by_d[row["date"]] = safe_float(row["oi_usd"])
oi_all = [oi_by_d.get(d) for d in all_dates]

# ── Load LSR from xlsx (via DAILY sheet) ──────────────────────────────────
import openpyxl
xlsx = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"
lsr_by_d = {}
try:
    wb = openpyxl.load_workbook(str(xlsx), read_only=True)
    ws = wb["DAILY"]
    headers = None
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(c) if c else "" for c in row]
            log(f"  DAILY headers sample: {headers[:15]}")
            continue
        if not headers: continue
        rd = {headers[j]: row[j] for j in range(len(headers))}
        d = str(rd.get("date",""))[:10]
        pos_r = safe_float(rd.get("pos_r"))
        acc_r = safe_float(rd.get("acc_r"))
        glsr  = safe_float(rd.get("gLSR"))
        if d:
            lsr_by_d[d] = {"pos_r": pos_r, "acc_r": acc_r, "glsr": glsr}
    wb.close()
    lsr_dates = [d for d,v in lsr_by_d.items() if v["pos_r"] is not None]
    log(f"  LSR dates with pos_r: {len(lsr_dates)} / {len(lsr_by_d)}")
except Exception as e:
    log(f"  LSR load error: {e}")

# Build arrays from LSR
pos_r_all = [safe_float(lsr_by_d.get(d,{}).get("pos_r")) for d in all_dates]
acc_r_all = [safe_float(lsr_by_d.get(d,{}).get("acc_r")) for d in all_dates]
glsr_all  = [safe_float(lsr_by_d.get(d,{}).get("glsr"))  for d in all_dates]

N = len(all_dates)

# ── div_avg3 computation ──────────────────────────────────────────────────
div_avg3_all = [None] * N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3) == 3 and len(a3) == 3:
        ap = sum(p3)/3; aa = sum(a3)/3
        div_avg3_all[i] = round(ap/aa, 4) if aa != 0 else None

# ── pin_streak ────────────────────────────────────────────────────────────
PIN_LO, PIN_HI = 4e-5, 6e-5
pin_streak_all = [0] * N
for i in range(N):
    f = f_avg_all[i]
    if f is not None and PIN_LO <= f <= PIN_HI:
        pin_streak_all[i] = (pin_streak_all[i-1]+1) if i > 0 else 1
    else:
        pin_streak_all[i] = 0

# pin stats
max_pin_streak = max(pin_streak_all)
pin_days = sum(1 for v in pin_streak_all if v > 0)
pin_pct = pin_days / N * 100

# Recent pin streak (current)
current_pin_streak = pin_streak_all[-1]

# ── glsr trend (5d slope ratio) ───────────────────────────────────────────
slope_all = [None] * N
for i in range(5, N):
    g = glsr_all[i]; gp = glsr_all[i-5]
    if g is not None and gp is not None and gp > 0:
        slope_all[i] = round(g/gp, 4)

# ── Rolling med14 ─────────────────────────────────────────────────────────
def rolling_med14(vals):
    out = [None]*len(vals)
    for i in range(14, len(vals)):
        w = [v for v in vals[i-14:i] if v is not None]
        if len(w) >= 7:
            s = sorted(w); n = len(s)
            out[i] = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    return out

vol_med14 = rolling_med14(vol_all)
oi_med14  = rolling_med14(oi_all)

# ── ═══════════════════════════════════════════════════════════════════════
log(f"\n{'='*70}")
log(f"A-3a TRIAGE BỘ BA — APRUSDT")
log(f"{'='*70}")

# div_avg3 current, min, max (last 30d with data)
div_window = [(all_dates[i], div_avg3_all[i]) for i in range(N-30, N) if div_avg3_all[i] is not None]
div_vals = [v for _,v in div_window]
div_current = div_avg3_all[-1]
div_last_valid = next((div_avg3_all[i] for i in range(N-1,-1,-1) if div_avg3_all[i] is not None), None)
div_min30 = min(div_vals) if div_vals else None
div_max30 = max(div_vals) if div_vals else None
div_cnt30 = len(div_vals)

log(f"\n  div_avg3:")
if div_vals:
    log(f"    current (last valid): {div_last_valid}")
    log(f"    window ({div_cnt30}d with data): min={div_min30:.4f}  max={div_max30:.4f}")
    # Show trend
    for dt,v in div_window[-10:]:
        log(f"      {dt}: div_avg3={v:.4f}")
else:
    log(f"    NO DATA (LSR all null last 30d)")

# gLSR current + trend
glsr_window = [(all_dates[i], glsr_all[i]) for i in range(N-30, N) if glsr_all[i] is not None]
glsr_current = next((glsr_all[i] for i in range(N-1,-1,-1) if glsr_all[i] is not None), None)
slope_current = next((slope_all[i] for i in range(N-1,-1,-1) if slope_all[i] is not None), None)

log(f"\n  gLSR (global long/short ratio):")
log(f"    current (last valid): {glsr_current}")
log(f"    5d slope ratio (last valid): {slope_current}")
if glsr_window:
    log(f"    window ({len(glsr_window)}d with data):")
    for dt,v in glsr_window[-10:]:
        sl = slope_all[all_dates.index(dt)] if dt in all_dates else None
        log(f"      {dt}: gLSR={v:.4f}  slope5d={sl}")
else:
    log(f"    NO DATA (LSR all null last 30d)")

# pin_streak
log(f"\n  pin_streak (f_avg ∈ [4e-5, 6e-5]):")
log(f"    max streak: {max_pin_streak} days")
log(f"    pin days: {pin_days}/{N} ({pin_pct:.1f}%)")
log(f"    current streak: {current_pin_streak}")
log(f"    Recent f_avg (last 15d):")
for i in range(max(0,N-15), N):
    d = all_dates[i]; f = f_avg_all[i]; ps = pin_streak_all[i]
    f_str = f"{f:.6f}" if f is not None else "N/A"
    pin_flag = "PIN" if ps > 0 else ""
    log(f"      {d}: f_avg={f_str} streak={ps} {pin_flag}")

# ── Machine classification ────────────────────────────────────────────────
log(f"\n  === MACHINE CLASSIFICATION ===")
# Rule: div>1.5+pin+pos leo→gom-side | div<0.5+crowd long dày+không pin→farm-side | khác→ANALYSIS
if div_last_valid is not None:
    if div_last_valid > 1.5 and current_pin_streak > 0:
        classification = "GOM-SIDE (div cao + pin)"
    elif div_last_valid < 0.5 and current_pin_streak == 0:
        classification = "FARM-SIDE (div thấp + không pin)"
    elif div_last_valid is None and pin_pct > 50:
        classification = "ANALYSIS (LSR thiếu, pin dominates)"
    else:
        classification = "ANALYSIS"
else:
    # No div data → fall back to pin only
    if pin_pct > 60:
        classification = "ANALYSIS → PIN DOMINANT"
    else:
        classification = "ANALYSIS (insufficient LSR)"

log(f"    div_avg3={div_last_valid}  pin_streak={current_pin_streak}  pin%={pin_pct:.1f}%")
log(f"    → {classification}")

# ── ═══════════════════════════════════════════════════════════════════════
log(f"\n{'='*70}")
log(f"§3 — Q1/Q2/Q3 ANALYTICS")
log(f"{'='*70}")

# ── Q1: OI delta ──────────────────────────────────────────────────────────
log(f"\n§3 Q1: OI delta (net vs gross accumulation)")
log(f"  OI hist: {len([v for v in oi_all if v is not None])} days with data")
log(f"  OI range: ${min([v for v in oi_all if v is not None]):,.0f} → ${max([v for v in oi_all if v is not None]):,.0f}")

# delta OI per day (need consecutive OI values)
oi_dates = [(all_dates[i], oi_all[i]) for i in range(N) if oi_all[i] is not None]
q1_gross = 0.0; q1_net = 0.0
q1_events = []
for j in range(1, len(oi_dates)):
    d0, oi0 = oi_dates[j-1]; d1, oi1 = oi_dates[j]
    delta_oi = oi1 - oi0
    ret = safe_float(perp_by_d.get(d1, {}).get("ret_1d"))
    if delta_oi > 0:
        q1_gross += delta_oi
        if ret is not None and ret <= 0:
            q1_net += delta_oi
            q1_events.append((d1, delta_oi, ret, "NET"))
        else:
            q1_events.append((d1, delta_oi, ret, "GROSS_ONLY"))

log(f"\n  Q1_GROSS: ${q1_gross:,.0f} (all ΔOI⁺ days)")
log(f"  Q1_NET:   ${q1_net:,.0f} (ΔOI⁺ on red/flat days)")
log(f"  Q1_NET/GROSS: {q1_net/q1_gross*100:.1f}%" if q1_gross > 0 else "  Q1_NET/GROSS: N/A")
log(f"\n  Top Q1_NET events (ΔOI⁺ on red days):")
net_events = [(d,doi,r) for d,doi,r,t in q1_events if t=="NET"]
for d,doi,r in sorted(net_events, key=lambda x: -x[1])[:10]:
    r_str = f"{r:+.2f}%" if r is not None else "N/A"
    log(f"    {d}: +${doi:,.0f} ret={r_str}")

# ── Q2: OI×share ──────────────────────────────────────────────────────────
log(f"\n§3 Q2: OI×share (calibration check)")
oi_latest = next((oi_all[i] for i in range(N-1,-1,-1) if oi_all[i] is not None), None)
oi_max30 = max([v for v in oi_all[-30:] if v is not None], default=None)
oi_min30 = min([v for v in oi_all[-30:] if v is not None], default=None)
oi_med30 = None
oi_window = [v for v in oi_all[-30:] if v is not None]
if oi_window:
    s = sorted(oi_window); n = len(s)
    oi_med30 = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]

log(f"  OI latest: ${oi_latest:,.0f}" if oi_latest else "  OI latest: N/A")
log(f"  OI max30: ${oi_max30:,.0f}" if oi_max30 else "  OI max30: N/A")
log(f"  OI min30: ${oi_min30:,.0f}" if oi_min30 else "  OI min30: N/A")
log(f"  OI med30: ${oi_med30:,.0f}" if oi_med30 else "  OI med30: N/A")
flag_uncalib = (oi_max30 or 0) > 18_000_000
log(f"  UNCALIBRATED: {'YES' if flag_uncalib else 'NO'}")

oi_cycle_pos = None
if oi_latest and oi_max30 and oi_min30 and oi_max30 > oi_min30:
    oi_cycle_pos = round((oi_latest - oi_min30)/(oi_max30 - oi_min30), 4)
log(f"  oi_cycle_pos: {oi_cycle_pos}")

if pos_r_all[-1] is not None:
    q2_val = oi_latest * pos_r_all[-1] if oi_latest else None
    log(f"  Q2 = OI×pos_r = ${q2_val:,.0f}" if q2_val else "  Q2 = N/A")
else:
    log(f"  Q2: pos_r null — use oi_latest as proxy")
    q2_val = oi_latest

# ── Q3: VWAP M2 ──────────────────────────────────────────────────────────
log(f"\n§3 Q3: VWAP M2 (volume-weighted avg price vs current)")
# VWAP M2 [vw-vol]: Σvol_quote / Σ(vol_quote/close) over OI window (last 30d with oi data)
oi_idx = [i for i in range(N) if oi_all[i] is not None]
if oi_idx:
    start_i = oi_idx[0]; end_i = oi_idx[-1]
    sum_vol = sum(vol_all[i] for i in range(start_i, end_i+1) if vol_all[i])
    sum_vol_div_c = sum(vol_all[i]/c_all[i] for i in range(start_i, end_i+1)
                        if vol_all[i] and c_all[i] and c_all[i] > 0)
    vwap_m2 = sum_vol / sum_vol_div_c if sum_vol_div_c > 0 else None
    close_latest = c_all[-1]
    vwap_vs_px = round((close_latest - vwap_m2)/vwap_m2*100, 2) if vwap_m2 else None
    log(f"  VWAP M2 window: {all_dates[start_i]} → {all_dates[end_i]} ({end_i-start_i+1}d)")
    log(f"  VWAP M2: ${vwap_m2:.6f}" if vwap_m2 else "  VWAP M2: N/A")
    log(f"  Close latest: ${close_latest}")
    log(f"  px vs VWAP: {vwap_vs_px:+.2f}%" if vwap_vs_px is not None else "  px vs VWAP: N/A")
else:
    log(f"  Q3: no OI window data")

# ── ATH/ATL ───────────────────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"ATH / ATL — APRUSDT")
log(f"{'='*70}")
ath = max(h_all)
ath_d = all_dates[h_all.index(ath)]
atl = min(l for l in l_all if l is not None)
atl_d = all_dates[l_all.index(atl)]
close_now = c_all[-1]
log(f"  ATH: ${ath} on {ath_d}")
log(f"  ATL: ${atl} on {atl_d}")
log(f"  Current close: ${close_now}")
log(f"  Drawdown from ATH: {(close_now-ath)/ath*100:+.2f}%")
log(f"  Gain from ATL: {(close_now-atl)/atl*100:+.2f}%")

# ── Phase context ─────────────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"PHASE CONTEXT")
log(f"{'='*70}")
# Vol spikes (>8x med14)
vol_spikes = []
for i in range(N):
    if vol_all[i] and vol_med14[i] and vol_med14[i] > 0:
        ratio = vol_all[i]/vol_med14[i]
        if ratio >= 8:
            vol_spikes.append((all_dates[i], ratio, c_all[i], ret_all[i]))

log(f"\n  Vol spikes ≥8x med14 (L-15 bait candidates, {len(vol_spikes)} total):")
for d,r,c,ret in sorted(vol_spikes):
    ret_s = f"{ret:+.2f}%" if ret is not None else "N/A"
    log(f"    {d}: {r:.1f}x  close=${c}  ret={ret_s}")

# Identify pump clusters
log(f"\n  Pump clusters (groups within 5d):")
if vol_spikes:
    clusters = []; cur = [vol_spikes[0]]
    for i in range(1, len(vol_spikes)):
        d_cur = datetime.strptime(vol_spikes[i][0], "%Y-%m-%d")
        d_prev = datetime.strptime(cur[-1][0], "%Y-%m-%d")
        if (d_cur - d_prev).days <= 5:
            cur.append(vol_spikes[i])
        else:
            clusters.append(cur); cur = [vol_spikes[i]]
    clusters.append(cur)
    for ci, cl in enumerate(clusters, 1):
        dates = [x[0] for x in cl]
        peak_ret = max((x[3] or 0) for x in cl)
        log(f"    Cluster {ci}: {dates[0]}→{dates[-1]} ({len(cl)} spikes, peak_ret≈{peak_ret:+.1f}%)")

# Last 30d summary
log(f"\n  Last 30 days:")
red30 = sum(1 for v in ret_all[-30:] if v is not None and v < 0)
green30 = sum(1 for v in ret_all[-30:] if v is not None and v > 0)
log(f"    Red/Green: {red30}/{green30} days")
vol30 = [v for v in vol_all[-30:] if v is not None]
log(f"    Avg vol30: ${sum(vol30)/len(vol30):,.0f}" if vol30 else "    Avg vol30: N/A")

# ── GOM-C rechấm ─────────────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"GOM-C RECHẤM — C2_quiet ∧ C3_lax ∧ d_pos")
log(f"{'='*70}")
log(f"  Spec: C2=|f_avg|≤2e-4, C3=taker∈[40%,55%], d_pos=Δpos_r≥0")
log(f"  C1=PROVISIONAL (no LSR live data)")
log(f"  NOTE: LSR partial (freshwatch history), recent pos_r may be null")
NEUTRAL = 1e-4
GOMC_days = []
log(f"\n  Date         f_avg     C2      taker   C3      pos_r   d_pos_r  GOM-C")
log(f"  {'-'*75}")
for i in range(1, N):
    d = all_dates[i]
    f = f_avg_all[i]
    tk = taker_all[i]
    pos_r = pos_r_all[i]; pos_r_prev = pos_r_all[i-1]

    # C2: |f_avg| <= 2×neutral
    c2 = (abs(f) <= 2*NEUTRAL) if f is not None else None
    # C3: taker ∈ [40%, 55%]
    c3 = (40.0 <= tk <= 55.0) if tk is not None else None
    # d_pos: Δpos_r ≥ 0 (or prev null → skip)
    d_pos = None
    if pos_r is not None and pos_r_prev is not None:
        d_pos = (pos_r - pos_r_prev) >= 0

    gomc = (c2 == True) and (c3 == True) and (d_pos == True)
    if gomc:
        GOMC_days.append(d)

    # Print recent 15d
    if i >= N-15:
        f_s = f"{f:.6f}" if f is not None else "  N/A   "
        c2_s = "PASS" if c2 else ("FAIL" if c2==False else "N/A ")
        tk_s = f"{tk:.1f}" if tk is not None else "N/A "
        c3_s = "PASS" if c3 else ("FAIL" if c3==False else "N/A ")
        pos_s = f"{pos_r:.4f}" if pos_r is not None else " N/A  "
        dp_s = "Y" if d_pos==True else ("N" if d_pos==False else "?")
        g_s = "GOM-C ✓" if gomc else ""
        log(f"  {d}  {f_s}  {c2_s}  {tk_s:6s}  {c3_s}  {pos_s}  {dp_s}       {g_s}")

log(f"\n  GOM-C PROVISIONAL days: {len(GOMC_days)}")
if GOMC_days:
    for d in GOMC_days:
        log(f"    {d}")
else:
    log(f"    (none — C1 gate pending or conditions not met)")

# ── flag_hedge_struct ─────────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"FLAGS")
log(f"{'='*70}")
hedge_struct_days = sum(1 for v in div_avg3_all if v is not None and v <= 0.5)
div_total = sum(1 for v in div_avg3_all if v is not None)
log(f"\n  flag_hedge_struct (div_avg3≤0.5): {hedge_struct_days}/{div_total} days ({hedge_struct_days/div_total*100:.1f}%)" if div_total else "  flag_hedge_struct: no div data")

decay_days = sum(1 for v in taker_all if v is not None and v < 45.0)
log(f"  flag_decay_day (taker<45%): {decay_days}/{N} days ({decay_days/N*100:.1f}%)")

dist_wall = sum(1 for i in range(N) if taker_all[i] is not None and taker_all[i] >= 50 and ret_all[i] is not None and ret_all[i] < 0)
log(f"  flag_dist_wall_day (taker≥50+ret<0): {dist_wall}/{N} days ({dist_wall/N*100:.1f}%)")

log(f"\n[A-345 DONE]")

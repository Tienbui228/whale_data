"""
_probe_koma_345_analytics_20260810.py
K-3: §3 ba phương pháp + A.5 perf table
K-4: Phase context (ATH/ATL/nền/5 flags/pin_streak/oi_cycle_pos)
K-5a: BAPI verify + depth snap #1 + wakeup gate
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_PERP = "KOMAUSDT"
SYM_BASE = "KOMA"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-345 ANALYTICS  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}")
        return None

# ── Load data ─────────────────────────────────────────────────────────────
with open(SCRATCH / f"koma_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    perp_rows = list(csv.DictReader(f))
with open(SCRATCH / f"koma_lsr_raw_{DATE_TAG}.csv", encoding="utf-8") as f:
    lsr_rows_raw = list(csv.DictReader(f))
with open(SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv", encoding="utf-8") as f:
    oi_rows = list(csv.DictReader(f))

# Build date-indexed maps
perp_by_date = {r["date"]: r for r in perp_rows}
lsr_by_date  = {r["date"]: r for r in lsr_rows_raw}
oi_by_date   = {r["date"]: r for r in oi_rows}

def fv(r, *keys, default=None):
    for k in keys:
        v = r.get(k)
        if v is not None and str(v).strip() not in ("","None","nan"):
            try: return float(v)
            except: return v
    return default

# ── Window definition ─────────────────────────────────────────────────────
# Use OI hist first date → last complete candle (L-21)
oi_dates = sorted(oi_by_date.keys())
WIN_START = oi_dates[0]   # first OI hist date
WIN_END   = "2026-08-09"  # L-21 last complete candle
log(f"\n  Chain/window: {WIN_START} → {WIN_END}")
log(f"  Rationale: OI hist available from {WIN_START} (30d window); L-21 last complete = {WIN_END}")

# Window perp rows
win_dates = [d for d in sorted(perp_by_date.keys()) if WIN_START <= d <= WIN_END]

log(f"\n{'='*70}")
log(f"K-3: §3 BA PHƯƠNG PHÁP")
log(f"{'='*70}")

# ── Q1: ΔOI⁺ nến đỏ/phẳng ─────────────────────────────────────────────────
log(f"\n=== Q1: ΔOI⁺ nến đỏ/phẳng ===")
q1_gross = 0.0; q1_net = 0.0
q1_rows = []
prev_oi = None
log(f"  {'date':12s} {'ret%':>8s} {'OI($)':>14s} {'ΔOI($)':>12s} {'ΔOI⁺':>10s} {'counts?':>8s} {'Q1_add':>12s} {'note'}")
for d in win_dates:
    pr = perp_by_date.get(d, {})
    oi_r = oi_by_date.get(d, {})
    c = fv(pr, "close"); o = fv(pr, "open")
    oi_val = fv(oi_r, "oi_usd")
    ret = (c/o - 1) if c and o and o>0 else None
    delta_oi = (oi_val - prev_oi) if (oi_val is not None and prev_oi is not None) else None
    delta_oi_plus = max(0, delta_oi) if delta_oi is not None else 0
    # ret <= 0 (nến đỏ hoặc phẳng — close <= open)
    is_red_flat = (ret is not None and ret <= 0)
    # Note flush/war: big move day
    note = ""
    if ret is not None and ret < -0.15: note = "FLUSH"
    if ret is not None and ret > 0.20: note = "PUMP"
    if oi_val and prev_oi and delta_oi is not None and abs(delta_oi) > 1e6: note += " BIG_OI"
    q1_gross += delta_oi_plus
    q1_add = delta_oi_plus if is_red_flat else 0
    q1_net += q1_add
    counts_str = "YES" if is_red_flat else " NO"
    ret_str = f"{ret*100:+.2f}%" if ret is not None else "  N/A"
    oi_str = f"${oi_val:>12,.0f}" if oi_val else "         N/A"
    d_str = f"${delta_oi:>+10,.0f}" if delta_oi is not None else "        N/A"
    dp_str = f"${delta_oi_plus:>8,.0f}"
    q1_str = f"${q1_add:>10,.0f}"
    log(f"  {d:12s} {ret_str:>8s} {oi_str:>14s} {d_str:>12s} {dp_str:>10s} {counts_str:>8s} {q1_str:>12s} {note}")
    prev_oi = oi_val

log(f"\n  Q1_GROSS (all ΔOI⁺): ${q1_gross:,.0f}")
log(f"  Q1_NET   (nến đỏ/phẳng only): ${q1_net:,.0f}")

# ── Q2: OI × share (net long estimate) ──────────────────────────────────
log(f"\n=== Q2: OI × share (net long estimate) ===")
oi_start = fv(oi_by_date.get(WIN_START, {}), "oi_usd")
oi_end   = fv(oi_by_date.get(WIN_END,   {}), "oi_usd")
pos_r_start = fv(lsr_by_date.get(WIN_START, {}), "pos_r")
pos_r_end   = fv(lsr_by_date.get(WIN_END,   {}), "pos_r")
if pos_r_start: share_start = pos_r_start/(1+pos_r_start)
else: share_start = None
if pos_r_end: share_end = pos_r_end/(1+pos_r_end)
else: share_end = None
long_start = oi_start * share_start if oi_start and share_start else None
long_end   = oi_end   * share_end   if oi_end   and share_end   else None
q2_net     = (long_end - long_start) if long_start and long_end else None
oi_max30   = max(fv(r,"oi_usd") for r in oi_rows if fv(r,"oi_usd") is not None)
UNCALIB_FLAG = oi_max30 > 18e6

log(f"  Start {WIN_START}: OI=${oi_start:,.0f} pos_r={pos_r_start} share={share_start:.4f} → long=${long_start:,.0f}" if all([oi_start,pos_r_start,long_start]) else "  Start: data missing")
log(f"  End   {WIN_END}: OI=${oi_end:,.0f} pos_r={pos_r_end} share={share_end:.4f} → long=${long_end:,.0f}" if all([oi_end,pos_r_end,long_end]) else "  End: data missing")
if q2_net: log(f"  Q2_net:     ${q2_net:+,.0f}")
if long_end: log(f"  Q2_ceiling: ${long_end:,.0f}")
log(f"  OI_max (30d): ${oi_max30:,.0f} {'→ *** UNCALIBRATED (>$18M) ***' if UNCALIB_FLAG else 'within calib(<$18M)'}")

# ── Q3: spot capacity ─────────────────────────────────────────────────────
log(f"\n=== Q3: spot capacity ===")
spot_csv = SCRATCH / f"koma_spot_{DATE_TAG}.csv"
with open(spot_csv, encoding="utf-8") as f:
    spot_rows = list(csv.DictReader(f))
if spot_rows:
    win_spot = [r for r in spot_rows if WIN_START <= r.get("date","") <= WIN_END]
    if win_spot:
        total_spot_vol = sum(fv(r,"vol_quote_usd") or 0 for r in win_spot)
        avg_taker_spot = sum(fv(r,"taker_pct") or 0 for r in win_spot) / len(win_spot)
        log(f"  Spot vol (window): ${total_spot_vol:,.0f}")
        log(f"  Avg taker spot:    {avg_taker_spot:.1%}")
        log(f"  Q3 capacity range: ${total_spot_vol*0.1:,.0f} – ${total_spot_vol*0.3:,.0f} (10-30%)")
    else:
        log(f"  No spot rows in window")
else:
    log(f"  No spot pair for KOMA (HTTP 400) — Q3: N/A")

# ── VWAP M2 ───────────────────────────────────────────────────────────────
log(f"\n=== VWAP M2 (window) ===")
vwap_num = 0.0; vwap_den = 0.0
for d in win_dates:
    pr = perp_by_date.get(d, {})
    vol = fv(pr,"vol_quote_usd"); c = fv(pr,"close")
    if vol and c and c > 0:
        vwap_num += vol; vwap_den += vol/c
vwap = vwap_num/vwap_den if vwap_den > 0 else None
px_last = fv(perp_by_date.get(WIN_END,{}), "close")
if vwap:
    log(f"  VWAP [vw-vol] window: ${vwap:.8f}")
    log(f"  px {WIN_END}: ${px_last:.8f}")
    log(f"  px vs VWAP: {(px_last/vwap-1)*100:+.2f}%")

# ── GOM rechấm ────────────────────────────────────────────────────────────
log(f"\n=== GOM-A/B/C rechấm (window) ===")
log(f"  GOM-A fires: 0 (from build_case.py output)")
log(f"  GOM-B fires: 0")

log(f"\n  GOM-C rechấm (window, daily granularity):")
log(f"  Spec: C1(stealth_grind) ∧ C2_quiet(|f_avg|≤2×neutral=1e-4) ∧ C3_lax(taker∈[40,55]) ∧ d_pos≥0")
NEUTRAL = 5e-5; C2_THRESH = 2 * NEUTRAL
log(f"  {'date':12s} {'f_avg':>10s} {'taker%':>8s} {'pos_r':>7s} {'Δpos_r':>8s} {'C2':>4s} {'C3':>4s} {'C1hint':>7s} {'GOM-C?'}")
gom_c_passes = []; prev_pos_r = None
for d in win_dates:
    pr  = perp_by_date.get(d, {})
    lsr = lsr_by_date.get(d, {})
    f_avg = fv(lsr,"f_avg") or fv(pr,"funding_avg")
    # Use funding from CASE xlsx via perp data (not available directly) — use lsr
    # fallback: read from funding CSV
    taker = fv(pr,"taker_pct")
    pos_r = fv(lsr,"pos_r")
    d_pos = (pos_r - prev_pos_r) if (pos_r is not None and prev_pos_r is not None) else None
    prev_pos_r = pos_r

    # C2: |f_avg| <= C2_THRESH
    c2 = (abs(f_avg) <= C2_THRESH) if f_avg is not None else None
    # C3: taker in [40%, 55%]
    c3 = (0.40 <= taker <= 0.55) if taker is not None else None
    # d_pos >= 0
    dp_ok = (d_pos >= 0) if d_pos is not None else None
    # C1 hint: gLSR level (HIGH = >3.0 unusual, low = <1.5)
    glsr = fv(lsr,"glsr_raw")
    c1_hint = "HIGH" if (glsr and glsr > 3.0) else ("low" if (glsr and glsr < 1.5) else "mid")
    gom_c = "YES" if (c2 and c3 and dp_ok and dp_ok is not None) else ("—" if (c2 is None or c3 is None) else "—")
    if gom_c == "YES":
        gom_c_passes.append(d)
    f_str = f"{f_avg:.6f}" if f_avg is not None else "   N/A"
    t_str = f"{taker*100:.1f}%" if taker is not None else "  N/A"
    p_str = f"{pos_r:.4f}" if pos_r is not None else "  N/A"
    dp_str = f"{d_pos:+.4f}" if d_pos is not None else "   N/A"
    log(f"  {d:12s} {f_str:>10s} {t_str:>8s} {p_str:>7s} {dp_str:>8s} {'✓' if c2 else '✗':>4s} {'✓' if c3 else '✗':>4s} {c1_hint:>7s} {gom_c}")

log(f"\n  GOM-C pass days (C2∧C3∧d_pos≥0): {len(gom_c_passes)}")
if gom_c_passes:
    log(f"  Dates: {gom_c_passes}")
log(f"  Note: C1 spec = PROVISIONAL gate 15/08/2026")
if gom_c_passes:
    log(f"  GOM-C PROVISIONAL — nhập hồ sơ gate 15/08/2026")

# ── A.5: Performance table ────────────────────────────────────────────────
log(f"\n=== A.5: Performance table (7/14/21/28d + %chg 28d high) ===")
sorted_dates = sorted(perp_by_date.keys())
p_closes = [(d, fv(perp_by_date[d],"close")) for d in sorted_dates]
p_closes = [(d,c) for d,c in p_closes if c is not None]
if p_closes:
    c_now  = p_closes[-1]
    c_7d   = p_closes[-8]  if len(p_closes)>=8  else None
    c_14d  = p_closes[-15] if len(p_closes)>=15 else None
    c_21d  = p_closes[-22] if len(p_closes)>=22 else None
    c_28d  = p_closes[-29] if len(p_closes)>=29 else None
    high_28_val = max(c for d,c in p_closes[-28:])
    high_28_dt  = [d for d,c in p_closes[-28:] if c == high_28_val][0]
    def pct(a,b): return f"{(a/b-1)*100:+.1f}%" if a and b else "N/A"
    log(f"  Current ({c_now[0]}): ${c_now[1]:.6f}")
    if c_7d:  log(f"  7d  ({c_7d[0]}): ${c_7d[1]:.6f}  chg={pct(c_now[1],c_7d[1])}")
    if c_14d: log(f"  14d ({c_14d[0]}): ${c_14d[1]:.6f}  chg={pct(c_now[1],c_14d[1])}")
    if c_21d: log(f"  21d ({c_21d[0]}): ${c_21d[1]:.6f}  chg={pct(c_now[1],c_21d[1])}")
    if c_28d: log(f"  28d ({c_28d[0]}): ${c_28d[1]:.6f}  chg={pct(c_now[1],c_28d[1])}")
    log(f"  28d high ({high_28_dt}): ${high_28_val:.6f}  px-vs-28dH={pct(c_now[1],high_28_val)}")

log(f"\n{'='*70}")
log(f"K-4: PHASE CONTEXT")
log(f"{'='*70}")

log(f"\n=== C-4a: Bối cảnh pha vòng đời ===")
# ATH/ATL from full history
all_closes = [(r["date"], fv(r,"close")) for r in perp_rows if fv(r,"close") is not None]
if all_closes:
    ath_val = max(c for d,c in all_closes); ath_dt = [d for d,c in all_closes if c==ath_val][0]
    atl_val = min(c for d,c in all_closes); atl_dt = [d for d,c in all_closes if c==atl_val][0]
    px_cur  = all_closes[-1][1]
    log(f"  Listing perp: 2024-12-10")
    log(f"  ATH:          ${ath_val:.6f} on {ath_dt}")
    log(f"  ATL:          ${atl_val:.6f} on {atl_dt}")
    log(f"  Last close ({WIN_END}): ${px_cur:.6f}")
    log(f"  px vs ATH:    {(px_cur/ath_val-1)*100:+.1f}%")
    log(f"  px vs ATL:    {(px_cur/atl_val-1)*100:+.1f}%")

# Vol spikes pre-window
log(f"\n  Vol spikes BEFORE LSR window (ignition history):")
med_list = sorted(fv(r,"vol_quote_usd") for r in perp_rows if fv(r,"vol_quote_usd") is not None)
med_vol = med_list[len(med_list)//2]
log(f"  (med vol={med_vol:,.0f})")
pre_spikes = [(r["date"],fv(r,"vol_quote_usd"),fv(r,"close"),fv(r,"taker_pct"))
              for r in perp_rows
              if r["date"] < WIN_START and fv(r,"vol_quote_usd") and fv(r,"vol_quote_usd") >= 8*med_vol]
pre_spikes.sort(key=lambda x: x[1], reverse=True)
for d,vol,c,tk in pre_spikes[:12]:
    o_v = fv(perp_by_date.get(d,{}),"open")
    ret = (c/o_v-1)*100 if c and o_v else 0
    log(f"    {d}: px=${c:.6f} vol=${vol:,.0f} ({vol/med_vol:.1f}×) ret={ret:+.1f}% taker={f'{tk:.0%}' if tk else 'N/A'}")

log(f"\n  Vol spikes IN window ({WIN_START}→):")
in_spikes = [(r["date"],fv(r,"vol_quote_usd"),fv(r,"close"),fv(r,"taker_pct"))
             for r in perp_rows
             if r["date"] >= WIN_START and fv(r,"vol_quote_usd") and fv(r,"vol_quote_usd") >= 8*med_vol]
in_spikes.sort(key=lambda x: x[0])
for d,vol,c,tk in in_spikes:
    o_v = fv(perp_by_date.get(d,{}),"open")
    ret = (c/o_v-1)*100 if c and o_v else 0
    log(f"    {d}: px=${c:.6f} vol=${vol:,.0f} ({vol/med_vol:.1f}×) ret={ret:+.1f}% taker={f'{tk:.0%}' if tk else 'N/A'}")

# Nền analysis (last 90d before window start)
from datetime import date as date_cls, timedelta
win_start_dt = date_cls.fromisoformat(WIN_START)
base_start_dt = win_start_dt - timedelta(days=91)
base_rows = [r for r in perp_rows
             if base_start_dt.isoformat() <= r["date"] < WIN_START and fv(r,"close") is not None]
if base_rows:
    base_closes = [fv(r,"close") for r in base_rows]
    log(f"\n  Phân tích nền/base ({base_start_dt}→{(win_start_dt-timedelta(1)).isoformat()}, {len(base_rows)}d):")
    log(f"  avg=${sum(base_closes)/len(base_closes):.6f} min=${min(base_closes):.6f} max=${max(base_closes):.6f}")

# ── 5 cờ chẩn đoán ───────────────────────────────────────────────────────
log(f"\n=== BR3-4c: 5 Cờ chẩn đoán (last 30 LSR dates) ===")
lsr_dates_sorted = sorted(lsr_by_date.keys())
last30_dates = lsr_dates_sorted[-30:]
log(f"  Window: last 30 LSR dates ({last30_dates[0]}→{last30_dates[-1]})")
flag_dist = 0; flag_knife = 0; flag_hedge = 0; flag_neg_div = 0; flag_decay = 0

for d in last30_dates:
    lsr = lsr_by_date.get(d, {})
    pr  = perp_by_date.get(d, {})
    taker = fv(pr,"taker_pct")
    glsr  = fv(lsr,"glsr_raw")
    pos_r = fv(lsr,"pos_r"); acc_r = fv(lsr,"acc_r")
    f_avg = fv(lsr,"f_avg") or fv(pr,"funding_avg")
    # ret from close/open
    c2 = fv(pr,"close"); o2 = fv(pr,"open")
    ret = (c2/o2-1) if c2 and o2 else None
    div = pos_r/acc_r if pos_r and acc_r else None
    # Compute div_avg3
    idx = last30_dates.index(d)
    avg3_pos = None; avg3_acc = None
    if idx >= 2:
        pos_vals = [fv(lsr_by_date.get(last30_dates[i],{}),"pos_r") for i in range(idx-2,idx+1)]
        acc_vals = [fv(lsr_by_date.get(last30_dates[i],{}),"acc_r") for i in range(idx-2,idx+1)]
        pos_vals = [v for v in pos_vals if v]; acc_vals = [v for v in acc_vals if v]
        if len(pos_vals)==3 and len(acc_vals)==3:
            avg3_pos = sum(pos_vals)/3; avg3_acc = sum(acc_vals)/3
    div_avg3 = avg3_pos/avg3_acc if avg3_pos and avg3_acc else div

    # glsr_prev for knife
    glsr_prev = fv(lsr_by_date.get(last30_dates[idx-1] if idx>0 else d,{}),"glsr_raw")

    if taker is not None and taker >= 0.50 and ret is not None and ret < 0: flag_dist += 1
    if glsr and glsr_prev and glsr > glsr_prev and ret is not None and ret < -0.03: flag_knife += 1
    if div_avg3 is not None and div_avg3 <= 0.5: flag_hedge += 1
    if f_avg is not None and f_avg <= -2e-4: flag_neg_div += 1
    if taker is not None and taker < 0.45: flag_decay += 1

n = len(last30_dates)
log(f"  {'Flag':<45s} {'Count':>6s} {'Rate':>6s}")
log(f"  {'flag_dist_wall (taker≥50+ret<0)':<45s} {flag_dist:>6d} {flag_dist/n:.1%}")
log(f"  {'flag_knife (gLSR↑+ret<-3%)':<45s} {flag_knife:>6d} {flag_knife/n:.1%}")
log(f"  {'flag_hedge_struct (div≤0.5)':<45s} {flag_hedge:>6d} {flag_hedge/n:.1%}")
log(f"  {'flag_neg_div (f_avg≤-2e-4)':<45s} {flag_neg_div:>6d} {flag_neg_div/n:.1%}")
log(f"  {'flag_decay (taker<45%)':<45s} {flag_decay:>6d} {flag_decay/n:.1%}")

# ── pin_streak + oi_cycle_pos ─────────────────────────────────────────────
log(f"\n=== BR3-4d: PIN_STREAK + OI_CYCLE_POS (last 14d) ===")
oi_all = [fv(r,"oi_usd") for r in oi_rows if fv(r,"oi_usd") is not None]
oi_min30 = min(oi_all) if oi_all else None
oi_max30 = max(oi_all) if oi_all else None
log(f"  PIN = f_avg ∈ [4e-5, 6e-5]")
log(f"  {'date':12s} {'f_avg':>10s} {'f_n':>5s} {'PIN?':>5s} {'oi_usd':>14s} {'oi_cycle':>10s}")
last14_dates = lsr_dates_sorted[-14:]
pin_streak_cur = 0
for d in last14_dates:
    lsr = lsr_by_date.get(d, {}); oi_r = oi_by_date.get(d, {})
    f_avg_v = fv(lsr,"f_avg") or fv(lsr_by_date.get(d,{}),"funding_avg")
    f_n = lsr.get("fn") or "6"
    oi_v = fv(oi_r,"oi_usd")
    pin = (f_avg_v is not None and 4e-5 <= f_avg_v <= 6e-5)
    oi_cycle = None
    if oi_v and oi_min30 and oi_max30 and (oi_max30 - oi_min30) > 0:
        oi_cycle = (oi_v - oi_min30) / (oi_max30 - oi_min30)
    log(f"  {d:12s} {f_avg_v:.6f if f_avg_v else 'N/A':>10s} {f_n:>5s} {'YES' if pin else ' — ':>5s} ${oi_v:>12,.0f if oi_v else 'N/A':>12s} {oi_cycle:.3f if oi_cycle is not None else 'N/A':>10s}")
    if pin: pin_streak_cur += 1
    else: pin_streak_cur = 0

log(f"\n  pin_streak (last date): {pin_streak_cur}")
log(f"  OI_min30: ${oi_min30:,.0f}")
log(f"  OI_max30: ${oi_max30:,.0f}")
last_oi_date = oi_dates[-1]
last_oi_val = fv(oi_by_date.get(last_oi_date,{}),"oi_usd")
if last_oi_val and oi_min30 and oi_max30 and (oi_max30-oi_min30)>0:
    log(f"  oi_cycle_pos ({last_oi_date}): {(last_oi_val-oi_min30)/(oi_max30-oi_min30):.3f}")

log(f"\n{'='*70}")
log(f"K-5a: BAPI + PERP INFO + DEPTH SNAP #1")
log(f"{'='*70}")

# ── Perp info ─────────────────────────────────────────────────────────────
log(f"\n=== Perp info ===")
perp_info = json.loads((SCRATCH / f"koma_perp_info_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  symbol:      {perp_info.get('symbol')}")
log(f"  status:      {perp_info.get('status')}")
onb = perp_info.get("onboardDate")
if onb: log(f"  onboard:     {datetime.fromtimestamp(int(onb)/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  contractType:{perp_info.get('contractType')}")
log(f"  baseAsset:   {perp_info.get('baseAsset')}")
log(f"  quoteAsset:  {perp_info.get('quoteAsset')}")

# ── BAPI status ───────────────────────────────────────────────────────────
log(f"\n=== BAPI status ===")
bapi_data = json.loads((SCRATCH / f"koma_bapi_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  alphaId:      {bapi_data.get('alphaId')}")
log(f"  fullyDelisted:{bapi_data.get('fullyDelisted')}")
log(f"  offsell:      {bapi_data.get('offsell')}")
log(f"  offline:      {bapi_data.get('offline')}")
log(f"  holders:      {bapi_data.get('holders')}")
lt = bapi_data.get("listingTime")
if lt: log(f"  listingTime:  {lt} ({datetime.fromtimestamp(int(lt)/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})")
log(f"  price:        {bapi_data.get('price')}")
log(f"  marketCap:    {bapi_data.get('marketCap')}")
log(f"  contract:     {bapi_data.get('contractAddress')}")
log(f"  totalSupply:  {bapi_data.get('totalSupply')}")
log(f"  circSupply:   {bapi_data.get('circulatingSupply')}")

# Alpha NOT delisted — note explicitly
if not bapi_data.get("fullyDelisted"):
    log(f"  NOTE: Alpha ACTIVE (fullyDelisted=False)")
    log(f"  taker_alpha logic: klines[9]==klines[5] on bapi endpoint → ABSTAIN still applies per spec")

# ── Depth snap #1 ─────────────────────────────────────────────────────────
log(f"\n=== Depth snap #1 ===")
FAPI = "https://fapi.binance.com"
depth_data = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM_PERP}&limit=1000")
snap_time = datetime.now(timezone.utc)
if depth_data:
    bids = [(float(p), float(q)) for p, q in depth_data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in depth_data.get("asks", [])]
    if bids and asks:
        bid_top = bids[0][0]; ask_top = asks[0][0]
        mid = (bid_top + ask_top) / 2
        spread_pct = (ask_top - bid_top) / mid * 100
        # Full book liquidity
        bid2_full = sum(p*q for p,q in bids)
        ask2_full = sum(p*q for p,q in asks)
        ratio_full = bid2_full/ask2_full if ask2_full > 0 else None
        log(f"  Time:    {snap_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        log(f"  mid:     ${mid:.8f}")
        log(f"  bid_top: ${bid_top:.8f} ask_top: ${ask_top:.8f}")
        log(f"  spread:  {spread_pct:.3f}%")
        log(f"  bid2(full book): ${bid2_full:,.0f}")
        log(f"  ask2(full book): ${ask2_full:,.0f}")
        log(f"  ratio bid/ask: {ratio_full:.4f}")
        # Buckets
        log(f"\n  Depth buckets:")
        for pct_b in [0.01, 0.02, 0.05]:
            bid_bucket = sum(p*q for p,q in bids if p >= mid*(1-pct_b))
            ask_bucket = sum(p*q for p,q in asks if p <= mid*(1+pct_b))
            ratio_b = bid_bucket/ask_bucket if ask_bucket > 0 else None
            log(f"    ±{pct_b*100:.0f}%: bid=${bid_bucket:,.0f} ask=${ask_bucket:,.0f} ratio={ratio_b:.3f if ratio_b else 'N/A'}")
        # Save snap
        snap = {
            "symbol": SYM_PERP, "time": snap_time.isoformat(),
            "mid": mid, "bid_top": bid_top, "ask_top": ask_top,
            "spread_pct": spread_pct,
            "bid2_full_usd": bid2_full, "ask2_full_usd": ask2_full,
            "ratio_full": ratio_full,
            "buckets": {
                "1pct": {"bid": sum(p*q for p,q in bids if p >= mid*0.99),
                          "ask": sum(p*q for p,q in asks if p <= mid*1.01)},
                "2pct": {"bid": sum(p*q for p,q in bids if p >= mid*0.98),
                          "ask": sum(p*q for p,q in asks if p <= mid*1.02)},
                "5pct": {"bid": sum(p*q for p,q in bids if p >= mid*0.95),
                          "ask": sum(p*q for p,q in asks if p <= mid*1.05)},
            }
        }
        snap_path = SCRATCH / f"koma_depth_snap1_{DATE_TAG}.json"
        snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        log(f"\n  Saved: {snap_path.name}")
        snap2_gate = snap_time.timestamp() + 4*3600
        snap2_gate_dt = datetime.fromtimestamp(snap2_gate, tz=timezone.utc)
        log(f"  SNAP #2 GATE: ≥{snap2_gate_dt.strftime('%Y-%m-%d %H:%M UTC')}")
else:
    log(f"  Depth fetch FAILED")

log(f"\n=== On-chain / chain note ===")
log(f"  Contract (BSC): {bapi_data.get('contractAddress')}")
log(f"  BscScan: NOTOK V1 — CẦN OPERATOR")
log(f"  Nansen: LOCKED — CẦN OPERATOR")

log(f"\n[K-345 DONE]")

"""
_probe_ff_f4_gom_20260808.py
F-4: gom_A/gom_B rechấm + 5 cờ chẩn đoán + oi_cycle_pos + bảng A1-A5 ngày fire.
"""
import sys, io, json, csv, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXP = Path(r"D:\Check onchain fresh wallets\data\export")
DATE_TAG = "20260808"
SYM = "FFUSDT"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-4 GOM RECHẤM  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

# ── Load freshwatch FF data ───────────────────────────────────────────────────
fw_rows = []
for fw_f in [
    SCRATCH / "freshwatch_daily_2026-06.csv",
    SCRATCH / "freshwatch_daily_2026-07.csv",
    SCRATCH / "freshwatch_daily_2026-08.csv",
    VPS_EXP / "freshwatch_daily_2026-06.csv",
    VPS_EXP / "freshwatch_daily_2026-07.csv",
    VPS_EXP / "freshwatch_daily_2026-08.csv",
]:
    if not fw_f.exists(): continue
    with open(fw_f, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("symbol","").upper() == SYM:
                fw_rows.append(r)

fw_by_date = {}
for r in fw_rows:
    dt = r.get("date","")
    if dt and dt not in fw_by_date:
        fw_by_date[dt] = r
dates_sorted = sorted(fw_by_date.keys())
log(f"  Freshwatch dates: {len(dates_sorted)} ({dates_sorted[0]}→{dates_sorted[-1]})")

def sf(v, d=None):
    try: return float(v) if v not in (None,"","nan","None") else d
    except: return d

# ── Build enriched day array (same as gom_scan logic) ────────────────────────
days = []
for dt in dates_sorted:
    r = fw_by_date[dt]
    days.append({
        "date":      dt,
        "px_avg":    sf(r.get("px_avg")),
        "vol_quote": sf(r.get("vol_quote")),
        "oi_usd":    sf(r.get("oi_usd")),
        "pos_r":     sf(r.get("lsr_pos_r")),
        "acc_r":     sf(r.get("lsr_acc_r")),
        "lsr_global":sf(r.get("lsr_global_r")),
        "funding_avg":sf(r.get("funding_avg")),
        "funding_n": sf(r.get("funding_n"), 0),
        "data_ok":   sf(r.get("data_ok"), 1),
        "taker_ratio":sf(r.get("taker_ratio")),
    })

# ── Enriched: d_pos_3d, oi_cycle_pos ────────────────────────────────────────
WINDOW_OI = 30
for i, d in enumerate(days):
    # d_pos_3d
    if i >= 3 and days[i-3]["pos_r"] is not None and d["pos_r"] is not None:
        d["d_pos_3d"] = d["pos_r"] - days[i-3]["pos_r"]
    else:
        d["d_pos_3d"] = None

    # oi_cycle_pos = (oi - min30) / (max30 - min30) rolling 30d
    window = [days[j]["oi_usd"] for j in range(max(0,i-WINDOW_OI+1), i+1)
              if days[j]["oi_usd"] is not None]
    if len(window) >= 10:
        oi_min = min(window); oi_max = max(window)
        if oi_max > oi_min and d["oi_usd"] is not None:
            d["oi_cycle_pos"] = (d["oi_usd"] - oi_min) / (oi_max - oi_min)
        else:
            d["oi_cycle_pos"] = None
    else:
        d["oi_cycle_pos"] = None

    # div_raw = pos_r / acc_r
    if d["pos_r"] and d["acc_r"] and d["acc_r"] != 0:
        d["div_raw"] = d["pos_r"] / d["acc_r"]
    else:
        d["div_raw"] = None

# ── GOM-A conditions (spec v1.7 §1.1) ────────────────────────────────────────
def avg5_glsr(days, i):
    """avg of last 5 lsr_global values up to and including i"""
    vals = [days[j]["lsr_global"] for j in range(max(0,i-4), i+1)
            if days[j]["lsr_global"] is not None]
    return sum(vals)/len(vals) if vals else None

def slope_5d_glsr(days, i):
    """slope_5d = lsr_global[i] / lsr_global[i-4] (5d window)"""
    if i < 4: return None
    v_end = days[i]["lsr_global"]; v_start = days[i-4]["lsr_global"]
    if v_end is None or v_start is None or v_start == 0: return None
    return v_end / v_start

A2_THRESH  = 1.1   # avg5 gLSR < 1.1 → shorts dominant
A3_SLOPE   = 1.15  # slope_5d ≤ 1.15 → gLSR not accelerating up

log("\n=== GOM-A RECHẤM — FULL WINDOW ===")
log(f"  Spec: A1=lsr_accum, A2=avg5(gLSR)<{A2_THRESH}, A3=slope_5d≤{A3_SLOPE}")
log(f"  A4=d_pos_3d≥0 OR pos_rerate, A5=oi_cycle_pos≤0.5")
log(f"  Fire = A1∧A2∧A3∧(A4∨A5)")
log()
log(f"  {'Date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'avg5g':>7} {'slope5d':>8} {'d_p3d':>7} {'oiCP':>6} | A1 A2 A3 A4 A5 FIRE")
log(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*8} {'-'*7} {'-'*6} | {'-'*2} {'-'*2} {'-'*2} {'-'*2} {'-'*2} {'-'*4}")

fire_dates = []
chain_open = False
chain_start = None
chain_n = 0
break_streak = 0
q1_gom_cum = 0.0
prev_oi = None
prev_px = None

for i, d in enumerate(days):
    dt = d["date"]
    pos_r  = d.get("pos_r")
    acc_r  = d.get("acc_r")
    glsr   = d.get("lsr_global")
    oi_usd = d.get("oi_usd")
    px     = d.get("px_avg")
    d_p3d  = d.get("d_pos_3d")
    oi_cp  = d.get("oi_cycle_pos")

    avg5g = avg5_glsr(days, i)
    slope5 = slope_5d_glsr(days, i)

    # A1: lsr_accum proxy — OI expanding (simplified: ΔOI > 0 OR pos_r climbing)
    # In gom_scan, A1 is complex (lsr_accum function). Here simplified:
    delta_oi = (oi_usd - prev_oi) if (oi_usd and prev_oi) else None
    # A1 approximation: OI not collapsing (ΔOI ≥ -5%) AND pos_r > 2.0
    a1_approx = (pos_r is not None and pos_r > 2.0 and
                 (delta_oi is None or delta_oi >= -0.05 * prev_oi))

    # A2: avg5(gLSR) < A2_THRESH
    a2 = (avg5g is not None and avg5g < A2_THRESH)

    # A3: slope_5d ≤ A3_SLOPE (or NaN → slope_dq=False → A3=True)
    if slope5 is None:
        a3 = True  # NaN → not disqualifying
    else:
        a3 = slope5 <= A3_SLOPE

    # A4: d_pos_3d >= 0 OR pos_rerate (simplified: skip pos_rerate)
    a4 = (d_p3d is not None and d_p3d >= 0)

    # A5: oi_cycle_pos ≤ 0.5
    a5 = (oi_cp is not None and oi_cp <= 0.5)

    fire = a1_approx and a2 and a3 and (a4 or a5)

    pos_s  = f"{pos_r:.4f}" if pos_r else " N/A "
    acc_s  = f"{acc_r:.4f}" if acc_r else " N/A "
    glsr_s = f"{glsr:.4f}" if glsr else " N/A "
    avg5s  = f"{avg5g:.4f}" if avg5g else " N/A "
    sl5s   = f"{slope5:.3f}" if slope5 else "  N/A "
    dp3s   = f"{d_p3d:+.3f}" if d_p3d is not None else " N/A "
    ocps   = f"{oi_cp:.3f}" if oi_cp is not None else " N/A"

    # Only print window 2026-07-25 onward
    if dt >= "2026-07-25":
        log(f"  {dt:<12} {pos_s:>7} {acc_s:>7} {glsr_s:>7} {avg5s:>7} {sl5s:>8} {dp3s:>7} {ocps:>6} | "
            f"{'T' if a1_approx else 'F':>2} {'T' if a2 else 'F':>2} {'T' if a3 else 'F':>2} "
            f"{'T' if a4 else 'F':>2} {'T' if a5 else 'F':>2} {'GOM' if fire else '   ':>4}")

    if fire:
        fire_dates.append(dt)

    # Q1 accumulation (simplified)
    if fire:
        if prev_oi and oi_usd:
            doi = max(oi_usd - prev_oi, 0)
        else:
            doi = 0
        if prev_px and px and prev_px > 0:
            ret = (px - prev_px)/prev_px
            if ret <= 0.01:
                q1_gom_cum += doi

    prev_oi = oi_usd
    prev_px = px

# ── Bảng ngày fire ───────────────────────────────────────────────────────────
log(f"\n  Fire dates (approx, using simplified A1): {fire_dates}")
log(f"  First fire: {fire_dates[0] if fire_dates else 'NONE'}")
log(f"  Last fire:  {fire_dates[-1] if fire_dates else 'NONE'}")

# ── Bảng A1-A5 NGÀY FIRE = CHAIN START = 2026-08-01 ─────────────────────────
log("\n=== BẢNG A1-A5: NGÀY CHAIN START 2026-08-01 ===")
log("  (Theo gom_state_v8: chain mở 08-01 — rechấm độc lập)")
fire_day = "2026-08-01"
fi = next((i for i,d in enumerate(days) if d["date"]==fire_day), None)
if fi is not None:
    d = days[fi]
    avg5g = avg5_glsr(days, fi)
    slope5 = slope_5d_glsr(days, fi)
    prev_d = days[fi-1] if fi > 0 else {}
    delta_oi_fire = d.get("oi_usd",0) - prev_d.get("oi_usd",0) if prev_d.get("oi_usd") else None

    log(f"\n  Ngày: {fire_day}")
    log(f"  pos_r:         {d.get('pos_r','N/A')}")
    log(f"  acc_r:         {d.get('acc_r','N/A')}")
    log(f"  lsr_global:    {d.get('lsr_global','N/A')}")
    log(f"  avg5(gLSR):    {avg5g:.4f}" if avg5g else "  avg5(gLSR):    N/A")
    log(f"  slope_5d:      {slope5:.3f}" if slope5 else "  slope_5d:      N/A (NaN→A3=True)")
    log(f"  d_pos_3d:      {d.get('d_pos_3d','N/A'):.4f}" if d.get('d_pos_3d') is not None else "  d_pos_3d: N/A")
    log(f"  oi_cycle_pos:  {d.get('oi_cycle_pos','N/A'):.4f}" if d.get('oi_cycle_pos') is not None else "  oi_cycle_pos: N/A")
    log(f"  OI:            ${d.get('oi_usd',0):,.0f}")
    if delta_oi_fire is not None:
        log(f"  ΔOI (vs prev): ${delta_oi_fire:+,.0f}")
    log()
    log(f"  A1 (lsr_accum / OI nở approx): {a1_approx} — [approx: pos_r>2.0 + ΔOI≥-5%]")
    a2_fire = (avg5g is not None and avg5g < A2_THRESH)
    log(f"  A2 avg5(gLSR)<{A2_THRESH}: {a2_fire} [{avg5g:.4f} if avg5g else 'N/A']")
    a3_fire = slope5 is None or slope5 <= A3_SLOPE
    log(f"  A3 slope≤{A3_SLOPE}: {a3_fire} [{slope5:.3f} if slope5 else 'N/A→True']")
    a4_fire = d.get("d_pos_3d") is not None and d.get("d_pos_3d") >= 0
    log(f"  A4 d_pos_3d≥0: {a4_fire} [{d.get('d_pos_3d','N/A'):.4f} if d.get('d_pos_3d') else 'N/A']")
    a5_fire = d.get("oi_cycle_pos") is not None and d.get("oi_cycle_pos") <= 0.5
    log(f"  A5 oi_cycle≤0.5: {a5_fire} [{d.get('oi_cycle_pos','N/A'):.4f} if d.get('oi_cycle_pos') else 'N/A']")
    fire_check = a1_approx and a2_fire and a3_fire and (a4_fire or a5_fire)
    log(f"\n  → GOM-A FIRE 08-01: {'HỢP LỆ' if fire_check else 'KHÔNG HỢP LỆ'} (A1∧A2∧A3∧(A4∨A5))")
    log(f"  NOTE: A1 dùng phép xấp xỉ — verify đầy đủ cần chạy qua gom_scan.py")

# ── pin_streak ────────────────────────────────────────────────────────────────
log("\n=== PIN_STREAK (funding pinned near 0) ===")
PIN_LO, PIN_HI = 4e-5, 6e-5
log(f"  Threshold: {PIN_LO:.1e} ≤ funding ≤ {PIN_HI:.1e}")
pin_streak = 0
for d in reversed(days):
    f_avg = d.get("funding_avg")
    if f_avg is None: break
    if PIN_LO <= f_avg <= PIN_HI:
        pin_streak += 1
    else:
        break
log(f"  pin_streak (current): {pin_streak}")
# Print last 14 days
log(f"\n  {'Date':<12} {'funding_avg':>14} {'pinned?':>8}")
for d in days[-14:]:
    f = d.get("funding_avg")
    pinned = (f is not None and PIN_LO <= f <= PIN_HI)
    f_s = f"{f:.6f}" if f else "N/A"
    log(f"  {d['date']:<12} {f_s:>14} {'PIN' if pinned else '   ':>8}")

# ── 5 diagnostic flags ─────────────────────────────────────────────────────────
log("\n=== 5 CỜ CHẨN ĐOÁN ===")
last = days[-1]
prev7 = days[-7] if len(days) >= 7 else days[0]

# decay: pos_r drop > 20% from peak in last 7d
pos_peak_7d = max(d.get("pos_r",0) or 0 for d in days[-7:])
pos_now = last.get("pos_r")
decay = pos_now is not None and pos_peak_7d > 0 and pos_now < pos_peak_7d * 0.80
log(f"  decay:         {decay} (pos_r now={pos_now:.4f} vs peak7d={pos_peak_7d:.4f})")

# post_climax: vol spike in last 7d + price drop
vol_7d = [d.get("vol_quote",0) or 0 for d in days[-7:]]
vol_21d = [d.get("vol_quote",0) or 0 for d in days[-21:]]
med21_vol = sorted(vol_21d)[len(vol_21d)//2]
vol_spike = max(vol_7d) > med21_vol * 8 if med21_vol > 0 else False
log(f"  post_climax:   {vol_spike} (max_vol7d={max(vol_7d):,.0f} vs med21={med21_vol:,.0f})")

# lsr_dist: pos_r > 3.5 for 3+ consecutive days
lsr_dist = all(d.get("pos_r",0) and d.get("pos_r",0) > 3.5 for d in days[-3:])
log(f"  lsr_dist:      {lsr_dist} (pos_r last 3d > 3.5?)")

# dist_wall: big ask wall detected (depth — not available here, N/A)
log(f"  dist_wall:     N/A (requires depth snap)")

# funding_neg_div: funding negative + pos_r diverging
fund_neg = last.get("funding_avg") is not None and last.get("funding_avg") < 0
log(f"  funding_neg_div: {fund_neg} (funding_avg={last.get('funding_avg','N/A')})")

log(f"\n  gom_state_v8: chain_open=True, break_streak=0, suspect_flag=False")

log("\n[F-4 DONE]")

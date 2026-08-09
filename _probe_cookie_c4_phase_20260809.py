"""
_probe_cookie_c4_phase_20260809.py
COOKIE C-4: Phase context + GOM-C rechấm + 5 cờ chẩn đoán + pin_streak + oi_cycle_pos
"""
import sys, io, json, csv, math, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-4 PHASE + GOM-C  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def read_csv(path):
    if not path.exists(): return []
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
fund = read_csv(SCRATCH / f"cookie_funding_{DATE_TAG}.csv")

perp_by_d = {r["date"]: r for r in perp}
lsr_by_d  = {r["date"]: r for r in lsr}
oi_by_d   = {r["date"]: gf(r,"oi_usd") for r in oi}
all_dates = sorted(perp_by_d.keys())

# Compute ret_1d
date_ret = {}
prev_c = None
for dt in all_dates:
    c = gf(perp_by_d[dt],"close")
    if c and prev_c:
        date_ret[dt] = (c - prev_c)/prev_c
    prev_c = c

# Fund per day (aggregate raw)
fund_by_d = {}
for r in fund:
    dt = r.get("date","")
    fr = gf(r,"fundingRate")
    if dt and fr is not None:
        if dt not in fund_by_d:
            fund_by_d[dt] = []
        fund_by_d[dt].append(fr)

# ── C-4a: PHASE CONTEXT ───────────────────────────────────────────────────────
log("\n=== C-4a: BỐI CẢNH PHA VÒNG ĐỜI ===")
closes = [(dt, gf(perp_by_d[dt],"close")) for dt in all_dates if gf(perp_by_d[dt],"close")]
prices = [c for _,c in closes]
ath = max(prices); ath_dt = closes[prices.index(ath)][0]
atl = min(prices); atl_dt = closes[prices.index(atl)][0]
c_last = closes[-1][1]; dt_last = closes[-1][0]
c_0803 = gf(perp_by_d.get("2026-08-03",{}),"close")

log(f"  ATH:          ${ath:.6f} on {ath_dt}")
log(f"  ATL:          ${atl:.6f} on {atl_dt}")
log(f"  Perp onboard: 2025-01-07")
log(f"  Alpha listing: 2024-12-23")
log(f"  Current (08-08): ${c_last:.6f}")
log(f"  Fire day (08-03): ${c_0803:.6f}" if c_0803 else "  Fire day (08-03): N/A")
log(f"  px vs ATH:   {(c_last/ath - 1)*100:+.1f}%")
log(f"  px vs ATL:   {(c_last/atl - 1)*100:+.1f}%")
log(f"  px vs VWAP (08-03): {(c_last/0.00774-1)*100:+.1f}%")

# Price history key milestones
log(f"\n  Price milestones (vol spikes ≥8× med14 from build output):")
vol_spikes = ["2025-02-10","2025-02-11","2025-04-29","2025-05-21","2025-05-22","2025-05-23",
              "2025-05-24","2025-05-25","2025-05-26","2025-05-27","2026-03-04","2026-05-18",
              "2026-06-28","2026-08-06","2026-08-07","2026-08-08"]
for dt in vol_spikes[-8:]:
    p = perp_by_d.get(dt, {})
    c = gf(p,"close")
    vol = gf(p,"vol_quote_usd")
    ret = date_ret.get(dt)
    if c and vol:
        log(f"    {dt}: close=${c:.6f} vol=${vol/1e6:.2f}M ret={ret*100:+.1f}%" if ret else f"    {dt}: close=${c:.6f} vol=${vol/1e6:.2f}M")

# Find "base/nền" (longest quiet period before current rally)
log(f"\n  Phân tích nền/base:")
# Count days in range $0.007-$0.012 before 08-06 rally
base_range = [dt for dt in all_dates if "2026-06-01" <= dt < "2026-08-06"]
base_closes = [gf(perp_by_d[dt],"close") for dt in base_range if gf(perp_by_d[dt],"close")]
if base_closes:
    log(f"  Nền 06-01→08-05 ({len(base_closes)} ngày): avg=${statistics.mean(base_closes):.6f} "
        f"min=${min(base_closes):.6f} max=${max(base_closes):.6f}")

# ── C-4b: GOM-C RECHẤM 08-03 (fire day) ──────────────────────────────────────
log("\n=== C-4b: GOM-C RECHẤM NGÀY FIRE (2026-08-03) ===")
log("  GOM-C spec: C1(stealth_grind) ∧ C2_quiet(f_avg≤2×neutral/interval) ∧")
log("              C3_lax(taker∈[40,55]) ∧ d_pos≥0 (pos_r non-declining)")
log("")

d_0803 = perp_by_d.get("2026-08-03", {})
ls_0803 = lsr_by_d.get("2026-08-03", {})
oi_0803 = oi_by_d.get("2026-08-03")
fund_0803 = fund_by_d.get("2026-08-03", [])
ret_0803 = date_ret.get("2026-08-03")

# C1: stealth_grind — typically: pos_r > threshold AND gLSR < crowd_thr
pos_0803 = gf(ls_0803,"pos_r")
glsr_0803 = gf(ls_0803,"glsr_raw")
log(f"  C1 stealth_grind: pos_r={pos_0803} gLSR={glsr_0803}")
log(f"    → gLSR={glsr_0803:.4f} >> 1.1 → C1 likely FAIL? (depends on exact C1 spec)")
log(f"    Note: in gom_scan.py, C1 for GOM-C is different from GOM-A A1")

# C2: f_avg ≤ 2×neutral per interval
# neutral 4h = 5e-5; 2×neutral = 1e-4
f_avg_0803 = statistics.mean(fund_0803) if fund_0803 else None
f_n_0803 = len(fund_0803)
c2_thr = 1e-4  # 2×neutral for 4h interval
c2_pass = (f_avg_0803 is not None and abs(f_avg_0803) <= c2_thr)
log(f"\n  C2_quiet: f_avg≤{c2_thr:.0e} per 4h interval")
log(f"    fund_0803 rates: {len(fund_0803)} intervals, f_avg={f_avg_0803:.6f}" if f_avg_0803 is not None else "    fund_0803: NO DATA")
log(f"    C2 threshold: {c2_thr:.1e} → {'PASS' if c2_pass else 'FAIL'}")

# C3: taker ∈ [40%, 55%]
taker_0803 = gf(d_0803,"taker_pct")
c3_pass = (taker_0803 is not None and 0.40 <= taker_0803 <= 0.55)
log(f"\n  C3_lax: taker_buy_pct ∈ [40%, 55%]")
log(f"    taker_0803 = {taker_0803:.2%}" if taker_0803 else "    taker_0803 = N/A")
log(f"    C3 → {'PASS' if c3_pass else 'FAIL'}")

# d_pos ≥ 0: pos_r non-declining (vs prev day)
ls_0802 = lsr_by_d.get("2026-08-02", {})
pos_0802 = gf(ls_0802,"pos_r")
d_pos = (pos_0803 - pos_0802) if (pos_0803 and pos_0802) else None
dpos_pass = (d_pos is not None and d_pos >= 0)
log(f"\n  d_pos ≥ 0: pos_r(08-03) - pos_r(08-02)")
log(f"    pos_r(08-03)={pos_0803:.4f} pos_r(08-02)={pos_0802:.4f}" if pos_0803 and pos_0802 else "    missing LSR")
log(f"    d_pos={d_pos:.4f} → {'PASS' if dpos_pass else 'FAIL'}" if d_pos is not None else "    d_pos = N/A")

log(f"\n  GOM-C FIRE 08-03 RECHẤM:")
log(f"  C1 stealth_grind: need exact spec — gLSR={glsr_0803:.4f} (high, typically C1 requires gLSR between bounds)")
log(f"  C2_quiet:         {'PASS' if c2_pass else 'FAIL'} (f_avg={f_avg_0803:.6f} vs thr={c2_thr:.0e})")
log(f"  C3_lax:           {'PASS' if c3_pass else 'FAIL'} (taker={taker_0803:.2%})")
log(f"  d_pos≥0:          {'PASS' if dpos_pass else 'FAIL'} (Δpos_r={d_pos:.4f})" if d_pos is not None else "  d_pos≥0:          N/A")

# ── C-4c: 5 CỜ CHẨN ĐOÁN (full LSR window) ────────────────────────────────────
log("\n=== C-4c: 5 CỜ CHẨN ĐOÁN (window LSR 30d) ===")
lsr_dates = sorted(lsr_by_d.keys())[-30:]  # last 30 dates with LSR

flag_dist_wall = 0   # taker ≥ 50% + ret < 0
flag_knife = 0       # gLSR↑ + ret < -3%
flag_hedge = 0       # div_avg3 ≤ 0.5
flag_neg_div = 0     # f_avg ≤ -2e-4 AND range3d ≤ ±7%
flag_decay = 0       # taker < 45%

for i, dt in enumerate(lsr_dates):
    ret = date_ret.get(dt)
    p = perp_by_d.get(dt, {})
    taker = gf(p,"taker_pct")
    ls = lsr_by_d.get(dt, {})
    pos = gf(ls,"pos_r")
    acc = gf(ls,"acc_r")
    glsr = gf(ls,"glsr_raw")
    div = pos/acc if (pos and acc and acc > 0) else None
    f = fund_by_d.get(dt)
    f_avg = statistics.mean(f) if f else None

    # flag_dist_wall
    if taker and ret and taker >= 0.50 and ret < 0:
        flag_dist_wall += 1
    # flag_knife
    if i > 0 and ret and glsr:
        prev_ls = lsr_by_d.get(lsr_dates[i-1], {})
        prev_glsr = gf(prev_ls,"glsr_raw")
        if prev_glsr and glsr > prev_glsr and ret < -0.03:
            flag_knife += 1
    # flag_hedge
    if div is not None and div <= 0.5:
        flag_hedge += 1
    # flag_neg_div (simplified)
    if f_avg is not None and f_avg <= -2e-4:
        flag_neg_div += 1
    # flag_decay
    if taker and taker < 0.45:
        flag_decay += 1

log(f"  Window: last 30 LSR dates ({lsr_dates[0]}→{lsr_dates[-1]})")
log(f"  {'Flag':30s} {'Count':>6s} {'Rate':>8s}")
log(f"  {'flag_dist_wall':30s} {flag_dist_wall:>6d} {flag_dist_wall/30:.1%}")
log(f"  {'flag_knife_crowd (gLSR↑+ret<-3%)':30s} {flag_knife:>6d} {flag_knife/30:.1%}")
log(f"  {'flag_hedge_struct (div≤0.5)':30s} {flag_hedge:>6d} {flag_hedge/30:.1%}")
log(f"  {'flag_neg_div (f_avg≤-2e-4)':30s} {flag_neg_div:>6d} {flag_neg_div/30:.1%}")
log(f"  {'flag_decay (taker<45%)':30s} {flag_decay:>6d} {flag_decay/30:.1%}")

# ── C-4d: PIN STREAK + OI_CYCLE_POS ─────────────────────────────────────────
log("\n=== C-4d: PIN_STREAK + OI_CYCLE_POS (last 14d) ===")
log("  PIN = f_avg ∈ [4e-5, 6e-5] (pinned near neutral)")
log(f"  {'date':12s} {'f_avg':>10s} {'f_min':>10s} {'f_n':>5s} {'PIN?':>6s} {'oi_usd':>12s} {'oi_cycle':>9s}")

oi_30d = [v for dt, v in sorted(oi_by_d.items()) if v is not None][-30:]
oi_min30 = min(oi_30d) if oi_30d else None
oi_max30 = max(oi_30d) if oi_30d else None
pin_streak = 0
oi_dates = sorted(oi_by_d.keys())[-14:]
for dt in oi_dates:
    f = fund_by_d.get(dt,[])
    f_avg = statistics.mean(f) if f else None
    f_min = min(f) if f else None
    f_n = len(f)
    oi_now = oi_by_d.get(dt)
    oi_cycle = (oi_now - oi_min30)/(oi_max30 - oi_min30) if (oi_now and oi_min30 and oi_max30 and oi_max30 > oi_min30) else None
    pin = (f_avg is not None and 4e-5 <= f_avg <= 6e-5)
    if pin:
        pin_streak += 1
    else:
        pin_streak = 0
    log(f"  {dt:12s} {f_avg:>10.6f} {f_min:>10.6f} {f_n:>5d} {'PIN✓' if pin else '—':>6s} "
        f"${oi_now:>11,.0f} {oi_cycle:>9.3f}"
        if f_avg is not None and oi_now and oi_cycle is not None
        else f"  {dt:12s} (missing data)")

log(f"\n  pin_streak at last date: {pin_streak}")
log(f"  OI_min30: ${oi_min30:,.0f}" if oi_min30 else "  OI_min30: N/A")
log(f"  OI_max30: ${oi_max30:,.0f}" if oi_max30 else "  OI_max30: N/A")
if oi_by_d.get("2026-08-08") and oi_min30 and oi_max30 and oi_max30 > oi_min30:
    oi_now = oi_by_d["2026-08-08"]
    cp = (oi_now - oi_min30)/(oi_max30 - oi_min30)
    log(f"  oi_cycle_pos(08-08): {cp:.3f}")

log(f"\n[C-4 DONE]")

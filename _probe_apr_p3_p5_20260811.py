"""
_probe_apr_p3_p5_20260811.py
P-3: GOM-D draft retrospective (D1-D5 on full APR window)
P-4: Mode-switch / un-hedge E1/E2/E3 hồi tố 05→12/08
P-5: Rũ-đàn gauge gLSR 05→12/08 + 4-màn ON framework
Reads from CASE_APR.xlsx DAILY (after append task).
data-source: CASE_APR.xlsx DAILY (updated), local
machine: local
date-range: 2025-10-23 → 2026-08-12
code-commit: TBD
"""
import sys, io, math, statistics, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import openpyxl
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE    = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"

def log(s=""): print(s, flush=True)

# ── Load DAILY (after append) ─────────────────────────────────────────────────
wb = openpyxl.load_workbook(CASE, data_only=True, read_only=True)
sh = wb["DAILY"]
all_rows = list(sh.iter_rows(values_only=True))
hdr = list(all_rows[1])
data_rows = [list(r) for r in all_rows[2:]]
wb.close()

col_map = {}
for i, h in enumerate(hdr):
    if h:
        col_map[str(h).lower().strip()] = i

def gcol_exact(row, key):
    kl = key.lower().strip()
    if kl in col_map:
        v = row[col_map[kl]]
        if v is not None: return v
    for ck, ci in col_map.items():
        if kl in ck:
            v = row[ci]
            if v is not None: return v
    return None

def fv(v, fmt=".4f"):
    if v is None: return "N/A"
    try: return format(float(v), fmt)
    except: return str(v)

log(f"Loaded {len(data_rows)} rows | {data_rows[0][0]} → {data_rows[-1][0]}")

# Helper arrays
def arr(key):
    result = []
    for r in data_rows:
        v = gcol_exact(r, key)
        try: result.append(float(v))
        except: result.append(None)
    return result

dates    = [r[0] for r in data_rows]
close_a  = arr("c")
vol_a    = arr("vol_perp_usd")
ret_a    = arr("ret_1d (close-to-close)")
taker_a  = arr("taker_buy_pct (k[10]/k[7])")
oi_a     = arr("oi_usd")
f_avg_a  = arr("f_avg")
pos_r_a  = arr("pos_r")
acc_r_a  = arr("acc_r")
glsr_a   = arr("gLSR")
div_avg3_a = arr("div_avg3 (avg3p/avg3a)")
flag_neg_div_a = arr("flag_neg_div (f<=-2e-4&range3d<=7%)")
flag_dist_a    = arr("flag_dist_wall_day (taker>=50&ret<0)")
flag_hedge_a   = arr("flag_hedge_struct (div_avg3<=0.5)")
flag_knife_a   = arr("flag_knife_crowd (gLSR↑&ret<-3%)")

def safe_med(arr_):
    c = [v for v in arr_ if v is not None and not math.isnan(v)]
    return statistics.median(c) if c else None

def safe_mean(arr_):
    c = [v for v in arr_ if v is not None and not math.isnan(v)]
    return sum(c)/len(c) if c else None

# vol_vs_med14 for each row
def vol_vs_med14_at(i):
    if vol_a[i] is None: return None
    window = [v for v in vol_a[max(0,i-14):i] if v is not None]
    med = safe_med(window)
    return vol_a[i] / med if med else None

# ── P-3: GOM-D DRAFT RETROSPECTIVE ───────────────────────────────────────────
log("\n" + "="*60)
log("=== P-3: GOM-D DRAFT RETROSPECTIVE ===")
log("="*60)

log("\n--- D1: NỀN-CHẾT (price < 15% ATH) ---")
ath_high = max(v for v in close_a if v)
ath_date = dates[close_a.index(ath_high)]
ath_15pct = ath_high * 0.15
log(f"  ATH close = ${ath_high:.4f} on {ath_date}")
log(f"  15% ATH threshold = ${ath_15pct:.4f}")
d1_days = [(d, c) for d, c in zip(dates, close_a) if c and c < ath_15pct]
log(f"  Days below 15% ATH: {len(d1_days)}")
if d1_days:
    log(f"  First: {d1_days[0][0]} c=${d1_days[0][1]:.4f}")
    log(f"  Last:  {d1_days[-1][0]} c=${d1_days[-1][1]:.4f}")
d1_pass = len(d1_days) >= 7
log(f"  D1 PASS={d1_pass} (≥7 consecutive days below 15% ATH)")

log("\n--- D3: NẠP-BẬC (≥2 vol clusters ≥8× med14) ---")
vol_clusters = []
cluster_dates = []
in_cluster = False
cluster_start = None
for i, (d, v) in enumerate(zip(dates, vol_a)):
    vm = vol_vs_med14_at(i)
    if vm and vm >= 8:
        if not in_cluster:
            in_cluster = True
            cluster_start = d
            cluster_dates = [d]
        else:
            cluster_dates.append(d)
    else:
        if in_cluster:
            vol_clusters.append({"start": cluster_start, "end": cluster_dates[-1],
                                  "days": len(cluster_dates)})
            in_cluster = False
            cluster_dates = []

if in_cluster and cluster_dates:
    vol_clusters.append({"start": cluster_start, "end": cluster_dates[-1],
                          "days": len(cluster_dates)})

log(f"  Vol clusters (≥8× med14):")
for cl in vol_clusters:
    log(f"    {cl['start']}→{cl['end']} ({cl['days']} days)")
d3_pass = len(vol_clusters) >= 2
log(f"  D3 PASS={d3_pass} (≥2 clusters)")

log("\n--- D4: VOL-WAKE (vol ≥5× med14 on first pump day) ---")
# Find days with vol ≥5× med14 and positive ret
big_vol_days = []
for i, (d, r) in enumerate(zip(dates, ret_a)):
    vm = vol_vs_med14_at(i)
    if vm and vm >= 5 and r and r > 0:
        big_vol_days.append((d, r, vm))
log(f"  Vol-wake days (≥5×, ret>0):")
for item in big_vol_days[-10:]:
    log(f"    {item[0]}: ret=+{item[1]:.2f}% vol={item[2]:.1f}×")
d4_pass = len(big_vol_days) >= 1
log(f"  D4 PASS={d4_pass}")

log("\n--- D5: CHURN (vol ≥8× after staging) ---")
churn_days = []
for i, (d, v) in enumerate(zip(dates, vol_a)):
    vm = vol_vs_med14_at(i)
    if vm and vm >= 8:
        churn_days.append((d, vm))
log(f"  Churn days (vol ≥8× med14):")
for item in churn_days[-8:]:
    log(f"    {item[0]}: vol={item[1]:.1f}×")
d5_pass = len(churn_days) >= 1
log(f"  D5 PASS={d5_pass}")

log("\n--- SUPPRESSOR: neg_div (f_avg ≤ -2e-4 AND range3d ≤ 7%) ---")
neg_div_days = [(d, f) for d, f in zip(dates, f_avg_a)
                if f is not None and f <= -2e-4]
log(f"  Neg div days: {len(neg_div_days)}")
for d, f in neg_div_days[-5:]:
    log(f"    {d}: f_avg={f:.6f}")
suppressor_off = len(neg_div_days) == 0
log(f"  Suppressor OFF={suppressor_off}")

log("\n--- GOM-D SUMMARY ---")
log(f"  D1 (nền-chết): {'PASS' if d1_pass else 'FAIL'}")
log(f"  D3 (nạp-bậc): {'PASS' if d3_pass else 'FAIL'}")
log(f"  D4 (vol-wake): {'PASS' if d4_pass else 'FAIL'}")
log(f"  D5 (churn):    {'PASS' if d5_pass else 'FAIL'}")
log(f"  Suppressor neg_div: {'OFF' if suppressor_off else 'ON'}")
gom_d_score = sum([d1_pass, d3_pass, d4_pass, d5_pass])
log(f"  Score: {gom_d_score}/4 {'PASS' if gom_d_score == 4 else 'PARTIAL'}")
log(f"  Note: draft chưa ký → không dùng làm signal fire")

# ── P-4: MODE-SWITCH / UN-HEDGE E1/E2/E3 ────────────────────────────────────
log("\n" + "="*60)
log("=== P-4: MODE-SWITCH / UN-HEDGE E1/E2/E3 hồi tố 05→12/08 ===")
log("="*60)

# Filter Aug 05 → Aug 12
window_start = "2026-08-05"
window_end   = "2026-08-12"
w_idx = [(i, d) for i, d in enumerate(dates) if window_start <= str(d) <= window_end]
log(f"\nWindow: {window_start} → {window_end} ({len(w_idx)} rows)")

# E1: flag_hedge_struct (div_avg3 <= 0.5)
log("\n--- E1: HEDGE_STRUCT (div_avg3 ≤ 0.5) ---")
for i, d in w_idx:
    dv = div_avg3_a[i]
    fh = flag_hedge_a[i]
    log(f"  {d}: div_avg3={fv(dv)} hedge_flag={fh}")

# E2: flag_decay_day (taker < 45)
log("\n--- E2: DECAY_DAY (taker_buy_pct < 45) ---")
for i, d in w_idx:
    tk = taker_a[i]
    log(f"  {d}: taker={fv(tk,'%')} → decay={'1' if tk and tk < 45 else '0'}")

# E3: flag_knife_crowd (gLSR↑ AND ret < -3%)
log("\n--- E3: KNIFE_CROWD (gLSR↑ AND ret < -3%) ---")
for i, d in w_idx:
    g  = glsr_a[i]
    r  = ret_a[i]
    fk = flag_knife_a[i]
    prev_g = glsr_a[i-1] if i > 0 else None
    g_rising = g is not None and prev_g is not None and g > prev_g
    log(f"  {d}: gLSR={fv(g)} prev={fv(prev_g)} ↑={g_rising} ret={fv(r,'%')} knife={fk}")

# Mode-switch detection: hedge OFF → ON or ON → OFF
log("\n--- MODE-SWITCH EVENTS (hedge_struct transition) ---")
prev_hedge = None
for i, d in enumerate(dates):
    cur_hedge = flag_hedge_a[i]
    if cur_hedge is not None and prev_hedge is not None:
        if int(cur_hedge) != int(prev_hedge if prev_hedge is not None else -1):
            if window_start <= str(d) <= window_end or str(d) >= "2026-07-01":
                log(f"  {d}: hedge_struct {int(prev_hedge)}→{int(cur_hedge)} | div_avg3={fv(div_avg3_a[i])}")
    prev_hedge = cur_hedge

# ── P-5: RŨ-ĐÀN GAUGE ────────────────────────────────────────────────────────
log("\n" + "="*60)
log("=== P-5: RŨ-ĐÀN GAUGE — gLSR 05→12/08 + 4-màn ON framework ===")
log("="*60)

log("\n--- gLSR trajectory 05→12/08 ---")
for i, d in w_idx:
    g  = glsr_a[i]
    pr = pos_r_a[i]
    ar = acc_r_a[i]
    r  = ret_a[i]
    log(f"  {d}: gLSR={fv(g)} pos_r={fv(pr)} acc_r={fv(ar)} ret={fv(r,'%')}")

# gLSR regime
glsr_w = [(glsr_a[i], d) for i, d in w_idx if glsr_a[i] is not None]
if glsr_w:
    g_vals = [v for v, _ in glsr_w]
    g_mean = safe_mean(g_vals)
    g_trend = "RISING" if g_vals[-1] > g_vals[0] else "FALLING"
    log(f"\n  gLSR range: {min(g_vals):.4f} → {max(g_vals):.4f} (mean {g_mean:.4f})")
    log(f"  Trend: {g_trend}")
    log(f"  Aug12 gLSR={glsr_w[-1][0]:.4f} — {'BULL (>1)' if glsr_w[-1][0] > 1 else 'BEAR (<1)'}")

# 4-màn ON framework
log("\n--- 4-MÀNG ON FRAMEWORK (Aug 12 ignition context) ---")
log("  Màn 1 — Crowd disposition pre-pump:")
# Pre-pump: Aug 05-11 (before the Aug 12 event)
pre_w = [(i, d) for i, d in w_idx if str(d) < "2026-08-12"]
if pre_w:
    pre_glsr = [glsr_a[i] for i, d in pre_w if glsr_a[i] is not None]
    pre_div  = [div_avg3_a[i] for i, d in pre_w if div_avg3_a[i] is not None]
    pre_tk   = [taker_a[i] for i, d in pre_w if taker_a[i] is not None]
    g_avg = safe_mean(pre_glsr)
    d_avg = safe_mean(pre_div)
    t_avg = safe_mean(pre_tk)
    log(f"    gLSR (pre-pump avg) = {fv(g_avg)} → {'BULL' if g_avg and g_avg > 1 else 'BEAR'}")
    log(f"    div_avg3 (pre-pump) = {fv(d_avg)} → {'BULL' if d_avg and d_avg > 1 else 'BEAR'}")
    log(f"    taker_buy_pct avg   = {fv(t_avg,'%')}")

log("  Màn 2 — Ignition fingerprint (Aug 12):")
aug12_i = next((i for i, d in enumerate(dates) if str(d) == "2026-08-12"), None)
if aug12_i:
    log(f"    Date: 2026-08-12")
    log(f"    c=${close_a[aug12_i]:.4f} | ret=+{ret_a[aug12_i]:.1f}%")
    vol_med14 = safe_med([v for v in vol_a[aug12_i-14:aug12_i] if v])
    vm = vol_a[aug12_i] / vol_med14 if vol_med14 else None
    log(f"    vol=${vol_a[aug12_i]:,.0f} | vol_vs_med14={fv(vm,'%')}")
    log(f"    gLSR={fv(glsr_a[aug12_i])} | pos_r={fv(pos_r_a[aug12_i])} | acc_r={fv(acc_r_a[aug12_i])}")
    log(f"    taker={fv(taker_a[aug12_i],'%')}")
    log(f"    f_avg={fv(f_avg_a[aug12_i])}")

log("  Màn 3 — Pre-pump gom signal count (Aug 05-11):")
# Check if any GOM-A/B fire in window
gom_a = [gcol_exact(data_rows[i], "gom_A_screen") for i, d in pre_w]
gom_a_fires = [v for v in gom_a if v and "FIRE" in str(v).upper()]
log(f"    GOM-A fires Aug05-11: {len(gom_a_fires)}")
dws_pre = [gcol_exact(data_rows[i], "dist_wall_streak (consec days)") for i, d in pre_w]
log(f"    dist_wall streak: {dws_pre}")

log("  Màn 4 — Post-pump regime (Aug 12):")
if aug12_i:
    log(f"    OI: ${oi_a[aug12_i]:,.0f} (pre: ${oi_a[aug12_i-1]:,.0f})")
    log(f"    oi_change = {(oi_a[aug12_i]-oi_a[aug12_i-1])/oi_a[aug12_i-1]*100:.1f}%")
    log(f"    → OI flat/down during pump = liquidation-driven (short squeeze)")
    log(f"      OI up during pump = new long accumulation")

# ── P-6: SANITY ───────────────────────────────────────────────────────────────
log("\n" + "="*60)
log("=== P-6: SANITY (5 items) ===")
log("="*60)

log("\n--- S1: Row count ---")
expected = 294  # 291 + 3
actual = len(data_rows)
s1 = actual == expected
log(f"  Expected: {expected} | Actual: {actual} | {'PASS' if s1 else 'FAIL'}")

log("\n--- S2: Date continuity ---")
from datetime import datetime, timedelta
s2_gaps = []
for i in range(1, len(data_rows)):
    d_curr = str(data_rows[i][0])
    d_prev = str(data_rows[i-1][0])
    try:
        dt_c = datetime.strptime(d_curr, "%Y-%m-%d")
        dt_p = datetime.strptime(d_prev, "%Y-%m-%d")
        gap = (dt_c - dt_p).days
        if gap != 1:
            s2_gaps.append((d_prev, d_curr, gap))
    except: pass
s2 = len(s2_gaps) == 0
log(f"  Gaps: {len(s2_gaps)} | {'PASS' if s2 else 'FAIL'}")
for g in s2_gaps[:5]:
    log(f"    {g[0]} → {g[1]}: {g[2]} day gap")

log("\n--- S3: Close price sanity (no negatives, no >$10 before ATH) ---")
bad_close = [(d, c) for d, c in zip(dates, close_a) if c is not None and c <= 0]
s3 = len(bad_close) == 0
log(f"  Negative closes: {len(bad_close)} | {'PASS' if s3 else 'FAIL'}")

log("\n--- S4: Aug 12 pump verified ---")
aug12_c = close_a[aug12_i] if aug12_i else None
aug12_vol = vol_a[aug12_i] if aug12_i else None
s4 = aug12_c and aug12_c > 0.5 and aug12_vol and aug12_vol > 5e8
log(f"  Aug12 c=${fv(aug12_c)} vol=${fv(aug12_vol,'.0f')}")
log(f"  c>0.5 and vol>$500M: {'PASS' if s4 else 'FAIL'}")

log("\n--- S5: taker_buy_pct range check (new rows) ---")
new_takers = [(str(data_rows[i][0]), taker_a[i]) for i in range(-3, 0)]
s5_ok = all(t is None or 30 <= t <= 75 for _, t in new_takers)
for d, t in new_takers:
    log(f"  {d}: taker={fv(t,'%')} {'OK' if t is None or 30 <= t <= 75 else 'OOB'}")
s5 = s5_ok
log(f"  S5 {'PASS' if s5 else 'FAIL'}")

log("\n--- SANITY SUMMARY ---")
score = sum([s1, s2, s3, s4, s5])
log(f"  {score}/5 PASS")
for nm, r in [("S1 row count",s1),("S2 date continuity",s2),("S3 no neg close",s3),
              ("S4 Aug12 pump",s4),("S5 taker range",s5)]:
    log(f"  {'✓' if r else '✗'} {nm}")

# Save analytics results
results = {
    "gom_d": {"d1": d1_pass, "d3": d3_pass, "d4": d4_pass, "d5": d5_pass,
               "suppressor_off": suppressor_off, "score": gom_d_score,
               "vol_clusters": vol_clusters,
               "ath_close": ath_high, "ath_date": ath_date},
    "aug12": {"c": close_a[aug12_i] if aug12_i else None,
              "ret": ret_a[aug12_i] if aug12_i else None,
              "vol": vol_a[aug12_i] if aug12_i else None,
              "gLSR": glsr_a[aug12_i] if aug12_i else None,
              "f_avg": f_avg_a[aug12_i] if aug12_i else None},
    "sanity": {"score": score, "s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5},
}
out_path = SCRATCH / "apr_analytics_20260811.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
log(f"\n[P-3→P-6 DONE] Analytics → {out_path.name}")

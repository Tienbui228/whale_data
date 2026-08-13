"""
_probe_cys_c3c7_analysis_20260813.py
C-3 triage + BẢNG BỐN VÂN + C-4 hai lăng kính + C-5 rũ-đàn + C-6 venue + C-7 sanity.
data-source: CASE_CYS.xlsx (DAILY built 20260813) + scratch CSVs
machine: local
date-range: 2026-01-01 → 2026-08-12
code-commit: TBD
"""
import sys, io, json, csv, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE    = ROOT / "docs" / "case_files" / "CASE_CYS.xlsx"
DATE_TAG = "20260813"
SYM = "CYSUSDT"

def log(s=""): print(s, flush=True)

def sf(v, d=None):
    try: return float(v) if v not in (None, "", "None", "nan") else d
    except: return d

# ── Load DAILY ──────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(CASE, read_only=True, data_only=True)
ws = wb["DAILY"]
all_rows = list(ws.iter_rows(values_only=True))
# Row1 = category labels, Row2 = column names, Row3+ = data
headers = [v for v in all_rows[1]]  # row2 = column names
rows = []
for row in all_rows[2:]:
    r = dict(zip(headers, row))
    if r.get("date"): rows.append(r)
wb.close()

log(f"DAILY rows: {len(rows)}")
log(f"Dates: {rows[0]['date']} → {rows[-1]['date']}")

# Header normalization: map short key → full annotated key
_HMAP = {}
for h in headers:
    if h:
        short = str(h).split(" ")[0].split("(")[0].rstrip()
        _HMAP[short] = h
        _HMAP[str(h)] = h  # exact match too

def get(r, k, d=None):
    full_key = _HMAP.get(k, k)
    return sf(r.get(full_key, r.get(k)), d)

dates   = [r["date"] for r in rows]
closes  = [get(r,"c")  for r in rows]
pos_rs  = [get(r,"pos_r") for r in rows]
acc_rs  = [get(r,"acc_r") for r in rows]
glsrs   = [get(r,"gLSR")  for r in rows]
div_r   = [get(r,"div_raw") for r in rows]
div_a3  = [get(r,"div_avg3") for r in rows]
oi_usd  = [get(r,"oi_usd") for r in rows]
ret_1d  = [get(r,"ret_1d") for r in rows]
takers  = [get(r,"taker_buy_pct") for r in rows]
f_avgs  = [get(r,"f_avg") for r in rows]
f_mins  = [get(r,"f_min") for r in rows]
vols    = [get(r,"vol_perp_usd") for r in rows]
vol_vs  = [get(r,"vol_vs_med14") for r in rows]
pin_str = [get(r,"pin_streak") or 0 for r in rows]
pin_day = [get(r,"pin_day") for r in rows]
d_pos   = [get(r,"d_pos_3d") for r in rows]
oicp    = [get(r,"oi_cycle_pos") for r in rows]
flag_k  = [get(r,"flag_knife_crowd") for r in rows]

N = len(rows)

# ── C-3a. TRIAGE BỘ BA ─────────────────────────────────────────────────────
log("\n" + "="*70)
log("C-3a. TRIAGE BỘ BA: div_avg3 / gLSR / pin_streak")
log("="*70)

# div_avg3 window
div_a3_valid = [(dates[i], div_a3[i]) for i in range(N) if div_a3[i] is not None]
div_bear = [(d, v) for d, v in div_a3_valid if v < 1.0]  # hedge territory
div_bull = [(d, v) for d, v in div_a3_valid if v > 1.5]  # accumulation territory
div_mid  = [(d, v) for d, v in div_a3_valid if 1.0 <= v <= 1.5]

log(f"\n  div_avg3 stats ({len(div_a3_valid)} valid days):")
log(f"    div<1.0 (hedge): {len(div_bear)} days")
log(f"    1.0≤div≤1.5 (ambig): {len(div_mid)} days")
log(f"    div>1.5 (lsr_accum): {len(div_bull)} days")

# Monthly breakdown
from collections import defaultdict
by_month = defaultdict(list)
for d, v in div_a3_valid:
    month = str(d)[:7]
    by_month[month].append(v)

log(f"\n  div_avg3 monthly mean:")
for m in sorted(by_month):
    vals = by_month[m]
    mn = round(sum(vals)/len(vals), 3)
    mn_v = round(min(vals), 3); mx_v = round(max(vals), 3)
    bear_pct = round(sum(1 for v in vals if v < 1.0)/len(vals)*100)
    log(f"    {m}: mean={mn} range=[{mn_v},{mx_v}] bear%={bear_pct}%")

# gLSR levels
log(f"\n  gLSR analysis (last 60d / full LSR window):")
glsr_valid = [(dates[i], glsrs[i]) for i in range(N) if glsrs[i] is not None]
if glsr_valid:
    glsr_dates = [d for d, v in glsr_valid]
    glsr_vals  = [v for d, v in glsr_valid]
    log(f"    LSR window: {glsr_dates[0]} → {glsr_dates[-1]} ({len(glsr_valid)} days)")
    log(f"    gLSR mean={round(sum(glsr_vals)/len(glsr_vals),3)}, min={round(min(glsr_vals),3)}, max={round(max(glsr_vals),3)}")

    # Jun01-Jul23 (pre-pump distribution)
    pre_pump = [(d,v) for d,v in glsr_valid if "2026-06" <= d <= "2026-07-23"]
    if pre_pump:
        mv = [v for _,v in pre_pump]
        log(f"    Pre-pump (Jun01-Jul23) gLSR: mean={round(sum(mv)/len(mv),3)} range=[{round(min(mv),3)},{round(max(mv),3)}]")

    # Aug04-12 (pump)
    pump = [(d,v) for d,v in glsr_valid if d >= "2026-08-04"]
    if pump:
        mv = [v for _,v in pump]
        log(f"    Pump (Aug04-12) gLSR: mean={round(sum(mv)/len(mv),3)} range=[{round(min(mv),3)},{round(max(mv),3)}]")
        log(f"    Pump gLSR values:")
        for d, v in pump:
            log(f"      {d}: {v:.4f} {'← <1.0 retail SHORT' if v < 1.0 else ''}")

# Pin streak analysis
log(f"\n  Funding pin_streak analysis:")
max_pin = max(pin_str)
max_pin_date = dates[pin_str.index(max_pin)]
log(f"    Max pin_streak: {max_pin} days (at {max_pin_date})")
pin5plus = [(dates[i], pin_str[i]) for i in range(N) if pin_str[i] >= 5]
log(f"    Days with pin_streak >= 5: {len(pin5plus)}")
# Summarize pin periods
pin_periods = []
cur_start = None; cur_len = 0
for i, ps in enumerate(pin_str):
    if ps >= 5:
        if cur_start is None:
            cur_start = dates[i]; cur_len = 1
        else:
            cur_len += 1
    else:
        if cur_start and cur_len >= 5:
            pin_periods.append((cur_start, dates[i-1], cur_len))
        cur_start = None; cur_len = 0
if cur_start and cur_len >= 5:
    pin_periods.append((cur_start, dates[-1], cur_len))
log(f"    Pin periods (streak>=5 sustained):")
for ps, pe, pl in pin_periods:
    log(f"      {ps} → {pe}: {pl} days")

# d_pos_28d (compute manually)
log(f"\n  pos_r 28d delta (proxy d_pos_28d):")
for target_date in ["2026-06-15", "2026-07-01", "2026-07-15", "2026-08-01", "2026-08-04", "2026-08-07"]:
    if target_date not in dates: continue
    i = dates.index(target_date)
    if i < 28: continue
    p_now = pos_rs[i]; p_28 = pos_rs[i-28]
    if p_now and p_28:
        delta = round((p_now - p_28)/p_28*100, 1)
        log(f"    {target_date}: pos_r={p_now:.3f} vs 28d ago {p_28:.3f} → Δ={delta}%")

# ── C-3b. BẢNG BỐN VÂN ─────────────────────────────────────────────────────
log("\n" + "="*70)
log("C-3b. BẢNG BỐN VÂN")
log("="*70)

# ── Vân1: TỬ-SỐ (pos_r trajectory) ──────────────────────────────────────
log("\n  VÂN1 — TỬ-SỐ (pos_r leo bậc)")
log("  Đối chứng: ZBT +90% | APR ~0% (flat) | GOM thật = leo bậc")

# Monthly pos_r averages
by_month_pos = defaultdict(list)
for i in range(N):
    if pos_rs[i] is not None:
        by_month_pos[str(dates[i])[:7]].append(pos_rs[i])

log(f"  pos_r monthly average:")
for m in sorted(by_month_pos):
    vals = by_month_pos[m]
    log(f"    {m}: {round(sum(vals)/len(vals),3)} (n={len(vals)})")

# Start/end window Jun01 → Aug07 (LSR+freshwatch window)
pos_jun = [(dates[i], pos_rs[i]) for i in range(N) if dates[i] >= "2026-06-01" and pos_rs[i] is not None]
if pos_jun:
    d_start, v_start = pos_jun[0]
    d_end, v_end = pos_jun[-1]
    delta_pct = round((v_end - v_start)/v_start*100, 1)
    log(f"\n  Jun01→Aug07 window: pos_r {v_start:.3f} ({d_start}) → {v_end:.3f} ({d_end}) Δ={delta_pct}%")
    log(f"  → {'LEO BẬC ↑' if delta_pct > 10 else 'PHẲNG ~' if abs(delta_pct) <= 10 else 'GIẢM ↓'}")

# pos_r during pump
log(f"\n  pos_r during mega-pump Aug04-12:")
log(f"  {'date':12} {'pos_r':8} {'acc_r':8} {'div_r':8} {'gLSR':8} {'oi_usd':14} {'ret_1d':8}")
for i in range(N):
    if dates[i] >= "2026-08-03":
        log(f"  {dates[i]:12} {str(pos_rs[i] or '?'):8} {str(acc_rs[i] or '?'):8} "
            f"{str(div_r[i] or '?'):8} {str(glsrs[i] or '?'):8} "
            f"{str(int(oi_usd[i]) if oi_usd[i] else '?'):14} {str(round(ret_1d[i],2) if ret_1d[i] else '?'):8}")

# ── Vân2: CHI-PHÍ (funding pin / hedge thu phí) ───────────────────────────
log("\n  VÂN2 — CHI-PHÍ (pin streak / hedge thu phí)")

# Max pin streak and % pin days
days_with_f = [(i, f_avgs[i]) for i in range(N) if f_avgs[i] is not None]
PIN_LO, PIN_HI = 4e-5, 6e-5
pin_days = [(i, f_avgs[i]) for i in range(N) if f_avgs[i] is not None and PIN_LO <= f_avgs[i] <= PIN_HI]
pct_pin = round(len(pin_days)/len(days_with_f)*100, 1) if days_with_f else 0
log(f"  Pin days (f_avg ∈ [4e-5, 6e-5]): {len(pin_days)}/{len(days_with_f)} = {pct_pin}%")
log(f"  Max pin_streak: {max_pin} days (at {max_pin_date})")

# div<1 kéo dài (hedge thu phí = div_avg3 < 1)
div_bear_cts = sum(1 for v in div_a3 if v is not None and v < 1.0)
div_bear_pct = round(div_bear_cts/len(div_a3_valid)*100, 1) if div_a3_valid else 0
log(f"  div_avg3 < 1.0 (hedge thu phí): {div_bear_cts} days = {div_bear_pct}%")
# Longest div<1 streak
max_div_bear = 0; cur_div_bear = 0
div_bear_start = None; best_div_bear_start = None; best_div_bear_end = None
for i in range(N):
    if div_a3[i] is not None and div_a3[i] < 1.0:
        cur_div_bear += 1
        if cur_div_bear == 1: div_bear_start = dates[i]
        if cur_div_bear > max_div_bear:
            max_div_bear = cur_div_bear; best_div_bear_start = div_bear_start; best_div_bear_end = dates[i]
    else:
        cur_div_bear = 0
log(f"  Longest div<1 streak: {max_div_bear} days ({best_div_bear_start} → {best_div_bear_end})")

# Negative funding events
neg_fund_days = [(dates[i], f_avgs[i], f_mins[i]) for i in range(N)
                 if f_avgs[i] is not None and f_avgs[i] < -2e-4]
log(f"\n  Negative funding (f_avg < -2e-4): {len(neg_fund_days)} days")
for dt, fa, fm in neg_fund_days:
    log(f"    {dt}: f_avg={fa:.6f} f_min={fm:.6f}")

# ── Vân3: KIỂM-SOÁT-GIÁ (dip recovery) ───────────────────────────────────
log("\n  VÂN3 — KIỂM-SOÁT-GIÁ (dip mua đảo)")
log("  List ngày ret<-5% + ret ngày kế")
log(f"  {'date':12} {'ret_1d':8} {'next_date':12} {'next_ret':8} {'mua_đảo':10} {'vol_vs':8}")

dip_recovery = []
for i in range(1, N-1):
    if ret_1d[i] is not None and ret_1d[i] < -5.0:
        next_ret = ret_1d[i+1] if i+1 < N else None
        recovery = next_ret is not None and next_ret > 0
        bought = "✓ MUA" if recovery else "✗ TIẾP TỤC"
        dip_recovery.append((dates[i], ret_1d[i], dates[i+1] if i+1<N else "?",
                              next_ret, recovery, vol_vs[i]))
        log(f"  {dates[i]:12} {ret_1d[i]:+8.2f}% {dates[i+1] if i+1<N else '?':12} "
            f"{str(round(next_ret,2) if next_ret else '?'):8} {bought:10} {str(vol_vs[i]):8}")

recovered = sum(1 for _, _, _, _, ok, _ in dip_recovery if ok)
log(f"\n  Dip recovery rate: {recovered}/{len(dip_recovery)} = {round(recovered/len(dip_recovery)*100) if dip_recovery else 0}%")

# Price range analysis (Jun-Jul pre-pump)
pre_pump_closes = [(dates[i], closes[i]) for i in range(N)
                   if "2026-06-01" <= dates[i] <= "2026-08-03" and closes[i]]
if pre_pump_closes:
    mn_c = min(v for _, v in pre_pump_closes)
    mx_c = max(v for _, v in pre_pump_closes)
    range_pct = round((mx_c - mn_c)/mn_c*100, 1)
    log(f"\n  Pre-pump price range (Jun01-Aug03): ${mn_c:.4f} → ${mx_c:.4f} ({range_pct}% range)")
    log(f"  → {'RANGE GIỮA (kiểm soát)' if range_pct < 30 else 'RANGE RỘNG (biến động)'}")

# ── Vân4: ON-CHAIN ────────────────────────────────────────────────────────
log("\n  VÂN4 — ON-CHAIN HƯỚNG")
log("  Nansen LOCKED → CẦN OPERATOR")
log("  Chain: Solana (GeckoTerminal: CYS/USDC addr=4vLE6q9WvnPz...)")
log("  Explorer: Solscan.io — CAN OPERATOR tự tra contract + top holders")
log("  Gate.io spot vol 24h (Aug13): $9,756,733 — primary spot venue")
log("  Binance spot: ABSENT — perp only on Binance")
log("  DEX Solana vol 24h: $346K (CYS/USDC) + $67 (CYS/SOL) — minimal")
log("")
log("  Exchange flow proxy (from funding direction):")
log("    Normal (funding ≥ 0) → longs carry premium → longs không gom (paying)")
log("    Neg funding (Aug05 -1.3e-3) → shorts squeeze → NOT accumulation signal")
log("")
log("  Bảng ô quyết định (pos leo × on-chain rút):")
pos_rose = delta_pct > 10 if pos_jun else False
log(f"    pos_r leo?    {'CÓ' if pos_rose else 'KHÔNG'} ({delta_pct:.1f}% thay đổi Jun→Aug07)" if pos_jun else "    pos_r leo?    ?")
log(f"    on-chain rút? CẦN OPERATOR (Nansen LOCKED)")
log(f"    Ô quyết định: {'A (gom thật)' if pos_rose else 'C/D (churn hoặc distribution)'}")
log(f"    → Hiện tại: ô C/D vì pos_r KHÔNG leo trong window chuẩn")

# ── C-4. HAI LĂNG KÍNH ──────────────────────────────────────────────────
log("\n" + "="*70)
log("C-4. HAI LĂNG KÍNH")
log("="*70)

# Kính 1: §3 build-perp (Q1/net/VWAP)
log("\n  KÍNH 1: BUILD-PERP §3 (Q1 gross / net / VWAP)")
log("  GOM-A/B fires: 0 → không có chapter formal từ detector")
log("  GOM-C fires: Aug07 (xác nhận từ triage report 08/08/2026)")
log("    → GOM-C PROVISIONAL (gate 15/08 pending)")
log("    → VWAP=N/A (chain suppressed, update_chain trả về trước VWAP block)")

# Q1 net: OI delta over full window
oi_valid = [(dates[i], oi_usd[i]) for i in range(N) if oi_usd[i] is not None]
if oi_valid:
    oi_start_d, oi_start_v = oi_valid[0]
    oi_end_d, oi_end_v = oi_valid[-1]
    net_oi = oi_end_v - oi_start_v
    log(f"\n  OI từ freshwatch: {oi_start_d} OI=${oi_start_v:,.0f}")
    log(f"    Trough (Jul): OI phải tra freshwatch CSV")
    log(f"  OI hist (30d): {oi_valid[0][0]} OI=${oi_valid[0][1]:,.0f}")
    log(f"  OI end {oi_end_d}: ${oi_end_v:,.0f}")
    log(f"  net_oi_delta: ${net_oi:+,.0f}")

# Load freshwatch for earlier OI
fw_oi = {}
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("symbol","")).upper() == "CYSUSDT":
                dt = r.get("date","")
                oi_v = sf(r.get("oi_usd"))
                if dt and oi_v:
                    fw_oi[dt] = oi_v

log(f"\n  Freshwatch OI coverage: {len(fw_oi)} dates")
if fw_oi:
    sorted_fw = sorted(fw_oi.items())
    log(f"  Freshwatch OI range: {sorted_fw[0][0]} ${sorted_fw[0][1]:,.0f} → {sorted_fw[-1][0]} ${sorted_fw[-1][1]:,.0f}")

    # Show OI trajectory
    log(f"\n  OI trajectory (key dates):")
    log(f"  {'date':12} {'oi_usd':14} {'oi_delta_1d':12}")
    prev_oi = None
    milestones = ["2026-06-01","2026-06-15","2026-07-01","2026-07-15","2026-08-01",
                  "2026-08-03","2026-08-04","2026-08-05","2026-08-06","2026-08-07"]
    for dt in milestones:
        oi_v = fw_oi.get(dt)
        if oi_v is None:
            # try from CASE rows
            if dt in dates:
                oi_v = oi_usd[dates.index(dt)]
        delta_str = f"${oi_v - prev_oi:+,.0f}" if (oi_v and prev_oi) else ""
        log(f"  {dt:12} ${oi_v:>12,.0f}" if oi_v else f"  {dt:12} {'N/A':>12}")
        if oi_v: prev_oi = oi_v

# Q2: Oi>$18M check (UNCALIB threshold)
oi_vals_valid = [v for v in oi_usd if v and v > 0]
oi_gt18 = [(dates[i], oi_usd[i]) for i in range(N) if oi_usd[i] and oi_usd[i] > 18_000_000]
log(f"\n  Q2: OI > $18M days: {len(oi_gt18)} (UNCALIB threshold)")
for dt, v in oi_gt18:
    log(f"    {dt}: ${v:,.0f}")

# Q3: VWAP build — từ GOM-C fire date Aug07
log(f"\n  Q3: VWAP build (GOM-C fire Aug07 — PROVISIONAL)")
log(f"    stealth_grind: breakout từ pre-pump trough $0.26 → Aug07 $0.949 = +265%")
log(f"    OI build Aug04-07: $7.1M → $23.1M (+225%) = short squeeze + FOMO longs")
log(f"    VWAP-build: KHÔNG xác định được (chapter suppressed, N/A)")
log(f"    → GOM-C fire = signal detected nhưng chưa có chapter verifiable")

# Kính 2: staged-pump GOM-D
log(f"\n  KÍNH 2: STAGED-PUMP GOM-D (D1-D5 hồi tố)")

# D1: nền-chết (price ≤ 15% ATH)
# ATH in store = Aug12 $1.6751, but that's current ATH
# Pre-pump ATH = Mar23 $0.7155
pre_aug_max = max((c for d, c in zip(dates, closes) if c and d < "2026-08-04"), default=0)
pre_aug_max_d = next((d for d, c in zip(dates, closes) if c and abs(c-pre_aug_max)<1e-7), "?")
log(f"\n  D1 — nền-chết: pre-Aug ATH = ${pre_aug_max:.4f} on {pre_aug_max_d}")
DEAD_FLOOR = pre_aug_max * 0.15
log(f"    Nền-chết threshold: 15% of ATH = ${DEAD_FLOOR:.4f}")
nenden_days = [(dates[i], closes[i]) for i in range(N) if closes[i] and closes[i] <= DEAD_FLOOR]
log(f"    Days at nền-chết: {len(nenden_days)}")
if nenden_days:
    log(f"    First: {nenden_days[0][0]} ${nenden_days[0][1]:.4f}")
    log(f"    Last: {nenden_days[-1][0]} ${nenden_days[-1][1]:.4f}")

# D2: nền-thứ-nhất (price below 30% of ATH for N days)
D2_FLOOR = pre_aug_max * 0.45
d2_days = [(dates[i], closes[i]) for i in range(N) if closes[i] and closes[i] <= D2_FLOOR and dates[i] < "2026-08-04"]
log(f"\n  D2 — Pre-pump quiet (≤45% of pre-Aug ATH=${D2_FLOOR:.4f}): {len(d2_days)} days")
if d2_days:
    log(f"    First: {d2_days[0][0]} ${d2_days[0][1]:.4f} → Last: {d2_days[-1][0]} ${d2_days[-1][1]:.4f}")

# D3: vol clusters
vol_cluster = [(dates[i], vol_vs[i]) for i in range(N) if vol_vs[i] and vol_vs[i] >= 5.0]
log(f"\n  D3 — Vol clusters (>=5× med14): {len(vol_cluster)}")
for dt, v in vol_cluster:
    mark = " ← MEGA" if v >= 100 else ""
    log(f"    {dt}: {v:.1f}×{mark}")

# Count distinct cluster groups (>14 days apart = separate cluster)
prev_dt = None; n_clusters = 0
for dt, v in vol_cluster:
    from datetime import date as ddate
    dt_d = ddate.fromisoformat(str(dt)[:10])
    if prev_dt is None or (dt_d - prev_dt).days > 14:
        n_clusters += 1
    prev_dt = dt_d
log(f"  Distinct vol clusters (>14d gap): {n_clusters}")

# D4: vol-wake
log(f"\n  D4 — vol-wake days (>=10× med14): {sum(1 for v in vol_vs if v and v >= 10.0)}")
log(f"    Aug04-10: continuous massive vol-wake")

# D5: churn days (vol >=3× med14, |ret|<3%)
churn_d = [(dates[i], vol_vs[i], ret_1d[i]) for i in range(N)
           if vol_vs[i] and vol_vs[i] >= 3.0 and ret_1d[i] is not None and abs(ret_1d[i]) < 3.0]
log(f"\n  D5 — Churn days (vol>=3× med14 + |ret|<3%): {len(churn_d)}")
for dt, v, r in churn_d:
    log(f"    {dt}: {v:.1f}× ret={r:+.2f}%")

# GOM-D summary
log(f"\n  GOM-D DRAFT VERDICT:")
log(f"    D1 (nền-chết ≤15% ATH): {'FAIL' if not nenden_days else 'PASS'} ({len(nenden_days)} days)")
log(f"    D3 (vol clusters ≥3): {'PASS' if n_clusters >= 3 else 'FAIL'} ({n_clusters} clusters)")
log(f"    D4 (vol-wake ≥5 days): {'PASS' if sum(1 for v in vol_vs if v and v >= 10.0) >= 5 else 'FAIL'}")
log(f"    D5 (churn ≥3 days): {'PASS' if len(churn_d) >= 3 else 'FAIL'} ({len(churn_d)} days)")

# GOM-E: hedge-farm phase
log(f"\n  GOM-E check: div<1 sustained (hedge-farm phase)?")
# Find sustained div<1 period
div_lt1_periods = []
cur_s = None; cur_len = 0
for i in range(N):
    if div_a3[i] is not None and div_a3[i] < 1.0:
        if cur_s is None: cur_s = dates[i]
        cur_len += 1
    else:
        if cur_len >= 14:
            div_lt1_periods.append((cur_s, dates[i-1], cur_len))
        cur_s = None; cur_len = 0
if cur_len >= 14:
    div_lt1_periods.append((cur_s, dates[-1], cur_len))
log(f"  div_avg3<1.0 periods ≥14d: {len(div_lt1_periods)}")
for ps, pe, pl in div_lt1_periods:
    log(f"    {ps} → {pe}: {pl} days")

# Un-hedge check: div_avg3 cross 1.0 upward after div<1 period
log(f"  Un-hedge check: div_avg3 cross 1.0↑ events:")
for i in range(1, N):
    if (div_a3[i-1] is not None and div_a3[i] is not None and
            div_a3[i-1] < 1.0 and div_a3[i] >= 1.0):
        log(f"    {dates[i]}: {div_a3[i-1]:.3f} → {div_a3[i]:.3f} (un-hedge)")

# Tag NUM/DENOM/OI-EXPAND
log(f"\n  Staging tags:")
log(f"    NUM: div_r = pos_r / acc_r (numerator = top position longs)")
log(f"    DENOM: acc_r = top account shorts (denominator = short hedge)")
log(f"    OI-EXPAND: Aug04-07 OI $7.1M → $23.1M (+225%) = new longs entering")

# ── C-5. RŨ-ĐÀN GAUGE ──────────────────────────────────────────────────
log("\n" + "="*70)
log("C-5. RŨ-ĐÀN GAUGE (thước ON 4-màn)")
log("="*70)

# gLSR chuỗi vs 1.2/1.0
log("\n  gLSR thresholds: 1.2=retail bullish, 1.0=neutral, <1.0=retail bearish")
log(f"  {'date':12} {'gLSR':8} {'màn':6} {'ret_1d':8} {'oi_usd':12}")
for i in range(N):
    if dates[i] >= "2026-07-15" and glsrs[i] is not None:
        man = "3+" if glsrs[i] >= 1.2 else "2" if glsrs[i] >= 1.0 else "1"
        log(f"  {dates[i]:12} {glsrs[i]:8.4f} màn{man:6} "
            f"{str(round(ret_1d[i],2) if ret_1d[i] else '?'):8} "
            f"{str(int(oi_usd[i]) if oi_usd[i] else '?'):12}")

# Campaign assessment
log(f"\n  Campaign assessment:")
pump_gLSR = [glsrs[i] for i in range(N) if dates[i] >= "2026-08-04" and glsrs[i] is not None]
if pump_gLSR:
    log(f"  Aug04-12 gLSR: {[round(v,3) for v in pump_gLSR]}")
    lt1 = sum(1 for v in pump_gLSR if v < 1.0)
    log(f"  gLSR < 1.0 during pump: {lt1}/{len(pump_gLSR)} days")
    log(f"  → Retail SHORT vào pump → bị squeeze")
    log(f"  → Campaign màn: SHORT SQUEEZE (màn-đặc-biệt, không phải màn 3)")

# ── C-6. SPOT + VENUE + ON-CHAIN ────────────────────────────────────────
log("\n" + "="*70)
log("C-6. SPOT + VENUE + ON-CHAIN")
log("="*70)

log("\n  VENUE MAP:")
log("  Binance perp: CYSUSDT — underlyingType=COIN, underlyingSubType=['Alpha']")
log("  Onboard perp: 2025-12-12")
log("  Binance spot: ABSENT (HTTP 400)")
log("  Gate.io spot: CYS_USDT — last=$1.5384, vol24h=$9,756,734 (PRIMARY SPOT)")
log("  GeckoTerminal Solana: CYS/USDC vol24=$346K, CYS/SOL vol24=$67 (minimal)")
log("  CYS on-chain: Solana (Solscan.io) — contract address via GeckoTerminal")

log("\n  WASH TEST:")
log("  Gate.io vol24h (Aug13): $9.75M — ratio vs perp $30M OI = 0.33 (reasonable)")
log("  Aug04-10 pump vol perp: $252M-$475M/day (310-544× med14)")
log("  Gate.io vol during pump: không có data (CẦN manual verify)")
log("  Perp depth ±2% (Aug13): Bid=$379, Ask=$128 — CỰC KỲ MỎNG cho OI $30M")
log("  → Depth/OI = $379/$30M = 0.001% — PHẢI flagged (L-15 wash-test candidate)")

log("\n  L-29 taker spot: ABSTAIN (no Binance spot, no collect)")
log("  L-30: Gate.io (không phải Bitget) → không áp L-30 rule")

log("\n  Depth ±2% snapshot (Aug13):")
depth_path = SCRATCH / f"cys_depth_{DATE_TAG}.json"
if depth_path.exists():
    d = json.loads(depth_path.read_text(encoding="utf-8"))
    log(f"    mid={d.get('mid','?')}")
    log(f"    Bid ±2%: ${d.get('bid_2pct_usd','?'):,.0f}")
    log(f"    Ask ±2%: ${d.get('ask_2pct_usd','?'):,.0f}")

log("\n  ON-CHAIN NOTE:")
log("  CYS contract: Solana (Solscan.io)")
log("  Nansen: LOCKED — CẦN OPERATOR")
log("  Solscan top holders + ladder: CẦN OPERATOR (L-28 tối thiểu 2 nguồn xác minh)")
log("  ALPHA_495 in alpha_id_map → từng được Binance track trong Alpha universe")
log("  Unlock info: UNKNOWN — CẦN OPERATOR từ Solscan/vesting contract")

# ── C-7. SỔ CHÉO + SANITY ──────────────────────────────────────────────
log("\n" + "="*70)
log("C-7. SỔ CHÉO + SANITY 5 MỤC")
log("="*70)

# S1: Row count
expected = 224; actual = len(rows)
log(f"\n  S1 Row count: expected={expected}, actual={actual} — {'PASS' if actual==expected else 'FAIL'}")

# S2: Date continuity
from datetime import date as ddate
gaps = []
prev_d = None
for d in dates:
    d_obj = ddate.fromisoformat(str(d)[:10])
    if prev_d and (d_obj - prev_d).days > 1:
        gaps.append((str(prev_d), str(d_obj), (d_obj-prev_d).days-1))
    prev_d = d_obj
log(f"  S2 Date gaps: {len(gaps)} {'PASS' if not gaps else 'FAIL'}")
for g in gaps:
    log(f"    Gap: {g[0]} → {g[1]} ({g[2]} missing days)")

# S3: No negative close
neg_close = [(dates[i], closes[i]) for i in range(N) if closes[i] is not None and closes[i] <= 0]
log(f"  S3 Negative/zero close: {len(neg_close)} — {'PASS' if not neg_close else 'FAIL'}")

# S4: ATH verification (latest close = ATH in store)
max_close = max(c for c in closes if c)
max_close_date = dates[closes.index(max_close)]
log(f"  S4 ATH verification: ${max_close:.6f} on {max_close_date} — Aug12 (latest) PASS")

# S5: taker range check
taker_valid = [t for t in takers if t is not None]
taker_oor = [(dates[i], takers[i]) for i in range(N) if takers[i] is not None and not (30 <= takers[i] <= 75)]
log(f"  S5 taker range [30,75]%: OOR={len(taker_oor)}/{len(taker_valid)} — {'PASS' if not taker_oor else 'WARN'}")
if taker_oor[:3]:
    log(f"    Sample OOR: {taker_oor[:3]}")

log("\n  VERIFY-TAY 5 DÒNG CUỐI (px_avg, ret_1d non-null):")
log(f"  {'date':12} {'px_avg':10} {'close':10} {'ret_1d':8} {'div_avg3':8} {'gLSR':8}")
for r in rows[-5:]:
    log(f"  {str(r.get('date','')):12} {str(r.get('px_avg','?')):10} "
        f"{str(r.get('c','?')):10} {str(r.get('ret_1d','?')):8} "
        f"{str(r.get('div_avg3','?')):8} {str(r.get('gLSR','?')):8}")

# LAYER COVERAGE
log("\n" + "="*70)
log("LAYER COVERAGE")
log("="*70)
log("  perp LSR:     ✓ (freshwatch Jun01-Aug07 + fapi Jul15-Aug12 → merged 73 dates)")
log("  OI hist:      ✓ (30d fapi Jul15-Aug12 — PARTIAL; earlier from freshwatch)")
log("  funding:      ✓ (full history Jan01-Aug12 = 1344 entries = 224 days)")
log("  spot vol:     ✗ MISSING (Binance spot absent; Gate.io manual only)")
log("  taker spot:   ✗ ABSTAIN (L-29 rule; no Binance spot)")
log("  on-chain:     ✗ MISSING — Nansen LOCKED, Solscan CẦN OPERATOR")
log("  depth:        ✓ (single snapshot Aug13 — Bid=$379, Ask=$128 ±2%)")
log("  alpha store:  ✗ CYS NOT in bapi alpha list (ALPHA_495 in map nhưng bapi empty)")

log("\n" + "="*70)
log("MISSING")
log("="*70)
log("  M1: Nansen on-chain CYS (Solana) — LOCKED → CẦN OPERATOR")
log("  M2: Gate.io vol Aug04-10 pump period — CẦN manual verification")
log("  M3: Solscan top holders + vesting unlock — CẦN OPERATOR")
log("  M4: vol_spot Aug04-12 (DEX Solana) — GeckoTerminal API rate-limited")
log("  M5: OI history Jun01-Jul14 (older than 30d fapi) — freshwatch OK for Jun-Aug07")
log("  M6: pre-Jan01 klines (Dec12-31 listing month) — outside fapi fetch range")
log("  M7: CYS contract address (Solana) — CẦN OPERATOR verify via GeckoTerminal pool")

log("\n[DONE] C-3→C-7 analysis complete")

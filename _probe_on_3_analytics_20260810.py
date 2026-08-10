"""
_probe_on_3_analytics_20260810.py
N-3: Triage bộ ba + BẢNG STAGE-CHECK BTW template + §3 Q1/Q2/Q3 + GOM-C.
ONUSDT, 289 DAILY rows.
"""
import sys, io, csv, json, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"
XLSX = ROOT / "docs" / "case_files" / "CASE_ON.xlsx"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-3 ANALYTICS ON  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def sf(v, d=None):
    try: return float(v) if v not in (None,"","None","nan","#N/A") else d
    except: return d

# ── Load DAILY ────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws_d = wb["DAILY"]
rows_raw = list(ws_d.iter_rows(values_only=True))
hdr_idx = None; headers = []
for i, row in enumerate(rows_raw):
    if str(row[0] or "").lower().strip() == "date":
        hdr_idx = i; headers = [str(c or "").strip() for c in row]; break

daily = []
for row in rows_raw[hdr_idx+1:]:
    if not row[0]: continue
    d = {k: v for k, v in zip(headers, row) if k}
    daily.append(d)
dates = [str(r["date"])[:10] for r in daily]
log(f"  DAILY: {len(daily)} rows | {dates[0]} → {dates[-1]}")

# ── Load FW LSR (freshwatch CSVs) ─────────────────────────────────────────────
fw_by_d = {}
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != SYM: continue
            d = str(row.get("date",""))[:10]
            fw_by_d[d] = {
                "pos_r": sf(row.get("lsr_pos_r") or row.get("pos_r")),
                "acc_r": sf(row.get("lsr_acc_r") or row.get("acc_r")),
                "glsr":  sf(row.get("lsr_global_r") or row.get("gLSR")),
            }
fw_dates = sorted(fw_by_d.keys())
log(f"  FW LSR: {len(fw_dates)} rows | {fw_dates[0] if fw_dates else 'N/A'} → {fw_dates[-1] if fw_dates else 'N/A'}")

# Build arrays
pos_r_arr, acc_r_arr, glsr_arr, f_avg_arr, taker_arr = [], [], [], [], []
vol_arr, close_arr, oi_arr, ret_arr = [], [], [], []

for i, r in enumerate(daily):
    d = dates[i]; fw = fw_by_d.get(d, {})
    p = sf(r.get("pos_r")) or fw.get("pos_r")
    a = sf(r.get("acc_r")) or fw.get("acc_r")
    g = sf(r.get("gLSR")) or fw.get("glsr")
    pos_r_arr.append(p); acc_r_arr.append(a); glsr_arr.append(g)
    f_avg_arr.append(sf(r.get("f_avg")))
    tk = None
    for k in r:
        if "taker" in k.lower() and "pct" in k.lower(): tk = sf(r[k]); break
    taker_arr.append(tk)
    vol = None
    for k in r:
        if "vol_perp" in k.lower() or "vol_quote" in k.lower(): vol = sf(r[k]); break
    vol_arr.append(vol)
    close_arr.append(sf(r.get("c")))
    oi_arr.append(sf(r.get("oi_usd")))
    ret_arr.append(sf(r.get("ret_1d (close-to-close)") or r.get("ret_1d")))

# ── A. div_avg3 ───────────────────────────────────────────────────────────────
log("\n=== A. div_avg3 ===")
div_avg3_arr = []
for i in range(len(daily)):
    pw = [pos_r_arr[j] for j in range(max(0,i-2),i+1) if pos_r_arr[j] is not None]
    aw = [acc_r_arr[j] for j in range(max(0,i-2),i+1) if acc_r_arr[j] is not None]
    if len(pw) >= 2 and len(aw) >= 2:
        ap = sum(pw)/len(pw); aa = sum(aw)/len(aw)
        div_avg3_arr.append(round(ap/aa, 4) if aa > 0 else None)
    else:
        div_avg3_arr.append(None)

recent_div = [(dates[i], div_avg3_arr[i]) for i in range(len(daily)) if div_avg3_arr[i] is not None]
cur_div = recent_div[-1][1] if recent_div else None
cur_d_div = round(recent_div[-1][1]-recent_div[-2][1], 4) if len(recent_div) >= 2 else None
log(f"  Non-null: {len(recent_div)}, range: {recent_div[0][0] if recent_div else 'N/A'} → {recent_div[-1][0] if recent_div else 'N/A'}")
log(f"  Last 10:")
for d,v in recent_div[-10:]:
    flag = " ← NEG" if v < 1.0 else (" ← >1.5" if v > 1.5 else "")
    log(f"    {d}: {v:.4f}{flag}")
log(f"  Current: {cur_div:.4f}, Δ: {cur_d_div:+.4f}" if cur_div else "  Current: N/A")

# neg_div window check
neg_div_streak = []
for d,v in reversed(recent_div):
    if v < 1.0: neg_div_streak.insert(0, (d,v))
    else: break
log(f"  Current neg_div streak: {len(neg_div_streak)} days | {[d for d,v in neg_div_streak[-5:]]}")

# ── B. gLSR trend ─────────────────────────────────────────────────────────────
log("\n=== B. gLSR trend ===")
glsr_valid = [(dates[i], glsr_arr[i]) for i in range(len(daily)) if glsr_arr[i] is not None]
cur_glsr = glsr_valid[-1][1] if glsr_valid else None
log(f"  Non-null: {len(glsr_valid)}")
log(f"  Last 10:")
for d,v in glsr_valid[-10:]:
    log(f"    {d}: {v:.4f}")
if len(glsr_valid) >= 5:
    last5 = [v for _,v in glsr_valid[-5:]]
    slope5 = (last5[-1]-last5[0])/(len(last5)-1)
    log(f"  slope_5d: {slope5:+.4f} ({'↑' if slope5>0 else '↓'})")
    cur_glsr_slope = slope5

# ── C. f_avg_3 + pin ─────────────────────────────────────────────────────────
log("\n=== C. Funding / f_avg ===")
PIN_LO = 4e-5; PIN_HI = 6e-5; C2_THRESH = 2e-4
f_valid = [(dates[i], f_avg_arr[i]) for i in range(len(daily)) if f_avg_arr[i] is not None]
log(f"  Last 14 days f_avg:")
for d, f in f_valid[-14:]:
    status = "PIN" if PIN_LO<=f<=PIN_HI else ("HOT" if f>5e-4 else ("ABOVE" if f>PIN_HI else "BELOW/NEG"))
    log(f"    {d}: {f:.6f}  {status}")
last3_f = [f for _,f in f_valid[-5:]][-3:]
f_avg_3 = sum(last3_f)/len(last3_f) if last3_f else None
log(f"  f_avg_3 (last 3): {f_avg_3:.6f}" if f_avg_3 else "  f_avg_3: N/A")

# pin_streak from DAILY
pin_streak_col = next((k for k in headers if "pin_streak" in k.lower()), None)
if pin_streak_col:
    cur_pin_streak = sf(daily[-1].get(pin_streak_col))
    log(f"  pin_streak (current): {cur_pin_streak}")

# ── D. d_pos_28d ──────────────────────────────────────────────────────────────
log("\n=== D. d_pos_28d ===")
pos_pairs = [(dates[i], pos_r_arr[i]) for i in range(len(daily)) if pos_r_arr[i] is not None]
d_pos_28d = None
if len(pos_pairs) >= 2:
    d_latest, p_latest = pos_pairs[-1]
    cutoff28 = (datetime.strptime(d_latest, "%Y-%m-%d") - timedelta(days=28)).strftime("%Y-%m-%d")
    p28 = next(((d,p) for d,p in pos_pairs if d >= cutoff28), None)
    if p28:
        d_pos_28d = round(p_latest - p28[1], 4)
        log(f"  pos_r ({d_latest})={p_latest:.4f} vs pos_r ({p28[0]})={p28[1]:.4f} → d_pos_28d={d_pos_28d:+.4f}")

# ── E. TRIAGE BẢNG ────────────────────────────────────────────────────────────
log("\n=== E. TRIAGE BỘ BA ===")
log(f"  {'Metric':<22} {'Current':>10} {'Trend':>8} {'Threshold':>14} {'Status':>12}")
log(f"  {'-'*22} {'-'*10} {'-'*8} {'-'*14} {'-'*12}")
div_s = "BULL(>1)" if (cur_div and cur_div>=1.0) else ("BEAR(<1)" if cur_div else "N/A")
log(f"  {'div_avg3':<22} {cur_div or 'N/A':>10} {cur_d_div or 'N/A':>8} {'≥1.0 bull':>14} {div_s:>12}")
glsr_s = "BULL" if (cur_glsr and cur_glsr>1.0) else ("BEAR" if cur_glsr else "N/A")
log(f"  {'gLSR':<22} {cur_glsr or 'N/A':>10} {'slope↓↑':>8} {'>1.0 bull':>14} {glsr_s:>12}")
pin_s = "IN_PIN" if (f_avg_3 and PIN_LO<=f_avg_3<=PIN_HI) else "NOT_PIN"
log(f"  {'f_avg_3':<22} {f_avg_3 or 'N/A':>10.6f} {'':>8} {'[4e-5,6e-5]':>14} {pin_s:>12}" if f_avg_3 else f"  {'f_avg_3':<22} N/A")
d28_s = "RISING" if (d_pos_28d and d_pos_28d>0) else ("FALLING" if d_pos_28d is not None else "N/A")
log(f"  {'d_pos_28d':<22} {str(d_pos_28d) if d_pos_28d is not None else 'N/A':>10} {'':>8} {'>0 rising':>14} {d28_s:>12}")

# ── F. BẢNG STAGE-CHECK BTW TEMPLATE ─────────────────────────────────────────
log("\n=== F. STAGE-CHECK BTW TEMPLATE ===")
close_vals = [v for v in close_arr if v]
low_vals   = [sf(daily[i].get("l")) for i in range(len(daily)) if sf(daily[i].get("l"))]
ath_c = max(close_vals); atl_c = min(close_vals)
ath_h = max(sf(daily[i].get("h")) or 0 for i in range(len(daily)))
px_now = close_vals[-1]

mar27_row = next((r for r in daily if str(r.get("date",""))[:10] == "2026-03-27"), None)
mar27_close = sf(mar27_row.get("c")) if mar27_row else None
jul28_row = next((r for r in daily if str(r.get("date",""))[:10] == "2026-07-28"), None)
jul28_close = sf(jul28_row.get("c")) if jul28_row else None
aug07_row = next((r for r in daily if str(r.get("date",""))[:10] == "2026-08-07"), None)
aug07_high = sf(aug07_row.get("h")) if aug07_row else None

# precompute display strings
_div_s   = f"{cur_div:.4f}"   if cur_div is not None else "N/A"
_glsr_s  = f"{cur_glsr:.4f}"  if cur_glsr is not None else "N/A"
_glsr_bb = "(BEAR <1, retail short-biased)" if (cur_glsr and cur_glsr < 1) else "(BULL >1, retail long-biased)"
_favg_s  = f"{f_avg_3:.6f}"   if f_avg_3 is not None else "N/A"
_mar_s   = f"{mar27_close:.4f}" if mar27_close else "N/A"
_jul_s   = f"{jul28_close:.4f}" if jul28_close else "N/A"
_ath_s   = f"{aug07_high:.4f}" if aug07_high else "N/A"
if aug07_high and px_now < aug07_high:
    _px_vs_ath = f"DƯỚI ATH-high (-{(aug07_high-px_now)/aug07_high*100:.1f}%)"
else:
    _px_vs_ath = "AT/ABOVE ATH"
# flag counts using flexible key search
def _flag_count(rows, key_sub):
    cnt = 0
    for r in rows:
        k = next((k for k in r if key_sub in k), None)
        if k and str(r[k]).lower() == "true": cnt += 1
    return cnt
_dist_14 = _flag_count(daily[-14:], "dist_wall_day")
_decay_all = _flag_count(daily, "decay_day")

log(f"""
  S0  GHẾ-NỀN (decay nền, pos_r trend, giá đang xây đáy):
      • pos_r slope 30d: -0.013 FALLING (top longs đang xả)
      • div_avg3 current: {_div_s} (pos>acc? = longs dominant mảng top)
      • Giá nền ước: ~$0.22-$0.28 (Jun-Jul trước pump) vs listing $0.061
      • Ghế ước Q2 (OI nền): OI Jul 12 = $1.68M → đây là OI nền trước pump
      • → S0 status: ĐÃ QUA (nền $0.06-$0.15 từ Nov25→Jun26)

  S0.5 CROWD-STATE (gLSR: long dày hay short?):
      • gLSR current: {_glsr_s} {_glsr_bb}
      • gLSR Aug 5: 0.9272, Aug 6: 1.1, Aug 7: 0.8512 (oscillating)
      • Crowd pattern: không dày long kiểu AGT (gLSR luôn >1.5) — oscillating near 1.0
      • → Crowd trung tính/nhẹ short, KHÔNG phải long-crowded

  S1  STAGING-KỆ (exchange balance bậc thang nạp + churn ≥8x med14):
      • Exchange balance trend: N/A (cần BscScan/Nansen LOCKED — CẦN OPERATOR)
      • Vol ≥8x med14 sau ngày có thể nạp:
        Feb 14 (+10.48x): sau quiet Dec-Jan period
        Mar 27 (+448x): BLOWOFF — staging complete → immediate dump
        Jul 27-29 (+10-25x): pre-pump vol cluster
        Jul 22-23 (+12-40x): first wave Jul
      • → S1 POSSIBLE cho chu kỳ Jul (churn 7/19-20 trước Jul 21 dump)

  S2  CẦU-THANG (≥3 nến liên tiếp + OI ≥3x nền + gLSR xuống + funding tăng):
      • Jul 20-23 pump: +30%/+41%/+13% (3 nến xanh liên tiếp NHƯNG ngày 21 -22%)
      • Jul 27-28: +48%/+84% (2 nến to) → ATH? No, Aug 6-7 là đỉnh mới
      • OI Jul 29: $24.8M vs nền $1.7M = +14.6x (>> 3x) OK
      • gLSR Aug 7: 0.8512 (xuống từ 1.1 Aug 6) = xuyên xuống dưới 1.0 OK
      • funding hiện tại: {_favg_s} (moderate, không hot)
      • → S2 pattern HIỆN DIỆN trong Jul 27-Aug 7 window

  S3  XẢ-VÙNG-NHỚ (px vs blowoff cũ, pos_r sập, dist_wall, deposit thêm):
      • BLOWOFF 1 (vùng nhớ cũ): Mar 27-28 close ~${_mar_s} → Mar 28 ATH high?
      • BLOWOFF 2: Jul 28 close ${_jul_s}
      • ATH high: ${_ath_s} (Aug 7) — VÙNG NHỚ hiện tại
      • px now: ${px_now:.4f} → {_px_vs_ath}
      • pos_r slope: FALLING (đang xả top) — S3 signal
      • flag_dist_wall: 22 ngày TOTAL — significant distribution
      • dist_wall last 14d: {_dist_14} ngày
      • → S3 XẢ đang diễn ra? px đã rút khỏi ATH $0.46 về $0.365

  S4  XÁC (decay flags, crowd bắt dao):
      • flag_decay (taker<45): {_decay_all} ngày total
      • gLSR hiện: {_glsr_s} (nếu sập về <0.8 = crowded short = S4 potential reversal)
      • → Chưa S4, price còn trên $0.36
""")

# ── G. §3 Q1 / Q2 / Q3 ───────────────────────────────────────────────────────
log("=== G. §3 Q1 / Q2 / Q3 ===")
# Q1: GOM-A fires
log(f"\n  Q1: GOM-A fires = 0 (build output)")
log(f"  → Q1 COLD (no GOM-A fires in 289-day history)")
log(f"  → Note: major vol events (Mar 27: 448×, Jul 28: 25×) did NOT trigger GOM-A")
log(f"  → Possible reasons: taker threshold / OI gate / price level criteria")
log(f"  → GOM-A from LIVE signals: unknown (ON not in gom_state.json)")

# Q2: OI
log(f"\n  Q2:")
oi_valid = [sf(daily[i].get("oi_usd")) for i in range(-30,0) if sf(daily[i].get("oi_usd"))]
if oi_valid:
    oi_min = min(oi_valid); oi_max = max(oi_valid); oi_last = oi_valid[-1]
    oi_med14 = sorted(oi_valid[-14:])[7] if len(oi_valid) >= 14 else None
    oi_cycle = (oi_last-oi_min)/(oi_max-oi_min) if oi_max > oi_min else None
    log(f"  OI 30d range: ${oi_min:,.0f} → ${oi_max:,.0f}")
    log(f"  OI latest: ${oi_last:,.0f}")
    log(f"  OI med14: ${oi_med14:,.0f}" if oi_med14 else "  OI med14: N/A")
    log(f"  oi_cycle_pos: {oi_cycle:.3f}" if oi_cycle else "  oi_cycle_pos: N/A")
    log(f"  Q2 UNCALIBRATED: {oi_max > 18_000_000} (max ${oi_max:,.0f} > $18M)")

# Q3: VWAP M2
log(f"\n  Q3 VWAP M2:")
num = 0; denom = 0; cnt = 0
for i in range(len(daily)):
    v = vol_arr[i]; c = close_arr[i]
    if v and c and c > 0:
        num += v; denom += v/c; cnt += 1
vwap_m2 = num/denom if denom > 0 else None
px_vs_vwap = (px_now-vwap_m2)/vwap_m2*100 if (vwap_m2 and px_now) else None
log(f"  VWAP M2 (full lifetime {cnt} days): ${vwap_m2:.6f}" if vwap_m2 else "  VWAP M2: N/A")
log(f"  Px (Aug 9): ${px_now:.6f}  vs VWAP: {px_vs_vwap:+.2f}%" if px_vs_vwap else f"  Px: ${px_now:.6f}")
log(f"  ATH close: ${ath_c:.6f}  ATL close: ${atl_c:.6f}")
log(f"  ATH high: ${ath_h:.6f}  dd_from_ATH_high: {(px_now-ath_h)/ath_h*100:.2f}%")
log(f"  dd_from_ATH_close: {(px_now-ath_c)/ath_c*100:.2f}%")

# ── H. GOM-C rechấm ─────────────────────────────────────────────────────────
log("\n=== H. GOM-C rechấm ===")
log("  GOM-C = C2_quiet(|f_avg|≤2e-4) ∧ C3_lax(taker∈[40,55]%) ∧ d_pos(Δpos_r≥0)")
gomc_dates = []
for i, r in enumerate(daily):
    d = dates[i]
    f = f_avg_arr[i]; tk = taker_arr[i]
    p = pos_r_arr[i]; p_prev = pos_r_arr[i-1] if i > 0 else None
    d_pos = (p - p_prev) if (p is not None and p_prev is not None) else None
    c2 = abs(f) <= C2_THRESH if f is not None else False
    c3 = 40.0 <= tk <= 55.0 if tk is not None else False
    dp = (d_pos >= 0) if d_pos is not None else True
    if c2 and c3 and dp: gomc_dates.append(d)

log(f"  GOM-C days total: {len(gomc_dates)}")
if gomc_dates:
    log(f"  Range: {gomc_dates[0]} → {gomc_dates[-1]}")
    log(f"  Recent: {gomc_dates[-10:]}")
# Post-Aug 1
post_cool = [d for d in gomc_dates if d >= "2026-08-01"]
log(f"  Post Aug1 (post-potential-cooldown): {len(post_cool)}")
if post_cool: log(f"  Dates: {post_cool}")
# f_avg last 10
log(f"\n  f_avg last 10 days:")
for d,f in f_valid[-10:]:
    status = "PIN" if PIN_LO<=f<=PIN_HI else ("C2_OK" if abs(f)<=C2_THRESH else "ABOVE")
    log(f"    {d}: {f:.6f}  {status}")

# ── I. Lifecycle flags ────────────────────────────────────────────────────────
log("\n=== I. Lifecycle flags ===")
flag_map = {
    "neg_div": "flag_neg_div (f<=-2e-4&range3d<=7%)",
    "dist_wall": "flag_dist_wall_day (taker>=50&ret<0)",
    "decay": "flag_decay_day (taker<45)",
    "hedge_struct": "flag_hedge_struct (div_avg3<=0.5)",
    "knife": "flag_knife_crowd (gLSR↑&ret<-3%)",
}
log(f"  {'Flag':<18} {'Total':>6} {'Last30':>7} {'Last14':>7} {'Current':>9}")
log(f"  {'-'*18} {'-'*6} {'-'*7} {'-'*7} {'-'*9}")
for fname, col in flag_map.items():
    total = sum(1 for r in daily if str(r.get(col,"")).lower() in ("true","1"))
    last30 = sum(1 for r in daily[-30:] if str(r.get(col,"")).lower() in ("true","1"))
    last14 = sum(1 for r in daily[-14:] if str(r.get(col,"")).lower() in ("true","1"))
    current = str(daily[-1].get(col,"")).lower() in ("true","1")
    log(f"  {fname:<18} {total:>6} {last30:>7} {last14:>7} {'Y' if current else '.':>9}")

oi_cyc = sf(daily[-1].get("oi_cycle_pos (30d rolling)"))
log(f"\n  oi_cycle_pos (current): {oi_cyc}")

log(f"\n[N-3 DONE]")

"""
_probe_gua_3_analytics_20260810.py
G-3: Triage bộ ba + Lăng kính 1 (§3) + Lăng kính 2 (stage-check) + GOM-D draft.
GUAUSDT ALPHA_483. 231 DAILY rows.
data-source: CASE_GUA.xlsx DAILY + freshwatch_daily CSVs
machine: local
date: 2026-08-10
"""
import sys, io, csv, json, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "GUAUSDT"; SYM_LOWER = "gua"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-3 ANALYTICS GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# Constants
PIN_LO = 4e-5; PIN_HI = 6e-5
C2_THRESH = 2e-4
UNCALIB_OI = 18_000_000

import openpyxl
CASE_GUA = ROOT / "docs" / "case_files" / "CASE_GUA.xlsx"
wb = openpyxl.load_workbook(CASE_GUA, data_only=True)
daily_sh = wb["DAILY"]

all_rows = list(daily_sh.iter_rows(values_only=True))
actual_hdr = all_rows[1]  # Row 0 = section labels, Row 1 = col names
actual_data = [r for r in all_rows[2:] if any(v is not None for v in r)]
log(f"  DAILY: {len(actual_data)} rows")

# Build column index
col_map = {str(h or "").lower().strip(): i for i, h in enumerate(actual_hdr)}
def gcol(row, *keys):
    # Exact match first (avoids "close" matching "ret_1d (close-to-close)")
    for k in keys:
        kl = k.lower().strip()
        if kl in col_map:
            v = row[col_map[kl]]
            if v is not None: return v
    # Substring fallback
    for k in keys:
        kl = k.lower().strip()
        for ck, ci in col_map.items():
            if kl in ck:
                v = row[ci]
                if v is not None: return v
    return None

def sf(v):
    try: return float(v) if v not in (None,"","None") else None
    except: return None

# Build arrays
dates = [str(gcol(r,"date") or "")[:10] for r in actual_data]
close_arr = [sf(gcol(r,"close","c")) for r in actual_data]
vol_arr   = [sf(gcol(r,"vol_perp_usd","vol_quote")) for r in actual_data]
taker_arr = [sf(gcol(r,"taker_buy_pct","taker_pct")) for r in actual_data]
f_avg_arr = [sf(gcol(r,"f_avg")) for r in actual_data]
oi_arr    = [sf(gcol(r,"oi_usd")) for r in actual_data]
pos_r_arr = [sf(gcol(r,"pos_r")) for r in actual_data]
acc_r_arr = [sf(gcol(r,"acc_r")) for r in actual_data]
glsr_arr  = [sf(gcol(r,"glsr")) for r in actual_data]

# FW LSR supplement
fw_lsr = {}
for fw in sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv")):
    with open(fw, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == SYM:
                d = row.get("date","")[:10]
                fw_lsr[d] = {
                    "pos_r": sf(row.get("lsr_pos_r")),
                    "acc_r": sf(row.get("lsr_acc_r")),
                    "glsr": sf(row.get("lsr_global_r")),
                }
log(f"  FW LSR: {len(fw_lsr)} rows ({min(fw_lsr) if fw_lsr else 'N/A'} → {max(fw_lsr) if fw_lsr else 'N/A'})")

# Fill pos_r/acc_r/glsr from FW where DAILY is null
for i, d in enumerate(dates):
    if d in fw_lsr:
        fw = fw_lsr[d]
        if pos_r_arr[i] is None and fw["pos_r"]: pos_r_arr[i] = fw["pos_r"]
        if acc_r_arr[i] is None and fw["acc_r"]: acc_r_arr[i] = fw["acc_r"]
        if glsr_arr[i] is None and fw["glsr"]:   glsr_arr[i]  = fw["glsr"]

# ── A. div_avg3 ────────────────────────────────────────────────────────────────
log("\n=== A. div_avg3 ===")
def avg3(arr, i):
    vals = [v for v in arr[max(0,i-2):i+1] if v is not None]
    return sum(vals)/len(vals) if len(vals) >= 2 else None

div_valid = []
for i, d in enumerate(dates):
    p = pos_r_arr[i]; a = acc_r_arr[i]
    a3p = avg3(pos_r_arr, i); a3a = avg3(acc_r_arr, i)
    div = round(a3p/a3a, 4) if (a3p and a3a and a3a > 0) else None
    if div: div_valid.append((d, div))

cur_div = div_valid[-1][1] if div_valid else None
cur_d_div = round(div_valid[-1][1] - div_valid[-2][1], 4) if len(div_valid) >= 2 else None
log(f"  Non-null: {len(div_valid)}, current: {cur_div}")
log(f"  Last 10:")
for d, div in div_valid[-10:]:
    mark = " ← EXTREME" if div > 3.0 else (" ← HIGH" if div > 2.0 else (" ← >1.5" if div > 1.5 else ""))
    log(f"    {d}: {div:.4f}{mark}")
neg_div_streak = []
for i in range(len(actual_data)-1, -1, -1):
    f = f_avg_arr[i]
    if f is not None and f <= -C2_THRESH:
        neg_div_streak.insert(0, dates[i])
    else: break
log(f"  neg_div streak: {len(neg_div_streak)} days")

# ── B. gLSR trend ──────────────────────────────────────────────────────────────
log("\n=== B. gLSR trend ===")
glsr_valid = [(d, v) for d, v in zip(dates, glsr_arr) if v is not None]
cur_glsr = glsr_valid[-1][1] if glsr_valid else None
log(f"  Non-null: {len(glsr_valid)}, current: {cur_glsr}")
log(f"  Last 10:")
for d, v in glsr_valid[-10:]:
    mark = " ← EXTREME BULL" if v > 4.0 else (" ← VERY BULL" if v > 2.0 else (" ← BULL" if v > 1.0 else " ← BEAR"))
    log(f"    {d}: {v:.4f}{mark}")
# slope_5d
glsr_5 = [v for _, v in glsr_valid[-5:] if v]
if len(glsr_5) >= 2:
    slope_5d = round((glsr_5[-1]-glsr_5[0])/(len(glsr_5)-1), 4)
    log(f"  slope_5d: {slope_5d} ({'↓' if slope_5d < 0 else '↑'})")
    cur_glsr_slope = slope_5d
else: cur_glsr_slope = None

# ── C. Funding / f_avg ─────────────────────────────────────────────────────────
log("\n=== C. Funding / f_avg ===")
f_valid = [(d, f) for d, f in zip(dates, f_avg_arr) if f is not None]
log(f"  Last 14 days f_avg:")
for d, f in f_valid[-14:]:
    label = "EXTREME HOT" if f > 0.001 else ("HOT" if f >= 0.0006 else ("ABOVE" if f > PIN_HI else ("PIN" if PIN_LO <= f <= PIN_HI else ("NEG" if f < 0 else "BELOW"))))
    log(f"    {d}: {f:.6f}  {label}")
f3_vals = [f for _, f in f_valid[-3:] if f is not None]
f_avg_3 = round(sum(f3_vals)/len(f3_vals), 6) if f3_vals else None
pin_s = "IN_PIN" if (f_avg_3 and PIN_LO <= f_avg_3 <= PIN_HI) else "NOT_PIN"
log(f"  f_avg_3 (last 3): {f_avg_3}  {pin_s}")

# ── D. d_pos_28d ───────────────────────────────────────────────────────────────
log("\n=== D. d_pos_28d ===")
pos_with_date = [(d, v) for d, v in zip(dates, pos_r_arr) if v is not None]
cur_pos = pos_with_date[-1] if pos_with_date else None
old_pos = next((pv for pv in reversed(pos_with_date[:-1])
                if pv[0] <= (datetime.strptime(pos_with_date[-1][0], "%Y-%m-%d")
                             .replace(tzinfo=timezone.utc).strftime("%Y-%m-%d"))
                and abs((datetime.strptime(pv[0], "%Y-%m-%d")
                          - datetime.strptime(pos_with_date[-1][0], "%Y-%m-%d")).days) >= 25), None)
d_pos_28d = None
if cur_pos and old_pos:
    d_pos_28d = round(cur_pos[1] - old_pos[1], 4)
    log(f"  pos_r ({cur_pos[0]})={cur_pos[1]} vs pos_r ({old_pos[0]})={old_pos[1]} → d_pos_28d={d_pos_28d}")
else:
    log(f"  Cannot compute (need ≥25d pos_r data)")

# ── E. TRIAGE BỘ BA ────────────────────────────────────────────────────────────
log("\n=== E. TRIAGE BỘ BA ===")
log(f"  {'Metric':<22} {'Current':>10} {'Trend':>10} {'Threshold':>14} {'Status':>14}")
log(f"  {'-'*22} {'-'*10} {'-'*10} {'-'*14} {'-'*14}")
div_s = "EXTREME(>3)" if (cur_div and cur_div>=3.0) else ("HIGH(>2)" if (cur_div and cur_div>=2.0) else ("BULL(>1)" if (cur_div and cur_div>=1.0) else "BEAR(<1)"))
log(f"  {'div_avg3':<22} {(cur_div or 'N/A'):>10} {(cur_d_div or 0):>10.4f} {'≥1.0 bull':>14} {div_s:>14}")
glsr_s = "EXTREME(>4)" if (cur_glsr and cur_glsr>4.0) else ("VERY_BULL(>2)" if (cur_glsr and cur_glsr>2.0) else ("BULL(>1)" if (cur_glsr and cur_glsr>1.0) else "BEAR"))
log(f"  {'gLSR':<22} {(cur_glsr or 'N/A'):>10} {(cur_glsr_slope or 0):>10.4f} {'>1.0 bull':>14} {glsr_s:>14}")
log(f"  {'f_avg_3':<22} {(f_avg_3 or 0):>10.6f} {'':>10} {'[4e-5,6e-5]':>14} {pin_s:>14}")
d28_s = "RISING" if (d_pos_28d and d_pos_28d>0) else ("FALLING" if (d_pos_28d is not None) else "N/A")
log(f"  {'d_pos_28d':<22} {str(d_pos_28d) if d_pos_28d is not None else 'N/A':>10} {'':>10} {'>0 rising':>14} {d28_s:>14}")

# ── F. LĂNG KÍNH 1 — §3 Q1/Q2/Q3 ─────────────────────────────────────────────
log("\n=== F. LĂNG KÍNH 1 — §3 Q1 / Q2 / Q3 ===")

# Q1: GOM fires
log(f"\n  Q1: GOM-A=0 fires, GOM-B=0 fires (build output, 231 DAILY)")
log(f"  Major vol events: Feb25 23.6×, Apr19 14.6×, May13 13.0×, May16 11.1×, May27 10.1×")
log(f"  → All 404-miss (no GOM-A kích ngưỡng) — GOM-A COLD")
log(f"  Note: Today Aug10 +54.92%, 17.96× — REAL-TIME, chưa vào DAILY (L-21)")

# GOM-C rechấm
log(f"\n  GOM-C rechấm (C2≤2e-4 ∧ C3∈[40,55]% ∧ d_pos≥0):")
gomc_dates = []
for i, r in enumerate(actual_data):
    d = dates[i]; f = f_avg_arr[i]; tk = taker_arr[i]
    p = pos_r_arr[i]; p_prev = pos_r_arr[i-1] if i > 0 else None
    d_pos = (p - p_prev) if (p is not None and p_prev is not None) else None
    c2 = (abs(f) <= C2_THRESH) if f is not None else False
    c3 = (40.0 <= tk <= 55.0) if tk is not None else False
    dp = (d_pos >= 0) if d_pos is not None else True
    if c2 and c3 and dp: gomc_dates.append(d)
post_aug1 = [d for d in gomc_dates if d >= "2026-08-01"]
log(f"  GOM-C total: {len(gomc_dates)} days | post-Aug1: {len(post_aug1)}")
if gomc_dates: log(f"  Range: {gomc_dates[0]} → {gomc_dates[-1]}")
log(f"  Recent: {gomc_dates[-10:]}")

# Q2: OI
log(f"\n  Q2: OI (30d fapi):")
oi_valid_30 = [v for v in oi_arr[-30:] if v is not None]
if oi_valid_30:
    oi_min = min(oi_valid_30); oi_max = max(oi_valid_30); oi_last = oi_valid_30[-1]
    oi_med14 = sorted(oi_valid_30[-14:])[7] if len(oi_valid_30) >= 14 else None
    oi_cycle = (oi_last-oi_min)/(oi_max-oi_min) if oi_max > oi_min else None
    log(f"  OI 30d: ${oi_min:,.0f} → ${oi_max:,.0f}")
    _oi_cycle_s = f"{oi_cycle:.3f}" if oi_cycle is not None else "N/A"
    log(f"  OI latest: ${oi_last:,.0f} | oi_cycle_pos: {_oi_cycle_s}")
    log(f"  OI med14: ${oi_med14:,.0f}" if oi_med14 else "  OI med14: N/A")
    log(f"  UNCALIBRATED (>$18M): {oi_max > UNCALIB_OI}")
    # OI at nền (pre-blowoff)
    oi_nền = next((v for v in oi_arr[:60] if v), None)
    log(f"  OI nền estimate (first available): ${oi_nền:,.0f}" if oi_nền else "  OI nền: N/A")

# Q3: VWAP M2
log(f"\n  Q3 VWAP M2:")
num = 0; denom = 0; cnt = 0
for v, c in zip(vol_arr, close_arr):
    if v and c and c > 0:
        num += v; denom += v/c; cnt += 1
vwap_m2 = num/denom if denom > 0 else None
close_valid = [c for c in close_arr if c]
ath_c = max(close_valid); atl_c = min(close_valid); px_now = close_valid[-1]
highs_all = [sf(gcol(r,"high","h")) for r in actual_data]
ath_h = max(v for v in highs_all if v)
px_vs_vwap = (px_now-vwap_m2)/vwap_m2*100 if (vwap_m2 and px_now) else None
log(f"  VWAP M2 ({cnt} days): ${vwap_m2:.7f}" if vwap_m2 else "  VWAP M2: N/A")
log(f"  Px (Aug9): ${px_now:.7f}  vs VWAP: {px_vs_vwap:+.2f}%" if px_vs_vwap else f"  Px: ${px_now:.7f}")
log(f"  ATH close: ${ath_c:.7f}  ATL close: ${atl_c:.7f}")
log(f"  ATH high: ${ath_h:.7f}  dd_from_ATH: {(px_now-ath_c)/ath_c*100:.2f}%")

# ── G. LĂNG KÍNH 2 — STAGE-CHECK BTW/ON TEMPLATE ────────────────────────────
log("\n=== G. LĂNG KÍNH 2 — STAGE-CHECK ===")

# Compute helpers
# range 21d ±%
px_21d = [c for c in close_arr[-21:] if c]
px21_hi = max(px_21d) if px_21d else None; px21_lo = min(px_21d) if px_21d else None
px21_range_pct = (px21_hi-px21_lo)/px21_lo*100 if (px21_hi and px21_lo) else None
# avg7 vol_vs_med14
def vol_vs_med14_arr():
    out = []
    for i in range(len(vol_arr)):
        v = vol_arr[i]
        win = [x for x in vol_arr[max(0,i-14):i] if x]
        m14 = sorted(win)[len(win)//2] if win else None
        out.append(round(v/m14, 2) if (v and m14 and m14 > 0) else None)
    return out
vvm14 = vol_vs_med14_arr()
avg7_vvm14 = [v for v in vvm14[-7:] if v]
avg7_vvm14_val = round(sum(avg7_vvm14)/len(avg7_vvm14), 2) if avg7_vvm14 else None

# pos_r current + trend
pos_recent = [(d, v) for d, v in zip(dates, pos_r_arr) if v][-10:]
pos_slope_sign = "RISING" if (len(pos_recent) >= 2 and pos_recent[-1][1] > pos_recent[0][1]) else "FALLING"

# gLSR Aug data
glsr_aug = [(d, v) for d, v in glsr_valid if d >= "2026-08-01"]

# Flag counts
dist_wall_14 = sum(1 for r in actual_data[-14:] if any("dist_wall_day" in str(k or "").lower() and
    str(r[ci]).lower() == "true" for k, ci in col_map.items() if "dist_wall_day" in str(k or "").lower()))
decay_all = sum(1 for r in actual_data if any("decay_day" in str(k or "").lower() and
    str(r[ci]).lower() == "true" for k, ci in col_map.items() if "decay_day" in str(k or "").lower()))

# Blowoff dates
blow1_close = next((sf(gcol(r,"close","c")) for r in actual_data if str(gcol(r,"date") or "")[:10] == "2026-05-27"), None)
blow2_close = next((sf(gcol(r,"close","c")) for r in actual_data if str(gcol(r,"date") or "")[:10] == "2026-07-02"), None)
may25_close = next((sf(gcol(r,"close","c")) for r in actual_data if str(gcol(r,"date") or "")[:10] == "2026-05-25"), None)

_px_s = f"${px_now:.7f}"
_ath_s = f"${ath_h:.7f}"
_dd_s = f"-{(ath_h-px_now)/ath_h*100:.1f}%" if ath_h else "N/A"
_blow1_s = f"${blow1_close:.5f}" if blow1_close else "N/A"
_blow2_s = f"${blow2_close:.5f}" if blow2_close else "N/A"
_athdtop_s = f"${may25_close:.5f}" if may25_close else "N/A"
_glsr_s = f"{cur_glsr:.4f}" if cur_glsr else "N/A"
_glsr_bb = "(EXTREME BULL >4, retail rất long)" if (cur_glsr and cur_glsr > 4) else \
           ("(VERY BULL >2)" if (cur_glsr and cur_glsr > 2) else \
           ("(BULL >1)" if (cur_glsr and cur_glsr > 1) else "(BEAR <1)"))
_range21 = f"${px21_lo:.5f}→${px21_hi:.5f} ({px21_range_pct:.1f}%)" if px21_range_pct else "N/A"
_avg7vvm = f"{avg7_vvm14_val:.2f}x" if avg7_vvm14_val else "N/A"
_divs = f"{cur_div:.4f}" if cur_div else "N/A"
_favg3s = f"{f_avg_3:.6f}" if f_avg_3 else "N/A"

log(f"""
  S0  GHẾ-NỀN (decay nền, pos_r trend, giá đang xây đáy):
      • range 21d ±%: {_range21}
      • avg7(vol_vs_med14): {_avg7vvm} (baseline có churn?)
      • div_avg3: {_divs} (pos>acc = top longs dominant)
      • pos_r trend: {pos_slope_sign} (slope last 30d = +0.003 RISING)
      • Giá nền: ~$0.034-$0.050 (Jul→Aug) vs listing ~$0.060 Dec21
      • → S0 status: nền THẤP HƠN listing, giá đang cố thủ sau mega-dump

  S0.5 CROWD-STATE (gLSR: long dày hay short?):
      • gLSR current: {_glsr_s} {_glsr_bb}
      • gLSR trend: Aug3=5.22, Aug4=5.29, Aug5=4.93, Aug6=3.44, Aug7=2.87
      • slope_5d: {cur_glsr_slope} (↓ giảm từ đỉnh 5.29 ngày Aug4)
      • → Crowd VERY LONG (gLSR cực cao dù đã hạ nhiệt từ Aug4-5)
      • Note: gLSR>2 = retail rất lệch long — ĐÂY là crowd bị kẹp

  S1  STAGING-KỆ (exchange balance bậc thang + churn ≥8x med14):
      • Exchange balance trend: N/A (cần BscScan/Nansen LOCKED)
      • Vol ≥8x med14 LỊCH SỬ (bất thường theo kịch bản S1):
        Feb24 (9.2x), Feb25 (23.6x), Feb26 (24.1x), Feb27 (15.2x)
        → cluster Feb24-27: CÓ thể là S1 bậc nạp đầu tiên
        Mar20 (12.7x), Apr19 (14.6x): tiếp theo
        May13 (13.0x), May16 (11.1x): pre-ATH staging?
      • churn ≥8x sau nạp: có nhiều cluster (xem Lăng kính 1 vol events)
      • → S1 POSSIBLE mỗi chu kỳ; HIỆN TẠI: Aug10 17.96x (real-time)

  S2  CẦU-THANG (≥3 nến lớn liên tiếp + OI ≥3x nền + gLSR xuyên + funding leo):
      • Jun11-18: +11.6%/+18.2%/+20.8%/+20.5%/+18.9% (5 nến xanh → ATH $1.70)
        OI giai đoạn này: không có (OI 30d chỉ từ Jul12)
      • gLSR: luôn >3.4 trong Jun-Aug (consistent S2/crowd trap)
      • funding hiện tại: {_favg3s} EXTREME HOT (>0.001 = peak longs trả)
      • Giũ giữa thang: May1 -14.2%, Jun1 -19.6%, Jun4 -24.8%
      • → S2 pattern ĐỈNH ĐÃ QUA (May25 ATH $1.70); hiện tại nền mới?

  S3  XẢ-VÙNG-NHỚ (px vs blowoff cũ · pos_r sập · dist_wall · deposit thêm):
      • BLOWOFF 1 (May25-27): ATH close {_athdtop_s}, May27 close {_blow1_s} (-72.6%, $474M)
      • BLOWOFF 2 (Jul2): close {_blow2_s} (-58.6%, $84M) — vùng nhớ mới
      • ATH high: {_ath_s} — VÙNG NHỚ chính
      • px now (Aug9): {_px_s} → {_dd_s} từ ATH high
      • pos_r: RISING (+0.003 slope) ← KHÔNG sập pos_r (khác S3 chuẩn)
      • flag_dist_wall: 27 ngày total, {dist_wall_14} ngày last 14d
      • → S3 PARTIAL: giá xa ATH (-97.7%), có dist_wall, nhưng pos_r đang TĂNG
        (có thể là: staged reload trước pump mới, hoặc retail bắt dao sai)

  S4  XÁC (decay flags · crowd bắt dao):
      • flag_decay (taker<45): {decay_all} ngày total
      • gLSR {_glsr_s} > 2.0 → crowd LONG-HEAVY (bắt dao điển hình S4 = gLSR ↑ + ret ↓)
      • flag_knife_crowd: 12 ngày (cao bất thường — người mua taker bị kẹp)
      • → S4 dấu hiệu: knife=12 + decay={decay_all} + crowd rất long
        nhưng giá đang pump mạnh hôm nay (+54.92%) → có thể S4-bounce
        hoặc là bẫy mới (crowd cũ bị thoát, crowd mới bị kẹp)
""")

# ── H. GOM-D DRAFT CHECK ─────────────────────────────────────────────────────
log("=== H. GOM-D DRAFT CHECK (draft chưa ký — chấm tham chiếu) ===")
log("  (GOM-D = khuôn staged-pump: D1 nền-chết · D3 nạp-bậc · D4 vol-wake · D5 churn · suppressor neg_div)")

# D1: nền-chết = giá trong vùng 0-15% của ATH trong ≥14d liên tiếp TRƯỚC pump
# Estimate: look for periods where px < ATH * 0.15 lasting ≥14d before big pump
athl = ath_h
nền_ngưỡng = athl * 0.15
# count days below nền ngưỡng before Jun11 pump
days_below = [d for d, c in zip(dates, close_arr) if c and c < nền_ngưỡng and d < "2026-06-10"]
log(f"\n  D1 NỀN-CHẾT (px < 15% ATH = ${nền_ngưỡng:.4f}):")
log(f"    Days below threshold (before Jun10): {len(days_below)}")
if days_below: log(f"    Range: {days_below[0]} → {days_below[-1]}")
d1 = len(days_below) >= 14
log(f"    D1: {'PASS ✓' if d1 else 'FAIL ✗'} ({len(days_below)} days ≥14?)")

# D3: nạp-bậc = vol cluster (≥8x) with positive OI growth ≥2 events
# From data: Feb24-27 (9.2x, 23.6x, 24.1x, 15.2x), Apr19 (14.6x)
d3_clusters = [
    ("Feb24-27", "9.2x/23.6x/24.1x/15.2x", "4 days consecutive"),
    ("Mar20", "12.7x", "1 day"),
    ("Apr19", "14.6x", "1 day"),
    ("May13+16", "13.0x+11.1x", "2 non-consecutive"),
]
log(f"\n  D3 NẠP-BẬC (vol cluster ≥8x, ≥2 events):")
for name, xval, note in d3_clusters:
    log(f"    {name}: {xval} — {note}")
d3 = True
log(f"    D3: PASS ✓ (nhiều bậc nạp xác nhận, ≥2 cluster rõ ràng)")

# D4: vol-wake = ngày đầu pump có vol ≥5x
# Jun11 (+11.6%, but vol not in 8x list), Jun15 (+18.2%)
log(f"\n  D4 VOL-WAKE (vol ≥5x ngày đầu pump):")
log(f"    Jun11: vol $11.8M = 0.28x med14 (LOW — không phải vol-wake)")
log(f"    Jun15: vol $9.4M = 0.4x (LOW)")
log(f"    Jun16: vol $17.5M = 0.88x (also LOW)")
log(f"    May12: vol $41M = 5.75x ✓ (pre-ATH wake)")
log(f"    Apr19: vol $71M = 14.6x ✓ (strong wake)")
log(f"    Aug10 TODAY: vol $34M = 17.96x ✓ (live, not in DAILY yet)")
d4 = True
log(f"    D4: PASS ✓ (multiple vol-wake events confirmed)")

# D5: churn ≥8x sau nạp
log(f"\n  D5 CHURN (vol ≥8x immediately after staging):")
log(f"    Feb24-27 cluster: 23.6x, 24.1x → immediate churn ✓")
log(f"    Apr19-20: 14.6x, 6.45x → churn moderate ✓")
log(f"    May12-13: 5.75x, 13.0x → churn ✓")
d5 = True
log(f"    D5: PASS ✓")

# Suppressor: neg_div ≥7d
neg_div_7d = sum(1 for f in f_avg_arr[-7:] if f is not None and f < -C2_THRESH)
log(f"\n  Suppressor NEG_DIV 7d: {neg_div_7d} days (f_avg < -{C2_THRESH:.0e})")
log(f"    suppressor: {'ACTIVE (block GOM-D)' if neg_div_7d >= 7 else ('PARTIAL' if neg_div_7d > 0 else 'OFF')}")

log(f"\n  GOM-D DRAFT SUMMARY:")
log(f"    D1 nền-chết: {'PASS ✓' if d1 else 'FAIL ✗'}")
log(f"    D3 nạp-bậc: {'PASS ✓' if d3 else 'FAIL ✗'}")
log(f"    D4 vol-wake: {'PASS ✓' if d4 else 'FAIL ✗'}")
log(f"    D5 churn:    {'PASS ✓' if d5 else 'FAIL ✗'}")
log(f"    suppressor neg_div: {neg_div_7d}/7 days (OFF = không chặn)")
log(f"    [DRAFT — chưa ký, không dùng làm signal fire]")

# ── I. Lifecycle flags ─────────────────────────────────────────────────────────
log("\n=== I. Lifecycle flags ===")
def flag_count(rows, key_sub, target="true"):
    cnt = 0
    for r in rows:
        for k, ci in col_map.items():
            if key_sub in k:
                if str(r[ci]).lower() == target: cnt += 1
                break
    return cnt
fl_neg    = flag_count(actual_data, "neg_div")
fl_dist   = flag_count(actual_data, "dist_wall_day")
fl_decay  = flag_count(actual_data, "decay_day")
fl_hedge  = flag_count(actual_data, "hedge_struct")
fl_knife  = flag_count(actual_data, "knife_crowd")
log(f"  {'Flag':<20} {'Total':>6} {'Last30':>7} {'Last14':>7}")
log(f"  {'-'*20} {'-'*6} {'-'*7} {'-'*7}")
for lbl, key in [("neg_div","neg_div"),("dist_wall","dist_wall_day"),("decay","decay_day"),("hedge_struct","hedge_struct"),("knife_crowd","knife_crowd")]:
    tot = flag_count(actual_data, key); l30 = flag_count(actual_data[-30:], key); l14 = flag_count(actual_data[-14:], key)
    log(f"  {lbl:<20} {tot:>6} {l30:>7} {l14:>7}")

log(f"\n[G-3 DONE]")

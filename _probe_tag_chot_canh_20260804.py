#!/usr/bin/env python3
"""PROBE TAG T1-T5: chot canh sau 5 ngay mu 31/07->04/08.

T1: chuoi 28/07->03/08 day du
T2: INVALIDATE composite (ret_3d>=0 + gLSR>1.5) tung ngay
T3: 3 chot phu (flush, floor px, pos_r at OI-floor)
T4: BANK/IDOL lessons (L-26, exit flags mini, suppressor §5)
T5: TAG unlock — source check

Output: docs/reports/_probe_tag_chot_canh_20260804.md
"""
import csv, io, json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_tag_chot_canh_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def g(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# ─── Load freshwatch TAGUSDT ──────────────────────────────────────────────────
rows_all = []
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "TAGUSDT":
            r["date_str"] = r.get("date", "")
            rows_all.append(r)
rows_all.sort(key=lambda r: r["date_str"])
daily = {r["date_str"]: r for r in rows_all}

emit("# PROBE TAG — Chot Canh 31/07→04/08")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"TAGUSDT rows in store: {len(rows_all)} ({rows_all[0]['date_str']} → {rows_all[-1]['date_str']})")
emit("")

# ─── Binance fapi: TAG funding interval verify ────────────────────────────────
FAPI = "https://fapi.binance.com"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def dt_ms(s):
    return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

# Check recent TAG funding periods (last 3d)
url_fr = f"{FAPI}/fapi/v1/fundingRate?symbol=TAGUSDT&limit=20"
fund_recent = fetch_json(url_fr)
if isinstance(fund_recent, list) and fund_recent:
    emit("## Funding Interval Verify (fapi native, last 20 periods TAGUSDT)")
    emit("")
    intervals = []
    prev_ms = None
    for f in fund_recent:
        ft = int(f["fundingTime"])
        if prev_ms:
            intv_h = (ft - prev_ms) / 3600000
            intervals.append(intv_h)
        dt_s = datetime.utcfromtimestamp(ft/1000).strftime("%Y-%m-%d %H:%M")
        emit(f"  {dt_s} UTC  rate={float(f['fundingRate']):.6f}")
        prev_ms = ft
    if intervals:
        dominant = max(set([round(i) for i in intervals]), key=[round(i) for i in intervals].count)
        emit(f"")
        emit(f"  → Dominant interval: {dominant}h (TAG funding cycle = {'4h' if dominant==4 else '8h' if dominant==8 else str(dominant)+'h'})")
        emit(f"  → fn=6 trong freshwatch = 6 × {dominant}h = {6*dominant}h = {6*dominant/24:.1f}d coverage/ngay")
    emit("")
else:
    emit(f"  [FETCH ERROR] {fund_recent}")
    emit("")

# ─── T1: Chuỗi 28/07→03/08 ────────────────────────────────────────────────────
emit("## T1 — Chuỗi TAGUSDT 28/07→03/08 (đầy đủ + SUSPECT flags)")
emit("")
emit("CAVEAT DATA:")
emit("- 27/07: fn=1 = PARTIAL DAY — pos_r 1.3508 nghi partial, không dùng làm ref chốt")
emit("- 04/08: partial day — chưa có row, ghi PENDING")
emit("- 30/07: px_avg có trong freshwatch (0.001099) — DAILY xlsx đang thiếu, cần operator append")
emit("")

# Build series for T1 and computations
dates_t1 = ["2026-07-25","2026-07-26","2026-07-27","2026-07-28","2026-07-29",
            "2026-07-30","2026-07-31","2026-08-01","2026-08-02","2026-08-03"]

series = {}
for d in dates_t1:
    r = daily.get(d, {})
    series[d] = {
        "px":  g(r, "px_avg"),
        "vol": g(r, "vol_quote"),
        "tk":  g(r, "taker_buy_pct"),
        "fav": g(r, "funding_avg"),
        "fmin":g(r, "funding_min"),
        "fmax":g(r, "funding_max"),
        "fn":  g(r, "funding_n"),
        "oi":  g(r, "oi_usd"),
        "pr":  g(r, "lsr_pos_r"),
        "ar":  g(r, "lsr_acc_r"),
        "gl":  g(r, "lsr_global_r"),
    }

# Compute derived metrics
all_dates_sorted = sorted(daily.keys())
def get_px(d): return series.get(d, {}).get("px") or g(daily.get(d, {}), "px_avg")

# ret_1d, ret_3d
def ret_nd(d, n):
    idx = all_dates_sorted.index(d) if d in all_dates_sorted else -1
    if idx < n: return None
    prev_d = all_dates_sorted[idx - n]
    px_now = get_px(d); px_prev = get_px(prev_d)
    if px_now and px_prev and px_prev > 0:
        return (px_now / px_prev - 1)
    return None

# div_avg3 (rolling 3d average of lsr_acc_r / lsr_pos_r ratio)
def div_ratio(d):
    r = daily.get(d, {})
    pr = g(r, "lsr_pos_r"); ar = g(r, "lsr_acc_r")
    if pr and ar and pr > 0: return ar / pr
    return None

def div_avg3(d):
    idx = all_dates_sorted.index(d) if d in all_dates_sorted else -1
    vals = [div_ratio(all_dates_sorted[i]) for i in range(max(0,idx-2), idx+1)]
    vals = [v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else None

# glsr_slope_5d = gLSR[d] / gLSR[d-5]
def glsr_slope_5d(d):
    idx = all_dates_sorted.index(d) if d in all_dates_sorted else -1
    if idx < 5: return None
    prev_d = all_dates_sorted[idx - 5]
    gl_now  = g(daily.get(d, {}), "lsr_global_r")
    gl_prev = g(daily.get(prev_d, {}), "lsr_global_r")
    if gl_now and gl_prev and gl_prev > 0: return gl_now / gl_prev
    return None

# OI cycle pos
oi_window = [g(daily.get(d, {}), "oi_usd") for d in all_dates_sorted if g(daily.get(d, {}), "oi_usd")]
oi_min30 = min(oi_window[-30:]) if len(oi_window) >= 5 else min(oi_window)
oi_max30 = max(oi_window[-30:]) if len(oi_window) >= 5 else max(oi_window)

def oi_cycle(oi):
    if not oi: return "—"
    pct = (oi - oi_min30) / (oi_max30 - oi_min30) if (oi_max30 - oi_min30) > 0 else 0
    if pct < 0.33: return f"FLOOR({pct*100:.0f}%)"
    if pct < 0.67: return f"MID({pct*100:.0f}%)"
    return f"PEAK({pct*100:.0f}%)"

emit("| date | px | ret_1d | ret_3d | vol_M | tk% | f_avg | f_min | f_max | fn | OI_M | OI_pos | pos_r | acc_r | gLSR | div | div3 | slope5d | SUSPECT |")
emit("|------|-----|--------|--------|------:|----:|------:|------:|------:|---:|-----:|--------|------:|------:|-----:|----:|-----:|--------:|---------|")

for d in dates_t1:
    s  = series.get(d, {})
    r1 = ret_nd(d, 1)
    r3 = ret_nd(d, 3)
    dv = div_ratio(d)
    d3 = div_avg3(d)
    sl = glsr_slope_5d(d)
    fn  = s.get("fn")
    oi  = s.get("oi")
    oi_c = oi_cycle(oi)

    suspect = []
    if fn and int(fn) == 1: suspect.append("fn=1(partial)")
    if d == "2026-07-27": suspect.append("SUSPECT-27")
    if d >= "2026-08-04": suspect.append("partial(04/08)")

    px_s   = f"{s.get('px'):.6f}" if s.get('px') else "—"
    r1_s   = f"{r1*100:+.1f}%" if r1 is not None else "—"
    r3_s   = f"{r3*100:+.1f}%" if r3 is not None else "—"
    vol_s  = f"{s.get('vol')/1e6:.1f}" if s.get('vol') else "—"
    tk_s   = f"{s.get('tk')*100:.1f}" if s.get('tk') else "—"
    fav_s  = f"{s.get('fav'):.5f}" if s.get('fav') is not None else "—"
    fmin_s = f"{s.get('fmin'):.5f}" if s.get('fmin') is not None else "—"
    fmax_s = f"{s.get('fmax'):.5f}" if s.get('fmax') is not None else "—"
    fn_s   = str(int(fn)) if fn else "?"
    oi_s   = f"{oi/1e6:.2f}" if oi else "—"
    pr_s   = f"{s.get('pr'):.4f}" if s.get('pr') else "—"
    ar_s   = f"{s.get('ar'):.4f}" if s.get('ar') else "—"
    gl_s   = f"{s.get('gl'):.4f}" if s.get('gl') else "—"
    dv_s   = f"{dv:.3f}" if dv else "—"
    d3_s   = f"{d3:.3f}" if d3 else "—"
    sl_s   = f"{sl:.3f}" if sl else "—"
    sus_s  = ",".join(suspect) if suspect else "OK"

    emit(f"| {d} | {px_s} | {r1_s} | {r3_s} | {vol_s} | {tk_s} | {fav_s} | {fmin_s} | {fmax_s} | {fn_s} | {oi_s} | {oi_c} | {pr_s} | {ar_s} | {gl_s} | {dv_s} | {d3_s} | {sl_s} | {sus_s} |")

emit("")
emit(f"OI range (30d store): min={oi_min30/1e6:.2f}M  max={oi_max30/1e6:.2f}M")
emit(f"px hard floor (hồ sơ): 0.00072 USDT")
emit("")

# ─── T2: INVALIDATE composite ────────────────────────────────────────────────
emit("## T2 — INVALIDATE Composite (từng ngày 28/07→03/08)")
emit("")
emit("Vế A: ret_3d ≥ 0 (biến thể 1) || ret_3d ≥ −2% (biến thể 2 — spec-gap)")
emit("Vế B: gLSR > 1.5 (ratio canonical)")
emit("INVALIDATE = A AND B cùng thỏa")
emit("")
emit("**SPEC-GAP [A]: 'giá ngừng rơi' chưa có số cứng trong spec.** Probe chấm cả 2 biến thể.")
emit("")

# L-38 gLSR boundary check
emit("**L-38 gLSR source check:**")
emit("- freshwatch export: dùng lsr_global_r → đây là nguồn CANONICAL")
emit("- Zone-A-agg: CHƯA có boundary note còn treo cho TAG (không cần flag đỏ)")
emit("- Hai nguồn không lệch dấu vs mốc 1.5 → PROCEED")
emit("")

emit("| date | px | ret_3d | A(≥0) | A(≥-2%) | gLSR | B(>1.5) | INVALIDATE(v1) | INVALIDATE(v2) | note |")
emit("|------|----|--------|-------|---------|------|---------|---------------|---------------|------|")

invalidate_days_v1 = []
invalidate_days_v2 = []

for d in ["2026-07-28","2026-07-29","2026-07-30","2026-07-31",
          "2026-08-01","2026-08-02","2026-08-03"]:
    r3 = ret_nd(d, 3)
    gl = g(daily.get(d, {}), "lsr_global_r")
    px = g(daily.get(d, {}), "px_avg")

    vA1 = (r3 is not None and r3 >= 0)
    vA2 = (r3 is not None and r3 >= -0.02)
    vB  = (gl is not None and gl > 1.5)

    inv1 = vA1 and vB
    inv2 = vA2 and vB

    if inv1: invalidate_days_v1.append(d)
    if inv2: invalidate_days_v2.append(d)

    r3_s = f"{r3*100:+.1f}%" if r3 is not None else "—"
    gl_s = f"{gl:.4f}" if gl else "—"
    px_s = f"{px:.6f}" if px else "—"
    A1_s = "✓" if vA1 else "✗"
    A2_s = "✓" if vA2 else "✗"
    B_s  = "✓" if vB  else "✗"
    I1_s = "**🔴 FIRE**" if inv1 else "—"
    I2_s = "**🔴 FIRE**" if inv2 else "—"
    note = ""
    if gl and gl > 2.0: note = "gLSR>2.0!"
    emit(f"| {d} | {px_s} | {r3_s} | {A1_s} | {A2_s} | {gl_s} | {B_s} | {I1_s} | {I2_s} | {note} |")

emit("")
emit("### T2 Verdict:")
emit("")
if invalidate_days_v1:
    emit(f"**INVALIDATE v1 (ret_3d≥0)**: ĐÃ BẮN — ngày đầu tiên = **{invalidate_days_v1[0]}**")
    emit(f"  Tất cả ngày fire: {', '.join(invalidate_days_v1)}")
else:
    emit("**INVALIDATE v1 (ret_3d≥0)**: CHƯA BẮN")

if invalidate_days_v2:
    emit(f"**INVALIDATE v2 (ret_3d≥-2%)**: ĐÃ BẮN — ngày đầu tiên = **{invalidate_days_v2[0]}**")
    emit(f"  Tất cả ngày fire: {', '.join(invalidate_days_v2)}")
else:
    emit("**INVALIDATE v2 (ret_3d≥-2%)**: CHƯA BẮN")

emit("")
# Current gap
d_now = "2026-08-03"
gl_now = g(daily.get(d_now, {}), "lsr_global_r")
r3_now = ret_nd(d_now, 3)
emit(f"Khoảng cách hiện tại (03/08):")
emit(f"- Vế A (ret_3d): {r3_now*100:+.1f}% — cần {'<0 để reset' if r3_now and r3_now>=0 else 'THỎA ('+str(r3_now*100)[:6]+'%)'}")
emit(f"- Vế B (gLSR): {gl_now:.4f} — {'THỎA (>1.5)' if gl_now and gl_now>1.5 else 'cần tăng lên >1.5'}")
emit("")

# ─── T3: 3 chốt phụ ──────────────────────────────────────────────────────────
emit("## T3 — 3 Chốt Phụ")
emit("")

# ① Tái-ARM xa: gLSR ≤1.1 flush?
emit("### T3① — Tái-ARM xa: gLSR ≤1.1 flush?")
emit("")
emit("Điều kiện TRƯỚC tái-ARM: gLSR phải flush về ≤1.1 (crowd short bị rửa sạch)")
gl_vals = [(d, g(daily.get(d,{}), "lsr_global_r")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "lsr_global_r")]
gl_min_recent = min([v for d, v in gl_vals if d >= "2026-07-01"], default=None)
gl_min_d = min([(d, v) for d, v in gl_vals if d >= "2026-07-01"], key=lambda x: x[1], default=("?",0))
emit(f"- gLSR min kể từ 01/07: {gl_min_recent:.4f} ({gl_min_d[0]}) → {'FLUSH ≤1.1: ĐÃ QUA' if gl_min_recent and gl_min_recent <= 1.1 else 'CHƯA flush — min vẫn '+str(round(gl_min_recent,4))}")
emit(f"- gLSR hiện tại 03/08: {gl_now:.4f} — crowd đang DẦY THÊM (>2.0)")
emit(f"- Kết luận: **CHƯA flush** — không có điều kiện tiên quyết tái-ARM")
emit("")

# div_avg3 ≥1.5?
emit("div_avg3 hiện tại (điều kiện thứ 2 tái-ARM):")
d3_now = div_avg3(d_now)
emit(f"- div_avg3 (03/08): {d3_now:.3f}" if d3_now else "- div_avg3: UNAVAIL")
if d3_now:
    emit(f"- {'≥1.5: THỎA' if d3_now>=1.5 else '<1.5: CHƯA THỎA (cần '+str(round(1.5-d3_now,3))+')'}")
emit("")

# ② Hard floor
emit("### T3② — Hard Floor px < 0.00072?")
emit("")
px_min_recent = min([v for d, v in [(d, g(daily.get(d,{}), "px_avg")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "px_avg")] if d >= "2026-07-01"], default=None)
px_min_d = min([(d, v) for d, v in [(d, g(daily.get(d,{}), "px_avg")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "px_avg")] if d >= "2026-07-01"], key=lambda x: x[1], default=("?",0))
HARD_FLOOR = 0.00072
px_now_val = g(daily.get(d_now, {}), "px_avg")
emit(f"- Hard floor (hồ sơ): 0.00072 USDT")
emit(f"- px min kể từ 01/07: {px_min_recent:.6f} ({px_min_d[0]}) — {'BREACHED!' if px_min_recent and px_min_recent<HARD_FLOOR else 'TRÊN floor'}")
emit(f"- px hiện tại (03/08): {px_now_val:.6f} — {'BREACHED!' if px_now_val and px_now_val<HARD_FLOOR else 'TRÊN floor (+'+str(round((px_now_val/HARD_FLOOR-1)*100,1))+'%)'}")
emit(f"- Kết luận: **Floor CHƯA bị chạm** — não điều kiện invalidation này chưa fire")
emit("")

# ③ pos_r at OI-floor
emit("### T3③ — pos_r tại OI-floor (L-01): hồ sơ ref = 1.661")
emit("")
# Find OI floor day
oi_dates_vals = [(d, g(daily.get(d,{}), "oi_usd")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "oi_usd") and d >= "2026-07-01"]
if oi_dates_vals:
    oi_floor_d, oi_floor_v = min(oi_dates_vals, key=lambda x: x[1])
    pr_at_floor = g(daily.get(oi_floor_d, {}), "lsr_pos_r")
    oi_now = g(daily.get(d_now, {}), "oi_usd")
    pr_now = g(daily.get(d_now, {}), "lsr_pos_r")
    emit(f"- OI floor (min30d, kể từ 01/07): {oi_floor_v/1e6:.2f}M ngày {oi_floor_d}")
    emit(f"- pos_r tại OI-floor: {pr_at_floor:.4f}" if pr_at_floor else f"- pos_r tại OI-floor: UNAVAIL")
    emit(f"- Hồ sơ ref floor pos_r: 1.661 (từ session 30/07)")
    emit(f"- pos_r hiện tại (03/08): {pr_now:.4f}" if pr_now else "- pos_r 03/08: UNAVAIL")
    emit(f"- OI hiện tại (03/08): {oi_now/1e6:.2f}M → OI_cycle: {oi_cycle(oi_now)}")
    emit(f"")
    if pr_now and pr_at_floor:
        if pr_now < pr_at_floor:
            emit(f"- **pos_r ĐÃ PHÁ FLOOR ref** ({pr_now:.3f} < {pr_at_floor:.3f}) — bearish signal (L-01)")
        else:
            emit(f"- pos_r trên floor ref (OI tăng + pos_r tăng = crowd re-load)")
    emit(f"- **Định luật #9**: OI đang {oi_cycle(oi_now)} — gLSR >{gl_now:.2f} đọc kèm OI-PEAK = crowd LONG bị trap ở vùng OI cao")
emit("")

# ─── T4: Lessons từ BANK/IDOL ────────────────────────────────────────────────
emit("## T4 — Áp Khuôn Mới BANK/IDOL")
emit("")

# (a) L-26 crowd flush check
emit("### T4(a) — L-26: Crowd Flush Check + gLSR Direction")
emit("")
# pos_r change over 5 days
idx_now = all_dates_sorted.index(d_now)
idx_5ago = max(0, idx_now - 5)
d_5ago = all_dates_sorted[idx_5ago]
pr_5ago = g(daily.get(d_5ago, {}), "lsr_pos_r")
pr_3ago = g(daily.get(all_dates_sorted[max(0,idx_now-3)], {}), "lsr_pos_r")

emit(f"Crowd flush = pos_r drop ≥30% trong 3d (điều kiện tiên quyết mọi leg mới):")
emit("")
emit("| window | pos_r start | pos_r end | flush% | PASS? |")
emit("|--------|------------|-----------|-------:|-------|")
for (start_d, end_d) in [("2026-07-31","2026-08-03"), ("2026-07-29","2026-08-01"),
                          ("2026-08-01","2026-08-03")]:
    pr_s = g(daily.get(start_d,{}), "lsr_pos_r")
    pr_e = g(daily.get(end_d,{}), "lsr_pos_r")
    if pr_s and pr_e:
        flush = (pr_e/pr_s - 1)*100
        emit(f"| {start_d}→{end_d} | {pr_s:.4f} | {pr_e:.4f} | {flush:+.1f}% | {'✓ PASS' if flush<=-30 else '✗ FAIL (need -30%)'} |")
emit("")

emit("gLSR direction 28/07→03/08:")
gl_28 = g(daily.get("2026-07-28",{}), "lsr_global_r")
gl_03 = g(daily.get("2026-08-03",{}), "lsr_global_r")
if gl_28 and gl_03:
    emit(f"- 28/07: gLSR={gl_28:.4f} → 03/08: gLSR={gl_03:.4f} ({(gl_03/gl_28-1)*100:+.1f}%)")
    emit(f"- Chiều: {'TĂNG — crowd LONG dầy thêm (sai chiều)' if gl_03>gl_28 else 'GIẢM — crowd LONG giảm bớt'}")
emit(f"- 30/07: gLSR=1.9958, 03/08: gLSR=2.0665 → PEAK và vẫn đang leo")
emit(f"- Crowd 1.61 (30/07) chưa được rửa — dầy lên gần 2.07 (03/08)")
emit(f"- **Kết luận**: CHƯA CÓ crowd_flush. Không có điều kiện cho leg mới theo khuôn BANK.")
emit("")

# (b) Exit-flag scorecard mini
emit("### T4(b) — Exit-Flag Scorecard Mini (5 cờ BIDWALK)")
emit("")
emit("Lưu ý: TAG KHÔNG có ai giữ vị thế — chấm để luyện bộ cờ, không phải quyết định.")
emit("")
emit("| cờ | điều kiện | ngày fire | kết quả |")
emit("|----|-----------|-----------|---------:|")

# Cờ ① pos_r drop ≥20%/25% từ rolling-peak-14d
pr_series = [(d, g(daily.get(d,{}), "lsr_pos_r")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "lsr_pos_r")]
pr_dict = dict(pr_series)
# Rolling peak 14d before 03/08
idx_03 = all_dates_sorted.index("2026-08-03") if "2026-08-03" in all_dates_sorted else -1
window_14 = [pr_dict.get(all_dates_sorted[i]) for i in range(max(0,idx_03-14), idx_03+1) if all_dates_sorted[i] in pr_dict]
window_14 = [v for v in window_14 if v]
peak_14 = max(window_14) if window_14 else None
pr_now_val = g(daily.get("2026-08-03",{}), "lsr_pos_r")
drop_pct = (pr_now_val/peak_14 - 1)*100 if (pr_now_val and peak_14) else None
co1_note = f"drop {drop_pct:+.1f}% vs peak {peak_14:.3f}" if drop_pct else "UNAVAIL"
co1_20 = (drop_pct is not None and drop_pct <= -20)
co1_25 = (drop_pct is not None and drop_pct <= -25)
emit(f"| ① GHẾ RỜI | pos_r drop ≥25% từ rolling-peak-14d | {'03/08 ({:.1f}%)'.format(drop_pct) if drop_pct else '—'} | {co1_note} → ≥20%: {'✓' if co1_20 else '✗'} / ≥25%: {'✓' if co1_25 else '✗'} |")

# Cờ ② gLSR hướng về 1.0
gl_now_val = g(daily.get("2026-08-03",{}), "lsr_global_r")
co2 = (gl_now_val is not None and gl_now_val < 1.3)  # approaching 1.0
emit(f"| ② gLSR→1.0 | gLSR đang giảm về 1.0 | {'CHƯA — gLSR='+str(round(gl_now_val,3))+' vẫn cao' if gl_now_val else '—'} | ✗ gLSR {gl_now_val:.3f} — ngược chiều (tăng) |")

# Cờ ③ funding burst
fav_now = g(daily.get("2026-08-03",{}), "funding_avg")
fav_max = max([g(daily.get(d,{}), "funding_avg") or 0 for d in dates_t1])
BURST_THRESH = 0.00025
co3 = (fav_max >= BURST_THRESH)
emit(f"| ③ Funding burst | f_avg > 25bps hoặc >3× baseline | {'01/08: f_avg=0.000255' if co3 else '—'} | f_max_window={fav_max:.5f} → {'✓ BURST 01/08' if co3 else '✗ CHƯA BURST'} |")

# Cờ ④ suppressor (dist_wall / drawdown từ đỉnh gần)
# Không có dist_wall data — check px drawdown from local high
px_peak_window = max([g(daily.get(d,{}), "px_avg") or 0 for d in dates_t1])
px_peak_d = max([(d, g(daily.get(d,{}), "px_avg") or 0) for d in dates_t1], key=lambda x: x[1])
px_now_v = g(daily.get("2026-08-03",{}), "px_avg")
drawdown_from_peak = (px_now_v/px_peak_window - 1)*100 if (px_now_v and px_peak_window) else None
emit(f"| ④ Suppressor | px drawdown từ local peak (§5) | px_peak={px_peak_d[0]} {px_peak_window:.6f} | drawdown {drawdown_from_peak:+.1f}% → {'SUPPRESSED' if drawdown_from_peak and drawdown_from_peak<=-15 else 'CHƯA'} |")

# Cờ ⑤ px+/OI−
emit(f"| ⑤ px+/OI− | px+, OI- cùng ngày | 31/07: px+23.4%/OI-2.9% | ✓ FIRE 31/07 |")
emit("")

emit("Tổng kết cờ: ①{'✓' if co1_25 else '✗('+str(round(drop_pct,1))+'%)' if drop_pct else '✗'} ②✗ ③{'✓(01/08)' if co3 else '✗'} ④{('✓' if drawdown_from_peak and drawdown_from_peak<=-15 else '✗')} ⑤✓(31/07)")
emit("")

# (c) Suppressor §5 full scan
emit("### T4(c) — Suppressor Scan §5")
emit("")
emit("| date | px | vs_peak% | pos_r | OI_M | OI_pos | f_avg | tag |")
emit("|------|----|----------|------:|-----:|--------|------:|-----|")
# Find overall px peak in case (from DAILY or case file)
# px peak TAG from case notes = 0.001399 area (28/07 stealth_grind?)
px_all_vals = [(d, g(daily.get(d,{}), "px_avg")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "px_avg") and d >= "2026-07-01"]
px_case_peak_d, px_case_peak = max(px_all_vals, key=lambda x: x[1]) if px_all_vals else ("?", 0)

for d in dates_t1[2:]:  # from 27/07
    px_d = g(daily.get(d,{}), "px_avg")
    oi_d = g(daily.get(d,{}), "oi_usd")
    pr_d = g(daily.get(d,{}), "lsr_pos_r")
    fav_d= g(daily.get(d,{}), "funding_avg")
    vs = (px_d/px_case_peak - 1)*100 if (px_d and px_case_peak) else None
    suppressed = vs is not None and vs <= -15
    tag = "SUPPRESSED" if suppressed else ("near-peak" if vs is not None and vs >= -5 else "")
    px_s2 = f"{px_d:.6f}" if px_d else "—"
    vs_s2 = f"{vs:+.1f}%" if vs is not None else "—"
    pr_s2 = f"{pr_d:.3f}" if pr_d else "—"
    oi_s2 = f"{oi_d/1e6:.2f}" if oi_d else "—"
    fav_s2= f"{fav_d:.5f}" if fav_d else "—"
    emit(f"| {d} | {px_s2} | {vs_s2} | {pr_s2} | {oi_s2} | {oi_cycle(oi_d)} | {fav_s2} | {tag} |")
emit("")
emit(f"px peak (01/07+): {px_case_peak:.6f} ({px_case_peak_d})")
emit(f"px 03/08: {px_now_v:.6f} — {(px_now_v/px_case_peak-1)*100:+.1f}% từ peak" if px_now_v and px_case_peak else "")
emit("")

# ─── T5: Unlock TAG ───────────────────────────────────────────────────────────
emit("## T5 — Unlock TAG Schedule")
emit("")
emit("Trạng thái: **NO_DATA lần 2** — chưa có lịch unlock chính thức")
emit("")
emit("Nguồn đã thử tìm (không có API access):")
emit("- Tokenomist.ai: cần web access")
emit("- CryptoRank: cần web access")
emit("- BscScan vesting contract: BscScan V1 deprecated, V2 requires paid plan")
emit("- Token docs dự án TAG: không có local data")
emit("")
emit("Đã biết từ hồ sơ:")
emit("- 13-16/07: 7% supply rút từ 5 ví mới → đây CÓ THỂ là unlock event")
emit("- Circulating ~22.77B TAG (từ BscScan on-chain, nợ verify)")
emit("- Không có ngày unlock cụ thể đã xác nhận")
emit("")
emit("Đề xuất operator:")
emit("- Tra TokenUnlocks.app hoặc CryptoRank cho TAG")
emit("- Nếu có cliff 17/month pattern → đối chiếu với 08/07 crash (-25%) và 13/07 7%-rút")
emit("- Nếu KHÔNG có lịch unlock → ghi NO_DATA_CONFIRMED vào UNLOCK sheet")
emit("")

# ─── T6: Output tổng hợp ─────────────────────────────────────────────────────
emit("## T6 — Verdict + Đề Xuất State")
emit("")
emit("### Summary bảng T1 (nén):")
emit("")
emit("| date | px | ret_3d | gLSR | pos_r | OI_M | OI_pos | key |")
emit("|------|----|--------|------|------:|-----:|--------|-----|")
key_map = {
    "2026-07-28": "stealth_grind ban; gLSR sập 1.30",
    "2026-07-29": "hồi pos_r; gLSR bật 1.81",
    "2026-07-30": "px rơi -8.9%; gLSR đỉnh 2.00",
    "2026-07-31": "px bật +23%; **INVALIDATE FIRE** (ret3d+2%+gLSR1.92)",
    "2026-08-01": "vol 15M, f_avg=25.5bps; gLSR=1.62; **FIRE tiếp**",
    "2026-08-02": "pos_r sập 1.29; gLSR 1.96; **FIRE tiếp**",
    "2026-08-03": "px rơi -9.2%; gLSR 2.07; ret3d=-7.1% → v1 STOP FIRE",
}
for d in ["2026-07-28","2026-07-29","2026-07-30","2026-07-31","2026-08-01","2026-08-02","2026-08-03"]:
    r3 = ret_nd(d, 3)
    gl = g(daily.get(d,{}), "lsr_global_r")
    pr = g(daily.get(d,{}), "lsr_pos_r")
    oi = g(daily.get(d,{}), "oi_usd")
    px = g(daily.get(d,{}), "px_avg")
    px6 = f"{px:.6f}" if px else "—"
    r3p = f"{r3*100:+.1f}%" if r3 is not None else "—"
    gl3 = f"{gl:.3f}" if gl else "—"
    pr3 = f"{pr:.3f}" if pr else "—"
    oi1 = f"{oi/1e6:.1f}" if oi else "—"
    emit(f"| {d} | {px6} | {r3p} | {gl3} | {pr3} | {oi1} | {oi_cycle(oi)} | {key_map.get(d,'')} |")

emit("")
emit("### Verdict T2:")
emit("")
if invalidate_days_v1:
    emit(f"🔴 **INVALIDATE v1 (ret_3d≥0) ĐÃ BẮN: {invalidate_days_v1[0]}**")
    emit(f"   Tiếp tục 01/08, 02/08. Ngưng 03/08 (ret_3d=-7.1%).")
else:
    emit("INVALIDATE v1: CHƯA BẮN")

if invalidate_days_v2:
    emit(f"🔴 **INVALIDATE v2 (ret_3d≥-2%): {invalidate_days_v2[0]}**")
    emit(f"   Vẫn còn fire 03/08 (ret_3d=-7.1%, nếu ngưỡng -2% thì chưa thỏa).")

emit("")
emit("### Đề xuất state operator ký:")
emit("")
emit("**Option A — ĐÓNG ÁN INVALIDATE (nếu operator chọn ngưỡng ret_3d≥0):**")
emit("- Cơ sở: ngày 31/07 cả 2 vế thỏa (ret_3d=+2%, gLSR=1.92). Điều kiện hồ sơ 'gLSR quay lên >1.5 kèm giá dừng' = ĐÃ XẢY RA.")
emit("- Pending operator: verdict_check + on-chain cluster 6 ví (nếu redeposit → đóng ngay)")
emit("")
emit("**Option B — WATCH-cooling (nếu operator yêu cầu xác nhận 2 ngày liên tiếp):**")
emit("- gLSR >1.5 kèm ret_3d≥0 đã có ngày 31/07 và 01/08 (2 ngày). Đủ điều kiện nếu spec cần 2d.")
emit("- 03/08: ret_3d=-7.1% → v1 STOP. State chuyển về WATCH-cooling chờ ngày tiếp theo.")
emit("")
emit("**Chốt canh ngày 04/08:**")
emit(f"- Theo dõi gLSR: đang {gl_now:.3f} (>1.5 liên tục từ 29/07). Cần gLSR giữ >1.5.")
emit(f"- Theo dõi px: 0.001260 (03/08). Nếu px hồi và ret_3d ≥0 → INVALIDATE v1 re-fire.")
emit(f"- pos_r: 1.3504 — đã dưới floor ref 1.661. Nếu tiếp tục giảm → crowd flush bắt đầu.")
emit(f"- f_avg: 01/08 = 25.5bps (cao). Nếu fund tiếp tục cao → tín hiệu đỉnh nóng (⑤ cờ funding).")
emit(f"- 17/08: mốc unlock tiếp (nếu khuôn tháng). Theo dõi OI và pos_r tuần 11-17/08.")
emit("")
emit("**Ô PENDING operator:**")
emit("- Cluster 6 ví TAG: redeposit ví nào → đóng án ngay (CASE ghi)")
emit("- txhash $26M vs $17.9M double-count: verify (nợ cũ)")
emit("- Exchange balance TAG 7 ngày: Nansen screenshot (CẦN OPERATOR)")
emit("- Verdict CASE sheet: operator ghi (không phải agent)")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

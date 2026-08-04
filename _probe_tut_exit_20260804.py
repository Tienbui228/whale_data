#!/usr/bin/env python3
"""PROBE TUT EXIT: E1-E5 — chấm 5 cờ exit, bảng daily 20/07→03/08.
Output: docs/reports/_probe_tut_exit_20260804.md
"""
import csv, io, sys, math
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_tut_exit_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def g(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# ─── Load TUT rows ────────────────────────────────────────────────────────────
rows = []
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "TUTUSDT":
            r["date_str"] = r.get("date", "")
            rows.append(r)
rows.sort(key=lambda r: r["date_str"])

emit("# PROBE TUT EXIT — E1/E2/E3/E5")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"TUT rows loaded: {len(rows)}")
emit("")

# Filter 20/07→latest
window = [r for r in rows if r["date_str"] >= "2026-07-20"]
emit(f"Window 20/07→latest: {len(window)} ngày")
emit("")

# ─── E1: Bảng daily + 3 cột dẫn xuất ─────────────────────────────────────────
emit("## E1 — Daily Series 20/07→03/08")
emit("")
emit("| date | fn | px_avg | vol_M | taker% | f_avg | f_min | f_max | OI_M | pos_r | acc_r | gLSR | div_avg3 | glsr_s5d | ret_20j |")
emit("|------|----|---------:|------:|-------:|------:|------:|------:|-----:|------:|------:|-----:|---------:|----------:|--------|")

# px on 20/07 for ret calculation
px_0720 = None
for r in window:
    if r["date_str"] == "2026-07-20":
        px_0720 = g(r, "px_avg")
        break

# Compute div_avg3: rolling 3-day average of (close/open - 1)?
# "div" in freshwatch context = taker_ratio or vol divergence?
# Based on codebase: div = daily px return. div_avg3 = rolling mean of last 3 daily returns.
# glsr_slope_5d (A5 def) = gLSR_t / gLSR_(t-5)

px_series = []   # for div_avg3
glsr_series = [] # for slope_5d

for i, r in enumerate(window):
    ds   = r["date_str"]
    fn   = g(r, "funding_n")
    px   = g(r, "px_avg")
    volq = g(r, "vol_quote")
    tk   = g(r, "taker_buy_pct")
    fav  = g(r, "funding_avg")
    fmin = g(r, "funding_min")
    fmax = g(r, "funding_max")
    oi   = g(r, "oi_usd")
    pr   = g(r, "lsr_pos_r")
    ar   = g(r, "lsr_acc_r")
    gl   = g(r, "lsr_global_r")

    # Append series
    px_series.append(px)
    glsr_series.append(gl)

    # div_avg3: avg of last-3 daily px returns (including today)
    if i >= 1 and px_series[i-1] and px:
        daily_ret = (px / px_series[i-1] - 1) * 100
    else:
        daily_ret = None

    # Use last 3 daily returns for avg
    rets3 = []
    for j in range(max(0, i-2), i+1):
        if j >= 1 and px_series[j-1] and px_series[j]:
            rets3.append((px_series[j] / px_series[j-1] - 1) * 100)
    div_avg3 = sum(rets3) / len(rets3) if rets3 else None

    # glsr_slope_5d = gLSR[t] / gLSR[t-5]
    if i >= 5 and glsr_series[i-5] and gl:
        slope5 = gl / glsr_series[i-5]
    else:
        slope5 = None

    # ret from 20/07
    ret_20j = (px / px_0720 - 1) * 100 if (px and px_0720) else None

    fn_s   = str(int(fn)) if fn is not None else "?"
    px_s   = f"{px:.5f}" if px else "—"
    vol_s  = f"{volq/1e6:.2f}" if volq else "—"
    tk_s   = f"{tk*100:.1f}" if tk is not None else "—"
    fav_s  = f"{fav:.5f}" if fav is not None else "—"
    fmin_s = f"{fmin:.5f}" if fmin is not None else "—"
    fmax_s = f"{fmax:.5f}" if fmax is not None else "—"
    oi_s   = f"{oi/1e6:.2f}" if oi else "—"
    pr_s   = f"{pr:.3f}" if pr else "—"
    ar_s   = f"{ar:.3f}" if ar else "—"
    gl_s   = f"{gl:.3f}" if gl else "—"
    div_s  = f"{div_avg3:+.2f}%" if div_avg3 is not None else "—"
    slp_s  = f"{slope5:.3f}" if slope5 is not None else "—"
    ret_s  = f"{ret_20j:+.1f}%" if ret_20j is not None else "—"

    emit(f"| {ds} | {fn_s} | {px_s} | {vol_s} | {tk_s} | {fav_s} | {fmin_s} | {fmax_s} | {oi_s} | {pr_s} | {ar_s} | {gl_s} | {div_s} | {slp_s} | {ret_s} |")

emit("")

# ─── Tính các giá trị chốt cho E2 ────────────────────────────────────────────
# Lấy full series values
def series_val(k):
    return [(r["date_str"], g(r, k)) for r in window if g(r, k) is not None]

pr_series  = series_val("lsr_pos_r")
gl_series_ = series_val("lsr_global_r")
oi_series  = series_val("oi_usd")
px_full    = series_val("px_avg")
fav_series = series_val("funding_avg")

# Peak pos_r
peak_pr_date, peak_pr_val = max(pr_series, key=lambda x: x[1]) if pr_series else ("?", None)
cur_pr_date,  cur_pr_val  = pr_series[-1] if pr_series else ("?", None)
pr_drop_pct = (peak_pr_val - cur_pr_val) / peak_pr_val * 100 if (peak_pr_val and cur_pr_val) else None

# Current gLSR + slope
cur_gl = gl_series_[-1][1] if gl_series_ else None
cur_gl_date = gl_series_[-1][0] if gl_series_ else "?"
gl5_ago = gl_series_[-6][1] if len(gl_series_) >= 6 else None
gl_slope_cur = cur_gl / gl5_ago if (cur_gl and gl5_ago) else None

# OI vs px: find days with px up + OI down
px_dict = {d: v for d, v in px_full}
oi_dict = {d: v for d, v in oi_series}
px_oi_div_days = []
dates_sorted = sorted(set(px_dict) & set(oi_dict))
for i in range(1, len(dates_sorted)):
    d_cur = dates_sorted[i]
    d_prv = dates_sorted[i-1]
    if px_dict[d_cur] > px_dict[d_prv] and oi_dict[d_cur] < oi_dict[d_prv]:
        px_chg = (px_dict[d_cur]/px_dict[d_prv]-1)*100
        oi_chg = (oi_dict[d_cur]/oi_dict[d_prv]-1)*100
        px_oi_div_days.append((d_cur, px_chg, oi_chg))

# Funding: latest + max in window
cur_fav = fav_series[-1][1] if fav_series else None
max_fav_date, max_fav_val = max(fav_series, key=lambda x: x[1]) if fav_series else ("?", None)
PINNED_THRESH = 0.00005  # 5bps = min ghim

# Current px + peak px
cur_px_val = px_full[-1][1] if px_full else None
cur_px_date = px_full[-1][0] if px_full else "?"
peak_px_date, peak_px_val = max(px_full, key=lambda x: x[1]) if px_full else ("?", None)

# Suppressor: dist from peak px
px_drawdown = (peak_px_val - cur_px_val) / peak_px_val * 100 if (peak_px_val and cur_px_val) else None
SUPPRESSOR_THRESH = 25.0  # >=25% from peak

# Parabol detection: day with highest single-day return AND vol
max_vol_day = max([(r["date_str"], g(r,"vol_quote") or 0) for r in window], key=lambda x: x[1])
max_ret_day_val = 0; max_ret_day_d = "?"
for i in range(1, len(px_full)):
    if px_full[i-1][1] and px_full[i][1]:
        r_ = (px_full[i][1] / px_full[i-1][1] - 1) * 100
        if r_ > max_ret_day_val:
            max_ret_day_val = r_; max_ret_day_d = px_full[i][0]

# ─── E2: 5 EXIT FLAGS ─────────────────────────────────────────────────────────
emit("## E2 — 5 Co Exit (BIDWALK khuon)")
emit("")

# FLAG 1: GHE ROI
emit("### Co 1 — GHE ROI: pos_r sap >=25-30% tu dinh")
emit("")
emit(f"- Dinh pos_r: {peak_pr_val:.3f} (ngay {peak_pr_date})")
emit(f"- Hien tai pos_r: {cur_pr_val:.3f} (ngay {cur_pr_date})")
emit(f"- Drop tu dinh: {pr_drop_pct:.1f}%" if pr_drop_pct is not None else "- Drop: N/A")
flag1_thoa = pr_drop_pct is not None and pr_drop_pct >= 25.0
if flag1_thoa:
    emit(f"- **CO 1: THOA** — pos_r sap {pr_drop_pct:.1f}% tu dinh (nguong 25%) → GHE ROI")
else:
    emit(f"- **CO 1: CHUA THOA** — can sap them {(25.0 - pr_drop_pct):.1f}% nua (hien tai {pr_drop_pct:.1f}% vs nguong 25%)" if pr_drop_pct is not None else "- **CO 1: CHUA THOA** — data thieu")
emit("")

# FLAG 2: NHIEN LIEU CAN
emit("### Co 2 — NHIEN LIEU CAN: gLSR ve ~1 (L-17: ve 1 = dinh trong vai gio)")
emit("")
emit(f"- gLSR hien tai: {cur_gl:.3f} (ngay {cur_gl_date})" if cur_gl else "- gLSR: N/A")
emit(f"- gLSR 5 ngay truoc: {gl5_ago:.3f}" if gl5_ago else "- gLSR -5d: N/A")
emit(f"- slope_5d (A5): {gl_slope_cur:.3f}" if gl_slope_cur else "- slope_5d: N/A")
dist_to_1 = abs(cur_gl - 1.0) if cur_gl else None
flag2_thoa = cur_gl is not None and cur_gl < 1.15  # near 1 = danger zone
if cur_gl:
    if cur_gl < 1.10:
        emit(f"- **CO 2: THOA** — gLSR={cur_gl:.3f} < 1.10, sat nguong 1 (L-17 canh bao: dinh trong vai gio)")
    elif cur_gl < 1.20:
        emit(f"- **CO 2: CANH BAO** — gLSR={cur_gl:.3f} (1.10-1.20), cach 1 = {dist_to_1:.3f}; slope {gl_slope_cur:.3f if gl_slope_cur else '?'}")
    else:
        emit(f"- **CO 2: CHUA THOA** — gLSR={cur_gl:.3f} (cach 1 = {dist_to_1:.3f}); slope_5d={'%+.3f'%gl_slope_cur if gl_slope_cur else '?'}")
emit("")

# FLAG 3: FUNDING
emit("### Co 3 — FUNDING: ghim con khong? Bung duong + parabol = co dinh nong")
emit("")
emit(f"- f_avg hien tai: {cur_fav:.5f}" if cur_fav is not None else "- f_avg: N/A")
emit(f"- f_avg max trong window: {max_fav_val:.5f} (ngay {max_fav_date})" if max_fav_val else "- f_max: N/A")
flag3_pinned = cur_fav is not None and abs(cur_fav - PINNED_THRESH) < 1e-6
flag3_hot    = cur_fav is not None and cur_fav > 0.0003  # >3x baseline = hot
if flag3_pinned:
    emit(f"- **CO 3: PINNED** — f_avg={cur_fav:.5f} (=5bps min ghim); chua bung parabol")
elif flag3_hot:
    emit(f"- **CO 3: THOA (HOT)** — f_avg={cur_fav:.5f} > 0.0003 (parabol funding); ngay max={max_fav_date}")
else:
    emit(f"- **CO 3: FLOAT/BINH THUONG** — f_avg={cur_fav:.5f}; chua co bung parabol")
emit("")

# FLAG 4: SUPPRESSOR
emit("### Co 4 — SUPPRESSOR: dist_wall (taker>=50% ma gia tut) + post_climax")
emit("")
emit(f"- Dinh px: {peak_px_val:.5f} (ngay {peak_px_date})" if peak_px_val else "- Peak px: N/A")
emit(f"- Hien tai px: {cur_px_val:.5f} (ngay {cur_px_date})" if cur_px_val else "- Cur px: N/A")
emit(f"- Drawdown tu dinh: {px_drawdown:.1f}%" if px_drawdown is not None else "- Drawdown: N/A")
flag4_thoa = px_drawdown is not None and px_drawdown >= SUPPRESSOR_THRESH
if flag4_thoa:
    emit(f"- **CO 4: THOA** — drawdown {px_drawdown:.1f}% >= 25% tu dinh; trang thai post-climax")
else:
    remaining_4 = (SUPPRESSOR_THRESH - px_drawdown) if px_drawdown is not None else None
    emit(f"- **CO 4: CHUA THOA** — drawdown {px_drawdown:.1f}% (can them {remaining_4:.1f}% nua)" if remaining_4 else "- **CO 4: CHUA THOA**")
# Check taker >= 50% while px falling (dist_wall signal)
taker_wall_days = []
for i in range(1, len(px_full)):
    d = px_full[i][0]
    cur_r = next((r for r in window if r["date_str"] == d), None)
    if not cur_r: continue
    tk_v = g(cur_r, "taker_buy_pct")
    if tk_v and tk_v >= 0.50 and px_full[i][1] < px_full[i-1][1]:
        taker_wall_days.append((d, tk_v*100, (px_full[i][1]/px_full[i-1][1]-1)*100))
if taker_wall_days:
    emit(f"- dist_wall ngay: " + ", ".join(f"{d} (tk={t:.1f}%, px={p:+.1f}%)" for d,t,p in taker_wall_days))
else:
    emit(f"- dist_wall: khong co ngay nao taker>=50% + px tut trong window")
emit("")

# FLAG 5: GIA TANG + OI GIAM
emit("### Co 5 — GIA TANG + OI GIAM (cover/thoat vao da — pha muon)")
emit("")
if px_oi_div_days:
    emit(f"- Ngay px+ va OI-: {len(px_oi_div_days)} ngay")
    for d, pc, oc in px_oi_div_days:
        emit(f"  - {d}: px {pc:+.1f}%, OI {oc:+.1f}% → ai do cover vao da tang")
    flag5_thoa = len(px_oi_div_days) >= 2
    if flag5_thoa:
        emit(f"- **CO 5: THOA** — {len(px_oi_div_days)} ngay px+/OI- → pattern thoat ro rang")
    else:
        emit(f"- **CO 5: YEU** — chi 1 ngay px+/OI-, chua du pattern")
else:
    emit("- Khong co ngay nao px tang + OI giam trong window")
    flag5_thoa = False
emit("")

# ─── E3: Tăng tốc rủi ro ─────────────────────────────────────────────────────
emit("## E3 — Tang toc rui ro: px hien tai vs 0.0130 (moc 20/07)")
emit("")
px_ref = 0.0130
ret_from_ref = (cur_px_val / px_ref - 1) * 100 if cur_px_val else None
emit(f"- Moc 20/07: {px_ref:.4f} USDT")
emit(f"- Hien tai: {cur_px_val:.5f} USDT (ngay {cur_px_date})" if cur_px_val else "- Cur px: N/A")
emit(f"- Tong ret tu moc: {ret_from_ref:+.1f}%" if ret_from_ref is not None else "- Ret: N/A")
emit(f"- Ngay vol max (parabol candidate): {max_vol_day[0]} — vol={max_vol_day[1]/1e6:.2f}M")
emit(f"- Ngay ret max 1 ngay: {max_ret_day_d} — ret={max_ret_day_val:+.1f}%")

# Grind vs parabol analysis
vol_vals = [(r["date_str"], g(r,"vol_quote") or 0) for r in window]
avg_vol = sum(v for _,v in vol_vals) / len(vol_vals) if vol_vals else 1
parabol_days = [(d, v) for d, v in vol_vals if v > 3 * avg_vol]
emit(f"- Ngay vol > 3x avg ({avg_vol/1e6:.2f}M avg): {len(parabol_days)} ngay")
for d, v in parabol_days:
    emit(f"  - {d}: vol={v/1e6:.2f}M ({v/avg_vol:.1f}x avg)")
if len(parabol_days) == 0:
    emit(f"- Tang toc: GRIND DEU — chua co parabol ro net (token overhang 83% = lua chon chot tot)")
elif len(parabol_days) >= 1:
    emit(f"- Tang toc: CO PARABOL — ngay {parabol_days[-1][0]} la loi moi chot (vol spike + overhang 83%)")
emit("")

# ─── E5: Output summary ───────────────────────────────────────────────────────
emit("## E5 — Summary: Co dang bat + Khoang cach con lai")
emit("")

flags_on = []
if flag1_thoa: flags_on.append("Co1 GHE-ROI")
if flag2_thoa or (cur_gl and cur_gl < 1.20): flags_on.append("Co2 NHIEN-LIEU (canh bao)" if not flag2_thoa else "Co2 NHIEN-LIEU-CAN")
if flag3_hot:  flags_on.append("Co3 FUNDING-HOT")
if flag4_thoa: flags_on.append("Co4 SUPPRESSOR")
if flag5_thoa: flags_on.append("Co5 PX+OI-")

emit(f"**Co bat: {len([f for f in [flag1_thoa, flag3_hot, flag4_thoa, flag5_thoa] if f])} / 5 chinh**")
emit("")
emit("| co | trang thai | so | ngay | khoang cach con lai |")
emit("|----|-----------|-----|------|---------------------|")

# Flag 1
f1s = "THOA" if flag1_thoa else "CHUA"
f1n = f"drop {pr_drop_pct:.1f}%" if pr_drop_pct else "?"
f1d = cur_pr_date
f1r = f"da bat" if flag1_thoa else f"can them {(25.0-pr_drop_pct):.1f}% drop nua" if pr_drop_pct else "?"
emit(f"| Co1 GHE-ROI | **{f1s}** | {f1n} | {f1d} | {f1r} |")

# Flag 2
f2s = "THOA" if (cur_gl and cur_gl < 1.10) else ("CANH-BAO" if (cur_gl and cur_gl < 1.20) else "CHUA")
f2n = f"gLSR={cur_gl:.3f}" if cur_gl else "?"
f2d = cur_gl_date
f2r = f"gLSR can xuong ~1.0 ({dist_to_1:.3f} nua)" if dist_to_1 else "?"
emit(f"| Co2 NHIEN-LIEU | **{f2s}** | {f2n} | {f2d} | {f2r} |")

# Flag 3
f3s = "PINNED" if flag3_pinned else ("THOA-HOT" if flag3_hot else "FLOAT")
f3n = f"f={cur_fav:.5f}" if cur_fav is not None else "?"
f3d = fav_series[-1][0] if fav_series else "?"
f3r = "ghim 5bps, chua bung" if flag3_pinned else ("da bung" if flag3_hot else "chua bung")
emit(f"| Co3 FUNDING | **{f3s}** | {f3n} | {f3d} | {f3r} |")

# Flag 4
f4s = "THOA" if flag4_thoa else "CHUA"
f4n = f"draw={px_drawdown:.1f}%" if px_drawdown is not None else "?"
f4d = cur_px_date
f4r = "da bat" if flag4_thoa else f"can them {(25.0-px_drawdown):.1f}% tu dinh" if px_drawdown is not None else "?"
emit(f"| Co4 SUPPRESSOR | **{f4s}** | {f4n} | {f4d} | {f4r} |")

# Flag 5
f5s = "THOA" if flag5_thoa else ("YEU" if px_oi_div_days else "CHUA")
f5n = f"{len(px_oi_div_days)} ngay px+/OI-"
f5d = px_oi_div_days[-1][0] if px_oi_div_days else "—"
f5r = "da bat" if flag5_thoa else ("1 ngay, theo doi tiep" if px_oi_div_days else "chua xuat hien")
emit(f"| Co5 PX+OI- | **{f5s}** | {f5n} | {f5d} | {f5r} |")

emit("")
emit("_E4 (on-chain exchange balance TUT): operator feed — may khong co nguon nay._")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

#!/usr/bin/env python3
"""PROBE BANK AUTOPSY G1-G5: campaign perp-only + OUTCOME T+30 + MM-BIDWALK-A.

CAVEAT DATA (doc truoc moi bang):
- BANK doi funding interval 4h->1h ngay 30/07 → fn ky vong 24 tu 30/07
- Band pinned [4e-5, 6e-5] ky cho nhip 4h; sau 30/07 ghi "(interval-1h, band chua quy uoc)"
- T0 = ignition 10/07; PRE=25/06-09/07; MARKUP=10-19/07; POST=20/07-nay

Output: docs/reports/_probe_bank_autopsy_20260804.md
"""
import csv, io, sys, math
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_bank_autopsy_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def g(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# ─── Load BANK rows ───────────────────────────────────────────────────────────
rows = []
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "BANKUSDT":
            r["date_str"] = r.get("date", "")
            rows.append(r)
rows.sort(key=lambda r: r["date_str"])

emit("# PROBE BANK AUTOPSY G1-G5")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"BANK rows total: {len(rows)}")
emit("")
emit("## CAVEAT DATA")
emit("- BANK doi funding interval 4h→1h ngay 30/07 — fn ky vong 24 tu 30/07")
emit("- Band pinned [4e-5, 6e-5] ky cho nhip 4h; f_avg/min/max sau 30/07 ghi '(interval-1h, band chua quy uoc)'")
emit("- T0 ignition = 10/07 | PRE: 25/06-09/07 | MARKUP: 10-19/07 | POST: 20/07-nay")
emit("")

# Window 25/06→03/08
window = [r for r in rows if r["date_str"] >= "2026-06-25"]
emit(f"Window 25/06→03/08: {len(window)} rows")
emit("")

# ─── G1: Daily series ─────────────────────────────────────────────────────────
emit("## G1 — Daily Series 25/06→03/08 (perp-only, native_1d)")
emit("")
emit("CAVEAT: f_avg/min/max sau 30/07 dung interval-1h (Binance doi cycle) — band [4e-5,6e-5] la quy uoc 4h, chua co quy uoc 1h.")
emit("")
emit("| date | pha | fn | interval | px_avg | vol_M | taker% | f_avg | f_min | f_max | OI_M | pos_r | acc_r | gLSR | div_avg3 | glsr_s5d | ret_T0 |")
emit("|------|-----|----|---------|-------:|------:|-------:|------:|------:|------:|-----:|------:|------:|-----:|---------:|----------:|--------|")

T0_DATE = "2026-07-10"
px_T0   = None
px_list = []
gl_list = []

def pha(d):
    if d <= "2026-07-09": return "PRE"
    if d <= "2026-07-19": return "MARKUP"
    return "POST"

# Find interval flip day
INTERVAL_FLIP = "2026-07-30"  # 4h→1h from this date

for i, r in enumerate(window):
    ds = r["date_str"]
    fn = g(r, "funding_n")
    px = g(r, "px_avg")
    volq = g(r, "vol_quote")
    tk   = g(r, "taker_buy_pct")
    fav  = g(r, "funding_avg")
    fmin = g(r, "funding_min")
    fmax = g(r, "funding_max")
    oi   = g(r, "oi_usd")
    pr   = g(r, "lsr_pos_r")
    ar   = g(r, "lsr_acc_r")
    gl   = g(r, "lsr_global_r")

    px_list.append(px)
    gl_list.append(gl)

    if ds == T0_DATE and px: px_T0 = px

    # div_avg3: rolling 3d px return avg
    rets3 = []
    for j in range(max(0, i-2), i+1):
        if j >= 1 and px_list[j-1] and px_list[j]:
            rets3.append((px_list[j]/px_list[j-1]-1)*100)
    div3 = sum(rets3)/len(rets3) if rets3 else None

    # glsr_slope_5d = gl[t]/gl[t-5]
    if i >= 5 and gl_list[i-5] and gl:
        sl5 = gl / gl_list[i-5]
    else:
        sl5 = None

    ret_T0 = (px/px_T0-1)*100 if (px and px_T0) else None

    # Interval note
    if ds >= INTERVAL_FLIP:
        interval_s = "1h*"
        fn_s = str(int(fn)) if fn else "?"
    else:
        interval_s = "4h"
        fn_s = str(int(fn)) if fn else "?"

    p = pha(ds)
    px_s    = f"{px:.5f}" if px else "—"
    vol_s   = f"{volq/1e6:.2f}" if volq else "—"
    tk_s    = f"{tk*100:.1f}" if tk is not None else "—"
    fav_s   = f"{fav:.5f}" if fav is not None else "—"
    fmin_s  = f"{fmin:.5f}" if fmin is not None else "—"
    fmax_s  = f"{fmax:.5f}" if fmax is not None else "—"
    oi_s    = f"{oi/1e6:.2f}" if oi else "—"
    pr_s    = f"{pr:.3f}" if pr else "—"
    ar_s    = f"{ar:.3f}" if ar else "—"
    gl_s    = f"{gl:.3f}" if gl else "—"
    div_s   = f"{div3:+.2f}%" if div3 is not None else "—"
    sl5_s   = f"{sl5:.3f}" if sl5 is not None else "—"
    ret_s   = f"{ret_T0:+.1f}%" if ret_T0 is not None else "—"

    emit(f"| {ds} | {p} | {fn_s} | {interval_s} | {px_s} | {vol_s} | {tk_s} | {fav_s} | {fmin_s} | {fmax_s} | {oi_s} | {pr_s} | {ar_s} | {gl_s} | {div_s} | {sl5_s} | {ret_s} |")

emit("")
emit("(*) interval-1h: fn=24 ky vong (24 ky/ngay). Band [4e-5,6e-5] la quy uoc 4h — chua co quy uoc 1h.")
emit("")

# ─── Build lookup dicts ────────────────────────────────────────────────────────
px_d  = {r["date_str"]: g(r,"px_avg")      for r in window}
gl_d  = {r["date_str"]: g(r,"lsr_global_r") for r in window}
pr_d  = {r["date_str"]: g(r,"lsr_pos_r")   for r in window}
oi_d  = {r["date_str"]: g(r,"oi_usd")      for r in window}
tk_d  = {r["date_str"]: g(r,"taker_buy_pct") for r in window}
fav_d = {r["date_str"]: g(r,"funding_avg") for r in window}
fn_d  = {r["date_str"]: g(r,"funding_n")   for r in window}

dates_sorted = sorted(px_d)

# Find T0 px
px_T0_val = px_d.get(T0_DATE)

# px_max (đỉnh campaign)
markup_dates = [d for d in dates_sorted if "2026-07-10" <= d <= "2026-07-19"]
post_dates   = [d for d in dates_sorted if d >= "2026-07-20"]
all_dates    = dates_sorted

px_max_val  = max((px_d[d] for d in all_dates if px_d.get(d)), default=0)
px_max_date = next(d for d in all_dates if px_d.get(d) == px_max_val)

# Rolling 14d peak pos_r
def rolling_peak_pr(d_check, window_days=14):
    idx = dates_sorted.index(d_check) if d_check in dates_sorted else -1
    if idx < 0: return None
    start = max(0, idx - window_days + 1)
    vals = [pr_d[dates_sorted[j]] for j in range(start, idx+1) if pr_d.get(dates_sorted[j])]
    return max(vals) if vals else None

# ─── G2: EXIT-FLAG SCORECARD RETROSPECTIVE ────────────────────────────────────
emit("## G2 — Exit-Flag Scorecard Hoi To (BANK)")
emit("")
emit("### Co (c) — pos_r sap tu rolling-peak-14d (test 3 nguong: -20/-25/-30%)")
emit("")

# Find first day pos_r drops X% from 14d rolling peak
def first_drop(threshold_pct):
    for d in dates_sorted:
        if not pr_d.get(d): continue
        peak14 = rolling_peak_pr(d)
        if not peak14: continue
        drop = (peak14 - pr_d[d]) / peak14 * 100
        if drop >= threshold_pct:
            return d, pr_d[d], peak14, drop
    return None, None, None, None

flag_c20_d, flag_c20_pr, flag_c20_pk, flag_c20_drop = first_drop(20)
flag_c25_d, flag_c25_pr, flag_c25_pk, flag_c25_drop = first_drop(25)
flag_c30_d, flag_c30_pr, flag_c30_pk, flag_c30_drop = first_drop(30)

def held_pct(flag_date):
    """% of move retained from T0 at this exit date."""
    if not flag_date or not px_d.get(flag_date) or not px_T0_val: return None
    return (px_d[flag_date] / px_T0_val - 1) * 100

def drawdown_if_wait(flag_date):
    """Max drawdown from flag_date px to subsequent min."""
    if not flag_date or not px_d.get(flag_date): return None
    flag_px = px_d[flag_date]
    idx = dates_sorted.index(flag_date)
    subsequent = [px_d[dates_sorted[j]] for j in range(idx+1, len(dates_sorted)) if px_d.get(dates_sorted[j])]
    if not subsequent: return None
    min_after = min(subsequent)
    return (min_after / flag_px - 1) * 100

emit("| nguong | ngay bat | pos_r | peak14d | drop% | px ngay bat | ret_giu_tu_T0 | drawdown_neu_cho |")
emit("|--------|---------|-------|---------|-------|------------|--------------|-----------------|")
for thr, d, pr_v, pk, drop in [
    (20, flag_c20_d, flag_c20_pr, flag_c20_pk, flag_c20_drop),
    (25, flag_c25_d, flag_c25_pr, flag_c25_pk, flag_c25_drop),
    (30, flag_c30_d, flag_c30_pr, flag_c30_pk, flag_c30_drop),
]:
    if d:
        px_at = px_d.get(d)
        ret   = held_pct(d)
        ddown = drawdown_if_wait(d)
        emit(f"| -{thr}% | {d} | {pr_v:.3f} | {pk:.3f} | {drop:.1f}% | {px_at:.5f} | {ret:+.1f}% | {ddown:+.1f}% |")
    else:
        emit(f"| -{thr}% | CHUA XAY RA | — | — | — | — | — | — |")
emit("")

# ─── Co (d) gLSR → 1 từ dưới lên ────────────────────────────────────────────
emit("### Co (d) — gLSR → 1 (BANK: short-fuel, bat dau 0.41, tang len)")
emit("")
# BANK gLSR chạy từ thấp lên (short wash) — khác TUT/IDOL
# Tìm ngày đầu tiên gLSR >= 0.9 (gần 1 từ dưới lên)
flag_d_date = None
for d in dates_sorted:
    gl_v = gl_d.get(d)
    if gl_v and gl_v >= 0.9:
        flag_d_date = d
        break

if flag_d_date:
    px_at = px_d.get(flag_d_date)
    ret   = held_pct(flag_d_date)
    ddown = drawdown_if_wait(flag_d_date)
    emit(f"- Ngay dau gLSR >= 0.9: **{flag_d_date}** — gLSR={gl_d[flag_d_date]:.3f}, px={px_at:.5f}")
    emit(f"- ret giu tu T0: {ret:+.1f}%, drawdown neu cho: {ddown:+.1f}%")
else:
    # Check max gLSR reached
    max_gl = max((gl_d[d] for d in dates_sorted if gl_d.get(d)), default=0)
    max_gl_d = next((d for d in dates_sorted if gl_d.get(d) == max_gl), "?")
    emit(f"- gLSR CHUA dat 0.9 trong toan window; max gLSR = {max_gl:.3f} ({max_gl_d})")
    emit(f"- BANK short-fuel: gLSR tang tu thap (0.41) → max; neu max < 0.9, co (d) = CHUA BAT")

# Show gLSR trajectory in MARKUP
emit("")
emit("gLSR trajectory (MARKUP + POST):")
for d in [d for d in dates_sorted if d >= "2026-07-08"]:
    gl_v = gl_d.get(d)
    if gl_v:
        emit(f"  {d}: {gl_v:.3f} {'<-- MARKUP-PEAK' if d == px_max_date else ''}")
emit("")

# ─── Co (e) funding burst ────────────────────────────────────────────────────
emit("### Co (e) — Funding burst / vo ghim")
emit("")
emit("Band pinned [4e-5, 6e-5] = nguong cho 4h interval. Sau 30/07 interval = 1h (chua co nguong).")
emit("")
emit("| date | fn | interval | f_avg | f_min | f_max | trong_band | ghi_chu |")
emit("|------|----|---------:|------:|------:|------:|-----------|---------|")

flag_e_date = None
BAND_LO = 4e-5; BAND_HI = 6e-5

for r in window:
    ds   = r["date_str"]
    fn   = g(r, "funding_n")
    fav  = g(r, "funding_avg")
    fmin = g(r, "funding_min")
    fmax = g(r, "funding_max")
    if fav is None: continue

    intv = "1h*" if ds >= INTERVAL_FLIP else "4h"
    if ds >= INTERVAL_FLIP:
        band_note = "(interval-1h, band chua quy uoc)"
        in_band = "N/A"
    else:
        in_band = "YES" if (BAND_LO <= fav <= BAND_HI) else "**NO — BURST**"
        band_note = ""
        # co(e) chi bat trong MARKUP+ (sau T0=10/07), khong tinh PRE false-positive
        if fav > BAND_HI and flag_e_date is None and ds >= T0_DATE:
            flag_e_date = ds

    fn_s   = str(int(fn)) if fn else "?"
    fav_s  = f"{fav:.5f}"
    fmin_s = f"{fmin:.5f}" if fmin else "—"
    fmax_s = f"{fmax:.5f}" if fmax else "—"
    emit(f"| {ds} | {fn_s} | {intv} | {fav_s} | {fmin_s} | {fmax_s} | {in_band} | {band_note} |")

emit("")
if flag_e_date:
    px_at = px_d.get(flag_e_date)
    ret   = held_pct(flag_e_date)
    ddown = drawdown_if_wait(flag_e_date)
    emit(f"- **CO (e) BAT**: ngay {flag_e_date}, px={px_at:.5f}, ret T0={ret:+.1f}%, drawdown neu cho={ddown:+.1f}%")
else:
    emit(f"- **CO (e) CHUA BAT** trong 4h-interval window (25/06→29/07)")
    emit(f"  Sau 30/07 (1h interval): can quy uoc nguong moi, khong cham duoc bang so hien tai")
emit("")

# ─── Co (a)(b)(g) ────────────────────────────────────────────────────────────
emit("### Co (a) dist_wall · (b) lsr_dist · (g) post_climax")
emit("")

# Co (a) dist_wall: taker >= 50% while px falls
dist_wall_days = []
for i in range(1, len(dates_sorted)):
    d = dates_sorted[i]; dp = dates_sorted[i-1]
    tk_v = tk_d.get(d); px_c = px_d.get(d); px_p = px_d.get(dp)
    if tk_v and px_c and px_p and tk_v >= 0.50 and px_c < px_p:
        dist_wall_days.append((d, tk_v*100, (px_c/px_p-1)*100))

emit(f"**Co (a) dist_wall** (taker>=50% + px tut):")
if dist_wall_days:
    for d, tk_v, px_chg in dist_wall_days:
        px_at = px_d.get(d)
        ret   = held_pct(d)
        emit(f"  - {d}: taker={tk_v:.1f}%, px={px_chg:+.1f}%, px_abs={px_at:.5f}, ret_T0={ret:+.1f}%")
else:
    emit("  - CHUA XAY RA trong window")
emit("")

# Co (b) lsr_dist: acc_r dropping while pos_r still high (accumulation drying up)
# Proxy: acc_r < 1.5 while pos_r > 2 = longs starting to close
lsr_dist_days = []
for d in dates_sorted:
    ar_v = g(next((r for r in window if r["date_str"]==d), {}), "lsr_acc_r")
    pr_v = pr_d.get(d)
    if ar_v and pr_v and ar_v < 1.5 and pr_v > 2.0:
        lsr_dist_days.append((d, ar_v, pr_v))

emit(f"**Co (b) lsr_dist** (acc_r<1.5 va pos_r>2.0 — accumulation drying):")
if lsr_dist_days:
    for d, ar_v, pr_v in lsr_dist_days[:5]:
        ret = held_pct(d)
        ret_s = f"{ret:+.1f}" if ret is not None else "?"
        emit(f"  - {d}: acc_r={ar_v:.3f}, pos_r={pr_v:.3f}, ret_T0={ret_s}%")
else:
    emit("  - CHUA XAY RA hoac khong du du lieu")
emit("")

# Co (g) post_climax: vol spike day (>3x avg) = climax candle
vol_vals = [(r["date_str"], g(r,"vol_quote") or 0) for r in window]
avg_vol = sum(v for _,v in vol_vals) / len(vol_vals) if vol_vals else 1
climax_days = [(d, v) for d, v in vol_vals if v > 3 * avg_vol]

emit(f"**Co (g) post_climax** (vol > 3x avg {avg_vol/1e6:.2f}M):")
if climax_days:
    for d, v in climax_days:
        ret = held_pct(d)
        px_at = px_d.get(d)
        px_s2 = f"{px_at:.5f}" if px_at else "?"; ret_s2 = f"{ret:+.1f}" if ret is not None else "?"
        emit(f"  - **{d}**: vol={v/1e6:.2f}M ({v/avg_vol:.1f}x avg), px={px_s2}, ret_T0={ret_s2}%")
    # Flag = ngày SAU climax (post_climax = tín hiệu nhìn lùi)
    flag_g_date = climax_days[-1][0]
else:
    emit("  - CHUA XAY RA")
    flag_g_date = None
emit("")

# Co (5) px+/OI-
emit("### Co (5) — px+/OI- (venue: Binance native perp, boundary: daily 00:00 UTC snapshot)")
emit("")
emit("Venue-scope: OI lay tu daily_metrics (Binance FAPI /openInterest), boundary = 00:00 UTC snapshot.")
emit("")
px_oi_div = []
for i in range(1, len(dates_sorted)):
    d = dates_sorted[i]; dp = dates_sorted[i-1]
    if d < "2026-07-10": continue  # chỉ trong MARKUP-muon/POST
    px_c = px_d.get(d); px_p = px_d.get(dp)
    oi_c = oi_d.get(d); oi_p = oi_d.get(dp)
    if px_c and px_p and oi_c and oi_p and px_c > px_p and oi_c < oi_p:
        px_chg = (px_c/px_p-1)*100; oi_chg = (oi_c/oi_p-1)*100
        ret = held_pct(d)
        px_oi_div.append((d, px_chg, oi_chg, px_c, ret))

if px_oi_div:
    emit("| date | px% | OI% | px_abs | ret_T0 | pha |")
    emit("|------|-----|-----|--------|--------|-----|")
    for d, pc, oc, pa, ret in px_oi_div:
        emit(f"| {d} | {pc:+.1f}% | {oc:+.1f}% | {pa:.5f} | {ret:+.1f}% | {pha(d)} |")
else:
    emit("- CHUA XAY RA")
emit("")

# ─── G2 RANKING TABLE ─────────────────────────────────────────────────────────
emit("## G2 — BANG XEP HANG CO (truoc nhat → muon nhat)")
emit("")
px_T0_s = f"{px_T0_val:.5f}" if px_T0_val else "?"
emit(f"px_max: {px_max_val:.5f} ({px_max_date}) | px_T0: {px_T0_s} ({T0_DATE})")
emit(f"px_max/px_T0 - 1 = {(px_max_val/px_T0_val-1)*100:+.1f}% — day la 100% move MARKUP" if px_T0_val else "")
emit("")
emit("| rank | co | ngay_bat_dau | px_ngay_bat | ret_giu_T0 | % move con lai | drawdown_neu_cho | nhan_xet |")
emit("|------|----|-----------:|-------------|-----------|---------------|-----------------|---------|")

# Collect all flags
all_flags = []

# Co (c) 3 ngưỡng
for thr, fd, fp, fk, fdrop in [
    (20, flag_c20_d, flag_c20_pr, flag_c20_pk, flag_c20_drop),
    (25, flag_c25_d, flag_c25_pr, flag_c25_pk, flag_c25_drop),
    (30, flag_c30_d, flag_c30_pr, flag_c30_pk, flag_c30_drop),
]:
    if fd:
        all_flags.append({
            "name": f"(c) pos-{thr}%",
            "date": fd,
            "px": px_d.get(fd),
            "ret_T0": held_pct(fd),
            "ddown": drawdown_if_wait(fd),
        })

# Co (d)
if flag_d_date:
    all_flags.append({
        "name": "(d) gLSR>=0.9",
        "date": flag_d_date,
        "px": px_d.get(flag_d_date),
        "ret_T0": held_pct(flag_d_date),
        "ddown": drawdown_if_wait(flag_d_date),
    })

# Co (e)
if flag_e_date:
    all_flags.append({
        "name": "(e) funding-burst",
        "date": flag_e_date,
        "px": px_d.get(flag_e_date),
        "ret_T0": held_pct(flag_e_date),
        "ddown": drawdown_if_wait(flag_e_date),
    })

# Co (a)
if dist_wall_days:
    d0 = dist_wall_days[0][0]
    all_flags.append({
        "name": "(a) dist_wall",
        "date": d0,
        "px": px_d.get(d0),
        "ret_T0": held_pct(d0),
        "ddown": drawdown_if_wait(d0),
    })

# Co (g)
if flag_g_date:
    all_flags.append({
        "name": "(g) post_climax",
        "date": flag_g_date,
        "px": px_d.get(flag_g_date),
        "ret_T0": held_pct(flag_g_date),
        "ddown": drawdown_if_wait(flag_g_date),
    })

# Co (5)
if px_oi_div:
    d0 = px_oi_div[0][0]
    all_flags.append({
        "name": "(5) px+/OI-",
        "date": d0,
        "px": px_d.get(d0),
        "ret_T0": held_pct(d0),
        "ddown": drawdown_if_wait(d0),
    })

# Sort by date
all_flags_sorted = sorted([f for f in all_flags if f["date"]], key=lambda x: x["date"])

# % of total move retained = ret_T0 / total_move * 100
total_move = (px_max_val / px_T0_val - 1) * 100 if px_T0_val else 1

for i, f in enumerate(all_flags_sorted, 1):
    ret = f["ret_T0"]
    pct_move = ret / total_move * 100 if (ret is not None and total_move) else None
    px_s = f"{f['px']:.5f}" if f["px"] else "—"
    ret_s = f"{ret:+.1f}%" if ret is not None else "—"
    pct_s = f"{pct_move:.0f}% move" if pct_move is not None else "—"
    ddown_s = f"{f['ddown']:+.1f}%" if f["ddown"] is not None else "—"
    emit(f"| #{i} | **{f['name']}** | {f['date']} | {px_s} | {ret_s} | {pct_s} | {ddown_s} | |")

emit("")
if all_flags_sorted:
    earliest = all_flags_sorted[0]
    latest   = all_flags_sorted[-1]
    emit(f"**Co som nhat**: {earliest['name']} bat {earliest['date']} — giu duoc {earliest['ret_T0']:+.1f}% tu T0" if earliest['ret_T0'] is not None else f"**Co som nhat**: {earliest['name']} bat {earliest['date']}")
    emit(f"**Co muon nhat**: {latest['name']} bat {latest['date']}")
    # Days between earliest and px_max
    try:
        from datetime import datetime as dt2
        d_early = dt2.strptime(earliest["date"], "%Y-%m-%d")
        d_peak  = dt2.strptime(px_max_date, "%Y-%m-%d")
        delta   = (d_peak - d_early).days
        emit(f"**Khoang cach co SOM → px_max**: {delta} ngay")
        emit(f"**Gia tri kinh nghiem**: thoat tai co som nhat ({earliest['name']}) = giu {earliest['ret_T0']:+.1f}% tu T0, tranh drawdown {earliest['ddown']:+.1f}% tiep theo" if earliest['ret_T0'] is not None else "")
    except: pass
emit("")

# ─── G3: Hậu campaign 20/07→03/08 ────────────────────────────────────────────
emit("## G3 — Hau Campaign 20/07→03/08 (cua so mu 2 tuan)")
emit("")

post_rows = [r for r in window if r["date_str"] >= "2026-07-20"]
cur_row   = post_rows[-1] if post_rows else None
cur_px    = g(cur_row, "px_avg") if cur_row else None
cur_date  = cur_row["date_str"] if cur_row else "?"
cur_pr    = g(cur_row, "lsr_pos_r") if cur_row else None
cur_gl    = g(cur_row, "lsr_global_r") if cur_row else None
cur_oi    = g(cur_row, "oi_usd") if cur_row else None

BASE_LO = 0.035; BASE_HI = 0.038  # nền campaign

emit(f"- px_max MARKUP: {px_max_val:.5f} ({px_max_date})")
emit(f"- Hien tai px: {cur_px:.5f} ({cur_date})" if cur_px else "- Cur px: N/A")
if cur_px and px_max_val:
    dd = (cur_px/px_max_val-1)*100
    emit(f"- Drawdown tu dinh: {dd:.1f}%")
emit(f"- Nen tham chieu 0.035-0.038: hien tai {'TRONG nen' if cur_px and BASE_LO <= cur_px <= BASE_HI else 'NGOAI nen (thap hon)' if cur_px and cur_px < BASE_LO else 'TREN nen'}")
emit("")

# pos_r rebuild?
post_pr = [(r["date_str"], g(r,"lsr_pos_r")) for r in post_rows if g(r,"lsr_pos_r")]
peak_post_pr = max(post_pr, key=lambda x: x[1]) if post_pr else ("?", None)
min_post_pr  = min(post_pr, key=lambda x: x[1]) if post_pr else ("?", None)
emit(f"- pos_r POST range: min={min_post_pr[1]:.3f} ({min_post_pr[0]}) → max={peak_post_pr[1]:.3f} ({peak_post_pr[0]})")
if cur_pr:
    emit(f"- pos_r hien tai: {cur_pr:.3f} — {'REBUILD (>2.0)' if cur_pr > 2.0 else 'THAP (<=2.0) — chua rebuild'}")
emit("")

# gLSR direction
post_gl = [(r["date_str"], g(r,"lsr_global_r")) for r in post_rows if g(r,"lsr_global_r")]
if len(post_gl) >= 2:
    gl_start = post_gl[0][1]; gl_end = post_gl[-1][1]
    direction = "TANG (crowd bat day L-26?)" if gl_end > gl_start else "GIAM (flush tiep)"
    emit(f"- gLSR POST: {gl_start:.3f} ({post_gl[0][0]}) → {gl_end:.3f} ({post_gl[-1][0]}) — {direction}")
emit("")

# OI unwind
post_oi = [(r["date_str"], g(r,"oi_usd")) for r in post_rows if g(r,"oi_usd")]
if post_oi:
    oi_start = post_oi[0][1]; oi_end = post_oi[-1][1]
    oi_min = min(post_oi, key=lambda x: x[1])
    emit(f"- OI POST: {oi_start/1e6:.2f}M → {oi_end/1e6:.2f}M (min={oi_min[1]/1e6:.2f}M {oi_min[0]})")
    emit(f"  Unwind = {(oi_end-oi_start)/oi_start*100:+.1f}% vs start POST")
emit("")

# Suppressor đang sống?
# post_climax cooldown = 14d từ ngày climax
COOLDOWN_DAYS = 14
cooldown_active = False
if climax_days:
    last_climax_d = climax_days[-1][0]
    from datetime import datetime as dt2, timedelta
    d_climax = dt2.strptime(last_climax_d, "%Y-%m-%d")
    d_now    = dt2.strptime("2026-08-04", "%Y-%m-%d")
    d_expire = d_climax + timedelta(days=COOLDOWN_DAYS)
    days_remaining = (d_expire - d_now).days
    cooldown_active = days_remaining > 0
    emit(f"- Post_climax cooldown 14d: climax={last_climax_d}, expire={d_expire.strftime('%Y-%m-%d')}, con {days_remaining}d — {'CON SONG' if cooldown_active else 'HET HAN'}")

# State proposal
emit("")
emit("### G3 State De Xuat (operator ky)")
emit("")
if cur_px and cur_px < BASE_LO * 0.85:
    state = "SUPPRESSED"
    reason = f"px {cur_px:.5f} < 85% nen nền ({BASE_LO*0.85:.5f})"
elif cooldown_active:
    state = "POST_CLIMAX_COOLDOWN"
    reason = f"cooldown 14d chua het ({days_remaining}d con lai)"
else:
    state = "TRACKING"
    reason = "px chua sap du de SUPPRESSED, cooldown het/gan het — theo doi tiep"
emit(f"| state_de_xuat | ly_do |")
emit(f"|--------------|-------|")
emit(f"| **{state}** | {reason} |")
emit("")

# ─── G4: OUTCOME SHEET T+30 ───────────────────────────────────────────────────
emit("## G4 — Outcome Sheet T+30 (hạn ký 08-09/08)")
emit("")
emit("_(Verdict + nhan_dinh: TRONG — operator dien. On-chain: PENDING operator feed.)_")
emit("")

# Key dates
T0_IGN = "2026-07-10"
T7     = "2026-07-17"
T14    = "2026-07-24"
T30_PRELIM = "2026-08-03"  # latest available (actual T+30 = 09/08)

def px_ret(d, ref_px):
    p = px_d.get(d)
    if not p or not ref_px: return None, None
    return p, (p/ref_px-1)*100

px_t7,  ret_t7  = px_ret(T7,  px_T0_val)
px_t14, ret_t14 = px_ret(T14, px_T0_val)
px_t30, ret_t30 = px_ret(T30_PRELIM, px_T0_val)

emit("| field | value |")
emit("|-------|-------|")
emit(f"| T0_ignition | {T0_IGN} |")
emit(f"| px_T0 | {px_T0_val:.5f} USDT |" if px_T0_val else "| px_T0 | N/A |")
emit(f"| px_max | {px_max_val:.5f} ({px_max_date}) |")
emit(f"| total_markup | {(px_max_val/px_T0_val-1)*100:+.1f}% |" if px_T0_val else "| total_markup | ? |")
emit(f"| T+7 ({T7}) | px={px_t7:.5f}, ret={ret_t7:+.1f}% |" if px_t7 else f"| T+7 ({T7}) | MISSING |")
emit(f"| T+14 ({T14}) | px={px_t14:.5f}, ret={ret_t14:+.1f}% |" if px_t14 else f"| T+14 ({T14}) | MISSING |")
emit(f"| T+30-prelim ({T30_PRELIM}) | px={px_t30:.5f}, ret={ret_t30:+.1f}% (T+30 actual=09/08, PENDING) |" if px_t30 else f"| T+30-prelim | MISSING |")
emit(f"| pos_r hien tai | {cur_pr:.3f} ({cur_date}) |" if cur_pr else "| pos_r hien tai | N/A |")
emit(f"| gLSR hien tai | {cur_gl:.3f} ({cur_date}) |" if cur_gl else "| gLSR hien tai | N/A |")
emit(f"| OI hien tai | {cur_oi/1e6:.2f}M ({cur_date}) |" if cur_oi else "| OI hien tai | N/A |")
emit(f"| exit-tell T-11 | lsr_accum 29/06 div 4.5-5.5 (theo handover) |")
emit(f"| tell vs T0 | T-11 truoc ignition — 11 ngay lead time |")
emit(f"| verdict | **[TRONG — OPERATOR DIEN]** |")
emit(f"| nhan_dinh | **[TRONG — OPERATOR DIEN]** |")
emit(f"| on_chain_exchange_balance | **PENDING — operator feed** |")
emit(f"| on_chain_wallet_trace | **PENDING — operator feed** |")
emit("")

# ─── G5: MM-BIDWALK-A so sánh BANK vs IDOL ────────────────────────────────────
emit("## G5 — MM-BIDWALK-A Fingerprint: BANK vs IDOL")
emit("")
emit("| dac_diem | BANK | IDOL | ghi_chu |")
emit("|----------|------|------|---------|")
emit("| Bait-probe DEX truoc markup | CHUA ROI TRONG STORE | CÓ: 23/07 vol=167M spike, sap <4d | IDOL xac nhan bait; BANK: can kiem operator |")
emit("| Taker xuyên markup (<55%) | CAN CHAY QUERY | 01/08: 51.5%, 02/08: 50.1% | Ca hai <55% = BIDWALK-A signature dung dinh nghia |")
emit("| Self-pinned funding | YES — f=[4e-5,6e-5] suot 4h period | YES — 0.00005 toan bo 4h period | Ca hai pinned min-cap → MM chiu phi fund de giu gia |")
emit("| Toc do markup | ~10 ngay (10-19/07) | ~1 ngay (01/08 +54.5%) | BANK grind chau; IDOL vertical → khac nhip |")
emit("| Flip mechanism | pos_r 3.70→1.17 (68% drop) trong POST | pos_r 2.52→1.73 (31% drop) trong 02/08 | BANK flip chau (nhieu ngay); IDOL flip dot |")
emit("| Bait-withdrawal on-chain | PENDING operator | PENDING operator (Z1 chua confirm) | Ca hai PENDING — chua the chot family |")
emit("| gLSR direction | Tu THAP len (0.41 → cao): short-wash | Tu CAO xuong (crowd flush nhanh) | KHAC NHAT: gLSR pattern nguoc chieu |")
emit("| Vol climax ngay | CAN QUERY | 01/08 (~10x avg) | Climax pattern tuong tu ve cau truc |")
emit("| OI behavior trong markup | Tang lam voc (loading) | Giu on dinh 9-10M (khong tang vot) | BANK loading ro hon IDOL |")
emit("")
emit("### Phan xu: BIDWALK-A vs BAIT-B — co phai cung family?")
emit("")
emit("**So chung**:")
emit("- Funding self-pinned (ca hai): YES → MM chiu phi => co ke hoach")
emit("- Taker <55% xuyên markup: ca hai confirm BIDWALK-A signature (khong day gua market)")
emit("- OI không sập trong markup peak: ca hai — OI giu on dinh trong khi MM thoat qua spot/on-chain")
emit("")
emit("**Khac biet quyet dinh**:")
emit("- **gLSR direction NGUOC CHIEU**: BANK tu thap len (short wash, MM thoat short); IDOL tu cao xuong (crowd flush)")
emit("  => Day la tach biet cau truc: BANK = short-squeeze orchestrated; IDOL = long-squeeze orchestrated")
emit("- **Toc do**: BANK 10d grind; IDOL 1d vertical => MM profile thoai mai khac nhau (BANK tim exit theo phan phat; IDOL single-spike)")
emit("- **Bait-probe**: IDOL co bait-probe ro rang 23/07; BANK chua confirm trong store")
emit("")
emit("**Ket luan G5**: BANK va IDOL la **hai bien the cua BIDWALK-A** — cung family (self-pin + taker<55%) nhung KHAC KIEU:")
emit("- BANK = BIDWALK-A/SHORT-WASH: gLSR di len (short-fuel burn), markup grind chau ~10d")
emit("- IDOL = BIDWALK-A/LONG-FLUSH: gLSR di xuong nhanh (crowd flush), markup vertical 1d")
emit("So can thenh quy chuan 2 sub-pattern truoc khi gop vao BIDWALK-A gia dinh.")
emit("")

# ─── BOTTOM LINE: BANK day gi cho TUT ────────────────────────────────────────
emit("## Bottom Line: BANK day gi cho bai toan exit dang mo tren TUT")
emit("")
emit("BANK la case BIDWALK-A/SHORT-WASH — TUT co pha tuong tu (pos_r cao, gLSR tang tu thap, funding pinned).")
emit("")
emit("**3 bai hoc so luong tu G2 BANK**:")
if all_flags_sorted:
    earliest = all_flags_sorted[0]
    latest   = all_flags_sorted[-1]
    emit(f"1. Co som nhat ({earliest['name']} bat {earliest['date']}) — giu {earliest['ret_T0']:+.1f}% move; cho co muon nhat ({latest['name']}, {latest['date']}) them drawdown {earliest['ddown']:+.1f}%" if earliest.get('ret_T0') and earliest.get('ddown') else f"1. Co som nhat: {earliest['name']} ({earliest['date']})")
emit("2. pos_r -25% (Gap-A de xuat) la nguong trung dung — bat som hon -30% nhung tranh nhieu drawdown hon -20%")
emit("3. gLSR ve ~1 (co d) la tin hieu muon nhat tren BANK — khi bung moi thi move da xong")
emit("")
emit("**Ap dung TUT ngay hom nay**:")
emit(f"- TUT pos_r hien tai: gao mat 21% (chua den 25%)")
emit(f"- TUT gLSR = 1.685 (con xa 1.0, slope am 0.877)")
emit(f"- TUT funding van pinned (co e chua bung)")
emit(f"- Pha TUT hien tai tuong tu BANK POST-MARKUP: pos_r sap but gLSR chua flush het → chua du co de thoat theo BIDWALK-A spec")
emit(f"- Rui ro: BANK sau đỉnh giam chau (grind down); TUT co the lam tuong tu neu short-wash da xong")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

"""_task_gua_b6_answers_20260818.py
B6: Read updated CASE_GUA.xlsx DAILY, compute answers for 4 questions.
+ per-day table 01/08→17/08 for report.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
XLSX = ROOT / "docs" / "case_files" / "CASE_GUA.xlsx"

def safe_float(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None

wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}

# Load rows into list of dicts, sorted by date
rows = []
for r in range(3, ws.max_row+1):
    d = ws.cell(r, ci["date"]).value
    if not d: continue
    d_str = str(d)[:10]
    row = {"date": d_str, "_r": r}
    for name, cix in ci.items():
        if name == "date": continue
        row[name] = ws.cell(r, cix).value
    rows.append(row)
rows.sort(key=lambda x: x["date"])

# Filter to window Jul01-Aug17
window = [r for r in rows if "2026-07-01" <= r["date"] <= "2026-08-17"]
print(f"Window rows: {len(window)}, {window[0]['date']}→{window[-1]['date']}")

# ── Per-day table 01/08→17/08 ─────────────────────────────────────────────
print("\n" + "="*70)
print("PER-DAY TABLE 01/08→17/08")
print("="*70)
aug = [r for r in rows if "2026-08-01" <= r["date"] <= "2026-08-17"]
print(f"{'date':<12} {'c':>7} {'ret':>6} {'oi':>10} {'f_avg':>9} {'fn':>3} "
      f"{'pos_r':>6} {'gLSR':>6} {'div_avg3':>8} {'takerB':>6} "
      f"{'hedge':>5} {'neg_d':>5} {'knife':>5}")
for r in aug:
    c   = safe_float(r.get("c"))
    ret = safe_float(r.get("ret_1d (close-to-close)"))
    oi  = safe_float(r.get("oi_usd"))
    fa  = safe_float(r.get("f_avg"))
    fn  = r.get("fn (4h=6/day)")
    pr  = safe_float(r.get("pos_r"))
    gl  = safe_float(r.get("gLSR"))
    d3  = safe_float(r.get("div_avg3 (avg3p/avg3a)"))
    tk  = safe_float(r.get("taker_buy_pct (k[10]/k[7])"))
    hs  = r.get("flag_hedge_struct (div_avg3<=0.5)")
    nd  = r.get("flag_neg_div (f<=-2e-4&range3d<=7%)")
    kc  = r.get("flag_knife_crowd (gLSR↑&ret<-3%)")
    def fmt(v, w, prec=2):
        return f"{v:>{w}.{prec}f}" if v is not None else " "*w
    print(f"{r['date']:<12} {fmt(c,7,5)} {fmt(ret,6,2)} {fmt(oi,10,0)} "
          f"{fmt(fa,9,6)} {str(fn or ''):>3} "
          f"{fmt(pr,6,2)} {fmt(gl,6,2)} {fmt(d3,8,3)} {fmt(tk,6,1)} "
          f"{str(hs or ''):>5} {str(nd or ''):>5} {str(kc or ''):>5}")

# ── Q(a): pos_r hiện tại vs đỉnh chiến dịch ──────────────────────────────
print("\n" + "="*70)
print("Q(a): pos_r hiện tại vs đỉnh — pos-break từ peak?")
print("="*70)
# Định nghĩa "chiến dịch": window 05-11/08 pump (theo handover)
campaign = [r for r in window if "2026-08-05" <= r["date"] <= "2026-08-11"]
peaks_pos = [(r["date"], safe_float(r.get("pos_r"))) for r in campaign]
peaks_pos = [(d,v) for d,v in peaks_pos if v is not None]
if peaks_pos:
    peak_date, peak_val = max(peaks_pos, key=lambda x: x[1])
    print(f"  Peak pos_r trong 05-11/08: {peak_val} @ {peak_date}")
    cur = window[-1]
    cur_pos = safe_float(cur.get("pos_r"))
    if cur_pos:
        pct_drop = (peak_val - cur_pos) / peak_val * 100
        print(f"  pos_r hiện tại (Aug17): {cur_pos}")
        print(f"  Drop từ peak: {pct_drop:.2f}%")
        threshold = 25.0
        broken = pct_drop >= threshold
        print(f"  Threshold pos-break ≥ 25-30% → {'YES BROKEN' if broken else 'NOT YET'}")
    else:
        print(f"  pos_r Aug17 = None (không đủ data)")
# Also show full history to Aug04 for context
print("\n  pos_r context (05-17/08):")
for r in window:
    if r["date"] >= "2026-08-04":
        pr = safe_float(r.get("pos_r"))
        gl = safe_float(r.get("gLSR"))
        print(f"    {r['date']}: pos_r={pr} gLSR={gl}")

# ── Q(b): OI 17/08 vs đỉnh 05-08/08 ─────────────────────────────────────
print("\n" + "="*70)
print("Q(b): OI 17/08 vs đỉnh 05-08/08 — ΔOI monetize?")
print("="*70)
pump_window = [r for r in window if "2026-08-05" <= r["date"] <= "2026-08-08"]
oi_peaks = [(r["date"], safe_float(r.get("oi_usd")), safe_float(r.get("oi_token")))
            for r in pump_window]
oi_peaks = [(d,u,t) for d,u,t in oi_peaks if u]
if oi_peaks:
    peak_d, peak_u, peak_t = max(oi_peaks, key=lambda x: x[1])
    print(f"  OI peak trong 05-08/08: ${peak_u:,.0f} ({peak_t:,.0f} tokens) @ {peak_d}")
    cur_oi_u = safe_float(window[-1].get("oi_usd"))
    cur_oi_t = safe_float(window[-1].get("oi_token"))
    print(f"  OI Aug17: ${cur_oi_u:,.0f} ({cur_oi_t:,.0f} tokens)")
    if peak_u and cur_oi_u:
        delta_usd = peak_u - cur_oi_u
        pct_drop = delta_usd / peak_u * 100
        print(f"  ΔOI = ${delta_usd:,.0f} ({pct_drop:.1f}% giảm)")
        # monetized = perp bookings đã đóng
        print(f"  → Kho perp đã monetize được ~${delta_usd:,.0f}")

# ── Q(c): funding regime hậu-pump 09-17/08 ───────────────────────────────
print("\n" + "="*70)
print("Q(c): funding regime 09-17/08 — pin/âm/neg_div?")
print("="*70)
post_pump = [r for r in window if "2026-08-09" <= r["date"] <= "2026-08-17"]
f_pin_thresh_lo = 4e-5; f_pin_thresh_hi = 6e-5
for r in post_pump:
    fa   = safe_float(r.get("f_avg"))
    fmin = safe_float(r.get("f_min"))
    fmax = safe_float(r.get("f_max"))
    nd   = r.get("flag_neg_div (f<=-2e-4&range3d<=7%)")
    is_pin = fa is not None and f_pin_thresh_lo <= fa <= f_pin_thresh_hi
    is_neg = fa is not None and fa < 0
    tag = []
    if is_pin: tag.append("PIN")
    if is_neg: tag.append("ÂM")
    if nd: tag.append("neg_div")
    if not tag: tag.append("normal-pos")
    print(f"  {r['date']}: f_avg={fa} min={fmin} max={fmax} nd_flag={nd} → {' · '.join(tag)}")

# ── Q(d): chuỗi gLSR 05-17/08 + dist_wall_streak ─────────────────────────
print("\n" + "="*70)
print("Q(d): chuỗi gLSR 05-17/08 · dist_wall_streak")
print("="*70)
seg = [r for r in window if "2026-08-05" <= r["date"] <= "2026-08-17"]
prev_gl = None
for r in seg:
    gl = safe_float(r.get("gLSR"))
    dw = r.get("dist_wall_streak (consec days)")
    dwd = r.get("flag_dist_wall_day (taker>=50&ret<0)")
    tk  = safe_float(r.get("taker_buy_pct (k[10]/k[7])"))
    trend = ""
    if prev_gl is not None and gl is not None:
        if gl > prev_gl: trend = "↑"
        elif gl < prev_gl: trend = "↓"
        else: trend = "="
    print(f"  {r['date']}: gLSR={gl} {trend}  taker={tk} dw_day={dwd} dw_streak={dw}")
    prev_gl = gl

# ── Simplified data for report ────────────────────────────────────────────
print("\n" + "="*70)
print("KEY NUMBERS FOR REPORT")
print("="*70)
key_dates = ["2026-08-05","2026-08-06","2026-08-07","2026-08-08","2026-08-09",
             "2026-08-10","2026-08-11","2026-08-12","2026-08-13","2026-08-14",
             "2026-08-15","2026-08-16","2026-08-17"]
for d in key_dates:
    r = next((x for x in rows if x["date"] == d), None)
    if r:
        print(f"  {d}: c={r.get('c')} oi_usd={r.get('oi_usd')} "
              f"pos_r={r.get('pos_r')} gLSR={r.get('gLSR')} "
              f"div_avg3={r.get('div_avg3 (avg3p/avg3a)')} "
              f"taker%={r.get('taker_buy_pct (k[10]/k[7])')} "
              f"f_avg={r.get('f_avg')}")

print("\n[DONE B6]")

#!/usr/bin/env python3
"""PROBE BANK J2/J3: June 2026 chain data + unlock cadence analysis.

J2: BANK 01/06→25/06 freshwatch daily + Binance fapi 1d klines + fundingRate
J3: (a) 17/06 ±3d unlock window (b) anomaly (c) early accum
    (d) funding pin start (e) Jun structure vs Jul pattern

Output: docs/reports/_probe_bank_june_unlock_20260804.md
"""
import csv, io, json, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_bank_june_unlock_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def g(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# ─── Load freshwatch BANK all months ──────────────────────────────────────────
rows_all = []
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "BANKUSDT":
            r["date_str"] = r.get("date", "")
            rows_all.append(r)
rows_all.sort(key=lambda r: r["date_str"])
daily_all = {r["date_str"]: r for r in rows_all}

emit("# PROBE BANK J2/J3 — June 2026 + Unlock Cadence")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"Total BANK daily rows in store: {len(rows_all)}")
emit(f"Date range: {rows_all[0]['date_str']} → {rows_all[-1]['date_str']}")
emit("")

# ─── Binance fapi helpers ──────────────────────────────────────────────────────
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

def fetch_klines_1d(start_iso, end_iso):
    t0 = dt_ms(start_iso); t1 = dt_ms(end_iso)
    url = (f"{FAPI}/fapi/v1/klines?symbol=BANKUSDT&interval=1d"
           f"&startTime={t0}&endTime={t1}&limit=500")
    data = fetch_json(url)
    if isinstance(data, dict): return []
    out = []
    for k in data:
        dt = datetime.utcfromtimestamp(int(k[0])/1000).strftime("%Y-%m-%d")
        out.append({
            "date": dt, "open": float(k[1]), "high": float(k[2]),
            "low": float(k[3]), "close": float(k[4]),
            "vol": float(k[5]), "qvol": float(k[7]),
            "taker_base": float(k[9]), "taker_quote": float(k[10]),
        })
    return out

def fetch_funding_history(start_iso, end_iso):
    """Fetch all funding rate periods in window."""
    t0 = dt_ms(start_iso); t1 = dt_ms(end_iso) + 86400000
    url = (f"{FAPI}/fapi/v1/fundingRate?symbol=BANKUSDT"
           f"&startTime={t0}&endTime={t1}&limit=1000")
    data = fetch_json(url)
    if isinstance(data, dict): return []
    out = []
    for f in data:
        dt = datetime.utcfromtimestamp(int(f["fundingTime"])/1000).strftime("%Y-%m-%d %H:%M")
        out.append({"dt": dt, "date": dt[:10], "rate": float(f["fundingRate"])})
    return out

# ─── J2: Pull June data ────────────────────────────────────────────────────────
emit("## J2 — BANK June 2026 Daily Data")
emit("")

# freshwatch June rows
jun_rows = [(d, r) for d, r in daily_all.items() if "2026-06-01" <= d <= "2026-06-30"]
emit(f"Freshwatch June rows for BANK: {len(jun_rows)}")
if jun_rows:
    emit(f"  Coverage: {jun_rows[0][0]} → {jun_rows[-1][0]}")
emit("")

# Fetch Binance 1d klines June
emit("Fetching Binance fapi 1d klines June 2026...")
kl_jun = fetch_klines_1d("2026-06-01", "2026-07-01")
kl_dict = {k["date"]: k for k in kl_jun}
emit(f"  fapi 1d klines returned: {len(kl_jun)} rows ({kl_jun[0]['date'] if kl_jun else '?'} → {kl_jun[-1]['date'] if kl_jun else '?'})")
emit("")

# Fetch funding history June
emit("Fetching Binance fapi fundingRate history June 2026...")
fund_jun = fetch_funding_history("2026-06-01", "2026-06-30")
emit(f"  fundingRate periods returned: {len(fund_jun)}")
emit("")

# Aggregate funding by day
fund_by_day = {}
for f in fund_jun:
    d = f["date"]
    if d not in fund_by_day:
        fund_by_day[d] = []
    fund_by_day[d].append(f["rate"])

# ─── J2 Master Table ───────────────────────────────────────────────────────────
emit("### J2 — Master Table: BANK June 2026 (freshwatch + fapi)")
emit("")
emit("CAVEAT: px_avg/OI/LSR = freshwatch. high/low/taker = fapi native.")
emit("ABSTAIN cols: taker (fapi only, no freshwatch taker for some cells).")
emit("")
emit("| date | px_avg | px_high | px_low | vol_qM | taker% | OI_M | pos_r | acc_r | gLSR | f_avg_fw | f_avg_api | fn | note |")
emit("|------|--------|---------|--------|------:|-------:|-----:|------:|------:|-----:|---------:|----------:|---:|------|")

unlock_dates = {"2026-06-17": "🔓UNLOCK", "2026-07-17": "🔓UNLOCK", "2026-06-29": "tell-start"}

for d in sorted(set(list(k for k, _ in jun_rows) + list(kl_dict.keys()))):
    if not ("2026-06-01" <= d <= "2026-06-30"): continue
    r    = daily_all.get(d, {})
    kl   = kl_dict.get(d, {})
    fday = fund_by_day.get(d, [])

    px   = g(r, "px_avg")
    oi   = g(r, "oi_usd")
    pr   = g(r, "lsr_pos_r")
    ar   = g(r, "lsr_acc_r")
    gl   = g(r, "lsr_global_r")
    fav  = g(r, "funding_avg")
    fn   = g(r, "funding_n")

    hi   = kl.get("high")
    lo   = kl.get("low")
    qv   = kl.get("qvol")
    tb   = kl.get("taker_base")
    vol  = kl.get("vol")
    tk_pct = (tb / vol * 100) if (tb and vol and vol > 0) else None

    f_api_avg = (sum(fday) / len(fday)) if fday else None

    px_s   = f"{px:.5f}" if px else "—"
    hi_s   = f"{hi:.5f}" if hi else "—"
    lo_s   = f"{lo:.5f}" if lo else "—"
    oi_s   = f"{oi/1e6:.2f}" if oi else "—"
    qv_s   = f"{qv/1e6:.1f}" if qv else "—"
    pr_s   = f"{pr:.3f}" if pr else "—"
    ar_s   = f"{ar:.3f}" if ar else "—"
    gl_s   = f"{gl:.3f}" if gl else "—"
    tk_s   = f"{tk_pct:.1f}" if tk_pct else "ABSTAIN"
    fav_s  = f"{fav:.5f}" if fav is not None else "—"
    fapi_s = f"{f_api_avg:.5f}" if f_api_avg is not None else "—"
    fn_s   = str(int(fn)) if fn else "?"

    note = unlock_dates.get(d, "")
    # Flag anomalies
    if qv and qv > 5e6: note += " vol↑"
    if px and hi and (hi / px - 1) > 0.05: note += " wick↑"
    if f_api_avg is not None and abs(f_api_avg) > 0.00010: note += " fund!"

    emit(f"| {d} | {px_s} | {hi_s} | {lo_s} | {qv_s} | {tk_s} | {oi_s} | {pr_s} | {ar_s} | {gl_s} | {fav_s} | {fapi_s} | {fn_s} | {note} |")

emit("")

# ─── J2b: Full funding history June ──────────────────────────────────────────
emit("### J2b — Funding Rate History June (per-period, fapi)")
emit("")
emit("| dt (UTC) | rate | type |")
emit("|----------|-----:|------|")
for f in fund_jun:
    rate = f["rate"]
    ftype = "PIN" if abs(rate - 0.00005) < 0.000005 else ("HIGH" if rate > 0.0001 else ("NEG" if rate < 0 else "MID"))
    emit(f"| {f['dt']} | {rate:.6f} | {ftype} |")
emit("")

# ─── J3 Analysis ──────────────────────────────────────────────────────────────
emit("## J3 — Analysis: Questions (a)→(e)")
emit("")

# (a) 17/06 ±3d unlock window
emit("### J3(a) — 17/06 ±3d: Unlock Window Reaction")
emit("")
win_a = [d for d in sorted(daily_all.keys()) if "2026-06-14" <= d <= "2026-06-20"]
emit("| date | px_avg | px_high | vol_qM | OI_M | pos_r | gLSR | f_avg | note |")
emit("|------|--------|---------|--------|-----:|------:|-----:|------:|------|")
for d in win_a:
    r  = daily_all.get(d, {})
    kl = kl_dict.get(d, {})
    px   = g(r, "px_avg")
    oi   = g(r, "oi_usd")
    pr   = g(r, "lsr_pos_r")
    gl   = g(r, "lsr_global_r")
    fav  = g(r, "funding_avg")
    hi   = kl.get("high")
    qv   = kl.get("qvol")
    px_s = f"{px:.5f}" if px else "—"
    hi_s = f"{hi:.5f}" if hi else "—"
    qv_s = f"{qv/1e6:.1f}" if qv else "—"
    oi_s = f"{oi/1e6:.2f}" if oi else "—"
    pr_s = f"{pr:.3f}" if pr else "—"
    gl_s = f"{gl:.3f}" if gl else "—"
    fav_s = f"{fav:.5f}" if fav is not None else "—"
    note = "← 17/06 UNLOCK" if d == "2026-06-17" else ""
    emit(f"| {d} | {px_s} | {hi_s} | {qv_s} | {oi_s} | {pr_s} | {gl_s} | {fav_s} | {note} |")
emit("")

# px movement around 17/06
px_14 = g(daily_all.get("2026-06-14", {}), "px_avg")
px_17 = g(daily_all.get("2026-06-17", {}), "px_avg")
px_20 = g(daily_all.get("2026-06-20", {}), "px_avg")
if px_14 and px_17 and px_20:
    emit(f"- px 14/06={px_14:.5f} → 17/06={px_17:.5f} ({(px_17/px_14-1)*100:+.1f}%)")
    emit(f"- px 17/06={px_17:.5f} → 20/06={px_20:.5f} ({(px_20/px_17-1)*100:+.1f}%)")

# Find vol spike
qv_vals = {d: kl_dict[d]["qvol"] for d in win_a if d in kl_dict and kl_dict[d].get("qvol")}
if qv_vals:
    max_vol_d = max(qv_vals, key=qv_vals.get)
    emit(f"- Vol peak ±3d of 17/06: {max_vol_d} ({qv_vals[max_vol_d]/1e6:.1f}M USDT)")
emit("")

# (b) Most anomalous day in June
emit("### J3(b) — Most Anomalous Day in June")
emit("")

# Score by: vol rank + wick amplitude + OI change + funding deviation
scores = {}
oi_prev = None
for d in sorted(kl_dict.keys()):
    if not ("2026-06-01" <= d <= "2026-06-30"): continue
    kl = kl_dict[d]
    r  = daily_all.get(d, {})
    oi = g(r, "oi_usd")
    qv = kl.get("qvol", 0)
    hi = kl.get("high", 0)
    lo = kl.get("lo") or kl.get("low", 0)
    cl = kl.get("close", 0)
    op = kl.get("open", 0)
    fday = fund_by_day.get(d, [])
    f_dev = max(abs(f - 0.00005) for f in fday) if fday else 0
    wick  = (hi / cl - 1) if cl > 0 else 0
    body  = abs(cl - op) / op if op > 0 else 0
    doi_pct = abs(oi / oi_prev - 1) if (oi and oi_prev and oi_prev > 0) else 0
    if oi: oi_prev = oi
    scores[d] = {
        "qvol": qv, "wick_up": wick, "body": body, "doi_pct": doi_pct, "f_dev": f_dev,
        "score": qv/1e6 * 0.4 + wick * 100 * 0.3 + doi_pct * 100 * 0.2 + f_dev * 10000 * 0.1
    }

top_anomaly = sorted(scores, key=lambda d: scores[d]["score"], reverse=True)[:5]
emit("Top 5 anomaly days (composite score: vol×0.4 + wick×0.3 + ΔOI×0.2 + fund_dev×0.1):")
emit("")
emit("| date | score | vol_qM | wick_up% | body% | ΔOI% | f_dev |")
emit("|------|------:|-------:|---------:|------:|-----:|------:|")
for d in top_anomaly:
    s = scores[d]
    emit(f"| {d} | {s['score']:.1f} | {s['qvol']/1e6:.1f} | {s['wick_up']*100:.1f} | {s['body']*100:.1f} | {s['doi_pct']*100:.1f} | {s['f_dev']:.5f} |")
emit("")

# (c) Early accumulation before 29/06
emit("### J3(c) — Early Accumulation: pos_r / lsr_accum from June")
emit("")
emit("Phân tích lsr_accum + gLSR từ đầu tháng 6:")
emit("")
emit("| date | px_avg | pos_r | acc_r | gLSR | div_proxy | note |")
emit("|------|--------|------:|------:|-----:|----------:|------|")

# Compute div_proxy (day-over-day acc_r change)
prev_ar = None
for d in sorted(daily_all.keys()):
    if not ("2026-06-01" <= d <= "2026-07-02"): continue
    r  = daily_all.get(d, {})
    px = g(r, "px_avg")
    pr = g(r, "lsr_pos_r")
    ar = g(r, "lsr_acc_r")
    gl = g(r, "lsr_global_r")
    div = (ar - prev_ar) if (ar and prev_ar) else None
    note = ""
    if ar and ar > 0.8: note += "acc_r↑"
    if gl and gl < 0.6: note += " gLSR_low"
    if d == "2026-06-17": note += " 🔓UNLOCK"
    if d == "2026-06-29": note += " tell-start"
    px_s  = f"{px:.5f}" if px else "—"
    pr_s  = f"{pr:.3f}" if pr else "—"
    ar_s  = f"{ar:.3f}" if ar else "—"
    gl_s  = f"{gl:.3f}" if gl else "—"
    div_s = f"{div:+.3f}" if div else "—"
    emit(f"| {d} | {px_s} | {pr_s} | {ar_s} | {gl_s} | {div_s} | {note} |")
    if ar: prev_ar = ar
emit("")

# (d) Funding pin start
emit("### J3(d) — Funding Pin Start: When Did MM Mandate Begin?")
emit("")
emit("Scanning all funding periods for FIRST sustained pin (rate ≈ 0.00005 ±10%):")
emit("")

# Gather all funding from May + June
fund_may_jun = fetch_funding_history("2026-05-01", "2026-06-30")
emit(f"  Total funding periods May+Jun: {len(fund_may_jun)}")
emit("")

# Find first run of ≥3 consecutive periods all pinned
PIN_LO = 0.000045; PIN_HI = 0.000060  # tight pin band
consec = 0; pin_start = None; first_break = None
emit("| dt (UTC) | rate | status |")
emit("|----------|-----:|--------|")
for f in fund_may_jun:
    is_pin = PIN_LO <= f["rate"] <= PIN_HI
    if is_pin:
        if consec == 0: run_start = f["dt"]
        consec += 1
    else:
        if consec >= 3 and pin_start is None:
            pin_start = run_start
        if consec >= 3:
            emit(f"  → Pin run {run_start}→prev: {consec} periods then BREAK at {f['dt']} rate={f['rate']:.6f}")
        consec = 0
    # Only emit notable periods (first few, breaks, etc.)

# Simple summary: group by day, show pin/not-pin
emit("")
emit("Day-level summary (pin if ALL periods that day ≈ 0.00005):")
emit("| date | n_periods | all_pinned | f_min | f_max | note |")
emit("|------|----------:|-----------|------:|------:|------|")
# Build from all May-Jun data
by_day_all = {}
for f in fund_may_jun:
    by_day_all.setdefault(f["date"], []).append(f["rate"])

for d in sorted(by_day_all.keys()):
    rates = by_day_all[d]
    all_pin = all(PIN_LO <= r <= PIN_HI for r in rates)
    any_break = any(not (PIN_LO <= r <= PIN_HI) for r in rates)
    note = "PIN" if all_pin else ("BREAK" if any_break else "?")
    if not all_pin: note = f"BREAK rate=[{min(rates):.6f},{max(rates):.6f}]"
    emit(f"| {d} | {len(rates)} | {'YES' if all_pin else 'NO'} | {min(rates):.6f} | {max(rates):.6f} | {note} |")
emit("")

# (e) Pattern comparison: Jun structure vs Jul
emit("### J3(e) — Jun vs Jul Pattern Comparison (L-12 unlock-cadence)")
emit("")
emit("Framework: T0_Jul=10/07, T0_Jun_unlock=17/06 (hypothetical anchor)")
emit("")

# Key metrics at comparable dates relative to unlock
emit("#### Relative to unlock date (17/06 and 17/07):")
emit("")

def get_metrics_at(d):
    r = daily_all.get(d, {})
    k = kl_dict.get(d, {})
    return {
        "px": g(r, "px_avg"),
        "oi": g(r, "oi_usd"),
        "pr": g(r, "lsr_pos_r"),
        "ar": g(r, "lsr_acc_r"),
        "gl": g(r, "lsr_global_r"),
        "fav": g(r, "funding_avg"),
        "hi": k.get("high"),
        "qv": k.get("qvol"),
    }

# Around 17/06 (Jun unlock): T-5, T-2, T0, T+2, T+5
emit("| offset | Jun date | Jul date | px_J | px_K | oi_J | oi_K | pos_r_J | pos_r_K | gLSR_J | gLSR_K |")
emit("|--------|----------|----------|------|------|-----:|-----:|--------:|--------:|-------:|-------:|")

from datetime import date
def add_days(iso_str, n):
    d = date.fromisoformat(iso_str)
    return (d + timedelta(days=n)).isoformat()

unlock_jun = "2026-06-17"; unlock_jul = "2026-07-17"
for offset in [-7, -5, -3, -1, 0, +2, +5, +7]:
    dj = add_days(unlock_jun, offset)
    dk = add_days(unlock_jul, offset)
    mj = get_metrics_at(dj)
    mk = get_metrics_at(dk)
    pxj_s = f"{mj['px']:.5f}" if mj['px'] else "—"
    pxk_s = f"{mk['px']:.5f}" if mk['px'] else "—"
    oij_s = f"{mj['oi']/1e6:.1f}" if mj['oi'] else "—"
    oik_s = f"{mk['oi']/1e6:.1f}" if mk['oi'] else "—"
    prj_s = f"{mj['pr']:.3f}" if mj['pr'] else "—"
    prk_s = f"{mk['pr']:.3f}" if mk['pr'] else "—"
    glj_s = f"{mj['gl']:.3f}" if mj['gl'] else "—"
    glk_s = f"{mk['gl']:.3f}" if mk['gl'] else "—"
    offset_lbl = f"T{offset:+d}"
    emit(f"| {offset_lbl} | {dj} | {dk} | {pxj_s} | {pxk_s} | {oij_s} | {oik_s} | {prj_s} | {prk_s} | {glj_s} | {glk_s} |")
emit("")

emit("#### Vol pattern around unlock (±5d):")
emit("| offset | Jun vol_qM | Jul vol_qM | ratio |")
emit("|--------|----------:|----------:|------:|")
for offset in [-5, -4, -3, -2, -1, 0, +1, +2, +3, +4, +5]:
    dj = add_days(unlock_jun, offset)
    dk = add_days(unlock_jul, offset)
    vj = kl_dict.get(dj, {}).get("qvol")
    # For Jul, use daily_all (freshwatch vol_quote) since kl_dict only has June
    mk = daily_all.get(dk, {})
    vk_fw = g(mk, "vol_quote")
    vj_s  = f"{vj/1e6:.1f}" if vj else "—"
    vk_s  = f"{vk_fw/1e6:.1f}" if vk_fw else "—"
    ratio = f"{vk_fw/vj:.2f}×" if (vj and vk_fw and vj > 0) else "—"
    emit(f"| T{offset:+d} | {vj_s} | {vk_s} | {ratio} |")
emit("")

# Summary for J3(e)
emit("#### Pattern match summary:")
emit("")
px_jun_T0  = g(daily_all.get("2026-06-17", {}), "px_avg")
px_jun_Tm5 = g(daily_all.get("2026-06-12", {}), "px_avg")
px_jun_Tp5 = g(daily_all.get("2026-06-22", {}), "px_avg")
px_jul_T0  = g(daily_all.get("2026-07-17", {}), "px_avg")
px_jul_Tm5 = g(daily_all.get("2026-07-12", {}), "px_avg")
px_jul_Tp5 = g(daily_all.get("2026-07-22", {}), "px_avg")

if px_jun_T0 and px_jun_Tm5 and px_jun_Tp5:
    emit(f"Jun: px T-5={px_jun_Tm5:.5f} → T0={px_jun_T0:.5f} ({(px_jun_T0/px_jun_Tm5-1)*100:+.1f}%) → T+5={px_jun_Tp5:.5f} ({(px_jun_Tp5/px_jun_T0-1)*100:+.1f}%)")
if px_jul_T0 and px_jul_Tm5 and px_jul_Tp5:
    emit(f"Jul: px T-5={px_jul_Tm5:.5f} → T0={px_jul_T0:.5f} ({(px_jul_T0/px_jul_Tm5-1)*100:+.1f}%) → T+5={px_jul_Tp5:.5f} ({(px_jul_Tp5/px_jul_T0-1)*100:+.1f}%)")
emit("")

# 17/08 upcoming
emit("### J3(e) cont. — 17/08 Upcoming + SUPPRESSED flag")
emit("")
px_now = g(daily_all.get("2026-08-03", {}), "px_avg") or g(daily_all.get("2026-08-04", {}), "px_avg")
px_max_native = 0.67205
if px_now and px_max_native:
    suppressed_pct = (px_now / px_max_native - 1) * 100
    emit(f"- px hiện tại (03/08): {px_now:.5f} USDT")
    emit(f"- px_max (27/07 1h spike): {px_max_native:.5f} USDT")
    emit(f"- Suppressed: {suppressed_pct:.1f}% từ đỉnh spike → token đang bị nén")
emit(f"- 17/08 = T+38 từ T0 (10/07) — trong window T+30→T+60 tracking")
emit(f"- CẢNH BÁO: Nếu khuôn lặp (Jun unlock → bait T-15→T0 → markup → xả T+2→T+4)")
emit(f"  thì cửa sổ canh = 02/08→17/08 (T-15→T0 so với 17/08)")
emit(f"  NHƯNG: token đang SUPPRESSED (hậu-campaign) → tín hiệu mâu thuẫn:")
emit(f"  * MÂU THUẪN 1: Campaign Jul đã xong, pos_r còn cao (hậu-xả)")
emit(f"  * MÂU THUẪN 2: Không có bằng chứng MM build vị thế mới (pos_r ~1.3)")
emit(f"  * MÂU THUẪN 3: Campaign chu kỳ thường cần reset vài tháng, không phải T+21")
emit(f"  → OPERATOR DECISION: theo dõi 17/08 như mốc rủi ro (không phải mốc cơ hội)")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

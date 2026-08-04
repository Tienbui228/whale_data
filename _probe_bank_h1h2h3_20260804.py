#!/usr/bin/env python3
"""PROBE BANK H1/H2/H3: verify window 20-27/07 + OI accumulate + VWAP exit.

H1: px_max verify (native 1h store) + pos_r/gLSR quanh 24-26/07
H2: OI accumulate 25/06-09/07 + funding PnL estimate
H3: VWAP exit 19-21/07 (pos_r sap manh) + MM multiple thuc

Data: VPS klines_1h (SSH read) + freshwatch daily (local)
Output: docs/reports/_probe_bank_h1h2h3_20260804.md
"""
import csv, io, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_bank_h1h2h3_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def g(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

def ms_to_dt(ms):
    return datetime.utcfromtimestamp(int(ms)/1000).strftime("%Y-%m-%d %H:%M")

# ─── Load freshwatch BANK ─────────────────────────────────────────────────────
rows = []
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "BANKUSDT":
            r["date_str"] = r.get("date", "")
            rows.append(r)
rows.sort(key=lambda r: r["date_str"])
daily = {r["date_str"]: r for r in rows}

emit("# PROBE BANK H1/H2/H3 — Verify + PnL Reconstruction")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"Daily rows: {len(rows)}")
emit("")

# ─── Fetch Binance fapi hourly klines (supplement VPS store) ─────────────────
FAPI = "https://fapi.binance.com"

def fetch_klines_1h(start_iso: str, end_iso: str) -> list:
    """Fetch BANKUSDT hourly klines from Binance fapi."""
    def dt_ms(s): return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    t0 = dt_ms(start_iso); t1 = dt_ms(end_iso)
    url = (f"{FAPI}/fapi/v1/klines?symbol=BANKUSDT&interval=1h"
           f"&startTime={t0}&endTime={t1}&limit=500")
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        emit(f"  [FETCH ERROR] {e}")
        return []

def klines_to_rows(kl):
    out = []
    for k in kl:
        out.append({
            "ms":    int(k[0]),
            "dt":    ms_to_dt(int(k[0])),
            "open":  float(k[1]),
            "high":  float(k[2]),
            "low":   float(k[3]),
            "close": float(k[4]),
            "vol":   float(k[5]),
            "qvol":  float(k[7]),
            "taker_base": float(k[9]),
            "taker_quote": float(k[10]),
        })
    return out

# ─── H1: Verify 20-27/07 ──────────────────────────────────────────────────────
emit("## H1 — Verify Window 20-27/07 (source: Binance fapi native)")
emit("")

kl_20_27 = fetch_klines_1h("2026-07-20", "2026-07-28")
h1_rows  = klines_to_rows(kl_20_27)

emit(f"Fetched {len(h1_rows)} hourly klines 20-28/07")
emit("")

# (a) px_max verify
if h1_rows:
    px_max_h = max(h1_rows, key=lambda x: x["high"])
    emit(f"### H1(a) — px_max verify")
    emit(f"- px_max (high): **{px_max_h['high']:.5f}** USDT tại {px_max_h['dt']} UTC")
    emit(f"- px_max (close-based): **{max(h['close'] for h in h1_rows):.5f}** USDT")
    emit(f"- Freshwatch 26/07 px_avg: {g(daily.get('2026-07-26',{}), 'px_avg') or '?'}")
    emit(f"- Source: Binance fapi /fapi/v1/klines (native, venue=binance_perp)")
    emit("")

# (b) pos_r 20-27/07 daily
emit("### H1(b) — Daily pos_r/acc_r/gLSR 20-27/07")
emit("")
emit("| date | px_avg | OI_M | pos_r | acc_r | gLSR | fn |")
emit("|------|--------|-----:|------:|------:|-----:|----:|")
for d in sorted(daily.keys()):
    if not ("2026-07-20" <= d <= "2026-07-27"): continue
    r = daily[d]
    fn = g(r, "funding_n")
    px = g(r, "px_avg")
    oi = g(r, "oi_usd")
    pr = g(r, "lsr_pos_r")
    ar = g(r, "lsr_acc_r")
    gl = g(r, "lsr_global_r")
    px_s = f"{px:.5f}" if px else "—"
    oi_s = f"{oi/1e6:.2f}" if oi else "—"
    pr_s = f"{pr:.3f}" if pr else "—"
    ar_s = f"{ar:.3f}" if ar else "—"
    gl_s = f"{gl:.3f}" if gl else "—"
    fn_s = str(int(fn)) if fn else "?"
    emit(f"| {d} | {px_s} | {oi_s} | {pr_s} | {ar_s} | {gl_s} | {fn_s} |")

emit("")

# (c) gLSR slope flip: find bottom and slope sign change
emit("### H1(c) — gLSR day quanh 24-27/07 (hourly proxy): test co-d-flip")
emit("")
emit("Gia thuyet dat truoc: slope dao dau 26-28/07.")
emit("")

# gLSR từ freshwatch daily
gl_series = [(d, g(daily[d], "lsr_global_r")) for d in sorted(daily.keys()) if g(daily.get(d,{}), "lsr_global_r")]
gl_dict   = dict(gl_series)

# Find gLSR minimum in POST phase
post_gl = [(d, v) for d, v in gl_series if d >= "2026-07-20"]
if post_gl:
    gl_min_d, gl_min_v = min(post_gl, key=lambda x: x[1])
    emit(f"- gLSR min POST (20/07+): {gl_min_v:.3f} ({gl_min_d})")

# Day-by-day gLSR with slope for full POST window
emit("")
emit("| date | gLSR | d_gLSR | slope_note |")
emit("|------|------|--------|-----------|")
prev_gl = None
for d, gl in sorted(gl_series):
    if d < "2026-07-19": continue
    d_gl = gl - prev_gl if prev_gl else 0
    slope = "UP" if d_gl > 0.02 else ("DOWN" if d_gl < -0.02 else "FLAT")
    flip  = " ← SLOPE FLIP" if (prev_gl and ((d_gl > 0) != (prev_slope_was_up if 'prev_slope_was_up' in dir() else True))) else ""
    try:
        flip = " ← FLIP UP" if (d_gl > 0 and prev_gl_delta < 0) else (" ← FLIP DOWN" if (d_gl < 0 and prev_gl_delta > 0) else "")
    except: flip = ""
    emit(f"| {d} | {gl:.3f} | {d_gl:+.3f} | {slope}{flip} |")
    prev_gl_delta = d_gl
    prev_gl = gl

emit("")

# H1: Hourly klines table 24-27/07 (key window)
emit("### H1 — Hourly klines 24-27/07 (source: Binance fapi native)")
emit("")
emit("| dt (UTC) | open | high | low | close | vol_K | qvol_M | taker% |")
emit("|----------|------|------|-----|-------|------:|------:|-------:|")
for h in h1_rows:
    d = h["dt"][:10]
    if not ("2026-07-24" <= d <= "2026-07-27"): continue
    tk_pct = h["taker_quote"] / h["qvol"] * 100 if h["qvol"] > 0 else 0
    emit(f"| {h['dt']} | {h['open']:.5f} | {h['high']:.5f} | {h['low']:.5f} | {h['close']:.5f} | {h['vol']/1000:.1f}K | {h['qvol']/1e6:.2f}M | {tk_pct:.1f}% |")

emit("")

# ─── H2: OI accumulate 25/06→09/07 ───────────────────────────────────────────
emit("## H2 — OI Accumulate 25/06→09/07 + Funding PnL Estimate")
emit("")

pre_dates = [d for d in sorted(daily.keys()) if "2026-06-25" <= d <= "2026-07-09"]
emit("### H2(a) — Daily OI + pos_r + ΔOI trong PRE phase")
emit("")
emit("| date | OI_M | dOI_M | pos_r | acc_r | f_avg | fn | note |")
emit("|------|-----:|------:|------:|------:|------:|----:|------|")

oi_prev = None
for d in pre_dates:
    r   = daily.get(d, {})
    oi  = g(r, "oi_usd")
    pr  = g(r, "lsr_pos_r")
    ar  = g(r, "lsr_acc_r")
    fav = g(r, "funding_avg")
    fn  = g(r, "funding_n")
    oi_M  = oi/1e6 if oi else None
    doi   = f"{(oi_M - oi_prev):+.2f}" if (oi_M and oi_prev) else "—"
    note  = "OI↑ pos_r↑" if (oi_M and oi_prev and oi_M > oi_prev and pr and g(daily.get(pre_dates[pre_dates.index(d)-1] if pre_dates.index(d) > 0 else d, {}), "lsr_pos_r") and pr > g(daily.get(pre_dates[pre_dates.index(d)-1] if pre_dates.index(d) > 0 else d, {}), "lsr_pos_r")) else ""
    oi_s  = f"{oi_M:.2f}" if oi_M else "—"
    pr_s  = f"{pr:.3f}" if pr else "—"
    ar_s  = f"{ar:.3f}" if ar else "—"
    fav_s = f"{fav:.5f}" if fav is not None else "—"
    fn_s  = str(int(fn)) if fn else "?"
    emit(f"| {d} | {oi_s} | {doi} | {pr_s} | {ar_s} | {fav_s} | {fn_s} | {note} |")
    if oi_M: oi_prev = oi_M

emit("")

# OI range in PRE
oi_pre_vals = [g(daily.get(d,{}), "oi_usd") for d in pre_dates if g(daily.get(d,{}), "oi_usd")]
if oi_pre_vals:
    oi_pre_min = min(oi_pre_vals); oi_pre_max = max(oi_pre_vals)
    oi_markup_peak = g(daily.get("2026-07-19",{}), "oi_usd") or 0
    emit(f"- OI PRE range: {oi_pre_min/1e6:.2f}M → {oi_pre_max/1e6:.2f}M")
    emit(f"- OI peak MARKUP (19/07): {oi_markup_peak/1e6:.2f}M")
    emit(f"- Net OI build PRE→MARKUP: {(oi_markup_peak - oi_pre_min)/1e6:+.2f}M")
emit("")

# Funding PnL estimate
emit("### H2(b) — Funding PnL Estimate")
emit("")
emit("Gia thuyet: MM net-long ~3-5M USD (oi_pre range) trong 4h interval.")
emit("Funding BANK ghim [4e-5, 6e-5]: MM net-long = MM nhan funding khi rate duong.")
emit("  → Khi f_avg > 0: MM (long) nhan tu MM (short) hoac crowd-short")
emit("  → Khi f_avg = 0 hoac f_min = -x: co ky MM (long) TRA cho short")
emit("")

# Collect funding data
fund_rows = []
for d in sorted(daily.keys()):
    if d > "2026-07-19": continue  # chỉ PRE+MARKUP (khi OI còn xây)
    r   = daily.get(d, {})
    fav = g(r, "funding_avg")
    fmin = g(r, "funding_min")
    fmax = g(r, "funding_max")
    fn   = g(r, "funding_n")
    oi   = g(r, "oi_usd")
    if fav is None or oi is None: continue
    fund_rows.append((d, fav, fmin, fmax, fn, oi))

# PnL per day: assume MM holds LONG_SIZE notional
LONG_SIZE_LO = 3e6  # 3M USD
LONG_SIZE_HI = 5e6  # 5M USD

total_fund_lo = 0.0; total_fund_hi = 0.0
emit("| date | f_avg | fn | oi_M | fund_income_lo (3M) | fund_income_hi (5M) |")
emit("|------|------:|---:|-----:|-------------------:|-------------------:|")
for d, fav, fmin, fmax, fn, oi in fund_rows:
    if d < "2026-06-27": continue
    periods = int(fn) if fn else 6
    # funding income = f_avg * periods * LONG_SIZE (positive = receive)
    fi_lo = fav * periods * LONG_SIZE_LO
    fi_hi = fav * periods * LONG_SIZE_HI
    total_fund_lo += fi_lo
    total_fund_hi += fi_hi
    emit(f"| {d} | {fav:.5f} | {periods} | {oi/1e6:.2f} | ${fi_lo:+.0f} | ${fi_hi:+.0f} |")

emit(f"| **TOTAL** | | | | **${total_fund_lo:+,.0f}** | **${total_fund_hi:+,.0f}** |")
emit("")
emit(f"- Tong funding income/cost MM (27/06→19/07): ${total_fund_lo:+,.0f} → ${total_fund_hi:+,.0f}")
emit(f"- Funding income nho so voi markup gain → PnL chu dao = gia, khong phai funding")
emit("")

# ─── H3: VWAP exit + MM multiple ─────────────────────────────────────────────
emit("## H3 — VWAP Exit + MM Multiple Thuc")
emit("")
emit("Exit window: 19-20/07 (pos_r sap manh 1.61→1.09) — fapi 1h klines")
emit("")

# Fetch 1h klines 19-21/07
kl_exit = fetch_klines_1h("2026-07-19", "2026-07-22")
h3_rows = klines_to_rows(kl_exit)

emit(f"Fetched {len(h3_rows)} klines 19-21/07")
emit("")

# VWAP build: từ PRE phase, các ngày OI tăng + pos_r tăng
# Approximate build window: 25/06→13/07 (before pos_r peak drop)
# Use daily data for build VWAP

emit("### H3(a) — Build VWAP (PRE + early MARKUP 25/06→12/07)")
emit("")
build_dates = [d for d in sorted(daily.keys()) if "2026-06-25" <= d <= "2026-07-12"]
build_vol_total = 0.0; build_qvol_total = 0.0
emit("| date | px_avg | vol_quote_M | note |")
emit("|------|--------|------------|------|")
for d in build_dates:
    r    = daily.get(d, {})
    px   = g(r, "px_avg")
    volq = g(r, "vol_quote")
    if not (px and volq): continue
    build_vol_total  += volq / px  # approx base vol
    build_qvol_total += volq
    emit(f"| {d} | {px:.5f} | {volq/1e6:.2f} | |")

build_vwap = build_qvol_total / build_vol_total if build_vol_total > 0 else 0
emit(f"")
emit(f"- Build VWAP (daily approx): **{build_vwap:.5f} USDT**")
emit(f"- Total quote vol build window: {build_qvol_total/1e6:.1f}M USDT")
emit("")

# Exit VWAP: 19-21/07 from hourly (pos_r crash window)
emit("### H3(b) — Exit VWAP (1h klines 19-21/07, pos_r sap window)")
emit("")
emit("| dt (UTC) | open | high | low | close | qvol_M | taker% |")
emit("|----------|------|------|-----|-------|------:|-------:|")
exit_qvol = 0.0; exit_bvol = 0.0
for h in h3_rows:
    d = h["dt"][:10]
    tk_pct = h["taker_quote"] / h["qvol"] * 100 if h["qvol"] > 0 else 0
    emit(f"| {h['dt']} | {h['open']:.5f} | {h['high']:.5f} | {h['low']:.5f} | {h['close']:.5f} | {h['qvol']/1e6:.2f} | {tk_pct:.1f}% |")
    exit_qvol += h["qvol"]
    exit_bvol += h["vol"]

exit_vwap = exit_qvol / exit_bvol if exit_bvol > 0 else 0
emit("")
emit(f"- Exit VWAP (19-21/07 window): **{exit_vwap:.5f} USDT**")
emit(f"- Total vol 19-21/07: {exit_qvol/1e6:.1f}M USDT (3 ngay)")
emit("")

# MM multiple
emit("### H3(c) — MM Multiple Thuc")
emit("")
px_T0  = g(daily.get("2026-07-10",{}), "px_avg") or 0.03773
px_max = 0.37632  # từ H1 verify (fapi high)

multiple_raw  = px_max / build_vwap if build_vwap else 0
multiple_vwap = exit_vwap / build_vwap if build_vwap else 0
ret_holder    = (px_max / px_T0 - 1) * 100

emit(f"| anchor | px | so sanh |")
emit(f"|--------|-----|--------|")
emit(f"| Build VWAP (25/06-12/07 daily approx) | {build_vwap:.5f} | — |")
emit(f"| px_T0 (10/07 open) | {px_T0:.5f} | ref |")
emit(f"| px_max (26/07 1h high native) | {px_max:.5f} | — |")
emit(f"| Exit VWAP (19-21/07 1h) | {exit_vwap:.5f} | — |")
emit(f"| px cuoi (03/08) | {g(daily.get('2026-08-03',{}), 'px_avg') or 0:.5f} | — |")
emit("")
emit(f"| metric | gia tri | y nghia |")
emit(f"|--------|---------|---------|")
emit(f"| Ret nguoi nam giu T0→max | {ret_holder:+.1f}% | +897% (giay tren bieu do) |")
emit(f"| MM multiple (max/build_vwap) | {multiple_raw:.2f}x | **{(multiple_raw-1)*100:.0f}%** — nhu the nay neu xuat vao dinh |")
emit(f"| MM exit VWAP / build VWAP | {multiple_vwap:.2f}x | **{(multiple_vwap-1)*100:.0f}%** — multiple THUC cua MM (xuat trong 3 ngay 19-21/07) |")
emit(f"| Gia tri 2 so: holder vs MM | {ret_holder:.0f}% vs {(multiple_vwap-1)*100:.0f}% | MM EXIT SOM HOM, holder tren giay cao hon |")
emit("")

# PnL reconstruction table
emit("### H3(d) — PnL Reconstruction Table (MM — gia thuyet)")
emit("")
POSITION_M = 4.0  # assume 4M USD average position
fund_pnl   = (total_fund_lo + total_fund_hi) / 2
price_pnl_lo = POSITION_M * (exit_vwap / build_vwap - 1) if build_vwap else 0
price_pnl_hi = POSITION_M * (px_max / build_vwap - 1) if build_vwap else 0  # nếu thoát đỉnh

emit(f"Gia thuyet: MM giu 4M USD notional long, build VWAP {build_vwap:.5f}, exit VWAP {exit_vwap:.5f}")
emit("")
emit(f"| chan | PnL_USD | ghi chu |")
emit(f"|------|---------|---------|")
emit(f"| Gia (price) — exit VWAP | ${POSITION_M * (exit_vwap/build_vwap - 1) * 1e6 / 1e6:.2f}M | 4M * ({exit_vwap:.5f}/{build_vwap:.5f}-1) |")
emit(f"| Gia (price) — neu xuat dinh | ${POSITION_M * (px_max/build_vwap - 1) * 1e6 / 1e6:.2f}M | upper bound (xuat vao 26/07) |")
emit(f"| Funding (27/06-19/07 avg) | ${fund_pnl/1e6:.3f}M | nho, thu phu |")
emit(f"| **TONG (exit VWAP chan)** | **${POSITION_M * (exit_vwap/build_vwap - 1) + fund_pnl/1e6:.2f}M** | |")
emit("")
emit(f"**Diem day cua H3**: MM multiple THUC (exit VWAP / build VWAP) = {multiple_vwap:.2f}x != +897% tren bieu do.")
emit(f"Nguoi nam giu tu T0 den max: +897% — nhung MM xuat TRONG vol cua cac ngay pos_r sap.")
emit(f"Hai con so nay KHAC nhau vi MM khong phat ra 1 lenh vao dinh — ho xuat dan trong high-vol window.")
emit("")

# ─── G3 cập nhật: pos_r flat 1.1-1.3 answer ─────────────────────────────────
emit("## H1(b) Follow-up — pos_r flat 1.1-1.3 suot chan +550% cuoi?")
emit("")
emit("Xem lai daily 20-27/07:")
for d in sorted(daily.keys()):
    if not ("2026-07-20" <= d <= "2026-07-27"): continue
    r  = daily.get(d, {})
    pr = g(r, "lsr_pos_r")
    px = g(r, "px_avg")
    gl = g(r, "lsr_global_r")
    oi = g(r, "oi_usd")
    if pr and px:
        oi_s    = f"{oi/1e6:.2f}" if oi else "?"
        ref20   = g(daily.get("2026-07-20", {}), "px_avg")
        ret_pct = f"{(px/ref20-1)*100:+.1f}" if ref20 else "0.0"
        emit(f"  {d}: pos_r={pr:.3f}, px={px:.5f} ({ret_pct}% vs 20/07), OI={oi_s}M")
emit("")
emit("Nhan xet: pos_r 1.091→1.317 trong khi px di tu 0.264→0.376 (+42.5%).")
emit("pos_r THUC SU di ngang 1.1-1.3 suot chan +550% cuoi (tu 26M px cuoi day MARKUP).")
emit("Day xac nhan: crowd KHONG dung them (pos_r khong tang) — MM xuat dan, crowd cung xuat/hold flat.")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")

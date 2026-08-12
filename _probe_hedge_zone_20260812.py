"""
Hedge zone reconstruction + trạng thái hiện tại: CLO, ESPORTS, GUA
5 chiều: [1] OI-build zone  [2] Short active/closed  [3] Funding regime
         [4] px_now vs zone  [5] Suppressor check
"""
import sys, math, csv, pathlib
from statistics import median

sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
from fw_loader_utils import load_fw_csvs, taker_scale_check_df

EXPORT_DIR = pathlib.Path("data/export")

TARGETS = {
    "CLOUSDT":     "2026-05-26",
    "ESPORTSUSDT": "2026-06-07",
    "GUAUSDT":     "2025-01-01",  # full lifetime
}

# ── Load all freshwatch_daily ─────────────────────────────────────────────────
df_all = load_fw_csvs(EXPORT_DIR, up_to_date="2026-08-11", lookback_days=450)
df_all = taker_scale_check_df(df_all)

def _f(v):
    try:
        x = float(v)
        return x if x == x else float("nan")
    except:
        return float("nan")

def _pct(a, b):
    if b and b != 0:
        return (a - b) / abs(b) * 100
    return float("nan")

def analyze(sym, from_date):
    rows = df_all[(df_all["symbol"] == sym) & (df_all["date"] >= from_date)].copy()
    rows = rows.sort_values("date").reset_index(drop=True)
    if rows.empty:
        print(f"\n{'='*60}\n{sym}: NO DATA from {from_date}\n")
        return

    # Build per-day dict list
    days = []
    for _, r in rows.iterrows():
        days.append({
            "date":       r["date"],
            "px":         _f(r.get("px_avg")),
            "oi":         _f(r.get("oi_usd")),
            "lsr_pos":    _f(r.get("lsr_pos_r")),
            "lsr_acc":    _f(r.get("lsr_acc_r")),
            "lsr_global": _f(r.get("lsr_global_r")),
            "fund_avg":   _f(r.get("funding_avg")),
            "fund_min":   _f(r.get("funding_min")),
            "taker":      _f(r.get("taker_buy_pct")),
        })

    # [1] OI delta + ramp detection
    for i in range(len(days)):
        if i == 0:
            days[i]["oi_delta"] = float("nan")
        else:
            prev = days[i-1]["oi"]
            cur  = days[i]["oi"]
            days[i]["oi_delta"] = cur - prev if (cur==cur and prev==prev) else float("nan")

    # Find all positive-OI-delta windows
    ramp_rows = [d for d in days if d["oi_delta"]==d["oi_delta"] and d["oi_delta"] > 0]
    all_delta = [d for d in days if d["oi_delta"]==d["oi_delta"]]

    # Peak OI-build day
    if ramp_rows:
        peak = max(ramp_rows, key=lambda d: d["oi_delta"])
    else:
        peak = None

    # OI-weighted avg_px over ALL positive-delta days
    tot_delta = sum(d["oi_delta"] for d in ramp_rows if d["px"]==d["px"])
    if tot_delta > 0:
        vwap = sum(d["oi_delta"] * d["px"] for d in ramp_rows
                   if d["px"]==d["px"] and d["oi_delta"]==d["oi_delta"]) / tot_delta
    else:
        vwap = float("nan")

    px_in_ramp = [d["px"] for d in ramp_rows if d["px"]==d["px"]]
    ramp_hi = max(px_in_ramp) if px_in_ramp else float("nan")
    ramp_lo = min(px_in_ramp) if px_in_ramp else float("nan")

    # Net cumulative OI build (sum of positive deltas)
    cum_build = sum(d["oi_delta"] for d in ramp_rows)

    # Net cumulative OI drop (sum of negative deltas = position unwinding)
    cum_drain = sum(d["oi_delta"] for d in all_delta if d["oi_delta"] < 0)

    # [2] Current short status
    last = days[-1]
    lsr_pos_now = last["lsr_pos"]
    lsr_acc_now = last["lsr_acc"]
    oi_now = last["oi"]
    px_now = last["px"]
    date_now = last["date"]

    # Is short active? pos < 1 = top accounts net short
    short_active = lsr_pos_now < 1.0 if lsr_pos_now == lsr_pos_now else None

    # OI vs peak OI
    oi_vals = [d["oi"] for d in days if d["oi"]==d["oi"]]
    oi_peak = max(oi_vals) if oi_vals else float("nan")
    oi_peak_date = days[[d["oi"] for d in days].index(oi_peak)]["date"] if oi_vals else "?"

    # [3] Funding regime (last 7 days)
    last7 = [d for d in days[-7:] if d["fund_avg"]==d["fund_avg"]]
    fund_avg7 = sum(d["fund_avg"] for d in last7) / len(last7) if last7 else float("nan")
    fund_neg_days = sum(1 for d in last7 if d["fund_avg"] < 0)
    fund_min_all = min(d["fund_min"] for d in days if d["fund_min"]==d["fund_min"]) if days else float("nan")

    # Pinned = positive and tight (< 0.03% range)
    fund_range = max((d["fund_avg"] for d in last7 if d["fund_avg"]==d["fund_avg"]), default=float("nan")) - \
                 min((d["fund_avg"] for d in last7 if d["fund_avg"]==d["fund_avg"]), default=float("nan"))
    funding_pinned = (fund_avg7 > 0) and (fund_range < 0.0003)
    funding_neg_div = fund_neg_days >= 4  # majority negative = distribution

    # [4] px_now vs vwap hedge zone
    pct_from_zone = _pct(px_now, vwap)

    # Retest count: days where price came within 5% of vwap AND was above vwap
    retests = 0
    if vwap == vwap:
        in_zone = False
        for d in days:
            px = d["px"]
            if px != px:
                continue
            near = abs(_pct(px, vwap)) <= 5.0  # within 5% of zone
            if near and not in_zone:
                retests += 1
            in_zone = near

    # [5] Suppressor: funding_pinned or OI floor + pos-rerate
    lsr_pos_vals = [d["lsr_pos"] for d in days[-14:] if d["lsr_pos"]==d["lsr_pos"]]
    pos_rising = (len(lsr_pos_vals) >= 2 and
                  lsr_pos_vals[-1] > lsr_pos_vals[0] and
                  lsr_pos_vals[-1] > 1.0)  # pos_r > 1 = longs gaining
    suppressor_flag = funding_pinned or pos_rising

    # ── Print ────────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"{sym}  |  data {from_date} → {date_now}  ({len(days)} rows)")
    print(f"{'='*65}")

    print(f"\n[1] OI-BUILD ZONE")
    print(f"  Peak OI-build day : {peak['date'] if peak else '?'}  delta=+${peak['oi_delta']:,.0f}" if peak else "  No build days")
    print(f"  OI peak (total)   : ${oi_peak:,.0f} on {oi_peak_date}")
    print(f"  Cum net build     : +${cum_build:,.0f}")
    print(f"  Cum net drain     : ${cum_drain:,.0f}")
    print(f"  OI-weighted VWAP  : {vwap:.6f}")
    print(f"  Range during ramp : lo={ramp_lo:.6f}  hi={ramp_hi:.6f}")
    print(f"  px_now ({date_now})  : {px_now:.6f}")
    print(f"  Δ px_now vs VWAP  : {pct_from_zone:+.1f}%")

    print(f"\n[2] SHORT STATUS")
    lsp_str = f"{lsr_pos_now:.4f}" if lsr_pos_now==lsr_pos_now else "NaN"
    lac_str = f"{lsr_acc_now:.4f}" if lsr_acc_now==lsr_acc_now else "NaN"
    verdict = "ACTIVE (pos<1, net short)" if short_active else \
              ("CLOSED/FLIPPED (pos≥1)" if short_active is False else "UNKNOWN")
    print(f"  lsr_pos_r now     : {lsp_str}  → {verdict}")
    print(f"  lsr_acc_r now     : {lac_str}")
    print(f"  oi_usd now        : ${oi_now:,.0f}")
    print(f"  oi_now / oi_peak  : {oi_now/oi_peak*100:.1f}%" if oi_peak>0 and oi_now==oi_now else "")

    print(f"\n[3] FUNDING REGIME (last 7d)")
    print(f"  fund_avg 7d       : {fund_avg7*100:+.4f}%")
    print(f"  neg-fund days     : {fund_neg_days}/7")
    print(f"  fund_range 7d     : {fund_range*100:.4f}%")
    print(f"  fund_min all-time : {fund_min_all*100:+.4f}%")
    regime = "DISTRIBUTION (neg-fund majority)" if funding_neg_div else \
             ("PINNED/ACCUM (positive tight)" if funding_pinned else "MIXED/NEUTRAL")
    print(f"  Regime            : {regime}")

    print(f"\n[4] PRICE vs HEDGE ZONE")
    print(f"  VWAP hedge        : {vwap:.6f}")
    print(f"  px_now            : {px_now:.6f}  ({pct_from_zone:+.1f}% từ VWAP)")
    above = "ABOVE zone (already at/past hedge)" if px_now > vwap else "BELOW zone (approaching)"
    trigger = "WATCH (>30% from zone)" if abs(pct_from_zone) > 30 else \
              "IN ZONE (<5%)" if abs(pct_from_zone) <= 5 else "NEAR ZONE (5-30%)"
    print(f"  Position          : {above}")
    print(f"  Entry trigger     : {trigger}")
    print(f"  Retest approaches : {retests} (within 5% of VWAP zone)")

    print(f"\n[5] SUPPRESSOR")
    print(f"  funding_pinned    : {'YES → CỜ ĐỎ accumulation' if funding_pinned else 'no'}")
    print(f"  pos_rising >1     : {'YES → CỜ ĐỎ long rerate' if pos_rising else 'no'}")
    print(f"  SUPPRESSOR ACTIVE : {'⚠ YES — CHECK ON pattern' if suppressor_flag else 'CLEAR'}")

    # LSR timeline (last 10 days)
    print(f"\n  LSR tail (last 10 days):")
    print(f"  {'date':>12}  {'lsr_pos':>8}  {'lsr_acc':>8}  {'fund_avg%':>10}  {'oi_usd':>14}  {'px':>10}")
    for d in days[-10:]:
        fp = f"{d['fund_avg']*100:+.4f}" if d['fund_avg']==d['fund_avg'] else "  NaN  "
        lp = f"{d['lsr_pos']:.4f}" if d['lsr_pos']==d['lsr_pos'] else "  NaN"
        la = f"{d['lsr_acc']:.4f}" if d['lsr_acc']==d['lsr_acc'] else "  NaN"
        oi = f"{d['oi']:,.0f}" if d['oi']==d['oi'] else "NaN"
        px = f"{d['px']:.6f}" if d['px']==d['px'] else "NaN"
        print(f"  {d['date']:>12}  {lp:>8}  {la:>8}  {fp:>10}  {oi:>14}  {px:>10}")

for sym, from_date in TARGETS.items():
    try:
        analyze(sym, from_date)
    except Exception as e:
        print(f"\nERROR {sym}: {e}")
        import traceback; traceback.print_exc()

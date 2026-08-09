"""Full signal trace for FF — why GOM opened 2026-08-01 and Q1=$1.988M.

Outputs per-day table: A1-A5, B1-B4, supp flags, OI/pos_r/taker/funding/vol,
Q1 delta, running VWAP. Includes pre-open context (07-28→07-31).
"""
import sys, math
from pathlib import Path
sys.path.insert(0, "scripts")

from fw_loader_utils import (
    load_fw_csvs, build_token_days, enrich_token_days,
    load_funding_intervals, taker_scale_check_df,
)
import gom_scan as gs
from scanner.screener.signals import (
    load_thresholds, lsr_accum, stealth_grind, s3_eve,
    pos_rerate, funding_unpin, hedge_structure,
    funding_pinned, funding_pinned_strong, absorption,
    dist_wall, lsr_dist, funding_neg_div, funding_extreme,
    decay, post_climax, crowd_flush, oi_ignition,
)

STORE    = Path("data/export")
CONFIG   = Path("data/config")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

TARGET = "2026-08-07"
df = load_fw_csvs(STORE, TARGET, lookback_days=45)
df = taker_scale_check_df(df)

days, _ = build_token_days(df, "FFUSDT", "2026-07-15", TARGET, intervals)
enrich_token_days(days)

# Replay chain state
chain: dict = {}
print("=== FF GOM SIGNAL TRACE — context 07-28 → 08-07 ===")
print()
hdr = (f"{'Date':<12} {'gom':^4} {'A1':^4}{'A2':^4}{'A3':^4}{'A4':^4}{'A5':^4}"
       f" {'B1':^4}{'B2':^4}{'B3':^4}{'B4':^4}"
       f" {'supp':^5} {'slope':^6}"
       f" {'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'div':>5}"
       f" {'OI_usd':>11} {'ΔOI⁺':>10} {'taker':>6} {'f_avg':>8} {'fn':>3}"
       f" {'px':>8} {'vol_q':>11}"
       f" {'Q1_run':>11} {'VWAP_run':>10}")
print(hdr)
print("-" * len(hdr))

show_from = "2026-07-28"
q1_run  = 0.0
vwap_n  = 0.0
vwap_d  = 0.0
vwap_fb = False

for i, d in enumerate(days):
    dt = d.get("date", "")

    skip = d.get("_skip_eval") or d.get("_suspect")
    if skip:
        result = gs._false_result()
    else:
        result = gs.eval_gom(days, i, cfg, sc)

    chain = gs.update_chain(chain, "FFUSDT", days, i, result, cfg, sc)

    if dt < show_from:
        continue

    ga   = result.get("gom_a", {})
    gb   = result.get("gom_b", {})
    supp = result.get("supp_dq", {})
    pd_  = result.get("perday_dq", {})
    gom  = result.get("gom_day", False)

    a1 = ga.get("A1", False)
    a2 = ga.get("A2", False)
    a3 = ga.get("A3", False)
    a4 = ga.get("A4", False)
    a5 = ga.get("A5", False)
    b1 = gb.get("B1", False)
    b2 = gb.get("B2", False)
    b3 = gb.get("B3", False)
    b4 = gb.get("B4", False)

    any_supp  = any(v for v in supp.values())
    slope_dq  = pd_.get("slope_dq", False)
    fired_supp = [k for k, v in supp.items() if v]

    pos_r  = d.get("lsr_pos", float("nan"))
    acc_r  = d.get("lsr_acc", float("nan"))
    glsr   = d.get("lsr_global", float("nan"))
    div_r  = pos_r / acc_r if (not math.isnan(acc_r) and acc_r != 0) else float("nan")
    oi     = d.get("oi_usd", float("nan"))
    taker  = d.get("taker_buy_pct", float("nan"))
    f_avg  = d.get("funding_avg", float("nan"))
    fn     = d.get("funding_n", 0)
    px     = d.get("avg_px", float("nan"))
    vol    = d.get("vol_quote", float("nan"))
    d3     = d.get("d_pos_3d", float("nan"))

    # Track Q1 and VWAP manually (mirror update_chain logic)
    if gom and not any_supp:
        oi_prev = days[i-1].get("oi_usd", float("nan")) if i > 0 else float("nan")
        if not math.isnan(oi) and not math.isnan(oi_prev):
            delta_oi = max(oi - oi_prev, 0.0)
        else:
            delta_oi = 0.0
        q1_run += delta_oi
        if not math.isnan(px) and delta_oi > 0:
            vwap_n += delta_oi * px
            vwap_d += delta_oi
        elif not math.isnan(px) and delta_oi == 0 and not math.isnan(vol) and vol > 0:
            vwap_n += vol * px
            vwap_d += vol
            vwap_fb = True
    else:
        delta_oi = float("nan")

    vwap_now = vwap_n / vwap_d if vwap_d > 0 else float("nan")

    def tf(x): return "T" if x else "F"
    def fn_f(x, fmt=".4f"): return f"{x:{fmt}}" if not math.isnan(x) else "N/A"
    def fi(x): return f"{x:,.0f}" if not math.isnan(x) else "N/A"

    supp_tag = "+".join(fired_supp)[:5] if fired_supp else ("slp" if slope_dq else "—")

    row = (
        f"{dt:<12} {tf(gom):^4} {tf(a1):^4}{tf(a2):^4}{tf(a3):^4}{tf(a4):^4}{tf(a5):^4}"
        f" {tf(b1):^4}{tf(b2):^4}{tf(b3):^4}{tf(b4):^4}"
        f" {supp_tag:^5} {'slp' if slope_dq else '—':^6}"
        f" {fn_f(pos_r):>6} {fn_f(acc_r):>6} {fn_f(glsr):>6} {fn_f(div_r, '.3f'):>5}"
        f" {fi(oi):>11} {fi(delta_oi):>10} {fn_f(taker, '.1f'):>6} {fn_f(f_avg, '.2e'):>8} {fn:>3}"
        f" {fn_f(px, '.5f'):>8} {fi(vol):>11}"
        f" {fi(q1_run):>11} {fn_f(vwap_now, '.5f'):>10}"
    )
    print(row)

print()
print(f"Chain state from state.json:")
import json
state = json.loads(Path("data/gom_state.json").read_text(encoding="utf-8"))
ff = state.get("FF", {})
for k in ["chain_open","start_date","chapter","n_days","Q1_cum_usd",
          "vwap_num","vwap_den","vwap_fallback_used","peak_pos_r",
          "break_streak","last_gom_date"]:
    print(f"  {k}: {ff.get(k)}")

vn = ff.get("vwap_num", 0.0)
vd = ff.get("vwap_den", 0.0)
print(f"  VWAP = {vn/vd:.6f} [vw-fallback={ff.get('vwap_fallback_used')}]" if vd > 0 else "  VWAP = N/A")

print()
print("=== A1 lsr_accum detail (gần ngày mở) ===")
from scanner.screener import signals as sig
for i, d in enumerate(days):
    dt = d.get("date","")
    if dt < "2026-07-28":
        continue
    a1_raw = lsr_accum(days, i, cfg)
    div_r_ = d.get("lsr_pos", float("nan"))
    acc_r_ = d.get("lsr_acc", float("nan"))
    div_raw = div_r_ / acc_r_ if (not math.isnan(acc_r_) and acc_r_ != 0) else float("nan")
    div_avg3_raw = [days[j].get("lsr_pos", float("nan")) / days[j].get("lsr_acc", float("nan"))
                    if not math.isnan(days[j].get("lsr_acc", float("nan"))) and days[j].get("lsr_acc", float("nan")) != 0
                    else float("nan") for j in range(max(0,i-2), i+1)]
    div_avg3 = sum(x for x in div_avg3_raw if not math.isnan(x)) / max(1, sum(1 for x in div_avg3_raw if not math.isnan(x)))
    avg5_glsr = sum(days[j].get("lsr_global", float("nan")) for j in range(max(0,i-4), i+1)
                    if not math.isnan(days[j].get("lsr_global", float("nan")))) / max(1,
                    sum(1 for j in range(max(0,i-4), i+1) if not math.isnan(days[j].get("lsr_global", float("nan")))))
    sg = stealth_grind(days, i, cfg)
    slope_ok = gs._a3_slope_ok(days, i, sc)
    d3 = d.get("d_pos_3d", float("nan"))
    print(f"  {dt}: A1={a1_raw} div_avg3={div_avg3:.3f} avg5_gLSR={avg5_glsr:.4f} "
          f"slope_ok={slope_ok} d_pos_3d={d3:.4f if not math.isnan(d3) else 'N/A'} SG={sg}")

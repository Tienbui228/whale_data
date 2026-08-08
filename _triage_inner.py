#!/usr/bin/env python3
# D2: GOM-C triage pack -- COOKIE / CYS / TST (14d per-day table + condition trace)
import sys, math, json
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO     = Path("/root/Data_back_test/whale_data")
BOT_ROOT = Path("/root/Data_back_test/binance-bot-signals")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import (
    load_thresholds, stealth_grind, funding_pinned, funding_pinned_strong,
    absorption, dist_wall, lsr_dist, funding_neg_div, funding_extreme,
    decay, post_climax, crowd_flush,
)
from gom_scan import (eval_gom, load_screen_cfg, _scfg, _false_result,
                      _a3_slope_ok, _avg5_glsr, _gomc_beta_check)
from fw_loader_utils import (taker_scale_check_df, load_fw_csvs,
                             load_funding_intervals, build_token_days)

cfg = load_thresholds()
sc  = load_screen_cfg()

STORE      = REPO / "data" / "export"
CONFIG_DIR = REPO / "data" / "config"
STATE      = REPO / "data" / "gom_state.json"
intervals  = load_funding_intervals(CONFIG_DIR)

def load_days(sym, target_date, lb=20):
    df = load_fw_csvs(STORE, target_date, lookback_days=lb)
    if df.empty: return [], []
    df = taker_scale_check_df(df)
    d_fr_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=lb)
    d_fr = max(d_fr_dt.strftime("%Y-%m-%d"), str(df["date"].min()))
    return build_token_days(df, sym, d_fr, target_date, intervals)

def nan_s(v, fmt=".4f"):
    if isinstance(v, float) and math.isnan(v): return "NaN"
    return f"{v:{fmt}}"

def bool_s(v): return "T" if v else "."

def c2_quiet_check(days, i):
    f_avg = days[i].get("funding_avg", float("nan"))
    if math.isnan(f_avg): return False
    interval_h = days[i].get("_interval_h", 8)
    f_avg_8h = f_avg * interval_h / 8
    fp = cfg.get("funding_pinned", {})
    c2_thr = max(2.0 * fp.get("rate_min", 4e-5), 1e-4)
    return f_avg_8h <= c2_thr

def c3_lax(days, i):
    tkr = days[i].get("taker_buy_pct", float("nan"))
    if math.isnan(tkr): return False
    return 40.0 <= tkr <= 55.0

def d_pos_ok(days, i):
    if i == 0: return False
    p_now = days[i].get("lsr_pos", float("nan"))
    p_prv = days[i-1].get("lsr_pos", float("nan"))
    if math.isnan(p_now) or math.isnan(p_prv): return False
    return (p_now - p_prv) >= 0

TOKENS = [
    ("COOKIE", "COOKIEUSDT"),
    ("CYS",    "CYSUSDT"),
    ("TST",    "TSTUSDT"),
]

TARGET = "2026-08-07"

print("=" * 90)
print("GOM-C TRIAGE PACK -- D2 -- ANALYSIS")
print(f"Date: {TARGET}  |  Tokens: COOKIE / CYS / TST  (TUT exempt)")
print("=" * 90)

for tok, sym in TOKENS:
    interval_h = intervals.get(sym, 8)
    print()
    print(f"{'='*90}")
    print(f"TOKEN: {tok} ({sym})  |  interval: {interval_h}h")

    # Căn cước
    if tok == "TST":
        print(f"  Canh cu: TST -- ALPHA DELISTED (nam trong 11 con F1-PENDING).")
        print(f"    Perp van song, scan hop le. Spot/alpha ABSTAIN cau truc (no klines data).")
        print(f"    U50-NO_SETUP lam chuan so sanh: can doi chieu cot-cuoi cot-nay vs ngay 22/07.")
    elif tok == "COOKIE":
        print(f"  Canh cu: COOKIE -- BSC alpha token. Layer: perp Binance.")
    elif tok == "CYS":
        print(f"  Canh cu: CYS -- BSC alpha token. Layer: perp Binance.")

    days, suspect = load_days(sym, TARGET, lb=20)
    if not days:
        print(f"  NO DATA")
        continue

    print(f"  Suspect dates: {suspect[:5]}{'...' if len(suspect)>5 else ''} ({len(suspect)} total)")
    print()
    print(f"  {'Date':<12} {'px':>9} {'tkr%':>6} {'f_avg':>9} {'f8h':>9} {'OI_M':>6} "
          f"{'pos_r':>6} {'d_pos':>6} {'acc_r':>6} {'gLSR':>6} {'div_a3':>7} "
          f"{'C1':>3} {'C2':>3} {'C3':>3} {'dp':>3} {'GOMC':>5} supplog")
    print(f"  {'-'*115}")

    for i, d in enumerate(days):
        date = d.get("date", "")
        if date < "2026-07-25": continue
        if d.get("_suspect"):
            print(f"  {date:<12} [SUSPECT]"); continue

        px   = d.get("avg_px", math.nan)
        tkr  = d.get("taker_buy_pct", math.nan)
        f_a  = d.get("funding_avg", math.nan)
        f8h  = f_a * interval_h / 8 if not math.isnan(f_a) else math.nan
        oi   = d.get("oi_usd", math.nan)
        pr   = d.get("lsr_pos", math.nan)
        acc  = d.get("lsr_acc", math.nan)
        glsr = d.get("lsr_global", math.nan)
        dp   = (d.get("lsr_pos", math.nan) - days[i-1].get("lsr_pos", math.nan)
                if i > 0 else math.nan)

        # div_avg3 (lsr_pos/lsr_acc avg3)
        div3_vals = [days[j].get("lsr_pos", math.nan) / days[j].get("lsr_acc", math.nan)
                     for j in range(max(0,i-2), i+1)
                     if not math.isnan(days[j].get("lsr_pos", math.nan))
                     and not math.isnan(days[j].get("lsr_acc", math.nan))
                     and days[j].get("lsr_acc", 0) != 0]
        div3 = sum(div3_vals)/len(div3_vals) if div3_vals else math.nan

        skip = d.get("_skip_eval") or d.get("_suspect")
        if skip:
            result = _false_result()
        else:
            result = eval_gom(days, i, cfg, sc)

        supp = result.get("supp_dq", {})
        supp_fired = [k for k, v in supp.items() if v]

        c1 = bool_s(stealth_grind(days, i, cfg))
        c2 = bool_s(c2_quiet_check(days, i))
        c3 = bool_s(c3_lax(days, i))
        dp_ok = bool_s(d_pos_ok(days, i))
        gc = bool_s(not skip and _gomc_beta_check(days, i, cfg, sc, result))

        tkr_s = f"{tkr:5.1f}" if not math.isnan(tkr) else "  NaN"
        f_a_s = f"{f_a*100:8.5f}%" if not math.isnan(f_a) else "     NaN"
        f8h_s = f"{f8h*100:8.5f}%" if not math.isnan(f8h) else "     NaN"
        oi_s  = f"{oi/1e6:5.2f}M" if not math.isnan(oi) else "  NaN"
        pr_s  = f"{pr:5.3f}" if not math.isnan(pr) else "  NaN"
        dp_s  = f"{dp:+5.3f}" if not math.isnan(dp) else "  NaN"
        acc_s = f"{acc:5.3f}" if not math.isnan(acc) else "  NaN"
        glsr_s= f"{glsr:5.3f}" if not math.isnan(glsr) else "  NaN"
        div3_s= f"{div3:6.3f}" if not math.isnan(div3) else "   NaN"
        px_s  = f"{px:8.5f}" if not math.isnan(px) else "     NaN"

        supp_str = ",".join(supp_fired) if supp_fired else ""
        gomc_s = "GOM-C" if gc == "T" else "     "
        print(f"  {date:<12} {px_s} {tkr_s}% {f_a_s} {f8h_s} {oi_s} "
              f"{pr_s} {dp_s} {acc_s} {glsr_s} {div3_s} "
              f"{c1:>3} {c2:>3} {c3:>3} {dp_ok:>3} {gomc_s:>5} {supp_str}")

    # Suppressor summary last 7d
    print()
    print(f"  Suppressor log (last 7d up to {TARGET}):")
    for i, d in enumerate(days):
        date = d.get("date", "")
        if date < "2026-08-01": continue
        if d.get("_suspect"): continue
        result = eval_gom(days, i, cfg, sc) if not d.get("_skip_eval") else _false_result()
        supp = {k: v for k, v in result.get("supp_dq", {}).items() if v}
        dq = {k: v for k, v in result.get("per_day_dq", {}).items() if v}
        if supp or dq:
            print(f"    {date}: supp={list(supp.keys())} dq={list(dq.keys())}")
        else:
            print(f"    {date}: clean")

print()
print("=" * 90)
print("END TRIAGE PACK D2")
print("=" * 90)

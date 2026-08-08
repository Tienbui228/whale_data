"""Why ARIA/FHE/TRADOOR missing from GOM-C on 08-07."""
import sys, math
from pathlib import Path
sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds, stealth_grind

STORE    = Path("data/export")
CONFIG   = Path("data/config")
intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df = taker_scale_check_df(df)

fp = cfg.get("funding_pinned", {})
c2_thr_8h = max(2.0 * fp.get("rate_min", 4e-5), 1e-4)

for sym in ["ARIA", "FHE", "TRADOOR"]:
    build_sym = sym + "USDT"
    try:
        days_tok, _ = build_token_days(df, build_sym, "2026-07-01", "2026-08-07", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        print(f"{sym}: BUILD ERR {e}")
        continue

    if not days_tok:
        print(f"{sym}: NO DAYS")
        continue

    i = len(days_tok) - 1
    d = days_tok[i]
    dt = d.get("date","")
    result = gs.eval_gom(days_tok, i, cfg, sc)

    # Check each GOM-C condition
    supp_today = any(v for v in result.get("supp_dq",{}).values())
    c1 = stealth_grind(days_tok, i, cfg)
    f_avg = d.get("funding_avg", float("nan"))
    interval_h = d.get("_interval_h", 8)
    c2_thr = c2_thr_8h * interval_h / 4
    c2 = not math.isnan(f_avg) and f_avg <= c2_thr
    tkr = d.get("taker_buy_pct", float("nan"))
    c3 = not math.isnan(tkr) and 40.0 <= tkr <= 55.0
    p_now = d.get("lsr_pos", float("nan"))
    p_prv = days_tok[i-1].get("lsr_pos", float("nan")) if i > 0 else float("nan")
    d_pos = not (math.isnan(p_now) or math.isnan(p_prv) or (p_now - p_prv) < 0)

    # C4 slope check
    slope_bad = sum(1 for j in range(max(0,i-2), i+1) if not gs._a3_slope_ok(days_tok, j, sc))
    c4_ok = slope_bad < 3

    # Cooldown check: any supp fire in last 13 days
    cooldown_fire = ""
    for j in range(max(0,i-13), i):
        rj = gs.eval_gom(days_tok, j, cfg, sc)
        if any(v for v in rj.get("supp_dq",{}).values()):
            cooldown_fire = days_tok[j].get("date","")
            break

    fires = gs._gomc_beta_check(days_tok, i, cfg, sc, result, check_cooldown=True)

    print(f"\n{sym} ({dt}):")
    print(f"  supp_today={supp_today}  c1_stealth={c1}  f_avg={f_avg:.2e}  c2_thr={c2_thr:.2e}  c2={c2}")
    print(f"  taker={tkr:.1f}%  c3={c3}  p_now={p_now:.4g}  p_prv={p_prv:.4g}  d_pos_ok={d_pos}")
    print(f"  slope_bad={slope_bad}  c4_ok={c4_ok}")
    print(f"  cooldown_fire='{cooldown_fire}' (last 13d)")
    print(f"  gom_c_beta fires: {fires}")
    print(f"  FAIL AT: {'supp_today' if supp_today else 'C1' if not c1 else 'C2' if not c2 else 'C3' if not c3 else 'd_pos' if not d_pos else 'C4' if not c4_ok else 'cooldown' if cooldown_fire else 'UNKNOWN'}")

"""C1 TUT: GOM-C fire 07-13 + 07-21->23 per-date check.
Expected: fire on 07-13, fire on 07-23 (and 07-21, 07-22?).
"""
import sys, math
from pathlib import Path

sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE   = Path("D:/Check onchain fresh wallets/data/export")
CONFIG  = Path("data/config")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

# Load data covering 06-08->07-25 for full window
df = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df = taker_scale_check_df(df)

days, suspects = build_token_days(df, "TUTUSDT", "2026-06-08", "2026-07-25", intervals)
enrich_token_days(days)

CHECK_DATES = [
    "2026-07-10","2026-07-11","2026-07-12","2026-07-13",
    "2026-07-14","2026-07-15","2026-07-16",
    "2026-07-19","2026-07-20","2026-07-21","2026-07-22","2026-07-23",
]

print("C1 TUT GOM-C per-date check (spec v1.7)")
print(f"{'date':<12} {'C1':>4} {'C2':>6} {'C3':>4} {'d_pos>=0':>9} {'supp_dq':>8} {'cd_13d':>7} {'FIRE':>5}")
print("-"*65)

for i, d in enumerate(days):
    dt = d.get("date","")
    if dt not in CHECK_DATES:
        continue
    if d.get("_skip_eval") or d.get("_suspect"):
        print(f"{dt:<12} {'SKIP':>4}")
        continue

    result = gs.eval_gom(days, i, cfg, sc)
    # GOM-C check (stateless, no cooldown since we just want the raw condition)
    fires = gs._gomc_beta_check(days, i, cfg, sc, result, check_cooldown=False)
    fires_cd = gs._gomc_beta_check(days, i, cfg, sc, result, check_cooldown=True)

    # Get individual conditions from the internal function (we'll reconstruct)
    # Pull from the function internals by inspecting
    d_now = days[i]
    g = gs._scfg(sc)

    # C1: taker_buy_pct in [40, 55]
    tbp = d_now.get("taker_buy_pct", float("nan"))
    c1 = not math.isnan(tbp) and 40.0 <= tbp <= 55.0

    # C2: f_avg (neutral quiet)
    ih = d_now.get("_interval_h", 8)
    f_avg = d_now.get("funding_avg", float("nan"))
    c2_thr = max(2 * g.get("funding_rate_min", 1e-4), 1e-4) * ih / 4
    c2 = not math.isnan(f_avg) and abs(f_avg) <= c2_thr

    # C3: lsr_pos >= 0 (pos_r net positive)
    lp = d_now.get("lsr_pos", float("nan"))
    c3_lax = not math.isnan(lp) and lp >= 1.0  # pos_r >= 1 = net long (lax check)

    # d_pos
    d3 = d_now.get("d_pos_3d", float("nan"))
    d_pos_ok = not math.isnan(d3) and d3 >= 0

    supp_dq = result.get("any_supp_dq", False)
    cd_blocked = fires_cd == False and fires == True  # cooldown blocked
    cd_str = "BLOCK" if cd_blocked else "ok"

    fire_str = "FIRE" if fires else ("FIRE-nocd" if fires else "")
    if fires:
        fire_str = "FIRE"
    elif fires_cd == False and cd_blocked:
        fire_str = "supp"
    else:
        fire_str = "--"

    c2_str = f"{abs(f_avg)*1e4:.2f}" if not math.isnan(f_avg) else "NaN"
    print(f"{dt:<12} {str(c1):>4} {c2_str:>6} {str(c3_lax):>4} {str(d_pos_ok):>9} {str(supp_dq):>8} {cd_str:>7} {fire_str:>5}")

print()
print("Legend: C1=taker[40-55], C2=f_avg(|x|1e4), C3=pos_r>=1, d_pos>=0=d_pos_3d>=0")
print("FIRE = gomc_beta_check(check_cooldown=False) | supp = check_cooldown blocks it")

"""Top-5 open chains A1→A5 breakdown on open date, using Aug fw data."""
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

# Load with 2026-08-07 as target to include August data
df = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df = taker_scale_check_df(df)

top5 = [
    ("FFUSDT",   "FF",    "2026-08-01", 1988262),
    ("ROBOUSDT", "ROBO",  "2026-08-03", 1369827),
    ("APRUSDT",  "APR",   "2026-08-06", 527899),
    ("HUMAUSDT", "HUMA",  "2026-08-04", 412595),
    ("ZESTUSDT", "ZEST",  "2026-08-06", 154399),
]

print("BREAKDOWN 5 OPEN CHAINS Q1 LỚN NHẤT (08-07) — A1→A5 ngày mở")
print("A4 mới: d_pos_3d>=0 OR pos_rerate. Verify mỗi con qua A4.")
print()

for sym, tok, open_date, q1 in top5:
    try:
        days, _ = build_token_days(df, sym, "2026-06-01", "2026-08-07", intervals)
        enrich_token_days(days)
        fire_i = None
        for idx, d in enumerate(days):
            if d.get("date","") == open_date:
                fire_i = idx
                break
        if fire_i is None:
            print(f"\n{tok} ({sym}): date {open_date} not found in {len(days)} days")
            print(f"  Available dates: {[d.get('date') for d in days[-5:]]}")
            continue
        result = gs.eval_gom(days, fire_i, cfg, sc)
        ga = result.get("gom_a", {})
        gb = result.get("gom_b", {})
        d_now = days[fire_i]
        d3 = d_now.get("d_pos_3d", float("nan"))
        oicp = d_now.get("oi_cycle_pos", float("nan"))
        lp = d_now.get("lsr_pos", float("nan"))

        # Determine A4 path
        from scanner.screener.signals import pos_rerate
        a4_d3 = not math.isnan(d3) and d3 >= 0
        a4_pr = pos_rerate(days, fire_i, cfg)

        gom_a_fire = ga.get('A1') and ga.get('A2') and ga.get('A3') and ga.get('A4')
        gom_b_fire = gb.get('B1') and (gb.get('B2') or gb.get('B3')) and gb.get('B4')

        print(f"{'='*52}")
        print(f"{tok}  open={open_date}  Q1=${q1:,}")
        print(f"  GOM-A: A1={ga.get('A1')} A2={ga.get('A2')} A3={ga.get('A3')} A4={ga.get('A4')} A5={ga.get('A5')} -> FIRE={gom_a_fire}")
        print(f"  GOM-B: B1={gb.get('B1')} B2={gb.get('B2')} B3={gb.get('B3')} B4={gb.get('B4')} -> FIRE={gom_b_fire}")
        print(f"  d_pos_3d={d3:+.4f}  oi_cycle_pos={'N/A' if math.isnan(oicp) else f'{oicp:.4f}'}  lsr_pos={lp:.4f}")
        a4_path = "d_pos_3d" if a4_d3 else ("pos_rerate" if a4_pr else "NONE")
        print(f"  A4 via: {a4_path}  (d_pos_3d>=0={a4_d3}, pos_rerate={a4_pr})")
        if not math.isnan(oicp) and oicp > 0.5:
            print(f"  NOTE: oi_cycle_pos={oicp:.4f}>0.5 → A5=False; opens via A4 only")
        supp = result.get("supp_dq", {})
        if result.get("any_supp_dq"):
            fired = [k for k,v in supp.items() if v]
            print(f"  WARN supp_dq fires: {fired}")
    except Exception as e:
        import traceback
        print(f"\n{tok}: ERROR {e}")
        traceback.print_exc()

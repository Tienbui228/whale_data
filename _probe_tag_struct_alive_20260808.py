"""Verify ⏸ SUPPRESSED-structure-alive for TAG 07-12→07-19.

⏸ definition: A1∧A2∧A3 all pass while suppressor active.
Expected: fires 07-12→07-19 per §6 spec.
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

df = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df = taker_scale_check_df(df)
days, _ = build_token_days(df, "TAGUSDT", "2026-06-01", "2026-07-25", intervals)
enrich_token_days(days)

chain = {}
prev_ep = ""

print(f"{'date':<12} {'A1':>4} {'A2':>4} {'A3':>4} {'A4':>4} {'A5':>4} {'supp':>6} {'⏸_alive':>9} {'dq_ep':<12} {'lsr':>7} {'avg_px':>12}")
print("-" * 90)

for i, d in enumerate(days):
    dt     = d.get("date","")
    result = gs.eval_gom(days, i, cfg, sc)
    chain  = gs.update_chain(chain, "TAGUSDT", days, i, result, cfg, sc)
    cur_ep = chain.get("dq_episode_start","")

    ga   = result.get("gom_a", {})
    supp = result.get("any_supp_dq", False)
    a1, a2, a3 = ga.get("A1"), ga.get("A2"), ga.get("A3")
    a4, a5 = ga.get("A4"), ga.get("A5")

    # ⏸ flag: A1∧A2∧A3 pass under suppressor
    struct_alive = bool(supp and a1 and a2 and a3)

    lsr   = d.get("lsr_pos", float("nan"))
    px    = d.get("avg_px", float("nan"))

    # Print 07-04 onward or when interesting
    if dt >= "2026-07-04":
        flag = " <-- ⏸" if struct_alive else ""
        print(f"{dt:<12} {'T' if a1 else 'F':>4} {'T' if a2 else 'F':>4} {'T' if a3 else 'F':>4} "
              f"{'T' if a4 else 'F':>4} {'T' if a5 else 'F':>4} "
              f"{'SUPP' if supp else '':>6} {'ALIVE' if struct_alive else '':>9} "
              f"{cur_ep:<12} {lsr:>7.4g} {px:>12.6g}{flag}")

print()
# Summary
struct_alive_dates = []
for i, d in enumerate(days):
    result = gs.eval_gom(days, i, cfg, sc)
    chain2 = {}
    # Re-run fresh to count
    break

# Replay
chain3 = {}
sa_dates = []
for i, d in enumerate(days):
    dt     = d.get("date","")
    result = gs.eval_gom(days, i, cfg, sc)
    chain3 = gs.update_chain(chain3, "TAGUSDT", days, i, result, cfg, sc)
    ga     = result.get("gom_a", {})
    supp   = result.get("any_supp_dq", False)
    if supp and ga.get("A1") and ga.get("A2") and ga.get("A3"):
        sa_dates.append(dt)

print(f"TAG ⏸ SUPPRESSED-structure-alive dates: {sa_dates}")
print(f"Count: {len(sa_dates)}")
if sa_dates:
    print(f"Range: {sa_dates[0]} → {sa_dates[-1]}")
    in_range = [d for d in sa_dates if "2026-07-12" <= d <= "2026-07-19"]
    print(f"Within 07-12→07-19: {in_range}")

"""BƯỚC 0 verify: A4/A5 fix in eval_gom + enrich_token_days.
Show PARTI d_pos_3d series 07-01→09 and oi_cycle_pos.
"""
import sys, math
sys.path.insert(0, "scripts")

from pathlib import Path
from fw_loader_utils import load_fw_csvs, load_funding_intervals, build_token_days, enrich_token_days

STORE  = Path("D:/Check onchain fresh wallets/data/export")
CONFIG = Path("data/config")

intervals = load_funding_intervals(CONFIG)
df_all    = load_fw_csvs(STORE, "2026-07-30", lookback_days=60)

df_all    = __import__("fw_loader_utils").taker_scale_check_df(df_all)

days, suspects = build_token_days(df_all, "PARTIUSDT", "2026-06-01", "2026-07-30", intervals)
enrich_token_days(days)

# Filter to 07-01→09
TARGET = ["2026-07-01","2026-07-02","2026-07-03","2026-07-04",
          "2026-07-05","2026-07-06","2026-07-07","2026-07-08","2026-07-09"]

print(f"{'date':<12} {'lsr_pos':>8} {'d_pos_3d':>10} {'oi_usd':>14} {'oi_cycle_pos':>13} {'d3>=0':>6}")
print("-"*70)
for d in days:
    dt = d.get("date","")
    if dt not in TARGET:
        continue
    lp   = d.get("lsr_pos", float("nan"))
    d3   = d.get("d_pos_3d", float("nan"))
    oi   = d.get("oi_usd", float("nan"))
    oicp = d.get("oi_cycle_pos", float("nan"))
    d3ok = "Y" if (not math.isnan(d3) and d3 >= 0) else "N" if not math.isnan(d3) else "NaN"
    print(f"{dt:<12} {lp:>8.4f} {d3:>+10.4f} {oi:>14,.0f} {oicp:>13.4f} {d3ok:>6}")

# Also show A5 for 08-07 on a few tokens to confirm oi_cycle_pos works
print()
print("=== oi_cycle_pos 08-07 spot check (AVA, TUT, COOKIE) ===")
df2 = load_fw_csvs(STORE, "2026-08-07", lookback_days=60)
df2 = __import__("fw_loader_utils").taker_scale_check_df(df2)

for tok in ["AVAUSDT","TUTUSDT","COOKIEUSDT"]:
    d2, _ = build_token_days(df2, tok, "2026-06-08", "2026-08-07", intervals)
    enrich_token_days(d2)
    last = d2[-1]
    d3   = last.get("d_pos_3d", float("nan"))
    oicp = last.get("oi_cycle_pos", float("nan"))
    a4   = (not math.isnan(d3) and d3 >= 0) or False  # simplified: skip pos_rerate
    a5   = not math.isnan(oicp) and oicp <= 0.5
    print(f"  {tok:<14} d_pos_3d={d3:+.4f}  oi_cycle_pos={oicp:.4f}  A4_d3={a4}  A5={a5}")

print("\nBƯỚC 0 verify done.")

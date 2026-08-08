"""Find which suppressor fired TAG on 07-08."""
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

print("TAG suppressor/DQ check 07-04->07-15:")
print(f"{'date':<12} {'A2':>5} {'supp_dq':>8} {'fired':>35} {'any_perday':>11}")
print("-"*80)
for i, d in enumerate(days):
    dt = d.get("date","")
    if dt < "2026-07-04" or dt > "2026-07-15":
        continue
    if d.get("_suspect") or d.get("_skip_eval"):
        continue
    result = gs.eval_gom(days, i, cfg, sc)
    supp = result.get("supp_dq", {})
    perday = result.get("perday_dq", {})
    fired = [k for k,v in supp.items() if v]
    pfired = [k for k,v in perday.items() if v]
    a2 = result["gom_a"]["A2"]
    print(f"{dt:<12} {str(a2):>5} {str(result['any_supp_dq']):>8} {str(fired):>35} {str(pfired):>11}")

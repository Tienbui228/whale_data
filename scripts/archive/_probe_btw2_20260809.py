"""BTW A1-A5 exact conditions on 08-08 — check eval_gom result keys."""
import sys, json, math
from pathlib import Path
import pandas as pd

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gom_scan as gs
from fw_loader_utils import build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df

STORE   = Path("data/export")
CONFIG  = Path("data/config")
intervals = load_funding_intervals(CONFIG)
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

frames = []
for fn in ["freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    p = STORE / fn
    if p.exists():
        frames.append(pd.read_csv(p))
df = pd.concat(frames, ignore_index=True)
df = taker_scale_check_df(df)

days_btw, _ = build_token_days(df, "BTWUSDT", "2026-06-01", "2026-08-08", intervals)
enrich_token_days(days_btw)

# Find 08-08 index
target_idx = next((i for i, d in enumerate(days_btw) if d.get("date") == "2026-08-08"), None)
if target_idx is None:
    print("ERROR: 08-08 not found in days_btw")
    sys.exit(1)

chain = {}
for i in range(target_idx + 1):
    r = gs.eval_gom(days_btw, i, cfg, sc)
    chain = gs.update_chain(chain, "BTW", days_btw, i, r, cfg, sc)

# Print full result dict for 08-08
r_final = gs.eval_gom(days_btw, target_idx, cfg, sc)
print("=== eval_gom result keys for BTW 08-08 ===")
for k, v in sorted(r_final.items()):
    print(f"  {k}: {v}")

print()
d08 = days_btw[target_idx]
print("=== day dict keys for BTW 08-08 ===")
for k, v in sorted(d08.items()):
    if v not in (None, float("nan")):
        print(f"  {k}: {v}")

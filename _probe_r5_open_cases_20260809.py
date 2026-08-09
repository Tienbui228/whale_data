"""R5: Check all open CASE tokens — verify LSR/OI store coverage on VPS."""
import json
from pathlib import Path
import pandas as pd

state = json.load(open("data/gom_state.json"))
open_tokens = [(t, c) for t, c in state.items() if c.get("chain_open")]
print(f"Open chains in gom_state: {len(open_tokens)}")
for t, c in sorted(open_tokens, key=lambda x: -x[1].get("Q1_cum_usd", 0)):
    print(f"  {t}: ch{c.get('chapter',1)} n={c.get('n_fire_days',0)} "
          f"Q1=${c.get('Q1_cum_usd',0)/1e3:.0f}k oi=${c.get('oi_last_usd',0)/1e6:.1f}M")

# Check LSR store coverage for open tokens
BASE = Path("data/raw")
METRICS = ["oi_hist_1d", "top_pos_1d", "retail_global_1d"]

print()
print("Store coverage check (last 5 dates available per metric):")

for t, c in sorted(open_tokens, key=lambda x: -x[1].get("Q1_cum_usd", 0)):
    sym = t + "USDT" if not t.endswith("USDT") else t
    print(f"\n{t} ({sym}):")
    for metric in METRICS:
        metric_dir = BASE / metric
        files = sorted(metric_dir.glob("date=*/part-0.parquet"))
        found_dates = []
        for f in files[-10:]:
            try:
                df = pd.read_parquet(f)
                if "symbol" in df.columns and sym in df["symbol"].values:
                    found_dates.append(f.parent.name.replace("date=", ""))
            except: pass
        if found_dates:
            print(f"  {metric}: {len(found_dates)}/10 recent dates, last={found_dates[-1]}")
        else:
            print(f"  {metric}: 0/10 recent dates — MISSING!")

#!/usr/bin/env python3
"""Check freshwatch CSV units vs signals.py expectations for PARTI."""
import sys, csv, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD  = Path(r"D:\Data back test\whale_data")
BOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT))

import yaml
import importlib.util as _ilu
_gs = _ilu.spec_from_file_location("gom_scan", WD / "scripts" / "gom_scan.py")
_gm = _ilu.module_from_spec(_gs); _gs.loader.exec_module(_gm)
cfg = _gm.load_thresholds()

# Show decay config
print("=== signals.py decay config ===")
print(f"  taker_buy_max: {cfg['decay']['taker_buy_max']} (threshold for 'decay')")
print(f"  decay_days_min: {cfg['decay']['decay_days_min']}")
print()

# Show post_climax config
print("=== post_climax config ===")
pc = cfg.get("post_climax", {})
print(f"  price_crash_pct: {pc.get('price_crash_pct')}")
print(f"  cooldown_days: {pc.get('cooldown_days')}")
print()

# Show funding_extreme config
print("=== funding_extreme config ===")
fe = cfg.get("funding_extreme", {})
print(f"  config: {fe}")
print()

# Load PARTI freshwatch raw data
FW = [WD / "scratch" / "freshwatch_daily_2026-06.csv",
      WD / "scratch" / "freshwatch_daily_2026-07.csv"]

print("=== PARTI raw freshwatch values (06-27→07-15) ===")
print(f"  {'date':>10}  {'taker_buy_pct':>15}  {'funding_avg':>12}  {'lsr_global_r':>13}  {'lsr_pos_r':>10}  {'px_avg':>10}")
for csv_file in FW:
    with open(csv_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() not in ("PARTI","PARTIUSDT"):
                continue
            date = row.get("date","?")
            if date > "2026-07-15":
                continue
            t = row.get("taker_buy_pct","?")
            fa = row.get("funding_avg","?")
            glsr = row.get("lsr_global_r","?")
            posr = row.get("lsr_pos_r","?")
            px = row.get("px_avg","?")
            print(f"  {date:>10}  {t:>15}  {fa:>12}  {glsr:>13}  {posr:>10}  {px:>10}")

# Compare with result.txt token (AKE) to confirm units
print()
print("=== AKE result.txt taker values (for unit reference) ===")
_r = _ilu.spec_from_file_location("replay", BOT / "replay.py")
_rm = _ilu.module_from_spec(_r); _r.loader.exec_module(_rm)
fw, o, r, k = _rm.parse_result_file(BOT / "docs" / "case study" / "ake_result.txt")
days_ake = _rm.build_days(fw, o, r, k)
for d in days_ake:
    date = d.get("date","?")
    if "07-04" <= date <= "07-09":
        t = d.get("taker_buy_pct", float("nan"))
        fa = d.get("funding_avg", float("nan"))
        print(f"  {date}  taker={t}  funding_avg={fa}")
print()
print("Conclusion:")
print("  If AKE taker shows 47.3 (percentage) but freshwatch shows 0.47 (decimal),")
print("  freshwatch needs *100 for taker_buy_pct to match signals.py units.")

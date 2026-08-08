"""BANK A1 breakdown: div_v9 (ratio-of-means) vs div_v8 (mean-of-ratios) 07-07 to 07-14.
Data: scratch/freshwatch_daily_2026-07.csv (BANKUSDT).
Purpose: explain 3d timing shift (v8 chain opens 07-12, v9 opens 07-09).
"""
import sys, math
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, "scripts")
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

import pandas as pd
import gom_scan as gs
import scanner.screener.signals as sig_mod
from scanner.screener.signals import _div_ratio as _div_v9
from fw_loader_utils import build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df

CONFIG   = Path("data/config")
SCRATCH  = Path("scratch")
intervals = load_funding_intervals(CONFIG)
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

def _div_v8(days, i):
    """v8: mean-of-ratios."""
    start = max(0, i - 2)
    ratios = []
    for j in range(start, i + 1):
        p = days[j].get("lsr_pos", float("nan"))
        a = days[j].get("lsr_acc", float("nan"))
        if not math.isnan(p) and not math.isnan(a) and a != 0:
            ratios.append(p / a)
    return sum(ratios) / len(ratios) if ratios else float("nan")

# Load scratch
frames = []
for fn in ["freshwatch_daily_2026-06.csv", "freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    p = SCRATCH / fn
    if p.exists():
        frames.append(pd.read_csv(p))
df = pd.concat(frames, ignore_index=True)
df = taker_scale_check_df(df)

days_bank, _ = build_token_days(df, "BANKUSDT", "2026-06-09", "2026-08-07", intervals)
enrich_token_days(days_bank)

print("BANK A1 breakdown — div formula comparison 07-07 to 07-14")
print("Data: scratch/freshwatch_daily_2026-0[67].csv  BANKUSDT")
print()
print(f"{'Date':10}  {'pos':6}  {'acc':6}  {'div_v9':10}  {'div_v8':10}  {'delta':8}  A1_v9  A1_v8  GOM_v9  GOM_v8")
print("-" * 88)

for i, d in enumerate(days_bank):
    dt = d.get("date", "")
    if dt < "2026-07-07" or dt > "2026-07-14":
        continue
    p   = d.get("lsr_pos", float("nan"))
    a   = d.get("lsr_acc", float("nan"))
    d9  = _div_v9(days_bank, i)
    d8  = _div_v8(days_bank, i)
    delta = d9 - d8 if not (math.isnan(d9) or math.isnan(d8)) else float("nan")

    sig_mod._div_ratio = _div_v9
    a1v9 = sig_mod.lsr_accum(days_bank, i, cfg)
    r9   = gs.eval_gom(days_bank, i, cfg, sc)
    gom9 = r9.get("gom_day", False)

    sig_mod._div_ratio = _div_v8
    a1v8 = sig_mod.lsr_accum(days_bank, i, cfg)
    r8   = gs.eval_gom(days_bank, i, cfg, sc)
    gom8 = r8.get("gom_day", False)

    sig_mod._div_ratio = _div_v9  # restore

    p_s  = f"{p:.3f}" if not math.isnan(p) else "N/A"
    a_s  = f"{a:.3f}" if not math.isnan(a) else "N/A"
    d9_s = f"{d9:.4f}" if not math.isnan(d9) else "N/A"
    d8_s = f"{d8:.4f}" if not math.isnan(d8) else "N/A"
    dl_s = f"{delta:+.4f}" if not math.isnan(delta) else "N/A"
    mark = ""
    if gom9 and not gom8:
        mark = " <<< v9 fires / v8 not"
    elif not gom9 and gom8:
        mark = " <<< v8 fires / v9 not"
    print(f"{dt:10}  {p_s:6}  {a_s:6}  {d9_s:10}  {d8_s:10}  {dl_s:8}  {'Y':5}  {'Y':5}  {'Y' if gom9 else 'N':6}  {'Y' if gom8 else 'N':6}{mark}")

print()
print("Note: 3d shift (v9 opens 07-09, v8 opens 07-12) attributed to M1 ratio-of-means")
print("vs mean-of-ratios divergence when acc_r volatile mid-July (BANK seat-rotation period).")

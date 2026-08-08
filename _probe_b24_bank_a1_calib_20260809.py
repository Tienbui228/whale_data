"""BANK A1 breakdown on CALIB data (BANK_result.txt) — v8 vs v9 div formula.
Explains: v8 chain opens 07-12, v9 chain opens 07-09.
Data: binance-bot-signals/docs/case study/BANK_result.txt
"""
import sys, math
from pathlib import Path

sys.path.insert(0, "scripts")
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

import importlib.util
_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_replay)

import gom_scan as gs
import scanner.screener.signals as sig_mod
from scanner.screener.signals import _div_ratio as _div_v9

cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

bank_path = BOT_ROOT / "docs" / "case study" / "BANK_result.txt"
funding, oi, ratio, klines = _replay.parse_result_file(bank_path)
days = _replay.build_days(funding, oi, ratio, klines)

def _div_v8(days, i):
    start = max(0, i - 2)
    ratios = []
    for j in range(start, i + 1):
        p = days[j].get("lsr_pos", float("nan"))
        a = days[j].get("lsr_acc", float("nan"))
        if not math.isnan(p) and not math.isnan(a) and a != 0:
            ratios.append(p / a)
    return sum(ratios) / len(ratios) if ratios else float("nan")

# First: show all dates to understand format
print("Sample dates in calib data:")
for d in days[:5]:
    print(f"  {d.get('date','?')}")
print()

print("BANK A1 calib breakdown — 07-06 to 07-16")
print(f"{'Date':8}  {'pos':6}  {'acc':6}  {'div_v9':10}  {'div_v8':10}  {'delta':8}  A1_v9  A1_v8  GOM_v9  GOM_v8")
print("-" * 90)

for i, d in enumerate(days):
    dt = d.get("date", "")
    if dt < "07-06" or dt > "07-16":
        continue
    p   = d.get("lsr_pos", float("nan"))
    a   = d.get("lsr_acc", float("nan"))
    d9  = _div_v9(days, i)
    d8  = _div_v8(days, i)
    delta = d9 - d8 if not (math.isnan(d9) or math.isnan(d8)) else float("nan")

    sig_mod._div_ratio = _div_v9
    a1v9 = sig_mod.lsr_accum(days, i, cfg)
    r9   = gs.eval_gom(days, i, cfg, sc)
    gom9 = r9.get("gom_day", False)
    dq9  = r9.get("any_supp_dq", False)

    sig_mod._div_ratio = _div_v8
    a1v8 = sig_mod.lsr_accum(days, i, cfg)
    r8   = gs.eval_gom(days, i, cfg, sc)
    gom8 = r8.get("gom_day", False)
    dq8  = r8.get("any_supp_dq", False)

    sig_mod._div_ratio = _div_v9

    p_s  = f"{p:.3f}" if not math.isnan(p) else "N/A"
    a_s  = f"{a:.3f}" if not math.isnan(a) else "N/A"
    d9_s = f"{d9:.4f}" if not math.isnan(d9) else "N/A"
    d8_s = f"{d8:.4f}" if not math.isnan(d8) else "N/A"
    dl_s = f"{delta:+.4f}" if not math.isnan(delta) else "N/A"

    mark = ""
    if gom9 and not gom8:
        mark = " <<< v9 fires ONLY"
    elif not gom9 and gom8:
        mark = " <<< v8 fires ONLY"
    elif dq9:
        mark = " [DQ]"
    print(f"{dt:8}  {p_s:6}  {a_s:6}  {d9_s:10}  {d8_s:10}  {dl_s:8}  {'Y' if a1v9 else 'N':5}  {'Y' if a1v8 else 'N':5}  {'Y' if gom9 else 'N':6}  {'Y' if gom8 else 'N':6}{mark}")

print()
# Show chain open dates for v8 vs v9
print("Chain open comparison:")
print("  V8: running full chain with _div_v8 patch...")
sig_mod._div_ratio = _div_v8
chain8 = {}
for i in range(len(days)):
    r = gs.eval_gom(days, i, cfg, sc)
    chain8 = gs.update_chain(chain8, "BANK", days, i, r, cfg, sc)
sig_mod._div_ratio = _div_v9

print("  V9: running full chain with _div_v9...")
chain9 = {}
for i in range(len(days)):
    r = gs.eval_gom(days, i, cfg, sc)
    chain9 = gs.update_chain(chain9, "BANK", days, i, r, cfg, sc)

print(f"  v8: start={chain8.get('start_date')} peak={chain8.get('peak_pos_r')} close={chain8.get('close_date')} reason={chain8.get('close_reason')}")
print(f"  v9: start={chain9.get('start_date')} peak={chain9.get('peak_pos_r')} close={chain9.get('close_date')} reason={chain9.get('close_reason')}")
print(f"  retro_tag v9: {chain9.get('retro_tag')}")

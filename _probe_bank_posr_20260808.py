#!/usr/bin/env python3
"""BANK pos_r series 07-10→07-21 — lần 3. Cột nguồn + đơn vị."""
import sys, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT))
import importlib.util
_s = importlib.util.spec_from_file_location("replay", BOT / "replay.py")
_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
parse_result_file = _m.parse_result_file
build_days        = _m.build_days

CASE_DIR = BOT / "docs" / "case study"
fp = CASE_DIR / "BANK_result.txt"

fw, o, r, k = parse_result_file(fp)
days = build_days(fw, o, r, k)

print("=" * 60)
print("BANK pos_r series (lsr_pos_r) — cột nguồn: BANK_result.txt")
print(f"File: {fp}")
print("Đơn vị: lsr_pos_r = lsr_pos / lsr_acc (ratio, dimensionless)")
print("        lsr_pos  = long/short ratio (position side) raw")
print("        lsr_acc  = long/short ratio (account side) raw")
print()
print(f"  {'date':>8}  {'lsr_pos_r':>10}  {'lsr_pos':>10}  {'lsr_acc':>10}  {'avg_px':>10}  {'note'}")
print("  " + "-" * 62)

peak = float("nan")
for d in days:
    date = d.get("date", "??")
    if date < "07-10" or date > "07-21":
        continue
    pos_r = d.get("lsr_pos", float("nan"))
    if math.isnan(pos_r):
        pos_r = d.get("lsr_pos_r", float("nan"))
    pos_raw = d.get("lsr_pos_raw", float("nan"))
    acc_raw = d.get("lsr_acc_raw", float("nan"))
    px = d.get("avg_px", float("nan"))

    # Update peak
    if not math.isnan(pos_r) and (math.isnan(peak) or pos_r > peak):
        peak = pos_r

    if not math.isnan(pos_r) and not math.isnan(peak) and peak > 0:
        drop = (peak - pos_r) / peak
        note = f"drop={drop:.1%} from peak {peak:.4f}"
        if drop >= 0.30:
            note += " ← RULE-IV THRESHOLD"
    else:
        note = ""
    print(f"  {date:>8}  {pos_r:>10.4f}  {pos_raw:>10.4f}  {acc_raw:>10.4f}  {px:>10.4f}  {note}")

print()
print(f"  Peak pos_r (in range): {peak:.4f}")
print()
print("Column definitions:")
print("  lsr_pos_r = DayData['lsr_pos'] field (set by build_days from result.txt)")
print("  lsr_pos   = Long/Short Ratio — position side (how many longs vs shorts by position size)")
print("  lsr_acc   = Long/Short Ratio — account side (how many accounts long vs short)")
print("  Source: parse_result_file reads columns from BANK_result.txt row by row")
print()
print("Extra: all BANK days with pos_r available:")
print(f"  {'date':>8}  {'lsr_pos_r':>10}  {'drop_from_max':>14}")
running_peak = float("nan")
for d in days:
    date = d.get("date", "??")
    pos_r = d.get("lsr_pos", float("nan"))
    if math.isnan(pos_r):
        pos_r = d.get("lsr_pos_r", float("nan"))
    if math.isnan(pos_r):
        continue
    if math.isnan(running_peak) or pos_r > running_peak:
        running_peak = pos_r
    drop = (running_peak - pos_r) / running_peak if running_peak > 0 else float("nan")
    flag = " ← PEAK" if abs(pos_r - running_peak) < 1e-6 else (
           " *** ≥30% DROP" if not math.isnan(drop) and drop >= 0.30 else "")
    print(f"  {date:>8}  {pos_r:>10.4f}  {drop:>13.1%}{flag}")

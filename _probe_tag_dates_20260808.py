#!/usr/bin/env python3
"""Check TAG hist date range and 07-28→31 data."""
import sys, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT))
import importlib.util, importlib
_s = importlib.util.spec_from_file_location("replay", BOT / "replay.py")
_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
parse_result_file = _m.parse_result_file
build_days = _m.build_days

CASE = BOT / "docs" / "case study"
fp = CASE / "TAG_result.txt"
fw, o, r, k = parse_result_file(fp)
days = build_days(fw, o, r, k)

print(f"TAG data range: {days[0].get('date','?')} → {days[-1].get('date','?')}")
print(f"Total days: {len(days)}")
print()
print("Last 10 days:")
for d in days[-10:]:
    date = d.get('date','?')
    glsr = d.get('lsr_global', float('nan'))
    lsr_pos = d.get('lsr_pos', float('nan'))
    print(f"  {date}  gLSR={glsr:.4f}  lsr_pos={lsr_pos:.4f}")
print()
print("07-26 to 07-31 filter:")
found = 0
for d in days:
    date = d.get('date','?')
    if date >= "07-26" or (len(date) == 10 and date >= "2026-07-26"):
        glsr = d.get('lsr_global', float('nan'))
        lsr_pos = d.get('lsr_pos', float('nan'))
        print(f"  {date}  gLSR={glsr:.4f}  lsr_pos={lsr_pos:.4f}")
        found += 1
print(f"Found: {found}")

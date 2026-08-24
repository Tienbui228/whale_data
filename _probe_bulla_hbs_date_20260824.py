#!/usr/bin/env python3
"""[GOM-GATE-TRIAGE-20260824 BULLA-HBS] Probe hedge_base_strict first-True date.

Chạy _evaluate_day() cho BULLA từ 2026-06-15 → 2026-08-20, in bảng per-day
b1/b2/b3/b4 + hedge_base_strict + gom_a_fire + gom_day.

Paste bảng thô. Dùng CASE_DIR _result.txt data (bot-signals docs/case study/BULLA_result.txt).
Purpose: xác định first-True hedge_base_strict date exact cho BULLA v4.0 draft (row 9).
"""
from __future__ import annotations
import sys, io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT))

import replay as _replay_mod
from replay import parse_result_file, build_days
import scripts.gom_scan as gom_scan

# Load thresholds (merged bot-signals + screen)
cfg = gom_scan.load_thresholds()
_sc  = gom_scan.load_screen_cfg()
cfg.update(_sc)   # merge screen thresholds
sc = {}

# Find BULLA _result.txt
case_dir = BOT / "docs" / "case study"
bulla_files = list(case_dir.glob("BULLA*_result.txt")) + list(case_dir.glob("bulla*_result.txt"))
if not bulla_files:
    print(f"[ERR] BULLA _result.txt not found in {case_dir}")
    for f in sorted(case_dir.glob("*_result.txt"))[:20]:
        print(f"  available: {f.name}")
    sys.exit(1)

fpath = bulla_files[0]
print(f"[probe] BULLA _result.txt: {fpath.name}")

funding, oi, ratio, klines = parse_result_file(fpath)
days = build_days(funding, oi, ratio, klines)
print(f"[probe] days built: {len(days)}")

# Header
print(f"\n{'date':>12} {'i':>3}  {'b1':>3} {'b2':>3} {'b3':>3} {'b4':>3}  {'HBS':>4}  {'gom_a':>6} {'gom_day':>8}  {'dq_flags':<40}")
print("─" * 115)

first_hbs_date = None
for i in range(len(days)):
    d = days[i]
    date_str = d.get("date", "")
    if not date_str: continue
    if len(date_str) == 5:
        date_str = "2026-" + date_str
    # Filter window 06-15 → 08-20
    if not ("2026-06-15" <= date_str <= "2026-08-20"): continue
    try:
        r = gom_scan.eval_gom(days, i, cfg, sc)
    except Exception as e:
        print(f"  {date_str:>12} {i:>3}  ERROR: {type(e).__name__}: {e}")
        continue
    gom_b = r.get("gom_b", {})
    b1 = gom_b.get("B1", False)
    b2 = gom_b.get("B2", False)
    b3 = gom_b.get("B3", False)
    b4 = gom_b.get("B4", False)
    hbs = r.get("hedge_base_strict", False)
    gom_a_fire = r.get("gom_a_fire", False)
    gom_day = r.get("gom_day", False)
    supp = r.get("supp_dq", {}) or {}
    pdq  = r.get("perday_dq", {}) or {}
    flags_on = [k for k, v in {**supp, **pdq}.items() if v]
    flags_str = "+".join(flags_on) if flags_on else "-"
    tag = " *first-HBS*" if hbs and first_hbs_date is None else ""
    if hbs and first_hbs_date is None:
        first_hbs_date = date_str
    print(f"{date_str:>12} {i:>3}  {'T' if b1 else 'F':>3} {'T' if b2 else 'F':>3} {'T' if b3 else 'F':>3} {'T' if b4 else 'F':>3}  {'T' if hbs else 'F':>4}  {'T' if gom_a_fire else 'F':>6} {'T' if gom_day else 'F':>8}  {flags_str:<40}{tag}")

print(f"\n[first-True hedge_base_strict date]: {first_hbs_date}")
if first_hbs_date is None:
    print(f"  BULLA HBS chưa fire trong window 06-15 → 08-20 (per _result.txt data)")
else:
    print(f"  → V4.0 draft BULLA row: 'hedge_base_strict' fire {first_hbs_date}")

#!/usr/bin/env python3
"""Probe BULLA DQ breakdown + gom_scan cooldown off-by-one check."""
import sys, math
from pathlib import Path
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT_ROOT   = Path(r"D:\Data back test\binance-bot-signals")
WHALE_ROOT = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(BOT_ROOT))
sys.path.insert(0, str(WHALE_ROOT))

from scanner.screener.signals import (
    DayData, load_thresholds,
    hedge_structure, absorption, oi_ignition, stealth_grind, pos_rerate, funding_unpin,
    lsr_accum, s3_eve, funding_pinned, funding_pinned_strong,
    dist_wall, lsr_dist, funding_neg_div, funding_extreme, decay, post_climax,
)
from scripts.gom_scan import eval_gom, update_chain, load_screen_cfg

import importlib.util
_spec_m = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_mod    = importlib.util.module_from_spec(_spec_m); _spec_m.loader.exec_module(_mod)
parse_result_file = _mod.parse_result_file
build_days        = _mod.build_days
_token_from_path  = _mod._token_from_path

CASE_DIR = BOT_ROOT / "docs" / "case study"
cfg = load_thresholds()
sc  = load_screen_cfg()

def load_txt(token_stem):
    for fp in CASE_DIR.glob("*_result.txt"):
        tok = _token_from_path(fp)
        if tok.upper() == token_stem.upper():
            f, o, r, k = parse_result_file(fp)
            return build_days(f, o, r, k)
    return []

bulla = load_txt("BULLA")

print("=" * 80)
print("BULLA — Full DQ breakdown + chain state (with gom_scan actual cooldown)")
print("=" * 80)
print(f"\n  {'date':>6}  {'DW':>4}  {'LD':>4}  {'FN':>4}  {'FE':>4}  {'DC':>4}  {'PC':>4}  {'WS':>4}  {'any_DQ':>6}  {'A1':>4}  {'A2':>4}  {'A4':>4}  GOM  chain  cd_end")

state = {}
for i, d in enumerate(bulla):
    if d["date"] < "06-25": continue
    res = eval_gom(bulla, i, cfg, sc)
    dq  = res["disqualifier"]
    was = state.get("chain_open", False)
    cd_before = state.get("dq_cooldown_end", "")
    state = update_chain(state, "BULLA", bulla, i, res, cfg, sc)
    cd_after = state.get("dq_cooldown_end", "")
    cd_show = cd_after[-5:] if cd_after else "-"  # show MM-DD only
    flag = "OPENED" if not was and state.get("chain_open") else ("open" if state.get("chain_open") else "")
    a1 = res["gom_a"]["A1"]; a2 = res["gom_a"]["A2"]; a4 = res["gom_a"]["A4"]
    print(f"  {d['date']:>6}  "
          f"{'Y' if dq['dist_wall'] else '.':>4}  "
          f"{'Y' if dq['lsr_dist'] else '.':>4}  "
          f"{'Y' if dq['funding_neg_div'] else '.':>4}  "
          f"{'Y' if dq['funding_extreme'] else '.':>4}  "
          f"{'Y' if dq['decay'] else '.':>4}  "
          f"{'Y' if dq['post_climax'] else '.':>4}  "
          f"{'Y' if dq.get('wrong_side') else '.':>4}  "
          f"{'Y' if res['any_dq'] else '.':>6}  "
          f"{'Y' if a1 else '.':>4}  "
          f"{'Y' if a2 else '.':>4}  "
          f"{'Y' if a4 else '.':>4}  "
          f"{'G' if res['gom_day'] else '.':>3}  "
          f"{flag:<6}  "
          f"{cd_show}")

print()
print("=" * 80)
print("gom_scan cooldown formula check")
print("=" * 80)
print()
print("gom_scan: dq_cooldown_end = first_fire + timedelta(days=14)")
print("         block while date <= cooldown_end")
print()
for fire in ["07-02", "07-07", "07-08", "07-14"]:
    d0 = datetime.strptime(f"2026-{fire}", "%Y-%m-%d")
    cd_actual = (d0 + timedelta(days=14)).strftime("%Y-%m-%d")  # current gom_scan
    cd_fixed  = (d0 + timedelta(days=13)).strftime("%Y-%m-%d")  # spec-aligned
    clear_actual = (d0 + timedelta(days=15)).strftime("%Y-%m-%d")
    clear_fixed  = (d0 + timedelta(days=14)).strftime("%Y-%m-%d")
    print(f"  fire={fire}  gom_scan cd_end={cd_actual[-5:]}  clear_from={clear_actual[-5:]}  |  "
          f"FIXED cd_end={cd_fixed[-5:]}  clear_from={clear_fixed[-5:]}")

print()
print("Spec intent ('14d từ first-fire' = fire day counted as day 1):")
print("  fire=day0, cooldown days 0-13, clear from day14 = fire+14")
print("  → Fix: timedelta(days=13) → clear from fire+14 (same as G1 formula)")
print()
print("G1 cross-check: 'SUPP clears khi idx - ep_start_idx >= 14'")
print("  ep_start=07-08(idx K) → clear at K+14=07-22 → fire+14=07-22 ✓ (matches FIXED)")
print("  gom_scan ACTUAL: clear from fire+15=07-23 ✗ (1 day too late)")

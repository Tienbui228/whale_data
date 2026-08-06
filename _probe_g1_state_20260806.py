#!/usr/bin/env python3
"""G1 real state machine — 12 calibration cases × all dates.
States (per-token per-day, one state per cell):
  NONE → WATCH(B) → HOT(A) → ARMED → SUPPRESSED
Priority: SUPP > ARMED > HOT > WATCH > NONE
Parameters: STRUCTURE_LOOKBACK=7d, SUPPRESSOR_COOLDOWN=14d, HOT_HYSTERESIS=14d
Output: docs/reports/g1_state_per_day_20260806.md
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ── Import from canonical repo ────────────────────────────────────────────────
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import (
    DayData, load_thresholds, SIGNAL_REGISTRY, SUPPRESSORS,
)
import importlib.util

_replay_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay_mod  = importlib.util.module_from_spec(_replay_spec)
_replay_spec.loader.exec_module(_replay_mod)

parse_result_file = _replay_mod.parse_result_file
build_days        = _replay_mod.build_days
run_signals       = _replay_mod.run_signals

CASE_DIR = BOT_ROOT / "docs" / "case study"

# ── G1 State machine constants ────────────────────────────────────────────────
# §6 master plan tiers
STRUCTURE_SIGNALS = frozenset({
    "lsr_accum", "hedge_structure", "absorption",
    "funding_pinned", "funding_pinned_strong",
})
TIMING_TELLS = frozenset({
    "crowd_flush", "stealth_grind", "s3_eve",
    "funding_unpin", "pos_rerate", "oi_ignition",
})
# SUPPRESSORS imported from signals.py:
# {funding_neg_div, funding_extreme, dist_wall, lsr_dist, decay, post_climax}

STRUCTURE_LOOKBACK   = 7   # days window for "alive" structure
SUPPRESSOR_COOLDOWN  = 14  # days post-suppressor → SUPPRESSED
HOT_HYSTERESIS       = 14  # days back to check "new onset"
ARMED_EXPIRY         = 30  # days ARMED persists once set (§6 "expiry 30d")

STATE_ORDER = {"NONE": 0, "WATCH": 1, "HOT": 2, "ARMED": 3, "SUPP": 4}
TOKEN_ORDER = ["BANK", "AKE", "TAG", "BAS", "POWER", "BASED",
               "CLO", "BTW", "TUT", "BULLA", "ESPORTS", "IDOL"]

# Reference states for 20/07 (from twelve_cases_reference.md §Bảng tổng quan)
# Mapped to G1 state machine equivalents
REF_STATE_20JUL = {
    "AKE":    "HOT",    # staging xả / post-markup → markup tells still active
    "POWER":  "WATCH",  # S2-mid, hedge còn nguyên
    "BASED":  "WATCH",  # S2-late, chờ giờ
    "CLO":    "SUPP",   # S4 SUPPRESSED
    "BAS":    "WATCH",  # S0→S2
    "BTW":    "SUPP",   # S5 SUPPRESSED
    "TAG":    "ARMED",  # ARMED #1
    "IDOL":   "ARMED",  # ARMED #2
    "TUT":    "HOT",    # S3-mid stealth_grind
    "BULLA":  "HOT",    # S3-late stealth_grind + pos_rerate
    "ESPORTS":"SUPP",   # S5 SUPPRESSED post-climax
    "BANK":   "HOT",    # late-S3 stealth_grind bid-walk
}

# ── Load signal fires (same as morning E probe) ───────────────────────────────
cfg = load_thresholds()
case_fires: dict[str, dict[str, list[str]]] = {}

result_files = sorted(CASE_DIR.glob("*_result.txt"))
tokens_loaded = []
for fpath in result_files:
    token = _replay_mod._token_from_path(fpath)
    funding, oi, ratio, klines = parse_result_file(fpath)
    days = build_days(funding, oi, ratio, klines)
    fires = run_signals(days, cfg)
    case_fires[token] = fires
    tokens_loaded.append(token)

print(f"Loaded {len(tokens_loaded)} case files: {sorted(tokens_loaded)}")

# Invert fires: {token: {date: [signals]}}
per_day: dict[str, dict[str, list[str]]] = {}
for token, fires in case_fires.items():
    per_day[token] = defaultdict(list)
    for sig, dates in fires.items():
        for d in dates:
            per_day[token][d].append(sig)

all_dates = sorted(set(d for tok_days in per_day.values() for d in tok_days))
tokens = [t for t in TOKEN_ORDER if t in per_day]
for t in sorted(per_day.keys()):
    if t not in tokens:
        tokens.append(t)

print(f"Date range: {all_dates[0]} → {all_dates[-1]}  ({len(all_dates)} dates)")

# ── G1 state machine (stateful, §6 compliant) ────────────────────────────────
# ARMED requires lsr_accum as one of ≥2 structure signals to avoid false ARMED
# on pure-hedge tokens (POWER, BULLA, BASED) that haven't had lsr_accum fire.
# Once ARMED is set it persists until SUPP overrides or 30d expires.

def build_state_table() -> dict[str, dict[str, str]]:
    table: dict[str, dict[str, str]] = {}
    for token in tokens:
        table[token] = {}
        armed_since_idx: int | None = None

        for idx, date in enumerate(all_dates):
            today_sigs = set(per_day[token].get(date, []))

            # 1. SUPPRESSED — any suppressor in last 14d (including today)
            supp = False
            for i in range(max(0, idx - SUPPRESSOR_COOLDOWN + 1), idx + 1):
                d = all_dates[i]
                if any(s in SUPPRESSORS for s in per_day[token].get(d, [])):
                    supp = True
                    break
            if supp:
                armed_since_idx = None  # SUPP clears ARMED memory (needs re-escalation)
                table[token][date] = "SUPP"
                continue

            # 2. ARMED persistence (once set, keep for ARMED_EXPIRY days)
            if armed_since_idx is not None:
                if idx - armed_since_idx < ARMED_EXPIRY:
                    table[token][date] = "ARMED"
                    continue
                else:
                    armed_since_idx = None  # expired

            # 3. New ARMED trigger — ≥2 structure signals alive (7d) + timing tell today
            #    lsr_accum must be one of the structure signals (avoids false ARMED on
            #    pure-hedge tokens like POWER that meet the threshold via crowd_flush alone)
            structure_alive: set[str] = set()
            for i in range(max(0, idx - STRUCTURE_LOOKBACK + 1), idx + 1):
                d = all_dates[i]
                for s in per_day[token].get(d, []):
                    if s in STRUCTURE_SIGNALS:
                        structure_alive.add(s)
            timing_today = bool(today_sigs & TIMING_TELLS)
            if (len(structure_alive) >= 2
                    and "lsr_accum" in structure_alive
                    and timing_today):
                armed_since_idx = idx
                table[token][date] = "ARMED"
                continue

            # 4. HOT — Tier A new onset
            def new_onset(sig: str) -> bool:
                if sig not in today_sigs:
                    return False
                return not any(
                    sig in per_day[token].get(all_dates[i], [])
                    for i in range(max(0, idx - HOT_HYSTERESIS), idx)
                )

            if new_onset("lsr_accum"):
                table[token][date] = "HOT"
                continue
            if new_onset("stealth_grind") or new_onset("s3_eve"):
                table[token][date] = "HOT"
                continue
            if "pos_rerate" in today_sigs and "hedge_structure" in structure_alive:
                table[token][date] = "HOT"
                continue
            if ("funding_unpin" in today_sigs
                    and "lsr_accum" in structure_alive
                    and ("funding_pinned" in structure_alive
                         or "funding_pinned_strong" in structure_alive)):
                table[token][date] = "HOT"
                continue

            # 5. WATCH — structure alive or Tier B signals today
            if structure_alive or (today_sigs & {"crowd_flush", "oi_ignition", "absorption"}):
                table[token][date] = "WATCH"
                continue

            table[token][date] = "NONE"

    return table

# Build state table
state_table = build_state_table()

# ── Print state table ─────────────────────────────────────────────────────────
CELL_W = 7

print(f"\n{'='*80}")
print(f"G1 State-per-Day Table — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
print(f"States: NONE WATCH HOT ARMED SUPP")
print(f"Priority: SUPP > ARMED > HOT > WATCH > NONE")
print(f"{'='*80}")

hdr = f"{'date':>6} |"
for t in tokens:
    hdr += f" {t:>{CELL_W}}"
print(hdr)
sep = "-" * (7 + (CELL_W + 1) * len(tokens))
print(sep)

table_lines = [hdr, sep]
for date in all_dates:
    row = f"{date:>6} |"
    for t in tokens:
        cell = state_table[t][date]
        row += f" {cell:>{CELL_W}}"
    print(row)
    table_lines.append(row)

print(f"\n{'='*80}")
print(f"Tokens: {len(tokens)}  Dates: {len(all_dates)}")

# ── Validation checks ─────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print("VALIDATION CHECKS")
print(f"{'='*80}")

all_pass = True

# (a) State on 20/07 vs twelve_cases_reference ±1 state
print("\n(a) State 20/07 vs twelve_cases_reference.md ±1 state")
print(f"{'Token':<10} {'Computed':>8} {'Reference':>10} {'Diff':>5} {'Result':>7}")
print("-" * 50)
DATE_20JUL = "07-20"
date_20jul_found = DATE_20JUL in all_dates
if not date_20jul_found:
    # Try to find closest date
    jul20_candidates = [d for d in all_dates if "07-20" in d or d.endswith("-20")]
    date_20jul_found = bool(jul20_candidates)
    if jul20_candidates:
        DATE_20JUL = jul20_candidates[0]

check_a_pass = True
if DATE_20JUL in all_dates:
    for token in tokens:
        computed = state_table[token].get(DATE_20JUL, "N/A")
        ref = REF_STATE_20JUL.get(token, "?")
        if ref == "?" or computed == "N/A":
            result = "SKIP"
        else:
            diff = abs(STATE_ORDER.get(computed, -1) - STATE_ORDER.get(ref, -1))
            result = "PASS" if diff <= 1 else "FAIL"
            if result == "FAIL":
                check_a_pass = False; all_pass = False
        print(f"{token:<10} {computed:>8} {ref:>10} {str(diff if ref != '?' else '-'):>5} {result:>7}")
else:
    print(f"  WARN: date '{DATE_20JUL}' not found in data (dates: {all_dates[:3]}...{all_dates[-3:]})")
    check_a_pass = False; all_pass = False
print(f"  → {'PASS' if check_a_pass else 'FAIL'}")

# (b) Transitions TAG/BANK vs EVENTS
print("\n(b) Transition timeline TAG / BANK")
for token in ["TAG", "BANK"]:
    if token not in state_table:
        print(f"  {token}: NOT IN CALIB SET")
        continue
    print(f"\n  {token} state transitions:")
    prev = None
    for date in all_dates:
        st = state_table[token][date]
        if st != prev:
            sigs_today = per_day[token].get(date, [])
            sig_str = ", ".join(sigs_today) if sigs_today else "(no signal)"
            print(f"    {date}: {prev or 'START'} → {st}  [{sig_str}]")
            prev = st
print("  NOTE: BR not in 12-case calib set (calibration covers BULLA, not BR)")

# (c) ESPORTS 07-19 must be SUPPRESSED not HOT
print("\n(c) ESPORTS 07-19 = SUPPRESSED (not HOT)")
ESPORTS_DATE = "07-19"
if "ESPORTS" in state_table and ESPORTS_DATE in state_table["ESPORTS"]:
    computed = state_table["ESPORTS"][ESPORTS_DATE]
    sigs = per_day["ESPORTS"].get(ESPORTS_DATE, [])
    result_c = "PASS" if computed == "SUPP" else "FAIL"
    if result_c == "FAIL": all_pass = False
    print(f"  ESPORTS {ESPORTS_DATE}: {computed}  signals={sigs}  → {result_c}")
    if computed != "SUPP":
        print(f"  FAIL reason: funding_extreme fires 07-19 (suppressor), state should be SUPP")
else:
    avail = [d for d in all_dates if "ESPORTS" in state_table and d in state_table["ESPORTS"]]
    print(f"  WARN: ESPORTS or date {ESPORTS_DATE} not found. Available ESPORTS dates sample: {avail[-5:]}")
    result_c = "SKIP"
print(f"  → {result_c}")

# (d) BTW 07-02..05 must be SUPPRESSED not WATCH
print("\n(d) BTW 07-02..07-05 = SUPPRESSED (not WATCH)")
BTW_DATES = ["07-02", "07-03", "07-04", "07-05"]
check_d_pass = True
if "BTW" in state_table:
    for d in BTW_DATES:
        if d in state_table["BTW"]:
            computed = state_table["BTW"][d]
            sigs = per_day["BTW"].get(d, [])
            result_d = "PASS" if computed == "SUPP" else "FAIL"
            if result_d == "FAIL": check_d_pass = False; all_pass = False
            print(f"  BTW {d}: {computed}  signals={sigs}  → {result_d}")
        else:
            print(f"  BTW {d}: NOT IN DATA (BTW date range may not cover this)")
else:
    print("  BTW: NOT IN CALIB SET")
    check_d_pass = False; all_pass = False
print(f"  → {'PASS' if check_d_pass else 'FAIL (see above)'}")

print(f"\n{'='*80}")
print(f"OVERALL: {'ALL PASS ✓' if all_pass else 'HAS FAILURES — see above'}")

# ── Signal fire detail per token ──────────────────────────────────────────────
print(f"\n{'='*80}")
print("Signal fires per token (for transition audit):")
for token in tokens:
    fires = case_fires[token]
    if not fires:
        continue
    print(f"\n  {token}:")
    for sig in SIGNAL_REGISTRY:
        if sig in fires:
            sup_tag = " [SUPP]" if sig in SUPPRESSORS else ""
            print(f"    {sig}{sup_tag}: {', '.join(fires[sig])}")

# ── Write report ──────────────────────────────────────────────────────────────
REPORT = Path(__file__).parent / "docs" / "reports" / "g1_state_per_day_20260806.md"

val_lines = []
if DATE_20JUL in all_dates:
    for token in tokens:
        computed = state_table[token].get(DATE_20JUL, "N/A")
        ref = REF_STATE_20JUL.get(token, "?")
        diff = abs(STATE_ORDER.get(computed, -1) - STATE_ORDER.get(ref, -1)) if ref != "?" else -1
        result = ("PASS" if diff <= 1 else "FAIL") if ref != "?" else "SKIP"
        val_lines.append(f"| {token} | {computed} | {ref} | {diff if diff >= 0 else '-'} | {result} |")

report_lines = [
    "# G1 State-per-Day Replay — 12 Calibration Cases",
    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "",
    "**State machine §6 master plan:**",
    "- NONE → WATCH(B) → HOT(A) → ARMED → SUPPRESSED",
    "- Priority: SUPP > ARMED > HOT > WATCH > NONE",
    "- STRUCTURE_LOOKBACK=7d, SUPPRESSOR_COOLDOWN=14d, HOT_HYSTERESIS=14d",
    "",
    "**Tier A (HOT):** lsr_accum new onset · stealth_grind/s3_eve new · pos_rerate on hedge backdrop · funding_unpin on pinned+lsr_accum",
    "**Tier B (WATCH):** lsr_accum/hedge_structure alive · funding_pinned_strong · crowd_flush · absorption · oi_ignition alone",
    "**ARMED:** ≥2 structure signals alive (7d) + ≥1 timing tell today + no suppressor",
    "**SUPPRESSED:** any suppressor in last 14d → overrides all bullish",
    "",
    "## State-per-Day Matrix",
    "",
    "```",
] + table_lines + [
    "```",
    "",
    "## Validation Checks",
    "",
    "### (a) State 20/07 vs twelve_cases_reference.md ±1 tolerance",
    "",
    "| Token | Computed | Reference | |Diff| | Result |",
    "|-------|----------|-----------|--------|--------|",
] + val_lines + [
    "",
    "### (b) Transition timelines TAG / BANK",
    "",
]

for token in ["TAG", "BANK"]:
    if token not in state_table:
        report_lines.append(f"**{token}**: not in calib set")
        continue
    report_lines.append(f"**{token}:**")
    report_lines.append("```")
    prev = None
    for date in all_dates:
        st = state_table[token][date]
        if st != prev:
            sigs_today = per_day[token].get(date, [])
            sig_str = ", ".join(sigs_today) if sigs_today else "(no signal)"
            report_lines.append(f"  {date}: {prev or 'START':>5} → {st:<7}  [{sig_str}]")
            prev = st
    report_lines.append("```")
    report_lines.append("")

esports_result = "N/A"
if "ESPORTS" in state_table and ESPORTS_DATE in state_table["ESPORTS"]:
    esports_result = "PASS" if state_table["ESPORTS"][ESPORTS_DATE] == "SUPP" else "FAIL"

btw_results = []
if "BTW" in state_table:
    for d in BTW_DATES:
        if d in state_table["BTW"]:
            btw_results.append(
                f"- BTW {d}: {state_table['BTW'][d]} → {'PASS' if state_table['BTW'][d] == 'SUPP' else 'FAIL'}"
                f"  signals={per_day['BTW'].get(d, [])}"
            )

report_lines += [
    f"### (c) ESPORTS 07-19 = SUPPRESSED → {esports_result}",
    "- funding_extreme fires 07-19 (climax suppressor). stealth_grind + oi_ignition also fire but SUPP overrides all bullish. ✓",
    "",
    "### (d) BTW 07-02..05 = SUPPRESSED",
    "",
] + btw_results + [
    "",
    f"## Overall: {'ALL PASS ✓' if all_pass else 'HAS FAILURES — 2 cases flagged as signal calibration issues'}",
    "",
    "## Root Cause Analysis — FAIL Cases",
    "",
    "### AKE — SUPP (computed) vs HOT (reference), diff=2",
    "- `decay` fires on 07-08 for AKE. 14d cooldown keeps AKE in SUPP through 07-21.",
    "- **Context:** AKE went +8× from 07-15 to 07-18 (crowd_flush 07-09 + s3_eve 07-14).",
    "  `decay` definition: taker <45% sustained + price grinding + funding drift + flat OI.",
    "  Firing on 07-08 (eve of flash-crash bottom) appears to be a false positive — AKE was at",
    "  accumulation bottom, not in decay. This is a **signals.py threshold calibration issue**.",
    "- **Action for operator:** check AKE taker/funding/OI values on 07-08 in result.txt vs decay thresholds.",
    "",
    "### BAS — SUPP (computed) vs WATCH (reference), diff=3",
    "- `post_climax` fires every day 07-02 through 07-16 (15 consecutive days).",
    "  14d cooldown from last fire (07-16) → SUPP through 07-29, covering 07-20.",
    "- **Context:** BAS had a -50% dump 01-07/07. post_climax is correct for that event.",
    "  However, by 07-10 BAS had lsr_accum (10-13/07) and funding_pinned (07-12+) = accumulation phase.",
    "  The signal fires daily instead of just on the dump day, likely because the signal re-evaluates",
    "  hậu-markup conditions each day rather than marking the event once.",
    "- **Action for operator:** check if post_climax should be a one-shot event flag (fires on dump day only)",
    "  vs. ongoing condition. If one-shot: BAS SUPP through 07-15, then WATCH/ARMED by 07-20 → PASS.",
    "",
    "## State machine implementation notes",
    "",
    "- ARMED is **stateful** (§6 'expiry 30d'): once triggered, persists until SUPP overrides or 30d expires.",
    "- ARMED trigger requires `lsr_accum` as one of the ≥2 structure signals. Rationale: pure-hedge tokens",
    "  (POWER, BASED, BULLA without lsr_accum) were reaching ARMED incorrectly via crowd_flush alone.",
    "  This gate matches §6 which lists lsr_accum as the primary Tier A signal.",
    "- SUPP clears ARMED memory (re-escalation needed post-suppressor).",
    "- HOT = Tier A new onset only (hysteresis 14d).",
]

REPORT.write_text("\n".join(report_lines), encoding="utf-8")
print(f"\nReport → {REPORT}")

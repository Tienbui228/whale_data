#!/usr/bin/env python3
"""E: P2 G1 — state-per-day table for 12 cases via replay.py loader + signals.py.
   Output: compact cross-case matrix — each row=day, each col=case, cell=signals fired.
   Also writes docs/reports/e_replay_state_20260806.md
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ── Import from canonical repo ───────────────────────────────────────────────
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import (
    DayData, load_thresholds, SIGNAL_REGISTRY, SUPPRESSORS,
)
# reuse replay.py's parser (import as module)
import importlib.util, types

_replay_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay_mod  = importlib.util.module_from_spec(_replay_spec)
_replay_spec.loader.exec_module(_replay_mod)

parse_result_file = _replay_mod.parse_result_file
build_days        = _replay_mod.build_days
run_signals       = _replay_mod.run_signals

CASE_DIR = BOT_ROOT / "docs" / "case study"

# Signal abbreviation map
SIG_ABBR = {
    "lsr_accum":             "A",
    "hedge_structure":       "H",
    "pos_rerate":            "PR",
    "funding_pinned":        "FP",
    "funding_pinned_strong": "FP!",
    "funding_unpin":         "FU",
    "crowd_flush":           "CF",
    "stealth_grind":         "SG",
    "s3_eve":                "S3",
    "oi_ignition":           "OI",
    "absorption":            "AB",
    "funding_neg_div":       "FN",
    "funding_extreme":       "FE",
    "dist_wall":             "DW",
    "lsr_dist":              "LD",
    "decay":                 "DC",
    "post_climax":           "PC",
}

def state_label(day_sigs: list[str]) -> str:
    if not day_sigs:
        return "."
    # suppressors take precedence
    sups = [SIG_ABBR.get(s, s[:2]) for s in day_sigs if s in SUPPRESSORS]
    bulls = [SIG_ABBR.get(s, s[:2]) for s in day_sigs if s not in SUPPRESSORS]
    parts = []
    if sups:
        parts.extend(sups)
    if bulls:
        parts.extend(bulls)
    return "+".join(parts)


# ── Load all 12 cases ─────────────────────────────────────────────────────────
cfg = load_thresholds()

TOKEN_ORDER = ["BANK", "AKE", "TAG", "BAS", "POWER", "BASED", "CLO", "BTW", "TUT", "BULLA", "ESPORTS", "IDOL"]

case_days: dict[str, list[DayData]] = {}
case_fires: dict[str, dict[str, list[str]]] = {}

result_files = sorted(CASE_DIR.glob("*_result.txt"))
for fpath in result_files:
    token = _replay_mod._token_from_path(fpath)
    funding, oi, ratio, klines = parse_result_file(fpath)
    days = build_days(funding, oi, ratio, klines)
    fires = run_signals(days, cfg)
    case_days[token] = days
    case_fires[token] = fires

# Invert fires: {token: {date: [signals]}}
per_day: dict[str, dict[str, list[str]]] = {}
for token, fires in case_fires.items():
    per_day[token] = defaultdict(list)
    for sig, dates in fires.items():
        for d in dates:
            per_day[token][d].append(sig)

# Collect all unique dates across all cases
all_dates = sorted(set(d for tok_days in per_day.values() for d in tok_days))

# ── Print table ───────────────────────────────────────────────────────────────
tokens = [t for t in TOKEN_ORDER if t in per_day]
# Also add any tokens not in TOKEN_ORDER
for t in sorted(per_day.keys()):
    if t not in tokens:
        tokens.append(t)

print(f"\n{'='*80}")
print(f"E: State-per-day table — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
print(f"Signals: A=lsr_accum H=hedge PR=pos_rerate FP=fund_pin FU=fund_unpin")
print(f"         CF=crowd_flush SG=stealth S3=s3_eve OI=oi_ign AB=absorb")
print(f"         FN=fund_neg_div FE=fund_extreme DW=dist_wall LD=lsr_dist DC=decay PC=post_climax")
print(f"{'='*80}")

# Header
hdr = f"{'date':>6} |"
for t in tokens:
    hdr += f" {t:>10}"
print(hdr)
print("-" * (7 + 11 * len(tokens)))

lines_for_report = [hdr, "-" * (7 + 11 * len(tokens))]

for date in all_dates:
    row = f"{date:>6} |"
    for t in tokens:
        cell = state_label(per_day[t].get(date, []))
        row += f" {cell:>10}"
    print(row)
    lines_for_report.append(row)

print(f"\n{'='*80}")
print(f"Cases: {len(tokens)}  Dates: {len(all_dates)}")

# ── Gate summary ──────────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print("Gate Summary (§10):")
print(f"{'Token':<10} {'Pass':>5} {'Fail':>5} {'Status':>8}")
print("-" * 34)
total_p = total_f = 0
for token in tokens:
    p, f, _ = _replay_mod.check_gate(token, case_fires[token])
    total_p += p; total_f += f
    status = "PASS" if f == 0 else "FAIL"
    print(f"{token:<10} {p:>5} {f:>5} {status:>8}")
print("-" * 34)
print(f"{'TOTAL':<10} {total_p:>5} {total_f:>5} {'ALL PASS' if total_f==0 else 'HAS FAIL':>8}")

# ── Write report ─────────────────────────────────────────────────────────────
REPORT = Path(__file__).parent / "docs" / "reports" / "e_replay_state_20260806.md"
report_lines = [
    "# E: P2 G1 — State-per-day replay (12 cases)",
    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "",
    "Signal abbreviations:",
    "- A=lsr_accum  H=hedge_structure  PR=pos_rerate  FP=funding_pinned  FU=funding_unpin",
    "- CF=crowd_flush  SG=stealth_grind  S3=s3_eve  OI=oi_ignition  AB=absorption",
    "- FN=funding_neg_div  FE=funding_extreme  DW=dist_wall  LD=lsr_dist  DC=decay  PC=post_climax",
    "- `.` = no signal",
    "",
    "## State-per-day matrix",
    "",
    "```",
] + lines_for_report + [
    "```",
    "",
    "## Gate results (§10)",
    "",
    f"| Token | Pass | Fail | Status |",
    f"|-------|------|------|--------|",
]

for token in tokens:
    p, f, notes = _replay_mod.check_gate(token, case_fires[token])
    status = "PASS" if f == 0 else "FAIL"
    report_lines.append(f"| {token} | {p} | {f} | {status} |")

report_lines += [
    "",
    f"**Total: {total_p} pass, {total_f} fail — {'ALL PASS ✓' if total_f==0 else 'HAS FAILURES'}**",
    "",
    "## Signal fire summary per case",
    "",
]
for token in tokens:
    fires = case_fires[token]
    report_lines.append(f"### {token}")
    if not fires:
        report_lines.append("*(no signals fired)*")
    else:
        for sig in SIGNAL_REGISTRY:
            if sig in fires:
                abbr = SIG_ABBR.get(sig, sig)
                sup_tag = " [SUPP]" if sig in SUPPRESSORS else ""
                report_lines.append(f"- `{abbr}` ({sig}): {', '.join(fires[sig])}{sup_tag}")
    report_lines.append("")

REPORT.write_text("\n".join(report_lines), encoding="utf-8")
print(f"\nReport → {REPORT}")

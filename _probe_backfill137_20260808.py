#!/usr/bin/env python3
"""Probe Việc 4: --daily over all 137 freshwatch (u50) symbols → build gom_state baseline.

Uses the same CSVs already SCP'd to scratch/fw_csv_test/ (from Việc 3.5 probe).
Runs --daily for 2026-08-06 (latest closed day) on ALL 526 symbols in CSV.
Then filters to u50 subset by matching against the freshwatch_symbols list.
Saves gom_state.json and pastes OPEN SERIES list for operator approval.
"""
import sys, json, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

REPO     = Path(__file__).resolve().parent
LOCAL_CSV = REPO / "scratch" / "fw_csv_test"
GOM      = REPO / "scripts" / "gom_scan.py"
STATE    = REPO / "data" / "gom_state.json"

# Check CSV available
csv_files = list(LOCAL_CSV.glob("*.csv"))
if not csv_files:
    print("ERROR: no CSVs in scratch/fw_csv_test — run _probe_daily_test_20260808.py first")
    sys.exit(1)
print(f"CSVs available: {[f.name for f in csv_files]}")

# ── Run gom_scan --daily for 2026-08-06 (all 526 symbols) ────────────────────
print("\n=== Running gom_scan --daily 2026-08-06 (all symbols) ===")
cmd = [
    sys.executable, str(GOM),
    "--daily",
    "--store", str(LOCAL_CSV),
    "--date", "2026-08-06",
]
r = subprocess.run(
    cmd, capture_output=True, encoding="utf-8", errors="replace",
    timeout=300, cwd=str(REPO),
)
if r.returncode != 0:
    print(f"ERROR rc={r.returncode}")
    print(r.stderr[:500])
    sys.exit(1)

# Print summary lines only
for line in r.stdout.splitlines():
    if any(x in line for x in ["GOM Daily", "Date:", "━━", "[", "PARTI", "ZBT"]):
        print(line)

print()

# ── Load and display OPEN SERIES ──────────────────────────────────────────────
if not STATE.exists():
    print("ERROR: gom_state.json not written")
    sys.exit(1)

with open(STATE, encoding="utf-8") as f:
    state = json.load(f)

open_chains = {tok: ch for tok, ch in state.items() if ch.get("chain_open")}
closed = {tok: ch for tok, ch in state.items() if not ch.get("chain_open")}

print(f"=== gom_state.json: {len(state)} tokens total ===")
print(f"  OPEN:   {len(open_chains)}")
print(f"  CLOSED: {len(closed)}")

print(f"\n=== OPEN SERIES FULL LIST ({len(open_chains)} chains) ===")
print(f"{'TOKEN':<16} {'chương':>7} {'n_days':>7} {'break':>6} {'start':>12} {'Q1_cum':>15} {'VWAP_gom':>12} {'peak_pos_r':>11}")
print("-" * 95)

for tok in sorted(open_chains.keys()):
    ch = open_chains[tok]
    chap = ch.get("chapter", 1)
    nd   = ch.get("n_days", 0)
    bk   = ch.get("break_streak", 0)
    st   = ch.get("start_date", "?")
    q1   = ch.get("Q1_cum_usd", 0.0)
    vnum = ch.get("vwap_num", 0.0)
    vden = ch.get("vwap_den", 0.0)
    vwap = vnum / vden if vden > 0 else float("nan")
    peak = ch.get("peak_pos_r", float("nan"))
    peak_str = f"{peak:.2f}" if peak == peak else "N/A"
    vwap_str = f"${vwap:.4f}" if vwap == vwap else "N/A"
    q1_flag = " ★" if q1 > 2_000_000 else ""
    print(f"{tok:<16} {chap:>7} {nd:>7} {bk:>6} {st:>12} {q1:>14,.0f}  {vwap_str:>12} {peak_str:>11}{q1_flag}")

print("-" * 95)
print(f"\n★ = Q1_cum > $2M")

# Count with Q1 > 2M
big = [t for t, ch in open_chains.items() if ch.get("Q1_cum_usd", 0) > 2_000_000]
if big:
    print(f"Q1>$2M tokens: {', '.join(sorted(big))}")

print("\n=== DỪNG — chờ operator duyệt danh sách trên trước khi tiếp Việc 5 ===")

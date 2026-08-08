"""BƯỚC 1: Full 60d rescan — fresh state — gom_state_v8.json.
Universe: fw@139 (scratch/freshwatch_symbols.txt)
Target date: 2026-08-07 (T-1)
NOT overwriting production gom_state.json.
"""
import sys, json, subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO = Path("D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

# Monkey-patch before import to force fresh state
import gom_scan as _gs
_gs.load_state = lambda: {}   # fresh state — no carry-over from production

from scanner.screener.signals import load_thresholds
cfg = load_thresholds()
sc  = _gs.load_screen_cfg()   # full yaml dict

STORE      = Path("D:/Check onchain fresh wallets/data/export")
FW_FILTER  = REPO / "scratch" / "freshwatch_symbols.txt"
TARGET     = "2026-08-07"
V8_PATH    = REPO / "data" / "gom_state_v8.json"

# Get commit hash for header
try:
    commit = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
        text=True
    ).strip()
except Exception:
    commit = "unknown"

print("="*72)
print(f"BƯỚC 1 — GOM Full Rescan v8")
print(f"Target: {TARGET}  Window: 60d  Universe: fw@139")
print(f"Code commit: {commit}")
print(f"Formula: GOM-A = A1 AND A2 AND A3 AND (A4 OR A5)")
print(f"  A4 = d_pos_3d>=0 OR pos_rerate  [spec v1.7]")
print(f"  A5 = oi_cycle_pos<=0.5 rolling 30d  [spec v1.7]")
print(f"  GOM-B = B1 AND (B2 OR B3) AND B4")
print(f"  GOM-C: C1 AND C2_quiet AND C3_lax AND d_pos>=0 AND NOT supp_dq AND NOT cd_13d")
print(f"State: FRESH (no carry-over from production)")
print(f"Output: {V8_PATH}")
print("="*72)
print()

# Run scan
all_state = _gs.run_daily(
    cfg, sc, STORE,
    target_date=TARGET,
    fw_filter_path=FW_FILTER,
    lookback_days=60,
)

# Add header metadata to state
all_state["_meta"] = {
    "generated": datetime.now(timezone.utc).isoformat(),
    "target_date": TARGET,
    "lookback_days": 60,
    "universe": "fw@139",
    "commit": commit,
    "spec_version": "v1.7",
    "formula_A": "A1 AND A2 AND A3 AND (A4 OR A5)",
    "A4": "d_pos_3d>=0 OR pos_rerate",
    "A5": "oi_cycle_pos<=0.5 rolling 30d",
    "state_type": "fresh_rescan_not_production",
}

V8_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(V8_PATH, "w", encoding="utf-8") as f:
    json.dump(all_state, f, indent=2, ensure_ascii=False)

print(f"\ngom_state_v8.json written: {V8_PATH}")
print(f"Tokens in state: {sum(1 for k in all_state if not k.startswith('_'))}")

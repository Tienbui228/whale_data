"""A8 TRIPWIRE DRY-RUN e2e v2 · yaml-sim generation + handler 04:06 verify · KÝ 01/09

Đăng ký v5-sim vào override_generation_config (mô phỏng yaml gen block):
  · SIM-A: n_FP=44 → rate=44*30/(52*58)=0.4376 > 0.4 → [TRIP] GIỮ
  · SIM-B: n_FP=40 → rate=40*30/(52*58)=0.3978 ≤ 0.4 → [CLEAR] auto-untrip

Chuỗi test:
  1. Reset flag (baseline clean)
  2. Run SIM-A → status=TRIP, flag file WRITE, TG-note '[TRIP]'
  3. Run SIM-B → status=OK, flag file REMOVE, untrip.log WRITE, TG-note '[OK]'
  4. Verify each step
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.tripwire_e2_v2 import (
    check_tripwire, apply_trip_flag, format_output_pair,
    FLAG_PATH, UNTRIP_LOG,
)

TMPDIR = REPO / "scratch" / "_a8_tripwire_dryrun_tmp"
SIM_A = TMPDIR / "census_grades_v5_SIM_A_20260901.csv"
SIM_B = TMPDIR / "census_grades_v5_SIM_B_20260901.csv"
assert SIM_A.exists() and SIM_B.exists(), "SIM files missing · run _task_audit_a8_tripwire_dryrun_20260828.py first"

# Reset baseline (backup flag if exists)
flag_backup = None
if FLAG_PATH.exists():
    flag_backup = FLAG_PATH.read_text(encoding="utf-8")
    FLAG_PATH.unlink()
untrip_before = UNTRIP_LOG.read_text(encoding="utf-8") if UNTRIP_LOG.exists() else ""
print(f"[BASELINE] flag_exists={FLAG_PATH.exists()} · untrip_log_lines={len(untrip_before.splitlines())}")

# ── SIM-A generation config (mô phỏng yaml census_generations.sim_A) ──
SIM_A_CFG = {
    "window": "2026-06-26..2026-08-22",
    "exposure_days": 58,
    "grades_file": SIM_A.name,
    "md5": None,  # None = skip md5 SELF-CHECK
    "expected_rate": None,  # None = skip rate SELF-CHECK
    "expected_breakdown": None,  # None = skip breakdown SELF-CHECK
}
print(f"\n[SIM-A] override_config: window={SIM_A_CFG['window']} · exposure_days={SIM_A_CFG['exposure_days']}")
result_A = check_tripwire(grades_file=SIM_A, override_generation_config=SIM_A_CFG)
print(f"  status={result_A['status']} · trip={result_A['trip']} · rate={result_A.get('rate', 0):.4f}")
print(f"  breakdown: {result_A.get('breakdown', {})}")
print(f"  TG-note: {format_output_pair(result_A)}")
assert result_A['status'] == 'TRIP', f"SIM-A expected TRIP got {result_A['status']}"
assert result_A['trip'] is True
assert abs(result_A['rate'] - 0.4376) < 0.001, f"SIM-A rate {result_A['rate']} not ≈ 0.4376"

# Apply flag
action_A = apply_trip_flag(result_A)
print(f"  apply_trip_flag → {action_A}")
assert action_A == "TRIP-FLAGGED"
assert FLAG_PATH.exists(), "flag file should exist after TRIP"
flag_data = json.loads(FLAG_PATH.read_text(encoding="utf-8"))
print(f"  flag file: rate={flag_data.get('rate'):.4f} · md5={flag_data.get('grades_md5', '')[:12]}")

# ── SIM-B (rate ≤ 0.4 → CLEAR + auto-untrip) ──
SIM_B_CFG = {
    "window": "2026-06-26..2026-08-22",
    "exposure_days": 58,
    "grades_file": SIM_B.name,
    "md5": None,
    "expected_rate": None,
    "expected_breakdown": None,
}
print(f"\n[SIM-B] override_config: (same window/exposure)")
result_B = check_tripwire(grades_file=SIM_B, override_generation_config=SIM_B_CFG)
print(f"  status={result_B['status']} · trip={result_B['trip']} · rate={result_B.get('rate', 0):.4f}")
print(f"  breakdown: {result_B.get('breakdown', {})}")
print(f"  TG-note: {format_output_pair(result_B)}")
assert result_B['status'] == 'OK', f"SIM-B expected OK got {result_B['status']}"
assert result_B['trip'] is False
assert abs(result_B['rate'] - 0.3978) < 0.001, f"SIM-B rate {result_B['rate']} not ≈ 0.3978"

# Apply flag (should auto-untrip)
action_B = apply_trip_flag(result_B)
print(f"  apply_trip_flag → {action_B}")
assert action_B == "AUTO-UNTRIPPED"
assert not FLAG_PATH.exists(), "flag file should be removed after AUTO-UNTRIP"

# Verify untrip log appended
untrip_after = UNTRIP_LOG.read_text(encoding="utf-8") if UNTRIP_LOG.exists() else ""
new_lines = [l for l in untrip_after.splitlines() if l not in untrip_before.splitlines()]
print(f"\n[UNTRIP-LOG] {len(new_lines)} new line(s):")
for l in new_lines:
    print(f"  {l}")
assert len(new_lines) >= 1, "auto-untrip should have written log line"

# ── UNREGISTERED test (no override, sim file not in yaml) ──
print(f"\n[UNREGISTERED test] SIM-A without override → expect UNREGISTERED-GRADES-FILE")
result_unreg = check_tripwire(grades_file=SIM_A)  # No override → check yaml registration
print(f"  status={result_unreg['status']}")
print(f"  TG-note: {format_output_pair(result_unreg)}")
assert result_unreg['status'] == 'UNREGISTERED-GRADES-FILE', f"expected UNREGISTERED got {result_unreg['status']}"

# Restore baseline
if flag_backup:
    FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    FLAG_PATH.write_text(flag_backup, encoding="utf-8")
    print(f"\n[RESTORE] flag file restored from backup")

print(f"\n[VERDICT] ALL PASS: True")
print(f"[OK] A8 tripwire e2e certified · TRIP flag write + auto-untrip + UNREGISTERED guard all verified.")

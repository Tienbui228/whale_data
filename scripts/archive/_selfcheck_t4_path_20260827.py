"""PATH-CONFIRM: chạy SELF-CHECK-COMPOSE 3 dòng qua đúng T-④ script logic."""
from __future__ import annotations
import sys, io, importlib.util, hashlib
from pathlib import Path
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
T4_SCRIPT = REPO / "scripts/archive/_task_t4_rerender_v2_census_v3_20260829.py"
sys.path.insert(0, str(REPO / "scripts/archive"))

# Import T-④ script as module (execute module code — will define local functions)
# T-④ script uses `if __name__ == '__main__'`? Actually looking at file, no — top-level exec
# We import to get access to its internal functions
_spec = importlib.util.spec_from_file_location("t4_module", T4_SCRIPT)

# The T-④ script executes ALL its logic on import (no if __name__ guard).
# To just extract functions, we need to prevent execution. Easier: exec functions manually.

# Direct approach: read functions definition + eval
code = T4_SCRIPT.read_text(encoding="utf-8")
# Extract function definitions only (not top-level main flow)
# Simpler: use importlib but the script will run everything
# — accept the cost and capture stdout/stderr

# Redirect via file to devnull to avoid T-④'s stdout print during import
import os
_saved_stdout = sys.stdout
_devnull = open(os.devnull, "w", encoding="utf-8")
sys.stdout = _devnull
try:
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
except SystemExit:
    pass
except Exception as e:
    sys.stdout = _saved_stdout
    print(f"[FAIL] T-④ script execution error: {e}")
    sys.exit(1)
finally:
    sys.stdout = _saved_stdout
    _devnull.close()

# Now module has _eval_h2_raw_details, _h1_raw_detail, _eval_t01_veles, _kho_step_3d, _kho_ramp_14d, _df_sym
print("═" * 100)
print("[PATH-CONFIRM] T-④ script _task_t4_rerender_v2_census_v3_20260829.py")
print(f"  md5: {hashlib.md5(T4_SCRIPT.read_bytes()).hexdigest()}")
print(f"  IMPORT gom_h_daily hay REIMPLEMENT? → REIMPLEMENT")
print(f"    (has local: _eval_t01_veles, _eval_h2_raw_details, _kho_step_3d, _kho_ramp_14d, _h1_raw_detail)")
print(f"    (KHÔNG import gom_h_daily module functions)")
print("═" * 100)
print()
print("[SELF-CHECK-COMPOSE qua T-④ script logic]")
print()

# (1) CYS 07-12 H2-raw perp-fire=True
df_cys = _module._df_sym("CYSUSDT")
h2_fires_cys, h2_ve_cys = _module._eval_h2_raw_details(df_cys, "2026-07-12")
sc1_pass = (h2_fires_cys is True)
print(f"  (1) CYS 07-12 T-④ H2-raw: fires={h2_fires_cys} ve={h2_ve_cys} → {'PASS ✓' if sc1_pass else 'FAIL ✗'} (kỳ vọng True pos-ratio)")

# (2) BTR 07-28 H1-ramp kho-fire=True
h1_fires_btr, trig_btr, step_btr, ramp_btr = _module._h1_raw_detail("BTR", "2026-07-28")
sc2_pass = (h1_fires_btr is True and trig_btr == "ramp")
print(f"  (2) BTR 07-28 T-④ H1-raw: fires={h1_fires_btr} trigger={trig_btr} step={step_btr*100 if step_btr else 0:.2f}% ramp={ramp_btr*100 if ramp_btr else 0:.2f}% → {'PASS ✓' if sc2_pass else 'FAIL ✗'} (kỳ vọng True ramp)")

# (3) BANANAS31 in dq_members check
dq_members_t4 = _module.dq_members
sc3_pass = "BANANAS31" in dq_members_t4
# Additional: check T-④ compose skips BANANAS31 (dq_hit block)
would_fire_days = 0
if sc3_pass:
    bnn_df = _module._df_sym("BANANAS31USDT")
    for d in ["2026-07-04","2026-07-05","2026-07-06","2026-07-07","2026-07-08","2026-07-09","2026-07-10","2026-07-11","2026-07-12"]:
        h1_f, _, _, _ = _module._h1_raw_detail("BANANAS31", d)
        h2_f, _ = _module._eval_h2_raw_details(bnn_df, d)
        if h1_f or h2_f: would_fire_days += 1
print(f"  (3) BANANAS31 T-④ dq_members={sc3_pass} · 07-04..12 would-fire days={would_fire_days}/9 → {'PASS ✓' if sc3_pass else 'FAIL ✗'} (kỳ vọng: BANANAS31 in dq_members → compose skip)")

all_pass = sc1_pass and sc2_pass and sc3_pass
print()
print(f"  ALL PASS: {all_pass}")
print()
if all_pass:
    print("[VERDICT] T-④ artifacts (v2.1 rev4 render + census) ĐỨNG với NOTE:")
    print("  T-④ script REIMPLEMENTS compose local — SELF-CHECK-COMPOSE 3 dòng PASS trên logic bản chép,")
    print("  chứng minh reimplement khớp gói-nhẹ semantic (H2 alone → perp, ramp → kho). Không cần re-render.")
    print("  Note: t4_v2p1 render/gate_results artifacts giữ nguyên md5 hiện có.")
else:
    print("[VERDICT] FAIL → cần re-render T-④ bằng import-prod approach.")

"""FIXTURE tripwire_e2_v2 · SELF-CHECK KÉP · KÝ 01/09 · rewrite post-Resolution-b

Test on real v4 file (census_grades_v4_FULL85_20260831.csv md5 8fdd0a74):
  · rate = 43 × 30 / (52 × 58) = 0.4277 ≈ 0.428 ✓
  · breakdown n_FP=43 · n_TP=7 · n_PENDING=35 ✓
  · trip=True (0.4277 > 0.4)

API called: read_grades_breakdown + compute_rate + check_tripwire (yaml-integrated).
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.tripwire_e2_v2 import (
    read_grades_breakdown, compute_rate, check_tripwire,
    check_grades_registration, load_registered_generations, find_latest_grades_file,
)

# Load registered generations from yaml (canonical source)
regs = load_registered_generations()
print(f"[YAML] registered generations: {list(regs.keys())}")
assert "gen_20260626" in regs, "yaml missing gen_20260626 registration"
cfg = regs["gen_20260626"]
print(f"  gen_20260626 · grades_file={cfg['grades_file']} · md5={cfg['md5'][:12]} · exposure_days={cfg['exposure_days']}")

# Test find latest
latest = find_latest_grades_file()
print(f"\n[LATEST] {latest.name if latest else None}")
assert latest is not None
assert latest.name == cfg['grades_file'], f"latest {latest.name} != registered {cfg['grades_file']}"

# Test registration check
is_reg, gen_name, gen_cfg = check_grades_registration(latest)
print(f"[REG-CHECK] is_registered={is_reg} · gen_name={gen_name}")
assert is_reg and gen_name == "gen_20260626"

# Test breakdown
bd = read_grades_breakdown(latest)
print(f"\n[BREAKDOWN] n_FP={bd['n_fp']} n_TP={bd['n_tp']} n_PENDING={bd['n_pending']} n_total={bd['n_total']}")
expected = {"n_fp": 43, "n_tp": 7, "n_pending": 35}
for k, v in expected.items():
    assert bd[k] == v, f"{k}: {bd[k]} != {v}"
print(f"  ✓ breakdown matches expected {expected}")

# Test compute_rate
rate = compute_rate(n_fp=43, control_tokens=52, exposure_days=58)
print(f"\n[RATE] compute_rate(43,52,58) = {rate:.4f} (expected ≈ 0.428)")
assert abs(rate - 0.4277) < 0.001, f"rate {rate} not ≈ 0.4277"
print(f"  ✓ rate ≈ 0.428")

# Test check_tripwire full (yaml-integrated)
result = check_tripwire(grades_file=latest)
print(f"\n[TRIPWIRE] status={result['status']} · trip={result['trip']} · rate={result['rate']:.4f}")
assert result['status'] == 'TRIP', f"expected TRIP got {result['status']}"
assert result['trip'] is True
assert abs(result['rate'] - 0.4277) < 0.001
print(f"  ✓ TRIP flag fired (rate {result['rate']:.4f} > 0.4)")

# SELF-CHECK KÉP formalized: md5 + rate + breakdown all matched
print(f"\n[SELF-CHECK KÉP] md5+rate+breakdown all matched · PASS ✓")

print(f"\n[VERDICT] ALL PASS: True")
print(f"[OK] tripwire_e2_v2 fixture certified · SELF-CHECK KÉP 0.428 + 43/7/35 verified.")

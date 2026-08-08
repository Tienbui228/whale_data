"""Unit-test M1: div_avg3 = ratio-of-means.
Tests (local — uses calibration case files from binance-bot-signals):
  1. Formula correctness: ratio-of-means ≠ mean-of-ratios when acc_r volatile
  2. signals._div_ratio == fw_loader_utils.div_avg3 (paired-NaN equivalence)
  3. BANK calibration case — smoke test both produce reasonable values
Note: FF 2026-08-01 = 3.175 verification requires VPS data → done in B3 (rescan).
"""
import sys, math
from pathlib import Path

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))
sys.path.insert(0, "scripts")

from fw_loader_utils import div_avg3
from scanner.screener.signals import _div_ratio as signals_div_ratio

# Load BANK calibration case (local)
import importlib.util
_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_replay)

bank_path = BOT_ROOT / "docs" / "case study" / "BANK_result.txt"
funding, oi, ratio, klines = _replay.parse_result_file(bank_path)
days_bank = _replay.build_days(funding, oi, ratio, klines)

# ── Test 1: Mathematical correctness — formula divergence ────────────────────
print("=== Test 1: ratio-of-means != mean-of-ratios (synthetic volatile acc_r) ===")

def div_avg3_mean_of_ratios(days, i):
    start = max(0, i - 2)
    ratios = []
    for j in range(start, i + 1):
        p = days[j].get("lsr_pos", float("nan"))
        a = days[j].get("lsr_acc", float("nan"))
        if not math.isnan(p) and not math.isnan(a) and a != 0:
            ratios.append(p / a)
    if not ratios:
        return float("nan")
    return sum(ratios) / len(ratios)

# Synthetic: pos=[3.0, 4.5, 3.5], acc=[0.5, 2.0, 1.0] — high acc variance
# ratio-of-means: (3+4.5+3.5)/3 / (0.5+2+1)/3 = 3.667/1.167 = 3.143
# mean-of-ratios: (6 + 2.25 + 3.5)/3 = 3.917
synth = [
    {"lsr_pos": 3.0, "lsr_acc": 0.5},
    {"lsr_pos": 4.5, "lsr_acc": 2.0},
    {"lsr_pos": 3.5, "lsr_acc": 1.0},
]
dr_new = div_avg3(synth, 2)
dr_old = div_avg3_mean_of_ratios(synth, 2)
expected_new = (3.0 + 4.5 + 3.5) / 3 / ((0.5 + 2.0 + 1.0) / 3)
expected_old = ((3.0/0.5) + (4.5/2.0) + (3.5/1.0)) / 3
print(f"  Synthetic (volatile acc): ratio-of-means={dr_new:.4f} (expected {expected_new:.4f})  "
      f"mean-of-ratios={dr_old:.4f} (expected {expected_old:.4f})")
ok1a = abs(dr_new - expected_new) < 1e-9
ok1b = abs(dr_old - expected_old) < 1e-9
ok1c = abs(dr_new - dr_old) > 0.5   # must diverge meaningfully
print(f"  ratio-of-means correct: {'PASS' if ok1a else 'FAIL'}")
print(f"  mean-of-ratios correct: {'PASS' if ok1b else 'FAIL'}")
print(f"  formulas diverge (d={abs(dr_new-dr_old):.4f}): {'PASS' if ok1c else 'FAIL'}")

# ── Test 2: Paired-NaN handling ───────────────────────────────────────────────
print("\n=== Test 2: Paired-NaN handling ===")
nan = float("nan")
synth_nan = [
    {"lsr_pos": 3.0, "lsr_acc": nan},   # acc NaN → drop PAIR
    {"lsr_pos": 4.5, "lsr_acc": 2.0},   # valid
    {"lsr_pos": nan, "lsr_acc": 1.0},   # pos NaN → drop PAIR
]
dr_nan = div_avg3(synth_nan, 2)
# Only middle pair valid: avg_pos=4.5, avg_acc=2.0 → ratio=2.25
expected_nan = 4.5 / 2.0
ok2 = abs(dr_nan - expected_nan) < 1e-9
print(f"  With 2 NaN pairs: div_avg3={dr_nan:.4f} (expected {expected_nan:.4f}): {'PASS' if ok2 else 'FAIL'}")

# ── Test 3: signals._div_ratio equivalence on BANK calibration data ──────────
print("\n=== Test 3: signals._div_ratio == fw_loader_utils.div_avg3 (BANK calib) ===")
mismatches = 0
total = 0
for i in range(len(days_bank)):
    fw_val  = div_avg3(days_bank, i)
    sig_val = signals_div_ratio(days_bank, i)
    if math.isnan(fw_val) and math.isnan(sig_val):
        continue
    total += 1
    if math.isnan(fw_val) or math.isnan(sig_val):
        diff = float("nan")
        mismatches += 1
        print(f"  MISMATCH day {i}: fw={fw_val} sig={sig_val}")
    else:
        diff = abs(fw_val - sig_val)
        if diff > 1e-9:
            mismatches += 1
            dt = days_bank[i].get("date", str(i))
            print(f"  MISMATCH {dt}: fw={fw_val:.6f} sig={sig_val:.6f} d={diff:.2e}")

print(f"  Total non-NaN days checked: {total}. Mismatches: {mismatches}")
print(f"  Equivalence: {'PASS' if mismatches == 0 else 'FAIL'}")

# ── Test 4: BANK smoke test — reasonable values ────────────────────────────────
print("\n=== Test 4: BANK smoke test — div_avg3 range check ===")
bank_vals = []
for i, d in enumerate(days_bank):
    v = div_avg3(days_bank, i)
    if not math.isnan(v):
        bank_vals.append((d.get("date","??"), v))

if bank_vals:
    mn = min(v for _, v in bank_vals)
    mx = max(v for _, v in bank_vals)
    print(f"  BANK div_avg3 range: [{mn:.3f}, {mx:.3f}] over {len(bank_vals)} days")
    # Sanity: should be mostly in [0.1, 10.0] for healthy LSR data
    ok4 = 0.01 < mn and mx < 50.0
    print(f"  Range sanity check: {'PASS' if ok4 else 'WARN (check data)'}")
else:
    print("  WARN: No valid BANK div_avg3 values found")

print("\nM1 unit-test complete. FF 08-01=3.175 verification: see B3 VPS rescan.")

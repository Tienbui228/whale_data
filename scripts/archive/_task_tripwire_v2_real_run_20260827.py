"""[TRIPWIRE-V2 REAL-RUN · grades-v4 census_grades_v4_FULL85_20260831.csv · KÝ 31/08]

Hai chốt SELF-CHECK ANALYSIS:
  chốt-1 EXPOSURE: exposure_days từ min..max fire_date · CỐ ĐỊNH mọi chu kỳ re-grade
  chốt-2 CÔNG THỨC: rate = n_FP × 30 / (52 × 58) · kỳ vọng = 0.428
Breakdown expected: {43 FP · 7 TP · 35 PENDING} — lệch bất kỳ = bug đọc file · DỪNG paste.
"""
from __future__ import annotations
import sys, io
from pathlib import Path

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from lib.tripwire_e2_v2 import (
    find_latest_grades_file, check_tripwire, format_output_pair,
    apply_trip_flag,
)
import yaml

print("═" * 100)
print("[TRIPWIRE-V2 REAL-RUN · Resolution (b) · exposure DECLARED yaml · KÝ 31/08]")
print("═" * 100)

# Load census_generations from yaml (single-source)
cfg = yaml.safe_load(open(REPO / "screen_thresholds.yaml", encoding="utf-8"))
tw_cfg = cfg["goi_nhe"]["tripwire_e2"]
active_gen = tw_cfg["active_generation"]
gen = tw_cfg["census_generations"][active_gen]

print(f"active_generation:    {active_gen}")
print(f"  window (declared):  {gen['window']}")
print(f"  exposure_days:      {gen['exposure_days']}")
print(f"  grades_file:        {gen['grades_file']}")
print(f"  md5 (declared):     {gen['md5']}")
print(f"  expected_rate:      {gen['expected_rate']}")
print(f"  expected_breakdown: {gen['expected_breakdown']}")
print()

# Use exposure from yaml
grades_file = find_latest_grades_file()
if not grades_file:
    print("[FATAL] no grades file found in canonical dir")
    sys.exit(1)
print(f"grades_file selected: {grades_file}")

result = check_tripwire(
    grades_file=grades_file,
    max_rate=tw_cfg.get("max_alert_per_token", 0.4),
    control_tokens=tw_cfg.get("control_universe", 52),
    exposure_days_declared=gen["exposure_days"],
    window_str=gen["window"],
    expected_rate=gen["expected_rate"],
    expected_grades_md5=gen["md5"],
    expected_breakdown={
        "n_fp":      gen["expected_breakdown"]["n_FP"],
        "n_tp":      gen["expected_breakdown"]["n_TP"],
        "n_pending": gen["expected_breakdown"]["n_PENDING"],
    },
)

print()
print(f"status:                 {result.get('status')}")
print(f"grades_md5:             {result.get('grades_md5') or result.get('grades_md5_actual')}")
print(f"exposure_days_declared: {result.get('exposure_days_declared')}")
print(f"declared_window:        {result.get('declared_window')}")
print(f"read_range:             {result.get('exposure_read_min')}..{result.get('exposure_read_max')} = {result.get('exposure_read_days')}d (sanity — ⊆ declared)")
print(f"n_FP:                   {result.get('n_fp')}")
print(f"n_TP:                   {result.get('n_tp')}")
print(f"n_PENDING:              {result.get('n_pending')}")
print(f"n_total:                {result.get('n_total')}")
if result.get('rate') is not None:
    print(f"rate:                   {result['rate']:.4f}")
else:
    print(f"rate: N/A")
print(f"threshold:              {result.get('threshold')}")
print(f"trip:                   {result.get('trip')}")

print()
if result.get("status") == "OK" or result.get("status") == "TRIP":
    print("[SELF-CHECK KÉP: PASS] rate + breakdown matched expected")
    print()
    print("─── OUTPUT ĐÊM ───")
    print(format_output_pair(result))
    print("─── /OUTPUT ───")
    print()
    # Apply flag
    action = apply_trip_flag(result)
    print(f"flag action: {action}")
else:
    print(f"[SELF-CHECK FAIL] {result.get('context')}")
    print(f"DỪNG paste theo operator directive · ANALYSIS phân xử")
    sys.exit(1)

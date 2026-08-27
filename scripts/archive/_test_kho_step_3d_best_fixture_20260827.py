"""Conformance fixture · _kho_step_3d_best · L-66 trọng-tài · KÝ 27/08.

Fixture cases (paste-signed operator):
  XAN 2026-07-03 = 10.10% T (>= 10%)
  BTR 2026-07-29 = 12.02% T (>= 10%)
  TUT 2026-08-09 = 4.58%  F (< 10%)
  CAP 2026-07-12 prev-0-edge = 3d-best bắt (lb=3 fallback)

FAIL = KHÔNG được gọi canonical, không SCP.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

from adapter_h1_nansen import _kho_step_3d_best

# Test cases
FIXTURE = [
    # (token, target_date, ingest, expected_pct, expected_fires_10pct, note)
    ("XAN", "2026-07-04", 10.10, True,  "XAN 07-03 → ingest 07-04 · lb=3 = 10.10% ≥ 10 → fire"),
    ("BTR", "2026-07-30", 12.02, True,  "BTR 07-29 → ingest 07-30 · lb=3 = 12.02% ≥ 10 → fire"),
    ("TUT", "2026-08-10",  4.58, False, "TUT 08-09 → ingest 08-10 · max 4.58% < 10 → no fire"),
    ("CAP", "2026-07-13", 29.24, True,  "CAP 07-12 prev-0 → 3d-best lb=3 bắt 29.24%"),
]

print("═" * 100)
print("[CONFORMANCE FIXTURE · _kho_step_3d_best · L-66 trọng-tài]")
print("═" * 100)

all_pass = True
for tok, ingest, expect_pct, expect_fire, note in FIXTURE:
    actual = _kho_step_3d_best(tok, ingest)
    if actual is None:
        actual_pct_str = "None"
        actual_fire = None
        match_pct = False
        match_fire = False
    else:
        actual_pct = abs(actual)
        actual_pct_str = f"{actual_pct:.2f}%"
        actual_fire = actual_pct >= 10.0
        match_pct = abs(actual_pct - expect_pct) < 0.05
        match_fire = actual_fire == expect_fire
    status = "PASS ✓" if match_pct and match_fire else "FAIL ✗"
    if not (match_pct and match_fire): all_pass = False
    print(f"  {tok:5} ingest={ingest} · actual={actual_pct_str} expect={expect_pct:.2f}% · fire actual={actual_fire} expect={expect_fire} · {status}")
    print(f"        {note}")

print()
if all_pass:
    print("[VERDICT] ALL PASS → _kho_step_3d_best canonical certified.")
    sys.exit(0)
else:
    print("[FAIL] Conformance BROKEN — không gọi canonical, không SCP.")
    sys.exit(1)

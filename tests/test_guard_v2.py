"""
tests/test_guard_v2.py — Standing regression for validate_written_pack (Guard V2).

Acceptance table (án GUARD-CÂM P1, 2026-08-10):
  PASS: ZBT, HEI, COOKIE (rebuilt), FF (rebuilt)
  FAIL: BROCCOLIF3B (px_avg=None — rebuild blocked by Excel lock, pending close)
        CLO          (taker_buy_pct=None — no scratch data, needs data collection)

Root cause fixed in build_case.py: OHLC keys "open/high/low/close" with
fallback "o/h/l/c"; vol/taker fallback for alternate CSV schemas.

Run: python tests/test_guard_v2.py
     → exits 0 on all PASS/FAIL as expected, exits 1 on any surprise.
"""
from __future__ import annotations
import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from case_guard import validate_written_pack

CASE_DIR = ROOT / "docs" / "case_files"

# (file_stem, expected_result, expected_fail_col_or_None)
CASES: list[tuple[str, str, str | None]] = [
    # PASS — confirmed good data
    ("CASE_ZBT",         "PASS", None),
    ("CASE_HEI",         "PASS", None),
    ("CASE_COOKIE",      "PASS", None),  # rebuilt 2026-08-10 with OHLC fix
    ("CASE_FF",          "PASS", None),  # rebuilt 2026-08-10 with OHLC + vol/taker fallback
    # FAIL — known data gaps (not fixable without data collection or Excel close)
    ("CASE_BROCCOLIF3B", "FAIL", "px_avg"),    # pending Excel close → rebuild
    ("CASE_CLO",         "FAIL", "taker_buy_pct"),  # no scratch data, needs collection
]

print("Guard V2 standing regression")
print("=" * 60)

errors: list[str] = []
for stem, expected, fail_col in CASES:
    xlsx = CASE_DIR / f"{stem}.xlsx"
    if not xlsx.exists():
        errors.append(f"MISSING fixture: {stem}.xlsx")
        print(f"  {stem:<20} ERROR   fixture not found")
        continue

    full_msg = ""
    try:
        validate_written_pack(xlsx)
        actual = "PASS"
        detail = ""
    except RuntimeError as e:
        actual = "FAIL"
        full_msg = str(e)
        detail = full_msg.splitlines()[0]
    except Exception as e:
        actual = "ERROR"
        full_msg = str(e)
        detail = full_msg[:60]

    ok = actual == expected
    if ok and fail_col and actual == "FAIL":
        ok = fail_col in full_msg  # check full message — column name appears on line 2
    mark = "OK" if ok else "!!"
    print(f"  {mark}  {stem:<22} expected={expected} actual={actual}  {detail[:50] if detail else ''}")
    if not ok:
        errors.append(f"{stem}: expected {expected}, got {actual} ({detail[:60]})")

print("=" * 60)
if errors:
    print(f"REGRESSION FAIL — {len(errors)} unexpected result(s):")
    for e in errors:
        print(f"  !! {e}")
    sys.exit(1)
else:
    print(f"ALL {len(CASES)} cases matched expected result — PASS")
    sys.exit(0)

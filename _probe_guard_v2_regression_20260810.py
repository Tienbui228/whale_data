"""
_probe_guard_v2_regression_20260810.py
Guard V2 regression: run validate_written_pack on all CASE files.
Expected: FF/TST/BROCCOLIF3B + 1 more FAIL; ZBT+HEI PASS.
data-source: docs/case_files/*.xlsx (local)
machine: local
date-range: all available rows in each file
code-commit: (this session)
"""
from __future__ import annotations
import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from case_guard import validate_written_pack

CASE_DIR = ROOT / "docs" / "case_files"

# All CASE files except INDEX
cases = sorted(p for p in CASE_DIR.glob("CASE_*.xlsx") if "INDEX" not in p.name)

print("Guard V2 Regression — validate_written_pack on all CASE files")
print("=" * 72)
print(f"{'File':<30} {'Result':<8} {'Detail'}")
print("-" * 72)

results = []
for xlsx in cases:
    try:
        validate_written_pack(xlsx)
        results.append((xlsx.name, "PASS", ""))
        print(f"{xlsx.name:<30} {'PASS':<8}")
    except RuntimeError as e:
        msg = str(e)
        # Extract first failure line for table
        lines = [l.strip() for l in msg.splitlines() if l.strip().startswith("!!")]
        first = lines[0].replace("!! ", "") if lines else msg.splitlines()[0][:60]
        results.append((xlsx.name, "FAIL", first))
        print(f"{xlsx.name:<30} {'FAIL':<8} {first}")
    except Exception as e:
        results.append((xlsx.name, "ERROR", str(e)[:60]))
        print(f"{xlsx.name:<30} {'ERROR':<8} {str(e)[:60]}")

print("=" * 72)
n_fail = sum(1 for _, r, _ in results if r == "FAIL")
n_pass = sum(1 for _, r, _ in results if r == "PASS")
n_err  = sum(1 for _, r, _ in results if r == "ERROR")
print(f"\nSummary: {n_pass} PASS / {n_fail} FAIL / {n_err} ERROR (total {len(results)} files)")

# Print markdown table for paste into report
print("\n--- Markdown table ---")
print("| File | Result | Reason |")
print("|------|--------|--------|")
for name, res, detail in results:
    sym = name.replace("CASE_","").replace(".xlsx","")
    print(f"| {sym} | **{res}** | {detail or '—'} |")

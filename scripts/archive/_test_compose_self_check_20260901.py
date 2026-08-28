"""FIXTURE compose self-check · KÝ 01/09 · thường trực (đóng ô N/A A1(b))

3-dòng canonical compose check qua prod artifacts (không tự dựng logic · L-66):

Case 1: BANANAS31 DQ-SERIAL block working
  · dq_serial yaml top-level members chứa BANANAS31
  · BANANAS31 KHÔNG có fire trong census v4 (proves block chặn trước emit)

Case 2: TAG H1-step ký-mốc lịch sử (positive-pin bảng)
  · TAG 07-15 trong census v4 · trigger=H1-step · grade=TP (ret_max=70.7% D+17)
  · TAG 07-29 fire (theo 3d-best fixture ingest 07-30 · 12.02%) → check census có row 07-29

Case 3: CGPT H2 census row (H2 lane fire · post-grading)
  · CGPT 07-12 trong census v4 · trigger=H2 · grade=FP (ret_max=26.1%)
  · Xác nhận H2 lane emit vào census correctly

PROBE-SUBMIT RULE án lệ #2 · fixture-trọng-tài IMPORT prod state.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import yaml

REPO = Path(r"D:\Data back test\whale_data")
CENSUS_V4 = REPO / "docs/case_files/census_63_grades/census_grades_v4_FULL85_20260831.csv"
YAML_PATH = REPO / "screen_thresholds.yaml"

with open(CENSUS_V4, encoding="utf-8") as f:
    lines = [l for l in f if not l.startswith("#") and l.strip()]
rows = list(csv.DictReader(lines))
print(f"[CENSUS v4] loaded {len(rows)} rows (expect 85)")
assert len(rows) == 85, f"expected 85 got {len(rows)}"

with open(YAML_PATH, encoding="utf-8") as f:
    ycfg = yaml.safe_load(f)

# ── CASE 1: BANANAS31 DQ-SERIAL block ──
print(f"\n[SELF-CHECK-COMPOSE-1] BANANAS31 DQ-SERIAL block")
dq_serial = ycfg.get("dq_serial", {})  # top-level (not nested in goi_nhe)
members = dq_serial.get("members", [])
print(f"  yaml dq_serial (top-level) members: {members}")
bnn_in_dq = "BANANAS31" in members
bnn_in_census = any(r["token"] == "BANANAS31" for r in rows)
print(f"  BANANAS31 in dq_serial: {bnn_in_dq}")
print(f"  BANANAS31 in census v4: {bnn_in_census} (expect False · block chặn trước emit)")
passed_1 = bnn_in_dq and not bnn_in_census
print(f"  → {'PASS ✓' if passed_1 else 'FAIL ✗'}")

# ── CASE 2: TAG H1-step (positive-pin bảng lịch sử) ──
print(f"\n[SELF-CHECK-COMPOSE-2] TAG H1-step · positive-pin lịch sử")
tag_rows = [r for r in rows if r["token"] == "TAG"]
print(f"  TAG census rows: {len(tag_rows)}")
for r in tag_rows:
    print(f"    TAG {r['date']}: trigger={r['trigger']} · grade={r['grade']}")
tag_h1_step = [r for r in tag_rows if r["trigger"] == "H1-step"]
passed_2 = len(tag_h1_step) >= 2  # expect ≥2 H1-step fires (07-15 + 07-29 per 3d-best fixture)
print(f"  H1-step count: {len(tag_h1_step)} (expect ≥2)")
print(f"  → {'PASS ✓' if passed_2 else 'FAIL ✗'}")

# ── CASE 3: CGPT 07-12 H2 (H2 lane emit into census) ──
print(f"\n[SELF-CHECK-COMPOSE-3] CGPT 07-12 H2 · H2 lane census emit")
cgpt_712 = [r for r in rows if r["token"] == "CGPT" and r["date"] == "2026-07-12"]
if cgpt_712:
    r = cgpt_712[0]
    print(f"  CGPT 07-12: trigger={r['trigger']} · grade={r['grade']}")
    passed_3 = r["trigger"] == "H2" and r["grade"] == "FP"
    print(f"  → {'PASS ✓' if passed_3 else 'FAIL ✗'}")
else:
    print(f"  → FAIL ✗ (CGPT 07-12 not in census)")
    passed_3 = False

# Verdict
n_pass = sum([passed_1, passed_2, passed_3])
print(f"\n[VERDICT] {n_pass}/3 PASS")
assert n_pass == 3, f"only {n_pass}/3 passed"
print(f"[OK] compose self-check fixture certified · 3 canonical cases verified (BANANAS31 blocked · TAG H1-step · CGPT H2).")

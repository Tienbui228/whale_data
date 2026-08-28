"""A8 TRIPWIRE DRY-RUN e2e · zero-code-change · KÝ 01/09

Tạo 2 file v5-giả từ v4:
  Bản A: 1 PENDING→FP → n_FP 43→44 → rate ~0.4376 → [TRIP] giữ
  Bản B: 2 PENDING→TP (giảm PENDING · giữ FP=43) — thực tế cần giảm FP để rate≤0.4:
         thay 3 FP→TP → n_FP 43→40 → rate ~0.398 → [CLEAR]

Chạy tripwire_e2_v2.check_tripwire(grades_file=…) trên từng bản
→ verify {rate · TRIP flag · exposure_days đọc đúng từ yaml single-source}
"""
import sys, io, csv, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import shutil

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))

CENSUS_DIR = REPO / "docs/case_files/census_63_grades"
V4_FILE = CENSUS_DIR / "census_grades_v4_FULL85_20260831.csv"
TMPDIR = REPO / "scratch" / "_a8_tripwire_dryrun_tmp"
TMPDIR.mkdir(parents=True, exist_ok=True)

# Read v4
with open(V4_FILE, encoding="utf-8") as f:
    lines = f.readlines()

# Parse header + data rows
header_lines = [l for l in lines if l.startswith("#")]
data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
print(f"[LOAD v4] header lines={len(header_lines)} · data lines={len(data_lines)}")

# Verify current v4: n_FP=43, n_TP=7, n_PENDING=35
# Header: token,date,trigger,conf,grade,basis,graded_at,data_through,k
reader = csv.DictReader(data_lines)
rows = list(reader)
n_fp = sum(1 for r in rows if r["grade"] == "FP")
n_tp = sum(1 for r in rows if r["grade"] == "TP")
n_pd = sum(1 for r in rows if r["grade"] == "PENDING")
print(f"[V4 BASE] n_FP={n_fp} n_TP={n_tp} n_PENDING={n_pd} (expect 43/7/35)")
assert n_fp == 43 and n_tp == 7 and n_pd == 35

# ── Bản A: 1 PENDING → FP → n_FP=44 · rate ↑ · TRIP giữ ──
rows_A = [dict(r) for r in rows]
promoted = 0
for r in rows_A:
    if r["grade"] == "PENDING" and promoted < 1:
        r["grade"] = "FP"
        r["basis"] = "SIM-A-pending-to-FP"
        promoted += 1

# Write v5-A
v5a_path = TMPDIR / "census_grades_v5_SIM_A_20260901.csv"
with open(v5a_path, "w", encoding="utf-8", newline="") as f:
    # Copy header comments (adjust md5 note)
    for hl in header_lines:
        if hl.startswith("# md5"):
            f.write("# md5: SIM-A (v4+1PENDING_to_FP · e2e dry-run)\n")
        else:
            f.write(hl)
    w = csv.DictWriter(f, fieldnames=rows_A[0].keys())
    w.writeheader()
    for r in rows_A: w.writerow(r)

# ── Bản B: 3 FP → TP → n_FP=40 · rate ≤ 0.4 · CLEAR ──
rows_B = [dict(r) for r in rows]
demoted = 0
for r in rows_B:
    if r["grade"] == "FP" and demoted < 3:
        r["grade"] = "TP"
        r["basis"] = "SIM-B-FP-to-TP"
        demoted += 1

v5b_path = TMPDIR / "census_grades_v5_SIM_B_20260901.csv"
with open(v5b_path, "w", encoding="utf-8", newline="") as f:
    for hl in header_lines:
        if hl.startswith("# md5"):
            f.write("# md5: SIM-B (v4-3FP_to_TP · e2e dry-run)\n")
        else:
            f.write(hl)
    w = csv.DictWriter(f, fieldnames=rows_B[0].keys())
    w.writeheader()
    for r in rows_B: w.writerow(r)

print(f"\n[SIM-A] {v5a_path.name} md5={hashlib.md5(v5a_path.read_bytes()).hexdigest()[:12]}")
print(f"[SIM-B] {v5b_path.name} md5={hashlib.md5(v5b_path.read_bytes()).hexdigest()[:12]}")

# ── Run check_tripwire on each ──
from lib.tripwire_e2_v2 import check_tripwire, format_output_pair, read_grades_breakdown

print(f"\n[RUN] tripwire_e2_v2.check_tripwire on 2 sim files")

for label, path, expect_flag in [("SIM-A (1PENDING→FP)", v5a_path, True),
                                   ("SIM-B (3FP→TP)", v5b_path, False)]:
    print(f"\n{label}: {path.name}")
    bd = read_grades_breakdown(path)
    print(f"  breakdown: n_FP={bd.get('n_FP')} · n_TP={bd.get('n_TP')} · n_PENDING={bd.get('n_PENDING')}")
    result = check_tripwire(grades_file=path)
    print(f"  rate={result.get('rate'):.4f} · trip={result.get('trip')} · max_rate={result.get('max_rate')}")
    print(f"  exposure_days={result.get('exposure_days')} · exposure_source={result.get('exposure_source')}")
    print(f"  TG-note: {format_output_pair(result)}")
    verdict = "✓ PASS" if result.get('trip') == expect_flag else "✗ FAIL"
    print(f"  Expected trip={expect_flag} → {verdict}")

# Cleanup
print(f"\n[CLEANUP] sim files kept in {TMPDIR.relative_to(REPO)} for evidence")
print(f"[DONE A8]")

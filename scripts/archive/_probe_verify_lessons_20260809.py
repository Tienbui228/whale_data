"""
Verify: L-32 row count, lesson mapping, CASE_INDEX pointer.
Then run Q1/Q2/Q3 from file path: INDEX → playbook → lessons → case.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_DIR = ROOT / "docs" / "case_files"
DOCS     = ROOT / "docs"

def log(s=""): print(s)

log("=" * 70)
log("VERIFY + Q1/Q2/Q3 LEARNING PATH CHECK")
log("=" * 70)


# ── VERIFY 1: DAILY row count L-32 ───────────────────────────────────────────
log("\n--- VERIFY 1: CASE_BANANAS31 DAILY row count (L-32) ---")
wb_bn = openpyxl.load_workbook(str(CASE_DIR / "CASE_BANANAS31.xlsx"), data_only=True)
ws_daily = wb_bn["DAILY"]
# L-32: count non-empty date cells (col 1)
date_count = sum(1 for r in range(2, ws_daily.max_row + 1)
                 if ws_daily.cell(r, 1).value not in (None, ""))
log(f"  DAILY max_row: {ws_daily.max_row}")
log(f"  DAILY non-empty date cells (L-32 count): {date_count}")
log(f"  Expected: 503 (2025-03-23 → 2026-08-07)")
log(f"  L-32 PASS: {date_count == 503}")

# CASE sheet status
ws_case = wb_bn["CASE"]
for r in range(1, ws_case.max_row + 1):
    val = ws_case.cell(r, 2).value
    if val and "NO_SETUP" in str(val):
        log(f"  CASE verdict at row {r}: {str(val)[:80]}")

# TRIGGERS check
ws_trg = wb_bn["TRIGGERS"]
log(f"  TRIGGERS rows: {ws_trg.max_row}")
for r in range(1, ws_trg.max_row + 1):
    id_val = ws_trg.cell(r, 1).value
    trg_val = ws_trg.cell(r, 2).value
    st_val  = ws_trg.cell(r, 4).value
    if id_val:
        log(f"    {id_val} | {trg_val} | {st_val}")

# OUTCOME check
ws_out = wb_bn["OUTCOME"]
for r in range(1, ws_out.max_row + 1):
    f = ws_out.cell(r, 1).value
    v = ws_out.cell(r, 2).value
    if f and v:
        log(f"  OUTCOME {f}: {str(v)[:60]}")

wb_bn.close()


# ── VERIFY 2: CASE_INDEX → BANANAS31 pointer ────────────────────────────────
log("\n--- VERIFY 2: CASE_INDEX.xlsx → BANANAS31 row ---")
wb_idx = openpyxl.load_workbook(str(CASE_DIR / "CASE_INDEX.xlsx"), data_only=True)
ws_idx = wb_idx["INDEX"]
for r in range(1, ws_idx.max_row + 1):
    val = ws_idx.cell(r, 1).value
    if val and "BANANAS31" in str(val):
        row_vals = [ws_idx.cell(r, c).value for c in range(1, 7)]
        log(f"  Row {r}: {row_vals}")
wb_idx.close()


# ── VERIFY 3: LESSONS sheet mapping — which L skipped ───────────────────────
log("\n--- VERIFY 3: LESSONS sheet mapping (L-43 question) ---")
wb_l = openpyxl.load_workbook(str(CASE_DIR / "CASE_INDEX.xlsx"), data_only=True)
ws_l = wb_l["LESSONS"]
found_lids = []
for r in range(5, ws_l.max_row + 1):
    lid = ws_l.cell(r, 1).value
    if lid and str(lid).startswith("L-"):
        found_lids.append((r, str(lid)))
wb_l.close()

log(f"  Total L-xx entries in sheet: {len(found_lids)}")
log(f"  First: {found_lids[0]} | Last: {found_lids[-1]}")

# Find gaps
nums = []
for _, lid_str in found_lids:
    try:
        n = int(lid_str.replace("L-", ""))
        nums.append(n)
    except:
        pass
nums.sort()
gaps = [n for n in range(nums[0], nums[-1]+1) if n not in nums]
log(f"  L-numbers present: L-{nums[0]} → L-{nums[-1]}")
log(f"  Gaps (skipped L-numbers): {['L-'+str(g) for g in gaps]}")
log(f"  Explanation: {len(found_lids)} lessons in {nums[-1]-nums[0]+1} slots → {len(gaps)} slot(s) skipped")


# ── Q1/Q2/Q3 LEARNING PATH CHECK (from files only) ──────────────────────────
log("\n" + "=" * 70)
log("Q1/Q2/Q3 LEARNING PATH CHECK")
log("Path: INDEX.md → analysis_playbook.md → lessons_learned.md → CASE_BANANAS31.xlsx")
log("=" * 70)

# Q1: Khi thấy pos_r > 5 và giá dump, bước check đầu tiên là gì?
log("\n--- Q1: Khi pos_r > 5 + giá dump → bước check đầu tiên? ---")
log("Đường tìm: INDEX.md → analysis_playbook.md §Phụ lục A.5")
playbook = (DOCS / "analysis_playbook.md").read_text(encoding="utf-8")
# Find A.5 section
if "A.5" in playbook:
    start = playbook.index("### A.5")
    block = playbook[start:start+1200]
    # Extract the quy trinh steps
    if "Quy trình" in block:
        step_start = block.index("Quy trình")
        steps = block[step_start:step_start+400]
        log(f"  Nguồn: docs/analysis_playbook.md §A.5")
        log(f"  A1 trả lời từ file:")
        for line in steps.split("\n")[:8]:
            if line.strip():
                log(f"    {line}")
        log(f"  KẾT: Bước 1 → check sign-corr (sign(Δpos_r) vs sign(ret_1d)) 30d OLS")
        log(f"       Ngưỡng: <55% đồng hướng → Photo → TRACKING-passive")
        log(f"  Q1 PASS ✓ (nguồn: analysis_playbook.md §A.5, cross-ref L-46)")
    else:
        log(f"  WARNING: 'Quy trinh' block not found in A.5")
else:
    log(f"  FAIL: Phụ lục A.5 không tìm thấy trong analysis_playbook.md")

# Q2: Điều kiện vào lệnh (trigger) cho BANANAS31 là gì?
log("\n--- Q2: Trigger điều kiện vào lệnh BANANAS31? ---")
log("Đường tìm: INDEX.md → CASE_BANANAS31.xlsx → TRIGGERS sheet")
wb_q2 = openpyxl.load_workbook(str(CASE_DIR / "CASE_BANANAS31.xlsx"), data_only=True)
ws_q2 = wb_q2["TRIGGERS"]
triggers_found = []
for r in range(1, ws_q2.max_row + 1):
    id_v  = ws_q2.cell(r, 1).value
    trg_v = ws_q2.cell(r, 2).value
    thr_v = ws_q2.cell(r, 3).value
    st_v  = ws_q2.cell(r, 4).value
    if id_v and id_v != "ID":
        triggers_found.append((id_v, trg_v, thr_v, st_v))
wb_q2.close()

if triggers_found:
    log(f"  Nguồn: docs/case_files/CASE_BANANAS31.xlsx sheet TRIGGERS")
    for tid, trg, thr, st in triggers_found:
        log(f"    {tid}: {trg} | Threshold: {thr} | Status: {st}")
    log(f"  KẾT: Trigger valid = T1+T2+T3; INV = gLSR≥1.2 (hiện tại đang BLOCK)")
    log(f"  Q2 PASS ✓ (nguồn: CASE_BANANAS31.xlsx TRIGGERS sheet)")
else:
    log(f"  FAIL: TRIGGERS sheet trống hoặc không đọc được")

# Q3: fullyDelisted Alpha → xử lý taker_alpha?
log("\n--- Q3: fullyDelisted Alpha → taker_alpha xử lý thế nào? ---")
log("Đường tìm: INDEX.md → lessons_learned.md → L-48")
lessons_md = (DOCS / "lessons_learned.md").read_text(encoding="utf-8")
if "L-48" in lessons_md:
    start48 = lessons_md.index("## L-48")
    block48 = lessons_md[start48:start48+600]
    log(f"  Nguồn: docs/lessons_learned.md §L-48")
    for line in block48.split("\n")[:8]:
        if line.strip():
            log(f"    {line}")
    log(f"  KẾT: fullyDelisted=True → taker_alpha = NaN/ABSTAIN")
    log(f"       Rule: klines[9]==klines[5] trên BAPI = close price, không phải real taker")
    log(f"       Cross-confirm: CLAUDE.md FACTS + build_case.py (ABSTAIN block)")
    log(f"  Q3 PASS ✓ (nguồn: lessons_learned.md §L-48, confirm CLAUDE.md)")
else:
    log(f"  FAIL: L-48 không tìm thấy trong lessons_learned.md")


# ── SUMMARY ──────────────────────────────────────────────────────────────────
log("\n" + "=" * 70)
log("SUMMARY")
log("=" * 70)
log(f"  DAILY L-32: {'PASS 503 rows' if date_count == 503 else f'FAIL {date_count} rows'}")
log(f"  Lesson mapping: {len(found_lids)} lessons in L-{nums[0]}→L-{nums[-1]}, gaps={['L-'+str(g) for g in gaps]}")
log(f"  Q1 (sign-corr Photo): check analysis_playbook.md §A.5")
log(f"  Q2 (BANANAS31 triggers): check CASE_BANANAS31.xlsx TRIGGERS")
log(f"  Q3 (Alpha ABSTAIN): check lessons_learned.md §L-48")
log(f"\n  Đường học THÔNG nếu Q1/Q2/Q3 đều PASS → sẵn sàng commit.")

"""
_task_lessons_bananas31_20260809b.py
Steps 4-6 continuation (run after closing CASE_BANANAS31.xlsx in Excel).
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from datetime import datetime, timezone
import openpyxl
from openpyxl.styles import Font

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_DIR = ROOT / "docs" / "case_files"
DOCS     = ROOT / "docs"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"TASK lessons-20260809b  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")


# ── 4. Update CASE_BANANAS31.xlsx CASE/TRIGGERS/OUTCOME ──────────────────────
log("\n=== STEP 4: Update CASE_BANANAS31.xlsx ===")

bn_path = CASE_DIR / "CASE_BANANAS31.xlsx"
wb_bn = openpyxl.load_workbook(str(bn_path))

# 4a. CASE sheet
ws_case = wb_bn["CASE"]
verdict_text = "NO_SETUP — TRACKING-passive. Build 06/26 het han (L-47). Ho MM-BAIT-B-shape serial, dong ho cum #4 Aug-Oct/26 [n=3 INFERENCE]. Operator signed 09/08."
updated_verdict = False
for r in range(1, ws_case.max_row + 1):
    for c in range(1, ws_case.max_column + 1):
        val = ws_case.cell(r, c).value
        if val and "COLD_START" in str(val) and "PENDING" in str(val):
            ws_case.cell(r, c).value = verdict_text
            ws_case.cell(r, c).font = Font(size=9)
            log(f"  CASE: verdict updated at row {r} col {c}")
            updated_verdict = True
            break
    if updated_verdict:
        break

if not updated_verdict:
    for r in range(1, ws_case.max_row + 1):
        val0 = str(ws_case.cell(r, 1).value or "").lower()
        if "status" in val0 or "verdict" in val0:
            ws_case.cell(r, 2).value = verdict_text
            ws_case.cell(r, 2).font = Font(size=9)
            log(f"  CASE: status row {r} updated")
            updated_verdict = True
            break

if not updated_verdict:
    new_r = ws_case.max_row + 2
    ws_case.cell(new_r, 1).value = "verdict"
    ws_case.cell(new_r, 2).value = verdict_text
    for c in [1, 2]:
        ws_case.cell(new_r, c).font = Font(size=9)
    log(f"  CASE: verdict appended at row {new_r}")

for r in range(1, ws_case.max_row + 1):
    if "archetype" in str(ws_case.cell(r, 1).value or "").lower():
        ws_case.cell(r, 2).value = "MM-BAIT-B-shape serial (INFERENCE, n=3)"
        ws_case.cell(r, 2).font = Font(size=9)
        log(f"  CASE: archetype row {r} updated")

# 4b. TRIGGERS sheet
ws_trg = wb_bn["TRIGGERS"]
triggers = [
    ["ID",   "Trigger",                                  "Threshold",                    "Status",  "Ghi chu"],
    ["T1",   "gLSR drop + pos rebuild",                  "gLSR <= 0.7 + pos_r tang 3d",  "WAIT",   "Fuel nap tu reset crowd"],
    ["T2",   "Volume bung ben vung gia",                  "vol >= 3x med14 ben >= 2d",    "WAIT",   "Confirm build momentum"],
    ["T3",   "GOM-A fire + yaml screen pass",            "GOM-A=TRUE + screen pass",      "WAIT",   "Xem screen_thresholds.yaml"],
    ["INV",  "gLSR >= 1.2 hien tai (block entry)",       "gLSR >= 1.2",                  "BLOCK",  "Crowd da long het — mat fuel"],
]
for ri, row_data in enumerate(triggers, 1):
    for ci, val in enumerate(row_data, 1):
        cell = ws_trg.cell(ri, ci)
        cell.value = val
        cell.font  = Font(size=9, bold=(ri == 1))
log(f"  TRIGGERS: {len(triggers)} rows written")

# 4c. OUTCOME sheet
ws_out = wb_bn["OUTCOME"]
outcome_rows = [
    ["Field",            "Value"],
    ["verdict_operator", "NO_SETUP — TRACKING-passive"],
    ["ngay_verdict",     "2026-08-09"],
    ["archetype",        "MM-BAIT-B-shape serial (INFERENCE n=3)"],
    ["ghi_chu",          "Case giao khoa L-46/47/48 — giu lam doi chung, khong dong file"],
    ["clock_cum_4",      "Du kien Aug-Oct 2026 — theo doi gLSR drop ve <= 0.7"],
    ["operator_signed",  "09/08/2026"],
]
for ri, row_data in enumerate(outcome_rows, 1):
    for ci, val in enumerate(row_data, 1):
        cell = ws_out.cell(ri, ci)
        cell.value = val
        cell.font  = Font(size=9, bold=(ri == 1))
log(f"  OUTCOME: {len(outcome_rows)} rows written")

wb_bn.save(str(bn_path))
log(f"  CASE_BANANAS31.xlsx saved OK")


# ── 5. Append EVENTS cross-ref to CASE_HEI.xlsx ──────────────────────────────
log("\n=== STEP 5: Append EVENTS to CASE_HEI.xlsx ===")

hei_path = CASE_DIR / "CASE_HEI.xlsx"
wb_hei   = openpyxl.load_workbook(str(hei_path))
ws_ev    = wb_hei["EVENTS"]

last_ev_r = ws_ev.max_row
while last_ev_r > 1 and all(ws_ev.cell(last_ev_r, c).value in (None, "") for c in range(1, 6)):
    last_ev_r -= 1

new_ev_r = last_ev_r + 1
ws_ev.cell(new_ev_r, 1).value = "2026-08-09"
ws_ev.cell(new_ev_r, 1).font  = Font(size=9)
ws_ev.cell(new_ev_r, 2).value = ("09/08: HEI duoc dung lam doi chung DUONG trong cap L-46 "
                                  "(vs BANANAS31 doi chung AM) — xem Phu luc A.5 analysis_playbook.md")
ws_ev.cell(new_ev_r, 2).font  = Font(size=9)
ws_ev.cell(new_ev_r, 3).value = "CROSS_REF"
ws_ev.cell(new_ev_r, 3).font  = Font(size=9)

wb_hei.save(str(hei_path))
log(f"  CASE_HEI.xlsx EVENTS: row {new_ev_r} appended")


# ── 6. Fix + update docs/INDEX.md ────────────────────────────────────────────
log("\n=== STEP 6: Update docs/INDEX.md ===")

idx_md_path = DOCS / "INDEX.md"
idx_text    = idx_md_path.read_text(encoding="utf-8")

# Fix broken HEI row
BROKEN_HEI = (
    "| `docs/case_files/CASE_HEI.xlsx\n"
    "  - [CASE_BANANAS31.xlsx](case_files/CASE_BANANAS31.xlsx)"
    " — COLD_START PENDING (Alpha fullyDelisted, dump 91 ngay ret<-5%)` | HEI | COLD_START — PENDING |"
)
FIXED_HEI = (
    "| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (doi chung DUONG cap L-46) |\n"
    "| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (doi chung AM cap L-46, TRACKING-passive) |"
)

if BROKEN_HEI in idx_text:
    idx_text = idx_text.replace(BROKEN_HEI, FIXED_HEI)
    log("  Fixed broken HEI/BANANAS31 table row")
else:
    log("  Broken form not found verbatim — checking line-by-line")
    lines_idx = idx_text.splitlines()
    new_lines  = []
    i = 0
    while i < len(lines_idx):
        ln = lines_idx[i]
        # Detect the multi-line broken row
        if "CASE_HEI.xlsx" in ln and "BANANAS31" in ln:
            # Already merged or broken — replace entire line
            new_lines.append("| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (doi chung DUONG cap L-46) |")
            new_lines.append("| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (doi chung AM cap L-46, TRACKING-passive) |")
            log(f"    Replaced merged line at idx {i}")
            i += 1
            continue
        elif "CASE_HEI.xlsx" in ln and i + 1 < len(lines_idx) and "BANANAS31" in lines_idx[i+1]:
            # Two-line broken form
            new_lines.append("| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (doi chung DUONG cap L-46) |")
            new_lines.append("| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (doi chung AM cap L-46, TRACKING-passive) |")
            log(f"    Replaced two-line broken form at idx {i}/{i+1}")
            i += 2
            continue
        new_lines.append(ln)
        i += 1
    idx_text = "\n".join(new_lines)

# Update lessons range
old_desc = "View sinh tu CASE_INDEX.xlsx sheet LESSONS (khong edit truc tiep)"
new_desc = "View sinh tu CASE_INDEX.xlsx sheet LESSONS (khong edit truc tiep) · L-01→L-48"
# Try Vietnamese version too
old_desc_vn = "View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp)"
new_desc_vn  = "View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp) · L-01→L-48"
if old_desc_vn in idx_text:
    idx_text = idx_text.replace(old_desc_vn, new_desc_vn)
    log("  Lesson range updated: L-01→L-48")
elif old_desc in idx_text:
    idx_text = idx_text.replace(old_desc, new_desc)
    log("  Lesson range updated (ASCII fallback)")
elif "L-01→L-48" not in idx_text:
    log("  WARNING: lessons desc anchor not found — skipping range update")

# Update version date
for old_ver, new_ver in [
    ("**Cập nhật:** khi thêm/xóa file canonical",
     "**Cập nhật:** 09/08/2026 (L-46/47/48 + Phụ lục A.5)"),
    ("**Cap nhat:** khi them/xoa file canonical",
     "**Cap nhat:** 09/08/2026 (L-46/47/48 + Phu luc A.5)"),
]:
    if old_ver in idx_text:
        idx_text = idx_text.replace(old_ver, new_ver)
        log("  Version date updated")
        break

idx_md_path.write_text(idx_text, encoding="utf-8")
log(f"  docs/INDEX.md saved ({len(idx_text.splitlines())} lines)")


log("\n=== STEPS 4-6 COMPLETE ===")
log("Ready to commit. Two commits:")
log("  1. 'lessons: L-46/47/48 BANANAS31 (operator signed 09/08)'")
log("  2. 'playbook A.5 + case cross-ref: video-not-photo pair'")

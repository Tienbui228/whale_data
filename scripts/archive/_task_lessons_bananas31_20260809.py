"""
_task_lessons_bananas31_20260809.py
Task 3: Lessons L-46/47/48 + Phụ lục A.5 + case cross-ref.
Operator signed 09/08/2026.

Steps:
  1. Append L-46/47/48 to CASE_INDEX.xlsx LESSONS sheet (rows 49/50/51)
  2. Regenerate docs/lessons_learned.md
  3. Insert Phụ lục A.5 into docs/analysis_playbook.md (after A.4)
  4. Update CASE_BANANAS31.xlsx CASE/TRIGGERS/OUTCOME sheets
  5. Append EVENTS cross-ref to CASE_HEI.xlsx
  6. Fix + update docs/INDEX.md
  7. Print Q1/Q2/Q3 learning path check
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from datetime import datetime, timezone
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_DIR = ROOT / "docs" / "case_files"
DOCS     = ROOT / "docs"

def log(s=""): print(s)

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TASK lessons-bananas31-20260809  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)


# ── 1. LESSONS sheet — append L-46/47/48 ──────────────────────────────────────
log("\n=== STEP 1: Append L-46/47/48 to CASE_INDEX LESSONS sheet ===")

IDX = CASE_DIR / "CASE_INDEX.xlsx"
wb  = openpyxl.load_workbook(str(IDX))
ws  = wb["LESSONS"]

# Verify current max row
max_r = ws.max_row
log(f"  LESSONS sheet max_row before append: {max_r}")

# Confirm last lesson
for ri in range(max_r, 3, -1):
    lid_val = ws.cell(ri, 1).value
    if lid_val and str(lid_val).startswith("L-"):
        log(f"  Last lesson found: {lid_val} at row {ri}")
        break

# New rows 49/50/51
# Schema: col1=lid, col2=ngay, col3=case_src, col4=bai_hoc, col5=loai, col6=trang_thai, col7=hanh_dong
LESSONS_NEW = [
    {
        "lid":        "L-46",
        "ngay":       "2026-08-09",
        "case_src":   "CASE_BANANAS31 + CASE_HEI",
        "bai_hoc": (
            "Video vs Photo: hai hồ sơ pos_r cao nhưng ý nghĩa khác nhau. "
            "\"Video\" (CASE_HEI) = build thật: pos_r vừa phải, đồng-bộ giá, ít dist_wall. "
            "\"Photo\" (CASE_BANANAS31) = snapshot đẹp nhưng static: pos_r=6.7 RẤT CAO nhưng "
            "sign-corr Δpos_r vs ret_1d ~50% (47.7% opposite) — pos_r KHÔNG predict giá. "
            "Thêm: dist_wall_day=57/503 (11.3%), knife_crowd=9 ngày — dấu MM đang bán vào pump. "
            "Kết luận: pos_r level đơn độc KHÔNG phân biệt được BTW vs phân phối. "
            "Cần 3 đạo hàm: level + slope + sync. Xem Phụ lục A.5. "
            "Nguồn: CASE_BANANAS31 phân tích 08-09/08/2026 · ký 09/08 · đối chứng: CASE_HEI.xlsx"
        ),
        "loai":       "ARM",
        "trang_thai": "ACTIVE",
        "hanh_dong": (
            "Khi pos_r >5: check sign-corr Δpos_r vs ret_1d (30d OLS). "
            "<55% → Photo → TRACKING-passive. "
            "Không vào setup cho đến đồng hồ cụm trigger (xem L-47). "
            "Implement: build_case.py đã in OLS slope + sign-corr."
        ),
    },
    {
        "lid":        "L-47",
        "ngay":       "2026-08-09",
        "case_src":   "CASE_BANANAS31",
        "bai_hoc": (
            "Đồng hồ cụm: Build-into-weakness không kéo dài vô tận. "
            "BANANAS31 pump cluster: Jun/Aug/Oct 2026 [n=3 inference từ vol spikes ≥8×med14]. "
            "Build cụm #3 từ 06/2026 → đồng hồ ~60-90 ngày → cụm #4 dự kiến Aug-Oct/26. "
            "Nếu không có ignite (gLSR≤0.7 + pos rebuild ≥3d) trong cửa sổ → build failed → MM exit. "
            "Hiện tại gLSR=1.20 > ngưỡng ignite 1.1 → block entry (crowd đã long hết). "
            "Verdict NO_SETUP — TRACKING-passive. "
            "Nguồn: CASE_BANANAS31 · ký 09/08"
        ),
        "loai":       "ARM",
        "trang_thai": "ACTIVE",
        "hanh_dong": (
            "Mỗi case BTW: ghi ngày dự kiến đồng hồ cụm tiếp theo. "
            "Theo dõi: gLSR drop về ≤0.7 (lý tưởng) hoặc ≤0.9 (cảnh báo). "
            "Nếu hết cửa sổ không trigger → escalate INVALIDATE check."
        ),
    },
    {
        "lid":        "L-48",
        "ngay":       "2026-08-09",
        "case_src":   "CASE_BANANAS31 + CASE_IDOL",
        "bai_hoc": (
            "fullyDelisted Alpha → ABSTAIN taker_alpha. "
            "Klines[9]==klines[5] trên BAPI khi fullyDelisted=True (taker column = close price, không phải real taker). "
            "Đã confirm: IDOL (ALPHA_223, L-43 context) + BANANAS31 (ALPHA_21). "
            "Rule chốt: IF offline=True OR offsell=True OR fullyDelisted=True → taker_alpha=NaN, flag=ABSTAIN. "
            "Áp dụng ngược cho mọi case đang mở có Alpha token. "
            "Nguồn: CASE_BANANAS31 + CASE_IDOL · ký 09/08"
        ),
        "loai":       "DATA",
        "trang_thai": "ACTIVE",
        "hanh_dong": (
            "Khi collect Alpha mới: check fullyDelisted trước khi parse klines[9]. "
            "Script build_case.py đã implement ABSTAIN block. "
            "Audit retrospective: CASE_TUT/BR/CLO — check Alpha status."
        ),
    },
]

font9 = Font(size=9)

for i, lesson in enumerate(LESSONS_NEW):
    row_num = max_r + 1 + i
    ws.cell(row_num, 1).value = lesson["lid"];        ws.cell(row_num, 1).font = font9
    ws.cell(row_num, 2).value = lesson["ngay"];       ws.cell(row_num, 2).font = font9
    ws.cell(row_num, 3).value = lesson["case_src"];   ws.cell(row_num, 3).font = font9
    ws.cell(row_num, 4).value = lesson["bai_hoc"];    ws.cell(row_num, 4).font = font9
    ws.cell(row_num, 5).value = lesson["loai"];       ws.cell(row_num, 5).font = font9
    ws.cell(row_num, 6).value = lesson["trang_thai"]; ws.cell(row_num, 6).font = font9
    ws.cell(row_num, 7).value = lesson["hanh_dong"];  ws.cell(row_num, 7).font = font9
    log(f"  Written {lesson['lid']} at row {row_num}")

wb.save(str(IDX))
log(f"  CASE_INDEX.xlsx saved (LESSONS now {ws.max_row} rows)")


# ── 2. Regenerate lessons_learned.md ──────────────────────────────────────────
log("\n=== STEP 2: Regenerate docs/lessons_learned.md ===")

MDOUT = DOCS / "lessons_learned.md"

wb2 = openpyxl.load_workbook(str(IDX), data_only=True)
ws2 = wb2["LESSONS"]

lessons_data = []
for r in range(5, ws2.max_row + 1):
    lid        = ws2.cell(r, 1).value
    ngay       = ws2.cell(r, 2).value
    case_src   = ws2.cell(r, 3).value
    bai_hoc    = ws2.cell(r, 4).value
    loai       = ws2.cell(r, 5).value
    trang_thai = ws2.cell(r, 6).value
    hanh_dong  = ws2.cell(r, 7).value
    if not lid or not str(lid).startswith("L-"):
        continue
    lessons_data.append((str(lid), str(ngay or ""), str(case_src or ""),
                         str(bai_hoc or ""), str(loai or ""),
                         str(trang_thai or ""), str(hanh_dong or "")))

wb2.close()
log(f"  Found {len(lessons_data)} lessons: {lessons_data[0][0]} → {lessons_data[-1][0]}")

lines = [
    "# Lessons Learned — FreshWatch",
    "",
    "> Auto-generated tu CASE_INDEX.xlsx sheet LESSONS. Khong edit file nay truc tiep.",
    (f"> Lan sinh: {datetime.now().strftime('%Y-%m-%d')} · "
     f"Tong: {len(lessons_data)} bai hoc "
     f"({lessons_data[0][0]} → {lessons_data[-1][0]})"),
    "",
]

for lid, ngay, case_src, bai_hoc, loai, trang_thai, hanh_dong in lessons_data:
    lines.append(f"## {lid} [{ngay}] {case_src} — `{loai}` · {trang_thai}")
    lines.append(bai_hoc)
    if hanh_dong:
        lines.append(f"*Hanh dong tiep: {hanh_dong}*")
    lines.append("")

MDOUT.write_text("\n".join(lines), encoding="utf-8")
log(f"  Written: {MDOUT} ({len(lines)} lines, {len(lessons_data)} lessons)")


# ── 3. Insert Phụ lục A.5 into analysis_playbook.md ─────────────────────────
log("\n=== STEP 3: Insert Phụ lục A.5 into analysis_playbook.md ===")

PLAYBOOK = DOCS / "analysis_playbook.md"
playbook_text = PLAYBOOK.read_text(encoding="utf-8")

A5_BLOCK = """
### A.5 Bảng ba-đạo-hàm: Video vs Photo

> Phân biệt \"Video\" (build thật) vs \"Photo\" (snapshot đẹp nhưng static) bằng ba tầng kiểm tra.
> Áp dụng khi pos_r >4 hoặc có câu hỏi \"BTW hay phân phối?\".

| Đạo hàm | Biến | Video (HEI) | Photo (BANANAS31) | Kết luận nếu Photo |
|---------|------|------------|------------------|--------------------|
| 1 — Level | pos_r hiện tại | ~2–4 (vừa) | 6.7 (rất cao) | Level cao ≠ bullish — cần check đạo hàm 2+3 |
| 2 — Slope | Δpos_r 30d OLS | Dương + đồng-trend giá | +0.036/ngày trong dump | Slope dương trong dump = Photo suspect |
| 3 — Sync | sign(Δpos_r) vs sign(ret_1d) | ≥55% đồng hướng | ~50/50 (47.7% opposite) | <55% → pos_r không predict giá |

**Cặp đối chứng (ký 09/08/2026):**

| Chỉ tiêu | CASE_HEI (đối chứng DƯƠNG) | CASE_BANANAS31 (đối chứng ÂM) |
|----------|--------------------------|-------------------------------|
| Verdict | BUILD-setup VALID | NO_SETUP — TRACKING-passive |
| pos_r level | Bình thường | 6.7 (cực cao) |
| Sign-corr Δpos_r/ret | Đồng bộ (>55%) | ~50/50 (47.7% opposite) |
| dist_wall_day / tổng | Thấp | 11.3% (57/503 ngày) |
| flag_knife_crowd | Hiếm | 9 ngày |
| gLSR hiện tại | Trong ngưỡng | 1.20 > 1.1 (block GOM-A A2) |
| Đồng hồ cụm | Active | Hết hạn 06/26, cụm #4 dự kiến Aug-Oct/26 |

**Quy trình khi thấy pos_r cao (>4):**
1. Check **đạo hàm 3** (sign-corr 30d). Nếu <55% → Photo → bước 2.
2. Check **dist_wall_streak** ≥ 3d. Nếu có → MM đang bán vào tăng.
3. Check **gLSR vs 1.1** (GOM-A A2). Nếu gLSR > 1.1 → crowd đã long → mất fuel.
4. Kết: TRACKING-passive, không vào setup đến khi **đồng hồ cụm** kế tiếp trigger (xem L-47).

*Cross-ref: L-46 (Video vs Photo) · L-47 (đồng hồ cụm) · L-48 (Alpha ABSTAIN) · CASE_HEI.xlsx · CASE_BANANAS31.xlsx*

"""

# Insert A.5 after the A.4 cross-ref line (before the --- separator)
INSERT_AFTER = "*Cross-ref: L-16 (div-flip) · L-25 (một-nhà-một-data) · L-31 (câu chữ nguồn) · gom_detect_spec §1 (A1/A3/B1 tiêu thụ các biến này).*"
if "A.5" in playbook_text:
    log("  Phụ lục A.5 already present — skipping insert")
elif INSERT_AFTER in playbook_text:
    playbook_text = playbook_text.replace(INSERT_AFTER, INSERT_AFTER + A5_BLOCK)
    log("  A.5 inserted after A.4 cross-ref line")
else:
    log("  WARNING: A.4 cross-ref anchor not found — appending A.5 before footer")
    # Fallback: insert before the Cross-reference table
    fallback = "## Phụ lục: Cross-reference Lessons theo Lớp"
    if fallback in playbook_text:
        playbook_text = playbook_text.replace(fallback, A5_BLOCK.lstrip("\n") + "\n---\n\n" + fallback)
    else:
        playbook_text = playbook_text.rstrip() + "\n" + A5_BLOCK

# Update Cross-reference table to add L-46/47/48 to ARM row
old_arm_row = "| VI (ARM) | L-02, L-03, L-04, L-08, L-12, L-13, L-18, L-38 |"
new_arm_row = "| VI (ARM) | L-02, L-03, L-04, L-08, L-12, L-13, L-18, L-38, **L-46, L-47** |"
if old_arm_row in playbook_text:
    playbook_text = playbook_text.replace(old_arm_row, new_arm_row)
    log("  Updated ARM row in cross-ref table")

old_data_row = "| VII (MM-ECON) | L-42 (archetype), L-26 (exit clock), L-05/B/C (kho classification) |"
new_data_row = "| VII (MM-ECON) | L-42 (archetype), L-26 (exit clock), L-05/B/C (kho classification) |\n| DATA | **L-48** (Alpha fullyDelisted ABSTAIN) |"
if old_data_row in playbook_text and "| DATA |" not in playbook_text:
    playbook_text = playbook_text.replace(old_data_row, new_data_row)
    log("  Added DATA row to cross-ref table")

# Update footer to mention A.5
old_footer = "*Playbook v0.2 — cập nhật 06/08/2026: thêm section VII (MM-ECON), LAYER COVERAGE header. cập nhật 08/08/2026: Phụ lục A biến dẫn xuất (án HEI div/slope).*"
new_footer = "*Playbook v0.2 — cập nhật 06/08/2026: thêm section VII (MM-ECON), LAYER COVERAGE header. cập nhật 08/08/2026: Phụ lục A biến dẫn xuất (án HEI div/slope). cập nhật 09/08/2026: Phụ lục A.5 bảng ba-đạo-hàm (Video vs Photo, cặp đối chứng HEI/BANANAS31).*"
if old_footer in playbook_text:
    playbook_text = playbook_text.replace(old_footer, new_footer)
    log("  Footer updated")

PLAYBOOK.write_text(playbook_text, encoding="utf-8")
log(f"  Saved: {PLAYBOOK} ({len(playbook_text.splitlines())} lines)")


# ── 4. Update CASE_BANANAS31.xlsx CASE/TRIGGERS/OUTCOME ──────────────────────
log("\n=== STEP 4: Update CASE_BANANAS31.xlsx CASE/TRIGGERS/OUTCOME ===")

bn_path = CASE_DIR / "CASE_BANANAS31.xlsx"
wb_bn = openpyxl.load_workbook(str(bn_path))

# 4a. CASE sheet — find verdict cell and update
ws_case = wb_bn["CASE"]
verdict_text = "NO_SETUP — TRACKING-passive. Build 06/26 het han (L-47). Ho MM-BAIT-B-shape serial, dong ho cum #4 Aug-Oct/26 [n=3 INFERENCE]. Operator signed 09/08."
updated_verdict = False
for r in range(1, ws_case.max_row + 1):
    for c in range(1, ws_case.max_column + 1):
        val = ws_case.cell(r, c).value
        if val and ("COLD_START" in str(val) or "verdict" in str(val).lower() or "status" in str(val).lower()):
            # Look for the status/verdict value cell
            if "COLD_START" in str(val) and "PENDING" in str(val):
                ws_case.cell(r, c).value = verdict_text
                ws_case.cell(r, c).font = Font(size=9)
                log(f"  CASE sheet: verdict updated at row {r} col {c}")
                updated_verdict = True
                break
    if updated_verdict:
        break

if not updated_verdict:
    # Try to find by label in adjacent col
    for r in range(1, ws_case.max_row + 1):
        val0 = ws_case.cell(r, 1).value
        if val0 and "status" in str(val0).lower():
            ws_case.cell(r, 2).value = verdict_text
            ws_case.cell(r, 2).font = Font(size=9)
            log(f"  CASE sheet: status row {r} updated")
            updated_verdict = True
            break

if not updated_verdict:
    # Append verdict at next empty row
    new_r = ws_case.max_row + 2
    ws_case.cell(new_r, 1).value = "verdict"
    ws_case.cell(new_r, 2).value = verdict_text
    ws_case.cell(new_r, 1).font = Font(size=9)
    ws_case.cell(new_r, 2).font = Font(size=9)
    log(f"  CASE sheet: verdict appended at row {new_r} (status not found)")

# Also update ngay_dong and archetype if found
for r in range(1, ws_case.max_row + 1):
    val0 = str(ws_case.cell(r, 1).value or "").lower()
    if "archetype" in val0:
        ws_case.cell(r, 2).value = "MM-BAIT-B-shape serial (INFERENCE, n=3)"
        ws_case.cell(r, 2).font = Font(size=9)
        log(f"  CASE sheet: archetype set at row {r}")

# 4b. TRIGGERS sheet
ws_trg = wb_bn["TRIGGERS"]
# Clear existing content and write fresh trigger set
triggers = [
    ["ID",    "Trigger",                                        "Threshold",                     "Status",  "Ghi chu"],
    ["T1",    "gLSR drop + pos rebuild",                        "gLSR <= 0.7 + pos_r tang 3d",   "WAIT",    "Fuel nap tu reset crowd"],
    ["T2",    "Volume bung ben vung gia",                        "vol >= 3x med14 ben >= 2 ngay",  "WAIT",    "Confirm build momentum"],
    ["T3",    "GOM-A fire + yaml screen pass",                  "GOM-A=TRUE + screen pass",       "WAIT",    "Xem screen_thresholds.yaml"],
    ["INV",   "gLSR >= 1.2 (hien tai da o day)",               "gLSR >= 1.2 = block entry",      "BLOCK",   "Crowd da long het — mat fuel"],
]
# Find first empty row or overwrite
for ri, row_data in enumerate(triggers, 1):
    for ci, val in enumerate(row_data, 1):
        cell = ws_trg.cell(ri, ci)
        cell.value = val
        cell.font  = Font(size=9, bold=(ri == 1))
log(f"  TRIGGERS sheet: {len(triggers)} rows written")

# 4c. OUTCOME sheet
ws_out = wb_bn["OUTCOME"]
outcome_rows = [
    ["Field", "Value"],
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
log(f"  OUTCOME sheet: {len(outcome_rows)} rows written")

wb_bn.save(str(bn_path))
log(f"  CASE_BANANAS31.xlsx saved")


# ── 5. Append EVENTS cross-ref to CASE_HEI.xlsx ──────────────────────────────
log("\n=== STEP 5: Append EVENTS cross-ref to CASE_HEI.xlsx ===")

hei_path = CASE_DIR / "CASE_HEI.xlsx"
wb_hei   = openpyxl.load_workbook(str(hei_path))
ws_ev    = wb_hei["EVENTS"]

# Find last used row in EVENTS
last_ev_r = ws_ev.max_row
while last_ev_r > 1 and all(ws_ev.cell(last_ev_r, c).value in (None, "") for c in range(1, 6)):
    last_ev_r -= 1

new_ev_r = last_ev_r + 1
ev_text  = ("09/08: HEI duoc dung lam doi chung DUONG trong cap L-46 "
            "(vs BANANAS31 doi chung AM) — xem Phu luc A.5 analysis_playbook.md")
ws_ev.cell(new_ev_r, 1).value = "2026-08-09"
ws_ev.cell(new_ev_r, 1).font  = Font(size=9)
ws_ev.cell(new_ev_r, 2).value = ev_text
ws_ev.cell(new_ev_r, 2).font  = Font(size=9)
ws_ev.cell(new_ev_r, 3).value = "CROSS_REF"
ws_ev.cell(new_ev_r, 3).font  = Font(size=9)

wb_hei.save(str(hei_path))
log(f"  CASE_HEI.xlsx EVENTS: row {new_ev_r} appended")


# ── 6. Fix + update docs/INDEX.md ────────────────────────────────────────────
log("\n=== STEP 6: Update docs/INDEX.md ===")

idx_md_path = DOCS / "INDEX.md"
idx_text    = idx_md_path.read_text(encoding="utf-8")

# Fix broken HEI row (BANANAS31 link got embedded inside HEI table row)
# Current broken state (two lines that need to be replaced by correct 2 rows):
BROKEN_HEI = (
    "| `docs/case_files/CASE_HEI.xlsx\n"
    "  - [CASE_BANANAS31.xlsx](case_files/CASE_BANANAS31.xlsx)"
    " — COLD_START PENDING (Alpha fullyDelisted, dump 91 ngay ret<-5%)` | HEI | COLD_START — PENDING |"
)
FIXED_HEI = (
    "| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (đối chứng DƯƠNG cặp L-46) |\n"
    "| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (đối chứng ÂM cặp L-46, TRACKING-passive) |"
)

if BROKEN_HEI in idx_text:
    idx_text = idx_text.replace(BROKEN_HEI, FIXED_HEI)
    log("  Fixed broken HEI/BANANAS31 table row")
else:
    # Try alternate broken form (single line, encoding variant)
    log("  Broken HEI row not found verbatim — trying partial fix")
    # Check if BANANAS31 is in the table
    if "CASE_BANANAS31.xlsx` | BANANAS31" not in idx_text:
        # Find HEI row and insert BANANAS31 after it
        lines_idx = idx_text.splitlines()
        new_lines = []
        inserted = False
        for ln in lines_idx:
            if "CASE_HEI.xlsx" in ln and not inserted:
                # Fix HEI row if it has embedded content
                if "BANANAS31" in ln or "\n" in ln:
                    new_lines.append("| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (đối chứng DƯƠNG cặp L-46) |")
                    new_lines.append("| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (đối chứng ÂM cặp L-46, TRACKING-passive) |")
                    inserted = True
                else:
                    new_lines.append(ln)
                    new_lines.append("| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (đối chứng ÂM cặp L-46, TRACKING-passive) |")
                    inserted = True
            else:
                new_lines.append(ln)
        idx_text = "\n".join(new_lines)
        log("  BANANAS31 row inserted via line-by-line fallback")
    else:
        # BANANAS31 already properly in table — just add annotations
        idx_text = idx_text.replace(
            "| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING |",
            "| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (đối chứng DƯƠNG cặp L-46) |"
        )
        idx_text = idx_text.replace(
            "| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING |",
            "| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (đối chứng ÂM cặp L-46, TRACKING-passive) |"
        )
        log("  Added L-46 annotations to existing rows")

# Update lessons_learned.md description to show lesson range
old_lessons_desc = "View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp)"
new_lessons_desc = "View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp) · L-01→L-48"
if old_lessons_desc in idx_text:
    idx_text = idx_text.replace(old_lessons_desc, new_lessons_desc)
    log("  Lesson range updated to L-01→L-48")

# Update version date in header
old_ver = "**Version:** 1.0 · **Ngày:** 06/08/2026 · **Cập nhật:** khi thêm/xóa file canonical"
new_ver = "**Version:** 1.0 · **Ngày:** 06/08/2026 · **Cập nhật:** 09/08/2026 (L-46/47/48 + Phụ lục A.5)"
if old_ver in idx_text:
    idx_text = idx_text.replace(old_ver, new_ver)
    log("  INDEX.md version date updated")

idx_md_path.write_text(idx_text, encoding="utf-8")
log(f"  docs/INDEX.md saved ({len(idx_text.splitlines())} lines)")


# ── 7. Learning Path Check Q1/Q2/Q3 ─────────────────────────────────────────
log("\n=== STEP 7: Learning Path Check Q1/Q2/Q3 ===")

log("""
Q1: Khi phân tích case mới có pos_r > 5 và giá đang dump, bước kiểm tra đầu tiên là gì?

A1: Check sign-corr (sign(Δpos_r) vs sign(ret_1d)) trên 30d OLS.
    - Nếu <55% đồng hướng → đây là \"Photo\" pattern → TRACKING-passive.
    - Nếu ≥55% đồng hướng → \"Video\" pattern → kiểm tra tiếp điều kiện setup.
    Nguồn: docs/analysis_playbook.md §Phụ lục A.5 + L-46 (CASE_BANANAS31 vs CASE_HEI)
    Script: build_case.py in OLS slope + sign-corr trong stdout.

──────────────────────────────────────────────────────────────────────

Q2: GOM-A điều kiện A2 và A3 là gì, ngưỡng chính xác?

A2: A2 = avg5(gLSR) ≤ 1.1  [LEVEL, không phải slope — avg 5 ngày]
    A3 = glsr_slope_5d ≤ 1.15  [DIRECTION — ratio gLSR(t)/gLSR(t-5)]
    Nguồn:
      - gom_detect_spec v1.4 §1 (canonical)
      - Phụ lục A.3 analysis_playbook.md (glsr_slope_5d = ratio, ngưỡng 1.15)
      - _task_patch_gom_spec_20260808.py (implementation, commit d74016e)
    Bẫy: A2 là LEVEL avg5 (không phải slope); A3 dùng ratio (không phải %chg).

──────────────────────────────────────────────────────────────────────

Q3: fullyDelisted Alpha token — xử lý taker_alpha như thế nào?

A3: ABSTAIN — set taker_alpha = NaN, ghi flag trong DAILY.
    Rule: IF fullyDelisted=True OR offline=True OR offsell=True
          → taker_alpha = ABSTAIN (klines[9]==klines[5] = close price, không phải real taker)
    Nguồn:
      - L-48 (CASE_BANANAS31 + CASE_IDOL, ký 09/08)
      - CLAUDE.md FACTS: \"taker_alpha: BANNED (k[9]==k[5] — confirmed từ bài ALPHA_435/IDOL)\"
      - build_case.py (ABSTAIN block implemented)
    Ứng dụng: Mọi case có Alpha — check fullyDelisted trước khi parse klines[9].
""")


log("\n=== ALL STEPS COMPLETE ===")
log(f"  L-46/47/48: appended to LESSONS sheet")
log(f"  lessons_learned.md: regenerated")
log(f"  analysis_playbook.md: Phụ lục A.5 inserted")
log(f"  CASE_BANANAS31.xlsx: CASE/TRIGGERS/OUTCOME updated")
log(f"  CASE_HEI.xlsx: EVENTS cross-ref appended")
log(f"  docs/INDEX.md: fixed + updated")
log(f"  Q1/Q2/Q3: answered above")
log(f"\nNext: two commits per operator spec:")
log(f"  1. 'lessons: L-46/47/48 BANANAS31 (operator signed 09/08)'")
log(f"  2. 'playbook A.5 + case cross-ref: video-not-photo pair'")

# docs/ INDEX — FreshWatch Knowledge Base
**Version:** 1.0 · **Ngày:** 06/08/2026 · **Cập nhật:** 09/08/2026 (L-46/47/48 + Phụ lục A.5)

> **Luật mồ côi:** File `.md` trong `docs/` không được tham chiếu từ tầng Playbook/Lessons/Model-spec/INDEX này → liệt kê vào mục "Orphan" → operator quyết archive hoặc link.
> Cron review: mỗi khi K-series consolidation.

---

## Tầng 0 — INDEX (file này)

| File | Mô tả |
|------|-------|
| `docs/INDEX.md` | File này — cây điều hướng toàn bộ docs/ |
| `docs/TASKS.md` | Task ledger — diff đầu mỗi session |

---

## Tầng 1 — Playbook (HOW-TO, chuẩn mực phân tích)

| File | Mô tả | Phủ lớp |
|------|-------|---------|
| `docs/analysis_playbook.md` | **Playbook chính** — 8 lớp phân tích I→VII + §VIII học thuyết + lessons cross-ref | I–VIII |
| `docs/handover/analysis_handover_20260817.md` | **Đọc thứ nhì** — bảng trạng thái 17 case (17/08) · §2 học thuyết phiên · spec/infra pending | Boot seq |
| `docs/lessons_learned.md` | View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp) · L-01→L-48 | All |
| `docs/lessons_rev2_source.md` | Source draft lessons (sửa vào CASE_INDEX sheet LESSONS) | All |

---

## Tầng 2 — Model Spec (calibration + economic model)

| File | Mô tả | Status |
|------|-------|--------|
| `docs/proposals/mm_econ_v0.2.md` | **MM-ECON v0.2** — bản sống, calibration 6 campaign, M1-M7 | ANALYSIS ONLY |
| `docs/proposals/mm_econ_tut_forward_20260804.md` | MM-ECON TUT forward P1-P8 predictions — hạn chấm 18/08 | LIVE đến 18/08 |
| `docs/proposals/archive/mm_econ_v0.md` | MM-ECON v0→v0.1 — SUPERSEDED | ARCHIVED |

---

## Tầng 3 — Case Files (hồ sơ từng token)

### Case Trackers

| File | Mô tả |
|------|-------|
| `docs/case_files/case_tracker.md` | Tổng quan tất cả case (OPEN/RESOLVED/BLOCKED) |
| `docs/case_files/CASE_INDEX.xlsx` | Master index + LESSONS sheet (canonical) |

### Case Excel (7 sheets: DAILY/CASE/EVENTS/TRIGGERS/OUTCOME/MM_PROFILE/UNLOCK)

| File | Token | Status |
|------|-------|--------|
| `docs/case_files/CASE_BANK.xlsx` | BANK | RESOLVED + T+30 CLOSED |
| `docs/case_files/CASE_BR.xlsx` | BR | TRACKING |
| `docs/case_files/CASE_CLO.xlsx` | CLO | ABSTAIN (T0 unconf.) |
| `docs/case_files/CASE_HEI.xlsx` | HEI | TRACKING (doi chung DUONG cap L-46) |
| `docs/case_files/CASE_BANANAS31.xlsx` | BANANAS31 | COLD_START — PENDING (doi chung AM cap L-46, TRACKING-passive) |
| `docs/case_files/CASE_TST.xlsx` | TST | COLD_START — PENDING (Alpha fullyDelisted, vol spike 07/08, -94% ATH) |
| `docs/case_files/CASE_AGT.xlsx` | AGT | COLD_START — PENDING (Alaya Governance Token, perp 2025-05-20, ATH -56%, 19 vol spikes, gLSR >1.5) |
| `docs/case_files/CASE_IDOL.xlsx` | IDOL | PARTIAL (post-climax) |
| `docs/case_files/CASE_TAG.xlsx` | TAG | TRACKING |
| `docs/case_files/CASE_TUT.xlsx` | TUT | LIVE (T+30=08/08) |
| `docs/case_files/CASE_XPIN.xlsx` | XPIN | WATCH |

### Evidence Files (frozen — không sửa sau commit)

| File | Liên quan | Nội dung |
|------|-----------|---------|
| `docs/case_files/evidence/tut_forensic_20260805.md` | CASE_TUT EVENTS | Pháp y khung dài TUT + Loài C analysis |
| `docs/case_files/evidence/clo_thesis_20260804.md` | CASE_CLO EVENTS | CLO thesis test spot-đạo-cụ / két perp |

---

## Tầng 4 — Reports & Probes (output thô, read-only)

| Thư mục | Mô tả |
|---------|-------|
| `docs/reports/` | Probe/task output còn sống (xem xét từng file) |
| `docs/reports/archive/` | Output đã xử lý xong |

> Danh sách đầy đủ `docs/reports/`: xem K4 orphan audit — không link hết vào đây để tránh noise.

---

## Mồ Côi (Orphan) — Tầng Playbook/Model chưa link

Kết quả K4 audit 06/08/2026. Operator quyết: **archive** hoặc **link từ canonical**.

| File | Nội dung (tóm) | Đề xuất |
|------|---------------|---------|
| `docs/gate_tag_probe.md` | Probe Gate/TAG data thô | → archive |
| `docs/reports/_probe_idol_k2_k5_20260804.md` | IDOL K2-K5 probe (bổ sung K1-K6) | → link từ CASE_IDOL EVENTS |
| `docs/reports/_probe_alpha_deadcode_20260803.md` | Alpha dead-code scan | → archive |
| `docs/reports/_probe_alpha_resolver_20260804.md` | Alpha ID resolver audit | → archive |
| `docs/reports/_probe_br_chot_canh_20260804.md` | BR chốt canh 04/08 | → link từ CASE_BR EVENTS |
| `docs/reports/_probe_tag_chot_canh_20260804.md` | TAG chốt canh 04/08 | → link từ CASE_TAG EVENTS |
| `docs/reports/_probe_tut_exit_20260804.md` | TUT exit analysis | → link từ CASE_TUT EVENTS |
| `docs/reports/_probe_tut_funding_exit_20260804.md` | TUT funding exit analysis | → link từ CASE_TUT EVENTS |
| `docs/reports/archive/cooldown_review_2026-07-30.md` | Cooldown review 3 case 30/07 | → giữ archive OK |
| `docs/reports/missing_jul.md` | Missing data Jul audit | → archive |

**Không orphan (đã linked):** `_probe_bank_autopsy`, `_probe_bank_h1h2h3`, `_probe_bank_june_unlock`, `_probe_idol_k1_k6` (tất cả linked từ mm_econ_v0.2.md CASE EVIDENCE INDEX).
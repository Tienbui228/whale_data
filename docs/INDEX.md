# docs/ INDEX — FreshWatch Knowledge Base
**Version:** 1.1 · **Ngày:** 06/08/2026 · **Cập nhật:** 18/08/2026 (M6-20260818 + mục "Tài liệu ngoài repo")

> **Luật mồ côi:** File `.md` trong `docs/` không được tham chiếu từ tầng Playbook/Lessons/Model-spec/INDEX này → liệt kê vào mục "Orphan" → operator quyết archive hoặc link.
> Cron review: mỗi khi K-series consolidation.
> **Cross-repo rule (M6-20260818):** INDEX chỉ TRỎ (không mirror nội dung file ngoài repo). Path tuyệt đối bắt buộc.

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
| `docs/analysis_playbook.md` | **Playbook chính** — 8 lớp phân tích I→VII + §VIII học thuyết (VIII.1-VIII.15) + lessons cross-ref | I–VIII |
| `docs/handover/analysis_handover_20260817.md` | **Đọc thứ nhì** — bảng trạng thái 17 case (17/08) · §2 học thuyết phiên · spec/infra pending | Boot seq |
| `docs/handover/analysis_handover_addendum_20260818.md` | **Đọc sau handover chính** — Sử ký M6 net-semantics (§A M6 amendment · §B TASKS net-dose · §C lessons + playbook line · §D commit checklist) | Boot seq / phụ đề |
| `docs/lessons_learned.md` | View sinh từ CASE_INDEX.xlsx sheet LESSONS (không edit trực tiếp) · L-01→L-48 | All |
| `docs/lessons_rev2_source.md` | Source draft lessons (sửa vào CASE_INDEX sheet LESSONS) | All |
| `proposals/lessons_pending_batch_20260818.md` | Batch pending 3 lessons §C net-semantics (chờ nhập LESSONS sheet, immutable sau ký) | All |

---

## Tầng 1b — TÀI LIỆU NGOÀI REPO (INDEX chỉ TRỎ, không mirror nội dung)

Spec canonical thuộc repo khác. Sửa nội dung = sửa tại nguồn (không ở INDEX).

| Đường dẫn tuyệt đối | Mô tả | Version |
|--------------------|-------|---------|
| `D:\Data back test\binance-bot-signals\docs\gom_detect_spec.md` | **GOM detector spec canonical** — §1-§9 v2.0 D-tier + §M1-M5 amendment (v1.8, 09/08) + **§M6 net-semantics (v3.1, 18/08 — mã án `M6-20260818`)** + §H0-H7 (ARCHIVED-BY-NUMBER 14/08) | **v3.1** (v3.0 + M6) |
| `D:\Data back test\binance-bot-signals\docs\STRATEGY_SPEC_long_accumulation_continuation_V1_3.md` | Long-accumulation-continuation strategy spec | V1.3 |
| `D:\Data back test\binance-bot-signals\docs\freshwatch_m45_master_plan.md` | Master plan §1 gốc (FreshWatch M4.5) — playbook §I-§VII trỏ về đây bằng "master plan §1 #X" | — |
| `D:\Data back test\binance-bot-signals\docs\ARCHITECTURE_AND_ADR_V2.md` | Architecture + ADR bot-signals | V2 |
| `D:\Data back test\binance-bot-signals\docs\CODE_MAP_V2.md` | Code map | V2 |

> **Repo canonical binance-bot-signals** (CLAUDE.md L-42, chốt 31/07): `D:\Data back test\binance-bot-signals\`. OneDrive copy đã RETIRED. replay.py + 12 calib files ở đây.

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
| `docs/case_files/CASE_TRIA.xlsx` | TRIA | TRACKING (cold-start 19/08 — hedge episode #1 start Aug04, un-hedge readout Aug18/19) |
| `docs/case_files/CASE_STBL.xlsx` | STBL | TRACKING (cold-start 19/08 — hedge episode start Jun27 struct_n=49, un-hedge sơ khai Aug17-18, contract UNVERIFIED §S4) |
| `docs/case_files/CASE_HEMI.xlsx` | HEMI | TRACKING (cold-start 20/08 — active 3-pump campaign Jul20/Aug15/Aug19, S3-HARVEST Aug18, deposit-in-pump +100M, contract UNVERIFIED §H6) |

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
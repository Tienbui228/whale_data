---
type: lessons-pending-batch
version: V3 (27/08/2026)
predecessor: proposals/lessons_pending_batch_V2.md (V2 21/08 — L-55/56/57/58/59 merged)
status: **SIGNED** — operator "ok batch lessons" ký chat 27/08. L-62/63/64/65 appended CASE_INDEX rows 67-70. lessons_learned.md regen. Sync commit: (post-commit)
scope: L-49 → L-57 sheet-sync verify + L-62 (đường-đọc-thật) NEW + 3 named lessons NEW
       (SCOPE-BY-MANIFEST · cfg-provenance · flip-hai-chiều)
signed_evidence:
  - CASE_INDEX.xlsx pre-sync md5: 1c36954353cd54b74f784e78e1e2b68b (mtime 24/08 08:27)
  - CASE_INDEX.xlsx post-sync md5: 13df4cd2f43b5e0e1d839febc87096e5 (mtime 26/08 10:18)
  - lessons_learned.md pre-regen md5: 31e4561550ee8bb7eaadb633ca8f1398
  - lessons_learned.md post-regen md5: be5e0ffe12a0752fbbb80be188c020d6
  - Rows 67-70 verified in md: L-62/63/64/65 all present
---

# LESSONS PENDING BATCH V3 — 27/08/2026

## Verify sheet-sync L-49 → L-57 (already merged, confirm)

Reference docs/lessons_learned.md rows already in sheet (verify chỉ, không edit):

| # | Title (from lessons_learned.md) | Date |
|---:|---|---|
| L-49 | [GUARD] | 2026-08-11 |
| L-50 | [P0] | 2026-08-11 |
| L-51 | [IDENTITY] | 2026-08-19 |
| L-52 | [VENUE] | 2026-08-19 |
| L-53 | [SPECIES] | 2026-08-20 |
| L-54 | [ENTRY] | 2026-08-20 |
| L-55 | [GO-LIVE] | 2026-08-21 |
| L-56 | [GATE-DISCIPLINE] | 2026-08-21 |
| L-57 | [SCHEMA-EVOLUTION] | 2026-08-21 |

Sync status: ✓ visible sheet + regen md. Operator "ok" chỉ = final ACK batch.

## NEW L-62 — Đường-đọc-thật (DRAFT)

**Case:** ⑬-CLOSE ERRATA-BAND (27/08) — probe 5b + Scope-A hardcoded band `[0.44, 0.505]` mismatch prod yaml `[0.44, 0.53]`. Bảng flip 11 → 10 (5b), 54 → 36 (Scope-A). Subset FAIL 8+27 extras.

**Text (draft):** Số/nhãn/verdict do probe/gate xuất ra CHỈ hợp lệ khi probe/gate declare **đường-đọc-thật** của mọi ngưỡng dùng trong tính toán. Không declare = thước tách khỏi số = bảng vô hiệu. Rule bắt buộc header cfg-provenance:
- Nguồn thresholds (yaml path | hardcode | free-layer)
- Giá trị THỰC từng ngưỡng dùng (không dựa comment)
- Timestamp yaml mtime nếu source = yaml (staleness detect)

**Evidence:** ERRATA-BAND-20260827 (sha `d353dc4`) + probe `_probe_band_check_20260827.py`, `_task_errata_band_20260827.py`.

**Apply:** Mọi probe/task/gate rà lại hardcode; thay bằng yaml load + provenance header print. Pre-commit hook check "no hardcoded thresholds" (grep pattern) sẽ add sau nếu operator ký scope hook.

## NEW L-63 — SCOPE-BY-MANIFEST (DRAFT)

**Case:** ⑬-CLOSE ⑩-AMENDMENT chuỗi (24-26/08) — scope regen ⑥ định nghĩa bằng TÊN SLICE ("taker slice") → mơ hồ RATIO vs KLINES → R4-v1 chỉ chạm RATIO → B3 fail hội tụ do avg_px basis (KLINES) chưa regen → phải R4-v2 mở rộng scope.

**Text (draft):** Scope regen/canonicalize/migrate định nghĩa bằng **DANH SÁCH BIẾN CANONICAL BỊ ẢNH HƯỞNG** (fields cụ thể: `taker_buy_pct`, `avg_px`, `lsr_pos`, ...) và block chứa nó (KLINES/RATIO/OI), KHÔNG bằng tên slice mờ ("taker slice", "LSR slice"). Manifest bảng per (block, col, source, consumer, canonical, verdict) làm nguồn duy nhất; xung đột → CONFLICT column, DỪNG hỏi.

**Evidence:**
- ⑩-AMENDMENT bot-signals `41d8d717` (initial stub → 3 vế mở rộng)
- R4-v2 regen sau khi phát hiện avg_px scope-miss `b400b5fc`
- Manifest v1 SIGNED `4cd6ec3` (bảng canonical per col)

**Apply:** Mọi ⑥ regen/⑩ migrate/canonicalize ⇒ manifest bảng trước; verdict per col: REGEN / VERIFY-THEN-KEEP / DEPRECATE-RENAME / N/A-BLOCK. Missing col ⇒ CONFLICT DỪNG.

## NEW L-64 — cfg-provenance header (DRAFT)

**Case:** ⑬-CLOSE ERRATA-BAND 27/08 — 2 probe hardcoded band 0.505 mismatch prod 53.0. Bảng flip 11/54 tính SAI thước → 8+27 extras subset FAIL.

**Text (draft):** Mọi probe/gate BẮT BUỘC in **cfg-provenance header** tại đầu run:
```
[CFG-PROVENANCE <artifact-name>]
Source: <yaml path | hardcode | free-layer>
Method: <load method>
Values ACTUALLY USED:
  <threshold_name> = <actual_value>  [comment: source line]
  ...
```
Kèm phần "assertions" nếu có (fail-loud khi mismatch). Không header = bảng vô hiệu (L-62 companion).

**Evidence:** ERRATA-BAND-20260827 (`d353dc4`) + probe 5b/Scope-A hardcode fix in place.

**Apply:** Template header in `scripts/gom_scan.py` load_thresholds() wrapper; probe/task tự động print. Add lint rule sau nếu operator ký scope.

## NEW L-65 — Flip-set XOR hai chiều (band-change không đơn điệu) (DRAFT)

**Case:** ⑬-CLOSE ERRATA-BAND 27/08 — assume "band nới chỉ bớt flip" (subset PROD ⊂ PROBE) → chứng minh SAI (8 extras 5b, 27 extras Scope-A). Mechanism ARIA 07-30, STAR 06-28 spot-check: band nới thay đổi flip-set hai chiều (thêm + bớt) do wider band = more 7d-window all-pass cases which can flip.

**Text (draft):** Rule ĐÚNG: **flip-set dưới band-change là XOR HAI CHIỀU, không đơn điệu.** Mọi thay đổi band ⇒ RERUN toàn bộ bằng chứng flip (không assume subset). Documentation phải note "subset không được giả định" cạnh mọi flip-count report.

**Evidence:** ERRATA-BAND probe `_task_errata_band_20260827.py` subset check FAIL; conditions probe spot ARIA/STAR window paste.

**Apply:** R6 skeleton rule vocabulary + E2-backlog note updated. Mọi flip-report post-⑬ dùng rule mới.

## Deliver

Sync CASE_INDEX LESSONS sheet: operator apply per CLAUDE.md workflow — thêm 4 rows L-62/63/64/65 với title + one-liner + ref (L-49→L-57 verify already merged).

Sau apply → `_task_gen_case_state_map_20260818.py` regen `case_state_map.md` + SCP VPS (per PHASE-TAG workflow).

Chờ operator "ok batch lessons" ký cuối để đóng batch V3.

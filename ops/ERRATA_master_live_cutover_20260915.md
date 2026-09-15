# ERRATA · master preview → master live cutover
target: 2026-09-15 (bản đầu chạy master live · cron 01:46 UTC 16/09)
ký: 15/09/2026 (một đêm errata)

## Bối cảnh

Bản `[MASTER-PREVIEW đêm k/2]` chạy hai đêm bó chỉ tiêu (targets 09-11, 09-12).
Đêm 09-13 in `3/2` · đêm 09-14 in `4/2` là **bug counter**: cả hai không phải "đêm 3, đêm 4"
mà là smoke sau đủ 2/2. Đêm 09-13 và 09-14 vẫn KHÔNG-KÍCH, standing xanh, postcheck bó,
lỗi chỉ ở NHÃN nhóm.

## Từ target 2026-09-15

- Nhãn: `[MASTER · live từ 2026-09-15]` (không đếm nữa).
- Journal: `preview_journal.jsonl` đóng · `master_journal.jsonl` mở. Field / seal / ledger_state
  giữ nguyên schema, tool đọc lịch sử union hai file.
- PHASE-MAP: rời tin sáng (kênh chính giữ nguyên · slot cron chuyển theo AMD-02 R6).
- Layout: V1.3-SPECIES-LAYOUT-ONLY. Prefix `[B]` · `[A·C]` · `[?]` từ tagger nhị phân
  `scripts/species_tag.py` (md5 388ac36f). Không k/n. Trục động cơ giữ nguyên byte cuối dòng.

## Guard giữ

- CỔNG (d): 6/6 full-pair · 6/6 sent · pin p1..p22 bó niêm · unknown-sentinel = 0.
- postcheck: p21 (px-missing không → PRE) · p22 (header đếm ≡ token in + tail).
- drift guard 01:44 UTC vẫn sống (baseline 8a70ad02e70e).
- p14 PX-COVERAGE-LOW audit `50%` threshold — kêu ở stderr, không chặn send.

## Nếu tin đầu bị fail

Không sửa tay artifact. Revert commit cutover, cron chạy V1.2 lại.

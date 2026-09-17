# NOTE · Luật 3 tầng ngân sách + van mở L2 · KÝ 17/09

## Bối cảnh

Sáng 17/09 UTC 01:46: cron master live đêm đầu (target 09-15) send FAIL HTTP 400
vì body V1.3-LO 6151 chars > TG limit 4096. Journal không mở, master_journal.jsonl
không được tạo, đêm KHÔNG-KÍCH biến mất khỏi sổ.

Rollback tạm DIGEST_V1_3=0 (chạy V1.2). Sau đó đo tường ngân sách:
- E1-E3: bóc thành phần · 4 khối token chiếm 60%
- F1-F4: mô phỏng L1/L2/L3/L4 · L2/L3 gain ~400 chars, không đủ
- G1-G5: cap-N · N nhỏ nhất thoả không tồn tại (16 cắt vào B/D)
- H1-H5: budget-driven cắt CHUA XEP first — chạm khối loài ở 09-15
- I1-I5: 3 tầng rule · CHỈ cắt CHUA XEP · dừng nếu cạn

Chốt: **3 tầng · budget 3680 body-only** (equivalent full_msg 3800 gồm prefix + seal).

## Luật 3 tầng (áp trong `digest_summary_v2.build_v2_digest` khi DIGEST_V1_3=1)

Applied AFTER `_v1_3_render_species_body`, BEFORE `hashlib.md5(body)` seal computation:

### Tầng 0 · body ≤ budget · no cut · no audit
Bình thường. Không đụng.

### Tầng 1 · cắt CHƯA XẾP LOÀI từ tail cho tới khi len ≤ budget
- Cut order: reverse insertion order (last-added-first)
- Mỗi token cắt: name di vào tail `(+K nữa: NAME·NAME·...)`
- Audit line insert TRƯỚC `━━ footer ━━`:
  `[BUDGET-CAP: cắt N dòng · còn X/BUDGET]`
- Trả body sau cắt

### Tầng 2 · CHƯA XẾP LOÀI cạn mà >budget · DỪNG
- KHÔNG cắt vào khối loài (A/B/C/D/E/?) · KHÔNG cắt vào 🔻 XẢ-WATCH · KHÔNG cắt POST-DUMP
- Audit line: `[BUDGET-EXCEEDED: CHƯA XẾP cạn · thân X/BUDGET]`
- Trả body dài (may vượt budget nhưng dưới 4096 vẫn gửi được)

### Tầng 3 · body >4096 chars · D3 pre-check trong `send_telegram` chặn
- KHÔNG tự cắt vào tin
- `send_telegram` return `(False, "BODY-TOO-LONG len=X")`
- D2 journal_append vẫn ghi entry với `sent_ok=False · send_error="BODY-TOO-LONG..."`
- Postcheck vẫn chạy · counter KHÔNG tăng
- Operator biết qua log `[N/A-ERROR:BODY-TOO-LONG]` · sáng đọc, fix wire

## Budget calibration

- `_v1_3_apply_3tier_cap(body, budget=3680)` — trên body-sans-prefix-sans-seal
- Full msg = prefix (~30) + body_after_cap + seal_line (~90)
- Target ≤ 3800 full_msg ↔ ≤ 3680 body-only
- D3 hard chặn ≥ 4096 full_msg

## Van mở L2

**Rule**: nếu **2 đêm liền trong 7 đêm liên tiếp** vào Tầng 2 (BUDGET-EXCEEDED) →
mở L2 (bỏ 👁 forward_tests khỏi body master, chuyển sang tin sáng cùng PHASE-MAP).

**Vì sao**: 2 lần EXCEEDED trong 1 tuần = universe đang mở rộng đủ để 3-tier
không giữ được budget. L2 tiết kiệm ~275 chars/đêm — đủ đưa 3844 → 3569 (T1 clean).

Mở L2 cần:
1. Handover doc riêng (L2 impl · destination 👁)
2. Wire L2 + test 6 đêm
3. ANALYSIS chấm định vị 👁 (tin ghim vs morning phase-map vs tuần một lần)

Không tự mở khi mới 1 đêm T2.

## Files đụng

- `scripts/digest_summary_v2.py`: thêm 3 hàm helper + wire trong `build_v2_digest`
  - `_v1_3_apply_L1_cites(body)` — cites compact
  - `_v1_3_apply_L3_strip_dups(body)` — bỏ số lặp POST-DUMP-dd/G1-POST-FLOOR-ret
  - `_v1_3_apply_3tier_cap(body, budget=3680)` — 3-tier cap logic
  - _v1_3_render_species_body: TOP_K=6 for species (except CHUA XEP) + 🔻 + POST-DUMP · CHUA XEP để 3-tier cắt
- `scripts/master_preview_send.py`: bật lại `os.environ["DIGEST_V1_3"] = "1"`
- Bak: `scripts/master_preview_send.py.bak_v12_run_019276a1` (VPS)

## Pin bảng ký

| pin | test | phạm vi | status |
|-----|------|---------|--------|
| p21 | px-missing không → PRE | postcheck body | PASS |
| p22 | header ≡ printed + tail names | postcheck body | PASS |
| p27 | md5(artifact)[:12] == seal-in-body | 3 nights J2 | PASS |
| p16 | postcheck/journal độc lập ok_send | sandbox D2 | PASS |
| p17 | pre-check độ dài (3 case: 5000/3900/3000) | sandbox D3 | PASS |
| p19 | 3-tier audit đen-xanh (T0/T1/T2) | sandbox I4 | PASS |

## Số ký tự 6 đêm · dry-run pipeline THẬT (J3)

| target | body | full | tier | audit |
|--------|-----:|-----:|:----:|-------|
| 09-11 | 3745 | 3770 | T1 | cắt 3 · còn 3618/3680 |
| 09-12 | 3703 | 3728 | T1 | cắt 5 · còn 3576/3680 |
| 09-13 | 3740 | 3765 | T1 | cắt 7 · còn 3613/3680 |
| 09-14 | 3760 | 3785 | T1 | cắt 8 · còn 3633/3680 |
| **09-15** | 3814 | 3844 | **T2** | CHƯA XẾP cạn · thân 3679/3680 (+44 above 3800) |
| 09-16 | 3705 | 3735 | T1 | cắt 8 · còn 3578/3680 |

**5/6 đêm T1 clean (full <3800)** · 1/6 T2 (09-15 · 3844 <4096 sendable). p27 PASS 3/3 test targets.

## Rollback nếu tối nay fail

```bash
# Rollback về V1.2-run (DIGEST_V1_3=0 hardcode)
ssh root@5.223.67.21 "cp /root/Data_back_test/whale_data/scripts/master_preview_send.py.bak_v12_run_019276a1 /root/Data_back_test/whale_data/scripts/master_preview_send.py"

# Digest_summary_v2 wire cũ nếu cần (git · sha ccd0e2b^):
git show ccd0e2b^:scripts/digest_summary_v2.py > /tmp/rev.py
scp /tmp/rev.py root@5.223.67.21:/root/Data_back_test/whale_data/scripts/digest_summary_v2.py
```

## Đêm đầu · target 09-17 · cron 01:46 UTC 18/09

Kỳ vọng render V1.3 · full_msg ~3735-3800 (nếu cohort tương tự 09-16) hoặc
~3844 T2 (nếu cohort cao 09-15).

postcheck FAIL → revert commit ngay · không sửa tay artifact.

Sáng 18/09: bảng đêm đầu · body_md5 · tier · audit · counter · master_journal entry.

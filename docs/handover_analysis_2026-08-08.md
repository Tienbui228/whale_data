# HANDOVER — TOPIC ANALYSIS · 2026-08-08 (kế nhiệm bản 03/08)

Đọc theo thứ tự: `docs/INDEX.md` (#0) → `docs/analysis_playbook.md` v0.2
(mục VII MM-ECON + LAYER COVERAGE) → `docs/lessons_learned.md`
(L-42 xác nhận ✓; **L-43 CHƯA TRONG SHEET LESSONS**: nội dung
"không suy diễn đã-ký từ im lặng" — PENDING operator thêm vào
CASE_INDEX.xlsx sheet LESSONS → regen lessons_learned.md sau khi thêm)
→ `docs/TASKS.md` (sổ việc sống — diff đầu mỗi report)
→ file này → `docs/case_files/CASE_<TOKEN>.xlsx` các con OPEN.

---

## 0. Trạng thái một đoạn (08/08/2026)

**Case sống:**

- **TUT** — TRACKING-WITH-POSITION (nếu operator còn giữ). **GHẾ-RỜI LẦN 1** bắn 02/08 @0.0174 (pos_r 5.08→2.83). **GHẾ-RỜI LẦN 2 = HARVEST-INTO-STRENGTH 08-05** (giá +33%, pos_r 4.01→2.07 −48%, gLSR GIẢM 1.44→1.11 — KHÔNG phải L-26). Kho Loài C chưa monetize; kho/vol ~50% [08-05: spot ~6.8M vs perp ~24M] = chương bán vẫn chưa mở. Scorecard T+30 = PENDING operator. **7 chốt 08/08:** ① CHƯA (pos_r 2.72, cần ≥3.81) · ② HỞ (funding NEG 08-06 ×2) · ③ GẦN (spot close-to-close −14.6% 08-06, vol 23.8M) · ④ GẦN (gLSR min 1.1119 chưa flush bền) · ⑤ 3× BAND ĐÃ CHẠM (OI ATH 7.873M 08-06 → co còn 6.07M) · ⑥ CHƯA (spot max 7.2M, taker ≥51%) · ⑦ CHƯA (mới 1 ngày đỏ 08-06). [08/08]
- **BANK** — SUPPRESSED + vòng-2 watch. +185M token nạp đáy 29/07-01/08. 3 điều kiện: gLSR-flush/pos-rebuild/tái-ghim — 0/3 thỏa [05/08, cần refresh 08/08]. Unlock 17/08 = T−9. Verdict T+30 = 09/08 (ngày mai).
- **IDOL** — SUPPRESSED → cooldown hết 18/08. EVAA checklist 2/5 thỏa [05/08] — con DUY NHẤT đang rửa đúng chiều. Unlock-test 11/08 (T−3): nền 0.0147 = hard-line. 58bro net 32.44M đang canh chiều.
- **XPIN** — WATCH-nhạt. Full spot/DEX coverage xong. Crowd 2.24 thuần đòn bẩy [05/08], ghế 1.87 còn. Chốt duy nhất = crowd_flush ≥30%. Spot $571K/day = detection floor thấp.
- **BR** — STAND_ASIDE. lsr_accum thành hình nhưng 1 ngày tuổi trên token SỔ ĐEN BAIT-B — cần bền 3d + pos_rerate. px/vol cause của flush 01-03/08 chưa phân loại.
- **CLO** — STAND_ASIDE-có-đồng-hồ (5-10 tuần). Cửa B live: div 0.295. KHÔNG SHORT — định luật #8 (L-08).
- **TAG** — ĐÓNG (S4-đuôi). Mở lại cần: gLSR≤1.1 + div≥1.5 + kho im.

---

## 1. Verdict vừa chấm (08-09/08)

*Điền dần khi operator ký từng mục. Để trống = chưa ký.*

| Verdict | Kết quả | Ghi chú |
|---------|---------|---------|
| TUT T+30 (08/08) | — | px_T30=? · outcome=? |
| BANK T+30 (09/08) | — | px=0.0495 đã confirm; verdict final=? |
| Cooldown PARTI | — | |
| Cooldown EVAA (IDOL) | — | |
| Cooldown BLUAI | — | |

---

## 2. Lịch máy đang chạy

| Ngày | Sự kiện |
|------|---------|
| **11/08** | IDOL unlock 97.29M tokens (2.03% supply) — hard-line test nền 0.0147 |
| **17/08** | BANK unlock event + Vòng-2 3/3 check |
| **18/08** | IDOL cooldown hết · P1-P8 TUT chấm PASS/FAIL (mm_econ_tut_forward, hạn cứng) |

---

## 3. Học thuyết kết tinh từ topic 03→08/08 (chỉ nhắc chỗ)

- **L-42 archetype A/B/C** (kho-mượn/unlock/tự-mua — loài chọn đồng hồ thoát)
- **Playbook VII MM-ECON**: nhiên liệu định trần · ΔOI/B band theo loài · kho/vol-regime · taker detection floor ~10% (n=1 BANK)
- **"ô-điền-≠-đã-trả-lời"** (L-KNOW): PENDING column ≠ answered — không dùng PENDING để luận kết quả
- **LAYER COVERAGE bắt buộc**: mọi báo cáo ghi rõ lớp nào có data, lớp nào ABSTAIN
- Shape on-chain ngụy tạo được (IDOL 3 màn đạo cụ). Khung 1Y trước khi tin withdrawal (TAG round-trip).
- **n= thật**: mọi calibration ghi n= cụ thể; không extrapolate từ n=1

---

## 4. Nợ operator mang sang

- **XPIN O1-O4**: kho wallet on-chain + vesting + BitMart verify (BscScan — Nansen LOCKED)
- **CLO O1-O2**: cost basis 10 ví → quyết F2/F3 (archetype + thesis)
- **TUT O1**: kho + total supply thực (BscScan)
- **K4 mười file mồ côi**: operator approve/reject archive hoặc link từng file (xem `docs/INDEX.md` mục Orphan)
- **L-43 chưa trong sheet**: thêm vào CASE_INDEX LESSONS ("không suy diễn đã-ký từ im lặng") → regen `docs/lessons_learned.md`
- **BR px/vol 01-03/08**: phân loại nguyên nhân flush-cause
- **quyết 40 file D untracked** (đề xuất: commit dọn một lần "archive session probes" — không xóa store, chỉ stage các D-file và commit; agent thực thi khi operator ký)

---

## 5. Kỷ luật không đổi

- Verdict chỉ operator ký · Số tự bảo vệ (nguồn+boundary — lệch = án) · Suppressor đè mọi bullish
- Precedent đếm thật n= · Không long khi không ghế · **KHÔNG SHORT** (định luật #8 / L-08)
- Agent đọc repo, operator không vác file · Claude-advisor đề xuất, không tự ARM
- Mỗi session: ghi agent_log.md + diff TASKS.md đầu report

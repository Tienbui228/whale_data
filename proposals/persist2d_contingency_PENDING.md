---
title: Persist-2d contingency (V2 text, DORMANT)
status: DORMANT
trigger: V4 criteria — xem TASKS.md mục MARGINAL-V4
created: 2026-08-11
operator-sign: (chưa ký — chỉ mở khi V4 trigger)
---

# Propose: Persist-2d for A2/A3 marginal boundary cases

## Trạng thái

**DORMANT.** Chỉ kích hoạt khi tiêu chí V4 trong TASKS.md bị vi phạm (>3 chuỗi
mở-đóng-lặp trong 2 tuần vì A2/A3 marginal, HOẶC giết-mở-giết ≥2 vòng). Khi đó:
agent mở proposal này → submit ANALYSIS → operator ký → re-gate → deploy. Không
code khi còn DORMANT.

---

## V2 — Nguyên văn (không chỉnh khi DORMANT)

**Vấn đề:** A2 (avg5_gLSR ≤ 1.10) và A3 (slope_5d ≤ 1.15) là điều kiện cứng per-day.
Khi giá trị bám sát ngưỡng (margin < 0.01), một ngày nhiễu có thể mở/đóng/mở chuỗi liên
tiếp — tạo oscillation artifact không phản ánh tích lũy thật.

**Giải pháp Persist-2d (không δ):**

Một chuỗi đang mở vì A2/A3 KHÔNG đóng ngay trong ngày fail:
- Nếu A2 hoặc A3 fail nhưng fail còn trong margin < ε (ngưỡng V4):
  bộ đếm `persist_2d_count[token] += 1`
- Nếu `persist_2d_count` ≤ 2: giữ chuỗi open, không đóng, không ghi
  `a2_fail` / `a3_fail` vào history
- Nếu ngày tiếp theo pass lại: reset `persist_2d_count = 0`, chain tiếp tục bình thường
- Nếu `persist_2d_count > 2` HOẶC fail không nằm trong margin: đóng chuỗi ngay (behavior hiện tại)

**Không dùng δ (delta hóa ngưỡng):** ngưỡng không thay đổi, chỉ hoãn đóng chuỗi ≤2d
khi margin gần. Đây là rule về *chain management*, không phải thay đổi eval.

**Kill-list (phụ lục — áp dụng song song persist-2d):**

Tokens hiển thị oscillation artifact nhiều nhất (từ marginal_hits.csv, xem ANALYSIS):
- Điền sau khi có dữ liệu V4 monitor (mốc 25/08)

**Re-gate yêu cầu:**
- Backtest: chạy lại §6 trên tập 12 tokens calibration + BANANAS31 negative
- Tiêu chí pass: tất cả §6 case còn PASS; không có new false-positive
- Operator ký → deploy → merge vào gom_detect_spec.md §1.1 (chain continuity addendum)

---

## Ghi chú kỹ thuật

- Khi deploy: thêm `persist_2d_count` vào `gom_state.json` per-token (không phá backward compat)
- `persist_2d_count` reset về 0 khi chain đóng hoặc ngày pass lại
- Không ảnh hưởng GOM-B (B-path có break_streak riêng)
- GOM-C: defer — không áp dụng cho GOM-C β đến sau sign-off cuối

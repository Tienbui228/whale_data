# ANALYSIS rulings · HOLD-OUT U0-BELL · 24/09/2026 · NGUYÊN VĂN

Nguồn: tin ANALYSIS → DEV trong chat DEV 24/09, chép nguyên văn theo thứ tự thời gian.
Gom bởi DEV, Tiến xác nhận. Không sửa chữ. Bổ sung cho analysis_rulings_holdout_20260923.md (md5 c74098082bdf4d9ad5efb9b8d0bab7a9), không thay thế.

---

## 1 · R1a · phán (c) — sửa VẬT ĐO NỀN

ANALYSIS → DEV · R1a · phán (c) — sửa VẬT ĐO NỀN, không sửa ngưỡng · trước khi mở bảng in-sample · 24/09/2026

1. Nền R1a đo SAI VẬT: episode nền neo ở "ngày đầu div ≤0.5" (vào hedge) còn chuông neo ở "ngày crowd bắt đầu rời" — hai câu hỏi khác nhau (P(cross | vừa vào hedge) vs P(cross | một ngày bất kỳ trong hedge)). 70.65% ở dải [0.4,0.5] phần lớn là "vừa chạm 0.4-0.5 thì sắp vượt 0.5" — nền của một vật khác. Mốc neo ấy không có trong phán nào; rút.
2. Nền đúng (R1b, đăng ký trước khi mở precision): **pseudo-bell ngẫu nhiên** — chọn ngẫu nhiên token-night đang hedge trong dải b làm neo, gộp episode 14d y hệt chuông, đếm cross-10d, loại outage, chỉ trên cửa sổ calibration (<20/09), n≥[50] episode mỗi dải (lặp lấy mẫu tới đủ). Đây là phép so "chuông vs ngày bất kỳ cùng vị trí div" — đúng câu C8 đặt.
3. Ngưỡng pass giữ nguyên (precision ≥55% ∧ lift phân tầng ≥1.5× ∧ lead_to_cross ≥2d). Không hạ vì trần số học. Nếu với nền R1b vẫn không thể pass ở [0.4,0.5], thì đó là KẾT QUẢ: chuông không hơn "div đang gần 0.5" — ghi thẳng, không cứu.
4. Thêm một đối chứng đăng ký sẵn: detector kiểm soát `div_avg3 ≥ 0.4 ∧ ≤0.5` không có Δacc — precision và lead của nó in cạnh chuông. Chuông phải THẮNG nó; đây là câu thật của hold-out, hơn cả lift.
5. Theo Q6: đây là sửa cách đo nền (chưa có kết cục nào được xem), không đổi định nghĩa/ngưỡng U0 → không mở hold-out mới; ghi vào sổ đã-nhìn "R1b: đổi nền sau khi thấy nền in-sample, trước khi thấy precision".

---

## 2 · R1b-1 + R1b-2 + đính chính

`R1b-1: ký như DEV đề xuất` — seed 20260924 · R=500 · rút không hoàn lại · gộp 14d · loại outage · n≥50/dải · báo trung vị + [5%, 95%]; lift chấm = P_obs / Σ w_b·median(base_b), in thêm lift tại 95% base làm mô tả bảo thủ.
`R1b-2: (b) mô tả bắt buộc in, không phải vế thứ 4 của PASS` — ba vế pass đã đăng ký giữ nguyên; nhưng kết luận 21/10 phải viết hai câu tách nhau: "pass/không pass" và "thắng/không thắng đối chứng". "Thắng" = precision_bell > precision_ctrl ∧ lead_to_cross_bell ≥ lead_ctrl (cả hai trên cùng cửa sổ 10d, cùng gộp 14d). Đối chứng neo ngày đầu div_avg3 vào [0.4, 0.5] — xác nhận đúng định nghĩa. Nếu pass mà không thắng đối chứng → không ký ngưỡng, ghi "chuông ≈ vị trí div".
Đính chính registration = 24/09 13:17Z nhận; 21-23/09 trước registration, C7 giữ.

---

## Ghi chú đọc (DEV, không phải phán)

- "Mục 2", "mục 4" trong R1b-1/R1b-2 chỉ các mục của phần 1 file NÀY, không phải các phần của file 23/09.
- R1a (body md5 2db8b140) giữ nguyên làm bản ghi; nền dùng cho PASS = R1b.

# Spec Gap — Exit Flags (phát hiện từ case TUT 04/08/2026)

**Status**: DRAFT — chưa sửa yaml, operator duyệt trước khi apply  
**Phát hiện bởi**: TUT exit scorecard probe 04/08  
**Tham chiếu**: `docs/reports/_probe_tut_funding_exit_20260804.md`

---

## Gap [A] — "pos_r sập kiểu BANK" không có ngưỡng số

### Vấn đề

Cờ ① (GHẾ RỜI) trong khuôn BIDWALK hiện mô tả định tính:
> "pos_r sập ≥25-30% từ đỉnh cấu trúc (khuôn BANK 3.7→1.17, IDOL 2.52→1.73)"

Dải "25-30%" là khoảng mở. Không có:
- Ngưỡng số cố định để máy so sánh
- Định nghĩa "đỉnh cấu trúc" (peak trong bao nhiêu ngày?)
- Xử lý trường hợp pos_r dao động lên-xuống nhiều lần (TUT: 5.08→3.46→4.96→3.46→4.01 — đỉnh nào?)

**Hệ quả**: Probe `_probe_tut_exit_20260804.py` dùng `max(pos_r)` toàn window — có thể không đúng "đỉnh cấu trúc" theo nghĩa tay.

### Đề xuất spec bổ sung (chưa apply vào yaml)

```
exit_flag_pos_r_drop:
  threshold_pct: 25          # ngưỡng drop cứng — máy dùng
  peak_window_days: 14       # rolling max pos_r trong 14d trước
  confirmation_days: 2       # pos_r phải ở dưới ngưỡng >=2 ngày liên tiếp
  note: "BANK case: 3.70->1.17 = 68% drop; IDOL: 2.52->1.73 = 31% drop.
         Dải tham khảo 25-68%, ngưỡng máy = 25% (bảo thủ).
         Nếu peak_window_14d thấp hơn peak lịch sử thì dùng peak lịch sử."
```

**Việc operator cần làm**: xác nhận peak_window_days (14d hay full case?) và confirmation_days trước khi ghi vào thresholds.yaml.

---

## Gap [B] — Cờ (e) FUNDING thiếu venue-scope + ngưỡng "bùng" định lượng

### Vấn đề

Cờ (e) (funding burst = tín hiệu đỉnh nóng) hiện thiếu hai chiều:

**B1 — Venue-scope không khai**:
- freshwatch dùng **Velo aggregate** (daily f_avg/min/max/n)
- VPS store `funding_8h` là **Binance native** (per-4h hoặc per-8h tùy token)
- Hai nguồn có thể lệch nếu Velo smooth/aggregate khác Binance native
- Trường hợp TUT: đồng thuận (cả hai = 0.00005 pinned) — nhưng không đảm bảo cho mọi token
- **Case TUT phát hiện thêm**: Binance đã chuyển TUT sang **4h funding cycle** (không phải 8h chuẩn). freshwatch/Velo không ghi nhận interval thay đổi này — funding_n vẫn báo 6 (= 6 × 4h = 24h, khác 6 × 8h = 48h cũ).

**B2 — Ngưỡng "bùng" không định lượng**:
- Spec hiện tại: "f_avg bùng dương + ngày parabol = cờ đỉnh nóng"
- "bùng" chưa có con số: gấp 2× baseline? absolute threshold? 
- Baseline TUT = 5bps (min cap) → "bùng" = bất kỳ rate > 5bps?
- Baseline BANK/TAG trong đỉnh nóng: thường 10-50bps → "bùng" = >100bps?

**Hệ quả**: Probe không thể auto-chấm cờ (e) — hiện dùng `rate > 0.0001` (>2× baseline) làm threshold tạm.

### Đề xuất spec bổ sung (chưa apply vào yaml)

```
exit_flag_funding_burst:
  venue_canonical: binance_fapi   # nguon chinh: /fapi/v1/fundingRate
  venue_fallback: velo_daily      # fallback: freshwatch funding_avg
  burst_multiplier: 3.0           # rate > 3× rolling_14d_avg = burst
  burst_abs_min: 0.00015          # absolute floor: rate > 15bps (neu baseline thap)
  interval_aware: true            # check actual funding_interval (4h vs 8h) tu fundingInfo
  confirmation: 1                 # 1 period du de bung = co (khac pos_r can 2 ngay)
  note: "TUT case: baseline = 5bps (min cap). Burst threshold = max(3*5bps, 15bps) = 15bps.
         Nếu token doi sang 4h cycle thi funding_n * 4h (khong phai * 8h).
         Velo aggregate co the smooth burst neu chi lay daily avg — uu tien fapi native."
```

**Việc operator cần làm**:
1. Xác nhận burst_multiplier (3× hay 5×?)
2. Xác nhận burst_abs_min (15bps là đủ hay cần cao hơn?)
3. Quyết định canonical venue: fapi native (cần VPS cron) hay Velo acceptable?

---

## Timeline

| ngày | việc |
|------|------|
| 04/08 | Phát hiện 2 gap từ TUT exit probe |
| ≤07/08 | Operator review + confirm ngưỡng số |
| ≤10/08 | Apply vào thresholds.yaml nếu approved |

**Reminder**: KHÔNG sửa thresholds.yaml trực tiếp — proposal này là chuẩn bị diff. Operator ký apply.

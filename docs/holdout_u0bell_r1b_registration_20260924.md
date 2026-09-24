# HOLD-OUT U0-BELL · R1b registration · pseudo-bell nền + detector đối chứng · CHỜ PIN

**Trạng thái:** **DRAFT · CHƯA PIN** · sẽ pin qua `_probe_pin_lib_20260924.py` (G2 · now_utc_iso).
**Ngày ghi:** 2026-09-24 (hold-out window · doctrine registration)
**Nguồn phán ANALYSIS:** `docs/analysis_rulings_holdout_20260924.md` · md5 `04f2826b884bde92ceb994af75bc849d`
  · grep clean · 0 backslash · 0 mojibake · 0 ctrl chars
**Nguồn phán liên đới (giữ):** `docs/analysis_rulings_holdout_20260923.md` · md5 `c74098082bdf4d9ad5efb9b8d0bab7a9`

---

## 1 · VẬT ĐO NỀN · pseudo-bell ngẫu nhiên (thay R1a(c))

**Nguồn:** rulings 24/09 mục 1 point 2:

> Nền đúng (R1b, đăng ký trước khi mở precision): **pseudo-bell ngẫu nhiên** — chọn ngẫu nhiên token-night đang hedge trong dải b làm neo, gộp episode 14d y hệt chuông, đếm cross-10d, loại outage, chỉ trên cửa sổ calibration (<20/09), n≥[50] episode mỗi dải (lặp lấy mẫu tới đủ). Đây là phép so "chuông vs ngày bất kỳ cùng vị trí div" — đúng câu C8 đặt.

**R1a giữ nguyên làm bản ghi** (body md5 `2db8b14052a8a3f3e6de7d3e530bd6f1`); **KHÔNG dùng R1a cho PASS**.
Nền dùng cho PASS = R1b (file này + kết quả B2 sau chạy).

---

## 2 · Tham số R1b-1 (nguyên văn)

**Nguồn:** rulings 24/09 mục 2:

> R1b-1: ký như DEV đề xuất — seed 20260924 · R=500 · rút không hoàn lại · gộp 14d · loại outage · n≥50/dải · báo trung vị + [5%, 95%]; lift chấm = P_obs / Σ w_b·median(base_b), in thêm lift tại 95% base làm mô tả bảo thủ.

| tham số | giá trị | đóng băng tới |
|---------|---------|---------------|
| SEED | **20260924** | 2026-10-31 |
| R (lần lặp) | **500** | 2026-10-31 |
| Rút | **token-night đang hedge (div_avg3(D) ≤ 0.5) trong dải b · KHÔNG hoàn lại** | 2026-10-31 |
| Gộp | **14d y hệt chuông** (gap ≤14d cùng token = cùng episode) | 2026-10-31 |
| Loại outage | **24-26/07/2026** (episode có `[D_first-2, D_first+10]` chạm outage → bỏ) | 2026-10-31 |
| Cửa sổ calibration | **2026-06-19 → 2026-09-05** (79 ngày · trước hold-out) | 2026-10-31 |
| n_min per bucket | **50 episodes** · dải không đủ 50 → **N/A** · KHÔNG hạ n · KHÔNG nới rút | 2026-10-31 |
| Báo per bucket | **trung vị + [5%, 95%]** percentile của rate qua R iterations | 2026-10-31 |
| Bucket biên | `[0, 0.3) · [0.3, 0.4) · [0.4, 0.5]` (theo C9 · registration R1 L64) | 2026-10-31 |
| Anchor | ngày ĐẦU episode (D_first · per gộp 14d) | 2026-10-31 |
| Cross-check window | `[D_first+1, D_first+10]` · Q1 cross-10d | 2026-10-31 |

**Lift chấm (nguyên văn từ rulings 24/09):**
```
lift = P_obs / Σ w_b · median(base_b)
```
- `median(base_b)` = trung vị rate qua R iterations của dải `b` (chỉ tính iterations đạt n≥50)
- `w_b` = tỷ lệ chuông thực rơi vào dải `b` (đo vào 21/10)
- **Bảo thủ:** in thêm lift tại 95% base_b (mô tả · không phải chấm chính)

---

## 3 · Đối chứng R1b-2 (detector)

**Nguồn:** rulings 24/09 mục 1 point 4 + mục 2:

> Thêm một đối chứng đăng ký sẵn: detector kiểm soát `div_avg3 ≥ 0.4 ∧ ≤0.5` không có Δacc — precision và lead của nó in cạnh chuông. Chuông phải THẮNG nó; đây là câu thật của hold-out, hơn cả lift.

> R1b-2: (b) mô tả bắt buộc in, không phải vế thứ 4 của PASS — ba vế pass đã đăng ký giữ nguyên; nhưng kết luận 21/10 phải viết hai câu tách nhau: "pass/không pass" và "thắng/không thắng đối chứng". "Thắng" = precision_bell > precision_ctrl ∧ lead_to_cross_bell ≥ lead_ctrl (cả hai trên cùng cửa sổ 10d, cùng gộp 14d). Đối chứng neo ngày đầu div_avg3 vào [0.4, 0.5] — xác nhận đúng định nghĩa. Nếu pass mà không thắng đối chứng → không ký ngưỡng, ghi "chuông ≈ vị trí div".

**Detector spec (đóng băng tới 31/10):**

| tham số | giá trị |
|---------|---------|
| Điều kiện in-band | `div_avg3(D) ∈ [0.4, 0.5]` (inclusive) |
| Δacc | **KHÔNG** (chỉ dùng div) |
| Gộp | **14d** (y hệt chuông) |
| Anchor | ngày ĐẦU episode |
| Cross-check window | **[D_first+1, D_first+10]** |
| Loại outage | 24-26/07 (giống pseudo-bell) |
| Cửa sổ | calibration `2026-06-19 → 2026-09-05` |

**"Thắng" chuông:**
```
precision_bell > precision_ctrl  AND  lead_to_cross_bell ≥ lead_ctrl
```
(cùng cửa sổ 10d · cùng gộp 14d · cùng loại outage)

**Kết luận 21/10 = HAI câu tách nhau:**
1. "Pass / không pass" (theo 3 vế đã ký R1 · registration Section 9: precision ≥55% ∧ lift phân tầng ≥1.5× ∧ lead_to_cross ≥2d)
2. "Thắng / không thắng đối chứng" (theo detector này)

**Pass mà không thắng đối chứng → KHÔNG KÝ NGƯỠNG · ghi "chuông ≈ vị trí div".**

---

## 4 · md5 code files đóng băng tới 31/10

**File:** `_probe_r1b_pseudo_bell_20260924.py`
- **md5: `cec7dc892a3a969e343289b16a2fb267`**
- bytes: 8904
- syntax OK verified

**File:** `_probe_r1b_detector_20260924.py`
- **md5: `72b880021f2662d9d7d0deeeaf9819d9`**
- bytes: 6258
- syntax OK verified

**File runner (chờ chạy B2 · sẽ thêm sau):** `_probe_r1b_run_20260924.py` (chưa tồn tại · md5 pin trong B2)

---

## 5 · Sổ đã-nhìn entry (đã ghi vào touch log)

**Nguồn:** rulings 24/09 mục 1 point 5:

> Theo Q6: đây là sửa cách đo nền (chưa có kết cục nào được xem), không đổi định nghĩa/ngưỡng U0 → không mở hold-out mới; ghi vào sổ đã-nhìn "R1b: đổi nền sau khi thấy nền in-sample, trước khi thấy precision".

Entry viết trong `docs/holdout_u0bell_touch_log.md` sau khi pin file này.

---

## 6 · Thứ tự thi hành (DEV giao)

```
B1 · Đăng ký R1b · file này · pin md5 body-self-ref · commit (SHA in vào touch log)
B2 · Chạy nền R1b (code pseudo-bell + detector đã pin)
      · In per dải: median · [5%, 95%] · n_episode · số lần đạt n≥50
      · Ghi addendum R1b-base (md5 riêng) · pin · commit
B3 · CHỈ SAU B2 commit: được chạy bảng precision in-sample
      (chuông + đối chứng · cửa sổ calibration)
      Chạy trước B2 → dừng, báo.
```

Hiện đang B1 · sau pin file này sẽ commit + báo SHA.

---

## 7 · Ranh giới

- **KHÔNG SCP** (V8)
- **KHÔNG sửa R1** (registration `96a97dca...` intact)
- **KHÔNG sửa R1a** (`2db8b140...` intact · giữ làm bản ghi · KHÔNG dùng PASS)
- **KHÔNG sửa rulings** 23/09 (`c74098082bdf...`) · 24/09 (`04f2826b884b...`)
- **KHÔNG chạy precision in-sample** cho tới sau B2 pin
- Code R1b (pseudo-bell + detector) ĐÓNG BĂNG tới 31/10 · thay đổi = file mới + doctrine reason

## 8 · R1b PIN md5

**md5 R1b pinned:** `d7a1e3a64e5af2c4524373d7cc4b1933` · pinned_at=2026-09-24T13:56:45Z · file này KHÔNG SỬA sau đây

# R1b-base · Addendum kết quả nền pseudo-bell · CHỜ PIN

**Trạng thái:** DRAFT · CHƯA PIN.
**Ngày ghi:** 2026-09-24
**Nguồn phán:** `docs/analysis_rulings_holdout_20260924.md` md5 `04f2826b884bde92ceb994af75bc849d`
**Nguồn luật registration R1b:** `docs/holdout_u0bell_r1b_registration_20260924.md` body-only md5 `d7a1e3a64e5af2c4524373d7cc4b1933`

**Code đã pin (verify run-time trong runner):**
- `_probe_r1b_pseudo_bell_20260924.py` md5 = `cec7dc892a3a969e343289b16a2fb267` (verified MATCH)
- `_probe_r1b_detector_20260924.py` md5 = `72b880021f2662d9d7d0deeeaf9819d9` (verified MATCH)
- `_probe_r1b_run_20260924.py` (runner)

---

## 1 · Tham số chạy (nguyên văn từ registration đã pin)

| tham số | giá trị |
|---------|---------|
| SEED | 20260924 |
| R (lần lặp) | 500 |
| GAP | 14d |
| N_MIN per bucket | 50 |
| CALIB WINDOW | 2026-06-19 → 2026-09-05 |
| OUTAGE | 24-26/07/2026 |
| BUCKETS | `<0.3` · `[0.3,0.4)` · `[0.4,0.5]` |
| Anchor | ngày ĐẦU episode (D_first per 14d group) |
| Cross-check | `[D_first+1, D_first+10]` |

## 2 · Pool (context)

| item | giá trị |
|------|-------:|
| Universe (freshwatch_symbols.txt) | 228 |
| by_sym coverage | 531 bare-syms |
| Total token-night hedge trong calib | **3537** |
| `<0.3` pool | 810 nights |
| `[0.3,0.4)` pool | 1270 nights |
| `[0.4,0.5]` pool | 1457 nights |

## 3 · Kết quả per bucket

**NGUỒN chạy:** `_probe_r1b_run_20260924.py` · 2026-09-24 · md5 pseudo-bell verified `cec7dc892a3a969e343289b16a2fb267`.

| bucket | median | [5%, 95%] | n_reached/R | ep_median | ep_min | ep_max | status |
|:------:|-------:|:---------:|:-----------:|----------:|-------:|-------:|:-------|
| `<0.3` | **N/A** | N/A | 0/500 | - | - | - | dải KHÔNG đạt n≥50 (theo phán · KHÔNG hạ n · KHÔNG nới rút) |
| `[0.3, 0.4)` | **25.77%** | [25.77%, 25.77%] | 500/500 | 97.0 | 97 | 97 | OK |
| `[0.4, 0.5]` | **66.42%** | [66.42%, 66.42%] | 500/500 | 137.0 | 137 | 137 | OK |

**Ghi chú (IN SỐ · KHÔNG kết luận):**
- Dải `<0.3`: 810 pool nights nhưng sau group 14d chỉ tạo episode dưới n_min=50 · KHÔNG hạ n · N/A. Không có nền hợp lệ cho dải này.
- Dải `[0.3, 0.4)` và `[0.4, 0.5]`: mọi 500 iterations tạo lượng episode giống nhau (ep_min = ep_max = median) → mọi rate iterations giống nhau → **[5%, 95%] shrink về single value = median**.
- Nguyên nhân quan sát được: sample pool + sort deterministic (tok, D) làm mọi iteration tạo cùng group episode identical. Đây là kết quả THẬT của code `cec7dc89` (đã đóng băng · KHÔNG sửa) trên pool hiện tại.
- Nếu DEV/ANALYSIS muốn phân phối thật ([5%, 95%] không suy sập về median), cần cách rút mới (VD sample subset K < pool size ngẫu nhiên) → **file mới + registration mới + pin mới** (doctrine giữ code đã pin).

## 4 · Nền base_b để dùng lift chấm (per registration Section 2)

**Công thức lift chấm:** `lift = P_obs / Σ w_b · median(base_b)`

**base_b (median rate qua R iterations · chỉ dải đạt n≥50):**

| bucket | median(base_b) | 95% base_b (bảo thủ) |
|:------:|---------------:|---------------------:|
| `<0.3` | **N/A** | N/A |
| `[0.3, 0.4)` | **25.77%** | 25.77% |
| `[0.4, 0.5]` | **66.42%** | 66.42% |

Vì median = 95% = single value (do variance zero), lift bảo thủ tại 95% base = lift chấm.

Khi 21/10 đo `w_b` (tỷ lệ chuông thực rơi vào dải), thay vào:
- Nếu chuông có mặt trong dải `<0.3` → base_b = N/A → cần ANALYSIS chấm cách xử lý (đề xuất: bỏ chuông dải đó khỏi lift, hoặc dùng nền chung 36.72%)

## 5 · So sánh với R1a (đã pin `2db8b14052a8...`) làm bản ghi

R1a giữ nguyên · KHÔNG dùng PASS.

| bucket | R1a (D_first anchor · loại outage) | R1b-base median | Δ |
|:------:|-----------------------------------:|----------------:|:---:|
| `<0.3` | 21.05% (n=19) | N/A | — |
| `[0.3, 0.4)` | 4.76% (n=21) | 25.77% (n=97) | +21.01 pp |
| `[0.4, 0.5]` | 70.65% (n=92) | 66.42% (n=137) | −4.23 pp |

**Đo (KHÔNG kết luận):** R1b có n_episode nhiều hơn R1a trong `[0.3, 0.4)` và `[0.4, 0.5]` do R1a chỉ tính D_first của first-hedge-episode per token (mỗi token 1-2 episode), còn R1b group từ ALL hedge nights trong bucket.

## 6 · Output artifact

- JSON: `scratch/R1b_base_result.json` · md5 `97001c81250305d61e84a361b5e20f04`
- Runner: `_probe_r1b_run_20260924.py`

## 7 · Ranh giới

- **KHÔNG SCP** (V8)
- **KHÔNG sửa R1** · R1a · R1b registration đã pin
- **KHÔNG sửa code pseudo-bell / detector đã pin** (nếu design cần thay đổi, tạo file mới)
- **KHÔNG chạy B3** (bảng precision in-sample) · chờ B2 addendum này pin + commit
- Sổ đã-nhìn giữ nguyên entry "R1b: đổi nền sau khi thấy nền in-sample, trước khi thấy precision"

## 8 · R1b-base PIN md5

**md5 R1b-base pinned:** `8b0c1e770c66a3f215dcd52b57d77fad` · pinned_at=2026-09-24T14:14:04Z · file này KHÔNG SỬA sau đây

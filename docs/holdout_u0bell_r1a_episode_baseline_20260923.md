# R1a · Addendum · nền episode theo dải · ĐO trước 21/10 · KHÔNG đổi luật

**Trạng thái:** **ADDENDUM · CHỈ SỐ NỀN** · không đổi luật R1 (registration md5 `96a97dca...`).
**Nguồn probe:** `_probe_r1a_episode_20260923.py`
**Nguồn output JSON:** `scratch/R1a_episode_baseline.json` · md5 `911840b8ec475d52b088f9341753ab5d`
**Ngày ghi:** 2026-09-23

**Luật R1 KHÔNG đổi:** file này chỉ chứa SỐ NỀN episode phân tầng theo dải (điều kiện thứ 10 trong Section 11 registration). Định nghĩa PASS · công thức C9 · ngày chấm C10/C12 · dải biên · outage filter · v.v. đều đã pin ở registration `96a97dca...`.

---

## 1 · Định nghĩa (khớp registration)

- **Episode:** chuỗi token-night baseline (div_avg3(D) ≤ 0.5) liên tiếp; **gap ≥14d** giữa 2 baseline nights cùng token = episode mới.
- **Nền chính:** token-episode (theo C8c + C12 · registration Section 9).
- **Kết cục:** cross trong `[D_first+1, D_first+10]` — `D_first` = chuông ĐẦU episode (C9 · registration L64 · L172).
- **Dải biên:** `[0, 0.3) · [0.3, 0.4) · [0.4, 0.5]` · div đo tại `D_first`.
- **Outage filter (C8b):** `[D_first-2, D_first+10] ∩ {2026-07-24, 25, 26}` ≠ ∅ → loại.

## 2 · Window đo

| item | value |
|------|-------|
| TARGET | 2026-09-17 (cùng V3 baseline để so-với 33.4% token-night) |
| WINDOW_START | 2026-06-19 (TODAY − 90) |
| WINDOW_END | 2026-09-05 (TODAY − 12) |
| n_days | 79 |
| universe | data/config/freshwatch_symbols.txt |

## 3 · Nền GỐC (không loại outage)

**Bảng R1a.a · toàn cửa sổ**

| n_denom (episodes) | n_num (cross) | rate |
|-------------------:|--------------:|-----:|
| 138 | 73 | **52.90%** |

**Bảng R1a.c · rate theo dải · GỐC**

| bucket | n_num | n_denom | rate |
|:------:|------:|--------:|-----:|
| `<0.3` | 4 | 19 | **21.05%** |
| `[0.3, 0.4)` | 1 | 21 | **4.76%** |
| `[0.4, 0.5]` | 68 | 98 | **69.39%** |

## 4 · Nền LOẠI outage (24-26/07)

**Bảng R1a.b · loại outage**

| n_loại | n_denom' | n_num' | rate' | Δ vs gốc |
|-------:|---------:|-------:|------:|:---------|
| 6 | 132 | 70 | **53.03%** | +0.13 pp |

**Bảng R1a.d · rate theo dải · LOẠI outage**

| bucket | n_num | n_denom | rate |
|:------:|------:|--------:|-----:|
| `<0.3` | 4 | 19 | **21.05%** |
| `[0.3, 0.4)` | 1 | 21 | **4.76%** |
| `[0.4, 0.5]` | 65 | 92 | **70.65%** |

## 5 · Nền chính dùng cho pass (C8a + C8b + C8c + C12)

**Nền phân tầng LOẠI OUTAGE (áp dụng cho pass · rate' phân tầng · R1a.d):**

| bucket | rate` (base_b) |
|:------:|---------------:|
| `<0.3` | 21.05% |
| `[0.3, 0.4)` | 4.76% |
| `[0.4, 0.5]` | 70.65% |

**Lift phân tầng (C9):**
```
lift = P_obs / Σ w_b · base_b
```
- `b` ∈ {<0.3 · [0.3, 0.4) · [0.4, 0.5]}
- `w_b` = tỷ lệ chuông rơi vào dải `b` (đo vào 21/10)
- `base_b` = rate' phân tầng (loại outage · Bảng R1a.d)

**Điều kiện PASS (registration Section 9 · không đổi):**
- Precision ≥ 55%
- Lift ≥ 1.5×
- Nhất quán trên nền lift phân tầng

## 6 · Ranh giới

- **KHÔNG đổi luật R1** (registration md5 `96a97dca4798b647a13ced5e05975d94` giữ nguyên)
- **KHÔNG in bảng precision in-sample** trước khi file này pin md5 (calibration đi sau)
- **File R1a này pin md5 riêng** · sau khi pin sẽ KHÔNG sửa
- Nếu số nền sai (VD probe bug), tạo R1a-v2 với lý do vào touch log · không sửa file này

## 7 · Provenance

| item | md5 |
|------|-----|
| Probe `_probe_r1a_episode_20260923.py` | (sẽ pin sau khi file này ổn định) |
| Output JSON `scratch/R1a_episode_baseline.json` | `911840b8ec475d52b088f9341753ab5d` |
| Registration R1 (nguồn luật) | `96a97dca4798b647a13ced5e05975d94` (body-only) |
| ANALYSIS rulings gốc | `c74098082bdf4d9ad5efb9b8d0bab7a9` |

## 8 · R1a PIN md5

**md5 R1a pinned:** `2db8b14052a8a3f3e6de7d3e530bd6f1` · pinned_at=2026-09-24T13:24:53Z · file này KHÔNG SỬA sau đây

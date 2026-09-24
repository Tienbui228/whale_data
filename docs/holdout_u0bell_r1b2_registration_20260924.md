# HOLD-OUT U0-BELL · R1b.2 registration · nền pseudo-bell ANALYSIS ký · CHỜ PIN

**Trạng thái:** DRAFT · sẽ pin qua `_probe_pin_lib_20260924.py` (G2 · now_utc_iso).
**Ngày ghi:** 2026-09-24
**Nguồn phán:** DEV → AGENT · 24/09 · R1b.2 · ANALYSIS đã ký (tin DEV chuyển)
**Rulings đính kèm:** `docs/analysis_rulings_holdout_20260924.md` md5 `04f2826b884bde92ceb994af75bc849d`

**Trỏ lỗi cũ:** R1b-base body md5 `8b0c1e770c66a3f215dcd52b57d77fad` = **BẢN GHI LỖI** · KHÔNG dùng cho PASS. Nguyên nhân: sorted sau shuffle làm mất tính ngẫu nhiên · anchor = đêm sớm nhất ≡ neo R1a đã rút.

---

## 1 · Thuật toán R1b.2 nguyên văn (ANALYSIS ký · DEV chuyển)

Mỗi dải `b`, mỗi lần lặp `i`:

```
seed_i = 20260924 + i
pool_b = token-night đang hedge, div_avg3(D) ∈ b,
         cửa sổ 2026-06-19 → 2026-09-05, loại outage 24-26/07

trộn pool_b theo seed_i;
duyệt theo thứ tự trộn;
nhận đêm (tok, D) nếu tok chưa có neo đã nhận trong [D−14, D+14] (trong dải b);
dừng khi đủ 50 neo;
không đủ 50 → lần lặp N/A cho dải b.
base_b,i = tỷ lệ neo có cross 0.5 trong [D+1, D+10].
```

Báo: `median` · `[5%, 95%]` · `số lần đủ 50 / 500` per dải.

---

## 2 · Hai cách đọc DEV (giữ rõ ràng)

### Cách đọc 1: pool ±14d THEO DẢI b

- `pool_b` = TẤT CẢ token-night có `div_avg3(D) ∈ b` trong cửa sổ calibration (loại outage)
- Ràng ±14d chỉ áp TRONG DẢI b: kiểm tra `tok` đã có neo trong [D−14, D+14] chỉ giữa các neo THUỘC dải b
- KHÔNG chia sẻ ràng ±14d giữa các dải (tok có thể có neo ở dải khác không ảnh hưởng)

### Cách đọc 2: P3 = median offset > 0

- `offset` = `D_neo − ngày đầu đoạn liên tục trong dải chứa neo`
- "Đoạn liên tục" = tập các đêm liên tiếp (gap ≤14d) TRONG DẢI b cho `tok` chứa `D_neo`
- Anchor "không sớm nhất run" khi offset > 0
- Test cho phân phối: median offset > 0 (không phải mọi anchor là ngày đầu run)

---

## 3 · Tham số đóng băng (tới 2026-10-31)

| tham số | giá trị |
|---------|---------|
| BASE_SEED | **20260924** |
| R (lần lặp) | **500** · `seed_i = BASE_SEED + i` |
| GAP_DAYS (±14d) | **14** |
| Forward window | `[D+1, D+10]` (Q1 cross-10d) |
| N_MIN per bucket | **50 neo · không đủ → N/A** |
| Cửa sổ calibration | `2026-06-19 → 2026-09-05` |
| Outage | `{2026-07-24, 2026-07-25, 2026-07-26}` (loại từ pool BEFORE trộn) |
| Buckets | `[0, 0.3)` · `[0.3, 0.4)` · `[0.4, 0.5]` |

---

## 4 · R1b.3 (a): dải N/A xử lý

**Phán DEV:** "R1b.3 (a): dải N/A loại khỏi lift, in `[dải <0.3: nền N/A, n_bell=k]`"

- Khi chuông thực có mặt trong dải b nhưng nền `base_b` = N/A (không đủ 50 neo trong iter nào):
  - **LOẠI dải b khỏi Σ w_b·median(base_b)** (không thêm vào tổng)
  - Renormalize weights: `w_b' = w_b / (1 - w_N/A)` cho các dải valid (**không · để lift bị pha loãng**)
  - **Print nguyên văn:** `[dải <0.3: nền N/A, n_bell=k]` trong output 21/10 để DEV thấy chuông bị bỏ

**Chọn (ANALYSIS chấm chọn hoặc phán khác):** hiện tại thiết kế = **loại dải khỏi lift · KHÔNG renormalize** · in số bell dải N/A. Chờ ANALYSIS xác nhận.

---

## 5 · md5 code mới (đóng băng tới 2026-10-31)

**Code chính:** `_probe_r1b2_pseudo_bell_20260924.py`
- **md5:** `6940d69da54fa2e87610517086be5195`
- 6316 bytes
- Import + gọi `resample_r1b2(pool_by_bucket, cross_check_fn, r_iterations, base_seed, n_min, gap)`

**Test suite:** `_probe_r1b2_tests_20260924.py` (chạy tests P1-P4 trên dữ liệu giả)

**Detector đối chứng (giữ nguyên từ R1b registration):**
- `_probe_r1b_detector_20260924.py` md5 `72b880021f2662d9d7d0deeeaf9819d9` (không đổi)

---

## 6 · P1-P4 tests trên dữ liệu GIẢ · ALL PASS

**Nguồn chạy:** `_probe_r1b2_tests_20260924.py` · 2026-09-24 · 20 tokens synthetic.

### P1 · 2 seed gốc khác → chuỗi base khác

| seed_base | n_rates (100 iter, bucket [0.4,0.5]) |
|-----------|-------------------------------------:|
| 1000 | 100 |
| 9999 | 100 |
| **Iter positions khác giá trị** | **87/100** |

**PASS.**

### P2 · Phương sai 500 lần > 0 (mỗi dải đủ 50)

| bucket | n_reached/R | median | variance | stdev |
|:------:|:-----------:|-------:|---------:|------:|
| `<0.3` | 500/500 | 68.00% | 30.6298 | 5.5344 |
| `[0.3, 0.4)` | 500/500 | 70.00% | 30.6877 | 5.5396 |
| `[0.4, 0.5]` | 500/500 | 72.00% | 24.4505 | 4.9447 |

**PASS · mọi dải variance > 0.**

### P3 · median offset > 0 (neo không luôn = ngày đầu run)

| bucket | n_anchors | median_offset | max_offset | n_off>0 |
|:------:|----------:|--------------:|-----------:|--------:|
| `<0.3` | 25000 | **22.0** | 76 | 21515/25000 |
| `[0.3, 0.4)` | 25000 | **25.0** | 78 | 21799/25000 |
| `[0.4, 0.5]` | 25000 | **16.0** | 77 | 21068/25000 |

**PASS · mọi dải median offset > 0.**

### P4 · Hand-verify thuật toán trên bộ giả nhỏ (5 tokens · 10 nights · seed 12345)

**Thứ tự trộn (seed=12345):**
```
[0] D · 2026-07-10 · div=0.47
[1] D · 2026-06-21 · div=0.48
[2] A · 2026-07-20 · div=0.43
[3] B · 2026-06-30 · div=0.46
[4] A · 2026-06-25 · div=0.44
[5] A · 2026-07-15 · div=0.41
[6] E · 2026-07-05 · div=0.49
[7] B · 2026-06-22 · div=0.45
[8] A · 2026-06-20 · div=0.42
[9] C · 2026-06-28 · div=0.40
```

**Neo đã nhận (n_min=5) · trace từng bước:**
- `[0] D · 07-10 → ACCEPT` (D chưa có neo)
- `[1] D · 06-21 → ACCEPT` (|07-10 − 06-21|=19d > 14d)
- `[2] A · 07-20 → ACCEPT` (A chưa có neo)
- `[3] B · 06-30 → ACCEPT` (B chưa có neo)
- `[4] A · 06-25 → ACCEPT` (|07-20 − 06-25|=25d > 14d)
- Dừng · **đủ 5 neo**

**Code output ≡ trace tay: TRUE**

**PASS.**

---

## 7 · Ranh giới

- **KHÔNG SCP** (V8)
- **KHÔNG chạy calibration data thật** cho tới sau khi file này pin + commit + có runner separately committed
- **KHÔNG chạy B3** (bảng precision in-sample) tới khi addendum R1b2-base pin + commit + DEV soát
- R1 (`96a97dca`) · R1a (`2db8b140`) · R1b registration (`d7a1e3a6`) · rulings 23/09 (`c74098082bdf`) · 24/09 (`04f2826b884b`) intact
- R1b-base 8b0c1e77 giữ nguyên · marker bản ghi lỗi
- Sổ đã-nhìn giữ nguyên "R1b: đổi nền sau khi thấy nền in-sample, trước khi thấy precision" + "R1b-base sorted-after-shuffle · phát hiện trước precision"

---

## 8 · Thứ tự thi hành

```
1. R1b.2 registration (file này) · pin body md5 self-ref · commit
2. Chạy nền R1b2 trên calib data thật · addendum R1b2-base
3. Pin R1b2-base · commit · in sha
4. DỪNG · chờ DEV soát trước B3
```

---

## 9 · R1b.2 PIN md5

**md5 R1b.2 pinned:** `ce6c667379bc743981e45cc0de834354` · pinned_at=2026-09-24T14:36:45Z · file này KHÔNG SỬA sau đây

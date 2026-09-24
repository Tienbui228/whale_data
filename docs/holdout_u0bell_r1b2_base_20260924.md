# R1b2-base · Addendum kết quả nền pseudo-bell (thuật toán ANALYSIS ký) · CHỜ PIN

**Trạng thái:** DRAFT · CHƯA PIN.
**Ngày ghi:** 2026-09-24
**Nguồn phán:** rulings 24/09 md5 `04f2826b884bde92ceb994af75bc849d` · DEV R1b.2 signed algo
**Nguồn luật registration:** R1b.2 body md5 `ce6c667379bc743981e45cc0de834354` · full-file `fdf8b416022a8616f1200f972d818e0d`

**Code đã pin (verify run-time):**
- `_probe_r1b2_pseudo_bell_20260924.py` md5 = `6940d69da54fa2e87610517086be5195` (verified MATCH lúc chạy)
- Runner: `_probe_r1b2_run_20260924.py`

---

## 1 · Tham số chạy

| tham số | giá trị (nguyên văn từ registration) |
|---------|-------|
| BASE_SEED | 20260924 · `seed_i = 20260924 + i` |
| R | 500 |
| GAP_DAYS | 14 (±14d cùng token trong dải) |
| N_MIN | 50 |
| CALIB | `2026-06-19 → 2026-09-05` |
| Outage | `{2026-07-24, 2026-07-25, 2026-07-26}` (loại từ pool BEFORE trộn) |
| Buckets | `<0.3` · `[0.3, 0.4)` · `[0.4, 0.5]` |
| Forward | `[D+1, D+10]` |

## 2 · Pool sizes (calibration THẬT · loại outage)

| bucket | pool_b size (nights) |
|:------:|--------------------:|
| `<0.3` | 696 |
| `[0.3, 0.4)` | 1056 |
| `[0.4, 0.5]` | 1268 |

Universe: 228 tokens (`freshwatch_symbols.txt`) · by_sym coverage: 531 bare-syms.

## 3 · Kết quả nền per bucket

**NGUỒN chạy:** `_probe_r1b2_run_20260924.py` · 2026-09-24T14:38:xxZ · verify md5 `6940d69d` MATCH.

| bucket | median | [5%, 95%] | variance | stdev | n_reached/R |
|:------:|-------:|:---------:|---------:|------:|:-----------:|
| `<0.3` | **18.00%** | [12.00%, 24.00%] | 13.3845 | 3.6585 | **500/500** |
| `[0.3, 0.4)` | **28.00%** | [20.00%, 38.00%] | 30.0328 | 5.4802 | **500/500** |
| `[0.4, 0.5]` | **60.00%** | [48.00%, 70.00%] | 43.3562 | 6.5845 | **500/500** |

**Mọi dải đạt 50 neo trong 500/500 iterations → không dải nào N/A.**

## 4 · Nền base_b để dùng lift chấm (R1b.2 công thức)

**Công thức lift chấm:** `lift = P_obs / Σ w_b · median(base_b)` (rulings 24/09)

**base_b (median · dùng cho lift):**

| bucket | median(base_b) | 95% base_b (bảo thủ) |
|:------:|---------------:|---------------------:|
| `<0.3` | **18.00%** | 24.00% |
| `[0.3, 0.4)` | **28.00%** | 38.00% |
| `[0.4, 0.5]` | **60.00%** | 70.00% |

**Không dải nào N/A → không phải áp R1b.3(a) loại dải khỏi lift.**

## 5 · So sánh 3 nền (R1a · R1b-base · R1b.2) · làm bản ghi

| bucket | R1a (rejected) | R1b-base (rejected · lỗi sort-after-shuffle) | **R1b.2 (dùng cho PASS · median)** |
|:------:|---------------:|---------------------------------------------:|-----------------------------------:|
| `<0.3` | 21.05% (n=19) | N/A | **18.00%** (n=50 · 500/500 iter) |
| `[0.3, 0.4)` | 4.76% (n=21) | 25.77% (single, 97 ep) | **28.00%** [20%, 38%] |
| `[0.4, 0.5]` | 70.65% (n=92) | 66.42% (single, 137 ep) | **60.00%** [48%, 70%] |

**Đo (không kết luận):**
- R1b.2 có phân phối thực sự (variance > 0) khác biệt R1b-base (variance = 0).
- R1b.2 `<0.3` = 18% (n=50 iter) tương đồng R1a 21% (n=19 non-resample).
- R1b.2 `[0.3, 0.4)` = 28% khác R1a 4.76% mạnh — R1a anchor D_first (biên vào hedge), R1b.2 anchor random qua các đêm trong bucket.
- R1b.2 `[0.4, 0.5]` = 60% median · [48%, 70%] · thấp hơn R1b-base 66% và R1a 70%.

## 6 · Output artifact

- JSON: `scratch/R1b2_base_result.json` · md5 `603ee3dfba25108b270fc3ede79ac34f`
- Runner: `_probe_r1b2_run_20260924.py`
- Code lib: `_probe_r1b2_pseudo_bell_20260924.py` md5 `6940d69da54fa2e87610517086be5195`

## 7 · Ranh giới

- **KHÔNG SCP** (V8)
- **KHÔNG chạy B3** (bảng precision in-sample) tới khi DEV soát R1b2-base này
- R1 · R1a · R1b · R1b.2 registration · rulings intact
- R1b-base 8b0c1e77 giữ · bản ghi lỗi
- Nếu 21/10 chuông rơi vào dải mà pool cạn (< 50 neo cho bất kỳ iter) → **R1b.3(a): loại dải khỏi lift · in `[dải X: nền N/A, n_bell=k]`** (hiện chưa xảy ra trong calib)

## 8 · R1b2-base PIN md5

**md5 R1b2-base pinned:** `4da9f4851aac977ae2bd80ad23543514` · pinned_at=2026-09-24T14:39:25Z · file này KHÔNG SỬA sau đây

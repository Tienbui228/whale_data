# gomh_gate_closure — H-tier §H5 gate closure doc
**Verdict: (a) ARCHIVE — operator ký 14/08/2026**

---

## PROVENANCE (L-48)

| Trường | Giá trị |
|--------|---------|
| data-source | `/root/Data_back_test/whale_data/data/raw/klines_1h` + `oi_hist_1h` (VPS canonical store) |
| machine | VPS 5.223.67.21 |
| date-range | BANK 2026-06-29→07-14 · TUT 2026-06-26→07-12 · AKE 2026-06-26→07-07 · CYS 2026-07-20→08-06 · BANANAS31 neg 07-01→07-20 · APR neg 07-01→08-04 · XPIN neg 07-31→08-07 |
| code-commit | `scripts/compute_h_daily.py` @ VPS HEAD (Phase 5, 14/08/2026) |

Gate probe: `_probe_phase6_h5_gate_20260814.py` · Verify probe: `_probe_6_verify_20260814.py`

---

## GATE §H5 RESULT — FAIL tất cả 4 metrics

| Metric | Gate §H5 (≥3/4 positive sep + nhất-quán-dấu) | Result |
|--------|----------------------------------------------|--------|
| h1_skew | 0/4 positive cases separate from negative | **FAIL** |
| h2_oiw | 0/4 | **FAIL** |
| h3_conc | 0/4 | **FAIL** |
| h4_cloc | 0/4 | **FAIL** |

Code verified per-hour (không phải daily aggregate): `_probe_6_verify_20260814.py` trace BANK 2026-07-05 → h1_skew +0.0198 computed per 18 giờ, MATCH stored value.

---

## EXHIBIT A — XPIN crowd-giả-gom vs BANK-build: 3-metric IQR

**Câu hỏi:** XPIN (crowd-giả-gom, book mỏng, markup +7.1%/taker 46.6% ngày 07/08) có phân biệt được khỏi BANK-build (gom thật Jun29-Jul14) trên h1/h3/h4 không?

| Metric | Window | n | median | Q1 | Q3 | IQR |
|--------|--------|---|--------|-----|-----|-----|
| h1_skew | BANK-build (Jun29-Jul14) | 15 | -0.0725 | -0.1014 | -0.0189 | 0.0825 |
| h1_skew | XPIN-neg (Jul31-Aug07) | 7 | -0.0967 | -0.1168 | -0.0788 | 0.0380 |
| h3_conc | BANK-build | 16 | 0.3629 | 0.2704 | 0.3946 | 0.1242 |
| h3_conc | XPIN-neg | 8 | 0.3301 | 0.3212 | 0.3862 | 0.0650 |
| h4_cloc | BANK-build | 16 | 0.2658 | 0.2174 | 0.3053 | 0.0879 |
| h4_cloc | XPIN-neg | 8 | 0.2844 | 0.2572 | 0.3292 | 0.0720 |

**Overlap check (tách = IQR không chồng):**

| Metric | BANK Q1–Q3 | XPIN Q1–Q3 | Overlap range | Tách? |
|--------|-----------|-----------|---------------|-------|
| h1_skew | [-0.101, -0.019] | [-0.117, -0.079] | [-0.101, -0.079] | **KHÔNG** |
| h3_conc | [0.270, 0.395] | [0.321, 0.386] | [0.321, 0.386] | **KHÔNG** |
| h4_cloc | [0.217, 0.305] | [0.257, 0.329] | [0.257, 0.305] | **KHÔNG** |

**Headline:** Texture 1h đo **BID-ĐỠ**, không đo **AI-ĐỠ** — XPIN crowd-giả-gom IQR-overlap BANK-build hoàn toàn cả 3 metric, **KHÔNG TÁCH**. Median build lệch chiều KHÔNG nhất quán (h1 BANK build có ngày dương lẫn âm) → không tồn tại phiên bản đảo-ngưỡng nào cứu gate.

---

## NOTES

**h1/h3/h4 build-vs-negative IQR overlap:** Overlap trên data hợp lệ (code verified per-hour). Baseline một số case rỗng do data-path: store VPS chỉ cache từ ngày collector bắt đầu hứng — xem carve-out B.

**h2_oiw confound share-based:** BANK build median h2=0.41 < BANANAS31 neg h2=0.61 — hướng ngược kỳ vọng KHÔNG phải bug code mà là confound cấu trúc: stealth_grind = giá grind lên = phần lớn giờ xanh → OI tự nhiên build trên giờ xanh → h2 thấp. Share-based metric phụ thuộc archetype. → carve-out A triệt confound bằng rate-normalize.

---

**Note ledger:** Closure-prompt ghi "cột thêm vào gom_h_daily.csv"; implementation tách thành file riêng `gom_h2prime_daily.csv`, có chủ đích — tránh kéo schema detection đã archive vào forward-experiment store, freeze ledger cũ đúng tinh thần archive.

## NOTE — BẮT CONFOUND-THAY-CONFOUND

h2_old share-based → h2′ difference (`rate_neg − rate_pos`) → h2r ratio (`rate_neg / rate_pos`).

**Iteration 1 (share):** confound archetype — mẫu số `Σ ΔOI⁺(all)` phụ thuộc tỉ lệ giờ đỏ/xanh của từng ngày, không phải absorption thật.

**Iteration 2 (difference):** triệt confound tỉ-lệ-giờ nhưng nhét confound mới: `rate_neg − rate_pos` còn phụ thuộc tuyệt-đối OI-size. Token OI 10× lớn hơn → difference tự nhiên lớn hơn dù absorption cùng cường độ → không thể so cross-token.

**Iteration 3 (ratio):** `h2r = rate_neg / rate_pos` — vô đơn vị, scale-free. Triệt cả hai confound. `h2r_log = ln(h2r)` — symmetric, sign-readable. Không cap — ngày cực đoan là tín hiệu thật, không nên truncate.

**Bài học:** Khi sửa confound bằng transform, kiểm tra transform mới có đưa confound khác vào không (đổi mẫu số → đổi unit → đổi confound). Vào regression checklist cạnh họ share-based (M1) và mean-of-ratios (M2).

---

## CARVE-OUT A — h2′ rate-normalized (SỐNG, không gate)

**Định nghĩa:** `h2_prime = mean(ΔOI⁺ | giờ ret≤0) − mean(ΔOI⁺ | giờ ret>0)`
- Triệt confound share-based: chia theo số giờ mỗi nhóm, không theo tổng
- `h2_prime > 0` = OI tăng NHANH HƠN PER-HOUR vào giờ giá giảm = absorption signal
- Ghi vào `gom_h2prime_daily.csv` (watchlist-only, append-only)
- Cron 00:20 UTC GIỮ NGUYÊN — scope thu nhỏ về watchlist
- Không gate, không alert — đọc khi ≥2 build-window forward đủ coverage

## CARVE-OUT B — data-path note (spec archive)

`klines_1h = fapi paginate TRỌN ĐỜI symbol, bất tử`. Store VPS (`data/raw/klines_1h`) chỉ cache từ ngày collector bắt đầu. Baseline TUT (Jun05-Jun25) rỗng vì store TUT bắt đầu Jun26. Mở lại H-tier bất kỳ biến thể nào **phải kéo fapi trực tiếp, KHÔNG đọc store** — store = convenience cache, không phải lịch sử hoàn chỉnh.

---

*Lessons ghi tay vào CASE_INDEX.xlsx LESSONS (operator, không agent):*
*① Gate 14/08 đóng texture-1h bằng số — G1 doctrine tái xác nhận hướng độc lập #2: cái tách gom khỏi xả không ở perp texture, ở CHIỀU DÒNG on-chain.*
*② Họ bệnh share-based-metric: metric dạng share mà mẫu số phụ thuộc archetype → normalize per-unit trước khi so. Vào regression checklist cạnh họ mean-of-ratios (M1). Bắt lần 4/3-tuần, lần đầu TRƯỚC production.*

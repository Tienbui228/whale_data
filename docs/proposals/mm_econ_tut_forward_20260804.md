# MM-ECON TUT — Forward Analysis v1
**Date:** 04/08/2026 | **Ngày T0:** 07-22 | **D hiện tại:** D+13
> ⏰ **Hạn chấm PASS/FAIL: 18/08/2026** (T+27 từ T0). Sau khi chấm xong → archive vào `docs/proposals/archive/`.
**Status:** ANALYSIS ONLY — bảng P1-P5 ghi predictions để chấm PASS/FAIL sau
**Nguồn:** freshwatch_daily (35 rows), fapi klines daily+4h, probe `_probe_tut_mm_econ_20260804.py`

> ⚠️ **04/08 LIVE UPDATE (klines):** px=0.02357 (+15.7%, H=0.02419), vol=24.3M USDT.
> Đây là ngày vol lớn nhất post-T0 (so với 17.9M ngày 03/08). OI 04/08 chưa có
> (cron 01:20 UTC 05/08). Theo dõi gLSR + OI ngay khi có data.

---

## U1 — B Tính Chính Xác (Bucket VWAP, khuôn F2-IDOL)

### U1.1 Full freshwatch series (06-27 → 08-03)

| Ngày | px | OI (M) | ΔOI (M) | pos_r | gLSR | vol | fn |
|------|-----|--------|---------|-------|------|-----|----|
| 06-27 | 0.01056 | 2.352 | — | 4.367 | 3.115 | 2.0M | 6 |
| 06-28 | 0.01054 | 2.238 | -0.115 | 3.897 | 3.548 | 2.5M | 6 |
| 06-29 | 0.01052 | 2.211 | -0.027 | 4.630 | 3.259 | 2.6M | 6 |
| 06-30 | 0.01048 | 2.229 | +0.018 | 4.721 | 3.643 | 3.7M | 6 |
| 07-01 | 0.01062 | 2.240 | +0.011 | 4.573 | 3.301 | 2.7M | 6 |
| 07-02 | 0.01058 | 2.319 | +0.079 | 4.515 | 3.058 | 3.6M | 6 |
| 07-03 | 0.01088 | 2.286 | -0.032 | 4.244 | 3.195 | 2.8M | 6 |
| 07-04 | 0.01126 | 2.339 | +0.052 | 4.490 | 3.134 | 3.1M | 6 |
| 07-05 | 0.01115 | 2.275 | -0.064 | 4.446 | 3.160 | 7.4M | 6 |
| 07-06 | 0.01019 | 2.244 | -0.031 | 4.104 | 2.946 | 6.0M | 6 |
| 07-07 | 0.01019 | 2.167 | -0.077 | 3.264 | 2.810 | 5.3M | 6 |
| 07-08 | 0.00972 | 2.020 | -0.147 | 3.148 | 2.857 | 2.5M | 6 |
| **07-09** | **0.01066** | **1.922** | -0.098 | **3.459** | **2.997** | 9.4M | 6 |← **OI FLOOR = B_min** |
| 07-10 | 0.01100 | 2.328 | **+0.406** | 3.519 | 2.529 | 5.0M | 6 |
| 07-11 | 0.01272 | 2.600 | +0.272 | 4.204 | 2.180 | 42.2M | 6 |← vol peak pre-ignition |
| **07-12** | **0.01239** | **3.269** | **+0.669** | **3.038** | **1.195** | 14.7M | 6 |← **gLSR_min = FUEL RELOAD** |
| 07-13 | 0.01226 | 2.774 | -0.495 | 4.620 | 1.562 | 6.4M | 6 |
| 07-14 | 0.01262 | 2.712 | -0.062 | 5.475 | 1.595 | 3.9M | 6 |
| 07-15 | 0.01278 | 2.708 | -0.003 | 5.812 | 1.767 | 4.7M | 6 |
| 07-16 | 0.01287 | 2.893 | +0.185 | 5.706 | 1.990 | 4.1M | 6 |
| 07-17 | 0.01293 | 2.808 | -0.085 | 5.678 | 1.979 | 3.8M | 6 |
| 07-18 | 0.01299 | 3.030 | +0.222 | 5.048 | 1.946 | 2.8M | 6 |
| 07-19 | 0.01312 | 3.162 | +0.132 | 4.921 | 1.772 | 2.0M | 6 |
| 07-20 | 0.01371 | 3.089 | -0.073 | 4.725 | 1.910 | 7.2M | 6 |
| 07-21 | 0.01516 | 3.413 | +0.324 | 4.305 | 1.896 | 15.8M | 6 |
| **07-22** | **0.01444** | **3.764** | **+0.351** | **3.887** | **1.779** | 7.5M | 6 |← **T0 (markup_start)** |
| 07-23 | 0.01387 | 3.387 | -0.377 | 5.083 | 1.729 | 4.0M | 6 |
| [07-24 MISS] | 0.01479* | — | — | — | — | 1.2M* | — |← klines data |
| [07-25 MISS] | 0.01533* | — | — | — | — | 2.1M* | — |← klines data |
| [07-26 MISS] | 0.01622* | — | — | — | — | 1.2M* | — |← klines data |
| 07-27 | 0.01571 | 4.202 | +0.815 | 4.333 | 1.904 | 1.5M | 6 |
| 07-28 | 0.01389 | 3.738 | -0.464 | 4.657 | 2.018 | 2.4M | 6 |
| 07-29 | 0.01466 | 3.683 | -0.054 | 4.911 | 1.922 | 2.2M | 6 |
| 07-30 | 0.01460 | 3.752 | +0.068 | 4.585 | 1.851 | 1.1M | 6 |
| 07-31 | 0.01560 | 3.899 | +0.147 | 4.959 | 1.857 | 2.4M | 6 |
| 08-01 | 0.01735 | 4.294 | +0.395 | 4.169 | 2.031 | 9.8M | 6 |
| 08-02 | 0.01741 | 4.997 | **+0.704** | 3.458 | 1.721 | 3.1M | 6 |← OI_max so far |
| 08-03 | 0.01986 | 4.831 | -0.167 | 4.014 | 1.685 | 17.9M | 6 |
| **08-04*** | **0.02357*** | **—** | — | — | — | 24.3M* | — |← **live klines** |

*`*` = từ Binance fapi klines (không phải freshwatch)

---

### U1.2 Bucket VWAP Analysis (klines daily)

**Định nghĩa buckets:**

| Bucket | Ngày | Ý nghĩa | OI range |
|--------|------|---------|---------|
| Bucket-0: Pre-grind | 06-27→07-08 | Crowd-long giảm, OI flat | 2.352→2.020M (-14%) |
| Bucket-1: Grind tới đáy | 07-09 | OI_floor = B_min | 1.922M |
| Bucket-2: Ignition spike | 07-10→07-12 | OI bùng +0.669M một ngày (07-12) | 1.922→3.269M (+70%) |
| Bucket-3: Post-spike rebuild | 07-13→07-22 | pos_r ổn định 5.0+, OI grind | 2.712→3.764M |
| Bucket-4: Post-T0 | 07-22→nay | Markup phase | 3.764→4.997M |

**Build VWAP theo bucket (klines typical = (H+L+C)/3):**

*Bucket-0 — Pre-grind RED candles (07-05 to 07-08 = dip days):*
- 07-05 RED: typical=0.01104, vol=2.5M
- 07-06 RED: typical=0.01030, vol=2.0M
- 07-07 RED: typical=0.01017, vol=1.8M
- 07-08 RED: typical=0.00972, vol=0.8M
→ VWAP_B0_red = 0.01052 USDT (vol-weighted 7.1M)

*Bucket-1 — OI floor day (07-09, GRN reversal day):*
- 07-09 GRN: typical=0.01048, vol=3.1M

*Bucket-2 — Ignition spike (07-10→07-12, dominant vol):*
- 07-10 GRN: typical=0.01132, vol=1.7M
- 07-11 GRN: typical=0.01255, vol=14.1M ← **56% of bucket vol**
- 07-12 RED: typical=0.01233, vol=4.9M (gLSR_min day)
→ VWAP_B2 = 0.01222 USDT (vol-weighted 20.7M)

*Bucket-3 — Post-spike rebuild (07-13→07-22):*
Red days: 07-19 (typical=0.01309, vol=0.7M), 07-22/T0 (typical=0.01423, vol=2.5M)
Green days: 07-13 to 07-21 (bulk vol on 07-21 = 5.3M, typical=0.01502)
→ VWAP_B3 = 0.01335 USDT (vol-weighted 24.4M)

**Composite Build_VWAP (khuôn F2 — OI_floor to T0 = B_min to B_T0):**
= (3.1×0.01048 + 20.7×0.01222 + 24.4×0.01335) / 48.2
= (0.03249 + 0.25295 + 0.32574) / 48.2
= **0.01269 USDT** ← Build_VWAP_F2

*So sánh với điểm nhất quán:*
| Phạm vi | Build_VWAP |
|---------|-----------|
| Full 01/07→22/07 (all candles) | 0.01239 USDT |
| OI_floor→T0 (07-09→22/07) | **0.01285 USDT** ← reference |
| Fuel-reload→T0 (07-12→22/07) | 0.01344 USDT |
| B2+B3 bucket (07-09→22/07, F2) | 0.01269 USDT |

**→ Build_VWAP canonical: 0.01285 USDT** (07-09→22/07, OI_floor to T0)
(Trước đây operator ước 0.0125 — số thực: **+2.8%** cao hơn ước)

---

### U1.3 ΔOI per bucket — Red vs Green split

**Tổng ΔOI dương (MM add-on) trong build period:**

| Giai đoạn | ΔOI positive | Ngày tương ứng |
|-----------|-------------|---------------|
| Pre-grind | +0.225M | 06-30, 07-01, 07-02, 07-04 |
| Bottom reversal | +0.406M | 07-10 (single day bounce) |
| B2 spike | +0.272M + 0.669M | 07-11 + 07-12 |
| B3 rebuild | +0.185M+0.222M+0.132M+0.324M+0.351M | 07-16→07-22 |
| **Tổng ΔOI+ build** | **+2.786M** | |

**ΔOI âm (crowd/short exit) trong build:**

| Giai đoạn | ΔOI negative | Ngày |
|-----------|-------------|------|
| Pre-grind | -0.375M | 06-28, 06-29, 07-03, 07-05, 07-06, 07-07, 07-08, 07-09 |
| B3 | -0.085M + -0.073M + -0.495M | 07-13, 07-17, 07-20 (07-13 là lớn nhất -0.495M = partial flush) |
| **Tổng ΔOI-** | **-1.028M** | |

**Net position built (07-09→07-22) = OI_T0 - OI_floor = 3.764 - 1.922 = 1.842M USDT**

Đây là ΔOI_net_build = B_netadd. MM contributed một phần, crowd-long contributed phần còn lại.

---

## U2 — OI Series + ΔOI_lũy_kế/B Clock

**B_ref = 1.922M** (OI_floor 07-09) — dùng cho clock, consistent với B_min.
**B_T0 = 3.764M** (T0 07-22) — dùng cho MM_mult calculation.

*Note: Binance fapi openInterestHist endpoint trả 404. Dùng freshwatch oi_usd = canonical 00:00 UTC snapshot.*

### ΔOI_cum/B_ref Clock Table

| Ngày | OI (M) | ΔOI_cum | ΔOI/B_ref | ΔOI/B_T0 | px | Sự kiện |
|------|--------|---------|-----------|----------|-----|---------|
| 07-09 | 1.922 | 0 | **0%** | — | 0.01066 | **B_ref (OI floor)** |
| 07-11 | 2.600 | +0.678 | **35%** | — | 0.01272 | Vol spike pre-ignition |
| 07-12 | 3.269 | +1.347 | **70%** | — | 0.01239 | **gLSR_min (fuel reload)** |
| 07-22 | 3.764 | +1.842 | **96%** | **0%** | 0.01444 | **T0 / B_T0** |
| 07-23 | 3.387 | +1.465 | **76%** | -10% | 0.01387 | |
| 07-27 | 4.202 | +2.280 | **119%** | +12% | 0.01571 | |
| 07-28 | 3.738 | +1.816 | **95%** | -1% | 0.01389 | |
| 07-29 | 3.683 | +1.761 | **92%** | -2% | 0.01466 | |
| 07-30 | 3.752 | +1.830 | **95%** | -0.3% | 0.01460 | |
| 07-31 | 3.899 | +1.977 | **103%** | +4% | 0.01560 | |
| 08-01 | 4.294 | +2.372 | **123%** | +14% | 0.01735 | |
| 08-02 | 4.997 | +3.075 | **160%** | +33% | 0.01741 | **OI_max so far** |
| 08-03 | 4.831 | +2.909 | **151%** | +28% | 0.01986 | |
| 08-04* | ~6M±1M* | ~+4M* | **~208%*** | **~59%*** | 0.02357 | **Live est. (vol 24.3M)** |

*08-04: OI ước tính từ vol spike và px +15.7%; chờ xác nhận cron 01:20 UTC 05/08.*

### P3 Watch Bands (ΔOI_cum/B_ref)

| Band | ΔOI_cum | OI target | Ý nghĩa |
|------|---------|----------|---------|
| **1× (chạm)** | 1.922M | **3.844M** | Đã vượt qua (07-12) |
| **2× (watch)** | 3.844M | **5.766M** | Ngưỡng gần — ~08-04/05 ước |
| **3× (alert)** | 5.766M | **7.688M** | Đồng hồ chính theo dõi hằng ngày |
| **5× (red zone)** | 9.610M | **11.532M** | Tương đương BANK exit zone |
| **7× (extreme)** | 13.454M | **15.376M** | Tương đương BANK pre-peak |

→ Thêm vào chốt canh hằng ngày: **"OI Binance vs 5M / 7M / 10M"** (scaled từ bands trên).

---

## U3 — Fuel-Reload Point Chính Xác

### Xác định

| Metric | Ngày | Giá trị | Ý nghĩa |
|--------|------|---------|---------|
| gLSR_max pre-reload | 06-30 | 3.643 | Peak crowd-long (nhất series) |
| gLSR_min (reload nadir) | **07-12** | **1.195** | **Fuel reload: từ cực kỳ long→gần neutral** |
| gLSR đầu rebuild | 07-13 | 1.562 | +31% từ đáy |
| gLSR rebuild ổn định | 07-14→08-03 | 1.595→2.031 | Rebuild band |
| gLSR 08-03 (mới nhất) | 08-03 | 1.685 | Đang trong band rebuild |

**Cơ chế fuel-reload:**
- 06-27→07-11: gLSR giảm từ 3.11→2.18 (crowd long vẫn mạnh nhưng đang giảm)
- 07-12 (spike event): OI +0.669M trong 1 ngày → crowd short vào ồ ạt → gLSR sập 2.18→1.195
  - Đây là wash-by-crash (L-14): OI tăng nhưng gLSR sập = crowd short flood in
  - KHÁC với L-26 (gia tăng gLSR khi giá sập)
- 07-13→nay: rebuild bền vững từ 1.56→2.03

**Hệ quả với P1 ceiling:**
- OI_reload point: 07-12, OI=3.269M, px=0.01239
- Nếu dùng px tại fuel-reload (0.01239) làm reference thay vì Build_VWAP_F2 (0.01285):
  - P1_low: 0.01239 × 1.5 = 0.01859
  - P1_mid: 0.01239 × 2.0 = 0.02478
  - P1_high: 0.01239 × 2.5 = 0.03098
- So với Build_VWAP canonical (0.01285): tương đương, spread nhỏ (<4%)

→ **P1 ceiling không nhạy cảm với việc chọn Build_VWAP hay px_reload** — cả hai cho kết quả rất gần nhau.

---

## U4 — Backfill 24-26/07 MISSING

### Kết quả probe

**VPS store**: không có file TUTUSDT klines_1h cho 24-26/07 (partition không tồn tại).
**Freshwatch**: xác nhận gap — 35 rows từ 06-27→08-03 với jump 07-23→07-27.

**Dữ liệu thay thế từ Binance fapi klines (daily):**

| Ngày | color | O | H | L | C | vol (M) | Ghi chú |
|------|-------|-----|-----|-----|-----|---------|---------|
| 07-24 | GRN | 0.01404 | 0.01480 | 0.01374 | 0.01479 | 1.2M | +5.3% — bình thường |
| 07-25 | GRN | 0.01478 | 0.01598 | 0.01465 | 0.01533 | 2.1M | +3.7% — tiếp tục |
| 07-26 | GRN | 0.01533 | 0.01625 | 0.01500 | 0.01622 | 1.2M | +5.8% — steady grind |

**Đánh giá:**
- 3 ngày đều green, vol 1.2–2.1M (thấp, không có event lớn)
- Không có vol spike, không có gLSR/OI data → không thể điền DAILY CASE sheet
- **Gap E1 vẫn còn về dữ liệu perp** (OI, gLSR, pos_r, taker không khôi phục được từ store)
- Hành động: ghi note vào DAILY TUT rows cho 24-26/07 = `data_bad=1, nguon=klines_only`

---

## U5 — Kho TUT Phân Loại L-42

### Tra cứu

| Nguồn | Kết quả |
|--------|---------|
| Freshwatch store | Không có cột exch_balance_delta hoặc wallet_activity |
| VPS store | Không có on-chain data cho TUT |
| Nansen | LOCKED (env NANSEN_KEY_LOCKED) |
| Local chain data | Không có |

**→ ABSTAIN — không có data nguồn kho TUT.**

**Hệ quả L-42 với TUT:**
- mm_archetype = **PENDING** (chờ operator)
- Toàn bộ M2/on-chain reads cho TUT = chưa thể phân loại
- P5 (exit ceiling adjustment per kho type) = **TREO** trên ô này

**Operator cần cung cấp:**
1. Nguồn kho 83% (đề cập trong task): deployer wallet? vesting? self-custody?
2. Unlock schedule TUT nếu có
3. Chain data deposit/withdrawal pattern

---

## U6 — Cập Nhật Chốt Canh TUT Daily

Thêm 2 dòng vào bảng chốt canh hằng ngày của TUT:

| Cờ | Điều kiện | Threshold | Ngày đo gần nhất (03/08) | Status |
|----|----------|----------|--------------------------|--------|
| **OI vs 8M** | OI ≥ 8.0M | OI 1h Binance ≥ 8M = alert zone | 4.831M | ❌ Chưa |
| **OI vs 10M** | OI ≥ 10.0M | OI ≥ 10M = red zone (P3 3× band) | 4.831M | ❌ Chưa |
| **gLSR vs 1.1** | gLSR ≤ 1.1 | wash-watch (L-26 precondition) | 1.685 | ❌ Không gần |
| **gLSR rebuild** | gLSR ≥ 2.5 | fuel đủ mạnh cho markup wave | 1.685 | ❌ Còn xa |
| **pos_r crash** | pos_r drop ≥30%/3d | L-26 trigger — dỡ STAND_ASIDE nếu có | pos_r=4.014 | ❌ Không gần |

*Tham chiếu: OI 8M/10M scaled từ P3 bands. gLSR 1.1 = threshold tái-ARM (L-38).*
*Nếu 04/08 OI xác nhận ≥5.5M → khoảng cách 8M = 45%; tiếp tục cần nhiều ngày.*

---

## Bảng P1-P5 — Predictions (Chấm PASS/FAIL)

> Bảng này là cam kết prediction tại 04/08/2026 D+13.
> Không sửa sau khi commit. Chấm tại deadline bên dưới.

### P1 — Exit Ceiling (px_max kỳ vọng)

**Build_VWAP canonical: 0.01285 USDT** (07-09→22/07, OI_floor to T0, F2 khuôn)
*(Trước đây ước 0.01250 → sửa lên 0.01285 từ probe thực)*

| Scenario | MM_mult | Exit_px_pred | Tình trạng vs hiện tại |
|----------|---------|-------------|----------------------|
| P1-low (1.5×) | 1.50× | **0.01928 USDT** | ĐÃ VƯỢT QUA (08-04 px=0.02357) |
| P1-mid (2.0×) | 2.00× | **0.02570 USDT** | Gần (px 04/08 close = 0.02357, H=0.02419) |
| P1-high (2.5×) | 2.50× | **0.03213 USDT** | Chưa |
| P1-extreme (3.0×) | 3.00× | **0.03855 USDT** | Chưa |

**Prediction P1**: Exit_px kỳ vọng trong range **0.02500–0.03500 USDT** (P1-mid → P1-high).
- Lý do: CROWD-LONG subtype chưa có calibrated MM_mult; dùng bracket 2.0–2.5× (thấp hơn BANK 5.0×, cao hơn IDOL 1.57×)
- **P1-low đã bị phá (04/08)** — là xác nhận markup đang chạy
- **Trigger PASS/FAIL**: px đỉnh đạt 0.025–0.035 trước khi L-26 trigger = PASS P1

**Deadline chấm P1:** Ngay sau L-26 trigger (pos_r crash ≥30%/3d), hoặc 01/09/2026 nếu không có L-26.

---

### P2 — L-26 Trigger Timeline

**Điều kiện L-26:** pos_r drop ≥30% trong 3 ngày liên tiếp (KHÔNG phải ≥30% 1 ngày).

**Observation tại 04/08:**
- pos_r 03/08: 4.014 (elevated, crowd-long mạnh)
- Để trigger: pos_r phải về ≤ 2.810 trong 3 ngày
- Khoảng cách: 4.014 → 2.810 = -30.0% (edge case chính xác)
- Tốc độ sập lịch sử TUT: max 1 ngày = -27.7% (07-12); max 3 ngày chưa thấy ≥30%

**Prediction P2:**
- L-26 sẽ xảy ra TRƯỚC 22/08/2026 (D+31)
- pos_r crash kỳ vọng: từ khoảng 4.0–5.5 → xuống ≤2.8 → cần catalyst (vol surge như 04/08)
- Nếu px tiếp tục tăng và crowd pile in → pos_r build thêm → cần flush lớn hơn
- Nếu px correction mạnh → pos_r crash tự nhiên

**Prediction P2-deadline:** L-26 trigger trước 22/08/2026.
- **PASS:** L-26 trigger xảy ra trong window AND px tại ngày trigger ≥ P1-low (0.01928)
- **FAIL:** Không có L-26 trigger đến 22/08 HOẶC px đã sập sâu trước khi L-26 (false dump)

---

### P3 — OI_exit Target + ΔOI/B Clock

**B_ref = 1.922M | B_T0 = 3.764M**

Current (ước 04/08): OI ~5.5–6.5M, ΔOI/B_ref ~186–238%

**Prediction P3:**
- OI_exit kỳ vọng: **8.0–11.0M USDT** tại thời điểm L-26 trigger
  - Conservative (2.27× = ESPORTS): 3.764 × 2.27 = **8.54M** ← lower bound
  - Base (2.50×): 3.764 × 2.50 = **9.41M**
  - Aggressive (2.73× = IDOL): 3.764 × 2.73 = **10.27M** ← upper bound
- ΔOI/B_ref tại exit: kỳ vọng **250–450%** (so với BANK 516% và IDOL 173%)

**Deadline chấm P3:** Ngay sau L-26 trigger — đọc OI tại ngày trigger.
- **PASS:** OI tại L-26 ∈ [8M, 12M] USDT
- **FAIL:** OI tại L-26 < 7M (weak build) hoặc > 15M (extreme beyond calibration)

---

### P4 — Kết Cấu Thời Gian

**CRITICAL OBSERVATION:** D+13 không có L-26 = TUT đang outlier so với calibration.
- BANK exit: D+10 | IDOL exit: D+11 | ESPORTS: D+4 per wave
- TUT: D+13, ΔOI/B_T0 = +28% (vs BANK +516% at exit D+10)

**Lý giải:** TUT subtype CROWD-LONG là subtype chưa calibrated. Hypothesis:
- Crowd-long với pos_r cực cao (4.0–5.8) = khó trigger L-26 hơn (cần flush lớn hơn)
- MM build slow (ΔOI +28% in 13 days) = campaign dài hơn bình thường
- Có thể còn 15–30 ngày trước khi L-26 trigger

**Prediction P4 — Timeline:**
| Milestone | Ngày dự kiến | Điều kiện |
|-----------|-------------|----------|
| OI vượt 8M | 08/08→15/08 | vol duy trì ≥5M/ngày |
| OI vượt 10M | 15/08→25/08 | vol tăng dần |
| **L-26 trigger** | **12/08→25/08** | Catalyst price correction + crowd flush |
| RESOLVED | 12/08→01/09 | Sau L-26 + 2 ngày confirm |

**Deadline chấm P4:** 01/09/2026 (D+41)
- **PASS:** L-26 trigger xảy ra trong 12/08→01/09
- **FAIL:** Không có L-26 đến 01/09 (chiến dịch quá dài hoặc canceled)

---

### P5 — Kho Phân Loại + Exit Adjustment

**Status tại 04/08:** ABSTAIN (no data, see U5)

**Prediction P5 framework:**
Phụ thuộc vào operator cung cấp nguồn kho 83%:

| Kho Loại (L-42) | Hệ quả | Adjustment vào P1/P3 |
|----------------|--------|---------------------|
| **A (mượn team)** | Tất cả M2/deposit reads = đạo cụ; kho hồi đáy sau markup = signal đóng chiến dịch; endgame round-trip → dập giá | P1 ceiling thấp hơn (-15%): MM không cần giữ giá cao lâu vì kho không thuộc họ |
| **B (unlock)** | Neo theo lịch unlock; sell trong 48h sau unlock = tell exit | P1 timing = unlock calendar; nếu unlock Q3/Q4 → markup kéo dài đến trước unlock |
| **C (tự mua)** | Không có deadline; có thể "đi cùng thuyền" | P1 ceiling uncertain; có thể cao hơn calibration |

**P5 conditional prediction:**
- Nếu Loại A → Exit_px_max ≤ 0.028 (P1-mid, sell nhanh vì không có kho để giữ)
- Nếu Loại B + unlock trong 60 ngày → markup trong 30 ngày tới, exit ~3d trước unlock
- Nếu Loại C → không có deadline, upper bound không xác định

**P5 TREO** trên phân loại kho của operator.

**Deadline chấm P5:** Cùng với P4 (01/09/2026) HOẶC ngay sau khi operator cung cấp kho nguồn.
- **PASS/FAIL condition:** Phụ thuộc loại được xác nhận.

---

## Bảng Tổng Hợp Predictions (Bản chấm điểm)

| ID | Prediction | Điều kiện PASS | Điều kiện FAIL | Deadline |
|----|-----------|---------------|---------------|---------|
| P1 | Exit_px ∈ [0.025, 0.035] trước L-26 | px_max tại L-26 ∈ band | px_max < 0.020 hoặc > 0.040 | Ngay sau L-26 hoặc 01/09 |
| P2 | L-26 trigger trước 22/08/2026 | pos_r drop ≥30%/3d confirmed | Không có L-26 đến 22/08 | 22/08/2026 |
| P3 | OI_exit ∈ [8M, 12M] | OI tại L-26 trong range | OI < 7M hoặc > 15M | Ngay sau L-26 |
| P4 | L-26 trong 12/08→25/08 | Trigger trong window | Trigger ngoài window | 01/09/2026 |
| P5 | Loại kho A/B/C xác định | Operator confirm trước 25/08 | Không xác nhận được nguồn | 25/08/2026 |

---

## Observations Thêm (04/08 Live)

**08-04 LIVE:** px=0.02357 (+15.7%), vol=24.3M — ngày vol lớn nhất post-T0.

- P1-low (0.01928) đã bị vượt qua → markup đang ACTIVE
- gLSR 08-03 = 1.685 (giảm từ 2.031 ngày 08-01): crowd đang xả long khi giá tăng (L-11 = wash-by-rally) → BULLISH fuel signal
- OI 08-02 = 4.997M (high), 08-03 = 4.831M (retreat) → cần 08-04 OI confirm để đánh giá
- Nếu 08-04 OI > 6M và gLSR tiếp tục giảm → campaign đang accelerate vào P3 2× band

**Cần theo dõi ngay (05/08 sau cron 01:20 UTC):**
1. OI 04/08 canonical (từ freshwatch 05/08)
2. gLSR 04/08 — nếu giảm tiếp về 1.4–1.5 = wash-by-rally tiếp diễn
3. pos_r 04/08 — nếu sập về 3.0 hoặc thấp hơn = dấu hiệu sớm crowd flush

---

*Tài liệu prediction này đông băng tại 04/08/2026 18:xx UTC. KHÔNG sửa sau commit.*
*Chấm điểm tại: deadline P2 (22/08), deadline P4/P5 (01/09).*

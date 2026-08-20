# HEMI CASE BUILD + GOM-MISS AUTOPSY — 20/08/2026
**Target:** `docs/case_files/CASE_HEMI.xlsx` (v2.1 schema, 52 cols, 7 sheets)  
**Window:** 2026-07-01 → 2026-08-19 (nến đóng L-21 D-1) — 50 ngày  
**Probes:** `_probe_hemi_h0_h1_20260820.py` + `_probe_hemi_h2_h4_20260820.py` + `_task_hemi_create_case_20260820.py`

**Data provenance (L-48):**
- `data-source`: fapi.binance.com (perp/funding/OI/LSR), `data/export/freshwatch_daily_*.csv` (LSR history, 49 rows Jun27-Aug17), bapi/defi/v1 (Alpha DELISTED), api.gateio.ws, api.mexc.com
- `machine`: local Windows scratch + VPS (watchlist_log check)
- `date-range`: 2026-07-01 → 2026-08-19 (perp 50d) · Aug17 fapi LSR fallback cho freshwatch gap Aug18-19

**LAYER COVERAGE:** I (Perp fapi) · II (Crowd-LSR freshwatch+fapi) · IV (Funding fapi) · V (Gate + MEXC spot; Alpha DELISTED) · **spot-ext: gate + mexc** (KHÔNG N/A, KHÔNG CHƯA-TRA) · III/VI/VII: **[OWNERSHIP-UNVERIFIED]** chờ operator §H6

---

## H0 — IDENTITY (Step-0 discipline)

### H0.① PERP fapi

| Field | Value |
|-------|-------|
| symbol | **HEMIUSDT** |
| status | TRADING |
| onboardDate | 1756441800000 = **2025-08-29** (12 tháng history) |
| baseAsset / quoteAsset | HEMI / USDT |
| tickSize | 0.0000010 |

### H0.② CONTRACT — **UNVERIFIED** (chờ operator §H6)

Alpha map + venue price-band phải dùng contract, KHÔNG dùng symbol-string (bài F1 GUA/SUPERFORTUNE).

### H0.③ Alpha bapi (symbol-string match, ⚠ UNVERIFIED F1 + DELISTED)

| Field | Value |
|-------|-------|
| alphaId | **ALPHA_343** |
| name | Hemi |
| **fullyDelisted** | **True** ⚠ |
| **offline** | **True** ⚠ |
| chain | BSC |
| contract (bapi) | `0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b` |

**→ Alpha DELISTED → không có vol_alpha usable · taker_alpha = N/A-DELISTED (tag mới, khác ABSTAIN-STRUCTURAL của STBL/TRIA)**

### H0.④ VENUE SWEEP L-52

| Venue | Instrument | Status | Deposit/Withdraw |
|-------|-----------|--------|------------------|
| **Binance spot api/v3** | **HEMIBNB** (base=HEMI, quote=BNB) | **BREAK** ⚠ | — (KHÔNG USDT pair, không dùng) |
| Bybit v5 | — | **NOT FOUND** | — |
| OKX v5 | — | **NOT FOUND** | — |
| **Gate v4** | **HEMI_USDT** | **tradable** | BSC: dep=0, wd=0 → **VAN THÔNG ✓** |
| KuCoin v1 | — | **NOT FOUND** | — |
| **MEXC v3** | **HEMIUSDT** | **status=1 (Trading)** | (flags chưa fetch public) |
| Bitget v2 | — | **NOT FOUND** | — |

**→ spot-ext = gate + mexc** (van thông confirmed cho gate BSC · mexc chờ flags).  
**Price-band check vs perp (bài SUPERFORTUNE):** Gate 0.02-0.04% dev · MEXC 0.00-0.04% dev → ✓ PASS (không wash-band).

---

## H1 — PERP FULL 01/07→19/08 (50 days)

**Constraints verified:**
- Funding: fn=6 @ 4h × 50 days ✓ L-41
- OI: dedup unique 30/30 (30d limit, covers Jul21-Aug19)
- Taker scale: percent [43.25-52.50] ✓
- LSR: freshwatch 49 rows Jun27-Aug17 (HEMI in fw-139) + fapi fallback for Aug18-19

**⚠ Watchlist_log:** **HEMI KHÔNG có row nào trong `watchlist_log_2026-08.csv`** — machine MISS hoàn toàn (khớp GOM-MISS autopsy §H2).

Full 30d table (last 30 days Jul21→Aug19):

| date | c | ret% | vol | oi | f_avg | fn | pos_r | acc_r | gLSR | div | tk% | src |
|------|-----|------|-----|----|-------|-----|-------|-------|------|-----|-----|-----|
| 07-21 | 0.00537 | -21.61 | 84.5M | — | 5e-05 | 6 | 1.268 | 1.905 | 1.844 | 0.665 | 47.16 | fw |
| 07-22 | 0.00505 | -5.94 | 14.5M | 4,730,379 | 5e-05 | 6 | 1.687 | 1.644 | 1.331 | 1.026 | 48.21 | fw |
| 07-23 | 0.00473 | -6.36 | 10.1M | 4,450,809 | 4.4e-05 | 6 | 1.828 | 1.584 | 1.186 | 1.154 | 45.55 | fw |
| 07-27 | 0.00456 | -7.27 | 5.7M | 4,056,545 | 4.1e-05 | 6 | 2.067 | 2.157 | 1.544 | 0.958 | 44.21 | fw |
| 07-31 | 0.00469 | +6.76 | 4.8M | 3,316,268 | 5e-05 | 6 | 2.302 | 1.968 | 1.350 | 1.170 | 52.04 | fw |
| 08-05 | 0.00496 | +6.03 | 3.8M | 3,202,160 | 5e-05 | 6 | 2.847 | 2.580 | 1.904 | 1.103 | 50.45 | fw |
| 08-10 | 0.00526 | -5.34 | 3.6M | 3,675,997 | 5e-05 | 6 | 3.056 | 3.801 | 3.058 | 0.804 | 44.24 | fw |
| 08-13 | 0.00476 | +0.89 | 2.4M | 3,251,203 | 5e-05 | 6 | 3.620 | 3.869 | 2.788 | 0.936 | 49.12 | fw |
| 08-14 | 0.00487 | +2.46 | 2.4M | 3,279,954 | 5e-05 | 6 | 3.466 | 3.955 | 2.932 | 0.876 | 47.75 | fw |
| **08-15** | **0.00700** | **+43.62** | **171.8M** | 3,364,618 | 4.7e-05 | 6 | **3.836** | 3.744 | 2.769 | 1.025 | 49.29 | fw |
| **08-16** | **0.00626** | **-10.56** | **420.7M** | **9,665,377** | **2.1e-05** | 6 | **1.761** | **1.171** | **1.118** | **1.504** | 50.44 | fw |
| 08-17 | 0.00699 | +11.60 | 85.4M | 8,249,562 | 5e-05 | 6 | 1.644 | 1.361 | 1.252 | 1.208 | 49.18 | fw |
| 08-18 | 0.00712 | +1.85 | 48.4M | 9,194,621 | 5e-05 | 6 | 1.972 | 1.317 | 1.249 | 1.496 | 48.28 | fapi |
| **08-19** | **0.00873** | **+22.72** | **277.8M** | **9,785,223** | 5e-05 | 6 | 2.344 | 1.403 | 1.208 | **1.671** | 50.91 | fapi |

**Special:** **Jul20 pump D1** — +51.50% ret, vol **$103.7M**, **f_avg = -0.000136 (âm duy nhất window)** — pump ăn theo short-side.

---

## H2 — GOM-MISS AUTOPSY Jul01-Aug13 (44 days baseline pre-pump)

**Điều kiện check per-day (khoảng cách tới ngưỡng):**

| Gate | Điều kiện | Kết quả 44d |
|------|-----------|-------------|
| **GOM-A A1** | `div_avg3 ≥ 1.5` AND `gLSR ≤ 1.1` | **MISS ALL 44 DAYS** — nearest miss Jul23: div3=0.932 (thiếu 0.568) + gLSR=1.186 (vượt 0.086). Max div_avg3 window = 1.115 @ Aug01 |
| **GOM-B B1** | `div_avg3 ≤ 0.5` AND `struct_n ≥ 3` AND pin | **HIT Jul05-09 (5 ngày liên tục)** — nhưng KHÔNG có A1 follow-through |
| **GOM-C stealth_grind** | breakout + oi_mult ≥ 2× + taker ≥ 50 | Không có breakout meaningful đến Jul20 pump (đột nhiên +51.5%, không phải grind) |

**Nearest-miss top 5 (A1):**
```
07-23: div3=0.932 (thiếu 0.568) · gLSR=1.186 (vượt 0.086) — closest overall
07-31: div3=1.057 (thiếu 0.443) · gLSR=1.350 (vượt 0.250)
08-01: div3=1.115 (thiếu 0.385) · gLSR=1.456 (vượt 0.356) — max div3 window
08-04: div3=1.082 (thiếu 0.418) · gLSR=1.541 (vượt 0.441)
07-30: div3=1.011 (thiếu 0.489) · gLSR=1.410 (vượt 0.310)
```

**Phân loại miss:** **(b) NEAR-MISS-CONFIG** — cả 2 vế A1 fail SIMULTANEOUSLY:
- div_avg3 chưa bao giờ vượt 1.5 (max 1.115 = -26% thiếu)
- gLSR chưa bao giờ ≤ 1.1 (min 1.186 Jul23 = +8% vượt)

**KHÔNG PHẢI:**
- (a) data-gap: dữ liệu đầy đủ (freshwatch 49 rows + fapi 30d fallback)
- (c) verdict-fail: máy không có cơ hội trigger (dưới ngưỡng cả 2 vế)

**B1 HIT không follow-through:** HEMI có 5 ngày B1 hit (Jul05-09) — hedge deep tối đa, nhưng chưa unwind lên A1. Đây là điểm chờ dài: hedge structure ổn định B1 nhưng không đi qua transition A1 → texture khác với TRIA/STBL (cả 2 đang trong episode dài).

**⚠ HEMI KHÔNG có row nào trong watchlist_log Aug 2026 (VPS grep 0 rows).** Machine miss vì HEMI không đạt gate B của watchlist v1.3.

---

## H3 — CAMPAIGN 14-19/08 READOUT

### (a) Pump anatomy per-day

| Date | ret% | vol | vol ÷ nền T7 perp | OI | ΔOI | taker% |
|------|------|-----|-------------------|----|----|--------|
| 08-14 pre | +2.46 | 2.4M | 0.7× | $3.28M | +28K | 47.75 |
| **08-15 PUMP_D2** | **+43.62** | **171.8M** | **48×** | $3.36M | +85K (chưa build) | 49.29 |
| **08-16 FLUSH+BUILD** | **-10.56** | **420.7M** | **118× (biggest)** | **$9.67M** | **+$6.3M (+187%)** | 50.44 |
| 08-17 REBOUND | +11.60 | 85.4M | 24× | $8.25M | -$1.4M | 49.18 |
| 08-18 CHOP | +1.85 | 48.4M | 13× | $9.19M | +$0.9M | 48.28 |
| **08-19 PUMP_D3** | **+22.72** | **277.8M** | **78×** | **$9.79M** | +$0.6M | 50.91 |

### (b) HARVEST detail (đối chiếu PHASE-TAG Aug18 S3-HARVEST)

- **pos_r peak:** **3.836 @ Aug15**
- **pos_r đáy sau HARVEST:** **1.644 @ Aug17**
- **pos-break %:** **-57.14%** (3.836 → 1.644) — **VƯỢT ngưỡng 25-30% XA**, đây là HARVEST clean
- **Ngày sập:** **Aug16** (crashed từ Aug15 pump khi price -10.56%)
- **acc_r peak → đáy:** 3.744 (Aug15) → **1.171 (Aug16) = -69%** short-cover CRUSHED

**PHASE-TAG chấm S3-HARVEST Aug18** = đúng (pos_r đã rơi từ 3.83 xuống 1.97 = -49%, giá vẫn giữ).

### (c) TEST-BAIT Aug18

- Vol Aug18 = $48.4M = **~13× nền T7 perp** (still spike)
- Ret1d = +1.85% (chop)
- OI +0.9M (không build mạnh)
- **TEST result HELD/REJECTED chấm 21/08** (3d cửa sổ post-test): Aug19 +22.72% pump = **HELD** (test không bị rejected) — theo dõi tiếp Aug20-21

### (d) gLSR/acc chuỗi + SQUEEZE-FUEL

```
Aug10-14 (pre-pump build): gLSR 3.06 → 2.93 (crowd bull dày), acc_r 3.80 → 3.95 (short-heavy tank)
Aug15 (PUMP D2):         gLSR 2.77, acc_r 3.74 (còn short đầy)
Aug16 (CRASH+BUILD):     gLSR 1.118, acc_r 1.171 (**crowd flip mạnh, short cover TRIỆT ĐỂ**)
Aug17-19 (rebuild):      gLSR 1.25 → 1.21, acc_r 1.36 → 1.40 (bull dâng chậm, short KHÔNG tái vào)
```

**SQUEEZE-FUEL kết luận:**
- **Short = CỦI** (Aug16 short-cover TRIỆT ĐỂ, acc_r sập từ 3.74 → 1.17 = -69%)
- **Long = ĐANG BUILD LẠI** (Aug17-19 pos_r 1.64 → 2.34 leo chậm)
- Củi short đã đốt gần hết trong Aug16 flush → **Aug19 pump ăn theo LONG BUILD MỚI**, không phải squeeze mới.

### (e) Funding regime

- **Baseline Jul01-Aug14:** PIN 100% (f_avg=+0.00005 mỗi ngày, band [4e-5, 6e-5])
- **Jul20 pump D1:** **f_avg=-0.000136 NEGATIVE** (âm duy nhất window) — pump short-side ignite (khác D2/D3)
- **Aug15 pump D2:** f_avg=+0.000047 (near-pin)
- **Aug16 flush:** f_avg=+0.000021 (thấp bất thường ~2× thấp hơn pin)
- **Aug19 pump D3:** f_avg=+0.00005 (quay lại pin)

**KHÔNG có neg_div ngày nào bẩn (đủ điều kiện f≤-2e-4 + range3d≤7%)** trong window.

---

## H4 — CHÂN HÀNG multi-venue + doctrine #10

### Nền T7 (Jul01-Aug13, pre-pump baseline, median)

| Venue | Median T7 | Range T7 | Identity-check |
|-------|-----------|----------|----------------|
| Perp | $3,578,625 | $1M..$103.8M | (native) |
| **Gate** | **$49,158** | $12K..$497K | bit-eq=False (3/3) ✓ PASS |
| **MEXC** | **$91,146** | $59K..$1.45M | bit-eq=False (3/3) ✓ PASS |
| Alpha | — | — | **DELISTED, không dùng** |
| **Tổng spot** | **$140,304/day** | — | |

**Price-band vs perp (3 samples Jul15/Aug01/Aug15):** Gate deviation 0.02-0.04% · MEXC 0.00-0.04% → ✓ PASS (không wash-band suspicious).

### Doctrine #10 — kho 590M ≈ $5.1M ÷ băng thông

**Kho hiện tại (operator feed 20/08):** **590M HEMI** ≈ **$5.15M** @ price $0.00873 (Aug19 close)

**Deposit event 14-19/08:** **+100M tokens (490M → 590M = +22.6%) TRONG giá +90% (0.00487 → 0.00873)** — khuôn APR deposit-in-pump.

**Kịch bản băng thông:**
- **10% MM spot-only tổng T7:** $5.15M ÷ (10% × $140K/day) = **~368 days** (~1 năm)
- **30% MM spot-only tổng T7:** $5.15M ÷ (30% × $140K/day) = **~123 days** (~4 tháng)
- **Peak day Aug16:** perp vol $420M · spot Aug16 chưa fetch riêng nhưng vol tổng chắc chắn ≥ nền × 100 (Aug16 perp × 118 nền) → nếu MM tận dụng peak days: có thể xả nhanh 1-2 tuần

**Nhưng chú ý:** perp không phải chân xả token thật (derivative). Chỉ spot Gate + MEXC + (nếu operator xác nhận) các van khác đếm được. Nếu chỉ tính spot: kho ~368d 10% MM → **HEMI KHÔNG THỂ XẢ SPOT HẾT trong short-term nếu không có peak days đột biến**.

---

## H5 — EVENTS (đã append vào CASE_HEMI EVENTS sheet)

10 rows:

| Date | Type | Description |
|------|------|-------------|
| 2025-08-29 | LISTING_PERP | HEMIUSDT onboard fapi |
| 2026-07-05 | GOM_B1_HIT_5D | Jul05-09 B1 hit (5 ngày) nhưng không có A1 follow-through |
| **2026-07-20** | **PUMP_D1_NEG_FUND** | +51.50%, vol $103.7M, **f_avg=-0.000136** — short-side ignite |
| 2026-07-21 | CRASH_D1 | -21.61%, pos_r 2.11→1.27, gLSR 3.35→1.84 flip |
| **2026-08-15** | **PUMP_D2** | +43.62%, vol $171.8M (~48× nền), pos_r 3.836 peak |
| **2026-08-16** | **FLUSH_WITH_OI_BUILD** | -10.56% + vol $420.7M + OI +187% — short-cover CRUSHED + long BUILD |
| 2026-08-17 | REBOUND | +11.60%, OI $8.25M |
| **2026-08-18** | **S3-HARVEST + TEST_BAIT** | PHASE-TAG chấm; TEST HELD/REJECTED chấm 21/08 (Aug19 +22.7% = HELD) |
| **2026-08-19** | **PUMP_D3** | +22.72%, vol $277.8M (~78× nền), OI $9.79M peak, div_raw 1.671 |
| **2026-08-19** | **DEPOSIT_IN_PUMP** | +100M tokens (490→590M = +22.6%) TRONG giá +90% (operator tracker) unresolved |

---

## H6 — CẦN OPERATOR (mọi nhãn treo `[OWNERSHIP-UNVERIFIED]`)

1. **Contract 0x + chain** — Alpha bapi trả `0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b` on BSC nhưng **ALPHA_343 DELISTED** — cần operator confirm contract khớp identity thật (bài F1 GUA).
2. **Kho lên sàn nào?** — trace ví đích của 100M token deposit 14-19/08. Binance hot wallet hay Gate/MEXC? BscScan trace cần mắt operator.
3. **Ví nguồn deposit chạm cụm GUA/TRIA/AIN?** — cluster analysis on BscScan (máy mù, mắt operator).
4. **Unlock schedule + supply** — BscScan totalSupply, vesting contract nếu có.
5. **MC tracker source** (CoinGecko/CMC/Bubblemap?) — để verify FDV vs 590M kho.

---

## §I. TỔNG KẾT + FILE LIST

**Số chốt:**
- Perp fapi 12 tháng history · Alpha DELISTED · 2 spot venues thông (Gate BSC + MEXC)
- **3 pumps trong 30d:** Jul20 (+51%, neg fund), Aug15 (+43%), Aug19 (+22%) — 3 wave crescendo
- **Aug16 = flush + OI +187% + short-cover -69%** = fuel-check đã đốt phần lớn short củi
- pos-break Aug15→17 = **-57%** (HARVEST clean, đối chiếu PHASE-TAG S3-HARVEST Aug18)
- GOM-MISS: máy MISS hoàn toàn (0 rows watchlist Aug) — cả A1 (div3 max 1.115 < 1.5) và B1 (chỉ hit Jul05-09 pre-pump)
- Nền T7 spot tổng = $140K/day → doctrine #10: kho $5.15M ÷ 10% MM = ~368d
- Deposit-in-pump +100M tokens (khuôn APR) — operator tracker feed unresolved

**Files:**
| Artifact | Path |
|----------|------|
| CASE file | `docs/case_files/CASE_HEMI.xlsx` (v2.1, 52 cols, 50 DAILY rows, 75 CASE meta, 10 EVENTS) |
| CASE_INDEX row | Row 28 · HEMI · TRACKING (cold-start Aug20, active campaign, contract UNVERIFIED) |
| Probe H0/H1 | `_probe_hemi_h0_h1_20260820.py` |
| Probe H2/H4 | `_probe_hemi_h2_h4_20260820.py` |
| Create task | `_task_hemi_create_case_20260820.py` |
| Scratch data | `scratch/hemi_{perp,funding,oi,lsr_freshwatch,lsr_fapi,gate,mexc}_20260820.csv` |
| Report | file này |

**KHÔNG VERDICT.** Số về, ANALYSIS đọc. Chờ operator §H6 relay để lift `[OWNERSHIP-UNVERIFIED]` treo.

**DỪNG sau paste.**

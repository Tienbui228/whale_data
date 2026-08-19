# STBL PROBE — TOKEN NGOÀI 17 CASE · 19/08/2026
**Target:** STBLUSDT (perp fapi) + STBL spot (multi-venue)  
**Window:** 2026-06-19 → 2026-08-18 (60d cắt, D-1 nến đóng L-21)  
**Probes:** `_probe_stbl_20260819.py` + `_probe_stbl_venues_supp_20260819.py` (read-only, chưa tạo CASE file)  
**Output:** Report này — CASE file sau khi ANALYSIS đọc.

**Data provenance (L-48):**
- `data-source`: fapi.binance.com (perp/funding/OI/LSR), bapi/defi/v1 (Alpha ALPHA_376 — **UNVERIFIED symbol-match**), api.gateio.ws, api.kucoin.com, api.mexc.com
- `machine`: local Windows
- `date-range`: 2026-06-19 → 2026-08-18 (perp 60d) · 2026-07-19 → 2026-08-18 (venue klines 30d)

**LAYER COVERAGE:** I (Perp fapi) · II (Crowd-LSR freshwatch + fapi fallback) · IV (Funding fapi) · V (Alpha bapi + Gate + KuCoin + MEXC spot) · **spot-ext: gate + kucoin + mexc** (KHÔNG N/A, KHÔNG CHƯA-TRA) · III/VI/VII: **[OWNERSHIP-UNVERIFIED]** chờ operator (§S4)

---

## S0 — IDENTITY (L-51 Step-0 discipline)

### S0.① PERP fapi

| Field | Value |
|-------|-------|
| symbol | **STBLUSDT** |
| status | TRADING |
| onboardDate | 1758087900000 = **2025-09-17** (11 tháng history) |
| baseAsset / quoteAsset | STBL / USDT |
| tickSize | 0.0000100 |

Window start = max(onboard, END-60d) = **2026-06-19**.

### S0.② CONTRACT (operator feed required)

**Contract 0x + chain:** **UNVERIFIED — operator chưa relay.**

→ Mọi mapping alpha/venue mang nhãn UNVERIFIED (symbol-string match KHÔNG dùng — bài F1 GUA).  
→ **CẦN OPERATOR (§S4):** paste `0x...` + chain (BSC/ETH/SOL/…) để confirm alpha map + verify token identity trên venues.

### S0.③ Alpha bapi (symbol-string lookup — UNVERIFIED)

| Field | Value (⚠ UNVERIFIED cho tới khi contract khớp) |
|-------|-------------------------------------------------|
| alphaId | **ALPHA_376** |
| name | STBL |
| chain | **BSC** |
| contract (from bapi) | `0x8dedf84656fa932157e27c060d8613824e7979e3` |
| fullyDelisted | False |
| offline | False |

**Cảnh báo bài F1 (GUA 19/08):** Alpha bapi trả về contract theo symbol-string match. Nếu operator paste contract khác `0x8ded...` → alpha map SAI, mọi vol_alpha bị nhiễm — cần rerun.

### S0.④ VENUE SWEEP L-52 (Binance-spot + Bybit + OKX + Gate + KuCoin + MEXC + Bitget)

| Venue | Instrument | Status | Deposit/Withdraw |
|-------|-----------|--------|------------------|
| **Binance spot api/v3** | STBLUSDT | **NOT_FOUND** | — |
| **Bybit v5 spot** | STBLUSDT | **NOT FOUND** | — |
| **OKX v5 spot** | STBL-USDT | **NOT FOUND** | — |
| **Gate v4 spot** | STBL_USDT | **tradable** | BSC (BEP20): withdraw_disabled=**0** · deposit_disabled=**0** → **VAN THÔNG** ✓ |
| **KuCoin v1 spot** | STBL-USDT | **enabled** | (chưa fetch capital config public) |
| **MEXC v3 spot** | STBLUSDT | **status=1 (Trading)** | (chưa fetch capital config public) |
| **Bitget v2 spot** | STBLUSDT | **NOT FOUND** | — |
| **Alpha bapi** | ALPHA_376USDT | Trading (bapi klines OK, ⚠ UNVERIFIED symbol match) | — |

**Kết luận venue coverage:**
- **Chân THÔNG confirmed:** Gate BSC (deposit+withdraw open) ✓
- **Chân TRADABLE nhưng deposit flag chưa check:** KuCoin, MEXC, Alpha bapi
- **Không có Binance spot** (như GUA án 17-18/08)
- Tổng **4 spot venues** cho STBL — chân hàng đa venue

**spot-ext = gate + kucoin + mexc + alpha** (đa venue, cần chọn theo doctrine "1 case 1 venue-ext ưu tiên" nếu áp v2.1 amendment — theo thứ tự Bybit > OKX > **Gate** > KuCoin > MEXC → **spot_ext_venue = gate** primary, các venue khác note metadata).

---

## S1 — PERP FULL (Jun19 → Aug18, 61 ngày)

**Fetched:**
- klines 1d: 61 rows
- funding: 61 days, 366 entries, **all fn=6 @ 4h intervals** (L-41 verified) ✓
- OI: 30 days (dedup unique)
- LSR: 
  - **freshwatch_store**: 49 days Jun27-Aug17 (STBL is in fw-139 universe)
  - **fapi fallback** (30d 4 endpoint): topPos + topAcc + globalRatio for Aug18 (freshwatch chưa có)

**Taker scale-check:** percent [42.01–50.79] scale ✓ (không cần ×100)

Full 30d per-day table below (§S3).

---

## S2 — CHÂN HÀNG (venue vol backfill 30d)

**Identity-check L-51 4-step (3 samples/venue):**

| Venue | Fields checked | bit-equal? | Verdict |
|-------|----------------|------------|---------|
| Gate | vol_quote_usd vs base_vol | **False** (all 3) | PASS (real 2-field) |
| KuCoin | turnover_usd vs base_vol | **False** (all 3) | PASS |
| MEXC | quote_vol_usd vs base_vol | **False** (all 3) | PASS |
| **Alpha ALPHA_376** | k[9]≡k[5], k[10]≡k[7] | **True 31/31** | **MIRROR** — L-48 pattern confirmed → **taker_alpha = ABSTAIN-STRUCTURAL** |

**Nền T7 spot per venue (Jul20-Aug01, 13 days median):**

| Venue | Median T7 | Range T7 |
|-------|-----------|----------|
| **Perp** | $1,134,194 | $848,073..$2,584,877 |
| Gate | $94,739 | $60,428..$162,883 |
| MEXC | $70,817 | $59,392..$94,075 |
| KuCoin | $19,013 | $9,181..$47,981 |
| Alpha | $5,976 | $2,417..$17,707 |
| **Tổng spot** | **$190,545** | — |
| **Tổng (perp + spot)** | **$1,324,739** | — |

**Ghi vào các cột đúng nhà (theo L-51 amendment v2.1):**
- vol_spot_usd (col 31) = **`N/A-STRUCTURAL`** (không có Binance spot api/v3)
- vol_alpha (col 35) = số alpha_bapi USD per-day (nhưng MIRROR flag → taker = ABSTAIN)
- taker_alpha (col 36) = **`ABSTAIN-STRUCTURAL`** (L-48)
- vol_spot_ext_usd (col 51) = **Gate turnover** per-day (venue ưu tiên nhất trong 4)
- spot_ext_venue (col 52) = **`gate`** (metadata note: cũng có kucoin/mexc/alpha)

---

## S3 — BẢNG PER-DAY 30d + 4 answers

Full 30 rows Jul20-Aug18 (perp + LSR + funding + OI):

| date | c | ret% | vol_perp | oi_usd | f_avg | fn | pin | pos_r | acc_r | gLSR | div | div3 | tk% | src_lsr |
|------|-----|------|----------|--------|-------|-----|-----|-------|-------|------|-----|------|-----|---------|
| 07-20 | 0.02171 | — | 926,240 | — | 5e-05 | 6 | T | 0.804 | 2.932 | 3.617 | 0.274 | — | 50.51 | fw |
| 07-21 | 0.02211 | +1.84 | 1,221,682 | 1,271,717 | 5e-05 | 6 | T | 0.770 | 3.022 | 3.859 | 0.255 | — | 49.71 | fw |
| 07-22 | 0.02471 | +11.76 | 2,557,734 | 1,339,158 | 5e-05 | 6 | T | 0.792 | 2.956 | 3.647 | 0.268 | 0.266 | 48.75 | fw |
| 07-23 | 0.02367 | -4.21 | 2,584,877 | 1,679,906 | 5e-05 | 6 | T | 0.854 | 2.391 | 2.854 | 0.357 | 0.289 | 46.70 | fw |
| 07-24 | 0.02367 | 0.00 | 901,530 | 1,547,264 | 5e-05 | 6 | T | 0.850 | 2.482 | 2.965 | 0.342 | 0.319 | 45.89 | fapi |
| 07-25 | 0.02437 | +2.96 | 1,108,984 | 1,467,911 | 5e-05 | 6 | T | 0.823 | 2.654 | 3.087 | 0.310 | 0.336 | 49.21 | fapi |
| 07-26 | 0.02482 | +1.85 | 1,134,194 | 1,570,150 | 5e-05 | 6 | T | 0.830 | 2.733 | 3.131 | 0.304 | 0.318 | 48.65 | fapi |
| 07-27 | 0.02228 | -10.23 | 1,218,969 | 1,623,725 | 5e-05 | 6 | T | 0.833 | 2.610 | 3.052 | 0.319 | 0.311 | 44.95 | fw |
| 07-28 | 0.02234 | +0.27 | 848,073 | 1,338,768 | 5e-05 | 6 | T | 0.752 | 2.962 | 3.454 | 0.254 | 0.291 | 50.79 | fw |
| 07-29 | 0.02203 | -1.39 | 1,420,174 | 1,329,954 | 5e-05 | 6 | T | 0.752 | 2.990 | 3.568 | 0.251 | 0.273 | 49.64 | fw |
| 07-30 | 0.02226 | +1.04 | 886,837 | 1,353,776 | 5e-05 | 6 | T | 0.780 | 3.032 | 3.509 | 0.257 | 0.254 | 49.01 | fw |
| 07-31 | 0.02290 | +2.88 | 994,872 | 1,426,580 | 5e-05 | 6 | T | 0.805 | 3.054 | 3.660 | 0.264 | 0.258 | 50.64 | fw |
| 08-01 | 0.02357 | +2.93 | 1,440,281 | 1,481,067 | 5e-05 | 6 | T | 0.803 | 3.211 | 3.808 | 0.250 | 0.257 | 48.83 | fw |
| 08-02 | 0.02477 | +5.09 | 2,368,413 | 1,549,422 | 5e-05 | 6 | T | 0.822 | 2.915 | 3.560 | 0.282 | 0.265 | 49.52 | fw |
| 08-03 | 0.02411 | -2.66 | 1,607,288 | 1,673,178 | 5e-05 | 6 | T | 0.821 | 2.786 | 3.462 | 0.295 | 0.274 | 45.92 | fw |
| 08-04 | 0.02390 | -0.87 | 1,239,950 | 1,612,922 | 5e-05 | 6 | T | 0.817 | 2.621 | 3.323 | 0.312 | 0.296 | 48.79 | fw |
| 08-05 | 0.02429 | +1.63 | 839,394 | 1,522,935 | 5e-05 | 6 | T | 0.814 | 2.757 | 3.392 | 0.295 | 0.300 | 48.29 | fw |
| 08-06 | 0.02468 | +1.61 | 1,376,266 | 1,582,342 | 5e-05 | 6 | T | 0.809 | 2.761 | 3.380 | 0.293 | 0.300 | 49.79 | fw |
| 08-07 | 0.02482 | +0.57 | 1,207,928 | 1,623,282 | 5e-05 | 6 | T | 0.832 | 3.143 | 3.909 | 0.265 | 0.283 | 42.01 | fw |
| 08-08 | 0.02489 | +0.28 | 472,783 | 1,625,101 | 5e-05 | 6 | T | 0.826 | 3.290 | 3.960 | 0.251 | 0.268 | 47.75 | fw |
| 08-09 | 0.02497 | +0.32 | 1,930,286 | 1,632,772 | 5e-05 | 6 | T | 0.821 | 3.337 | 4.131 | 0.246 | 0.254 | 48.15 | fw |
| 08-10 | 0.02332 | -6.61 | 1,197,288 | 1,802,292 | 5e-05 | 6 | T | 0.866 | 3.686 | 4.348 | 0.235 | 0.244 | 45.59 | fw |
| 08-11 | 0.02332 | 0.00 | 1,896,321 | 1,559,501 | 5e-05 | 6 | T | 0.881 | 3.836 | 4.568 | 0.230 | 0.236 | 49.73 | fw |
| 08-12 | 0.02275 | -2.44 | 590,371 | 1,565,754 | 5e-05 | 6 | T | 0.913 | 3.638 | 4.244 | 0.251 | 0.238 | 44.96 | fw |
| 08-13 | 0.02267 | -0.35 | 653,292 | 1,504,959 | 5e-05 | 6 | T | 0.897 | 3.764 | 4.311 | 0.238 | 0.239 | 47.18 | fw |
| 08-14 | 0.02336 | +3.04 | 1,223,219 | 1,480,822 | 5e-05 | 6 | T | 0.917 | 3.815 | 4.379 | 0.240 | 0.243 | 48.39 | fw |
| 08-15 | 0.02418 | +3.51 | 1,203,187 | 1,519,505 | 5e-05 | 6 | T | 0.931 | 3.673 | 4.168 | 0.254 | 0.244 | 47.32 | fw |
| **08-16** | **0.02675** | **+10.63** | 2,633,541 | 1,598,811 | 5e-05 | 6 | T | 0.933 | 3.888 | 4.280 | 0.240 | 0.245 | 49.91 | fw |
| **08-17** | **0.02702** | +1.01 | **6,886,746** | 1,960,647 | 5e-05 | 6 | T | 0.978 | 2.997 | 3.346 | **0.326** | 0.269 | 47.81 | fw |
| **08-18** | 0.02603 | -3.66 | 1,467,100 | **2,062,661** | 5e-05 | 6 | T | 0.973 | 2.535 | 2.630 | **0.384** | 0.306 | 43.76 | fapi |

**Multi-venue vol Aug10-Aug18 (chân hàng đầy đủ):**

| date | perp | gate | kucoin | mexc | alpha | spot-tổng |
|------|------|------|--------|------|-------|-----------|
| 08-10 | 1,197,288 | 368,190 | 11,256 | 91,779 | 21,842 | 493,067 |
| 08-11 | 1,896,321 | 145,277 | 26,144 | 72,414 | 15,362 | 259,197 |
| 08-12 | 590,371 | 34,651 | 18,806 | 57,118 | 2,062 | 112,637 |
| 08-13 | 653,292 | 49,329 | 18,305 | 57,839 | 2,693 | 128,166 |
| 08-14 | 1,223,219 | 65,745 | 29,941 | 99,575 | 4,391 | 199,652 |
| 08-15 | 1,203,187 | 79,380 | 17,368 | 74,938 | 3,724 | 175,410 |
| **08-16** | **2,633,541** | **150,568** | 26,084 | 81,082 | **34,509** | **292,243** |
| **08-17** | **6,886,746** | **302,962** | **75,650** | **93,927** | **81,173** | **553,712** |
| 08-18 | 1,467,100 | 93,301 | 18,544 | 64,894 | 18,252 | 194,991 |

---

### (a) Phase-tag texture (14 ngày cuối, chạy tay v0.3.3)

| Date | Stage | Evidence |
|------|-------|----------|
| 08-05→08-09 | **S2-EARLY** | Hedged-waiting: div_avg3 ~0.25-0.30, pin funding, pos_r ~0.82, OI phẳng 1.5-1.6M, low vol |
| 08-10 | **S2-EARLY (flush)** | Flush -6.61% + gLSR leo 4.13→4.35, OI leo 1.63→1.80M (short bổ sung + long hedged giữ) |
| 08-11 | **S2-MID** | OI rơi 1.80→1.56M sau flush (short + long bớt), gLSR peak 4.57 |
| 08-12→08-13 | **S2-MID** | Consolidate quanh 0.0227, div_avg3 ~0.24, gLSR 4.24-4.31 |
| 08-14→08-15 | **S2-MID → S2-LATE** | Price leo +6.7% 2d (0.0233→0.0242), pos_r cross 0.9 (0.917→0.931), OI phẳng |
| **08-16** | **S3-BIDWALK (ứng viên)** | +10.63% ret1d + vol × 2 nền, alpha vol ×5 (34K vs nền 6K), Gate vol ×1.6, MEXC ×1.1 = spot ignite cùng ngày |
| **08-17** | **S3-BIDWALK peak / S3-HARVEST đầu** | Perp vol × 6 (6.9M vs 1.13M nền), Alpha × 13.6, Gate × 3.2 — spike cùng lúc perp; OI leo 1.60→1.96M (+22%); pos_r 0.978 cross-1 imminent; **acc_r giảm 3.89→3.00 (-23%)** — top-trader hedge unwind |
| **08-18** | **S4-TRANSITION ứng viên** | Price -3.66%, OI vẫn peak $2.06M (cycle_pos=1.0), div_raw NHẢY 0.326→0.384 (top acc_r rơi tiếp 3.00→2.54 = -15%) — un-hedge sơ khai; nếu Aug19-21 OI rơi + div tiếp leo → S4 confirmed. Nếu OI giữ → có thể re-hedge, quay lại S2-MID |

**Texture đọc:** STBL đang ở **S3-BIDWALK peak vs S4-TRANSITION** — cần theo dõi Aug19-21 để chốt pha.

### (b) OI cycle 30d

- **OI 30d min:** $1,271,717 (2026-07-21)
- **OI 30d max:** $2,062,661 (2026-08-18)
- **OI hiện tại (Aug18):** $2,062,661
- **oi_cycle_pos = (2,062,661 − 1,271,717) / (2,062,661 − 1,271,717) = 1.0000** — **AT PEAK OF BUILD CYCLE**

Đọc: OI leo +62% từ đáy 30d, hiện đang ở top. Không có headroom build thêm mà không phá kỷ lục 30d — cực nhạy cảm với cover đầu (Aug19-21).

### (c) Funding regime

**PINNED 30/30 ngày** — f_avg = **+0.00005** mỗi ngày, chính xác 5e-5 pin band edge.
- Không có ngày f_avg âm
- Không có ngày f_avg > 6e-5 (không warm)
- Không có neg_div (không đủ điều kiện f ≤ -2e-4 + range3d ≤ 7%)
- **pin_streak = 30 (max cho window)**

Cùng khuôn với TRIA (30 ngày pin liên tục) — captive committed cực chặt.

### (d) Event tags 30d

| Date | Tag | Detail |
|------|-----|--------|
| 07-22 | VOL_SPIKE + PUMP | +11.76%, vol 2.56M (2× nền) |
| 07-27 | FLUSH_D1 | -10.23% single day |
| 08-02 | RALLY_D1 | +5.09%, vol 2.37M |
| 08-10 | FLUSH_D1 | -6.61% flush |
| **08-16** | **PUMP_D1 + SPOT_IGNITE** | +10.63% ret1d, Alpha × 5 nền, Gate × 1.6, MEXC × 1.1 |
| **08-17** | **VOL_5X_SPIKE + OI_BUILD** | Perp vol × 6 ($6.9M), Alpha × 13.6, Gate × 3.2 — spot chuỗi cùng nổ; OI +22% (1.60→1.96M) |
| **08-18** | **ACC_R_UNWIND / UN-HEDGE-EARLY** | acc_r rơi 3.00→2.54 (-15%), div_raw 0.326→0.384 (peak trong window) — top-trader giảm hedge trong khi OI vẫn giữ peak |

**KHÔNG có tag:** WASH (không phát hiện depth mismatch qua venue tại instrument-info), WRONG-SIDE (không có short-cover pattern rõ), BAIT (không có burst ≥15bps).

### (e) Băng thông xả tổng — doctrine #10 mẫu số

**Nền T7 (Jul20-Aug01, median):**
- Chân THÔNG confirmed: **Gate $94,739/day** (BSC deposit+withdraw OPEN ✓)
- Chân chưa xác định flag (nhưng klines tradable): KuCoin $19K + MEXC $71K + Alpha $6K = **$96K/day**
- **Tổng spot venues (Gate + KuCoin + MEXC + Alpha) T7 median = $190,545/day**
- Perp T7 median = $1,134,194/day (không phải chân xả token thật — derivative)

**Doctrine #10 chờ mẫu số (kho on-chain):**
- Chưa có số kho STBL (§S4 CẦN OPERATOR)
- Nếu operator paste kho $X:
  - Kịch bản 10% MM: $X ÷ $19,054 = ~$X/$19K days
  - Kịch bản 30% MM: $X ÷ $57,163 = ~$X/$57K days

**Băng thông peak day (Aug17):** spot tổng $553,712 = ×2.9 nền T7 — cửa xả rộng khi crowd tham gia.

---

## S4 — CẦN OPERATOR (on-chain data thiếu)

**Chưa có (mọi nhãn S2/S3/S4 sẽ treo `[OWNERSHIP-UNVERIFIED]` đúng luật cho tới khi có):**

1. **Contract 0x + chain** — quan trọng nhất, để confirm Alpha bapi match. Alpha bapi trả `0x8dedf84656fa932157e27c060d8613824e7979e3` on **BSC** — cần operator confirm khớp (bài F1 GUA — symbol-string match KHÔNG đủ).
2. **Exchange balance trend** — số token nằm sàn theo ngày (30d), khuôn ảnh GUA/TRIA (exch bal delta = deposit signal).
3. **Whale movements** — top 100 holders + recent buy/sell/deposit clusters.
4. **Circ supply + FDV + unlock schedule** — mâu thuẫn kiểm tra (mẫu ảnh GUA: 130M × 0.043 = $5.57M > MC tracker).
5. **Top100 concentration** — % holdings top 10/50/100 (mẫu để biết đây có phải whale-heavy token).

**Format request:** operator có thể paste một block:
```
contract: 0x... (BSC/ETH/SOL)
tracker source: CoinGecko/CMC/Bubblemap/...
exchange balance 30d snapshot: [date, amount_tokens] rows
whale note: (nếu có)
supply: total=X circ=Y locked=Z
```

---

## §F — TỔNG KẾT + FILE LIST

**Số chốt (đã có):**
- Perp onboard 2025-09-17, 11 tháng history · fapi TRADING
- Alpha ALPHA_376 UNVERIFIED symbol-match (contract từ bapi: 0x8ded... BSC)
- 4 spot venues: Gate (BSC deposit+withdraw OPEN), KuCoin, MEXC, Alpha (mirror-taker broken)
- Hedge episode ONGOING (div_avg3 dưới 0.5 ~30d chuỗi, khớp watchlist Aug17 struct_n=49 hedge_start=Jun27)
- Funding pin 30/30 (như TRIA)
- Aug16-17-18 cluster event: +10.6% pump → vol × 6 spike → OI peak $2.06M + div_raw jump 0.384 (un-hedge sơ khai)
- oi_cycle_pos = 1.000 (AT PEAK)
- Nền T7 chân spot tổng = $190K/day (Gate + KuCoin + MEXC + Alpha)

**Chưa có (chờ operator §S4):**
- Contract 0x confirmed
- Kho on-chain + whale
- Doctrine #10 tính đầy đủ (thiếu mẫu số kho)

**Files touched:**
| Artifact | Path |
|----------|------|
| Probe main | `_probe_stbl_20260819.py` (root, sẽ archive sau) |
| Probe supplement | `_probe_stbl_venues_supp_20260819.py` |
| Report | `docs/reports/_stbl_probe_20260819.md` (file này) |
| Scratch perp | `scratch/stbl_perp_60d_20260819.csv` (61 rows) |
| Scratch spot | `scratch/stbl_{gate,kucoin,mexc,alpha_bapi}_20260819.csv` (31 rows each) |

**KHÔNG VERDICT. KHÔNG tạo CASE file.** Chờ ANALYSIS đọc + operator relay §S4.

**DỪNG sau paste.**

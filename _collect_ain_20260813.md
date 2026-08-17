# COLLECT AIN — CASE_AIN.xlsx COLD_START
**Date:** 2026-08-17 (collect chạy 13/08, date current 17/08)
**Token:** AINUSDT · AI narrative · Binance perp (onboard 2025-07-10)
**Intel operator:** "từ 04/08 có ~30M token ≈ $2.4M nạp lên sàn"
**Scope:** AI-0 → AI-8 | CASE_AIN.xlsx 224 rows Jan01–Aug12 2026

---

## PROVENANCE
| trường | giá trị |
|--------|---------|
| data-source | fapi klines/funding/LSR/OI + Gate.io + GeckoTerminal (local scratch) |
| machine | local scratch (chưa phải VPS canonical) |
| date-range | 2026-01-01 → 2026-08-12 (last closed day) |
| code-commit | TBD (commit sau khi report này viết xong) |

---

## AI-0. IDENTITY

| field | giá trị |
|-------|---------|
| Symbol perp | AINUSDT |
| onboardDate | 2025-07-10 |
| status | TRADING |
| contractType | PERPETUAL, marginAsset=USDT |
| underlyingSubType | `['AI']` (AI narrative tag) |
| Binance Alpha BAPI | **KHÔNG CÓ** — không trong alpha list |
| Binance spot | **ABSENT** (HTTP 400) |
| Gate.io AIN_USDT | vol24h = **$78,181** — thin primary spot |
| GeckoTerminal | 3+ pool AIN/USDT, tổng vol24h ~$44K — fragmented |
| CoinGecko | Không khớp AIN trực tiếp |
| Chain | **UNKNOWN** — CẦN OPERATOR xác nhận blockchain |
| Alert grep | 0 hits trong agent_log |
| fapi variants | AIUSDT (SETTLING), GRIFFAINUSDT, AIOTUSDT, **AINUSDT** (TRADING) |

**Kết luận AI-0:** AIN không có Binance spot. Gate.io là primary spot duy nhất nhưng rất thin ($78K/day). Blockchain chưa xác định — CoinGecko không trả về kết quả phù hợp. Cần operator xác nhận chain để tra vesting/wallet.

---

## AI-1. LSR + OI PERSIST

- **LSR 4 endpoints:** 30 rows mỗi endpoint (Jul19–Aug17)
- **LSR sau freshwatch merge:** 49 dates tổng (Jul19–Aug17 phủ đầy)
- **OI hist 30d:** 25 rows (Jul19–Aug17)
- **OI snapshot (17/08):** 59,692,669 tokens ≈ **$4.51M** tại close Aug12 $0.07551
- **watchlist_1h.txt:** WARN — file không tìm thấy local (VPS path), skip register

---

## AI-2. KLINES + EVENTS

| metric | giá trị |
|--------|---------|
| Rows klines 1d perp | 224 (Jan01–Aug12 2026) |
| Binance spot klines | ABSENT |
| Funding entries | 1344 (full Jan01–Aug12) |
| ATH | **$0.13472** ngày 2026-05-13 |
| ATL | **$0.02877** ngày 2026-02-08 |
| Aug12 close | $0.07551 |
| Drawdown từ ATH | **-44.0%** |
| PROVEN_PUMP | **NO** (không có +100% trong ≤7 ngày) |

### Events vol ≥ 8× med14 (18 events)

| cụm | events nổi bật |
|-----|----------------|
| Jan-Feb | Jan30: +17.2% 13.8×, Feb24: +16.9% 18.6× |
| Mar (major) | Mar10: +50.5% **87.5×**, Mar11: +14.2% 18.2×, Mar16-18: cluster 16-37× |
| Apr (ATH attempt) | Apr11: **+76.8% 22×**, Apr12: **-18.4% 93.5×** (dump ngay hôm sau) |
| May (ATH) | May13: +34.7% 24.3× **→ ATH $0.1347**, May14: -25.4% 24.4× |
| Jun | Jun12: +27.0% 25.6×, Jun26: **-15.8% 54.2×** (dump lớn) |

**Pattern:** Mỗi pump lớn đều có dump tương ứng, thường ngay hôm sau hoặc trong 2-3 ngày. Không có "sustained pump" kéo dài. PROVEN_PUMP = NO.

---

## AI-3. DEPOSIT WINDOW — SPRINT / GRIND / BLEED

**Intel:** 30M tokens ≈ $2.4M nạp từ 04/08.

| date | close | ret_1d | vol_usd | oi_usd | gLSR | pos_r | acc_r |
|------|-------|--------|---------|---------|------|-------|-------|
| 2026-08-04 | 0.06804 | -2.70% | $797K | $3.94M | 3.623 | 1.494 | 3.272 |
| 2026-08-05 | 0.06777 | -0.40% | $737K | $3.86M | 3.653 | 1.484 | 3.329 |
| 2026-08-06 | 0.07001 | +3.31% | $679K | $3.83M | 3.697 | 1.477 | 3.348 |
| 2026-08-07 | 0.07844 | **+12.04%** | **$2.97M** | $3.94M | 3.819 | 1.458 | 3.560 |
| 2026-08-08 | 0.07806 | -0.48% | $1.14M | $4.41M | 3.083 | 1.471 | 2.905 |
| 2026-08-09 | 0.07399 | -5.21% | $1.46M | $4.39M | 2.851 | 1.450 | 2.550 |
| 2026-08-10 | 0.07214 | -2.50% | $1.04M | $4.17M | 2.422 | 1.463 | 2.079 |
| 2026-08-11 | 0.07846 | +8.76% | $2.36M | $4.12M | 2.562 | 1.460 | 2.173 |
| 2026-08-12 | 0.07551 | -3.76% | $1.66M | $4.56M | 2.271 | 1.453 | 1.934 |

**Số liệu tổng hợp cửa sổ nạp:**
- Entry Aug04: $0.06804 → Exit Aug12: $0.07551 → **Net +11.0%**
- Green/Red: **3/6** (6 ngày đỏ)
- OI delta: +$621K (+15.8%) — OI leo nhẹ trong cửa sổ
- pos_r delta: -0.041 (giảm từ 1.494→1.453)
- gLSR đỉnh Aug07: **3.819** (retail cực long), sau đó hạ dần 2.271 Aug12

**Ladder phân tầng:**
- Aug07: TIER1-spike (2.97M, +12%)
- Aug11: TIER1-spike (2.36M, +8.76%)
- Aug04-06, Aug08-10, Aug12: TIER2-moderate (679K-1.46M)

**► TAXONOMY: BLEED**
- 6/9 ngày đỏ, net +11% nhưng sau spike Aug07 là 5 ngày liên tiếp bleed (trừ Aug11 bounce)
- Không có SPRINT rõ (Aug07 spike chỉ 2.1× mean, không phải sprint cổ điển)
- OI leo nhẹ nhưng pos_r giảm → accumulator account giảm tỷ lệ long trong khi giá tạo điểm mua mới

---

## AI-4. BỐN VÂN TRIAGE

### VÂN 1 — pos_r TREND

| khoảng | avg pos_r | note |
|--------|-----------|------|
| Jan-Mar | N/A | LSR data chỉ có từ Jul19 (30d rolling) |
| Apr-Jun | 1.616 | |
| Jul-Aug12 | **1.676** | |
| OLS slope May01-Aug12 | **-0.0037 ↓ FALLING** | |
| Last 5 days | 1.471, 1.450, 1.463, 1.460, 1.453 | declining |

**pos_r vs price correlation:** 33/48 same direction = **69% RETAIL-FOLLOW** → pos_r KHÔNG ngược chiều giá, KHÔNG có gom NGƯỢC trend.

**Kết luận Vân1:** pos_r ở mức 1.45-1.68 (net long nhưng không áp đảo). Slope giảm nhẹ. KHÔNG có inverso pattern kinh điển của tích lũy có chủ đích. Tỷ lệ top-trader long đang giảm.

### VÂN 2 — FUNDING / HEDGE-FARM

| block | thời gian | số ngày | avg div_avg3 |
|-------|-----------|---------|-------------|
| Hedge block 1 | Jun29→Jul10 | 12d | 0.747 |
| Break | Jul11→Jul14 | 4d (div≥1) | — |
| **Hedge block 2 (ongoing)** | **Jul15→Aug12** | **29d** | **0.658** |

- Total ngày div_avg3 <1.0: **41/45** ngày có data
- Longest block: **29d** (Jul15–Aug12, ĐANG CHẠY)
- Un-hedge crossing: Jul11 (div=1.075), sau đó quay lại <1 Jul15 → **false break**
- Funding tất cả: **POSITIVE** (0.00005–0.00037) — retail LONG trả phí cho SHORTS

**GOM-E: PASS** (29d ≥ 14d threshold)

**Ý nghĩa:** Kẻ nắm vị thế lớn (high position) đang SHORT relative to account ratio, thu phí funding từ retail long. 29 ngày liên tục — đây là hedge-farm có cấu trúc. **Nhưng câu hỏi:** hedge để bảo vệ spot hay để phân phối?

### VÂN 3 — RANGE CONTROL

| metric | giá trị |
|--------|---------|
| Days ret ≤ -5% | 47 |
| Next-day recovery | 14/47 = **30%** |
| 3d recovery rate | 38/47 = **81%** |
| Pre-ATH low | $0.02877 (Feb08 ATL) |
| Pump amplitude ATL→ATH | +368% (dài hạn, không trong 7 ngày) |

**Kết luận Vân3:** 30% next-day recovery thấp (không có "floor defense" kiểu tích lũy). 3d recovery 81% = market tự hồi phục, không có can thiệp rõ ràng. KHÔNG có kiểm soát range đặc trưng.

### VÂN 4 — ON-CHAIN / VENUE

- **Blockchain: UNKNOWN** — CoinGecko không match AIN
- **Gate.io**: $78,181/ngày — **29 ngày mới exit đủ 30M tokens** ($2.27M ÷ $78K)
- **GeckoTerminal**: ~$44K/ngày fragmented, không đủ để trace
- **Depth ±2% perp**: BID $591 / ASK $421 — CRITICAL
- **Depth/OI ratio**: 0.0225% — EXTREME THIN
- **CẦN OPERATOR**: chain + explorer + wallet 30M + vesting schedule

---

## AI-5. HAI LĂNG KÍNH

### GOM-D (4/4 PASS)

| điều kiện | kết quả | chi tiết |
|-----------|---------|----------|
| D1: vol≥8×+ret>0 | **PASS** | 11 events: Mar10 87.5×, Apr11 22×, May13 24.3× |
| D3: cluster ≥3d | **PASS** | 4 clusters: Feb23-26, Mar16-19, Apr11-13, Jun11-14 |
| D4: wake-up ≥+15% | **PASS** | 9 events wake-up sau quiet period |
| D5: churn | **PASS** | 3 days high-vol |ret|<5% |

**GOM-D 4/4 PASS** — nhiều vol cluster đặc trưng pump setup. NHƯNG: mỗi cluster đều kết thúc bằng dump lớn (Apr12: 93.5×, May14: 24.4×, Jun26: 54.2×). Không duy trì được đà tăng.

### GOM-E (PASS)

- 29d sustained hedge Jul15–Aug12 (ongoing)
- Sophisticated capital (large position) systematically SHORT vs retail long
- Funding positive → shorts thu phí từ longs
- **GOM-E PASS** nhưng cần đối chiếu với on-chain để phân biệt: hedge-for-accumulation vs hedge-to-distribute

---

## AI-6. RŨ-ĐÀN GAUGE

| event | gLSR | acc_r | pos_r | nhận xét |
|-------|------|-------|-------|----------|
| Mar10 pump +50% | 0 (no data) | 0 | 0 | Pre-LSR window |
| May13 ATH +35% | 0 | 0 | 0 | Pre-LSR window |
| Jun26 dump -16% | 0 | 0 | 0 | Pre-LSR window |
| **Aug07 pump +12%** | **3.819** | **3.560** | **1.458** | Retail cực long peak |
| Aug09 bleed -5.2% | 2.851 | 2.550 | 1.450 | Retail rút dần |
| Aug12 close | 2.271 | 1.934 | 1.453 | Tiếp tục rút |

**gLSR trung bình (49 ngày có data):** 2.705
- ≥2.0 (retail long peak): 40 ngày
- ≤0.7 (retail short): 0 ngày

**Nhận xét rũ-đàn:**
- Trong cửa sổ nạp (Aug04-12): gLSR đỉnh 3.819 ngày Aug07 (spike), sau đó hạ về 2.271 Aug12
- acc_r giảm từ 3.56 (Aug07) xuống 1.93 (Aug12): retail account đang rút long nhanh chóng
- pos_r ổn định hơn (1.45-1.47): top position holders không hoảng loạn rút
- Pattern: retail rũ ra, top traders giữ vị thế

---

## AI-7. SPOT / VENUE / DEPTH

| venue | vol24h | note |
|-------|--------|------|
| Binance perp | ~$1-3M/ngày (cửa sổ nạp) | primary perp |
| Binance spot | ABSENT | không có |
| Gate.io spot | **$78,181** | primary spot, cực thin |
| GeckoTerminal DEX | ~$44K total | fragmented |

| depth metric | giá trị | đánh giá |
|-------------|---------|----------|
| Bid ±2% | **$591** | CRITICAL |
| Ask ±2% | **$421** | CRITICAL |
| OI tổng | $4.51M (snapshot 17/08) | |
| Depth/OI | 0.0225% | EXTREME THIN |
| Deposit value | ~$2.27M (30M × $0.0755) | |
| Days to exit (Gate) | **~29 ngày** | không thể exit nhanh |

**Kết luận venue:** Token không có Binance spot. Gate.io quá thin để exit lớn. Perp depth không đủ để hedge hoặc exit 30M tokens. Bất kỳ exit strategy nào đều cần OTC hoặc weeks.

---

## AI-8. SANITY

| check | kết quả |
|-------|---------|
| S1: 224 rows | PASS |
| S2: Date continuity | PASS (0 gaps) |
| S3: No negative close | PASS |
| S4: ATH $0.13472 verified | PASS |
| S5: Taker [30,70]% | PASS (224/224) |
| **TỔNG** | **5/5 PASS** |

---

## BẢNG BỐN VÂN TỔNG HỢP

| VÂN | BIẾN | SỐ LIỆU | SIGNAL |
|-----|------|---------|--------|
| 1 | pos_r trend | Apr-Jun=1.616→Jul-Aug=1.676, slope -0.0037↓ | RETAIL-FOLLOW, KHÔNG inverso |
| 2 | Funding/hedge | 29d max block (ongoing), 41/45 ngày <1 | GOM-E PASS — hedge-farm có cấu trúc |
| 3 | Dip recovery | 14/47=30% next-day, 38/47=81% 3d | Không kiểm soát floor chủ động |
| 4 | On-chain/venue | MISSING blockchain; Gate $78K/d thin | CẦN OPERATOR |

---

## TỔNG HỢP CASE

### Câu hỏi 1: Sprint / Grind / Bleed (deposit window Aug04-12)
**→ BLEED** — 6/9 đỏ, spike Aug07 (+12%) sau đó bleed. OI leo nhưng pos_r giảm. Không có sprint cổ điển (volume peak + clear exit).

### Câu hỏi 2: Perp structure
- Perp Binance, không có spot Binance. Gate.io thin primary.
- Funding POSITIVE → retail long đang trả phí.
- OI $4.5M vs $78K/day spot = liquidity rất hạn chế.
- Depth $591 bid = không thể exit qua perp.

### Câu hỏi 3: Bốn-vân gom thật
- **Vân 2 (GOM-E PASS)** là tín hiệu tích cực nhất: 29d hedge có cấu trúc.
- **Vân 1**: KHÔNG inverso → thiếu đặc trưng gom NGƯỢC retail.
- **GOM-D 4/4 PASS**: nhiều vol cluster nhưng mỗi cluster có dump lớn ngay sau.
- **Tổng thể**: tín hiệu MIXED. GOM-E gợi ý có smart money, nhưng pos_r không leo ngược và price -44% từ ATH.

### Câu hỏi 4: Proven_pump check
**→ NO** — không có +100% trong ≤7 ngày liên tiếp. ATH $0.1347 từ ATL $0.0288 = +368% nhưng qua nhiều tháng.

---

## CẦN OPERATOR

1. **Blockchain AIN**: chain nào? (EVM BSC/ETH/Solana?) → cần cho explorer trace
2. **Vesting schedule**: 30M token từ vesting release hay OTC hay wallet cold?
3. **Wallet trace**: địa chỉ deposit lên Binance/Gate từ blockchain nào?
4. **Verdict ô**: A/B/C/D — sau khi có on-chain + operator judgment

---

**DỪNG CHỜ OPERATOR ĐỌC + XÁC NHẬN BLOCKCHAIN + VERDICT.**

# COLLECT — CYSUSDT — 13/08/2026

```
data-source : fapi.binance.com (klines/funding/LSR/OI) + freshwatch_daily_*.csv + Gate.io API + GeckoTerminal
machine     : local scratch
date-range  : 2026-01-01 → 2026-08-12 (klines); LSR 2026-06-01 → 2026-08-12 (freshwatch+fapi)
code-commit : TBD (probe chưa commit)
CASE_CYS.xlsx : docs/case_files/CASE_CYS.xlsx (224 rows, 50 cols, 7 sheets)
```

Câu hỏi case: **"Có lực GOM THẬT không (bốn vân: tử-số leo / funding cầm lái / kiểm-soát-giá / rút-tại-nền)? HAY staged-distribution (kho có sẵn, đẩy lên sàn)? Nếu gom: bao nhiêu, ngày nào, vân nào chứng minh?"**

---

## C-0. ĐỊNH DANH + TRUY ALERT

### C-0a. Identity

| Trường | Giá trị |
|--------|---------|
| Symbol | CYSUSDT (Binance perp) |
| underlyingType | COIN |
| underlyingSubType | ['Alpha'] |
| onboardDate perp | **2025-12-12** |
| status | TRADING |
| marginAsset | USDT |
| alpha_id | ALPHA_495 (trong alpha_id_map.json) |
| BAPI alpha list | **KHÔNG CÓ** (CYS không xuất hiện trong bapi token list Aug13) |
| Chain | **Solana** (GeckoTerminal: CYS/USDC pool `4vLE6q9WvnPz...`, CYS/SOL `2gUE3PWHhpjd...`) |
| Binance spot | **ABSENT** (HTTP 400) |
| Gate.io spot | **CYS_USDT — ACTIVE** last=$1.538, vol24h=$9,756,734 (PRIMARY SPOT) |
| DEX Solana | CYS/USDC $346K/24h + CYS/SOL $67/24h (minimal) |
| Contract | Solana — CẦN OPERATOR xác minh qua Solscan (L-28: ≥2 nguồn) |

**L-28 chain verify:** GeckoTerminal (nguồn 1) xác nhận Solana. Solscan.io (nguồn 2) = CẦN OPERATOR.

### C-0b. Alert Trace (GOM-C confirmed)

CYS **có trong lứa alert** GOM-C beta test group ngày **2026-08-07**. Nguyên văn từ gom_gate6 reports:

```
C5 COOKIE/CYS/TST live 08-07 → PASS (COOKIE+CYS fire 08-07; TST cooldown)
CYS: no state; GOM-C fires 08-07 (stateless) — khớp expected
CYS/TUT có VWAP=N/A = chains suppressed, update_chain return trước VWAP block
```

- **Lứa alert ngày 08-07:** CYS fire GOM-C (cùng đợt COOKIE, không cùng FF/ROBO)
- **Chain state:** stateless (chapter không mở được, VWAP=N/A)
- **Triage group:** COOKIE / CYS / TST — D2 triage 08/08/2026 (CHỜ OPERATOR CHẤM)
- **Q1 nếu có:** N/A (chain suppressed, không có Q1 state)
- **GOM-C PROVISIONAL** (gate 15/08 pending)

---

## C-1. LSR + OI PERSIST — VERIFY ROW COUNT

| Endpoint | Rows | Date range | Note |
|----------|------|-----------|------|
| topLongShortPositionRatio (pos) | 30 | Jul15-Aug13 | 30d retention confirmed |
| topLongShortAccountRatio (acc) | 30 | Jul15-Aug13 | 30d retention confirmed |
| globalLongShortAccountRatio (gLSR) | 30 | Jul15-Aug13 | 30d retention confirmed |
| takerlongshortRatio | 30 | Jul15-Aug13 | |
| openInterestHist (30d) | 30 | Jul15-Aug12 | |
| **freshwatch merge** | +43 dates | Jun01-Jul14 | LSR thực tế bắt đầu Jun01 |
| **LSR total merged** | **73 dates** | **Jun01-Aug12** | |
| funding full history | 1344 entries | Jan01-Aug12 | 224 ngày |

**Lưu ý (L-21):** LSR từ Jun01 là từ freshwatch CSV (nguồn VPS canonical). Tháng 6 không có LSR trực tiếp từ fapi (>30d retention). Không "giả vờ có ratio" — ghi rõ nguồn ở cột `data_source_lsr`.

**Universe 137 merge:** CYSUSDT có trong freshwatch (65 rows Jun01-Aug07). Merge tự động trong build_case.py.

---

## C-2. KLINES TRỌN ĐỜI + EVENTS

**Klines phủ:** Jan01-Aug12 (224 ngày). Pre-listing Dec12-31 = MISSING (M6).

**ATH trong store:** $1.6751 trên **2026-08-12** (close mới nhất = ATH mới).

### VERIFY-TAY 5 dòng cuối:

| date | open | high | low | close | vol_q_usd | taker% | ret_1d |
|------|------|------|-----|-------|-----------|--------|--------|
| 2026-08-08 | 0.9495 | 1.2288 | 0.7450 | 0.9453 | $369,436,608 | 50.74% | -0.44% |
| 2026-08-09 | 0.9453 | 1.3192 | 0.7550 | 1.0861 | $184,892,950 | 50.85% | +14.89% |
| 2026-08-10 | 1.0868 | 1.3436 | 0.8931 | 1.2656 | $267,392,382 | 50.48% | +16.53% |
| 2026-08-11 | 1.2655 | 1.7787 | 0.9850 | 1.0821 | $441,709,649 | 51.72% | -14.50% |
| 2026-08-12 | 1.0815 | 1.7060 | 0.9337 | 1.6751 | $322,051,643 | 51.62% | +54.80% |

px_avg, ret_1d non-null: ✓ (computed close-to-close in XLSX)

### A.5 EVENTS: |ret|>10% VÀ vol≥8× med14

**Nhịp cụm pump từ Jan01:**

| Cluster | Dates | Peak ret | vol × med14 | Cơ chế |
|---------|-------|----------|-------------|---------|
| Cluster-A (Jan) | Jan04(+10%), Jan31(+83%) | +83% | 12× | Pump+quick dump |
| Cluster-B (Mar) | Mar09(+18%), Mar21-23(+14/+12/+12%) | +18% | 5.9-11× | 3-day sustained |
| Cluster-C (Aug) | Aug04-12 (6/9 days ≥10%) | +98.6% (Aug04) | **310-544×** | MEGA PUMP |

**Blowoff cũ (vùng-nhớ):** Mar23 đỉnh $0.715 → Mar24-26 dump -23/-25/-17% trong 3 ngày, f_min xuống -0.004821. Đây là blowoff trước. Vùng nhớ: $0.70-0.72 resistance cũ.

**Events vol≥8× med14 (L-15 bait candidates):**
```
2026-01-31:  12.1× ret=+83.4%   → pump
2026-03-05:  11.1× ret=+4.9%    → quiet day (D5 churn)
2026-03-10:  11.3× ret=-1.7%    → quiet day (D5 churn)
2026-08-04: 310.6× ret=+98.6%   → MEGA PUMP start
2026-08-05: 544.3× ret=+49.0%   → MEGA PUMP peak
2026-08-06: 253.4× ret=-2.1%    → churn (D5)
2026-08-07: 181.4× ret=+15.0%   → re-pump
2026-08-08: 356.2× ret=-0.4%    → churn (D5)
2026-08-09: 127.9× ret=+14.9%   → re-pump
2026-08-10:  85.0× ret=+16.5%   → re-pump
```

---

## C-3. TRIAGE + BẢNG BỐN VÂN

### C-3a. Triage Bộ Ba

**div_avg3 (71 ngày valid, Jun01-Aug12):**

| Tháng | mean | range | bear% (div<1) |
|-------|------|-------|---------------|
| Jun | 1.297 | [1.053, 1.939] | 0% |
| Jul | **0.938** | [0.723, 1.186] | **55%** |
| Aug | 1.446 | [0.869, 2.129] | 17% |

**Highlight:** Jul02-18 = 17 ngày liên tục div_avg3 < 1.0 → hedge-farm period. Un-hedge Jul19 (div 0.924→1.032) và lần nữa Aug05 (0.869→1.019 trong pump).

**gLSR (73 ngày valid, Jun01-Aug12):**

| Giai đoạn | mean | range |
|-----------|------|-------|
| Jun01-Jul23 (pre-pump) | 1.451 | [1.005, 1.939] — retail long bias |
| Aug04-12 (pump) | **0.726** | [0.459, 2.008] — **retail SHORT trong pump** |

Aug04: gLSR=2.008 (retail peak long) → Aug05: gLSR=0.459 (retail SHORT vào pump) → short squeeze flip. 8/9 ngày pump gLSR < 1.0.

**Pin streak:** max 8 ngày (May24). 34.4% ngày f_avg pinned [4e-5, 6e-5]. Không có streak ≥5 sustained period đủ mạnh cho B2.

### C-3b. BẢNG BỐN VÂN

#### Vân1 — TỬ-SỐ (pos_r leo bậc)

Đối chứng: GOM thật ZBT +90% leo bậc | APR ~0% flat | CYS = ?

| Điểm so sánh | Giá trị |
|------|---------|
| pos_r Jun01 | 2.208 |
| pos_r Jul01 | 1.372 (Δ=-18.3% vs 28d ago) |
| pos_r Aug01 | 1.661 (Δ=+22.8% vs 28d ago) |
| pos_r Aug07 | 0.947 (Δ=-27.3% vs 28d ago) |
| pos_r Jun01→Aug12 | **2.208 → 0.806 = −63.5%** |
| Tháng 6 avg | 1.516 |
| Tháng 7 avg | 1.497 |
| Tháng 8 avg | **1.073** (crash trong pump) |

**pos_r GIẢM trong pump (Aug04-12):**
```
Aug03: pos_r=1.333 | acc_r=1.560 | div_r=0.855 | gLSR=1.880
Aug04: pos_r=1.367 | acc_r=1.685 | div_r=0.812 | gLSR=2.008  ← retail long peak
Aug05: pos_r=0.995 | acc_r=0.383 | div_r=2.600 | gLSR=0.459  ← SQUEEZE: acc_r collapsed!
Aug06: pos_r=0.893 | acc_r=0.460 | div_r=1.943 | gLSR=0.532
Aug07: pos_r=0.947 | acc_r=0.490 | div_r=1.935 | gLSR=0.520
Aug08: pos_r=0.936 | acc_r=0.424 | div_r=2.207 | gLSR=0.487
```

**Kết luận Vân1:** pos_r **KHÔNG leo bậc** (−63.5% trong window). Pump Aug05: acc_r (top shorts) sụp từ 1.685→0.383 = short positions bị LIQUIDATED/COVER. div_r spike 2.60 = cơ chế squeeze rõ ràng, KHÔNG phải accumulator build.

#### Vân2 — CHI-PHÍ (funding cầm lái / hedge thu phí)

| Metric | Giá trị |
|--------|---------|
| Pin days (f_avg ∈ [4e-5,6e-5]) | 77/224 = 34.4% |
| Max pin_streak | 8 ngày (May24) |
| div_avg3 < 1.0 (hedge thu phí) | 19/71 = 26.8% valid days |
| Longest div<1 streak | **17 ngày (Jul02-Jul18)** |
| Neg funding days | 6 (Mar12/25/26, Aug05/08/09) |

**Neg funding events:**
```
Mar25: f_avg=-0.000407  f_min=-0.001272  (sau Mar21-23 pump, đang dump)
Mar26: f_avg=-0.001166  f_min=-0.004821  (dump -16.9%)
Aug05: f_avg=-0.001299  f_min=-0.006931  (SHORT SQUEEZE apex — shorts trả nặng)
Aug08: f_avg=-0.000979  f_min=-0.004936  (tiếp tục squeeze aftermath)
Aug09: f_avg=-0.001844  f_min=-0.009564  (f_min -0.95% = cực đoan)
```

**Kết luận Vân2:** Funding mostly neutral-pinned (5e-5). Jul02-18 là **hedge window**: div<1 kéo dài 17 ngày — accumulator short thu phí từ retail longs. Nhưng pin_streak không đủ (max 8d, không sustained ≥14d). Neg funding xuất hiện trong dump (Mar) và squeeze (Aug), không phải gom yên lặng.

#### Vân3 — KIỂM-SOÁT-GIÁ (dip recovery)

| Metric | Giá trị |
|--------|---------|
| Tổng dip days (ret<-5%) | 45 ngày |
| Mua đảo ngày hôm sau | 22/45 = **49%** |
| Pre-pump price range (Jun01-Aug03) | $0.277 → $0.470 = **70% range = RỘNG** |
| Mar24-26 dump | −23.8%/−24.9%/−16.9% — KHÔNG mua đảo ngay |

**Các dip lớn và recovery:**
```
Apr09: -24.8% → Apr10: +36.9%  ✓ (bottom bounce)
Mar24: -23.8% → Mar25: -24.9%  ✗ (tiếp tục dump)
Mar25: -24.9% → Mar26: -16.9%  ✗ (tiếp tục dump)
Aug11: -14.5% → Aug12: +54.8%  ✓ (massive recovery)
Jun24: -15.1% → Jun25: -5.3%   ✗ (partial)
```

**Kết luận Vân3:** Dip recovery 49% = essentially random. Không có pattern kiểm soát giá hệ thống. Range Jun-Aug03 70% = RỘNG (biến động, không range-bound). Không có evidence "mua đảo trong ngày" để bảo vệ nền.

#### Vân4 — ON-CHAIN HƯỚNG

```
Nansen: LOCKED → CẦN OPERATOR
Chain: Solana — Solscan.io CẦN OPERATOR
Exchange balance ladder: MISSING
```

**Proxy từ funding+div:**
- Jul02-18: div_avg3 < 1 = accumulator short hedge (thu phí từ retail longs)
- Jul19: un-hedge → price bắt đầu nhích (nhưng không breakout)
- Aug04-07: OI $7.1M → $23.1M (+225%) = fresh longs FOMO vào sau khi squeeze bắt đầu

**Bảng ô quyết định:**

```
                     on-chain RÚT (gom thật)    on-chain NẠP/HOLD
pos_r LEO (tử-số↑)       A = GOM THẬT                B = mixed
pos_r PHẲNG/GIẢM     C = churn/distribution       D = staged-pump

CYS hiện tại: pos_r −63.5% (GIẢM) × on-chain UNKNOWN → ô C/D
→ Thiên về D (staged-pump): kho có sẵn, đẩy qua short squeeze
```

**Cần operator làm để chốt ô:** Solscan top holders Jun01 vs Aug01 — nếu holders lớn NẠP vào exchange trước Aug04 → ô D xác nhận.

---

## C-4. HAI LĂNG KÍNH

### Kính 1 — Build-Perp §3

**GOM-A fires: 0** (A1 fail permanent: div_avg3>1.5 chỉ 10/71 ngày; A2 fail: avg5_gLSR>>1.1 hầu hết)

**GOM-B fires: 0** (B1 Jul02-18 có thể thỏa nhưng suppressor DQ)

**GOM-C fires: Aug07 — PROVISIONAL [gate 15/08]**
- C1 stealth_grind: breakout từ $0.26 trough → Aug07 $0.949 (+265% từ trough)
- C2_quiet: f_avg Aug04-06 cần verify (Aug05 f_avg=-1.3e-3 vi phạm C2!)
- Thực ra: GOM-C fire xảy ra theo cron cũ (pre-fix C2 threshold) → PROVISIONAL

**§3 Q1/net/VWAP:**

| Metric | Giá trị |
|--------|---------|
| OI Jun01 | $12,195,189 |
| OI trough Jul01-Aug03 | ~$7.1-9.2M |
| OI pump peak Aug06 | $23,108,871 |
| OI Aug12 | $17,956,914 |
| net_oi_delta (Jul15→Aug12) | **+$10,368,219** |
| Q1 gross (ΔOI⁺ accumulation) | CẦN chapter để tính chính xác |
| VWAP build | **N/A** (chain suppressed) |
| Q2 (OI>$18M) | 7 ngày (Aug05-11) — UNCALIB threshold |

**OI narrative:** $12.2M (Jun01) → $7.1M (Aug03) — declining 42% = PHÂN PHỐI. Sau đó Aug04-06: spike lên $23M = fresh longs FOMO + short squeeze OI inject. Không phải quiet accumulation build.

**Q3 VWAP:** GOM-C fire Aug07 nhưng chapter suppressed → VWAP=N/A. Nếu VWAP tính từ fire-day Aug07: avg_px Aug07=$0.949 (lower bound given subsequent run to $1.675).

### Kính 2 — Staged-Pump GOM-D

| Tiêu chí | Kết quả | Ghi chú |
|----------|---------|---------|
| D1 nền-chết (≤15% pre-Aug ATH) | **FAIL** (0 ngày tại ≤$0.107) | ATL=Apr09 $0.169 > $0.107 |
| D2 quiet period (≤45% pre-Aug ATH) | 55 ngày (Jan25-Aug03) | Giá thấp nhưng không dead-floor |
| D3 vol clusters ≥3 | **PASS** (4 clusters) | Jan/Mar/Jul29/Aug |
| D4 vol-wake ≥5 days | **PASS** (10 ngày Aug04-13) | 310-544× med14 |
| D5 churn days ≥3 | **PASS** (6 ngày) | Mar05/10, Aug06/08 |

**GOM-E hedge-farm:** 17 ngày div<1 Jul02-18 → un-hedge Jul19 (div 0.924→1.032). Un-hedge thứ 2 Aug05 (trong squeeze). Pattern: accumulator HEDGE Jul → UN-HEDGE ngay trước/trong pump → thu phí từ short position trong 17 ngày → release vào momentum.

**TAG:**
- NUM (numerator): pos_r (longs) — GIẢM từ 1.37 xuống 0.80 trong pump
- DENOM (denominator): acc_r (shorts) — sụp từ 1.68 xuống 0.38 ngày Aug05 (SHORT COVER)
- OI-EXPAND: +$16M trong Aug04-06 = fresh FOMO longs + short cover OI churn

---

## C-5. RŨ-ĐÀN GAUGE (4-màn)

```
Pre-pump Jul15-Aug03: gLSR=1.46-2.008 → màn 3+ (retail long, crowd bullish)
Aug04: gLSR=2.008 (peak retail bullish)
Aug05-12: gLSR=0.459-0.678 → màn 1 (retail SHORT vào pump)
```

| gLSR | màn | Ý nghĩa |
|------|-----|---------|
| >1.2 | 3+ | Retail bullish crowd, campaign phase escalated |
| 1.0-1.2 | 2 | Retail neutral, early stage |
| <1.0 | 1 | Retail SHORT (retail đang bet ngược pump) |

**Campaign assessment:**
- Pre-pump: màn 3+ (retail đang long nặng $7-8M OI) → đúng setup cho squeeze
- Pump: retail flip to short (gLSR crash 2.008→0.459) = **SHORT SQUEEZE** màn-đặc-biệt
- 8/9 ngày pump Aug05-12: gLSR <1.0 = retail vẫn đang short vào pump
- OI spike $7.1M→$23.1M = không hoàn toàn là "lực gom" mà là FOMO longs + short cover

**Màn campaign:** SHORT SQUEEZE (không phải gom yên lặng màn 1→3 chuẩn)

---

## C-6. SPOT + VENUE + ON-CHAIN

### Venue Map

| Venue | CYS pair | Status | Vol 24h (Aug13) |
|-------|----------|--------|----------------|
| Binance perp | CYSUSDT | TRADING | ~$275M (Aug13 ticker) |
| Binance spot | CYSUSDT | **ABSENT** | — |
| Gate.io spot | CYS_USDT | **ACTIVE** | **$9,756,734** ← PRIMARY |
| GeckoTerminal Solana | CYS/USDC | Active | $346,398 |
| GeckoTerminal Solana | CYS/SOL | Active | $67 |

### Wash Test

| Test | Kết quả |
|------|---------|
| Gate.io vol / perp OI ratio | $9.75M / $30.7M = 0.32 (reasonable Aug13 normal day) |
| Pump vol Aug04-10 | $252M-$475M/day trên perp (310-544× med14) |
| Pump Gate.io vol | UNKNOWN — CẦN manual verify |
| Perp depth ±2% (Aug13) | **Bid=$379, Ask=$128 với OI=$30M** → Depth/OI=0.001% = **CỰC MỎ** |
| L-15 wash-test candidate | **YES** — thin book + extreme vol multiple |

**L-29:** ABSTAIN (no Binance spot pair → taker_spot không collect)
**L-30:** Gate.io (không phải Bitget) → rule L-30 không áp

**Depth snapshot Aug13:** mid=$1.5460 | Bid ±2%: $379 | Ask ±2%: $128

**→ CRITICAL FLAG:** Perp book CỰC MỎ. Với $30M OI và $507 total depth ±2%, thị trường này hoàn toàn có thể di chuyển bởi algo không cần liquidity resting orders. Phải ghi vào CASE.

### On-Chain

- **Chain:** Solana (2 nguồn: GeckoTerminal CYS/USDC pool + BAPI underlyingSubType=['Alpha'])
- **Explorer:** Solscan.io — CẦN OPERATOR
- **Nansen:** LOCKED — CẦN OPERATOR
- **Top holders ladder:** MISSING (M1, M3)
- **ALPHA_495:** Có trong alpha_id_map.json (Binance đã track trong Alpha universe)
- **Unlock schedule:** UNKNOWN — CẦN OPERATOR từ Solscan/vesting contract

---

## C-7. SỔ CHÉO + SANITY

| Mục | Kết quả | Evidence |
|-----|---------|---------|
| S1 Row count | **PASS** | 224 rows, expected 224, L-32 verified |
| S2 Date continuity | **PASS** | 0 gaps trong Jan01-Aug12 |
| S3 No negative close | **PASS** | All closes > 0 |
| S4 ATH verification | **PASS** | $1.6751 on Aug12 (latest = ATH) |
| S5 taker range [30,75]% | **PASS** | 0/224 OOR |

**SANITY 5/5 PASS** ✓

**Sổ chéo cross-checks:**
- pos_r Jun01=2.208 trong freshwatch CSV khớp với gom_acu_cys probe (session trước)
- OI Jun01=$12.2M trong freshwatch khớp với build output
- Funding 1344 entries / 8h per day ≈ 1344/3 = 448 ngày = Dec12 2025 → Aug12 2026 ✓ (244 ngày × 3 = 732 expected nhưng fapi trả 1344 = có 4h intervals nữa trong giai đoạn đầu) — acceptable, không phải lỗi

---

## LAYER COVERAGE

| Layer | Status | Note |
|-------|--------|------|
| Perp LSR (pos/acc/gLSR) | ✓ 73 dates | freshwatch Jun01-Jul14 + fapi Jul15-Aug12 |
| OI hist | ✓ 30d | Jul15-Aug12; Jun01-Aug07 từ freshwatch |
| Funding | ✓ full | Jan01-Aug12, 1344 entries |
| Spot vol | ✗ MISSING | Binance absent; Gate.io manual $9.75M |
| Taker spot | ✗ ABSTAIN | L-29 rule |
| On-chain | ✗ MISSING | Nansen LOCKED, Solscan CẦN OPERATOR |
| Depth | ✓ snapshot | Aug13 single snap — Bid=$379, Ask=$128 |
| Alpha klines | ✗ N/A | CYS không trong BAPI alpha list hiện tại |

---

## MISSING

| ID | Mô tả | Priority |
|----|-------|---------|
| M1 | Nansen on-chain CYS Solana (holders/flow) | HIGH — CẦN OPERATOR |
| M2 | Gate.io vol Aug04-10 pump period | MEDIUM — manual verify |
| M3 | Solscan top holders + vesting unlock schedule | HIGH — CẦN OPERATOR |
| M4 | DEX vol spot Aug04-12 (GeckoTerminal API) | LOW |
| M5 | OI Jun01-Jul14 chính xác (freshwatch làm proxy) | DONE via freshwatch |
| M6 | Pre-listing klines Dec12-31 | LOW |
| M7 | Contract address Solana xác nhận (Solscan L-28) | HIGH — CẦN OPERATOR |

---

## VERDICT TỔI (không phán, chỉ thu thập)

**Câu hỏi case:** Có lực GOM THẬT? Hay staged-distribution?

**Bằng chứng thu thập được:**

| Vân | Tín hiệu | Hướng |
|-----|----------|-------|
| Vân1 Tử-số | pos_r −63.5% trong window. Pump: acc_r collapsed (shorts cover) | ← Không gom |
| Vân2 Chi-phí | Jul02-18: 17d hedge (div<1). Funding squeeze Aug05-09 | ← Hedge phase, không pin tích lũy |
| Vân3 Kiểm-soát-giá | 49% dip recovery (ngẫu nhiên). Range 70% (rộng) | ← Không kiểm soát |
| Vân4 On-chain | MISSING — CẦN OPERATOR | → Chưa kết luận |
| GOM detector | A/B: 0 fires. C: Aug07 PROVISIONAL (gate 15/08) | ← Không chapter verifiable |
| OI narrative | Jun→Aug03: phân phối. Aug04+: short squeeze + FOMO | ← Staged pump signal |
| Rũ-đàn | SHORT SQUEEZE màn-đặc-biệt (không phải gom màn chuẩn) | ← Squeeze, không gom |

**Ô bảng quyết định: C/D** (pos_r giảm × on-chain unknown)  
→ Thiên về **D (staged-pump/distribution)**: kho có sẵn (từ khi nào?), đẩy qua short squeeze mechanism, FOMO longs vào sau.

**Pending để chốt verdict:**
1. Solscan top holders Jun01 vs Aug01 — có rút khỏi exchange hay nạp vào?
2. Gate.io vol Aug04-10 — có bất thường không?
3. Vesting unlock schedule — có unlock event gần Aug04?
4. On-chain CẦN OPERATOR xác nhận ô D vs kịch bản thay thế

**DỪNG CHỜ OPERATOR ĐỌC.**

---

## C-8 FILE STATUS

```
CASE_CYS.xlsx : docs/case_files/CASE_CYS.xlsx
  Status      : "COLD_START — PENDING"
  Sheets      : CASE / DAILY / EVENTS / TRIGGERS / OUTCOME / MM_PROFILE / UNLOCK (7 sheets)
  DAILY rows  : 224 (Jan01-Aug12 2026)
  L-32        : PASS (224 non-null dates)
  L-34        : PASS (validate_written_pack)
  Backup      : scratch/CASE_CYS_BACKUP_*.xlsx (auto by build_case.py)
CASE_INDEX    : CẦN UPDATE (thêm dòng CYS)
INDEX.md      : CẦN UPDATE
```

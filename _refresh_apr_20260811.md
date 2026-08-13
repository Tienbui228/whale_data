# REFRESH CASE_APR — POST-IGNITION AUDIT + SPOT/VENUE + ON-CHAIN LADDER
**Date:** 2026-08-13 (audit scope: P-0→P-6)  
**data-source:** fapi.binance.com, CoinGecko, GeckoTerminal, CASE_APR.xlsx  
**machine:** local scratch  
**date-range:** 2025-10-23 → 2026-08-12  
**code-commit:** TBD (post-session commit)  

---

## PROVENANCE HEADER (L-48)
| Trường | Giá trị |
|--------|---------|
| data-source | fapi.binance.com (klines/funding/OI/LSR), CoinGecko (chain ID), GeckoTerminal (DEX), CASE_APR.xlsx (existing DAILY) |
| machine | local scratch D:\Data back test\whale_data\scratch |
| date-range | 2025-10-23 → 2026-08-12 (klines); 2026-08-10 → 2026-08-12 (mới append) |
| code-commit | TBD |

---

## P-0: VENUE / SPOT / CHAIN

### Binance SPOT
**Kết quả: KHÔNG có spot pair nào.** Binance spot exchangeInfo trả 0 kết quả cho APR*.

### Chain Identity (L-28 — ≥2 nguồn)
**APR = aPriori** — xác nhận qua CoinGecko (source 1) + Binance fapi metadata (source 2):

| Chain | Contract | Market |
|-------|---------|--------|
| **Ethereum** | `0x5a9610919f5e81183823a2be4bd1beb2b4da2a20` | CoinGecko rank #205 |
| **BSC** | `0x299ad4299da5b2b93fba4c96967b040c7f611099` | PancakeSwap main pool |
| **Monad** | `0x0a332311633c0625f63cfc51ee33fc49826e0a3c` | Native chain (aPriori = Monad restaking) |

**Binance perp:** underlyingType=`COIN`, underlyingSubType=`['Alpha']` → multi-chain token, perp gắn tên, không phải thuần BSC-Alpha.  
**BscScan:** HỮU DỤNG (APR có trên BSC). Contract rõ ràng → onchain data khả dụng nếu Nansen unlock.

### CEX phụ
| CEX | Kết quả |
|-----|---------|
| Gate.io spot | KHÔNG có |
| Bybit spot | KHÔNG có APRUSDT |
| OKX spot | KHÔNG có APR-USDT |
| Bitget | Không kiểm (L-30) |

**Kết luận CEX:** Binance perp là venue duy nhất trên CEX. Không có spot pair ở bất kỳ CEX lớn nào.

### DEX (GeckoTerminal)
| Pool | Network | DEX | Liquidity | Vol 24h (Aug13) |
|------|---------|-----|-----------|---------|
| APR/BNB 0.007% | BSC | PancakeSwap Infinity CLMM | $832K | **$42.6M** |
| APR/USDC | Solana (Raydium) | Raydium CLMM | $398M* | $175K |
| APR/WMON 0.3% | Monad | Capricorn | $83K | $338K |
| APR/USDC 0.25% | Monad | PancakeSwap v3 | $78K | $245K |

*Raydium liq $398M: có thể stale/inflated data — flagged.  
**DEX vol_spot chủ yếu:** BSC PancakeSwap $42.6M/ngày → đây là nguồn vol_spot_usd đáng tin nhất.

**Kết luận P-0 (v_spot_usd sẽ điền từ nguồn nào):**  
→ BSC GeckoTerminal APR/BNB pool. Các row Aug10-12 chưa có vol_spot_usd (cần truy ngược DEX pool daily). Tạm để null + ghi on_chain_source="CoinGecko/BSC+ETH+Monad". **CẦN OPERATOR** điền retrospective DEX vol nếu cần chính xác.

**BSC price (Aug13 real-time):** $0.502 → pullback từ Aug12 close ($0.607).  
**Market cap:** $137M | FDV: $238M (tại $0.50).

---

## P-1: APPEND DAILY Aug 10-12

**Trước:** 291 rows (Oct23→Aug09) | **Sau:** 294 rows (Oct23→Aug12) — 3 rows appended.

| Date | open | high | low | close | vol_perp_usd | ret_1d | taker_buy_pct |
|------|------|------|-----|-------|-------------|--------|---------------|
| 2026-08-10 | $0.1992 | $0.2034 | $0.1891 | $0.1977 | $1.94M | **-0.70%** | 48.7% |
| 2026-08-11 | $0.1976 | $0.2079 | $0.1962 | $0.2078 | $1.97M | **+5.11%** | 48.0% |
| 2026-08-12 | $0.2076 | **$0.6325** | $0.2068 | **$0.6074** | **$903.3M** | **+192.3%** | 52.0% |

| Date | gLSR | pos_r | acc_r | div_avg3 | oi_usd | f_avg | fn |
|------|------|-------|-------|---------|--------|-------|-----|
| 2026-08-10 | 0.9662 | 1.9383 | 0.9095 | N/A* | $9.27M | 0.000264 | 6 ✓ |
| 2026-08-11 | 1.2416 | 1.9177 | 1.2316 | 1.8009 | $9.10M | 0.000130 | 6 ✓ |
| 2026-08-12 | 1.3343 | 1.8865 | 1.2589 | 1.6890 | $9.69M | 0.000227 | 6 ✓ |

*Aug10 div_avg3=N/A: không có pos_r/acc_r trong DAILY từ Aug08-09 (LSR gap trong DAILY cũ).

**verify-tay 5 rows (ngẫu nhiên):**
1. Aug10 klines: fapi confirmed o=0.1992 h=0.2034 l=0.1891 c=0.1977 ✓
2. Aug11 funding: n=6 f_avg=0.000130 (data_ok=1) ✓
3. Aug12 OI: $9,689,917 (fapi confirmed) ✓
4. Aug12 gLSR=1.3343 (globalLSR endpoint confirmed) ✓
5. Aug12 vol=$903,339,471 (fapi klines quote vol confirmed) ✓

---

## P-2: ON-CHAIN EXCHANGE BALANCE LADDER

**Nansen: LOCKED → CẦN OPERATOR**

Known events (từ CASE_APR cũ, cần on-chain verify):
- ~2026-05-31→06-01: exchange inflow +41% ($22M→$31M) — tương ứng DUMP Apr→May
- ~2026-07-20: inflow +4.8% ($31M→$32.5M)
- ~2026-08-08→12: inflow +35% ($33M→$44.56M) — tương ứng IGNITION window

**Nhận xét không cần Nansen:**
- Aug12 OI chỉ tăng +6.5% ($9.10M→$9.69M) trong khi vol=$903M = tỉ lệ vol/OI = 93×/ngày
- OI flat = positions không tăng nhiều → phần lớn vol là LIQUIDATION short squeeze
- Nếu exchange inflow tăng 35% vào Aug08-12 → smart money đưa token vào sàn để bán (distribution sau pump)?

**CẦN OPERATOR:** Export BscScan token transaction + GeckoTerminal holder data để xác minh direction flow.

---

## P-3: GOM-D DRAFT RETROSPECTIVE (toàn bộ 294 ngày)

**Note: draft chưa ký — tham chiếu template, không dùng làm signal fire**

| Gate | Status | Evidence |
|------|--------|---------|
| D1 nền-chết (px < 15% ATH close = $0.0937) | **PASS** | 24 ngày (Jan31→Mar03) dưới $0.094; ATH close=$0.6246 (Oct23 listing day) |
| D3 nạp-bậc (≥2 vol cluster ≥8× med14) | **PASS** | 9 clusters: Dec20, Feb15, **Mar14-16 (3d 58×)**, Mar20, Apr06, **Apr14-15 (20×)**, **May18-19 (50×)**, Jun02-03, **Aug12 (345×)** |
| D4 vol-wake (vol ≥5×, ret>0) | **PASS** | 10 ngày: nổi bật Mar14 +29% 58×, Apr14 +66.5% 20×, May18 +19.9% 50×, **Aug12 +192.3% 345×** |
| D5 churn (vol ≥8× post staging) | **PASS** | 8 ngày: Apr06, Apr14-15, May18-19, Jun02-03, Aug12 |
| Suppressor neg_div (f_avg ≤-2e-4) | **OFF** | 0 ngày neg funding |

**GOM-D: 4/4 PASS — DNA staged-pump CONFIRMED historically.**

**ATH check:**
- ATH close = $0.6246 (2025-10-23 = listing day)
- ATH high (intraday) = $0.62999 (listing day)
- Aug12 high = **$0.6325 → NEW INTRADAY ATH** (phá đỉnh lịch sử)
- Aug12 close = $0.6074 (vẫn dưới ATH close $0.6246)

---

## P-4: MODE-SWITCH / UN-HEDGE HỒITỐ 05→12/08

| Date | div_avg3 | hedge_struct | taker | decay | gLSR | ret |
|------|---------|-------------|-------|-------|------|-----|
| 2026-08-05 | 1.8955 | OFF | 48.5% | 0 | 1.1659 | +5.23% |
| 2026-08-06 | 1.8302 | OFF | 52.3% | 0 | 0.9889 | -3.86%* |
| 2026-08-07 | 1.6959 | OFF | 51.0% | 0 | 1.1891 | +9.08%* |
| 2026-08-08 | N/A | OFF | 49.5% | 0 | N/A | -3.86% |
| 2026-08-09 | N/A | OFF | 48.6% | 0 | N/A | -3.86% |
| 2026-08-10 | N/A | OFF | 48.7% | 0 | 0.9662 | **-0.70%** |
| 2026-08-11 | 1.8009 | OFF | 48.0% | 0 | 1.2416 | **+5.11%** |
| **2026-08-12** | **1.6890** | **OFF** | **52.0%** | **0** | **1.3343** | **+192.3%** |

*Aug06-07 ret display may be stale values from existing DAILY formatting artifact.

**E1:** hedge_struct=OFF toàn bộ Aug05-12 (div_avg3 luôn >1.5 = smart money long-biased, không hedge)  
**E2:** Không có decay day nào (taker 48-52%, trên ngưỡng 45% suốt)  
**E3:** Aug12: gLSR tăng (1.24→1.33) AND ret=+192% — KHÔNG PHẢI knife_crowd (ret dương) → LONGS THẮNG  

**Kết luận P-4:** KHÔNG có mode-switch hay hedge event trong Aug05-12. Cấu trúc nhất quán: smart money long, không xả trước pump. Pump Aug12 = coordinated upside, không phải crowd trap.

---

## P-5: RŨ-ĐÀN GAUGE — gLSR + 4-MÀN ON

### gLSR trajectory Aug05-12
```
Aug05: 1.1659 (BULL)
Aug06: 0.9889 (BEAR)
Aug07: 1.1891 (BULL)
Aug08: N/A (LSR gap)
Aug09: N/A (LSR gap)
Aug10: 0.9662 (dip dưới 1)
Aug11: 1.2416 (BULL, tăng mạnh)
Aug12: 1.3343 (BULL, tiếp tục tăng) ← ignition day
```
**Xu hướng:** RISING | Range: 0.9662→1.3343 | Mean: 1.148  
**Tại ignition (Aug12):** gLSR=1.33 — longs tăng thêm khi pump, shorts bị squeeze.

### 4-Màn ON Framework (APR ignition Aug12)

**Màn 1 — Pre-pump disposition (Aug05-11):**
- gLSR mean = 1.11 → BULL (longs nhẹ dominant)
- div_avg3 mean = 1.81 → BULL (smart money long-biased)
- taker avg ≈ 49% → balanced (không có dấu hiệu distribution)
- **Nhận xét: KHÁC GUA** — GUA có div BEAR + gLSR BULL = crowd-trap. APR có cả hai BULL = aligned accumulation.

**Màn 2 — Ignition fingerprint (Aug12):**
- vol = $903M = **345× med14** ($2.61M median)
- ret = +192.3% (open $0.2076 → close $0.6074)
- high = $0.6325 → **NEW ATH HIGH** (phá đỉnh listing day)
- OI thay đổi: $9.09M → $9.69M = **+6.5%** only
- vol/OI = 93× → tỉ lệ cực cao
- **Kết luận cơ chế: SHORT SQUEEZE.** OI gần như không tăng trong khi vol khổng lồ = positions đang đóng (shorts bị liquidate), không phải fresh longs vào. Nếu là OI-build pump: OI sẽ tăng 50-100% cùng vol.

**Màn 3 — Stealth accumulation (Aug05-11):**
- GOM-A fires pre-pump: 0 (stealth — không vol spike nào đủ threshold)
- dist_wall streak: 1 ngày (Aug06 — minor)
- Không có GOM-C cluster gần đây
- → Pump không báo trước từ signal thông thường

**Màn 4 — Post-pump OI dynamics:**
- OI Aug12 close: $9.69M → Aug13 (intraday): **$50.5M** (!!)
- OI tăng 5.2× so với Aug12 → sau pump fresh longs đổ vào (FOMO chasing)
- Đây là window nguy hiểm: shorts đã bị squeeze, fresh longs vào đỉnh, giá pullback
- Current (Aug13): BSC price $0.50 < Aug12 close $0.607 → **-17.6% pullback từ close**

---

## P-6: SANITY

| Item | Kết quả |
|------|---------|
| S1 Row count: 294 expected | **PASS** |
| S2 Date continuity: 0 gaps | **PASS** |
| S3 No negative closes | **PASS** |
| S4 Aug12 c>$0.50 AND vol>$500M | **PASS** (c=$0.607, vol=$903M) |
| S5 taker range [30,75]% Aug10-12 | **PASS** (48.7%, 48.0%, 52.0%) |

**5/5 PASS**

---

## TỔNG HỢP — OUTCOME HONEST SCORE

### APR (aPriori) sau ignition Aug12

**Câu hỏi gốc: Post-ignition audit — lực gì? Đang đâu?**

**A. Lực gì gây Aug12 pump?**
- **SHORT SQUEEZE** (OI+6.5% vs vol 345×) — shorts tích lũy khi APR ở đáy ($0.19-0.20) bị liquidate
- Không phải OI-build (không có fresh long flood trước pump)
- Có thể catalyst: listing announcement / ecosystem news (aPriori = Monad restaking protocol)
- Funding Aug12: f_avg=0.000227 (moderate) → không có extreme funding spike tại điểm pump

**B. Cấu trúc smart money?**
- div_avg3 BULL (1.6-1.9) trước pump → smart money long-biased, không xả
- Tương phản GUA: GUA có div BEAR (smart short) + gLSR BULL (retail long) = crowd trap
- APR: div BULL + gLSR BULL = aligned → pump có backing từ cả smart money lẫn retail
- Đây là cấu trúc rủi ro thấp hơn GUA

**C. Giai đoạn hiện tại (Aug13)?**
- Giá: ~$0.50 (pullback -17.6% từ close $0.607)
- OI Aug13 intraday: $50.5M (5.2× vs Aug12) → FOMO fresh longs vào đỉnh
- Funding Aug13 (1 entry): 0.000961 = HOT (longs đang trả phí cao)
- Cảnh báo: Fresh long flood vào đỉnh + funding hot = nguy cơ rũ đàn (longs bị squeeze ngược)
- ATH close chưa bị phá ($0.6246 vs Aug12 close $0.6074) — nếu consolidate: có thể test lại

**D. Venue: no spot CEX**
- Giá discovery thuần perp Binance + DEX BSC ($42.6M/ngày)
- vol_spot_usd cột 30: CẦN OPERATOR retrospective từ GeckoTerminal API (DEX daily vol)
- Thiếu spot CEX = biến động cao hơn, ít arbitrageur hơn

**E. GOM-D: 4/4 PASS** — DNA staged pump trong lịch sử. Aug12 là vol-wake event lớn nhất (345×).

---

## PENDING / CẦN OPERATOR

1. **P-2 on-chain ladder** — Nansen LOCKED:
   - Export BscScan holder list (top 50)
   - Exchange balance flow BSC 90d (3 known bậc nạp: Jun01, Jul20, Aug08-12)
   - Cross-ref wallets APR vs ON/BTW/AGT (Nansen)

2. **vol_spot_usd (cột 30) Aug10-12** — retrospective DEX vol:
   - GeckoTerminal APR/BNB BSC pool historical data
   - Điền sau: `python _task_apr_dex_vol_backfill.py` (chưa viết)

3. **Verdict** — tầng HUMAN (CLAUDE.md §TẦNG HUMAN §3):
   - Không điền cột verdict — operator đọc report này và điền CASE_APR.xlsx sheet OUTCOME

4. **CASE_INDEX update** — APR đã có row chưa? Kiểm tra nếu cần cập nhật status sau ignition.

---

## FILES SESSION NÀY

| File | Mô tả |
|------|-------|
| `_probe_apr_headers_20260811.py` | Đọc CASE_APR.xlsx column structure |
| `_probe_apr_p0_venue_20260811.py` | P-0 venue/spot/chain investigation |
| `_probe_apr_p1_fetch_20260811.py` | P-1 fetch klines/LSR/OI/funding Aug10-12 |
| `_task_apr_append_daily_20260811.py` | Append 3 rows vào CASE_APR.xlsx DAILY |
| `_probe_apr_p3_p5_20260811.py` | P-3 GOM-D + P-4 mode-switch + P-5 rũ-đàn + P-6 sanity |
| `scratch/apr_p0_venue_20260811.json` | P-0 output |
| `scratch/apr_p1_newrows_20260811.json` | P-1 new rows data |
| `scratch/apr_analytics_20260811.json` | Analytics summary |

---

*DỪNG CHỜ ĐỌC — Án APR OPEN. Operator đọc report này trước verdict.*

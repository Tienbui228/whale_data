# COLLECT ON — 2026-08-10

**Symbol:** ONUSDT (baseAsset=ON, PERPETUAL)
**Alpha ID:** ALPHA_444 | **Contract (BSC):** `0x0e4f6209ed984b21edea43ace6e09559ed051d48`
**Pipeline:** N-0 → N-8 | **Date:** 2026-08-10
**Analyst:** whale-data-operator

---

## PROVENANCE (L-48)
| Field | Value |
|-------|-------|
| data-source (perp) | fapi.binance.com klines 1d + funding (public, no auth) |
| data-source (LSR) | freshwatch_daily_*.csv (Jun27–Aug7, 39 rows) |
| data-source (OI) | fapi.binance.com openInterestHist 30d |
| data-source (alpha) | data/raw/spot_klines_1d (local store, venue=binance_alpha) |
| machine | local scratch D:\Data back test\whale_data\scratch |
| date-range (perp) | 2025-10-25 → 2026-08-09 (289 days) |
| date-range (LSR) | 2026-06-27 → 2026-08-07 (39 rows) |
| code-commit | (pre-commit, see git log) |

---

## N-0: ĐỊNH DANH
- ONUSDT lock: baseAsset=ON, PERPETUAL, TRADING, onboard=2025-10-24
- 18 symbols chứa "ON" trên FAPI → ONE có ONUSDT là duy nhất khớp
- Disambiguation: ONUS≠ON, ON1USDT≠ONUSDT — đã lock
- Alpha ID: ALPHA_444 (từ alpha_id_map.json)
- Spot: KHÔNG có trên Binance spot (perp-only)
- FreshWatch: 39 rows (Jun27–Aug7)

---

## N-1: LSR + OI
| Metric | Value |
|--------|-------|
| globalLSR | 404 (endpoint không hỗ trợ) |
| topAccount LSR | 404 |
| topPosition LSR | 404 |
| takerLSR | 404 |
| OI 30d | 30 rows, $1.68M → $24.8M |
| OI flag | **UNCALIBRATED** (max > $18M) |
| OI latest | $16.4M |
| OI med14 | $13.4M |
| FW LSR rows | 39 (Jun27–Aug7) |

LSR fallback: freshwatch_daily_*.csv, columns: lsr_pos_r, lsr_acc_r, lsr_global_r.

---

## N-2: KLINES + BUILD
- Klines: 290 candles fetched (2025-10-24 → 2026-08-10, L-21 exclude today → 289 rows)
- Funding: 1,740 rows từ onboard date
- Build exit=0 | 289 DAILY rows × 50 cols
- GOM-A fires: **0** | GOM-B fires: **0**
- EVENTS: 48 rows (vol ≥8× med14, key pumps)

### KEY EVENTS từ klines
| Date | Ret | Vol USD | Vol×med14 | Taker | Note |
|------|-----|---------|-----------|-------|------|
| 2026-02-14 | ? | ~$85M | 10.5× | | Quiet → spike |
| 2026-03-27 | +46% | $387M | 448× | 51% | BLOWOFF 1 |
| 2026-07-21 | +30% | $110M | 12× | | Wave 1 |
| 2026-07-22 | +41% | ~$360M | 40× | | Wave 2 |
| 2026-07-27 | +48% | $150M | 16× | | Jul pump |
| 2026-07-28 | +84% | $474M | 25× | 50.7% | Jul ATH attempt |
| 2026-08-06 | ? | | | | ATH close $0.3765 |
| 2026-08-07 | ? | | | | ATH high $0.460 intraday |

ATH high: **$0.460** (Aug 7 intraday) | ATH close: **$0.37647** (Aug 6) | ATL close: **$0.06166** (listing)

---

## N-3: TRIAGE + STAGE-CHECK

### Triage bộ ba
| Metric | Current | Trend | Threshold | Status |
|--------|---------|-------|-----------|--------|
| div_avg3 | **1.4118** | Δ -0.082 | ≥1.0 bull | **BULL(>1)** |
| gLSR | **0.8512** | slope_5d -0.052↓ | >1.0 bull | **BEAR** |
| f_avg_3 | **0.000385** | — | [4e-5,6e-5] | **NOT_PIN** |
| d_pos_28d | **-0.2177** | — | >0 rising | **FALLING** |

**Đọc:** div_avg3=1.41 → top traders vẫn nghiêng long (pos>acc). Nhưng gLSR=0.85 BEAR → global crowd đang short-biased. Hai chiều này đối nghịch: top long, crowd short → KHÔNG phải setup gom thuần túy.

### Stage-check BTW template
| Stage | Marker | Số liệu ON | Status |
|-------|--------|------------|--------|
| S0 ghế-nền | pos_r slope 30d | -0.013 FALLING | **ĐÃ QUA** (nền Oct25–Jun26) |
| S0.5 crowd | gLSR current | 0.8512 BEAR | Crowd trung tính/nhẹ short |
| S1 staging-kệ | churn ≥8×med14 + exch balance | Jul vol cluster 10-40×; balance N/A | **POSSIBLE** Jul cycle |
| S2 cầu-thang | ≥3 nến liên tiếp + OI ≥3× | Jul 27-Aug 7: +48/+84%, OI 14.6×nền | **HIỆN DIỆN** |
| S3 xả-vùng-nhớ | px vs ATH · dist_wall · pos_r sập | BLOWOFF1=$0.1756, ATH=$0.46, px=$0.366, dist_wall=22d | **ĐANG DIỄN RA** |
| S4 xác | decay flags · gLSR <0.8 | gLSR=0.85 chưa sập, decay=10d | **Chưa S4** |

**Kết luận stage:** ON đang ở **S3 xả-vùng-nhớ** — giá rút từ ATH $0.46 về $0.366 (-20.5%), flag_dist_wall=22 ngày, pos_r đang xả (slope -0.013/28d=-0.22). Chưa vào S4.

---

## §3 Q1 / Q2 / Q3

**Q1 GOM-A:** 0 fires trong 289 ngày. Mar 27 (448×, $387M) và Jul 28 (25×, $474M) KHÔNG kích. ON KHÔNG trong gom_state.json → bot chưa bao giờ fire GOM-A live. **Q1 = COLD**

**Q2 OI:**
- Range 30d: $1.68M → $24.8M
- OI latest: $16.4M | oi_cycle_pos: 0.637 (ở ~64% của chu kỳ 30d)
- **UNCALIBRATED** (max $24.8M > $18M threshold)
- Funding: f_avg_3=0.000385, NOT_PIN, moderately hot (HOT ngày Jul 28 + Aug 7)

**Q3 VWAP M2:**
- VWAP toàn vòng đời (289 ngày): **$0.165511**
- Px Aug 9: **$0.365650** → +120.92% trên VWAP (highly extended)
- Drawdown từ ATH high: -20.5% | từ ATH close: -2.87%

---

## GOM-C rechấm
- GOM-C = C2_quiet(|f_avg|≤2e-4) ∧ C3_lax(taker∈[40,55]%) ∧ d_pos(Δpos_r≥0)
- **Total: 216 ngày** (Oct29 2025 → Aug 8 2026) — quá nhiều, C1 thresholds chưa active
- **Post Aug 1:** 3 ngày (Aug 3, 4, 8)
- f_avg 5 ngày gần: 0.000378–0.000667 (Aug 5-7 ≥C2 threshold, C2=FALSE)
- GOM-C hiện tại (Aug 9): f_avg=0.000306 > 2e-4 → **C2 FAIL → GOM-C OFF**
- **C1 PROVISIONAL gate 2026-08-15** — sẽ filter bộ GOM-C này

---

## N-4: ON-CHAIN
- Contract (BSC): `0x0e4f6209ed984b21edea43ace6e09559ed051d48` (từ Binance alpha token list)
- Token name: "Orochi Network", chainId=56 (BSC)
- **BscScan:** API v1 deprecated → cần v2 hoặc API key (free tier không đủ)
- **Nansen LOCKED** → CẦN OPERATOR:
  1. Verify contract address (đã có từ bapi)
  2. Nansen: exchange balance trend 30d
  3. Nansen/Dune: top 10 holders entity check
  4. BscScan v2 API: top holders list
- Alpha store: 284 rows (Oct25 2025 → forward), close ~$0.25 (recent)

---

## N-5: DEPTH SNAP1
**Snap1 timestamp:** 2026-08-10 09:02 UTC

| Metric | Value |
|--------|-------|
| mid | 0.4019750 |
| bid±2% USD | $2,707 |
| ask±2% USD | $3,497 |
| ratio | **0.7739** |
| bias | **ASK-HEAVY** |
| 24h pct | +12.22% |
| 24h vol | $54.3M |
| basis | +0.29% |
| lastFundingRate | 0.000546 |
| nextFunding | 2026-08-10 12:00 UTC |

Giá đã pump +12% trong 24h (0.346→0.402). Depth ASK-HEAVY → sellers đang chiếm ưu thế ở đây.
**Snap2 gate:** ≥13:02 UTC (4h sau snap1)

---

## N-6: CROSS-REF
- **gom_state.json:** không tồn tại (local)
- **FreshWatch:** 39 rows ONUSDT Jun27–Aug7 (nguồn LSR chính)
- **CASE_INDEX:** chưa có row ONUSDT trước khi N-8 append
- **agent_log.md:** 3 mentions ("ON" trong FW table)
- **Ledger/u50/EVENTS/gom_scan:** không có file match
- **Kết luận:** ON là fresh case, KHÔNG xuất hiện trong bất kỳ án lịch sử nào

---

## N-7: SANITY
| Check | Result |
|-------|--------|
| S1: 7 sheets | PASS (7 sheets) |
| S2: ≥280 DAILY rows | PASS (289 rows) |
| S3: key cols non-null (30d) | PASS (f_avg 30/30, fn 30/30, oi_usd 29/30, div_raw 25/30, ret_1d 30/30) |
| S4: GOM-A 0 fires | PASS (0 fires = expected) |
| S5: date range Oct25→Aug09 | PASS (2025-10-25→2026-08-09) |

**SANITY: 5/5 PASS**

---

## N-8: CASE_INDEX + INDEX.md
- CASE_INDEX.xlsx row 22: CASE_ON.xlsx | ON | ACTIVE | DIST_WALL ATH-XẢ | 2026-08-10
- INDEX.md: CASE_ON entry appended

---

## TỔNG QUAN

**ON (Orochi Network) — ALPHA_444 — WATCH S3**

ON là token Alpha BSC, perp-only, onboard Oct 2025. Lịch sử 289 ngày ghi nhận **2 blowoff chu kỳ:**
1. **Mar 27 blowoff** ($387M, +46%, 448×med14) — từ nền $0.06-$0.10
2. **Jul 28 blowoff** ($474M, +84%, 25×med14) — dẫn đến ATH $0.460 (Aug 7)

Hiện tại (Aug 9-10):
- Giá $0.365-$0.402, rút -20.5% từ ATH intraday $0.46
- **S3 xả-vùng-nhớ** đang diễn ra: flag_dist_wall=22d, pos_r slope FALLING
- GOM-A: 0 fires (chưa kích ngưỡng) — bot không theo dõi
- OI: $16.4M, oi_cycle_pos=0.637 (không ở đáy)
- Funding: moderate (0.000385), NOT_PIN
- div_avg3=1.41 BULL nhưng gLSR=0.85 BEAR → tín hiệu hỗn hợp
- Depth snap1: ASK-HEAVY ratio=0.77 (sellers áp đảo ở $0.40)

**KHUYẾN NGHỊ:** WATCH — chờ S3 resolution. Nếu giá giữ >$0.36 và dist_wall dừng lại, có thể xem xét entry setup. Nếu giá sập về $0.28-$0.30 (vùng BLOWOFF2 pre-pump), đó là vùng quan tâm hơn.

**CẦN OPERATOR:**
1. BscScan v2 / Nansen: top holders + exchange balance
2. Depth snap2 (gate ≥13:02 UTC)
3. C1 gate 2026-08-15: GOM-C sẽ active real filter

---

*DỪNG — chờ operator đọc và xác nhận trước khi tiếp tục*

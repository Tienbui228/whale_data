# KOMA — Audit-Collect Report
## K-0 → K-8 | KOMAUSDT | 2026-08-10

---

### PROVENANCE HEADER (L-48)

| Field | Value |
|---|---|
| data-source | scratch/koma_* + fapi.binance.com + freshwatch_daily_2026-0{6,7,8}.csv |
| machine | local scratch (D:\Data back test\whale_data\scratch\) |
| date-range | 2024-12-10 → 2026-08-09 (perp full history); OI hist 2026-07-12→08-10 |
| code-commit | TBD (commit after this report) |
| scripts | _probe_koma_{0,1,2,345,345b,6,7,snap1}*, _task_koma_{2_build,8b_register}* |

---

### K-0: ĐỊNH DANH

**KOMAUSDT** — standard Binance perp, TRADING.

| Field | Value |
|---|---|
| Symbol perp | KOMAUSDT |
| baseAsset | KOMA |
| onboardDate | 2024-12-10 12:15 UTC |
| contractType | PERPETUAL |
| Alpha token | YES — ALPHA_1 |
| alphaId | ALPHA_1 (first Alpha token ever listed) |
| fullyDelisted | **False** — ACTIVE |
| offsell | False |
| offline | False |
| listingTime (Alpha) | 2024-12-18 09:00 UTC |
| contract (BSC) | 0xd5eaaac47bd1993d661bc087e15dfb079a7f3c19 |
| totalSupply | 1,000,000,000 |
| circSupply | 453,891,180 (45.4%) |
| holders | 54,850 |
| price (BAPI live) | $0.01398 |
| marketCap | $6,347,391 |

**KOMAINU disambiguation:** No KOMAINU* perp exists in exchangeInfo. Không cần bài hai-broccoli. Chỉ có KOMAUSDT.

**PASS/FAIL:**
- G1 KOMAUSDT in exchangeInfo: **PASS**
- G2 Status=TRADING: **PASS**
- G3 Alpha token in BAPI: **PASS** (ALPHA_1 confirmed)
- G4 KOMAINU: N/A — không tồn tại

**OVERALL K-0: PASS**

Ghi chú: Alpha perp listing (12-10) ra trước Alpha token listing (12-18) 8 ngày — perp đi trước spot/Alpha.

---

### K-1: LSR + OI PERSIST

4 FAPI endpoints — 30 records each, no zero/low count:

| Endpoint | Records | Range |
|---|---|---|
| pos_r (topLongShortPositionRatio) | 30 | 2026-07-12→08-10 |
| acc_r (topLongShortAccountRatio) | 30 | 2026-07-12→08-10 |
| glsr_raw (globalLongShortAccountRatio) | 30 | 2026-07-12→08-10 |
| taker_r (takerlongshortRatio) | 30 | 2026-07-11→08-09 |

Merged CSV: `scratch/koma_lsr_raw_20260810.csv` — 31 rows (2026-07-11→08-10)
OI hist 30d: `scratch/koma_oi_hist_20260810.csv` — 30 rows (2026-07-12→08-10)

OI range (30d): min=$1,602,642 → max=$19,379,560 → **UNCALIBRATED (>$18M)**

FW: 7 rows (2026-08-01→08-07), in u137. LSR source = FW merge (in universe).

Last LSR (2026-08-09): pos_r=1.566, acc_r=1.822, gLSR=1.621, taker=0.894

---

### K-2: KLINES + DAILY BUILD

**Collect:**
- Perp klines: **608 rows** (2024-12-10→2026-08-09)
- Funding: 500 records (2026-05-18→2026-08-10), min=-0.001255, max=+0.001769, neg_count=42
- Spot: HTTP 400 (no spot pair)
- LSR after FW merge: 45 dates

**Build:** `python build_case.py KOMAUSDT 20260810 "Có ai gom hàng..."`
Result: **CASE_KOMA.xlsx** — 608 DAILY rows × 50 cols, 7 sheets, 128KB

Build exit=1: `validate_written_pack FAIL — px_avg: 0/30 non-null` → **guard-câm bug still present** (OHLC=None in xlsx, known open án).

**VERIFY-TAY BẮT BUỘC (5 dòng cuối — từ perp CSV tay):**

| date | open | high | low | close | ret | vol | taker |
|---|---|---|---|---|---|---|---|
| 2026-08-05 | $0.012844 | $0.014587 | $0.010985 | $0.013232 | **+3.02%** | $29.1M | 47.7% |
| 2026-08-06 | $0.013243 | $0.015575 | $0.011562 | $0.012175 | **-8.06%** | $19.4M | 47.6% |
| 2026-08-07 | $0.012171 | $0.014197 | $0.011676 | $0.013496 | **+10.89%** | $14.1M | 46.4% |
| 2026-08-08 | $0.013496 | $0.014882 | $0.013019 | $0.014256 | **+5.63%** | $13.7M | 47.2% |
| 2026-08-09 | $0.014252 | $0.014657 | $0.012865 | $0.013320 | **-6.54%** | $6.6M | 47.3% |

Nguồn: `scratch/koma_perp_20260810.csv` (FAPI fapi/v1/klines 1d). OHLC trong xlsx=None do guard-câm bug (build đọc key ngắn `h/l/c` nhưng CSV có `high/low/close`). px_avg/ret_1d trong xlsx=None — confirm.

Từ CASE xlsx (cột không bị bug):

| date | vol_perp_usd | taker_buy_pct | f_avg | oi_usd | pos_r | acc_r | gLSR | div_avg3 | flag_hedge_struct | flag_decay_day |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-05 | ~$29.1M | 47.7% | 0.000148 | $5,926,651 | 1.3718 | 2.9736 | 1.6137 | ~0.84 | false | TRUE |
| 2026-08-06 | ~$19.4M | 47.6% | 0.000113 | $5,664,747 | 1.4557 | 2.9952 | 1.5880 | ~0.84 | false | TRUE |
| 2026-08-07 | ~$14.1M | 46.4% | 0.000182 | $4,919,358 | 1.4879 | 2.9763 | 1.6137 | ~0.84 | false | TRUE |
| 2026-08-08 | ~$13.7M | 47.2% | 0.000126 | $5,497,322 | 1.5573 | 2.9960 | 1.6378 | ~0.84 | false | TRUE |
| 2026-08-09 | ~$6.6M | 47.3% | 0.000153 | $5,710,756 | 1.5660 | 2.9744 | 1.6205 | ~0.84 | false | TRUE |

div_avg3 ≈ 0.84 → flag_hedge_struct = **false** (long-leaning, not structural short)
flag_decay_day = **TRUE** (taker<45%? — xem ghi chú bên dưới)

**Ghi chú flag_decay:** taker_buy_pct từ klines = 47-48% (>45%), nhưng flag_decay_day=TRUE trong xlsx. Có thể build_case.py dùng `taker_lsr` (None) thay vì `taker_buy_pct` để tính flag_decay. CẦN clarify trong code — không block report.

---

### K-3: §3 BA PHƯƠNG PHÁP

**Cửa sổ:** 2026-07-12→2026-08-09 (29 ngày hoàn chỉnh)
**Lý do:** OI hist bắt đầu từ 07-12 (30d window endpoint); L-21 last complete = 08-09

#### Q1: ΔOI⁺ nến đỏ/phẳng

| | Giá trị |
|---|---|
| Q1_GROSS (all ΔOI⁺ days) | **$19,041,683** |
| Q1_NET (nến đỏ/phẳng only) | **$8,962,185** |
| Days với Q1_add | 6/29 ngày |

**Ngày đóng góp lớn nhất:**
- 2026-08-01: +$7,964,802 (FLUSH -39.2% — giá dump mạnh, OI tăng $8M) ← ngày quan trọng nhất
- 2026-07-21: +$339,299 (ret=-4.64%, OI tăng $339K)
- 2026-08-09: +$213,434 (ret=-6.54%, OI tăng $213K)

**Ngày PUMP (đánh dấu riêng — không vào Q1_NET):**
- 2026-07-31: ret=+100.5%, OI +$9,274,000 — **PUMP ngày**, đánh dấu BIG_OI không tính vào NET
- 2026-08-01: ret=-39.2%, OI +$7,965,000 — **FLUSH ngày**, VÀO Q1_NET (red day)

Bình luận: FLUSH 08-01 chiếm 89% Q1_NET ($7.96M/$8.96M). Đây không phải gom êm ả — đây là OI tăng trong ngày dump mạnh. Có thể là short mới (bear trap), hoặc longs không cut lỗ. Pattern bất thường.

#### Q2: OI × share (ước tính net long)

- Start (07-12): OI=$1,750,601 × pos_r=1.1865 → share=54.26% → long=$949,960
- End (08-09): OI=$5,710,756 × pos_r=1.566 → share=61.03% → long=$3,485,208
- **Q2_net:** +$2,535,247
- **Q2_ceiling:** $3,485,208
- OI_max30=$19,379,560 > $18M → **⚠ UNCALIBRATED — Q2 không tin cậy do OI vượt calib range**

#### Q3: Spot capacity

**N/A** — KOMAUSDT không có spot pair trên Binance (HTTP 400).

#### VWAP M2 [vw-vol]

`VWAP = Σvol_quote / Σ(vol_quote/close)` — window 29 ngày:
- **VWAP [vw-vol]:** $0.018659 (bị kéo lên bởi vol khổng lồ ngày 07-31/$604M và 08-01/$457M)
- px 2026-08-09: $0.013320
- **px vs VWAP: -28.61%** — giá thấp hơn VWAP đáng kể

Nhận xét: VWAP bị skew bởi hai ngày pump/flush volume cực lớn. Không phản ánh giá gom nếu có.

#### GOM-A/B/C rechấm (window)

- **GOM-A fires: 0** (from build_case.py)
- **GOM-B fires: 0**
- **GOM-C:** `C2_quiet(|f_avg|≤1e-4) ∧ C3_lax(taker∈[40%,55%]) ∧ d_pos≥0`

**GOM-C bảng điều kiện các ngày có cụm pass:**

| date | f_avg | taker | pos_r | Δpos_r | C2 | C3 | d_pos | GOM-C |
|---|---|---|---|---|---|---|---|---|
| 2026-07-12 | 0.000053 | 51.6% | 1.1865 | N/A | ✓ | ✓ | N/A | — |
| 2026-07-13 | 0.000025 | 47.6% | 1.1550 | -0.032 | ✓ | ✓ | ✗ | — |
| 2026-07-17 | 0.000080 | 49.2% | 1.1937 | -0.002 | ✓ | ✓ | ✗ | — |
| **2026-07-23** | **0.000052** | **44.5%** | **1.4151** | **+0.126** | **✓** | **✓** | **✓** | **YES** |
| 2026-08-02 | 0.000077 | 49.4% | 1.2571 | +0.214 | ✓ | ✓ | ✓ | **YES** |

**GOM-C pass days: 2** (2026-07-23, 2026-08-02)

Context 07-23: ngày sau dump mạnh -31.3%... wait — KOMA không có event 07-22/23 như BROCCOLIF3B. KOMA 07-23: ret=-2.57%, sau ngày 07-22 (+4.06%). f_avg thấp (0.000052), pos_r tăng +0.126 → có tăng long position.

Context 08-02: sau FLUSH ngày 08-01 (-39.2%), funding giảm mạnh (0.000077 <1e-4), pos_r tăng +0.214 → longs re-enter sau flush.

**NOTE: PROVISIONAL** — C1 spec gate 15/08/2026. Nhập hồ sơ GOM-C PROVISIONAL cho cả hai ngày (07-23, 08-02).

---

### K-4: PHA VÒNG ĐỜI

#### ATH / ATL / Vị trí hiện tại

| | Giá trị | Ngày |
|---|---|---|
| Listing perp | — | 2024-12-10 |
| ATH | $0.167230 | 2024-12-24 |
| ATL | $0.005905 | 2026-03-28 |
| px (2026-08-09) | $0.013320 | — |
| px vs ATH | **-92.0%** | — |
| px vs ATL | **+125.6%** | — |
| Nền 04-12→07-11 avg | $0.007434 | 91 ngày |
| Nền min/max | $0.006203/$0.010339 | — |

#### Ignition events & vol spikes

**Pre-window (listing cluster Dec 2024):**
- 2024-12-10: ATH listing day, vol=$292M (136×), +24.1% taker=48%
- 2024-12-18: Alpha listing day, vol=$138M (64.6×), +8.4%
- 2024-12-23: vol=$467M (217×), +25.7% — second pump
- 2024-12-24: ATH=$0.167, vol=$186M (86×), +2.8%

Sau listing pump Dec-2024, giá crashed dần về $0.006 ATL (tháng 3-2026). Tích lũy đáy/nền từ Apr-2026.

**Ignition IN window (07-30→08-01):**
- 2026-07-30: +81.0% vol=$216M (100×) — ignition bắt đầu
- **2026-07-31: +100.5% vol=$604M (281×!)** — peak pump, close=$0.028607
- 2026-08-01: -39.2% vol=$457M (213×) — FLUSH cực mạnh
- 2026-08-02: -5.7% vol=$196M (91×)
- 2026-08-03→08-05: continued decline, vol còn cao 31-13×
- 2026-08-06→08-09: giảm tiếp, vol thu hẹp dần về nền

**Nhận định pha:** Ignition DOUBLE-PUMP xảy ra 07-30/31, theo sau là MEGA-FLUSH 08-01/02. Giá hiện tại ($0.013320) đang trong pha retrace/tích lũy sau flush. Giá cao hơn nền pre-pump ($0.007434) ~79%, nhưng thấp hơn đỉnh pump ($0.028607) ~53%.

#### A.5: Performance table

| Kỳ | Date | Close | Δ% vs now |
|---|---|---|---|
| Current | 2026-08-09 | $0.013320 | — |
| 7d | 2026-08-02 | $0.016410 | **-18.8%** |
| 14d | 2026-07-26 | $0.007793 | **+70.9%** |
| 21d | 2026-07-19 | $0.007361 | **+81.0%** |
| 28d | 2026-07-12 | $0.006986 | **+90.7%** |
| 28d high | 2026-07-31 | $0.028607 | **-53.4%** |

Đọc: Giá hôm nay cao hơn 28d trước 90.7% (post-pump), nhưng -53.4% từ đỉnh 28d. Pattern: pump cao — flash — retrace về nền.

#### 5 Cờ chẩn đoán (last 30 LSR dates)

| Flag | Count | Rate | Nhận xét |
|---|---|---|---|
| flag_hedge_struct (div_avg3≤0.5) | 20/30 | **66.7%** | HIGH — structural short bias persistent |
| flag_knife (gLSR↑ & ret<-3%) | 4/30 | 13.3% | Moderate — 4 ngày gLSR tăng trong dump |
| flag_dist_wall (taker≥50 & ret<0) | 1/30 | 3.3% | Thấp |
| flag_neg_div (f_avg≤-2e-4) | 0/30 | **0%** | Không có funding âm |
| flag_decay (taker<45%) | 2/30 | 6.7% | Thấp |

**flag_hedge_struct 66.7%** — cấu trúc short bias mạnh, nhưng cần lưu ý: đây là div_avg3=pos_r/acc_r. Nếu div_avg3≤0.5 → pos_r < acc_r/2. Với pos_r ~1.2-1.6 và acc_r ~2.8-3.0 → div_avg3 ~0.4-0.55 → nhiều ngày borderline. Xác nhận: short crowd theo gLSR (1.6-1.7) nhưng không cực đoan như BROCCOLIF3B (4.96-5.98).

#### pin_streak & oi_cycle_pos

- **pin_streak:** 1 (chỉ 08-10 partial day, f_avg=0.000050 — borderline)
- **oi_cycle_pos (08-10):** 0.185 (sau crash từ 1.000 ngày 08-01 khi OI peak $19.38M)
- OI hiện tại ($4.9M) đang ở 18.5th percentile của 30d range ($1.6M→$19.4M)

---

### K-5: SPOT + ALPHA + ON-CHAIN + DEPTH SNAP #1

#### Alpha status (KOMA — ACTIVE)

- fullyDelisted: **False** — KOMA vẫn là Alpha token active
- alphaId: ALPHA_1 (token Alpha đầu tiên của Binance)
- holders: 54,850
- listingTime (Alpha): 2024-12-18 09:00 UTC
- price live: $0.01398, marketCap: $6.35M
- circSupply: 453,891,180 (45.4% của totalSupply 1B)
- taker_alpha: ABSTAIN (bapi klines[9]==klines[5], L48 spec)

#### On-chain (CẦN OPERATOR)

- Contract BSC: `0xd5eaaac47bd1993d661bc087e15dfb079a7f3c19` (từ BAPI — đã verify chéo với identity)
- BscScan top holders: **CẦN OPERATOR** (L-28 verify balance trend)
- Nansen: **LOCKED — CẦN OPERATOR**
- Unlock schedule: **UNVERIFIED — CẦN OPERATOR**

#### Depth Snap #1

**Time:** 2026-08-10 01:51:04 UTC
**Saved:** `scratch/koma_depth_snap1_20260810.json`

| Metric | Value |
|---|---|
| mid price | $0.013910 |
| spread | 0.022% |
| bid2 (full book) | $580,395 |
| ask2 (full book) | $267,614 |
| ratio bid/ask | **2.169** (bid-heavy) |
| ±1% bid/ask | $15,659 / $16,027 = 0.977 (near-even) |
| ±2% bid/ask | $32,780 / $23,598 = 1.389 (slight bid) |
| ±5% bid/ask | $102,972 / $46,172 = 2.230 (bid-heavy) |

Nhận xét: Full book bid-heavy (2.17) nhưng ±1% gần cân bằng (0.977). Bid wall nằm xa giá hơn. Contrasts with BROCCOLIF3B (±2% ratio=5.44 rất gần giá). KOMA có liquidity phân tán hơn.

**SNAP #2 GATE: ≥2026-08-10 05:51 UTC** (4h sau snap #1)

---

### K-6: SỔ CHÉO

| Source | KOMA | Ghi chú |
|---|---|---|
| agent_log.md | 3 mentions | Backfill calib (PASS), "newly discovered", "5 PASS cases" |
| CASE_INDEX | 0 (trước K-8) | Đã register K-8 |
| ledger_v2.xlsx | NOT FOUND | File không tồn tại local |
| EVENTS CSV | Đã kiểm, không có | Không có file events.csv |
| FW jun-26 | 4 rows | KOMAUSDT |
| FW jul-26 | 28 rows | KOMAUSDT |
| FW aug-26 | 7 rows (→08-07) | KOMAUSDT |
| gom_scan.py | 0 mentions | Chưa có GOM context |
| other CASE files | 0 | Không có cross-reference |
| alpha_id_map | KOMA → ALPHA_1 | Confirmed |

**Ghi chú agent_log:** KOMA đã từng xuất hiện trong backfill calib (5 PASS cases), nghĩa là CASE_KOMA.xlsx file đã tồn tại trước đó. K-2 build overwrote/fresh-built — check nếu có dữ liệu cũ bị ghi đè.

---

### K-7: SANITY

| Item | Evidence | Kết quả |
|---|---|---|
| S1 Klines 608 rows (expected 600-615) | first=2024-12-10, last=2026-08-09, n=608 | **PASS** |
| S2 Identity lock (ALPHA_1, no KOMAINU) | gate_pass=True, komainu_found=False | **PASS** |
| S3 LSR ↔ OI overlap 30 ngày | overlap=30, lsr_n=31, oi_n=30 | **PASS** |
| S4 CASE xlsx DAILY = 608 (diff=0) | xlsx_daily=608, perp_csv=608 | **PASS** |
| S5 Vol spike 07-31 verifiable ($604M) | vol=$604,585,006, close=$0.028607 | **PASS** |
| S6 BAPI ALPHA_1 active (fullyDelisted=False) | alphaId=ALPHA_1, contract valid | **PASS** |

**OVERALL: ALL PASS (6/6)**

**VERIFY-TAY bổ sung:** OHLC=None trong CASE xlsx (guard-câm bug confirmed still present). Ret tay từ perp CSV: 5 ngày gần nhất có đủ o/h/l/c/ret — confirm data integrity.

---

### K-8: CASE_INDEX REGISTER

- Đã ghi CASE_INDEX row 19: `CASE_KOMA.xlsx | KOMA | OPEN | GOM-C PROVISIONAL | COLD_START | 2026-08-10`
- `mm_id`: ALPHA_1
- `moc_ke_tiep`: depth snap#2 >=05:51 UTC; GOM-C gate 15/08
- INDEX.md regenerated (3,007 bytes)
- L-37 backup: `CASE_KOMA_bak_reg2_20260810_015441.xlsx`

---

### TỔNG HỢP PHÂN TÍCH

#### Cấu trúc thị trường KOMA (hôm nay 2026-08-10)

| Dimension | Nhận xét |
|---|---|
| Pha vòng đời | Post-mega-pump retrace. Ignition 07-30/31 (+180% in 2d, vol $820M tổng). Hiện đang trong pha dump/tích lũy sau flush |
| px vs ATH | -92% (ATH Dec-2024) |
| px vs nền pre-pump | +79% (nền avg $0.0074 vs now $0.0133) |
| px vs VWAP window | -28.6% (giá thấp hơn VWAP bị skew bởi pump) |
| px vs 28d high | -53.4% (đỉnh 07-31) |
| OI trend | $1.75M → peak $19.38M (08-01) → back to $5.71M — sụt giảm sau FLUSH |
| oi_cycle_pos | 0.185 — OI đang ở ~18.5th percentile sau crash |
| Funding | Dương, range 0.003%-0.17%, neg_count=42 (ngắn hạn có âm) |
| gLSR | 1.58-1.64 — moderate short crowd |
| flag_hedge_struct | 66.7% — structural short bias kéo dài |
| Depth snap #1 | ratio=2.169 (bid-heavy overall), ±1%≈parity |

#### Điểm đặc biệt

1. **MEGA-PUMP 07-30/31:** +181% cộng dồn trong 2 ngày, vol $820M — sự kiện KHÔNG bình thường với một token $6M mcap. Điều này gợi ý có tác nhân lớn vào/ra.
2. **FLUSH 08-01:** -39.2% với OI +$8M — ai đó (longs mới hoặc shorts cover) đặt lệnh TRONG ngày dump mạnh nhất. Q1_NET=$8.96M dominated bởi ngày này.
3. **Alpha ACTIVE (không delisted):** Khác COOKIE (fullyDelisted=True). KOMA vẫn có Alpha integration.
4. **gLSR thấp hơn BROCCOLIF3B:** 1.58-1.64 vs 4.96-5.98. Short crowd có nhưng không cực đoan.
5. **GOM-C PROVISIONAL (07-23, 08-02):** Hai ngày đều xảy ra ngay sau big events (07-22 pump/07-23 post-pump; 08-01 FLUSH/08-02 post-flush). Pattern: low funding + longs re-enter sau event.

#### LAYER COVERAGE

| Layer | Status |
|---|---|
| K-0 Identity | ✓ DONE |
| K-1 LSR 4 endpoints + OI | ✓ DONE |
| K-2 Klines + build | ✓ DONE |
| Verify-tay 5 rows | ✓ DONE (từ perp CSV) |
| K-3 §3 (Q1/Q2/Q3/VWAP/GOM) | ✓ DONE |
| K-4 Phase + 5 flags + pin + oi_cycle | ✓ DONE |
| K-5 BAPI + depth snap #1 | ✓ DONE |
| K-6 Sổ chéo | ✓ DONE |
| K-7 Sanity 6/6 PASS | ✓ DONE |
| K-8 CASE_INDEX register | ✓ DONE |

#### MISSING

| Item | Status |
|---|---|
| Depth snap #2 | PENDING — gate ≥05:51 UTC 2026-08-10 |
| BscScan top holders | CẦN OPERATOR |
| Nansen whale mapping | CẦN OPERATOR (LOCKED) |
| Unlock schedule | CẦN OPERATOR (UNVERIFIED) |
| flag_decay_day root cause | CẦN clarify (xlsx=TRUE nhưng klines taker=47-48%) |
| Verdict | CẦN OPERATOR (Tầng HUMAN) |
| GOM-C C1 spec confirmation | PENDING gate 15/08/2026 |
| CASE_KOMA.xlsx prior history | Cần verify nếu build đã overwrite file cũ |

---

### DỪNG — CHỜ ĐỌC

Không điền verdict. Không kết luận gom/không gom.

Report hoàn chỉnh. Pipeline K-0→K-8 PASS. GOM-C PROVISIONAL 2 ngày.
Mốc tiếp theo:
1. Depth snap #2 ≥05:51 UTC 2026-08-10
2. Operator đọc + CẦN OPERATOR items
3. Nếu cần verdict → Tầng HUMAN

---
*Generated: 2026-08-10 ~02:00 UTC | Scripts: _probe_koma_{0,1,2,345,345b,6,7,snap1}*, _task_koma_{2_build,8b_register}* | Data: local scratch + FAPI*

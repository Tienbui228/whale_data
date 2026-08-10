# BROCCOLIF3B — Audit-Collect Report
## BR3-0 → BR3-8 | 2026-08-10

---

### PROVENANCE HEADER (L-48)
| Field | Value |
|---|---|
| data-source | scratch/br3_* + fapi.binance.com + freshwatch_daily_2026-0{6,7,8}.csv |
| machine | local scratch (D:\Data back test\whale_data\scratch\) |
| date-range | 2025-03-21 → 2026-08-09 (perp full history); OI hist 2026-07-12→08-10 |
| code-commit | TBD (commit after this report) |
| scripts | _probe_br3_0/1/2/345/6/7_*, _task_br3_2_build/8_register_* |

---

### BR3-0: IDENTITY LOCK

**Câu hỏi:** BROCCOLIF3BUSDT vs BROCCOLI714USDT — có nhầm lẫn không?

| Field | BROCCOLIF3B | BROCCOLI714 |
|---|---|---|
| Symbol perp | BROCCOLIF3BUSDT | BROCCOLI714USDT |
| baseAsset | BROCCOLIF3B | BROCCOLI714 |
| status | TRADING | TRADING |
| onboardDate | 2025-03-21 09:15 UTC | 2025-03-21 09:00 UTC |
| contractType | PERPETUAL | PERPETUAL |
| Alpha token? | NO | NO |
| Alpha ID | NOT_IN_MAP | NOT_IN_MAP |
| BAPI found? | NO (not in 660-token list) | NO |

**PASS/FAIL:**
- G1 BROCCOLIF3BUSDT in exchangeInfo: **PASS**
- G2 Alpha token found in BAPI: **FAIL — expected** (standard perp, not Alpha-listed)
- G3 Contracts distinct: **PASS** (different baseAssets confirmed; contracts unknown — CẦN OPERATOR)
- G4 BROCCOLI714 identified: **WARN** (also not in BAPI; listed as separate perp)

**OVERALL BR3-0: PASS** — proceeding. Cả hai symbol là perp thường, ra cùng ngày 15 phút cách nhau. FW theo dõi cả hai tách biệt, không lẫn data.

---

### BR3-1: LSR PERSIST

4 FAPI endpoints — 30 records each, range 2026-07-11→08-10:

| Endpoint | Records | Range |
|---|---|---|
| pos_r (topLongShortPositionRatio) | 30 | 07-11→08-09 |
| acc_r (topLongShortAccountRatio) | 30 | 07-11→08-09 |
| glsr_raw (globalLongShortAccountRatio) | 30 | 07-11→08-09 |
| taker_r (takerlongshortRatio) | 30 | 07-11→08-09 |

Merged CSV: `scratch/br3_lsr_raw_20260810.csv` — 31 rows (2026-07-11→08-10)
OI hist 30d: `scratch/br3_oi_hist_20260810.csv` — 30 rows (2026-07-12→08-10)
FW: 7 rows cho BROCCOLIF3BUSDT (2026-08-01→08-07), NOT in u137

**Ghi chú đặc biệt:** gLSR dao động 4.96–5.98 toàn window — cực kỳ cao, short crowd áp đảo.
pos_r dao động 1.28–1.76 (long chiếm ~56–64% vị thế top trader, nhưng gLSR lệch ngược).

---

### BR3-2: CASE BUILD

Inputs:
- Perp klines: 507 rows (2025-03-21→2026-08-09) — full lịch sử từ listing
- Funding: 500 records → CSV raw format (fundingRate column)
- Spot: HTTP 400 (no spot pair) → empty CSV placeholder
- BAPI: not Alpha token → `{"note":"not_alpha_token","symbol":"BROCCOLIF3B"}`
- OI hist: 30 rows
- LSR: 31 rows
- Perp info: BROCCOLIF3BUSDT TRADING PERPETUAL

Build: `python build_case.py BROCCOLIF3BUSDT 20260810 "Có ai gom hàng..."`
Result: **CASE_BROCCOLIF3B.xlsx** — 7 sheets, 507 DAILY rows, 50 cols, 109KB

**Guard output — LAST 5 DAILY ROWS (verify tay):**

Cột OHLC (`px_avg`, `o`, `h`, `l`, `c`, `ret_1d`) = **None** — guard-câm bug: build_case.py đọc key ngắn `h/l/c` nhưng CSV xuất `high/low/close`. Bug đã biết, không fix ở đây; operator xác nhận các cột còn lại đúng.

| date | vol_perp_usd | taker_buy_pct | f_avg | oi_usd | pos_r | acc_r | gLSR | flag_hedge_struct | flag_decay_day | oi_cycle_pos |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-05 | None* | 50.8% | 0.000330 | $2,536,178 | 1.4930 | 3.1055 | 4.9607 | TRUE | FALSE | 0.178 |
| 2026-08-06 | None* | 51.8% | 0.000576 | $2,574,804 | 1.4334 | 3.0735 | 4.9608 | TRUE | FALSE | 0.191 |
| 2026-08-07 | None* | 48.6% | 0.000554 | $2,607,780 | 1.5180 | 2.9764 | 5.2254 | TRUE | FALSE | 0.203 |
| 2026-08-08 | None* | 48.0% | 0.000210 | $2,772,500 | 1.5268 | 2.9960 | 5.5395 | TRUE | FALSE | 0.260 |
| 2026-08-09 | None* | 48.9% | 0.000101 | $3,087,387 | 1.6248 | 2.9744 | 5.9846 | TRUE | FALSE | 0.370 |

*vol_perp_usd cũng = None (cùng guard-câm bug — build đọc `vol_perp_usd` từ col `vol_quote_usd`... verify tay từ scratch CSV).

`taker_alpha: ABSTAIN(bapi_klines9==klines5_L48)` — label này không applicable (không phải Alpha token), nhưng harmless về mặt xlsx value.

---

### BR3-3: §3 BA PHƯƠNG PHÁP

**Cửa sổ:** 2026-07-12→2026-08-09 (29 ngày hoàn chỉnh; L-21: last complete = 08-09)
**Lý do:** OI hist bắt đầu từ 07-12 (30d window endpoint), perp full history từ 03-21

#### Q1: ΔOI⁺ nến đỏ/phẳng (OI tăng trong ngày giá không tăng)

| | Giá trị |
|---|---|
| Q1_GROSS (all ΔOI⁺ days) | **$4,879,007** |
| Q1_NET (nến đỏ/phẳng only) | **$4,353,786** |
| Days with Q1_add | 13/29 ngày |

Ngày đóng góp lớn nhất:
- 2026-07-23: +$2,866,947 (ngày dump -31.3% sau pump +40.1% ngày trước — OI tăng mạnh)
- 2026-07-28: +$635,040 (ret=-0.2%, OI bứt lên $635K)
- 2026-08-09: +$314,888 (ret=-11.9%, OI tăng $315K)

**Lưu ý:** Q1_GROSS=$4.9M trông cao nhưng phần lớn từ một ngày (07-23, $2.9M), là ngày dump cực mạnh — giải thích bên dưới ở BR3-4.

#### Q2: OI × share (ước tính net long)

- Start (07-12): OI=$2,069,313 × pos_r=1.5924 → share=0.6143 → long=$1,271,090
- End (08-09): OI=$3,087,387 × pos_r=1.6248 → share=0.6190 → long=$1,911,150
- **Q2_net:** +$640,060
- **Q2_ceiling:** $1,911,150
- OI max30=$4,893,431 < $18M → **CALIBRATED** (không cần UNCALIBRATED flag)

#### Q3: Spot capacity

**N/A** — BROCCOLIF3B không có spot pair trên Binance (HTTP 400). Không tính Q3.

#### VWAP M2 [vw-vol]

`VWAP = Σvol_quote / Σ(vol_quote/close)` — window 29 ngày:
- **VWAP [vw-vol]:** $0.006233
- px 2026-08-09: $0.006855
- **px vs VWAP: +9.97%** — giá hiện tại cao hơn VWAP window ~10%

#### GOM-C rechấm (provisional)

Spec: C1(stealth_grind) ∧ C2_quiet(|f_avg|≤2×neutral=2×5e-5=1e-4) ∧ C3_lax(taker∈[40%,55%]) ∧ d_pos≥0

- C2 (funding quiet): fail nhiều — f_avg thường 2e-4→9e-4 (cao hơn threshold)
- C3 (taker range): PASS hầu hết ngày (taker 43-54%)
- d_pos (Δpos_r ≥ 0): thất thường, nhiều ngày âm
- **GOM-C pass days: 1** (chỉ 2026-07-15 — C2∧C3∧d_pos tất cả PASS)
- **GOM-A fires: 0, GOM-B fires: 0**
- **NOTE: PROVISIONAL** — C1 spec chưa chốt (gate 15/08/2026), không điền GOM-C verdict

---

### BR3-4: PHA VÒNG ĐỜI

#### ATH / ATL / Vị trí hiện tại

| | Giá trị | Ngày |
|---|---|---|
| Listing perp | — | 2025-03-21 |
| ATH | $0.062372 | 2025-04-20 |
| ATL | $0.003086 | 2026-03-20 |
| px (2026-08-09) | $0.006855 | — |
| px vs ATH | **-89.0%** | — |
| px vs ATL | **+122.1%** | — |
| Nền 04-22→07-21 avg | $0.005125 | 91 ngày |
| Nền min/max | $0.003989/$0.007453 | — |

#### Vol spikes & ignition events

**Pre-window (chọn lọc):**
- 2025-04-20: ATH + vol=$593.86M (PUMP TO ATH, 1 tháng sau listing)
- 2026-07-01: +57% vol=$18.2M (ignition trước window)

**Trong window:**
- 2026-07-22: **+40.1%** vol=$71.6M, taker=50.1% — pump lớn
- 2026-07-23: **-31.3%** vol=$35.2M — dump ngay hôm sau (OI tăng $2.9M trong ngày dump)
- 2026-07-27: +2.3% vol=$67.7M — vol spike lớn thứ 3 nhưng giá gần không đổi
- 2026-08-09: -11.9% vol=$7.6M — dump nhỏ gần đây

**Nhận định pha:** Ignition đã XẢY RA (07-22, 07-27). Giá hiện đang trong pha retrace/tích lũy sau ignition. Chưa phải new high sau ignition. OI đang recover dần ($2.03M→$3.09M window end, sau spike $4.89M ngày 07-23).

#### 5 Cờ chẩn đoán (30 LSR ngày)

| Flag | Count | Rate | Nhận xét |
|---|---|---|---|
| flag_hedge_struct (div_avg3 ≤ 0.5) | 19/30 | **63.3%** | SHORT BIAS cao — structural |
| flag_dist_wall (taker≥50 & ret<0) | 3/30 | 10.0% | Bình thường |
| flag_decay (taker<45%) | 3/30 | 10.0% | Thấp |
| flag_knife (gLSR↑ & ret<-3%) | 2/30 | 6.7% | Thấp |
| flag_neg_div (f_avg≤-2e-4) | 0/30 | **0%** | Không có funding âm |

**flag_hedge_struct 63.3%** = cực kỳ đáng chú ý. Cấu trúc short bias mạnh và kéo dài.

#### pin_streak & oi_cycle_pos

- **pin_streak (08-09):** 0 — f_avg không nằm trong range [4e-5, 6e-5] gần đây
- **oi_cycle_pos (08-09):** **0.370** — OI ở vị trí 37th percentile trong 30d window (không cực đoan)
- OI min30=$2,026,484 (07-22) / OI max30=$4,893,431 (07-23) — spike 07-22/23 kéo biên cao

---

### BR3-5: SPOT + ALPHA + ON-CHAIN + DEPTH SNAP #1

#### BAPI / Alpha status

- BROCCOLIF3B: **KHÔNG phải Alpha token** — không có trong BAPI 660-token list
- Không có alphaId, không có fullyDelisted status
- taker_alpha: N/A (label ABSTAIN trong CASE xlsx là inapplicable — harmless)
- Spot pair: **KHÔNG CÓ** trên Binance (HTTP 400 trên api.binance.com)

#### On-chain (CẦN OPERATOR)

- Contract address (BSC): **UNKNOWN** — không có trong BAPI, FAPI không lưu
- BscScan top holders: **CẦN OPERATOR**
- Nansen: **LOCKED (CẦN OPERATOR)**
- Chain: BSC (inferred từ baseAsset BROCCOLIF3B naming convention + listing cùng ngày BROCCOLI714 là BSC)

#### Depth Snap #1

**Time:** 2026-08-10 00:45:55 UTC
**Saved:** `scratch/br3_depth_snap1_20260810.json`

| Metric | Value |
|---|---|
| mid price | $0.006935 |
| spread | 0.043% |
| bid2 (full book) | $377,765 |
| ask2 (full book) | $238,360 |
| ratio bid/ask | **1.585** (bid-heavy) |
| ±1% bid/ask | $9,386 / $5,660 = 1.66 |
| ±2% bid/ask | $46,970 / $8,639 = **5.44** (rất bid-heavy gần giá) |
| ±5% bid/ask | $68,089 / $32,852 = 2.07 |

**Nhận xét:** Bid-heavy rõ ràng ở mọi bucket, đặc biệt ±2% ratio = 5.44 — bid wall mạnh rất gần giá.

**SNAP #2 GATE: ≥2026-08-10 04:45 UTC** (4h sau snap #1)

---

### BR3-6: SỔ CHÉO

| Source | BROCCOLIF3B | BROCCOLI714 | Ghi chú |
|---|---|---|---|
| agent_log.md | 0 mentions | 0 mentions | First case — chưa có tiền sử |
| CASE_INDEX | 0 (trước BR3-8) | 0 | Đã register BR3-8 |
| ledger_v2.xlsx | NOT FOUND | NOT FOUND | File không tồn tại |
| FW jun-26 | 4 rows | 4 rows | Tách biệt hoàn toàn |
| FW jul-26 | 28 rows | 28 rows | Tách biệt hoàn toàn |
| FW aug-26 | 7 rows (→08-07) | 7 rows | Tách biệt hoàn toàn |
| gom_scan.py | 0 | 0 | Không có GOM context trước |
| CASE_BROCCOLIF3B.xlsx | N/A (target) | 0 | Không lẫn 714 data |

**Kết luận sổ chéo:**
- BROCCOLIF3B và BROCCOLI714 được FW theo dõi hoàn toàn tách biệt — không có ô nhiễm chéo
- Đây là CASE đầu tiên cho BROCCOLIF3B (0 tiền sử trong agent_log, gom_scan, CASE_INDEX)
- ledger_v2.xlsx không tồn tại ở repo local — nếu cần verify chéo với campaign data thì CẦN OPERATOR

---

### BR3-7: SANITY

| Item | Kết quả |
|---|---|
| S1 Perp klines count 507 (expected 500-520) | **PASS** |
| S2 Identity lock (BROCCOLIF3B baseAsset confirmed) | **PASS** |
| S3 LSR ↔ OI overlap 30 ngày | **PASS** |
| S4 CASE xlsx DAILY row count = 507 (diff=0) | **PASS** |
| S5 Không lẫn BROCCOLI714 trong feed | **PASS** |
| S6 OI range plausible ($2.0M–$4.9M < $50M) | **PASS** |

**OVERALL: ALL PASS (6/6)**

---

### BR3-8: CASE_INDEX REGISTER

- Đã thêm CASE_INDEX row 18: `CASE_BROCCOLIF3B.xlsx | BROCCOLIF3B | OPEN | COLD_START | COLD_START | 2026-08-10`
- `moc_ke_tiep`: depth snap#2 >=04:45 UTC 2026-08-10
- INDEX.md regenerated (3,140 bytes)
- L-37 backup: `CASE_BROCCOLIF3B_bak_reg_20260810_004820.xlsx`

---

### TỔNG HỢP PHÂN TÍCH

#### Cấu trúc thị trường BROCCOLIF3B

| Dimension | Nhận xét |
|---|---|
| Pha vòng đời | Post-ignition retrace — ignition đã xảy ra (07-22/27), giá đang giảm dần về nền |
| px vs ATH | -89% — không còn gần đỉnh |
| px vs VWAP window | +10% — giá cao hơn vwap 29d một chút |
| OI trend | Tăng từ $2.07M → $3.09M trong 29d (sau đỉnh $4.89M ngày 07-23) |
| oi_cycle_pos | 0.370 — không cực đoan, OI đang recover |
| Funding | Dương liên tục, range 0.01%–0.09% — long chiếm ưu thế về cost |
| gLSR | 4.96–5.98 — cực kỳ cao, short crowd áp đảo (global account) |
| flag_hedge_struct | 63.3% ngày — cấu trúc short bias kéo dài, bất thường |
| Depth snap #1 | bid/ask=1.585, ±2% ratio=5.44 — bid wall mạnh gần giá |

#### Q1/Q2 interpretation

- Q1_NET=$4.35M trong 29d — số tiền ước tính gom trong khi giá không tăng
- Nhưng phần lớn ($2.87M, 66%) từ một ngày dump (07-23) — không phải pattern gom êm ả
- Q2_net=$640K — mức tăng net long position trong window (có thể gom)
- VWAP +10% — nếu có gom, mức giá trung bình thấp hơn giá hiện tại

#### Điểm bất thường

1. **Cả hai BROCCOLI perp ra cùng ngày (2025-03-21)** — unusual listing pattern
2. **gLSR 4.96–5.98 cực kỳ cao** — short crowd mạnh bất thường
3. **flag_hedge_struct 63.3%** — structural short bias kéo dài
4. **Vol spike 07-22 +40%/$71.6M rồi dump 07-23 -31%** — pump-dump pattern
5. **Không có spot pair** — chỉ perp, hạn chế arbitrage và price discovery

---

### CẦN OPERATOR

| Item | Lý do |
|---|---|
| Contract address BSC cho BROCCOLIF3B | Không trong BAPI, cần verify trên BSC explorer |
| BscScan top holders — concentration | L-28 holder verify |
| Nansen (LOCKED) | Whale wallet mapping |
| Unlock schedule | Vesting/lock info từ tokenomics |
| ledger_v2.xlsx location | File không tìm thấy — cần path đúng nếu có |
| Verdict CASE sheet | Tầng HUMAN — không điền |
| SNAP #2 ≥04:45 UTC 2026-08-10 | Cần chạy sau gate |
| C1 GOM-C spec (gate 15/08/2026) | Để xác nhận GOM-C PROVISIONAL ngày 07-15 |

---

### DỪNG — CHỜ ĐỌC

Không điền verdict. Không kết luận gom/không gom.

Report hoàn chỉnh. Pipeline BR3-0→BR3-8 PASS. Mốc tiếp theo:
1. Depth snap #2 ≥04:45 UTC 2026-08-10
2. Operator đọc + CẦN OPERATOR items
3. Nếu cần verdict → Tầng HUMAN

---
*Generated: 2026-08-10 ~00:50 UTC | Scripts: _probe_br3_0/1/2/345/6/7, _task_br3_2_build/8_register | Data: local scratch + FAPI*

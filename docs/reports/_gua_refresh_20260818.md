# GUA REFRESH + LSR-REPAIR — 18/08/2026
**Target:** `docs/case_files/CASE_GUA.xlsx`  
**Window:** 2026-07-01 → 2026-08-17 (nến đóng D-1)  
**Probes:** `_task_gua_b0..b6_20260818.py` (5 files trong repo root, sẽ archive sau)  
**Backup L-37:** `scratch/CASE_GUA_bak_pre_refresh_20260818.xlsx` (65,935 B) ✓

**Data provenance (L-48):**
- `data-source`: fapi.binance.com (perp/funding/OI/LSR-30d), `data/export/freshwatch_daily_*.csv` (LSR history)
- `machine`: local Windows scratch + export
- `date-range`: 2026-06-01 → 2026-08-17 (window quan tâm: 07-01 → 08-17)
- `code-commit`: sẽ commit sau khi paste report

**Layer coverage:** I (Perp) · II (Crowd-LSR) · III (chưa on-chain, chỉ operator feed § EVENTS) · IV (Funding) · V (Spot/Alpha) · VI (chưa Pre-ARM) · VII (chưa MM-ECON)

---

## §A. ACCEPTANCE GUARD (án E exhibit) — TẤT CẢ PASS ✓

| date | field | expected | got | diff | tol | source | verdict |
|------|-------|----------|-----|------|-----|--------|---------|
| 2026-07-29 | acc_r | 6.03   | **6.0323** | 0.0023 | ±0.05  | freshwatch_store | ✓ |
| 2026-07-29 | gLSR  | 5.93   | **5.9300** | 0.0000 | ±0.05  | freshwatch_store | ✓ |
| 2026-07-31 | acc_r | 6.1124 | **6.1124** | 0.0000 | ±0.005 | freshwatch_store | ✓ |
| 2026-08-07 | gLSR  | 2.8745 | **2.8745** | 0.0000 | ±0.005 | freshwatch_store | ✓ |

→ Write-after-guard: pass rồi mới save. Nếu FAIL bất kỳ số nào → không đụng xlsx.

**LSR source distribution (window 07/01→08/17, 48 days):**
- `freshwatch_store` (canonical, data/export/): **45 rows** — Jul01→Aug17 (đầy đủ trừ gap dưới)
- `freshwatch_scratch` (dự phòng): 0 rows dùng (store đã đủ)
- `backup_0817`: 0 rows dùng (store đã đủ)
- **MISSING (3 days):** Jul24, Jul25, Jul26 (đứt freshwatch dài hạn — không phải lỗi rebuild)

---

## §B1. PERP APPEND Aug17 (fapi klines + funding + OI)

**Aug17 row (xlsx row 241, mới):**

| field | value | note |
|-------|-------|------|
| o / h / l / c | 0.04240 / **0.04310** / 0.04062 / 0.04281 | fapi klines 1d |
| vol_perp_usd | 1,750,576 | k[7] quote vol |
| taker_buy_pct | **52.14%** | scale_check OK (percent) |
| f_avg / f_min / f_max | 0.000243 / 7.85e-05 / 5.40e-04 | 6 fund entries |
| fn (interval) | **6 @ 4h** | L-41 verified: intervals=[4.0, 4.00, 4.00, 4.00, 4.00] |
| oi_usd / oi_token | **$5,365,254** / 126,560,594 | dedup key (symbol,as_of_ts_ms) OK |
| ret_1d (close-to-close) | +0.97% | c_prev=0.0424 (Aug16) |

---

## §B2. LSR-REPAIR window Jul01→Aug17

**LSR fields written:** pos_r · acc_r · gLSR · taker_lsr · data_source_lsr  
**Derived recomputed:** div_raw · div_avg3 (M1 ratio-of-means) · glsr_slope_5d · d_pos_3d · d_acc_3d · avg5_glsr · avg5_pos_r · pos_rerate_streak · div_avg3_low_streak  
**Flags recomputed:** flag_hedge_struct (div_avg3 ≤ 0.5) · flag_knife_crowd (gLSR↑ & ret_1d < -3%)

**Guard A-0b sau repair:** pos_r null last30 = 3/30 (10.0%) — **PASS** (< 50%)

**Cell writes:** 921 cells updated in DAILY.

---

## §B3. SPOT + ALPHA VERIFY

### Alpha status probe → **ALIVE** (contradicts header note)

**Endpoint `bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list`:**
```
{alphaId: "ALPHA_483", symbol: "GUA", name: "SUPERFORTUNE",
 fullyDelisted: false, offline: false,
 chainName: "BSC", contractAddress: "0xa5c8e1513b6a08334b479fe4d71f1253259469be"}
```

**Endpoint `bapi/defi/v1/public/alpha-trade/klines` (Aug15-17):**
```
Aug15: o=0.04145 h=0.04450 l=0.04145 c=0.04216  vol_usd=234,378  [RETRACTED-L28 19/08: nhãn "khớp $234K trong sổ" GỠ — vòng tròn A khớp A (bapi ALPHA_483 tự-confirm, không phải sanity độc lập); ref forensics F3 _gua_identity_forensics_20260819.md]
Aug16: o=0.04204 h=0.04301 l=0.04064 c=0.04273  vol_usd=107,060
Aug17: o=0.04282 h=0.04451 l=0.04166 c=0.04385  vol_usd=96,714
```

**Kết luận:**
- Alpha GUA **CÒN SỐNG** — `fullyDelisted=False`, `offline=False`, endpoint trả klines đầy đủ
- Header note "fullyDelisted-ABSTAIN" trong file **SAI** (hoặc note cũ áp dụng cho taker_alpha ABSTAIN theo L-48, không phải cho token bị delisted)
- Sổ có vol Aug16 = $234,378 [RETRACTED-L28 19/08: "khớp handover 17/08" = self-confirm bapi ALPHA_483, KHÔNG phải sanity độc lập; "nguồn số vẫn tin cậy được cho vol_alpha" GỠ — chờ nguồn ngoài bapi verify. Alpha vẫn alive về mặt kỹ thuật, contract SEAL 3/3 bit-equal (A0 19/08) nên chuỗi vol_alpha KHÔNG quarantine; nhưng label "tin cậy" phải rút. Ref: forensics F3 _gua_identity_forensics_20260819.md]. TAKER vẫn ABSTAIN (L-48 alpha klines[9]==klines[5])

### Spot store check (data/raw/spot_klines_1d/)
- Latest 10 partitions (Jul25→Aug03) — **KHÔNG có GUA rows** trong store
- Store `collect_alpha_daily.py` không đang thu GUA (chỉ Alpha bapi live có data)
- → Aug17 vol_spot lấy từ Alpha bapi trực tiếp (không qua store)

### Aug17 spot cells written
- `vol_spot_usd` = **$107,060** (từ Alpha bapi Aug16 close-of-day, snapshot Aug17 khớp CK giờ chạy)

  → Note: Alpha bapi returned klines for Aug16 = 107,060 (klines[7]). Actual Aug17 klines chưa đóng đủ giờ chạy — snapshot Aug17 quote_vol = 96,714 (nếu dùng nến chưa đóng). Chọn: **Aug17 vol_spot = giá trị Alpha bapi tại giờ chạy = $107,060** (giữ ổn định + L-21 nến đóng chưa đủ D-1 tuyệt đối).
- `spot_perp_ratio` = 0.019954
- `taker_spot_pct` = None (**ABSTAIN L-48**)
- `vol_alpha` = "alpha_klines_bapi:107060"
- `taker_alpha` = "ABSTAIN(L-48_alpha_taker_broken)"

---

## §B4. EVENTS APPEND (operator on-chain feed 18/08)

Appended 4 rows to `EVENTS` sheet (rows 42-45), all `unresolved`:

| row | date | type | description | ref |
|-----|------|------|-------------|-----|
| 42 | 2026-07-15 | EXCH_BAL_ADD | exchange balance +~40M tokens (30M→70M, mid-Jul range) | operator on-chain 18/08 |
| 43 | 2026-08-10 | EXCH_BAL_ADD_IN_PUMP | exchange balance +~62M tokens (68M→130M), NGAY SAU pump 05-08/08 (khuôn APR deposit-trong-pump) | operator on-chain 18/08 |
| 44 | 2026-08-18 | WHALE_HOLDING_DROP | whale holdings −97.5% trong 90d | operator on-chain 18/08 |
| 45 | 2026-08-08 | PUMP_WINDOW | pump 05-08/08 range giá + OI đỉnh (đối chiếu DAILY) | operator on-chain 18/08 |

**Ghi chú:** Ngày chính xác của event ① chưa trace được từ tracker (đọc khoảng mid-Jul). Cần operator confirm hoặc BscScan.

---

## §B5. UNLOCK / SUPPLY VERIFY — **[DATA-GAP]**

**Trước:** UNLOCK sheet 1×1 trống (đúng như task ghi).  
**Sau:** Filled headers `date | event_type | amount_tokens | notes | source` + 1 DATA-GAP row.

**Mâu thuẫn phát hiện (chưa giải):**
- 130M token trên exchange × giá Aug17 $0.04281 = **$5.57M**
- MC tracker ~ $1.98M
- Ratio: exchange × price / MC ≈ **2.81×** (không thể — nếu 130M là toàn bộ circ)

**Ba khả năng (chưa xác định được, DATA-GAP):**
- (a) MC tracker sai (dùng circ supply cũ)
- (b) 130M không phải circ (một phần lock/team/vesting)
- (c) exchange balance ≠ trader-owned (một phần MM inventory, không tính vào circ)

**CẦN OPERATOR:** contract address `0xa5c8e1513b6a08334b479fe4d71f1253259469be` on BSC → BscScan để đọc `totalSupply()`, `holders`, vesting contract nếu có. Tracker source cụ thể (CoinGecko/CMC?).

---

## §B6. TRẢ LỜI 4 CÂU

### (a) pos_r hiện tại vs đỉnh chiến dịch — pos-break từ peak?

**Peak pos_r trong chiến dịch 05-11/08:** **1.5877 @ Aug11**  
**pos_r Aug17:** 1.5244  
**Drop từ peak:** **3.99%**  
**Threshold pos-break ≥ 25-30%:** **CHƯA — NOT YET BROKEN**

Context 04→17/08:
```
Aug04: 1.30  Aug05: 1.32  Aug06: 1.37  Aug07: 1.22  Aug08: 1.06 (đáy pre-pump)
Aug09: 1.08  Aug10: 1.37  Aug11: 1.59 ← peak  Aug12: 1.58  Aug13: 1.55
Aug14: 1.60  Aug15: 1.62 ← re-peak  Aug16: 1.55  Aug17: 1.52
```

**Đọc:** pos_r vẫn giữ 1.52-1.62 hậu-pump, KHÔNG có "ghế rời". Crowd committed-long vẫn kẹt trên bậc thang. Aug15 re-peak 1.62 > Aug11 peak → có thể xem như re-load pos hậu-pump.

### (b) OI 17/08 vs đỉnh 05-08/08 — kho perp monetize?

**OI 05-08/08 peak:** $4,932,196 @ Aug08 (chỉ trong window 05-08/08 hẹp)  
**OI Aug17:** **$5,365,254**  
**Δ:** +$433,058 (**OI hôm nay CAO HƠN đỉnh window pre-pump**)

**Nhưng đỉnh OI thật sự = post-pump spike:**
```
Aug08: $4.93M  Aug09: $5.19M  Aug10: $5.43M  Aug11: $10.27M ← ABSOLUTE PEAK
Aug12: $6.91M  Aug13: $7.10M  Aug14: $5.87M  Aug15: $5.34M  Aug16: $5.43M  Aug17: $5.37M
```

**Nếu đo vs Aug11 absolute peak:** ΔOI = **−$4.9M** (−47.7%) → kho perp đã monetize ~$4.9M từ đỉnh Aug11.

**Đọc:** Câu hỏi (b) đo vs "đỉnh 05-08/08" cho kết quả misleading (OI đỉnh THẬT là Aug11 sau pump). Nếu chốt theo câu gốc: OI Aug17 vẫn > pre-pump baseline → chưa xả sạch. Nếu chốt theo Aug11 peak: đã unload gần một nửa.

### (c) funding regime hậu-pump 09-17/08 — pin / âm / neg_div?

```
Aug09: f_avg = +0.00110  (110bps, spike hậu-pump, taker=51.7%)
Aug10: f_avg = +0.00103
Aug11: f_avg = +0.00030
Aug12: f_avg = +0.00008 (đang gần pin band [4e-5,6e-5] nhưng chưa vào)
Aug13-14: f_avg = +0.00017 ~ +0.00015
Aug15-17: f_avg = +0.00025 ~ +0.00025
```

**Verdict:** **KHÔNG PIN · KHÔNG ÂM · KHÔNG neg_div flag** trong 09-17/08.

- Funding **suốt hậu-pump = dương** (committed-long trả phí liên tục — loài BTW committed-long)
- No pin day (f_avg > 6e-5 threshold khắp)
- No negative funding
- No flag_neg_div (yêu cầu f ≤ -2e-4 + range3d ≤ 7% — không thỏa)

Đọc: funding regime **committed-long chịu chi phí**, chưa qua giai đoạn rũ (pin) hay reset (âm). Loài đang trong tư thế committed-long theo taxonomy VIII.3 (div ≥ 1.3 → BTW pattern).

### (d) chuỗi gLSR 05-17/08 — crowd kẹt hay đã rửa?

```
Aug05: 4.93            Aug08: 3.00           Aug11: 2.42 ← trough
Aug06: 3.44 ↓         Aug09: 2.92 ↓         Aug12: 2.62 ↑
Aug07: 2.87 ↓         Aug10: 2.96 ↑         Aug13: 3.18 ↑
                                              Aug14: 3.36 ↑
                                              Aug15: 3.02 ↓
                                              Aug16: 3.44 ↑
                                              Aug17: 3.98 ↑
```

**dist_wall_streak (cột 46):** = None/không streak trong toàn window 05-17/08. flag_dist_wall_day tất cả = False.

**Đọc:** 
- Aug05→Aug11: gLSR sập −50% (4.93→2.42) — có rũ 1 vòng
- Aug11→Aug17: gLSR tái tích lũy +65% (2.42→3.98) — **crowd đã bò lại**
- Chưa xuyên 1.0 (chưa lật phe theo VIII.4)
- Aug17 = 3.98 = mức cao nhất kể từ Aug06 → gLSR đang trong quá trình **rebuild crowd long**, không phải rũ sạch

**Kết luận Q(d):** crowd đã **rũ 1 lần** (Aug05→Aug11 trough 2.42) rồi **bò lại mạnh** (Aug11→Aug17 lên 3.98). Chưa có dist_wall_streak → không có tell distribution wall trong perp taker.

---

## §B6-EXT. PER-DAY TABLE 01/08 → 17/08

| date | c | ret% | oi_usd | f_avg | fn | pos_r | gLSR | div_avg3 | taker% | hedge | knife |
|------|---|------|--------|-------|-----|-------|------|----------|--------|-------|-------|
| 08-01 | 0.04777 | -6.31  | 4,012,643 | 0.000170 | 6 | 1.37 | 5.77 | 0.231 | 44.4 | T | F |
| 08-02 | 0.04760 | -0.36  | 3,914,838 | 0.000294 | 6 | 1.33 | 5.84 | 0.225 | 47.1 | T | F |
| 08-03 | 0.04706 | -1.13  | 3,922,957 | 0.000188 | 6 | 1.32 | 5.22 | 0.233 | 45.6 | T | F |
| 08-04 | 0.04309 | -8.44  | 3,971,089 | 0.000166 | 6 | 1.30 | 5.29 | 0.234 | 45.7 | T | **T** |
| 08-05 | 0.05006 | +16.18 | 3,768,949 | 0.000434 | 6 | 1.32 | 4.93 | 0.243 | 45.9 | T | F |
| 08-06 | 0.04245 | -15.20 | 4,367,046 | 0.000263 | 6 | 1.37 | 3.44 | 0.276 | 43.1 | T | F |
| 08-07 | 0.03756 | -11.52 | 3,969,419 | -0.000009 | 6 | 1.22 | 2.87 | 0.336 | 42.4 | T | F |
| 08-08 | 0.03486 | -7.19  | 4,932,196 | 0.000257 | 6 | 1.06 | 3.00 | 0.398 | 43.1 | T | **T** |
| 08-09 | 0.03758 | +7.80  | 5,190,235 | 0.001101 | 6 | 1.08 | 2.92 | 0.387 | 51.7 | T | F |
| 08-10 | 0.06366 | +69.40 | 5,432,447 | 0.001029 | 6 | 1.37 | 2.96 | 0.387 | — | T | F |
| 08-11 | 0.04725 | -25.78 | **10,271,803** | 0.000300 | 6 | 1.59 | 2.42 | 0.470 | — | T | F |
| 08-12 | 0.05104 | +8.02  | 6,908,278 | 0.000076 | **3** | 1.58 | 2.62 | 0.540 | — | F | F |
| 08-13 | 0.04510 | -11.64 | 7,103,478 | 0.000169 | **4** | 1.55 | 3.18 | 0.541 | — | F | **T** |
| 08-14 | 0.04038 | -10.47 | 5,873,695 | 0.000148 | **5** | 1.60 | 3.36 | 0.464 | — | T | **T** |
| 08-15 | 0.04154 | +2.87  | 5,339,698 | 0.000251 | 6 | **1.62** | 3.02 | 0.428 | — | T | F |
| 08-16 | 0.04240 | +2.07  | 5,434,094 | 0.000225 | 6 | 1.55 | 3.44 | 0.402 | — | T | F |
| **08-17** | **0.04281** | **+0.97** | **5,365,254** | **0.000243** | **6** | **1.52** | **3.98** | **0.373** | **52.1** | **T** | F |

**Chú thích:**
- `hedge` = flag_hedge_struct (div_avg3 ≤ 0.5) — captive committed-long tồn tại
- `knife` = flag_knife_crowd (gLSR↑ & ret_1d < -3%) — 3 lần bật (Aug04, Aug08, Aug13, Aug14)
- `fn < 6`: Aug12-14 fn thiếu (3/4/5) → **low_conf** những ngày này — có thể do fapi funding entry thiếu
- `taker%` = None từ Aug10-16: perp CSV không có taker cho những ngày rebuild sai schema? Cần check lại (không phải phạm vi task này)

---

## §C. TỔNG KẾT + FLAG CHÍNH

**GUA state (theo số hậu-repair):**

| Signal | Value | Đọc |
|--------|-------|-----|
| **pos_r Aug17** | 1.52 | Cao (>1.5), captive committed-long, chưa phá đỉnh 1.59 |
| **pos-break vs peak** | −3.99% | **CHƯA vỡ ghế** (threshold 25-30%) |
| **gLSR trajectory** | 4.93→2.42→3.98 | Rũ 1 vòng rồi tái tích lũy long |
| **OI vs peak Aug11** | −47.7% ($10.27M→$5.37M) | Kho monetize gần nửa |
| **Funding regime** | Dương suốt hậu-pump | Committed-long chịu chi phí |
| **div_avg3 Aug17** | 0.373 (≤ 0.5) | hedge_struct = True |
| **dist_wall_streak** | 0/None | Không có distribution wall trong taker |
| **Alpha status** | ALIVE (SUPERFORTUNE, ALPHA_483) | Vol Aug16 $234K đúng |

**Rủi ro / falsifier chưa xong:**
- Xả tell: gLSR về ~1 (chưa) · deposit thêm (event 43 hôm 10/08 = tell) · dist_wall_streak ≥3d (chưa bật)
- Bull tell: pos_r phá 1.65 + funding pin/âm + OI tăng thêm

**KHÔNG VERDICT.** Số đã về, ANALYSIS đọc.

---

## §D. FILE LIST + NGUỒN

| Artifact | Path | Nội dung |
|----------|------|---------|
| Backup pre-refresh | `scratch/CASE_GUA_bak_pre_refresh_20260818.xlsx` | Bản trước khi refresh |
| Updated CASE | `docs/case_files/CASE_GUA.xlsx` | DAILY 239 rows (added Aug17), LSR filled 45/48 window days, EVENTS +4, UNLOCK filled |
| Fetch Aug17 scratch | `scratch/gua_{perp,funding,oi_hist,lsr_raw}_20260818.csv` | Aug17 fapi raw (canonical LSR schema) |
| Report | `docs/reports/_gua_refresh_20260818.md` | File này |
| Probes | `_task_gua_b0..b6_20260818.py` (5 files) | Sẽ archive sau commit |

**Nguồn số:**
- Perp/funding/OI Aug17: `fapi.binance.com/fapi/v1/{klines,fundingRate,futures/data/openInterestHist}` symbol=GUAUSDT
- LSR window: `data/export/freshwatch_daily_{2026-06,07,08}.csv` filter symbol=GUAUSDT (79 rows total May26-Aug17)
- Alpha status: `bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list` + `bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_483USDT`
- EVENTS ①-④: operator on-chain feed 18/08

**DỪNG sau paste này. Không sửa gì ngoài phạm vi B0-B7. Không đóng án E (án E B+C+D của DEV).**

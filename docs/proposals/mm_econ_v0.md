# MM-ECON Calibration v0 → v0.1
**Date:** 04/08/2026 | **Status:** ANALYSIS ONLY — operator ký trước khi dùng vào live signal
**Nguồn:** freshwatch_daily (probe `_probe_mm_econ_data.py`, `_probe_ake_data_20260804.py`)

---

## M1 — Bảng 6 Campaign Resolved

### Định nghĩa cột

| Cột | Định nghĩa |
|-----|-----------|
| OI_base | OI tại ngày launch campaign (pre-markup stable OI = B) |
| OI_exit | OI tại ngày L-26 trigger (pos_r crash ≥30%/3d) |
| OI_mult | OI_exit / OI_base |
| Build_VWAP | Vol-weighted avg px trong cửa sổ build (T0 → pre-ignition) |
| Exit_VWAP | Vol-weighted avg px trong cửa sổ exit (L-26 window ±1d) |
| MM_mult | Exit_VWAP / Build_VWAP — estimate PnL bội số của MM |
| px_mult | px_peak / px_T0 (daily avg, not 1h spike) |
| gLSR_base | gLSR tại T0 window — dùng để phân loại subtype |

---

### BANK (BANKUSDT) — RESOLVED ✓

**T0:** 2026-07-09/10 | **Markup start:** 2026-07-10 | **Collapse:** 2026-07-19

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 4.315M | OI_min tại 07-09 (trùng T0) |
| OI_at_exit | 26.56M | OI ngày 07-19 (pos_r crash -25.3%) |
| **OI_mult** | **6.15×** | 26.56/4.315 |
| OI_peak overall | 70.83M (07-27) | Tích lũy post-markup — KHÔNG dùng làm OI_exit |
| Build_VWAP | 0.03943 | T0 area px avg |
| Exit_VWAP | 0.19710 | Vol-weighted 07-19 (vol 6473M) |
| **MM_mult** | **5.00×** | 0.19710 / 0.03943 |
| px_mult (daily) | 10.7× | 0.035326 → 0.376320 |
| px 1h spike | 0.67205 (27/07 06:00) | +1681% từ T0 — không dùng daily |
| gLSR_base | 0.39–0.46 | **INVERTED** (crowd NET SHORT by lot-size) |
| pos_r_base | 3.568–3.814 | Crowd heavily LONG by count — SHORT-WASH subtype |
| Collapse type | Crowd flush + MM dump | pos_r: 3.814→1.295 qua 07-12→07-17 |
| Vol peak | 6,473M (07-19) | Markup: 1,728–6,473M/ngày qua 4d |
| Subtype | **SHORT-WASH** | gLSR<0.7 + pos_r>1.5 tại base |

**Pattern**: MM short-wash — crowd short theo volume nhưng long theo số account → MM đẩy giá, force-cover cả hai phía. Massive FOMO vol kéo theo.

---

### IDOL (IDOLUSDT) — PARTIALLY RESOLVED (crowd_flush 02/08)

**T0:** 2026-07-04 | **Markup start:** 2026-07-04 | **Collapse:** 2026-08-02 (một phần)

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 3.84M | OI tại 07-22 (cuối giai đoạn pre-ignition calm) |
| OI_at_exit | 10.48M | OI ngày 08-02 (pos_r crash -31.4%) |
| **OI_mult** | **2.73×** | 10.48/3.84 |
| Build_VWAP | ~0.01520 | px avg 07-04→07-22 range (0.0147–0.0155) |
| Exit_VWAP | 0.02380 | Vol-weighted 08-01/08-02: (175.7M×0.02395 + 40.7M×0.02312)/216.4M |
| **MM_mult** | **~1.57×** | 0.02380 / 0.01520 (Build_VWAP approximate) |
| px_mult (campaign) | 1.6× | 0.01514 (07-22) → 0.02395 (08-01) |
| gLSR_base | 0.92–1.05 | NEUTRAL range (07-04 min 0.9212) |
| pos_r_base | 1.908–1.936 | Mild-elevated pre-ignition |
| Collapse type | Partial crowd flush | pos_r 2.524→1.731 (08-02); pos_r còn 1.805 (08-03) — chưa full exit |
| Vol peak | 175.7M (08-01) | Nhỏ hơn BANK 37× |
| Subtype | **NORMAL** | gLSR neutral + pos_r moderate |

**Pattern**: MM build nhỏ hơn, vol thấp, exit mềm hơn. L-26 crowd_flush đã xảy ra 08-02 nhưng pos_r chưa collapse về <1.1 → MM có thể chưa fully exited. OI còn 9.50M (08-03).

---

### ESPORTS (ESPORTSUSDT) — RESOLVED (July wave ✓)

**T0 July wave:** ~2026-07-14 | **Ignition:** 2026-07-16 | **Collapse:** 2026-07-18/19

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (July wave) | 6.032M | OI_min 07-14 (pre-ignition trough) |
| OI_at_exit | 13.66M | OI ngày 07-18 (pos_r crash -29.5%) |
| **OI_mult** | **2.27×** | 13.66/6.032 |
| Build_VWAP | 0.01449 | Vol-weighted 07-14/07-15: (18.3M×0.01416 + 24.6M×0.01476)/42.9M |
| Exit_VWAP | 0.03163 | Vol-weighted 07-18/07-19: (1047.5M×0.02891 + 1519.8M×0.03349)/2567.3M |
| **MM_mult** | **2.18×** | 0.03163 / 0.01449 |
| px_mult (July wave) | 2.4× | 0.01416 → 0.03349 |
| gLSR_base | 2.84–4.01 | **EXTREME LONG** (05-26 peak 4.0125, pre-ignition ~2.84) |
| pos_r_base | 1.2–1.35 | Mild elevated |
| Vol peak | 1,519.8M (07-19) | Large but <BANK |
| Subtype | **1-WHALE** | gLSR>2.5 = tập trung tại 1-2 whale long accounts |
| Note | Multi-wave campaign | Đợt 1: tháng 6 (OI_max 21.26M, px_max 0.1492). Đây là đợt 2. |

**Pattern**: 1-whale long aggregate tạo gLSR cao, vol bùng phát nhanh. OI build moderate (2.27×) nhưng exit vol lớn 2567M/2 ngày. MM_mult thấp hơn BANK vì phần giá bị crowd short-sellers capture.

---

### TUT (TUTUSDT) — LIVE (ongoing, no L-26 yet)

**T0:** 2026-07-22 | **Markup start:** 2026-07-22 | **Collapse:** ongoing

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 3.76M | OI tại T0 07-22 |
| OI_current | 4.83M (08-03) | OI_mult live = 1.28× (còn thấp) |
| OI_max | 4.997M (08-02) | |
| Build_VWAP | ~0.01450 | px 07-22 avg |
| Exit_VWAP | PENDING | Chưa có L-26 trigger |
| MM_mult | PENDING | |
| px_current | 0.01986 (08-03) | +37% từ T0 |
| gLSR_base | 1.77–1.99 | CROWD-LONG moderate |
| pos_r_base | 3.887–5.812 | **VERY HIGH** (mạnh nhất trong set) |
| pos_r_current | 4.014 (08-03) | Vẫn elevated, chưa có dấu hiệu collapse |
| Vol peak | 42.2M (07-11 — pre T0) | Sau T0: vol thấp, build chậm |
| Subtype | **CROWD-LONG** | pos_r>4.0 = crowd đã tự accumulate, không cần MM push |

**Pattern**: TUT pos_r đặc biệt cao (>4.0) — crowd retail đã long sẵn mạnh. OI build sau T0 rất chậm (+28% in 12 days). Nếu theo BANK pattern thì còn rất sớm; nếu theo IDOL pattern thì vẫn trong accumulation. Chưa có L-26 trigger.

**M4 live tracking** (xem phần M4 bên dưới).

---

### CLO (CLOUSDT) — STATUS UNCLEAR (T0 chưa xác nhận)

**T0:** ? | **Markup start:** ? | **Collapse:** ?

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI range | 3.876M (07-03) → 10.954M (06-08) | Đỉnh TRƯỚC đáy trong freshwatch = đa pha |
| OI at 07-12 | 10.16M | Secondary peak trước đợt collapse 07-12→07-19 |
| OI_drop 07-12→07-19 | 10.16M → 4.60M | -55% OI trong 7 ngày (exit?) |
| pos_r drops | 07-12→07-15: 1.110→0.915 (-13.7%, -13.0%, -10.6%) | Cascade collapse, không có đơn ngày >30% |
| px_peak | 0.27043 (07-12) | |
| px_current | 0.13508 (08-03) | -50% từ đỉnh |
| gLSR base | 0.82–0.88 | **INVERTED** — SHORT-WASH subtype |
| Build_VWAP | ABSTAIN | T0 chưa ký |
| Exit_VWAP | ABSTAIN | Window chưa xác nhận |
| MM_mult | ABSTAIN | |
| Status | ABSTAIN | Cần operator xác nhận T0 + collapse date |

---

### AKE (AKEUSDT) — LIVE (massive position still open)

**T0:** ~2026-07-01 | **Markup start:** 2026-07-16 | **Collapse:** PENDING

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 3.14M | OI_min 07-15 (pre-ignition trough, 1d trước ignition) |
| OI_baseline | ~3.65M | OI ổn định 06-27→07-03 (true build base) |
| OI_peak | 73.95M (07-19) | OI_mult từ baseline = 23.55× |
| OI_current | 32.95M–47.43M | Vẫn rất lớn, oscillating |
| Build_VWAP | ~0.00038 | px avg 06-27→07-03 (stable base period) |
| px_current | 0.00464–0.00499 | +1126–1313% từ build base |
| gLSR_base (T0) | 2.97–3.26 | CROWD LONG at launch |
| gLSR_post_ignition | 0.37–0.46 | **FLIPPED TO INVERTED** sau 07-16 — crowd rushed SHORT |
| pos_r_base | 1.2–1.3 | Moderate pre-ignition |
| pos_r_current | 0.732–0.856 | Declining (crowd covering?) |
| Vol peak | 1,978.4M (07-17) | 2nd largest in set |
| Subtype | **SHORT-WASH-XL** | gLSR flipped post-ignition; OI_mult cực cao |
| L-26 status | CHƯA | Chưa có pos_r drop ≥30%/3d |

**Pattern**: AKE khởi đầu CROWD-LONG (gLSR 3.0+) nhưng sau ignition (07-16) crowd flip sang SHORT — pattern hybrid: MM dùng existing crowd-long sentiment để push, sau đó crowd bán short khi px cao → tạo SHORT-WASH pha 2. OI vẫn 32-47M (8-15× baseline) → MM chưa exit.

---

## M1 Summary Table

| Token | Subtype | OI_mult | MM_mult | px_mult | gLSR_base | Status |
|-------|---------|---------|---------|---------|-----------|--------|
| BANK | SHORT-WASH | 6.15× | 5.00× | 10.7× | 0.39–0.46 | RESOLVED |
| ESPORTS | 1-WHALE | 2.27× | 2.18× | 2.4× | 2.84–4.01 | RESOLVED (Jul wave) |
| IDOL | NORMAL | 2.73× | ~1.57× | 1.6× | 0.92–1.05 | PARTIAL (crowd_flush 02/08) |
| CLO | SHORT-WASH | ABSTAIN | ABSTAIN | 2.5× | 0.82–0.87 | ABSTAIN (T0 unconf.) |
| TUT | CROWD-LONG | LIVE | PENDING | 1.37×* | 1.77–1.99 | LIVE |
| AKE | SHORT-WASH-XL | 23.55× (live) | PENDING | 12.2×* | 2.97–3.26 | LIVE |

*Tính đến 04/08/2026

---

## M2 — Test Hai Quan Hệ

### M2-A: MM_multiple vs OI_multiple

**Dữ liệu đủ tin (3 điểm resolved):**

| Token | OI_mult | MM_mult | Ratio (MM/OI) | Subtype |
|-------|---------|---------|---------------|---------|
| BANK | 6.15× | 5.00× | 0.813 | SHORT-WASH |
| ESPORTS | 2.27× | 2.18× | 0.960 | 1-WHALE |
| IDOL | 2.73× | ~1.57× | ~0.575 | NORMAL |

**Quan sát:**
- 3 điểm không đủ để fit regression có nghĩa thống kê
- Trend thô: OI_mult cao hơn → MM_mult cao hơn (monotone trong 3 điểm)
- SHORT-WASH có ratio MM/OI = 0.81 (substantial but not 1:1) — MM chi phí để maintain short-wash
- 1-WHALE có ratio gần 1.0 — MM_mult ≈ OI_mult (hiệu quả cao nhất per unit OI)
- NORMAL subtype có ratio thấp nhất (~0.58) — crowd sharing nhiều hơn vào exit slippage

**Cần thêm:** ≥3 RESOLVED cases mỗi subtype → có thể fit by-subtype regression.
**Tạm thời:** Không dùng MM_mult prediction từ OI_mult — margin of error quá lớn.

### M2-B: gLSR_base vs Subtype phân loại

| gLSR_base range | Subtype | Observed campaigns | OI_mult range |
|----------------|---------|-------------------|---------------|
| < 0.70 | SHORT-WASH | BANK (0.39–0.46) | 6.15× (resolved) |
| 0.70–0.90 | SHORT-WASH-MILD | CLO (0.82–0.87) | ABSTAIN |
| 0.90–1.30 | NORMAL | IDOL (0.92–1.05) | 2.73× |
| 1.30–2.50 | CROWD-LONG | TUT (1.77–1.99) | LIVE |
| > 2.50 | 1-WHALE hoặc EXTREME-LONG | ESPORTS (2.84–4.01), AKE (2.97–3.26) | 2.27×, LIVE |

**Ghi chú AKE**: gLSR tại base là 2.97–3.26 (EXTREME-LONG category) nhưng sau ignition flip sang 0.37–0.46 (SHORT-WASH category). Đây là **HYBRID pattern** — cần nhãn riêng: **FLIP-TO-SHORT-WASH**.

**Conclusion M2**: gLSR_base là discriminator tốt cho subtype (khoảng tách rõ); không đủ data để fit OI_mult range confidence interval per subtype.

---

## M3 — Đồng Hồ Thoát Hồi Tố (Exit Clock)

### BANK: ΔOI/B theo ngày từ T0

B = 4.315M (07-09)

| Ngày | OI (M) | ΔOI/B | px | pos_r | Event |
|------|--------|-------|----|-------|-------|
| 07-09 | 4.315 | 0% | 0.035 | ~3.5 | T0 (B) |
| 07-15 | 6.05 | +40% | 0.051 | 2.864 | Pre-ignition build |
| 07-16 | 8.82 | +104% | 0.059 | 2.021 | Ignition |
| 07-17 | 14.53 | +237% | 0.068 | 1.295 | OI surge |
| 07-18 | 13.57 | +214% | 0.091 | 2.156 | Short bounce |
| 07-19 | 26.56 | **+516%** | 0.167 | 1.610 | **L-26 trigger day** |
| 07-20 | 50.46 | +1069% | 0.264 | 1.091 | Post-exit crowd FOMO |
| 07-27 | 70.83 | +1542% | 0.374 | 1.304 | OI_peak (crowd all-in) |

**Exit clock BANK**: L-26 trigger tại ΔOI/B = +516%, ngày D+10 từ T0 (D+6 từ ignition 07-10).
**Post-exit OI còn tăng**: crowd FOMO sau khi MM đã exit → OI_peak 07-27 là crowd trap, không phải MM position.

### IDOL: ΔOI/B theo ngày từ T0

B = 3.84M (07-22)

| Ngày | OI (M) | ΔOI/B | px | pos_r | Event |
|------|--------|-------|----|-------|-------|
| 07-22 | 3.84 | 0% | 0.01514 | 1.908 | T0 (B) |
| 07-23 | 3.95 | +3% | 0.01800 | 1.911 | Ignition spike |
| 07-27 | 6.60 | +72% | 0.01568 | 2.059 | OI building |
| 07-28 | 10.71 | +179% | 0.01681 | 2.207 | OI surge |
| 07-29 | 9.91 | +158% | 0.01569 | 2.328 | |
| 07-30 | 8.87 | +131% | 0.01523 | 2.558 | pos_r peak |
| 07-31 | 8.81 | +129% | 0.01640 | 2.546 | |
| 08-01 | 9.84 | +156% | 0.02395 | 2.524 | Vol surge 175.7M |
| 08-02 | 10.48 | **+173%** | 0.02312 | 1.731 | **L-26 trigger** |
| 08-03 | 9.50 | +147% | 0.01887 | 1.805 | Post-flush partial |

**Exit clock IDOL**: L-26 trigger tại ΔOI/B = +173%, ngày D+11 từ T0, D+10 từ ignition (07-23). Tương tự BANK về số ngày nhưng OI_mult thấp hơn 3.7×.

### Tổng hợp M3

| Token | Ngày T0→Exit | ΔOI/B tại exit | OI_mult | MM_mult | Subtype |
|-------|-------------|---------------|---------|---------|---------|
| BANK | D+10 | +516% | 6.15× | 5.00× | SHORT-WASH |
| IDOL | D+11 | +173% | 2.73× | ~1.57× | NORMAL |

**Pattern tạm thời**: Exit trong khoảng D+10 đến D+11 từ T0 — nhất quán hơn mong đợi. Cần validate với ESPORTS:
- ESPORTS July wave: T0 ~ 07-14, exit 07-18 = D+4. Ngắn hơn (nhanh hơn, 1-WHALE subtype).

**Hypothesis v0.1**: Exit clock theo subtype:
- SHORT-WASH: D+8 đến D+12 từ T0
- NORMAL: D+10 đến D+12 từ T0
- 1-WHALE: D+3 đến D+5 từ T0 (nhanh hơn do volume tập trung)

Cần ≥3 data points mỗi subtype để confirm.

---

## M4 — TUT Live Tracking (04/08/2026)

**B = 3.76M | T0 = 07-22 | Ngày hiện tại: D+13**

| Ngày | OI (M) | ΔOI/B | px | pos_r | gLSR |
|------|--------|-------|----|-------|------|
| 07-22 | 3.76 | 0% | 0.01444 | 3.887 | 1.7785 | T0 |
| 07-23 | 3.39 | -10% | 0.01387 | 5.083 | 1.7285 | |
| 07-27 | 4.20 | +12% | 0.01571 | 4.333 | 1.9044 | |
| 07-28 | 3.74 | -1% | 0.01389 | 4.657 | 2.0184 | |
| 07-29 | 3.68 | -2% | 0.01466 | 4.911 | 1.9223 | |
| 07-30 | 3.75 | 0% | 0.01460 | 4.585 | 1.8506 | |
| 07-31 | 3.90 | +4% | 0.01560 | 4.959 | 1.8571 | |
| 08-01 | 4.29 | +14% | 0.01735 | 4.169 | 2.0312 | |
| 08-02 | 5.00 | +33% | 0.01741 | 3.458 | 1.7211 | |
| 08-03 | 4.83 | +28% | 0.01986 | 4.014 | 1.6853 | |

**Phân tích:**
- ΔOI/B = +28% tại D+13 — **rất thấp** so với BANK (+516% tại D+10) hoặc IDOL (+173% tại D+11)
- pos_r vẫn ở 4.014 — crowd-long mạnh, chưa có L-26 trigger
- gLSR 1.69 (08-03) — vẫn CROWD-LONG moderate, giảm dần từ peak 2.03
- Vol sau T0 rất thấp (1.1–17.9M/ngày, vol peak 07-11 pre-T0 là 42.2M)
- px tăng +37% trong 13 ngày — nhẹ nhàng, không phải ignition spike

**Chẩn đoán**: TUT chưa ignite. Theo IDOL pattern, ignition xảy ra D+1 từ T0 (07-23 vol 167.3M). TUT chưa có ngày vol >50M post-T0. Có thể:
1. Campaign bị delay (MM chưa push)
2. Campaign đang ở slow-build pha khác với BANK/IDOL
3. pos_r cao (4.0+) là "pre-loaded" từ trước T0, MM không cần build thêm nhiều

**Trigger cần theo dõi**: Vol day >100M + pos_r drop >15%/d = potential ignition signal.

---

## M5 — Kết: Công Thức v0 → v0.1

### v0 (trước calibration)

```
B = OI_at_T0
MM_position ≈ B (giả định MM build từ scratch tại T0)
Exit signal = pos_r drop ≥30%/3d (L-26)
Exit_VWAP ≈ px tại L-26 trigger day
MM_mult = Exit_VWAP / Build_VWAP
```

### Sửa đổi → v0.1

**[FIX 1] OI_base cẩn thận hơn (BANK case)**
- BANK: OI_min (4.315M) = T0 = pre-markup minimum. OK.
- IDOL: OI_min overall (2.886M) tại 05-26 ≠ T0 baseline. Dùng OI tại cuối pre-ignition calm (3.84M).
- **Rule v0.1**: OI_base = OI tại cuối window pre-ignition calm, không phải OI_min overall nếu OI_min xảy ra pre-campaign.

**[FIX 2] Subtype classification tại T0**
- Thêm step phân loại trước khi estimate OI_mult hoặc MM_mult:

```
if gLSR_base < 0.70:
    subtype = "SHORT-WASH"        → OI_mult estimate: 4–8×, exit D+8→12
elif gLSR_base < 1.30:
    subtype = "NORMAL"            → OI_mult estimate: 2–4×, exit D+10→12
elif gLSR_base < 2.50:
    subtype = "CROWD-LONG"        → OI_mult estimate: 1.5–3×, exit UNKNOWN (chưa đủ data)
else:
    subtype = "1-WHALE-OR-HYBRID" → OI_mult estimate: 2–3× per wave, exit D+3→5 per wave
    # Flag: monitor gLSR post-ignition. If flip to <0.70 → reclassify SHORT-WASH-HYBRID
```

**[FIX 3] Exit_VWAP window**
- BANK: L-26 trigger ngày 07-19 (1 ngày: vol 6473M). Đủ vol để định giá.
- IDOL: L-26 trigger 08-02, nhưng peak vol là 08-01 (175.7M). Window = 08-01/08-02 (2 ngày).
- ESPORTS: 07-18/07-19 window (2 ngày: vol 2567M).
- **Rule v0.1**: Exit_VWAP = vol-weighted px trong cửa sổ [L-26 trigger day -1, L-26 trigger day]. Dùng tối thiểu 2 ngày để giảm spike noise.

**[FIX 4] Post-exit OI vẫn tăng ≠ MM position**
- BANK: OI_peak 70.83M (07-27) >> OI_exit 26.56M (07-19). Post-exit là crowd FOMO build.
- **Rule v0.1**: OI_exit ≠ OI_peak. OI_exit = OI tại L-26 trigger, không phải OI_max.
- Corollary: Tránh nhầm OI_max overall thành MM position size.

**[FIX 5] MM_mult confidence levels**
- HIGH confidence (2 inputs confirmed): BANK (5.00×), ESPORTS (2.18×)
- MED confidence (Build_VWAP estimated): IDOL (~1.57×)
- ABSTAIN: TUT, AKE, CLO (no confirmed exit)
- **Rule v0.1**: Báo cáo MM_mult kèm confidence level. Không dùng MED/ABSTAIN cho live signal.

### v0.1 Formula Summary

```
Bước 1: Phân loại subtype → gLSR_base + pos_r_base tại T0
Bước 2: OI_base = OI tại cuối pre-ignition calm (≠ OI_min overall nếu OI_min pre-campaign)
Bước 3: Monitor ΔOI/B hàng ngày:
         SHORT-WASH: alert tại ΔOI/B > 200% (BANK hit 516% at exit)
         NORMAL:     alert tại ΔOI/B > 100% (IDOL hit 173% at exit)
Bước 4: L-26 trigger = pos_r drop ≥30%/3d → compute Exit_VWAP [D-1, D]
Bước 5: MM_mult = Exit_VWAP / Build_VWAP (confirm nếu vol D-1+D > 500M)
Bước 6: Declare RESOLVED. OI tiếp tục tăng sau đây = CROWD TRAP, không liên quan MM P&L.
```

---

## Data Gaps và Giới Hạn

| Gap | Tác động | Priority |
|-----|---------|---------|
| AKE chưa resolved | MM_mult ABSTAIN cho case lớn nhất | HIGH |
| CLO T0 chưa xác nhận operator | ABSTAIN toàn bộ | HIGH |
| TUT chưa ignite | Chưa biết subtype exit cadence | MED |
| IDOL Build_VWAP approximate | MM_mult ±10% error | MED |
| ESPORTS đa sóng (June + July) | June wave unanalyzed | LOW |
| BAS, BTW, POWER, BASED, BULLA chưa phân loại | Extended M2 table incomplete | LOW |

**Calibration status**: v0.1 có thể dùng để phân loại subtype + monitor ΔOI/B thresholds. Không đủ data để predict MM_mult range với CI >80%. Cần ≥5 RESOLVED cases (hiện tại: 2 HIGH + 1 MED).

---

## Extended M2: Hồ Sơ Nhanh (chưa resolved)

| Token | OI_mult (min→max) | gLSR range | pos_r range | Subtype est. | Notes |
|-------|------------------|-----------|-------------|-------------|-------|
| BAS | 8.42× | 0.78–3.19 | 1.15–3.20 | MIXED | OI đang decay (gLSR flip Long) |
| BTW | 10.93× | 0.54–2.17 | 0.89–2.00 | SHORT-WASH? | Pha 2 suppressor L-05; OI 14.27M live |
| TAG | 2.34× | 0.69–2.16 | 1.29–2.52 | NORMAL-SHORT | Live, OI 11.83M; gLSR 2.07 (flip?) |
| POWER | 1.70× | 1.92–4.90 | 1.01–1.53 | 1-WHALE | gLSR cực cao 4.0+; OI stable |
| BASED | 2.59× | 0.90–3.00 | 1.21–1.73 | MIXED | Campaign mờ, no clear T0 |
| BULLA | 3.89× | 1.21–6.19 | 1.56–1.98 | CROWD-LONG-HIGH | gLSR 6.0+ rare; OI 9.21M |

---

*Proposal này cần operator ký để dùng vào live signal. Hiện trạng: calibration internal, research only.*
*Next update khi AKE hoặc TUT resolved (L-26 trigger).*

# MM-ECON Calibration v0.2
**Date:** 05/08/2026 | **Status:** ANALYSIS ONLY — operator ký trước khi dùng vào live signal
**Supersedes:** `mm_econ_v0.md` (v0.1 patch tích hợp luôn)
**Changes v0.2:**
1. BANK T+30 RESOLVED (09/08): px 0.0495 vs T0 0.0377 = +31.3% — dòng ĐÓNG
2. Thêm cột `kho_vol_ratio` vào M1 summary
3. Thêm section M6: Taker Detection Floor + kho_vol_ratio methodology
4. BANK Vòng 2 watch: 3 điều kiện 01-05/08

---

## M1 — Bảng 6 Campaign (Updated)

### Định nghĩa cột mới (v0.2)

| Cột | Định nghĩa |
|-----|-----------|
| kho_vol_ratio | kho_tokens × avg_px_at_exit / total_spot_vol_campaign — tỷ lệ kho có thể thoát qua spot mà không bị phát hiện bằng taker signal |
| taker_detect_floor | Ngưỡng kho/spot vol tối thiểu để taker signal phân biệt được sell-side (thực nghiệm: ~10%) |

### BANK (BANKUSDT) — RESOLVED + T+30 CLOSED ✓

**T0:** 2026-07-09/10 | **Exit:** 2026-07-19 | **T+30:** 2026-08-09

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 4.315M | T0 OI |
| OI_at_exit | 26.56M | L-26 trigger 07-19 |
| **OI_mult** | **6.15×** | |
| Build_VWAP | 0.03943 | |
| Exit_VWAP | 0.19710 | Vol-weighted 07-19 (6473M) |
| **MM_mult** | **5.00×** | HIGH confidence |
| T+30 px (09/08) | **0.0495** | Operator-provided |
| T0 ref px | **0.0377** | Open 09/06 |
| T+30 ret vs T0 | **+31.3%** | Từ +897% đỉnh về +31% = FULL COLLAPSE |
| T+14 px | 0.28339 | Vẫn +651% lúc T+14 |
| advisor_exit VWAP | 0.19710 | T+30 px/exit = **-74.9%** — crowd giữ túi |
| kho_size est. | 80M tokens | Unlock 17/07 deposit 18/07 |
| kho_val_at_exit | ~$15.8M | 80M × 0.19710 (Exit_VWAP) |
| total_spot_vol | $598M | Peak week 20-27/07 (8 ngày) |
| **kho_vol_ratio** | **2.6%** | 15.8M / 598M = kho nhỏ hơn 40× spot vol |
| taker_detect | AMBIGUOUS | Taker peak week = 51.2% (neutral) — nằm dưới detection floor |

**P8 verdict (kéo-sau-ghế-thoát-kho):** AMBIGUOUS từ taker. Perp pos_r exit (19-21/07) là signal rõ ràng hơn spot taker.

**Vòng 2 watch** (cập nhật 05/08): xem M7 bên dưới.

---

### IDOL (IDOLUSDT) — PARTIAL RESOLVED

| Metric | Giá trị |
|--------|---------|
| OI_mult | 2.73× |
| MM_mult | ~1.57× |
| kho_vol_ratio | PENDING (need total_spot_vol) |
| taker_detect | PENDING |

---

### ESPORTS (ESPORTSUSDT) — RESOLVED

| Metric | Giá trị |
|--------|---------|
| OI_mult | 2.27× |
| MM_mult | 2.18× |
| kho_vol_ratio | PENDING |
| taker_detect | PENDING |

---

### TUT (TUTUSDT) — LIVE (CỜ GHẾ-RỜI FIRED 02/08)

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| OI_base (B) | 3.76M | T0 07-22 |
| OI_current | PENDING 05/08 | |
| Build_VWAP | 0.01450 | |
| Exit_VWAP | PENDING | Chưa trigger chính thức |
| pos_r_current | ~4.0 | Vẫn CROWD-LONG mạnh |
| CỜ GHẾ-RỜI | FIRED 02/08 | pos_r ≤ 3.81 (peak-14d=5.083 × 0.75) |
| kho_vol_ratio | PENDING | Cần total_supply + cost basis |
| taker_detect | Binance spot 51.1% neutral | Tương tự BANK — nằm dưới floor |

---

## M1 Summary Table (v0.2)

| Token | OI_mult | MM_mult | kho_vol_ratio | taker_detect | T+30 | Status |
|-------|---------|---------|---------------|--------------|------|--------|
| BANK | 6.15× | 5.00× | **2.6%** | AMBIGUOUS (51.2%) | +31.3% vs T0 | **RESOLVED+CLOSED** |
| ESPORTS | 2.27× | 2.18× | PENDING | PENDING | PENDING | RESOLVED (Jul wave) |
| IDOL | 2.73× | ~1.57× | PENDING | PENDING | PENDING | PARTIAL |
| CLO | ABSTAIN | ABSTAIN | ABSTAIN | PENDING | N/A | ABSTAIN |
| TUT | LIVE | PENDING | PENDING | AMBIGUOUS (51.1%) | T+30=08/08 | LIVE |
| AKE | 23.55× live | PENDING | PENDING | PENDING | N/A | LIVE |

---

## M6 — Taker Detection Floor (NEW)

### Phương pháp kho_vol_ratio

```
kho_vol_ratio = (kho_tokens × avg_px_at_exit) / total_spot_vol_campaign

Nếu kho_vol_ratio < 10% → taker signal KHÔNG đủ để phát hiện organized sell-side
Nếu kho_vol_ratio > 30% → taker signal CÓ KHẢ NĂNG phân biệt (cần xem taker <45% sustained)
Nếu kho_vol_ratio > 50% → taker signal MẠNH: sell wall pattern rõ (taker <40% trên vol lớn)
```

### Thực nghiệm từ BANK

- kho 80M × $0.197 = $15.8M
- total spot peak week $598M
- kho_vol_ratio = **2.6%**
- Taker vol-weighted = 51.2% (neutral) → **KHÔNG PHÁT HIỆN ĐƯỢC**
- Lý do: kho bằng 2.6% spot vol → ngay cả nếu MM bán 100% kho bằng limit sell,
  tác động lên taker chỉ là: 51% → 51% × 0.974 + 0% × 0.026 ≈ 49.7%
  (giảm 1.3 pp so với neutral = không nhìn thấy được)

### Taker detection floor ~10%

**Rule M6 v0.2:**
> Nếu kho_vol_ratio < 10%, ABSTAIN việc kết luận sell-side organization từ taker spot.
> Cần on-chain exchange balance (BscScan) để confirm.

**Threshold evidence:**
- BANK: 2.6% → AMBIGUOUS (confirmed)
- TUT: kho_vol_ratio PENDING (cần total_supply O1)
  - Estimate: nếu spot vol TUT avg $1.4M/day × 27 ngày = $37.8M total
  - Cần biết kho TUT size để compute ratio
- Ngưỡng 10% là thực nghiệm từ 1 case — cần validate thêm với ESPORTS/IDOL

### Implication cho P8 thesis

- P8 ("kéo-sau-ghế-thoát-kho") KHÔNG thể xác nhận bằng taker spot khi kho nhỏ vs vol
- Phương pháp tốt hơn: (a) on-chain exchange balance delta, (b) perp pos_r crash pattern,
  (c) OI_exit timing vs px peak
- BANK perp pos_r crash (3.814→1.295 trong 07-12→07-17) = SIGNAL MẠNH nhất
  = MM bán perp long position trước khi kho chạm spot

---

## M7 — BANK Vòng 2 Watch (NEW, 05/08)

### Context

Sau khi Vòng 1 collapsed (exit 19-21/07, px peak 0.672 spike 27/07):
- 30/07-01/08: 190M tokens nạp vào sàn (theo operator chart) = kho Vòng 2
- 01-05/08: px phục hồi từ 0.044 lên ~0.052 (range; fapi)
- 04/08: nến lớn O=0.0442 H=0.0619 C=0.0524 vol=$471.6M

### 3 Điều Kiện Theo Dõi Vòng 2

**Điều kiện 1: gLSR (→~1 = spent / >1.5 stable = Vòng 2 setup)**

| Ngày | gLSR | Nx |
|------|------|----|
| 31/07 | 1.501 | ↑ recovering |
| 01/08 | 1.800 | ↑↑ |
| 02/08 | 1.884 | peak |
| 03/08 | 1.726 | ↓ |
| 04/08 | 1.649 | ↓ |
| 05/08 | 1.396 | ↓↓ post-pump |

Verdict: CHƯA THỎA — gLSR đạt peak 1.88 (02/08) rồi quay đầu. Nến +19% của 04/08 khiến crowd bán long (gLSR 1.649→1.396). Chưa thấy "stable >1.5 + pin mới".

**Điều kiện 2: pos_r (re-rate từ đáy 1.09 = Vòng 2 tích lũy)**

| Ngày | pos_r | Nx |
|------|-------|----|
| 31/07 | 1.109 | đáy |
| 01/08 | 1.181 | ↑ |
| 02/08 | 1.320 | ↑↑ |
| 03/08 | 1.312 | ~ |
| 04/08 | 1.313 | ~ |
| 05/08 | 1.199 | ↓ post-pump |

Verdict: ĐANG XẢY RA nhưng chưa ổn định — pos_r re-rate từ 1.11→1.32, nhưng nến pump 04/08 khiến top traders take profit/flip short.

**Điều kiện 3: Funding + fn (pin mới = Vòng 2 signal)**

| Ngày | f_avg | f_n | Regime |
|------|-------|-----|--------|
| 01/08 | -0.000806 | 24 | neg_batch |
| 02/08 | -0.000349 | 24 | neg_light |
| 03/08 | -0.000186 | 24 | neg_light |
| 04/08 | -0.000548 | 24 | neg_batch (spike day) |
| 05/08 | ~0 (fapi) | N/A | near_zero |

Verdict: CHƯA THỎA — funding vẫn âm/gần zero. KHÔNG có "pin dương mới". Vòng 1 đặc trưng bởi funding DƯƠNG ổn định (0.00005 mỗi giờ × 8h = 0.0004/ngày). Hiện tại âm hoặc gần zero = MM chưa rebuild perp long position.

### Phân Tích Nến 04/08 (+19% O→C, H=+40% từ Open)

| Metric | Giá trị | Đọc |
|--------|---------|-----|
| vol perp | $471.6M | 3.3× ngày trước = spike lớn |
| taker perp | 49.1% | NEUTRAL — không có FOMO buy rush |
| OI delta | $17.25M→$17.36M | **FLAT** (+0.6%) |
| spot vol | $46.83M | Tăng 3.8× so với 03/08 |
| spot taker | 48.3% | NEUTRAL |
| gLSR sau nến | 1.396 (↓ từ 1.649) | Crowd BÁN longs post-pump |

**Pattern: SHORT SQUEEZE không phải Ignition**
- OI flat + vol spike + taker neutral = liquidation cascade (shorts bị squeeze) + profit-taking
- Không có dấu hiệu "MM build perp long mới"
- Consistent với MM test liquidity trước Vòng 2 OR crowd-driven bounce

### Verdict Vòng 2

**Điều kiện đủ để CONFIRM Vòng 2: 0/3 thỏa mãn (05/08)**

| Điều kiện | Ngưỡng | Trạng thái |
|-----------|--------|------------|
| gLSR ổn định > 1.5 | ≥3 ngày liên tiếp | ❌ Đang giảm (1.88→1.40) |
| pos_r ổn định > 1.5 | ≥3 ngày liên tiếp | ❌ Max 1.32, đang ↓ |
| Funding pin dương | f_avg > +0.00005 × ≥3 ngày | ❌ Âm/gần zero |

**190M deposit kho là điều kiện cần, chưa đủ.** Nạp kho không đồng nghĩa ignition — BANK Vòng 1 cũng có kho deposit 18/07 nhưng phải đến 19-21/07 mới exit. Theo dõi tiếp: mốc 17/08 = next unlock event.

---

## M5 — Formula v0.1 → v0.2 Update

```
v0.2 bổ sung:

Bước 0 (mới): Tính kho_vol_ratio = kho_USD / total_spot_vol
  Nếu ratio < 10%: ABSTAIN taker detection — dùng on-chain balance thay thế
  Nếu ratio > 30%: Taker signal có thể phát hiện (cần taker <45% sustained ≥2d)

Bước 6b (mới): Sau RESOLVED, monitor Vòng 2 qua 3 điều kiện:
  - gLSR ổn định > 1.5 (≥3 ngày)
  - pos_r ổn định > 1.5 (≥3 ngày)
  - Funding pin dương (f_avg > +0.00005 × ≥3 ngày)
  → Nếu 3/3 thỏa: WARN Vòng 2 preparation
```

---

## Data Gaps (v0.2)

| Gap | Priority |
|-----|----------|
| BANK T+30 px 09/08 (operator verify) | MED — dùng 0.0495 per operator |
| TUT kho_vol_ratio (cần O1 total_supply) | MED |
| IDOL, ESPORTS kho_vol_ratio | LOW |
| AKE, CLO resolved | HIGH |
| Validation taker_detect floor từ ESPORTS/IDOL | MED |

---

*v0.2 analysis only — cần operator ký. Taker detection floor 10% là thực nghiệm từ 1 case (BANK).*
*Next update: khi AKE hoặc TUT resolved, hoặc khi BANK Vòng 2 có 3/3 điều kiện.*

# PROBE BR — Chốt Canh + Lớp Mới (04/08/2026)
Run: 2026-08-04

Lưu ý: BR trong SỔ ĐEN BAIT-B (L-05) — đọc bull phải biện hộ gấp đôi.

---

## Funding Interval Verify (fapi native BRUSDT)

```
2026-08-01 08:00 UTC  rate=0.000350
2026-08-01 12:00 UTC  rate=0.000234
2026-08-01 16:00 UTC  rate=0.000408
2026-08-01 20:00 UTC  rate=0.000051
2026-08-02 00:00 UTC  rate=0.000082
2026-08-02 04:00 UTC  rate=0.000334
...
2026-08-04 04:00 UTC  rate=0.000288
2026-08-04 08:00 UTC  rate=0.000050
2026-08-04 12:00 UTC  rate=0.000302
```

→ **Dominant interval: 4h** (BRUSDT cũng 4h, như TAG và TUT — không phải 8h)
→ fn=6 trong freshwatch = 6 × 4h = **24h/ngày** coverage đầy đủ

---

## R1 — Chuỗi BR 28/07→03/08

CAVEAT: 25-26/07 MISSING trong freshwatch (gap data). 04/08 partial — PENDING.

| date | px | ret_1d | ret_3d | vol_M | tk% | f_avg | fn | OI_M | OI_vs_floor | OI_pos | pos_r | acc_r | gLSR | div | div3 | sl5d | SUSPECT |
|------|-----|--------|--------|------:|----:|------:|---:|-----:|------------|--------|------:|------:|-----:|----:|-----:|-----:|---------|
| 27/07 | 0.151580 | — | — | 1.4 | 50.5 | 0.00014 | 6 | 3.778 | ×1.00 | FLOOR(20%) | 1.696 | 1.495 | 1.8441 | 0.881 | 0.881 | — | OK |
| 28/07 | 0.146810 | -3.1% | — | 0.6 | 50.9 | 0.00008 | 6 | 3.686 | ×0.97 | FLOOR(19%) | 1.674 | 1.521 | 1.9214 | 0.909 | 0.895 | — | OK |
| 29/07 | 0.146850 | +0.0% | — | 0.7 | 48.2 | 0.00012 | 6 | 3.782 | ×1.000 | FLOOR(20%) | 1.661 | 1.490 | **1.9438** | 0.897 | 0.896 | — | OK |
| 30/07 | 0.147313 | +0.3% | -2.8% | 0.7 | 49.2 | 0.00005 | 6 | 3.800 | ×1.005 | MID(20%) | 1.658 | 1.342 | 1.7525 | 0.809 | 0.872 | — | OK |
| 31/07 | 0.150344 | +2.1% | +2.4% | 0.6 | 46.4 | 0.00010 | 6 | 3.841 | ×1.016 | MID(21%) | 1.651 | 1.400 | 1.8401 | 0.848 | 0.851 | — | OK |
| 01/08 | 0.159674 | **+6.2%** | +8.7% | 1.4 | 51.7 | 0.00019 | 6 | 3.874 | ×1.024 | MID(21%) | 1.660 | 1.472 | 1.8860 | 0.886 | 0.848 | 1.023 | OK |
| 02/08 | 0.160787 | +0.7% | **+9.1%** | **3.3** | 42.6 | 0.00016 | 6 | **4.383** | **×1.159** | MID(28%) | 1.665 | 1.330 | 1.6371 | 0.799 | 0.844 | 0.852 | OK |
| 03/08 | 0.145374 | **-9.6%** | -3.3% | 1.3 | 50.7 | 0.00007 | 6 | 3.761 | ×0.995 | FLOOR(20%) | **1.709** | **0.841** | **1.0786** | **0.492** | 0.726 | **0.555** | OK |

OI floor canonical: **3,782,263 USD** (mốc hồ sơ)

**Sự kiện nổi bật:**
- 29/07: gLSR PEAK = **1.9438** (cao nhất chuỗi — đúng mốc hồ sơ 1.944)
- 02/08: OI spike = **4.383M (+15.9% vs floor)** + vol 3.3M (×5 so với trung bình) + taker_buy 42.6% (thấp = bán nhiều hơn)
- 03/08: gLSR CRASH **1.9438→1.0786** trong 4 ngày (−44.5%), acc_r **1.472→0.841**, px −9.6%, OI về floor

---

## R2 — 4 Chốt Hồ Sơ

### ① pos_r nhích bền tại floor (vs mốc 1.661)

| date | pos_r | vs ref | OI_M | nhận xét |
|------|------:|-------:|-----:|---------|
| 27/07 | 1.696 | ↑+0.035 | 3.778 | trên ref |
| 28/07 | 1.674 | ↑+0.013 | 3.686 | trên ref |
| 29/07 | 1.661 | = 0.000 | 3.782 | đúng ref |
| 30/07 | 1.658 | ↓−0.003 | 3.800 | dưới ref |
| 31/07 | 1.651 | ↓−0.010 | 3.841 | dưới ref |
| 01/08 | 1.660 | ↓−0.001 | 3.874 | dưới ref (sát) |
| 02/08 | 1.665 | ↑+0.004 | 4.383 | trên ref, OI spike |
| 03/08 | **1.709** | ↑+0.048 | 3.761 | cao nhất chuỗi — SAU px −9.6% |

**Chuỗi tăng liên tục max: 3 ngày** (01-03/08: 1.660→1.665→1.709) — đúng ngưỡng ≥3d.

**Nhưng CONTEXT quan trọng hơn số:**
- pos_r tăng 03/08 là khi px rơi −9.6%: shorts đóng vị thế (buy-back) → pos_r = L/S tăng cơ học
- KHÔNG phải signal mua thuần — là shorts bị squeezed ra khỏi thị trường
- acc_r cùng ngày CRASH 1.472→0.841 (đa số tài khoản lật short): mâu thuẫn — đọc ① thận trọng

**Verdict ①:** Đã đủ ≥3d nhưng cơ chế là shorts-exit không phải longs-build. OI ở floor = đúng điều kiện L-01. Không đủ biện hộ bull độc lập.

---

### ② TIÊN QUYẾT — gLSR crowd_flush (mốc 1.944, flush ≤1.1)

**gLSR 29/07=1.9438 → 03/08=1.0786 = −44.5% trong 4 ngày**

**gLSR ≤1.1 ĐÃ XẢY RA: 03/08 = 1.0786** ✓

**NHƯNG — L-26 pos_r crowd_flush (−30%/3d) CHƯA:**

| window 3d | pos_r start | pos_r end | drop% | PASS? |
|-----------|------------|-----------|------:|-------|
| 27→29/07 | 1.696 → 1.661 | −2.1% | ✗ |
| 28→30/07 | 1.674 → 1.658 | −1.0% | ✗ |
| 29→31/07 | 1.661 → 1.651 | −0.6% | ✗ |
| 30→01/08 | 1.658 → 1.660 | +0.1% | ✗ |
| 31/07→02/08 | 1.651 → 1.665 | +0.8% | ✗ |
| **01→03/08** | **1.660 → 1.709** | **+2.9%** | ✗ |

**Khoảng cách crowd_flush L-26:** max drop 3d = **−2.1%** (cần −30%). Còn thiếu **27.9%**.

**Giải mã gLSR crash 03/08:**
- gLSR (global = tất cả tài khoản) sập −44.5%: phần lớn TÀI KHOẢN đang short
- acc_r sập 1.47→0.84: số tài khoản short > long
- NHƯNG pos_r vẫn 1.709: KHỐI LƯỢNG vị thế long vẫn lớn hơn short
- Ý nghĩa: tài khoản nhỏ mở short mới; tài khoản lớn (whale) vẫn giữ long
- Đây là divergence pattern BTW giai đoạn 2: "whale long, retail short" = phân phối dưới màng phủ

**Verdict ②:** gLSR flush ≤1.1 ĐÃ QUA nhưng cơ chế KHÔNG như IDOL (không có pos_r drop lớn). Crowd_flush L-26 CHƯA đủ. **Theo quy trình: chưa đủ → STAND_ASIDE giữ nguyên.**

---

### ③ Kho 6%

**PENDING OPERATOR** — CẦN exchange balance + ví kho.
Từ hồ sơ: redeposit kho 6% = tín hiệu xả. Chưa có on-chain xác nhận.

---

### ④ BTW hình bẫy pha 2 (nguy hiểm nhất)

**Giá phẳng ≤±7%?**
- px 31/07→03/08: 0.1503→0.1600→0.1608→0.1454
- Biên độ: (0.1608−0.1454)/0.1454 = **+10.6% → KHÔNG FLAT ✗**
- 01-02/08 có spike lên 0.160 rồi sập 03/08 = không phải dải phẳng

**Funding neg-div §5 (avg ≤−2e-4 OR min ≤−5e-4)?**

| date | f_avg | f_min | SUPPRESSOR? |
|------|------:|------:|------------|
| 28/07 | 0.00008 | 0.00005 | — |
| 29/07 | 0.00012 | 0.00005 | — |
| 30/07 | 0.00005 | 0.00005 | — |
| 31/07 | 0.00010 | 0.00005 | — |
| 01/08 | 0.00019 | 0.00005 | — |
| 02/08 | 0.00016 | 0.00006 | — |
| 03/08 | 0.00007 | 0.00005 | — |

**SUPPRESSOR §5 = KHÔNG BẬT.** Funding dương, không có negative divergence.

**Verdict ④:** BTW pha 2 trap KHÔNG bật (giá không flat, funding không âm). Đây là tín hiệu tốt — cửa suppressor chưa đóng.

---

### L-26 check tổng: 5 ngày qua (28/07→03/08)

| Metric | Direction | Số |
|--------|-----------|---|
| gLSR | ↓ mạnh | 1.9214→1.0786 (−43.9%) |
| px | Sideways rồi sập | 0.1468→0.1454 (−1.0% net, peak 0.1608 +01/08) |
| pos_r | ↑ nhẹ | 1.674→1.709 (+2.1%) |
| OI | ↓ về floor | 3.686→3.761M (stable at floor) |

**Không có crowd_flush — crowd LONG đang được giữ bởi cấu trúc vị thế, trong khi tài khoản nhỏ lật short.**

---

## R3 — Gate Tape (lần đọc thật đầu tiên)

**STATUS: COLLECTOR CHƯA DEPLOY**

- `collect_tape.py` đã viết, config schema sẵn (`tape_targets.json` mẫu: BR@Gate, enabled_date 2026-07-30)
- Nhưng `tape_targets.json` KHÔNG tồn tại cả local lẫn VPS
- `spot_tape_1d` store = KHÔNG tồn tại

**→ R3 = NO_DATA. Gate bid/ask wall, CVD, size distribution = CHƯA ĐO.**

**CẦN OPERATOR:**
1. Deploy `tape_targets.json` trên VPS với `{"symbol":"BR","venue":"gate","pair":"BR_USDT","enabled_date":"2026-07-30"}`
2. Chạy backfill `python scripts/collect_tape.py --date 2026-07-30` trên VPS
3. Sau khi có data: đọc size_cv (>1 = phân phối đều tổ chức — II.4 phân phối có tổ chức)

---

## R4 — Alpha Layer BR (ALPHA_118)

Alpha vol BR là **NEGLIGIBLE**:

| Metric | Giá trị |
|--------|---------|
| Alpha vol avg (Jul-Aug 2026) | **$5,352/ngày** |
| Alpha vol max | $28,166 (19/07) |
| Alpha vol window 28/07→03/08 | $883→$1,253→$1,537→$878→$4,136→$7,143→$2,799 |
| Alpha spread vs perp | ±2% (thin market) |

**Kết luận R4:**
- Không có dòng mua Alpha đều đặn kiểu controlled-fill
- Vol alpha không có spike nào gắn với OI cycle (max 07/19 $28K = vô nghĩa về size)
- alpha_vol/perp_vol ratio ≈ 0.001-0.003 (so với IDOL có spike 0.5+)
- Pool Alpha BR = về cơ bản CHẾT — chỉ có retail nhỏ, không có MM signature
- **alpha_suspect = không bật**

---

## R5 — So Khuôn IDOL vs BR

| Chiều | IDOL pre-ignition | BR hiện tại (03/08) |
|-------|-------------------|---------------------|
| Ngày case open (T0) | 2026-07-04 (est.) | — (chưa ignite) |
| Vị trí chu kỳ | OI tại floor, đang build | OI tại floor, FLAT từ 2 tháng |
| gLSR lúc "chờ" | **Thấp + TĂNG** (~1.3-1.5 rising) | **Cao sau đó CRASH** (1.94→1.08) |
| pos_r | Floor, rising bền | Floor, oscillating 1.65-1.71 |
| acc_r | Tăng (tích lũy tài khoản) | **CRASH 1.47→0.84** (tài khoản lật short) |
| Funding | PIN 0.00005 toàn bộ | 4h cycle, floating (0.00005-0.00041) |
| Vol alpha | Có spike (×10+ vs avg) | Dead pool ($883-$7K/ngày) |
| Crowd fuel | Đủ short để squeeze | **GAS ĐÃ ĐỐT (acc_r<1.0 = đa số đang short)** |
| Thời gian chờ | 2-3 tuần pre-T0 | 2+ tháng không ignite |
| Ghế deposited | Operator confirm pre-campaign | 6% kho chưa xác nhận hướng |

**Verdict R5:**
**BR đang giống BTW-trước-sập hơn IDOL-trước-ignite.**

Lý do cốt lõi:
1. **Trajectory gLSR ngược chiều**: IDOL = gLSR thấp rising (crowd SHORT bị squeeze). BR = gLSR cao rồi CRASH (crowd LONG bị flush — không có fuel mới)
2. **acc_r crash 0.84**: Đa số tài khoản đã short. IDOL pre-ignite: acc_r đang tích lũy. BR: đã tiêu hao
3. **Alpha pool chết**: IDOL có alpha vol spike trước ignition. BR flat $5K/ngày
4. **Thời gian**: 2+ tháng từ khi vào sổ không có ignition signal = BAIT-B pattern giữ nguyên

**Điểm khác biệt với BTW**: OI không tăng (flat floor), px không tăng rõ. BTW có OI build trước xả. BR đang ở giai đoạn trước BTW hơn.

---

## R6 — Unlock BR (nợ cũ L-12)

**STATUS: NO_DATA (lần đầu tra)**

- TokenUnlocks.app: cần web access — không có local
- CryptoRank: tương tự
- BscScan vesting: V2 yêu cầu paid plan
- Không có lịch unlock trong hồ sơ hiện tại

**Đã biết từ context:**
- BR là Binance Alpha token (BSC contract)
- Không có bằng chứng unlock event trong 28/07→03/08 từ data available

**CẦN OPERATOR:** Tra TokenUnlocks.app BR → đối chiếu với redeposit 6% kho (nếu ≤48h sau unlock = chân xả, bài BANK khuôn L-12)

---

## Tổng Kết — State Đề Xuất + Chốt Canh Ngày Mai

### Verdict trần hiện tại: **STAND_ASIDE**

Lý do (từng điểm):
- ① pos_r ≥3d tăng: **Đủ** nhưng cơ chế shorts-exit, không phải longs-build. Không thay đổi verdict.
- ② gLSR flush ≤1.1: **03/08 = 1.0786** ĐÃ QUA — signal mới. NHƯNG pos_r crowd_flush L-26 CHƯA (−2.1% vs −30%). Verdict trần STAND_ASIDE chưa dỡ.
- ③ Kho 6%: PENDING operator.
- ④ Suppressor BTW §5: CHƯA BẬT — tốt.

**Verdict:** STAND_ASIDE giữ. gLSR flush là signal đáng chú ý nhưng cơ chế không đủ (acc_r crash = không phải organic flush mà là tài khoản nhỏ mở short mới).

### Ô PENDING operator:
| Việc | Lý do |
|------|-------|
| Exchange balance + ví kho 6% | Xác nhận redeposit/withdrawal direction |
| TokenUnlocks.app BR | Đối chiếu khuôn L-12 |
| Deploy tape_targets.json VPS | Bật Gate tape collector |
| Verdict CASE sheet | Không phải agent |

### Chốt canh 05/08 — số cần theo dõi:

| Metric | Hiện tại (03/08) | Ngưỡng cần đạt |
|--------|-----------------|----------------|
| gLSR | 1.0786 (flush done) | Cần TĂNG BỀN ≥1.5 tái-ARM |
| pos_r | 1.709 | Giảm ≥30% trong 3d (crowd flush L-26) |
| acc_r | 0.841 | Cần tăng >1.0 (net long accounts trở lại) |
| OI | 3.761M (at floor) | Nếu rời floor = có money mới |
| px | 0.145374 | Nếu giảm <0.130 = new low → re-read |
| Funding | PIN (03/08) | Nếu burst >25bps = heat signal |

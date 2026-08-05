# TUT — Pháp y khung dài + Loài C analysis + Tiến độ monetize
**Soạn: 05/08/2026 | ANALYSIS only | PENDING operator: cụm ví gom TUT + supply total**

---

## RANH GIỚI DỮ LIỆU (ghi nguồn per L-10)

| Nguồn | Coverage | Trạng thái |
|---|---|---|
| VPS klines_1h TUTUSDT | 0 files | EMPTY — không có gì để dùng |
| freshwatch export | **36 rows: 27/06 → 04/08** | OK — bắt đầu muộn |
| fapi klines 1d | 01/05 → 05/08 (97 rows) | OK |
| fapi klines 4h | 01/05 → 22/07 (499 rows) | OK |
| fapi fundingRate | 01/05 → 05/08 (576 rows) | OK |
| fapi OI daily | 06/07 → 05/08 (31 rows) | OK (31d retention) |
| OI 1h | 400 error | UNAVAIL |
| GeckoTerminal BSC | snapshot 05/08 | OK |
| Binance Alpha store | **TUT NOT IN STORE** | ABSENT (ALPHA_117 không có parquet) |
| On-chain (cụm ví, supply) | R4 — Nansen LOCKED | PENDING OPERATOR |

**Boundary cứng:** OI/LSR/pos_r chỉ có từ 27/06 (freshwatch). Trước đó = ABSTAIN hoàn toàn theo L-10.

---

## V1 — CHUỖI 01/05→05/08: PHÁ PHA

### V1.1 Funding — Van tay quan trọng nhất

**FUNDING PINNED 0.00005 TUYỆT ĐỐI — từ 01/05 đến 05/08, không một ngày nào bùng.**

```
01/05-08/04: avg=0.00005, n=6/ngày, [min, max] gần như [0.00005, 0.00005]
Ngoại lệ nhỏ: 05/04 min=-0.00002 (1 tick âm), 06/28 min=-0.00001 — đều insignificant
08/04: avg=0.00004 (n=6, đang suy giảm nhẹ)
08/05: avg=0.00005 (1 tick mới nhất)
```

So sánh:
- BANK: funding bùng 23bps trong markup
- CLO: funding bùng 90bps, 86bps
- TUT: **ZERO burst qua toàn bộ 97 ngày, kể cả qua +149% markup**

→ Đây là van tay cực kỳ độc đáo. Funding pinned xuyên markup = không có crowd overheating trên perp = MM control hoàn toàn. Loại trừ mọi kịch bản crowd-driven rally.

### V1.2 Phase timeline

| Phase | Ngày | Price range | Vol | OI | Mô tả |
|---|---|---|---|---|---|
| **LISTEN/QUIET** | 01-02/05 | 0.01062-0.01093 | 0.75-1.22M | ABSTAIN | Flat, vol cực thấp |
| **CHƯƠNG 1 MARKUP** | 03-04/05 | → H=0.01450 | 11.5M + **29.7M** | ABSTAIN | Debut burst |
| **C1 FLUSH + GRIND** | 05/05-28/05 | 0.00943-0.01411 | 0.87-10.5M | ABSTAIN | Bleed từ H xuống 0.00971 |
| **BAIT/TEST** | 04-07/06 | 0.00955 → 0.01074 | 3.5-10.2M | ABSTAIN | Jun bounce bị dump |
| **NỀN CHÍNH** | 08/06-26/06 | 0.00957-0.01081 | 0.58-2.65M | ABSTAIN | Low-vol consolidation |
| **NỀN CÓ DATA** | 27/06-08/07 | 0.01000-0.01090 | 0.66-2.00M | **2.020-2.352M** | gLSR 2.81-3.64 (!!) |
| **IGNITION** | 09-11/07 | 0.00964 → 0.01276 | 3.1-14.0M | 1.922→2.600M | +32.3% trong 3 ngày |
| **LOCAL TOP + WASH** | 12/07 | H=0.01311, close 0.01224 | 4.9M | **3.269M** (+0.669M trên RED) |
| **GRIND UP** | 13-26/07 | 0.01224 → 0.01622 | 0.93-2.43M | 2.712→4.006M | +32.5%, vol thấp |
| **LOCAL DUMP** | 27-29/07 | 0.01622 → 0.01439 | 1.49-2.43M | 3.683-4.202M | -11.3% |
| **ACCELERATION** | 30/07-05/08 | 0.01439 → 0.02403 | 1.13-33.25M | 3.752→**6.344M** | +66.9% |

### V1.3 Số chuỗi đầy đủ (merged, từ ngày có data)

| date | px | color | vol(M) | tk% | OI(M) | ΔOI(M) | gLSR | pos_r | acc_r | f_avg |
|---|---|---|---|---|---|---|---|---|---|---|
| 27/06 | 0.01025 | RED | 0.66 | 46.6% | 2.352 | — | 3.115 | 4.367 | 4.628 | 0.00004 |
| 28/06 | 0.01041 | GRN | 0.84 | 48.7% | 2.238 | -0.115 | 3.548 | 3.897 | 5.297 | 0.00004 |
| 29/06 | 0.01036 | RED | 0.87 | 48.8% | 2.211 | -0.027 | 3.259 | 4.630 | 4.787 | 0.00005 |
| 30/06 | 0.01037 | GRN | 1.24 | 47.2% | 2.229 | +0.018 | 3.643 | 4.721 | 5.447 | 0.00005 |
| 01/07 | 0.01073 | GRN | 0.89 | 51.4% | 2.240 | +0.011 | 3.301 | 4.573 | 4.747 | 0.00005 |
| 02/07 | 0.01049 | RED | 1.21 | 40.9% | 2.319 | +0.079 | 3.058 | 4.515 | 4.238 | 0.00005 |
| 03/07 | 0.01106 | GRN | 0.93 | 50.6% | 2.286 | -0.032 | 3.195 | 4.244 | 4.577 | 0.00005 |
| 04/07 | 0.01120 | GRN | 1.05 | 47.0% | 2.339 | +0.053 | 3.134 | 4.490 | 4.333 | 0.00005 |
| 05/07 | 0.01090 | RED | 2.47 | 50.4% | 2.275 | -0.064 | 3.160 | 4.446 | 4.574 | 0.00005 |
| 06/07 | 0.01014 | RED | 2.00 | 43.0% | 2.244 | -0.031 | 2.946 | 4.104 | 3.819 | 0.00005 |
| 07/07 | 0.01000 | RED | 1.76 | 47.9% | 2.167 | -0.077 | 2.810 | 3.264 | 3.780 | 0.00005 |
| 08/07 | 0.00965 | RED | 0.84 | 50.2% | **2.020** | -0.147 | 2.857 | 3.148 | 3.682 | 0.00005 |
| **09/07** | **0.01062** | GRN | **3.12** | 50.0% | **1.922** | -0.098 | 2.997 | 3.459 | 4.187 | 0.00005 |
| 10/07 | 0.01162 | GRN | 1.66 | 53.2% | 2.328 | +0.406 | 2.529 | 3.519 | 3.350 | 0.00005 |
| 11/07 | 0.01276 | GRN | **14.05** | 49.6% | 2.600 | +0.272 | 2.180 | 4.204 | 2.855 | 0.00005 |
| 12/07 | 0.01224 | RED | 4.90 | 49.6% | **3.269** | **+0.669** | **1.195** | 3.038 | 1.343 | 0.00005 |
| 13/07 | 0.01252 | GRN | 2.13 | 48.6% | 2.774 | **-0.495** | 1.562 | 4.620 | 1.915 | 0.00005 |
| 14/07 | 0.01253 | GRN | 1.30 | 47.8% | 2.712 | -0.062 | 1.595 | 5.475 | 2.062 | 0.00004 |
| 15/07 | 0.01293 | GRN | 1.56 | 52.2% | 2.708 | -0.003 | 1.767 | 5.812 | 2.189 | 0.00005 |
| 16/07 | 0.01300 | GRN | 1.38 | 48.5% | 2.893 | +0.185 | 1.990 | 5.706 | 2.465 | 0.00005 |
| 17/07 | 0.01329 | GRN | 1.28 | 46.5% | 2.808 | -0.085 | 1.979 | 5.678 | 2.454 | 0.00005 |
| 18/07 | 0.01336 | GRN | 0.93 | 47.6% | 3.030 | +0.222 | 1.946 | 5.048 | 2.470 | 0.00005 |
| 19/07 | 0.01302 | RED | 0.66 | 48.8% | 3.162 | +0.132 | 1.772 | 4.921 | 2.312 | 0.00005 |
| 20/07 | 0.01424 | GRN | 2.41 | 48.9% | 3.089 | -0.073 | 1.910 | 4.725 | 2.433 | 0.00005 |
| 21/07 | 0.01508 | GRN | 5.27 | 49.4% | 3.413 | +0.324 | 1.896 | 4.305 | 2.466 | 0.00005 |
| 22/07 | 0.01373 | RED | 2.50 | 42.7% | **3.764** | **+0.351** | 1.779 | 3.887 | 2.233 | 0.00005 |
| 23/07 | 0.01404 | GRN | 1.34 | 49.2% | 3.387 | -0.377 | 1.729 | 5.083 | 2.308 | 0.00005 |
| 27/07 | 0.01489 | RED | 1.49 | 48.1% | 4.202 | +0.195 | 1.904 | 4.333 | 2.481 | 0.00005 |
| 28/07 | 0.01448 | RED | 2.43 | 45.1% | 3.738 | -0.464 | 2.018 | 4.657 | 2.779 | 0.00005 |
| 29/07 | 0.01439 | RED | 2.23 | 51.0% | 3.683 | -0.054 | 1.922 | 4.911 | 2.525 | 0.00005 |
| 30/07 | 0.01506 | GRN | 1.13 | 47.7% | 3.752 | +0.068 | 1.851 | 4.585 | 2.405 | 0.00005 |
| 31/07 | 0.01610 | GRN | 2.39 | 51.5% | 3.899 | +0.147 | 1.857 | 4.959 | 2.359 | 0.00005 |
| 01/08 | 0.01752 | GRN | **9.82** | 52.0% | 4.294 | +0.395 | 2.031 | 4.169 | 2.430 | 0.00005 |
| 02/08 | 0.01757 | GRN | 3.06 | 47.6% | 4.997 | **+0.704** | 1.721 | 3.458 | 2.103 | 0.00005 |
| 03/08 | 0.02038 | GRN | **17.95** | 52.7% | 4.831 | -0.167 | 1.685 | 4.014 | 2.206 | 0.00005 |
| 04/08 | 0.02157 | GRN | **33.25** | 48.6% | 5.672 | +0.841 | 1.438 | 2.830 | 1.591 | 0.00004 |
| **05/08** | **0.02403** | GRN | 3.68 | 49.8% | **6.344** | **+0.672** | ABSTAIN | ABSTAIN | ABSTAIN | 0.00005 |

---

## V2 — CỬA SỔ GOM + VỐN GOM

### V2.1 Pre-ignition state (27/06 — earliest data)

Khi freshwatch bắt đầu coverage (27/06):
- OI đã = **2.352M** — không phải 0
- gLSR = **3.115** → pos_r = **4.367** (4.4 longs cho mỗi 1 short theo position!)
- Giá = 0.01025 (nền thấp)

**Kết luận**: Đến 27/06, TUT đã có một khối lượng perp long rất lớn so với size thị trường. Tích lũy perp PHẢI đã xảy ra trong tháng 5-6 (trước khi freshwatch coverage bắt đầu). Không thể verify số cụ thể → ABSTAIN cho OI tuyệt đối pre-27/06.

### V2.2 ΔOI+ trên nến đỏ/giá phẳng (V2a perp gom signal)

Từ data có được (07/06+):

| Date | Color | ΔOI (M) | gLSR | Đọc |
|---|---|---|---|---|
| 02/07 | RED | +0.079 | 3.058 | Nhỏ, gom ngầm vào dump |
| **12/07** | RED | **+0.669** | **1.195** | WASH-BY-CRASH: OI nổ +20% trên nến đỏ (LOCAL TOP) |
| 19/07 | RED | +0.132 | 1.772 | Gom thêm vào ngày đỏ nhỏ |
| **22/07** | RED | **+0.351** | 1.779 | Gom mạnh vào dump -9% (local top 2) |
| 27/07 | RED | +0.195 | 1.904 | Gom vào dump -8.2% |
| **02/08** | GRN | **+0.704** | 1.721 | OI spike lớn nhất (+14%) trên ngày tăng nhẹ |
| **04/08** | GRN | **+0.841** | 1.438 | OI spike +17% trên vol 33M (acceleration) |
| **05/08** | GRN | **+0.672** | ABSTAIN | OI spike +12% tiếp tục |

**Điểm đặc biệt ngày 12/07:**
- OI nhảy từ 2.600M → 3.269M (+0.669M = +26%) trên NẾN ĐỎ (price -4.1%)
- gLSR sụp từ 2.180 → **1.195** (SHORT-WASH: crowd shorts flood in, OI nổ = new shorts opening)
- Đây là "fuel-reload" moment: MM không exit mà crowd SHORT vào → MM bán cho shorts, sau đó tiếp tục squeeze

**Nhận xét quan trọng**: ΔOI+ trên nến đỏ = crowd mở SHORT (bán vào price dip). MM có thể:
(a) Đang MUA perp long từ shorts ngắn hạn (net: MM longs tăng, OI tăng)
(b) Crowd shorts đóng vai trò counterparty — khi price hồi họ sẽ bị squeeze

### V2.3 Spot gom — Controlled fill signals (V2b)

Từ klines 1d, pre-ignition window:
```
Pre-ignition avg daily vol: $2.58M
```

Controlled fill candidates (taker 44-51%, vol >1.5× avg, |ret| <6%):

| Date | Color | px | ret | vol | vol_ratio | tk% | Đọc |
|---|---|---|---|---|---|---|---|
| **05/05** | RED | 0.01306 | -5.8% | 10.52M | **4.1×** | 46.9% | Post-C1 absorption: vol lớn, giá không sụp thêm, taker neutral |
| **07/05** | GRN | 0.01334 | +4.2% | 5.24M | 2.0× | 49.0% | Recovery with elevated vol, neutral taker |
| **09/05** | RED | 0.01367 | -0.9% | 4.23M | 1.6× | 47.5% | Flat day với vol cao, neutral = absorption |

**Window 05-09/05 là controlled fill quan trọng nhất:**
- Post-Campaign 1 dump (từ 0.01450 về 0.01367)
- Vol tổng 3 ngày: 10.52 + 5.24 + 4.23 = **19.99M** trong 5d window
- Taker% trung bình: 47.8% (rất neutral)
- Price không rơi xuống dưới 0.01267 (floor được hứng)

**Interpretation**: 3 ngày sau Campaign 1, có lực mua THẬT hấp thụ volume bán ra. Loại C pattern: mua spot ở giá post-markup (0.013-0.014) sau khi crowd đã sell.

Venue spot: TUT **KHÔNG** có trên Binance Alpha store (ALPHA_117 absent). Spot trading qua:
- BSC DEX: TUT/WBNB 1% pool (liq=$2.37M, vol24h=$1.17M) — venue chính
- TUT/USDT 0.25% pool: liq=$23k (tiny)

### V2.4 BẢNG VỐN GOM — Tổng hợp (V2c)

| Component | Window | VWAP ước | Capital/Vol | Data quality | Ghi chú |
|---|---|---|---|---|---|
| **Perp Window A** | May 01-28 (quiet 16d) | ~0.01164 | 22.2M vol | klines only, OI ABSTAIN | Bao gồm post-C1 retracement |
| **Perp Window B** | Jun 01-26 (excl. spikes) | ~0.01030 | ~39M vol | klines only, OI ABSTAIN | Nền chính, giá 0.0096-0.0108 |
| **Perp Window C** | Jul 01-08 | **0.01076** | 8.6M vol | klines + freshwatch OI | OI confirmed 2.020-2.352M |
| **B_T0 (ignition)** | 09/07 | — | — | freshwatch + fapi OI | **1.922M** = baseline chính |
| **Spot accumulation** | May 05-09 | ~0.01340 | ~20M perp proxy | klines controlled fill | Không có spot-specific data |
| **Spot (BSC DEX)** | N/A | ABSTAIN | ABSTAIN | GeckoTerminal no history | Venue xác nhận: TUT/WBNB |

**VWAP GOM TỔNG (ước, perp blend):**
```
Blend: 30% Window A (0.01164) + 50% Window B (0.01030) + 20% Window C (0.01076)
= 0.003492 + 0.005150 + 0.002152 = 0.01079 USDT

Build_VWAP_tổng ≈ 0.01079 USDT (floor kinh tế perp MM)
```

**OI trajectory (phần có data):**
```
27/06: 2.352M (baseline đầu tiên, gLSR=3.115 → đã tích lũy nhiều)
09/07: 1.922M (B_T0 — dip trước ignition)
12/07: 3.269M (local peak week 1)
22/07: 3.764M (local peak week 2)
05/08: 6.344M (LATEST, đang build)

ΔOI từ B_T0: 6.344 - 1.922 = +4.422M = **+2.30×B_T0**
```

**Vốn perp ước (nếu MM chiếm 50% ΔOI build):**
- ΔOI build = 4.422M, MM 50% = 2.211M USD danh nghĩa
- Nếu dùng 5× leverage: capital thật = $442k
- Nếu 10×: capital thật = $221k
- Nếu 2×: capital thật = $1.1M

**Ô PENDING OPERATOR:**
- O1: Total supply TUT → tính K = 83% kho (số tuyệt đối)
- O2: Cost basis spot (cụm ví gom, BscScan/Nansen) → so với VWAP 0.01079 có lợi không?
- O3: Exchange balance history (1Y) để xác nhận timing gom

---

## V3 — LỊCH SỬ CAMPAIGN (TUT là chương mấy?)

**TUT = Chương 3 (campaign đang chạy), trước đó 1 markup thật + 1 bait:**

### Chương 1 (Debut Markup): 03-04/05/2026

| | Số |
|---|---|
| Build px pre-spike | 0.01062-0.01093 (01-02/05, 2 ngày quiet) |
| Ignition | 03/05: +6.3% (11.5M vol), 04/05: +19.4% (**29.7M vol**) |
| Peak price | H=0.01450 (04/05) |
| px_mult | 0.01450/0.01063 = **1.37×** (modest) |
| Vol spike | 20.6× median |
| Funding | PINNED 0.00005 |
| OI | ABSTAIN (pre-coverage) |
| Wash ngay sau | 05/05: -5.8% (10.5M vol), partial flush |
| Recovery | 07-11/05: bounce 0.01280→0.01411 |
| Bleed | 12/05→28/05: 0.01411→0.00943 (-33%) slow |

**Assessment C1**: Markup ngắn (2 ngày), biên độ nhỏ (37%). Không có OI data. Funding pinned hoàn toàn. Rất có thể là *volume test* / *market probe* để xem depth trước khi chuẩn bị Campaign 3.

### Bait/Test: 04-07/06/2026 (không phải campaign)

- Jun 04: 3.54M vol (2.5×), RED, -0.7% ở 0.00955 → bottom test
- Jun 05: **10.23M vol** (7.1×), GRN, +9% 
- Jun 06: 5.59M, GRN, +3.2%
- Jun 07: 4.57M (3.2×), RED, **-6.5%** → DUMP sau bounce
- Pattern: Pump → dump trong 3d, không sustain → BAIT/WASH

**Assessment**: Không phải campaign thật. Giá không vượt C1 high (0.01450). Dùng để xả lượng nhỏ + kiểm tra độ chịu đựng của crowd.

### Chương 3 (MAIN CAMPAIGN — đang chạy): 09/07/2026→nay

- **Serial**: CLO có 3 campaigns full trong 5 tháng; TUT có 1 campaign nhỏ (C1) → 1 bait → 1 main = ít serial hơn, main là lần đầu tiên ở scale này
- Giai đoạn tích lũy dài hơn (ít nhất 2 tháng Jun-Jul) → consistent với Loại C (cần thời gian build kho + perp)
- Không có mini-cycle giữa C1 và C3 → KHÔNG serial như CLO

---

## V4 — TIẾN ĐỘ MONETIZE

### V4.1 Venue spot (xác nhận trước)

| Venue | Liq | Vol24h (05/08) | Status |
|---|---|---|---|
| TUT/WBNB 1% BSC (0x6dafbf) | $2,370,825 | $1,172,717 | **MAIN DEX** |
| TUT/USDT 0.25% BSC (0x27ad51) | $23,438 | $44,467 | Nhỏ |
| Binance Alpha (ALPHA_117) | NOT IN STORE | ABSTAIN | Không collect được |
| Binance perp (TUTUSDT) | 6.344M OI | ~17.95M vol (03/08) | Perp venue |

Spot trading chủ yếu qua BSC DEX (TUT/WBNB). Không có Binance spot listing.

### V4.2 px+/OI− signals (thoát perp từng phần)

Từ V4 scan:

| Date | Color | ret | OI Δ | Vol | Đọc |
|---|---|---|---|---|---|
| **13/07** | GRN | +2.3% | **-0.495M (-15%)** | 2.13M | EXIT LỚN: 07/12 LOCAL TOP → MM thoát một phần |
| 14/07 | GRN | +0.1% | -0.062M | 1.30M | Nhỏ, tiếp tục thoát |
| **15/07** | GRN | +3.2% | -0.003M | 1.56M | Gần như flat |
| 17/07 | GRN | +2.2% | -0.085M | 1.28M | Thoát nhỏ |
| **20/07** | GRN | +9.4% | -0.073M | 2.41M | Exit nhỏ vào ngày pump mạnh |
| **23/07** | GRN | +2.3% | -0.377M (-10%) | 1.34M | Exit đáng kể post local-top |
| **03/08** | GRN | **+16%** | **-0.167M (-3%)** | **17.95M** | Exit nhỏ vào ngày pump lớn nhất |

**Nhận xét:**
- Tổng OI giảm trên GRN days: ~0.495+0.062+0.003+0.085+0.073+0.377+0.167 = **~1.26M USD** đã được thoát trên các px+ days
- Nhưng sau đó OI BUILD back lên mạnh hơn (từ 2.712M → 6.344M = +3.63M)
- Kết luận: **Thoát là partial/tactical**, toàn bộ vị thế chưa exit. OI đang ở ATH.

### V4.3 gLSR trajectory → Monetize signal

```
27/06: gLSR = 3.115, pos_r = 4.367  ← Baseline (crowd cực long)
09/07: gLSR = 2.997                  ← Ignition, crowd still long
12/07: gLSR = 1.195                  ← SHORT-WASH tại local top week 1 (!!)
13/07: gLSR = 1.562                  ← Bounce sau wash
22/07: gLSR = 1.779                  ← Local top 2, crowd bắt đầu short
04/08: gLSR = 1.438                  ← Declining (crowd adding shorts)
05/08: ABSTAIN (no freshwatch yet)
```

**Cơ chế đang diễn ra:**
- gLSR giảm từ 3.115 → 1.438 trong khi OI tăng từ 2.352M → 6.344M
- Điều này có nghĩa: NEW SHORTS đang vào thị trường (crowded-short bet: crowd nghĩ price sẽ rơi)
- MM có thể CLOSE LONG PERP vào incoming shorts = exit không làm OI drop (vì 1 long đóng = 1 short mở, net OI có thể tăng)
- Đây là CỬA B: MM đang dần exit perp bằng cách bán cho crowd shorts

**Ước tính: MM đã monetize bao nhiêu % kho perp?**
```
B_T0 OI tokens: 199,403,957 tokens (07/09, từ fapi)
Nếu MM = 50% OI = ~100M tokens long
07/13 exit: -0.495M USD / 0.01252 px = -39.5M tokens đóng
→ 39.5/100M = ~39.5% của OI ban đầu đã exit tại 0.01252

Nhưng MM đã rebuild/add nhiều hơn:
Current OI: 294M tokens (05/08) vs 199M (07/09) = +95M tokens thêm vào
→ Nếu MM giữ 50%: ~147M tokens hiện tại

Thực tế: tất cả đây là ước tính. Không biết exact split MM vs crowd.
```

**Verdict V4 (một dòng):** Monetize đang diễn ra PARTIAL — ước 10-20% thoát trên các px+/OI- days. OI đang ở ATH (6.344M). Campaign CHƯA KẾT THÚC. Còn ~80-90% position chưa exit (cả perp lẫn spot).

### V4.4 Đồng hồ Cửa A (bao lâu hype cần thiết để xả kho spot)

```
Venue chính: TUT/WBNB BSC pool
  Liquidity pool: $2,370,825
  Vol 24h: $1,172,717
  
Stealthy sell capacity: 10% pool liq/day = $237,082/day
Conservative: 10% daily vol = $117,272/day
Range: $117k - $237k / ngày

K_spot = 83% total supply = X tokens (PENDING OPERATOR — O1)
Giá hiện tại: $0.02403

Nếu K_spot tương đương $5M:  $5M / $177k avg = ~28 ngày
Nếu K_spot tương đương $10M: $10M / $177k avg = ~57 ngày (~2 tháng)
Nếu K_spot tương đương $20M: $20M / $177k avg = ~113 ngày (~4 tháng)
```

Campaign bắt đầu 09/07, nay 05/08 = 27 ngày. Nếu cần 57-113 ngày, TUT đang ở **giữa đường** (27/57 = 47% hoặc 27/113 = 24%).

### V4.5 Dấu Cửa B (short-hedge sau đỉnh cục bộ)

| Local top | Ngày | gLSR | pos_r | OI | Đọc |
|---|---|---|---|---|---|
| Local top 1 | 12/07 | **1.195** | 3.038 | 3.269M | SHORT-WASH mạnh: crowd short flood vào |
| Post-L1 | 13-15/07 | 1.56-1.77 | 4.62-5.81 | 2.71-2.77M | Phục hồi, longs đóng đã re-enter |
| Local top 2 | 22/07 | 1.779 | 3.887 | 3.764M | Short hedge nhẹ hơn (gLSR ít sụp hơn) |
| Acceleration | 02-04/08 | 1.44-1.72 | 2.83-3.46 | 4.83-5.67M | gLSR tiếp tục giảm trong khi OI build |

**Dấu Cửa B xác nhận:** gLSR declining + OI building = crowd đang mở SHORT (bet against price). Mỗi short mới = một đối tác để MM bán long vào. Đây là cấu trúc harvest chuẩn: crowd short → MM close long → crowd bị squeeze sau → tiếp tục.

---

## V5 — CHẤM LẠI P1-P5 DƯỚI ÁNH SÁNG LOÀI C

### Context P1-P5 gốc (04/08/2026, frozen)

| # | Prediction | Deadline | Status hôm nay (05/08) |
|---|---|---|---|
| P1 | Exit_px [0.025, 0.035] trước L-26 | Trước 22/08 | **TRACKING** — px=0.02403, sắp chạm P1-low (0.025) |
| P2 | L-26 trigger (pos_r drop 30%/3d) trước 22/08 | 22/08 | **TRACKING** — pos_r=2.830, declining nhưng chưa 30%/3d |
| P3 | OI_exit 8-12M tại L-26 | Tại L-26 | **TRACKING** — OI=6.344M, cần +1.66M để đạt 8M (P3-low) |
| P4 | L-26 window 12/08-25/08 | 25/08 | **TRACKING** — 7 ngày nữa đến window start |
| P5 | Kho TREO | TREO | Vẫn TREO |

### Điều chỉnh P1-P5 theo Loài C

**P1 — Floor kinh tế (%):**
Gốc: P1-low=0.01928 (build_VWAP 0.01285 × 1.5)
Cập nhật từ V2c: build_VWAP_tổng = **0.01079** (toàn bộ khung)
Floor kinh tế Loại C: **0.01079** (= điểm MM break even trên perp)
P1-low của forward doc (0.01928) = **1.79× build_VWAP_tổng** — đã breached (px=0.02403 = 2.23×)

**P3 — OI_clock bands (Loại C adjustment):**
```
B_T0 = 1.922M
P3-bands (từ forward doc): 5×B = 5×1.922 = 9.61M; 7×B = 13.45M

Tình trạng 05/08: OI = 6.344M = 3.30×B_T0
Còn cần:
  → 5×B = 9.61M: cần +3.27M (tại tốc độ 0.5M/day ≈ 6-7 ngày)
  → 7×B = 13.45M: cần +7.11M
  
Ghi chú: TUT là điểm dữ liệu ĐẦU TIÊN cho CROWD-LONG subtype (chưa calibrate).
Không có prior reference cho OI_exit band của Loại C.
```

**P3 CLOCK TABLE (cập nhật):**

| ΔOI/B | OI target (M) | Status |
|---|---|---|
| 1× | 3.844 | PASSED (13/07) |
| 1.5× | 4.805 | PASSED (02/08) |
| 2× | 5.766 | PASSED (04/08) |
| **2.30×** | **6.344** | **HIỆN TẠI (05/08)** |
| 3× | 7.688 | ~6-7 ngày nữa |
| 5× | 11.532 | PENDING (2-3 tuần?) |
| 7× | 15.376 | PENDING |

**Nhận xét quan trọng**: TUT đang bước vào vùng 2×-3× rất nhanh (từ B_T0 09/07 đến 05/08 = 27 ngày đã đạt 2.30×). Nếu tiếp tục ở tốc độ này, 3×B sẽ đạt trong 1-2 tuần.

**P2 — L-26 dưới Loại C lens:**
```
pos_r hiện tại: 2.830 (04/08)
L-26 trigger: drop 30%/3d
3d về trước (01/08): pos_r = 4.169
Drop: (4.169-2.830)/4.169 = -32.1% → L-26 TRIGGERED ngày 04/08!
```

**WAIT — kiểm tra lại:**
- 01/08: pos_r = 4.169
- 02/08: pos_r = 3.458
- 03/08: pos_r = 4.014 (bounce)
- 04/08: pos_r = 2.830

From 01/08 to 04/08 = 3 days. Drop = (4.169-2.830)/4.169 = -32.1%.

**L-26 CÓ THỂ ĐÃ TRIGGER NGÀY 04/08.** Cần verify với freshwatch 05/08 (có sẵn: px=0.02403, vol=3.68M, OI=6.344M, fn=1 — partial day).

Nếu L-26 triggered 04/08:
- P2 deadline = trước 22/08 → PASS (triggered sớm hơn dự báo)
- P4 window (12/08-25/08) = FAIL on timing (triggered 04/08, không phải 12-25/08)
- P1 at L-26: px=0.02157 (04/08) hoặc 0.02403 (05/08) → trong dải [0.025, 0.035]? 0.02157 < 0.025 → MISS P1-low. 0.02403 ≈ đang tiến vào. Nếu L-26 là 05/08: px=0.02403 vẫn hơi dưới P1-low 0.025.

→ Cần freshwatch 05/08 fn=6 để confirm L-26. Hiện tại fn=1 (stale).

**P5 — Kho TREO:** Vẫn TREO (Nansen locked, BscScan pending operator).

### V5 tóm tắt P1-P5

| | Gốc (04/08) | Cập nhật (05/08 Loại C lens) |
|---|---|---|
| **Floor kinh tế** | 0.01928 (P1-low) | **0.01079 (build_VWAP_tổng)** — đã xa bên dưới px hiện tại |
| **P1** | [0.025, 0.035] | Sắp đạt P1-low. P1-high (0.035) vẫn là target hợp lý |
| **P2 (L-26)** | Trước 22/08 | **Có thể đã trigger 04/08** (pos_r -32.1%/3d) — VERIFY 05/08 fn=6 |
| **P3 (OI clock)** | 8-12M | OI=6.344M, đang build. Bands 5×B=9.6M cần 6-7d nữa |
| **P4 (window)** | 12-25/08 | Nếu P2 trigger sớm (04/08): P4 REVISED to 04-10/08 |
| **P5 (kho)** | TREO | TREO |

---

## V6 — OUTPUT: BẢNG TRỌNG TÂM + CHỐT CANH

### V6.1 Bảng vốn gom (trọng tâm V2c)

| # | Component | VWAP ước | Capital ước | Độ tin cậy |
|---|---|---|---|---|
| 1 | Perp build VWAP tổng (Blend A+B+C) | **0.01079 USDT** | N/A (leverage unknown) | MEDIUM (Bound B+C from data) |
| 2 | Build B_T0 (09/07 OI base) | 0.01062 px at ignition | 1.922M OI USD | HIGH (freshwatch confirmed) |
| 3 | Controlled fill spot (05-09/05) | ~0.01340 | 20M perp vol proxy | LOW (no spot-specific venue) |
| 4 | Spot kho K (83%) | PENDING O1 | PENDING | PENDING |
| 5 | Spot DEX venue | BSC TUT/WBNB | $237k/day stealthy max | MEDIUM (GeckoTerminal snapshot) |

**Floor kinh tế MM (perp): 0.01079 USDT**
→ Tại px hiện tại 0.02403: unrealized gain = +122.5% trên perp long

### V6.2 Timeline V3

```
Chương 1 (Probe campaign): 03-04/05, px_mult=1.37×, vol 41M — ngắn, thử thị trường
Bait/Test: 04-07/06, vol 19M — không sustain
Chương 3 (MAIN): 09/07→nay (27 ngày), OI 1.922→6.344M (+2.30×B), px +149%
```

### V6.3 Verdict V4 (một dòng)

**Đã monetize ~15-20% kho perp (ước, partial exits trên GRN days); spot chưa exit (DEX thin, PENDING on-chain confirm). OI đang ở ATH 6.344M. Campaign tiếp tục.**

### V6.4 Chốt canh cập nhật (05/08)

| # | Chốt | Điều kiện | Tình trạng |
|---|---|---|---|
| 1 | **L-26 CONFIRM** | pos_r 05/08 fn=6: 30% drop vs 01/08 (4.169) | Cần freshwatch 05/08 fn=6 |
| 2 | **OI 8M (P3 band 1)** | OI ≥ 8M = approach 5×B | OI=6.344M, ~6-7d nữa ở tốc độ hiện tại |
| 3 | **gLSR < 1.5** | Đang ở 1.44 (04/08) — tiếp tục declining | ĐANG THEO DÕI — gần ngưỡng |
| 4 | **P1-low 0.025** | px cần ≥ 0.025 | px=0.02403, cách 0.0010 = +4% nữa |
| 5 | **Funding burst** | f_avg > 0.00010 sustained | Vẫn PINNED (van tay đặc biệt) |
| 6 | **DEX dump signal** | TUT/WBNB pool size giảm đột ngột + 24h vol spike >3M | Snapshot hiện tại bình thường |

**Bổ sung vào chốt canh (Loại C specific):**
- Floor kinh tế: px < 0.01079 = MM thủng vốn (không likely, but trigger để đọc lại)
- 04/08 vol 33.25M + 05/08 vol 3.68M = acceleration tháo ra nhanh? → Watch ngày 06-07/08 vol + OI delta

---

## PENDING OPERATOR — DANH SÁCH Ô CHỜ

| # | Mục | Ảnh hưởng |
|---|---|---|
| O1 | Total supply TUT (CoinGecko/BscScan) | K_spot = 83% × supply → calibrate đồng hồ Cửa A |
| O2 | Cụm ví gom TUT (BscScan, Nansen cost basis) | Verify V2c, confirm Loại C |
| O3 | Exchange balance history 1Y | Timing tích lũy, confirm Window A/B |
| O4 | freshwatch 05/08 fn=6 (confirm L-26) | P2/P4 verdict |
| O5 | Alpha_117 store check VPS bapi endpoint | Spot vol data nếu có |

---

## AGENT LOG ENTRY

```
[TUT-FORENSIC-20260805]
Probe: _probe_tut_forensic_20260804.py → scratch/tut_forensic_20260804.txt
Nguồn:
  - VPS: 0 files TUTUSDT → ABSTAIN pre-27/06 cho OI/LSR
  - freshwatch: 36 rows (27/06→04/08)
  - fapi klines 1d: 97 rows (01/05→05/08)
  - fapi fundingRate: 576 rows — PINNED 0.00005 TUYỆT ĐỐI 97 ngày
  - fapi OI daily: 31 rows (06/07→05/08)
  - GeckoTerminal BSC: TUT/WBNB liq=$2.37M, vol24h=$1.17M (MAIN SPOT VENUE)
  - Alpha store: TUT NOT IN STORE (ALPHA_117 absent)

Key findings:
- Funding PINNED 0.00005 100% — van tay unique: funding không bùng kể cả qua +149% markup
- gLSR đã ở mức cao cực cao (3.115) từ 27/06, declining đến 1.44 (04/08)
  → Crowd đang mở SHORT vs price → MM đang close long vào shorts
- L-26 CÓ THỂ ĐÃ TRIGGER 04/08: pos_r drop -32.1%/3d (01/08 4.169 → 04/08 2.830)
  → CẦN VERIFY freshwatch 05/08 fn=6
- OI trajectory: 1.922M (B_T0 09/07) → 6.344M (05/08) = +2.30×B
  → P3 band 5×B = 9.61M (est. 6-7 ngày nữa)
- Monetize: ~15-20% partial exits (GRN/px+/OI- days). Chưa full exit.
- Chương 3 (main campaign). C1 (03-04/05) là volume probe. Bait (04-07/06).
- Build_VWAP_tổng = 0.01079. Floor kinh tế = 0.01079.
- PENDING: O1 supply, O2 cụm ví, O3 exchange balance, O4 05/08 fn=6

Output: docs/proposals/tut_forensic_20260805.md
Probe archived: scripts/archive/_probe_tut_forensic_20260804.py
```

# CLO — Thesis Test: Spot-Đạo-Cụ / Két Perp 2 Campaign
**Soạn: 04/08/2026 | ANALYSIS only | Frozen cho verdict operator ký**

---

## NGUỒN DỮ LIỆU

| Nguồn | Phủ | Trạng thái |
|---|---|---|
| freshwatch_daily | 53 rows 05/06–03/08 | OK |
| fapi klines 1d | 01/03→04/08 (157 ngày) | OK |
| fapi fundingRate | 01/04→04/08 (753 rows) | OK |
| fapi OI daily (futures/data) | 05/07–04/08 (31 rows) | OK |
| GeckoTerminal DEX | BSC pools | OK |
| On-chain (kho, outflow) | R4 PENDING operator | TREO |
| VPS klines_1h CLOUSDT | SSH fail (script syntax) | UNKNOWN |
| Spot Binance klines | 400 error (futures-only pair) | N/A |

**freshwatch dist_wall / lsr_dist**: 100% empty ("—") cho toàn bộ 53 rows CLO. Không thể đánh giá hai signal này.

---

## C1 — CHUỖI 22/07→04/08

### C1.1 Series tích hợp

| date | px | OI(M) | vol(M) | tk% | pos_r | acc_r | gLSR | fav | fn |
|---|---|---|---|---|---|---|---|---|---|
| 07-22 | 0.10904 | 4.084 | 27.9* | 49.5%* | 0.905 | 1.109 | **0.8657** | -0.00002 | 6 |
| 07-23 | 0.12360 | 4.049 | 94.8* | 48.3%* | 0.909 | 1.196 | 0.9608 | +0.00005 | 6 |
| 07-27 | 0.11787 | 4.365 | 5.1 | — | 0.921 | 1.513 | 1.1829 | +0.00005 | 6 |
| 07-28 | 0.12091 | 4.347 | 3.2 | — | 0.899 | 1.628 | 1.2558 | +0.00005 | 6 |
| 07-29 | 0.12855 | 4.172 | 8.2 | — | 0.870 | 1.705 | 1.4010 | +0.00008 | 6 |
| 07-30 | 0.12249 | 4.281 | 3.5 | — | 0.916 | 1.614 | 1.4149 | +0.00005 | 6 |
| 07-31 | 0.12081 | 4.175 | 1.7 | — | 0.912 | 1.973 | 1.6738 | +0.00007 | 6 |
| 08-01 | 0.12495 | 4.177 | 2.9 | — | 0.920 | 2.396 | 1.9612 | +0.00010 | 6 |
| 08-02 | 0.12835 | 4.441 | 2.3 | — | 0.883 | 2.663 | **2.2949** | +0.00006 | 6 |
| 08-03 | 0.13508 | 4.633 | 6.6 | — | 0.854 | 2.894 | **2.6483** | +0.00021 | 6 |
| 08-04* | 0.12045 | 4.457 | 4.1* | 46.8%* | — | — | — | — | — |

*= từ fapi klines (freshwatch lag 1 ngày)

### C1.2 Signal checklist

**dist_wall còn sống?** → KHÔNG XÁC ĐỊNH — freshwatch không có data cột này cho CLO (tất cả "—").

**lsr_dist còn?** → KHÔNG XÁC ĐỊNH — tương tự, cột trống toàn bộ.

**Điều kiện tái xét cũ (pin 5d + pos>1 + outflow tại nền):**
- pos_r: 0.854–0.921, trend giảm dần. **KHÔNG ĐẠT** (pos>1 chưa hội tụ)
- OI: 4.1–4.6M stable. **PARTIAL** — không bùng nổ, không xả hết
- 5d pin quanh 0.120–0.135: YES — price stuck ≥7 tuần
- outflow tại nền: **PENDING OPERATOR** (R4, cần on-chain)

→ Điều kiện tái xét OLD PACKET: 2/4 met, 1 PENDING, 1 FAIL.

**gLSR 0.85 đã hồi chưa?** → YES — 3 lần breach:
- 07/08: **0.8396** (D+1 campaign, vol 64M phá đỉnh)
- 07/12: **0.8488** (D+5, ngày giá đỉnh H=0.293, gLSR dump = SHORT-WASH tại peak)
- 07/21: **0.8232** (D+14, cooldown floor — fuel-reload nadir)

Sau 07/21: gLSR tăng mạnh: 0.866→0.961→1.183→1.256→1.401→1.415→1.674→1.961→2.295→**2.648**

**ĐÂY LÀ ANOMALY:** gLSR hiện tại 2.648 (03/08) — cao hơn mọi điểm trong cooldown Campaign 2 (max ~2.297 ngày 06/25), và CÒN CAO HƠN cả gLSR đỉnh Campaign 3 (1.664 ngày 07/11). Đám đông đang LONG mạnh nhất trong toàn bộ lịch sử 53 rows trong giai đoạn giá flat.

**L-26 check (chiều giá vs gLSR):**

pos_r 3d drop check — KHÔNG trigger:
```
07/29: 0.870  (vs 07/27: 0.921 → -5.5% 2d)
07/31: 0.912  (vs 07/29: 0.870 → +4.8%)
08/01: 0.920
08/02: 0.883
08/03: 0.854
```
Không có drop ≥30%/3d. **L-26 KHÔNG fired trong campaign 3 exit.**

Hệ quả quan trọng: Campaign 3 thoát theo kịch bản PRICE DUMP (07/13 -15.1%) chứ không phải pos_r flush. L-26 signal không khớp với CLO's fast-cycle campaign.

**gLSR chiều vs giá (post-exit):** gLSR đang tăng 0.82→2.65 trong khi giá flat (0.105→0.135). Divergence BEARISH: đám đông accumulate long ở nền nhưng giá không confirm → either (a) longs sẽ bị harvest trong Campaign 4, hoặc (b) overhang đang chặn upside.

**Funding cooldown:** Phần lớn ở floor 0.00005. 04/08 bắt đầu tăng: avg=0.00048, 4 ticks. Theo dõi — nếu sustained ≥0.00050 × 6/day = dấu hiệu pre-campaign build.

---

## C2 — SĂN CAMPAIGN LỊCH SỬ (F1 test)

### C2.1 Phát hiện: CLO có ÍT NHẤT 2 campaign trước July

**Campaign 1 — Tháng 4/2026:**

| Mốc | Date | Price | Vol | Mô tả |
|---|---|---|---|---|
| Build base | 03/01-03/31 | 0.068–0.075 | 1-7M/day | Sideway stable |
| Kick-off | 04/01 | +19.9% → 0.084 | 22M | Burst đầu tiên |
| Wave 1 peak | 04/05–04/06 | H=0.112 | 13.5M | OI N/A |
| Wave 2 peak | 04/17 | H=0.138 | **29M** | f=0.00086 (peak!) |
| Wave 3 peak | 04/22 | **H=0.173** | **40M** | **Absolute high C1** |
| Crash begin | 05/16 | -28.2% → 0.082 | 18M | Flash dump |
| Crash bottom | 05/19 | L=**0.055** | 11.5M | Low C1 |

Campaign 1 profile:
- Duration: ~7 tuần (04/01→05/15)
- px_mult: H=0.173 / build~0.070 = **2.47×**
- OI: KHÔNG có data (trước vùng freshwatch/fapi retention)
- Funding peak: 04/17 avg=**0.00086** (highest entire history)
- Đặc trưng: multiple waves (3 waves), không sụp hoàn toàn giữa waves

**Campaign 2 — Tháng 5-6/2026:**

| Mốc | Date | Price | Vol | Funding | OI (M) |
|---|---|---|---|---|---|
| Post-C1 low | 05/19 | 0.055 | 11.5M | 0.00005 | — |
| Build base | 05/20–05/26 | 0.060–0.070 | 2.7–4.6M | 0.00005 | — |
| Kick-off | 05/27 | +18.5% → 0.080 | **19M** | 0.00023 | — |
| Vol burst | 05/28–05/29 | H=0.095 → dump -17% | 34M | 0.00013 | — |
| Re-attack | 05/30 | +26.4% → 0.091 | 11.6M | 0.00007 | — |
| Wave 2 | 06/01–06/03 | 0.106→0.140→**H=0.199** | 9.9/39.3/**147M** | 0.00093/0.00076 | — |
| fw start | 06/05 | 0.125 | — | 0.00032 | **5.402M** |
| Wave 3 | 06/07 | H=0.272, C=0.240 | 42.6M | 0.00050 | **9.907M** |
| OI peak 1 | 06/08 | dump -35.9% to 0.154 | 40.3M | 0.00011 | **10.954M** |
| Wave 4 | 06/11–06/15 | H=**0.275** | 101M peak | 0.00090/0.00073 | 8.0M |
| Wave 5 | 06/20 | H=**0.303** | 48.7M | 0.00014 | 8.558M |
| OI peak 2 | 06/21 | dump -32.6% | 66.3M | 0.00005 | **10.723M** |
| Absolute high | 06/23 | **H=0.304** | 84.8M | 0.00046 | 9.314M |
| Distribution | 06/24–06/26 | fade | 21-51M | neg/flat | 7.5-7.8M |
| Crash | 06/27 | -27.4% → 0.151 | 24M | 0.00003 | 5.757M |
| Cooldown base | 06/28–07/06 | 0.132–0.158 | 3-10M | 0.00005-0.00012 | 3.9-4.8M |

Campaign 2 profile:
- Duration: ~5 tuần intensive (05/27→06/27)
- px_mult: H=0.304 / build~0.067 = **4.54×**
- OI_peak: 10.954M (06/08) / est. base ~3.0M = **~3.65× OI**
- Funding peak: 06/12 avg=**0.00090** (6 ticks × 0.00090 = 0.0054/day → very hot)
- Đặc trưng: 5 waves với multiple OI spikes, absolute longest campaign

**Campaign 3 — Tháng 7/2026:**

| Mốc | Date | Price | Vol | Funding | OI (M) |
|---|---|---|---|---|---|
| Build base | 07/01–07/06 | 0.132–0.148 | 4-10M/day | 0.00006-0.00019 | 3.876-3.944M |
| Kick-off D0 | 07/07 | +36.5% → 0.202 | **40M** | 0.00044 | 3.944M |
| D+1 OI spike | 07/08 | H=0.230, C=0.189 (-6.4%) | **64M** | 0.00027 | **6.341M** |
| D+4 push | 07/11 | +27.1% → H=0.272 | **80M** | 0.00045 | 5.662M |
| D+5 absolute high | 07/12 | **H=0.293** | 48M | 0.00022 | **10.163M** |
| OI peak | 07/13 | dump -15.1% | 27M | 0.00006 | **10.394M** |
| Exit window | 07/12–07/13 | 0.227–0.268 range | — | — | — |
| Cooldown low | 07/22 | L=**0.100** | 9.2M | -0.00002 | 4.084M |
| Cooldown now | 08/03 | 0.135 | 6.6M | 0.00021 | 4.633M |

Campaign 3 profile:
- Duration: ~5 ngày markup (07/07→07/12), exit ~D+1
- px_mult: H=0.293 / B_px=0.148 = **1.98×** (mạnh nhưng ngắn nhất)
- OI_mult: peak 10.394M / B_T0 3.944M = **2.63×**
- ΔOI/B clock:

| Day | Date | OI(M) | ΔOI_cum/B |
|---|---|---|---|
| D0 | 07/07 | 3.944 | 0 |
| D+1 | 07/08 | 6.341 | **+0.61×** |
| D+2 | 07/09 | 5.446 | +0.38× |
| D+3 | 07/10 | 5.199 | +0.32× |
| D+4 | 07/11 | 5.662 | +0.44× |
| D+5 | 07/12 | 10.163 | +1.58× |
| **D+6** | **07/13** | **10.394** | **+1.64× (PEAK)** |
| D+7 | 07/14 | 7.515 | +0.91× |
| D+15 | 07/22 | 4.084 | +0.04× (near B) |
| D+17+ | 07/23+ | 4.0-4.6 | ±0.1× (stable) |

### C2.2 Bảng MM-ECON CẢ BA VÒNG

| Campaign | Build_px | Exit_VWAP | px_mult | B_OI(M) | OI_peak(M) | OI_mult | f_peak | Duration |
|---|---|---|---|---|---|---|---|---|
| C1 (Apr) | ~0.070 | ~0.160* | **~2.3×*** | N/A | N/A | N/A | 0.00086 | ~7 tuần |
| C2 (May-Jun) | ~0.067 | ~0.232** | **~3.5×** | ~3.0M est. | 10.954M | **~3.65×** | 0.00090 | ~5 tuần |
| C3 (Jul) | 0.143† | 0.256†† | **1.79×** | 3.944M | 10.394M | **2.63×** | 0.00045 | 5 ngày |

*C1 exit_VWAP: ước từ klines 04/22 cluster (H=0.173), VWAP ~0.160 — thiếu OI để confirm
**C2 exit_VWAP: VWAP 4 ngày đỉnh 06/20-06/23 = 0.232 (tính từ klines, xem C3 dưới)
†C3 build_VWAP: VWAP vol-weighted 07/01-07/06 = 0.143 (klines daily)
††C3 exit_VWAP: VWAP 07/12-07/13 = 0.256

**Build_VWAP tính chi tiết (C3):**
```
07/01: typical=(0.170+0.133+0.135)/3=0.146, vol=10.88M → 1.588
07/02: typical=(0.147+0.127+0.133)/3=0.136, vol=5.15M → 0.700
07/03: typical=(0.155+0.128+0.137)/3=0.140, vol=7.68M → 1.075
07/04: typical=(0.154+0.136+0.152)/3=0.147, vol=5.49M → 0.807
07/05: typical=(0.152+0.136+0.140)/3=0.143, vol=2.76M → 0.395
07/06: typical=(0.154+0.138+0.148)/3=0.147, vol=3.98M → 0.585
VWAP = (1.588+0.700+1.075+0.807+0.395+0.585) / 35.94M = 5.150/35.94 = 0.1433
```

**Exit_VWAP tính chi tiết (C3):**
```
07/12: typical=(0.293+0.245+0.268)/3=0.269, vol=48.38M → 13.014
07/13: typical=(0.269+0.204+0.227)/3=0.233, vol=27.45M → 6.396
VWAP = 19.410/75.83M = 0.2559
```

**Exit_VWAP tính chi tiết (C2, 4 ngày phân phối):**
```
06/20: typical=(0.303+0.211+0.267)/3=0.260, vol=48.69M → 12.659
06/21: typical=(0.282+0.175+0.180)/3=0.212, vol=66.30M → 14.056
06/22: typical=(0.257+0.177+0.240)/3=0.225, vol=60.94M → 13.712
06/23: typical=(0.304+0.193+0.211)/3=0.236, vol=84.83M → 20.020
VWAP = 60.447/260.76M = 0.2318
```

**Nhận xét pattern:**
1. Mỗi campaign đều có funding burst tại peak (0.00045–0.00090)
2. OI peak luôn trùng hoặc lag giá 1 ngày (D+5 giá peak, D+6 OI peak)
3. Campaign càng về sau (C1→C2→C3) px_mult càng giảm (2.3→3.5→1.79) → KHÔNG nhất thiết, C2 là lớn nhất; C3 ngắn và brutal nhất
4. gLSR < 0.85 xuất hiện tại PEAK MỖI CAMPAIGN: đặc trưng SHORT-WASH cấu trúc

---

## C3 — PnL KHUNG CAMPAIGN-LEVEL (F3 test)

### Giả định cho phân tích (điền theo dòng)

```
Ký hiệu:
  K_spot  = số tokens kho spot MM sở hữu (PENDING OPERATOR)
  K_perp  = exposure perp MM (không biết chính xác — suy ra từ OI nếu MM = 1 entity)
  Giả định: MM chiếm 50–70% OI change = ΔOI build = 6.219M tokens = 
            K_perp_proxy ~ 3.1–4.4M tokens × giá
```

### C3.1 Perp — Campaign 3

| Dòng | Công thức | Số | Ghi chú |
|---|---|---|---|
| Entry price perp | Build_VWAP | 0.1433 USD | 07/01-07/06 |
| Exit price perp | Exit_VWAP | 0.2559 USD | 07/12-07/13 |
| Gross perp return / token | 0.2559-0.1433 | **+0.1126 USD** | +78.6% |
| K_perp_proxy (tokens) | ΔOI × 50% | ~3.1M tokens | proxy only |
| Gross perp PnL | 3.1M × 0.1126 | **~$349k** | proxy |
| Funding income (C3, 5 days) | 0.00044+0.00027+0.00012+0.00045+0.00022 = 0.00150/token/day × 5d × (K_perp) | +$6.6k proxy | minor |
| **Perp PnL estimate** | | **~$356k** | proxy at K_perp=3.1M |

### C3.2 Spot kho — Campaign 3

| Dòng | Công thức | Số | Ghi chú |
|---|---|---|---|
| K_spot (tokens) | **PENDING OPERATOR** | K | [ô trống] |
| Giá mua spot trung bình | ~build period? | ~0.10-0.14 | uncertain |
| Giá bán spot (if MM exits) | ~exit campaign? | ~0.20-0.27 | uncertain |
| Spot PnL gross | K × (exit-entry) | K × [0.06→0.17] | nếu MM bán trong campaign |
| Nếu spot CÒN giữ (chưa exit) | paper loss vs peak | K × (0.125-0.293) = K × (-0.168) | chưa realized |
| **Spot PnL** | | **K × [...] PENDING** | [ô chờ K] |

**Thesis test "lỗ có kế hoạch":** Nếu K_spot lớn và MM CHƯA bán (còn đang xả dần trong cooldown), thì:
- Cost of carry spot = cơ hội cost
- Spot overhang = nguồn cung chặn upside → giá kẹt ở 0.12
- Net = Perp profit - Spot carry cost → phụ thuộc K và exit plan

### C3.3 Net PnL dải min-max

| Kịch bản | Perp | Spot | Net |
|---|---|---|---|
| **MIN**: K_spot=5M tokens, perp=3.1M | +$349k | Spot bought 0.140, chưa bán (paper) | **+$349k perp (confirmed) − $15k carry** |
| **MID**: K_spot=10M, sold avg 0.200 | +$349k | +$600k spot | **~$949k** |
| **MAX**: K_spot=20M, perp=4.4M, sold peak | +$496k | +$2.72M spot | **~$3.2M** |
| Funding paid (MM short) | irrelevant — MM was LONG | 0 | — |

**ÔI CHỜ OPERATOR:**
- `K_spot` = số thực tế tokens kho CLO (nguồn: on-chain, Nansen LOCKED)
- `K_perp` actual = có thể reverse-engineer từ VPS store 1h OI data (chưa check được)
- `giá mua trung bình spot` = nếu operator có data cụm ví

### C3.4 Campaign 2 PnL (tham chiếu)

| Dòng | Số |
|---|---|
| Build_VWAP C2 (05/20-05/26) | 0.0669 USD |
| Exit_VWAP C2 (06/20-06/23) | 0.2318 USD |
| Gross perp return / token | **+$0.165 (+246%)** |
| OI_base est. | ~3.0M |
| K_perp_proxy C2 (50% ΔOI) | ~3.9M tokens |
| Gross perp PnL C2 | ~$643k (proxy) |
| Funding income C2 (5 peak days) | 06/02=0.00093, 06/03=0.00076, 06/12=0.00090, 06/15=0.00073, 06/23=0.00046 → ~0.00378/day × 5 × K_perp | +~$26k proxy |

C2 perp return (246%) là lớn nhất trong 3 campaigns về PnL/token.

---

## C4 — ĐỒNG HỒ OVERHANG

### C4.1 Thanh khoản có thể hấp thụ

| Venue | Daily depth/vol | Khả năng hấp thụ |
|---|---|---|
| KuCoin + MEXC spot | $16k orderbook depth | ~$16k/ngày không slippage |
| BSC DEX Pool chính (0x8d23) | liq=$1,306,584, vol24h=$4,218,018 | ~$100-200k/ngày (stealthy) |
| BSC DEX Pool phụ (0xb95d) | liq=$200,017, vol24h~$0 | minimal |
| Binance perp liquidation | — | độc lập — sẽ thêm supply |
| **Tổng thực tế (stealthy)** | | **~$120k–$220k/ngày** |

*DEX vol 4.2M/day không thể absorb hết — selling $500k vào pool $1.3M sẽ di chuyển giá ~28% (AMM formula). Stealthy limit: <15% pool depth/ngày = ~$200k.

### C4.2 Tính đồng hồ

```
Absorb capacity: $120k–220k/ngày
Giá hiện tại: ~$0.125

Nếu K_spot = 5M tokens  → K × 0.125 = $625k  → 2.8–5.2 tuần
Nếu K_spot = 10M tokens → $1.25M              → 5.7–10.4 tuần
Nếu K_spot = 20M tokens → $2.5M              → 11.4–20.8 tuần
Nếu K_spot = 40M tokens → $5.0M              → 22.7–41.7 tuần
```

Campaign 3 bắt đầu 07/07, nay 04/08 = 28 ngày. 28 × $170k avg = ~$4.76M đã hấp thụ nếu xả liên tục. Điều này không khớp với vol thực tế (DEX vol 4.2M/ngày rất volatile, không phải tất cả là MM sell).

**Ước thực tế từ vol pattern:**
Vol trung bình cooldown (07/27-08/03): 5.2M perp, DEX ~$200-500k/day. Nếu MM xả 10% DEX vol/day: ~$20-50k/ngày → rất chậm.

**Thời hạn falsifiable:**
- CASE A (K=5M tokens): xả xong trước 01/10/2026
- CASE B (K=10M): xả xong trước 01/12/2026
- CASE C (K=20M+): xả kéo dài đến Q1 2027
- **Dấu hiệu kết thúc overhang**: (1) on-chain cụm ví balance → 0, HOẶC (2) capitulation dump + bounce bền → balance cleared, HOẶC (3) Campaign 4 launch (MM xả hàng vào lúc crowd mua mạnh)

**Tại sao gLSR 2.648 trong cooldown không phải bullish:**
- gLSR cao = đám đông có nhiều LONG position đang mở ở giá thấp (0.12)
- Nếu giá không tăng → các longs này sẽ bị chặn bởi overhang supply
- Khi MM ready cho Campaign 4 → mọi volume buy của crowd + LONG squeeze = exit window cho MM
- Kết luận: gLSR 2.648 là setup fuel cho Campaign 4, KHÔNG phải bullish signal hiện tại

---

## C5 — VERDICT COOLDOWN CLO (quá hạn từ 27/07)

### Căn cứ số C1

| Signal | Trạng thái | Đọc |
|---|---|---|
| gLSR | 2.648 (03/08), tăng đều | Crowd LONG mạnh nhất = fuel Campaign 4 |
| pos_r | 0.854, declining | Dưới 1.0, thiếu conviction short hedge |
| acc_r | 2.894 (03/08) | Account-wise very long |
| OI | 4.1-4.6M stable | Không build, không xả hết |
| Volume | 1.7-8M/day | Dead market |
| Funding | 0.00005 floor | Không có trend cost |
| L-26 | Không trigger | Campaign 3 exit không theo pos_r signal |
| dist_wall/lsr_dist | DATA ABSENT | Không verify được |
| On-chain outflow | PENDING OPERATOR | R4 |

---

### PHƯƠNG ÁN (a): Theo packet cũ — UNLOCK khỏi suppressed → NO_SETUP/WATCH-nhạt

**Luận điểm:**
- Cooldown tiêu chuẩn đã đủ dài (28 ngày từ peak)
- OI đã collapse từ 10.4M → 4.1M (-60%)
- Giá đã dump từ H=0.293 xuống L=0.100 (-66%)
- Có bounce nhỏ (07/23 +12.2%, 07/24 +9.7%) chứng tỏ demand floor
- gLSR phục hồi → crowd rebuilding → tiền đề cho Campaign 4

**Hành vi sau verdict:**
→ Chuyển sang WATCH mode, chờ: pos_r >1.2 + vol burst + funding burst → tín hiệu setup Campaign 4

**Điểm yếu:** Bỏ qua overhang (K unknown), bỏ qua gLSR bất thường cao.

---

### PHƯƠNG ÁN (b): Theo thesis operator — STAND_ASIDE có đồng hồ

**Luận điểm:**
- Overhang C4 đang chạy (K PENDING, nhưng DEX pool $1.3M + CEX depth $16k = thin liquidity)
- gLSR 2.648 trong flat price = BEARISH divergence: crowd mua lên mà giá không tăng → bị chặn
- Mọi bounce (07/23 +12.2%, 07/24 +9.7%) = window MM xả thêm vào demand
- Price kẹt ở 0.12-0.135 kể từ 23/07 (12 ngày, không breakout) → overhang xác nhận
- L-26 không trigger = campaign 3 chưa "resolved" theo signal chuẩn
- 04/08 funding bắt đầu nhích lên (0.00048) → theo dõi, chưa phải signal

**Đồng hồ STAND_ASIDE:**
- Terminus: on-chain balance cạn HOẶC capitulation HOẶC Campaign 4 launch confirmed
- Ước: 2-4 tháng từ nay nếu K trong dải 10-20M tokens (CASE B/C)
- Mốc check: 01/10/2026 (CASE A end), 01/12/2026 (CASE B end)

**Hành vi sau verdict:**
→ Không trade CLO cho đến khi: (i) on-chain confirms balance near-zero, HOẶC (ii) Campaign 4 launch signal rõ (pos_r spike + OI build + funding burst tất cả cùng lúc)
→ Bounce lên 0.15-0.18: MỞ SHORT HEDGE (nếu confirmed = distribution sell)

**Điểm mạnh:** Falsifiable với đồng hồ cụ thể; giải thích được vì sao STAND_ASIDE hữu hạn thay vì vô hạn.
**Điểm yếu:** Cần K từ operator để calibrate đồng hồ chính xác.

**Khác biệt hành vi chính:**
| | Phương án (a) | Phương án (b) |
|---|---|---|
| Bounce 0.15-0.18 | Xem là LONG setup | Xem là sell window |
| gLSR 2.648 | Tích cực — crowd rebuilding | Cảnh báo — fuel không được dùng |
| Thời gian chờ | Indefinite/short | 2-4 tháng có terminus |
| Action trigger | vol+pos_r+funding burst | on-chain clear + capitulation |

---

## C6 — NHÁP LESSON L-4x (chờ operator ký + nối vào LESSONS sheet)

**[DRAFT — chưa append, chờ F1/F2/F3 confirm từ operator]**

```
Topic: Đơn vị hạch toán MM = CAMPAIGN; chi phí đạo cụ chủ động; archetype C-vỏ-A-ruột

Body:
Trong archetype "C-vỏ-A-ruột": token mang kho Loại C bề ngoài (người mua thật 
trên sàn spot) nhưng thực chất kho đó phục vụ campaign perp (ruột). 

Cơ chế:
1. MM mua spot → đẩy giá → tín hiệu "đắt-đáng-tin" cho retail
2. Retail long perp → OI nở → funding dương → MM (long perp) thu funding
3. MM exit perp tại peak → profit MM = perp multiple × capital
4. Spot kho còn lại = overhang → bán dần trong cooldown (chi phí xả, không phải lỗ 
   nếu mua thấp hơn exit price)

Điểm cốt lõi:
- Đơn vị lời/lỗ = CAMPAIGN (không phải ngày): phân tích phải nhìn từ B đến exit, 
  không phải từng nến
- "Lỗ có kế hoạch" = không phải lỗ thực — là chi phí marketing (spot buy) để 
  tạo price signal đủ mạnh cho retail long perp
- Mỗi campaign kế tiếp thường có OI_base cao hơn (crowd quen token) → compounding 
  nếu MM giữ kho qua nhiều vòng

Phân biệt với L-42 Loại C:
- Loại C thực: người mua spot vì conviction, không deadline — reads = real ownership signal
- C-vỏ-A-ruột: mua spot VÌ campaign, deadline = exit window → reads = campaign signal, 
  không phải ownership signal
- Phân biệt bằng: (1) kho xuất hiện đúng build window campaign, (2) wallet không giữ 
  qua multiple campaigns, (3) on-chain flow = mua khi OI thấp, bán khi OI peak

Scope: Áp dụng sau khi xác nhận F1 (≥1 prior campaign) + F3 (PnL net positive). 
Chưa kết luận trên thi bản CLO chờ K từ operator. Có thể đúng cho: ESPORTS (2 waves 
trong 1 campaign), BR (kho 6% PENDING), TAG (nghi archetype A).

Action: Khi nhận diện archetype này → STAND_ASIDE suốt cooldown + estimate đồng hồ 
overhang = K / absorb_capacity. Mọi bounce trong cooldown = distribution sell opportunity 
cho MM, không phải reversal.
```

**Status F-test:**
- F1 (≥2 prior campaigns CLO): **PASS** — April + May-June confirmed
- F2 (perp profit > spot cost): **PARTIAL PASS** — structure confirms, K pending
- F3 (net PnL positive): **PENDING** — cần K_spot từ operator
- Lesson append: chờ operator xác nhận F3 và ký L-4x number

---

## PENDING OPERATOR — DANH SÁCH ÔI CHỜ

| # | Mục | Tại sao cần | Ảnh hưởng đến |
|---|---|---|---|
| O1 | K_spot = số tokens kho CLO MM | Calibrate C3 PnL + C4 overhang clock | C3, C4, verdict (a) vs (b) |
| O2 | Nguồn kho: bought khi nào, giá bao nhiêu | Xác nhận "lỗ có kế hoạch" hay lời trên spot | F2, F3, lesson append |
| O3 | On-chain cụm ví CLO balance hiện tại | Xác nhận overhang đang xả hay đã clear | C4 terminus, verdict |
| O4 | Verdict chọn (a) hay (b) | Ký | Ghi vào CASE_CLO DAILY + agent_log |
| O5 | F3 confirm | Ký lesson L-4x | C6 append |

---

## AGENT LOG ENTRY

```
[CLO-THESIS-20260804]
- C1: 10-row 22/07-03/08 series — gLSR anomaly 2.648 (highest ever), 
  pos_r declining <0.854, OI stable 4.1-4.6M, vol dead 1.7-8M/day
- C2: 3 campaigns confirmed (Apr, May-Jun, Jul). klines 01/03→04/08 + 
  funding 01/04→04/08. OI only from 07/05 (fapi) + freshwatch từ 06/05
- Campaigns: C1 px_mult~2.3×, C2 px_mult~3.5× (largest), C3 px_mult=1.79×
- F1 PASS; F2 partial (K_perp proxy $349k-$496k perp profit C3)
- F3 PENDING K_spot operator
- C4 overhang: $120k-$220k/day absorb, đồng hồ 2.8-20 tuần tùy K
- gLSR 2.648 trong flat = fuel Campaign 4 hoặc đòn bẩy long bị chặn
- dist_wall/lsr_dist: ABSENT in freshwatch CLO — không verify được
- L-26: không trigger trong C3 exit — exit theo price dump pattern
- Verdict C5: 2 phương án chờ operator ký
- Lesson C6: draft ready, chờ F3 + operator ký
- PENDING: O1-O5 (xem bảng trên)
```

# TUT — T+30 Analysis 08/08/2026
**Chạy:** 2026-08-07 02:06 UTC (09:06 VN = 08/08 sáng)
**T0 = 09/07/2026 | T+30 = 08/08/2026 | B = 1.922M (OI floor)**
**Status: ANALYSIS ONLY — verdict thuộc operator**

---

## LAYER COVERAGE

| Layer | Nguồn | Độ phủ | Quality |
|-------|-------|--------|---------|
| PERP daily (01/07→06/08) | freshwatch_daily export | 34 rows, đủ | fn=6 tất cả ✓ |
| PERP daily 07/08 | MISSING từ export (cron 01:20 UTC chưa chạy) | — | Fallback: fapi intraday |
| PERP intraday 07/08 | fapi/v1/klines 1h | 3 nến đóng (00:00-02:00 UTC) | OK — L-38 boundary |
| OI realtime | fapi/v1/openInterest | snapshot 02:06 UTC | Approx (tokens×px) |
| Funding lịch sử | fapi/v1/fundingRate limit=30 | 5 ngày gần (~30 kỳ) | Đủ |
| LSR intraday | fapi/futures/data 5m | snapshot 02:05 UTC | L-38: intraday ≠ daily |
| SPOT Binance TUTUSDT | api/v3/klines 1d | 07/08 (partial 2h) | k[10]/k[7] venue=binance_spot ✓ |
| DEX BSC GeckoTerminal | Search API | **404 N/A** | Endpoint error |
| On-chain (kho, wallet) | LOCKED | — | ABSTAIN (Nansen LOCKED) |

---

## TASKS.md DIFF

Luật hiện hành: mỗi session mở bằng diff TASKS.md. Cập nhật đề xuất sau session này:

| ID | Trạng thái cũ | Đề xuất sau session | Lý do |
|----|--------------|---------------------|-------|
| TUT-T30 | `DOING — deadline 08/08` | `DONE` (sau operator ký outcome) | Analysis xong — operator điền verdict |
| TUT-OUTCOME | `QUEUED — sau 08/08` | `DOING — operator ký + write OUTCOME sheet` | T+30 đã đến |
| GOM-B4 | `BLOCKED — chờ operator duyệt §6 + chat_id` | Không đổi | Chờ operator |
| XS3B-RETRY | `QUEUED` | Không đổi | Chưa done |

**Chú ý:** TASKS.md chỉ operator commit thay đổi — đây là đề xuất diff.

---

## D1 — PERP

### D1a. Export canonical (fn verify từng dòng)

| Ngày | px_avg | vol_perp | taker% | f_avg | fn | fn_ok | OI | pos_r | acc_r | gLSR | data_ok |
|------|--------|----------|--------|-------|-----|-------|-----|-------|-------|------|---------|
| 08-04 | 0.02249 | 33,252,326 | 48.63% | 0.000043 | 6 | ✓ | 5,671,593 | 2.8299 | 1.5913 | 1.4384 | True |
| 08-05 | 0.02603 | 24,157,157 | 51.92% | 0.000042 | 6 | ✓ | 6,343,787 | 2.0739 | 1.1920 | 1.1119 | True |
| 08-06 | 0.02737 | 23,750,950 | 48.83% | 0.000020 | 6 | ✓ | 7,873,423 | 2.2014 | 1.2727 | 1.2878 | True |
| 08-07 | MISSING | — | — | — | — | — | — | — | — | — | cron 01:20 UTC chưa chạy |

> fn=6 cho cả 3 ngày → không có dòng SUSPECT. 08-06 f_avg=0.000020 nằm ngoài pin range [4e-5,6e-5] — xem D3②.

### D1b. Fapi intraday 07/08 UTC (09:06 VN 08/08)

**Nến 1h từ 00:00 UTC — L-38 boundary: INTRADAY ≠ daily 00:00, KHÔNG trộn vào bảng DAILY**

| H:MM UTC | open | high | low | close | vol$ | taker% |
|----------|------|------|-----|-------|------|--------|
| 00:00 | 0.02449 | 0.02480 | 0.02407 | 0.02423 | 559,703 | 48.1% |
| 01:00 | 0.02424 | 0.02562 | 0.02414 | 0.02552 | 672,961 | 53.3% |
| 02:00 (open) | 0.02553 | 0.02584 | 0.02553 | 0.02565 | 83,258 | 41.8% |

**Cumulative 07/08 UTC (3h):**
- px_open 00:00 = 0.02449 | H = 0.02584 | L = 0.02407 | px_last = 0.02565 (+4.74%)
- vol_perp_day (so far) = $1,315,922
- taker_day = 50.36%

> Note: 07/08 00:00 UTC open = 0.02449 vs 06/08 close ≈ 0.02450 (spot) → gap không đáng kể.
> Tuy nhiên 06/08 px_avg export = 0.02737 (VWAP cao hơn close = spike trong ngày rồi đóng thấp hơn).

**OI realtime (02:06 UTC):**
- OI tokens = 236,770,007
- OI USD = **$6,073,151** (×0.02565) — L-38: approximate, dùng cho direction check chỉ

**premiumIndex / funding:**
- markPrice = 0.025684 | indexPrice = 0.025721
- Premium = **-0.1456%** (mark < index → perp đang discount nhẹ so với spot)
- lastFundingRate = **0.000012** (FLOAT) — kỳ cuối cùng đã settle
- nextFundingTime = **04:00 UTC** (còn ~2h)
- Với premium âm hiện tại → kỳ 04:00 UTC có thể ra âm hoặc floating

**Funding lịch sử 12 kỳ gần nhất:**

| Kỳ settle | Rate | Status |
|-----------|------|--------|
| 08-05 04:00 | 0.000050 | ✓ PIN |
| 08-05 08:00 | 0.000050 | ✓ PIN |
| 08-05 12:00 | 0.000050 | ✓ PIN |
| 08-05 16:00 | 0.000025 | FLOAT |
| 08-05 20:00 | 0.000027 | FLOAT |
| 08-06 00:00 | 0.000050 | ✓ PIN |
| 08-06 04:00 | 0.000050 | ✓ PIN |
| 08-06 08:00 | 0.000050 | ✓ PIN |
| **08-06 12:00** | **-0.000021** | **⚠ NEG** |
| **08-06 16:00** | **-0.000059** | **⚠ NEG** (mạnh) |
| 08-06 20:00 | 0.000050 | ✓ PIN (khôi phục) |
| 08-07 00:00 | 0.000043 | ✓ PIN (borderline floor của range) |

→ Pin streak BỊ PHÁ: 08-05 16:00-20:00 (float), 08-06 12:00-16:00 (NEG).
→ Hai kỳ NEG lúc 12:00-16:00 UTC 08-06 = sự kiện đáng chú ý (xem D3②).

**LSR intraday snapshots (5m, 02:05 UTC — L-38):**
- pos_r = **2.7185** [08-07 02:00 UTC]
- acc_r = **1.2815** [08-07 02:05 UTC]
- gLSR  = **1.1801** [08-07 02:05 UTC]

---

## D2 — SPOT

### Binance TUTUSDT daily (venue=binance_spot, k[10]/k[7])

| Ngày | vol_spot | taker_spot% | close | note |
|------|----------|-------------|-------|------|
| 08-01 | 2,752,516 | 54.20% | 0.01754 | |
| 08-02 | 1,019,876 | 54.06% | 0.01758 | |
| 08-03 | 5,475,175 | 56.58% | 0.02039 | vol bắt đầu tăng mạnh |
| 08-04 | 7,156,175 | 50.93% | 0.02157 | |
| 08-05 | 6,841,531 | 53.66% | 0.02870 | close cao nhất |
| **08-06** | **6,767,132** | **55.59%** | **0.02450** | close sập từ intraday peak |
| 08-07 (2h) | 359,056 | 63.97% | 0.02575 | intraday partial |

**08-07 spot intraday (2h):**
- vol_spot = $359,056 (quá sớm)
- taker_spot = 63.97% [k[10]/k[7], venue=binance_spot]
- L-29 guard = spot/perp = 0.273× ✓ CLEAR (<3×)

### DEX BSC — GeckoTerminal
**404 N/A** — endpoint search trả lỗi. DEX layer = MISSING session này.

---

## D3 — Chấm 7 chốt

**Baseline:** B=1.922M | OI ATH = 7.873M (06/08) | T0 px = 0.01066 | P1-mid = 0.02570

---

**① pos_r vs 3.81 (FIRED 02/08) — giờ ở đâu? rebuild?**

Chuỗi pos_r:

| Ngày | pos_r | vs 3.81 | note |
|------|-------|---------|------|
| 08-01 | 4.1687 | +9.4% | peak gần nhất |
| **08-02** | **3.4581** | **-9.2%** | **FIRE: xuyên qua 3.81** |
| **08-03** | **4.0144** | **+5.4%** | **REBUILD (vượt lại 3.81)** |
| 08-04 | 2.8299 | -25.7% | sập sâu |
| 08-05 | 2.0739 | -45.4% | sập tiếp — L-26 FIRED |
| 08-06 | 2.2014 | -42.1% | nhúc nhích rebuild |
| 07/08 02:05 UTC | 2.7185 (intraday) | -28.6% | đang rebuild tiếp |

→ **CHƯA THỎA.** pos_r hiện tại 2.72, còn 41% dưới 3.81.
→ **Có nến rebuild:** 08-03 (vượt 3.81 một ngày) và 08-06+07/08 (đang leo từ 2.07).
→ **[⚠ ÁN NHÃN SỬA]** 08-03→08-05: pos_r sập 4.0144→2.0739 = **-48.4%/3 ngày → HARVEST-INTO-STRENGTH / GHẾ-RỜI LẦN 2** (khuôn BANK 19-21/07). Giá đồng thời +33%, gLSR GIẢM 1.44→1.11 = đối lập L-26. **L-26 chưa fired** (L-26 đòi giá SẬP + gLSR TĂNG).
→ Rebuild hiện tại (2.22→2.72) = kịch bản kéo-tiếp nếu giữ được; invalidate nếu pos_r sập lần 2 dưới 2.07.

---

**② Funding ghim [4e-5,6e-5] — kỳ nào hở?**

→ **CHƯA THỎA liên tục.** Pin streak đã bị phá 3 lần:
- 08-05 16:00+20:00 UTC: FLOAT (0.000025, 0.000027) — hở nhẹ
- **08-06 12:00 UTC: NEG -0.000021** ⚠
- **08-06 16:00 UTC: NEG -0.000059** ⚠⚠ — kỳ mạnh nhất, trùng với intraday spike đỉnh rồi collapse
- 08-06 20:00: khôi phục PIN
- 08-07 00:00: PIN (0.000043, borderline floor)
- 07/08 02:06 UTC hiện tại: lastRate=0.000012 (FLOAT), premium=-0.145% → kỳ 04:00 UTC có thể FLOAT hoặc NEG

→ Pattern: ghim ON→hở→NEG→khôi phục = volatility event 08-06 phá pin tạm thời.
→ Nếu kỳ 04:00 UTC 08/08 ra NEG hoặc FLOAT → streak không xây lại được = tín hiệu xả áp lực.

---

**③ Ngày đỏ ≥8-10% vol lớn (06-08/08)**

| Ngày | px_avg | thay đổi ngày | vol_perp | màu | ≥8-10%? |
|------|--------|--------------|----------|-----|---------|
| 08-04 | 0.02249 | +13.3% từ 08-03 | 33.2M | XANH | — |
| 08-05 | 0.02603 | +15.7% | 24.2M | XANH | — |
| 08-06 | 0.02737 | +5.2% (VWAP) | 23.8M | XANH* | — |
| 08-07 (3h) | 0.02565 | -6.5% từ px_avg 06/08 | ~1.3M | ? | quá sớm |

*08-06 VWAP=0.02737 nhưng spot close=0.02450 (vs 08-05 close=0.02870 = -14.6%). Nếu dùng close-to-close: 08-06 = **ĐỎ -14.6% trên spot.**

→ **Số gần nhất:** 08-06 spot close-to-close = -14.6% từ 08-05 đỉnh, vol 23.8M = ĐỎ LỚN.
→ Nhưng tính theo px_avg export (VWAP): 08-06 = +5.2% xanh. Hai cách đọc khác nhau vì intraday spike.
→ **Chốt ③ convention (chốt):** close-to-close daily klines (KHÔNG dùng px_avg VWAP — VWAP smooths intraday spike cho ra số tốt hơn thực). 08-06 = ĐỎ -14.6% close-to-close (0.02870→0.02450).
→ 08-07 (3h): taker cao (63.97% spot), giá đang lên từ 0.02449→0.02565 = chưa đỏ.

---

**④ gLSR vs 1.1 (wash-watch) — 1.438 (04/08) → nay? slope?**

| Ngày | gLSR | vs 1.1 | note |
|------|------|--------|------|
| 08-04 | 1.4384 | +30.8% trên 1.1 | tham chiếu |
| **08-05** | **1.1119** | **+1.1% trên 1.1** | **cận 1.1 nhất — suýt chạm** |
| 08-06 | 1.2878 | +17.1% trên 1.1 | bounce lên |
| 07/08 02:05 UTC | 1.1801 (5m) | +7.3% trên 1.1 | đang rơi xuống lại |

**Slope 5 ngày:**
- glsr_slope_5d (08-06 vs 08-01): 1.2878/2.0312 = 0.634 — giảm -36.7% trong 5 ngày

→ **CHƯA THỎA (≤1.1 sustained).** gLSR chưa flush qua 1.1.
→ Pattern đáng lo: dao động 1.11→1.29→1.18 trong 3 ngày, không thoát lên mà cũng không xuyên xuống.
→ **P8 critical:** "không vượt 0.026-0.028 bền khi gLSR chưa flush ≤1.1" — giá ĐÃ vượt 0.026 (px 08-05 VWAP 0.02603) khi gLSR=1.1119 (chưa flush). P8 cảnh báo đang bị test.
→ **Biến quyết định:** nếu gLSR xuyên ≤1.1 bền (≥2 ngày liên tiếp) → leg mới. Nếu bounce về ≥1.3 → kịch bản (b) grind.

---

**⑤ OI-clock ΔOI/B — OI nay vs B=1.922M, chiều unwind**

| Ngày | OI | ΔOI/B | so P3 band |
|------|-----|-------|-----------|
| 08-02 | 4.997M | 1.60× | dưới 2× (5.766M) |
| 08-04 | 5.671M | 1.95× | dưới 2× — xấp xỉ |
| **08-05** | **6.343M** | **2.30×** | **vượt P3 2× band (5.766M)** |
| **08-06** | **7.873M** | **3.10×** | **vượt P3 3× band (7.688M) = ALERT ZONE** |
| 07/08 02:06 UTC | ~6.073M | **2.16×** | **OI CO LẠI từ ATH 7.873M = -22.8%** |

→ **OI đã vượt P3 3× band trên 08-06 (7.873M > 7.688M).**
→ **Intraday 07/08: OI co lại còn ~6.073M = -1.800M từ ATH.**
→ **Ai đóng?** Với pos_r rebuild (2.07→2.72) + gLSR ≈ 1.18: crowd shorts đang đóng (gLSR tăng nhẹ = longs tăng tỷ lệ) HOẶC longs đóng một phần + shorts cũng đóng = giá giữ.
→ Nếu OI co tiếp về <5M: unwind crowd thật = pos_r sẽ sập tiếp. Nếu OI ổn định quanh 6M: tích lũy lại.

---

**⑥ Spot >$10M/ngày + taker_spot <45% — kho mở?**

| Ngày | vol_spot | taker_spot% | ≥$10M? | <45%? | thỏa? |
|------|----------|-------------|--------|-------|-------|
| 08-03 | 5.475M | 56.58% | ✗ | ✗ | ✗ |
| 08-04 | 7.156M | 50.93% | ✗ | ✗ | ✗ |
| 08-05 | 6.841M | 53.66% | ✗ | ✗ | ✗ |
| 08-06 | 6.767M | 55.59% | ✗ | ✗ | ✗ |

→ **CHƯA THỎA.** Vol spot max chỉ ~7.2M (08-04). Taker liên tục >50% = net buyers, không có dấu hiệu kho xả.
→ 4 ngày liên tiếp taker_spot ≥50% → đây là input cho chốt ⑦.

---

**⑦ Dist_wall spot — ≥3d taker_spot ≥50% mà giá không lên**

| Ngày | taker_spot% | close (spot) | giá lên? |
|------|-------------|--------------|---------|
| 08-03 | 56.58% | 0.02039 | ← baseline |
| 08-04 | 50.93% | 0.02157 | +5.8% ✓ lên |
| 08-05 | 53.66% | 0.02870 | +33.1% ✓ lên mạnh |
| **08-06** | **55.59%** | **0.02450** | **-14.6% ↓ ĐỎ** |
| 08-07 (2h) | 63.97% | 0.02575 | +5.1% ✓ lên (tạm) |

→ **Mới có 1 ngày không lên (08-06) trong chuỗi taker≥50%.** Điều kiện "≥3d không lên" = CHƯA THỎA.
→ Nhưng 08-06 = ngày đầu tiên dist_wall có thể bắt đầu: taker cao + giá đóng thấp.
→ Nếu 07/08 và 08/08 đóng thấp hơn (taker vẫn cao) → chốt ⑦ sẽ thỏa D+2.

---

**Tóm tắt 7 chốt:**

| # | Chốt | Trạng thái | Số |
|---|------|-----------|-----|
| ① | pos_r vs 3.81 | **CHƯA** — 2.72 (intraday), có rebuild | cần vượt 3.81 bền |
| ② | Funding pin | **HỞ** — 3 lần vỡ (float+NEG 08-06) | pin chưa stable |
| ③ | Ngày đỏ ≥8-10% vol lớn | **GẦN** — 08-06 spot close -14.6% (vol 23.8M) | cần operator confirm close-to-close |
| ④ | gLSR vs 1.1 | **GẦN NHƯNG CHƯA** — min 1.1119 (08-05) | chưa flush bền |
| ⑤ | OI-clock ΔOI/B | **3× BAND ĐÃ CHẠM** (08-06 = 3.10×) → đang co | OI ATH = P3 alert zone |
| ⑥ | Spot >$10M + taker<45% | **CHƯA** — max 7.2M, taker ≥51% | kho chưa mở |
| ⑦ | Dist_wall 3d | **CHƯA** — mới 1 ngày đỏ (08-06) | cần theo dõi 07-08/08 |

---

## D4 — T+30 Outcome (T0=09/07)

**Ngày T+30 = 08/08 (VN) = 07/08 UTC (đang chạy)**

| Mốc | Giá | Ret vs T0 |
|-----|-----|----------|
| T0 = 09/07 (B_ref day) | 0.01066 | — |
| Tell cờ ghế-rời 02/08 | 0.0174 | — |
| Advisor_ref | 0.0197 | — |
| **T+30 intraday 07/08 02:06 UTC** | **0.02565** | **+140.6%** |

**Scorecard hai lớp:**

| Layer | Giá tham chiếu | px hiện tại | Khoảng cách | Trạng thái |
|-------|---------------|-------------|-------------|-----------|
| Tell ghế-rời (02/08) | 0.0174 | 0.02565 | +47.4% trên tell | Giá chưa về dưới tell |
| Advisor_ref | 0.0197 | 0.02565 | +30.2% trên ref | |
| P1-low (1.5×) | 0.01928 | 0.02565 | +33.0% trên P1-low | **ĐÃ VƯỢT** |
| P1-mid (2.0×) | 0.02570 | 0.02565 | **-0.2% dưới P1-mid** | Xấp xỉ P1-mid |
| P1-high (2.5×) | 0.03213 | 0.02565 | -20.2% dưới | Chưa |

**Trạng thái vị thế:** PENDING — không có thông tin operator.

**pos/gLSR/OI tại T+30:**

| Metric | Giá trị | Nguồn | so baseline mm_econ (04/08) |
|--------|---------|-------|---------------------------|
| pos_r | 2.7185 (intraday) / 2.2014 (daily 06/08) | L-38 | Giảm từ 4.0144 (08-03) |
| gLSR | 1.1801 (intraday) / 1.2878 (daily 06/08) | L-38 | Giảm từ 1.6853 (08-03) — gần wash zone |
| OI | ~6.073M (intraday) / 7.873M (daily 06/08) | L-38 | OI tăng mạnh rồi co từ ATH |
| GHẾ-RỜI LẦN 2 | **HARVEST-INTO-STRENGTH 08-05** (pos_r −48%, giá +33%, gLSR GIẢM 1.44→1.11) | Export canonical | KHÔNG phải L-26; L-26 chưa fired (L-26 = giá sập + gLSR tăng) |

**Verdict: Ô TRỐNG — Operator ký.**

---

## D5 — Interim P1-P8 (hạn cứng 18/08)

### P8 — "không vượt 0.026-0.028 bền khi gLSR chưa flush ≤1.1"

| Mốc | gLSR | px close/VWAP | vi phạm P8? |
|-----|------|---------------|-------------|
| 08-05 | 1.1119 (chưa ≤1.1) | 0.02603 (VWAP) — vượt 0.026 | **Vượt ceiling khi gLSR chưa flush** |
| 08-06 | 1.2878 (bounce) | 0.02737 (VWAP) — vượt 0.026 | Tiếp tục |
| 07/08 | 1.1801 (intraday) | 0.02565 | gần 0.026 |
| **Spot 08-05 close** | 1.1119 | **0.02870** | **Cao nhất — xa 0.028** |

→ **P8 đang bị test:** px đã vượt 0.026-0.028 trong khi gLSR chưa flush bền ≤1.1.
→ Ghi bảng: **px_max từ 05/08 = 0.02870** (spot close 08-05). Nếu tính perp VWAP: 0.02737 (08-06). Trong mọi trường hợp: đã vượt 0.026.
→ **Hướng: P8 CHALLENGED** — ghi interim "px đã vượt ceiling 0.026 khi gLSR=1.11 (chưa ≤1.1). Nếu gLSR flush ≤1.1 bền → cập nhật sang scenario mới."

### P3 OI-clock band (interim)

| Band | OI target | Trạng thái 07/08 |
|------|-----------|-----------------|
| 2× band | 5.766M | ĐÃ VƯỢT (08-05: 6.343M) |
| **3× band (alert)** | **7.688M** | **ĐÃ CHẠM (08-06: 7.873M) rồi CO** |
| 5× band (red zone) | 11.532M | Chưa |
| 7× band (extreme) | 15.376M | Chưa |

→ OI vượt 3× band (alert zone) ngày 08-06 rồi co lại = sự kiện quan trọng.
→ Nếu co về <5.766M (2× band): reset clock đáng kể.

### Bảng interim P1-P5

| ID | Prediction | Trạng thái interim 07/08 |
|----|-----------|--------------------------|
| P1 | Exit_px ∈ [0.025, 0.035] | **GẦN P1-mid** — 0.02565 vs 0.02570. px_max 0.02870 (spot 08-05) trong [0.025,0.035] ✓ |
| P2 | L-26 trước 22/08 | **CHƯA** — 08-05 = HARVEST-INTO-STRENGTH (không phải L-26). L-26 chưa fired, vẫn trong track. |
| P3 | OI_exit ∈ [8M, 12M] tại L-26 | **CHỜ** — L-26 chưa fired. OI ATH 08-06 = 7.873M (trong band [8M,12M]); đọc OI tại L-26 thật khi có. |
| P4 | L-26 trigger 12/08→25/08 | **ĐÚNG window** — L-26 chưa fired. Window 12-25/08 còn nguyên. Monitor pos_r drop ≥30%/3d kèm giá sập. |
| P5 | Kho loại A/B/C | ABSTAIN — PENDING operator |

> **Ghi chú P2/P4 [SỬA ÁN NHÃN]:** 08-05 = HARVEST-INTO-STRENGTH / GHẾ-RỜI LẦN 2 (giá +33%, pos_r −48%, gLSR GIẢM 1.44→1.11 — đối lập L-26). **L-26 chưa fired.** P2 tiếp tục track. P4 window 12/08→25/08 còn nguyên — cần pos_r drop ≥30%/3d kèm giá sập để fired.

---

## D6 — Kịch bản

**Tổng hợp tín hiệu 07/08:**

| Tín hiệu | Giá trị | Chiều |
|----------|---------|-------|
| pos_r (daily 08-06) | 2.2014 | Giảm từ 4.17 — đang rebuild |
| gLSR (daily 08-06) | 1.2878 | Dao động 1.11–1.44, giảm từ 2.03 |
| OI (daily 08-06) | 7.873M ATH → intraday 6.073M | Co từ ATH |
| Funding (08-06 12-16h) | NEG ×2 → phục hồi PIN | Vỡ rồi sửa |
| Taker spot (08-03→08-06) | 51–56% | Buyers net liên tục |
| px (08-05→08-07) | 0.02870→0.02450→0.02565 | Spike→pullback→mild recovery |
| GHẾ-RỜI LẦN 2 | HARVEST-INTO-STRENGTH 08-05 | pos_r −48% + giá +33% + gLSR giảm = KHÔNG phải L-26; L-26 chưa fired |

---

**Ba kịch bản:**

**(a) Wash đang đến (gLSR trượt ≤1.1 + giá rũ = nạp đạn leg-kho)**
- Signal ủng hộ: gLSR dao động quanh 1.1-1.3 (không thoát lên); 08-05 chạm 1.1119; intraday 07/08 = 1.1801
- Phản bác: gLSR bounce từ 1.11→1.29 (08-06) = chưa flush bền; pos_r đang rebuild (không sập tiếp)
- Xác suất định tính: TRUNG BÌNH. Cần 1-2 ngày gLSR xuống bền ≤1.1.

**(b) Grind tiếp trên bình cạn (giá lên, gLSR đứng, không flush)**
- Signal ủng hộ: taker_spot ≥50% liên tục (buyers); pos_r rebuild; giá 07/08 +4.74% từ open
- Phản bác: OI đang co từ ATH (7.873M→6.073M = -22.8%); funding vỡ PIN; px không breakout ATH
- Xác suất định tính: TRUNG BÌNH. Tùy vào việc OI có ổn định hay tiếp tục co.

**(c) Gãy (chốt ③ bắn / pos rơi tiếp không rebuild)**
- Signal ủng hộ: GHẾ-RỜI LẦN 2 đã có (08-05, HARVEST-INTO-STRENGTH); OI co mạnh; funding NEG trên 08-06 (distribution signal); 08-06 spot close -14.6%
- Phản bác: pos_r đang rebuild (không sập tiếp); giá 07/08 đang lên; taker cao
- Xác suất định tính: THẤP ngay bây giờ nếu rebuild tiếp. Tăng nếu 08/08 UTC pos_r sập lần 2.

---

**Phán quyết định tính:**

Tín hiệu mâu thuẫn nhau đặc trưng của giai đoạn chuyển tiếp post-ghế-rời. Pattern đọc được:

> OI đỉnh 08-06 (7.873M, 3× band) + funding NEG + GHẾ-RỜI LẦN 2 (08-05: pos_r −48%, giá +33%) = **sự kiện phân phối lớn nhất từ T0 đến nay.** Nhưng pos_r rebuild ngay (08-06,07) = MM/smart money KHÔNG rời hẳn.

**Kịch bản nhiều khả năng nhất (theo tín hiệu, KHÔNG kết luận):**
→ Hybrid (a)+(b): wash nhỏ đang diễn ra (gLSR về 1.1-1.3), sau đó leg mới nếu OI ổn định và gLSR flush bền. Kịch bản (c) cần pos_r sập lần 2 dưới 2.07.

---

**Chốt canh ngày 08/08:**

| Biến | Threshold | Hành động nếu chạm |
|------|-----------|-------------------|
| gLSR | ≤1.1 bền (2+ ngày) | Tái-ARM watch kịch bản (a) |
| pos_r | <2.07 (thấp hơn L-26 fire) | Kịch bản (c) tăng — inform operator |
| OI | Co về <5.766M (2× band) | Reset P3 clock đáng kể |
| funding 04:00 UTC | NEG | Pin streak thêm vỡ → ghi log |
| px | ≥0.02870 (ATH spot) đóng cửa | Leg mới xác nhận |
| px | ≤0.02157 (08-04 close) | Retrace sâu — L-26 follow-through |

**Verdict tổng: Operator ký sau khi đọc bảng trên. KHÔNG suy diễn vị thế.**

---

*Probe: `_probe_tut_refresh_20260808.py` | Nguồn: freshwatch_daily export + fapi klines/funding/LSR/OI*
*ANALYSIS ONLY — không điền verdict, không khuyến nghị vị thế*

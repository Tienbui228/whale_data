# GOM-A/B/C — ACUUSDT & CYSUSDT — 13/08/2026

```
data-source : scratch/freshwatch_daily_2026-{06,07,08}.csv + fapi.binance.com (bổ sung klines/funding)
machine     : local scratch
date-range  : 2026-06-01 → 2026-08-07  (store max; L-21 hôm nay 13/08 skip)
code-commit : TBD (probe chưa commit)
note        : fapi LSR endpoint trả 400 lỗi cho khoảng Jul01→Aug12 → toàn bộ LSR data đến từ freshwatch CSV
              Aug08-12 KHÔNG có trong store → analysis giới hạn đến Aug07
              GOM-C dùng local reimplementation (gom_scan._check_gom_c không export)
              taker CSV = ratio 0-1 (0.5 ≈ 50%); fapi days (Jul24-26) = percentage (47-52) → display khác đơn vị, logic đúng
```

---

## ACUUSDT

### P0 — Độ sâu dữ liệu

| Trường | Giá trị |
|--------|---------|
| lsr_min_date | 2026-06-01 |
| total rows | 68 (2026-06-01 → 2026-08-07) |
| LSR-valid rows | 65 |
| peak price | **$0.095635 ngày 2026-06-01 — TRONG store** |
| NaN gaps (lsr/oi) | 3 ngày: Jul24, Jul25, Jul26 (gap synthetic đã biết) |
| Latest snapshot (Aug07) | px=$0.080 · oi=$1.19M · lsr_pos=1.099 · lsr_acc=2.489 · gLSR=3.119 · f_avg=0.000315 · taker≈50% |

**Nhận xét P0:**
- Đỉnh giá ($0.096) = ngày đầu store (Jun01) → toàn bộ store là giai đoạn SAU đỉnh, giá suy giảm liên tục đến ~$0.073 (Jul15) rồi phục hồi nhẹ về $0.080 (Aug07).
- gLSR cực kỳ cao (2.5–4.2) xuyên suốt → retail long dominance toàn tập, KHÔNG phải môi trường gom.
- OI: $1.21M (Jun01) → $0.87M (Jul15) → $1.19M (Aug07) — net ~flat, nhưng trọng tâm là declining rồi phục hồi (không có build-up mới).

---

### Detector Fires — ACUUSDT

| Detector | Fires | Ngày |
|----------|-------|------|
| GOM-A | **0** | — |
| GOM-B | **0** | — |
| GOM-C | **0** | — |

**Lý do không fire:**

- **GOM-A blocked — A1 fail (primary):** A1 = avg3(lsr_pos)/avg3(lsr_acc) ≥ 1.5. Trên ACU, lsr_pos ≈ 1.0–1.19 và lsr_acc ≈ 2.1–3.7 → div_ratio ≈ 0.35–0.55 **< 1.5 mọi ngày**. Smart money không long-bias (accumulator short >> pos long).
- **GOM-A blocked — A2 fail (constant):** avg5(gLSR) ≤ 1.1 required. gLSR = 2.9–4.2 suốt 68 ngày → vượt threshold 3–4×. Retail quá lệch long, không thể là gom yên lặng.
- **GOM-B — suppressor DQ:** B1 (hedge_structure: div_ratio ≤ 0.5) về mặt số học *có thể thỏa* (div_ratio≈0.44 ≤ 0.5), B2 (funding_pinned) *có thể thỏa* (f_avg=5e-5 nhiều ngày), B4 (NOT funding_neg_div) thỏa. **Nhưng suppressor block toàn bộ** — khả năng cao lsr_dist DQ do gLSR=3.0+ vượt ngưỡng.
- **GOM-C blocked:** C1 (stealth_grind: breakout ≥9% từ 14d high) không xảy ra — giá declining toàn bộ khoảng Jun-Aug07, không có breakout momentum. Suppressor cũng DQ.

---

### Chapter Analysis — ACUUSDT

```
Chapters với net > 0 : 0
Churn chapters       : 0
GOM-A/B fires        : 0
Q1_cum_usd           : $0
net_oi_delta_usd     : ≈ −$20K (Jun01: $1.21M → Aug07: $1.19M, net flat/slight decline)
VWAP build           : N/A (không có chapter)
```

---

### Forward Analysis — ACUUSDT

Không có chapter → không có forward.

---

### RAW LSR — ACUUSDT (tóm tắt operator)

```
date          avg_px       oi_usd   pos_r   acc_r    gLSR     f_avg  taker
--------------------------------------------------------------------------
2026-06-01   0.09564    1,210,629  0.9530  2.8715  3.3085  0.000050   ~50%
2026-06-10   0.07368      894,672  1.0433  3.3215  3.9164  0.000050   ~50%
2026-06-20   0.08632      969,128  1.1475  2.9417  3.4033  0.000050   ~50%
2026-06-30   0.08023      950,328  1.0762  2.5587  3.0833  0.000063   ~50%
2026-07-10   0.07641      892,777  1.1747  2.5753  2.9185  0.000050   ~50%
2026-07-20   0.07518      870,245  1.1094  2.5727  3.3234  0.000050   ~50%
2026-07-27   0.07805      969,490  1.0831  2.5137  3.0634  0.000085   ~50%
2026-08-01   0.07633    1,133,482  1.1323  2.6657  3.0177  0.000089   ~50%
2026-08-07   0.08011    1,187,748  1.0992  2.4892  3.1186  0.000315   ~50%
```

**Key pattern ACU:** lsr_pos ~1.0–1.2 (retail long, nhẹ), lsr_acc ~2.1–3.7 (accumulator NẶNG SHORT). gLSR = 3.0–4.2 (toàn bộ hệ thống lệch long nặng). Funding = cố định 5e-5 (neutral max pinned). Đây là cấu trúc: retail ôm long + accumulator hedge mạnh → **phân phối chậm, không phải gom**.

---

### Kết luận — ACUUSDT

> **KHÔNG có lực gom RÒNG.** 0/3 detector fire. Cấu trúc gLSR=3.0–4.2 toàn store = wrong-side permanent. div_ratio=0.44 < 1.5 → A1 fail tuyệt đối. Price declining từ đỉnh (Jun01) → không có breakout. Net OI ~flat. Tín hiệu: retail ôm long, accumulator hedge, funding pinned neutral → **churn seat-rotation**, không phải accumulation có hướng.

---

---

## CYSUSDT

### P0 — Độ sâu dữ liệu

| Trường | Giá trị |
|--------|---------|
| lsr_min_date | 2026-06-01 |
| total rows | 68 (2026-06-01 → 2026-08-07) |
| LSR-valid rows | 65 |
| peak price | **$0.812567 ngày 2026-08-06 — TRONG store (pump event)** |
| NaN gaps (lsr/oi) | 3 ngày: Jul24, Jul25, Jul26 |
| Latest snapshot (Aug07) | px=$0.786 · oi=$20.9M · lsr_pos=0.947 · lsr_acc=0.490 · gLSR=0.520 · f_avg=0.000075 |

**Nhận xét P0:**
- Store bắt đầu tại $0.452 (Jun01), suy giảm xuống $0.263 (Jul29), sau đó pump mạnh lên $0.813 (Aug06).
- Đỉnh Aug06 NẰM TRONG store (KHÔNG phải lịch sử pre-store) → đây là pump event được capture đầy đủ.
- Pump Aug04–07 đi kèm OI tăng 3×: $7.1M → $23.1M → massive short squeeze.
- Aug08-12 KHÔNG có trong store → không biết hướng hậu-pump.

---

### Detector Fires — CYSUSDT

| Detector | Fires | Ngày |
|----------|-------|------|
| GOM-A | **0** | — |
| GOM-B | **0** | — |
| GOM-C | **0** | — |

**Partial signal:** Jun06 có partial "a" trong raw (một điều kiện GOM-A thỏa) nhưng suppressor DQ block.

**Lý do không fire:**

- **Giai đoạn Jun01–Jul23 (distribution):** OI declining $12.2M → $7.6M, giá declining. lsr_pos = 1.4–2.2, lsr_acc = 0.97–1.6, gLSR = 1.0–1.9. A2 thất bại (gLSR > 1.1 phần lớn thời gian). Suppressor DQ liên tục — cấu trúc phân phối, không phải gom.

- **Giai đoạn Jul27–Aug03 (flat/pre-pump):** OI flat $7.2–8.1M. gLSR = 1.4–1.7. A2 vẫn fail (avg5_gLSR > 1.1). Không có accumulation signal.

- **Aug04–07 (pump):** SHORT SQUEEZE — không phải gom mới:
  - Aug04: px +64% một ngày ($0.289 → $0.475), OI chỉ +$0.8M (không build nhiều)
  - Aug05: px $0.646, OI $22.3M (+$15M!), funding = **−0.001299** (shorts trả longs cực mạnh), gLSR = 0.459 (retail SHORT vào giữa pump → bị squeeze)
  - Aug06: px đỉnh $0.813, OI $23.1M, funding = +0.000046 (bình thường)
  - Aug07: px $0.786 (pullback), OI $20.9M (giảm nhẹ)
  - Cơ chế: retail short + OI build mới (FOMO longs) vào pump, không phải gom yên lặng trước.
  - Suppressor: funding_neg_div Aug05 (f_avg=−0.001299 << −2e-4), post_climax sau pump → 14d cooldown.

- **GOM-C:** C1 (stealth_grind ≥9% từ 14d high) nếu tính từ flat zone Jul-Aug03 thì Aug04 có thể breakout. Nhưng funding_neg_div Aug05 DQ ngay, và C2_quiet yêu cầu f_avg ≤ 2e-4 (f_avg Aug05 = −1.3e-3, vi phạm nặng). GOM-C không thể fire trong vùng short squeeze.

---

### Chapter Analysis — CYSUSDT

```
Chapters với net > 0 : 0
GOM-A/B fires        : 0
Q1_cum_usd           : $0
net_oi_delta_usd     : ~−$4.15M (Jun01: $12.2M → Jun25: $8.2M = distribution leg)
                        post-pump Aug07: $20.9M vs pre-pump Aug03: $7.2M → +$13.7M (FOMO longs, không phải gom)
VWAP build           : N/A
```

**OI narrative:**
- Jun01–Jun25: OI $12.2M → $8.2M (−33%) = active distribution / long unwinding
- Jun25–Aug03: OI $8.2M → $7.2M (further −12%) = continued attrition
- Aug04–07: OI $7.1M → $23.1M = short squeeze + FOMO fresh longs vào đỉnh
- Net gom yên lặng (ΔOI⁺ accumulation trong quiet period): **$0** — không có chapter nào fire

---

### Forward Analysis — CYSUSDT

Không có chapter → không có forward.

---

### RAW LSR — CYSUSDT (tóm tắt operator)

```
date          avg_px       oi_usd   pos_r   acc_r    gLSR     f_avg     event
--------------------------------------------------------------------------
2026-06-01   0.45211   12,195,189  2.2084  1.1290  1.1692  0.000133   (store open)
2026-06-10   0.44219   11,812,903  1.4820  1.1441  1.2075  0.000113
2026-06-20   0.41952   10,864,029  1.4457  1.2075  1.1925  0.000065   (distribution)
2026-06-30   0.35064    8,437,911  1.3595  1.3513  1.4594  0.000055   (OI -31%)
2026-07-10   0.30431    7,653,250  1.3027  1.7189  1.8241  0.000061
2026-07-20   0.30113    7,491,350  1.7014  1.6212  1.7315  0.000099   (flat zone, price low)
2026-07-29   0.26334    7,735,260  1.6287  1.4010  1.5394  0.000078   (price trough)
2026-08-03   0.28952    7,245,374  1.3326  1.5595  1.8802  0.000050   (pre-pump)
2026-08-04   0.47517    7,141,222  1.3673  1.6846  2.0084  0.000310   [PUMP START]
2026-08-05   0.64568   22,337,355  0.9948  0.3826  0.4586 -0.001299   [SHORT SQUEEZE peak ← funding crash]
2026-08-06   0.81257   23,108,871  0.8931  0.4596  0.5316  0.000046   [PRICE ATH IN STORE]
2026-08-07   0.78642   20,863,458  0.9474  0.4896  0.5198  0.000075   (post-squeeze pullback)
```

**Key pattern CYS:**
- Jun01–Jul23: lsr_pos=1.4–2.2, lsr_acc=0.97–1.6, gLSR=1.0–1.9 → retail long, accumulator short-neutral. Distribution cấu trúc (pos > acc = longs > shorts trong retail segment, nhưng OI declining → longs đang bán ra).
- Aug04–07: gLSR drops 2.0 → 0.46 → retail SHORT vào pump. lsr_acc drops 1.68 → 0.38 (accumulator cover short hoặc flip long). Funding = −1.3e-3 ngày Aug05 = short sellers trả lãi cực mạnh. **Đây là SHORT SQUEEZE textbook, không phải gom yên lặng.**

---

### Kết luận — CYSUSDT

> **KHÔNG có lực gom RÒNG.** 0/3 detector fire. Giai đoạn Jun–Jul là distribution (OI declining −40%). Pump Aug04–07 là SHORT SQUEEZE (funding −1.3e-3, retail short vào pump, OI tripling = longs mới vào sau sự kiện). Không có chapter nào net > 0. Không có stealth accumulation trước pump — cơ chế hoàn toàn khác GOM signature.

---

---

## TỔNG KẾT

| Token | GOM-A | GOM-B | GOM-C | Chapter net>0 | Kết luận |
|-------|-------|-------|-------|---------------|---------|
| ACUUSDT | 0 | 0 | 0 | 0 | **KHÔNG gom RÒNG** — churn/seat-rotation |
| CYSUSDT | 0 | 0 | 0 | 0 | **KHÔNG gom RÒNG** — distribution + short squeeze |

### Tại sao không fire (structural summary)

**ACUUSDT:**
- gLSR = 3.0–4.2 toàn store → wrong-side permanent, A2 fail absolute
- div_ratio (pos/acc) = 0.35–0.55 < 1.5 → A1 fail absolute (accumulator heavy short, không phải smart-money long)
- Price declining từ đỉnh Jun01 → không có breakout momentum cho GOM-C
- Funding = 5e-5 neutral pinned → không có urgency signal
- **Pattern:** retail long + accumulator hedge = slow distribution hoặc neutral rotation, KHÔNG phải accumulation

**CYSUSDT:**
- Jun–Jul: OI declining 40%, gLSR > 1.1 → distribution zone, A2 fail
- Aug04–07 pump: funding_neg_div DQ (f_avg = −1.3e-3), post_climax cooldown → GOM suppressed
- **Pattern:** distribution Jun→Jul → short squeeze Aug04–07 (không có gom phase trước pump)

### Điều tra sau nếu operator muốn

1. **CYS pre-pump accumulation offchain?** Onchain wallet analysis (BscScan) — store perp không capture onchain gom. Đây là tầng HUMAN (Nansen LOCKED).
2. **ACU store sau Aug07?** Fetch Aug08–12 manually khi store VPS cập nhật — có thể có breakout signal post-Aug12.
3. **GOM-D retrospective CYS?** Vol-wake Aug04–07 (345×? chưa tính) + nền-chết Jun–Jul → GOM-D criteria khác với A/B/C.

---

**DỪNG CHỜ OPERATOR ĐỌC.**

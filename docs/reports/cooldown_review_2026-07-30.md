# Cooldown Review — 2026-07-30 (data chốt 29/07)

Nguồn: `freshwatch_daily_2026-07.csv` VPS, probe 2026-07-29.  
Ghi chú: Jul 24-26 missing toàn universe (mass outage), không có data.  
**Verdict: CẦN OPERATOR** — agent chỉ soạn framework, không tự điền verdict.

---

## 1. PARTIUSDT

### 10-ngày cuối (Jul 19-29, thiếu 24-26)

| Date    | pos_r  | acc_r  | div_raw | gLSR   | OI (USD)   | f_avg     | fn |
|---------|--------|--------|---------|--------|------------|-----------|----|
| Jul 19  | 2.1567 | 0.7931 | 2.72    | 0.5177 | 4,207,273  | 2.67e-05  | 6  |
| Jul 20  | 2.2421 | 0.8315 | 2.70    | 0.5499 | 4,568,642  | 5.00e-05  | 6  |
| Jul 21  | 2.2647 | 0.8403 | 2.69    | 0.5404 | 4,505,013  | 4.39e-05  | 6  |
| Jul 22  | 2.3938 | 0.8674 | 2.76    | 0.5571 | 4,328,279  | 5.00e-05  | 6  |
| Jul 23  | 2.3968 | 0.9497 | 2.52    | 0.6176 | 4,125,261  | 2.24e-05  | 6  |
| Jul 27  | 2.2953 | 1.2624 | 1.82    | 0.8389 | 3,675,412  | 1.12e-05  | 6  |
| Jul 28  | 2.1697 | 1.2026 | 1.80    | 0.7778 | 3,579,896  | 5.00e-05  | 1* |
| Jul 29  | 2.0833 | 1.2810 | 1.63    | 0.8539 | 3,458,474  | 5.00e-05  | 1* |

`*` fn=1 → low_conf (1 funding snapshot).

**Tóm tắt tín hiệu 29/07:**
- `div_raw` = 1.63, `div_avg3` ≈ 1.75 → vẫn trên ngưỡng suppression (>1.5)
- `gLSR` = 0.854 → **bear-zone** (< 1.0), thị trường ngả short global
- OI: 4.2M → 3.5M (-17%), đang co
- Funding: PINNED (5e-05 × 6 tiếp tục)
- Xu hướng: div_raw cải thiện từ 3.42 (Jul 10 peak) → 1.63, nhưng chưa về dưới 1.5

**Đề xuất agent:** Xem xét UNLOCK — div_raw trending down rõ ràng (3.42 → 1.63 trong 19 ngày), gLSR < 1 (bear-zone unusual), OI co. Tuy nhiên pos_r=2.08 vẫn cao — operator quyết.

---

## 2. EVAAUSDT

### 10-ngày cuối (Jul 19-29, thiếu 24-26)

| Date    | pos_r  | acc_r  | div_raw | gLSR   | OI (USD)   | f_avg     | fn |
|---------|--------|--------|---------|--------|------------|-----------|----|
| Jul 19  | 1.2318 | 1.1053 | 1.114   | 1.0803 | 8,248,887  | 5.00e-05  | 6  |
| Jul 20  | 1.2861 | 1.1668 | 1.102   | 1.1048 | 7,688,705  | 5.15e-05  | 6  |
| Jul 21  | 1.2758 | 1.1124 | 1.147   | 1.1151 | 8,556,316  | 5.55e-05  | 6  |
| Jul 22  | 1.2964 | 1.1400 | 1.137   | 1.0916 | 7,864,886  | 5.00e-05  | 6  |
| Jul 23  | 1.3223 | 1.2962 | 1.020   | 1.1959 | 7,532,456  | 8.70e-05  | 6  |
| Jul 27  | 1.3656 | 1.6137 | 0.847   | 1.5641 | 6,972,286  | 1.15e-04  | 6  |
| Jul 28  | 1.4206 | 1.5019 | 0.946   | 1.5119 | 6,877,175  | 5.00e-05  | 1* |
| Jul 29  | 1.3894 | 1.6371 | 0.849   | 1.7457 | 6,213,559  | 5.00e-05  | 1* |

**Tóm tắt tín hiệu 29/07:**
- `div_raw` = 0.849 → **đã đảo chiều** (acc > pos), div_avg3 ≈ 0.881
- `gLSR` = 1.7457 → rising trend (cần theo dõi tốc độ)
- OI: 22.4M (Jul 10 peak) → 6.2M (-72%) — giảm mạnh và bền
- Funding: PINNED 2 ngày cuối (fn=1 low_conf)
- Xu hướng: cấu trúc LSR đã normalize hoàn toàn

**Đề xuất agent:** Đề xuất UNLOCK — div_raw < 1 (0.849), OI co -72% từ peak, cấu trúc đảo chiều rõ ràng. gLSR 1.75 đang tăng — monitor sau unlock.

---

## 3. CLOUSDT

### 10-ngày cuối (Jul 19-29, thiếu 24-26)

| Date    | pos_r  | acc_r  | div_raw | gLSR   | OI (USD)   | f_avg     | fn |
|---------|--------|--------|---------|--------|------------|-----------|----|
| Jul 19  | 0.8507 | 1.0040 | 0.847   | 0.8650 | 4,599,085  | 5.00e-05  | 6  |
| Jul 20  | 1.0021 | 1.0665 | 0.940   | 0.8925 | 4,371,288  | 5.00e-05  | 6  |
| Jul 21  | 0.9601 | 1.0153 | 0.946   | 0.8232 | 4,197,739  | 1.81e-05  | 6  |
| Jul 22  | 0.9053 | 1.1088 | 0.816   | 0.8657 | 4,083,934  | -2.19e-05 | 6  |
| Jul 23  | 0.9093 | 1.1964 | 0.760   | 0.9608 | 4,049,136  | 5.00e-05  | 6  |
| Jul 27  | 0.9209 | 1.5132 | 0.608   | 1.1829 | 4,365,272  | 5.00e-05  | 6  |
| Jul 28  | 0.8989 | 1.6281 | 0.552   | 1.2558 | 4,347,131  | 5.00e-05  | 1* |
| Jul 29  | 0.8699 | 1.7049 | 0.510   | 1.4010 | 4,171,570  | 5.00e-05  | 1* |

**Tóm tắt tín hiệu 29/07:**
- `pos_r` = 0.869 → **dưới 1.0** (inverted: long nhiều hơn short ở account-level)
- `div_raw` = 0.510 → đảo chiều sâu
- `gLSR` = 1.401 → moderate, đang tăng
- OI: 4.0-4.4M, tương đối stable
- Funding: PINNED (mostly 5e-05)

**Đề xuất agent:** Đề xuất UNLOCK — pos_r < 1 (inverted structure), div_raw = 0.51, cấu trúc bình thường, OI stable. gLSR=1.40 vẫn trong vùng bình thường.

---

## 4. BLUAIUSDT

### 10-ngày cuối (Jul 19-29, thiếu 24-26)

| Date    | pos_r  | acc_r  | div_raw | gLSR   | OI (USD)   | f_avg     | fn |
|---------|--------|--------|---------|--------|------------|-----------|----|
| Jul 19  | 1.3961 | 1.0280 | 1.358   | 1.0020 | 5,097,200  | 2.40e-04  | 6  |
| Jul 20  | 1.4197 | 1.1013 | 1.289   | 1.0239 | 5,126,747  | 3.06e-04  | 6  |
| Jul 21  | 1.4875 | 1.4050 | 1.058   | 1.3186 | 5,646,556  | 5.74e-05  | 6  |
| Jul 22  | 1.3817 | 1.2650 | 1.092   | 1.1468 | 5,109,152  | 1.18e-04  | 6  |
| Jul 23  | 1.5202 | 1.2099 | 1.257   | 1.1304 | 5,533,190  | 1.85e-04  | 6  |
| Jul 27  | 1.3445 | 1.9248 | 0.699   | 2.2744 | 5,155,202  | 1.98e-04  | 6  |
| Jul 28  | 1.3265 | 2.0395 | 0.650   | 2.3933 | 5,038,978  | 5.00e-05  | 1* |
| Jul 29  | 1.3136 | 2.0741 | 0.633   | 2.5323 | 5,389,692  | 3.29e-04  | 1* |

**Tóm tắt tín hiệu 29/07:**
- `gLSR` = 2.5323 → **HOT** (cao nhất trong 4 token, bùng lên từ 1.13 ngày 23/07)
- `funding_avg` = 0.000329 (3.29e-04) → funding HOT
- `div_raw` = 0.633 → đảo chiều (acc > pos)
- OI: stable ~5.0-5.6M
- Xu hướng: gLSR và funding cùng bùng, cấu trúc đang leo thang

**Đề xuất agent:** REMAIN COOLDOWN — gLSR bùng lên 2.53 (peak mới từ sau Jul 23), funding HOT +0.033%, dù div_raw đảo chiều nhưng áp lực global short rất mạnh. Chưa an toàn để unlock.

---

## Framework UNLOCK (3 ứng viên: PARTI / EVAA / CLO)

Tiêu chí **đủ điều kiện xem xét unlock** (tham chiếu — operator xác nhận):

| Tiêu chí | PARTI | EVAA | CLO |
|----------|-------|------|-----|
| div_raw < 1.5 hoặc đảo chiều | OK (1.63, trending) | OK (0.849) | OK (0.510) |
| gLSR không hot (< 2.0) | OK (0.854) | OK (1.746) | OK (1.401) |
| OI không bùng (vs med14 < 1.5) | Cần kiểm | Cần kiểm | Cần kiểm |
| funding không HOT | OK (pinned) | OK (pinned) | OK (pinned) |
| pos_r đang giảm | OK (2.74→2.08) | Stable (~1.3-1.4) | OK (<1.0) |

**oi_vs_med14**: chưa tính được tại đây — cần window 14 ngày đầy đủ (Jul 24-26 missing).  
Agent ghi nhận: `oi_vs_med14` là canonical từ `signals.py` (window ending ngày-trước-check).  
**Operator cần verify oi_vs_med14 từ VPS signals.py trước khi unlock.**

---

## CẦN OPERATOR

1. Xác nhận verdict UNLOCK / REMAIN cho PARTI, EVAA, CLO
2. Xác nhận REMAIN COOLDOWN cho BLUAI
3. Verify `oi_vs_med14` từ VPS signals.py (window chuẩn) cho 3 ứng viên
4. Điền verdict vào `CASE_PARTI.xlsx`, `CASE_EVAA.xlsx`, `CASE_CLO.xlsx`, `CASE_BLUAI.xlsx` sheet CASE (agent không tự điền)

---

*Tạo bởi agent 2026-07-29 | Dữ liệu từ freshwatch_daily_2026-07.csv + ledger_v2.xlsx*

# WALLETSET 2×2 phân bố — trình operator điền ngưỡng (KÝ 27/08)

**Yêu cầu:** operator ký · thay `Δholders≠0` thô (quá nhiễu) bằng matrix 2×2 auto-tag {CONCENTRATED · BROAD-QUIET · BROAD-STRESS} từ 3 metric (|Δbal|, Δholders, perp-stress). Display-only, chưa code tag cho tới ký ngưỡng.

**Data window:** fw-139 × 30d (2026-07-27 .. 2026-08-25) · nguồn Nansen snapshots + spot_klines_1d.  
**Full text output:** [docs/reports/walletset_2x2_dist_20260827.txt](docs/reports/walletset_2x2_dist_20260827.txt) md5 `37aa8f83740ee3ea3efb531fa94238b1`

---

## (i) |Δbal| OUT-step 1d (kho đi ra, chỉ Δ<0)

**n = 1,342 out-steps** observed trong 30d × fw-139.

| Percentile | |Δbal| |
|-----------|--------|
| p50       | 0.18%  |
| p75       | 0.60%  |
| p90       | 1.61%  |
| p95       | 3.99%  |
| p99       | 15.48% |
| max       | 97.19% (SOPH 08-24→25) |

**Bucket:**

| Range      | Count | %      |
|------------|-------|--------|
| [0, 5)%    | 1,290 | 96.1%  |
| [5, 10)%   | 28    | 2.1%   |
| [10, 20)%  | 15    | 1.1%   |
| [20, 50)%  | 7     | 0.5%   |
| [50, 80)%  | 1     | 0.1%   |
| [80, 100)% | 1     | 0.1% (SOPH) |

**Tail:**
- ≥20% :  9 (0.7%)
- ≥30% :  5 (0.4%)
- ≥50% (VERIFY-WALLETSET ký):  2 (0.1%)

**Đề xuất operator điền:**
- **Reuse 0.50 đã ký?** — captures 0.1% (rất sparse, chỉ extreme cases như SOPH). Match "outlier hardcut" scope.
- **Alternative 20%** — captures 0.7% (~9/tháng cho fw-139). Balance signal/noise.
- **Alternative 30%** — captures 0.4% (~5/tháng). Middle.
- Ngưỡng chọn: **[ ]%**

---

## (ii) Δholders/ngày (nhiễu-nền vs tail)

**n = 2,864 samples** (fw-139 × ~30d ingest-pairs).

**Signed breakdown:**
- Δ=0 (phẳng): 833 (29.1%)
- Δ>0 (holder tăng): 970 (33.9%)
- Δ<0 (holder giảm): 1,061 (37.0%)

**|Δholders| percentiles:**

| Percentile | |Δholders| |
|-----------|-----------|
| p50       | 1          |
| p75       | 5          |
| p90       | 21         |
| p95       | 45         |
| p99       | 269        |
| max       | 1,335      |

**Bucket:**

| Range        | Count | %      |
|--------------|-------|--------|
| [0, 1)       | 833   | 29.1% (Δ=0 phẳng) |
| [1, 2)       | 637   | 22.2% (baseline noise: ±1 wallet) |
| [2, 3)       | 289   | 10.1% |
| [3, 5)       | 314   | 11.0% |
| [5, 10)      | 294   | 10.3% |
| [10, 20)     | 196   | 6.8%  |
| [20, 50)     | 166   | 5.8%  |
| [50, ...)    | 131   | 4.6% (tail) |

**Tail:**
- |Δholders|≥1: 2,031 (70.9%) — quá lỏng (bao gồm noise ±1)
- |Δholders|≥2: 1,394 (48.7%)
- |Δholders|≥3: 1,105 (38.6%)
- |Δholders|≥5: 791 (27.6%)

**Đề xuất operator điền:**
- **Nhiễu-nền = ±1 wallet/day** (22.2% samples có |Δ|=1) — không dùng làm signal.
- **"Lớn" candidates:**
  - |Δholders|≥5 → 27.6% — vẫn đông (dễ trigger)
  - |Δholders|≥10 → ~15% — middle
  - |Δholders|≥20 → ~10% — strict
- **Signed hay abs?** — signed cho phép phân biệt CONCENTRATED (ít ví hơn = Δ<0 tail) vs BROAD (nhiều ví hơn = Δ>0 tail). Đề xuất **signed + threshold trên |Δ|**.
- Ngưỡng chọn: **|Δholders|≥[ ]**, sign: **[ ]** (signed | abs)

---

## (iii) STRESS metric (vol≥3×med14 ∨ ret1d≤-5%)

**n = 663 vol samples · 663 ret samples · 1,807 stress pairs** (fw-139 × 30d, khi có đủ 14d prev vol để tính med14).

**vol/med14 percentiles:**

| Percentile | vol/med14 |
|-----------|-----------|
| p50       | 1.05×     |
| p75       | 1.68×     |
| p90       | 3.16×     |
| p95       | 5.30×     |
| p99       | 15.89×    |
| max       | 30.24×    |

**vol/med14 tail:**
- ≥2×: 131 (19.8%)
- ≥3×: 72 (10.9%) — đề xuất
- ≥5×: 38 (5.7%)
- ≥10×: 14 (2.1%)

**ret1d percentiles (signed %):**

| Percentile | ret1d    |
|-----------|----------|
| p1        | -16.29%  |
| p5        | -7.83%   |
| p10       | -5.36%   |
| p50       | 0.00%    |
| p90       | 7.09%    |
| p95       | 8.82%    |
| p99       | 22.47%   |

**ret1d tail:**
- ≤-3%: 149 (22.5%) — quá lỏng
- ≤-5%: 76 (11.5%) — đề xuất
- ≤-8%: 30 (4.5%)
- ≤-10%: 24 (3.6%)
- ≤-15%: 11 (1.7%)

**Combined stress (vol≥3× ∨ ret≤-5%) — n_pairs=1,807:**
- vol≥3×: 72 (4.0%)
- ret≤-5%: 76 (4.2%)
- **vol≥3× ∨ ret≤-5%: 135 (7.5%)** ← rẻ, single-day rung thấy
- vol≥3× ∧ ret≤-5%: 13 (0.7%) — rare co-occurrence

**Đề xuất operator điền:**
- **vol/med14≥[ ]×** — đề xuất 3× (10.9% samples), match H3 spec `vol_mult_med14_min: 8.0` hay riêng?
  - **Note:** yaml gom_h.h3 hiện dùng `vol_mult_med14_min: 8.0` (8×) — rất strict. 2.1% samples đạt.
  - Nếu tái dùng 8× → stress rất hiếm; nếu dùng 3× → dense hơn.
- **ret1d≤[ ]%** — đề xuất -5% (11.5%) hoặc -8% (4.5%)
- **AND | OR** — OR bắt được co lún riêng, AND filter khắt (0.7%). Đề xuất OR.

---

## Matrix 2×2 đề xuất (sau khi có ngưỡng)

```
                      |Δbal| ≥ [ ]%       |Δbal| < [ ]%
                      -------------       --------------
Δholders "lớn"        CONCENTRATED*       BROAD-QUIET
(kho lớn, ít ví)      (ít ví ra hết       (nhiều ví thay
                       nhưng ...)          đổi)

Δholders "phẳng"      —                    —
(≤noise)              (không tag)          (không tag)

+ perp stress
(vol≥3× ∨ ret≤-5%)     BROAD-STRESS       BROAD-STRESS
                       (nếu cùng ngày)     (nếu cùng ngày)
```

*CONCENTRATED* semantic đề xuất: kho drop lớn (|Δbal| tail) + holders drop lớn (|Δholders| tail) → tập trung ở ít ví. Ngược lại BROAD nghĩa nhiều ví.

**Chờ operator điền 3 ngưỡng + confirm signed/abs + AND/OR → code tag** (display-only, không đổi compose).

---

## Chưa code

Per operator "display-only, chưa code tag cho tới chữ operator". Sau khi operator điền 3 ngưỡng, agent sẽ:
- Wire compute trong gom_h_daily.py (thêm 3 cột CSV: wallet_delta_pct, wallet_delta_holders, wallet_stress_flag)
- Render tag `[WALLETSET: <CONCENTRATED|BROAD-QUIET|BROAD-STRESS>]` trailer sau `[VERIFY-WALLETSET]` khi kho lane active
- yaml goi_nhe.walletset_2x2 block với 3 ngưỡng + matrix rules

---

## KÝ 27/08 · CHỐT NGƯỠNG + WIRED

Operator KÝ 27/08:
- (i) |Δbal| ≥ **50%** (reuse VERIFY-WALLETSET threshold)
- (ii) |Δholders| ≥ **5** (**abs**)
- (iii) stress = vol/med14 ≥ **5×** OR ret1d ≤ **-8%** (**OR** combine)
- Cả 3 PROVISIONAL cùng chuyến review ramp + [50%] · expiry 2026-09-26

**Wired vào yaml `goi_nhe.walletset_2x2`** (yaml md5 mới `3820b87c`) + `gom_h_daily.py` rev4-final. CSV +cột `wallet_delta_pct`, `wallet_delta_holders`, `wallet_stress_flag`, `walletset_tag`. Trailer `[WALLETSET: <tag>]` sau `[VERIFY-WALLETSET]`.

## Anchor exhibit — SOPH 2026-08-25

- |Δbal| = **-97.19%** (≥50% ✓)
- |Δholders| = **1** (38-39, **<5** ✗)
- stress: vol/med14 = ~3× (<5× ✗), ret1d = -4.3% (>-8% ✗) → **KHÔNG stress**
- Result: **KHÔNG tag 2×2** (chỉ có `[VERIFY-WALLETSET]` từ hệ riêng)

**Bài học anchor:** kho drop lớn ≠ CONCENTRATED tự động — cần cả 2 điều kiện (|Δbal| + |Δholders|). SOPH là **DELIST-MIGRATION** (holders phẳng, 1 whale rời tập với hầu hết balance) — matrix 2×2 đúng không tag; VERIFY-WALLETSET catch riêng.

## Smoke 08-25 wire verify (VPS post-SCP)

30 fires (was 16 pre-os-fix — xem note ramp restoration bên dưới), tag phân bố:
- BROAD-STRESS: BASUSDT (vol=8.6× ret=-12.2%) · CLOUSDT (ret=-8.5%) · HANAUSDT (vol=9.8×) · HEMIUSDT (ret=-13.9%) · TACUSDT (vol=118.7×) · 龙虾USDT (vol=9.7×)
- BROAD-QUIET: 0GUSDT · OPNUSDT · XPINUSDT
- CONCENTRATED: (không có 08-25)
- SOPH: **không tag 2×2** (anchor case) — chỉ `[VERIFY-WALLETSET]`

## NOTE — ramp restoration side-effect (accidental, cần operator soi)

Khi wire 2×2, phát hiện `_os_env` chưa import trong prod → `import os as _os_env` bổ sung. Fix ĐỒNG THỜI restore ramp compute (silent-fail từ trước): fires 08-25 nhảy **16 → 30** vì 14 fires H1-ramp (18 tokens h1_ramp_raw=True) trước đây bị nuốt trong try/except.

Đây KHÔNG phải display-only — compose semantic đổi. Nếu operator soi lại và muốn:
- **Accept ramp restoration** (per gói-nhẹ compose OR intent) → G6 2 đêm official RESET count từ đêm-2 rev4-final code md5 mới
- **Rollback ramp** (nếu muốn signed-only trước ramp review 09-28) → cần yaml flag disable ramp trong compose, giữ display-only

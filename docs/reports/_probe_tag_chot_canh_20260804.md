# PROBE TAG — Chot Canh 31/07→04/08
Run: 2026-08-04 08:13 UTC
TAGUSDT rows in store: 70 (2026-05-26 → 2026-08-03)

## Funding Interval Verify (fapi native, last 20 periods TAGUSDT)

  2026-08-01 04:00 UTC  rate=0.000305
  2026-08-01 08:00 UTC  rate=0.000068
  2026-08-01 12:00 UTC  rate=0.000050
  2026-08-01 16:00 UTC  rate=0.000168
  2026-08-01 20:00 UTC  rate=0.000380
  2026-08-02 00:00 UTC  rate=0.000272
  2026-08-02 04:00 UTC  rate=0.000156
  2026-08-02 08:00 UTC  rate=0.000050
  2026-08-02 12:00 UTC  rate=0.000050
  2026-08-02 16:00 UTC  rate=0.000050
  2026-08-02 20:00 UTC  rate=0.000050
  2026-08-03 00:00 UTC  rate=0.000050
  2026-08-03 04:00 UTC  rate=0.000050
  2026-08-03 08:00 UTC  rate=0.000050
  2026-08-03 12:00 UTC  rate=0.000050
  2026-08-03 16:00 UTC  rate=0.000050
  2026-08-03 20:00 UTC  rate=0.000050
  2026-08-04 00:00 UTC  rate=0.000050
  2026-08-04 04:00 UTC  rate=0.000050
  2026-08-04 08:00 UTC  rate=0.000050

  → Dominant interval: 4h (TAG funding cycle = 4h)
  → fn=6 trong freshwatch = 6 × 4h = 24h = 1.0d coverage/ngay

## T1 — Chuỗi TAGUSDT 28/07→03/08 (đầy đủ + SUSPECT flags)

CAVEAT DATA:
- 27/07: fn=1 = PARTIAL DAY — pos_r 1.3508 nghi partial, không dùng làm ref chốt
- 04/08: partial day — chưa có row, ghi PENDING
- 30/07: px_avg có trong freshwatch (0.001099) — DAILY xlsx đang thiếu, cần operator append

| date | px | ret_1d | ret_3d | vol_M | tk% | f_avg | f_min | f_max | fn | OI_M | OI_pos | pos_r | acc_r | gLSR | div | div3 | slope5d | SUSPECT |
|------|-----|--------|--------|------:|----:|------:|------:|------:|---:|-----:|--------|------:|------:|-----:|----:|-----:|--------:|---------|
| 2026-07-25 | 0.001037 | +0.8% | -3.8% | 3.1 | 49.9 | 0.00006 | 0.00005 | 0.00010 | 6 | 8.32 | MID(35%) | 1.7082 | 1.1608 | 1.5800 | 0.680 | 0.680 | 1.199 | OK |
| 2026-07-26 | 0.001111 | +7.2% | +7.2% | 2.8 | 46.9 | 0.00010 | 0.00005 | 0.00034 | 6 | 8.77 | MID(41%) | 1.7046 | 1.2533 | 1.6774 | 0.735 | 0.698 | 1.202 | OK |
| 2026-07-27 | 0.001127 | +1.5% | +9.5% | 0.3 | 50.2 | 0.00005 | 0.00005 | 0.00005 | 1 | 9.13 | MID(46%) | 1.3508 | 1.2563 | 1.7071 | 0.930 | 0.782 | 1.112 | fn=1(partial),SUSPECT-27 |
| 2026-07-28 | 0.001330 | +18.0% | +28.3% | 11.9 | 49.9 | 0.00018 | 0.00005 | 0.00031 | 6 | 12.19 | PEAK(87%) | 1.5950 | 0.9988 | 1.2978 | 0.626 | 0.764 | 0.833 | OK |
| 2026-07-29 | 0.001206 | -9.3% | +8.6% | 5.5 | 49.5 | 0.00010 | 0.00005 | 0.00026 | 6 | 11.17 | PEAK(73%) | 1.6204 | 1.3719 | 1.8129 | 0.847 | 0.801 | 1.189 | OK |
| 2026-07-30 | 0.001099 | -8.9% | -2.5% | 3.5 | 49.1 | 0.00005 | 0.00005 | 0.00005 | 6 | 9.66 | MID(53%) | 1.6632 | 1.5316 | 1.9958 | 0.921 | 0.798 | 1.263 | OK |
| 2026-07-31 | 0.001356 | +23.3% | +1.9% | 20.8 | 50.1 | 0.00016 | 0.00005 | 0.00047 | 6 | 9.38 | MID(49%) | 1.6811 | 1.4795 | 1.9223 | 0.880 | 0.883 | 1.146 | OK |
| 2026-08-01 | 0.001387 | +2.3% | +15.0% | 14.2 | 51.3 | 0.00026 | 0.00005 | 0.00056 | 6 | 12.57 | PEAK(92%) | 1.5905 | 1.2753 | 1.6157 | 0.802 | 0.868 | 0.946 | OK |
| 2026-08-02 | 0.001387 | -0.0% | +26.2% | 8.1 | 46.9 | 0.00010 | 0.00005 | 0.00027 | 6 | 13.20 | PEAK(100%) | 1.2863 | 1.5981 | 1.9560 | 1.242 | 0.975 | 1.507 | OK |
| 2026-08-03 | 0.001260 | -9.2% | -7.1% | 4.8 | 47.3 | 0.00005 | 0.00005 | 0.00005 | 6 | 11.83 | PEAK(82%) | 1.3504 | 1.7367 | 2.0665 | 1.286 | 1.110 | 1.140 | OK |

OI range (30d store): min=5.64M  max=13.20M
px hard floor (hồ sơ): 0.00072 USDT

## T2 — INVALIDATE Composite (từng ngày 28/07→03/08)

Vế A: ret_3d ≥ 0 (biến thể 1) || ret_3d ≥ −2% (biến thể 2 — spec-gap)
Vế B: gLSR > 1.5 (ratio canonical)
INVALIDATE = A AND B cùng thỏa

**SPEC-GAP [A]: 'giá ngừng rơi' chưa có số cứng trong spec.** Probe chấm cả 2 biến thể.

**L-38 gLSR source check:**
- freshwatch export: dùng lsr_global_r → đây là nguồn CANONICAL
- Zone-A-agg: CHƯA có boundary note còn treo cho TAG (không cần flag đỏ)
- Hai nguồn không lệch dấu vs mốc 1.5 → PROCEED

| date | px | ret_3d | A(≥0) | A(≥-2%) | gLSR | B(>1.5) | INVALIDATE(v1) | INVALIDATE(v2) | note |
|------|----|--------|-------|---------|------|---------|---------------|---------------|------|
| 2026-07-28 | 0.001330 | +28.3% | ✓ | ✓ | 1.2978 | ✗ | — | — |  |
| 2026-07-29 | 0.001206 | +8.6% | ✓ | ✓ | 1.8129 | ✓ | **🔴 FIRE** | **🔴 FIRE** |  |
| 2026-07-30 | 0.001099 | -2.5% | ✗ | ✗ | 1.9958 | ✓ | — | — |  |
| 2026-07-31 | 0.001356 | +1.9% | ✓ | ✓ | 1.9223 | ✓ | **🔴 FIRE** | **🔴 FIRE** |  |
| 2026-08-01 | 0.001387 | +15.0% | ✓ | ✓ | 1.6157 | ✓ | **🔴 FIRE** | **🔴 FIRE** |  |
| 2026-08-02 | 0.001387 | +26.2% | ✓ | ✓ | 1.9560 | ✓ | **🔴 FIRE** | **🔴 FIRE** |  |
| 2026-08-03 | 0.001260 | -7.1% | ✗ | ✗ | 2.0665 | ✓ | — | — | gLSR>2.0! |

### T2 Verdict:

**INVALIDATE v1 (ret_3d≥0)**: ĐÃ BẮN — ngày đầu tiên = **2026-07-29**
  Tất cả ngày fire: 2026-07-29, 2026-07-31, 2026-08-01, 2026-08-02
**INVALIDATE v2 (ret_3d≥-2%)**: ĐÃ BẮN — ngày đầu tiên = **2026-07-29**
  Tất cả ngày fire: 2026-07-29, 2026-07-31, 2026-08-01, 2026-08-02

Khoảng cách hiện tại (03/08):
- Vế A (ret_3d): -7.1% — cần THỎA (-7.073%)
- Vế B (gLSR): 2.0665 — THỎA (>1.5)

## T3 — 3 Chốt Phụ

### T3① — Tái-ARM xa: gLSR ≤1.1 flush?

Điều kiện TRƯỚC tái-ARM: gLSR phải flush về ≤1.1 (crowd short bị rửa sạch)
- gLSR min kể từ 01/07: 0.6875 (2026-07-11) → FLUSH ≤1.1: ĐÃ QUA
- gLSR hiện tại 03/08: 2.0665 — crowd đang DẦY THÊM (>2.0)
- Kết luận: **CHƯA flush** — không có điều kiện tiên quyết tái-ARM

div_avg3 hiện tại (điều kiện thứ 2 tái-ARM):
- div_avg3 (03/08): 1.110
- <1.5: CHƯA THỎA (cần 0.39)

### T3② — Hard Floor px < 0.00072?

- Hard floor (hồ sơ): 0.00072 USDT
- px min kể từ 01/07: 0.000488 (2026-07-08) — BREACHED!
- px hiện tại (03/08): 0.001260 — TRÊN floor (+75.0%)
- Kết luận: **Floor CHƯA bị chạm** — não điều kiện invalidation này chưa fire

### T3③ — pos_r tại OI-floor (L-01): hồ sơ ref = 1.661

- OI floor (min30d, kể từ 01/07): 5.64M ngày 2026-07-09
- pos_r tại OI-floor: 1.4641
- Hồ sơ ref floor pos_r: 1.661 (từ session 30/07)
- pos_r hiện tại (03/08): 1.3504
- OI hiện tại (03/08): 11.83M → OI_cycle: PEAK(82%)

- **pos_r ĐÃ PHÁ FLOOR ref** (1.350 < 1.464) — bearish signal (L-01)
- **Định luật #9**: OI đang PEAK(82%) — gLSR >2.07 đọc kèm OI-PEAK = crowd LONG bị trap ở vùng OI cao

## T4 — Áp Khuôn Mới BANK/IDOL

### T4(a) — L-26: Crowd Flush Check + gLSR Direction

Crowd flush = pos_r drop ≥30% trong 3d (điều kiện tiên quyết mọi leg mới):

| window | pos_r start | pos_r end | flush% | PASS? |
|--------|------------|-----------|-------:|-------|
| 2026-07-31→2026-08-03 | 1.6811 | 1.3504 | -19.7% | ✗ FAIL (need -30%) |
| 2026-07-29→2026-08-01 | 1.6204 | 1.5905 | -1.8% | ✗ FAIL (need -30%) |
| 2026-08-01→2026-08-03 | 1.5905 | 1.3504 | -15.1% | ✗ FAIL (need -30%) |

gLSR direction 28/07→03/08:
- 28/07: gLSR=1.2978 → 03/08: gLSR=2.0665 (+59.2%)
- Chiều: TĂNG — crowd LONG dầy thêm (sai chiều)
- 30/07: gLSR=1.9958, 03/08: gLSR=2.0665 → PEAK và vẫn đang leo
- Crowd 1.61 (30/07) chưa được rửa — dầy lên gần 2.07 (03/08)
- **Kết luận**: CHƯA CÓ crowd_flush. Không có điều kiện cho leg mới theo khuôn BANK.

### T4(b) — Exit-Flag Scorecard Mini (5 cờ BIDWALK)

Lưu ý: TAG KHÔNG có ai giữ vị thế — chấm để luyện bộ cờ, không phải quyết định.

| cờ | điều kiện | ngày fire | kết quả |
|----|-----------|-----------|---------:|
| ① GHẾ RỜI | pos_r drop ≥25% từ rolling-peak-14d | 03/08 (-22.9%) | drop -22.9% vs peak 1.751 → ≥20%: ✓ / ≥25%: ✗ |
| ② gLSR→1.0 | gLSR đang giảm về 1.0 | CHƯA — gLSR=2.067 vẫn cao | ✗ gLSR 2.067 — ngược chiều (tăng) |
| ③ Funding burst | f_avg > 25bps hoặc >3× baseline | 01/08: f_avg=0.000255 | f_max_window=0.00026 → ✓ BURST 01/08 |
| ④ Suppressor | px drawdown từ local peak (§5) | px_peak=2026-08-01 0.001387 | drawdown -9.2% → CHƯA |
| ⑤ px+/OI− | px+, OI- cùng ngày | 31/07: px+23.4%/OI-2.9% | ✓ FIRE 31/07 |

Tổng kết cờ: ①{'✓' if co1_25 else '✗('+str(round(drop_pct,1))+'%)' if drop_pct else '✗'} ②✗ ③{'✓(01/08)' if co3 else '✗'} ④{('✓' if drawdown_from_peak and drawdown_from_peak<=-15 else '✗')} ⑤✓(31/07)

### T4(c) — Suppressor Scan §5

| date | px | vs_peak% | pos_r | OI_M | OI_pos | f_avg | tag |
|------|----|----------|------:|-----:|--------|------:|-----|
| 2026-07-27 | 0.001127 | -18.8% | 1.351 | 9.13 | MID(46%) | 0.00005 | SUPPRESSED |
| 2026-07-28 | 0.001330 | -4.1% | 1.595 | 12.19 | PEAK(87%) | 0.00018 | near-peak |
| 2026-07-29 | 0.001206 | -13.0% | 1.620 | 11.17 | PEAK(73%) | 0.00010 |  |
| 2026-07-30 | 0.001099 | -20.8% | 1.663 | 9.66 | MID(53%) | 0.00005 | SUPPRESSED |
| 2026-07-31 | 0.001356 | -2.3% | 1.681 | 9.38 | MID(49%) | 0.00016 | near-peak |
| 2026-08-01 | 0.001387 | +0.0% | 1.591 | 12.57 | PEAK(92%) | 0.00026 | near-peak |
| 2026-08-02 | 0.001387 | -0.0% | 1.286 | 13.20 | PEAK(100%) | 0.00010 | near-peak |
| 2026-08-03 | 0.001260 | -9.2% | 1.350 | 11.83 | PEAK(82%) | 0.00005 |  |

px peak (01/07+): 0.001387 (2026-08-01)
px 03/08: 0.001260 — -9.2% từ peak

## T5 — Unlock TAG Schedule

Trạng thái: **NO_DATA lần 2** — chưa có lịch unlock chính thức

Nguồn đã thử tìm (không có API access):
- Tokenomist.ai: cần web access
- CryptoRank: cần web access
- BscScan vesting contract: BscScan V1 deprecated, V2 requires paid plan
- Token docs dự án TAG: không có local data

Đã biết từ hồ sơ:
- 13-16/07: 7% supply rút từ 5 ví mới → đây CÓ THỂ là unlock event
- Circulating ~22.77B TAG (từ BscScan on-chain, nợ verify)
- Không có ngày unlock cụ thể đã xác nhận

Đề xuất operator:
- Tra TokenUnlocks.app hoặc CryptoRank cho TAG
- Nếu có cliff 17/month pattern → đối chiếu với 08/07 crash (-25%) và 13/07 7%-rút
- Nếu KHÔNG có lịch unlock → ghi NO_DATA_CONFIRMED vào UNLOCK sheet

## T6 — Verdict + Đề Xuất State

### Summary bảng T1 (nén):

| date | px | ret_3d | gLSR | pos_r | OI_M | OI_pos | key |
|------|----|--------|------|------:|-----:|--------|-----|
| 2026-07-28 | 0.001330 | +28.3% | 1.298 | 1.595 | 12.2 | PEAK(87%) | stealth_grind ban; gLSR sập 1.30 |
| 2026-07-29 | 0.001206 | +8.6% | 1.813 | 1.620 | 11.2 | PEAK(73%) | hồi pos_r; gLSR bật 1.81 |
| 2026-07-30 | 0.001099 | -2.5% | 1.996 | 1.663 | 9.7 | MID(53%) | px rơi -8.9%; gLSR đỉnh 2.00 |
| 2026-07-31 | 0.001356 | +1.9% | 1.922 | 1.681 | 9.4 | MID(49%) | px bật +23%; **INVALIDATE FIRE** (ret3d+2%+gLSR1.92) |
| 2026-08-01 | 0.001387 | +15.0% | 1.616 | 1.591 | 12.6 | PEAK(92%) | vol 15M, f_avg=25.5bps; gLSR=1.62; **FIRE tiếp** |
| 2026-08-02 | 0.001387 | +26.2% | 1.956 | 1.286 | 13.2 | PEAK(100%) | pos_r sập 1.29; gLSR 1.96; **FIRE tiếp** |
| 2026-08-03 | 0.001260 | -7.1% | 2.067 | 1.350 | 11.8 | PEAK(82%) | px rơi -9.2%; gLSR 2.07; ret3d=-7.1% → v1 STOP FIRE |

### Verdict T2:

🔴 **INVALIDATE v1 (ret_3d≥0) ĐÃ BẮN: 2026-07-29**
   Tiếp tục 01/08, 02/08. Ngưng 03/08 (ret_3d=-7.1%).
🔴 **INVALIDATE v2 (ret_3d≥-2%): 2026-07-29**
   Vẫn còn fire 03/08 (ret_3d=-7.1%, nếu ngưỡng -2% thì chưa thỏa).

### Đề xuất state operator ký:

**Option A — ĐÓNG ÁN INVALIDATE (nếu operator chọn ngưỡng ret_3d≥0):**
- Cơ sở: ngày 31/07 cả 2 vế thỏa (ret_3d=+2%, gLSR=1.92). Điều kiện hồ sơ 'gLSR quay lên >1.5 kèm giá dừng' = ĐÃ XẢY RA.
- Pending operator: verdict_check + on-chain cluster 6 ví (nếu redeposit → đóng ngay)

**Option B — WATCH-cooling (nếu operator yêu cầu xác nhận 2 ngày liên tiếp):**
- gLSR >1.5 kèm ret_3d≥0 đã có ngày 31/07 và 01/08 (2 ngày). Đủ điều kiện nếu spec cần 2d.
- 03/08: ret_3d=-7.1% → v1 STOP. State chuyển về WATCH-cooling chờ ngày tiếp theo.

**Chốt canh ngày 04/08:**
- Theo dõi gLSR: đang 2.067 (>1.5 liên tục từ 29/07). Cần gLSR giữ >1.5.
- Theo dõi px: 0.001260 (03/08). Nếu px hồi và ret_3d ≥0 → INVALIDATE v1 re-fire.
- pos_r: 1.3504 — đã dưới floor ref 1.661. Nếu tiếp tục giảm → crowd flush bắt đầu.
- f_avg: 01/08 = 25.5bps (cao). Nếu fund tiếp tục cao → tín hiệu đỉnh nóng (⑤ cờ funding).
- 17/08: mốc unlock tiếp (nếu khuôn tháng). Theo dõi OI và pos_r tuần 11-17/08.

**Ô PENDING operator:**
- Cluster 6 ví TAG: redeposit ví nào → đóng án ngay (CASE ghi)
- txhash $26M vs $17.9M double-count: verify (nợ cũ)
- Exchange balance TAG 7 ngày: Nansen screenshot (CẦN OPERATOR)
- Verdict CASE sheet: operator ghi (không phải agent)
# REVIEW LOG · Đóng vòng A5-A9 · U0-BELL & bàn 27/09

**KÝ**: 2026-09-18 · DEV ghi sổ theo AA0 · CHỜ ANALYSIS đóng chữ · KHÔNG WIRE.

## AA0-1 · Ba mục review từ vòng A5-A9

### 1. `acc-drop + pos-rise = mô tả chuyện thường ngày` — RÚT khỏi mọi vế

**Bằng chứng A9-3**:
- Tập A8 proven: 17/17 = **100%** chạm cả acc-drop (Δacc_bwd ≤ -20%) ∧ pos-rise (Δpos_bwd ≥ +10%) trong window 35d
- Random 50 mẫu universe: **83%** chạm cả hai
- Delta chỉ **17 pp**

**Kết luận**: hai mốc này là **chuyện thường ngày** trên token bất kỳ. **KHÔNG PHÂN BIỆT** proven khỏi random.

**Cùng bài LR-10**: "acc_r sập ≥ 50%/≤3d quanh ignition = xác nhận, không lead"
(per PATTERN_BOOK §21 · 7/7 hàng chấm ✓). Acc-drop cũng thuộc xác-nhận, không phân biệt.

**HÀNH ĐỘNG**: RÚT hai mốc này khỏi mọi vế/gate DEV đang xét. Không dùng làm chuông đơn hoặc gate compose. 

### 2. `U0-BELL phục vụ NHÁNH B` — không mở sang A/C/D

**Bằng chứng A9-2**:
- Trong 17 đợt A8: 5 đợt có div-cross (chuông pre-cross scope) · 2 đợt từng hedge rồi thoát · **10 đợt (59%) chưa hedge bao giờ**
- 10 đợt chưa-hedge = 龙虾×2, MITO×2, MARSCOIN×2, CYS×2, PROM×3
- Các token này thuộc loài A (BANK/TUT/CYS/PROM) · C (BTW) · D (龙虾/CAP) per PATTERN_BOOK §21

**Kết luận**: U0-BELL scope = nhánh B (hedge → unhedge). **5/17 đợt** = subset nhỏ. Cover ≈ 29% tập proven.

10 đợt chưa-hedge **thuộc A/C/D · chuông của chúng KHÔNG ở div-cross**:
- Loài A (BANK/CYS/PROM/TUT): H2b seat-lift · A1 pos-ramp · H1 kho-step · pin funding
- Loài C (BTW · AKE-đạp-rồi-gom): H1-OUT kho rút · dump→plateau→ignition
- Loài D (龙虾/CAP): kho-ramp · OI build 2-7 tuần

**HÀNH ĐỘNG**: **KHÔNG mở U0-BELL sang A/C/D** — sai hướng. Mỗi loài giữ chuông chuyên hình.

### 3. `Đợt 2+ CHƯA ĐO ĐƯỢC` — không kết luận

**Bằng chứng A9-1**:
- Sau gộp WL-EPISODE (gap < 14d = một đợt): 17 → 13 đợt · đợt 2+ n = **5** (không phải 9)
- Số này quá nhỏ để so tần suất pos-đi-trước với đợt 1

**Đo được (chỉ ghi, không diễn giải)**:
- Đợt 1 (n=8): pos-đi-trước 4/8 = 50%
- Đợt 2+ (n=5): pos-đi-trước 2/5 = 40%

**HÀNH ĐỘNG**: **KHÔNG ghi là bác bỏ** hypothesis "whale-trước-crowd-sau". CHƯA ĐO ĐƯỢC · chờ thêm đợt 2+ mới trong holdout hoặc tương lai.

---

## AA0-3 · Ba câu cho bàn 27/09 (đúng ba · không thêm)

1. **U0-BELL** = chuông nhánh B · T = −20% · `[CALIBRATION-ONLY]` · hold-out 21/10 quyết bật/tắt
2. **U1** = v2∧v1 (bỏ v3, v3 làm mô tả) · n_CONFIRMED = 5 (BTR, BULLA 08-30, UAI 07-07, SOPH 09-08, KOMA 07-31) · mở lại tune ngưỡng khi ≥10 CONFIRMED
3. **A/C/D đi kênh riêng** (H2b · A1 · H1-OUT · kho-ramp) · KHÔNG ép qua LSR-div-cross

## AA0-4 · Hold-out clause

- **Grid 8 ô đã đăng ký khoá** (`ops/holdout_changelog_20260920.md`): `{w=2, w=3} × {−10%, −15%, −20%, −30%}`
- **Không đụng gì tới 20/10**. Chạy grid ngày 21/10 sau khi holdout đóng.
- **Mọi thay đổi chạm `div_avg3` · `acc/pos source` · `universe` · `tagger`** phải ghi vào changelog kèm ngày + sha.

## AA0-5 · Trạng thái wire

- **U0-BELL: KHÔNG WIRE**. Sandbox `sandbox/u0_bell_a3/` giữ nguyên.
- Live production giữ nguyên: `scripts/species_tag.py` md5 `a9a134df7ec175cd50a7e2833ddccc4e` (chỉ có cross_today primitives từ AF4/AG1/AH1 · KHÔNG có u0_bell wired vào check_B).

## Files vòng A5-A9 (all sandbox)

```
sandbox/u0_bell_a3/
├── u0_bell.py                     A5-0 (bỏ cap Δpos)
├── a3_4_calib_v2v1.py             U1 v2∧v1 n=5
├── pin_p85_v2_no_pos_cap.py       4/4 PASS
├── pin_p86_lint_dknown.py         3/3 PASS
├── pin_p87_bulla_0830.py          2/2 PASS
├── pin_p88_holdout_header.py      5/5 PASS
├── a5_calibration_e2.py           E2 first pass · window dừng D0 (bug)
├── a6_calibration_extended.py     E2 extended · window mở qua D0+45
├── a6_investigate_5_ca.py         5 ca đích danh
├── a7_trinh_tu_dot2.py            đợt 1 vs 2+ acc-lead
├── a8_ba_chuyen_dong.py           bảng 4 cột 17 đợt (pre-merge)
├── a9_ba_cau.py                   ★ 3 câu · bằng chứng khép vòng
├── rename_u0_to_u0class_plan.md   A3-2
└── (probes trace/investigate)

docs/handover/
├── dev_a3_header_distinct_token_20260918.md
├── dev_review_log_a5_a9_close_20260918.md   ← this file
├── (ealier handovers: T1/T2/T3, ruling 12/09, universe 222, stale CSV, U1 tay)

ops/
└── holdout_changelog_20260920.md            ← baseline + grid 8 ô
```

## Chờ ANALYSIS

- (a) Ba câu 27/09 đúng chưa? Cần sửa gì?
- (b) A/C/D kênh riêng — DEV cần dựng probe riêng cho từng loài trước bàn 27/09 không?
- (c) Chấp thuận đóng vòng A5-A9 · giữ sandbox cho tới 21/10 grid?

Không có action DEV nào tới khi ANALYSIS đóng chữ.

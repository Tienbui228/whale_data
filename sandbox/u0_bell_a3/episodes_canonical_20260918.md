# SỔ ĐỢT · A5-A9 · CANONICAL 13 · PRE-MERGE 17

**KÝ**: 2026-09-18 · Áp luật WL-EPISODE (gap D0 < 14d = một đợt)

## Luật gộp đã áp

Cặp có gap D0 < 14 ngày → GỘP thành một đợt · giữ đợt gốc (earliest D0).

| pair | gap (ngày) | quyết định | đợt bỏ (redundant) |
|------|-----------:|------------|--------------------|
| 龙虾 D0 25/08 · leg 2 29/08 | 4 | **GỘP** | leg 2 29/08 |
| MITO đạp 28/08 · long 10-11/09 | 13 | **GỘP** | long 10-11/09 |
| MARSCOIN D0 03/09 · rebuild 07-10/09 | 5 | **GỘP** | rebuild 07-10/09 |
| CYS D0 04/08 · 13-15/08 | 10 | **GỘP** | 13-15/08 |
| BULLA sóng 1 · sóng 2 | 47 | giữ | — |
| HEMI wave-1 · D0 15/08 | 26 | giữ | — |
| UAI pump#1 · push 24/08 | 48 | giữ | — |
| PROM sóng 1 · sóng 2 | 17 | giữ | — |
| PROM sóng 2 · sóng 3 | 20 | giữ | — |

## CANONICAL 13 đợt

Bản gộp (13 đợt) = **canonical** cho mọi phân tích sau A9.

```
#   token       ep_label         D0            đợt đợt-1-hay-2+
1   BULLA       sóng 1           2026-07-20    đợt 1
2   BULLA       sóng 2           2026-09-05    đợt 2+
3   HEMI        wave-1 20/07     2026-07-20    đợt 1
4   HEMI        D0 15/08         2026-08-15    đợt 2+
5   UAI         pump#1           2026-07-07    đợt 1
6   UAI         push 24/08       2026-08-24    đợt 2+
7   龙虾         D0 25/08         2026-08-25    đợt 1 (leg 2 gộp)
8   MITO        đạp 28/08        2026-08-28    đợt 1 (long gộp)
9   MARSCOIN    D0 03/09         2026-09-03    đợt 1 (rebuild gộp)
10  CYS         D0 04/08         2026-08-04    đợt 1 (13-15 gộp)
11  PROM        sóng 1           2026-07-19    đợt 1
12  PROM        sóng 2           2026-08-05    đợt 2+
13  PROM        sóng 3           2026-08-25    đợt 2+
```

## PRE-MERGE 17 đợt (đánh dấu · KHÔNG dùng làm nguồn)

Bản gốc (17 đợt trước gộp) = `sandbox/u0_bell_a3/a8_ba_chuyen_dong.py` output.
**Marked `[PRE-MERGE]`** · GIỮ để so đối chiếu · KHÔNG DÙNG làm số cho phân tích mới.

Bốn đợt trong 17 pre-merge đã bị gộp (redundant):
- 龙虾 leg 2 29/08 · giống 龙虾 D0 25/08
- MITO long 10-11/09 · giống MITO đạp 28/08
- MARSCOIN rebuild 07-10/09 · giống MARSCOIN D0 03/09
- CYS 13-15/08 · giống CYS D0 04/08

## Thống kê canonical

- **Đợt 1**: n = 8 (BULLA×1, HEMI×1, UAI×1, 龙虾×1, MITO×1, MARSCOIN×1, CYS×1, PROM×1)
- **Đợt 2+**: n = 5 (BULLA sóng 2, HEMI D0 15/08, UAI push, PROM sóng 2 + sóng 3)

Thứ tự (per A9-1):
- Đợt 1 · pos đi trước 4/8 = 50%
- Đợt 2+ · pos đi trước 2/5 = 40%

## Reference

- Luật WL-EPISODE gap ≥14d đăng ký trước A9-1
- A8 code: `sandbox/u0_bell_a3/a8_ba_chuyen_dong.py`
- A9 code: `sandbox/u0_bell_a3/a9_ba_cau.py`
- Review log: `docs/handover/dev_review_log_a5_a9_close_20260918.md`

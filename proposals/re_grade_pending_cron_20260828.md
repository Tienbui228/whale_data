# Re-grade PENDING cron — DEPLOY PLAN [CHỜ KÝ]

**Status:** DRAFT · CHỜ operator KÝ · TRÌNH sau A4 ingest census_63_grades_20260828.csv (md5 `dd57b42b`).
**Purpose:** tự động re-grade PENDING rows khi age_days ≥30 tại data_through mới.

## §5 luật (recap)

> PENDING hết hạn: tự động khi fire đủ 30d tuổi → re-grade ở lần census kế; mỗi grade ghi `graded_at + data_through`.

## Current PENDING inventory (22 rows)

Từ `docs/case_files/census_63_grades/census_63_grades_20260828.csv`:

| token | date | data_through hiện | mature date (D+30) |
|:--|:--|:--|:--|
| BREV | 08-04 | 08-26 | **2026-09-03** |
| BREV | 08-05 | 08-26 | 2026-09-04 |
| GENIUS | 08-10 | 08-26 | 2026-09-09 |
| GENIUS | 08-18 | 08-26 | 2026-09-17 |
| GENIUS | 08-19 | 08-26 | 2026-09-18 |
| GENIUS | 08-20 | 08-26 | 2026-09-19 |
| GENIUS | 08-21 | 08-26 | 2026-09-20 |
| HUMA | 08-06 | 08-26 | 2026-09-05 |
| HUMA | 08-07 | 08-26 | 2026-09-06 |
| HUMA | 08-08 | 08-26 | 2026-09-07 |
| OPG | 08-06 | 08-26 | 2026-09-05 |
| OPG | 08-08 | 08-26 | 2026-09-07 |
| OPG | 08-09 | 08-26 | 2026-09-08 |
| OPG | 08-10 | 08-26 | 2026-09-09 |
| OPG | 08-11 | 08-26 | 2026-09-10 |
| OPG | 08-12 | 08-26 | 2026-09-11 |
| OPG | 08-15 | 08-26 | 2026-09-14 |
| ROBO | 07-30 | 08-26 | **2026-08-29** ← sắp mature |
| SAHARA | 08-10 | 08-26 | 2026-09-09 |
| SAHARA | 08-11 | 08-26 | 2026-09-10 |
| SAHARA | 08-12 | 08-26 | 2026-09-11 |
| SAHARA | 08-13 | 08-26 | 2026-09-12 |

**Earliest mature:** ROBO 07-30 → 2026-08-29 (3 ngày nữa)
**Latest mature:** GENIUS 08-21 → 2026-09-20

## Cron deploy plan (5 dòng, per operator C1 convention)

```
GIỜ    : 06 04 * * *  (04:06 UTC daily; sau daily-metrics 00:35 + spot 01:05 + gom_h 01:45)
INPUT  : docs/case_files/census_63_grades/census_63_grades_<latest>.csv
         + scratch/census_ret_63_<latest>.csv (re-fetch fapi k[4] fresh nếu >48h)
OUTPUT : docs/case_files/census_63_grades/census_63_grades_<today>.csv (append-only)
GUARD  : go-live ≠ verify: dry-run mode default → in ra "SẼ re-grade N rows" không ghi
         file; --live flag mới ghi (operator gõ tay sau verify)
ROLLBACK: giữ 30d bản grades cũ trong docs/case_files/census_63_grades/*.csv;
         re-grade sai → operator xóa bản mới, không cần undo (append-only)
```

## Semantic re-grade rule

```
For each PENDING row where fire_age (today − date) ≥ 30:
    Fetch fapi k[4] fresh close D0..D+30
    If any close[i] / close[D0] ≥ 1.50 (i.e. +50% per §5) → grade = TP
    Elif close D+30 exists AND all closes < +50% threshold → grade = FP
    Elif no close data D+30 → grade = NOT-EVALUABLE (data still MISSING)
    basis: "re-graded from PENDING · ret_max=X% @D+N, window=31d, threshold=+50%"
    graded_at = today (YYYY-MM-DD)
    data_through = min(today, D+30)
Write new census_63_grades_<today>.csv với PENDING rows đã re-grade + rows khác giữ nguyên.
```

## Script draft path

`scripts/regrade_pending_census.py` (CHƯA VIẾT — chờ ký merge)

Skeleton:
```python
def regrade_pending(input_csv, ret_csv, today, live=False):
    grades = read_csv(input_csv)
    ret = read_csv(ret_csv)  # census_ret_63 nếu fresh
    todo = [r for r in grades if r['grade']=='PENDING' and age(r['date'], today) >= 30]
    for r in todo:
        max_ret = ret.get((r['token'], r['date']), {}).get('ret_max')
        if max_ret is None: r['grade'] = 'NOT-EVALUABLE'; r['basis'] = 're-grade fail: no ret data'
        elif max_ret >= 0.50: r['grade'] = 'TP'; r['basis'] = f're-graded · ret_max={max_ret:.1%}'
        else: r['grade'] = 'FP'; r['basis'] = f're-graded · ret_max={max_ret:.1%} <+50%'
        r['graded_at'] = today; r['data_through'] = min(today, r['date']+30d)
    if live: write_csv(f'census_63_grades_{today}.csv', grades)
    else: print(f'DRY-RUN: SẼ re-grade {len(todo)} rows')
```

## Sign-off checklist

- [ ] Operator KÝ deploy plan (cron GIỜ + guard mode)
- [ ] DEV viết `scripts/regrade_pending_census.py` per skeleton
- [ ] Smoke test dry-run trên bản hiện tại: expected "SẼ re-grade 0" (chưa có PENDING nào mature)
- [ ] 2026-08-29 (ROBO mature): live re-grade lần đầu, operator verify
- [ ] Cron install trên VPS (crontab -e append)

## Refs
- §5 census TP/FP luật chấm (gate_defs md5 hiện `c369905251`, chờ `824bdcb6` supersede)
- Grades store: `docs/case_files/census_63_grades/census_63_grades_20260828.csv` md5 `dd57b42b`
- Ret table source: `scratch/census_ret_63_20260828.csv` md5 `300a1230`

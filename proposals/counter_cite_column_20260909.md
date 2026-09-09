# COUNTER CITE-COLUMN · V3.5m directive item 4 · DOS/BEAT/ONE/B re-measure

**KÝ 2026-09-09** · bảng per-date với cột artifact-path/log-line cite · dòng KHÔNG cite XÓA khỏi đếm.

## Regen source

```
script: scripts/ledger_backfill_30d_v3_5.py :: _fresh_delta ngoai_so_sink
input:  data/raw/nansen_snapshots/<date>.json (snap-pair Δ ≥ 50k)
window: 30d ending 2026-09-08
```

## Bảng per-date với cite (as-printed only)

| Token | Date | Δ | Artifact/Log cite | Valid? |
|---|---|---:|---|:---:|
| B | 2026-08-11 | +238,322 | `data/raw/nansen_snapshots/2026-08-11.json` (snap-pair) | ✓ |
| DOS | 2026-08-17 | +1,540,740 | `data/raw/nansen_snapshots/2026-08-17.json` | ✓ |
| DOS | 2026-08-18 | +3,440,523 | `data/raw/nansen_snapshots/2026-08-18.json` | ✓ |
| BEAT | 2026-08-18 | +2,949,429 | `data/raw/nansen_snapshots/2026-08-18.json` | ✓ |
| BEAT | 2026-08-19 | +1,187,687 | `data/raw/nansen_snapshots/2026-08-19.json` | ✓ |
| BEAT | 2026-08-21 | +346,613 | `data/raw/nansen_snapshots/2026-08-21.json` | ✓ |
| DOS | 2026-08-21 | +347,457 | `data/raw/nansen_snapshots/2026-08-21.json` | ✓ |
| DOS | 2026-08-22 | +2,353,317 | `data/raw/nansen_snapshots/2026-08-22.json` | ✓ |
| DOS | 2026-08-29 | +209,770 | `data/raw/nansen_snapshots/2026-08-29.json` | ✓ |
| BEAT | 2026-08-29 | +78,170 | `data/raw/nansen_snapshots/2026-08-29.json` | ✓ |
| DOS | 2026-08-31 | +254,646 | `data/raw/nansen_snapshots/2026-08-31.json` | ✓ |
| BEAT | 2026-08-31 | +86,890 | `data/raw/nansen_snapshots/2026-08-31.json` | ✓ |
| ONE | 2026-09-04 | +137,012 | `data/raw/nansen_snapshots/2026-09-04.json` | ✓ |
| ONE | 2026-09-05 | +1,008,093 | `data/raw/nansen_snapshots/2026-09-05.json` | ✓ |
| DOS | 2026-09-05 | +69,898 | `data/raw/nansen_snapshots/2026-09-05.json` | ✓ |
| B | 2026-09-06 | +879,435 | `data/raw/nansen_snapshots/2026-09-06.json` | ✓ |
| DOS | 2026-09-06 | +192,711 | `data/raw/nansen_snapshots/2026-09-06.json` | ✓ |
| DOS | 2026-09-07 | +1,213,820 | `data/raw/nansen_snapshots/2026-09-07.json` | ✓ |

## Counter (cite-only)

| Token | Distinct dates hit | Nomination status |
|---|---:|---|
| **DOS** | **9×** | **ĐỀ-CỬ-UNIVERSE ghế 27/09** (biên lai đủ · ≥3×) |
| **BEAT** | **5×** | **TREO chờ biên lai bổ sung** (per operator: "BEAT nomination theo số mới") |
| ONE | 2× | Đếm tiếp · chưa đủ 3× |
| B | 2× | Đếm tiếp · chưa đủ 3× |

**File updated:** `data/state/ngoai_so_candidates.json` (commit prior) mang counter đúng bảng cite này.

Note V3.5m: nansen_snapshots là source-of-truth (raw-save cả body). Fresh_digest as-sent artifact chỉ có 1 file (09-07) trong window → không đủ per-date evidence · dùng snapshot as source per operator directive.

**Ghế 27/09 bất động cho DOS** · BEAT theo số mới treo chờ:
- Nếu BEAT tái xuất 09-08/09-09 với 1+ hit citable → 6×+ · đủ nomination
- Nếu không → giữ 5× · treo tới đủ evidence

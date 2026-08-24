# L-58 amendment RE-PIN-20260824

**Operator ký chat 24/08 (α).**

## Bối cảnh

Pin cũ ở `C:\Users\Hello\AppData\Local\Temp\e_r7_20260819\freshwatch_daily_2026-{06,07,08}.csv`
chết do Windows Temp cleanup 24/08 (chiều). Snapshot vật lý MẤT, không tái tạo được:

- Fixture pin md5 (07): `e7e9fc1fc86095a64e57ede3b0a02c9c`
- Current data/export md5 (07): `4179ddbf1486fd22b133096248571cea`
- `.bak_pre_F5e_20260824` backup (07): `c7143e37bf98cc11bf171068a2518857`

Đã thử: truncate current ≤ 08-19 (với/không trailing NL), git blob F5a-VOL-REBUILD
(68c824d), backup pre-F5e — không md5 nào khớp pin.

VALUE-stability historical: L-58 fixture PASS 5/5 ba lần cuối 24/08 sáng (before Temp cleanup).
Vấn đề là snapshot vật lý, không phải logic.

## Amendment (1 dòng doctrine bổ sung)

> **L-58 điều kiện cứng bổ sung (24/08):** `DATA_DIR` fixture PHẢI nằm trong git
> (`tests/fixtures/data_snapshot_*/`). CẤM pin path ngoài git — Temp/, ổ ngoài, share
> network — vì Temp cleanup / rotate / permission drift sẽ giết pin không phục hồi được.

## Guard code-level

`tests/test_conformance.py` line ~44 assert `DATA_DIR.is_relative_to(REPO)` — chạy
ngay khi import module, fail loud nếu ai đó set `DATA_DIR = Path(r"C:\...")` trong tương lai.

## Migration

Snapshot mới: `tests/fixtures/data_snapshot_20260824/freshwatch_daily_2026-{06,07,08}.csv`
- copy từ `data/export/` hiện hành (post-F5a, post-guard)
- window ≤ 2026-08-23 (mở rộng 4 ngày so cũ 08-19)
- md5:
  - 06: `5cb3761efb62ede28a7deb84b4958145` (bất biến — không có row mới)
  - 07: `4179ddbf1486fd22b133096248571cea`
  - 08: `1f3023e7239611f2ed1fb56b4c09494b`

Fixture json `registry_conformance_20260821.json` cập nhật:
- `snapshot_date`: 2026-08-19 → 2026-08-23
- `window_end`: 2026-08-19 → 2026-08-23
- `data_snapshot_md5`: 3 md5 mới (in-tree)
- Golden values `episodes/registry_events/watchlist_daily` regen từ snapshot mới

## Deep-diff VALUE-stability (điều kiện ii)

Chạy `_probe_re_pin_deepdiff_20260824.py` — so old golden vs new snapshot:

- (v1) F5a vol_quote rebuild: **0 drift** (đã proved tại F5e commit e1c9028)
- (v2) rows 08-20..23 extended range: **48 drift** (end_date/count_le050/ep_len tăng, sn tăng, new episodes/events sau 08-19, watchlist +4 rows/token × 7 tokens = 28 rows)
- **OTHER (unexplained): 0**

Mọi drift giải thích được bằng đúng 2 nguồn đã biết → an toàn re-pin.

## Sync CASE_INDEX

Chờ operator update sheet LESSONS L-58 với amendment text, regen `docs/lessons_learned.md`.

## Signed

Operator chat 24/08 — 3 điều kiện (i)(ii)(iii) đầy đủ.

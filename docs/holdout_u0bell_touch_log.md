# HOLD-OUT U0-BELL · touch log · sổ "đã nhìn"

**Cửa sổ:** 2026-09-20 → 2026-10-20 (30 ngày · A3.2 registration)
**Registration date:** 2026-09-23 (R1 pending · ANALYSIS chuyển chữ 1-4)
**Quy ước:** một dòng cho MỖI quyết định chạm U0-BELL / events_build / collector acc/pos/div.
Không ghi việc đọc/ báo. Không ghi việc snapshot ops/ (đó là R0).

## Cột

| date_utc | who | change | dùng dữ liệu ≥20/09 | md5_trước | md5_sau | git_sha | file | dòng chú |
|----------|-----|--------|:---:|-----------|----------|---------|------|----------|

## Entries (thời gian tăng dần · chỉ ghi actual code touches)

| date_utc | who | change | dùng≥20/09 | md5_trước | md5_sau | git_sha | file | dòng |
|----------|-----|--------|:---:|-----------|----------|---------|------|------|
| 2026-09-21T08:06:XXZ | agent | AH5 · remove `lead=` field | no | (pre-AH5) | 2ab17d49ef1d | (pre-doctrine) | scripts/u0_bell_audit.py | AH5 chỉnh trước hold-out doctrine · logged retro |
| 2026-09-21T13:51:XXZ | agent | AO1 · L1 threshold -30/5 → -15/10 | no | (pre-AO1) | b422d88e8898 | (pre-doctrine) | scripts/b_state_tracker.py | AO1 chỉnh trước hold-out doctrine · logged retro |
| 2026-09-22T05:35:XXZ | agent | AW-α' α1 · extract classify_tier to lib/u0_class_tier.py | no | (pre-α1) | 2a6ab5a578e9 · 08bbbbd08c86 | 6f92e50 | scripts/events_build.py + scripts/lib/u0_class_tier.py | Refactor · KHÔNG đổi số học · lib mới có ngưỡng ký -15/10 |
| 2026-09-22T05:36:XXZ | agent | Regen data/artifacts/events_2026-09-20.jsonl (new schema L2/L3) | **yes** | (legacy L2_OR_L3) | ae150ca18688 | 6f92e50 | data/artifacts/events_2026-09-20.jsonl | Rewrite output artifact (claim deterministic PENDING · cần diff regen×2 để chứng minh · S3 diff legacy vs artifacts=2 nhưng đó là hai pipeline khác nhau, không phải regen determinism) |
| 2026-09-23T00:57:XXZ | agent | R0 snapshot (copy files vào ops/holdout_u0bell_20260920/) | **yes** (view-only) | n/a | n/a | 6af9359498a7 | ops/holdout_u0bell_20260920/ | Chỉ COPY · KHÔNG mutate source · doctrine #11 xem-không-để-dấu OK |

## Rule

- **KHÔNG** ghi việc đọc log/verdict/dry-run (đó là view-only).
- **CÓ** ghi việc: sửa code U0, sửa events_build, sửa collector acc/pos/div, regen file trong ops/ hoặc data/artifacts/events_*.jsonl, mutate state gom_e / bell_journal / verdict_epoch.
- Cột "dùng≥20/09": có sử dụng dữ liệu ngày ≥ 20/09 để tính/quyết định không? Snapshot = view-only nên ghi "yes (view-only)".
- Cột "md5_trước / md5_sau": lấy md5 của file trước/sau touch. Nếu tạo mới, md5_trước = n/a.

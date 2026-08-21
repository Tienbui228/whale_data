---
type: yaml-change-proposal
date: 2026-08-21
target: data/config/watchlist_thresholds.yaml
scope: rename semantic-only (không đổi value, không đổi hành vi runtime)
signed_by: PENDING operator
---

# yaml_change 21/08/2026 — rename `struct_n_min` → `sn_count_min`

## Rationale

Sau conformance-pack 21/08 merge (`fe4e38c`) + A2 gate switch (`72e36b1`):
- Watchlist List A gate hiện dùng `sn_count_le050` = count(div_avg3 ≤ 0.5) — canonical
- Key config `struct_n_min` bị lệch tên: tên gợi "struct_n" (= ep_len legacy incl gap-days) nhưng semantics áp lên `sn_count_le050`
- Operator A4(1) 21/08: "nếu watchlist gate → đổi tên key, khai rõ"

## Change

```yaml
hedge:
  div_ratio_max: 0.5
- struct_n_min: 5             # LEGACY tên, semantics đã lệch
+ sn_count_min: 5             # canonical: count(div_avg3 ≤ 0.5) in episode ≥ này → vào List A
  gap_tolerance_days: 2
  episode_break_days: 3
```

## Compatibility

Code path `scripts/watchlist_daily.py::in_list_a` đã update (commit A4(1)):
- Prefer `hedge.sn_count_min` (canonical)
- Fallback `hedge.struct_n_min` (backward-compat khi yaml chưa apply rename)

Nghĩa là:
- **Trước apply yaml:** watchlist đọc `struct_n_min: 5` — hoạt động như hiện tại
- **Sau apply yaml:** watchlist đọc `sn_count_min: 5` — cùng behavior, tên đúng semantics
- **Value KHÔNG đổi** — không có behavior diff → không rescan CORRECTIONS lớp-2

## Apply steps (operator ký + apply)

```bash
# 1. Edit yaml (rename key, value 5 giữ)
vim data/config/watchlist_thresholds.yaml

# 2. SCP VPS
scp data/config/watchlist_thresholds.yaml root@5.223.67.21:/root/Data_back_test/whale_data/data/config/

# 3. Verify cron 01:40 UTC ngày kế đọc yaml mới (log expect: sn_count_min gate applied)
```

## Cross-ref

- `proposals/unhedge_registry_spec_v1.0.md` §E-R1 conformance-pack — canonical struct_n vs sn_count_le050
- `proposals/hedge_watchlist_spec.md` §3 — consumer split
- commit `72e36b1` A2 — code path gate switch
- fixture `tests/fixtures/registry_conformance_20260821.json` — pin config keys canonical names

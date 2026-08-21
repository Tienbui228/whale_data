---
type: migration-proposal
name: D1 rename struct_n → ep_len (deprecate-then-remove)
version: draft-1 (21/08/2026)
status: **DRAFT — CHƯA APPLY, chờ operator ký**
signed_by: PENDING operator
related_commits: d20bd8a (A1 field add) · 72e36b1 (A2 watchlist gate switch) · b6a44b7 (A4(2) cases I-L) · 2193f9d (A4(4) golden fixture)
---

# D1 — Migration path: deprecate `struct_n` → canonical `ep_len` (không alias)

## Rationale (per operator ER-HOME 21/08 D1 directive)

Sau §E-R1 conformance-pack (`fe4e38c`) + A1/A2 (`d20bd8a`/`72e36b1`):
- `struct_n` (semantics ep_len = i-ep_start+1 while in_hedge, incl gap-days) là **tên legacy**
- `ep_len` là **canonical tên mới** (cùng semantics)
- Hiện tại `struct_n` STILL EXIST khắp code với alias `ep_len = sn` → hai tên, một số

Operator D1: **"rename struct_n → ep_len trong lib, grep toàn repo, KHÔNG ALIAS"** — nghĩa là:
- Xóa `struct_n` field khỏi mọi output dict (lib episodes, watchlist snap, CSV, JSON)
- Chỉ giữ `ep_len` (canonical) + `sn_count_le050` (canonical §E-R1)

## Blast radius (grep-based, ĐO trước khi ký)

Consumer path đọc `struct_n`:
- `scripts/watchlist_daily.py` — inline detect_episodes + snapshot + in_list_a fallback + CSV header + row + print (11 chỗ, verified L37/L122/L129-132/L168/L224/L244/L296/L493/L544/L565)
- `lib/hedge_episode.py` — detect_episodes output field (L104-106)
- `lib/registry_events.py` — `_detect_ev` (a) fallback `ep[i-1].get("sn_count_le050", ep[i-1]["struct_n"])`, `_detect_episodes_registry` output field (L194, L333, L369)
- `data/state/hedge_watchlist_2026-08-{16,17,18}.json` — snapshot JSON có field struct_n
- `data/export/watchlist_log_2026-08.csv` — cột 8 struct_n + cột 9 sn_count_le050 (mới thêm A2 migrate)
- `data/export/watchlist_corrections_2026-08.csv` — có col struct_n?
- Registry backfill CSVs — có col struct_n?
- CASE_INDEX.xlsx / CASE_*.xlsx sheet DAILY — có col struct_n?

Downstream consumer (mà đọc watchlist CSV/JSON output — nếu có):
- Reporting tools (analyzer scripts, notebook, external readers)
- CASE_INDEX apply script (append DAILY từ watchlist_log — cần check)
- Any manual reader (dashboard, spot-check)

## Migration path — 3 phase deprecate-then-remove

### Phase 1 — DEPRECATE (ký + apply immediate)

**Goal:** Add deprecation warning + doc note. Không xóa gì. Alias `ep_len` = `struct_n` giữ (backward-compat).

Actions:
1. `lib/hedge_episode.py::detect_episodes`: docstring note deprecation.
   ```python
   struct_n        # DEPRECATED alias for ep_len — will be removed in Phase 3 (target 2026-09-30). Use ep_len canonical.
   ```
2. `lib/registry_events.py::_detect_episodes_registry`: same docstring note.
3. `scripts/watchlist_daily.py`: same docstring note.
4. `proposals/unhedge_registry_spec.md` §E-R1: add "**DEPRECATION NOTE Phase 1:** struct_n deprecated tên, canonical `ep_len` + `sn_count_le050`. struct_n legacy alias sẽ bị xóa Phase 3 (target 2026-09-30)."
5. Commit: `[D1-PHASE1-<date>] deprecate struct_n alias (docstring + spec note only)`.

**Gate:** L-58 conformance fixture PASS (5/5 unchanged — Phase 1 chỉ thêm text, không đổi field).

### Phase 2 — DUAL-WRITE + CONSUMER MIGRATION (ký, apply theo checklist)

**Goal:** Đồng thời write cả `struct_n` (legacy) + `ep_len` (canonical) trong mọi output. Consumer chuyển đọc `ep_len` một cách tuần tự.

Actions:
1. Watchlist inline detect_episodes: keep both `struct_n` + `ep_len` (đã có, không đổi).
2. Watchlist CSV/JSON output: keep both cols (đã có sau A2 migrate).
3. Consumer migration checklist (từng chỗ đọc, đổi sang `ep_len`):
   - [ ] `scripts/watchlist_daily.py::in_list_a`: đọc `s['ep_len']` thay `s['struct_n']` (semantics = ep_len, không cần đổi số). GIỮ fallback `sn_count_le050` gate switch A2.
   - [ ] `scripts/watchlist_daily.py` print rows L296/L493: đổi label header `sn` → `ep_l` explicit.
   - [ ] Registry probes (_probe_registry_backfill_*.py): đọc `ep_len` thay `struct_n` (nếu có).
   - [ ] Downstream tools (external reader): verify KHÔNG dùng field struct_n; nếu có, notify consumer + đổi.
   - [ ] CASE_INDEX apply script (append DAILY): đổi col name (nếu có struct_n col).
   - [ ] Historical CSVs (data/export/watchlist_log_2026-*.csv): migrate script rename col struct_n → ep_len (KHÔNG xóa data, chỉ rename header).
4. Yaml key: `data/config/watchlist_thresholds.yaml` rename `struct_n_min` → `sn_count_min` (per proposals/yaml_change_20260821.md — chờ operator apply riêng).
5. Commit: `[D1-PHASE2-<date>] dual-write struct_n + ep_len; consumer migration ...`.

**Gate:** L-58 fixture PASS. Cron watchlist 01:40 UTC ngày kế verify CSV có cả 2 cols, cron output khớp legacy.

### Phase 3 — REMOVE (ký, apply cuối, cutover date)

**Goal:** Xóa `struct_n` field khỏi mọi output. Không alias. Canonical `ep_len` only.

Actions:
1. Bump L-58 fixture: regenerate golden với semantics MỚI (chỉ có `ep_len`, `sn_count_le050`).
2. `lib/hedge_episode.py::detect_episodes`: XÓA `"struct_n": sn` khỏi output dict. Giữ `"ep_len": sn` + `"sn_count_le050": sn_count`.
3. `lib/registry_events.py`: same.
4. `scripts/watchlist_daily.py`:
   - XÓA `"struct_n"` khỏi inline detect_episodes output + snap + CSV header + row + print header
   - Nếu bit-equal check pass với ep_len rename (should = same value), commit.
5. Migrate historical CSVs: cột `struct_n` → rename `ep_len` (script + backup).
6. Migrate historical JSONs: same.
7. Watchlist ONLY: verify VPS cron 01:40 chạy đúng post-cutover.
8. Registry probes/tests: 100% dùng `ep_len` + `sn_count_le050`.
9. Commit: `[D1-PHASE3-<date>] remove struct_n alias — canonical ep_len only. Cutover.`.

**Gate:** 
- L-58 fixture regen + PASS trên semantics mới.
- P0 check watchlist bit-equal (verify chỉ đổi TÊN, không đổi VALUE).
- Cron VPS 01:40 UTC ngày kế: CSV không còn col struct_n, chỉ ep_len + sn_count_le050.
- Downstream tools verify (report script, dashboard) — 0 KeyError('struct_n').

**Timeline:**
- Phase 1: 21/08 (ngay sau operator ký) — 1 commit, ~1h
- Phase 2: 22-25/08 (theo consumer migration checklist) — ~3-5 commits
- Phase 3: cutover 2026-09-30 (target — chờ operator ký date)

## Risk assessment

- **Phase 1 low**: chỉ text note. Không đổi hành vi.
- **Phase 2 medium**: dual-write mới, consumer migration. Cron test verify.
- **Phase 3 high**: cutover, downstream reader có thể vỡ nếu miss consumer. Cần L-58 fixture PASS + P0 SAFE bit-equal check + cron VPS verify.

## Fallback rollback plan

Nếu Phase 3 cutover VỠ:
- Revert commit → alias struct_n restore.
- Fix consumer, re-apply.

Historical CSVs migration KHÔNG destructive (dùng backup + rename header, không xóa data).

## Decision needed từ operator

- [ ] Ký Phase 1 apply immediate (docstring + spec note)?
- [ ] Ký Phase 2 dual-write + consumer migration timeline (22-25/08)?
- [ ] Ký Phase 3 cutover target date (2026-09-30 hoặc khác)?
- [ ] Ký yaml_change_20260821.md apply cùng Phase 2?
- [ ] Ký downstream reader audit (identify external tools reading struct_n) trước Phase 3?

## Cross-ref

- Operator directive: ER-HOME Option 2 ký 21/08 (D1 mục "rename struct_n→ep_len trong lib, không alias")
- Spec canonical: `D:/Data back test/whale_data/proposals/unhedge_registry_spec.md` §E-R1 conformance
- L-58: fixture-first migration (mỗi phase cần fixture PASS)
- Related proposals: `proposals/yaml_change_20260821.md` (yaml key rename cùng scope)
- Sha history: d20bd8a (A1) · 72e36b1 (A2) · b6a44b7 (A4 I-L) · 2193f9d (A4 fixture golden) · 401366e (D4 header)

---
type: migration-proposal
name: D1 rename struct_n → ep_len + sn_count_le050 (HƯU struct_n hoàn toàn)
version: SIGNED (b)+3-sửa 21/08/2026
status: **SIGNED** — operator ký chat 21/08 · Phase 1 KÝ · Phase 2 22-25/08 KÝ (yaml struct_n_min→sn_count_min cùng đợt) · Phase 3 cutover 2026-09-30 KÝ · downstream audit trong Phase 2 KÝ
signed_by: operator (chat 21/08)
related_commits: d20bd8a (A1 field add) · 72e36b1 (A2 watchlist gate switch) · b6a44b7 (A4(2) cases I-L) · 2193f9d (A4(4) golden fixture) · 401366e (D4 header) · 48daf42 (D1 draft superseded)
---

# D1 — Migration path: HƯU `struct_n` hoàn toàn → canonical `ep_len` + `sn_count_le050`

## Ánh xạ tên (per operator M1(b) 21/08)

**`struct_n` trong doctrine/lessons/pre-commit (vd 'struct_n=3', baseline 25.9%, L-53)
≡ field `sn_count_le050`. Không có field nào tên struct_n sau Phase 3.**

- Text doctrine/lessons dùng "struct_n" = ngữ nghĩa canonical `count(div_avg3 ≤ 0.5)` = field code `sn_count_le050`.
- Field code cũ `struct_n` (semantics ep_len = i-ep_start+1 while in_hedge, incl gap-days) → rename `ep_len`.
- Sau Phase 3: KHÔNG có field nào tên `struct_n` trong code/output. Doctrine text vẫn dùng chữ "struct_n" là legitimate — semantic ≡ `sn_count_le050`.

## Rationale (operator M1(b) 21/08)

Sau §E-R1 conformance-pack (`fe4e38c`) + A1/A2 (`d20bd8a`/`72e36b1`):
- `struct_n` (field code cũ = ep_len semantics) là **tên legacy field**
- `ep_len` là **canonical tên field mới** (cùng semantics ep_len legacy)
- `sn_count_le050` là **canonical tên field mới** cho count(div≤0.5) — TƯƠNG ĐƯƠNG "struct_n" trong doctrine text
- Hiện tại `struct_n` STILL EXIST khắp code với alias `ep_len = sn` → hai tên, một số

Operator (b): **HƯU `struct_n` hoàn toàn. Canonical = `ep_len` + `sn_count_le050`. Không có field nào tên struct_n sau Phase 3.**

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
4. `proposals/unhedge_registry_spec.md` §E-R1: add **DEPRECATION NOTE Phase 1** + dòng ánh xạ (M1b).
5. Commit: `[D1-PHASE1-<date>] deprecate struct_n alias (docstring + spec note only)`.

**Gate:** L-58 conformance fixture PASS (5/5 unchanged — Phase 1 chỉ thêm text, không đổi field).

### Phase 2 — DUAL-WRITE + CONSUMER MIGRATION + DOWNSTREAM AUDIT + YAML RENAME (ký, apply 22-25/08)

**Goal:** Đồng thời write cả `struct_n` (legacy) + `ep_len` (canonical) trong mọi output. Consumer chuyển đọc `ep_len` một cách tuần tự. Audit + yaml rename cùng đợt.

Actions:
1. Watchlist inline detect_episodes: keep both `struct_n` + `ep_len` (đã có, không đổi).
2. Watchlist CSV/JSON output: keep both cols (đã có sau A2 migrate).
3. Consumer migration checklist (từng chỗ đọc, đổi sang `ep_len` / `sn_count_le050`):
   - [ ] `scripts/watchlist_daily.py::in_list_a`: đọc `s['ep_len']` thay `s['struct_n']` (semantics = ep_len, không cần đổi số). GIỮ fallback `sn_count_le050` gate switch A2.
   - [ ] `scripts/watchlist_daily.py` print rows L296/L493: đổi label header `sn` → `ep_l` explicit.
   - [ ] Registry probes (_probe_registry_backfill_*.py): đọc `ep_len` thay `struct_n` (nếu có).
   - [ ] **M1 Sửa 2 — lib/registry_events.py bỏ fallback im lặng `ep.get("sn_count_le050", ep["struct_n"])` → đọc thẳng `ep["sn_count_le050"]` (KeyError = fail-loud, bài L-51). Grep toàn repo `.get("sn_count_le050"` → 0.**
   - [ ] Downstream tools (external reader) AUDIT — identify tất cả reader dùng field struct_n (analyzer scripts, notebook, dashboard, CASE_INDEX apply script). Notify consumer + đổi. **KHÔNG chuyển sang Phase 3 — audit trong Phase 2 (M1 Sửa 3).**
   - [ ] CASE_INDEX apply script (append DAILY): đổi col name (nếu có struct_n col).
   - [ ] **KHÔNG rewrite historical CSVs** — CSV/JSON cũ giữ nguyên header (M1 Sửa 1).
4. **Yaml key rename cùng đợt (M1 5-ô KÝ)**: `data/config/watchlist_thresholds.yaml` rename `struct_n_min` → `sn_count_min` (per `proposals/yaml_change_20260821.md`). Apply cùng Phase 2 commit.
5. Commit series: `[D1-PHASE2A-<date>] dual-write ...`, `[D1-PHASE2B-<date>] consumer migration ...`, `[D1-PHASE2C-<date>] yaml rename ...`, `[D1-PHASE2D-<date>] downstream audit ...`.

**Gate:** L-58 fixture PASS. Cron watchlist 01:40 UTC ngày kế verify CSV có cả 2 cols, cron output khớp legacy. Grep `.get("sn_count_le050"` toàn repo = 0.

### Phase 3 — REMOVE (ký, apply cuối, cutover 2026-09-30)

**Goal:** Xóa `struct_n` field khỏi mọi output. Không alias. Canonical `ep_len` + `sn_count_le050` only.

Actions:
1. **Bump L-58 fixture: regenerate golden với semantics MỚI. Fixture in BẢNG CHỨNG VALUE bit-equal cho MỌI token/ngày (chỉ KEY đổi struct_n→ep_len, VALUE = same). Khác value = FAIL (M1 Sửa 3).**
2. `lib/hedge_episode.py::detect_episodes`: XÓA `"struct_n": sn` khỏi output dict. Giữ `"ep_len": sn` + `"sn_count_le050": sn_count`.
3. `lib/registry_events.py`: same. Bỏ `_detect_ev` (a) fallback `ep[i-1]["struct_n"]` — đọc thẳng `ep[i-1]["sn_count_le050"]`.
4. `scripts/watchlist_daily.py`:
   - XÓA `"struct_n"` khỏi inline detect_episodes output + snap + CSV header + row + print header
   - Nếu bit-equal check pass với ep_len rename (should = same value), commit.
5. **File tháng MỚI (watchlist_log_2026-09.csv, snapshot từ cutover) dùng header mới** — reader đọc theo TÊN cột, KHÔNG theo vị trí. **CSV/JSON cũ giữ nguyên header — KHÔNG rewrite lịch sử. CORRECTIONS không chạm (M1 Sửa 1).**
6. Watchlist ONLY: verify VPS cron 01:40 chạy đúng post-cutover (file tháng 09 header mới).
7. Registry probes/tests: 100% dùng `ep_len` + `sn_count_le050`.
8. Commit: `[D1-PHASE3-<date>] HƯU struct_n — canonical ep_len + sn_count_le050 only. Cutover 2026-09-30.`.

**Gate (M1 Sửa 3):** 
- **L-58 fixture regen PASS + IN BẢNG CHỨNG VALUE bit-equal (chỉ KEY đổi, VALUE = same trên MỌI token/ngày). Khác value = FAIL.**
- P0 check watchlist bit-equal (verify chỉ đổi TÊN, không đổi VALUE).
- Cron VPS 01:40 UTC ngày kế cutover: file 2026-09.csv header mới (không col struct_n).
- Downstream tools verify (report script, dashboard) — 0 KeyError('struct_n'). **Audit đã hoàn tất trong Phase 2.**

**Timeline:**
- Phase 1: 21/08 (M2 sau operator ký) — 1 commit, ~1h
- Phase 2: 22-25/08 (theo consumer migration checklist + yaml rename + downstream audit) — ~4 commits (A/B/C/D)
- Phase 3: cutover 2026-09-30 (KÝ) — 1 commit series với fixture regen bảng chứng

## Risk assessment (post M1 Sửa 1/2/3)

- **Phase 1 low**: chỉ text note. Không đổi hành vi.
- **Phase 2 medium**: dual-write mới, consumer migration + yaml rename + downstream audit. Cron test verify. Fail-loud thay fallback im lặng (Sửa 2 = bài L-51 dùng).
- **Phase 3 medium**: cutover, downstream reader đã audit ở Phase 2, không có surprise. **Không rewrite lịch sử = risk historical CSV giảm về 0.** Fixture bảng chứng VALUE bit-equal chặn silent VALUE drift.

## Fallback rollback plan

Nếu Phase 3 cutover VỠ:
- Revert commit → alias struct_n restore.
- Fix consumer, re-apply.

**Historical CSVs KHÔNG bị chạm (M1 Sửa 1)** — không cần rollback lịch sử.

## Decisions (5 ô KÝ — operator chat 21/08)

- [x] **Ký Phase 1 apply immediate (docstring + spec note + dòng ánh xạ)** — M2 commit ngay
- [x] **Ký Phase 2 22-25/08** (dual-write + consumer migration + yaml struct_n_min→sn_count_min cùng đợt + downstream audit cùng đợt)
- [x] **Ký Phase 3 cutover target date 2026-09-30**
- [x] **Ký yaml_change_20260821.md apply cùng Phase 2** (không riêng phase)
- [x] **Ký downstream reader audit trong Phase 2** (không đợi Phase 3 — M1 Sửa 3)

## Cross-ref

- Operator directive: ER-HOME Option 2 ký 21/08 (D1) + M1 (b)+3 sửa ký 21/08 supersedes D1 draft (48daf42)
- Spec canonical: `D:/Data back test/whale_data/proposals/unhedge_registry_spec.md` §E-R1 conformance
- L-58: fixture-first migration (mỗi phase cần fixture PASS)
- L-51: fail-loud, không fallback im lặng (M1 Sửa 2 áp dụng)
- Related proposals: `proposals/yaml_change_20260821.md` (yaml key rename cùng scope Phase 2)
- Sha history: d20bd8a (A1) · 72e36b1 (A2) · b6a44b7 (A4 I-L) · 2193f9d (A4 fixture golden) · 401366e (D4 header) · 48daf42 (D1 draft SUPERSEDED by this SIGNED)

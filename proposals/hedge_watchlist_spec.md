---
type: spec
name: HEDGE WATCHLIST — DAILY SCAN
version: v1.4 (base) + conformance-pack 21/08/2026
canonical_source: scripts/watchlist_daily.py (inline detect_episodes/avg3/calc_div, bit-equal lib/hedge_episode.py per P0 SAFE 139-token verify)
status: ACTIVE — cron 01:40 UTC production
signed: v1.3 (13/08 · framework) · v1.4 (17/08 · B1/B2/PHẲNG split + 🎓 graduation) · conformance-pack (21/08)
---

# HEDGE WATCHLIST — spec pointer + conformance-pack note

**Canonical code:** `scripts/watchlist_daily.py` (line 107-158 inline `avg3` / `calc_div` / `detect_episodes` — bit-equal `lib/hedge_episode.py` per P0 CHECK 2ba669f: 0 diffs across 139 tokens, 0 diffs across 9 TARGETS math sample).

**Config:** `data/config/watchlist_thresholds.yaml` (v1.4 with hedge/list_b/trends/oi_guard/data/output blocks).

**Consumer contract (P0 SAFE):** watchlist inline `detect_episodes` = lib bit-equal. **KHÔNG được edit lib** một cách phá bit-equal — nếu cần đổi semantics lib, phải:
1. Ký amendment (§L-58 conformance fixture doctrine)
2. Cùng lúc refactor watchlist inline copy hoặc split lib API
3. Chạy conformance fixture PASS trước merge

---

## §1 — Episode definition (POINTER watchlist v1.3 §1, giữ nguyên)

`div_avg3 ≤ div_ratio_max=0.5` streak, gap-tolerance 2d, episode_break 3d.

Xem `scripts/watchlist_daily.py::detect_episodes` (canonical inline).

---

## §2 — List B condition (POINTER watchlist v1.4 §VIII.2)

Cover Monitor gate:
- `in_hedge` trong `recent_hedge_days=2`  
- `div_delta > 0` (nới)
- `pos_trend = BẬT`

Split B1/B2/PHẲNG per §VIII.2 (pos_r ↑ ≥15%/2d + OI ↓ = SHORT-COVER B1 · OI ↑ = LONG-MỚI B2 · else PHẲNG).

🎓 graduation classifier: token rời List B day-over-day → tra snapshot prev-day → classify.

---

## §3 — struct_n canonical (conformance-pack 21/08/2026)

**canonical struct_n = `count(div_avg3 ≤ 0.5)` trong episode** (cùng §E-R1 conformance-pack canonical, `proposals/unhedge_registry_spec_v1.0.md`).

- EXCLUDE gap-tolerated days (những ngày `div > 0.5` được tolerance ep_break=3d không tính).
- Biến đếm CẢ gap-days (`i − ep_start_i + 1 while in_hedge=True`) đổi tên **`ep_len`**.
- **CẤM đội tên `struct_n` cho `ep_len`** — hai đại lượng khác nhau khi episode có gap.

**Watchlist consumer note (frozen inline):**
- Watchlist inline `detect_episodes` hiện trả về `struct_n = i − ep_start_i + 1 while in_hedge` (semantics `ep_len` theo canonical mới).
- Bit-equal với lib (P0 SAFE 0 diffs 139 tokens) → KHÔNG edit lib.
- Watchlist output field name `struct_n` **giữ nguyên tên cũ** để backward-compat downstream consumers (list_b filter, snapshots hedge_watchlist_YYYY-MM-DD.json, corrections CSV).
- **Semantics label `struct_n` trong watchlist output = `ep_len` canonical** — downstream đọc watchlist_log_YYYY-MM.csv col `struct_n` phải hiểu theo `ep_len` (include gap-days).
- **List B struct_n ≥ 5**: v1.4 watchlist config điều kiện `struct_n_min=5` áp trên field hiện tại (= ep_len). Per canonical mới, "struct_n≥5" phải hiểu theo `count(div≤0.5)`. **PROVISIONAL:** vì bit-equal watchlist=lib và không kick List B (list_b không dùng struct_n_min gate cứng, chỉ list_a), semantics discrepancy KHÔNG áp gate hiện tại. Nếu ANALYSIS quyết áp gate `count(div≤0.5)≥5` cho List A hedge_start_date filter → cần amendment ký riêng + refactor.

**Consumer split canonical (per §E-R1 conformance-pack):**
- **Watchlist (`scripts/watchlist_daily.py`):** tiếp tục dùng field `struct_n` = `ep_len` semantics (frozen inline, backward-compat). Downstream label hiểu theo `ep_len`.
- **Registry (`_probe_registry_backfill_e_r7e_*.py`):** dùng `sn_count_le050` mới compute từ episode (count `div_avg3 ≤ 0.5` trong ep). CẤM dùng `ep_data[i]["struct_n"]` từ lib cho registry — dùng count mới.

---

## §4 — Cross-ref

- `proposals/unhedge_registry_spec_v1.0.md` §E-R1 conformance-pack — canonical struct_n definition
- `proposals/lessons_pending_batch_V2.md` L-58 — conformance fixture doctrine
- `lib/hedge_episode.py` — shared function (bit-equal watchlist inline)
- `scripts/watchlist_daily.py::detect_episodes` (L107-158) — canonical INLINE (P0 SAFE)

**Changelog (spec file this):**

| Version | Date | Changes |
|---------|------|---------|
| pointer | 21/08/2026 | Spec pointer file created + conformance-pack note (§3 struct_n canonical + consumer split). Operator ký chat 21/08. |

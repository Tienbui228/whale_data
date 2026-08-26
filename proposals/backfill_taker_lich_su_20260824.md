# Backfill lịch sử `taker_buy_pct` store — one-page proposal

**Status:** DRAFT — CHỜ OPERATOR KÝ RIÊNG (không nằm trong scope ⑩-AMENDMENT deploy).
**Ngày soạn:** 2026-08-24
**Companion:** ⑩-AMENDMENT-20260824 vế 3 (`41d8d717` bot-signals + `a594115` whale_data) — migrate forward-only.
**Trigger:** Row 9 hai họ divergence_note verbatim ký lượt cuối: *"(v)-taker-lineage 4 ngày TỒN TẠI CHO ĐẾN KHI backfill lịch sử taker được ký riêng."*

---

## Nguồn data có sẵn (KHÔNG cần re-fetch klines)

VPS `/root/Data_back_test/whale_data/scratch/vol_k7_fresh_*.csv`:

| file | rows | header |
|---|---:|---|
| `vol_k7_fresh_2026-06.csv` | 1370 | `date, symbol, k5_base_vol, k7_quote_vol, n_trades, taker_buy_base, taker_buy_quote` |
| `vol_k7_fresh_2026-07.csv` | 4308 | (same) |
| `vol_k7_fresh_2026-08.csv` | 2781 | (same) |
| `vol_k7_fresh_full_v2_20260824.csv` | (combined) | (subset cols) |

**Có `taker_buy_quote` = k[10] — đủ tính canonical `taker_buy_pct = k[10]/k[7]` per (symbol, date).**

Coverage estimate: ~527 symbols × 3 tháng (06-08/2026) = **≈8,459 (symbol, date) rows** trực tiếp từ scratch, KHÔNG cần fetch klines fapi.

Pre-tháng 06 (05, 04, ...) = chưa có `vol_k7_fresh_*` → cần re-fetch klines_1d nếu muốn.

---

## Đề xuất scope backfill

**Scope A (minimal — chỉ dùng scratch có sẵn):**
- Backfill `taker_buy_pct` store cho tháng 06, 07, 08/2026 (~8,459 rows).
- Update `taker_source` = `"k10_over_k7_scratch_backfill_20260824"` (giá trị mới, khác `"k10_over_k7_fresh"` forward-only).
- Idempotent: nếu `taker_source` đã là `k10_over_k7_*` → skip (không double-write).
- Không đụng dữ liệu ngoài phạm vi scratch cover.

**Scope B (extended — cần re-fetch):**
- Backfill lịch sử pre-06/2026 (từ 04, 05/2026 hoặc xa hơn) = re-fetch klines_1d fapi ~527 syms × N days.
- Time estimate: 527 × 90d × 1 API call ≈ 47,430 calls. Với rate-limit 6000/min = ~8 phút fetch, tổng ~15-30 phút deploy.
- Store: append vào scratch pattern `vol_k7_fresh_2026-<M>.csv` hoặc partition mới.

---

## Idempotent + upsert semantics

- Key: `(symbol, date)` — upsert (không duplicate row per date).
- Nếu row đã có `taker_source = "k10_over_k7_fresh"` (post-migrate forward): **skip** (mới hơn scratch backfill).
- Nếu row có `taker_source = "r_over_1p r_LEGACY"` hoặc missing: **overwrite** với scratch canonical.
- Log: per (symbol) count skipped vs overwritten.

## Consumer impact

Consumers đã ăn `taker_buy_pct` (dry-run 5b evidence):
- absorption() B3: 11 flip already evaluated + accepted (boundary ±0.5%).
- Backfill lịch sử → **N-thêm flips khác** (chưa đo — cần dry-run tương tự 5b trên scratch data trước khi commit).

**Đề xuất:** Chạy dry-run consumer diff (5b-clone) trên scope A trước khi apply. Nếu delta stats khớp 5b (mean~0.0004, max~1.5%, absorption flips ~11-30 cluster), safe apply. Nếu lớn hơn → chờ signoff.

---

## Ước lượng ngày phủ + impact

**Scope A (recommended, backfill 3 tháng):**
- Rows: ~8,459
- Time: ~2-3 phút agg + write (không API call)
- Consumer flips: ước ~30-50 rows absorption (tương xứng scale 8459/807 × 11 = 115 nhưng cluster TAG-like → mediate)
- Row 9 hai họ hội tụ: cải thiện 4 ngày (v)-taker-lineage → 0 nếu BULLA scratch 06-27→08-24 có đủ

**Scope B (extended, backfill pre-06):**
- Rows: ~47,430
- Time: 15-30 phút fetch + agg
- Impact: unknown — cần dry-run

## Đề xuất TL;DR

1. **Ký Scope A** (idempotent + provenance tag `k10_over_k7_scratch_backfill_20260824`).
2. Chạy dry-run consumer diff clone 5b trên scope A trước SCP.
3. Nếu flips ≤ 3× threshold từ 5b baseline → apply + verify Row 9 hai họ (v)-tag giảm về 0.
4. Nếu flips lớn → paste bảng chờ signoff phase 2.
5. Scope B pending Scope A verdict.

**CHỜ OPERATOR KÝ** — không tự chạy. Backup L-37 mọi ghi vào store trước apply.

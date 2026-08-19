---
type: lessons_pending_batch
for_sheet: CASE_INDEX.xlsx → LESSONS
date: 2026-08-18
status: DRAFT — chờ operator nhập một lượt
mã_án: M6-20260818
source: docs/handover/analysis_handover_addendum_20260818.md §C
---

# Batch lessons pending — 18/08/2026

Trọn batch đang treo (chưa nhập LESSONS sheet). Ký một lần → nhập LESSONS sheet CASE_INDEX → `lessons_learned.md` regenerate view. **Không sửa file này sau khi nhập** — giữ làm sử ký nguồn.

Batch gồm hai nhóm:
- **Nhóm §C net-semantics (3 lessons)** — từ addendum 20260818, mã án `M6-20260818`.
- **Nhóm handover §5 pending** — còn treo từ handover 17/08 (chưa nhập).

Operator chỉnh lời văn tùy ý trước khi nhập; batch này giữ nguyên logic + citation.

---

## §C.1 — MỘT-TÊN-HAI-NGHĨA: `net_oi_delta` đọc ngược 180°

**Title:** Một-tên-hai-nghĩa — cùng nhãn biến, ba nghĩa trái dấu

**Body:**
Cùng nhãn "net" nhưng ba số ba nghĩa: `gross_adds_usd` (Σ ΔOI⁺ trên FIRE ∧ counts_q1) · `net_oi_window_usd` (OI_end − OI_start ungated) · `net_gated_usd` (Σ ΔOI cả ± trên FIRE ∧ counts_q1 — CANONICAL). Trước khi so sánh/verdict, TRA ĐỊNH NGHĨA đầy đủ; không dùng tên viết tắt "net".

**Exhibit AKE ch1 (2026-08-12 → 08-17):** `{net_window +$14.67M · gross $0 · net_gated −$5.16M}`. Đọc `net_oi_delta` cũ (window ungated) sẽ tưởng chain "gom mạnh"; đọc `net_gated` (canonical) thấy 2 ngày qualifying (08-16, 08-17) RÚT ròng −$5.16M — chase-pump chứ không phải gom.

**Rule:** Mọi verdict "net dose" phải trích tên biến FULL (`net_gated_usd`, không "net"). Reader thấy tên viết tắt → hỏi lại định nghĩa trước khi đọc số.

**Ref:** commit `da81774` (code split); mã án `M6-20260818`; sử ký `docs/handover/analysis_handover_addendum_20260818.md`.

---

## §C.2 — L-31 ADDENDUM: trích gate PHẢI kèm enclosing condition

**Title:** L-31 addendum — trích gate phải kèm enclosing block

**Body:**
Gate spec (ret≤1%, not-partial) chỉ đúng nghĩa khi kèm enclosing block. Trích `counts_q1 = ret ≤ 1% ∧ not_partial` mà bỏ `if gom_day:` bao ngoài = mất doctrine (thu ngày non-fire vào doctrine sai).

**Why:** `update_chain()` gọi từ scan CHỈ khi `eval_gom.gom_day = True`. counts_q1 sống TRONG nhánh fire. Bỏ enclosing = mở rộng day-universe không đúng thiết kế. R-1b Option 2 (bỏ fire) sinh 15 chain có counts_q1>0 mà n_fire<counts_q1 — khớp dấu hiệu drift.

**How to apply:** Mọi trích dẫn gate/công thức: (a) trích trọn from-outer-block-to-innermost; (b) khai enclosing condition trên đầu (fire-day, chain-open, non-cooldown, etc.). Comment code header cũng phải khai enclosing.

**Ref:** L-31 (gốc); `gom_scan.py::_empty_chain` header comment M6 addendum; mã án `M6-20260818`.

---

## §C.3 — ĐĂNG-KÝ-TRƯỚC HAI PHÍA

**Title:** Đăng-ký-trước-hai-phía: tiêu chí PASS + FAIL + bucket phụ, TRƯỚC khi nhìn số

**Body:**
Trước khi nhìn số, đăng-ký NGUYÊN VĂN cả tiêu chí PASS lẫn FAIL + xử lý bucket bổ sung (n<threshold → UNDERPOWERED, không verdict; đói mẫu → thêm K secondary CÙNG tiêu chí).

**Why:** Day-k=3 run 15/08 đã "FAIL — net không tradeable" nhưng dùng wrong-variable (`net_oi_delta` raw ungated) → verdict INVALID. Nếu tiêu chí đăng-ký-trước có ràng buộc "biến CANONICAL + trích enclosing", verdict cũ đã tự loại. Đăng-ký-trước hai phía chống ex-post cắt kết luận.

**How to apply:** Report design PHẢI có block "TIÊU CHÍ ĐĂNG-KÝ-TRƯỚC" ở đầu, TRƯỚC data section. Bao gồm: (a) tên biến FULL, (b) tiêu chí PASS nguyên văn, (c) tiêu chí FAIL nguyên văn, (d) bucket phụ (C=NaN, UNDERPOWERED=n<X) đăng ký cùng lượt, (e) fallback K/threshold secondary (nếu đói mẫu). Modify tiêu chí sau khi nhìn số = **cấm**.

**Ref:** R-1b (32/56 MATCH, n(C) 62.5% tại fire+3); mã án `M6-20260818`.

---

## Nhóm handover §5 pending (còn treo 17/08 — hỏi lại operator batch nào ưu tiên)

Handover 17/08 §5 (Verdict drafts) liệt kê: **AIN TRACKING-ACTIVE · APR→DIST-WATCH · DORMANT-register · APR-DEX-RETRACTED · BANK verdict · TUT T+30 feed**.

Ba lesson §C trên **KHÔNG bao trùm** các verdict này. Batch pending §5 = riêng, chờ operator queue thứ tự nhập LESSONS sheet. Không tự nhập.

---

## Nhóm §D venue-coverage (1 lesson) — thêm 19/08 (mã án V1-20260819)

## §D.1 — L-52: Venue coverage — "không có spot Binance" ≠ "không có spot"

**Title:** L-52 Venue coverage — xác định venue trước, kết luận chân hàng sau

**Body:**
"Không có spot Binance" chỉ là phát biểu về Binance, không phải về thị trường. Băng thông xả và chân hàng phải tính trên venue spot **lớn nhất thực tế** (không phải venue mặc định đầu tiên tra). Trước khi kết luận "Alpha-only" hay "perp-only chain": tra spot venues lớn (Bybit · OKX · Gate · KuCoin · MEXC · Bitget) trước, kết luận sau. LAYER COVERAGE của mọi report case từ nay PHẢI khai `spot-ext: <venue>/N/A/CHƯA-TRA` — quy ước: **CHƯA-TRA ≠ N/A**; N/A chỉ được ghi sau khi đã tra và xác nhận không có.

**Exhibit TRIA (2026-08-19):** Probe 19/08 kết luận TRIA "Alpha-only + Perp" dựa trên Binance api/v3 (0 pair) — báo cáo `taker_spot_pct = ABSTAIN-STRUCTURAL`. Backfill 19/08 phát hiện **Bybit có TRIAUSDT spot Trading** (`/v5/market/instruments-info retCode=0 status=Trading`). Bybit turnover Aug18 = **$2,304,652** (**3× Alpha $770K**), Aug17 = $133K. Nếu không tra Bybit → mù nguyên một van xả 3× Alpha. Cú pump +18% Aug18 chạy trên 3 chân: perp $25M · Bybit $2.3M · Alpha $770K. Doctrine #10 (kho ÷ băng-thông) nếu chỉ tính Alpha sẽ đọc SAI hệ số 4×.

**Reconnaissance đi kèm (chưa kéo klines, chỉ instruments-info):**
- BTW: Bybit=∅ · OKX=∅ · Gate=∅ (perp-only)
- GUA: Bybit=∅ · OKX=∅ · **Gate=TRADABLE GUA_USDT** ← án 17/08 và 18/08 bỏ sót
- APR: Bybit=∅ · OKX=∅ · Gate=∅ (perp-only)
- CLO: Bybit=∅ · OKX=∅ · Gate=∅ (perp-only)
- TRIA: Bybit=Trading · OKX=∅ · Gate=∅

**Rule:** 
1. Case-open probe: tra ≥3 venue spot (Bybit + OKX + Gate) tối thiểu trước khi ghi verdict Alpha/perp-only.
2. LAYER COVERAGE header line bắt buộc: `spot-ext: <venue1,venue2>/N/A/CHƯA-TRA`.
3. Cột canonical CASE schema v2.1: `vol_spot_ext_usd` (col 51) · `spot_ext_venue` (col 52) — CẤM ghi vào `vol_spot_usd` (col 31 = Binance api/v3 canonical, một-thứ-hai-tên L-51/GUA án 17/08).
4. Trước khi dùng field mới nào từ venue mới: identity-check bit-level ≥3 mẫu so với field nguồn nghi vấn (chống mirror).

**Ref:** commit sau paste; probe `_probe_tria_venue_20260819.py`; report `docs/reports/_tria_venue_backfill_20260819.md`; schema amendment `docs/handover/spot_top_venue_howto_dev_analysis_20260815.md` §D4-ext.

---

## Trình tự nhập (operator)

1. Đọc §C.1 → §C.3 (batch net-semantics — có exhibit AKE cứng, chèn LESSONS sheet ngay).
2. **Đọc §D.1 L-52 (batch venue-coverage — exhibit TRIA + recon 4 token cứng, chèn LESSONS sheet ngay).**
3. Sau khi các dòng LESSONS nhập → `_task_regen_lessons.py` chạy → `lessons_learned.md` refresh view.
4. Nhóm handover §5 pending: hỏi operator queue thứ tự (batch riêng, ngoài M6/V1 scope).
5. **KHÔNG xóa file này** sau khi nhập — giữ sử ký batch (immutable_after_sign).

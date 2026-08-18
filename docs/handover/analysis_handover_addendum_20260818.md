---
topic: Addendum handover 20260817 — NET-SEMANTICS SPLIT (án semantic-drift)
purpose: Sử ký ký 18/08 · phân phối vào canonical homes bằng lệnh U-0→U-6
author: Analysis (relay) + DEV agent
signed_by: operator
signed_at: 2026-08-18
mã_án: M6-20260818
immutable_after_commit: true
---

# Addendum handover 20260817 — NET-SEMANTICS SPLIT

**Ngày ký:** 18/08/2026 · **Án:** semantic-drift (một-tên-hai-nghĩa) · **Boot:** đọc SAU handover chính (docs/handover/analysis_handover_20260817.md).

Sử ký này là NGUỒN duy nhất; mọi bản sao ở các nhà canonical (gom_detect_spec §M6, playbook §VIII.15, lessons_pending_batch, TASKS net-dose, INDEX) chỉ là copy. Sửa addendum = **CẤM** sau merge.

---

## §A. AMENDMENT M6 — NET SEMANTICS SPLIT (target: gom_detect_spec.md)

### M6 — NET SEMANTICS SPLIT (ký 18/08/2026, án semantic-drift)

Thay thế mọi cách dùng `net_oi_delta` cũ. BA SỐ BA TÊN:

- **`gross_adds_usd`** = Σ max(ΔOI,0) trên ngày FIRE ∧ counts_q1 [GIỮ NGUYÊN — "lực gom cộng dồn"]
- **`net_oi_window`** = OI_end − OI_start toàn chain, MỌI ngày, ungated [rename từ `net_oi_delta`; nhãn bắt buộc mọi output: "window, ungated — reality-check, KHÔNG phải lực gom"; CẤM làm signal]
- **`net_gated_usd`** [CANONICAL "gom ròng doctrine"] = Σ ΔOI (CẢ ÂM LẪN DƯƠNG, không max) trên ngày FIRE ∧ ret_1d ≤ 0.01 ∧ not-partial. Lý do doctrine: ΔOI là biến MÙ-PHÍA — fire-day là mỏ neo attribution duy nhất; cùng day-universe với gross/Q1 lịch sử. CHÚ Ý TRÍCH GATE: counts_q1 nằm TRONG nhánh fire của eval-loop — mọi trích dẫn gate phải kèm enclosing condition (L-31 addendum).
- **`net_qualifying_usd`** [exploratory, non-canonical] = Σ ΔOI ngày qua-ret-gate KỂ CẢ không-fire — chưa có quyền vào verdict.

**LUẬT n_q1=0:** `net_gated` = NaN (không phải 0) + cờ `NO-QUALIFIED-DAYS`; report template 3-bucket (GOM-RÒNG / CHURN-ROTATION / NO-QUALIFIED); alert chain n_q1=0 **CẤM** chữ "gom".

**LUẬT NHÃN (governance, áp mọi metric dẫn xuất từ nay):** header khai 2 dòng "ĐO GÌ / KHÔNG ĐO GÌ" trước khi metric được dùng trong bất kỳ giả thuyết/verdict nào.

**Exhibit:** AKE ch1 `{net_window +$14.67M · gross $0 · net_gated −$5.16M}` — một chain ba sự thật; một-biến cũ đọc ngược 180°.

**Thi hành:** commit `da81774` + R-1b fire-day flags (scratch/r1b_fireday_flags_20260818.json, 32 MATCH / 24 MISMATCH). Experiment day-k: `docs/reports/r2_dayk_design` (spec chỉ trỏ, không nhúng).

---

## §B. TRẠNG THÁI NET-DOSE (target: TASKS.md — khối net-dose)

| Bước | Trạng thái | Ghi chú |
|---|---|---|
| **R-0** (verdict semantic-drift) | ✅ SIGNED 17/08 | operator ký qua relay |
| **N-0..N-4 code split** | ✅ DONE `da81774` | 3 vars trong `gom_scan.py`, formatter `run_gom_daily.py`, label L-31 |
| **R-1a backfill net_gated Option 2** | ✅ DONE | 56 chapters, freshwatch_daily dedup-safe |
| **R-1b backfill Option 1 (canonical fire ∧ counts_q1)** | ✅ GO | 32/56 MATCH, 24 MISMATCH loại; ROBO/AKE verify khớp expectation |
| **R-2 day-k=3 re-run trên net_gated** | ⏸ chờ số | Đăng-ký-trước hai phía đã ghi; n(C)=62.5% > 40% → thêm K=5 secondary; primary VẪN K=3 |
| **DORMANT net-dose register** | ⏸ chờ R-2 kết luận | Ngưỡng $634K ĐÓNG BĂNG — đổi biến ≠ refit |
| **Trình tự đọc** | Đã đăng ký | R-1b → R-2 (net_gated) → operator đọc → verdict thứ 4 (biến đúng nghĩa + tập ngày đúng doctrine + tiêu chí đăng-ký-trước) |

**Câu hỏi cũ "net-signal đóng vì Group B beat A":** VÔ HIỆU (đo biến sai). MỞ LẠI trên net_gated, phân xử bởi R-2.

---

## §C. LESSONS + PLAYBOOK LINE (target: playbook §VIII.15 + lessons_pending_batch)

### Playbook §VIII.15 (dòng nguyên văn, append)

**VIII.15 — một-tên-hai-nghĩa: `net_oi_delta` đọc ngược 180°**

Cùng nhãn "net" nhưng ba số ba nghĩa: `gross_adds` (Σ ΔOI⁺ trên fire∧gate) · `net_oi_window` (OI_end−OI_start ungated) · `net_gated` (Σ ΔOI cả ± trên fire∧gate — CANONICAL). Exhibit AKE ch1: `{window +$14.67M · gross $0 · gated −$5.16M}` — cùng chain ba câu trả lời trái dấu. Trước khi ném biến vào giả thuyết/verdict: đọc 2 dòng "ĐO GÌ / KHÔNG ĐO GÌ" của biến; thiếu 2 dòng = biến chưa đủ tư cách vào doctrine.

### 3 Lessons (chèn vào CASE_INDEX sheet LESSONS qua batch file)

**Lesson §C.1 — một-tên-hai-nghĩa + exhibit AKE**

- Rule: Cùng tên biến (`net_...`) không đảm bảo cùng nghĩa. Trước khi so sánh/verdict, TRA ĐỊNH NGHĨA đầy đủ (không dùng tên viết tắt).
- Why: AKE ch1 net_oi_delta cũ = +$14.67M → nghe như "chain gom mạnh". Ba biến mới nói ngược: gross=$0 (không lực gom ngày qualifying), net_gated=−$5.16M (2 ngày qualifying RÚT ròng). Chain thực chất chase-pump.
- How to apply: Mọi verdict về "net dose" phải trích tên biến FULL (net_gated_usd, không "net"). Reader thấy tên viết tắt → hỏi lại định nghĩa trước khi đọc số.

**Lesson §C.2 — L-31 addendum: trích gate PHẢI kèm enclosing condition**

- Rule: Gate spec (ret≤1%, not-partial) chỉ đúng nghĩa khi kèm enclosing block. Trích `counts_q1 = ret ≤ 1% ∧ not_partial` mà bỏ `if gom_day:` bao ngoài = mất doctrine (thu ngày non-fire vào doctrine sai).
- Why: `update_chain()` gọi từ scan CHỈ khi `eval_gom.gom_day = True`. counts_q1 sống TRONG nhánh fire. Bỏ đi = mở rộng day-universe không đúng thiết kế. R-1b Option 2 (bỏ fire) sinh 15 chain có counts_q1>0 mà n_fire<counts_q1 → khớp dấu hiệu drift.
- How to apply: Mọi trích dẫn gate/công thức: (a) trích trọn from-outer-block-to-innermost; (b) khai enclosing condition trên đầu (fire-day, chain-open, non-cooldown, etc.).

**Lesson §C.3 — đăng-ký-trước-hai-phía**

- Rule: Trước khi nhìn số, đăng-ký NGUYÊN VĂN cả tiêu chí PASS lẫn FAIL + xử lý bucket bổ sung (n<threshold → UNDERPOWERED, không verdict; đói mẫu → thêm K secondary CÙNG tiêu chí).
- Why: Day-k=3 run 15/08 đã "FAIL — net không tradeable" nhưng dùng wrong-variable (net_oi_delta raw ungated) → verdict INVALID. Nếu tiêu chí đăng-ký-trước có ràng buộc "biến CANONICAL", verdict cũ đã tự loại. Đăng-ký-trước hai phía chống ex-post cắt kết luận.
- How to apply: Report design PHẢI có block "TIÊU CHÍ ĐĂNG-KÝ-TRƯỚC" ở đầu, trước data section. Modify tiêu chí sau khi nhìn số = không được. Bucket phụ (C, UNDERPOWERED) đăng ký cùng lượt.

---

## §D. COMMIT CHECKLIST (M6-20260818)

Trình tự đóng án:
1. ✅ `da81774` — N-0..N-4 code split (`scripts/gom_scan.py`, `scripts/run_gom_daily.py`)
2. ✅ R-1a probe `scratch/r1_backfill_net_gated_20260818.csv` (56 chapters Option 2)
3. ✅ R-1b probe `scratch/r1b_fireday_flags_20260818.json` (Option 1 canonical, 32 MATCH)
4. ⏳ **U-0 commit addendum này** (whale_data) — sử ký vào sổ TRƯỚC
5. ⏳ U-1 chèn M6 vào `binance-bot-signals/docs/gom_detect_spec.md` (line 526/548)
6. ⏳ U-2 annotate 5 refs `net_oi_delta` cùng file (bảo toàn nguyên văn cũ)
7. ⏳ U-3 append VIII.15 vào `whale_data/docs/analysis_playbook.md`
8. ⏳ U-4 tạo `whale_data/proposals/lessons_pending_batch_20260818.md` (3 lessons §C)
9. ⏳ U-5 update `whale_data/docs/TASKS.md` khối net-dose (theo §B)
10. ⏳ U-6a `whale_data/docs/INDEX.md` mục "TÀI LIỆU NGOÀI REPO"
11. ⏳ U-6b bump changelog `gom_detect_spec.md` → v3.1 (v3.0 + M6)
12. ⏳ Commit 1 (whale_data): `[M6-20260818] distribute: playbook VIII.15 + TASKS + INDEX cross-ref + lessons_pending_batch`
13. ⏳ Commit 2 (binance-bot-signals): `[M6-20260818] gom_detect_spec: amendment M6 net-semantics + 5 refs annotated + changelog v3.1`

**Quy ước cross-repo (thêm CLAUDE.md sau này):** Án span 2 repo → tiền tố commit `[<mã-án>-<ngày>]` chung ở cả hai. Grep một mã ra trọn án ở cả hai nhà.

**SAU khi 2 commit xong:** R-2 (day-k re-run trên `net_gated`) chờ operator/ANALYSIS trigger. Không auto-run.

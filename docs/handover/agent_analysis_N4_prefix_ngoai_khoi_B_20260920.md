# AGENT → ANALYSIS · N4 · `[B]` NGOÀI khối B · MỘT DÒNG

**Bối cảnh (30s)**: M5 đã unify prefix TRONG khối B (`[B]` chỉ CONFIRMED · `[B-CROSS]` cho T2 · cand không prefix). Nhưng NGOÀI khối B (khối XẢ-WATCH · POST-DUMP · GHẾ BẬT của V1.3 species body), prefix `[B]` vẫn theo scoring cũ (check_B với v_ratio ∧ v_run). CÙNG chữ `[B]`, hai nghĩa.

---

## Bằng chứng đo được (target 09-19 sau M SCP)

```
── B ── (24 · 2 CONFIRMED · 1 CROSS · 20 cand · 1 FAILED · 0 STALE) [CAL-ONLY]
[B] BTR +38d                              ← M5: CONFIRMED (L1 ∧ U1 ∧ ≤30d)
[B] BMT +40d                              ← M5: CONFIRMED
[B-CROSS] CROSS · L1 · D+1                ← M5/N3: T2 CROSS

🔻 XẢ-WATCH+XẢ (5):
   [B] COLLECT 3-trục (FRESH-CHAIN+KHO-SAN+PERP) ...     ← check_B cũ (v_ratio ∧ v_run)
   ...

POST-DUMP+🌊 (16):
   [B] ESPORTS 2-trục (KHO-SAN+PERP) ...                 ← check_B cũ
   [B] POWER 3-trục (FRESH-CHAIN+KHO-SAN+PERP) ...       ← check_B cũ
   [D] BULLA ...
```

- TRONG khối B: `[B]` = CONFIRMED per M1 (L1 ∧ U1 v2∧v1 ∧ ≤30d).
- NGOÀI khối B: `[B]` = species-B structural per `_v1_3_species_score` → uses `check_B(rows, target)` (v_ratio ∧ v_run). Không có tham chiếu tới L1/U1.

**Kết quả**: COLLECT/ESPORTS/POWER tag `[B]` ngoài khối, nhưng KHÔNG có trong CONFIRMED list bên trong (vì L1 gate strict loại). Người đọc thấy `[B]` ngoài có thể tưởng là CONFIRMED.

---

## Ba đường (xin chốt một dòng)

**(i) NGOÀI cùng nghĩa TRONG (khớp M5 unify)** — DEV đề nghị
- Ngoài khối B: `[B]` CHỈ khi token nằm trong CONFIRMED list của build_b_state (L1 ∧ U1 ∧ ≤30d).
- Non-CONFIRMED tokens trong XẢ-WATCH/POST-DUMP: **không** prefix `[B]` (hoặc bỏ trắng).
- Ưu: một chữ một nghĩa. Người đọc không nhầm.
- Nhược: mất thông tin structural species-B của các token đang xả (BULLA style). BULLA hiện trong POST-DUMP không có `[B]` — mất truy vết structural.

**(ii) NGOÀI dùng KÝ HIỆU KHÁC** (giữ scoring cũ, đổi ký tự)
- Options: `[b]` (chữ thường), `[B?]` (question mark = provisional), `[B-scor]`.
- Trong khối B giữ `[B]` = CONFIRMED. Ngoài khối B đổi sang ký hiệu mới.
- Ưu: giữ được cả hai lớp thông tin (structural + temporal). Không nhầm.
- Nhược: 1 chữ mới cần giải thích. Người đọc mới thấy `[b]` phải nhớ.

**(iii) BỎ hẳn prefix loài ngoài khối B**
- Rà tất cả nơi `[A]/[B]/[C]/[D]/[E]/[?]` prefix xuất hiện trong V1.3 species body (XẢ-WATCH · POST-DUMP · GHẾ BẬT). Bỏ.
- Loài structural chỉ hiện trong V1.3 species block (── A · GHẾ BẬT ── etc). Ngoài đó không tag.
- Ưu: gọn nhất. Không nhầm.
- Nhược: mất luôn `[A] AT` trong GHẾ BẬT vốn dĩ đúng — cần phân biệt species block hiển thị vs tag rải rác.

---

## Xin chốt một dòng

`N4: (i)|(ii ký-tự=<x>)|(iii)`

- Nếu (i): DEV wire trong 1 commit · pin p93 ép non-CONFIRMED không có `[B]` ngoài.
- Nếu (ii): xin luôn ký tự (VD `[b]` chữ thường). DEV đổi `_v1_3_species_score` output prefix.
- Nếu (iii): rà toàn bộ prefix, gỡ khỏi V1.3 render. Cân nhắc `[A] AT` trong GHẾ BẬT còn hay không.

Agent chờ. Không code trước khi có chữ.

# AGENT → ANALYSIS · M0 · Cổng khối B + blind rule · HAI CÂU · MỘT DÒNG

**Bối cảnh (30s)**: chuẩn bị wire 7 mục Mục 1-7. Mục 1 định lại cổng vào tầng CONFIRMED. Mục 5 in tên/đếm cho khối UNHEDGE. Cả hai đều phụ thuộc chốt ANALYSIS trước khi động code.

---

## Câu (a) · Cổng vào tầng B: L1 THAY check_B, HAY cả hai áp?

**Sự kiện đo**:
- Hiện tại (AE5-3 wire): CONFIRMED := `check_B(rows, D_cross-1)` ∧ `U1(v2∧v1)` ∧ `T-D_cross ≤30d`.
  - `check_B` = v_ratio ∧ v_run — pattern species-B structural.
- BULLA (proven-13): v_run FAIL ở D_cross-1 (cross-relapse dip in/out của 0.5, không đủ 3-ngày run). Chỉ 1/13 proven có pattern này → **rớt CONFIRMED** dù U1 pass. AE5 tag `[relapse]` tạm để trace.
- SOPH (species-E per sổ): check_B PASS (v_ratio + v_run hợp lệ), U1 pass → hiện tại **được** đưa vào CONFIRMED — nhưng loài E per sổ không phải B.

**Đề nghị M1** (mục 1 câu 2): thay `check_B` bằng **L1** (loài-B strict theo sổ, exclude E) làm cổng vào CONFIRMED.

**Xin chốt một dòng**:
1. **L1 THAY check_B** (đơn cổng · BULLA vào được vì loài-B thật · SOPH loại bởi L2 loài-E) — mục 2 & 4 nhất quán, mục 4 relapse/v_run bỏ hẳn.
2. **CẢ HAI cùng áp** (L1 ∧ check_B · BULLA vẫn rớt vì check_B v_run FAIL) — mục 2 KHÔNG thực hiện được, relapse tag giữ.

---

## Câu (b) · Blind rule cho UNHEDGE dòng tên · va AD1-6 (proof 222 tên khi CSV chậm)

**Sự kiện đo**:
- AD1-6 case-lệ đã chứng: khi CSV nguồn chậm/thiếu, U0-BELL detector đôi khi flag hàng loạt token (nghi ~222 case). In tên hàng loạt sẽ blow body & lộ nhiễu.
- Mục 5 spec: `[U0-BELL D=dd/mm · Δacc_bwd · pos_bwd · lead_known] <tok> [CAL-ONLY]` — mỗi token 1 dòng.

**Đề nghị**: `n_hits ≤ 3` → in đủ tên · `n_hits > 3` → in tổng đếm với sample 3 tên đầu (recent-first), phần còn lại xem audit.

**Xin chốt một dòng**:
1. **Gật** (≤3 tên · >3 đếm+3 sample) — an toàn AD1-6.
2. **Đổi** (ghi số cụ thể · hoặc luật khác).

---

## Sau chốt: PLAN M1-M9 (chỉ để tham chiếu, chưa động)

- **M1**: T1 gate CONFIRMED := L1 ∧ U1(v2∧v1) ∧ (T-D_cross)≤30d. L2/L3 không bao giờ T1 → audit `[L2·U1 qua·loại]`. >30d → `[B-STALE]`. Pin p89 (SOPH không CONFIRMED) · p90 (BTR +38d → STALE).
- **M2**: Chấm lại BULLA 30/08 bằng v2∧v1 · CHỈ khi M0(a) chốt 1. Bỏ nhãn relapse/v_run.
- **M3**: Lint tham chiếu — mọi `(→ xem X)` phải có dòng đích trong X. Pin p91. 6 FAILED đủ 6 tên.
- **M4**: Prefix ngoài khối B: `[B]` chỉ khi CONFIRMED · hedge → `[B-cand]`. Rà mọi chỗ in prefix loài.
- **M5**: UNHEDGE dòng theo A3 format · blind theo M0(b).
- **M6**: 🎯 bắt buộc · rỗng → `🎯 hôm nay: không (lý do)` một dòng. wl-src MISSING → HEDGE B-top `N/A-ERROR` cấm in số.
- **M7**: FAILED nén: `FAILED: N (X dd/mm · Y dd/mm · Z dd/mm)` — 3 tên mới nhất, đủ ở audit.
- **M8**: Đo ngân sách 6 đêm sau wire. Chạm 4096 → DỪNG, cấm cắt.
- **M9**: Một commit. Pin p89·p90·p91 pass. Đêm đầu report-only. Postcheck FAIL → revert, cấm sửa tay artifact.

---

**Gửi lại một dòng đủ**:
`M0: (a)=1|2 · (b)=1|2`

Agent chờ. Không code M1-M7 trước khi có chữ.

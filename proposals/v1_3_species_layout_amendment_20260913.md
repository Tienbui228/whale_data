# V1.3 SPECIES LAYOUT · AMENDMENT · KÝ 2026-09-13 · DEV DRAFT

**Nhánh C · local commit only · KHÔNG SCP hôm nay** — SCP+wire vào cron VPS sáng 14/09.

**Ref**:
- Spec §16 PATTERN_BOOK v1.3 md5=`77d86654`
- V3.5s GATE-D deployed 2026-09-11 02:41 UTC (md5=`02a6c4f7`)
- Cửa-thi 2-đêm passed (counter 09-11 + 09-12 all-green)

---

## 1. Layout mới · 9 khối theo thứ tự

```
━━ FRESHWATCH TỔNG · dd/mm · target=YYYY-MM-DD ━━
⛔ tripwire (nếu có · KHÔNG đổi)
[loài = trạng thái hôm nay theo khuôn §16 PATTERN_BOOK v1.3 md5 77d86654 — draft, chưa đủ mẫu]

🎯 ĐÁNG CHÚ Ý (≤5)
⛔ CẤM (≤3)

── A · GHẾ BẬT ──
   [A k/6] TOKEN X-trục (...) DATES · retX% ddX% → PRE
   ...

── B · HEDGE → UNHEDGE ──
   [B k/6] TOKEN ... → PRE [B-PENDING/CONFIRMED/FAILED/STALE]
   B-cand: n (nếu đang hedge, U1 chưa CONFIRMED)

── C · ĐẠP → GOM → ĐẨY ──
── D · GRIND ──                  (n=5)
── E · MỘT CỘT ──                (n=5)
── ? CHƯA NHÌN ĐƯỢC ──           (trục chính mù)
── CHƯA XẾP LOÀI ──              (2 ≤ k < n-1)

🔻 XẢ-WATCH+XẢ (khối riêng như V1.2 · direction-based)
POST-DUMP+🌊 (như V1.2)

DẢI-NỢ line
📒 SỔ THƯỜNG · 🚪 RỜI-SỔ (như V1.2)
[NHỊP-KÊNH 5 dòng như V1.2]
[👁 forward_tests như V1.2]

━━ footer ━━
ledger_state=... · fixture_master=... · species=<tagger sha> · book=77d86654 · amendments_applied=[V1.3-SPECIES-LAYOUT, FOCUS-c+D, UNHEDGE-v2+A1+A2]
cites: ...
concat-seal=... · target=... · built=...
```

---

## 2. Scoring · n=6/6/6/5/5

| loài | vé | n | note |
|------|-----|---|------|
| **A** GHẾ BẬT | a1 pos_ramp_14d · a2 pos_ge_7 · a3 close_low30 · a4 oi_flat · **a5 kho-OUT (MÙ)** · a6 fund_pin_7d | 6 (a5 mù) → runtime **k/5(?1)** | a5=exchange_balance không có trong freshwatch store |
| **B** HEDGE→UNHEDGE | b1 gLSR/acc≥2 · b2 div_run≤0.5×3d · b3 age · b4 div-cross · **b5 kho-IN (MÙ)** · b6 U0 W3 (Δacc≤−15% ∧ |Δpos|≤10%) | 6 (b5 mù) → **k/5(?1)** | b5=exchange_balance N/A |
| **C** ĐẠP→GOM→ĐẨY | c1 dump≤0.6H · c2 plateau · c3 lag≥7 · c4 pos_hold · c5 acc↑ · c6 pin | 6 | không có vé mù |
| **D** GRIND | d1 OI≥1.5x · d2 close_band · d3 no_div_run · d4 taker<52 · d5 bait-45d | 5 | |
| **E** MỘT CỘT | e1 spike≥35% · e2 follow≤10% · e3 vol_spike · e4 crowd_flip · e5 fresh-N/A | 5 | |

**★ Vé phụ mù**:
- a5/b5 mù VĨNH VIỄN (exchange_balance chưa có nguồn) → **n effective = 5**, in `k/5(?1)`
- Vé phụ mù (không phải trục chính) làm **GIẢM n**, KHÔNG ép [?]
- **[?] chỉ khi TRỤC CHÍNH mù**:
  - A trục chính = pos_r → pos_r(T) None → [?A]
  - B trục chính = gLSR/acc → cả hai None → [?B]
  - C trục chính = close/px → không đọc được px → [?C]
  - D trục chính = OI → OI(T) None → [?D]
  - E trục chính = close(T-1)/close(T-2) → None → [?E]

## 3. Xếp khối

| k score | xếp vào |
|---------|---------|
| k ≥ n−1 (5/5 hoặc 5/5(?1) hoặc 4/5(?1) etc) | **khối loài** đó |
| 2 ≤ k < n−1 | **── CHƯA XẾP LOÀI ──** (in `[A 4/6]` để thấy điểm) |
| k < 2 mọi loài (tất cả zero-tag) | **── CHƯA XẾP LOÀI ──** (in dòng, không giấu) |
| ≥1 trục chính mù | **── ? CHƯA NHÌN ĐƯỢC ──** |

**Lai species (≥3 loài khớp)**: giữ **2 theo C>D>B>A** (không tính E), in theo **chữ cái đầu**.
- Ví dụ token BD (khớp cả B và D): đặt ở khối B (chữ cái đầu). Khối D in 1 dòng nhắc `(→ xem B)` — dòng nhắc **có dấu riêng**, KHÔNG tính là dòng token (p72).

**Trong mỗi khối giữ SORT ĐỘNG CƠ hiện tại**. Không sort mới.

## 4. Prefix `[X k/n]` per token

- Dòng token as-sent **GIỮ NGUYÊN BYTE** (từ PRE/XẢ/POST-DUMP source hiện có).
- Chỉ **thêm tiền tố** `[X k/n]` ở đầu (sau indent).
- **Direction động cơ ở CUỐI dòng KHÔNG đổi** vì loài.
- Ví dụ:
  - V1.2: `   MITO 3-trục (...) → XẢ-WATCH[...]`
  - V1.3 (loài C·B lai): `   [C·B 4/6·5/6] MITO 3-trục (...) → XẢ-WATCH[...]`
  - Wait — XẢ-WATCH tokens STAY in XẢ-WATCH block (direction-based). Loài prefix vẫn thêm để cho mắt người.

## 5. ✦ ⭐-confluence AMD-01

- Dùng hàm p13 sẵn có (không tính lại).
- Render per-line: `[X k/n] ✦ TOKEN ...`

## 6. Dòng UNHEDGE · fb30dd88 + A1 + A2

Theo lifecycle từ ledger `unhedge_registry`:
- **[B-PENDING]** tại D+2 (chỉ có U0 W3 pass, U1 chưa chấm)
- **[B-CONFIRMED]** tại D+5 (U1 3/3 pass với luật acc≤0.6 · OI≥1.5 · pos≥1.0)
- **[B-FAILED k/3: vế rớt]** tại D+5 (U1 <3/3, liệt kê vé rớt)
- **[B-STALE]** sau 30d không nến ≥+20% (E-R4 EXPIRED)

Áp vào cuối dòng B token: `...→ PRE [B-CONFIRMED]`

**[B] chỉ in khi U1 CONFIRMED ≤30d.** Đang hedge (chưa cross break) → in 1 dòng riêng: `B-cand: n` (n = số token đang hedge chờ break).

## 7. 🎯 ĐÁNG CHÚ Ý (≤5) — vế (c) + D theo LR-13

| loài | chuông |
|------|--------|
| **B** | WATCHLIST-B-NEW-EPISODE `[ledger]` **∨** div_crossing_up (derived · W3 LR-13 · confirm_day=D+2) |
| **D** | **CÂM** (p57 · FIRE-SENT không tách ramp/chiều) |
| A/C | audit line "chuông-chưa-map" (không fire) |
| E | không chuông |

Rỗng → `🎯 hôm nay: không (lý do)`.

**Vé số trên dòng ▲** (ĐÁNG CHÚ Ý):
- as-printed **[sent]** > **[ledger]** > **N/A-ERROR**
- CẤM boolean, CẤM tính lại

## 8. ⛔ CẤM (≤3) — từ POST-DUMP direction

Không đổi từ V1.2 · các token direction=POST-DUMP đưa vào section này.

## 9. Postcheck tái định đích (chữ Tiên 13/09)

**p21 mới**: token có `px_now=None` phải mang direction WATCH và **KHÔNG** mang PRE, **BẤT KỂ nằm khối nào**. Vắng chủ thể → N/A (như cũ).

**p22 mới**: với **MỌI khối có header đếm** (── A ── · ── B ── · ⭐-PRE · 🔻 XẢ-WATCH · POST-DUMP · ⏸ WATCH-PX-PENDING), header ≡ **số dòng token in** + **số tên trong `(+k nữa: …)`**. **Lệch bất kỳ khối nào = FAIL**.

Sửa trong hàm canonical `_check_p21_apr_watch()` và thêm `_check_p22_header_count_all_blocks()` — harness import. **MỘT bản, không chép đôi.**

## 10. Header run

Trong body header (đầu file) và footer:
- `species=<tagger sha md5[:12]>`
- `book=77d86654`
- `amendments_applied=[V1.3-SPECIES-LAYOUT, FOCUS-c+D, UNHEDGE-v2+A1+A2]`

---

## Nợ · scope MVP session này (nhánh C)

**Wire trong W1b hôm nay**:
- Species tagger integration + [X k/n] prefix
- 9-block layout reorder
- Header attribution
- Basic 🎯 (B chuông từ ledger nếu có, else "không (lý do)")
- Basic UNHEDGE lifecycle (đọc ledger, gán state)

**Nợ NGOÀI MVP** (ghi để không quên):
- Full 🎯 A/C audit "chuông-chưa-map" line format (chi tiết chờ ANALYSIS)
- ✦ AMD-01 confluence marker — nếu p13 helper đã có in via existing render path (không code thêm)
- ⛔ CẤM (≤3) block với logic riêng — hiện dùng lại POST-DUMP block (đủ semantic)
- b3 age, b4 div-cross, c4-c6, d3-d5, e3-e5 — dùng heuristic đơn giản (`age >= 30`, `div_cross-based`) nếu không có formal spec, ghi rõ trong code là DRAFT

## Files touched

- `scripts/digest_summary_v2.py` (renderer wire)
- `scripts/postcheck_gate_d.py` (p21 tái định + p22 mới)
- `scripts/probe/species_tag.py` (NO CHANGE · reuse existing tagger)
- `tests/fixtures/parity/FIXTURE_MASTER_MD5.md` (regen after W3)
- `proposals/v1_3_species_layout_amendment_20260913.md` (this file)

## Guarantees

- Dòng token as-sent GIỮ NGUYÊN BYTE (chỉ prepend prefix)
- Không đổi direction động cơ
- Không đổi cấu trúc XẢ-WATCH / POST-DUMP / WATCH-PX-PENDING blocks (chỉ thêm prefix)
- Không đổi 5 nhịp-kênh · footer · seal
- Postcheck mới bám semantic mới, harness import 1 bản
- Cửa-thi rollback: git revert + cp .bak trên VPS = < 1 phút

## Chốt

- **HÔM NAY**: W1a + W1b + W1c + dry-run sandbox + commit LOCAL. Không SCP.
- **SÁNG 14/09**: W2 (pin đen-xanh) + W3 (fixture regen) + W4 (verify commit) + W5 (SCP + verify + buông tay).
- **ĐÊM 14/09**: cron 01:46 UTC 14/09 target 2026-09-13 = đêm đầu V1.3. Fallback = git revert + cp .bak.

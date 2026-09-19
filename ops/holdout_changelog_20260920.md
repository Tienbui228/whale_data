# HOLDOUT CHANGELOG · 2026-09-20 → 2026-10-20

**Mục đích**: mọi thay đổi chạm `div_avg3` · `acc/pos source` · `universe` · `tagger` 
trong window hold-out phải ghi vào file này kèm ngày + git sha.

**Lý do**: nếu hệ thống đổi giữa chừng thì 21/10 đang đo một hệ KHÁC — phải biết 
điều đó. Không đổi = giữ hệ so sánh sạch.

**Đối tượng đo trong holdout** (per AO pre-reg + A3-1 U0-BELL):
- U0-BELL grid: 4 ngưỡng {−10%, −15%, −20%, −30%} × `div ≤ 0.5` × `|Δpos_bwd| ≤ 10%`
- U1 v2∧v1 gate (D+5)
- Chuông cross_today (AF4 primitive)
- Universe fw_symbols (228 hiện tại)

**Format entry**:
```
## <YYYY-MM-DD HH:MM UTC> · <component> · git=<sha> · operator=<who>

<mô tả ngắn thay đổi>

- Files chạm: <list>
- Sanity check: <ok/pending>
- Ảnh hưởng holdout: <có/không · nếu có, note>
```

---

## 2026-09-18 · KÝ · pre-holdout baseline

**Baseline lock trước hold-out mở 2026-09-20**:

- `scripts/species_tag.py` · md5 `a9a134df7ec175cd50a7e2833ddccc4e`
  - `_div_avg3` (unchanged from V3.5r)
  - `run_le_yesterday`, `div_today_gt`, `cross_today` (AF4 · 18/09)
  - `hedge_age`, `chronic_history` (AG1/AH1 · 18/09) — chưa wire vào GOM-E
- `scripts/master_preview_send.py` · md5 `85125d59185670ef713d88479127f3f3`
  - AB1 pre-check HTML + length
  - AB2 26h sentinel window
  - AB3 STUCK bell (AC1-4 union preview+master)
- `sandbox/u0_bell_a3/u0_bell.py` · CALIBRATION-ONLY · chưa wire live
  - A3-1 detector: div ≤ 0.5 ∧ Δacc_bwd ≤ −20% ∧ |Δpos_bwd| ≤ 10%
- `data/config/freshwatch_symbols.txt` · md5 `b6be4f8430ecfb928d71bef073dcf007` · 228 tokens
- `data/config/freshwatch_source.json` · md5 `8a65e689b5c00a74b7ba10e01bf0d901` · 228 entries

**Pins đã PASS (18/09)**:
- p23 (26h sentinel window) · 3/3
- p25 (STUCK bell) · 4/4
- p29 (pre-check HTML+length) · 9/9
- p34 (hedge_age) · 4/4
- p35 (chronic_history) · 4/4
- p83 (cross_today) · 4/4
- p85 (BTR U0-BELL from store) · 4/4
- p86 (D_known == D lint) · 3/3
- p87 (BULLA 08-30 v2∧v1) · 2/2
- p88 (holdout header format) · 5/5

**Git status**: `git status` chưa clean · nhiều file A3 chưa commit · commit khi ANALYSIS ký.

**Ảnh hưởng holdout**: baseline lock. Từ 20/09, mọi thay đổi entry phải added dưới dòng này.

---

<!-- Add entries below during holdout -->

## 2026-09-18 · pre-holdout · A5-5 · đăng ký lưới {w=3, w=2} × 4 ngưỡng

**Grid holdout-eval sẽ chạy ngày 21/10 khi hold-out đóng**:

- **Dimension 1**: BWD_WINDOW ∈ {2, 3}
  - w=3 = current spec letter (Δacc_bwd = (acc(D) − acc(D−3)) / acc(D−3))
  - w=2 = variant (khớp Tiên's ví dụ "3.6168/1.030" ở p85, tính từ D−2)
- **Dimension 2**: DACC_BELL_MAX ∈ {−10%, −15%, −20%, −30%} (AO pre-reg 4 cells)
- **Tổng**: 8 cells (2 × 4)

**Nội dung mỗi cell** (chạy 21/10, đo trên window 20/09 → 20/10):
- n_rings (đang-hedge dân số)
- n_hits (có cross UP trong 10d sau)
- precision
- lead_known median + % ≤0
- lift vs baseline 33.4% (từ AM1)

**Rule đóng cứng**: cells=8 · added=0 giữ nguyên. Không thêm ô nào sau khi thấy kết quả.

**Nếu w=2 precision KHÁC w=3 ≥5 pp trên bất kỳ ngưỡng nào**: 
- Đây là hint spec cần chọn w rõ · handover ANALYSIS ký chọn.
- KHÔNG tự chọn w tối ưu (post-hoc = fitting).

**Chuông ACC-BELL-A5-0 nào wire vào GOM-E trong holdout window (20/09 → 20/10)?**
- Trả lời: **KHÔNG WIRE** trong holdout window. Chuông ở [CALIBRATION-ONLY] state.
- Nếu wire giữa chừng → đóng holdout, mở lại từ ngày wire.

**Baseline probes trước holdout** (từ dữ liệu ≤ 2026-09-17):
- A4-1: DƯƠNG hedge 1/12 · ÂM 2/4 (sau bỏ cap: DƯƠNG 2/12, ÂM 3/4)
- A5-1 (A5-0 bỏ cap):
  - T=-20% · HEDGE (B) 2/6 = 33% · ÂM 5/8 = 62%
  - T=-15% · HEDGE (B) 3/6 = 50% · ÂM 5/8 = 62%
- SOPH · POWER · BASED · LIGHT · BROCCOLIF3B đều có chuông ÂM · noise chưa lọc được

**Ghi chú**: Nếu tape 20/09-20/10 mang thêm ≥3 proven hedge case mới (BULLA vòng 2, KOMA breakout, v.v.) → mở lại re-fit khi n_CONFIRMED ≥ 10 (per A3-4).

## 2026-09-18 · AA0 · đóng vòng A5-A9 · KHÔNG WIRE

Ba mục rút từ A5-A9 (chi tiết trong `docs/handover/dev_review_log_a5_a9_close_20260918.md`):

1. **acc-drop + pos-rise = mô tả chuyện thường ngày** — random baseline 83% chạm cả hai vs proven 100%. Delta 17 pp. Cùng bài LR-10 (acc sập = xác nhận, không lead). **RÚT khỏi mọi vế**.
2. **U0-BELL scope = nhánh B** (hedge → unhedge). 5/17 đợt proven cover · 10/17 chưa-hedge thuộc A/C/D → chuông của chúng KHÔNG ở div-cross. **KHÔNG mở U0 sang A/C/D**.
3. **Đợt 2+ CHƯA ĐO ĐƯỢC** · n=5 sau gộp WL-EPISODE. KHÔNG kết luận, KHÔNG bác bỏ.

**Sổ đợt canonical** = 13 (sandbox/u0_bell_a3/episodes_canonical_20260918.md). Pre-merge 17 giữ để đối chiếu, đánh dấu `[PRE-MERGE]`.

**Ba câu 27/09**:
- U0-BELL = chuông nhánh B · T=−20% · CALIBRATION-ONLY · hold-out 21/10
- U1 = v2∧v1 · n_CONFIRMED=5 · mở lại khi ≥10
- A/C/D đi kênh riêng (H2b · A1 · H1-OUT · kho-ramp), không ép qua LSR-div

**Trạng thái wire**:
- U0-BELL: **KHÔNG WIRE**. Sandbox giữ nguyên.
- Live `scripts/species_tag.py` md5 `a9a134df7ec175cd50a7e2833ddccc4e` không đổi.

**Grid 8 ô khoá đến 21/10** (không đụng gì tới 20/10):
- w ∈ {2, 3} × threshold ∈ {−10%, −15%, −20%, −30%}
- cells=8 · added=0 (invariant)

**Rule ghi thay đổi trong hold-out**:
Mọi thay đổi chạm `div_avg3` · `acc/pos source` · `universe` · `tagger` phải append entry dưới với: ngày · component · git sha · files · sanity check · ảnh hưởng holdout.

## 2026-09-19 · AB0 · U0-BELL AUDIT-ONLY wired

**Chữ Tiên 19/09**: wire U0-BELL ở mức AUDIT-ONLY, giữ hold-out sạch.

**Files wire**:
- `scripts/u0_bell.py` · md5 `baa8f525a8c03c2d183351f7fe64ba8c` (copy từ sandbox A3.1' + HOLD-OUT rail comment đầu file)
- `scripts/u0_bell_audit.py` · md5 `5c94b6ba283ef0282e8a8d9c0a8ef1a3` (runner đọc universe · in stderr · append jsonl · HOLD-OUT rail)
- `scripts/master_preview_send.py` · md5 `f1e97879dbfa9ced1675dfe8cba75956` (thêm call `run_audit` sau step concat-seal · trước idempotent-check)

**Git sha baseline**: `d14bf6554d3a` (pre-wire · sẽ commit sau khi SCP xanh)

**Rào HOLD-OUT (viết trong code)**:
```
# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
```
Ghi ở đầu 2 file `u0_bell.py` và `u0_bell_audit.py`.

**Kết quả wire (AUDIT-ONLY)**:
- Body bản tin **KHÔNG đổi 1 byte** (pin p36 6/6 PASS)
- Audit ghi ra:
  - stderr per token có BELL/NEAR/BLIND
  - `data/logs/u0_bell_audit.jsonl` (append-only)
- Log tổng đêm: `[U0-BELL-COUNT target=<T> · n_bell=<n> · n_near=<n> · n_blind=<n>]`

**Sanity check (dry-run 6 đêm sandbox)**:
```
target       body_md5_before body_md5_after  match   n_bell  n_near n_blind
2026-09-12   d92d91a6d8f7    d92d91a6d8f7    PASS    7       9      0
2026-09-13   2b38e90cda80    2b38e90cda80    PASS    2       2      0
2026-09-14   964fe32d9b7b    964fe32d9b7b    PASS    1       0      0
2026-09-15   619af47e92ed    619af47e92ed    PASS    1       0      0
2026-09-16   319331e97926    319331e97926    PASS    0       1      0
2026-09-17   3933847f4cfe    3933847f4cfe    PASS    3       1      0
```
Tất cả 6/6 body_md5 khớp trước/sau.

**Ảnh hưởng holdout**: **KHÔNG** — audit-only, không đọc để tune, không chạm body. File `data/logs/u0_bell_audit.jsonl` sẽ tích luỹ dữ liệu cho grid 8 ô đọc lại ngày 21/10.

**Chốt cấm**: mọi decision ngưỡng {w, T} dựa data từ `u0_bell_audit.jsonl` trong window 20/09-20/10 = VI PHẠM hold-out. File này CHỈ được đọc từ 21/10.

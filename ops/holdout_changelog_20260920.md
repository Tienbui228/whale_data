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

## 2026-09-19 · AE0-3 · Tiên nhìn khối U0-BELL trên bản tin

**Chữ Tiên 19/09**: bật khối UNHEDGE vào thân bản tin (AD1 format · CAL-ONLY).

**Ghi rõ vào sổ hold-out**:

> "Tiên đã NHÌN các đêm ≥ 20/09 (bản tin bật U0-BELL); không dùng để chỉnh."

**Ý**: Tiên đọc được khối UNHEDGE trong bản tin từ đêm cron đầu 21/09 (target 09-20)
xuyên hold-out (20/09 → 20/10). **Việc NHÌN** dữ liệu không phải là vi phạm hold-out.
**Việc CHỈNH** ngưỡng {w, T, các cap} dựa vào những gì đã nhìn được TRƯỚC 21/10 = VI PHẠM.

Grid 8 ô đã khoá `{w=2, w=3} × {−10%, −15%, −20%, −30%}` giữ nguyên · chạy ngày 21/10.

## 2026-09-19 · AE0-4 · Detector C wire audit-only

**Files**:
- `scripts/c_detect_audit.py` · md5 `7ec86f5682c5abfb9ac860a58e0c8737` · SCP xong · AST OK
- Rào HOLD-OUT trong comment đầu file
- Log path: `data/logs/c_detect_audit.jsonl` (append-only)
- Nguồn spec: S1 c1-c6 (sha 298bf565, per sổ · KHÔNG tự đặt số)

**Pin p38 · 3/3 PASS** (`_probe_p38_c_detect_20260919.py`):
- p38-a · blind → không tính, không giả vờ đạt · PASS
- p38-b · dữ liệu đủ → k=3 · PASS
- p38-c · lint dead-leg (PASS ∧ value=None) · PASS

**Live test AKE/BTW/UAI-C quanh D0 · k/6**:
```
AKE D0=07-15    · k=1/1/1/0 (D-7/-3/0/+3)
BTW D0=08-03    · k=2/2/2/1
UAI D0=08-24    · k=3/3/2/1
UAI D0=07-07    · k=3/2/2/1
```
Max k = 3/6. Sensitivity thấp — chờ ≥10 dương ∧ ≥10 âm mới đọc lại (per AE0-4 rule).

**Trạng thái**: KHÔNG vào bản tin · KHÔNG seed · KHÔNG ngưỡng ký.

## 2026-09-19 · AE0-2 · ERRATA GOM-E scanned vs universe_gen

**File**: `proposals/ERRATA_gome_scanned_vs_universe_gen_20260919.md`

**Nội dung**: `scanned=k/228` TÁCH khỏi `universe_gen=228`. Hai số hai nghĩa,
không đứng chung ô. Cấm gộp thành `k/N universe_gen=N`.

Chờ ANALYSIS niêm → apply vào GOM-E spec.

## 2026-09-19 · H · SỬA MISMATCH Opt-A ↔ verdict · retro-audit 4 đêm SKIP

**Root cause 4 đêm SKIP** (09-15 → 09-18):

**Opt-A** (commit `bf115ed` · KÝ 18/09 · handover session cũ):
- `digest_daily_vps.py` đổi target fresh/exch từ D-1 sang D (today snapshot)
- Artifact dump: `tg_final_fresh_digest_<snap>.txt` với `snap = today` (Opt-A shift +1)
- Log grep marker: `snapshot=<today>.json`

**BUG**: `compute_night_verdict(target=T)` cũ:
- Grep `snapshot=T.json` (T = master target = today-1) → **Opt-A đã shift sang T+1** → miss
- Check `tg_final_<r>_<T>.txt exists` (T = master target) → **artifact tên là T+1** → miss

Kết quả: `fresh_digest` và `exch_digest` cả 2 fail SENT + fail full_pair → `n_full=4/6, n_sent=4/6` → verdict **KÍCH** cả 4 đêm.

**FIX H · ký 19/09**:
- `scripts/digest_daily_vps.py` (md5 `d3a53a2ea1b0ea6a9f04ad27f44b177e`): thêm marker canonical `[LEG-SENT renderer=X snapshot=<snap> md5=<...> ts_utc=<...>]` sau send OK
- `scripts/master_preview_send.py` (md5 `888686680eea43addf718cf535d669b4`):
  - LEG-SENT detection · ưu tiên marker · fallback legacy `[SENT] X ok=True` với ts prefix
  - Window = 25h TRƯỚC `cron_close = target+1d 01:46 UTC` (không dùng `now`)
  - Full_pair check cho fresh/exch: `_has_recent_artifact(renderer, 25h)` glob file với mtime trong window (không match filename target)
- Pin p42 · 3/3 PASS (Opt-A shift · shift lần nữa · outside window)

**Retro-audit 4 đêm SKIP với logic mới**:
```
target       verdict         full   sent   missing
2026-09-15   KHÔNG-KÍCH      6/6    6/6    []
2026-09-16   KHÔNG-KÍCH      6/6    6/6    []
2026-09-17   KHÔNG-KÍCH      6/6    6/6    []
2026-09-18   KHÔNG-KÍCH      6/6    6/6    []
```

**Xác nhận đúng nguyên nhân**: Opt-A mismatch verdict logic · 4 đêm KHÔNG do wire khối B / U0-BELL / detector C. Sau H fix, cả 4 đêm sẽ ra KHÔNG-KÍCH.

**Ghi bổ sung Opt-A 18/09 (lẽ ra ghi hôm ấy)**:
- 2026-09-18 · Opt-A commit `bf115ed` · `scripts/digest_daily_vps.py` shift target snapshot D-1 → D
- Chạm nguồn: `data/logs/digest_daily_vps.log` marker format · `data/artifacts/tg_final_fresh_digest_*.txt` filename convention
- Hệ quả: **4 đêm SKIP** (09-15 → 09-18) do verdict không đọc được leg fresh/exch với target-name mới
- Fix trong H session 19/09.

**Verdict epoch retro giữ nguyên** (V3.5q ĐIỂM-THI-BẤT-BIẾN · epoch stamp original). Live compute mới ghi forensic-note với `verdict = epoch verdict` (unchanged), `verdict_at_stamp = <old KÍCH>`.

## 2026-09-19 · AE0-1 · Khối B ba tầng · ĐO NGÂN SÁCH · CHỜ WIRE

**Budget dry-run 6 đêm** (`sandbox/u0_bell_a3/ae0_1_bblock_3tier_probe.py`):

```
target     old_B   new_B   delta   body_after   tier
09-12      559     224     -335    3526         T0 no-cut
09-13      588     258     -330    3433         T0 no-cut
09-14      598     260     -338    3446         T0 no-cut
09-15      632     259     -373    3427         T0 no-cut
09-16      615     265     -350    3408         T0 no-cut
09-17      640     297     -343    3454         T0 no-cut
```

**Không đêm nào chạm 4096** ★. Delta trung bình **-343 chars/đêm** (khối mới gọn hơn nhiều).

**Chưa wire live** vì cần logic runtime để xác định CONFIRMED/FAILED per token per night
(hiện chỉ hardcoded cho 09-17 test). Chờ Tiên chọn approach:
- (a) Pilot với hardcoded set cho tuần đầu
- (b) Dựng state tracker (bell_journal query + U1 D+5 eval history)

## 2026-09-19 · AE0-5 · Bảng AA4 cổng đếm dương/âm cho 27/09

**File**: `_probe_ae0_5_gate_count_20260919.py`

```
gate         n_pos   n_neg   ≥5?
H2b          4       10      pos THIẾU 1 · neg ✓
H1-step      3       9       pos THIẾU 2 · neg ✓
H1-ramp      1       4       pos THIẾU 4 · neg THIẾU 1
kho-ramp     3       0       pos THIẾU 2 · neg THIẾU 5 (N/A · cần Nansen slice)
```

**Không cổng nào đạt ≥5 mỗi phía**. Cấm mượn âm chéo cổng đã áp.
Cổng gần nhất "đo lại được" = H2b (thiếu 1 pos).

Chỉ đếm · KHÔNG precision · KHÔNG ngưỡng.

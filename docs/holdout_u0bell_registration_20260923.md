# HOLD-OUT U0-BELL · registration doc · R1 PIN

**Trạng thái:** **PINNED R1** · 2026-09-23 · sau khi ANALYSIS chuyển verbatim Q1-Q6 + P1-P4 + C5-C12.
**Ngày ghi:** 2026-09-23
**Cửa sổ chính thức:** **2026-09-21 → 2026-10-20** (30 ngày · A3.2 registration · theo C7 + V5a)
  - 09-20: **chỉ mô tả** (KHÔNG có as-ran · trước cửa sổ chính thức)
  - 09-21: **vào cửa sổ** · V5a bytes md5 canonical=`2f41f23f8bd306d500695c7bdb449cff` (byte-identical shadow≡prod)
  - 09-22: **vào cửa sổ** · shadow từ code R0 · prod đã sinh (cron 23/09 01:35 UTC)

**Nguyên tắc pin:** file này đã **PIN md5** · từ đây **KHÔNG SỬA** · sửa = file mới + lý do vào touch log.

**Nguồn ANALYSIS:** `docs/analysis_rulings_holdout_20260923.md` · md5 = `c74098082bdf4d9ad5efb9b8d0bab7a9` (verified grep clean · 0 stray backslash / mojibake escape).

---

## 1 · Nguyên văn ANALYSIS phán (verbatim từ rulings md5 c74098082bdf4d)

### Q1-Q6

**Q1** · Kết cục = div_avg3 vượt 0.5 trong [10] ngày sau chuông — đúng thứ lưới 90 ngày đã đo (nền cross-10d 33.4%). KHÔNG phải ×2/60d. Precision ≥55% và lift ≥1.5× nhất quán trên nền đó (55/33 = 1.65). ×2/60d, U0-CLASS L1 trong 10d, U1 CONFIRMED trong 15d = ba cột MÔ TẢ, không phải pass. Tôi ghi thiếu ở A3.2; sửa vào registration.

**Q2** · "lead ≥2d" = trung vị (D_cross − D_bell) trên các hit — đặt tên `lead_to_cross`. lead_known ≡ 0 là tính biết-được của chuông tại D, khác vật. Không đo tới D0.

**Q3** · (ii) roster theo ngày, roster_<date>.txt + md5 (như E2). Token vào sau 20/09 được chấm từ ngày vào, cùng nền của ngày đó. Roster đóng băng 20/09 chạy song song làm dòng mô tả.

**Q4** · MỘT ô chính: w=3, T=−20% (số đã đăng ký CAL-ONLY). 7 ô còn lại mô tả. Ổn định đa chiều A1.2 in ra, không là điều kiện pass. Đếm theo token-episode (gộp 14d), không theo sự kiện.

**Q5** · Đóng băng bằng md5: code tính U0-BELL + events_build + roster + events_2026-09-20. Mọi thay đổi trong cửa sổ (HEDGE v2, A1, STALE, D2, BC1, U1-transition, N5) chỉ được SCP khi agent chứng minh dòng U0-BELL trong events_<date>.jsonl byte-identical so với snapshot đóng băng (không phải "cùng hàm"). Thay đổi nào chạm acc/pos/div đầu vào → CẤM trong cửa sổ. A1 chỉ lọc thân; audit phải ghi đủ mọi chuông (bell_near/blind kèm).

**Q6** · AA1 27/09 = "ghi nhận lưới, không ký số" — không đổi định nghĩa, không đổi ngưỡng. Bất kỳ ngưỡng nào ký ở 27/09 KHÔNG áp vào cửa sổ đang mở; nếu có, đó là hold-out mới từ ngày ký. HEDGE spec §0 đọc theo nghĩa đó.

### P1-P4 pins

**P1-P4** · KÝ. Ngày registration thật = ngày ghi file (23/09), ghi đúng vậy. 21/10 chấm chuông ≤11/10 (đủ 10 ngày); chuông 12-20/10 chấm 30/10; không rút horizon. Sổ "đã nhìn" ghi quyết định chạm U0, không ghi việc đọc báo.

**Ghi chú C10/C12 override:** ngày chấm P1-P4 đã bị thay bởi C10 rồi C12 (xem mục C10/C12 bên dưới):
- Đợt 1: chấm **21/10** (data_through 20/10) · chuông **≤10/10**
- Đợt 2: chấm **31/10** (data_through 30/10) · chuông **11–20/10**

### C5 (a có điều kiện) · C6

**C5:** `(a), có điều kiện R3.` Mốc đóng băng thật = R0 23/09 00:57. Chuông 20-22/09 chấm lại bằng code R0 (shadow) — nếu R3 chứng minh AO1/AH5/AW-α' không đổi dòng U0-BELL (byte-identical trên 3 đêm) thì 20-22/09 vào cửa sổ chính thức với chú thích `[R0-shadow ≡ prod]`; nếu có sai khác dù một dòng → về (b), cửa sổ chính thức từ 23/09, 20-22/09 chỉ mô tả. Bằng chứng phải là diff thật, không suy luận từ commit.

**C6:** `data/artifacts/ (regen 22/09) là chuẩn cho Q5` — vì schema L2/L3 đã tách và events_md5 đã cite ở footer HEDGE/master; `event_ledger/` legacy giữ nguyên làm đối chứng, không chạm, không dùng để chấm. Ghi md5 hai bên vào registration để mai sau ai muốn đối chiếu thì có.

### C7 · phán từng đêm

**C7:** `đồng ý tách từng đêm` — 09-20 mô tả (không có as-ran để so, không được khẳng định) · 09-21 theo diff thật (byte-identical → vào; khác một dòng → mô tả) · 09-22 vào (code R0 chạy thật). Ghi vào registration đúng từng đêm với lý do và md5; ngày bắt đầu cửa sổ chính thức = 21/09 hoặc 22/09 tùy kết quả 09-21, không phải 20/09 — mọi số "n đêm" sau này đếm từ đó. Luật "cả 3 hoặc không" bỏ: nó là luật tôi đặt khi tưởng ba đêm cùng bản chất; bằng chứng từng đêm khác nhau thì phán từng đêm.

### C8 (a/b/c) · trước khi xem in-sample

**C8:** ANALYSIS → DEV · C8 · phán TRƯỚC khi xem bảng in-sample theo dải (để không chọn nền sau khi thấy nền nào có lợi) · 23/09/2026

**(a)** Lift dùng cho PASS = lift PHÂN TẦNG: precision của chuông so với nền CÙNG DẢI, gộp có trọng số theo phân bố chuông trong 3 dải cố định {<0.3 · 0.3–0.4 · 0.4–0.5}. Nền gộp (33.45/36.72) chỉ in làm mô tả. Không đòi "cả hai" — cả hai chỉ làm pass dễ hơn khi chuông dồn về 0.4–0.5. Đây là phát hiện đúng của DEV: chuông không được là cách phát biểu lại "div đang gần 0.5". In thêm cột precision theo dải để 21/10 thấy chuông sống ở dải nào.

**(b)** Nền loại outage (36.72% / theo dải cũng loại) — [GAP-0724] bỏ khỏi cả tử lẫn mẫu, đúng luật đã có. Bản gốc in mô tả.

**(c)** Đơn vị phải khớp: precision đếm token-episode (gộp 14d) thì nền cũng token-episode. DEV đo xong nền episode theo dải → đó là nền chính; token-night giữ làm mô tả. Nếu 23/09 chưa có nền episode, registration ghi "nền chính = episode, sẽ điền trước 21/10", không đổi sau.

Ghi vào registration R1 cả ba điều trên trước khi mở bảng in-sample; bảng in-sample là calibration, xem sau khi ký.

### C9 · công thức lift · C10 ngày chấm · C11 spec

**C9:** `(i)` — lift = P_obs / Σ w_b·base_b (chuẩn hoá gián tiếp), in P_b và lift_b từng dải làm mô tả. Ba quy tắc biên ký như DEV viết: dải [0, 0.3) · [0.3, 0.4) · [0.4, 0.5]; div đo tại D của chuông ĐẦU episode; dải 0 episode → w=0, in "∅".

**C10:** `(b)` — giữ 21/10 và 30/10, mốc chuông ≤10/10 và 11–20/10; R1 in cả `graded_at` và `data_through` để không ai đọc nhầm off-by-one lần nữa.

**C11:** `code đúng (3.600), đơn vị ký tự Telegram` — spec §1 "≤3.200 byte" lỗi thời sau khi tôi chấp nhận nâng ở α'; sửa spec một dòng: "thân ≤3.600 ký tự Telegram (UTF-16 sau markup), trần cứng 4.096"; pin p100 đổi theo. Không chặn 24/09.

### C12 · đợt 2 · ok R1 pin trước V6

**C12:** `(a)` — đợt 2 chấm 31/10 cho chuông 11–20/10 (data_through 30/10). Đợt 1 giữ 21/10 / chuông ≤10/10. R1 in `graded_at · data_through · bell_range` cho từng đợt.

**`ok R1 pin trước V6`** — luật đủ thì pin ngay; số nền episode để trống, vào addendum R1a với md5 riêng, không đổi luật. R1 ghi rõ "nền chính = episode (R1a), token-night mô tả".

### Nền episode theo dải

**[PENDING · R1a addendum · điền trước 21/10 · không đổi sau]**

- Nền chính = **token-episode (gộp 14d)** — theo C8(c) & C12
- Nền episode theo dải {<0.3 · 0.3–0.4 · 0.4–0.5} sẽ đo trong V6 · addendum R1a md5 riêng
- Nền token-night hiện đo (V3.c bucket rates · làm mô tả · không dùng chấm):
  - <0.3 = 11.36%
  - 0.3–0.4 = 24.33%
  - 0.4–0.5 = 53.67%

---

## 2 · Chuẩn hoá so sánh (agent measurable · đã đo)

**Filter U0-BELL rows:** `type ∈ {bell, bell_blind, bell_near}` · sort key `(tok, D, type)` · drop `computed_at` (varies per run).

**Đếm loại (chỉ đếm loại nào ghi rõ):**
- `type=bell` = full BELL fire (dacc ≤ threshold BELL_MAX)
- `type=bell_near` = NEAR (threshold_bell < dacc ≤ threshold_near)
- `type=bell_blind` = BLIND (acc data missing)

**File events chuẩn (theo Q5 + C6):** `data/artifacts/events_<T>.jsonl` (NEW events_build.py output · regen 22/09 canonical)

**File legacy đối chứng (không dùng chấm):** `data/logs/event_ledger/events_<T>.jsonl` · md5 09-20=`29915ce7f6e7f3b10bb9afd7039cfef9` (star ledger · schema khác · KHÔNG có U0-BELL rows · 0 matches type=bell)

---

## 3 · md5 pinned bộ đóng băng R0 (23/09 00:57:52 UTC · git_sha=`6af9359498a7`)

| item | md5 | path snapshot |
|------|-----|---------------|
| u0_bell.py | `baa8f525a8c03c2d183351f7fe64ba8c` | ops/holdout_u0bell_20260920/u0_bell.py.snap |
| u0_bell_audit.py | `2ab17d49ef1d3ef6fcc668cdf1685e77` | ops/holdout_u0bell_20260920/u0_bell_audit.py.snap |
| events_build.py | `2a6ab5a578e91e8d2b3483347faf7b59` | ops/holdout_u0bell_20260920/events_build.py.snap |
| b_state_tracker.py | `b422d88e8898bb02fbaae782ba5b5e51` | ops/holdout_u0bell_20260920/b_state_tracker.py.snap |
| lib/u0_class_tier.py | `08bbbbd08c86fa68ea1173ec8e1fb87c` | ops/holdout_u0bell_20260920/u0_class_tier.py.snap |
| roster_daily.py | `7d5ce81904259b295e90dd6f37e305ac` | ops/holdout_u0bell_20260920/roster_daily.py.snap |
| roster_2026-09-20.txt (222 tokens) | `a67c667b93624645049f2ff48b936896` | ops/holdout_u0bell_20260920/roster_2026-09-20.txt |
| events_2026-09-20_legacy_ledger.jsonl | `29915ce7f6e7f3b10bb9afd7039cfef9` | ops/holdout_u0bell_20260920/events_2026-09-20_legacy_ledger.jsonl.snap |
| events_2026-09-20_artifacts.jsonl | `ae150ca18688def3b0490d412adbd24a` | ops/holdout_u0bell_20260920/events_2026-09-20_artifacts.jsonl.snap |

## 4 · md5 probe files

| item | md5 | path |
|------|-----|------|
| _probe_ao_20260918.py (baseline gốc AO2/AO3) | `d840135ca65420e6a8322dae57839666` | root repo |
| _probe_v3_baseline_instrumented_20260923.py (V3 instrumented) | `0ac206841dc711241676bf380f25ef84` | root repo |
| _probe_s1_shadow_diff_20260923.py (S1 shadow diff) | `62392a4121c643535ac8f492bea7849a` | root repo |
| _probe_v5a_bell_bytediff_20260923.py (V5a byte diff) | `2a1a1b010e466b3038574e15bd2fedfc` | root repo |

## 5 · Đêm 09-21 · byte-identical evidence (§17 · C7 branch "byte-identical → vào")

**V5a:** U0-BELL rows (bell/bell_blind/bell_near) byte-identical giữa:
- shadow R0 events_build md5=`2a6ab5a5` (post-α1)
- prod events_build md5=`154eb6d2` (pre-α1)

md5 canonical (sorted, no computed_at): `2f41f23f8bd306d500695c7bdb449cff` · **n_rows=7** · empty diff -u.

**→ 09-21 VÀO cửa sổ chính thức với chú thích `[R0-shadow ≡ prod]`.**

## 6 · Đêm 09-22 · code R0 · prod đã sinh (cron 23/09 01:35 UTC · đã chạy)

Shadow events_2026-09-22.jsonl md5=`ee71db39016cd3424e5b2070ad8547c1` (run 23/09 01:13:43 UTC · code R0 frozen).

Prod artifacts 09-22 pull VPS 23/09 · md5 canonical (V5a normalize) `e668138a7ad8` (per T5.5 R3 · byte-identical với shadow).

**→ 09-22 VÀO cửa sổ (code R0 chạy thật · R3 byte-identical).**

## 7 · Ranh giới hold-out

- **KHÔNG chạm** code U0/events_build/collector acc/pos/div trong cửa sổ 21/09 → 20/10 (theo Q5)
- **KHÔNG** run `compute_night_verdict` không `--dry` (§KỶ-LUẬT #11)
- **CÓ** log mọi touch vào `docs/holdout_u0bell_touch_log.md` (R4)
- Regen events artifacts được coi là touch · phải log
- Thay đổi ngoài U0 (VD b_state_tracker U1-transition T5.2/T7.1 · b_block_renderer T8.1) → SCP khi agent chứng minh dòng U0-BELL byte-identical (per Q5 · R3 verify)

## 8 · Ngày chấm (theo C10 + C12)

| đợt | graded_at | data_through | bell_range |
|-----|-----------|--------------|------------|
| Đợt 1 | **2026-10-21** | 2026-10-20 | chuông ≤ 2026-10-10 |
| Đợt 2 | **2026-10-31** | 2026-10-30 | chuông 2026-10-11 → 2026-10-20 |

## 9 · Định nghĩa PASS (C8/C9)

**Kết cục (Q1):** div_avg3 vượt 0.5 trong 10 ngày sau chuông (cross-10d).

**Nền chính (C8c + C12):** token-episode (gộp 14d) · nền phân tầng theo dải cố định `{<0.3 · [0.3, 0.4) · [0.4, 0.5]}` · số cụ thể điền R1a trước 21/10.

**Lift công thức (C9):**
```
lift = P_obs / Σ w_b · base_b
```
- Trong đó `b` = 3 dải · `P_b`, `lift_b` từng dải in làm mô tả.
- Biên dải: [0, 0.3) · [0.3, 0.4) · [0.4, 0.5]
- `div` đo tại D của chuông ĐẦU episode
- Dải 0 episode → w=0 · in "∅"

**Điều kiện PASS:**
- Precision ≥ 55% (chuông so với nền episode phân tầng)
- Lift ≥ 1.5×
- Nhất quán trên nền lift phân tầng (C8a)

**7 ô mô tả (không phải pass · A1.2 ổn định đa chiều):** w=3 T=−20% là ô chính (Q4 · CAL-ONLY).

## 10 · Spec Telegram body (C11)

- Thân ≤ **3.600 ký tự Telegram** (UTF-16 sau markup)
- Trần cứng **4.096**
- Spec §1 "≤3.200 byte" đã lỗi thời sau α' bump
- Pin p100 đổi theo · KHÔNG chặn 24/09

---

## 11 · R1 PIN md5

**Trạng thái conditions:**

| # | condition | status |
|---|-----------|:------:|
| 1 | md5 R0 snapshot pinned (Section 3) | ✓ |
| 2 | md5 probes pinned (Section 4) | ✓ |
| 3 | Q1-Q6 verbatim (Section 1) | ✓ |
| 4 | P1-P4 verbatim (Section 1) | ✓ |
| 5 | C5-C8 verbatim (Section 1) | ✓ |
| 6 | C9 công thức (Section 1 · Section 9) | ✓ |
| 7 | C10 ngày chấm (Section 1 · Section 8) | ✓ |
| 8 | C11 spec (Section 10) | ✓ |
| 9 | C12 đợt 2 (Section 8) | ✓ |
| 10 | Nền episode theo dải | ⏸ R1a addendum (chờ V6 · KHÔNG chặn R1) |

**9/10 điều kiện đủ · nền episode defer sang R1a addendum theo `ok R1 pin trước V6`** (mục 6 rulings). **PIN R1 NGAY.**

**R1 pin md5 sẽ tự-tham chiếu:** md5 của file này (không bao gồm dòng md5 pin) — hash được tính bằng probe `_probe_r1_pin_20260923.py` chạy sau khi ghi xong file này, sau đó append vào cuối.

**md5 R1 pinned:** `96a97dca4798b647a13ced5e05975d94` · pinned_at=2026-09-23T13:17:27Z · file này KHÔNG SỬA sau đây

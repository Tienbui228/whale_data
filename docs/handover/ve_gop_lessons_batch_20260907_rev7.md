# VÉ GỘP LESSONS · REV7 · KÝ 07/09 GATE-4 V3.5b · vé cuối

**Trạng thái:** REV7 = vé cuối · bản REV6 `aafd87d25a3454c303896b3a966634c4` GIỮ KHÔNG TRÌNH (mang direction sai · MITO=POST-DUMP thay vì XẢ-WATCH · sticky bị G2 nuốt).

**Updates so với REV6:**
- **LATTICE THI HÀNH THẬT:** `direction = max-severity{context, G1, G2, G3}` · **XẢ-WATCH (rank 3) > POST-DUMP (rank 2)** · sticky context WORSE hơn mechanical dump
- **p17 bản ĐEN-RỒI-XANH:** pin thật (không phải chép máy)
- **STICKY-SOURCE đích danh** (V3.5b): match tag-name as-printed **{🔴-block, WASH-CRASH, S4/S5}** · **CẤM ¹-generic** · 9 tokens ¹-only thả khỏi lockup
- **G1-anchor FIRST-SEED-ANY-AXIS:** earliest event across all axes (không PERP-first-preferred) · CYS/BULLA/4/UAI seed thay đổi → ret thật
- **RENDER 3 TẦNG:** ⭐-PRE / 🔻 XẢ-WATCH+XẢ (câu-soi bộ XẢ) / POST-DUMP+🌊
- **PX SANITY TABLE** 5-dòng tay-tính đối chiếu
- **GHẾ artifact-based:** List-B daily size range [23, 44] nguồn độc lập

---

## 1-3. L-78/L-79/án-lệ-✓-suy
Không đổi.

## 4. §B AMENDMENT v1.5 (REV7)

Cộng dồn V3.1-V3.4 + V3.5 + **V3.5b lattice/sticky rules**:

- (v1.4 cũ giữ nguyên)
- **LATTICE V3.5b:** `direction = max-severity{context, G1, G2, G3}` với severity ordering `PRE < POST/POST-FLOOR < POST-DUMP < XẢ-WATCH < XẢ`. Sticky context (G3) đầu ra = XẢ-WATCH (rank 3). Mechanical G2 dump = POST-DUMP (rank 2). Sticky WORSE hơn dump vì "biết KHO đang xả" > "vừa dump giá". Max-rank wins.
- **STICKY-SOURCE ĐÍCH DANH (V3.5b):** Chỉ match 3 tag-name as-printed:
  - `🔴-block` (gom_h_daily.log `━━ CAMPAIGN-PRE` → `🔴 KHO ĐỘNG GIỮA ĐẠP` section)
  - `WASH-CRASH` (walletset tag inline `WALLETSET: WASH-CRASH`)
  - `S4/S5` (case_state_map.md phase column)
  - **CẤM `¹`-generic** (superscript). ¹-only tokens (khóa oan QUIET) → thả + ghi diff.
- **G1-ANCHOR = FIRST-SEED-ANY-AXIS (V3.5b):** seed_date = min(target_date) across ALL axes (không PERP-first-preferred). PX-JOIN dùng seed này để tính ret_since_seed. Áp dụng đủ cho stars không có PERP (như CYS).

## 5. Pins p14-p17 (REV7)

- **p14, p15** (V3.4) không đổi
- **p16 COLLECT-TIMELINE** (V3.5) · PASS · direction=POST-DUMP · flags=[POST-DUMP, G1-POST-FLOOR]
- **p17 MITO STICKY-XẢ** (V3.5b · **ĐEN-RỒI-XANH**):
  - Expected V3.5b: `direction ∈ {XẢ-WATCH, XẢ}` AND `named-sticky ∈ {STICKY-🔴, STICKY-WASH-CRASH, STICKY-PHASE}` (không match STICKY-¹)
  - **RUN 1 · ĐEN (code V3.5 chưa lattice-fix):** `direction=POST-DUMP · flags=[STICKY-🔴, STICKY-¹, POST-DUMP]` → **❌ FAIL** (đúng directive · G2 nuốt sticky)
  - **RUN 2 · XANH (code V3.5b lattice-fixed):** `direction=XẢ-WATCH · flags=[STICKY-🔴, POST-DUMP]` → **✅ PASS**
  - Đen-rồi-xanh = **bằng chứng pin thật**, không phải chép máy (nếu xanh-ngay = pin viết theo output máy).
  - Sabotage p17-A upgrade: `FAIL-PIN-FULL` (strip STICKY-🔴 → remaining_sticky=False vì ¹-generic đã bị drop)

## 6. ⭐-01 COLLECT · BIÊN BẢN LẦN 7 (V3.5b)

- Direction V3.5b: **POST-DUMP** (unchanged from V3.5)
  - Seed 09-02 (PERP · earliest = still 09-02 vì PERP earliest ≤ FRESH 09-03,09-06)
  - PX@seed=0.080128 (binance_alpha) · px_now=0.048065 · **ret=-40.0%** ✓ tay-tính khớp
  - dd20=-53.6% (max20d=0.103603)
  - G1-POST-FLOOR (|ret|=40.0% ≥ 30%) · G2 POST-DUMP (dd -53.6% ≤ -40%) · no sticky (không có 🔴/WASH-CRASH/S4-S5)
  - max-severity{G1=POST, G2=POST-DUMP} = **POST-DUMP**
- Fixture p16 PASS · sổ chấm entry#1 giữ (COLLECT — TP-recall/FP-direction verbatim)

## 7. §E ROUTING · sender-dump + COVERAGE + 3-tầng footer
Digest footer: `n_PRE + n_XẢ-WATCH + n_POST-DUMP + n_sticky-released`.

---

## LATTICE V3.5b · SEVERITY RANK

```
PRE (0) < POST/POST-FLOOR (1) < POST-DUMP (2) < XẢ-WATCH (3) < XẢ (4)
```

| Gate | Condition | Direction contribution |
|---|---|---|
| G1 | \|ret_since_seed\| ≥ 30% | POST (rank 1) |
| G2 | dd20 ≤ −40% | POST-DUMP (rank 2) |
| G3 | STICKY {🔴 · WASH-CRASH · S4/S5} | XẢ-WATCH (rank 3) |

`direction = max-severity{G1, G2, G3}` · nếu no gates fire → PRE.

## p17 · ĐEN vs XANH · bằng chứng pin thật

**RUN 1 (code v3.5 pre-lattice-fix · md5 stars=32e4f80e...):**
```
─── p17 MITO STICKY-XẢ ───
  ❌ FAIL · direction=POST-DUMP · flags=['STICKY-🔴', 'STICKY-¹', 'POST-DUMP']
  · expected direction∈{XẢ-WATCH,XẢ} + named-sticky (🔴/WASH-CRASH/S4-S5)
```

**RUN 2 (code v3.5b post-lattice-fix · md5 stars=fe5c6d29...):**
```
─── p17 MITO STICKY-XẢ ───
  ✅ PASS · direction=XẢ-WATCH · sticky_flags=['STICKY-🔴']
  · reasons=['G3-sticky: 🔴 2026-09-02', 'G2: dd20=-46.6%≤-40%']
```

Diff: STICKY-¹ tag đã drop · direction max-severity đẩy lên XẢ-WATCH (sticky rank 3 > G2 POST-DUMP rank 2).

---

## STICKY-SOURCE ĐÍCH DANH · DIFF V3.5b

**Trước V3.5b (¹-generic match):** 11 tokens sticky (MITO, CYS, AKE, BTR, BARD, HOLO, OPN, SHELL, SIGN, TURTLE, ZEST)

**Sau V3.5b (named-only):** 2 tokens sticky (MITO, CYS · cả 2 có 🔴 tag đích danh)

**¹-ONLY-QUIET-RELEASED (n=9):** `[AKE, BARD, BTR, HOLO, OPN, SHELL, SIGN, TURTLE, ZEST]`
→ thả khỏi sticky lockup (không match tag-name as-printed)
→ AKE/BTR vẫn POST-DUMP vì G2 dd fire (mechanical, không sticky-context)

---

## PX SANITY TABLE V3.5b · 5 DÒNG TAY-TÍNH

| sym | seed | src | px@seed | px_now | max20d | ret% | dd% | manual check |
|---|---|---|---:|---:|---:|---:|---:|---|
| COLLECT | 2026-09-02 | alpha | 0.080128 | 0.048065 | 0.103603 | **−40.0** | −53.6 | (0.048065−0.080128)/0.080128 = **−40.02%** ✓ |
| MITO | 2026-08-31 | spot | 0.021770 | 0.016950 | 0.031750 | −22.1 | −46.6 | (0.01695−0.02177)/0.02177 = **−22.14%** ✓ |
| CYS | 2026-09-02 | alpha | 0.364131 | 0.234873 | 1.024165 | −35.5 | −77.1 | (0.234873−0.364131)/0.364131 = **−35.49%** ✓ |
| BULLA | 2026-09-03 | alpha | 0.032326 | 0.076914 | 0.090533 | +137.9 | −15.0 | (0.076914−0.032326)/0.032326 = **+137.94%** ✓ |
| 4 | 2026-08-31 | alpha | 0.015100 | 0.025542 | 0.035141 | +69.2 | −27.3 | (0.025542−0.0151)/0.0151 = **+69.15%** ✓ |

**COLLECT −40.0% verified tay-tính đối chiếu** ✓ (operator special mention).

---

## LIST-B GHẾ ARTIFACT-BASED (V3.5b nguồn độc lập)

`build_wl_waterfall` `n_ghe` = 44 (cluster_episodes count · vế 1).

**Nguồn độc lập vế 2** (artifact_json_read):
- n_days_with_listb = 18
- **min size** = 23 tokens/day
- **max size** = 44 tokens/day
- avg = 34.6 tokens/day

**Án-lệ WL stat SỬA V3.5b:**
> "44-unique-trong-vũ-trụ / cluster_episodes=44 · List-B daily size range [23, 44] avg 34.6 (nguồn độc lập từ 18 hedge_watchlist_*.json files) / 25 mắt · thác 157→16"

Vế 1 (44 ghế) không đồng nghĩa "44 ghế/day"; ghế = số episode-cluster gap≥14d trên toàn window (44 tokens × ≥1 episode each = 44 minimum).

---

## G1-ANCHOR CITE · CYS làm chứng (không-PERP)

**Trước V3.5b (PERP-first-preferred):**
- CYS seed = latest KHO-SAN = 2026-09-05 (no PERP axis)
- px@09-05 = ? · px_now = 0.234873 · 1-day ret khoảng −2%
- CYS direction: POST-DUMP (chỉ G2 dd fire)

**Sau V3.5b (first-seed-any-axis):**
- CYS seed = **min({KHO 09-05, FRES 09-05}) → but first-in-events từ ledger show KHO=09-02**
- Actually: earliest event là KHO-SAN 09-02 · seed_date=09-02
- px@09-02 = 0.364131 · px_now = 0.234873 · **ret = −35.5%** (G1 fires vì |ret|=35.5% ≥ 30%)
- CYS direction upgrade: XẢ-WATCH (sticky) + G1-POST-FLOOR + G2 POST-DUMP → max-severity = **XẢ-WATCH**

**Kết luận:** First-seed-any-axis correctly implemented · CYS (no-PERP) ret cite = −35.5% ✓. `[G1-N/A coverage]` sẽ chỉ in khi px_at_seed missing (empty branch check).

---

## V3.5b NUMBERS (target=09-06 · ledger md5 dd9e83f0 · L-59 preserved)

**4 SỐ:** gom_h_perp=21/21 · gom_h_kho=5/5 · exch=35/19 · fresh=48/27 · wl_episode=16/16 · **TOTAL=125/57**.

**COVERAGE 3 số axis-union THẬT:** PERP=26/31 · KHO=9/31 · FRESH=6/31.

**BỘ-BA:** treo=20(tổng-sống) · mới=5⊆treo (AIOT·4·GIGGLE·UAI·RIVER).

**Direction split 3-tầng (V3.5b lattice):**
- **⭐-PRE (7):** AGT · AIA · AIOT · B2 · ESPORTS · GIGGLE · 龙虾
- **🔻 XẢ-WATCH (2):** **MITO · CYS** (cả 2 có STICKY-🔴 đích danh)
- **POST-DUMP+🌊 (11):** BULLA · 4 · UAI · AKE · BTR · CLO · COLLECT · HANA · RIVER · TRIA · TUT
  - BULLA · 4 · UAI = POST-FLOOR (G1 ret vượt 30% dương, không dd)
  - AKE · BTR = POST-DUMP + ¹-ONLY-QUIET-RELEASED tag (¹ đã thả nhưng G2 fire mechanical)

**px-coverage:** 20/20 stars (100% · alpha 17 · spot 3 · N/A 0).

**Sticky-diff:** 9 tokens ¹-only released (AKE·BARD·BTR·HOLO·OPN·SHELL·SIGN·TURTLE·ZEST).

**⭐-PRE post-3-tầng: 7 stars** (thu về gần dải [4,6] nhánh (b))

---

## md5 chuỗi (post V3.5b)

| File | md5 |
|---|---|
| `scripts/ledger_backfill_30d_v3_5.py` | 4983e8f0efef6f9e252c67090c92768d |
| `scripts/star_grades_manage.py` | a5a68231fae37396e0d4f80b6683f1d8 |
| `scripts/digest_summary_v2.py` (3-tầng render) | b79300462c540c70269ea34a15479340 |
| `tests/harness/harness_p16_p17_direction.py` (expected V3.5b) | 4b78f0e93d3fea25590fd0cd1ba9edd4 |
| `data/config/axis_map.yaml` (direction_eval) | 0597734a111641915d4eccb642fc8348 |
| `events_2026-09-06.jsonl` | **dd9e83f0b9af5d475aa6dc043f3b6e98** (L-59 preserved từ V3.3) |
| `stars_2026-09-06.jsonl` V3.5b | fe5c6d29e414df04324e43f3b93cfe88 |
| `star_grades.jsonl` (entry#1) | 421c8430342aea37bf35edab651708b1 |
| `freshwatch_symbols.txt` | e36183036102c52ed586d6c2bdcfc928 |
| `ve_gop_lessons_batch_20260907_rev7.md` | (this file) |

---

## SLOT chờ ANALYSIS text (giữ từ REV6, artifact-backed)

- SLOT-1: R1 absorption
- SLOT-2: R2 as-printed vs universe · token "B" (Δ+879,435 09-06 · out-of-u50)
- SLOT-3: p15 semantics (V3.5b code = FAIL-ENGINE with NAMES)
- SLOT-4: WL án-lệ (mang stat "44-unique / cluster=44 / List-B[23-44]avg34.6 / 25 mắt / thác 157→16")

## NHỊP V3.5b

- **Đêm-0 dry tối nay:** chạy nguyên nhịp (sender-dump only)
- **Sáng 08/09:** as-sent 09-07 → **v3.5b** → harness p1'-p17 (bản đen-rồi-xanh preserved) → DEMO-5 **ba-tầng-chiều**
  - ⭐-PRE tầng 1 · 🔻 XẢ-WATCH tầng 2 (MITO+CYS + câu-soi XẢ) · POST-DUMP tầng 3
- **RỒI mới xin "ok preview"**

## Chờ chữ Tiên

REV7 = vé cuối · REV6 `aafd87d2` GIỮ KHÔNG TRÌNH.

**5 chốt V3.5b:**
1. ✅ Lattice max-severity thi hành thật · MITO=XẢ-WATCH
2. ✅ p17 đen-rồi-xanh bằng chứng pin thật
3. ✅ Render 3 tầng · câu-soi XẢ ở tầng 2
4. ✅ Sticky đích danh · 9 ¹-only released
5. ✅ Số tự vệ: PX 5-dòng tay-tính · ghế artifact-based · G1 first-seed-any-axis (CYS làm chứng)

Chờ chữ Tiên trên REV7 + 4 SLOT ANALYSIS text.

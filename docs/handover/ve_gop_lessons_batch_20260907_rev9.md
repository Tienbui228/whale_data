# VÉ GỘP LESSONS · REV9 · KÝ 07/09 GATE-4 V3.5f · vé cuối

**Trạng thái:** REV9 = **vé cuối** · bản REV8 `89ae70724e3f455386b8d9d4d230ef26` **SUPERSEDED**. Chờ Tiên "khớp REV9 <md5>".

**Updates so với REV8:**
- **FIX SORT DẢI-A THẬT** (V3.5f): sort by **star-birth-date** (2nd-axis-arrival) DESC · NOT first-seed
  - Trước (V3.5e sai): ESPORTS · 龙虾 · B2 (đội nhãn mới-nhất-trước bằng con CŨ nhất)
  - Sau (V3.5f xanh): GIGGLE 09-06 · AIOT 09-06 · 龙虾 09-05 ← khớp kỳ vọng operator
- **MERGE WL-ÁN-LỆ VERBATIM ANALYSIS** vào SLOT cuối (REV9 CLOSE)
- **LABEL-CLAIMS-LINT** wired + tuyển-dụng PASS (bắt orphan `pointer-integrity: OK`)
- **DOS-PACKAGE** doc drop (ghế 27/09)
- **HARNESS-LOG** canonical dump 17 rows đủ 4-field

---

## 1-3. L-78/L-79/án-lệ-✓-suy · không đổi

## 4. §B AMENDMENT v1.7 (REV9)

Cộng dồn V3.1-V3.5e + V3.5f:

- (v1.6 giữ nguyên · KEY-NORM · UNIVERSE · EPISODE×COVERAGE · EXPLICIT-PARSER · WATERFALL · p15 FAIL-ENGINE với NAMES · LATTICE max-severity · STICKY-đích-danh · G1-anchor first-seed-any-axis · PIN-TUYỂN-DỤNG · NGOÀI-SỔ counter · SỔ ĐỌC-ENFORCEMENT L-80 DRAFT)
- **FIX SORT DẢI-A (V3.5f):** dải-a top-N sort by **star-birth-date** DESC (khi có ≥2 axis), KHÔNG dùng first-seed (which is earliest event = có thể misleading). Label không đi trước data.
- **LABEL-CLAIMS-LINT (V3.5f wire · text tuần sau):** grep các nhãn CLAIM {sorted·sort:·✓·checked·verified·OK·PASS·đã-*} → hợp lệ chỉ khi trong bán kính k=5 dòng có phép-kiểm-in-được (`md5=X · n=Y · X==Y · <=/>=`) hoặc cite `[per <seal-id>]`. Nhãn mồ côi = lint-FAIL cửa merge.

## 5. Pins p14-p17 (REV9)

- **p14 DẢI-KÉP (V3.5d/f)** — chân-a `n_PRE ∈ [4,6]` · chân-b `n_treo ≤ 15 ∧ coverage-sạch` · sort star-birth DESC · CAVEAT "án-ở-ống" khi coverage thủng.
- **p15 FAIL-ENGINE with NAMES** — inject PHANTOM_XYZ_OOB → FAIL-ENGINE-NAMED ✓
- **p16 COLLECT-TIMELINE** — POST-DUMP · G1-POST-FLOOR-ret-40%
- **p17 MITO STICKY-XẢ V3.5c** — XẢ-WATCH · `STICKY-XẢ vì 🔴-02/09`

## 6. ⭐-01 COLLECT · BIÊN BẢN LẦN 9
Direction=POST-DUMP · ret=-40.0% · dd=-53.6% (unchanged since V3.5).

## 7. §E ROUTING · 3-tầng · tag khóa in-message · NGOÀI-SỔ footer
Không đổi.

---

## FIX SORT DẢI-A · V3.5f · ĐEN-THEN-XANH

**V3.5e ĐEN (sort=first-seed DESC · WRONG):**
```
top-3 PRE "mới nhất": [('ESPORTS','09-02'),('龙虾','09-02'),('B2','08-31')]
```
Ba con CŨ nhất đội nhãn mới-nhất-trước · label đi trước data.

**V3.5f XANH (sort=star-birth-date DESC · sửa):**
```
BẢNG 7 PRE {sym · first_seed · star_birth} sorted star-birth DESC:
  1. GIGGLE     first_seed=2026-08-31 · star_birth=2026-09-06  ← top-3
  2. AIOT       first_seed=2026-08-30 · star_birth=2026-09-06  ← top-3
  3. 龙虾         first_seed=2026-09-02 · star_birth=2026-09-05  ← top-3
  4. ESPORTS    first_seed=2026-09-02 · star_birth=2026-09-03
  5. AIA        first_seed=2026-08-29 · star_birth=2026-09-03
  6. AGT        first_seed=2026-08-30 · star_birth=2026-09-03
  7. B2         first_seed=2026-08-31 · star_birth=2026-09-02
```

GIGGLE 09-06 · AIOT 09-06 · 龙虾 09-05 top ✓ khớp kỳ vọng operator (AIOT/GIGGLE trong "mới=5" AND PRE-7).

**Fix location:** `tests/harness/harness_digest_summary.py` `_p14_dai_kep()` · sort key = `(star_birth, sym) DESC` · star_birth computed as `min(target_date) khi len(axes_seen) >= 2`.

---

## WL-ÁN-LỆ · SLOT CUỐI · VERBATIM ANALYSIS MERGE (REV9 CLOSE)

> **"18≡18 đối-chứng-hai-nguồn · 44-unique · List-B[23,44]avg34.6 · thác 157→16 · thay vĩnh viễn mọi trích tiền-REV4"**

Số cuối cùng đã niêm:
- **18 mắt SENT block-scoped ≡ 18 base** (đối-chứng hai-nguồn: SENT-log + state-file · block-scoped regex fix áp)
- **44-unique** (tier-3 unique tokens post universe-filter)
- **List-B[23, 44] avg 34.6** (18 hedge_watchlist_*.json files · min/max/avg)
- **thác 157 → 16** (tier-4 diagnostic input → tier-5 episode×coverage output)

**Thay vĩnh viễn mọi trích tiền-REV4** (án lệ chồng · legacy 25 phantom retired vĩnh viễn).

---

## LABEL-CLAIMS-LINT V3.5f (wire · enforcement-trước-chữ)

**Script:** `tests/harness/label_claims_lint.py` md5 `ca45943794a677179ab377963f1ccd15`

**Rule:** grep các nhãn CLAIM {`sorted`·`sort:`·`✓`·`checked`·`verified`·`OK`·`PASS`·`đã-*`} → hợp lệ chỉ khi bán kính k=5 dòng có PHÉP-KIỂM-IN-ĐƯỢC hoặc cite `[per <seal-id>]`.

**Phép-kiểm-in-được** = một trong:
- `md5=<hex>` · `n=<int>` · `file=<path>` · `hash=<hex>`
- `X == Y` · `n=X ≤ ceiling=Y` · `→` · `expected:`
- `[per <seal-id>]` cite

**TUYỂN-DỤNG (V3.5f):**
```
Corpus: tests/harness/_lint_demo4_corpus.txt
- L4 "pointer-integrity: OK" (không có evidence gần) → CAUGHT ORPHAN ✓
- L11 "p13 checked: sent_hash=..." (evidence gần) → PASSED
- L12 "verified: coverage fresh 6/31..." (evidence gần) → PASSED
- L15 "PRE tokens sorted..." (evidence L10 md5= trong window) → PASSED
- L18 "verdict: PASS [per harness_sabotage_20260907]" (cite) → PASSED

LINT RESULT: 1 orphan caught (L4)
✅ TUYỂN-DỤNG PASS
```

Wire hook: gọi lint pre-merge trên digest body + report file · orphan >0 → block merge.

**Text vé LABEL-CLAIMS-LINT (tuần sau)** — chờ ANALYSIS niêm formal wording.

---

## DOS-PACKAGE (khuôn ANALYSIS · ghế 27/09)

**Doc:** `docs/handover/dos_package_20260907.md` md5 `e5816b17f6880857169cf6193d144919`

**Câu kiến trúc mới (verbatim):**
> **"exposure-declared-theo-thế-hệ tầng universe — đổi mẫu số tại ranh thế hệ"**

**Observation:** DOS 3×/30d target=09-06 · Δ tổng = +517,255 · KHÔNG trong u50=139.

**Trạng thái:** `[ĐỀ-CỬ-UNIVERSE: DOS 3×/30d — chờ chữ 27/09]` · ghế 27/09 ANALYSIS bàn.

**BEAT/ONE/B đếm tiếp:** BEAT 1× · ONE 2× · B 1× · không đề cử sớm (<3×).

**Câu hỏi kiến trúc mở:**
1. Universe thế hệ: gen-0 (u50=139 lock 07/2026) → gen-1 (u51=140 với DOS)?
2. Ranh thế hệ: effective at T · exposure per-token comparison across boundary
3. Denominator switch: N-day rolling window đi qua ranh · bridge policy?
4. Backfill semantic: rerun cũ với universe cũ hay mới?

---

## HARNESS-LOG CANONICAL · 17 dòng đủ 4-field (fresh dump 2026-09-08T01:02)

```
2026-09-08T01:02:44+00:00	p1'	rename digest token → not-in-children	FAIL-PIN	f377f054
2026-09-08T01:02:44+00:00	p2	blank digest gomh_reo=0 · artifact=3	FAIL-VACUOUS-PIN	ded06938
2026-09-08T01:02:44+00:00	p3	blank digest LIST_A=0 · artifact=66	FAIL-VACUOUS-PIN	5ffa8bc8
2026-09-08T01:02:44+00:00	p4	blank digest 📥=0 · artifact=6	FAIL-VACUOUS-PIN	2e94f637
2026-09-08T01:02:44+00:00	p5	blank digest fresh=0 · artifact=18	FAIL-VACUOUS-PIN	64f858be
2026-09-08T01:02:44+00:00	p6	blank digest open=0 · artifact=14	FAIL-VACUOUS-PIN	6b8fc19d
2026-09-08T01:02:44+00:00	p7	flip 1 byte in body · seal mismatch	FAIL-PIN	462fdeb8
2026-09-08T01:02:44+00:00	p8	strip 1 provenance label · 4/5	FAIL-PIN	28f3b364
2026-09-08T01:02:44+00:00	p12	inflate digest 9000B > ceiling=7800	FAIL-PIN	4791e0f7
2026-09-08T01:02:44+00:00	p13	strip COLLECT events	FAIL-PIN	c5f4e2e7
2026-09-08T01:02:44+00:00	p14	inject 10 fake PRE stars · chân-a	FAIL-PIN	398d6ce2
2026-09-08T01:02:44+00:00	p14	mutate treo 20→50 · chân-b	FAIL-PIN	028d3cef
2026-09-08T01:02:44+00:00	p15	inject PHANTOM_XYZ_OOB ∉ universe(139)	FAIL-ENGINE-NAMED	8be66b59
2026-09-08T01:02:44+00:00	p16	COLLECT ret→5% strip G1-POST-FLOOR-*	FAIL-PIN	f6e3487c
2026-09-08T01:02:44+00:00	p16	strip FRESH axis · single-axis	FAIL-PIN	3e0a1cf7
2026-09-08T01:02:44+00:00	p17	strip STICKY-XẢ vì 🔴-* · V3.5c	FAIL-PIN-FULL	a594d19e
2026-09-08T01:02:44+00:00	p17	strip STICKY-¹ · V3.5b vô-hại	PIN-INTACT-VÔ-HẠI	1ac3e0b2
```

**Log canonical:** `data/logs/harness_sabotage.log` · **17 dòng đủ 4-field** (ts · pin · mutate · verdict · revert_sha) · **16 FAIL-PIN + 1 VÔ-HẠI intended**.

Bảng report trong VÉ = bản rút (không lặp revert-sha).

---

## V3.5f NUMBERS (target=09-06 · ledger dd9e83f0 L-59 preserved)

**4 SỐ:** gom_h_perp=21/21 · gom_h_kho=5/5 · exch=35/19 · fresh=48/27 · wl=16/16 · TOTAL=125/57.

**COVERAGE (block-scoped corrected):** PERP=19/31 · KHO=9/31 · FRESH=6/31.

**BỘ-BA:** treo=20(tổng-sống) · mới=5⊆treo · [DAO-DEFERRED].

**Direction 3-tầng V3.5c/f:**
- ⭐-PRE (7): AGT · AIA · AIOT · B2 · ESPORTS · GIGGLE · 龙虾
  - **top-3 dải-a sort star-birth DESC: GIGGLE·AIOT·龙虾** (V3.5f fix)
- 🔻 XẢ-WATCH (2): MITO · CYS (STICKY-XẢ vì 🔴-02/09)
- POST-DUMP+🌊 (11): BULLA · 4 · UAI · AKE · BTR · CLO · COLLECT · HANA · RIVER · TRIA · TUT

**NGOÀI-SỔ counter:** DOS 3× → ĐỀ-CỬ-UNIVERSE 27/09 · ONE 2× · BEAT 1× · B 1× (đếm tiếp).

**px-coverage:** 20/20 stars · Sticky-diff: 9 ¹-only-released · List-B[23,44]avg34.6.

---

## md5 chuỗi (V3.5f · REV9 final)

| File | md5 |
|---|---|
| `scripts/ledger_backfill_30d_v3_5.py` | a0b8132e86ad9e86639a033bfb24d716 |
| `scripts/watchlist_daily.py` (L-66 sentinel) | 6f7189c618f85fbd7a04c3392eebefb2 |
| `scripts/digest_summary_v2.py` (3-tầng · in-message tag) | b79300462c540c70269ea34a15479340 |
| `tests/harness/harness_full_sabotage_sweep.py` | a30fc5e8a89a3fbb4500044124e8a9dd |
| `tests/harness/harness_digest_summary.py` (V3.5f sort fix) | **571be51a04fecbe4098fe10010391f12** |
| `tests/harness/harness_p16_p17_direction.py` | 630d73d898abfe44fc8b34926337e5ae |
| `tests/harness/label_claims_lint.py` (V3.5f wire) | **ca45943794a677179ab377963f1ccd15** |
| `data/config/axis_map.yaml` | 0597734a111641915d4eccb642fc8348 |
| `events_2026-09-06.jsonl` | **dd9e83f0b9af5d475aa6dc043f3b6e98** (L-59) |
| `stars_2026-09-06.jsonl` | ade90907ec2e0e840e148d54e747cf92 |
| `star_grades.jsonl` (entry#1) | 421c8430342aea37bf35edab651708b1 |
| `docs/handover/dos_package_20260907.md` | **e5816b17f6880857169cf6193d144919** |
| `data/logs/harness_sabotage.log` (17 rows) | (append-only) |
| `ve_gop_lessons_batch_20260907_rev9.md` | (this file · md5 sau write) |

## Chờ chữ Tiên

REV9 = **vé cuối** · REV8 `89ae7072` **SUPERSEDED**. Bản REV9 mang:
- FIX SORT DẢI-A ĐÚNG chiều (star-birth) — bằng chứng mắt trong BẢNG 7 PRE
- WL-ÁN-LỆ VERBATIM ANALYSIS merged (18≡18 · 44-unique · List-B[23,44]avg34.6 · thác 157→16)
- LABEL-CLAIMS-LINT wire + tuyển-dụng PASS
- DOS-PACKAGE doc + ghế 27/09
- HARNESS-LOG 17 dòng 4-field canonical

**Chờ Tiên "khớp REV9 <md5>"** trước khi công bố.

## NHỊP CUỐI (V3.5f)

- **Đêm-0 dry tối nay 07→08:** chạy nguyên · đồng thời đêm-thử **không-kích** nhánh (a) closure · **report sáng PHẢI tuyên đích danh kích/không-kích** (không nói mơ hồ)
- **Sáng 08/09:** as-sent 09-07 → v3.5e/f → harness 14 pins/17 sabotage + label-lint → DEMO-5 ba-tầng
- **DEMO-5:** {`[STAR-ANOMALY dải-a n=7]` với **top-3 GIGGLE·AIOT·龙虾 ĐÚNG chiều** · tag khóa in-message `STICKY-XẢ vì 🔴-02/09` · `[NGOÀI-SỔ: 09-07: ...]` nếu tái xuất · **coverage MỘT vector** {fresh 6·kho 9·perp 19}/31}
- **RỒI mới xin "ok preview"**

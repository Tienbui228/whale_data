# VÉ GỘP LESSONS · REV8 · KÝ 07/09 GATE-4 V3.5e · MERGE 5 text + p14 kép + WL SLOT

**Trạng thái:** REV8 · bản REV7 `0e23c420ed355313fdd31b4369c80c03` SUPERSEDED (merge 5 text). REV8 chờ MỘT SLOT cuối = WL-án-lệ ANALYSIS re-niêm số.

**Updates so với REV7:**
- MERGE 5 text verbatim đã đóng: **PIN-TUYỂN-DỤNG (V3.5e) · KHÓA-ĐÍCH-DANH+vế-đuôi (V3.5c) · R1 [MA n-ep] display-only · R2 strict-139+[NGOÀI-SỔ]+[3]-đề-cử (V3.5d/e) · p15-semantics (V3.5 FAIL-ENGINE with NAMES)**
- + **p14-DẢI-KÉP** (V3.5d)
- **SỔ ĐỌC-ENFORCEMENT** text vào vé (L-80 DRAFT-KHÔNG-KÍCH-HOẠT)
- **SLOT cuối** = WL-án-lệ số cuối cùng chờ ANALYSIS re-niêm

---

## 1-3. L-78/L-79/án-lệ-✓-suy
Không đổi (V3.4/V3.5b).

## 4. §B AMENDMENT v1.6 (REV8 MERGE)

Cộng dồn V3.1-V3.5b + V3.5c/d/e:

- (v1.5 giữ nguyên · KEY-NORM · UNIVERSE-FILTER · EPISODE×COVERAGE · EXPLICIT-PARSER · WATERFALL 5-TIER · p15 FAIL-ENGINE with NAMES · LATTICE max-severity · STICKY-đích-danh · G1-anchor first-seed-any-axis)
- **PIN-TUYỂN-DỤNG (V3.5e NEW):** mỗi pin ≥1 mutate thật · 4-field log `pin · mutate · verdict · revert-sha` · nhánh nào ngôn ngữ luật-chết viết lại trước · p15 sabotage = inject out-of-139 token → FAIL-ENGINE với TÊN (chứng cổng-không-rây) · p2-p6 sabotage = FAIL-VACUOUS (blank digest vế khi child artifact đầy · empty-guard L-78 vế 4 fires).
- **NGOÀI-SỔ COUNTER + ĐỀ-CỬ-UNIVERSE (V3.5e NEW):** Fresh Δ≥50k out-of-u50 gom vào `ngoai_so_fresh[target]` · per-token counter /30d · token ≥3× → `[ĐỀ-CỬ-UNIVERSE: X n×/30d — chờ chữ 27/09]` in cuối khối 📒 · token <3× đếm tiếp không đề cử sớm.
- **SỔ ĐỌC-ENFORCEMENT (V3.5e NEW · L-80 DRAFT-KHÔNG-KÍCH-HOẠT):** 
  > **"Regex đọc log đa-target PHẢI block-scoped** (anchor target → next-target/EOF). DOTALL-span = phantom-đếm chờ sẵn."
  - Án lệ kép: {forensic-25-phantom 07/09 · extractor-watchlist 62≠30}
  - L-80 hiện DRAFT-KHÔNG-KÍCH-HOẠT trong vé · sentinel size+existence (L-66 wire) giữ làm lưới
  - Fix pattern: `re.search(rf"^INFO:\s+target_date={target}(.*?)(?=^INFO:\s+target_date=|\Z)", txt, re.MULTILINE|re.DOTALL)` + `if "snapshot SAVED" in m.group(1)`

## 5. Pins p14-p17 (REV8)

- **p14 DẢI-KÉP (V3.5d)** — chân-a `n_PRE ∈ [4,6]` · chân-b `n_treo ≤ 15 ∧ coverage-sạch` · coverage thủng → CAVEAT "án-ở-ống"
  - **Vector duy nhất (V3.5e re-run · coverage corrected 25→18-19):**
    ```
    p14 FAIL · chân-a: n_PRE=7 in [4,6] ✗ [STAR-ANOMALY dải-a n=7]
      top-3 PRE seed mới-nhất-trước: [('ESPORTS','2026-09-02'),('龙虾','2026-09-02'),('B2','2026-08-31')]
    · chân-b: n_treo=20≤15 ✗ · coverage-sạch=False [fresh=6/31 kho=9/31 perp=19/31]
      top-3 treo cũ-nhất: [('TRIA','2026-08-31'),('B2','2026-09-02'),('AIA','2026-09-03')]
      · CAVEAT: coverage thủng → án-ở-ống (không phải án-chợ)
    ```
- **p15 UNIVERSE-BOUND FAIL-ENGINE with NAMES (V3.5 semantics)** — sabotage: inject `PHANTOM_XYZ_OOB` → **FAIL-ENGINE-NAMED** ["PHANTOM_XYZ_OOB"] ✓
- **p16 COLLECT-TIMELINE** — direction=POST-DUMP · G1-POST-FLOOR-ret-40% (V3.5c prefix-match sweep)
- **p17 MITO STICKY-XẢ V3.5c** — direction=XẢ-WATCH · `STICKY-XẢ vì 🔴-02/09` · sabotage A=FULL-FAIL · B=VÔ-HẠI (đen-rồi-xanh · REV7 evidence)

## 6. ⭐-01 COLLECT · BIÊN BẢN LẦN 8 (V3.5e)
Direction=POST-DUMP · ret=-40.0% · dd=-53.6% · flags=`[POST-DUMP-dd-54%, G1-POST-FLOOR-ret-40%]` · sổ chấm entry#1 verbatim (TP-recall/FP-direction).

## 7. §E ROUTING · sender-dump + 3-tầng + tag khóa in-message + NGOÀI-SỔ footer
Digest body mang tag khóa đủ nguồn+ngày trên DÒNG ⭐ (bản in không phải jsonl-only). NGOÀI-SỔ block cuối 📒 với per-token counter + ĐỀ-CỬ-UNIVERSE khi ≥3×.

---

## MERGE 5 TEXT VERBATIM (đã đóng · REV8)

### Text 1 · PIN-TUYỂN-DỤNG (V3.5e)

Bảng sabotage 17 dòng / **14 pins distinct** · 16 FAIL-PIN + 1 VÔ-HẠI intended:

| pin | ngày-đen | mutate | verdict | còn-hạn |
|---|---|---|---|:---:|
| p1' | 2026-09-07 | rename digest token → not-in-children | FAIL-PIN | ✓ |
| p2 | 2026-09-07 | blank digest gomh_reo=0 · artifact=3 | **FAIL-VACUOUS-PIN** | ✓ |
| p3 | 2026-09-07 | blank digest LIST_A=0 · artifact=66 | **FAIL-VACUOUS-PIN** | ✓ |
| p4 | 2026-09-07 | blank digest 📥=0 · artifact=6 | **FAIL-VACUOUS-PIN** | ✓ |
| p5 | 2026-09-07 | blank digest fresh=0 · artifact=18 | **FAIL-VACUOUS-PIN** | ✓ |
| p6 | 2026-09-07 | blank digest open=0 · artifact=14 | **FAIL-VACUOUS-PIN** | ✓ |
| p7 | 2026-09-07 | flip 1 byte in body · seal mismatch | FAIL-PIN | ✓ |
| p8 | 2026-09-07 | strip 1 provenance label · 4/5 | FAIL-PIN | ✓ |
| p12 | 2026-09-07 | inflate digest 9000B > ceiling=7800 | FAIL-PIN | ✓ |
| p13 | 2026-09-07 | strip COLLECT events | FAIL-PIN | ✓ |
| p14a | 2026-09-07 | inject 10 fake PRE stars · chân-a | FAIL-PIN | ✓ |
| p14b | 2026-09-07 | mutate treo 20→50 · chân-b | FAIL-PIN | ✓ |
| **p15** | 2026-09-07 | **inject PHANTOM_XYZ_OOB ∉ universe(139)** | **FAIL-ENGINE-NAMED** | ✓ |
| p16a | 2026-09-07 | COLLECT ret→5% strip G1-POST-FLOOR-* | FAIL-PIN | ✓ |
| p16b | 2026-09-07 | strip FRESH axis · single-axis | FAIL-PIN | ✓ |
| p17a | 2026-09-07 | strip STICKY-XẢ vì 🔴-* · V3.5c | FAIL-PIN-FULL | ✓ |
| p17b | 2026-09-07 | strip STICKY-¹ · V3.5b vô-hại | PIN-INTACT-VÔ-HẠI | ✓ |

Log file: `data/logs/harness_sabotage.log` · script: `tests/harness/harness_full_sabotage_sweep.py`.

### Text 2 · KHÓA-ĐÍCH-DANH + VẾ ĐUÔI (V3.5c)

Sticky-source ĐÍCH DANH: chỉ match `{🔴-block · WASH-CRASH · S4/S5}` · CẤM ¹-generic.
9 tokens ¹-only released: `[AKE·BARD·BTR·HOLO·OPN·SHELL·SIGN·TURTLE·ZEST]`.
Tag khóa in trên dòng digest: `[STICKY-XẢ vì 🔴-02/09]` (nguồn+ngày inline · bản in không phải jsonl-only).
Sabotage p17-A strip-🔴 → FULL-FAIL · p17-B strip-¹ → VÔ-HẠI (bằng chứng luật mới).

### Text 3 · R1 [MA n-ep] display-only

R1 renderer hiển thị **moving-average n-episodes** dưới dòng ⭐ (display-only · không quyết định seed/direction). Format: `[MA n-ep=X trong Y ngày]` dưới mỗi star hoặc tại footer summary.
DISPLAY-ONLY · không tham gia lattice · không thay đổi verdict.

### Text 4 · R2 strict-139 + [NGOÀI-SỔ] + [3]-đề-cử (V3.5d/e)

R2 interim mode STRICT-139:
- Fresh Δ≥50k out-of-u50 (139) → CẤM seed vào PERP/FRESH-CHAIN axis
- Ghi vào `[NGOÀI-SỔ: <date>] <sym> Δ=+X` (V3.5d)
- Per-token counter /30d window (V3.5e)
- Token ≥3× trong window → `[ĐỀ-CỬ-UNIVERSE: X n×/30d — chờ chữ 27/09]` (V3.5e)
- Token <3× đếm tiếp không đề cử sớm

**V3.5e counter target=09-06 (window 30d):**
- DOS: 3× → **⇒ [ĐỀ-CỬ-UNIVERSE: DOS 3×/30d — chờ chữ 27/09]**
- ONE: 2× · BEAT: 1× · B: 1× (đếm tiếp)

### Text 5 · p15 SEMANTICS · FAIL-ENGINE with NAMES

`n_unique` mọi trục ≤ `|universe|=139`. Vi phạm = **FAIL-ENGINE · treo verdict TRƯỚC khi so số · in ĐÍCH DANH oob syms per axis**. CẤM silent-drop. Universe cite = `file + md5` trong header mỗi run.

Sabotage verified V3.5e: inject `PHANTOM_XYZ_OOB` vào seed-path → engine detects oob · named=[PHANTOM_XYZ_OOB] · **FAIL-ENGINE-NAMED** ✓ · cổng-không-rây chứng thực.

TODO L-48: per-target-date universe(target) cho SOPH-family delist giữa cửa sổ (chưa wire).

---

## SLOT cuối · WL-ÁN-LỆ CHỜ ANALYSIS RE-NIÊM SỐ

[PENDING-ANALYSIS-TEXT · WL-án-lệ number-set final]:

Số cần re-niêm (verbatim):
- **44-unique-trong-vũ-trụ** (tier-3 unique tokens after universe-filter)
- **List-B daily-size [23, 44] avg 34.6** (18 hedge_watchlist_*.json files trong window · nguồn artifact độc lập)
- **18 mắt SENT block-scoped ≡ 18 base** (SENT-SAVED block-scoped regex = state-file-present · match hoàn hảo · KHÔNG 25 phantom)
- **thác 157 → 16** (tier-4 diagnostic input → tier-5 episode×coverage output)

Chờ operator drop text verbatim niêm.

---

## FORENSIC LỚN V3.5d/e · phát hiện regex phantom

**7 dates SENT-SAVED-but-file-vắng = KHÔNG TỒN TẠI** (án lệ #1).
Root cause: `_wl_sent_by_target` regex `.*?` với DOTALL span-across-target-blocks.
Legacy 25 = 7 phantom + 18 thật · Real: **18 SENT-SAVED (block-scoped) = 18 state-file-present · diff 0**.

Fix V3.5d applied `ledger_backfill_30d_v3_5.py` line ~113:
```python
m = re.search(rf"^INFO:\s+target_date={re.escape(target)}(.*?)(?=^INFO:\s+target_date=|\Z)",
              txt, re.MULTILINE | re.DOTALL)
return "snapshot SAVED" in m.group(1) if m else False
```

Cascade fix: coverage wl 25 → 18 · perp-union 26 → 19 · WL episodes UNCHANGED (16/16 · 7 phantom days có 0 fires).

**L-66 SENTINEL wired** `watchlist_daily.py:671` sau `save_snapshot()`:
```python
if (not _snap_path.exists()) or _snap_path.stat().st_size < 100:
    raise RuntimeError(f"WRITE-FAIL-CÂM sentinel: {_snap_path} size={_sz}")
print(f"INFO: snapshot SAVED to {_snap_path} size={_snap_path.stat().st_size}")
```
Future write-fail-câm sẽ raise + Telegram alert · size cite trong log line.

**L-80 (DRAFT-KHÔNG-KÍCH-HOẠT):** "Regex đọc log đa-target PHẢI block-scoped · DOTALL-span = phantom-đếm chờ sẵn". Án lệ kép áp dụng cho V3.5e forensic + extractor-watchlist 62≠30 (án đã có tiền lệ).

---

## V3.5e NUMBERS (target=09-06 · ledger md5 dd9e83f0 · L-59 preserved)

**4 SỐ:** gom_h_perp=21/21 · gom_h_kho=5/5 · exch=35/19 · fresh=48/27 · wl=16/16 · TOTAL=125/57.

**COVERAGE V3.5e CORRECTED (block-scoped regex):**
- **PERP  = 19/31** (union 9 gomh ∪ 18 wl · giảm từ 26 phantom-fixed)
- **KHO   = 9/31**
- **FRESH = 6/31**

**BỘ-BA:** treo=20(tổng-sống) · mới=5⊆treo · [DAO-DEFERRED coverage: fresh 6/31 · kho 9/31 · perp 19/31].

**Direction 3-tầng V3.5c:**
- ⭐-PRE (7): AGT · AIA · AIOT · B2 · ESPORTS · GIGGLE · 龙虾
- 🔻 XẢ-WATCH (2): MITO(STICKY-XẢ vì 🔴-02/09) · CYS(STICKY-XẢ vì 🔴-02/09)
- POST-DUMP+🌊 (11): BULLA · 4 · UAI (G1-FLOOR) · AKE · BTR · CLO · COLLECT · HANA · RIVER · TRIA · TUT

**px-coverage:** 20/20 stars (alpha 17 · spot 3).

**NGOÀI-SỔ counter V3.5e (per-token /30d):**
- DOS: 3× → **[ĐỀ-CỬ-UNIVERSE: DOS 3×/30d — chờ chữ 27/09]**
- ONE: 2× · BEAT: 1× · B: 1×

**LIST-B artifact-based:** n_days=18 · min=23 · max=44 · avg=34.6.

**Sticky-diff V3.5c:** 9 ¹-only-released.

---

## md5 chuỗi (V3.5e)

| File | md5 |
|---|---|
| `scripts/ledger_backfill_30d_v3_5.py` (regex fix + NGOÀI-SỔ counter) | a0b8132e86ad9e86639a033bfb24d716 |
| `scripts/watchlist_daily.py` (L-66 sentinel) | 6f7189c618f85fbd7a04c3392eebefb2 |
| `scripts/digest_summary_v2.py` (3-tầng · in-message tag) | b79300462c540c70269ea34a15479340 |
| `tests/harness/harness_full_sabotage_sweep.py` | a30fc5e8a89a3fbb4500044124e8a9dd |
| `tests/harness/harness_digest_summary.py` (p14 kép · namespace note) | f1386d3304ef622e1e28a6ac0d0e5580 |
| `tests/harness/harness_p16_p17_direction.py` | 630d73d898abfe44fc8b34926337e5ae |
| `data/config/axis_map.yaml` (direction_eval) | 0597734a111641915d4eccb642fc8348 |
| `events_2026-09-06.jsonl` | **dd9e83f0b9af5d475aa6dc043f3b6e98** (L-59) |
| `stars_2026-09-06.jsonl` V3.5c | ade90907ec2e0e840e148d54e747cf92 |
| `data/logs/harness_sabotage.log` (17 rows tuyển-dụng) | (append-only) |
| `star_grades.jsonl` (entry#1) | 421c8430342aea37bf35edab651708b1 |
| `ve_gop_lessons_batch_20260907_rev8.md` | (this file) |

## Chờ chữ Tiên

REV8 = MERGE 5 text đã đóng + p14 kép + SỔ ĐỌC-ENFORCEMENT + FORENSIC verdict. Bản REV7 `0e23c420` **SUPERSEDED**.

**SLOT cuối duy nhất:** WL-án-lệ số cuối cùng chờ ANALYSIS re-niêm ({44-unique · List-B[23,44]avg34.6 · 18 mắt SENT block-scoped ≡ 18 base · thác 157→16}).

REV8 → REV9 = vé cuối khi SLOT về.

## NHỊP V3.5e

- **Đêm-0 dry tối nay 07→08:** chạy nguyên · đồng thời đêm-thử **không-kích** nhánh (a) closure
- **Sáng 08/09:** as-sent 09-07 → v3.5e → harness ĐỦ-TUYỂN (14 pins · 17 sabotage rows) → DEMO-5 ba-tầng
- **DEMO-5:** {[STAR-ANOMALY dải-a n=7] · tag khóa in-message · [NGOÀI-SỔ: 09-07: DOS×N ONE×N?] nếu tái xuất}
- **RỒI mới xin "ok preview"**

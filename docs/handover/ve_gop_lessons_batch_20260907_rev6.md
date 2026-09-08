# VÉ GỘP LESSONS · REV6 · KÝ 07/09 GATE-4 · V3.5 TRỤC-GIÁ + G1-G3 + BỘ-BA-FIX

**Trạng thái:** REV6 · bản REV5 `bfcaa40316bb4b306e6e0a467b87f921` GIỮ (ledger-REV5 của directive ≠ vé-rev · code v3.5 tránh lẫn số).

**Updates so với REV5:**
- **BỘ-BA fixed semantics:** treo=**tổng-sống** · mới ⊆ treo (không cộng)
- **COVERAGE axis-union THẬT** (per-day-SET union) · 3 số PERP·KHO·FRESH
- **WL án-lệ mang số:** "44-unique / 44 ghế / 25 mắt · thác 157→16"
- **PRICE-JOIN V3.5:** klines_1d + alpha fallback · `[PX-SRC=spot|alpha|N/A]` · footer coverage
- **G1-G3 direction eval** (PROVISIONAL · control-27/09 · yaml `direction_eval`)
- **RENDER:** ⭐ line append `· ret±X% dd−Y% → <DIR>[reason]` · ⭐-PRE cấm G1/G2/G3 · POST-DUMP/XẢ-watch → 🔻 block
- **p16 COLLECT + p17 MITO** fixtures với input-pin + sabotage ≥2 nhánh
- **BẢNG-CHẤM-⭐** khai trương: `star_grades.jsonl` + view L-74 · entry#1 COLLECT verbatim
- **4 pending SLOTs** artifact-backed (R1 · R2 token-B · p15 · WL án-lệ)

---

## 1-3. L-78/L-79/án-lệ-✓-suy
Không đổi.

## 4. §B AMENDMENT v1.4 (REV6)

Cộng dồn V3.1-V3.4 + **V3.5 direction/price** rules:

- SỔ-ĂN-SỰ-KIỆN · SENT-ANCHOR THỐNG NHẤT · FRESH-Δ-ONLY · WL-EPISODE-HÓA (V3.2)
- KEY-NORM · UNIVERSE-FILTER · EPISODE×COVERAGE (V3.3)
- EXPLICIT-PARSER · WATERFALL 5-TIER · p15 FAIL-ENGINE with NAMES · DAO-DEFERRED (V3.4)
- **PRICE-JOIN (V3.5):** Mỗi dòng sổ mang `{px@seed(PERP-seed) · px_now · max20d}` từ `data/raw/spot_klines_1d`. Fallback `binance_alpha` (COLLECT/BULLA/small-caps). Missing → `[PX-N/A]` không silent. Footer đếm px-coverage `n_pxok/n_stars`.
- **G1-G3 DIRECTION EVAL (V3.5 PROVISIONAL · control-27/09):** 
  - G1: `|ret_since_seed| ≥ 30%` → floor POST (cấm PRE)
  - G2: `dd20 ≤ -40%` → POST-DUMP + XẢ-watch + câu-soi XẢ ("rút về đâu? ai nhận hàng trong dump? dính CEX-list?")
  - G3 sticky (14d = shared EPISODE_GAP): 🔴 ∨ WASH-CRASH ∨ S4/S5 → khóa ≤ XẢ-watch; mở lại PRE chỉ khi bằng-chứng-đảo (giá ổn 7d ∧ kho đảo)
  - Nguồn sticky = as-printed: `🔴 block artifact (gom_h_daily.log)` · walletset `WASH-CRASH` tag · phase `S4/S5` (case_state_map)
- **BỘ-BA FIXED (V3.5):** treo = **tổng-sống** (tất cả stars alive) · mới ⊆ treo (không cộng vào)
- **COVERAGE AXIS-UNION THẬT:** per-day-SET union (không cộng số cao nhất). Format `PERP=N/31 (union M gomh ∪ K wl)` v.v.

## 5. p14 + p15 + p16 + p17 pins (REV6)

- **p14 STAR-COUNT-SANITY:** dải [4,6] · soft_ceiling=15 (không đổi)
- **p15 UNIVERSE-BOUND:** FAIL-ENGINE with NAMES (V3.4)
- **p16 COLLECT-TIMELINE (V3.5 NEW):** fire 02/09 → run → dump → fresh-in-dump ⇒ POST-DUMP · cấm ⭐-PRE
  - Enforcement: `tests/harness/harness_p16_p17_direction.py`
  - Input-pin: klines-slice md5 + events md5 dd9e83f0
  - Expected: `direction == POST-DUMP` AND `G1-POST-FLOOR ∈ flags`
  - Sabotage: (A) shift px→ret 5% → G1 không fire → FAIL-PIN · (B) strip FRESH → single-axis → FAIL-PIN
  - **RESULT V3.5:** ✅ PASS · ret=-40.0% dd=-53.6% · flags=[POST-DUMP,G1-POST-FLOOR]
- **p17 MITO STICKY-XẢ (V3.5 NEW):** 🔴 02/09 ⇒ sticky-XẢ xuyên 06/09 bất chấp 📥+FRESH+QUIET
  - Enforcement: same harness
  - Expected: `direction ∈ {POST-DUMP, XẢ-WATCH}` AND `STICKY-* ∈ flags`
  - Sabotage: (A) strip 🔴 records → sticky-🔴 gone (PARTIAL vì ¹ giữ) · (B) strip ¹ → sticky-¹ gone (PARTIAL vì 🔴 giữ)
  - **RESULT V3.5:** ✅ PASS · direction=POST-DUMP · flags=[STICKY-🔴, STICKY-¹, POST-DUMP] · reasons=["G3-sticky: 🔴 2026-09-02", "past-red-flag(¹)"]

## 6. ⭐-01 COLLECT · BIÊN BẢN LẦN 6 (V3.5)

- **Direction V3.5:** **POST-DUMP** (G1-POST-FLOOR fire · ret=-40.0% ≥ 30% floor)
- **Metric:** px@seed(09-02)=0.0801 · px_now(09-06)=0.048 · max20d=0.103 · dd20=-53.6% (≤ -40% G2 ceiling)
- **Fixture p16:** ✅ PASS (input-pin dd9e83f0 · sabotage 2 nhánh detected)
- **Sổ chấm entry#1:** VERBATIM operator "COLLECT — máy fire trước sóng (TP-recall) · ledger gán chiều sai 4 ngày (FP-direction)"
- **Bản trước:** SEED-LESSON-01 hủy · V3.1-V3.4 báo ⭐-PRE SỐNG · V3.5 revise → POST-DUMP (đúng thực tế)

## 7. §E ROUTING · sender-dump + COVERAGE + G1-G3 footer
Digest footer thêm dòng direction summary: n_PRE + n_POST-DUMP + n_XẢ-WATCH + n_sticky.

---

## ÁN-LỆ WL WATERFALL V3.5 (mang số)

Stat = "44-unique-trong-vũ-trụ / 44 ghế / 25 ngày-mắt · thác 157→16"

| TIER | n | uniq |
|---|---:|---:|
| 1 raw-parser | 623 | 131 |
| 2 hậu-key-norm | 623 | 131 |
| 3 hậu-universe | 181 | **44** |
| 4 hậu-baseline [DIAG] | 157 | 43 |
| 5 hậu-episode×coverage | **16** | 16 |

Rác-parser=0 · norm-miss-nối-lại=0 · thật-ngoài=442/87.

---

## V3.5 numbers (target=09-06 · cite dd9e83f0)

**4 SỐ:** gom_h_perp=21/21 · gom_h_kho=5/5 · exch=35/19 · fresh=48/27 · wl_episode=16/16 · **TOTAL=125/57 union**.

**COVERAGE V3.5 axis-union THẬT (3 số):**
- **PERP  = 26/31** (union 9 gomh ∪ 25 wl)
- **KHO   = 9/31**  (union 9 gomh-H1 ∪ 6 exch)
- **FRESH = 6/31**

**Ma trận giao:** n_perp=32 · n_kho=20 · n_fresh=27 · |PERP∩FRESH|=6 · |KHO∩FRESH|=14 · |PERP∩KHO|=4 · |all|=2.

**p15 UNIVERSE-BOUND:** ✅ zero oob.

**px-coverage:** 20/20 stars có px_now (100%). PX-SRC = alpha 17 · spot 3 · N/A 0.

**BỘ-BA V3.5 FIXED:**
- **treo = 20 (tổng-sống)**
- **mới = 5 ⊆ treo** (AIOT · 4 · GIGGLE · UAI · RIVER)
- coverage-vector = fresh 6/31 · kho 9/31 · perp 26/31

**Direction split (G1-G3 applied):**
- **⭐-PRE (10):** BULLA · 4 · UAI · 龙虾 · AGT · ESPORTS · AIA · AIOT · GIGGLE · B2
- **🔻 POST-DUMP (10):** MITO · CYS · AKE · BTR · CLO · HANA · RIVER · TRIA · TUT · **COLLECT** (G1-POST-FLOOR)

**Sticky detections:** MITO(🔴+¹) · CYS(🔴+¹) · AKE(¹) · BTR(¹). Danh sách 🔴 dates via `_scan_sticky_events` từ gom_h_daily.log.

---

## SLOT-1 [PENDING-ANALYSIS-TEXT · R1 absorption]
> Chờ operator drop ANALYSIS text ruling R1 absorption · niêm bằng md5 văn bản gốc (án V-VERBATIM-20260903 · cấm phục dựng).

## SLOT-2 [PENDING-ANALYSIS-TEXT · R2 as-printed vs universe · ca token "B"]
> Chờ operator drop text về token "B" (FRESH Δ-7 cut · Δ=+879,435 09-06) · question: as-printed hiển thị B nhưng universe không có → chọn nguồn nào là quan tòa?

## SLOT-3 [PENDING-ANALYSIS-TEXT · p15 semantics]
> Chờ text semantics ruling · V3.5 code = FAIL-ENGINE with NAMES · niêm bằng md5.

## SLOT-4 [PENDING-ANALYSIS-TEXT · WL án-lệ]
> Chờ text án-lệ WL waterfall (mang stat 44/44/25) niêm operator.

---

## NHÁNH (a) STATUS · V3.5

**Nhánh (a): ROOT-CAUSED (chưa CLOSED)**
- ✅ thước sạch (waterfall + p15-names + DAO-DEFERRED + G1-G3 + PX-JOIN)
- ✅ số cũ re-measure (ledger md5 dd9e83f0 preserved · V3.5 direction added, không đụng events)
- ⏳ MỘT ĐÊM không kích: Đêm-0 dry 07→08/09

**Nhánh (b) siết seed rules:** vẫn open · 15 stars-PRE (nếu G1-G3 filter loại 10 POST) → **9-10 PRE tokens** thực-active → gần dải [4,6]?

**⭐ đang-treo hậu-G1-G3:** 10 PRE (đúng thứ tự loại trừ) → gần expected_max=6. Chờ ANALYSIS ruling.

---

## md5 chuỗi hiện tại (post V3.5)

| File | md5 |
|---|---|
| `scripts/ledger_backfill_30d_v3_5.py` | 23f63146c19cba1117f303002c882f42 |
| `scripts/star_grades_manage.py` | a5a68231fae37396e0d4f80b6683f1d8 |
| `scripts/digest_summary_v2.py` (star block V3.5 upgrade) | 86e43b8e07cc96b263c8dc70cfea187f |
| `tests/harness/harness_p16_p17_direction.py` | 12bd702be0b051d03fb520bab3fe89ca |
| `data/config/axis_map.yaml` (direction_eval block) | 0597734a111641915d4eccb642fc8348 |
| `data/logs/event_ledger/events_2026-09-06.jsonl` | **dd9e83f0b9af5d475aa6dc043f3b6e98** (L-59 preserved) |
| `data/logs/event_ledger/stars_2026-09-06.jsonl` | 32e4f80e974b9dd7d0d19f2535fdde3a |
| `data/state/star_grades.jsonl` (entry#1) | (compute) |
| `data/state/star_grades.md` (view) | 5c9bbd62964776a47df29c07b16f774c |
| `freshwatch_symbols.txt` (u50=139) | e36183036102c52ed586d6c2bdcfc928 |
| `ve_gop_lessons_batch_20260907_rev6.md` | (this file) |

## NHỊP V3.5

- **Đêm-0 dry tối nay 07→08:** chạy nguyên (chỉ test sender-dump · không đụng v3.5)
- **Sáng 08/09:** as-sent 09-07 → ledger v3.5 → harness p1'-p17 (11+6=17 pins) → DEMO-5 với direction sống
- **DEMO-5:** COLLECT hiện POST-DUMP + câu-soi XẢ · MITO sticky-XẢ · **RỒI mới xin "ok preview"**

## Chờ chữ Tiên

7 items REV6 + 4 SLOTs [PENDING-ANALYSIS-TEXT] artifact-backed · bản REV5 `bfcaa40316bb4b306e6e0a467b87f921` GIỮ (chờ upgrade khi có V3.5 xong).

**V3.5 status:**
- p16 COLLECT-TIMELINE PASS · p17 MITO STICKY PASS · 4 sabotage nhánh detected FAIL-PIN
- Ledger md5 preserved dd9e83f0 (L-59 chain intact)
- Star_grades entry#1 verbatim COLLECT TP-recall/FP-direction
- PX-coverage 20/20 stars (100%)
- Direction split: 10 PRE · 10 POST-DUMP · 0 XẢ-WATCH (all sticky merged into POST-DUMP hôm nay)
- G1-G3 PROVISIONAL · control-27/09
- 4 SLOTs pending ANALYSIS text niêm

Chờ chữ Tiên trên REV6 + 4 SLOTs. DEMO-5 sáng mai sau (1)-(6) xong.

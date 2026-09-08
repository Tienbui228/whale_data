# VÉ GỘP LESSONS · REV5 · KÝ 07/09 GATE-4 · GIẢI-PHẪU + CỔNG-THAY-RÂY

**Trạng thái:** REV5 · bản REV4 `65ee9fe2eb43cba500b0b4ca7ab93b3b` KHÔNG TRÌNH (label CLEAR sai · chưa mắt-mở) · **KHÔNG trình bản cũ**.

**Updates so với REV4:**
- Thêm **án-lệ WL WATERFALL 5-tier** (mang số thác-nước · rác-parser=0)
- **p15 semantics khớp máy** (FAIL-ENGINE with NAMES · cấm silent-drop)
- **⭐-01 COLLECT biên bản lần 5** (V3.4 recheck)
- **FRESH Δ-7 diễn giải đích danh** (7 events/4 unique bị cut · tên·ngày·lý do)
- **DAO NHÃN SỬA:** DAO-DEFERRED (không CLEAR · không ANOMALY · chờ mắt mở)
- **Nhánh (a) relabel:** ROOT-CAUSED (chưa CLOSED · công thức đóng theo ANALYSIS)
- **Slots 2 ANALYSIS text verbatim** (PENDING-ANALYSIS-TEXT: WL-án-lệ · EPISODE×COVERAGE ruling)

---

## 1. L-78-APPEND · vế-tồn-tại (EMPTY-GUARD)
Không đổi. BỐN-VẾ L-78: (1) độc-lập · (2) không cùng-object · (3) đẳng-thức bất-biến · (4) **vế-tồn-tại**.

## 2. L-79 · BLOCKER-BỊA + DEMO-RUỘT
Không đổi.

## 3. Án-lệ-✓-suy · phái sinh L-79
Không đổi.

---

## 4. §B AMENDMENT · SỔ-ĂN-SỰ-KIỆN + SENT-only + WL-EPISODE + KEY-NORM + UNIVERSE + EPISODE×COVERAGE + WATERFALL (REV5)

**Amendment §B seed-list v1.3 (KÝ 07/09 GATE-4 verbatim):**

- **SỔ-ĂN-SỰ-KIỆN:** Ledger events chỉ record TÍN-HIỆU MỚI · loại loài-cum-standing.
- **SENT-ANCHOR THỐNG NHẤT (V3.1):** Mọi trục anchor [SENT]-log; provenance file chỉ label.
- **FRESH-Δ-ONLY:** Loài-Δ≥50k duy nhất seed.
- **WL-EPISODE-HÓA (V3.2):** `cluster_episodes()` VERBATIM prod archive · `EPISODE_GAP=14`.
- **KEY-NORM (V3.3):** Bare-symbol strip USDT trước union.
- **UNIVERSE-FILTER (V3.3):** `freshwatch_symbols.txt` u50=139 · filter mọi source.
- **EPISODE×COVERAGE (V3.3):** Episode-start CHỈ khi lookback-14d có ≥`COVERAGE_MIN_DAYS=10` days WL-coverage. Thiếu → UNKNOWN-EPISODE, KHÔNG seed.
- **L-59 RECONCILE-KEY (V3.3):** File md5 = source-of-truth (không phải run stdout) · reconcile định kỳ.

**NEW V3.4:**

- **EXPLICIT-PARSER (V3.4 NEW):** `list_b_tokens_from()` chấp nhận **cả list[str] và dict[str,meta]** · CẤM accidental parsing. Án: schema drift 2026-08-19 (list→dict), v3.3 vô tình đọc đúng nhờ Python iterate dict-keys. V3.4 tường minh: `.keys()` if dict, direct if list, skip non-string.
- **WATERFALL 5-TIER (V3.4 NEW):** WL pipeline giải phẫu 5 tầng đích danh, mỗi tầng in số. Rác-parser>0 = SỬA PARSER (không để universe-gate dọn hộ). Baseline tier-4 = **DIAGNOSTIC-ONLY** (không gate ngưỡng · án V3.4-BASELINE-DIAG · baseline delegated cho k=10 lookback ở tier-5).
- **p15 FAIL-ENGINE with NAMES (V3.4 SỬA):** Vi phạm = in ĐÍCH DANH symbols out-of-bound · treo verdict · CẤM silent-drop. Universe cite = `file + md5` header.
- **DAO-DEFERRED LABEL (V3.4 SỬA):** Coverage < ceiling target → `[DAO-DEFERRED coverage: fresh X/Y·kho X/Y] đang-treo=N · mới=M`. Không "CLEAR", không "ANOMALY". Chờ mắt mở operator.

---

## 5. p14 STAR-COUNT-SANITY + p15 UNIVERSE-BOUND + STAR-LINE SOURCE-TAG (REV5)

**p14 (verbatim REV4):** dải `[4,6]` · soft_ceiling=15 · vượt → `[STAR-ANOMALY]` in digest.

**p15 UNIVERSE-BOUND (V3.4 semantic khớp máy):**

> **n_unique** mọi trục **≤ |universe|=139** · chạy SAU key-norm + parser-fix (V3.4 order).
> Vi phạm = FAIL-ENGINE · treo verdict TRƯỚC khi so số · in ĐÍCH DANH oob syms per axis.
> CẤM silent-drop. Universe cite = `file + md5` trong header mỗi run.
> TODO L-48: per-target-date universe(target) cho SOPH-family delist giữa cửa sổ (chưa wire).

**Enforcement:** `ledger_backfill_30d_v3_4.py` in `## p15 UNIVERSE-BOUND CHECK` block với `p15_violations` dict.

**STAR-LINE SOURCE-TAG (V3.2):** `ᴳ`(gomh) · `ᵂ`(watchlist) · `ᴱ`(exch) · `ᶠ`(fresh)

---

## 6. ⭐-01 · COLLECT · BIÊN BẢN LẦN 5 (REV5 V3.4)

**⭐-01 COLLECT hậu-V3.4 · KÝ 07/09 GATE-4:**

- **Symbol:** COLLECT · ∈ universe u50=139 ✓
- **Axes:** {PERP, FRESH-CHAIN}
- **n_events (30d, V3.4):** 3 (2 fresh + 1 perp · unchanged v3.3/v3.2/v3.1)
- **PERP fire (SENT-verified):**
  - target=**2026-09-02**
  - Relay hash `f58843a649cf` · HTTP 200 · resp_len=5906 · n_lines=53
  - Line: `🟢 • COLLECTUSDT [H2·ghế] ···· 0/4 LOW`
  - source-tag: **ᴳ** (gom_h)
- **FRESH-Δ events (V3.4 · post universe-filter · both kept):**
  - date=2026-09-03 · Δ=+117,896
  - date=**2026-09-06** · Δ=+1,978,820 (anchor: digest_daily_vps.log [SENT] Fresh-Wallets ok=True)
  - source-tag: **ᶠ** (fresh)
- **V3.4 recheck lần-5:** COLLECT NOT in FRESH Δ-7 cut list (BEAT/DOS/ONE/B đều out-of-universe). COLLECT survived universe-filter. WATERFALL không đụng COLLECT (không phải WL-source). p15 zero-oob.
- **Star-line:** `COLLECT 2-trục (FRESH-CHAIN+PERP) PERP=09-02ᴳ · FRES=09-06ᶶ`
- **Verdict:** ⭐-PRE 2-trục · SỐNG chính thức · **BIÊN BẢN LẦN 5 PASS**
- **Cite (V3.4):** "fire target=09-02 · SENT 03/09 hash f58843a649cf · FRESH-Δ 09-06 SENT digest_daily_vps · V3.4 universe-filter PASS · file md5 dd9e83f0"

**SEED-LESSON-01 hủy kích hoạt** · giữ khuôn.

---

## 7. §E ROUTING amendment · sender-dump hooks + COVERAGE footer
Không đổi so với REV4 · footer digest thêm axis-union 3 số.

---

## ÁN-LỆ WL WATERFALL (V3.4 · SỐ THÁC-NƯỚC)

**Án lệ V3.4-WATERFALL · KÝ 07/09:**

> WL pipeline giải phẫu 5 tầng đích danh. Rác-parser=0 → parser CLEAN (dict/list explicit-handled). Tier-3 drops 442/87 đều `thật-ngoài-vũ-trụ` (u50 broader universe · không phải bug parser). Baseline tier-4 giữ diagnostic-only vì gate ở đó sẽ shift episode-starts sai (án V3.4-BASELINE-DIAG). Baseline delegated cho k=10 coverage lookback ở tier-5.

**Số thác-nước target=2026-09-06 · window=30d:**

| TIER | n_entries | n_unique |
|---|---:|---:|
| 1. raw-parser | 623 | 131 |
| 2. hậu-key-norm | 623 | 131 |
| 3. hậu-universe | 181 | 44 |
| 4. hậu-baseline (D-1) [DIAGNOSTIC-ONLY] | 157 | 43 |
| 5. hậu-episode×coverage | **16** | **16** |

**TIER-3 drops classification (V3.4 đích danh):**

| Class | n_entries | n_unique |
|---|---:|---:|
| rác-parser | 0 | 0 |
| norm-miss-nối-lại | 0 | 0 |
| thật-ngoài-vũ-trụ | 442 | 87 |

Sample thật-ngoài: `['1000000MOG', 'AEVO', 'ALL', 'ANIME', 'ANKR', 'APE', 'ARK', 'ASR', 'ASTR', 'BANANA', 'BCH', 'BEAMX', 'BIRB', 'BNT', 'BRETT', 'BROCCOLIF3B', 'C98', 'CC', 'CELR', 'CHILLGUY']` (u50 broader, non-freshwatch subset).

**Tier-4 dropped no-D-1-baseline = 24** (diagnostic count · does NOT gate seeds).

---

## FRESH Δ-7 CUT · ĐÍCH DANH (V3.4 diag)

**7 events / 4 unique bị cut khi apply universe-filter (V3.3 → V3.4):**

| symbol | date | Δ | lý do |
|---|---|---:|---|
| BEAT | 2026-08-31 | +86,890 | thật-ngoài-vũ-trụ |
| DOS | 2026-08-31 | +254,646 | thật-ngoài-vũ-trụ |
| ONE | 2026-09-04 | +137,012 | thật-ngoài-vũ-trụ |
| DOS | 2026-09-05 | +69,898 | thật-ngoài-vũ-trụ |
| ONE | 2026-09-05 | +1,008,093 | thật-ngoài-vũ-trụ |
| B | 2026-09-06 | +879,435 | thật-ngoài-vũ-trụ |
| DOS | 2026-09-06 | +192,711 | thật-ngoài-vũ-trụ |

Tất cả 4 unique (BEAT/DOS/ONE/B) không có trong `freshwatch_symbols.txt` u50=139 → legitimately cut.

**⭐-01 COLLECT khôᴶg trong list này** (COLLECT ∈ universe · survived · both fresh events kept: 09-03, 09-06).

---

## V3.4 numbers (bằng chứng cite · từ file dd9e83f0)

**Header cite (L-59 semantics đã áp):** file `data/logs/event_ledger/events_2026-09-06.jsonl` · md5 `dd9e83f0b9af5d475aa6dc043f3b6e98`.

| Source | n_events | n_unique |
|---|---:|---:|
| gom_h_perp_SENT | 21 | 21 |
| gom_h_kho_SENT | 5 | 5 |
| exch_qualified_SENT | 35 | 19 |
| fresh_delta_SENT | 48 | 27 |
| watchlist_b_episode_SENT | 16 | 16 |
| **TOTAL** | **125** | **57 union** |

**EXCLUDED:** `gom_h_NO-relay-SENT`=22 · `exch_NO-digest-SENT`=25 · `fresh_NO-digest-SENT`=25 · `wl_UNKNOWN-EPISODE`=28.

**COVERAGE V3.4 NHÃN SỬA (axis-union 3 số):**
- **PERP-union = 9∪25/31** (gomh · wl)
- **KHO-union  = 9∪6/31** (gomh-H1 · exch)
- **FRESH      = 6/31**

Diagnostic split: gomh-PERP=9/31 · gomh-KHO=9/31 · exch=6/31 · fresh=6/31 · wl=25/31.

**Ma trận giao (in lại từ file dd9e83f0 · L-59 cite):**
- n_perp=32 · n_kho=20 · n_fresh=27 · vs |universe|=139
- |PERP∩FRESH|=6 · |KHO∩FRESH|=14 · |PERP∩KHO|=4 · |all|=2

**p15 UNIVERSE-BOUND:** ✅ all axes ≤ 139 · zero out-of-bound · zero silent-drops.

**DAO line V3.4:**
```
[DAO-DEFERRED coverage: fresh 6/31 · kho 6/31] đang-treo=15 · mới=5
```
(không CLEAR · không ANOMALY · chờ mắt mở operator)

**⭐-LIST 15 hanging + 5 new = 20 tổng (in lại từ file dd9e83f0):**

**3-trục (2):**
- MITO (FRESH-CHAIN+KHO-SAN+PERP) KHO=09-06ᴱ · FRES=09-06ᶶ · PERP=09-04ᴳ
- BULLA (FRESH-CHAIN+KHO-SAN+PERP) KHO=09-06ᴱ · FRES=09-05ᶶ · PERP=09-06ᴳ

**2-trục (18):**
| Sym | Axes | Star-line |
|---|---|---|
| 4 [NEW] | FRESH+KHO | FRES=09-06ᶶ · KHO=09-06ᴱ |
| CYS | FRESH+KHO | KHO=09-05ᴱ · FRES=09-05ᶶ |
| UAI [NEW] | FRESH+KHO | FRES=09-06ᶶ · KHO=09-06ᴱ |
| AKE | FRESH+KHO | FRES=09-06ᶶ · KHO=09-06ᴱ |
| BTR | FRESH+KHO | FRES=09-03ᶶ · KHO=09-03ᴱ |
| CLO | FRESH+KHO | FRES=09-03ᶶ · KHO=09-04ᴱ |
| HANA | FRESH+KHO | FRES=08-31ᶶ · KHO=09-05ᴱ |
| RIVER [NEW] | FRESH+KHO | FRES=09-06ᶶ · KHO=09-06ᴱ |
| 龙虾 | FRESH+KHO | KHO=09-05ᴱ · FRES=09-06ᶶ |
| AGT | FRESH+PERP | PERP=08-30ᴳ · FRES=09-05ᶶ |
| COLLECT | FRESH+PERP | PERP=09-02ᴳ · FRES=09-06ᶶ |
| ESPORTS | KHO+PERP | PERP=09-02ᵂ · KHO=09-04ᴱ |
| TUT | FRESH+KHO | FRES=09-06ᶶ · KHO=09-03ᴱ |
| AIA | FRESH+PERP | PERP=08-29ᵂ · FRES=09-03ᶶ |
| AIOT [NEW] | FRESH+PERP | PERP=08-30ᵂ · FRES=09-06ᶶ |
| B2 | FRESH+KHO | KHO=08-31ᴱ · FRES=09-02ᶶ |
| GIGGLE [NEW] | KHO+PERP | PERP=08-31ᴳ · KHO=09-06ᴱ |
| TRIA | FRESH+KHO | FRES=08-31ᶶ · KHO=08-31ᴱ |

⭐ **BỘ BA:** đang-treo=15 · mới-hôm-nay=5 (AIOT·4·GIGGLE·UAI·RIVER) · coverage-vector=perp∪wl 9∪25/31·kho 9∪6/31·fresh 6/31.

---

## SLOT 1: [PENDING-ANALYSIS-TEXT-WL-ÁN-LỆ]
> (2 text ANALYSIS verbatim chưa niêm — chờ operator drop text WL waterfall án-lệ)

## SLOT 2: [PENDING-ANALYSIS-TEXT-p15-SEMANTICS]
> (chờ operator drop text p15 semantics ruling · niêm bằng md5-thô)

---

## NHÁNH (a) STATUS · RELABEL V3.4

**Nhánh (a): ROOT-CAUSED (chưa CLOSED)**

- Root: WL universe-mismatch (u50=139 vs futures=527) + accidental dict-parsing.
- Fix: UNIVERSE-FILTER + KEY-NORM + EXPLICIT-PARSER + EPISODE×COVERAGE.
- Bằng chứng: WL n_perp collapse 131→16 · rác-parser=0 · p15 zero-oob.

**Công thức CLOSED theo ANALYSIS = (thước sạch) ∧ (số cũ re-measure) ∧ (MỘT ĐÊM không kích):**
- ✅ **thước sạch:** V3.4 waterfall + p15-names + DAO-DEFERRED labels
- ✅ **số cũ re-measure:** V3.4 = V3.3 numbers (dd9e83f0 md5 match)
- ⏳ **MỘT ĐÊM không kích:** Đêm-0 dry tối 07→08/09 · chờ chứng

**Nhánh (b) open:** 15 stars vẫn > expected_max=6 → siết seed rules gì thêm? (chờ ANALYSIS ruling)

---

## md5 chuỗi hiện tại (post V3.4)

| File | md5 |
|---|---|
| ledger_backfill_30d_v3_4.py | (compute post-SCP) |
| digest_summary_v2.py | 5f8c0562aae795f39157d950e1b94f9c |
| harness_digest_summary.py | 5ef9dec6bcdc01a35599d98c28b936e1 |
| axis_map.yaml | 1e134bea962c3cb3e5d33cf8a6c2356d |
| **events_2026-09-06.jsonl (V3.4 = V3.3)** | **dd9e83f0b9af5d475aa6dc043f3b6e98** |
| freshwatch_symbols.txt (u50=139) | e36183036102c52ed586d6c2bdcfc928 |
| ve_gop_lessons_batch_20260907_rev5.md | (this file) |

## Chờ chữ Tiên

7 items REV5 + 2 SLOTs ANALYSIS pending · bản REV4 `65ee9fe2` KHÔNG TRÌNH (label CLEAR sai · chưa mắt-mở).

**V3.4 status:**
- Rác-parser = 0 (parser CLEAN, dict/list explicit-handled)
- p15 semantics khớp máy: FAIL-ENGINE with NAMES + universe md5 cite
- L-59 md5 preserved: dd9e83f0
- DAO label: DAO-DEFERRED (chờ mắt mở)
- ⭐-01 COLLECT biên bản lần 5 PASS (survived universe + fresh 2/2)
- FRESH Δ-7 cut liệt đích danh (BEAT/DOS/ONE/B)
- Nhánh (a) = ROOT-CAUSED · chờ MỘT ĐÊM không kích để CLOSED

DEMO-5 sáng mai NẾU (1)-(6) xong · ⭐ block in caveat coverage · operator quyết bằng mắt mở.

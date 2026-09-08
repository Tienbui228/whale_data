# VÉ GỘP LESSONS · REV4 · KÝ 07/09 GATE-4 RECONCILE · trình Tiên MỘT chữ

**Trạng thái:** REV4 · bản REV3 `292a665bf79fd07da0ad9bfa3e4b0c3d` SUPERSEDED (mang số v3.2 nhiễm) · **KHÔNG trình bản cũ**.

**Updates so với REV3:**
- Item 4 §B-amendment thêm **KEY-NORM + UNIVERSE-FILTER** rule (bare-symbol strip USDT · filter u50 139-set trước union)
- Item 4 thêm **EPISODE×COVERAGE guard** (episode-start CHỈ khi lookback-14d có ≥k=10 ngày WL-coverage · thiếu = UNKNOWN-EPISODE, không seed)
- Item 5 p14 thêm **p15 UNIVERSE-BOUND pin** (n_unique mọi trục ≤ |universe 139|)
- Item 6 ⭐-01 COLLECT cập nhật cite theo V3.3 numbers
- Thêm **L-59 RECONCILE-KEY** rule (file md5 = source-of-truth · run vs file must match)
- BỘ BA đọc: (đang-treo · mới-hôm-nay · coverage-vector)

---

## 1. L-78-APPEND · vế-tồn-tại (EMPTY-GUARD)
Không đổi so với REV3. **Nội dung:**

> BỐN-VẾ L-78: (1) độc-lập · (2) không cùng-object · (3) đẳng-thức bất-biến · (4) **vế-tồn-tại** (empty-guard chống vacuous-pass).

---

## 2. L-79 · BLOCKER-BỊA + luật-con DEMO-RUỘT
Không đổi. *"Trình vỏ khi chưa kiểm ruột = exit-0-rỗng tầng trình diễn"*

---

## 3. Án-lệ-✓-suy · phái sinh L-79
Không đổi. `[UNVERIFIED]` explicit · cấm ✓ suy.

---

## 4. §B AMENDMENT · SỔ-ĂN-SỰ-KIỆN + SENT-only + FRESH-Δ + WL-EPISODE + KEY-NORM + UNIVERSE + EPISODE×COVERAGE (REV4)

**Amendment §B seed-list v1.2 (KÝ 07/09 GATE-4 RECONCILE verbatim):**

- **SỔ-ĂN-SỰ-KIỆN:** Ledger events chỉ record TÍN-HIỆU MỚI · membership-đứng-yên loại.

- **SENT-ANCHOR THỐNG NHẤT (V3.1):** Mọi trục anchor [SENT]-log:
  - GOM-H → `tg_relay.log`
  - FRESH/EXCH → `digest_daily_vps.log`
  - WL → `watchlist_cron.log` snapshot SAVED
  - Provenance file chỉ label, không phải quan tòa

- **FRESH-Δ-ONLY:** Loài-Δ≥50k duy nhất seed.

- **WL-EPISODE-HÓA (V3.2):** WL new-entry seed CHỈ khi token vắng List-B ≥`EPISODE_GAP=14` days trước đó. Dùng `cluster_episodes()` prod (từ `scripts/archive/_task_spot_cvd_annex125c_20260828.py:68-82` VERBATIM · cấm viết hàm mới). Tái-nhập <14d = refresh, KHÔNG seed.

- **KEY-NORM (V3.3 NEW):** Mọi symbol strip suffix `USDT` (bare-symbol) trước union · WL `list_b_tokens` chưa hậu tố nhưng gom_h in `SYMUSDT` → cùng khoá `SYM` sau norm. Cấm union raw-key.

- **UNIVERSE-FILTER (V3.3 NEW):** Load `data/config/freshwatch_symbols.txt` (139 u50 syms) · **filter mọi source** (WL/gom_h/fresh/exch) chỉ giữ symbols ∈ universe. WL `list_b_tokens` có 527 futures broader → filter cắt xuống u50.

- **EPISODE×COVERAGE (V3.3 NEW):** Episode-start CHỈ khi lookback-14d trước có ≥`COVERAGE_MIN_DAYS=10` days WL-coverage (WL state file exist). Thiếu k=10 → UNKNOWN-EPISODE, KHÔNG seed · log excluded `wl_UNKNOWN-EPISODE`. Unknown ≠ absent (coverage-law chiếu xuống episode).
  - **V3.3 evidence:** 28 sym-days UNKNOWN-EPISODE cắt · WL n_perp unique giảm 131→16.

- **COVERAGE-AXIS-UNION per §B (V3.2):** Digest coverage line theo TRỤC:
  - `PERP = union(gomh_days, wl_days)`
  - `KHO = union(H1_days, exch_days)`
  - `FRESH = fresh_days`

- **L-59 RECONCILE-KEY (V3.3 NEW):** File md5 = source-of-truth (không phải run stdout). Mọi cite dùng md5 file · reconcile audit định kỳ: read file → count → so run · lệch = ĐIỀU TRA (không auto-cover).

- **Test enforcement:** "30-đêm-không-gì-mới" · biến-cố true-zero test.

---

## 5. p14 STAR-COUNT-SANITY + p15 UNIVERSE-BOUND + STAR-LINE SOURCE-TAG (REV4)

**p14 (verbatim REV3, dải đạt):**

> **STAR-COUNT-SANITY:** n_⭐ đang-treo per target expected `[expected_min=4, expected_max=6]` · soft_ceiling=15. Vượt → `[STAR-ANOMALY]` IN DIGEST · cảnh báo · CẤM tự cắt · **GATE-4 branch(c) mandatory** trước khi bàn branch(b) siết seed.

**V3.3 status:** ⭐ đang-treo=**15** ≤ ceiling=15 → **ANOMALY-CLEAR** (đạt dải mềm) · vẫn > expected_max=6 → nhánh (b) siết-seed vẫn active question.

**p15 UNIVERSE-BOUND (V3.3 NEW):**

> **n_unique** mọi trục **≤ |universe|=139** (u50 bound). Vượt = FAIL-ENGINE · treo verdict, không so số. Log `p15_violations` per axis + out-of-bound sample.

**Enforcement:** `harness_digest_summary.py` p15 wired · `ledger_backfill_30d_v3_3.py` in `## p15 UNIVERSE-BOUND CHECK` block.

**STAR-LINE SOURCE-TAG (V3.2):** Mỗi ngày-trục kèm chữ nguồn:
- `ᴳ` = gom_h (relay)
- `ᵂ` = watchlist (episode)
- `ᴱ` = exch (digest)
- `ᶠ` = fresh (digest)

**Example (V3.3 target=09-06):**
```
COLLECT   2-trục (FRESH-CHAIN+PERP) PERP=09-02ᴳ · FRES=09-06ᶠ
BULLA     3-trục (FRESH-CHAIN+KHO-SAN+PERP) KHO=09-06ᴱ · FRES=09-05ᶠ · PERP=09-06ᴳ
```

---

## 6. ⭐-01 · COLLECT · ENTRY BẢN SỐNG (REV4 cite V3.3)

**⭐-01 SỐNG · KÝ 07/09 V3.3 GATE-4 RECONCILE:**

- **Symbol:** COLLECT
- **Axes:** {PERP, FRESH-CHAIN}
- **n_events (30d, V3.3):** 3 (unchanged v3.2/v3.1)
- **PERP fire (SENT-verified):**
  - target=**2026-09-02**
  - Relay hash `f58843a649cf` · HTTP 200 · resp_len=5906 · n_lines=53
  - Line: `🟢 • COLLECTUSDT [H2·ghế] ···· 0/4 LOW`
  - source-tag: **ᴳ** (gom_h)
- **FRESH-Δ latest:**
  - target=**2026-09-06**
  - Anchor: digest_daily_vps.log [SENT] Fresh-Wallets ok=True target 09-06
  - Snap-pair line: `Δ=+1,978,820`
  - source-tag: **ᶠ** (fresh)
- **Star-line format:** `COLLECT 2-trục (FRESH-CHAIN+PERP) PERP=09-02ᴳ · FRES=09-06ᶠ`
- **Verdict:** ⭐-PRE 2-trục · SỐNG chính thức
- **Cite (V3.3):** "fire target=09-02 · SENT 03/09 hash f58843a649cf · FRESH-Δ 06/09 SENT digest_daily_vps · V3.3 universe-filter PASS · V3.3 file md5 dd9e83f0"

**SEED-LESSON-01 hủy kích hoạt** · giữ khuôn.

---

## 7. §E ROUTING amendment · sender-dump hooks (5/5) + COVERAGE-UNION footer
Không đổi so với REV3.

---

## V3.3 numbers (bằng chứng cite · post KEY-NORM + UNIVERSE + EPISODE×COVERAGE)

**Backfill v3.3 target=09-06 window=30d:**

| Source | n_events | n_unique |
|---|---:|---:|
| gom_h_perp_SENT | 21 | 21 |
| gom_h_kho_SENT | 5 | 5 |
| exch_qualified_SENT | 35 | 19 |
| fresh_delta_SENT | 48 | 27 |
| **watchlist_b_episode_SENT** | **16** | **16** (V3.3 · universe+coverage-cut · v3.2 was 132/131) |
| **TOTAL** | **125** | **57 union** |

**EXCLUDED:**
- `gom_h_NO-relay-SENT` = 22 days
- `exch_NO-digest-SENT` = 25 days
- `fresh_NO-digest-SENT` = 25 days
- `wl_UNKNOWN-EPISODE` = 28 sym-days (V3.3 coverage guard active)

**Coverage-per-axis:** PERP-gomh=9/31 · KHO-SAN-gomh=9/31 · KHO-SAN-exch=6/31 · FRESH-CHAIN=6/31 · WL=25/31

**Coverage axis-union:** PERP=union(9,25) · KHO=union(9,6)=9 · FRESH=6

**Ma trận giao (post universe-filter):**
- n_perp=32 · n_kho=20 · n_fresh=27 · vs |universe|=139
- |PERP∩FRESH|=6 · |KHO∩FRESH|=14 · |PERP∩KHO|=4 · |all|=2

**p15 UNIVERSE-BOUND:** ✅ all axes ≤ 139 · zero violations · zero out-of-bound symbols.

**⭐ BỘ BA:**
- đang-treo = **15** (v3.2: 22 · Δ-7)
- mới-hôm-nay = 5 (AIOT, "4", GIGGLE, UAI, RIVER)
- coverage-vector = perp=9/31 · kho-exch=6/31 · fresh=6/31 · wl=25/31
- **tổng = 20** · **đạt ceiling=15 · ANOMALY-CLEAR** (nhưng > expected_max=6 → nhánh (b) siết-seed vẫn open)

**⭐ danh sách (V3.3):**
- **3-trục (2):** MITO, BULLA
- **2-trục (18):** 4·CYS·UAI·AKE·BTR·CLO·HANA·RIVER·龙虾·AGT·COLLECT·ESPORTS·TUT·AIA·AIOT·B2·GIGGLE·TRIA

**L-59 RECONCILE:** file md5 = `dd9e83f0b9af5d475aa6dc043f3b6e98` · **run vs file PASS** (5/5 sources match) ✅

---

## md5 chuỗi hiện tại (post V3.3)

| File | md5 |
|---|---|
| ledger_backfill_30d_v3_3.py | d5b1c2910f7356442de320d861a31e10 |
| digest_summary_v2.py | 5f8c0562aae795f39157d950e1b94f9c |
| harness_digest_summary.py | 5ef9dec6bcdc01a35599d98c28b936e1 |
| axis_map.yaml | 1e134bea962c3cb3e5d33cf8a6c2356d |
| ve_gop_lessons_batch_20260907_rev4.md | (this file) |
| **events_2026-09-06.jsonl (V3.3)** | **dd9e83f0b9af5d475aa6dc043f3b6e98** |
| freshwatch_symbols.txt (universe u50=139) | (VPS canonical) |

## Chờ chữ Tiên

7 items REV4 · bản REV3 `292a665bf79fd07da0ad9bfa3e4b0c3d` SUPERSEDED (mang số v3.2 nhiễm) · KHÔNG trình.

**V3.3 numbers CLEAN:**
- ⭐ đang-treo=15 đạt ceiling (ANOMALY-CLEAR)
- p15 UNIVERSE-BOUND PASS
- L-59 RECONCILE PASS (file=run)
- WL n_perp collapsed 131→16 (v3.2 nổ-trên-giấy fixed)

**Nhánh (a) closed:** WL universe-mismatch = root cause identified & fixed via UNIVERSE-FILTER + EPISODE×COVERAGE.
**Nhánh (b) open:** 15 stars vẫn > expected_max=6 → siết seed rules gì thêm để đạt dải 4-6? (chờ ANALYSIS ruling)

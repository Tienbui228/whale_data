# VÉ GỘP LESSONS · REV3 · KÝ 07/09 GATE-4 · trình Tiên MỘT chữ

**Trạng thái:** REV3 · bản REV2 `db79a36016d42cdbcf7897b9fd223c6e` SUPERSEDED · **KHÔNG trình bản cũ**.

**Updates so với REV2:**
- Item 4 §B-amendment thêm **WL-EPISODE-HÓA** (via `cluster_episodes` prod archive)
- Item 4 thêm **COVERAGE-PER-AXIS AXIS-UNION** rule (per §B: PERP=union(gomh,wl) · KHO=union(H1,exch))
- Item 6 ⭐-01 COLLECT cập nhật cite theo v3.2 numbers
- Thêm **STAR-LINE SOURCE-TAG** rule + BẢNG TUỔI-SAO GATE-4 branch(c)

---

## 1. L-78-APPEND · vế-tồn-tại (EMPTY-GUARD)
Không đổi so với REV2. **Nội dung:**

> BỐN-VẾ L-78: (1) độc-lập · (2) không cùng-object · (3) đẳng-thức bất-biến · (4) **vế-tồn-tại** (empty-guard chống vacuous-pass).

---

## 2. L-79 · BLOCKER-BỊA + luật-con DEMO-RUỘT
Không đổi. *"Trình vỏ khi chưa kiểm ruột = exit-0-rỗng tầng trình diễn"*

---

## 3. Án-lệ-✓-suy · phái sinh L-79
Không đổi. `[UNVERIFIED]` explicit · cấm ✓ suy.

---

## 4. §B AMENDMENT · SỔ-ĂN-SỰ-KIỆN + SENT-only + FRESH-Δ-only + WL-EPISODE + COVERAGE-AXIS-UNION (REV3)

**Amendment §B seed-list v1.1 (KÝ 07/09 GATE-4 verbatim):**

- **SỔ-ĂN-SỰ-KIỆN:** Ledger events chỉ record TÍN-HIỆU MỚI · membership-đứng-yên loại (loài-cum-standing 258/36 evidence GATE-3).

- **SENT-ANCHOR THỐNG NHẤT (V3.1):** Mọi trục anchor [SENT]-log:
  - GOM-H → `tg_relay.log`
  - FRESH/EXCH → `digest_daily_vps.log`
  - WL → `watchlist_cron.log` snapshot SAVED
  - Provenance file chỉ label, không phải quan tòa

- **FRESH-Δ-ONLY:** Loài-Δ≥50k duy nhất seed.

- **WL-EPISODE-HÓA (V3.2 GATE-4 NEW):** WL new-entry seed CHỈ khi token vắng List-B ≥`EPISODE_GAP=14` days trước đó. Dùng `cluster_episodes()` prod (từ `scripts/archive/_task_spot_cvd_annex125c_20260828.py:68-82` VERBATIM · cấm viết hàm mới). Tái-nhập <14d = refresh, KHÔNG seed.
  - **Evidence 3-cột (v3.2 target=09-06):** before=148 · after-baseline=117 · after-episode=**80** (episode-rule cắt 37 refresh events)

- **COVERAGE-AXIS-UNION per §B (V3.2 GATE-4 NEW):** Digest coverage line theo TRỤC (union sub-sources):
  - `PERP = union(gomh_days, wl_days)`
  - `KHO = union(H1_days, exch_days)`
  - `FRESH = fresh_days`
  - Split sub-source giữ trong diagnostic table (chẩn đoán) · digest chỉ union.

- **Test enforcement:** "30-đêm-không-gì-mới" · biến-cố true-zero test.

---

## 5. p14 · STAR-COUNT-SANITY + STAR-LINE SOURCE-TAG (REV3)

**p14 (verbatim REV2, thêm GATE-4 flow):**

> **STAR-COUNT-SANITY:** n_⭐ đang-treo per target expected `[expected_min=4, expected_max=6]` · soft_ceiling=15. Vượt → `[STAR-ANOMALY]` IN DIGEST · cảnh báo · CẤM tự cắt · **GATE-4 branch(c) mandatory** trước khi bàn branch(b) siết seed.

**STAR-LINE SOURCE-TAG (V3.2 GATE-4 NEW):** Mỗi ngày-trục trên dòng ⭐ kèm chữ nguồn:
- `ᴳ` = gom_h (relay)
- `ᵂ` = watchlist (episode)
- `ᴱ` = exch (digest)
- `ᶠ` = fresh (digest)

**Example (v3.2 target=09-06):**
```
COLLECT   2-trục (FRESH-CHAIN+PERP) PERP=09-02ᴳ · FRES=09-06ᶠ
CROSS     2-trục (FRESH-CHAIN+PERP) PERP=08-19ᵂ · FRES=09-05ᶠ
```

Operator phân biệt ghế-fire (`ᴳ`) vs list-entry (`ᵂ`) khi soi.

---

## 6. ⭐-01 · COLLECT · ENTRY BẢN SỐNG (REV3 cite v3.2)

**⭐-01 SỐNG · KÝ 07/09 V3.2 GATE-4:**

- **Symbol:** COLLECT
- **Axes:** {PERP, FRESH-CHAIN}
- **n_events (30d, v3.2):** 3
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
- **Cite (v3.2):** "fire target=09-02 · SENT 03/09 hash f58843a649cf · FRESH-Δ 06/09 SENT digest_daily_vps · WL-EPISODE-RULE không impact (chỉ FRESH+PERP)"

**SEED-LESSON-01 hủy kích hoạt** · giữ khuôn.

---

## 7. §E ROUTING amendment · sender-dump hooks (5/5) + COVERAGE-UNION footer
Không đổi so với REV2 · footer digest thêm axis-union coverage line.

---

## GATE-4 branch(c) · BẢNG TUỔI-SAO (KÝ 07/09 V3.2 · trước bàn branch(b))

**⭐ đang-treo = 22 · phân bố tuổi:**

| Age | n_tokens | Symbols |
|---|---:|---|
| 0d (hôm nay) | **8** | RIVER, 4, MITO, TUT, COLLECT, 龙虾, AKE, BULLA |
| 1-3d | 9 | CROSS, SIGN, AGT, HANA, CYS, CLO, ESPORTS, AIA, BTR |
| 4-7d | 5 | XAN, 我踏马来了, B2, LAB, TRIA |
| >7d | **0** | (none) |

**Chẩn đoán trỏ vào số:** 22 sao TẤT CẢ có latest signal ≤7d fresh. **KHÔNG có aged/stale tokens cần cắt bằng TTL.** Confluence density cao 3-5d gần đây · WL-EPISODE rule đã bỏ 37 refresh events nhưng ⭐ vẫn tăng (20→22) vì episode-rule catches earlier entries in window (WL n_perp unique 110→131).

**Question cho ANALYSIS branch(b):** siết thêm rules gì để dải 4-6? Options theo dõi:
- Time-proximity requirement (2 axes phải trong ≤N ngày)
- Axis-density gate (chỉ 1 event/axis/token trong window)
- Confluence-strength ranking (top-N by combined recency+strength)

Chờ ANALYSIS ruling.

---

## V3.2 numbers (bằng chứng cite)

**Backfill v3.2 target=09-06:**
| Source | n_events | n_unique |
|---|---:|---:|
| gom_h_perp_SENT | 21 | 21 |
| gom_h_kho_SENT | 5 | 5 |
| exch_qualified_SENT | 35 | 19 |
| fresh_delta_SENT | 55 | 31 |
| **watchlist_b_episode_SENT** | **132** | **131** (V3.2 episode-rule · ratio 1.01) |
| **TOTAL** | **248** | **165 union** |

**Coverage axis-union:** PERP=union(9,25) · KHO=union(9,6)=9 · FRESH=6

**Ma trận giao:** n_perp=144 · n_kho=20 · n_fresh=31 · |PERP∩FRESH|=12 · |KHO∩FRESH|=14 · |PERP∩KHO|=9 · |all|=5

**⭐:** đang-treo=22 · mới-hôm-nay=3 · tổng=25 · **⚠ STAR-ANOMALY** persist

---

## md5 chuỗi hiện tại (post V3.2)

| File | md5 |
|---|---|
| ledger_backfill_30d_v3_2.py | (compute) |
| digest_summary_v2.py | 5f8c0562aae795f39157d950e1b94f9c |
| harness_digest_summary.py | 5ef9dec6bcdc01a35599d98c28b936e1 |
| axis_map.yaml | 1e134bea962c3cb3e5d33cf8a6c2356d |
| ve_gop_lessons_batch_20260907_rev3.md | (this file) |
| events_2026-09-06.jsonl (v3.2) | d0aa3a9d96130027264a03a8349f8cbd |

## Chờ chữ Tiên

7 items REV3 · bản REV2 `db79a36016d42cdbcf7897b9fd223c6e` SUPERSEDED · KHÔNG trình.
**GATE-4 branch(b) chờ ANALYSIS ruling siết seed rules để đạt dải 4-6.**

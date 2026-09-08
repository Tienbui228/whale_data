# VÉ GỘP LESSONS · REV2 · KÝ 07/09 V3.1 · trình Tiên ký MỘT PHÁT

**Trạng thái:** REV2 · bản `0db64191` (rev1) SUPERSEDED · KHÔNG trình bản cũ.
**Updates so với rev1:**
- Item 4/6 cập nhật theo backfill v3.1 (SENT-anchor thống nhất mọi trục)
- Item 6 sửa FRESH-Δ date COLLECT → **09-06** (v3.1 recover từ snap-pair khi digest [SENT] chấp nhận anchor)
- Item 5 p14 thêm "in trong digest khi vượt" (không chỉ harness)
- Thêm items §B-amendment cụ thể + COVERAGE-PER-AXIS rule + WL-baseline-rule

---

## 1. L-78-APPEND · vế-tồn-tại (EMPTY-GUARD)

**Append vào L-78 SEAL-KHÔNG-PHẢI-GƯƠNG bản BA-VẾ:**

> **VẾ-TỒN-TẠI (EMPTY-GUARD):** Nếu child-artifact non-empty ∧ vế-digest = 0 ⇒ **VACUOUS-PASS = FAIL**. Ba-vế L-78 mở rộng thành BỐN-VẾ:
> - (1) độc-lập
> - (2) không cùng-một-object
> - (3) đẳng-thức theo bất-biến
> - (4) **vế-tồn-tại:** empty-guard chống vacuous-pass · assert phải thực-sự-đo-cái-gì-đó

**Án lệ 07/09:** p1' harness ban đầu report PASS với `n_digest_syms=0` khi digest có `$SYM` markers. FAIL-VACUOUS bắt bằng EMPTY-GUARD sau FIX-ROUND-3.

**Enforcement:** `harness_digest_summary.py` `_empty_guard()` helper wired.

---

## 2. L-79 · BLOCKER-BỊA + luật-con DEMO-RUỘT (verbatim operator 07/09)

**L-79 BLOCKER-BỊA:** Đưa placeholder `PENDING-<x>` vào tin trình-diễn khi thực chất nguồn artifact đã sẵn = **bịa blocker**. Placeholder không có căn cứ = ERRATA + xóa.

**Luật-con DEMO-RUỘT (verbatim):** *"Trình vỏ khi chưa kiểm ruột = exit-0-rỗng tầng trình diễn"*

Preview/demo phải kiểm ruột trước khi trình. Placeholder = giả xanh · cùng lớp L-66 SILENT-FAIL.

**Án lệ:** `assembler_preview.py` PENDING-ANALYSIS-V1.1 4 khối (SUPERSEDED bởi `assembler_v2.py`).

---

## 3. Án-lệ-✓-suy · phái sinh L-79

> Nhãn nào chưa có seal đứng sau → in `[UNVERIFIED]` · **CẤM ✓ suy**.

Harness phân biệt {PASS ✅ · FAIL ❌ · UNVERIFIED [tag]}.

**Án lệ:** `harness_digest_summary.py` rev1 in `[UNVERIFIED PINS]` khi p2-p6 chưa build · rev2 build đủ · rev3 zero UNVERIFIED.

---

## 4. §B AMENDMENT · SỔ-ĂN-SỰ-KIỆN + SENT-only + FRESH-Δ-only + WL-BASELINE + COVERAGE (V3.1 cập nhật)

**Amendment §B seed-list v1.1 (KÝ 07/09 V3.1 verbatim):**

- **SỔ-ĂN-SỰ-KIỆN:** Ledger events chỉ record TÍN-HIỆU MỚI (biến-cố), KHÔNG record membership-đứng-yên. Bằng chứng GATE-3: loài-cum-standing 258 events/36 unique (ratio 7.2/token/30d) = membership đội lốt event.

- **SENT-ANCHOR THỐNG NHẤT (V3.1 mới):** Mọi trục anchor vào [SENT]-log của CHÍNH kênh nó:
  - GOM-H (PERP+KHO) → `tg_relay.log [SENT]`
  - FRESH/EXCH → `digest_daily_vps.log [SENT]` + Nansen snap same-target
  - WL new-entry → `watchlist_cron.log` snapshot SAVED / Telegram OK
  - **Provenance file chỉ label, không phải quan tòa · [SENT] log là quan tòa**

- **FRESH-Δ-ONLY:** FRESH seed = loài-Δ≥50k DUY NHẤT. Cum-standing → context-tag.

- **WL-BASELINE RULE (V3.1 mới):** WL new-entry chỉ hợp lệ khi D-1 baseline TỒN TẠI. Thiếu D-1 → zero-seed + ghi coverage-gap. Cấm đổ nguyên list thành "mới".

- **COVERAGE-PER-AXIS = stale-contract (V3.1 mới):** Bảng số ngày có SENT-anchor / N-day window per axis. Footer digest in `coverage: PERP x/30 · KHO y/30 · FRESH z/30`. Phân biệt "chợ im" (in coverage nhưng zero fires) vs "sổ mù" (no SENT-anchor day).

- **Test enforcement:** "30-đêm-không-gì-mới" · biến-cố true zero vs membership-only nổ vì cum-standing luôn có.

---

## 5. p14 · STAR-COUNT-SANITY (harness + dải-yaml + IN DIGEST)

**Nội dung pin p14 (V3.1 cập nhật):**

> **STAR-COUNT-SANITY:** n_⭐ đang-treo per target expected trong dải `[expected_min, expected_max]`. Vượt `soft_ceiling` → in `[STAR-ANOMALY]` **TRONG DIGEST** (không chỉ trong harness) · cảnh báo · **CẤM tự cắt** (require GATE-4 diagnosis).

**Dải yaml (chờ chữ Tiên khắc):**
```yaml
star_count_sanity:
  expected_min: 4
  expected_max: 6
  soft_ceiling: 15
  ruling_source: "FIX-ROUND-3b + V3.1 operator directive 07/09"
```

**Enforcement:** `harness_digest_summary.py` p14 wired + `digest_summary_v2.py` `_star_block_from_ledger` in `[STAR-ANOMALY đang-treo=N>ceiling=15]` inline khi vượt.

**Current V3.1 target=09-06:** ⭐ đang-treo=**20** > ceiling=15 → **STAR-ANOMALY** in digest. Chờ ANALYSIS ruling GATE-4 nếu vượt persistent.

---

## 6. ⭐-01 · COLLECT · ENTRY BẢN SỐNG (V3.1 update)

**⭐-01 chính thức SỐNG · KÝ 07/09 V3.1 (rev từ rev1):**

- **Symbol:** COLLECT
- **Axes:** {PERP, FRESH-CHAIN}
- **n_events (30d):** 3 (v3.1 SENT-verified · tighter than v3's 7)
- **PERP fire (SENT-verified):**
  - target=**2026-09-02**
  - SENT via `tg_relay_gom_h.py` at `2026-09-03T01:20:02Z`
  - Relay hash: **`f58843a649cf`** · HTTP 200 · resp_len=5906 · n_lines=53
  - Line: `🟢 • COLLECTUSDT [H2·ghế] ···· 0/4 LOW`
  - Block: `━━ CAMPAIGN-PRE · 02/09 · 2026-09-02 ━━` · REO 7
- **FRESH-Δ latest (V3.1 fix · từ 09-03 → 09-06):**
  - target=**2026-09-06** (v3.1 correctly recovered from snap-pair when digest_daily_vps [SENT] anchored)
  - Anchor: `digest_daily_vps.log [SENT] Fresh-Wallets ok=True` for target 2026-09-06
  - Snap-pair line: `snap-pair Δ=+1,978,820`
- **Verdict:** ⭐-PRE 2-trục · SỐNG chính thức
- **Cite (updated V3.1):** "fire target=09-02 · SENT 03/09 hash f58843a649cf · FRESH-Δ 06/09 SENT anchor digest_daily_vps · qua re-seed v3.1"

**SEED-LESSON-01 hủy kích hoạt** · giữ làm khuôn cho án COLLECT-like không đạt SENT-verified.

---

## 7. §E ROUTING amendment · sender-dump hooks (5/5 wired) + COVERAGE footer

**Ghi vào §E routing spec (V3.1):**

> Từ 07/09 · 5 sender scripts wire `artifact_dump.dump_as_sent()` hook sau HTTP 200. Sinh `data/artifacts/tg_final_<renderer>_<target>.txt` + `.jsonl` mỗi lần cron fire. Đủ 6/6 tin → posthoc RETIRE candidate.

**V3.1 mới:** Digest footer thêm coverage line:
```
━━ footer ━━
coverage: PERP x/30 · KHO y/30 · FRESH z/30 · WL w/30
ledger_state=... · fixture_master=...
cites: gomh=... · fresh=... · exch=... · hedge=... · rong=...
concat-seal=...
```

Consumer đọc coverage line để phân biệt "chợ im" vs "sổ mù".

**Enforcement:** `scripts/lib/artifact_dump.py` + `digest_summary_v2.py` footer render coverage line inline.

---

## V3.1 numbers (bằng chứng cite)

**Backfill v3.1 target=09-06 window=30d:**
| Source | n_events | n_unique |
|---|---:|---:|
| gom_h_perp_SENT | 21 | 21 |
| gom_h_kho_SENT | 5 | 5 |
| exch_qualified_SENT | 35 | 19 |
| fresh_delta_SENT | 55 | 31 |
| watchlist_b_new_SENT | 137 | 110 |
| **TOTAL** | **253** | **146 (union)** |

**Coverage-per-axis:** PERP=9/31 · KHO=9/31 · KHO-exch=6/31 · FRESH=6/31 · WL=16/31

**⭐ hai con số:** đang-treo=20 · mới-hôm-nay=4 · tổng=24 · ⚠ STAR-ANOMALY

**Excluded:**
- gom_h_NO-relay-SENT: 22 days
- exch_NO-digest-SENT: 25 days
- fresh_NO-digest-SENT: 25 days
- wl_baseline_missing: 15 days

---

## md5 chuỗi hiện tại (post V3.1)

| File | md5 |
|---|---|
| ledger_backfill_30d_v3_1.py | (compute) |
| digest_summary_v2.py (with STAR-ANOMALY inline) | (compute) |
| harness_digest_summary.py (p13 SENT + p14 anomaly) | (compute) |
| axis_map.yaml (star_count_sanity block) | 1e134bea962c3cb3e5d33cf8a6c2356d |
| ve_gop_lessons_batch_20260907_rev2.md | (this file · compute) |
| events_2026-09-06.jsonl (v3.1 SENT-verified) | 3e29511a3fe9f2f8d4c5052b0b166595 |

## Chờ chữ Tiên

7 items REV2 trên trình Tiên ký MỘT PHÁT. Bản rev1 `0db64191` SUPERSEDED · KHÔNG trình.

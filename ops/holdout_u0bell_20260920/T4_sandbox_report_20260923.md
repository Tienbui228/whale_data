# T4 · Nháp sandbox U1-transition · KHÔNG sửa prod · KHÔNG SCP

Doctrine áp: #11 xem-không-để-dấu · #16 mọi bảng NGUỒN · #17 code identity + kiểm ca ký · #18 mọi số mang gốc.

**Sandbox location:** `ops/holdout_u0bell_20260920/sandbox_u1/` · KHÔNG chạm prod.

---

## T4.1 · Sandbox setup + A1 fix

**Files (md5):**

| item | md5 | source |
|------|-----|--------|
| Original snap b_state_tracker.py | `b422d88e8898bb02fbaae782ba5b5e51` | ops/.../b_state_tracker.py.snap |
| **Patched sandbox b_state_tracker.py** | `378e59469f4ff65a6fd5ca6457f31a15` | sandbox_u1/scripts/b_state_tracker.py |
| Original snap events_build.py | `2a6ab5a578e91e8d2b3483347faf7b59` | ops/.../events_build.py.snap |
| Sandbox events_build.py (chỉ patch sys.path prepend) | (khác) | sandbox_u1/scripts/events_build.py |
| Original snap u0_bell.py + u0_bell_audit.py + u0_class_tier.py | unchanged | copied from R0 snap |

**Fix A1 áp dụng:**

```diff
--- b_state_tracker.py.orig
+++ sandbox_u1/scripts/b_state_tracker.py
@@ Line 214 @@
-        if d_plus_k <= CROSS_D_PLUS_MAX:
+        if d_plus_k <  CROSS_D_PLUS_MAX:  # T4/A1 sandbox · dpk=5 vào nhánh U1

@@ After line 225 @@ Add blind handling
+        # T4/blind (U1b sandbox) · phân biệt blind vs u1 thật FAIL · KHÔNG đổi signature
+        blind_v1 = ratios.get("v1") is None
+        blind_v2 = ratios.get("v2") is None
+        blind = blind_v1 or blind_v2
+        blind_reason = None
+        if blind_v1 and blind_v2: blind_reason = "OI+acc"
+        elif blind_v1: blind_reason = "acc"
+        elif blind_v2: blind_reason = "OI"
+        if blind:
+            if 5 <= d_plus_k <= 7:
+                result[tok] = {"tier": "CROSS", ..., "u1_state": "QUÁ HẠN", "blind_reason": blind_reason}
+                continue
+            elif d_plus_k >= 8:
+                result[tok] = {"tier": "FAILED-BLIND", ..., "blind_reason": blind_reason}
+                continue
```

**events_build.py KHÔNG đổi số học** · chỉ patch sys.path để dùng sandbox b_state_tracker (khớp shadow harness R3 pattern).

---

## T4.2 · Replay 8 target · btier diff prod vs sandbox

**NGUỒN:** sandbox events tại `ops/holdout_u0bell_20260920/sandbox_u1/data_out/` · so với prod `data/artifacts/`.

**Chỉ tokens có tier khác giữa 2 bản (14 diffs):**

| target | tok | D_cross | dpk | tier PROD | tier SANDBOX | u1_state |
|--------|-----|---------|:---:|:---------:|:------------:|:--------:|
| 09-15 | BEAT | 09-10 | 5 | CROSS | **FAILED** | - |
| 09-15 | RAVE | 09-10 | 5 | CROSS | **FAILED** | - |
| 09-17 | BSB | 09-12 | 5 | CROSS | **FAILED** | - |
| 09-17 | ORDER | 09-12 | 5 | CROSS | **FAILED** | - |
| 09-17 | LAB | - | 0 | cand | **-** | - |
| 09-18 | C | - | 0 | cand | **-** | - |
| 09-18 | TAG | - | 0 | cand | **-** | - |
| 09-19 | TRUTH | 09-14 | 5 | CROSS | **FAILED** | - |
| 09-19 | ARX | - | 0 | cand | **-** | - |
| 09-19 | GOAT | - | 0 | cand | **-** | - |
| 09-21 | IDOL | 09-16 | 5 | CROSS | **FAILED** | - |
| 09-22 | SPACE | 09-17 | 5 | CROSS | **FAILED** | - |
| 09-22 | BAS | - | 0 | cand | **-** | - |
| 09-22 | COOKIE | - | 0 | cand | **-** | - |

**Đo:**
- **7 tokens transition CROSS → FAILED tại D+5** (intent A1)
- **7 tokens `cand` mất khỏi btier state** (SIDE EFFECT · L2/L3 tại dpk=5 · trước là cand · sau vào nhánh L2/L3 audit reject line 228-234 · KHÔNG entry result)

**Side effect explanation:** trong prod line 214 `dpk<=5`: L2/L3 tại dpk=5 rơi vào block 217-221 → cand (if hedge). Sau A1 line 214 `dpk<5`: dpk=5 rơi vào nhánh 224 → check U1 → nếu L2/L3 (line 228) → audit reject continue → KHÔNG entry.

7 tokens dropped: LAB · C · TAG · ARX · GOAT · BAS · COOKIE — đều L2/L3 tại D+5 (không L1) · hedge div ≤0.5 · trước cand · sau reject.

**Cần DEV chấm:** side effect này có chấp nhận không · hay cần handle L2/L3 tại dpk=5 riêng?

---

## T4.3 · Retro 7 tokens · CROSS D+5 → tier sandbox

| tok | D_cross | D+5 | tier prod | tier sandbox | u1_verdict |
|-----|---------|-----|:---------:|:------------:|:----------:|
| RAVE | 09-10 | 09-15 | CROSS | **FAILED** | FAIL |
| BEAT | 09-10 | 09-15 | CROSS | **FAILED** | FAIL |
| BSB | 09-12 | 09-17 | CROSS | **FAILED** | FAIL |
| ORDER | 09-12 | 09-17 | CROSS | **FAILED** | FAIL |
| TRUTH | 09-14 | 09-19 | CROSS | **FAILED** | FAIL |
| IDOL | 09-16 | 09-21 | CROSS | **FAILED** | FAIL |
| SPACE | 09-17 | 09-22 | CROSS | **FAILED** | FAIL |

**7/7 PASS:** all transition đúng đêm D+5 · khớp u1 verdict FAIL. **Trễ 1 đêm đã fix.**

---

## T4.4 · R3 U0-BELL byte-identical

**Chuẩn hoá V5a:** type ∈ {bell, bell_blind, bell_near} · sort (tok, D, type) · drop computed_at.

| target | prod n | prod md5 | sandbox n | sandbox md5 | match |
|--------|-------:|----------|-----------:|-------------|:---:|
| 09-21 | 7 | `2f41f23f8bd3` | 7 | `2f41f23f8bd3` | **True** |
| 09-22 | 3 | `1aa2e1c50496` | 3 | `1aa2e1c50496` | **True** |

**R3 PASS:** U0-BELL rows KHÔNG bị impact bởi b_state_tracker A1 fix (đúng như thiết kế · u0_bell.py không đổi).

---

## T4.5 · Pins đen-rồi-xanh

### Pin ca đã ký (3 cases)

**NGUỒN retention:** `data/export/freshwatch_daily_2026-{07,08,09}.csv` · check D-1 và D+5 acc/oi.

| case | acc D-1 | oi D-1 | acc D+5 | oi D+5 | v1 | v2 | u1_pass | replay |
|------|--------:|-------:|--------:|-------:|-----:|-----:|:---:|:---:|
| BTR 08-12 → CONFIRMED 08-17 | 3.6664 | 169537 | 1.8393 | 367943 | 0.5017 | 2.170 | **True** | **PASS** |
| LIGHT 08-29 → FAILED D+5 | 3.9925 | 432329 | 3.4763 | 403417 | 0.8707 | 0.933 | False | **PASS** |
| IDOL 09-16 → FAILED 09-21 | 3.1545 | 465222 | 2.8521 | 573249 | 0.9041 | 1.232 | False | **PASS** |

**3/3 pins PASS** · data retention đầy đủ · không N/A.

### Pin hằng số

`events_build.py:119` (chú ý: DEV nói :120 · thực tế :119): `if dpk == 5:` — emit u1 event condition. Hằng số `5` **khớp** `CROSS_D_PLUS_MAX == 5` (b_state_tracker.py:48). **PIN PASS.**

### Pin mutation (đảo biên về `<= 5`)

Sandbox mutation: `< CROSS_D_PLUS_MAX` → `<= CROSS_D_PLUS_MAX` (revert). Re-run events_build target 09-21.

**Kết quả:** IDOL btier=CROSS · k=5 · u1 verdict=FAIL · v1=0.9041 v2=1.2322 (both non-null · KHÔNG blind).

**p84 mới ("không tồn tại dòng CROSS D+5 kèm u1 FAIL không-blind"):** **FAIL** (đúng như expected · mutation đảo biên phá pin) → **1 vi phạm** (IDOL).

Restore A1: `<= CROSS_D_PLUS_MAX` → `< CROSS_D_PLUS_MAX` · md5 trở về `378e59469f4f`. ✓

### Pin blind (data mutation) — SKIP

Data mutation (xoá hàng D+5 của 1 token trong bản sao data) yêu cầu tạo sandbox data · không có mock hiện tại. Sẽ implement khi DEV ok toàn bộ hướng T4.

---

## T4.6 · ERRATA đêm đầu (draft)

**Tính từ dữ liệu:**
- Trễ 1 đêm từ **09-15** tới **09-22** (đêm cuối trước fix) · **7 tokens** transition CROSS D+5 kèm u1 FAIL (thay vì FAILED trực tiếp)
- Từ **đêm apply fix (TBD, dự kiến sau 25/09)** chấm đúng D+5

**Text ERRATA:**
```
⚠ ERRATA U1-transition: U1 chấm trễ 1 đêm từ 15/09 tới 22/09 (7 token: RAVE · BEAT ·
BSB · ORDER · TRUTH · IDOL · SPACE) · tầng B in "CROSS" tại D+5 kèm u1 FAIL trong file
sự kiện. Từ 25/09 (đêm apply A1) chấm đúng D+5.
```

**Side effect nhắc:** 7 tokens L2/L3 tại dpk=5 mất khỏi tầng cand (LAB · C · TAG · ARX · GOAT · BAS · COOKIE) · thay vì cand giờ audit-rejected. Cần DEV xác nhận.

---

## T4.6b · Docs proposal cho CLAUDE.md #12 (nguyên văn U1a chờ DEV chuyển)

**NGUỒN DEV vòng T4:** "U1a = khô bằng ≥5 target REPLAY (wire 25/09)"

**Đề xuất text nguyên văn thêm vào #12:**
> Khô = ≥5 target replay cho thay đổi render/tầng đọc (VD b_state_tracker · digest_summary). Đêm lịch (dry pipeline mỗi đêm) chỉ bắt buộc cho động cơ/sender (VD master_preview_send · hedge_v2_sender). ANALYSIS U1a · 25/09.

Chưa apply · chờ DEV ký nguyên văn.

---

## T4.6c · Nợ ghi sổ (không sửa hôm nay)

- Dòng u1 trong `events_<T>.jsonl` vẫn ghi `verdict=FAIL` cho blind (events_build.py:126-131 không phân biệt blind)
- Fix: sau 21/10 (hết hold-out) · sửa events_build.py hoặc _check_u1_v2v1 signature
- **KHÔNG sửa trong window** hold-out

---

## Ranh giới đã giữ

- **KHÔNG SCP** (DEV chờ postcheck HEDGE sáng 24/09 mới ra lệnh SCP riêng)
- **KHÔNG sửa prod** (sandbox chỉ trong `ops/holdout_u0bell_20260920/sandbox_u1/`)
- **KHÔNG chạm events_build.py.snap** (giữ bộ đóng băng R0)
- **KHÔNG đổi signature `_check_u1_v2v1`** (per DEV directive)
- Sandbox `b_state_tracker.py` md5 sau patch: `378e59469f4ff65a6fd5ca6457f31a15`

Agent IN SỐ · KHÔNG kết luận · DEV chấm.

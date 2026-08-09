---
title: L-44 Acceptance — GOM Daily Cron (v2)
date: 2026-08-09
status: SIGNED
author: agent session 25 (v2 sau sửa)
signed_by: Tien (operator)
signed_text: "Tôi ký l44_acceptance_gom_daily_20260809.md — acceptance gom_scan delivery chain; A6 PENDING-alias flag OFF; GOM-C ngoài phạm vi, chờ gate 15/08."
---

# L-44 Acceptance — GOM Daily Delivery Chain

**Đối tượng:** `scripts/run_gom_daily.py` cron 01:25 UTC trên VPS  
**Quy tắc L-44:** Missing dependency → ERROR + exit≠0 + alert (cấm no-op êm). (CLAUDE.md)  
**Yêu cầu ký:** Operator xác nhận 7 mục + M1/A6 test kết quả.

---

## 7-Item Compliance Checklist

### Mục 1 — Script định nghĩa

| Field | Giá trị |
|-------|---------|
| Script | `scripts/run_gom_daily.py` |
| Commit triển khai | `c7e67cd` (split-message + fail-exit + heartbeat fix) |
| File hiện tại | Đã SCP → VPS canonical (MD5 khớp) |

**Status:** DONE ✓

---

### Mục 2 — Spec phiên bản + Conformance A6

| Signal | Formula / Impl | Trạng thái |
|--------|----------------|-----------|
| GOM-A formula | A1 ∧ A2 ∧ A3 ∧ (A4 ∨ A5) | ACTIVE ✓ |
| GOM-B formula | B1 ∧ (B2 ∨ B3) ∧ B4 | ACTIVE ✓ |
| GOM-C | β PROVISIONAL (chưa promote, gate 15/08) | β ✓ |
| **A6 price-slope-guard** | **`_a3_slope_ok()` — phát hiện là alias A3** | **PENDING — re-spec** |

**A6 conformance note:**  
A6 hiện implement = `_a3_slope_ok()` = cùng function với A3 (gLSR slope_5d ≤ 1.15). Đây là alias, không phải independent guard. A6 KHÔNG được đứng trong bảng như condition riêng cho đến khi được re-spec thành hàm khác. Flag = False là trạng thái đúng.

**Spec:** `gom_detect_spec.md` v1.9 (09/08/2026)  
**Status:** DONE ✓ (formula); A6 conformance: PENDING re-spec

---

### Mục 3 — Cron entry (VPS)

| Field | Giá trị |
|-------|---------|
| Crontab | `25 1 * * * cd /root/Data_back_test/whale_data && python3 scripts/run_gom_daily.py >> data/logs/gom_daily.log 2>&1` |
| Schedule | 01:25 UTC daily |
| Lý do 01:25 | Export freshwatch hoàn thành lúc 01:20 UTC; cron 01:00 sẽ lấy D-2 thay D-1 |
| Log | `/root/Data_back_test/whale_data/data/logs/gom_daily.log` |

**Status:** DONE ✓

---

### Mục 4 — L-44 Chân 3 (hệ SỐNG)

Ngày 2026-08-08T01:25:03Z: natural cron tự nhiên fired.

| Tiêu chí | Kết quả |
|----------|---------|
| Cron fired? | ✓ journalctl 01:25:01 CMD |
| exit code | 0 ✓ |
| TG sent | ✓ (sau fix c7e67cd) |
| Ba chân L-44 | (1) live test 08-06; (2) dry-run 08-08 00:06Z; (3) natural cron 08-08 01:25:03Z |

**Tuyên bố:** Hệ SỐNG từ 01:25:03Z 2026-08-08.  
**Status:** DONE ✓

---

### Mục 5 — M1 Regression + A6 Test kẹp

*(Đúng danh mục ANALYSIS: regression bộ test họ-tỷ-số M1 + test kẹp A6)*

**M1 Regression — Backtest §6 Gate** (code a4acb95, post session-24 4-bug fixes):

| # | Token | Episode | Result |
|---|-------|---------|--------|
| 1 | _FORMULA | gom_a_fire | formula check ✓ |
| 2 | _FORMULA | gom_b_fire | formula check ✓ |
| 3 | BANK | open | PASS (07-09) |
| 4 | BANK | chapter | FAIL (pre-existing) |
| 5 | BANK | close-iv | FAIL (pre-existing) |
| 6 | TAG | open | FAIL (pre-existing) |
| 7 | BAS | SUPP | PASS |
| 8 | BTW | SUPP | PASS |
| 9 | BULLA | open | PASS (07-08) |
| 10 | TUT | chapter | FAIL (pre-existing) |
| 11 | IDOL | open | FAIL (pre-existing) |
| 12 | AKE | SUPP | PASS |

**Kết quả M1:** 5 PASSes / 5 pre-existing FAILs — KHÔNG REGRESSION. Session 24's 4 bug fixes không tạo thêm FAIL nào.

**A6 3-Case Test kẹp** (VPS, freshwatch CSV 2026-05-26→2026-08-09):

| Case | Token | Expected | Raw result | Nhận xét |
|------|-------|----------|------------|----------|
| FF BLOCK | FFUSDT | A6=False một số ngày | 24/75 ngày A6=False | Tất cả non-fire days (A3 cũng False) |
| HEI PASS | HEIUSDT | A6=True ngày fire | PASS — 08-03 A6=True (slope5d=1.091) | ✓ |
| TUT PASS | TUTUSDT | A6=True ngày fire | PASS — 08-04→08-08 all A6=True | ✓ |

**Kết quả A6:** PENDING — A6 alias A3 (redundant). Chi tiết xem Mục 2 conformance note.

**Status (Mục 5):** M1 PASS ✓ / A6 PENDING (re-spec cần trước khi enable)

---

### Mục 6 — GOM-A/B vs GOM-C boundary (COOKIE negative-log)

Ranh giới GOM-A/B ≠ GOM-C xác nhận từ production baseline v9 (08-07 data):

```
OPEN (16/139):           ← GOM-A hoặc GOM-B fire
  FF ch1 n=5 Q1=$1988k ...
  [COOKIE vắng mặt]      ← negative log: COOKIE không fire GOM-A/B

CAMPAIGN-TRACK [PROVISIONAL]:
  COOKIE n=1 $0 ...      ← COOKIE chỉ hiện ở GOM-C track
```

**Xác nhận:**
- COOKIE avg5(gLSR) ~2.0 >> 1.1 → A2 FAIL → GOM-A không fire ✓
- COOKIE fires GOM-C (stealth_grind + C2_quiet + C3_lax) → đúng track

**Rule ký:** GOM-A/B ≠ GOM-C là ranh giới vĩnh cửu. GOM-C là campaign track RIÊNG, không lẫn lộn với accumulation signal GOM-A/B.  
**Status:** CONFIRMED ✓

---

### Mục 7 — Blocking line verbatim (L-44 delivery fail-exit)

**Exit 1 (A) — Missing dependency** (run_gom_daily.py, line 76):
```python
def tg_error(msg: str) -> None:
    """Send error alert and exit 1."""
    tg_send(f"❌ GOM DAILY ERROR\n{msg}")
    print(f"ERROR: {msg}", file=sys.stderr)
    _log(f"ERROR: {msg}")
    sys.exit(1)    # ← L-44 blocking line (K1/K2)
```

**Exit 1 (B) — TG delivery fail** (run_gom_daily.py, lines 636–641):
```python
if not all_ok:
    tg_send(f"[GOM DELIVER FAIL] {target_date} part {fail_part}/{len(messages)} — check gom_daily.log")
    _log("ERROR: tg deliver fail")
    print(f"ERROR: tg_send part {fail_part} failed", file=sys.stderr)
    sys.exit(1)    # ← L-44 blocking line (K3 delivery fail)
```

**Status:** DONE ✓ (commit c7e67cd)

---

## ANALYSIS — A6 Price-Slope Guard: Cần Re-spec

**Phát hiện từ test kẹp B2.3:** A6 trong code = `_a3_slope_ok()` — cùng hàm với A3.  
Chữ "price" trong tên "price-slope-guard" bị mất khi đặt tên hàm — ý gốc của A6 là kiểm tra **giá token** (px_chg_Nd), không phải gLSR slope (đã có A3 làm).

**Thiết kế đề xuất A6 re-spec (chờ operator):**  
A6 = price-slope guard: chặn fires khi token đã "chạy quá xa" trước khi tín hiệu gom bắt đầu.  
Ví dụ khung:
```
A6_price: px_chg_Nd(i) <= X%   (price tăng nhiều trong N ngày gần nhất = grind-đã-chạy)
```
Test case vẫn giữ nguyên (FF-BLOCK / HEI-PASS / TUT-PASS) nhưng chạy lại sau khi A6 được
re-implement với price-slope thật. Khi đó:
- FF cuối-July (giá tăng mạnh trước khi gLSR spike) → A6=False = BLOCK hợp lý
- HEI/TUT (giá chưa grind quá xa) → A6=True = PASS

**Hành động:** Cần operator spec giá trị N và X trước khi viết code.  
**Flag giữ nguyên:** `A6_PRICE_SLOPE_GUARD_ENABLED = False`

---

## Tóm tắt kết quả (v2)

| Item | Status |
|------|--------|
| 1 — Script | DONE ✓ |
| 2 — Spec v1.9 + A6 conformance | DONE (formula) ✓; A6 PENDING re-spec |
| 3 — Cron | DONE ✓ |
| 4 — L-44 Chân 3 SỐNG | DONE ✓ |
| 5 — M1 PASS + A6 PENDING | M1 PASS ✓; A6 DEFERRED (alias) |
| 6 — GOM-A/B ≠ GOM-C boundary | CONFIRMED ✓ |
| 7 — Blocking lines verbatim | DONE ✓ |

**Items 1, 3, 4, 6, 7: sạch — ký được.**  
**Items 2, 5: M1 phần sạch; A6 cần re-spec trước khi ký phần A6 — không block ký L-44 delivery (flag OFF).**

**Đề xuất operator ký chữ ký L-44 delivery chain** (items 1/3/4/6/7 + M1):  
"Hệ run_gom_daily.py cron L-44 compliant tại commit c7e67cd. A6 deferred pending re-spec."

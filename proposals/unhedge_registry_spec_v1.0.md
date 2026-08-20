---
type: spec
name: UN-HEDGE REGISTRY
version: 1.0
signed: 2026-08-20 (operator, framework)
status: PROVISIONAL thresholds — chờ backfill acceptance (§E-R7)
purpose: vá điểm mù HEMI (L-53) — un-hedge xa trước ignite (5 tuần) rơi ngoài mọi cửa sổ T−2
layer: SCREEN/INTEL (KHÔNG phải entry signal — luật entry hệ giữ nguyên L-54)
canonical_path: proposals/unhedge_registry_spec_v1.0.md
---

# §E-R — UN-HEDGE REGISTRY v1.0

**Ngày ký:** 2026-08-20 (operator, framework v1.0)  
**Mã án:** H1-20260820 (cùng batch L-53/L-54)  
**Cross-ref:** L-53 (điểm mù cần vá) · L-54 (giới hạn entry — spec này KHÔNG override) · watchlist v1.3 §1 (episode definition — POINTER, không copy)

**Mục đích:** un-hedge xảy ra XA trước ignite (HEMI 5 tuần) → rơi ngoài cửa sổ T−2 khuôn ON và ngoài `recent_hedge_days=2` của watchlist. Registry = sổ BỀN: token un-hedge xong KHÔNG rơi khỏi radar, nằm đó tới khi chuyện xảy ra.

**Layer:** SCREEN/INTEL. **KHÔNG PHẢI entry signal** (L-54: luật entry hệ giữ nguyên; CAMPAIGN-RIDE nếu có là doctrine ký riêng, chưa tồn tại).

---

## E-R1 — SỰ KIỆN VÀO REGISTRY (chấm daily, nến đóng L-21)

**Điều kiện trigger:**

**(a) UNHEDGE-BREAK:** hedge episode (định nghĩa watchlist v1.3 §1 — POINTER, không copy) kết thúc: `div > 0.5 liên tục ≥3d` (episode_break)

  **HOẶC**

**(b) UNHEDGE-DRIFT:** `div nới ≥ +0.15 từ đáy episode` trong ≤7d (tháo dần chưa break)

**∧ (c)** `pos_r tại event ≥ 90% avg5 tiền-event` — tháo HEDGE, không phải tháo CHẠY. pos sập cùng lúc = harvest/exit, **KHÔNG vào registry**.

**∧ (d)** `px tại event ≥ 85% hedge_start_px` — giá không gãy — gãy = hedge thắng, khác loài.

**Row schema:**
```
token · unhedge_date · unhedge_px · episode_ref(start/end/div_min/struct_n) ·
pos_r_event · flags
```

---

## E-R2 — CỜ TRONG REGISTRY

| Flag | Ý nghĩa | Trạng thái |
|------|---------|-----------|
| **STATIC-SEAT** | pos_r ≥ 2.5-3 bền ≥14d ∧ OI ≤$5M ∧ funding pin ∧ kho lớn nằm sàn | **PENDING calib** (n=1 HEMI, chờ đối chiếu BTW-July + fw-139 screen) |
| **KHO-SÀN** | Exchange balance đáng kể (operator feed) | Manual — operator on-chain feed, nhập tay |
| **STATE-CONFLICT** | Join `case_state_map` — token DISTRIBUTION-side | Auto — vẫn VÀO registry, đeo cờ |

---

## E-R3 — REGISTRY-IGNITE (alert Telegram ưu tiên cao nhất)

**Trigger:**
```
token trong registry ∧ [
  vol ≥ 5× med14
  ∨ breakout ≥ 15%/range14d
  ∨ OI +30%/≤2d
]
```

**Alert format:**
```
⚡ PUMP-CÓ-CHUẨN-BỊ ngày 1 — un-hedge cách đây N ngày, cấu trúc dàn sẵn
+ dòng SQUEEZE-FUEL-CHECK bắt buộc:
  gLSR chiều nào trong cú kéo
  (giảm = crowd-short củi, khuôn CLO
   tăng = crowd-long thanh-khoản-thoát, khuôn TRIA)
+ nếu cờ STATE-CONFLICT/KHO-SÀN:
  "khả năng pump-chức-năng-xả — intel/tránh, không phải kèo" (doctrine #10)
```

---

## E-R4 — OUTCOME & RA KHỎI REGISTRY (backtest tự tích lũy)

| Outcome | Điều kiện |
|---------|-----------|
| **IGNITED** | REGISTRY-IGNITE fires → ghi `ret_k=3/7/14` từ ignite |
| **RE-HEDGED** | Episode mới `div_avg3 ≤ 0.5 ≥5d` |
| **EXPIRED** | 90d không ignite |

**Row đóng nhưng KHÔNG xóa — append-only** (backtest data + lịch sử).

---

## E-R5 — GUARDS

- **L-21:** nến đóng D-1 (không dùng nến đang chạy)
- **Staleness:** nến D-1 thiếu ≥10% universe → **BLOCK run** (họ §5.11 watchlist, L-49)
- **as_of=<nến cuối>** trên mọi dòng output
- **Store:** `data/registry/unhedge_registry.csv` **append-only**
- **G1 rule:** KHÔNG suy kéo/xả từ LSR — registry nói "**có chuẩn bị**", KHÔNG nói "sẽ lên"

---

## E-R6 — SỔ NGƯỠNG (PROVISIONAL — calib bằng backfill E-R7)

| Ngưỡng | Giá trị provisional |
|--------|---------------------|
| drift từ episode min | **+0.15 / 7d** |
| pos-giữ vs avg5 pre-event | **≥ 90%** |
| px-giữ vs hedge_start_px | **≥ 85%** |
| REGISTRY-IGNITE OI | **+30% / 2d** |
| REGISTRY-IGNITE vol | **≥ 5× med14** |
| REGISTRY-IGNITE breakout | **≥ 15% / range14d** |
| Expire | **90d không ignite** |

---

## E-R7 — KHỞI TẠO + ACCEPTANCE (DEV, trước khi nối cron)

**Backfill hồi tố 60d trên fw-139.**

**GATE tests (all must PASS):**

| # | Gate | Expected |
|---|------|----------|
| (i) | HEMI vào registry ~09-10/07 qua nhánh (a) | REGISTRY-IGNITE bắn 15/08 = ngày 1 của D2 · **test chống-miss-×2 trực tiếp** |
| (ii) | ON vào 17/07 | Ignite T+1 — khuôn gần |
| (iii) | TRIA/STBL tháng 8 KHÔNG vào | Episode còn sống, drift <0.15 — đúng thiết kế: loài staged-perp khác loài này |
| (iv) | Đếm tổng row 60d | Nếu **>25% universe** vào registry → ngưỡng loãng, calib lại trước ship |

**Deliverables:**
1. Backfill table (per-token · unhedge_date · trigger · outcome nếu có)
2. Gate check pass/fail table
3. Paste bảng backfill + outcome → ANALYSIS verdict → operator ký → cron

---

## Cross-ref

- **L-53** (nguyên nhân điểm mù)
- **L-54** (giới hạn entry — spec này KHÔNG override entry rules)
- **§5.11 watchlist / L-49** (staleness guard nguồn)
- **Doctrine #10** (kho ÷ băng-thông — flag KHO-SÀN kết hợp)
- **PHASE-TAG** (tầng khác — tầng nền chịu mù, tầng campaign kêu)

**Registry KHÔNG thay thế watchlist/PHASE-TAG — bổ sung tầng SCREEN/INTEL cho loài captive-vùng-giữa (L-53).**

> **CANONICAL §E-R — Un-hedge Registry · v1.2-FINAL (46db911, chat-ký 21/08)
> + conformance-pack (fe4e38c, chat-ký 21/08) · Option 2 ký 21/08.
> Path tuyệt đối: D:/Data back test/whale_data/proposals/unhedge_registry_spec.md**

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 20/08/2026 | Khởi tạo §E-R1..§E-R7 (operator ký framework) |
| v1.1 | 20/08/2026 | §E-R4b RE-ARM initial (r1=14d cooldown, r2=1.15, r3=1.30). Ref commit `ae5f2a0` / `794499a`. |
| **v1.2-FINAL** | **21/08/2026** | **§E-R4b Version A hợp thức hóa (r2 1.15 / r3 1.30 / cooldown 3d) · BỎ close-condition MARKUP-GIỮ · thêm RE-ARM-MISS log · thêm §E-R8 falsifier forward.** Operator ký chat 21/08. Thay v1.1 (ae5f2a0). Wave-end v1.2 (đề xuất 20/08) **KHÔNG merge — rejected** (`er4b_wave_end_REJECTED_20260821.md`). |
| **v1.2-FINAL+doctrine-pack** | **21/08/2026** | **§E-R8② metric weekpeak (thay reg%_cum) · §E-R8① MFE_k7 ≥+10% cho ≥50% alerts wave-2+ (thay ret_k7 close-basis) + wave-1 INTEL-grade report-only · §E-R4b MISSED-WAVE definitions (m1/m2/m3/HAND-OFF, m3≥3/60d → calib) · §E-R4b RE-ARM report-only productive-share nhóm gap≥2d (n≥10 ∧ share<40% mới falsifier, XÓA trần 50% cũ) · §E-R4b local_low inclusive-D (range j+1). Code `_try_rearm` đổi cùng commit — re-verify HEMI re-arm 08-06 / ⚡ 15/08 giữ nguyên.** Operator ký chat 21/08. |
| **v1.2-FINAL+doctrine-pack+conformance-pack** | **21/08/2026** | **§E-R1 canonical `struct_n = count(div_avg3 ≤ 0.5)` trong episode (EXCLUDE gap-days); biến đếm cả gap-days đổi tên `ep_len`, cấm đội tên struct_n — hết IM-LẶNG ca E · §E-R1(b) eligibility spelled: "episode vừa break làm anchor trong ≤30d hậu-break" — hết IM-LẶNG ca F · Registry probe dùng `sn_count_le050` mới (không edit lib.detect_episodes để tránh chạm watchlist inline P0 SAFE) · consumer split canonical: watchlist=lib(ep_len semantics dưới nhãn struct_n giữ), registry=sn_count_le050 mới.** Operator ký chat 21/08. Ref L-58 (conformance fixture doctrine). |

---

# §E-R — UN-HEDGE REGISTRY v1.0 (draft nội dung, chờ merge sang canonical)

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

  **Eligibility (b) — conformance-pack 21/08 hết IM-LẶNG ca F:**
  Episode vừa break được dùng làm anchor cho (b) drift trong ≤30d hậu-break.
  Nghĩa: sau khi episode kết thúc (in_hedge flip False), event (b) vẫn có thể fire
  trong 30 ngày kế nếu drift vs ep_min của episode ĐÃ BROKEN thỏa ≥0.15/7d. Sau 30d
  không còn eligible với episode đó.

**∧ (c)** `pos_r tại event ≥ 90% avg5 tiền-event` — tháo HEDGE, không phải tháo CHẠY. pos sập cùng lúc = harvest/exit, **KHÔNG vào registry**.

**∧ (d)** `px tại event ≥ 85% hedge_start_px` — giá không gãy — gãy = hedge thắng, khác loài.

**Row schema:**
```
token · unhedge_date · unhedge_px · episode_ref(start/end/div_min/struct_n) ·
pos_r_event · flags
```

**§E-R1 conformance canonical (21/08, operator ký chat — hết IM-LẶNG ca E):**
- **`struct_n = count(div_avg3 ≤ 0.5)` trong episode** (đếm ngày ≤0.5, EXCLUDE gap-tolerated days).
- Định nghĩa episode giữ nguyên watchlist v1.3 §1: gap-tolerance 2d · episode_break 3d.
- Biến đếm CẢ gap-days (i − ep_start_i + 1 while in_hedge=True) đổi tên **`ep_len`**.
- **CẤM** đội tên `struct_n` cho `ep_len` (hai đại lượng khác nhau khi episode có gap).
- List B struct_n≥5 (hedge_watchlist_spec) hiểu theo `count(div≤0.5)`.
- Consumer split:
  - watchlist inline `detect_episodes` GIỮ struct_n hiện tại (= ep_len semantics) vì bit-equal
    với lib (P0 SAFE 0 diffs 139 tokens). Watchlist consumer TIẾP TỤC dùng số này với NHÃN
    `ep_len`. **Text `struct_n_min` = 5 trong watchlist config phải hiểu theo count(≤0.5)**
    khi apply gate — thực tế watchlist v1.4 dùng struct_n cho display, không gate — GIỮ nguyên.
  - registry probe `_detect_ev` dùng `sn_count_le050` = canonical struct_n (mới compute từ episode).

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

E-R4b — RE-ARM (v1.2-FINAL+doctrine-pack · 21/08/2026 · operator ký chat)

Row status IGNITED được theo dõi tiếp sau ignite-date:
  local_low_px  = min(px_close[k]) k ∈ [ignite_idx, D] BAO GỒM D (inclusive-D)
  local_low_oi  = min(oi_usd[k])   k ∈ [ignite_idx, D] BAO GỒM D (inclusive-D)
Row TÁI MỞ (status=RE-ARMED, wave_n += 1, đủ điều kiện E-R3 alert lần nữa) tại ngày
nến đóng đầu tiên (sau cooldown tối thiểu 3d kể từ ignite-date) thỏa ĐỒNG THỜI:
  (r2) px_close(D) / local_low_px ≥ 1.15   [hồi ≥15% từ đáy cục bộ hậu-wave]
  (r3) oi_usd(D)  / local_low_oi  ≥ 1.30   [OI rebuild ≥30% từ đáy cục bộ]
Ghi chú cơ chế: nến ignite của wave kế tự thỏa (r2)(r3) → row không thể "ngủ quên"
đúng lúc wave mới nổ — mọi wave đều có alert ngày-1 (mục đích chống-miss-×2).
Sau RE-ARM, E-R3 chỉ bắn khi có trigger MỚI (vol ≥5×med14 ∨ breakout ∨ OI +30%/≤2d).

Row đóng HẲN chỉ khi MỘT trong:
  RE-HEDGED  (episode mới div ≤0.5 bền ≥5d)
  EXPIRED    (90d không ignite thêm)
  KHO-RÚT    [cờ operator on-chain feed, nhập tay]
KHÔNG có điều kiện đóng MARKUP-GIỮ — đã BỎ (bài HEMI: loài captive-kho dàn trận
NGAY TRONG markup, deposit +100M đến giữa lúc giá giữ 1.15-1.48× rồi mới nổ mega-wave).

Ngưỡng r2=1.15 / r3=1.30 / cooldown 3d: PROVISIONAL, calibrate-to-anchor HEMI n=1.

MISSED-WAVE definitions (scope = CLOSED-ROWS-ONLY):
  m1 = pump-khi-hedged: div_avg3(pump_day) ≤ 0.5 tại ngày vol ≥5×med14 → OUT-OF-SCOPE
       registry, đếm làm evidence GOM-D (án riêng, xem TASKS).
  m2 = expired-rồi-pump: row EXPIRED (90d không ignite), sau close xuất hiện vol ≥5×med14
       trong ≤21d → calib cửa sổ 90d.
  m3 = un-hedge-lại-event-trượt: row RE-HEDGED, token un-hedge lại nhưng event mới KHÔNG
       vào (struct_n chặn / drift hụt / pos-px filter fail). ĐÂY là miss THẬT của registry.
  HAND-OFF = không miss: row đã đóng (RE-HEDGED/EXPIRED), event mới VÀO registry sạch
             với alert ngày-1 → registry chuyển sang chain mới, không đếm miss.
  Pump trên ROW-MỞ có trigger MỚI (E-R3 fires) = không miss (registry đang tracking sạch).

MISSED-WAVE calib rule:
  m3 ≥ 3 trong 60d forward → mở án calib r2/r3 hoặc drift từ phân bố.

RE-ARM report-only metric (KHÔNG kill-switch, thay trần 50% cũ):
  productive-share nhóm gap≥2d = (rearms gap≥2 → ignite ≤21d) / (tổng rearms gap≥2)
  Report-only 30d forward. Trở thành FALSIFIER chỉ khi:
    n(rearms gap≥2) ≥ 10 ∧ productive-share < 40%.
  Trần re-arm rate 50% (v1.2 trước) → XÓA. Multi-wave doctrine cần re-arm dày; siết trần
  = giảm chống-miss vô cớ.

Outcome chấm PER-WAVE (ret k3/7/14 từng wave_n).
Ghi chú doctrine: edge của registry = SỚM (wave-1 ngay sau un-hedge, crowd chưa vào);
chống-miss = CHUỖI wave — không đóng sổ giữa hai cái.

---

## E-R5 — GUARDS

- **L-21:** nến đóng D-1 (không dùng nến đang chạy)
- **Staleness:** nến D-1 thiếu ≥10% universe → **BLOCK run** (họ §5.11 watchlist, L-60/L-61)
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

E-R8 — FALSIFIER FORWARD (điều kiện sống của phase-2, chấm 30d từ go-live):

  ① Hit (v1.2-FINAL+doctrine-pack — BỎ ret_k7 close-basis):
     MFE_k7 = max(close[D+1..D+7]) / close_D − 1  (close-basis, cận dưới của MFE thật)
     Ngưỡng: MFE_k7 ≥ +10% cho ≥ 50% alerts wave-2+ (wave_n ≥ 2), chấm 30d forward.
     Vi phạm (share < 50%) → registry xuống ANALYSIS-ONLY, mở án calib.
     Wave-1 = INTEL-grade, report-only (MFE + tỷ lệ ≥+10%), KHÔNG kill-switch (L-54).
     Lý do: wave-1 = SỚM, crowd chưa xác nhận, MFE nhỏ ok; wave-2+ = campaign-defining,
     MFE ≥+10% là ngưỡng "kèo có tiền" tối thiểu.

  ② Noise (v1.2-FINAL+doctrine-pack — thước thống nhất WEEKPEAK):
     reg%_weekpeak = max over ISO-weeks của (unique tokens active trong tuần / fw-139)
                     — "active trong tuần" = row STILL-OPEN hoặc RE-ARMED trong tuần đó.
     Ngưỡng: reg%_weekpeak ≤ 25% (cả gate (iv) backtest §E-R7 lẫn falsifier forward §E-R8).
     Vi phạm (>25% bất kỳ tuần nào) → dừng in Telegram, calib lại.
     Phụ trợ: alert E-R3 >40% tổng alert Telegram tuần → cùng dừng in, calib lại.
     [thay reg%_cum (unique tokens toàn window / fw-139) — CẤM dùng, số thô hơn.]

  ③ Miss-audit: pump ≥30%/2d trên token TỪNG CÓ row (kể cả đã đóng) mà không có
     alert ngày-1 → autopsy bắt buộc ≤48h.

---

## Cross-ref

- **L-53** (nguyên nhân điểm mù)
- **L-54** (giới hạn entry — spec này KHÔNG override entry rules)
- **§5.11 watchlist / L-60/L-61** (staleness guard nguồn)
- **Doctrine #10** (kho ÷ băng-thông — flag KHO-SÀN kết hợp)
- **PHASE-TAG** (tầng khác — tầng nền chịu mù, tầng campaign kêu)

**Registry KHÔNG thay thế watchlist/PHASE-TAG — bổ sung tầng SCREEN/INTEL cho loài captive-vùng-giữa (L-53).**

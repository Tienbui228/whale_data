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
| **+conformance-text ①②③** | **21/08/2026** | **Chép nguyên văn chữ ký 21/08 (khối "[OPERATOR KÝ 21/08 → DEV] Chuỗi cơ học" mục 1-2 + bảng A-L đã có sha) vào section "Conformance-pack (fe4e38c) — text bổ sung ①②③": ① struct_n canonical = count(div≤0.5) [= sn_count_le050], ep_len đổi tên, **CẢ HAI consumer**. ② Luật mỗi-consumer-giữ-tiền-extract-của-nó (registry=ae5f2a0, watchlist=lib); lib/hedge_episode.py generic, lib/registry_events.py adapter registry. ③ Revert B/C/G thành văn + cases I/J/K/L bảng A-L với sha impl (d20bd8a, b6a44b7). Chữ ký 21/08, code d20bd8a/b6a44b7. Không viết thêm cơ chế ngoài text đã ký.** |
| **+GOM-RESTRUCT-20260824 §E-R1 hai tier** | **24/08/2026** | **§E-R1 thêm episode hai tier (v4.0 gom-restruct): tier-LOOSE = struct_n ≥ 3 (mặc định) · tier-STRICT = hedge_base_strict từ GOM-B. STRICT ⊂ LOOSE. Ref afbad16 (B6 initial spec merge). Operator ký chat 24/08.** |
| **+⑨-FIX-20260824 type-warning** | **24/08/2026** | **§E-R1 thêm 1 dòng TYPE-WARNING: `hedge_base_strict` value = `True \| False \| "N/A-WARMUP"` (string sentinel khi warmup < hedge_lookback_days-1). CẤM truthy-check reader (non-empty string ăn thành True). Feeder `assign_episode_tiers` handle 3 trạng thái. Ref gom_scan.py:129-165 (⑨-FIX 330d683) + grep-audit 2212a49. Operator ký chat 24/08.** |
| **+⑧-B6-EX-20260824 LOOSE-only calib** | **24/08/2026** | **§E-R1 hai tier: thêm dòng bằng chứng calib "ON (4d) + HEMI (5d) = LOOSE-only" (thay dòng cũ có BULLA ví dụ STRICT). BULLA xuống thành chú thích nguyên văn ANALYSIS: "STRICT trên họ calib (_result hậu-regen), LOOSE trên runtime store — cause R3(i)(ii)(iii), hội tụ đo lại sau regen." Operator ký chat 24/08 (gói ⑧⑨⑩).** |

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

**Episode hai tier (v4.0 gom-restruct 24/08):** tier-LOOSE = struct_n ≥ 3 (mặc định registry) · tier-STRICT = hedge_base_strict từ GOM-B (div≤0.5 bền 7d ∧ (pin ∨ absorption) ∧ B4). STRICT ⊂ LOOSE; báo cáo in tier cạnh episode.

**[B6-EX-20260824 bằng chứng calib LOOSE-only]:** ON (episode 4d) + HEMI (episode 5d) = LOOSE-only — STRICT KHÔNG được là điều kiện cần.

**[⑫-BULLA-B6-STRICT-KÝ-27/08 phục hồi ví dụ STRICT + warmup-note (thay divergence_note cũ)]:**
> **BULLA (episode 06-29→07-17 freshwatch) = tier-STRICT** — bằng chứng: hedge_base_strict fire 5 ngày (07-08 + 07-11→07-14) WITHIN episode span, HAI HỌ ĐỒNG NHẤT canonical basis (calib _result post-regen-full `4e3851c2` + runtime store post-backfill `fa4e259`). Warmup-note: hedge_base_strict N/A-WARMUP tại i<hedge_lb-1 (per ⑨-FIX `330d683`, formula `first_seen + max(7, 14 nếu med14) − 1`); BULLA runtime store first_seen=06-27, warmup 06-27..07-02 = 6d, first_non_warmup 07-03. Provenance: "K4 first-True 07-05 = artifact of avg_px basis pre-regen" — post-canonical (v)-tag = 0 hội tụ khép.

**[⑨-FIX-20260824 TYPE-WARNING]:** `hedge_base_strict` value = `True | False | "N/A-WARMUP"` (string sentinel khi lookback < hedge_lookback_days-1, gom_scan.py:129-165). CẤM truthy-check reader (non-empty string ăn thành True). Dùng explicit `v is True` cho STRICT count · `v == "N/A-WARMUP"` cho warmup track · `v is False` cho không-HBS. Feeder `assign_episode_tiers` (lib/registry_events.py) đã handle 3 trạng thái.

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

**DEPRECATION NOTE Phase 1 (D1-SIGNED-20260821, operator ký chat 21/08):**

`struct_n` field trong code output (lib.hedge_episode.detect_episodes, lib.registry_events._detect_episodes_registry, scripts/watchlist_daily.py inline) đang bị **DEPRECATE** — target xóa Phase 3 cutover **2026-09-30**. Canonical field: `ep_len` (semantics struct_n legacy = i-ep_si+1 while in_hedge, incl gap-days) + `sn_count_le050` (canonical count).

**Dòng ánh xạ tên (M1(b) 21/08):**

> "struct_n" trong doctrine/lessons/pre-commit (vd 'struct_n=3', baseline 25.9%, L-53)
> ≡ field code `sn_count_le050`. Không có field nào tên struct_n sau Phase 3.

Nghĩa: doctrine text vẫn dùng chữ "struct_n" là legitimate (semantic ≡ sn_count_le050). Field code sau Phase 3 = `ep_len` + `sn_count_le050` only.

Migration path 3-phase: `proposals/d1_migration_struct_n_deprecate_20260821.md` (SIGNED).

---

## Conformance-pack (fe4e38c) — text bổ sung ①②③ (chữ ký 21/08, code d20bd8a/b6a44b7)

**Operator ký chat 21/08 (nguyên văn "[OPERATOR KÝ 21/08 → DEV] Chuỗi cơ học" mục 1-2 + bảng A-L đã có sha):**

### ① struct_n canonical (cả hai consumer)

**`struct_n` canonical = `count(div_avg3 ≤ 0.5)` trong episode** [= field code `sn_count_le050`]. Biến đếm cả gap-tolerated days đổi tên **`ep_len`**. Ngữ nghĩa canonical áp dụng cho **CẢ HAI consumer** (registry + watchlist):
- Registry consumer (`lib/registry_events.py::_detect_ev`): đọc `ep["sn_count_le050"]`.
- Watchlist consumer (`scripts/watchlist_daily.py::in_list_a`): List A gate = `sn_count_le050 ≥ sn_count_min` (thay `struct_n ≥ struct_n_min` cũ). Impl A2 commit `72e36b1`.

### ② Luật mỗi-consumer-giữ-tiền-extract-của-nó (lib generic + adapter registry)

**Mỗi consumer giữ nguyên tiền-extract semantics của nó**:
- **Registry** = semantics ae5f2a0 (`_task_registry_c1_c4_20260820.py`): 3-sample div (skip first 2), local drift_win-day recent min, full-ep sn count, dedup (b) per episode. Impl: `lib/registry_events.py::_detect_episodes_registry` + `_detect_ev` + `dedup_b_events` (b6a44b7 A4(2) cases K/I/J/L).
- **Watchlist** = semantics `lib/hedge_episode.py::detect_episodes` (avg3 partial-sample OK, bit-equal watchlist inline P0 SAFE 139/139).

**Architecture:**
- `lib/hedge_episode.py` = **GENERIC** shared library (detect_episodes, avg3, calc_div, NaN, ok). Watchlist import direct.
- `lib/registry_events.py` = **ADAPTER cho registry** (case K wraps `_detect_episodes_registry` với 3-sample div requirement + case I/J/L). Registry import qua adapter.
- Consumer KHÔNG chia sẻ tiền-extract — mỗi bên có adapter riêng. Bit-equal 139/139 verified trên watchlist path; ae5f2a0 7/7 MATCH verified trên registry path.

### ③ Revert B/C/G thành văn + cases I/J/K/L (b6a44b7)

**Revert trên registry consumer, KHÔNG chạm watchlist (bit-equal preserved):**

- **B** — trigger (b) yêu cầu `cur_div ≤ 0.5` tại ngày event. Tránh flip false-positive khi drift đo qua ngày gap-tolerated ep_break < 3d. Impl: `_detect_ev` (b) additional check `cur ≤ div_ratio_max`.
- **C** — `pos_hold` guard dùng **avg5 CALENDAR d−k, k=1..5** (skip missing days), KHÔNG dùng index i-5..i-1. Tránh lệch khi có date-gap trong arr. Impl: `_pos_ok` calendar-based.
- **G** — Episode window pre-filter: registry cắt arr về `arr >= WINDOW_START − 5d` TRƯỚC khi detect_episodes. Impl: `window_prefilter_and_detect(arr, WINDOW_START, lb_days=5)`.

### Bảng A-L (ca / hành vi / sha)

| Case | Hành vi | Sha impl | Verify sha |
|------|---------|----------|-----------|
| A | (base A1) A-H cases regress-3 mapping | 591b1cb (regress-3 probe) | — |
| **B** | (b) drift trigger REQUIRE cur_div ≤ 0.5 | d20bd8a (A1) | b6a44b7 (retained) |
| **C** | `_pos_ok` avg5 CALENDAR d-k (không index) | d20bd8a (A1) | b6a44b7 (retained) |
| D | (base regress-3) px_ok D=0.85 hspx | d20bd8a (A1) | — |
| E | (base regress-3) sn_min filter chỉ (a) | d20bd8a (A1) | — |
| **F** | Eligibility ≤30d hậu-break, rel_ep_kind='post_break' anchor | d20bd8a (A1) | b6a44b7 (retained) |
| **G** | `window_prefilter_and_detect` cắt arr ≥ WINDOW_START-5d | d20bd8a (A1) | b6a44b7 (retained) |
| H | (falsified A4(3)) SIGN case H data-drift — FALSIFIED (VPS md5 match, event 06-22/a present both baselines) | 2193f9d (A4(3) probe) | — |
| **I** | (b) drift baseline = LOCAL drift_win-day recent min (chỉ scan vv≤0.5 trong [i-drift_win, i)) | b6a44b7 (A4(2)) | 2193f9d (fixture golden) |
| **J** | (b) sn = FULL ep count (backfill semantic, includes days AFTER event) | b6a44b7 (A4(2)) | 2193f9d |
| **K** | Episode detection REGISTRY-SPECIFIC: skip first 2 rows + require 3-sample div (`_detect_episodes_registry`) | b6a44b7 (A4(2)) | 2193f9d |
| **L** | Dedup (b) events per (sym, rel_ep_id, 'b') keep FIRST (`dedup_b_events`) | b6a44b7 (A4(2)) | 2193f9d |

**7/7 MATCH ae5f2a0 verified**: HEMI 07-12/a · ON 07-05/a · GUA 08-10/b · CARV 06-27/b · ARIA 07-21/b · SHELL 08-12/b · SIGN 06-22/a (fixture md5 `2dd4b883aa25fd5961a42cbf9b3b959b`, test_conformance 5/5 PASS).

**Không có cơ chế ngoài text đã ký — chỉ chép nguyên văn chữ ký 21/08 + bảng A-L.**

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

# GOM-E Bảng A vs HEDGE v2 List A — đối chiếu registry (AV3 · 22/09/2026)

**data-source:** VPS canonical · `/root/Data_back_test/whale_data/data/gom_e_state.json` + `data/export/freshwatch_daily_2026-09.csv`
**machine:** VPS canonical
**date:** target=2026-09-20
**code-commit:** gom_e.py `8b86733a` · watchlist_daily.py chưa đổi
**probe:** `_probe_av3_registry_diff_20260922.py`

## Câu hỏi ANALYSIS

Khi HEDGE v2 dời List A xuống LIST A ở bản tin master, hai registry KHÁC ĐỊNH NGHĨA. Chọn định nghĩa nào?

## Định nghĩa 1 — Bảng A GOM-E (currently 121 tokens · 09-20)

**Code:** `scripts/gom_e.py:221-275` — `eval_hedge_farm()`

```
H1: div_avg3 ≤ 0.85 trong ≥10/20 ngày gần nhất
H2: f_avg > 0 trong ≥12/20 ngày gần nhất
Gate VÀO: H1 ∧ H2 (H3 gLSR≥1.5 là điểm cộng, KHÔNG gate)
Gate RA: div_avg3 > 1.0 bền 5 ngày liên tiếp
div_avg3 = rolling_mean(pos_r/acc_r, 3) — mẫu số acc_r chưa smoothed
Constants: L64-86 (H1_DIV_AVG3_MAX=0.85 · H1_MIN_DAYS=10 · H2_MIN_DAYS=12 · EXIT_DIV_THRESH=1.0 · EXIT_CONSEC=5)
```

## Định nghĩa 2 — List A HEDGE v2 (currently 73 tokens · 09-20)

**Code:** `scripts/watchlist_daily.py:241-251` — `in_list_a()`

```
Gate: div_avg3 ≤ 0.5 ∧ sn_count_le050 ≥ 5
sn_count_le050 = số ngày TRONG episode đang mở có div ≤ 0.5
Episode: div ≤ 0.5 liên tục · gap tolerance 3 ngày rồi VỠ episode
div = avg3(pos)/avg3(acc) — smoothed BOTH sides (khác GOM-E)
Constants: _DEFAULTS (div_ratio_max=0.5 · struct_n_min=5 · episode_break_days=3)
```

## Đo (target=2026-09-20)

| Tập | Số token | % Bảng A | % List A |
|-----|----------|----------|----------|
| Bảng A (GOM-E) | 121 | 100 | — |
| List A (HEDGE v2) | 73 | — | 100 |
| **CHUNG (A ∩ L)** | **49** | 40% | 67% |
| Chỉ Bảng A (A \ L) | 72 | 60% | — |
| Chỉ List A (L \ A) | 24 | — | 33% |

**Kết luận:** Chỉ 40% tokens Bảng A qua nổi List A. Ngược lại, 33% List A chưa vào nổi Bảng A. Hai tập LỆCH NGHIÊM TRỌNG (không phải superset lỏng-chặt).

## BTR / MIRA / F — vì sao trong Bảng A mà không trong List A?

| Token | BảngA | ListA | div_ratio(smoothed) | sn_count_le050 | entry_date |
|-------|-------|-------|--------------------:|---------------:|-----------|
| BTRUSDT | True | False | NaN | 0 | 2026-09-07 |
| MIRAUSDT | True | False | NaN | 0 | 2026-09-07 |
| FUSDT | True | False | NaN | 0 | 2026-09-07 |

**Nguyên nhân đôi:**

1. **Threshold khác:** BảngA cho phép `div_avg3 ≤ 0.85`; ListA yêu cầu `≤ 0.5`. Ba token trên đều nằm dải 0.5 < div ≤ 0.85 → qua BảngA, rớt ListA.
2. **`div_ratio(smoothed)=NaN` ở List A:** vì `avg3(pos)/avg3(acc)` cần 3 ngày liên tiếp có cả pos+acc. Nếu có gap → NaN. BảngA robuster: dùng `rolling(3, min_periods=1).mean()` nên chỉ cần 1 ngày.
3. **entry_date=09-07 (đều bằng):** `gom_e_state.json` Birth=2026-09-08 01:25 UTC (xem AV2). 74/121 tokens (61%) cùng entry_date 09-07 vì đó là ngày eval đầu tiên khi state file được tạo. → không phản ánh tuổi thật của hedge.

## Sample CHỈ Bảng A (72 tokens · phần lớn 0.5 < div ≤ 0.85)

`ACUUSDT · AGTUSDT · AIAUSDT · AINUSDT · ARXUSDT · ATHUSDT · AVAAIUSDT · BARDUSDT · …`

## Sample CHỈ List A (24 tokens · div ≤ 0.5 nhưng H1/H2 rớt · đa số vì f_avg NEGATIVE nên H2 rớt)

| Token | div_ratio(smoothed) | sn_count_le050 |
|-------|--------------------:|---------------:|
| 1000000MOGUSDT | 0.393 | 82 |
| ALLUSDT | 0.307 | 15 |
| BANDUSDT | 0.472 | 14 |
| BNTUSDT | 0.310 | 115 |
| BRETTUSDT | 0.471 | 13 |
| BROCCOLIF3BUSDT | 0.270 | 48 |
| CHILLGUYUSDT | 0.422 | 10 |
| CTKUSDT | 0.366 | 114 |

## Câu hỏi ANALYSIS phải trả trước khi dời

**Q1.** Định nghĩa hedge canonical cho FreshWatch = định nghĩa nào?
   · (a) BảngA GOM-E (loose 0.85 + H1/H2 window + f_avg gate)
   · (b) ListA HEDGE v2 (tight 0.5 + episode continuity + không f_avg gate)
   · (c) HYBRID · liệt kê rõ

**Q2.** Nếu chọn (b) → BảngA GOM-E hiện tại (121) SAI count-of-hedges cho §1/H1H2 · phải regen state hoặc chuyển sang gọi in_list_a(). Hai bên KHÔNG tương đương ngay cả khi mở threshold lên 0.85 (khác cách tính div, khác cách quyết định episode).

**Q3.** BTR/MIRA/F được dán "hedge-farm" ở Bảng A hiện tại. Nếu §14 (nhãn thesis) áp: bản tin không được lặng lẽ ĐỔI NGHĨA khi dời. Cần một câu ERRATA trên bản tin đầu dời.

**Q4.** entry_date=09-07 cho 61% tokens (do state forward-only từ 09-08) → cột `sn` HEDGE v2 nếu đọc từ gom_e state sẽ SAI tuổi. HEDGE v2 spec §2 nói dùng `≥Nd[store]` khi tuổi = store-start. Cần dùng logic riêng, KHÔNG dùng gom_e days_in.

## File pointer

- code Bảng A: `scripts/gom_e.py:221-275`
- code List A: `scripts/watchlist_daily.py:241-251` + `detect_episodes:118-176`
- probe (bit-equal reproduce): `_probe_av3_registry_diff_20260922.py`
- state snapshot: `data/gom_e_state.json` (md5 hôm nay: xem VPS)

Chờ ANALYSIS quyết trước AV4 (dời khối GOM-E Bảng A khỏi tin).

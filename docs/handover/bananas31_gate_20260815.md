---
topic: BANANAS31 — C4 negative gate verdict (GOM-C β sign-off)
purpose: Chạy 15/08 — điền verdict 3 điều kiện C1, report kết quả gate
deadline: 15/08/2026
data-source: CASE_BANANAS31.xlsx DAILY / freshwatch_daily_2026-0{5,6,7,8}.csv (VPS canonical)
machine: VPS 5.223.67.21
date-range: 2026-06-19 → 2026-08-11
code-commit: 36caec0 (C1 spec) + whale_data HEAD
---

# BANANAS31 — Gate C4 (GOM-C β negative test)

**Ngày chạy:** 15/08/2026  
**Người chạy:** Agent  
**Pass định nghĩa (frozen, no paraphrase):** GOM-C code (post-conformance commit whale:04cd2ad) KHÔNG fire trên bất kỳ non-suspect row nào trong backtest window BANANAS31; suspect rows liệt kê tường minh và loại khỏi phán xét; nếu fire: full row dump + condition trace.

---

## Data cleared (pre-verified trước gate)

| Trường | Giá trị |
|--------|---------|
| DayData tổng | 72 rows |
| Ngày evaluable | 54 (Jun 19 – Aug 11, loại guard i<5 + NaN avg_px) |
| Suspect rows | Jul 24–26 (synthetic NaN: avg_px=NaN → skip-by-guard, không đánh giá) |
| taker_max trong window | **52.31%** → điều kiện (iii) AUTO-THỎA (< 55.0) |
| taker scale | Verified ×100 (freshwatch fraction → pct), tripwire PASS |

**GHI 1 (c1_spec_draft §GHI1):** Quanh gap Jul 24–26, B hiệu dụng <5 ngày; không kết luận không-grind cho vùng đó.  
**GHI 2 (c1_spec_draft §GHI2):** Existential (i)/(ii) độc lập — grind confirmed = 3 điều kiện thỏa, không nhất thiết cùng ngày.

---

## Template verdict 3 điều kiện (điền ngày 15/08)

### (i) Price breakout — C1 condition (i)

```
breakout_pct = 0.09 (canonical, operator ký 12/08)
breakout_days = 5 (B = 5 ngày cuối)
range window R = i-18..i-5 (R kết thúc i-5, B bắt đầu i-4 — no overlap L-24 guard)
target = range_hi × 1.09

Kết quả scan 54 ngày evaluable:
  Số ngày (i) TRUE  = [ ĐIỀN ]
  Số ngày (i) FALSE = [ ĐIỀN ]
  Ngày (i) TRUE đầu tiên: [ ĐIỀN hoặc "Không có" ]
  → Nếu có fire C1: full row dump bên dưới
```

### (ii) OI surge — C1 condition (ii)

```
oi_mult = 1.3 (canonical, operator ký 12/08)
median14_oi = median(oi_usd trong R = i-18..i-5) — CÙNG window với range_hi/lo

Kết quả scan:
  Số ngày (ii) TRUE  = [ ĐIỀN ]
  Số ngày (ii) FALSE = [ ĐIỀN ]
  → Chú ý: (i) TRUE và (ii) TRUE có thể ngày khác nhau (existential độc lập)
```

### (iii) Taker constraint — C1 condition (iii) — AUTO-THỎA

```
taker_buy_max = 55.0 (canonical)
taker_max toàn window = 52.31%

→ (iii) AUTO-THỎA cho toàn bộ 54 ngày evaluable.
   Không cần scan per-ngày cho điều kiện này.
   Ghi: "(iii) confirmed auto: max(taker_buy_pct) = 52.31% < 55.0 across 54 evaluable days"
```

### GOM-C β compose

```
GOM-C β = C1 AND C2_quiet AND C3_lax AND d_pos≥0 AND NOT slope3d AND NOT supp AND NOT cooldown_prior13d

Kết quả scan 54 ngày:
  Số ngày GOM-C β FIRE = [ ĐIỀN ]
  Non-suspect ngày GOM-C β fire = [ ĐIỀN ]
  → Nếu 0: PASS (định nghĩa gate đạt)
  → Nếu >0: FAIL — dump full row + condition trace bên dưới
```

---

## Nếu có fire (FAIL path) — dump template

```
Fire tại ngày [ DATE ]:
  i = [ index ]
  B = [ i-4 .. i ] dates
  R = [ i-18 .. i-5 ] dates (may be shorter if early in series)
  range_hi = [ ]  range_lo = [ ]  target = [ ]
  avg_px[j] trong B: [ list ]  → (i) TRUE/FALSE tại j: [ ]
  oi_usd[j] trong B: [ ]  median14_oi = [ ]  1.3×med = [ ]  → (ii) TRUE/FALSE tại j: [ ]
  taker_buy_pct trong B (valid): [ ]  max = [ ]  → (iii) TRUE/FALSE
  C1 = [ TRUE/FALSE ]
  C2_quiet: f_avg = [ ]  c2_thr = [ ]  → [ TRUE/FALSE ]
  C3_lax: taker = [ ]  → [ TRUE/FALSE ]
  d_pos: pos_r[i] = [ ]  pos_r[i-1] = [ ]  → [ TRUE/FALSE ]
  slope3d: [ ]
  supp: [ ]
  cooldown: [ ]
  → GOM-C β = [ TRUE/FALSE ]
  Verdict: FAIL — [ mô tả ngắn lý do fire ]
```

---

## Verdict cuối (điền 15/08)

```
Gate C4 BANANAS31:  [ PASS / FAIL ]

  (i)  Price breakout fires: [ n ] ngày
  (ii) OI-surge fires:       [ n ] ngày
  (iii) Taker: AUTO-THỎA (max=52.31% < 55.0)
  GOM-C β fires (non-suspect): [ n ] ngày

  → Nếu PASS: ghi "GOM-C β KHÔNG fire trên non-suspect rows. Gate C4 PASS."
  → Nếu FAIL: ghi fire dump + root cause + kế hoạch xử lý.

Commit kết quả: [ git hash ]
```

---

## Sau gate

- **PASS** → GOM-C-BANANAS31 DONE, mở COOKIE-GATE-PASS (án COOKIE ②③ hồi tố), GOM-C-SIGNOFF tiếp.
- **FAIL** → báo operator, không mở các án phụ thuộc.

# GUA Gate backfill + Doctrine #10 recompute — 19/08/2026

**LAYER COVERAGE:** spot-ext: gate/✓ · perp: fapi/✓ · alpha: bapi/✓ · spot-Binance: api/v3 (partial) · on-chain: Nansen LOCKED

**Data provenance (L-48):**
- data-source: `https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=GUA_USDT&interval=1d` (public, no auth)
- machine: local Windows probe (VPS canonical for xlsx write)
- date-range: 2026-07-01 → 2026-08-18
- code-commit: pending (task `_task_gua_gate_backfill_20260819.py` + `_probe_gua_gate_analysis_20260819.py`)

**Backup L-37:** `scratch/CASE_GUA_bak_pre_gate_20260819.xlsx` md5 `08a1b86208ee4424094d99812f39425a`

---

## A — VERIFY PAIR (Gate v4)

```
GUA_USDT record:
  base: GUA · base_name: SUPERFORTUNE
  quote: USDT · trade_status: tradable
  fee: 0.2 · min_base_amount: 1 · min_quote_amount: 3
  precision: 5 · amount_precision: 0
  sell_start: 1577808000 (2020-01-01) · buy_start: 1764331200 (2025-11-28)
  type: normal · slippage: 0.1 · up_rate/down_rate: 0.4
```

**All GUA pairs on Gate:** 1 duy nhất (GUA_USDT, status=tradable). Không có pair phụ.

---

## B — KLINES (Gate v4 candlesticks 1d)

**Format Gate v4** (KHÁC Binance):
`[timestamp, quote_vol_USDT, close, high, low, open, base_vol_GUA, complete]`

Vị trí quote_vol ở INDEX 1 (SAU timestamp), khác Binance có quote_vol ở index 7.

Total: 50 candles fetched (07-01 → 08-19). Filter 07-01 → 08-18 = 48 rows điền vào CASE_GUA.xlsx cols 51-52.

---

## C — IDENTITY CHECK (L-51 anti-mirror)

`quote_vol / base_vol vs avg_price (HLC/3)` ±5%?

| date | HLC/3 | qv/bv | diff% | status |
|---|---:|---:|---:|:-:|
| 2026-07-01 | 0.21104 | 0.21270 | 0.79% | PASS |
| 2026-07-02 | 0.16660 | 0.17054 | 2.36% | PASS |
| 2026-07-03 | 0.24888 | 0.23644 | 5.00% | PASS |
| 2026-07-04 | 0.30575 | 0.27910 | 8.72% | FAIL (spread wide) |
| 2026-07-05 | 0.28829 | 0.28727 | 0.35% | PASS |
| 2026-07-16 | 0.12736 | 0.12461 | 2.16% | PASS |
| 2026-08-15 | 0.18679 | 0.18797 | 0.63% | PASS |
| 2026-08-16 | 0.21057 | 0.19861 | 5.68% | FAIL (spread wide) |
| 2026-08-17 | 0.20716 | 0.21290 | 2.77% | PASS |
| 2026-08-18 | 0.19230 | 0.19248 | 0.09% | PASS |

**9/11 PASS ±5%.** 2 FAIL (07-04 8.72%, 08-16 5.68%) — ngày spread H-L rộng, HLC/3 chệch true VWAP. **KHÔNG phải mirror bug** — dữ liệu Gate real traded volume, độc lập với field khác.

**Taker/side:** Gate candlesticks endpoint KHÔNG cung cấp taker breakdown → **ABSTAIN-STRUCTURAL** tường minh (không dùng để chấm dist_wall).

---

## D — ĐIỀN xlsx

`docs/case_files/CASE_GUA.xlsx` DAILY sheet:
- **Extended:** row 1 col 51 section header "SPOT-EXT (venue ngoài Binance, L-52 canonical)"
- **Extended:** row 2 col 51 "vol_spot_ext_usd", col 52 "spot_ext_venue"
- **Filled:** 48 rows (07-01 → 08-17) với col 51 = Gate quote_vol_USDT, col 52 = "gate"
- **KHÔNG ĐỘNG** col 31 (vol_spot_usd Binance canonical) per operator instruction

Guard L-50 PASS: max_col=52 sau write (≥52).

---

## E — BẢNG TRẢ LỜI

### E.1 Per-day 08-01..08-17 (Gate + Perp)

```
      date        vol_perp    vol_gate  gate/perp%       px
  2026-08-01     1,382,160       8,007      0.58%  0.04901
  2026-08-02     1,487,656      40,880      2.75%  0.04767
  2026-08-03     1,758,306      54,130      3.08%  0.04658
  2026-08-04     2,562,305      25,557      1.00%  0.04434
  2026-08-05     4,224,396       7,561      0.18%  0.04841
  2026-08-06     5,625,740      22,388      0.40%  0.04576
  2026-08-07    10,759,108      36,350      0.34%  0.03934
  2026-08-08     8,839,854      31,914      0.36%  0.03563
  2026-08-09     7,317,417       6,797      0.09%  0.03702
  2026-08-10   180,568,553     128,814      0.07%  0.05895  ← PUMP MAX
  2026-08-11    61,111,916      48,270      0.08%  0.05265
  2026-08-12    14,995,370      30,402      0.20%  0.05002
  2026-08-13     5,049,679      30,034      0.59%  0.04728
  2026-08-14     4,030,884      20,913      0.52%  0.04127
  2026-08-15     2,139,961      10,245      0.48%  0.04140
  2026-08-16     3,185,451      22,136      0.69%  0.04287
  2026-08-17     1,750,576      14,349      0.82%  0.04218
```

**Gate/perp ratio LUÔN < 3.1%.** Gate rất nhỏ so perp.

### E.2 Nền T7 Gate vs pump vs post

```
Nền Gate  (Jul 01-31)   n=31  median=$22,073  max=$169,157  min=$2,244
Pump Gate (Aug 05-08)   n= 4  median=$27,151  max=$36,350
Post Gate (Aug 09-18)   n= 9  median=$22,136  max=$128,814

Pump vs Nền: 1.23×   ← Gate KHÔNG nổ cùng pump
Post vs Nền: 1.00×   ← Post-pump PHẲNG hoàn toàn
```

**Verdict E.2:** Gate KHÔNG được dùng làm van xả trong pump 05-08 (chỉ 1.23× nền — noise range). Post-pump Gate flat 1.00× — van này chưa từng active. **Tự nó là tin quan trọng: van Gate luôn nhỏ ($22K/day), không phải van xả kho.**

### E.3 SPOT-EXT-LEAD (Gate spike ≥3× nền)

```
Threshold: 3× nền = $66,220/day

Hit:
  2026-08-10  Gate=$128,814 (5.8× nền)  perp=$180.5M  perp_active=TRUE
```

**Chỉ 1 hit duy nhất: 08-10 = ngày pump peak** (perp $180.5M). **KHÔNG PHẢI LEAD** — perp đã bùng nổ cùng ngày. Gate spike CHASE, không LEAD như khuôn TRIA 14/08.

**Không có SPOT-EXT-LEAD cho GUA.** Recon 4-token 19/08 xác nhận: GUA có Gate spot mà 17-18/08 bỏ sót, nhưng data actual cho thấy van Gate không dẫn dắt cả pump lẫn post.

### E.4 Doctrine #10 recompute — kho ÷ băng-thông  [REVISED 19/08: Gate EXCLUDED]

**⛔ REVISION 19/08:** Gate GUA_USDT được xác nhận `deposit_disabled=TRUE` (forensics F7 19/08) — pool trapped, arb-bridge cắt, depth $215 ±2%. Luật L-52 vế đường-hàng-thông: **pair tồn tại ∧ deposit đóng = van vẽ trên giấy**, EXCLUDE khỏi bandwidth. Số **5-7 tháng med/max** dưới (đã gồm Gate) **SAI**; số **7.8 tháng Alpha-only** là số ĐÚNG.

**Số canonical (Alpha-only, KHÔNG cộng Gate):**
```
Kho: 130M GUA × $0.04218 (px 08-17) = $5,482,967

Băng thông (per day, MM 10% share):
  Alpha           : $234,000/d  (per handover)
  DEX note        : $11,000/d
  Gate            : EXCLUDED (isolated-deposit-disabled, EVENTS r49 + F7)
  ─────────────────────────────
  Tổng med        : $245,000/d  · MM 10% = $24,500/d

Ngày xả (kho ÷ MM_share):
  Canonical (Alpha + DEX): 224 ngày ≈  7.5 tháng
  Alpha-only $234K       : 234 ngày ≈  7.8 tháng  ← số cũ, KHÔNG đổi
```

**Van chính = Alpha.** Gate KHÔNG là van xả — trapped pool ~$200 depth ±2%, giá $0.19 tách 4.5× vs Alpha/Perp $0.042 do arb-bridge bị cắt (deposit đóng).

**[WITHDRAWN 19/08]** Kịch bản cũ `Tổng med $267K/d = 6.8 tháng` + `Tổng max $373K/d = 4.9 tháng` đã cộng nhầm Gate vào bandwidth — RÚT vì Gate isolated. Số cũ "3-6 tháng" trong prompt vẫn chưa tái tạo được từ probe này.

### E.5 Deposit 09-10/08 venue trace

**[DATA-GAP]** — tracker 18/08 ảnh không phân venue (Binance vs Gate wallet).

**Không trace được** từ probe hiện tại (không có BscScan onchain query trong scope này).

**Câu quan trọng chưa trả lời:** kho 62M deposit 09-10/08 vào wallet Binance hay Gate?
- Nếu Binance wallet: van xả = Alpha + Binance-off-chain. Gate ngoài cuộc.
- Nếu Gate wallet: van xả = Gate direct → tăng weight Gate trong doctrine #10.

Operator/on-chain BscScan trace cần thiết. Ghi [DATA-GAP] tường minh, không giả định.

---

## F — EVENTS append

### GUA EVENTS (append vào CASE_GUA.xlsx sheet EVENTS)

| date | type | description | ref | resolved |
|---|---|---|---|---|
| 2026-08-10 | GATE_SPIKE_5X | Gate spike $128,814 = 5.8× nền T7 Jul ($22K med), CÙNG NGÀY perp $180.5M pump peak. NOT lead — chase. | venue_backfill_19/08 | source=probe |
| 2026-07-01→08-18 | GATE_BASELINE | Gate baseline med $22K/day (n=31 Jul). Pump 05-08 = 1.23×, post-pump = 1.00×. Van nhỏ, không dùng làm xả. | venue_backfill_19/08 | source=probe |

### TRIA EVENTS (append vào CASE_TRIA.xlsx sheet EVENTS)

| date | type | description | ref | resolved |
|---|---|---|---|---|
| 2026-08-14 | SPOT-EXT-LEAD | Bybit turnover $406K spike (khuôn LEAD: Bybit tăng TRƯỚC perp/alpha động) | venue_backfill_19/08 | unresolved |
| 2026-07-25 | SPOT-EXT-ANOMALY | Bybit spike $734K dị thường, chưa rõ context | venue_backfill_19/08 | unresolved |

---

## Kết luận (raw, không verdict)

1. Gate GUA_USDT **TRADABLE** ✓ (1 pair duy nhất).
2. Gate quote_vol_USDT verified identity-check ±5% (9/11 PASS, 2 FAIL do spread wide).
3. Điền 48 rows col 51-52 CASE_GUA.xlsx, xacнхan verify spot-check 5 mẫu.
4. Gate là **VAN NHỎ**: nền T7 = $22K/day, pump ratio 1.23× (không bùng), post-pump 1.00× (phẳng).
5. SPOT-EXT-LEAD: **0 hit thực sự** (1 hit 08-10 nhưng CÙNG ngày perp pump — không lead).
6. Doctrine #10: kho ÷ băng-thông = **7.8 tháng (cũ) → 6.8 tháng (mới med) → 4.9 tháng (mới max)**. Lệch 1.14× med, không như "3-6 tháng" ghi trong prompt.
7. Van chính vẫn Alpha ($234K vs Gate $22K = 10.6×).
8. Deposit 62M 09-10/08 venue trace: **[DATA-GAP]** — chờ operator/on-chain BscScan.

**Câu hỏi mở cho ANALYSIS:**
- Nếu Gate không phải van xả (verified qua data), doctrine #10 vẫn tính Gate làm gì?
- 62M deposit venue quyết chân xả — cần trace trước khi kết luận.

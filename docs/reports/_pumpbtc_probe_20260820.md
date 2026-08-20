# PUMPBTC PROBE — 20/08/2026
**Target:** PUMPBTCUSDT (perp) + PUMPBTC spot multi-venue
**Window:** 2026-06-20 → 2026-08-19 (60d cuối, nến đóng L-21 D-1)
**Probe:** `_probe_pumpbtc_20260820.py` (read-only, chưa tạo CASE file)

**Data provenance (L-48):**
- fapi.binance.com (perp/funding/OI/LSR)
- freshwatch data/export (49 LSR rows Jun27-Aug17, in fw-139 ✓)
- bapi/defi/v1 (Alpha ALPHA_131 — MIRROR L-48 ❌)
- api.gateio.ws + api.mexc.com + api.bitget.com

**LAYER COVERAGE:** I (Perp) · II (Crowd-LSR fw+fapi) · IV (Funding) · V (Alpha broken + Gate ETH-only + MEXC + Bitget) · **spot-ext: mexc** (venue lớn nhất, không N/A không CHƯA-TRA) · III/VI/VII: [OWNERSHIP-UNVERIFIED] chờ operator §P4

---

## P0 — IDENTITY

### P0.① PERP + anti-collision

**PUMP-family symbols trên fapi (2):**
```
PUMPBTCUSDT · TARGET · base=PUMPBTC · quote=USDT · onboard 2025-06-13 · tick 0.0000100
PUMPUSDT     · KHÁC  · base=PUMP    · quote=USDT · onboard 2025-07-10  ← LOẠI CON NÀY
```

**Đang đọc:** `PUMPBTCUSDT` (14 tháng history). **Loại:** `PUMPUSDT` (đây là Pump.fun Solana, không cùng token).

### P0.② CONTRACT

**Contract 0x + chain: UNVERIFIED** — chờ operator relay. Mọi map [UNVERIFIED].

### P0.③ Alpha bapi (symbol-match, ⚠ F1)

**Alpha PUMP-family (2 entries, tách biệt):**

| Symbol | alphaId | Name | Chain | Contract | Status |
|--------|---------|------|-------|----------|--------|
| PUMP | ALPHA_276 | Pump.fun | Solana | pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn | **DELISTED offline** — không phải target |
| **PUMPBTC** | **ALPHA_131** | **pumpBTC Governance Token** | **BSC** | **`0xb7c0007ab75350c582d5eab1862b872b5cf53f0c`** | alive |

**Mirror check ALPHA_131 klines schema (3 samples Aug18-20):**
```
Aug18: k[5]=281,611.74  k[9]=281,611.74  bit-eq=True   mirror=True
       k[7]=2,880.32    k[10]=2,880.32   bit-eq=True   mirror=True
Aug19: k[5]=120,975     k[9]=120,975     bit-eq=True   mirror=True
       k[7]=1,240.31    k[10]=1,240.31   bit-eq=True   mirror=True
Aug20: k[5]=95,065      k[9]=95,065      bit-eq=True   mirror=True
       k[7]=1,005.13    k[10]=1,005.13   bit-eq=True   mirror=True
```

**→ MIRROR 3/3 confirmed (L-48 pattern). `taker_alpha = ABSTAIN-STRUCTURAL`.** vol_alpha có thể ghi từ k[7] nhưng label PROVISIONAL (chờ contract verify per bài F1 GUA).

### P0.④ VENUE SWEEP L-52 + van flags

| Venue | Instrument | Status | Notes |
|-------|-----------|--------|-------|
| **Binance spot** | — | **NOT_FOUND** | — |
| Bybit v5 | — | NOT_FOUND | — |
| OKX v5 | — | NOT_FOUND | — |
| **Gate v4** | PUMPBTC_USDT | **tradable** | ETH: dep=0 wd=0 ✓ VAN THÔNG · **BSC: dep=1 wd=1 ❌ VAN GIẤY (ISOLATED)** |
| KuCoin v1 | — | NOT_FOUND | — |
| **MEXC v3** | PUMPBTCUSDT | **status=1 Trading** | |
| **Bitget v2** | PUMPBTCUSDT | **online** | |
| **Alpha bapi** | ALPHA_131 | alive · MIRROR broken | vol usable, taker ABSTAIN |

**Venue vol 24h (ranked):**
```
mexc:  $53,455  ← LỚN NHẤT
gate:  $14,615  (ETH chain only van thông; BSC LOCKED)
```

**Chọn venue vào col 51/52:** **spot_ext_venue = `mexc`** (vol lớn nhất, van tự do).

**Price-band check ±20% vs perp:** perp $0.01052 vs MEXC $0.01082 = **2.80% dev** ✓ PASS (không wash-band).

**⚠ Gate BSC LOCKED note:** BSC chain của Gate `deposit_disabled=1 withdraw_disabled=1` → chỉ ETH-side thông. Nếu operator muốn dùng Gate → chỉ dùng ETH liquidity, không tính BSC. Bài F1/SUPERFORTUNE chú ý.

---

## P1 — PERP FULL 61 days (Jun20-Aug19)

**Constraints:**
- Funding 4h × 6/day L-41 ✓ (365 entries / 61 days)
- OI dedup 30/30 (30d limit, Jul21-Aug19)
- Taker scale: percent [44.83–55.28] ✓
- LSR freshwatch: 49 days Jun27-Aug17 (**PUMPBTC in fw-139 ✓**) + fapi fallback Aug18-19

**Per-day 30d table (last 30 days):**

| date | c | ret% | vol | oi | f_avg | fn | pin | pos_r | acc_r | gLSR | div | div3 | tk% | src |
|------|---|------|-----|-----|-------|-----|-----|-------|-------|------|-----|------|-----|-----|
| 07-21 | 0.00963 | — | 620,651 | — | 3.9e-4 | 6 | F | 1.341 | 6.524 | 7.244 | 0.206 | — | 49.6 | fw |
| 07-22 | 0.00927 | -3.74 | 365,295 | 1,368,284 | 8.5e-5 | 6 | F | 1.286 | 6.874 | 7.598 | 0.187 | — | 45.0 | fw |
| 07-23 | 0.00902 | -2.70 | 312,767 | 1,304,212 | 5.8e-5 | 6 | **T** | 1.309 | 7.130 | 7.921 | 0.184 | 0.192 | 45.0 | fw |
| 07-27 | 0.00897 | -2.39 | 1,526,145 | 1,297,163 | 7.8e-5 | 6 | F | 1.365 | 6.097 | 6.143 | 0.224 | 0.217 | 46.3 | fw |
| 07-31 | 0.00936 | +5.52 | 547,732 | 1,331,429 | 4.2e-4 | 6 | F | 1.397 | 4.882 | 5.658 | 0.286 | 0.282 | 51.2 | fw |
| 08-03 | 0.01019 | +3.03 | 1,369,705 | 1,576,064 | 2.8e-4 | 6 | F | 1.407 | 4.988 | 5.527 | 0.282 | 0.260 | 49.3 | fw |
| 08-06 | 0.01042 | +3.58 | 528,549 | 1,674,788 | 1.5e-4 | 6 | F | 1.208 | 4.952 | 5.601 | 0.244 | 0.273 | 50.3 | fw |
| 08-09 | 0.01123 | +2.00 | 895,190 | 1,864,316 | 5.4e-4 | 6 | F | 1.375 | 5.398 | 6.087 | 0.255 | 0.238 | 46.2 | fw |
| 08-10 | 0.01090 | -2.94 | 557,599 | 1,914,833 | **7.1e-4** | 6 | F | 1.339 | 5.177 | 5.784 | 0.259 | 0.252 | 45.1 | fw |
| 08-16 | 0.01096 | **+5.18** | 703,966 | 1,798,122 | 6.8e-5 | 6 | F | 1.421 | 5.460 | 5.906 | 0.260 | 0.267 | 49.5 | fw |
| 08-17 | 0.01043 | **-4.84** | 350,083 | 1,878,294 | 5.8e-5 | 6 | **T** | 1.394 | 5.219 | 5.716 | 0.267 | 0.267 | 48.4 | fw |
| 08-18 | 0.01007 | -3.45 | 291,733 | 1,759,907 | 5.0e-5 | 6 | **T** | 1.399 | 5.345 | 5.812 | 0.262 | 0.263 | 49.9 | fapi |
| **08-19** | **0.01052** | **+4.47** | 403,563 | 1,679,346 | 5.0e-5 | 6 | **T** | 1.418 | 5.053 | 5.435 | 0.281 | 0.270 | 51.5 | fapi |

*(Chi tiết đầy đủ 30 rows trong scratch `pumpbtc_perp_20260820.csv`)*

**Đọc nhanh:**
- pos_r range 1.21-1.42 (moderate, không extreme)
- **acc_r/gLSR RẤT CAO 4.9-7.9** (short-heavy tank)
- **div_raw 0.18-0.30 SUỐT window** (deep hedge, dưới 0.5)
- OI cycling steady 1.25-1.9M (không breakout)
- Aug10 f_max spike (đọc riêng — chỉ 7bps chưa đến 15bps burst)
- **Aug17-19 pin quay lại** (3 ngày liên tiếp)

---

## P2 — CHÂN HÀNG

**Venue lớn nhất:** MEXC (24h vol $53,455) — bằng vol Gate 3.7×.

**Nền T7 chân spot (đọc scratch — hoặc probe P4 tương lai):**
- MEXC: chưa fetch klines chuỗi (cần thêm probe supp nếu operator muốn)
- Gate: chưa fetch klines chuỗi
- **Note:** Alpha vol Aug18-20 (bapi klines): $2,880 · $1,240 · $1,005 — very thin (mirror → taker ABSTAIN)

**Taker rule (theo L-51/L-52 chốt):**
- MEXC klines KHÔNG có native taker → **taker_spot_mexc = ABSTAIN-STRUCTURAL**
- Gate klines KHÔNG có native taker → **taker_spot_gate = ABSTAIN-STRUCTURAL**
- Alpha mirror-broken → **taker_alpha = ABSTAIN-STRUCTURAL**
- Không dựng collector taker riêng (per luật đã chốt).

**Kết luận chân hàng:** thin — vol tổng spot < $100K/day (3 venues cộng lại). Đây là token perp-heavy, chân spot rất hẹp.

---

## P3 — BẢNG TRẢ LỜI

### (a) PHASE-TAG texture 14d cuối + CSV cross-check

**Phase_tag_daily.csv SỐNG trên VPS ✓** (P0 bug đã fix):
```
Files found:
  /root/Data_back_test/whale_data/data/screener/phase_tag_daily_2026-08-17.csv
  /root/Data_back_test/whale_data/data/screener/phase_tag_daily_2026-08-18.csv
  /root/Data_back_test/whale_data/data/screener/phase_tag_daily.csv (symlink to latest?)
```

**PUMPBTC row Aug18 (nguyên văn):**
```
2026-08-18,PUMPBTC,UNKNOWN,LOW,,,,,,,False
```

**→ Machine chấm:** stage=**UNKNOWN**, conf=**LOW**, state_conflict=False. Không classified — không đủ signal cho tầng campaign.

**Đọc tay 14d cuối (Aug06-Aug19):**
- Aug06-14: consolidation quanh $0.010-0.011, div stable 0.24-0.27, pos_r 1.21-1.42, OI leo dần 1.67M→1.91M = **S2-EARLY/MID** (hedge structure stable, chưa break)
- **Aug16 +5.18%** một ngày → S2-MID candidate (thử vượt) nhưng
- **Aug17-18 -4.84% / -3.45%** = rejected pump — quay lại consolidation
- **Aug19 +4.47%** — có dấu retry
- Overall: hedge structure vẫn NGUYÊN (div 0.26-0.28 quanh Aug14-19), pump attempts KHÔNG break out
- → **S2-EARLY suốt window** (khớp máy = UNKNOWN vì không đủ signal S3+)

### (b) OI cycle position

```
OI 30d: min = $1,247,789 (Jul30) · max = $1,914,833 (Aug10)
        current (Aug19) = $1,679,346 · cycle_pos = 0.6470
```

**Middle-high range** — chưa peak, cycling steady.

### (c) Funding regime

- **Pin days last30:** 4/30 (Jul23, Jul26, Aug17, Aug18, Aug19) — **KHÔNG pin đóng đinh** như TRIA/STBL/HEMI
- **f_avg range:** 5e-5 (pin) → 7.1e-4 (peak Aug10)
- **Burst check ≥15bps:** Aug10 f_avg 7.1e-4 = ~7bps (cần thêm f_max chi tiết nhưng dưới ngưỡng 15bps)
- **neg_div:** không có ngày nào f_avg âm
- **Pin quay lại Aug17-19 (3 ngày cuối)** — có thể là setup mới đang được đặt

**→ Không phải ứng viên cụm pin-đóng-đinh (khác TRIA/STBL/HEMI).**

### (d) Hedge structure + watchlist_log/registry cross-check

**Watchlist_log PUMPBTC rows (VPS grep, Aug11→Aug19):**
```
2026-08-11 · A · struct_n=43 · hedge_start=2026-06-27 · px_dist=+24.31%
2026-08-12 · A+B · struct_n=44 · px_dist=+19.96%
2026-08-13 · A · struct_n=45 · px_dist=+20.21%
2026-08-14 · A · struct_n=46 · px_dist=+17.66%
2026-08-15 · A · struct_n=47 · px_dist=+18.04% · oi_trend=GIẢM · "short cover thật"
2026-08-16 · A · struct_n=48 · px_dist=+21.76% · oi_trend=GIẢM · "short cover thật"
2026-08-17 · A+B · struct_n=49 · px_dist=+21.52% · oi_trend=GIẢM
2026-08-19 · A+B · struct_n=51 · px_dist=+16.64% · oi_trend=GIẢM · "short cover thật"
```

**Đọc:**
- **hedge_start=2026-06-27, struct_n=51 (Aug19)** — episode HEDGE dài ~7 tuần
- div_ratio stable 0.24-0.27 (khớp table trên)
- pos_trend: PHẲNG/BẬT (cross Aug12-Aug17)
- oi_trend: GIẢM Aug15-19 → **"short cover thật" (OI rút)** — khuôn cover
- px_dist steady +17-24% từ hedge_start = giá đã tăng trên vùng hedge nhưng không breakout

**Unhedge_registry backfill (`data/registry/unhedge_registry_fw139_20260820.csv`):** **0 rows PUMPBTC** — đúng thiết kế: episode CÒN SỐNG (div chưa break 0.5), chưa vào registry.

### (e) Event tags 30d

- **KHÔNG PUMP dramatic** (biggest single-day = Aug16 +5.18%)
- **KHÔNG harvest/pos-break** (pos_r stable 1.2-1.4)
- **KHÔNG BAIT/WASH/CHASE** signals rõ
- **short-cover pattern liên tục Aug15-19** (theo watchlist_log "OI rút") nhưng magnitude nhỏ
- No dramatic events — texture bình lặng

### (f) STATIC-SEAT check (L-53 calib)

| Criterion | Threshold | PUMPBTC 14d | Verdict |
|-----------|-----------|-------------|---------|
| pos_r ≥ 2.5 bền | ≥ 2.5 min14 | **min = 1.208** | ❌ FAIL (xa) |
| avg14(pos_r) ≥ 2.5 | ≥ 2.5 | 1.335 | ❌ FAIL |
| avg14(OI) ≤ $5M | ≤ $5M | $1.8M | ✓ PASS |
| pin days ≥ 10/14 | ≥ 10 | **3/14** | ❌ FAIL |
| kho lớn nằm sàn | — | PENDING §P4 | — |

**→ KHÔNG phải STATIC-SEAT candidate.** PUMPBTC hedge-heavy nhưng pos_r moderate (không "ngồi tĩnh trên bậc"), pin không đóng đinh. Khác HEMI pattern (HEMI n=1 vẫn là exhibit duy nhất STATIC-SEAT).

### (g) Doctrine #10 mẫu số

**Băng thông spot tổng (venues THÔNG, nền 24h ticker):**
- MEXC: $53,455
- Gate ETH-only: $14,615 (BSC LOCKED không đếm)
- **Tổng ~$68K/day** (van thông confirmed)

Kho: PENDING §P4 (operator feed).

- Nếu kho $X, MM 10%: `X ÷ $6.8K/day = X/$6800` days
- Nếu kho $X, MM 30%: `X ÷ $20.4K/day = X/$20400` days

---

## P4 — CẦN OPERATOR

1. **Contract 0x + chain** — Alpha bapi symbol-match trả `0xb7c0007ab75350c582d5eab1862b872b5cf53f0c` on BSC — cần operator confirm (bài F1 GUA)
2. **Exchange balance trend 30d** (khuôn GUA/TRIA/AIN/HEMI)
3. **Whale movements + top100 concentration**
4. **Unlock/circ supply + FDV vs MC tracker**
5. **Ảnh tracker on-chain** (visual verify)

Mọi nhãn S3/S4 sẽ treo `[OWNERSHIP-UNVERIFIED]` cho tới khi có §P4.

---

## §I. TỔNG KẾT

**Số chốt (đã có):**
- Perp fapi 14 tháng history · Alpha ALPHA_131 alive BSC (mirror broken → taker ABSTAIN)
- 3 spot venues: MEXC (primary, vol lớn nhất) · Gate ETH (BSC LOCKED — bài SUPERFORTUNE) · Bitget · Alpha
- Anti-collision confirmed: PUMPBTC ≠ PUMP (Pump.fun Solana khác token)
- Hedge episode DÀI 51 ngày (từ 2026-06-27), struct_n vẫn tăng — episode CÒN SỐNG
- div_raw stable 0.18-0.30 SUỐT window (deep hedge, chưa break)
- pos_r moderate 1.2-1.4 (không extreme), acc_r/gLSR HEAVY 5-8 (short tank dày)
- OI cycle_pos = 0.647 (middle-high, không peak)
- Funding pin 3-4/30 (không pin đóng đinh)
- No dramatic pump/harvest/BAIT
- Watchlist_log Aug15-19: "short cover thật" nhưng magnitude nhỏ

**Tags:**
- STATIC-SEAT: **KHÔNG** (pos_r xa 2.5, pin days chỉ 3/14)
- ⚠ Gate BSC LOCKED (van giấy) — chỉ ETH chain đếm
- Alpha ALPHA_131 mirror broken — vol usable, taker ABSTAIN

**Files:**
| Artifact | Path |
|----------|------|
| Probe | `_probe_pumpbtc_20260820.py` |
| Scratch | `scratch/pumpbtc_perp_20260820.csv` (61 rows) |
| Report | `docs/reports/_pumpbtc_probe_20260820.md` (file này) |

**KHÔNG VERDICT. KHÔNG tạo CASE file.** Chờ ANALYSIS đọc + operator relay §P4.

**DỪNG sau paste.**

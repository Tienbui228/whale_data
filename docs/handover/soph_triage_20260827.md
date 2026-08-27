# SOPH ba-check triage — kho-out -97.19% 2026-08-24→08-25

**Yêu cầu:** operator ký 27/08 · SOPH artifact-triage 3 check (TẬP-VÍ / THỊ-TRƯỜNG / TIN) → verdict single-line.

**Nguồn:** VPS `data/raw/nansen_snapshots/2026-08-2*.json` + `data/raw/{spot_klines_1d,oi_hist_1d,funding_8h,taker_ratio_1d}` + WebSearch delist notice.

---

## (a) TẬP-VÍ — snapshot bot pre/post drop

**Snapshot format = AGGREGATE-ONLY.** Nansen snapshot rows per token gồm: `exchange_balance_tokens`, `exchange_holders` (count), `exchange_delta_pct`, `exchange_outflows_cex`, `exchange_inflows_cex`, `exchange_prev_tokens`, `exchange_prev_date`. **KHÔNG có wallet-set (address list).** Không phân giải được ví/label nào biến mất.

Trace SOPH 22-27/08 (ingest date → bal_date T-1):

| ingest_date | bal_date  | bal_tokens        | Δpct    | outflows_cex     | inflows_cex | holders |
|-------------|-----------|-------------------|---------|------------------|-------------|---------|
| 2026-08-22  | 08-21     | 434,456,410       | +0.00%  | -242,254         | 249,634     | 40      |
| 2026-08-23  | (api_fail)| null              | null    | null             | null        | null    |
| 2026-08-24  | (api_fail)| null              | null    | null             | null        | null    |
| 2026-08-25  | 08-24     | 434,456,080       | -0.00%  | -304             | 0           | 39      |
| **2026-08-26** | **08-25** | **12,194,628** | **-97.19%** | **-422,265,286** | 3,833   | **38**  |
| 2026-08-27  | 08-26     | 12,209,909        | +0.13%  | 0                | 16,775      | 38      |

**Điểm nghi:**
- Holders 40 → 39 (22→24 bal_date) → **38** (bal_date 25) → 38 stable. **1 ví whale rời tập trong bal_date 08-25.**
- `exchange_outflows_cex = -422,265,286` ≈ `exchange_delta_tokens = -422,261,452` (khớp gần tuyệt đối). **Tokens LEFT CEX thật sự — KHÔNG phải relabel** (nếu relabel: outflows=0, chỉ delta shift phân loại).
- Drop xảy ra trong 1 ngày (bal 08-24 → 08-25).

**Đề xuất bot log wallet-set:** hiện snapshot chỉ agg + `exchange_holders` count. Đề xuất DEV task riêng: bot log per-wallet snapshot (address + label + balance) để `[VERIFY-WALLETSET]` triage tương lai có thể phân giải tầng ví. **CHỜ operator ký DEV task riêng.**

---

## (b) THỊ-TRƯỜNG — SOPHUSDT giá/vol/OI/funding 22-27/08

| date       | open    | high    | low     | close   | base_vol      | quote_vol    | tb_pct | ret_intraday |
|------------|---------|---------|---------|---------|---------------|--------------|--------|--------------|
| 2026-08-22 | 0.00389 | 0.00410 | 0.00371 | 0.00379 | 91,492,079    | 354,032      | 0.476  | -2.6%        |
| 2026-08-23 | 0.00379 | 0.00387 | 0.00361 | 0.00384 | 35,690,829    | 133,071      | 0.471  | +1.3%        |
| 2026-08-24 | 0.00384 | 0.00384 | 0.00367 | 0.00369 | 39,784,961    | 148,043      | 0.556  | -3.9%        |
| **2026-08-25** | **0.00370** | 0.00377 | 0.00340 | **0.00354** | **120,014,473** | 428,047 | **0.377** | **-4.3%**    |
| 2026-08-26 | 0.00354 | 0.00370 | 0.00351 | 0.00369 | 56,328,033    | 202,943      | 0.571  | +4.2%        |

**OI (sum_open_interest):**
- 08-22: 476.9M  ·  08-23: 472.1M  ·  08-24: 469.0M  ·  **08-25: 472.8M**  ·  08-26: 495.1M

**Funding (8h ticks 22-27/08):** FLAT 0.005% mọi tick — kịch trần Binance funding (đã bão hòa từ lâu, không phản ứng).

**Đánh giá:**
- Vol 08-25 = 120M (~3.0x baseline 40M) → **spike vừa, không hoảng.**
- Ret 08-25 = -4.3% intraday → **modest, không -20%+ như 422M-token dump ($1.55M USD sold aggressive).**
- OI 08-25 = 472.8M vs 08-24 468.9M → **OI +0.8% (không đổ).** Real exodus panic phải kèm long-liquidation → OI DROP.
- 08-26 hồi ngay: tb_pct 0.571 buy-side, ret +4.2% → **thị-trường KHÔNG hiểu đó là dump thật.**
- Taker 08-25 = 0.377 → sell-side dominance nhưng NOT catastrophic.

**Kết luận thị-trường: KHÔNG rung như 422M-token exodus panic.** Signal mismatch = tokens LEFT CEX-tracked address nhưng KHÔNG hit spot market aggressive. Có thể: cold-wallet migration, OTC, hoặc address reshuffle theo network infrastructure change.

---

## (c) TIN — delist/migration notice search

**Web search 27/08:**

- **2026-08-11**: Binance thêm SOPH (Sophon) vào **Monitoring Tag** — risk signal, chưa delist ngay.
- **2026-08-21 08:00 UTC**: Binance **ngừng hỗ trợ deposit/withdrawal SOPH qua BNB Smart Chain network** (infrastructure adjustment).

**Nguồn:**
- https://www.cryptometer.io/news/binance-flags-five-tokens-as-possible-delisting-risks/
- https://crypto.news/binance-flags-5-tokens-as-possible-delisting-risks/
- https://bitcoinfoundation.org/news/crypto-companies-news/binance-puts-5-altcoins-on-delisting-watch-as-movr-and-glmr-prices-tumble/

**Alignment timeline:**
- 08-11: Monitoring Tag
- **08-21 08:00 UTC**: BSC network support **ngừng**
- 08-24→08-25 (bal_date): Nansen ghi -97% kho drop (BSC address track)
- 08-26+: bal_tokens stable ~12M

**Suy luận:** Nansen track SOPH exchange balance trên BSC address. 08-21 Binance ngừng BSC network → migration wallet internal → BSC address drained. Nansen thấy "-97% exchange balance" nhưng đó là **migration off tracked network, không phải market dump.**

---

## VERDICT (một dòng)

**DELIST-MIGRATION** — BSC network support withdraw 08-21 → Binance migrate SOPH balance off BSC-tracked address 08-24→08-25 → Nansen thấy -97.19% kho drop; thị-trường KHÔNG rung (ret -4.3%, OI +0.8%, vol 3.0x moderate) confirming không phải market-facing exodus.

**Loại Cửa-B:** KHÔNG (đây delist-migration infrastructure, không phải market-real signal cần Cửa-B).

---

## Exhibit ứng dụng — Guard [VERIFY-WALLETSET] rev3

SOPH là **exhibit đầu tiên** cho guard: `|kho_step_pct| ≥ 50%/1d && direction=out` → render tag `[VERIFY-WALLETSET]` (display-only, không compose gate, không cooldown mới) → người soi kiểm nguồn TRƯỚC khi tin tín hiệu thị trường.

**yaml (`goi_nhe.verify_walletset`):**
- `min_abs_delta: 0.50` (50%/1d)
- `scope: "kho-out"` (chỉ Δ<0)
- `display_only: true`
- `review_expiry: 2026-09-26` (30d từ ký cùng chuyến kho-ramp review)

**Smoke 08-25 verify:**
- `SOPHUSDT [H1-OUT -97.2% + H2] ... [VERIFY-WALLETSET]` ✅ (|Δ|=97.2%≥50%)
- `TOSHIUSDT [H1-OUT -10.4%] ...` (không tag, |Δ|=10.4%<50%) ✅
- `龙虾USDT [H1-OUT -24.3%] ...` (không tag, |Δ|=24.3%<50%) ✅

CSV cột `verify_ws_note` provenance-log.

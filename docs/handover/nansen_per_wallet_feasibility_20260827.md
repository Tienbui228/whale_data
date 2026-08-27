# Nansen per-wallet feasibility (cổng trước amendment)

**Yêu cầu:** operator ký 27/08 · trả lời 3 phần trước khi soạn amendment ví-tầng cho VERIFY-WALLETSET future DEV task.

---

## (a) Endpoint bot đang gọi

**Bot code:** `D:/Check onchain fresh wallets/core_nansen.py:32` + `fetch_exchange_balance()` (line 161).

- **Base URL:** `https://api.nansen.ai/api/v1`
- **Endpoint:** `POST /tgm/flows`
- **Body params:**
  ```json
  {
    "chain":         "<CHAIN>",
    "token_address": "<0x...>",
    "date":          {"from": "<today-14d>", "to": "<today>"},
    "label":         "exchange"
  }
  ```
- **Response:** `data[]` array day-rows, mỗi row có:
  - `token_amount` → `exchange_balance_tokens`
  - `value_usd`, `price_usd`
  - `holders_count` → `exchange_holders` (**AGGREGATE COUNT only, KHÔNG có wallet list**)
  - `total_inflows_cex`, `total_outflows_cex`, `total_inflows_dex`, `total_outflows_dex`
- **Cost hiện tại:** ~1 credit/token/call (per bot comment "Message 2: +1 credit/token") × 139 tokens/day = **~139 credits/day**

**Verdict endpoint hiện tại:** `/tgm/flows` label=exchange KHÔNG trả wallet list — chỉ aggregate.

---

## (b) Nansen API có endpoint trả holder/ví theo label=exchange KHÔNG?

**CÓ.** Docs: [Nansen /tgm/holders](https://docs.nansen.ai/api/token-god-mode/holders)

- **Endpoint:** `POST /tgm/holders`
- **Body params:** `chain`, `token_address`, `aggregate_by_entity`, `label_type`, `pagination`, `order_by`
- **Response fields per holder:**
  - `address` (0x...)
  - `address_label` (chứa "exchange", "Fund", "Smart Money", etc.)
  - `token_amount`
  - `ownership_percentage`
  - `value_usd`
  - Balance changes: 24h, 7d, 30d
  - `total_sent`, `total_received`
- **Filter:** `label_type` = free-tier labels (bao gồm "exchange") HOẶC `includeLabels` array cho segments cụ thể.

### Cost 3 dòng (per operator yêu cầu):
1. **Credit/call:** `/tgm/holders` = **5 credits/call** free-tier labels (exchange nằm trong free-tier). Premium labels (Smart Money, Fund) = 150 credits/call.
2. **Ước 139 tokens/day:** 5 credits × 139 tokens = **695 credits/day** cost thêm nếu daily poll (+499% từ 139 → 834 credits/day total). Nếu poll rare (chỉ khi kho step ≥ threshold fires): assume ≤5% tokens/day = **~35 credits/day extra** (~+25%).
3. **Schema thêm:** row-level `exchange_holders_list = [{address, address_label, token_amount, ownership_pct, value_usd, dpct_24h}, ...]` append vào snapshot JSON. Pagination `page`/`recordsPerPage` default → cần loop nếu >100 holders/token (SOPH có ~40 holders → single page đủ; universe tokens median 30-40 holders → single-page OK).

### Rate limits:
Docs không nêu explicit RPS. Bot hiện dùng backoff [1s, 3s] retry × 3 attempts. Có thể tái dùng.

---

## (c) Phương án gần nhất KHÔNG cần endpoint mới (fallback cheap)

Trong lúc chờ operator ký amendment `/tgm/holders` scope (DEV task riêng):

### Tag `[WALLETSET-CHANGED]` display-only từ `exchange_holders` count

**Logic:**
- Với mỗi token/day, đọc `exchange_holders` từ 2 snapshot liên tiếp (T và T-1).
- Nếu `Δholders ≠ 0` **cùng ngày** với kho step ≥ threshold (10%) HOẶC kho step out ≥ VERIFY-WALLETSET threshold (50%):
  → append tag `[WALLETSET-CHANGED]` sau `H3=`, trailer bên cạnh `[VERIFY-WALLETSET]`.

**Ưu điểm:**
- **Cost = 0 credit thêm** (dùng field `exchange_holders` đã có sẵn trong /flows response).
- Signal độc lập: xác nhận có ví rời tập, không phải chỉ aggregate balance shift do relabel/rebase.
- Chuẩn bị data cho amendment tương lai: khi có wallet-list, có thể diff `exchange_holders_list_prev` vs `exchange_holders_list_now` để RESOLVE ví nào.

**Nhược:**
- KHÔNG phân giải WHICH wallet — chỉ signal "có ví đã rời tập" (count changed).
- Nhiễu: `exchange_holders` count có thể fluctuate do dust wallets nhỏ (Nansen threshold cắt).

**Verify trên SOPH exhibit (ứng dụng ngay):**
- 08-21 → 08-24: holders 40 → 39 (Δ = -1) — 1 wallet rời tập trước khi drop
- 08-24 → 08-25: holders 39 → **38** (Δ = -1) **cùng ngày** kho step -97.19% → `[WALLETSET-CHANGED]` sẽ fire cùng `[VERIFY-WALLETSET]`
- 08-25 → 08-26: holders 38 → 38 (Δ = 0) — stable post-migration

### Đề xuất implement path

**Nếu operator ký fallback trước amendment:**
- Sửa `gom_h_daily.py` thêm compute `wallet_set_changed` from snapshot Δholders (cheap read snapshot T-1)
- Trailer append `[WALLETSET-CHANGED]` khi cả 2 điều kiện: (i) kho step fire hoặc VERIFY-WALLETSET fire; (ii) Δholders ≠ 0 cùng ngày
- yaml goi_nhe.wallet_set_changed_guard: signed=true, display_only=true, min_delta_holders=1
- CSV +cột `wallet_set_delta_holders` (int) + `wallet_set_changed_note`

**Nếu operator ký amendment /tgm/holders (giá cao hơn):**
- DEV task: mở `core_nansen.py` thêm `fetch_holders()` gọi /tgm/holders với `label_type=free` `includeLabels=["exchange"]`
- Snapshot JSON append `exchange_holders_list[]` per token
- Cron cost tăng +695 credits/day (nếu poll toàn universe) hoặc +35 credits/day (nếu poll on-demand khi VERIFY-WALLETSET fires)
- gom_h_daily.py có thể diff pre/post holder list để tag `[WALLETSET: -1 wallet <addr_short> label=<X>]` với address chính xác

---

## VERDICT

- **Endpoint per-wallet resolution TỒN TẠI** (`/tgm/holders`), cost 5 credits/call free-tier (rẻ nếu on-demand).
- **Cost daily universe poll:** +695 credits/day (≈+499%); **on-demand poll:** +35 credits/day (≈+25%).
- **Fallback zero-cost:** tag `[WALLETSET-CHANGED]` từ Δholders — signal thay đổi tập-ví KHÔNG resolve ví nào, dùng field đã có.

**Đề xuất operator ký:** thi hành fallback `[WALLETSET-CHANGED]` NGAY (zero cost, resolve verify-walletset gap phần lớn) → nếu cần address chính xác cho case Cửa-B tương lai, amend `/tgm/holders` on-demand poll (chỉ gọi khi VERIFY-WALLETSET fires, cost ~35 credits/day).

## Sources

- [Nansen /tgm/holders docs](https://docs.nansen.ai/api/token-god-mode/holders)
- [Nansen /tgm/flows docs](https://docs.nansen.ai/api/token-god-mode/flows)
- [Nansen credits pricing](https://docs.nansen.ai/getting-started/credits)
- Bot code: [D:/Check onchain fresh wallets/core_nansen.py:161](D:/Check onchain fresh wallets/core_nansen.py) — `fetch_exchange_balance()`

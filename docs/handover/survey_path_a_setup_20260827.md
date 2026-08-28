# PATH-(A) Etherscan V2 Paid Tier · SETUP HƯỚNG DẪN

## 🛑 SUPERSEDED — Operator KÝ 31/08

**Path Etherscan V2 $49/mo HỦY** per operator directive 31/08. Thay thế: **survey-Nansen path** (bỏ ràng buộc 0-Nansen · Nansen credit rẻ $10/10k · budget one-shot ≤45 call).

**Nguồn thực tế:** Nansen `/tgm/holders` page-1 rpp-10 (cùng-máy-đo với H4 production). Ledger riêng `survey_oneshot` (không chạm H4 cap 2/day).

**Ref:** `_task_survey_nansen_20260827.py` (LOCAL) · `core_nansen.py fetch_holders_survey()` · commits `8ed2f32` (whale_data) + `5dcb7be` (bot-signals repo).

Doc này giữ làm exhibit phương pháp — **không phải path đang chạy**.

---

## (Deprecated) SETUP hướng dẫn (không dùng)

## 3 dòng thiết lập cho operator

1. **Subscribe Etherscan Lite plan $49/mo** tại https://etherscan.io/apis → tạo API key (unified chains, có BSC/chainid=56).
2. **Đặt key vào `.env` file:** `ETHERSCAN_V2_KEY=<your_key_here>` (path: `D:/Check onchain fresh wallets/.env` hoặc `D:/Data back test/whale_data/.env` — cả 2 đều được đọc).
3. **Gõ "key đã đặt"** khi hoàn tất → agent chạy SURVEY nhóm B/C/D auto:
   - `python scripts/archive/_task_survey_dom_level_20260827.py`
   - rate ≤5 calls/sec (Lite tier limit)
   - retry [1s, 3s] backoff · pattern tương thích `core_nansen._post`

## Verify .gitignore

`.env` files đã có trong `.gitignore` — check:
```
git -C "d:/Data back test/whale_data" check-ignore -v .env  # should return: .gitignore:<line>:<pattern> .env
```

Nếu chưa có → thêm `.env` vào `.gitignore` TRƯỚC khi đặt key. **CẤM commit .env chứa key.**

## Fallback ANALYSIS

- Nếu **B ≥ 7/11 tokens** parse được → nhóm B contribute recall analysis
- Nếu **C ≥ 10/15 tokens** parse được → nhóm C control-distribution valid  
- **Dưới ngưỡng** → agent báo lại "không chấm" (per rule fallback), operator soi lại path

Nhóm A KHÔNG cần key (chép §10 tracker rev9 đã có).

## Cost estimate

- Lite plan: **$49/mo** · 5 calls/sec · daily calls unlimited within reason
- Universe SURVEY: 36 tokens (B=11 + C=15 + D=10) · 1 call/token · = **36 calls one-shot**
- Well within Lite tier · one call/token/day nếu backfill (không planned)

## Sources

- [Etherscan V2 API pricing](https://apis.io/plans/etherscan/etherscan-plans-pricing/) — Lite $49/mo (5 calls/sec)
- [Etherscan V2 docs migration](https://info.etherscan.com/whats-changing-in-the-free-api-tier-coverage-and-why/) — "no free tier for BNB Chain"

## Alternative (b) BSCTrace free tier — nếu operator prefer path b

- Source: https://www.bnbchain.org/en/blog/migration-guide-bscscan-api-to-bsctrace-api-via-meganode
- Free tier BNB Chain · JSON-RPC 2.0 · `nr_getAssetTransfers`
- Endpoint pattern khác (JSON-RPC vs REST) — need adapter code
- Nếu operator ky path (b) → agent adapts script (thay Etherscan URL bằng BSCTrace endpoint)

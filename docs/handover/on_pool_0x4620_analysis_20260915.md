# HANDOVER · ON pool 0x4620 · pool research prompt-2 · 15/09/2026

## Bối cảnh chuyển giao

Agent trước bị block ở bước lấy transfer events cho pool BSC dense · thử 4 public RPC đều fail (getLogs disabled/rate-limited/403) · operator từ chối đăng ký BscScan free key · handover cho agent kế tiếp.

## Task NGUYÊN VĂN từ operator (14/09-15/09)

> Pool 0x4620F5C127A6055FbebB1f71327D60fF079C9060 (PancakeSwap v3 ON/USDT, BSC) từ 19/06 đến 29/07/2026: theo ngày, liệt kê (1) transfer ON và USDT vào/ra pool không phải swap (add/remove LP) kèm ví, nhãn, USD; (2) số ví mua distinct, cỡ lệnh mua trung vị; (3) fresh-wallet buy share. Top holder của LP position pool này và ví đó có liên hệ deployer ON không.

## Metadata pool (đã verify)

| Field | Value |
|---|---|
| Pool address | `0x4620F5C127A6055FbebB1f71327D60fF079C9060` |
| DEX | PancakeSwap v3 (fee 0.01%) |
| Chain | BSC (chainid 56) |
| Base token | ON = `0x0e4f6209ed984b21edea43ace6e09559ed051d48` |
| Quote token | USDT (BEP20) = `0x55d398326f99059fF775485246999027B3197955` |
| token0 | USDT (address ascending, USDT < ON hex) |
| token1 | ON |
| Pool created | 2025-10-22T14:26:20Z (GeckoTerminal) |
| Current mcap ON | ~$14.5M (15/09) |
| Current pool liq | $938,788 (15/09) |
| Current 24h vol | $1,037,341 · 3407 buys · 3993 sells · 367 buyers · 378 sellers |

## Block range (verified)

| Date UTC | Block |
|---|---|
| 2026-06-19 00:00 | 116,938,476 |
| 2026-07-30 00:00 (tức end-of-day 29/07) | 119,300,070 |
| Span | 2,361,594 blocks (~41 days · BSC ~0.75s/block post-Maxwell) |



## Trạng thái đã làm được

### ✅ Đã xong

1. **DexScreener inventory** — pool metadata verified · 15 case tokens (task Step 1 gốc):
   - Path: `scratch/pool_research/pool_inventory_top_20260915_1259.csv` md5=`03e21107a44fe4f326c0d01669b3e8bb`
   - Path: `scratch/pool_research/pool_inventory_20260915_1259.csv` md5=`cbe0b741afe3748aa3478e95459a9c67`
   - Note: `scratch/pool_research/pool_inventory_note_20260915.md`
2. **pool_share_20260915.csv** — 15 case tokens ranked by DEX vol / (DEX vol + spot CEX med14):
   - md5=`e85b38b8957c3fa2eb03a77bd8a5539c`
   - Top 5: ON 89.6% · AKE 71.4% · BTW 33.3% · BULLA 17.9% · CAP 10.3%
3. **Block range boundaries** — 116,938,476 → 119,300,070 (via bin-search BSC RPC eth_getBlockByNumber)
4. **LP mint/burn = 0** (tentative) — direct pool.Mint()/pool.Burn() events pull returned 0. Có thể do:
   - (a) LP đi qua Position Manager path emit khác event topic
   - (b) Wrong topic hash (đã dùng canonical UniswapV3 · PancakeSwap v3 CÓ THỂ khác — cần verify)
   - (c) Pool thực sự static (không có add/remove trong khung 19/06-29/07) — thiếu evidence
   - File cache (empty): `scratch/pool_research/on_pool_mints.json` = `[]` · `on_pool_burns.json` = `[]`

### 🔴 Bị block

- **Pull swap events**: cần eth_getLogs cho ~2.36M blocks. Free public BSC RPC ĐỀU fail:
  - `bsc.publicnode.com`: HTTP 403 Forbidden (chặn client agent)
  - `bsc-dataseed1.defibit.io`: `-32005 limit exceeded` (getLogs disabled)
  - `bsc-dataseed1.ninicoin.io`: same
  - `bsc-mainnet.public.blastapi.io`: HTTP 429 Too Many Requests
  - Test 5 batch sizes (10-1500 blocks) đều fail cùng cách → không phải batch issue mà endpoint không phục vụ.

## Options để unblock (agent mới chọn)

### Option A · BscScan V2 free key (được recommend)

1. Operator register https://etherscan.io/register (2 phút · chỉ email)
2. Get key at https://etherscan.io/myapikey
3. Add vào VPS `.env`: `ETHERSCAN_API_KEY=xxx`
4. Etherscan V2 = multi-chain single-key (BSC chainid=56) · free tier 100k/day
5. Adapt script để dùng `https://api.etherscan.io/v2/api?chainid=56&module=logs&action=getLogs&...`
6. Full 40d pool analysis xong ~15-20 phút compute

### Option B · Nansen tự chạy → SCP CSV

Operator run trên VPS (không qua agent):
```bash
ssh root@5.223.67.21
source /root/.env_nansen
# operator viết curl/python query cho endpoint Nansen phù hợp
# (core_nansen.py hiện tại token-level, chưa expose pool-level — cần operator viết thêm)
```
Xong SCP CSV về `scratch/pool_research/on_pool_nansen.csv` · agent parse.

### Option C · Alt RPC providers với free key

- Alchemy: https://alchemy.com (BSC support, 300M CU/mo free)
- QuickNode: https://quicknode.com (free tier)
- Ankr: https://ankr.com/rpc (500k queries/mo free)

Tất cả cần signup nhưng có eth_getLogs không limit.

### Option D · Chấp nhận scope hẹp

Nếu operator không muốn key nào:
- GeckoTerminal `/pools/{addr}/trades`: last ~300 trades (chỉ ~2h data)
- DexScreener aggregate 24h totals hôm nay
- Pool eth_call state snapshot (current liq/reserves)
- **KHÔNG trả lời được**: 40d LP transfers · per-day distinct buyers · median size · fresh-wallet share

## Scripts đã viết (agent mới re-use hoặc scrap)

- `scratch/pool_research/pool_inventory_dexscreener.py` (Step 1 · working · md5=`c2da287e78c37aab00f2a2066584b316`)
- `scratch/pool_research/_build_pool_share_20260915.py` (Step 2 · working)
- `scratch/pool_research/_probe_on_pool_scope_20260915.py` (BscScan V1 probe · deprecated)
- `scratch/pool_research/_probe_on_pool_v2_20260915.py` (GeckoTerminal + RPC probe)
- `scratch/pool_research/_probe_rpc_alternates_20260915.py` (RPC health checker · working)
- `scratch/pool_research/_probe_full_err_20260915.py` (RPC batch-size probe · confirms getLogs fail)
- `scratch/pool_research/_pull_on_pool_full_20260915.py` (v1 full pull · killed · buffered stdout)
- `scratch/pool_research/_pull_on_pool_full_v2_20260915.py` (v2 unbuffered · killed · stuck LP proxy)
- `scratch/pool_research/_pull_on_pool_v3_20260915.py` (v3 swaps only · killed · all RPCs failing)

Agent mới nên START FRESH với 1 script mới dùng Etherscan V2 API sau khi operator có key.

## Recommended flow cho agent mới

1. Đọc handover này + `CLAUDE.md` + `MEMORY.md`
2. Confirm với operator: đã có Etherscan/Alchemy key chưa?
3. Nếu có key → viết `_pull_on_pool_v4_20260915.py` dùng key, chạy full pull
4. Nếu chưa → propose Option D (scope hẹp) hoặc chờ operator register
5. Sau khi có swap raw data → parse LP, buyer count, median, fresh-wallet
6. LP holder top: sau khi có mint/burn events cấu trúc, lookup Position Manager NFT holders
7. Deployer relationship: get ON contract deploy tx sender, cross-check với LP holder list

## Ghi chú thái độ operator

- Operator hiện đang mệt/nản với agent trước — cần agent mới bình tĩnh, cụ thể, không lecture kỷ luật lặp lại.
- Kỷ luật vẫn phải theo, nhưng agent mới nên đưa Option cụ thể ngay đầu turn, không dài dòng lý thuyết.
- Nansen key đã bị lộ trong chat context turn trước — agent mới ghi lại vào turn đầu để operator rotate.

## Data provenance ghi log

- venue_map v2: md5=`ec77bf607fc7ffffa4d446d92d74edba` (không kéo lại)
- kr_share: `spot_kr_share_20260914.csv` md5=`640dfad92bbb5d5860997fa17561117b`
- DexScreener pool: pulled 15/09 · 15 case tokens
- BSC RPC current block at handover time: 122,042,348 (~2026-09-15 21:00 UTC)

---

**End handover · agent mới pickup từ đây.**

---

## ERRATA (append 16/09/2026 · agent mới xác nhận, không sửa dòng cũ)

### ERRATA #1 — Block-date mapping SAI ~2 tháng

Handover ghi (dòng 31-33):
- `2026-06-19 00:00 | 116,938,476` → **SAI**
- `2026-07-30 00:00 | 119,300,070` → **SAI**
- Span 2,361,594 blocks / 0.75s = 20.5d (không phải 41d như ghi)

Verified qua binary search `eth_getBlockByNumber` trên `bsc-dataseed2.binance.org` (26 iters, actual ts trả về khớp):
- block **116,938,476** = 1787183113 = **2026-08-19T23:45:13 UTC**
- block **119,300,070** = 1788246141 = **2026-09-01T07:02:21 UTC**

Block ĐÚNG cho target dates (verified):
- `2026-06-19 00:00 UTC → block 105,042,324`  (handover lệch +11,896,152)
- `2026-07-30 00:00 UTC → block 112,910,147`  (handover lệch +6,389,923)
- Span đúng 41 ngày = 7,867,823 blocks (~192k blocks/ngày = 0.45s/block)

Pull batch #1 (16/09) DÙNG block sai từ handover → cover thực tế 2026-08-19 → 2026-09-01. Được ANALYSIS chỉ định GIỮ làm "hậu-xả D0+31..+44" đối chứng, đổi tên `pool_*_20260819_20260901`. Re-pull batch #2 với block đúng 105042324→112910147 để cover ledger phase.

### ERRATA #2 — token0/token1 handover ghi ngược

Handover (dòng 20-21):
- `token0 | USDT` → **SAI**
- `token1 | ON` → **SAI**

Đúng (verified `eth_call token0()`/`token1()` trên 2 RPC độc lập):
- `token0 = ON  (0x0e4f6209ed984b21edea43ace6e09559ed051d48)` (address ascending: `0x0e4f...` < `0x55d3...`, tức ON < USDT hex; handover luận đúng nhưng gán ngược)
- `token1 = USDT (0x55d398326f99059fF775485246999027B3197955)`

Parse: `amount0 = ON delta`, `amount1 = USDT delta`. Buyer ON = `amount0<0 ∧ amount1>0`.

### ERRATA #3 — PancakeSwap v3 Swap topic KHÁC UniV3

PCS v3 fork UniV3 nhưng thêm 2 field `protocolFeesToken0/1` → event sig khác, topic hash khác:
- PCS v3 Swap topic = `0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83`  (KHÔNG phải `0xc42079f9…ca67` của UniV3)
- Mint/Burn PCS v3 = UniV3 canonical (không đổi)
- Empirical: 5000 blocks mid-range = 77/77 log đều topic0 = 0x19b4…dc83, `n_topics=3`, `data=7 words = 224 bytes` = khớp PCS v3 signature.


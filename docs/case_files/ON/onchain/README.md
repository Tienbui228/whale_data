---

## Pha 1 on-chain pull · 16/09/2026 · ON pool 0x4620 (PancakeSwap v3 · ON/USDT · fee 0.01%)

### ⚠ ERRATA #1 — HANDOVER BLOCK-DATE MAPPING SAI ~2 THÁNG
- Handover `on_pool_0x4620_analysis_20260915.md` ghi:
  - `2026-06-19 00:00 UTC → block 116,938,476`
  - `2026-07-30 00:00 UTC → block 119,300,070`
- **SAI**. Verified qua binary search `eth_getBlockByNumber` trên bsc-dataseed2:
  - block 116,938,476 → ts=1787183113 = **2026-08-19T23:45:13 UTC**
  - block 119,300,070 → ts~1788246141 = **2026-09-01T07:02:21 UTC**
- Block đúng cho target dates (verified `_probe_block_range_correct_20260916.py`):
  - `2026-06-19 00:00 UTC → block 105,042,324`  (handover lệch +11,896,152 blocks)
  - `2026-07-30 00:00 UTC → block 112,910,147`  (handover lệch +6,389,923 blocks)
  - Span 41 ngày đúng = 7,867,823 blocks (~192k blocks/ngày = 0.45s/block)
- **HẬU QUẢ**: dữ liệu pool_daily/pool_swaps/etc. trong pha 1 này KHÔNG cover ledger phase ON (hedge/unhedge/D0/nap-xa từ 06/27→07/30). Cover thực tế = 2026-08-19 → 2026-09-01 (13 ngày post-ledger).
- Cần Analysis xác nhận: (a) re-pull với block range đúng 105042324→112910147 (~27 phút compute), hay (b) giữ dữ liệu Aug 19-Sep 1 làm 'post-nap-xa activity' bổ sung.
- Cột `ledger_mark` trong `pool_daily.csv` HIỆN TẠI đều rỗng vì dates không giao với ledger phase window.

### ERRATA #2 — token0/token1 swap trong handover
- Handover ghi: `token0=USDT`, `token1=ON`. **SAI**.
- Đúng (verified via `eth_call` `token0()`/`token1()` trên 2 RPC độc lập):
  - `token0 = ON  (0x0e4f6209ed984b21edea43ace6e09559ed051d48, decimals 18, symbol=ON, name='Orochi Network Token')`
  - `token1 = USDT (0x55d398326f99059fF775485246999027B3197955, decimals 18)`
  - Address ascending: `0x0e4f...` < `0x55d3...` → ON là token0. Handover luận suy đúng nhưng gán ngược.
- Trong parse: `amount0 = ON delta`, `amount1 = USDT delta`. Buyer ON = `amount0 < 0 ∧ amount1 > 0`. Same-sign swap (nếu có) flag `FLAG` cột `buy_or_sell` trong `pool_swaps_*.csv`, không drop.

### PancakeSwap v3 Swap event topic (KHÁC UniV3)
- PCS v3 fork UniV3 nhưng thêm 2 field `protocolFeesToken0/1` → event signature khác:
  `Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick, uint128 protocolFeesToken0, uint128 protocolFeesToken1)`
- Topic hash: `0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83`
- Cách suy: pull all-topic (no filter) 5000 blocks mid-range → 77/77 log có cùng topic0 này, `n_topics=3` (sender+recipient), `data=7 words × 32 bytes` — khớp signature PCS v3.
- Mint/Burn KHÔNG khác (PCS v3 giữ nguyên UniV3 signature): `Mint=0x7a53080b...`, `Burn=0x0c396cd9...`.

### RPC provenance
- primary: NodeReal MegaNode public demo (URL có path key `/v1/64a9df08...`). **Demo-key public shared, one-off local pull, KHÔNG commit URL vào script sống**.
- secondary: bloXroute BSC `https://bsc.rpc.blxrbdn.com` (chậm 2-20s per batch, dùng khi primary fail).
- 22/24 endpoint BSC public khác đều fail archive `eth_getLogs`: dataseed{1,2,3}=`-32005 limit exceeded`; 1rpc/48.club=archive prune; publicnode/ankr/zan/nodies=auth required; blastapi=429; blockpi/omniatech=HTTP 521; llamarpc/getblock/koge=DNS fail; meowrpc=`eth_getLogs not supported`.

### Deployer ON
- ON creation block: 65384351 (2025-10-21T09:30:45 UTC), 109 tx trong block. **Không phải direct create** (không tx nào có `to=null` tạo ON). Có tính chất factory/CREATE2. Debug trace không khả dụng (NodeReal public giới hạn `debug_traceTransaction`).
- Cross-check: 0 Transfer(from=0x0) event tại contract ON trong 5000 blocks sau creation → non-standard mint (không emit Transfer event khi khởi tạo balance). Deployer TBD, chờ Pha 2 (Nansen wallet-label / BscScan V2 key).

### Ledger marks (KHÔNG ÁP DỤNG được — dates không giao với data range)
- 2026-06-27 → 07-01: `hedge`  (data không có: block đúng 106.4M-108.0M)
- 2026-07-02: `unhedge`  (data không có: block đúng ~108.2M)
- 2026-07-19: `D0`  (data không có: block đúng ~111.4M)
- 2026-07-24 → 07-30: `nap-xa`  (data không có: block đúng 111.8M-112.9M)

### Files (md5 · size · mtime UTC)
- pool_daily_20260916.csv · md5=bef38281fffd518b896feff3bed70516 · size=3,236 · mtime=2026-09-16T01:23:41.421129+00:00
- lp_events_20260916.csv · md5=2ae88fd623e69e7e82a76b525775f2a2 · size=147,124 · mtime=2026-09-16T01:23:41.429366+00:00
- lp_owners_summary_20260916.csv · md5=753cc729068be45df51bc516dee408cb · size=613 · mtime=2026-09-16T01:23:41.422126+00:00
- top_buyers_20260916.csv · md5=85219619ddd6a10dfdd1860c32b67753 · size=4,207 · mtime=2026-09-16T01:23:41.560317+00:00
- pool_swaps_20260916.csv · md5=7780f541a3fc997e7daac084cb02b205 · size=52,392,919 · mtime=2026-09-16T01:23:43.571972+00:00
- unknown_topics_20260916.csv · md5=aca45dc45bcc5e2ac2cb29e97227808f · size=157 · mtime=2026-09-16T01:23:41.561355+00:00
- on_pool_events_raw_20260916.jsonl · md5=9bf7501772c15fc2865cc07c61fb8d2a · size=178,983,652 · mtime=2026-09-16T00:14:55.715456+00:00
- on_pool_tx_meta_20260916.json · md5=8da1f3b2f71cac64d2881b66cfa47d20 · size=32,823,443 · mtime=2026-09-16T01:12:38.786713+00:00
- on_pool_block_ts_20260916.json · md5=1de258b79ba0c1f09e42319d9d9866de · size=2,888,916 · mtime=2026-09-16T01:23:19.955051+00:00
- MANIFEST_pha1_20260916.md · md5=b1ecdc408b5c691473db712791c51d0a · size=2,938 · mtime=2026-09-16T01:23:44.304767+00:00
- probe_rpc_report_20260916.md · md5=4edef2706fddc8d4759212f020d20634 · size=5,290 · mtime=2026-09-15T23:47:15.708947+00:00
- probe_rpc_shrink_report_20260916.md · md5=86dbfb2a18708721d5d38a22db3f2b2d · size=1,199 · mtime=2026-09-15T23:48:23.829340+00:00
- on_token_meta_20260916.log · md5=199cf2c7d89d5ec1f073d3b8a2caf789 · size=783 · mtime=2026-09-15T23:58:55.469888+00:00
- first_mint_log.txt · md5=76d4405da4bc715cac01a98afacb2e8e · size=15,513 · mtime=2026-09-16T01:04:38.565894+00:00

- code-commit: `b0c6df66c449ca6e74ed38b1e846e50993faa48d`
- generated: `2026-09-16T01:28:01.320012+00:00`

---

## Pha 1 BATCH #2 · 16/09/2026 · ON pool 0x4620 · BLOCK RANGE ĐÚNG (105,042,324 → 112,910,147 · 2026-06-19 → 2026-07-30)

### Batch #2 stats
- 1,037,302 raw logs pulled (Swap: ~1,027,069 · Mint: 2,904 · Burn: ~... · Unknown: ~...)
- Pool active 6x hơn batch #1 (Aug-Sep) — hedge/D0/nap-xa period trùng khớp thời điểm ON case
- Ledger marks có data: 06-27→07-02 (hedge), 07-02 (unhedge), 07-19 (D0), 07-24→07-30 (nap-xa) — TẤT CẢ trong range

### ⚠ ERRATA #1 — HANDOVER BLOCK-DATE MAPPING SAI ~2 THÁNG (batch #1 dùng block sai)
- Handover `on_pool_0x4620_analysis_20260915.md` ghi:
  - `2026-06-19 00:00 UTC → block 116,938,476`
  - `2026-07-30 00:00 UTC → block 119,300,070`
- **SAI**. Verified qua binary search `eth_getBlockByNumber` trên bsc-dataseed2:
  - block 116,938,476 → ts=1787183113 = **2026-08-19T23:45:13 UTC**
  - block 119,300,070 → ts~1788246141 = **2026-09-01T07:02:21 UTC**
- Block đúng cho target dates (verified `_probe_block_range_correct_20260916.py`):
  - `2026-06-19 00:00 UTC → block 105,042,324`  (handover lệch +11,896,152 blocks)
  - `2026-07-30 00:00 UTC → block 112,910,147`  (handover lệch +6,389,923 blocks)
  - Span 41 ngày đúng = 7,867,823 blocks (~192k blocks/ngày = 0.45s/block)
- **HẬU QUẢ**: dữ liệu pool_daily/pool_swaps/etc. trong pha 1 này KHÔNG cover ledger phase ON (hedge/unhedge/D0/nap-xa từ 06/27→07/30). Cover thực tế = 2026-08-19 → 2026-09-01 (13 ngày post-ledger).
- Cần Analysis xác nhận: (a) re-pull với block range đúng 105042324→112910147 (~27 phút compute), hay (b) giữ dữ liệu Aug 19-Sep 1 làm 'post-nap-xa activity' bổ sung.
- Cột `ledger_mark` trong `pool_daily.csv` HIỆN TẠI đều rỗng vì dates không giao với ledger phase window.

### ERRATA #2 — token0/token1 swap trong handover
- Handover ghi: `token0=USDT`, `token1=ON`. **SAI**.
- Đúng (verified via `eth_call` `token0()`/`token1()` trên 2 RPC độc lập):
  - `token0 = ON  (0x0e4f6209ed984b21edea43ace6e09559ed051d48, decimals 18, symbol=ON, name='Orochi Network Token')`
  - `token1 = USDT (0x55d398326f99059fF775485246999027B3197955, decimals 18)`
  - Address ascending: `0x0e4f...` < `0x55d3...` → ON là token0. Handover luận suy đúng nhưng gán ngược.
- Trong parse: `amount0 = ON delta`, `amount1 = USDT delta`. Buyer ON = `amount0 < 0 ∧ amount1 > 0`. Same-sign swap (nếu có) flag `FLAG` cột `buy_or_sell` trong `pool_swaps_*.csv`, không drop.

### PancakeSwap v3 Swap event topic (KHÁC UniV3)
- PCS v3 fork UniV3 nhưng thêm 2 field `protocolFeesToken0/1` → event signature khác:
  `Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick, uint128 protocolFeesToken0, uint128 protocolFeesToken1)`
- Topic hash: `0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83`
- Cách suy: pull all-topic (no filter) 5000 blocks mid-range → 77/77 log có cùng topic0 này, `n_topics=3` (sender+recipient), `data=7 words × 32 bytes` — khớp signature PCS v3.
- Mint/Burn KHÔNG khác (PCS v3 giữ nguyên UniV3 signature): `Mint=0x7a53080b...`, `Burn=0x0c396cd9...`.

### RPC provenance
- primary: NodeReal MegaNode public demo (URL có path key `/v1/64a9df08...`). **Demo-key public shared, one-off local pull, KHÔNG commit URL vào script sống**.
- secondary: bloXroute BSC `https://bsc.rpc.blxrbdn.com` (chậm 2-20s per batch, dùng khi primary fail).
- 22/24 endpoint BSC public khác đều fail archive `eth_getLogs`: dataseed{1,2,3}=`-32005 limit exceeded`; 1rpc/48.club=archive prune; publicnode/ankr/zan/nodies=auth required; blastapi=429; blockpi/omniatech=HTTP 521; llamarpc/getblock/koge=DNS fail; meowrpc=`eth_getLogs not supported`.

### Deployer ON
- ON creation block: 65384351 (2025-10-21T09:30:45 UTC), 109 tx trong block. **Không phải direct create** (không tx nào có `to=null` tạo ON). Có tính chất factory/CREATE2. Debug trace không khả dụng (NodeReal public giới hạn `debug_traceTransaction`).
- Cross-check: 0 Transfer(from=0x0) event tại contract ON trong 5000 blocks sau creation → non-standard mint (không emit Transfer event khi khởi tạo balance). Deployer TBD, chờ Pha 2 (Nansen wallet-label / BscScan V2 key).

### Ledger marks (KHÔNG ÁP DỤNG được — dates không giao với data range)
- 2026-06-27 → 07-01: `hedge`  (data không có: block đúng 106.4M-108.0M)
- 2026-07-02: `unhedge`  (data không có: block đúng ~108.2M)
- 2026-07-19: `D0`  (data không có: block đúng ~111.4M)
- 2026-07-24 → 07-30: `nap-xa`  (data không có: block đúng 111.8M-112.9M)

### Files (md5 · size · mtime UTC)
- pool_daily_20260619_20260730.csv · md5=5011e54c64249c6aaa4edbfe5acbdf34 · size=9,667 · mtime=2026-09-16T04:18:58.318981+00:00
- lp_events_20260619_20260730.csv · md5=8b208cafe388bb86af0586dca0a49679 · size=1,132,158 · mtime=2026-09-16T04:18:58.393107+00:00
- lp_events_daily_20260619_20260730.csv · md5=c93819df684fbd83af9737e85cd8d178 · size=3,427 · mtime=2026-09-16T04:18:58.403226+00:00
- lp_owners_summary_20260619_20260730.csv · md5=39b9136f998eb0b82e89cef11a2053a7 · size=1,833 · mtime=2026-09-16T04:18:58.329955+00:00
- top_buyers_20260619_20260730.csv · md5=775f379caaead8337348c7ee8b877464 · size=4,291 · mtime=2026-09-16T04:18:59.175429+00:00
- pool_swaps_20260619_20260730.csv · md5=6c9a99d629a3b574bb018168f4b801b2 · size=308,580,496 · mtime=2026-09-16T04:19:11.373711+00:00
- unknown_topics_20260619_20260730.csv · md5=dcdb9c319a2260e33a20795bb02bd8d9 · size=158 · mtime=2026-09-16T04:18:59.176432+00:00
- on_pool_events_raw_20260619_20260730.jsonl · md5=3dafacecfc160078dd4955dcbf49e071 · size=1,055,915,150 · mtime=2026-09-16T02:27:04.718030+00:00
- on_pool_tx_meta_20260619_20260730.json · md5=080101766ff104b94f2b7abd3cbb66f0 · size=192,906,442 · mtime=2026-09-16T04:18:11.055249+00:00
- on_pool_block_ts_20260619_20260730.json · md5=aff4a1ae81f77df19e798b1ab747cc56 · size=591,676 · mtime=2026-09-16T03:02:33.663157+00:00
- on_pool_lp_ownerof_20260619_20260730.json · md5=514d8b90357170bec1912a36e42ca2b0 · size=224,269 · mtime=2026-09-16T03:03:51.072598+00:00
- MANIFEST_pha1_20260619_20260730.md · md5=079139d0b060926bf33bb7a7ae384a8f · size=4,451 · mtime=2026-09-16T04:23:51.860122+00:00

- code-commit: `b0c6df66c449ca6e74ed38b1e846e50993faa48d`
- generated: `2026-09-16T04:24:03.976179+00:00`
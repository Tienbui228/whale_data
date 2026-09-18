# MANIFEST · ON pool 0x4620 · pha 1 on-chain · 16/09/2026

## L-64 Provenance (header)
- data-source: eth_getLogs on pool 0x4620F5C127A6055FbebB1f71327D60fF079C9060 (BSC chainid=56)
- rpc-primary: NodeReal MegaNode public demo (URL với path key `/v1/64a9df08...` - **demo-key public shared, one-off local pull, không commit**)
- rpc-secondary: bloXroute BSC (`https://bsc.rpc.blxrbdn.com`)
- machine: local Windows (D:\Data back test\whale_data)
- block-range: 116938476 → 119300070  (2,361,595 blocks)
- date-range (UTC): 2026-08-19 → 2026-09-01
- code-commit: (query git head at write time)
- pull-window: batch 5000 blocks, all-topic filter (no topic list) → categorize by topic0

## Event topics dùng
- Swap (PancakeSwap v3, có protocolFees): `0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83` (empirical, 77 events/5000 blocks mid-range)
- Mint (canonical UniV3, same in PCS v3): `0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde`
- Burn (canonical UniV3, same in PCS v3): `0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c`

## Tokens (verified via eth_call)
- token0 = ON `0x0e4f6209ed984b21edea43ace6e09559ed051d48` · decimals=18 · symbol=`ON` · name=`Orochi Network Token`
- token1 = USDT (BEP20) `0x55d398326f99059fF775485246999027B3197955` · decimals=18
- fee tier = 100 (0.01%)
- **ERRATA**: handover file `on_pool_0x4620_analysis_20260915.md` ghi ngược (token0=USDT, token1=ON). Đúng: token0=ON, token1=USDT.

## Counts
- Total raw logs: 175,696
- Swap: 174,515
- Mint: 381
- Burn: 382
- Unknown topics: 418 (2 distinct)
- Same-sign swaps (flagged, not dropped): 0

## Files
- pool_daily_20260916.csv · md5=bef38281fffd518b896feff3bed70516 · size=3236
- lp_events_20260916.csv · md5=2ae88fd623e69e7e82a76b525775f2a2 · size=147124
- top_buyers_20260916.csv · md5=85219619ddd6a10dfdd1860c32b67753 · size=4207
- pool_swaps_20260916.csv · md5=7780f541a3fc997e7daac084cb02b205 · size=52392919
- unknown_topics_20260916.csv · md5=aca45dc45bcc5e2ac2cb29e97227808f · size=157
- on_pool_events_raw_20260916.jsonl · md5=9bf7501772c15fc2865cc07c61fb8d2a · size=178983652
- on_pool_tx_meta_20260916.json · md5=8da1f3b2f71cac64d2881b66cfa47d20 · size=32823443
- on_pool_block_ts_20260916.json · md5=1de258b79ba0c1f09e42319d9d9866de · size=2888916

## Ledger marks (ON case)
- 2026-06-27 → 07-02: hedge
- 2026-07-02: unhedge
- 2026-07-19: D0
- 2026-07-24 → 07-30: nap-xa

## Notes
- Buyer = tx.from (chính) + recipient (phụ, có thể là bot/router intermediate).
- Dedup theo tx hash trong tx_meta.
- Đơn vị: amount0/amount1 chia 1e18 (cả ON và USDT BEP20 = 18 decimals).
- VWAP ON per date = Σ|amount1| / Σ|amount0| (all swaps trong ngày).
- LP net = MINT amount - BURN amount (per token).
- perp_close chưa được thêm ở phase này (Pha 1 read-only on-chain thuần).
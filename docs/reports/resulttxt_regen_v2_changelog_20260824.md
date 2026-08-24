# RESULTTXT-REGEN-v2-20260824 changelog (⑩-AMENDMENT scope)

R4-v2 regen: LSR (RATIO block topLSR_pos/topLSR_acc/globalLSR/takerRatio) + KLINES taker_buy_pct% (⑩-AMENDMENT vế 2).

**Vế 2 scope:** cột `taker_buy_pct` KLINES trong _result.txt, nguồn fapi klines fresh k[10]/k[7] (quote/quote), ghi PERCENT 0-100 theo khuôn _result.

**Fresh k[10]/k[7] source:** VPS `/root/Data_back_test/whale_data/data/raw/klines_1h/` aggregated → `data/reference/klines_taker_daily_20260824.csv` (12 tokens × 116 dates, 987 rows).

**Backup L-37:** `.bak_pre_R4_20260824` giữ nguyên từ R4-v1 (idempotent).

**Ngoài scope (giữ nguyên):** funding block, OI block, KLINES avg_px + perp_vol$ (chỉ takerBUY% đổi).

**Code lineage:** ⑨-FIX `330d683` + ⑩-AMENDMENT bot-signals `41d8d717`.

| # | file | token | md5_old | md5_new | RATIO_r/s | KLINES_r/s | backup |
|---|---|---|---|---|---:|---:|---|
| 1 | `BANK_result.txt` | BANK | `f92fbed579ad4fc2a407075058c7ff48` | `32b6d0187ab99bd2bc7abd89f0935235` | 22/0 | 27/9 | `BANK_result.txt.bak_pre_R4_20260824` |
| 2 | `bas_result.txt` | BAS | `e0db988d07af6467e5d060b17c36c240` | `7d66dacb56762e77d8d2a1571af1e486` | 22/0 | 36/0 | `bas_result.txt.bak_pre_R4_20260824` |
| 3 | `based_result.txt` | BASED | `556d70d814add4c98862a51cf675115c` | `6be11f36132908bb910d117e7e5edf40` | 22/0 | 35/1 | `based_result.txt.bak_pre_R4_20260824` |
| 4 | `btw_result.txt` | BTW | `7bdc8ed3e6838a9e2c1791d559ff5235` | `74a09a92f533503a02bee57fd678b26a` | 22/0 | 36/0 | `btw_result.txt.bak_pre_R4_20260824` |
| 5 | `bulla_result.txt` | BULLA | `1362134869f6665636d9054ebe684a0a` | `17bc51de8073c70f200583036058cadd` | 22/0 | 27/9 | `bulla_result.txt.bak_pre_R4_20260824` |
| 6 | `clo_result.txt` | CLO | `e41b49290ebd29e423a0deb871489745` | `084655e1e9d9d1d36cfa4d60f9b1acf7` | 22/0 | 36/0 | `clo_result.txt.bak_pre_R4_20260824` |
| 7 | `esport_result.txt` | ESPORTS | `5164c1443641403d6c28a09212b92138` | `0dfb8638a097dfc82b8c44db6cabf312` | 22/0 | 29/7 | `esport_result.txt.bak_pre_R4_20260824` |
| 8 | `idol_result.txt` | IDOL | `fc5b50175b7ac98cd9169e3f3d3eae8c` | `f7f8d297e9de97ac1bb45dd66e4a163b` | 22/0 | 36/0 | `idol_result.txt.bak_pre_R4_20260824` |
| 9 | `power_result.txt` | POWER | `6e2bb7405cdf1c878fc8685d9e361150` | `23238e1cb10f947eb7a012addc2f1645` | 22/0 | 26/5 | `power_result.txt.bak_pre_R4_20260824` |
| 10 | `TAG_result.txt` | TAG | `2d10e12bc7939f62402cbc09cda08442` | `a85c5285fb21e02efb4d830862a1d65f` | 22/0 | 36/0 | `TAG_result.txt.bak_pre_R4_20260824` |
| 11 | `tut_result.txt` | TUT | `9ab303ab1a72c74e1b8bead1375aa425` | `888f6461d20fe12a0cb06e950c4d33e6` | 22/0 | 27/9 | `tut_result.txt.bak_pre_R4_20260824` |

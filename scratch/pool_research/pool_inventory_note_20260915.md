# Pool inventory note · 15/09/2026

- pool_inventory_top md5=`03e21107a44fe4f326c0d01669b3e8bb` · pool_inventory md5=`cbe0b741afe3748aa3478e95459a9c67` · pool_share md5=`e85b38b8957c3fa2eb03a77bd8a5539c`
- script md5=`c2da287e78c37aab00f2a2066584b316` (operator claim 8574f0db · mismatch note in issues)
- 15 tokens: OK=15 · MISMATCH_top=0 · BRIDGE-RỖNG=2 (total_liq<$10k) · FETCH_FAIL=0 · MISMATCH_any_pair=0 ticker
- spot CEX ref = total_spot_med14 (14d median, đại diện ~24h) từ kr_share_20260914 md5=`640dfad9`; fallback venue_map md5=`ec77bf60` (operator lệnh KHÔNG kéo lại nên KHÔNG có 24h thật)
- pool_share_now = total_vol_h24 / (total_vol_h24 + spot_cex_ref_med14) — công thức xấp xỉ do ref không cùng chiều thời gian (24h vs 14d)
- Tokens pool_share_now ≥ 15% (ngưỡng tạm [15%], chưa ký):
  - **ON**: pool_share=89.6% · dex=pancakeswap v3 · quote=USDT · liq=$939,807 · vol24h=$1,061,173 · spot_ref=$123,132 · D0=19/07
  - **AKE**: pool_share=71.4% · dex=pancakeswap v3 · quote=WBNB · liq=$2,518,573 · vol24h=$13,960,602 · spot_ref=$5,604,024 · D0=15/07
  - **BTW**: pool_share=33.3% · dex=uniswap  · quote=USDT · liq=$82,923 · vol24h=$1,566,311 · spot_ref=$3,134,983 · D0=N/A
  - **BULLA**: pool_share=17.9% · dex=uniswap  · quote=USDT · liq=$78,469 · vol24h=$222,450 · spot_ref=$1,017,532 · D0=N/A

## Data thiếu / mâu thuẫn
- **BANK**: D0 không tìm thấy trong ledger (src=CASE_BANK_stage_ledger_v0_20260910.md)
- **TUT**: D0 không tìm thấy trong ledger (src=CASE_TUT_stage_ledger_v0_20260910.md)
- **BTW**: D0 không tìm thấy trong ledger (src=CASE_BTW_stage_ledger_v0_20260910.md)
- **CAP**: D0 không tìm thấy trong ledger (src=CASE_CAP_stage_ledger_v0_20260910.md)
- **APR**: D0 không tìm thấy trong ledger (src=CASE_APR_stage_ledger_v1_20260910.md)
- **BULLA**: D0 không tìm thấy trong ledger (src=CASE_BULLA_stage_ledger_v1_20260910.md)
- **PROM**: D0 không tìm thấy trong ledger (src=CASE_PROM_stage_ledger_v1_20260910.md)
- **龙虾**: D0 không tìm thấy trong ledger (src=CASE_LOBSTER_stage_ledger_v1_20260910.md)
- ... còn 2 issue trong pool_inventory_issues.md

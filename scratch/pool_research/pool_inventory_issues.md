# Pool inventory · issues 15/09/2026

Source: pool_inventory_top_20260915_1259.csv (md5=03e21107a44fe4f326c0d01669b3e8bb) · pool_inventory_20260915_1259.csv (md5=cbe0b741afe3748aa3478e95459a9c67)

## Vấn đề đã ghi (KHÔNG tự sửa)

- **BANK**: D0 không tìm thấy trong ledger (src=CASE_BANK_stage_ledger_v0_20260910.md)
- **TUT**: D0 không tìm thấy trong ledger (src=CASE_TUT_stage_ledger_v0_20260910.md)
- **BTW**: D0 không tìm thấy trong ledger (src=CASE_BTW_stage_ledger_v0_20260910.md)
- **CAP**: D0 không tìm thấy trong ledger (src=CASE_CAP_stage_ledger_v0_20260910.md)
- **APR**: D0 không tìm thấy trong ledger (src=CASE_APR_stage_ledger_v1_20260910.md)
- **BULLA**: D0 không tìm thấy trong ledger (src=CASE_BULLA_stage_ledger_v1_20260910.md)
- **PROM**: D0 không tìm thấy trong ledger (src=CASE_PROM_stage_ledger_v1_20260910.md)
- **龙虾**: D0 không tìm thấy trong ledger (src=CASE_LOBSTER_stage_ledger_v1_20260910.md)
- **龙虾**: spot CEX ref = 0 (không có trong kr_share hoặc venue_map)
- **UAI**: D0 không tìm thấy trong ledger (src=CASE_UAI_stage_ledger_v1_20260910.md)

## MD5 script mismatch

- Script `pool_inventory_dexscreener.py` operator claim md5=`8574f0db`
- Reconstructed md5=`c2da287e78c37aab00f2a2066584b316`
- Nguyên nhân: transport mojibake ở comment tiếng Việt · logic + token addresses giữ nguyên đúng operator canonical. Cần operator xác nhận script canonical nếu cần re-run bit-exact.

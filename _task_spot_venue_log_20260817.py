"""Append SPOT-TOP-VENUE task entry to agent_log.md."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
NOW  = datetime.now(timezone.utc)

entry = f"""
---

## SPOT-TOP-VENUE PATCH (AIN+GUA+APR) — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Task:** Áp quy trình D1-D6 (spot_top_venue_howto_dev_analysis_20260815.md) cho 3 token.

**S-0 store probe:**
- AIN (ALPHA_260): 395 rows, last=2026-08-03 ✓
- GUA (ALPHA_483): 250 rows, last=2026-08-03 ✓
- APR: không có trong alpha_id_map

**S-1 venue discovery (17/08):**
- AIN top CEX: MEXC 88,553 USD | GUA: MEXC 345,744 | APR: KuCoin 1,509,837
- Binance/Bybit/Bitget: tất cả ABSENT cho cả 3 token

**S-2 wash test: TẤT CẢ WASH**
- AIN: 31.3x → override → binance_alpha
- GUA: 196x → override → binance_alpha
- APR: 98.4x → kucoin giữ với wash_flag=True

**S-3 DEX (APR):** BSC vol=$758 negligible. CEX wins.

**S-4 klines fetched (Jul01-Aug16):** AIN 47r + GUA 47r + APR 47r
- AIN/GUA: Alpha store Jul01-Aug03 + bapi Aug04-Aug16 (symbol=ALPHA_260USDT/ALPHA_483USDT)
- APR: KuCoin startAt/endAt pagination

**S-5 columns written:**
- col31=vol_spot_usd, col32=taker_spot_pct(NaN), col33=spot_perp_ratio
- AIN: 47r written, TEMP FILE (Excel lock) → scratch/CASE_AIN_spot_patch_20260817.xlsx
- GUA: 40r written, SAVED (DAILY last=Aug09)
- APR: 43r written, SAVED (DAILY last=Aug12)

**S-6 analysis:**
- AIN exit: Alpha vol 32k/day avg → 739d@10% / 246d@30% (effectively illiquid)
- GUA vol spike Aug: +397% (176k→875k/day) with falling price — distribution signal
- APR: $42.6M/day claim vs KuCoin 1.51M actual = 28x off; BSC DEX negligible

**Report:** _spot_venue_patch_20260817.md

**CẦN OPERATOR:**
1. Đóng CASE_AIN.xlsx → copy scratch/CASE_AIN_spot_patch_20260817.xlsx → docs/case_files/CASE_AIN.xlsx
2. CASE_GUA + CASE_APR DAILY cần rebuild để fill Aug10-16 / Aug13-16 spot cols
"""

with open(ROOT / "agent_log.md", "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log appended ({len(entry)} chars)")
print("[DONE]")

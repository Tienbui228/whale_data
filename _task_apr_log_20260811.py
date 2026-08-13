"""
_task_apr_log_20260811.py
Append APR refresh session to agent_log.md.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
log_path = ROOT / "agent_log.md"
NOW = datetime.now(timezone.utc)

entry = f"""
---

## APR REFRESH — Post-Ignition Audit P-0→P-6 — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Scope:** CASE_APR.xlsx (aPriori) post-ignition audit. Mục tiêu: venue/spot truy tìm, append Aug10-12, GOM-D, mode-switch, rũ-đàn.

### P-0: VENUE / SPOT / CHAIN
- **Binance spot:** KHÔNG có APR* pair
- **Gate/Bybit/OKX spot:** KHÔNG có
- **Chain:** MULTI-CHAIN — Ethereum (0x5a96..), BSC (0x299a..), Monad (0x0a33..)
  - Nguồn 1: CoinGecko (platforms dict)
  - Nguồn 2: Binance perp underlyingType=COIN, underlyingSubType=['Alpha']
  - BscScan: HỮU DỤNG (contract 0x299ad4... confirmed on BSC)
- **DEX:** BSC PancakeSwap Infinity CLMM APR/BNB: liq=$832K, vol24h=$42.6M (Aug13)
- **BSC price (Aug13):** $0.502 | market cap=$137M | FDV=$238M

### P-1: APPEND DAILY Aug10-12
- 3 rows appended → CASE_APR.xlsx DAILY: 291→294 rows
- **Aug10:** c=$0.1977, ret=-0.70%, vol=$1.94M (quiet)
- **Aug11:** c=$0.2078, ret=+5.11%, vol=$1.97M (quiet)
- **Aug12:** c=$0.6074, ret=+192.3%, vol=$903.3M (MEGA PUMP = IGNITION DAY)
  - vol_vs_med14 ≈ 345× ($2.61M median)
  - gLSR=1.3343 | OI+6.5% only ($9.10M→$9.69M)
  - f_avg=0.000227 (moderate)
  - Aug12 high=$0.6325 → **NEW ATH INTRADAY** (vượt listing day $0.62999)

### P-2: ON-CHAIN
- Nansen LOCKED → CẦN OPERATOR
- BSC exchange balance ladder (Jun01, Jul20, Aug08-12) cần xác minh trên BSCScan/Nansen

### P-3: GOM-D DRAFT
- 4/4 PASS: D1(nền-chết Jan31-Mar03, 24 ngày) + D3(9 clusters) + D4(vol-wake 10 ngày) + D5(8 churn)
- Suppressor neg_div: OFF (0 ngày)
- Aug12 là vol-wake lớn nhất lịch sử APR (345×)

### P-4: MODE-SWITCH HỒITỐ
- div_avg3 BULL (1.6-1.9) suốt Aug05-12 — không có hedge event
- taker ~49% (không có decay) — không phân phối
- gLSR tăng + ret dương Aug12 = LONGS THẮNG (không phải knife_crowd)

### P-5: RŨ-ĐÀN GAUGE
- gLSR rising 0.97→1.33 (BULL, RISING)
- KHÁC GUA: APR div BULL + gLSR BULL = aligned (smart money long, không phải crowd-trap)
- CƠCHẾ AUG12: SHORT SQUEEZE (OI+6.5% vs vol 345×) — không phải OI-build
- OI Aug13 intraday: $50.5M (5.2× vs Aug12) = FOMO fresh longs vào đỉnh

### P-6: SANITY
- 5/5 PASS (row count, date continuity, no neg close, Aug12 pump verified, taker range)

### PENDING
- P-2 on-chain: CẦN OPERATOR (Nansen LOCKED)
- vol_spot_usd Aug10-12: CẦN retrospective DEX data (GeckoTerminal BSC pool)
- Verdict: tầng HUMAN — operator đọc `_refresh_apr_20260811.md`

**ÁN APR OPEN — DỪNG CHỜ ĐỌC.**
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"Appended APR session to {log_path.name}")
print(f"Entry length: {len(entry)} chars")

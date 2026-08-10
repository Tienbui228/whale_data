"""
_task_gua_log_20260810.py
Append GUA pipeline session to agent_log.md.
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

## G-0→G-8 GUAUSDT (SUPERFORTUNE / ALPHA_483) — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Câu hỏi case:** Có lực gom không (khuôn GOM-A/B/C)? HAY thuộc loài captive staged-pump (khuôn ON/BTW) — nếu vậy đang stage nào? Cụm ví có dấu vết trùng ON/BTW/AGT không?

**Pipeline runs:**
- G-0: identity — ALPHA_483 SUPERFORTUNE, BSC contract 0xa5c8e151..., onboard 2025-12-21 10:15 UTC
- G-1: LSR 0/4 (404), OI $3.77M→$5.19M NOT UNCALIB, FW 64 rows Jun1→Aug7
- G-2: 231 klines Dec22→Aug9, ATH $1.701 (May25), MEGA DUMP May27 -72.6% $474M
- G-2b: build_case.py exit=0, CASE_GUA.xlsx 231 rows × 50 cols
- G-3: triage + hai lăng kính
  - div_avg3=0.4141 BEAR, gLSR=2.8745 VERY BULL → crowd-trap structure
  - f_avg_3=0.000450 NOT_PIN, d_pos_28d=-0.052 FALLING
  - GOM-A=0/GOM-B=0 COLD; GOM-C 64 total, 0 post-Aug1
  - VWAP M2=$0.282 → px -86.7%; ATH -97.7%
  - GOM-D draft D1+D3+D4+D5 PASS
  - Stage: S3/S4 border, crowd-trap tại nền thứ 2
- G-4: BscScan v1 deprecated → CẦN OPERATOR (top holders, wallet crossref)
- G-5 snap1: 13:49 UTC, mid=$0.0600, ratio=1.2511 BID-HEAVY (pump in-progress)
- G-6: FW 64 rows, alpha store 250 rows, NOT in gom_state (current)
- G-7: 5/5 PASS
- G-8: CASE_INDEX row 23 registered

**TODAY Aug10 real-time:** +54.92%, 17.96×med14, funding 0.001101 EXTREME HOT

**CẦN OPERATOR:**
- Top 50 holders BscScan export CSV
- Fresh wallet check top 20
- Wallet crossref GUA vs ON/BTW/AGT (Nansen LOCKED)

**PENDING:**
- Snap2 ≥15:50 UTC: `python _probe_gua_snap2_20260810.py`
- Verdict: operator đọc `_collect_gua_20260810.md`
- Aug10 candle vào DAILY sau 00:00 UTC Aug11

**DỪNG chờ đọc.** Án OPEN.
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"Appended GUA session to {log_path.name}")
print(f"Entry length: {len(entry)} chars")

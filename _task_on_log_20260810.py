"""_task_on_log_20260810.py — append ON pipeline summary to agent_log.md."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
NOW = datetime.now(timezone.utc)

entry = """

---

## 2026-08-10 09:05 UTC — ON Pipeline N-0→N-8

**Script batch:** _probe_on_0→1→2_collect, _task_on_2b_fix, _probe_on_3→6, _task_on_7_sanity
**Output:** _collect_on_20260810.md (DỪNG chờ đọc)

### ON (ONUSDT) pipeline summary

| Bước | Script | Kết quả |
|------|--------|---------|
| N-0 | _probe_on_0_identity | ONUSDT lock, ALPHA_444, onboard 2025-10-24, 39 FW rows |
| N-1 | _probe_on_1_lsr | 4/4 LSR 404, OI 30 rows $1.68M→$24.8M UNCALIBRATED |
| N-2 | _probe_on_2_collect | 290 klines Oct25→Aug10, 1740 funding |
| N-2b | _task_on_2_build + fix | exit=0, 289 DAILY rows ×50 cols, 0 GOM-A |
| N-3 | _probe_on_3_analytics | div_avg3=1.41 BULL, gLSR=0.85 BEAR, stage S3 |
| N-4 | _probe_on_4_onchain | contract=0x0e4f62..., Nansen LOCKED → CẦN OPERATOR |
| N-5 | _probe_on_5_depth | snap1 09:02UTC mid=0.4020 ratio=0.7739 ASK-HEAVY |
| N-6 | _probe_on_6_crossref | 39 FW rows, KHÔNG có án lịch sử |
| N-7 | _task_on_7_sanity | 5/5 PASS |
| N-8 | _task_on_7_sanity | CASE_INDEX row 22, INDEX.md updated |

**Triage bộ ba:**
- div_avg3 = 1.4118 BULL (>1, top longs dominant)
- gLSR = 0.8512 BEAR (slope_5d -0.052↓)
- f_avg_3 = 0.000385 NOT_PIN
- d_pos_28d = -0.2177 FALLING

**Stage:** S3 xả-vùng-nhớ (ĐANG DIỄN RA — px -20.5% từ ATH $0.46)
**GOM-C post-Aug1:** 3 ngày (Aug 3,4,8) | hiện tại C2 FAIL (f=0.000306 > 2e-4)
**Depth snap1:** 09:02 UTC, ratio=0.7739 ASK-HEAVY, +12.22% 24h
**Snap2 gate:** ≥13:02 UTC

**CẦN OPERATOR:**
- BscScan v2: top holders ON (BSC contract confirmed 0x0e4f6209...)
- Nansen: exchange balance trend 30d
- C1 gate 2026-08-15: GOM-C active filter
"""

log_path = ROOT / "agent_log.md"
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log.md updated (+{len(entry.splitlines())} lines)")

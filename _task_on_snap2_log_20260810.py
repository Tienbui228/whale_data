"""_task_on_snap2_log_20260810.py — append ON snap2 result to agent_log.md."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")

entry = """
---

## 2026-08-10 13:05 UTC — ON Depth Snap2

**Script:** _probe_on_snap2_20260810.py

| Metric | Snap1 (09:02) | Snap2 (13:05) | Delta |
|--------|---------------|---------------|-------|
| mid | $0.401975 | $0.398605 | -0.84% |
| bid2_usd (±2%) | $2,707 | $1,090 | -59.7% |
| ask2_usd (±2%) | $3,497 | $1,774 | -49.2% |
| ratio_2pct | 0.7739 ASK-HEAVY | 0.6146 ASK-HEAVY | -0.159 |

**Trend:** ASK strengthening — ratio tiếp tục giảm (0.77→0.61). Cả hai bên wall rút mạnh (thị trường mỏng hơn).
**Live (13:05 UTC):** last=$0.3987 24h_pct=-3.11% vol=$49.5M
**Kết luận:** ON duy trì ASK-HEAVY, depth rút. Consistent với S3 xả-vùng-nhớ — không có lực mua bảo vệ rõ ràng ở $0.39-$0.40.
"""

log_path = ROOT / "agent_log.md"
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log.md appended ({len(entry.splitlines())} lines)")

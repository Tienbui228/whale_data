"""_task_btw_snap2_log_20260810.py — append BTW snap2 result to agent_log.md."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")

entry = """
---

## 2026-08-10 12:57 UTC — BTW Depth Snap2

**Script:** _probe_btw_snap2_20260810.py

| Metric | Snap1 (08:01) | Snap2 (12:57) | Delta |
|--------|---------------|---------------|-------|
| mid | $0.198785 | $0.177570 | -10.67% |
| bid2_usd (±2%) | $47,746 | $29,837 | -37.5% |
| ask2_usd (±2%) | $38,218 | $41,490 | +8.6% |
| ratio_2pct | 1.249 BID-HEAVY | 0.719 ASK-HEAVY | -0.530 |

**Trend:** BID weakening significantly — ratio sụp từ 1.25 xuống 0.72, bias đổi chiều BID→ASK.
**Live (12:57 UTC):** last=$0.1764 24h_pct=-5.26% vol=$67.6M
**Kết luận:** Áp lực bán tăng mạnh trong ~5h. BLOWOFF 2.0 phase — consistent với S3 xả.
"""

log_path = ROOT / "agent_log.md"
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log.md appended ({len(entry.splitlines())} lines)")

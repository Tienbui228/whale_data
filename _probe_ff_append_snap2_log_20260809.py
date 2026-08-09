"""Append FF snap #2 note to agent_log.md SESSION FF section"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")
log_path = ROOT / "agent_log.md"

entry = """
---

## SESSION FF addendum — depth snap #2 (2026-08-09 02:00 UTC)

FF snap #2 collected 2026-08-09 02:00:19 UTC (+13h53m vs snap #1, gate ≥16:07 UTC 08-08 ✓).

| Metric | Snap #1 (12:07 UTC 08-08) | Snap #2 (02:00 UTC 08-09) | Delta |
|--------|--------------------------|--------------------------|-------|
| mid | $0.064325 | $0.064555 | +0.36% |
| bid ±2% | $81,907 | $77,539 | -5.3% |
| ask ±2% | $59,410 | $51,150 | -13.9% |
| ratio ±2% | 1.3787 | 1.5161 | +0.14 (bid↑) |
| full book ratio | — | 1.0949 | — |

Đọc: Bid-heavy maintained và ratio tăng nhẹ. Price stable +0.36%. Spread tight 0.015%.
_collect_ff_20260808.md updated, F-5 snap #2 DONE, M-1 DONE.
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)

with open(log_path, encoding="utf-8", errors="replace") as f:
    total = sum(1 for _ in f)
print(f"Appended FF snap2 note. Total lines: {total}")

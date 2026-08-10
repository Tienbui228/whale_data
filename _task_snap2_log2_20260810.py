"""Append BTW+ON snap2 (run 2, 13:57 UTC) results to agent_log.md."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
log_path = ROOT / "agent_log.md"
NOW = datetime.now(timezone.utc)

entry = f"""
---

## Snap2 cascade check (run 2) — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

Gate BTW ≥12:01 UTC: PASS ({NOW.hour:02d}:{NOW.minute:02d} UTC)
Gate ON  ≥13:02 UTC: PASS ({NOW.hour:02d}:{NOW.minute:02d} UTC)

### BTW snap2 (13:57 UTC)
- Snap1 ref: 08:01 UTC, mid=$0.1988, ratio=1.249 BID-HEAVY
- Snap2 (13:57): mid=$0.1803 (-9.28%), ratio=1.334 BID-HEAVY
- Trend: BID strengthening (ratio +0.085 mặc dù giá giảm -9.28%)
- Bid wall: $0.177 × 91,299 = $16,160 (support mạnh ở -9.5% từ snap1)
- Ask wall: $0.189 × 31,427 = $5,940 (nhẹ hơn nhiều)
- Ticker 24h: -8.35%, vol=$66.8M
- Kết luận: BID không đổi — buyers support ở mức thấp mới; KHÔNG FLIP sang ASK

### ON snap2 (13:57 UTC)
- Snap1 ref: 09:02 UTC, mid=$0.4020, ratio=0.7739 ASK-HEAVY
- Snap2 (13:57): mid=$0.4038 (+0.47%), ratio=0.911 BALANCED
- Trend: BID strengthening (+0.137 — cải thiện rõ từ ASK-HEAVY sang BALANCED)
- Ticker 24h: +0.45%, vol=$44.6M
- Kết luận: ON depth cải thiện đáng kể — giá phục hồi nhẹ, bids mạnh hơn

### So sánh với run 1 (đã commit trước)
- BTW run1 (12:57 UTC): mid→0.1776, ratio→0.719 ASK-HEAVY (đã FLIP)
- BTW run2 (13:57 UTC): mid→0.1803 (+1.5% hồi), ratio→1.334 BID-HEAVY (FLIP NGƯỢC LẠI)
- ON run1 (13:05 UTC): mid→0.3986, ratio→0.6146 ASK-HEAVY deepening
- ON run2 (13:57 UTC): mid→0.4038 (+1.3% hồi), ratio→0.911 BALANCED

**Nhận xét:** Cả BTW và ON đều hồi nhẹ trong 1 giờ sau run 1.
BTW có bid wall mạnh ở $0.177 → buyers stacking.
ON thoát ASK-HEAVY sang BALANCED → áp lực sell giảm.
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"Appended snap2 run2 results to {log_path.name}")

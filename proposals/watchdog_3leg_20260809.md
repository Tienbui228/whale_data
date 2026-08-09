---
title: GOM Daily Watchdog — 3-Leg Spec
date: 2026-08-09
status: PROPOSAL (chưa ký)
author: agent session 24
---

# Watchdog GOM Daily — 3 Chân

## Bối cảnh: Ba kiểu chết

| Kiểu | Mô tả | Phát hiện bằng hiện tại |
|---|---|---|
| K1 | Missing dep → script exit 1 trước khi chạy | tg_error() ping ✓ |
| K2 | Script crash mid-run → exit ≠ 0 | tg_error() ping ✓ |
| **K3** | **Script chạy xong, exit 0, nhưng giao hàng thất bại (TG send fail)** | **MÙ trước 09/08** |

K3 (09/08): message 4860 > 4096 → sendMessage 400 → return False → exit 0 → không ping. Heartbeat ghi "sống". Watchdog heartbeat-only = mù với K3.

**Fix đã deploy (c7e67cd):** exit 1 khi tg_send fail. Nhưng còn hai lỗ:
- Ops ping khi fail có thể cũng fail nếu là lỗi network (không phải length).
- Cron chỉ gửi mail khi có stdout — không có external watcher.

## Chân 1 — Heartbeat (đã có)

**Hiện trạng:** `data/gom_heartbeat.txt` = `datetime.now(timezone.utc).isoformat()` ghi sau khi gom_scan exit 0.

**Vấn đề:** Heartbeat ghi TRƯỚC khi TG send → nếu TG fail, heartbeat vẫn fresh.

**Fix:** Chuyển `HB_PATH.write_text(...)` xuống SAU khi `all_ok=True`. Nếu TG fail → heartbeat KHÔNG ghi → watcher thấy stale.

```python
# run_gom_daily.py — sau block tg_send
if all_ok:
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    HB_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
```

## Chân 2 — Cross-watch (cần tạo mới)

Script cron riêng, chạy 02:30 UTC (sau 01:25 + 65 phút buffer).

```
# 02:30 UTC — cross-watch GOM daily delivery
30 2 * * * cd /root/Data_back_test/whale_data && python3 scripts/watchdog_gom.py >> data/logs/watchdog.log 2>&1
```

**`scripts/watchdog_gom.py`:**
```python
"""Cross-watch: verify GOM daily heartbeat is fresh (< 90 min old).
Fires at 02:30 UTC. If heartbeat > 90 min old → TG alert + exit 1.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys, os
# ... load .env, TG creds ...
HB = Path("data/gom_heartbeat.txt")
if not HB.exists():
    tg_alert("GOM WATCHDOG: heartbeat missing")
    sys.exit(1)
ts = datetime.fromisoformat(HB.read_text().strip())
age = datetime.now(timezone.utc) - ts
if age > timedelta(minutes=90):
    tg_alert(f"GOM WATCHDOG: stale heartbeat {age.total_seconds()/60:.0f} min old")
    sys.exit(1)
print(f"watchdog OK hb_age={age.total_seconds()/60:.1f}min")
```

Điều kiện: heartbeat stale → alert. Nếu K3 xảy ra (TG fail + heartbeat không ghi = chân 1 đã fix) → watcher thấy stale → alert.

## Chân 3 — Deliverable verify (optional, nâng cấp)

Verify bằng TG getUpdates hoặc message-id log: "report cuối có timestamp hôm nay chưa".

**Cách đơn giản:** Log message-id vào `data/logs/tg_delivered.log` sau mỗi lần send thành công.

```python
# run_gom_daily.py — trong tg_send():
resp = json.loads(r.read().decode())
if resp.get("ok"):
    msg_id = resp.get("result", {}).get("message_id")
    if msg_id:
        with open(LOG_PATH.parent / "tg_delivered.log", "a") as fh:
            fh.write(f"{datetime.now(timezone.utc).isoformat()} msg_id={msg_id} len={len(text)}\n")
    return True
```

Watchdog cross-check: đọc `tg_delivered.log` → xem message_id cuối có timestamp hôm nay không.

**Phân tích:** Chân 3 phụ thuộc TG API trả message_id (luôn trả khi ok=True). Implement sau khi chân 1+2 ổn định.

## Tóm tắt ưu tiên

| Chân | Effort | Priority | Status |
|---|---|---|---|
| C1 Heartbeat fix (ghi sau send) | 5 dòng | P0 | **CẦN OPERATOR KÝ** |
| C2 Cross-watcher script + cron | ~50 dòng | P1 | **CẦN OPERATOR KÝ** |
| C3 Deliverable log + verify | ~30 dòng | P2 | Sau C1+C2 ổn |

## Diff C1 (heartbeat timing)

```diff
-    # Heartbeat
-    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
-    HB_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
-
     # Format and send Telegram report ...
     ...
+    if not all_ok:
+        ...
+        sys.exit(1)
+
+    # Heartbeat: only write after confirmed delivery
+    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
+    HB_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
```

Cron watchdog (chân 2) cần operator sign off trước khi deploy.

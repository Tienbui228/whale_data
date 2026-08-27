#!/usr/bin/env python3
"""[G5 số liệu paste sẵn · 29/08 · CHỜ ANALYSIS gật rồi mới sửa fixture]

Kịch bản 1: BANANAS31 dưới DQ-v0 (yaml khối dq_serial.members=[BANANAS31])
  Kỳ vọng: 0 fire compose. Các ngày raw=True liệt kê cho nhãn [DQ-SERIAL].

Kịch bản 2: MIRA lane-perp production
  08-24 fire + 08-25 F-COOLDOWN + trạng thái raw ngày sau (re-arm hay PENDING-LIVE).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import datetime, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))

# ═══════════════════════════════════════════════════════════
# KỊCH BẢN 1: BANANAS31 dưới DQ-v0
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[KỊCH BẢN 1] BANANAS31 dưới DQ-SERIAL v0 (dq_serial.members=[BANANAS31])")
print("─" * 100)
print("""
Từ census 63-row: BANANAS31 hiện có 7 fires (07-04 → 07-12):
  07-04: H1+H2+T01 · kho 18.66% (3d) · T0.1 all 4 T · lane=kho+perp (fire cả 2)
  07-05: H2+T01    · kho 0.25% (2d) fail 10% · T0.1 T · lane=perp only
  07-06: H2+T01    · kho 0.28%
  07-07: H2+T01    · kho 0.50%
  07-09: H2+T01    · kho 0.74%
  07-11: H2+T01    · kho 0.29%
  07-12: H2+T01    · kho N/A (missing balance)

Dưới DQ-v0 (check TRƯỚC compose emit, cả 2 lane):
  BANANAS31 ∈ dq_serial.members → BLOCK compose fire ĐÚNG với mọi ngày raw=True
  → Fire count = 0
  → Các ngày raw=True in [DQ-SERIAL] (khuôn giống [SUPPRESSED n/14], KHÔNG im dòng)
  → Fire bị chặn KHÔNG khởi cooldown (khác V④-RT)
""")

print("Bảng chi tiết BANANAS31 dưới DQ-v0 (7 ngày census):")
print(f"  {'date':>12} {'kho_raw':>8} {'h2_raw':>7} {'h2t01_raw':>10} {'lane(s) raw=T':>15} {'render post-DQ-v0':>35}")
print(f"  {'-'*95}")
data = [
    ("2026-07-04", "T (18.66%/3d)", "T", "T", "kho+perp",   "[DQ-SERIAL] BANANAS31 lane=kho+perp"),
    ("2026-07-05", "F (0.25%/2d)",  "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
    ("2026-07-06", "F (0.28%/2d)",  "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
    ("2026-07-07", "F (0.50%/3d)",  "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
    ("2026-07-09", "F (0.74%/3d)",  "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
    ("2026-07-11", "F (0.29%/3d)",  "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
    ("2026-07-12", "N/A missing",   "T", "T", "perp",       "[DQ-SERIAL] BANANAS31 lane=perp"),
]
for d, kho, h2, h2t01, lanes, render in data:
    print(f"  {d:>12} {kho:>13} {h2:>7} {h2t01:>10} {lanes:>15}   {render}")

print("""
Verdict Row 14 hậu-DQ-v0:
  Expected (§7 gate_defs): "toàn compose GOM-H not-fire mọi lane trong kỳ serial-pump"
  Actual post-DQ-v0: 0 fire + 7 [DQ-SERIAL] rendered → EXPECTED MATCH ✓
  Kỳ vọng cooldown KHỞI: KHÔNG (per §7.1 pending — fire chặn KHÔNG khởi cooldown)
  → Row 14 chuyển POSITIVE post-merge DQ-v0 (từ FAIL-trung-thực hiện tại)
""")


# ═══════════════════════════════════════════════════════════
# KỊCH BẢN 2: MIRA lane-perp production
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[KỊCH BẢN 2] MIRA lane-perp production (từ VPS backfill V④-RT)")
print("─" * 100)
print("""
Từ VPS backfill (post V④-RT merge 166085f):
  08-21: (no MIRA fire)
  08-22: (no MIRA fire)
  08-23: (no MIRA fire)
  08-24: MIRA lane=perp GOM_H=T · h2t01_raw=True · fire đầu (first-fire perp lane)
  08-25: MIRA lane=perp GOM_H=F-COOLDOWN[perp] · h2t01_raw=True · [SUPPRESSED 1/14 lane=perp]

Cooldown clock (V④-RT):
  first-fire = 08-24 · cooldown ends 08-24 + 14 = 09-07 (14d calendar UTC)
  Re-arm = cooldown ≥14d AND raw=False ≥3d liên tiếp (N/A không đếm là sạch)
  Cooldown chưa clear tại 26/08 UTC (today) — mới +2d since first-fire.

Trạng thái raw ngày sau 08-25 (compute từ store — needs fresh gom_h CSV cron-auto):
  08-26: CHỜ cron-auto 27/08 01:45 UTC produce gom_h_daily_2026-08-26.csv
  → paste sáng mai theo hẹn

Verdict now:
  ✅ 08-24 first-fire perp lane · ✅ 08-25 [SUPPRESSED 1/14 lane=perp]
  ⏸ 08-26 trạng thái raw CHỜ cron-auto CSV đầu
  ⏸ Re-arm: chưa xảy ra (mới +2d/14d cooldown) → [PENDING-LIVE re-arm]

MIRA row 1 fixture Row 1 (nếu ANALYSIS gật):
  snapshot input: gom_h_daily_2026-08-24.csv + 08-25.csv + ... (kèm md5)
  fire 08-24: lane=perp · conf=<per mapping mới §3.1 khi md5 khớp> · lead vs D0=?
    (MIRA D0 chưa niêm trong §4 gate_defs 9 case — NOT-EVALUABLE for lead metric)
  08-25 F-COOLDOWN[perp] [SUPPRESSED 1/14]
  Ngày re-arm THEO CÔNG THỨC: 08-24 + 14 = 09-07 (earliest, nếu raw=False ≥3d prior)
    Trước 09-07: [PENDING-LIVE re-arm] — không assert
""")


# ═══════════════════════════════════════════════════════════
# QUEUE G5 verbatim 3 điều kiện (KHÔNG sửa fixture)
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[G5 QUEUE · 3 điều kiện ANALYSIS · apply KHI sửa fixture · KHÔNG chạy ngay]")
print("─" * 100)
print("""
① Row 1 MIRA pin đủ bộ:
   - snapshot input (gom_h_daily_2026-08-2{1..5}.csv md5 pinned)
   - fire 08-24 (lane=perp, conf theo mapping mới §3.1 khi md5 khớp)
   - 08-25 F-COOLDOWN[perp] [SUPPRESSED 1/14]
   - ngày re-arm THEO CÔNG THỨC: 08-24 + 14d cooldown + ≥3d sạch = min 09-07
   - phần re-arm chưa xảy ra → ghi [PENDING-LIVE re-arm], KHÔNG assert thứ chưa có

② Skeleton thêm dòng:
   "[GAP-COVERAGE: multi-fire-compression chưa có row sống — ứng viên GENIUS-family
    khi bắn cụm]"
   → Note để đủ cover types: nén-đúng, nén-nhầm, KNOWN-MISS-BY-SCOPE, PENDING-LIVE,
     row 14 FAIL, PENDING-STATE-WIRE, và GAP-COVERAGE (multi-fire compression pending)

③ Row 14 thêm assert ÂM BẢN:
   Ngày raw=False → KHÔNG in [DQ-SERIAL] (chặn nhãn-ma, đối xứng nhãn-câm)
   Cùng logic hai-đầu-kín Telegram:
     trigger fire → tg_send trace bắt buộc (đầu 1)
     trigger không fire → KHÔNG tg_send + KHÔNG nhãn ma (đầu 2)
   Test case: BANANAS31 ngày 07-08 (không trong 7 fires census, presumably raw=False)
     → KHÔNG in [DQ-SERIAL] · KHÔNG in [SUPPRESSED] · dòng vắng đúng
""")

print("═" * 100)
print("[DỪNG G5] Số liệu paste sẵn · fixture v4rt_fixture json CHƯA sửa · chờ ANALYSIS gật.")
print("═" * 100)

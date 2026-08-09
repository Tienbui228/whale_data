#!/usr/bin/env python3
"""TST Q2 seat-rotation estimate — window 30d backfill (07-10→08-09).

Q2 = OI × dải × (pos_r - 1)/(pos_r + 1) heuristic — áp dụng khi có GOM-A/B fire.
Điều kiện entry: ngày GOM-A/B fire tồn tại trong window → không có → Q2 N/A.

data-source: scratch/tst_lsr_backfill_20260809.csv (hoặc VPS parquet store)
machine: local scratch (derived from VPS canonical parquet)
date-range: 2026-07-10 → 2026-08-09
code-commit: 9338008
"""
from __future__ import annotations
import sys
import math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ── Dữ liệu TST 30d từ backfill (từ scratch CSV hoặc hardcode từ R2 verify) ───
# Source: scratch/tst_lsr_backfill_20260809.csv (SCP từ VPS)
# Nếu không có CSV, dùng subset từ R3 merge đã xác nhận.

# gLSR range: 1.54–2.37 trên toàn bộ 30d (từ R2)
# pos_r range: 1.30 (07-11) → 5.34 (08-07)
# oi_usd range: 1.63M (07-11) → 4.37M (08-09 ước)
# GOM-A fire: 0/545 (A2 hard-block toàn bộ)

SCRATCH = Path(__file__).parent / "scratch" / "tst_lsr_backfill_20260809.csv"

print("=" * 60)
print("TST Q2 Seat-Rotation Estimate — 30d Backfill Window")
print("=" * 60)
print()

# ── Bước 1: Điều kiện tiên quyết ─────────────────────────────────────────────
print("Bước 1: Kiểm tra điều kiện entry Q2")
print("  Q2 seat-rotation yêu cầu: ít nhất 1 ngày GOM-A/B fire trong window")
print("  TST GOM-A fire: 0/545 (R3 verified)")
print("  TST GOM-B fire: 0/545 (R3 verified)")
print("  --> Không có ngày GOM-A/B fire")
print()
print("  Kết luận: Q2 = N/A (không applicable)")
print("  Lý do N/A: A2 hard-block (avg5 gLSR 1.54→2.37 >> 1.1) loại toàn bộ window.")
print("  Không có seat-rotation eligible ngày nào để ước.")
print()

# ── Bước 2: Informational — nếu giả định có fire (hypothetical) ──────────────
print("Bước 2: Hypothetical Q2 nếu có fire (upper-bound tham khảo)")
print("  [KHÔNG phải số chốt — chỉ để bound tham chiếu khi TST điều kiện thay đổi]")
print()

# Dữ liệu key ngày mạnh nhất (08-07 — pos_r peak)
oi_peak    = 4.37e6    # oi_usd 08-07 (xấp xỉ)
pos_r_peak = 5.34      # top positions L/S ratio peak
# Dải = tỷ lệ OI change qua fire window (không có window → dùng 30d full = 1.0→4.37M)
# (pos_r - 1) / (pos_r + 1) = long bias fraction
long_bias  = (pos_r_peak - 1.0) / (pos_r_peak + 1.0)

q2_upper = oi_peak * long_bias
print(f"  oi_peak(08-07) = ${oi_peak/1e6:.2f}M")
print(f"  pos_r_peak     = {pos_r_peak:.2f}")
print(f"  long_bias      = (5.34-1)/(5.34+1) = {long_bias:.3f}")
print(f"  Q2_hyp_upper   = ${q2_upper/1e3:.0f}k (dải=1.0, ngay trước cooldown)")
print()
print("  Với pos_r thấp hơn (07-11 pos_r=1.30):")
pos_r_low  = 1.30
lb_low     = (pos_r_low - 1.0) / (pos_r_low + 1.0)
q2_lower   = 1.63e6 * lb_low
print(f"  oi(07-11)={1.63:.2f}M, pos_r={pos_r_low}, lb={lb_low:.3f}")
print(f"  Q2_hyp_lower = ${q2_lower/1e3:.0f}k")
print()

# ── Tóm tắt ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("TÓM TẮT TST Q2 ANALYSIS")
print("=" * 60)
print()
print("  Q2 seat-rotation: N/A")
print("  Lý do: GOM-A/B fire = 0 ngày trong cả lịch sử 545 ngày")
print("         (A2 structural block: avg5 gLSR >> 1.1 toàn bộ)")
print()
print("  Nếu điều kiện A2 thay đổi tương lai (gLSR avg5 <= 1.1):")
print(f"    Q2 est range: ${q2_lower/1e3:.0f}k–${q2_upper/1e3:.0f}k")
print("    (dùng pos_r tại ngày fire thực tế × oi_usd ngày đó)")
print()
print("  TST chỉ track được trong GOM-C (campaign), không seat-rotation.")
print("  GOM-C Q1 = $0 (OI declining on fire day 08-04, per baseline v9).")
print()

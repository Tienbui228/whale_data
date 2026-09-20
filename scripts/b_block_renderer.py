# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""B Block Renderer · M1-M8/19-09 · L1 gate · relapse BỎ · FAILED nén 3 tên mới nhất.

Tier hiển thị:
  · T1 CONFIRMED: [B] TOKEN +kd
  · T2 CROSS:     [B-cand] TOKEN · L1 · D+k (đang hedge sau cross)
  · T3 cand:      TOKEN dd/mm · ... (trần 10 · (+N))
  · T3 FAILED:    FAILED: N (TOK dd/mm · TOK dd/mm · TOK dd/mm)  ← nén 3 mới nhất (M8)
  · STALE:        TOKEN

Header: `── B ── (n_total · X CONFIRMED · Y CROSS · Z cand · W FAILED · V STALE) [CAL-ONLY]`

M2: relapse BỎ · KHÔNG in relapse tier.
M4: mọi `(→ xem X)` reference phải có dòng đích trong khối X (lint p91).
M5: prefix `[B]` chỉ khi CONFIRMED · đang hedge sau cross → `[B-cand]`.
M8: FAILED nén 1 dòng đếm + 3 tên mới nhất theo D_cross · danh sách đủ ở audit.

HOLD-OUT 20/09→20/10: Tiên ĐỌC được nhưng CẤM chỉnh ngưỡng theo cái đọc được
trước 21/10. Grid 8 ô đã khoá.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
from datetime import datetime

_SCRIPTS = Path(__file__).parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from b_state_tracker import build_b_state


def _fmt_dm(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return f"{d.day:02d}/{d.month:02d}"


def render_b_block(target: str, universe=None, by_sym=None, cand_cap: int = 10) -> str:
    """Trả string khối B cho target · M1-M8/19-09."""
    state = build_b_state(target, universe=universe, by_sym=by_sym)

    conf = [(t, s) for t, s in state.items() if s["tier"] == "CONFIRMED"]
    cross = [(t, s) for t, s in state.items() if s["tier"] == "CROSS"]
    cand = [(t, s) for t, s in state.items() if s["tier"] == "cand"]
    failed = [(t, s) for t, s in state.items() if s["tier"] == "FAILED"]
    stale = [(t, s) for t, s in state.items() if s["tier"] == "STALE"]

    n_conf = len(conf); n_cross = len(cross); n_cand = len(cand)
    n_fail = len(failed); n_stale = len(stale)
    n_total = n_conf + n_cross + n_cand + n_fail + n_stale

    if n_total == 0:
        return "── B ── (0) [CAL-ONLY] · hôm nay không có token loài B"

    header = (f"── B ── ({n_total} · {n_conf} CONFIRMED · {n_cross} CROSS · "
              f"{n_cand} cand · {n_fail} FAILED · {n_stale} STALE) [CAL-ONLY]")
    lines = [header]

    # M5 · [B] CHỈ khi CONFIRMED
    for tok, s in conf:
        lines.append(f"[B] {tok} +{s['d_plus_k']}d")
    # M5 · [B-cand] khi CROSS (đang hedge sau cross · L1 tại D_cross)
    for tok, s in cross:
        lines.append(f"[B-cand] {tok} · L1 · D+{s['d_plus_k']}")

    if n_cand > 0:
        lines.append("── ứng viên ──")
        cap = cand[:cand_cap]
        overflow = max(0, n_cand - cand_cap)
        td_date = datetime.strptime(target, "%Y-%m-%d").date()
        dd_mm = f"{td_date.day:02d}/{td_date.month:02d}"
        parts = [f"{t} {dd_mm}" for t, _ in cap]
        suffix = f" (+{overflow})" if overflow > 0 else ""
        lines.append("   " + " · ".join(parts) + suffix)

    # M8 · FAILED nén 1 dòng · đếm + 3 tên mới nhất (D_cross recent-first)
    if n_fail > 0:
        failed_sorted = sorted(failed, key=lambda x: x[1]["d_cross"], reverse=True)
        top3 = failed_sorted[:3]
        parts = [f"{tok} {_fmt_dm(s['d_cross'])}" for tok, s in top3]
        lines.append(f"── FAILED: {n_fail} ({' · '.join(parts)})")

    if n_stale > 0:
        lines.append("── STALE ──")
        lines.append("   " + " · ".join(t for t, _ in stale))

    return "\n".join(lines)


def lint_b_references(body: str) -> list:
    """M4 · lint tham chiếu: mọi `(→ xem X)` phải có dòng đích chứa `[X]` hoặc `X:`.

    Trả list các reference thiếu đích. Empty list = PASS.
    """
    import re
    refs = re.findall(r"\(→\s*xem\s+([A-Za-z0-9\-_]+)\)", body)
    orphans = []
    for ref in refs:
        # Đích: dòng chứa `[ref]` hoặc `ref:` hoặc `── ref ──`
        found = (re.search(rf"\[{re.escape(ref)}\]", body) or
                 re.search(rf"^{re.escape(ref)}:", body, re.MULTILINE) or
                 re.search(rf"──\s*{re.escape(ref)}\s*──", body))
        if not found:
            orphans.append(ref)
    return orphans

# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""B Block Renderer · AE1-AE5 · dựng khối B ba tầng cho thân bản tin.

Tier hiển thị:
  · T1 CONFIRMED: [B-CONFIRMED · +kd] TOKEN
  · T2 CROSS:     [B-CROSS · L1 · D+k] TOKEN
  · T3 cand:      TOKEN dd/mm · ... (trần 10 · (+N))
  · T3 FAILED:    TOKEN dd/mm · ... (D_cross ≤14d gần)
  · STALE:        TOKEN
  · RELAPSE:      [relapse] TOKEN dd/mm · v_run FAIL   ← AE5-1

Header: `── B ── (n_total · X CONFIRMED · Y CROSS · Z cand · W FAILED · V STALE · U relapse) [CAL-ONLY]`

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
    """Trả string khối B ba tầng cho target."""
    state = build_b_state(target, universe=universe, by_sym=by_sym)

    conf = [(t, s) for t, s in state.items() if s["tier"] == "CONFIRMED"]
    cross = [(t, s) for t, s in state.items() if s["tier"] == "CROSS"]
    cand = [(t, s) for t, s in state.items() if s["tier"] == "cand"]
    failed = [(t, s) for t, s in state.items() if s["tier"] == "FAILED"]
    stale = [(t, s) for t, s in state.items() if s["tier"] == "STALE"]
    relapse = [(t, s) for t, s in state.items() if s["tier"] == "RELAPSE"]

    n_conf = len(conf); n_cross = len(cross); n_cand = len(cand)
    n_fail = len(failed); n_stale = len(stale); n_rel = len(relapse)
    n_total = n_conf + n_cross + n_cand + n_fail + n_stale + n_rel

    if n_total == 0:
        return "── B ── (0) [CAL-ONLY] · hôm nay không có token loài B"

    header = f"── B ── ({n_total} · {n_conf} CONFIRMED · {n_cross} CROSS · {n_cand} cand · {n_fail} FAILED · {n_stale} STALE · {n_rel} relapse) [CAL-ONLY]"
    lines = [header]

    for tok, s in conf:
        lines.append(f"[B-CONFIRMED · +{s['d_plus_k']}d] {tok}")
    for tok, s in cross:
        lines.append(f"[B-CROSS · L1 · D+{s['d_plus_k']}] {tok}")

    if n_cand > 0:
        lines.append("── ứng viên ──")
        cap = cand[:cand_cap]
        overflow = max(0, n_cand - cand_cap)
        td_date = datetime.strptime(target, "%Y-%m-%d").date()
        dd_mm = f"{td_date.day:02d}/{td_date.month:02d}"
        parts = [f"{t} {dd_mm}" for t, _ in cap]
        suffix = f" (+{overflow})" if overflow > 0 else ""
        lines.append("   " + " · ".join(parts) + suffix)

    if n_fail > 0:
        lines.append("── FAILED ──")
        parts = []
        for tok, s in failed:
            parts.append(f"{tok} {_fmt_dm(s['d_cross'])}")
        lines.append("   " + " · ".join(parts))

    if n_stale > 0:
        lines.append("── STALE ──")
        lines.append("   " + " · ".join(t for t, _ in stale))

    # AE5-1 · relapse in ở cuối · một dòng per ca
    for tok, s in relapse:
        lines.append(f"[relapse] {tok} {s['dd_mm']} · {s['fail_reason']}")

    return "\n".join(lines)

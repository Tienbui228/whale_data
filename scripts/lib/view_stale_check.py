"""L-74 · consumer-side VIEW-STALE checker · L/19-09 · md5-based (BỎ age gate)

Doctrine (L/19-09 · niêm): "một view đúng thì mười ngày tuổi vẫn đúng".
So MD5, KHÔNG so tuổi. Nguồn không đổi thì view không cũ.

Enforcement:
  · Load VIEW file (case_state_map.md) · parse header source_md5
  · Load sidecar md5 file (case_index_source.md5) — ghi bởi local gen script, SCP kèm map
  · Khớp → IM (dù age bao nhiêu)
  · Lệch → [VIEW-STALE · nguồn đã đổi, map chưa regen]
  · Sidecar thiếu → [VIEW-STALE · không kiểm được nguồn] (fail-closed L-174)

Usage (import trong consumer):
    from lib.view_stale_check import check_view_stale
    stale_note = check_view_stale(
        view_path=REPO / "docs/case_files/case_state_map.md",
        source_md5_path=REPO / "data/state/case_index_source.md5",
    )
    if stale_note:
        print(stale_note)  # gate cảnh báo
"""
from __future__ import annotations
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "(missing)"


def check_view_stale(view_path: Path, source_md5_path: Path = None,
                     source_path: Path = None, max_age_hours: int = 24) -> str:
    """Check VIEW freshness bằng md5, KHÔNG bằng age.

    Args:
        view_path: file view (case_state_map.md)
        source_md5_path: sidecar 32-byte md5 file (case_index_source.md5)
            · VPS: SCP kèm map · md5-based check
            · Bỏ qua nếu source_path được truyền (local side dùng xlsx trực tiếp)
        source_path: canonical source xlsx (LOCAL only) · check md5 khớp trực tiếp
        max_age_hours: DEPRECATED — chỉ dùng cho fallback thông tin, KHÔNG làm gate

    Returns:
        "" nếu view fresh (md5 khớp)
        "[VIEW-STALE ...]" nếu stale (md5 lệch, hoặc không kiểm được)

    Doctrine: age là mô tả, không phải cổng. Nguồn không đổi → view không cũ.
    """
    if not view_path.exists():
        return f"[VIEW-STALE view-missing path={view_path.name}]"

    view_text = view_path.read_text(encoding="utf-8")
    m_md5 = re.search(r"<!--\s*source_md5:\s*([0-9a-f]+)\s*-->", view_text)
    m_gen = re.search(r"<!--\s*generated_at:\s*([0-9T:.+\-Z]+)\s*-->", view_text)

    if not m_md5:
        return f"[VIEW-STALE view-no-header path={view_path.name} · missing L-74 source_md5]"

    view_source_md5 = m_md5.group(1)

    # Tuổi in ra làm mô tả (không cổng)
    age_desc = ""
    if m_gen:
        try:
            gen_dt = datetime.fromisoformat(m_gen.group(1))
            age_hours = (datetime.now(timezone.utc) - gen_dt).total_seconds() / 3600
            age_desc = f" (age={age_hours/24:.1f}d)"
        except Exception:
            pass

    # LOCAL path · source_path xlsx có sẵn → so md5 trực tiếp
    if source_path is not None and source_path.exists():
        current_source_md5 = _md5(source_path)
        if view_source_md5 != current_source_md5:
            return (f"[VIEW-STALE · nguồn đã đổi, map chưa regen · "
                    f"view={view_source_md5[:8]} current={current_source_md5[:8]}]{age_desc}")
        return ""  # khớp → im

    # VPS path · dùng sidecar md5 file
    if source_md5_path is None:
        # Không có cách kiểm nguồn → fail-closed
        return f"[VIEW-STALE · không kiểm được nguồn · source_md5_path=None]{age_desc}"

    if not source_md5_path.exists():
        return (f"[VIEW-STALE · không kiểm được nguồn · "
                f"sidecar thiếu: {source_md5_path.name}]{age_desc}")

    try:
        current_source_md5 = source_md5_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        return f"[VIEW-STALE · không kiểm được nguồn · sidecar read fail: {e}]{age_desc}"

    # Basic format check · 32-hex
    if not re.fullmatch(r"[0-9a-f]{32}", current_source_md5):
        return (f"[VIEW-STALE · không kiểm được nguồn · "
                f"sidecar format sai: {current_source_md5[:16]}…]{age_desc}")

    if view_source_md5 != current_source_md5:
        return (f"[VIEW-STALE · nguồn đã đổi, map chưa regen · "
                f"view={view_source_md5[:8]} sidecar={current_source_md5[:8]}]{age_desc}")

    return ""  # md5 khớp → view fresh dù age bao nhiêu


if __name__ == "__main__":
    # Self-test
    import sys
    REPO = Path(r"D:\Data back test\whale_data") if sys.platform == "win32" else Path("/root/Data_back_test/whale_data")
    # LOCAL side · dùng xlsx trực tiếp
    result = check_view_stale(
        view_path=REPO / "docs/case_files/case_state_map.md",
        source_path=REPO / "docs/case_files/CASE_INDEX.xlsx",
    )
    if result:
        print(result)
        sys.exit(1)
    else:
        print("[VIEW-FRESH] case_state_map md5 khớp CASE_INDEX.xlsx (age không quan tâm)")
        sys.exit(0)

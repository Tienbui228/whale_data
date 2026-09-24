"""G2 · Pin library · dùng chung cho R/T pin doctrine.

Sửa lỗi cũ trong `_probe_r1_pin_20260923.py:25` viết cứng `2026-09-23T{HH:MM:SSZ}` —
thay bằng `datetime.now(timezone.utc)` cho FULL ISO 8601 UTC.

Usage:
    from _probe_pin_lib_20260924 import pin_self_ref, now_utc_iso
    md5_body, md5_full = pin_self_ref(path, placeholder="**md5 R? pinned:** `<sẽ điền>`",
                                       pin_prefix="**md5 R? pinned:** ")
"""
import hashlib
import pathlib
from datetime import datetime, timezone


def now_utc_iso() -> str:
    """Trả ISO 8601 UTC current time · KHÔNG hardcoded date."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pin_self_ref(path: pathlib.Path,
                 placeholder: str,
                 pin_prefix: str) -> tuple[str, str]:
    """Self-referential md5 pin cho file docs (R1, R1a, tương tự).

    Args:
        path: file path (Path)
        placeholder: chuỗi placeholder trong file (VD "**md5 R1a pinned:** `<sẽ điền sau probe>`")
        pin_prefix: prefix cho pin line (VD "**md5 R1a pinned:** ")

    Steps:
        1. Đọc file text
        2. Strip placeholder → body
        3. md5(body) = body_md5 (self-referential · pin không tự chứa mình)
        4. Append pin line với NOW UTC (full ISO date-time · KHÔNG hardcode)
        5. Ghi file · trả (body_md5, full_file_md5)
    """
    text = path.read_text(encoding="utf-8")
    if placeholder not in text:
        raise ValueError(f"placeholder không tìm thấy trong {path}: {placeholder!r}")

    body = text.replace(placeholder + "\n", "").replace(placeholder, "")
    body = body.rstrip() + "\n"
    body_md5 = hashlib.md5(body.encode("utf-8")).hexdigest()

    now = now_utc_iso()
    pin_line = f"\n{pin_prefix}`{body_md5}` · pinned_at={now} · file này KHÔNG SỬA sau đây\n"
    final = body + pin_line
    path.write_text(final, encoding="utf-8")

    full_md5 = hashlib.md5(final.encode("utf-8")).hexdigest()
    return body_md5, full_md5


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"pin_lib · now_utc_iso() = {now_utc_iso()}")
    print("Import as module: from _probe_pin_lib_20260924 import pin_self_ref, now_utc_iso")

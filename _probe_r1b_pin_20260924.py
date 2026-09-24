"""B1 · Pin R1b registration dùng lib G2 (now_utc_iso không hardcode)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

# Import G2 lib
sys.path.insert(0, ".")
from _probe_pin_lib_20260924 import pin_self_ref, now_utc_iso

REG = Path("docs/holdout_u0bell_r1b_registration_20260924.md")
body_md5, full_md5 = pin_self_ref(
    REG,
    placeholder="**md5 R1b pinned:** `<sẽ điền qua _probe_pin_lib_20260924.py>`",
    pin_prefix="**md5 R1b pinned:** ",
)
print(f"body-only md5: {body_md5}")
print(f"full-file md5: {full_md5}")
print(f"pinned_at (from G2 now_utc_iso): {now_utc_iso()}")
print(f"path: {REG}")

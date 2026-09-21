"""tg_len.py · AH4/22-09 · Unified length measurement for Telegram.

Telegram API đo len bằng **UTF-16 code unit** (không phải Python `len(str)` count code
points, không phải byte count). Emoji ngoài BMP (U+10000+, ví dụ 🎯, 🅱, 龙虾) tốn 2
code units (surrogate pair). Cần đếm đúng để tránh:
  - Body 4096 code points có thể = 4200+ UTF-16 units → Telegram reject 400
  - Body 3000 bytes UTF-8 có thể chỉ ~1500 chars khi tiếng Việt
  - Prefix HTML tags <b>...</b> chiếm len HTTP nhưng KHÔNG tính vào len sender

Rule (AH4/22-09):
  · Đo len sau BỎ THẺ HTML whitelist (b/i/u/s/a/code/pre/tg-spoiler/blockquote)
  · Đếm UTF-16 code unit qua encode("utf-16-le") / 2
  · Cap Telegram = 4096 UTF-16 code units.

Usage:
  from lib.tg_len import tg_len
  if tg_len(msg) > 4096: ...

Test cases:
  tg_len("hello")              == 5
  tg_len("hello <b>world</b>") == 11   # bỏ <b>...</b>
  tg_len("🎯")                  == 2    # emoji ngoài BMP = surrogate pair
  tg_len("龙虾")                == 2    # 2 code points BMP
"""
from __future__ import annotations
import re

_HTML_TAG_RE = re.compile(
    r"</?(?:b|i|u|s|a|code|pre|tg-spoiler|blockquote)(?:\s[^<>]*)?/?>",
    re.IGNORECASE,
)


def strip_html_whitelist(text: str) -> str:
    """Loại các thẻ HTML whitelist Telegram · giữ nội dung text."""
    return _HTML_TAG_RE.sub("", text)


def tg_len(text: str) -> int:
    """Trả len UTF-16 code unit sau khi bỏ HTML whitelist tags.

    Telegram API 4096-char limit = 4096 UTF-16 code units.
    """
    cleaned = strip_html_whitelist(text)
    # UTF-16 LE: 2 bytes per code unit · không BOM
    return len(cleaned.encode("utf-16-le")) // 2


if __name__ == "__main__":
    # Self-test
    import sys as _sys
    try: _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except: pass  # L-66-OK (stdout reconfigure benign)
    cases = [
        ("hello", 5),
        ("hello <b>world</b>", 11),   # 5 + 1(space) + 5 = 11
        ("🎯", 2),                    # BMP surrogate pair
        ("龙虾", 2),                  # 2 BMP code units
        ("A<code>x</code>B", 3),      # A + x + B = 3
        ("", 0),
    ]
    for txt, expected in cases:
        got = tg_len(txt)
        ok = "PASS" if got == expected else "FAIL"
        print(f"  tg_len({txt!r}) = {got} (expected {expected}) · {ok}")

"""_task_handover_fix_20260817.py
Fix mojibake: try latin-1 encode first (recovers 0x80-0x9F range), fall back to cp1252.
Write to docs/handover/analysis_handover_20260817.md.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
HANDOVER = ROOT / "docs" / "handover"

src = SCRATCH / "temp_handover_raw_20260817.txt"
dst = HANDOVER / "analysis_handover_20260817.md"

with open(src, encoding="utf-8", errors="replace") as f:
    raw = f.read()

# Strategy: garbling used latin-1 reading of UTF-8 bytes.
# Control chars U+0080-U+009F (latin-1) are preserved in the Python string.
# latin-1 encode maps U+0000-U+00FF directly 1:1 to bytes.
# Then decode bytes as UTF-8 recovers the original Vietnamese.
# Note: any cp1252-specific chars (€=U+20AC, '=U+2018, etc.) that
# survived as printable will NOT encode to latin-1 → we try cp1252 per-char.

def fix_encoding(raw_str):
    # Try to encode each char to build the byte stream
    result_bytes = bytearray()
    i = 0
    chars = list(raw_str)
    while i < len(chars):
        c = chars[i]
        cp = ord(c)
        if cp <= 0xFF:
            # latin-1 range: direct byte
            result_bytes.append(cp)
        elif cp == 0x20AC:
            result_bytes.append(0x80)  # € in cp1252
        elif cp == 0x201A:
            result_bytes.append(0x82)
        elif cp == 0x0192:
            result_bytes.append(0x83)
        elif cp == 0x201E:
            result_bytes.append(0x84)
        elif cp == 0x2026:
            result_bytes.append(0x85)
        elif cp == 0x2020:
            result_bytes.append(0x86)
        elif cp == 0x2021:
            result_bytes.append(0x87)
        elif cp == 0x02C6:
            result_bytes.append(0x88)
        elif cp == 0x2030:
            result_bytes.append(0x89)
        elif cp == 0x0160:
            result_bytes.append(0x8A)
        elif cp == 0x2039:
            result_bytes.append(0x8B)
        elif cp == 0x0152:
            result_bytes.append(0x8C)
        elif cp == 0x017D:
            result_bytes.append(0x8E)
        elif cp == 0x2018:
            result_bytes.append(0x91)  # ' in cp1252
        elif cp == 0x2019:
            result_bytes.append(0x92)  # '
        elif cp == 0x201C:
            result_bytes.append(0x93)  # "
        elif cp == 0x201D:
            result_bytes.append(0x94)  # "
        elif cp == 0x2022:
            result_bytes.append(0x95)
        elif cp == 0x2013:
            result_bytes.append(0x96)  # –
        elif cp == 0x2014:
            result_bytes.append(0x97)  # —
        elif cp == 0x02DC:
            result_bytes.append(0x98)
        elif cp == 0x2122:
            result_bytes.append(0x99)
        elif cp == 0x0161:
            result_bytes.append(0x9A)
        elif cp == 0x203A:
            result_bytes.append(0x9B)
        elif cp == 0x0153:
            result_bytes.append(0x9C)
        elif cp == 0x017E:
            result_bytes.append(0x9E)
        elif cp == 0x0178:
            result_bytes.append(0x9F)
        else:
            # Unknown high codepoint — skip (lost in garbling)
            result_bytes.append(0x3F)  # '?'
        i += 1
    return result_bytes.decode("utf-8", errors="replace")

fixed = fix_encoding(raw)

print("Preview (first 6 lines of fixed):")
for ln in fixed.splitlines()[:6]:
    print(" ", ln)

# Count replacement chars
n_replace = fixed.count('�') + fixed.count('?')
print(f"\nTotal chars: {len(fixed)}, replacement markers: {n_replace}")

with open(dst, "w", encoding="utf-8") as f:
    f.write(fixed)

print(f"\nWritten: {dst}")
print("[DONE]")

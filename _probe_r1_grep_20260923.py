"""R1 · Grep ký tự \\ lạ + md5 file rulings."""
import pathlib, hashlib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

p = pathlib.Path("docs/analysis_rulings_holdout_20260923.md")
data = p.read_bytes()
text = data.decode("utf-8")

print(f"file: {p}")
print(f"md5 = {hashlib.md5(data).hexdigest()}")
print(f"bytes = {len(data)}")
print(f"chars = {len(text)}")
print(f"lines = {text.count(chr(10))}")
print(f"CR count = {data.count(bytes([13]))}")
print(f"LF count = {data.count(bytes([10]))}")
print(f"CRLF pairs = {data.count(bytes([13,10]))}")
print()

BS = chr(92)  # backslash
bs_count = text.count(BS)
print(f"backslash raw count in text: {bs_count}")

print("\n=== lines containing backslash ===")
for i, line in enumerate(text.splitlines(), 1):
    if BS in line:
        print(f"  L{i}: {repr(line)}")

# Escape sequences that could be mojibake or unintended escapes:
print("\n=== escape-like sequences (may be mojibake) ===")
patterns = [
    (BS + "n", "\\n literal"),
    (BS + "r", "\\r literal"),
    (BS + "t", "\\t literal"),
    (BS + BS, "\\\\ double"),
]
for pat, label in patterns:
    n = text.count(pat)
    if n > 0:
        print(f"  {label}: {n} occurrences")

# Suspect mojibake patterns
moji = ["â€", "Â", "á»", "�", "​", "‌", "‍"]
print("\n=== mojibake / zero-width chars ===")
for m in moji:
    n = text.count(m)
    if n > 0:
        print(f"  {repr(m)}: {n}")
print("  (empty output = clean)")

# Control chars (< 0x20 except LF/CR/TAB)
print("\n=== control chars < 0x20 except LF/CR/TAB ===")
weird = [(i,c) for i,c in enumerate(text) if ord(c) < 32 and c not in ("\n","\r","\t")]
print(f"  count: {len(weird)}")
for i,c in weird[:10]:
    print(f"  at char index {i}: {ord(c):#04x}")

# Non-ASCII chars outside common Vietnamese range
print("\n=== non-Vietnamese unicode (outside common blocks) ===")
common = set(range(0x20, 0x7F)) | set([0x0A, 0x0D, 0x09])  # ASCII printable + LF/CR/TAB
# Common Vietnamese: Latin Extended, combining marks
suspect = []
for i, c in enumerate(text):
    cp = ord(c)
    if cp in common: continue
    # Basic Latin, Latin-1 Supplement, Latin Extended-A/B, IPA Extensions
    if 0x00A0 <= cp <= 0x024F: continue
    # Latin Extended Additional (Vietnamese)
    if 0x1E00 <= cp <= 0x1EFF: continue
    # General Punctuation (VD dấu · –)
    if 0x2000 <= cp <= 0x206F: continue
    # Arrows
    if 0x2190 <= cp <= 0x21FF: continue
    # Math ops
    if 0x2200 <= cp <= 0x22FF: continue
    # Miscellaneous Symbols (warning ⚠)
    if 0x2600 <= cp <= 0x26FF: continue
    # CJK etc → suspect
    suspect.append((i, c, cp))
print(f"  count: {len(suspect)}")
for i, c, cp in suspect[:10]:
    print(f"  at {i}: {repr(c)} U+{cp:04X}")

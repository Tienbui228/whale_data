"""R1 pin · compute md5 of registration file BEFORE the pin line, then append pin line."""
import pathlib, hashlib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REG = pathlib.Path("docs/holdout_u0bell_registration_20260923.md")
text = REG.read_text(encoding="utf-8")

# Strip the placeholder pin line (if present)
placeholder = "**md5 R1 pinned:** `<sẽ điền sau probe>`\n"
if placeholder in text:
    text_stripped = text.replace(placeholder, "")
else:
    # Also try without trailing newline
    text_stripped = text.replace("**md5 R1 pinned:** `<sẽ điền sau probe>`", "")

# Ensure ends with single newline
text_stripped = text_stripped.rstrip() + "\n"

# Compute md5 on stripped body (pin doesn't include itself)
md5 = hashlib.md5(text_stripped.encode("utf-8")).hexdigest()
print(f"md5 (of body BEFORE pin line, LF only): {md5}")
print(f"body bytes: {len(text_stripped.encode('utf-8'))}")

# Append pin line
pin_line = f"\n**md5 R1 pinned:** `{md5}` · pinned_at=2026-09-23T{__import__('datetime').datetime.utcnow().strftime('%H:%M:%SZ')} · file này KHÔNG SỬA sau đây\n"
final = text_stripped + pin_line
REG.write_text(final, encoding="utf-8")
print(f"\n[write] final md5 (of body + pin line): {hashlib.md5(final.encode('utf-8')).hexdigest()}")
print(f"[write] path: {REG}")
print(f"[write] final bytes: {len(final.encode('utf-8'))}")

"""R1.v1 · Verify command · một lệnh duy nhất kiểm lại 2 md5 registration.
- Body md5 (bỏ dòng pin): phải = 96a97dca4798b647a13ced5e05975d94
- Full file md5:          phải = f60ca41faae81d377c83ad0675c3a1c2

Usage: python _probe_r1_verify_20260923.py
Exit 0 khi cả 2 md5 khớp · exit 1 khi mismatch.
"""
import hashlib, pathlib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REG = pathlib.Path("docs/holdout_u0bell_registration_20260923.md")
EXPECT_BODY = "96a97dca4798b647a13ced5e05975d94"
EXPECT_FULL = "f60ca41faae81d377c83ad0675c3a1c2"

text = REG.read_text(encoding="utf-8")
full_md5 = hashlib.md5(text.encode("utf-8")).hexdigest()

# Strip pin line to compute body-only md5
lines = text.rstrip("\n").split("\n")
pin_idx = None
for i, l in enumerate(lines):
    if l.startswith("**md5 R1 pinned:**"):
        pin_idx = i
        break
if pin_idx is None:
    print(f"[FAIL] pin line KHÔNG tìm thấy")
    sys.exit(1)
body_only = "\n".join(lines[:pin_idx]).rstrip() + "\n"
body_md5 = hashlib.md5(body_only.encode("utf-8")).hexdigest()

ok_body = (body_md5 == EXPECT_BODY)
ok_full = (full_md5 == EXPECT_FULL)

print(f"body-only md5: {body_md5} · expected {EXPECT_BODY} · {'MATCH' if ok_body else 'MISMATCH'}")
print(f"full-file md5: {full_md5} · expected {EXPECT_FULL} · {'MATCH' if ok_full else 'MISMATCH'}")
print(f"file: {REG} · bytes={len(text.encode('utf-8'))}")

sys.exit(0 if (ok_body and ok_full) else 1)

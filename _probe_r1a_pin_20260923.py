"""R1a pin · self-referential md5 for addendum file."""
import hashlib, pathlib, sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

F = pathlib.Path("docs/holdout_u0bell_r1a_episode_baseline_20260923.md")
text = F.read_text(encoding="utf-8")

placeholder = "**md5 R1a pinned:** `<sẽ điền sau probe>`"
if placeholder not in text:
    print("[FAIL] placeholder not found")
    sys.exit(1)

body_stripped = text.replace(placeholder + "\n", "").replace(placeholder, "")
body_stripped = body_stripped.rstrip() + "\n"

md5_body = hashlib.md5(body_stripped.encode("utf-8")).hexdigest()
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

pin_line = f"\n**md5 R1a pinned:** `{md5_body}` · pinned_at={now} · file này KHÔNG SỬA sau đây\n"
final = body_stripped + pin_line
F.write_text(final, encoding="utf-8")

full_md5 = hashlib.md5(final.encode("utf-8")).hexdigest()
print(f"body-only md5: {md5_body}")
print(f"full-file md5: {full_md5}")
print(f"bytes: {len(final.encode('utf-8'))}")
print(f"path: {F}")

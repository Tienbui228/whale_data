"""AL4 · gửi tay bản v3 · master label ngắn."""
import sys, hashlib, subprocess
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from master_preview_send import send_telegram, _tg_scan_bad_html
from lib.tg_len import tg_len

r = subprocess.run(
    [sys.executable, "/root/Data_back_test/whale_data/_probe_al4_alerts_v3_20260922.py"],
    capture_output=True, encoding="utf-8", timeout=180,
)
body = r.stdout.strip()
if not body:
    print(f"[FAIL] stderr={r.stderr[:200]}"); sys.exit(1)

n = tg_len(body)
body_md5 = hashlib.md5(body.encode()).hexdigest()
print(f"[COMPOSED] n={n} utf16-u · md5={body_md5[:12]}")

if n > 4096:
    print(f"[N/A-ERROR:BODY-TOO-LONG] {n}"); sys.exit(1)
bad = _tg_scan_bad_html(body)
if bad is not None:
    print(f"[N/A-ERROR:BAD-HTML] tag={bad[0]}"); sys.exit(1)

ok, det = send_telegram(body)
print(f"[SENT] ok={ok} · det={det} · chars={n} · md5={body_md5[:12]}")
sys.exit(0 if ok else 1)

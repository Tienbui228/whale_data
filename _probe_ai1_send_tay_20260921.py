"""AI1 · gửi tay bảng 28 cảnh báo GOM-E bị cắt 09-09..09-20 cho Tiên.

Prefix `[GỬI TAY · 28 cảnh báo GOM-E bị cắt 09-09..09-20]`
KHÔNG ghi state · KHÔNG counter · qua U7 gate + tg_len.
"""
import sys, os, hashlib, subprocess
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from master_preview_send import send_telegram, _tg_scan_bad_html
from lib.tg_len import tg_len

# Chạy probe AI1, capture stdout
r = subprocess.run(
    [sys.executable, "/root/Data_back_test/whale_data/_probe_ai1_missed_alerts_20260921.py"],
    capture_output=True, encoding="utf-8", timeout=120,
)
body = r.stdout.strip()
if not body:
    print(f"[FAIL] empty body · stderr={r.stderr[:200]}")
    sys.exit(1)

# Prepend prefix
PREFIX = "[GỬI TAY · 28 cảnh báo GOM-E bị cắt 09-09..09-20]\n\n"
full_msg = PREFIX + body
n = tg_len(full_msg)
body_md5 = hashlib.md5(full_msg.encode()).hexdigest()

print(f"═══ COMPOSED ═══")
print(f"  n_chars (tg_len): {n} vs 4096")
print(f"  body_md5        : {body_md5}")

if n > 4096:
    print(f"[N/A-ERROR:BODY-TOO-LONG] {n} > 4096")
    sys.exit(1)
bad = _tg_scan_bad_html(full_msg)
if bad is not None:
    print(f"[N/A-ERROR:BAD-HTML] tag={bad[0]}")
    sys.exit(1)

print(f"═══ SEND ═══")
ok, det = send_telegram(full_msg)
print(f"  ok={ok} · det={det} · chars={n} · md5={body_md5[:12]}")
sys.exit(0 if ok else 1)

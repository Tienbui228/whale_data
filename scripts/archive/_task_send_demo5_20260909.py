"""SEND DEMO-5 target=09-08 · V3.5j directive · Daily channel via /root/.env_tg loader."""
import os, sys, json, hashlib, urllib.request, urllib.parse
from pathlib import Path

# Load /root/.env_tg (relay pattern · chmod 600 · outside repo)
ENV_PATH = Path("/root/.env_tg")
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()

BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_DAILY = os.environ.get("TG_CHAT_ID_DAILY", "")
print(f"[ENV] bot_set={bool(BOT)} · chat_daily_set={bool(CHAT_DAILY)} · chat_daily={CHAT_DAILY[:8]}...")

# Rebuild body from digest_summary_v2 (fresh)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from digest_summary_v2 import build_v2_digest
target = "2026-09-08"
body = build_v2_digest(target)

# Prepend DEMO prefix
prefix = "[DEMO — đêm-0 chưa sạch, chưa đếm preview]\n[MASTER-PREVIEW · DEMO-5 · target=2026-09-08]\n\n"
full_msg = prefix + body
print(f"[BODY] len={len(full_msg)}B · md5={hashlib.md5(full_msg.encode()).hexdigest()[:12]}")

if not BOT or not CHAT_DAILY:
    print("[N/A-ERROR:SEND] env missing"); sys.exit(1)

# Telegram may reject if >4096 chars · use HTML mode + chunk if needed
url = f"https://api.telegram.org/bot{BOT}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT_DAILY, "text": full_msg, "parse_mode": "HTML",
    "disable_web_page_preview": "true",
}).encode()
try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read().decode())
        ok = resp.get("ok"); mid = resp.get("result", {}).get("message_id")
        h12 = hashlib.md5(full_msg.encode()).hexdigest()[:12]
        print(f"[SENT] master_preview_DEMO-5 ok={ok} HTTP {r.status} hash={h12} message_id={mid} target={target}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[SEND-HTTPError] {e.code} · {body[:200]}")
    sys.exit(1)
except Exception as e:
    print(f"[SEND-ERR] {type(e).__name__}: {e}")
    sys.exit(1)

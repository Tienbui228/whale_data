"""SEND DEMO-6 target=09-08 · V3.5k fix-round · Daily channel."""
import os, sys, json, hashlib, urllib.request, urllib.parse
from pathlib import Path

ENV_PATH = Path("/root/.env_tg")
for line in ENV_PATH.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("="); os.environ[k.strip()] = v.strip()

BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TG_CHAT_ID_DAILY"]

sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from digest_summary_v2 import build_v2_digest
body = build_v2_digest("2026-09-08")

prefix = "[DEMO-6 · fix-round · target=09-08]\n\n"
full = prefix + body
h12 = hashlib.md5(full.encode()).hexdigest()[:12]
print(f"[BODY-LEN] {len(full)}B · md5={h12}")

# Send Telegram
url = f"https://api.telegram.org/bot{BOT}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT, "text": full, "parse_mode": "HTML",
    "disable_web_page_preview": "true",
}).encode()
try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read().decode())
        ok = resp.get("ok"); mid = resp.get("result", {}).get("message_id")
        print(f"[SENT] master_preview_DEMO-6 ok={ok} HTTP {r.status} hash={h12} message_id={mid} target=2026-09-08")
        # Wire into bell_journal
        from lib.artifact_dump import log_bell
        log_bell("master_preview", "2026-09-08", "TG_CHAT_ID_DAILY", ok, r.status, mid, full)
        print(f"[BELL-JOURNAL] appended")
except urllib.error.HTTPError as e:
    body_err = e.read().decode()
    print(f"[SEND-HTTPError] {e.code} · {body_err[:400]}")
    sys.exit(1)

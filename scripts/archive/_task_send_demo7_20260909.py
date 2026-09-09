"""SEND DEMO-7 target=09-08 · V3.5l PRE-SUBTAG · Daily channel."""
import os, sys, json, hashlib, urllib.request, urllib.parse
from pathlib import Path

for line in Path("/root/.env_tg").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("="); os.environ[k.strip()] = v.strip()

sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from digest_summary_v2 import build_v2_digest
body = build_v2_digest("2026-09-08")
prefix = "[DEMO-7 · fix-round · V3.5l PRE-SUBTAG · target=09-08]\n\n"
full = prefix + body
h12 = hashlib.md5(full.encode()).hexdigest()[:12]
print(f"[BODY-LEN] {len(full)}B · md5={h12}")

url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": os.environ["TG_CHAT_ID_DAILY"], "text": full,
    "parse_mode": "HTML", "disable_web_page_preview": "true",
}).encode()
req = urllib.request.Request(url, data=data, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    resp = json.loads(r.read().decode())
    ok = resp.get("ok"); mid = resp.get("result", {}).get("message_id")
    print(f"[SENT] DEMO-7 ok={ok} HTTP {r.status} hash={h12} message_id={mid} target=2026-09-08")

# Bell-journal
from lib.artifact_dump import log_bell
log_bell("master_preview", "2026-09-08", "TG_CHAT_ID_DAILY", ok, r.status, mid, full)
print("[BELL-JOURNAL] appended")

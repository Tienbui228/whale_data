"""ERRATA send target=09-08 · V3.5m directive item 0 · proxy label thu hồi."""
import os, sys, json, hashlib, urllib.request, urllib.parse
from pathlib import Path

for line in Path("/root/.env_tg").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("="); os.environ[k.strip()] = v.strip()

errata = (
    "[ERRATA · DEMO-7 target 09-08 msg_id=22]\n\n"
    "Nhãn OPEN/CAGED trong khối ⭐-PRE đêm qua (msg_id=22) từ nguồn PROXY chưa niêm — "
    "đọc bằng mắt cũ. Proxy = watchlist LIST-A membership + freshwatch_daily div_avg3/gLSR, "
    "KHÔNG phải GOM-E as-printed spec. Discrepancy: AIO (div=0.386 · NOT in LIST-A) và "
    "GIGGLE (div=3.094) impl=OPEN nhưng operator kỳ vọng CAGED · lệch spec.\n\n"
    "Rollback deployed (V3.5m commit sắp về): khối ⭐-PRE render PRE trần + banner "
    "'[SUBTAG-PENDING: nguồn GOM-E chưa niêm]' · zero OPEN/CAGED từ proxy.\n\n"
    "Đêm 1/2 KHÔNG được đếm. Đồng hồ chờ subtag về đúng nhánh (GOM-E source niêm)."
)
h12 = hashlib.md5(errata.encode()).hexdigest()[:12]
print(f"[BODY-LEN] {len(errata)}B · md5={h12}")

url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": os.environ["TG_CHAT_ID_DAILY"], "text": errata,
    "parse_mode": "HTML", "disable_web_page_preview": "true",
}).encode()
req = urllib.request.Request(url, data=data, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    resp = json.loads(r.read().decode())
    ok = resp.get("ok"); mid = resp.get("result", {}).get("message_id")
    print(f"[SENT] ERRATA ok={ok} HTTP {r.status} hash={h12} message_id={mid} corrects=msg_id=22")

sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from lib.artifact_dump import log_bell
log_bell("errata_master_preview", "2026-09-08", "TG_CHAT_ID_DAILY", ok, r.status, mid, errata)
print("[BELL-JOURNAL] appended")

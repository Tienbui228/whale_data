"""V3.5q · execute item 1+2+4 batch:
- Restore verdict 09-09 = KÍCH (forensic note post-fix)
- Delete standing_active.marker (V3.5q gỡ bypass)
- Send ERRATA msg-24/25 void-đếm to Daily
- Initialize preview_journal with epoch header
- Reset demo5_sent.marker (điểm-thi standard)
"""
import os, sys, json, hashlib, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

for l in Path("/root/.env_tg").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k,_,v = l.partition("="); os.environ[k.strip()] = v.strip()

REPO = Path("/root/Data_back_test/whale_data")
STATE = REPO / "data/state"

# 1. Restore verdict 09-09 = KÍCH · store epoch first-compute
verdict_kich = {
    "verdict": "KÍCH",
    "date": "2026-09-09",
    "computed_at": "2026-09-10T01:46:02.004891+00:00",
    "evidence_pointer": "V3.5q restore · điểm-thi-bất-biến · missing phase_map · cause IndentationError V3.5o",
    "n_full_pair": "5/6",
    "n_sent": "5/6",
    "sent_leg_detail": {
        "tg_relay_gom_h": {"ok": True, "source": "native-marker", "cite": "tg_relay.log: [SENT] all_ok=True"},
        "fresh_digest": {"ok": True, "source": "native-marker", "cite": "digest_daily_vps.log: [SENT] Fresh-Wallets ok=True"},
        "exch_digest": {"ok": True, "source": "native-marker", "cite": "digest_daily_vps.log: [SENT] EXCH-BAL ok=True"},
        "gom_daily": {"ok": True, "source": "bell_journal", "cite": "body_md5=5ce780d6c9cf msg_id=None"},
        "phase_map": {"ok": False, "source": None, "cite": None},
        "watchlist": {"ok": True, "source": "bell_journal", "cite": "body_md5=cf65cd10e990 msg_id=None"},
    },
    "missing_legs": ["phase_map"],
    "pin_scan_p1_p22_bo_niem": "PASS",
    "unknown_sentinels": [],
    "forensic_note": "post-fix 6/6 (phase_map CATCH-UP + IndentationError fix) · điểm-thi bất-biến giữ KÍCH · fix ở PERFORMER (sender) · KHÔNG grader-fix",
    "full_pair_detail": {},
}
# Save both epoch (immutable) + live
epoch_p = STATE / "verdict_epoch_2026-09-09.json"
epoch_p.write_text(json.dumps(verdict_kich, ensure_ascii=False, indent=2), encoding="utf-8")
live_p = STATE / "dem0_lan2_verdict.json"
live_p.write_text(json.dumps(verdict_kich, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[RESTORE] verdict 09-09 = KÍCH · epoch stored · live overwritten")

# 2. Delete standing_active (V3.5q gỡ bypass)
sa_p = STATE / "standing_active.marker"
if sa_p.exists():
    sa_p.unlink()
    print(f"[DELETE] {sa_p.name} · bypass gỡ")

# 3. Delete demo5_sent.marker (reset · điểm-thi standard · marker sẽ tạo lại từ preview journal)
d5_p = STATE / "demo5_sent.marker"
if d5_p.exists():
    d5_p.unlink()
    print(f"[DELETE] {d5_p.name} · reset")

# 4. Initialize preview_journal (empty · epoch=2026-09-10)
pj_p = REPO / "data/logs/preview_journal.jsonl"
if not pj_p.exists():
    pj_p.parent.mkdir(parents=True, exist_ok=True)
    pj_p.write_text("", encoding="utf-8")
    print(f"[INIT] preview_journal.jsonl empty · epoch=2026-09-10")

# 5. Send ERRATA (msg-24/25 void-đếm)
errata = (
    "[ERRATA · msg 24/25 void-đếm]\n\n"
    "Nhãn 'đêm 1/2 · 2/2' trên msg 24 và msg 25 (DEMO Daily channel) VÔ HIỆU.\n"
    "Hai send cùng target=2026-09-09 · một cú qua bypass standing (bug V3.5p).\n\n"
    "Bộ đếm RESET. Đêm 1/2 thật do máy tự trình sáng 11/09 UTC sau cron chấm target=09-10.\n\n"
    "V3.5q: điểm-thi-bất-biến áp dụng · verdict 09-09 giữ KÍCH · post-fix chỉ forensic-note.\n"
    "Bypass logic ĐÃ XÓA · re-send tay đòi --resend + [CATCH-UP]/[CORRECTED] + bell-evidence-check."
)
h12 = hashlib.md5(errata.encode()).hexdigest()[:12]
print(f"[BODY] len={len(errata)}B md5={h12}")

url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": os.environ["TG_CHAT_ID_DAILY"], "text": errata,
    "parse_mode": "HTML", "disable_web_page_preview": "true",
}).encode()
try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read().decode())
        ok = resp.get("ok"); mid = resp.get("result", {}).get("message_id")
        print(f"[SENT] ERRATA-void-đếm ok={ok} HTTP {r.status} hash={h12} message_id={mid} corrects=msg 24,25")
except Exception as e:
    print(f"[SEND-ERR] {e}")

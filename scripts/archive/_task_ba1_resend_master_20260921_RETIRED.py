"""BA1 · gửi lại master 09-21 vào đúng kênh master (TG_CHAT_ID_DAILY).

AY1 msg_id=8852 đã gửi sai kênh (TELEGRAM_CHAT_ID ...49295207 · kênh phụ).
Master channel = TG_CHAT_ID_DAILY (...73659017 · từ .env_tg).

Fix:
  · Đọc .env_tg cho TG_CHAT_ID_DAILY + TG_BOT_TOKEN (fallback TELEGRAM_BOT_TOKEN)
  · parse_mode=HTML (master convention)
  · prefix [GỬI TAY · target=2026-09-21]
  · state md5 SAME 5/5 (no journal · no epoch · no counter)
"""
from __future__ import annotations
import os, sys, hashlib, json, urllib.request, urllib.parse
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

# Load both env files (like master does): .env_tg has master chat_id
for f in [_REPO / ".env", Path("/root/.env_tg")]:
    if not f.exists(): continue
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TG_TOKEN = os.environ.get("TG_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_MASTER = os.environ.get("TG_CHAT_ID_DAILY", "")

STATE_FILES = [
    _REPO / "data/state/dem0_lan2_verdict.json",
    _REPO / "data/state/master_preview_journal.jsonl",
    _REPO / "data/state/preview_epoch.marker",
    _REPO / "data/logs/bell_journal.jsonl",
    _REPO / "data/logs/master_preview.log",
]


def _md5_state():
    out = {}
    for p in STATE_FILES:
        if p.exists():
            out[p.name] = (hashlib.md5(p.read_bytes()).hexdigest(), p.stat().st_size)
        else:
            out[p.name] = ("ABSENT", 0)
    return out


TARGET = "2026-09-21"
BODY_P = _REPO / "data/logs/master_preview_body.txt"

if not TG_CHAT_MASTER or not TG_TOKEN:
    print(f"ERROR: TG_BOT_TOKEN or TG_CHAT_ID_DAILY missing")
    print(f"  TG_TOKEN present: {bool(TG_TOKEN)} · TG_CHAT_MASTER: {bool(TG_CHAT_MASTER)}")
    sys.exit(1)

# md5 BEFORE
md5_before = _md5_state()
print("═══ BA1 · state md5 BEFORE ═══")
for name, (h, sz) in sorted(md5_before.items()):
    print(f"  {name:35s} · {h[:12] if h != 'ABSENT' else 'ABSENT':>12s} · {sz}b")

# Load body
if not BODY_P.exists():
    print(f"ERROR: {BODY_P} missing"); sys.exit(1)
body = BODY_P.read_text(encoding="utf-8")
if not body.startswith(f"━━ FRESHWATCH TỔNG · 21/09 · target={TARGET} ━━"):
    print("ERROR: body head mismatch"); sys.exit(1)
prefix = f"[GỬI TAY · target={TARGET}]\n"
full_msg = prefix + body
full_md5 = hashlib.md5(full_msg.encode()).hexdigest()[:12]
print(f"body md5={hashlib.md5(body.encode()).hexdigest()[:12]} · full_msg size={len(full_msg)} · full_md5={full_md5}")
print(f"→ Sending to chat_id=...{TG_CHAT_MASTER[-8:]} (TG_CHAT_ID_DAILY) via bot ...{TG_TOKEN[-8:]} · parse_mode=HTML")

url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": TG_CHAT_MASTER, "text": full_msg,
    "parse_mode": "HTML",
    "disable_web_page_preview": "true",
}).encode("utf-8")
try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        resp_body = r.read().decode()
        resp = json.loads(resp_body)
        ok = bool(resp.get("ok"))
        msg_id = resp.get("result", {}).get("message_id")
        chat_id_resp = resp.get("result", {}).get("chat", {}).get("id")
        print(f"  ok={ok} · msg_id={msg_id} · http={r.status} · chat_id_resp=...{str(chat_id_resp)[-8:] if chat_id_resp else '?'}")
except Exception as e:
    print(f"  SEND FAIL: {e}"); ok = False; msg_id = None

# md5 AFTER
md5_after = _md5_state()
print()
print("═══ BA1 · state md5 AFTER ═══")
all_same = True
for name in sorted(md5_before.keys()):
    b, bs = md5_before[name]
    a, ash = md5_after[name]
    same = "SAME" if b == a else "CHANGED"
    if b != a: all_same = False
    print(f"  {name:35s} · {b[:12] if b != 'ABSENT' else 'ABSENT':>12s} → {a[:12] if a != 'ABSENT' else 'ABSENT':>12s} · {bs}b → {ash}b · {same}")

print()
print(f"═══ state md5 all-SAME: {all_same} ═══")
print(f"send ok={ok} · msg_id={msg_id} · full_md5={full_md5} · chat=TG_CHAT_ID_DAILY · target={TARGET}")
sys.exit(0 if (ok and all_same) else 1)

"""AY1 · gửi tay master target=2026-09-21 · như W4.

Constraint (ANALYSIS AY1):
  · prefix "[GỬI TAY · target=2026-09-21]\\n"
  · KHÔNG journal (không ghi master_preview_journal.jsonl)
  · KHÔNG epoch (không stamp preview_epoch.marker)
  · KHÔNG counter (không đếm distinct_targets)
  · state md5 trước/sau SAME (all state files not mutated)

Flow:
  1. md5 state files BEFORE
  2. Load master_preview_body.txt (target 09-21 · rendered 22/09 06:33 UTC)
  3. Verify body starts with "━━ FRESHWATCH TỔNG · 21/09 · target=2026-09-21 ━━"
  4. Prepend prefix + tg_send
  5. md5 state files AFTER · assert SAME
  6. Print result
"""
from __future__ import annotations
import os, sys, hashlib, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

# Load .env for TG credentials
_env_p = _REPO / ".env"
if _env_p.exists():
    for _ln in _env_p.read_text(encoding="utf-8").splitlines():
        _ln = _ln.strip()
        if _ln and not _ln.startswith("#") and "=" in _ln:
            _k, _, _v = _ln.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

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


def _fmt_md5_diff(before, after):
    lines = []
    for name in sorted(before.keys()):
        b, bs = before[name]
        a, ash = after[name]
        same = "SAME" if b == a else "CHANGED"
        lines.append(f"  {name:35s} · {b[:12] if b != 'ABSENT' else 'ABSENT':>12s} → {a[:12] if a != 'ABSENT' else 'ABSENT':>12s} · {bs}b → {ash}b · {same}")
    return "\n".join(lines)


TARGET = "2026-09-21"
BODY_P = _REPO / "data/logs/master_preview_body.txt"

# Step 1 · md5 BEFORE
md5_before = _md5_state()
print("═══ AY1 · state md5 BEFORE ═══")
for name, (h, sz) in sorted(md5_before.items()):
    print(f"  {name:35s} · {h[:12] if h != 'ABSENT' else 'ABSENT':>12s} · {sz}b")

# Step 2-3 · Load + verify body
if not BODY_P.exists():
    print(f"ERROR: {BODY_P} missing"); sys.exit(1)
body = BODY_P.read_text(encoding="utf-8")
expected_head = f"━━ FRESHWATCH TỔNG · 21/09 · target={TARGET} ━━"
if not body.startswith(expected_head):
    print(f"ERROR: body head mismatch · got:\n{body[:80]!r}"); sys.exit(1)
print(f"body from {BODY_P.name} · size={len(body)} chars · md5={hashlib.md5(body.encode()).hexdigest()[:12]}")

# Step 4 · Prefix + send
prefix = f"[GỬI TAY · target={TARGET}]\n"
full_msg = prefix + body
full_md5 = hashlib.md5(full_msg.encode()).hexdigest()[:12]
print(f"full_msg size={len(full_msg)} · full_md5={full_md5}")

if not TG_TOKEN or not TG_CHAT_ID:
    print("ERROR: TG_TOKEN or TG_CHAT_ID missing in .env"); sys.exit(1)

print(f"→ Sending to chat_id={TG_CHAT_ID} ...")
url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": full_msg}).encode("utf-8")
try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        resp_body = r.read().decode()
        resp = json.loads(resp_body)
        ok = bool(resp.get("ok"))
        msg_id = resp.get("result", {}).get("message_id")
        print(f"  ok={ok} · msg_id={msg_id} · http={r.status}")
except Exception as e:
    print(f"  SEND FAIL: {e}"); ok = False; msg_id = None

# Step 5 · md5 AFTER (note: master_preview.log MAY change if anything writes to it,
# but our script doesn't · however send may trigger log entries via Telegram lib · check)
md5_after = _md5_state()
print()
print("═══ AY1 · state md5 AFTER ═══")
print(_fmt_md5_diff(md5_before, md5_after))

all_same = all(md5_before[n][0] == md5_after[n][0] for n in md5_before)
print()
print(f"═══ state md5 all-SAME: {all_same} ═══")
print(f"send ok={ok} · msg_id={msg_id} · full_md5={full_md5} · target={TARGET}")
sys.exit(0 if (ok and all_same) else 1)

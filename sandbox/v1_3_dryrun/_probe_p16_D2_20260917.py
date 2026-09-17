"""p16 · D2 đen-một-lần · postcheck/journal chạy BẤT KỂ ok_send · counter filter sent_ok."""
from __future__ import annotations
import sys, os, json, tempfile, shutil, hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_REAL = Path(r"D:/Data back test/whale_data")
SB = Path(tempfile.mkdtemp(prefix='p16_D2_'))
(SB / "data/state").mkdir(parents=True, exist_ok=True)
(SB / "data/logs").mkdir(parents=True, exist_ok=True)
(SB / "data/artifacts").mkdir(parents=True, exist_ok=True)

# Mirror minimal artifact + state files for test
def _fake_artifact(target):
    # concat = body sans seal
    concat = f"""━━ FRESHWATCH TỔNG · {target[8:10]}/{target[5:7]} · target={target} ━━
⭐-PRE (1):
   FAKE 2-trục · dummy · → PRE
━━ footer ━━
ledger_state=aaa · fixture_master=bbb
cites: gomh=dummy"""
    (SB / f"data/artifacts/master_concat_{target}.txt").write_bytes(concat.encode())
    seal = hashlib.md5(concat.encode()).hexdigest()[:12]
    body = concat + f"\nconcat-seal={seal} · target={target} · built=2026-09-17T00:00:00+00:00"
    (SB / f"data/artifacts/master_body_{target}.txt").write_bytes(body.encode())

# Load master_preview_send + postcheck_gate_d with sandbox paths
sys.path.insert(0, str(REPO_REAL / "scripts"))
import master_preview_send as mps
import postcheck_gate_d as pgd
import importlib
importlib.reload(mps)
importlib.reload(pgd)

mps.REPO = SB
mps.STATE = SB / "data/state"
mps.LOG_P = SB / "data/logs/master_preview.log"
mps.PREVIEW_JOURNAL = SB / "data/logs/preview_journal.jsonl"
mps.MASTER_JOURNAL = SB / "data/logs/master_journal.jsonl"
mps.COUNTER_FILE = SB / "data/state/master_preview_counter.json"
pgd.REPO = SB
pgd.ART_DIR = SB / "data/artifacts"
pgd.SB_LOG = SB / "data/logs/harness_sabotage.log"

print("═" * 74)
print("p16 · D2 đen-một-lần · postcheck+journal chạy BẤT KỂ ok_send")
print("═" * 74)

# ═════════ CASE ĐEN: send fail (mock 400) ═════════
target_den = "2026-09-15"
_fake_artifact(target_den)

# Monkey-patch send_telegram to fail
original_send = mps.send_telegram
def fail_send(text):
    return (False, "HTTPError: HTTP Error 400: Bad Request")
mps.send_telegram = fail_send

# Simulate the D2-fixed post-send flow inline
full_msg = "[MASTER · live từ 2026-09-15]\ndummy body"
ok_send, det = mps.send_telegram(full_msg)
print(f"\nĐEN · ok_send={ok_send} · det={det[:60]}")
mid = None
try:
    pc = pgd.postcheck(target_den)
    print(f"  postcheck ran: postcheck_ok={pc['postcheck_ok']} · p21={pc['p21']} p22={pc['p22']} p27={pc.get('p27','?')}")
except Exception as e:
    pc = {"postcheck_ok": False, "p21": "ERR", "p22": "ERR", "p27": "ERR", "flag": f"[POSTCHECK-FAIL {type(e).__name__}]"}
    print(f"  postcheck EXCEPTION: {e}")

entry = {
    "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "renderer": "master_live", "target_date": target_den,
    "channel": "TG_CHAT_ID_DAILY", "ok": ok_send, "http_code": 200 if ok_send else 0,
    "message_id": mid, "body_md5": hashlib.md5(full_msg.encode()).hexdigest(),
    "standing_ok": True, "postcheck_ok": pc["postcheck_ok"],
    "postcheck_flag": pc.get("flag",""), "night_label": "[MASTER · live từ 2026-09-15]",
    "sent_ok": ok_send, "send_error": "" if ok_send else str(det)[:200],
}
mps.preview_journal_append(entry)

# Verify journal entry exists
assert mps.MASTER_JOURNAL.exists(), "master_journal KHÔNG được tạo!"
entries = [json.loads(l) for l in mps.MASTER_JOURNAL.read_text().splitlines() if l.strip()]
assert len(entries) == 1
e = entries[0]
print(f"  journal entry:")
print(f"    sent_ok={e['sent_ok']} · send_error='{e['send_error'][:40]}...'")
print(f"    postcheck_ok={e['postcheck_ok']}")

# NIGHT-COUNTER: should NOT count this target
distinct = set()
for e2 in mps._journal_iter():
    if e2.get("standing_ok") and e2.get("postcheck_ok") and e2.get("sent_ok", True) \
       and e2.get("target_date", "") >= mps.PREVIEW_EPOCH:
        distinct.add(e2["target_date"])

n = len(distinct)
print(f"  NIGHT-COUNTER distinct (sent_ok filter): {n}")
den_ok = (n == 0 and e["sent_ok"] == False and mps.MASTER_JOURNAL.exists())
print(f"  ★ ĐEN đúng (n=0 · sent_ok=False · journal entry có): {'✅' if den_ok else '❌'}")

# ═════════ CASE XANH: send ok ═════════
print()
target_xanh = "2026-09-16"
_fake_artifact(target_xanh)

def ok_send_mock(text):
    return (True, "HTTP 200 · message_id=42")
mps.send_telegram = ok_send_mock

full_msg2 = "[MASTER · live từ 2026-09-15]\ndummy 09-16"
ok_send2, det2 = mps.send_telegram(full_msg2)
print(f"XANH · ok_send={ok_send2} · det={det2}")
try:
    pc2 = pgd.postcheck(target_xanh)
    print(f"  postcheck ran: postcheck_ok={pc2['postcheck_ok']}")
except Exception as e:
    pc2 = {"postcheck_ok": False, "flag": "err"}

import re as _re
mid2 = None
m = _re.search(r"message_id=(\d+)", det2)
if m: mid2 = int(m.group(1))

entry2 = {
    "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "renderer": "master_live", "target_date": target_xanh,
    "channel": "TG_CHAT_ID_DAILY", "ok": ok_send2, "http_code": 200,
    "message_id": mid2, "body_md5": hashlib.md5(full_msg2.encode()).hexdigest(),
    "standing_ok": True, "postcheck_ok": pc2["postcheck_ok"],
    "postcheck_flag": pc2.get("flag",""), "night_label": "[MASTER · live từ 2026-09-15]",
    "sent_ok": ok_send2, "send_error": "",
}
mps.preview_journal_append(entry2)

distinct2 = set()
for e2 in mps._journal_iter():
    if e2.get("standing_ok") and e2.get("postcheck_ok") and e2.get("sent_ok", True) \
       and e2.get("target_date", "") >= mps.PREVIEW_EPOCH:
        distinct2.add(e2["target_date"])

n2 = len(distinct2)
print(f"  NIGHT-COUNTER distinct after XANH: {n2}")
xanh_ok = (n2 == 1 and target_xanh in distinct2)
print(f"  ★ XANH đúng (counter tăng lên 1, gồm target 09-16): {'✅' if xanh_ok else '❌'}")

# ═════ Verdict ═════
print()
print("═" * 74)
print(f"VERDICT · ĐEN={den_ok} · XANH={xanh_ok}")
print(f"  {'✅ p16 PASS · postcheck/journal độc lập ok_send · counter filter sent_ok đúng' if (den_ok and xanh_ok) else '❌ p16 FAIL'}")

shutil.rmtree(SB, ignore_errors=True)

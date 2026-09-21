"""W4 · GỬI TAY target 09-20 (đêm 09-20 SKIP vì lint fail).

Rules:
- BỎ QUA standing gate + label-lint
- Prefix `[GỬI TAY · target=2026-09-20 · không tính NIGHT-COUNTER]`
- KHÔNG ghi verdict_epoch / journal / counter
- Print SỐ KÝ TỰ trước khi gửi; >4096 → KHÔNG gửi
- Quét HTML tag lạ (U7 gate)
- Print: message_id, HTTP, chars, body_md5, md5 3 state file trước/sau (SAME)
"""
import sys, os, hashlib, json
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import master_preview_send as mps

TARGET = "2026-09-20"
PREFIX = f"[GỬI TAY · target={TARGET} · không tính NIGHT-COUNTER]\n"

STATE = Path("/root/Data_back_test/whale_data/data/state")
LOGS = Path("/root/Data_back_test/whale_data/data/logs")

def md5f(p):
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "MISSING"

# BEFORE
before = {
    "verdict_epoch_09_20": md5f(STATE / "verdict_epoch_2026-09-20.json"),
    "master_journal": md5f(LOGS / "master_journal.jsonl"),
    "preview_journal": md5f(LOGS / "preview_journal.jsonl"),
    "dem0": md5f(STATE / "dem0_lan2_verdict.json"),
}
print(f"═══ BEFORE state ═══")
for k, v in before.items(): print(f"  {k}: {v}")

# ── STEP RENDER ──
print(f"\n[STEP RENDER] build_v2_digest({TARGET})")
ok, res = mps.step_render_digest(TARGET)
if not ok:
    print(f"  FAIL · {res}"); sys.exit(1)
body = res
print(f"  ok · body_len={len(body)} · md5={hashlib.md5(body.encode()).hexdigest()[:12]}")

# ── STEP LINT (BYPASS · lint fail đêm nay do dòng '[B] = unhedge đã xác nhận') ──
print(f"\n[STEP LINT] BYPASS (đêm nay lint fail vì header O1 'đã xác nhận')")

# ── STEP SEAL ──
print(f"\n[STEP SEAL] concat-seal verify")
ok, msg = mps.step_concat_seal(body)
print(f"  {'PASS' if ok else 'FAIL'} · {msg}")
if not ok: sys.exit(1)

# ── COMPOSE ──
full_msg = PREFIX + body
n_chars = len(full_msg)
body_md5 = hashlib.md5(full_msg.encode()).hexdigest()

print(f"\n═══ COMPOSED ═══")
print(f"  prefix     : {PREFIX.strip()}")
print(f"  n_chars    : {n_chars} (limit=4096)")
print(f"  body_md5   : {body_md5}")

if n_chars > 4096:
    print(f"\n[N/A-ERROR:BODY-TOO-LONG] {n_chars} > 4096 · KHÔNG gửi"); sys.exit(1)

# ── HTML U7 ──
bad = mps._tg_scan_bad_html(full_msg)
if bad is not None:
    print(f"\n[N/A-ERROR:BAD-HTML] tag={bad[0]} pos={bad[1]} · KHÔNG gửi"); sys.exit(1)
print(f"  html-scan  : OK")

# ── SEND ──
print(f"\n═══ SEND ═══")
ok_send, det = mps.send_telegram(full_msg)
print(f"  ok      : {ok_send}")
print(f"  det     : {det}")
print(f"  chars   : {n_chars}")
print(f"  body_md5: {body_md5}")

# ── AFTER state ──
after = {
    "verdict_epoch_09_20": md5f(STATE / "verdict_epoch_2026-09-20.json"),
    "master_journal": md5f(LOGS / "master_journal.jsonl"),
    "preview_journal": md5f(LOGS / "preview_journal.jsonl"),
    "dem0": md5f(STATE / "dem0_lan2_verdict.json"),
}
print(f"\n═══ AFTER state ═══")
all_same = True
for k, v in after.items():
    same = "SAME" if before[k] == v else "CHANGED"
    if before[k] != v: all_same = False
    print(f"  {k}: {v} · {same}")

print(f"\n═══ INVARIANT · KHÔNG state đổi: {'PASS' if all_same else 'FAIL'} ═══")
sys.exit(0 if ok_send else 1)

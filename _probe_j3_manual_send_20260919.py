"""J3 · GỬI TAY bản tin cho Tiên · target=2026-09-18 (09-19 chưa đủ chân).

Rules:
- BỎ QUA standing gate
- Prefix `[GỬI TAY · target=2026-09-18 · không tính NIGHT-COUNTER]`
- KHÔNG ghi verdict_epoch, KHÔNG ghi master_journal, KHÔNG tăng counter
- Print SỐ KÝ TỰ trước khi gửi; >4096 → KHÔNG gửi
- Quét HTML tag lạ trước khi gọi API (U7 gate đã sẵn trong send_telegram)
- Print: message_id, HTTP, chars, body_md5, khối B + khối UNHEDGE nguyên văn
"""
import sys, os, hashlib
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

# Env toggles cho V1.3 + U0-BELL + B-tier (như main pipeline)
os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import master_preview_send as mps

TARGET = "2026-09-18"
PREFIX = f"[GỬI TAY · target={TARGET} · không tính NIGHT-COUNTER]\n"

print(f"═══ J3 · GỬI TAY · target={TARGET} ═══\n")

# --- STEP RENDER ---
print(f"[STEP RENDER] build_v2_digest(target={TARGET})")
ok, res = mps.step_render_digest(TARGET)
if not ok:
    print(f"  FAIL · {res}")
    sys.exit(1)
body = res
print(f"  ok · body_len={len(body)} · md5={hashlib.md5(body.encode()).hexdigest()[:12]}")

# --- STEP LINT ---
print(f"\n[STEP LINT] label_claims_lint")
ok, msg = mps.step_label_lint(body)
print(f"  {'PASS' if ok else 'FAIL'} · {msg}")
if not ok:
    print(f"  ABORT · lint fail")
    sys.exit(1)

# --- STEP SEAL ---
print(f"\n[STEP SEAL] concat-seal verify")
ok, msg = mps.step_concat_seal(body)
print(f"  {'PASS' if ok else 'FAIL'} · {msg}")
if not ok:
    print(f"  ABORT · seal fail")
    sys.exit(1)

# --- COMPOSE MSG ---
full_msg = PREFIX + body
n_chars = len(full_msg)
body_md5 = hashlib.md5(full_msg.encode()).hexdigest()

print(f"\n═══ COMPOSED MSG ═══")
print(f"  prefix     : {PREFIX.strip()}")
print(f"  n_chars    : {n_chars} (limit=4096)")
print(f"  body_md5   : {body_md5}")

# --- PRE-CHECK LEN ---
if n_chars > 4096:
    print(f"\n[N/A-ERROR:BODY-TOO-LONG] {n_chars} > 4096 · KHÔNG gửi")
    sys.exit(1)

# --- HTML SCAN (U7 gate · pre-flight) ---
bad = mps._tg_scan_bad_html(full_msg)
if bad is not None:
    tag_str, pos = bad
    print(f"\n[N/A-ERROR:BAD-HTML] tag={tag_str} pos={pos} · KHÔNG gửi")
    sys.exit(1)
print(f"  html-scan  : OK · không có tag lạ")

# --- EXTRACT [B] + [UNHEDGE] BLOCKS ---
print(f"\n═══ KHỐI B (verbatim) ═══")
lines = body.split("\n")
in_b = False; b_block = []
for ln in lines:
    if ln.startswith("── B ──"):
        in_b = True
    elif in_b and (ln.startswith("── ") or ln.startswith("━━")):
        break
    if in_b:
        b_block.append(ln)
for ln in b_block:
    print(f"  {ln}")

print(f"\n═══ KHỐI UNHEDGE (verbatim) ═══")
in_u = False; u_block = []
for ln in lines:
    if "UNHEDGE" in ln.upper() or ln.startswith("── U0-BELL") or ln.startswith("── UNHEDGE"):
        in_u = True
    elif in_u and (ln.startswith("── ") or ln.startswith("━━")):
        break
    if in_u:
        u_block.append(ln)
if u_block:
    for ln in u_block:
        print(f"  {ln}")
else:
    print(f"  (không tìm thấy khối UNHEDGE trong body)")

# --- SEND ---
print(f"\n═══ SEND ═══")
ok_send, det = mps.send_telegram(full_msg)
print(f"  ok    : {ok_send}")
print(f"  det   : {det}")
print(f"  chars : {n_chars}")
print(f"  md5   : {body_md5}")

# --- KHÔNG ghi journal, KHÔNG stamp epoch ---
print(f"\n═══ NO STATE MUTATION ═══")
print(f"  KHÔNG gọi preview_journal_append")
print(f"  KHÔNG gọi compute_night_verdict")
print(f"  KHÔNG tăng NIGHT-COUNTER")

sys.exit(0 if ok_send else 1)

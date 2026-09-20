"""J2 · DRY-CHECK target 09-19 · KHÔNG stamp epoch · verify state files không đổi."""
import sys, json, hashlib, os
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

import master_preview_send as mps

TARGET = "2026-09-19"
STATE = Path("/root/Data_back_test/whale_data/data/state")
LOGS = Path("/root/Data_back_test/whale_data/data/logs")

def md5f(p):
    if not Path(p).exists(): return "MISSING"
    return hashlib.md5(Path(p).read_bytes()).hexdigest()

# Snapshot BEFORE
before = {
    "dem0": md5f(STATE / "dem0_lan2_verdict.json"),
    "master_preview.log": md5f(LOGS / "master_preview.log"),
    "master_journal": md5f(LOGS / "master_journal.jsonl"),
    "preview_journal": md5f(LOGS / "preview_journal.jsonl"),
    "epoch_09_19": md5f(STATE / f"verdict_epoch_{TARGET}.json"),
}
print(f"═══ BEFORE dry-check ═══")
for k, v in before.items(): print(f"  {k}: {v}")

print(f"\n═══ CALL compute_night_verdict('{TARGET}', dry=True) ═══")
result = mps.compute_night_verdict(TARGET, dry=True)

# Snapshot AFTER
after = {
    "dem0": md5f(STATE / "dem0_lan2_verdict.json"),
    "master_preview.log": md5f(LOGS / "master_preview.log"),
    "master_journal": md5f(LOGS / "master_journal.jsonl"),
    "preview_journal": md5f(LOGS / "preview_journal.jsonl"),
    "epoch_09_19": md5f(STATE / f"verdict_epoch_{TARGET}.json"),
}

print(f"\n═══ AFTER dry-check ═══")
for k, v in after.items():
    same = "SAME" if before[k] == v else "CHANGED"
    print(f"  {k}: {v} · {same}")

all_same = all(before[k] == after[k] for k in before)
print(f"\n═══ INVARIANT · KHÔNG state đổi: {'PASS' if all_same else 'FAIL'} ═══")

print(f"\n═══ VERDICT DETAIL · target={TARGET} ═══")
print(f"  verdict     : {result['verdict']}")
print(f"  n_full_pair : {result['n_full_pair']}")
print(f"  n_sent      : {result['n_sent']}")
print(f"  missing_legs: {result['missing_legs']}")
print(f"  unknown_sentinels: {result.get('unknown_sentinels', 'N/A')}")

print(f"\n═══ PER-LEG SOURCE ═══")
for r, d in result.get('sent_leg_detail', {}).items():
    src = d.get('source', 'N/A')
    ok = d.get('ok')
    cite = (d.get('cite') or "")[:80]
    print(f"  {r:20s} ok={ok} · source={src} · cite={cite}")

print(f"\n═══ FULL-PAIR STATUS ═══")
for r, d in result.get('full_pair_status', {}).items():
    print(f"  {r:20s} {d}")

# Standing check
print(f"\n═══ STANDING ═══")
ok_standing, reason = mps.check_standing()
print(f"  ok={ok_standing} · {reason}")

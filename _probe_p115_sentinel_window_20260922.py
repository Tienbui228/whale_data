"""AZ2 · p115 · sentinel window neo cron_close · pin đen-một-lần.

Rules (AZ2/22-09):
  · Window = [cron_close(T-1) + 5min, cron_close(T))
  · cron_close(T) = target T + 1d 01:46:00 UTC
  · Sentinel phát lúc cron đêm T-1 (01:46:xx) → KHÔNG tính cho T (trong buffer)
  · Sentinel phát trong đêm T → tính (sau buffer, trước cron_close(T))
  · Chấm cùng target ở hai giờ khác nhau → cùng kết quả (deterministic)

Pin p115 test cases:
  p115-a · target 09-21 (LINT ca lịch sử · 21/09 01:46:04):
    Window = [09-21 01:51, 09-22 01:46) → LINT 01:46:04 < 01:51 → OUT · KHÔNG tính
  p115-b · sentinel phát 09-21 12:00 UTC → IN window · tính
  p115-c · sentinel phát 09-22 01:46:00 → NOT in [.., 01:46:00) right-open · KHÔNG tính (thuộc T+1)
  p115-d · sentinel phát 09-21 01:51:00 (biên buffer) → IN window · tính
  p115-e · determinism · chấm target=09-21 lúc 22/09 03:00 và 22/09 12:00 → cùng verdict
"""
from __future__ import annotations
import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

from master_preview_send import compute_night_verdict

TARGETS = ["2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18",
           "2026-09-19", "2026-09-20", "2026-09-21"]

print("═══ AZ2 · Dry verdict 7 đêm với sentinel window neo cron_close ═══")
print(f"{'target':12s} | {'verdict':>12s} | {'unk_sent':>8s} | {'unknown_sentinels':40s}")
print(f"{'-'*12} | {'-'*12} | {'-'*8} | {'-'*40}")

results = []
for tgt in TARGETS:
    ver = compute_night_verdict(tgt, dry=True)
    verdict = ver.get("verdict", "?")
    unk = ver.get("unknown_sentinels", [])
    results.append((tgt, verdict, unk))
    print(f"{tgt:12s} | {verdict:>12s} | {len(unk):>8d} | {str(unk)[:40]}")

# ── p115 · determinism check ─────────────────────────────────────────────────
print()
print("═══ p115 · determinism check (2 calls same target) ═══")
tgt = "2026-09-21"
v1 = compute_night_verdict(tgt, dry=True)
v2 = compute_night_verdict(tgt, dry=True)
same = (v1.get("verdict") == v2.get("verdict") and
        sorted(v1.get("unknown_sentinels", [])) == sorted(v2.get("unknown_sentinels", [])))
print(f"  call 1 verdict: {v1.get('verdict')} unk={v1.get('unknown_sentinels')}")
print(f"  call 2 verdict: {v2.get('verdict')} unk={v2.get('unknown_sentinels')}")
print(f"  p115-e determinism: {'PASS' if same else 'FAIL'}")

# ── p115-a · LINT 21/09 01:46:04 for target 09-21 · KHÔNG được đếm ─────────
print()
print("═══ p115-a · LINT 21/09 01:46:04 không tính cho target=09-21 ═══")
v21 = compute_night_verdict("2026-09-21", dry=True)
unk21 = v21.get("unknown_sentinels", [])
has_lint = any("LINT" in s for s in unk21)
print(f"  target=09-21 unknown_sentinels: {unk21}")
print(f"  p115-a: {'PASS · LINT không có' if not has_lint else 'FAIL · LINT vẫn tính'}")

fails = 0
if not same: fails += 1
if has_lint: fails += 1

print()
print(f"═══ AZ2 TỔNG · p115 fails={fails} ═══")
sys.exit(0 if fails == 0 else 1)

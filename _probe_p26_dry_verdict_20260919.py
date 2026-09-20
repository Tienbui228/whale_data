"""p26 · pin U5-2 · compute_night_verdict(dry=True) không để lại dấu.

Cases:
  a. Gọi dry → verdict_epoch KHÔNG được tạo/đổi
  b. Gọi thường (dry=False) → có stamp epoch
  c. Gọi dry khi epoch ĐÃ tồn tại → file không đổi 1 byte (md5 + mtime)
"""
import sys, tempfile, hashlib, os, importlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

# Setup tmpdir isolated
tmpdir = Path(tempfile.mkdtemp(prefix="p26_"))
(tmpdir / "data/logs").mkdir(parents=True)
(tmpdir / "data/artifacts").mkdir(parents=True)
(tmpdir / "data/state").mkdir(parents=True)
(tmpdir / "data/export").mkdir(parents=True)
(tmpdir / "tests/harness").mkdir(parents=True)
(tmpdir / "tests/harness/harness_p20_p22_v3_5k.py").write_text("import sys; sys.exit(0)\n", encoding="utf-8")

# Fake artifacts (all 6 pairs present)
for r in ["tg_relay_gom_h", "fresh_digest", "exch_digest", "gom_daily", "phase_map", "watchlist"]:
    (tmpdir / f"data/artifacts/tg_final_{r}_2026-09-15.txt").write_text("body", encoding="utf-8")
    (tmpdir / f"data/artifacts/tg_final_{r}_2026-09-15.jsonl").write_text("{}\n", encoding="utf-8")

(tmpdir / "data/logs/bell_journal.jsonl").write_text("", encoding="utf-8")
(tmpdir / "data/logs/master_preview.log").write_text("", encoding="utf-8")
(tmpdir / "data/logs/tg_relay.log").write_text(f"[2026-09-16T01:20:00+00:00] [SENT] all_ok=True target_date=2026-09-15\n", encoding="utf-8")
(tmpdir / "data/logs/digest_daily_vps.log").write_text(f"[2026-09-16T01:25:00+00:00] [LEG-SENT renderer=fresh_digest snapshot=2026-09-15 md5=aaa111 ts_utc=2026-09-16T01:25:00+00:00]\n[2026-09-16T01:25:01+00:00] [LEG-SENT renderer=exch_digest snapshot=2026-09-15 md5=bbb222 ts_utc=2026-09-16T01:25:01+00:00]\n", encoding="utf-8")
(tmpdir / "data/logs/gom_daily.log").write_text(f"[2026-09-16T01:30:00+00:00] [SENT] gom_daily ok=True target=2026-09-15\n", encoding="utf-8")
(tmpdir / "data/logs/phase_tag.log").write_text(f"[2026-09-16T01:35:00+00:00] [SENT] phase_map ok=True target=2026-09-15\n", encoding="utf-8")
(tmpdir / "data/export/watchlist_cron.log").write_text(f"[2026-09-16T01:40:00+00:00] [SENT] watchlist ok=True target=2026-09-15\n", encoding="utf-8")

import master_preview_send as mps; importlib.reload(mps)
mps.REPO = tmpdir
mps.STATE = tmpdir / "data/state"
mps.LOG_P = tmpdir / "data/logs/master_preview.log"
mps.PREVIEW_JOURNAL = tmpdir / "data/logs/preview_journal.jsonl"
mps.MASTER_JOURNAL = tmpdir / "data/logs/master_journal.jsonl"

TARGET = "2026-09-15"
epoch_p = mps.STATE / f"verdict_epoch_{TARGET}.json"
dem0_p = mps.STATE / "dem0_lan2_verdict.json"
log_p = mps.LOG_P

def snap_state():
    """Trả (epoch_md5, epoch_mtime, dem0_md5, log_md5)."""
    def _md5(p): return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else None
    def _mtime(p): return p.stat().st_mtime_ns if p.exists() else None
    return (_md5(epoch_p), _mtime(epoch_p), _md5(dem0_p), _md5(log_p))


# ── p26-a · dry (không có epoch trước) · KHÔNG được tạo ──
assert not epoch_p.exists(), "setup: epoch phải không tồn tại đầu"
before = snap_state()
r_dry = mps.compute_night_verdict(TARGET, dry=True)
after = snap_state()

p26_a = (not epoch_p.exists()) and (not dem0_p.exists()) and (before[3] == after[3])
print(f"p26-a · dry (epoch chưa có) · epoch không tạo, dem0 không tạo, log không đổi")
print(f"        verdict returned = {r_dry['verdict']} · epoch exists = {epoch_p.exists()} · dem0 exists = {dem0_p.exists()}")
print(f"        → {'PASS' if p26_a else 'FAIL'}\n")


# ── p26-b · thường (không dry) · CÓ stamp epoch + dem0 ──
r_normal = mps.compute_night_verdict(TARGET)
p26_b = epoch_p.exists() and dem0_p.exists()
print(f"p26-b · normal · epoch tạo, dem0 tạo")
print(f"        verdict = {r_normal['verdict']} · epoch exists = {epoch_p.exists()} · dem0 exists = {dem0_p.exists()}")
print(f"        → {'PASS' if p26_b else 'FAIL'}\n")


# ── p26-c · dry (epoch đã tồn tại) · file KHÔNG đổi 1 byte ──
before_c = snap_state()
import time; time.sleep(0.05)
r_dry2 = mps.compute_night_verdict(TARGET, dry=True)
after_c = snap_state()

# Epoch md5 phải giống trước sau
epoch_md5_same = before_c[0] == after_c[0]
epoch_mtime_same = before_c[1] == after_c[1]
# dem0 md5 phải giống (dry không ghi)
dem0_md5_same = before_c[2] == after_c[2]
# log md5 giống (không log sentinel)
log_md5_same = before_c[3] == after_c[3]

p26_c = epoch_md5_same and epoch_mtime_same and dem0_md5_same and log_md5_same
print(f"p26-c · dry sau khi epoch tồn tại · file không đổi 1 byte")
print(f"        epoch md5 same: {epoch_md5_same} · mtime same: {epoch_mtime_same}")
print(f"        dem0 md5 same: {dem0_md5_same} · log md5 same: {log_md5_same}")
print(f"        → {'PASS' if p26_c else 'FAIL'}\n")

fails = sum(1 for p in [p26_a, p26_b, p26_c] if not p)
print(f"═══ p26 · TỔNG 3 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)

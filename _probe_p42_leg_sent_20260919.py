"""p42 · pin H · leg-sent marker · verdict xác định leg bằng bản ghi.

Cases:
  a. Opt-A shift · renderer fresh log LEG-SENT với snapshot=T+1 · verdict target=T
     → leg PHẢI nhận đúng (bằng ts_utc window, không phải target match)
  b. Đổi lịch renderer lần nữa (snapshot=T+2 hoặc T+3) → pin vẫn xanh
  c. LEG-SENT ngoài 25h (cũ) → không nhận
"""
import sys, tempfile, importlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

# Monkey patch REPO for isolated test
tmpdir = Path(tempfile.mkdtemp(prefix="p42_"))
(tmpdir / "data/logs").mkdir(parents=True)
(tmpdir / "data/artifacts").mkdir(parents=True)
(tmpdir / "data/state").mkdir(parents=True)
(tmpdir / "tests/harness").mkdir(parents=True)
(tmpdir / "tests/harness/harness_p20_p22_v3_5k.py").write_text("import sys; sys.exit(0)\n", encoding="utf-8")

# fake full_pair artifacts (all 6 pairs present)
for r in ["tg_relay_gom_h", "fresh_digest", "exch_digest", "gom_daily", "phase_map", "watchlist"]:
    (tmpdir / f"data/artifacts/tg_final_{r}_2026-09-18.txt").write_text("body", encoding="utf-8")
    (tmpdir / f"data/artifacts/tg_final_{r}_2026-09-18.jsonl").write_text("{}\n", encoding="utf-8")

# fake bell_journal empty
(tmpdir / "data/logs/bell_journal.jsonl").write_text("", encoding="utf-8")

# Anchor: cron_close cho target 09-18 = 09-19 01:46 UTC · fresh cron ≈ 09-19 01:25 UTC
# Set LEG-SENT ts = 21 min before cron_close (giả lập fresh chạy đúng lịch)
TARGET_DT = datetime(2026, 9, 18)
CRON_CLOSE = TARGET_DT.replace(tzinfo=timezone.utc) + timedelta(days=1, hours=1, minutes=46)
now = CRON_CLOSE - timedelta(minutes=21)   # 09-19 01:25 UTC

# ── Case a · Opt-A shift snapshot=T+1 · LEG-SENT trong 25h ──
ts_recent = now.isoformat(timespec="seconds")
digest_log_a = f"""[{ts_recent}] [SENT] Fresh-Wallets part=1/1 · ok=True · HTTP 200
[{ts_recent}] [LEG-SENT renderer=fresh_digest snapshot=2026-09-19 md5=abc123def456 ts_utc={ts_recent}]
[{ts_recent}] [SENT] EXCH-BAL part=1/1 · ok=True · HTTP 200
[{ts_recent}] [LEG-SENT renderer=exch_digest snapshot=2026-09-19 md5=def456abc789 ts_utc={ts_recent}]
"""

# Also fake other renderers with SENT markers for target 09-18
tg_relay_content = f"[{ts_recent}] [SENT] all_ok=True target_date=2026-09-18\n"
gom_daily_content = f"[{ts_recent}] [SENT] gom_daily ok=True target=2026-09-18\n"
phase_content = f"[{ts_recent}] [SENT] phase_map ok=True target=2026-09-18\n"
(tmpdir / "data/export").mkdir(exist_ok=True)
watch_content = f"[{ts_recent}] [SENT] watchlist ok=True target=2026-09-18\n"

# Standard master_preview log (empty · no sentinel)
master_log = ""

def setup_env():
    (tmpdir / "data/logs/digest_daily_vps.log").write_text(digest_log_a, encoding="utf-8")
    (tmpdir / "data/logs/tg_relay.log").write_text(tg_relay_content, encoding="utf-8")
    (tmpdir / "data/logs/gom_daily.log").write_text(gom_daily_content, encoding="utf-8")
    (tmpdir / "data/logs/phase_tag.log").write_text(phase_content, encoding="utf-8")
    (tmpdir / "data/export/watchlist_cron.log").write_text(watch_content, encoding="utf-8")
    (tmpdir / "data/logs/master_preview.log").write_text(master_log, encoding="utf-8")

setup_env()

import master_preview_send as mps; importlib.reload(mps)
mps.REPO = tmpdir
mps.STATE = tmpdir / "data/state"
mps.LOG_P = tmpdir / "data/logs/master_preview.log"
mps.PREVIEW_JOURNAL = tmpdir / "data/logs/preview_journal.jsonl"
mps.MASTER_JOURNAL = tmpdir / "data/logs/master_journal.jsonl"

TARGET = "2026-09-18"

result = mps.compute_night_verdict(TARGET)
print(f"═══ p42 · Case a: Opt-A shift snapshot=T+1 · LEG-SENT trong 25h ═══")
print(f"  verdict: {result['verdict']}")
print(f"  n_full: {result['n_full_pair']} · n_sent: {result['n_sent']}")
print(f"  fresh: {result['sent_leg_detail']['fresh_digest']}")
print(f"  exch:  {result['sent_leg_detail']['exch_digest']}")
p42_a = (result['verdict'] == "KHÔNG-KÍCH" and
         result['sent_leg_detail']['fresh_digest']['ok'] and
         result['sent_leg_detail']['exch_digest']['ok'])
print(f"  → PASS' if p42_a else 'FAIL' · leg nhận đúng dù snapshot=T+1 · verdict=KHÔNG-KÍCH")
print(f"  · {'PASS' if p42_a else 'FAIL'}\n")

# ── Case b · shift snapshot=T+3 (đổi lịch xa hơn) · LEG-SENT vẫn trong 25h ──
digest_log_b = f"""[{ts_recent}] [LEG-SENT renderer=fresh_digest snapshot=2026-09-21 md5=xyz111 ts_utc={ts_recent}]
[{ts_recent}] [LEG-SENT renderer=exch_digest snapshot=2026-09-21 md5=xyz222 ts_utc={ts_recent}]
"""
(tmpdir / "data/logs/digest_daily_vps.log").write_text(digest_log_b, encoding="utf-8")
# Reset epoch (delete for fresh compute)
epoch_p = tmpdir / f"data/state/verdict_epoch_{TARGET}.json"
if epoch_p.exists(): epoch_p.unlink()

result_b = mps.compute_night_verdict(TARGET)
p42_b = (result_b['sent_leg_detail']['fresh_digest']['ok'] and
         result_b['sent_leg_detail']['exch_digest']['ok'])
print(f"═══ p42 · Case b: snapshot=T+3 (shift đổi lịch) · vẫn nhận ═══")
print(f"  fresh ok: {result_b['sent_leg_detail']['fresh_digest']['ok']}")
print(f"  exch  ok: {result_b['sent_leg_detail']['exch_digest']['ok']}")
print(f"  · {'PASS' if p42_b else 'FAIL'}\n")

# ── Case c · LEG-SENT ngoài 30h (J1 window nới) → không nhận · ts = cron_close - 36h ──
ts_old = (CRON_CLOSE - timedelta(hours=36)).isoformat(timespec="seconds")
digest_log_c = f"""[{ts_old}] [LEG-SENT renderer=fresh_digest snapshot=2026-09-16 md5=old111 ts_utc={ts_old}]
[{ts_old}] [LEG-SENT renderer=exch_digest snapshot=2026-09-16 md5=old222 ts_utc={ts_old}]
"""
(tmpdir / "data/logs/digest_daily_vps.log").write_text(digest_log_c, encoding="utf-8")
if epoch_p.exists(): epoch_p.unlink()

result_c = mps.compute_night_verdict(TARGET)
p42_c = (not result_c['sent_leg_detail']['fresh_digest']['ok'] and
         not result_c['sent_leg_detail']['exch_digest']['ok'])
print(f"═══ p42 · Case c: LEG-SENT ngoài 30h (36h cũ) · KHÔNG nhận ═══")
print(f"  fresh ok: {result_c['sent_leg_detail']['fresh_digest']['ok']}")
print(f"  exch  ok: {result_c['sent_leg_detail']['exch_digest']['ok']}")
print(f"  · {'PASS' if p42_c else 'FAIL'}\n")

fails = sum(1 for p in [p42_a, p42_b, p42_c] if not p)
print(f"═══ p42 · TỔNG 3 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)

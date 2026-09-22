"""β4 · dry verdict master 6 đêm · HEDGE làm chân watchlist · 6/6.

Backup bell_journal → append HEDGE dry entries (renderer=watchlist, ok=True) →
run compute_night_verdict per target → restore bell_journal (no side-effect).
"""
import sys, os, json, shutil, hashlib, tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

BELL_JOURNAL = _REPO / "data/logs/bell_journal.jsonl"
ART_DIR = _REPO / "data/artifacts"

# Backup bell_journal
backup_p = None
if BELL_JOURNAL.exists():
    backup_p = Path(tempfile.mkdtemp(prefix="bell_backup_")) / "bell_journal.jsonl"
    shutil.copy2(BELL_JOURNAL, backup_p)

from master_preview_send import compute_night_verdict

TARGETS = ["2026-09-16", "2026-09-17", "2026-09-18",
           "2026-09-19", "2026-09-20", "2026-09-21"]

# Append HEDGE dry entries to bell_journal (renderer=watchlist)
def _append_hedge_dry_entries():
    BELL_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with BELL_JOURNAL.open("a", encoding="utf-8") as f:
        for tgt in TARGETS:
            body_p = ART_DIR / f"tg_final_watchlist_{tgt}.txt"
            if not body_p.exists(): continue
            body_md5 = hashlib.md5(body_p.read_bytes()).hexdigest()
            entry = {
                "ts_utc":       ts,
                "target_date":  tgt,
                "renderer":     "watchlist",
                "product":      "hedge_v2",
                "ok":           True,
                "body_md5":     body_md5,
                "message_id":   0,   # dry · no real msg
                "dry":          True,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

try:
    _append_hedge_dry_entries()

    print(f"{'target':12s} | {'verdict':>12s} | {'watch_sent':>10s} | {'source':>15s} | {'body_md5':>14s}")
    print(f"{'-'*12} | {'-'*12} | {'-'*10} | {'-'*15} | {'-'*14}")

    n_ok = 0
    for tgt in TARGETS:
        try:
            ver = compute_night_verdict(tgt, dry=True)
        except Exception as e:
            print(f"{tgt:12s} | ERR: {e}")
            continue
        verdict = ver.get("verdict", "?")
        watch_sent = ver.get("sent_leg_detail", {}).get("watchlist", {})
        ok = watch_sent.get("ok", False)
        src = watch_sent.get("source", "?")
        cite = watch_sent.get("cite", "")[:16]
        print(f"{tgt:12s} | {verdict:>12s} | {str(ok):>10s} | {str(src):>15s} | {cite:>14s}")
        if ok:
            n_ok += 1

    print()
    print(f"═══ TỔNG · watchlist SENT ok (HEDGE làm chân): {n_ok}/{len(TARGETS)} ═══")
    print(f"(Verdict KÍCH ở đêm khác legit — thiếu chân khác, KHÔNG do HEDGE)")
finally:
    # Restore bell_journal
    if backup_p and backup_p.exists():
        shutil.copy2(backup_p, BELL_JOURNAL)
        try: backup_p.parent.rmdir()
        except OSError: pass  # L-66-OK
    else:
        # Original didn't exist — remove appended file
        if BELL_JOURNAL.exists():
            BELL_JOURNAL.unlink()

sys.exit(0 if n_ok == len(TARGETS) else 1)

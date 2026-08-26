#!/usr/bin/env python3
"""[STUB · CHỜ KÝ merge full impl] Re-grade PENDING census — DRY-RUN default.

Per proposals/re_grade_pending_cron_20260828.md (SIGNED 28/08 by operator).
Cron entry: `06 04 * * *` UTC — sau daily-metrics 00:35 + gom_h 01:45 + universe 01:30.

Current state: STUB — chỉ verify latest census + scan PENDING rows đủ tuổi ≥30d.
Real impl chờ scripts/regrade_pending_census.py full với fapi k[4] fresh re-fetch.

Usage:
  python scripts/regrade_pending_census.py            # dry-run default (SẼ ... không ghi)
  python scripts/regrade_pending_census.py --live     # ghi census_63_grades_<today>.csv (chưa impl)
"""
from __future__ import annotations
import sys, io, argparse, csv
from pathlib import Path
from datetime import datetime, timezone
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
LOG_PATH = REPO / "data/logs/regrade_pending.log"
CENSUS_DIR = REPO / "docs/case_files/census_63_grades"


def _log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="Write new census file (default: dry-run)")
    args = ap.parse_args()

    today = datetime.now(timezone.utc).date()
    _log(f"[REGRADE-PENDING · STUB] START · today={today} · mode={'LIVE' if args.live else 'DRY-RUN'}")

    # Find latest census file
    if not CENSUS_DIR.exists():
        _log(f"[SKIP] census_63_grades dir missing: {CENSUS_DIR}")
        return 0

    files = sorted(CENSUS_DIR.glob("census_63_grades_*.csv"))
    if not files:
        _log(f"[SKIP] no census file found")
        return 0

    latest = files[-1]
    _log(f"[INPUT] latest census: {latest.name}")

    # Scan PENDING rows đủ tuổi ≥30d
    with open(latest, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    todo = []
    for r in rows:
        if r.get("grade") != "PENDING": continue
        try:
            fire_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
            age = (today - fire_date).days
            if age >= 30:
                todo.append({"token": r["token"], "date": r["date"], "age": age})
        except Exception:
            continue

    _log(f"[SCAN] PENDING rows: {sum(1 for r in rows if r.get('grade')=='PENDING')} · mature (age≥30d): {len(todo)}")

    if todo:
        _log(f"[MATURE] SẼ re-grade {len(todo)} rows:")
        for r in todo:
            _log(f"  {r['token']:<10} {r['date']} (age={r['age']}d)")

    if args.live:
        _log(f"[LIVE] STUB IMPL — fapi re-fetch + TP/FP compute chưa merge. Exit 0 (no writes).")
    else:
        _log(f"[DRY-RUN] SẼ re-grade {len(todo)} rows · KHÔNG ghi census_63_grades_<today>.csv")

    _log(f"[REGRADE-PENDING · STUB] DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

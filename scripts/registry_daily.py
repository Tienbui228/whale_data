#!/usr/bin/env python3
"""[STUB · CHỜ KÝ merge full impl] Registry phase-2 daily runner — DRY-RUN default.

Per proposals/registry_phase2_cron_deploy_20260828.md (SIGNED 28/08 by operator).
Cron entry: `50 1 * * *` UTC — sau gom_h 01:45 UTC.

Current state: STUB — chỉ verify infrastructure (imports, paths, guard).
Real impl chờ scripts/registry_daily.py full version với §E-R triggers/gates.

Usage:
  python scripts/registry_daily.py            # dry-run default (SẼ ... không ghi)
  python scripts/registry_daily.py --live     # write files + Telegram (chưa impl)
"""
from __future__ import annotations
import sys, io, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
LOG_PATH = REPO / "data/logs/registry_daily.log"


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
                    help="Write files + send Telegram (default: dry-run)")
    ap.add_argument("--date", default="auto",
                    help="Target date YYYY-MM-DD or 'auto' (=yesterday UTC)")
    args = ap.parse_args()

    target = args.date if args.date != "auto" else \
        (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    _log(f"[REGISTRY-DAILY · STUB] START · target={target} · mode={'LIVE' if args.live else 'DRY-RUN'}")

    # Check inputs exist (verify infra path)
    fw_path = REPO / f"data/export/freshwatch_daily_{target[:7]}.csv"
    snap_path = REPO / f"data/state/hedge_watchlist_{target}.json"

    _log(f"[INPUTS] freshwatch: {fw_path.name} exists={fw_path.exists()}")
    _log(f"[INPUTS] snapshot  : {snap_path.name} exists={snap_path.exists()}")

    # §E-R8 guards (stub — no actual data check yet)
    _log(f"[GUARDS §E-R8 stub] reg%_weekpeak (target ≤25%): PLACEHOLDER · MFE_k7 (≥50% wave-2+): PLACEHOLDER")

    if args.live:
        _log(f"[LIVE] STUB IMPL — real §E-R triggers/gates chưa merge. Exit 0 (no writes).")
    else:
        _log(f"[DRY-RUN] SẼ open/close/re-arm N rows (N=0 stub) · KHÔNG ghi CSV · KHÔNG send Telegram")

    _log(f"[REGISTRY-DAILY · STUB] DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

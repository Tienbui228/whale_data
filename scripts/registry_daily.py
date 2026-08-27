#!/usr/bin/env python3
"""[WRAPPER FULL v1 · day-28 build · CHỜ ANALYSIS ký merge] Registry phase-2 daily runner.

Per proposals/registry_phase2_cron_deploy_20260828.md SIGNED operator 28/08.
Wrapper scope (per operator KÝ (i) 29/08): tái dùng lib/registry_events + er8_guards
+ state_store + telegram — CẤM rebuild trigger/re-arm ở đây.

Cron entry: `50 1 * * *` UTC (installed 26/08).

Modes:
  --dry-run (default): scan + compute + log, KHÔNG ghi state store, KHÔNG send Telegram
  --live: full write state + send Telegram (chỉ chạy sau operator ký --live)
"""
from __future__ import annotations
import sys, io, argparse, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from lib.registry_events import (
    window_prefilter_and_detect, _detect_ev, dedup_b_events,
    check_rearm_all, _load_unhedge_cfg,
)
from lib.registry_er8_guards import check_all_guards
from lib.registry_state_store import (
    load_state, save_state, open_row, close_row, mark_ignite,
    update_daily_tracker, mark_rearmed, get_open_rows, get_open_rows_by_week,
)
from lib.registry_telegram import tg_send_registry

LOG_PATH = REPO / "data/logs/registry_daily.log"
STATE_PATH = REPO / "data/state/unhedge_registry_state.json"
FW_UNIVERSE_SIZE = 139


def _log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _fmt_registry_alert(sym, event, detail):
    """Format Telegram khối REGISTRY (per §E-R render doctrine)."""
    lines = [f"⚡ REGISTRY {event} · {sym}"]
    for k, v in detail.items():
        if k in ("history", "detail_expanded"): continue
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="Write state + send Telegram (default: dry-run, chỉ log)")
    ap.add_argument("--date", default="auto",
                    help="Target date YYYY-MM-DD or 'auto' (=yesterday UTC)")
    args = ap.parse_args()

    target = args.date if args.date != "auto" else \
        (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    _log(f"[REGISTRY-DAILY v1 · WRAPPER] START target={target} mode={'LIVE' if args.live else 'DRY-RUN'}")

    # Load cfg + state
    cfg = _load_unhedge_cfg()
    if cfg is None:
        _log(f"[FATAL] unhedge_registry cfg missing in screen_thresholds.yaml"); return 1

    state = load_state(str(STATE_PATH))
    _log(f"[STATE] loaded {len(state)} tokens · {len(get_open_rows(state))} open/re-armed")

    # Data inputs (existence check + log)
    fw_path = REPO / f"data/export/freshwatch_daily_{target[:7]}.csv"
    _log(f"[INPUTS] freshwatch: {fw_path.name} exists={fw_path.exists()}")
    if not fw_path.exists():
        _log(f"[SKIP] freshwatch input missing — abort"); return 0

    # NOTE: Real detection loop would iterate per-token via window_prefilter_and_detect
    # + _detect_ev, then check_rearm_all for open rows. Skeleton below shows wire, actual
    # per-token compute chờ full data load (fw CSV → arr per sym).

    # §E-R8 guards — pre-check (block Telegram if trip)
    open_rows_by_week = get_open_rows_by_week(state)
    guards_pass, guards_detail = check_all_guards(
        alerts=[], klines_by_token={},  # TODO: populate from state history + fapi cache
        open_rows_by_week=open_rows_by_week,
        alerts_by_type_week={},  # TODO: parse telegram log
        pump_events=[], alert_rows=[{"sym": s, "alert_date": r["opened_at"]}
                                     for s, r in state.items()],
        universe_size=FW_UNIVERSE_SIZE,
    )
    _log(f"[§E-R8 GUARDS] all_pass={guards_pass} · action_if_fail={guards_detail.get('action_if_fail')}")
    if not guards_pass:
        _log(f"[BLOCK] Telegram sends blocked, ANALYSIS-ONLY 30d mode")

    # Wrapper skeleton events (real per-token loop TODO — day-29 morning verify)
    events_new = []  # {sym, event, detail}

    # DRY-RUN report
    if not args.live:
        _log(f"[DRY-RUN] SẼ open={sum(1 for e in events_new if e['event'].startswith('E-R1'))} "
             f"· close={sum(1 for e in events_new if e['event'].startswith('E-R4'))} "
             f"· re-arm={sum(1 for e in events_new if e['event'].startswith('E-R4b'))} "
             f"· r4-evidence={sum(1 for e in events_new if 'r4' in e['event'])}")
        _log(f"[DRY-RUN] KHÔNG ghi state · KHÔNG send Telegram")
    else:
        if not guards_pass:
            _log(f"[LIVE-BLOCKED] guards fail → skip writes + sends")
        else:
            # Apply events to state + send Telegram (per event)
            for e in events_new:
                sym, event, detail = e["sym"], e["event"], e["detail"]
                # State mutation via lib
                if event == "E-R1_a":
                    state = open_row(state, sym, target, detail["hedge_start"], detail["hspx"], "E-R1_a")
                elif event == "E-R1_b":
                    state = open_row(state, sym, target, detail["hedge_start"], detail["hspx"], "E-R1_b")
                elif event == "E-R4_close":
                    state = close_row(state, sym, target, detail["reason"])
                elif event == "E-R3_ignite":
                    state = mark_ignite(state, sym, target, detail["px"], detail["oi"])
                elif event == "E-R4b_rearm":
                    state = mark_rearmed(state, sym, target, detail["evidence"])
                # Telegram
                msg = _fmt_registry_alert(sym, event, detail)
                ok, reason = tg_send_registry(sym, event, msg)
                _log(f"[TG] {sym} {event} ok={ok} reason={reason}")
            save_state(state, str(STATE_PATH))
            _log(f"[LIVE] state saved · {len(events_new)} events applied")

    _log(f"[REGISTRY-DAILY v1] DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

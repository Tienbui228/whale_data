"""lib/registry_state_store.py — Registry state store JSON persist.

Per proposals/registry_phase2_cron_deploy_20260828.md SIGNED 28/08.

State schema per token (data/state/unhedge_registry_state.json):
  {
    "SYM": {
      "state": "open" | "closed" | "re-armed",
      "opened_at": "YYYY-MM-DD",
      "closed_at": "YYYY-MM-DD" | None,
      "close_reason": "RE-HEDGED" | "EXPIRED" | None,
      "hedge_start_date": "YYYY-MM-DD",
      "hedge_start_px": float,
      "opened_by": "E-R1_a" | "E-R1_b",
      "ignite_at": "YYYY-MM-DD" | None,
      "ignite_px": float | None,
      "ignite_oi": float | None,
      "local_low_px_since_ignite": float | None,
      "local_low_oi_since_ignite": float | None,
      "days_since_ignite": int | None,
      "rearmed_at": "YYYY-MM-DD" | None,
      "rearm_count": int,
      "history": [{"event": "opened|closed|ignite|rearmed|r4_evidence", "date": "...", "detail": {...}}]
    }
  }

Archive: 30d rolling in data/state/archive/unhedge_registry_state_<YYYYMMDD>.json.
Append-only history log: mọi mutation append record trước ghi lại top-level state.

Consumer (wrapper) reads/writes via this module — KHÔNG trực tiếp mutate JSON file.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from datetime import date as _date, timedelta as _td, datetime, timezone

DEFAULT_PATH = "data/state/unhedge_registry_state.json"
ARCHIVE_DIR = "data/state/archive"
ARCHIVE_KEEP_DAYS = 30


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_state(path=DEFAULT_PATH):
    """Load state JSON. Return {} nếu chưa tồn tại (init empty)."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        # Fail-loud: bad JSON = data corruption, cần audit
        raise RuntimeError(f"registry state store corrupt: {p} ({e})")


def save_state(state, path=DEFAULT_PATH, archive=True):
    """Save state JSON (atomic write via .tmp rename). Archive current before overwrite.

    Args:
      state: dict state (đã mutate).
      path: canonical state store path.
      archive: True → copy current file to archive/ before overwrite (rollback 30d).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Archive current (if exists) before overwrite
    if archive and p.exists():
        arch_dir = Path(ARCHIVE_DIR)
        arch_dir.mkdir(parents=True, exist_ok=True)
        stamp = _date.today().isoformat()
        arch_path = arch_dir / f"{p.stem}_{stamp}.json"
        if not arch_path.exists():  # keep first snapshot per day
            shutil.copy2(p, arch_path)
        _cleanup_archive(arch_dir, keep_days=ARCHIVE_KEEP_DAYS)

    # Atomic write
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8")
    tmp.replace(p)


def _cleanup_archive(arch_dir, keep_days=ARCHIVE_KEEP_DAYS):
    """Remove archive files older than keep_days."""
    cutoff = _date.today() - _td(days=keep_days)
    for f in arch_dir.glob("*.json"):
        try:
            # Extract date from filename suffix
            stem = f.stem
            date_part = stem.rsplit("_", 1)[-1]
            file_date = _date.fromisoformat(date_part)
            if file_date < cutoff:
                f.unlink()
        except Exception:
            pass  # skip malformed filenames


def _init_token_row(sym, opened_at, hedge_start_date, hedge_start_px, opened_by):
    """Init a fresh open row."""
    return {
        "state": "open",
        "opened_at": opened_at,
        "closed_at": None, "close_reason": None,
        "hedge_start_date": hedge_start_date,
        "hedge_start_px": hedge_start_px,
        "opened_by": opened_by,
        "ignite_at": None, "ignite_px": None, "ignite_oi": None,
        "local_low_px_since_ignite": None, "local_low_oi_since_ignite": None,
        "days_since_ignite": None,
        "rearmed_at": None, "rearm_count": 0,
        "history": [{"event": "opened", "date": opened_at,
                      "detail": {"opened_by": opened_by,
                                  "hedge_start_date": hedge_start_date,
                                  "hedge_start_px": hedge_start_px},
                      "recorded_at": _now_iso()}],
    }


def open_row(state, sym, opened_at, hedge_start_date, hedge_start_px, opened_by):
    """Open new row for sym. If already open, KHÔNG reopen (log noop)."""
    if sym in state and state[sym]["state"] == "open":
        state[sym]["history"].append({
            "event": "open_noop", "date": opened_at,
            "detail": {"reason": "already open"}, "recorded_at": _now_iso(),
        })
        return state
    state[sym] = _init_token_row(sym, opened_at, hedge_start_date, hedge_start_px, opened_by)
    return state


def close_row(state, sym, closed_at, reason):
    """Close row (RE-HEDGED | EXPIRED). Reason: str."""
    if sym not in state or state[sym]["state"] == "closed":
        return state  # noop
    state[sym]["state"] = "closed"
    state[sym]["closed_at"] = closed_at
    state[sym]["close_reason"] = reason
    state[sym]["history"].append({
        "event": "closed", "date": closed_at,
        "detail": {"reason": reason}, "recorded_at": _now_iso(),
    })
    return state


def mark_ignite(state, sym, ignite_at, ignite_px, ignite_oi):
    """Mark IGNITE event for sym (E-R3 fires). Initializes local_low trackers."""
    if sym not in state: return state
    state[sym]["ignite_at"] = ignite_at
    state[sym]["ignite_px"] = ignite_px
    state[sym]["ignite_oi"] = ignite_oi
    state[sym]["local_low_px_since_ignite"] = ignite_px
    state[sym]["local_low_oi_since_ignite"] = ignite_oi
    state[sym]["days_since_ignite"] = 0
    state[sym]["history"].append({
        "event": "ignite", "date": ignite_at,
        "detail": {"px": ignite_px, "oi": ignite_oi}, "recorded_at": _now_iso(),
    })
    return state


def update_daily_tracker(state, sym, today, px_today, oi_today):
    """Daily update local_low + days_since_ignite for re-arm r2/r3 checks.
    Called by wrapper mỗi run for each open row có ignite_at."""
    if sym not in state or state[sym].get("ignite_at") is None: return state
    ignite_dt = _date.fromisoformat(state[sym]["ignite_at"])
    state[sym]["days_since_ignite"] = (_date.fromisoformat(today) - ignite_dt).days
    if px_today is not None:
        ll_px = state[sym].get("local_low_px_since_ignite")
        if ll_px is None or px_today < ll_px:
            state[sym]["local_low_px_since_ignite"] = px_today
    if oi_today is not None:
        ll_oi = state[sym].get("local_low_oi_since_ignite")
        if ll_oi is None or oi_today < ll_oi:
            state[sym]["local_low_oi_since_ignite"] = oi_today
    return state


def mark_rearmed(state, sym, rearmed_at, evidence):
    """Mark RE-ARM fire (r1 ∧ r2 ∧ r3). evidence = dict from check_rearm_all."""
    if sym not in state: return state
    state[sym]["state"] = "re-armed"
    state[sym]["rearmed_at"] = rearmed_at
    state[sym]["rearm_count"] = state[sym].get("rearm_count", 0) + 1
    state[sym]["history"].append({
        "event": "rearmed", "date": rearmed_at,
        "detail": evidence, "recorded_at": _now_iso(),
    })
    return state


def append_r4_evidence(state, sym, date, evidence):
    """Append r4 evidence flag (REPORT-ONLY, không mutate state field)."""
    if sym not in state: return state
    state[sym]["history"].append({
        "event": "r4_evidence", "date": date,
        "detail": evidence, "recorded_at": _now_iso(),
    })
    return state


def get_open_rows(state):
    """Return list of syms currently open/re-armed."""
    return [s for s, r in state.items() if r["state"] in ("open", "re-armed")]


def get_open_rows_by_week(state):
    """§E-R8 ② reg%_weekpeak input: {iso_week_str: set(sym)} of active-in-week rows."""
    from collections import defaultdict
    out = defaultdict(set)
    for sym, row in state.items():
        if row["state"] not in ("open", "re-armed"): continue
        opened = _date.fromisoformat(row["opened_at"])
        end = _date.fromisoformat(row["closed_at"]) if row["closed_at"] else _date.today()
        cur = opened
        while cur <= end:
            year, week, _ = cur.isocalendar()
            wk = f"{year}-W{week:02d}"
            out[wk].add(sym)
            cur += _td(days=7)  # step 1 week
    return dict(out)

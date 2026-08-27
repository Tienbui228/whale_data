"""lib/tripwire_e2.py — E2 tripwire runtime counter (GOI-NHE-20260829 SIGNED).

Per gate_defs §3 gói-nhẹ point 3: trần 0.4 alert/token/30d hậu-cooldown.
Vượt trần → flag file + Telegram dòng warning + compose vốn report-only.
KHÔNG tự tắt (per operator "không tự tắt" luật).

State: data/state/tripwire_e2_counter.json — {token: [fire_dates trong 30d rolling]}
Flag:  data/state/tripwire_e2_TRIPPED.flag (present = trip active)
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date as _date, timedelta as _td, datetime, timezone

DEFAULT_COUNTER_PATH = Path("data/state/tripwire_e2_counter.json")
DEFAULT_FLAG_PATH = Path("data/state/tripwire_e2_TRIPPED.flag")
DEFAULT_TRAILING_DAYS = 30
DEFAULT_MAX_ALERT_PER_TOKEN = 0.4


def _load_counter(path):
    p = Path(path)
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}


def _save_counter(state, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)


def record_fire(token, fire_date, counter_path=DEFAULT_COUNTER_PATH,
                 flag_path=DEFAULT_FLAG_PATH,
                 trailing_days=DEFAULT_TRAILING_DAYS,
                 max_per_token=DEFAULT_MAX_ALERT_PER_TOKEN):
    """Record a compose fire (hậu-cooldown) for token @ fire_date.
    Update counter; check trip; return (tripped: bool, cur_rate: float, action_taken: str).
    """
    counter = _load_counter(counter_path)
    fires = counter.get(token, [])
    # Dedup (token, fire_date): re-runs same day must not inflate rate (KÝ 27/08 B3)
    if fire_date not in fires:
        fires.append(fire_date)
    # Purge older than trailing_days
    cutoff = _date.fromisoformat(fire_date) - _td(days=trailing_days)
    fires = sorted({f for f in fires if _date.fromisoformat(f) >= cutoff})
    counter[token] = fires
    _save_counter(counter, counter_path)

    cur_rate = len(fires) / trailing_days
    tripped = cur_rate > max_per_token
    action = ""
    if tripped:
        # Create/touch flag file
        Path(flag_path).parent.mkdir(parents=True, exist_ok=True)
        Path(flag_path).write_text(
            f"[TRIPPED] token={token} fire_date={fire_date} rate={cur_rate:.3f} "
            f"trailing_{trailing_days}d n={len(fires)} threshold={max_per_token}\n"
            f"triggered_at={datetime.now(timezone.utc).isoformat()}\n"
            f"action: report-only + Telegram warn (KHÔNG tự tắt per operator)\n",
            encoding="utf-8")
        action = f"[TRIPWIRE-E2] {token} rate={cur_rate:.3f}>{max_per_token} · flag+Telegram"
    return tripped, cur_rate, action


def is_tripped(flag_path=DEFAULT_FLAG_PATH):
    """Check flag file exists (persistent, KHÔNG tự tắt)."""
    return Path(flag_path).exists()


def read_flag(flag_path=DEFAULT_FLAG_PATH):
    """Read flag contents if exists."""
    p = Path(flag_path)
    return p.read_text(encoding="utf-8") if p.exists() else None

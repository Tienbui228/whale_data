"""lib/registry_telegram.py — Registry Telegram alert với ASSERTION tầng-alert.

Per proposals/registry_phase2_cron_deploy_20260828.md plan update (b) 27/08:
Assertion: trigger event ∧ tg_send trace trong log.
Log format: [YYYY-MM-DDTHH:MM:SSZ] TG-SEND sym=<X> event=<E> ok=<T|F> reason=<...>

Fixture kiểm được: mock TG endpoint → verify log line matches (trigger fire → send call).
Fail-loud: trigger fire + tg_send skip → WARN + counter++ cho §E-R8 ③ miss-audit.
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = Path("data/logs/registry_telegram.log")
_MISSED_COUNTER_PATH = Path("data/state/registry_tg_missed_counter.json")


def _now_iso():
    return datetime.now(timezone.utc).isoformat().split(".")[0] + "Z"


def _log_line(msg, log_path=DEFAULT_LOG_PATH):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{_now_iso()}] {msg}\n")


def _increment_missed_counter(sym, event, reason):
    """§E-R8 ③ tracking: trigger fired but tg_send skip/fail — count."""
    _MISSED_COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if _MISSED_COUNTER_PATH.exists():
        try: data = json.loads(_MISSED_COUNTER_PATH.read_text(encoding="utf-8"))
        except Exception: data = {}
    key = f"{sym}:{event}"
    data[key] = data.get(key, 0) + 1
    data["_last_missed"] = {"sym": sym, "event": event, "reason": reason, "at": _now_iso()}
    _MISSED_COUNTER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def tg_send_registry(sym, event, message, dry_run=False, log_path=DEFAULT_LOG_PATH,
                      tg_token=None, tg_chat_id=None, mock_send=None):
    """Send Telegram registry alert với ASSERTION log line.

    Args:
      sym: token symbol
      event: str event type (E-R1_a, E-R3_ignite, E-R4b_rearm, r4_evidence...)
      message: str formatted Telegram content
      dry_run: True → không call API, chỉ log
      tg_token/tg_chat_id: override env vars (default None → read env)
      mock_send: callable(url, data) → return (status, body) — for fixture testing

    Returns: (ok: bool, reason: str)
    """
    tg_token = tg_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id = tg_chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    if dry_run:
        _log_line(f"TG-SEND sym={sym} event={event} ok=DRY reason=dry-run-mode", log_path)
        return True, "dry-run-mode"

    if not tg_token or not tg_chat_id:
        # Fail-loud: trigger fired but env missing
        reason = "env-missing"
        _log_line(f"TG-SEND sym={sym} event={event} ok=False reason={reason}", log_path)
        _increment_missed_counter(sym, event, reason)
        return False, reason

    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {"chat_id": tg_chat_id, "text": message}
    try:
        if mock_send is not None:
            status, body = mock_send(url, payload)
        else:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as r:
                status = r.status
                body = r.read().decode("utf-8", errors="replace")
        if 200 <= status < 300:
            _log_line(f"TG-SEND sym={sym} event={event} ok=True reason=HTTP-{status}", log_path)
            return True, f"HTTP-{status}"
        else:
            reason = f"HTTP-{status}"
            _log_line(f"TG-SEND sym={sym} event={event} ok=False reason={reason} body={body[:100]}", log_path)
            _increment_missed_counter(sym, event, reason)
            return False, reason
    except Exception as e:
        reason = f"exception-{type(e).__name__}-{str(e)[:60]}"
        _log_line(f"TG-SEND sym={sym} event={event} ok=False reason={reason}", log_path)
        _increment_missed_counter(sym, event, reason)
        return False, reason


def assert_alert_traced(log_path, sym, event, since_ts=None):
    """FIXTURE assertion: verify TG-SEND line exists trong log cho (sym, event) sau since_ts.
    Return (traced: bool, matching_lines: list).
    Used by fixture test: trigger fire → assert_alert_traced returns True.
    """
    if not Path(log_path).exists():
        return False, []
    matches = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            if f"sym={sym}" in line and f"event={event}" in line:
                if since_ts is None or line.startswith(f"[{since_ts}") or line > f"[{since_ts}":
                    matches.append(line.rstrip())
    return len(matches) > 0, matches

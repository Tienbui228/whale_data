"""Minimal Telegram error alert for pipeline jobs.

Usage:
    from whale_collector.alert import telegram_error
    telegram_error("collect_alpha_spot: alpha_config_missing — no symbols collected")

Credentials: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID env vars.
If not set → logs ERROR every call and returns (never blocks pipeline exit).
Dedup: calls within 60s with identical msg are dropped.
"""
from __future__ import annotations

import os
import time
import urllib.error
import urllib.parse
import urllib.request
import structlog

log = structlog.get_logger()

_TELE_API = "https://api.telegram.org/bot{token}/sendMessage"
_last_sent: dict[str, float] = {}  # msg_hash → timestamp
_DEDUP_WINDOW = 60  # seconds


def telegram_error(msg: str) -> None:
    """Send msg to Telegram error channel. Silent on all failures."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.error("telegram_alert_no_credentials",
                  hint="Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env")
        return

    now = time.monotonic()
    key = msg[:120]
    if now - _last_sent.get(key, 0) < _DEDUP_WINDOW:
        return
    _last_sent[key] = now

    url = _TELE_API.format(token=token)
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": f"[whale_data ERROR]\n{msg}"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
        log.info("telegram_alert_sent", msg=msg[:80])
    except (urllib.error.URLError, OSError) as exc:
        log.warning("telegram_alert_failed", error=str(exc))

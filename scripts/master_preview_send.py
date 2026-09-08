"""MASTER-PREVIEW send · V3.5i · REV10 item 2.

Standing conditions (auto-check before send):
  1. data/state/dem0_lan2_verdict.json == "KHÔNG-KÍCH"
  2. data/state/demo5_sent.marker exists (dated same-day or day-before)
  3. data/state/harness_labellint.marker exists (both xanh)

Sends prefix `[MASTER-PREVIEW đêm N/2]` where N/2 = counter file.
Target = TG_CHAT_ID_DAILY env var (or config).
Counter: đêm 1/2 = 09→10 · 10→11/09.

Operator veto: `data/state/preview_veto.marker` exists → NO SEND.
"""
from __future__ import annotations
import os, sys, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.parse

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
STATE = REPO / "data/state"
LOG_P = REPO / "data/logs/master_preview.log"

STANDING_FILES = {
    "dem0_verdict": STATE / "dem0_lan2_verdict.json",
    "demo5_marker": STATE / "demo5_sent.marker",
    "harness_lint_marker": STATE / "harness_labellint.marker",
    "veto_marker": STATE / "preview_veto.marker",
}
COUNTER_FILE = STATE / "master_preview_counter.json"


def _log(msg):
    LOG_P.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_P.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg, file=sys.stderr)


def check_standing() -> tuple[bool, str]:
    """Return (ok_to_send, reason)."""
    if STANDING_FILES["veto_marker"].exists():
        return (False, "VETO marker present · operator dừng preview")
    if not STANDING_FILES["dem0_verdict"].exists():
        return (False, "đêm-0 lần-2 verdict chưa có file")
    try:
        v = json.loads(STANDING_FILES["dem0_verdict"].read_text(encoding="utf-8"))
        if v.get("verdict") != "KHÔNG-KÍCH":
            return (False, f"đêm-0 verdict = {v.get('verdict')} · cần KHÔNG-KÍCH")
    except Exception as e:
        return (False, f"dem0_verdict parse error: {e}")
    if not STANDING_FILES["demo5_marker"].exists():
        return (False, "DEMO-5 sent marker chưa có")
    if not STANDING_FILES["harness_lint_marker"].exists():
        return (False, "harness/label-lint xanh marker chưa có")
    return (True, "standing OK · 4 điều kiện đạt")


def _load_counter() -> dict:
    if not COUNTER_FILE.exists():
        return {"night_index": 0, "total_nights": 2, "started_at": None}
    try:
        return json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except:
        return {"night_index": 0, "total_nights": 2}


def _save_counter(c):
    COUNTER_FILE.write_text(json.dumps(c, indent=2), encoding="utf-8")


def _increment_counter() -> tuple[int, int]:
    c = _load_counter()
    c["night_index"] = int(c.get("night_index", 0)) + 1
    if c.get("started_at") is None:
        c["started_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save_counter(c)
    return (c["night_index"], int(c.get("total_nights", 2)))


def build_body() -> str | None:
    """Call digest_summary_v2.build_v2_digest for yesterday target."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from digest_summary_v2 import build_v2_digest
    except Exception as e:
        _log(f"IMPORT digest_summary_v2 fail: {e}")
        return None
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    try:
        body = build_v2_digest(yesterday)
        return body
    except Exception as e:
        _log(f"build_v2_digest fail: {e}")
        return None


def send_telegram(text: str) -> bool:
    """Send via TG_CHAT_ID_DAILY."""
    bot = os.getenv("TG_BOT_TOKEN")
    chat = os.getenv("TG_CHAT_ID_DAILY")
    if not bot or not chat:
        _log(f"[N/A-ERROR] missing TG_BOT_TOKEN or TG_CHAT_ID_DAILY env")
        return False
    url = f"https://api.telegram.org/bot{bot}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            ok = r.status == 200
        return ok
    except Exception as e:
        _log(f"send fail: {e}")
        return False


def main():
    ok, reason = check_standing()
    _log(f"standing_check: ok={ok} · {reason}")
    if not ok:
        _log("SKIP send · standing not met")
        return 0
    body = build_body()
    if body is None:
        _log("SKIP send · build_body failed")
        return 1
    n, total = _increment_counter()
    prefix = f"[MASTER-PREVIEW đêm {n}/{total}]\n"
    full_msg = prefix + body
    _log(f"about to send · night {n}/{total} · body_size={len(body)}")
    ok_send = send_telegram(full_msg)
    _log(f"[SENT] master_preview ok={ok_send} night={n}/{total} hash={hashlib.md5(full_msg.encode()).hexdigest()[:12]}")
    return 0 if ok_send else 1


if __name__ == "__main__":
    sys.exit(main())

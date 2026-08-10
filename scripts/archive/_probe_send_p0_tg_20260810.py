"""Send P0 reconcile summary to Telegram.

data-source: gom_state.json (VPS) + agent_log.md (local)
machine: local (TG env from .env)
date-range: 2026-08-10
code-commit: see git log
"""
from __future__ import annotations
import sys, io, os, json, urllib.request, urllib.parse
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")
_env = ROOT / ".env"
if _env.exists():
    for ln in _env.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, _, v = ln.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def tg_send(text: str) -> bool:
    if not TG_TOKEN or not TG_CHAT_ID:
        print("WARN: TG creds missing"); return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode())
            return bool(resp.get("ok"))
    except Exception as exc:
        print(f"TG fail: {exc}"); return False

# P0 reconcile message
p0_msg = """📋 P0 RECONCILE — 2026-08-10

NGUYÊN NHÂN:
• cron 08-08 chạy gom_scan full-rebuild (không incremental)
• FF 08-01: A3 slope = 0.7001/0.6093 = 1.149 ≈ 1.15 (boundary)
• Full-rebuild floating-point flip → FF chain không mở được
• 17 token lệch trạng thái (backup 59 open vs corrupt 44 open)

ĐÃ LÀM (08-10):
✅ Cron DISABLED ngay khi phát hiện
✅ Backup bc3f8c35 (59 open) restore → verify md5
✅ gom_scan.py → INCREMENTAL (§8.2): cron chỉ append, không rebuild
  - last_eval_date track per-token
  - --full-rebuild CHỈ với GOM_ALLOW_FULL_REBUILD=1 (tường minh)
  - assert trong run_gom_daily.py: cron KHÔNG thể gọi --full-rebuild
✅ Replay incremental 08-08 → 08-09 trên backup sạch
✅ Cron RE-ENABLED (01:25 UTC, incremental §8.2)

ANCHOR CHECK (3/3 PASS):
• FF: chain_open=True, start=08-01, Q1=$1.99M, last_eval=08-09 ✅
• PARTI: chain_open=False, close=07-11 ✅
• BANK: chain_open=False, close=07-14, retro=07-16 (47% drop) ✅

TRẠNG THÁI SAU REPLAY:
• Scanned (fw139): 13 open, 126 closed, last_eval=08-09
• Legacy backup: 43 open (không trong fw filter, giữ nguyên)
• Tổng state: 527 tokens / 56 open

NGÀY MAI: cron chạy 01:25 UTC, incremental 08-10 → verify md5 closed-chapters BẤT ĐỘNG"""

ok = tg_send(p0_msg)
print(f"TG send: {'OK' if ok else 'FAIL'}")

"""send_manual.py · BB2 · gửi tay bản tin theo kênh CHỈ ĐỊNH · assert chat.id khớp.

Từ nay MỌI gửi tay qua script này. Không dùng ad-hoc urllib nữa.

Args:
  --channel {master,hedge,gom}   BẮT BUỘC · không mặc định
  --body-file <path>             file body (UTF-8) · prefix tự thêm
  --target <YYYY-MM-DD>          target date (dùng cho prefix)
  --prefix <str>                 override prefix (default "[GỬI TAY · target=<T>]\\n")
  --parse-mode {HTML,plain}      default HTML cho master · plain cho hedge/gom
  --dry-run                      chỉ tính md5 + hiển thị · không gửi

Channel → env mapping:
  master → TG_BOT_TOKEN (fallback TELEGRAM_BOT_TOKEN) · TG_CHAT_ID_DAILY (từ /root/.env_tg)
  hedge  → TELEGRAM_BOT_TOKEN · TELEGRAM_CHAT_ID (từ .env)
  gom    → TELEGRAM_BOT_TOKEN · TELEGRAM_CHAT_ID (từ .env · cùng chat như hedge)

Assert:
  · chat.id trong TG response == expected chat_id → PASS
  · lệch → RED · exit 1 · không journal · không epoch

State md5 verify:
  · Trước/sau send · các file: dem0_verdict · master_journal · preview_epoch
    · bell_journal · master_preview.log · hedge_v2_journal
  · Bất kỳ file nào CHANGED → cảnh báo (nhưng không fail · admin xem)
"""
from __future__ import annotations
import argparse, os, sys, hashlib, json
import urllib.request, urllib.parse
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

CHANNEL_MAP = {
    "master": {
        "bot_env":   ["TG_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"],
        "chat_env":  "TG_CHAT_ID_DAILY",
        "parse_mode_default": "HTML",
    },
    "hedge": {
        "bot_env":   ["TELEGRAM_BOT_TOKEN"],
        "chat_env":  "TELEGRAM_CHAT_ID",
        "parse_mode_default": "plain",
    },
    "gom": {
        "bot_env":   ["TELEGRAM_BOT_TOKEN"],
        "chat_env":  "TELEGRAM_CHAT_ID",
        "parse_mode_default": "plain",
    },
}

STATE_FILES = [
    _REPO / "data/state/dem0_lan2_verdict.json",
    _REPO / "data/state/master_preview_journal.jsonl",
    _REPO / "data/state/preview_epoch.marker",
    _REPO / "data/logs/bell_journal.jsonl",
    _REPO / "data/logs/master_preview.log",
    _REPO / "data/logs/hedge_v2_journal.jsonl",
]


def _load_envs():
    """Load .env (repo) + /root/.env_tg (master creds)."""
    for f in [_REPO / ".env", Path("/root/.env_tg")]:
        if not f.exists(): continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def _md5_state():
    out = {}
    for p in STATE_FILES:
        if p.exists():
            out[p.name] = (hashlib.md5(p.read_bytes()).hexdigest(), p.stat().st_size)
        else:
            out[p.name] = ("ABSENT", 0)
    return out


def main():
    ap = argparse.ArgumentParser(description="Gửi tay bản tin đúng kênh (BB2)")
    ap.add_argument("--channel", required=True, choices=["master", "hedge", "gom"],
                    help="Kênh đích · BẮT BUỘC · không mặc định")
    ap.add_argument("--body-file", required=True, help="File chứa body (UTF-8)")
    ap.add_argument("--target", required=True, help="Target date YYYY-MM-DD")
    ap.add_argument("--prefix", default=None,
                    help="Prefix override (default '[GỬI TAY · target=<T>]')")
    ap.add_argument("--parse-mode", choices=["HTML", "plain"], default=None,
                    help="parse_mode override (default per channel)")
    ap.add_argument("--dry-run", action="store_true", help="Không gửi · chỉ tính md5")
    args = ap.parse_args()

    _load_envs()
    ch_cfg = CHANNEL_MAP[args.channel]

    # Resolve bot token (multiple fallback keys)
    bot = None
    for k in ch_cfg["bot_env"]:
        v = os.environ.get(k)
        if v: bot = v; break
    chat = os.environ.get(ch_cfg["chat_env"])
    parse_mode = args.parse_mode or ch_cfg["parse_mode_default"]

    if not bot or not chat:
        print(f"ERROR: env missing · bot={bool(bot)} · chat_env={ch_cfg['chat_env']}={bool(chat)}")
        sys.exit(1)

    # Load body
    body_p = Path(args.body_file)
    if not body_p.exists():
        print(f"ERROR: body file missing: {body_p}"); sys.exit(1)
    body = body_p.read_text(encoding="utf-8")
    prefix = args.prefix if args.prefix is not None else f"[GỬI TAY · target={args.target}]\n"
    full_msg = prefix + body
    body_md5 = hashlib.md5(body.encode()).hexdigest()[:12]
    full_md5 = hashlib.md5(full_msg.encode()).hexdigest()[:12]

    print(f"═══ send_manual · channel={args.channel} · target={args.target} ═══")
    print(f"body_file:    {body_p}")
    print(f"body_md5:     {body_md5} · {len(body)} chars")
    print(f"prefix:       {prefix.strip()}")
    print(f"full_md5:     {full_md5} · {len(full_msg)} chars")
    print(f"channel:      {args.channel}")
    print(f"chat_env:     {ch_cfg['chat_env']} · expected chat_id=...{chat[-8:]}")
    print(f"bot:          ...{bot[-8:]}")
    print(f"parse_mode:   {parse_mode}")

    # md5 BEFORE
    md5_before = _md5_state()

    if args.dry_run:
        print()
        print("═══ DRY-RUN · KHÔNG gửi ═══")
        sys.exit(0)

    # Send
    url = f"https://api.telegram.org/bot{bot}/sendMessage"
    payload = {"chat_id": chat, "text": full_msg,
               "disable_web_page_preview": "true"}
    if parse_mode == "HTML":
        payload["parse_mode"] = "HTML"
    data = urllib.parse.urlencode(payload).encode("utf-8")
    print()
    print(f"→ Sending ...")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            resp_body = r.read().decode()
            resp = json.loads(resp_body)
            ok = bool(resp.get("ok"))
            msg_id = resp.get("result", {}).get("message_id")
            chat_id_resp = resp.get("result", {}).get("chat", {}).get("id")
    except Exception as e:
        print(f"  SEND FAIL: {e}"); sys.exit(1)

    # Verify chat.id
    chat_id_resp_str = str(chat_id_resp) if chat_id_resp is not None else ""
    chat_match = chat_id_resp_str == str(chat)
    print(f"  ok={ok} · msg_id={msg_id} · chat_id_resp=...{chat_id_resp_str[-8:] if chat_id_resp_str else '?'}")
    print()
    if not chat_match:
        print(f"⛔ CHANNEL MISMATCH · expected chat_id={chat} · got={chat_id_resp}")
        print(f"⛔ Gửi tay ĐỎ · không dùng bản tin này · điều tra .env vs .env_tg")
        sys.exit(1)
    print(f"✓ chat_id verified: {chat_id_resp_str[-8:]} == {chat[-8:]}")

    # md5 AFTER
    md5_after = _md5_state()
    changed = []
    for name in sorted(md5_before.keys()):
        b, _ = md5_before[name]
        a, _ = md5_after[name]
        if b != a: changed.append(name)
    if changed:
        print(f"⚠ state changed: {changed} · admin verify — send_manual không được ghi state file")
    else:
        print(f"✓ state md5 SAME 6/6 file (no side-effect)")

    sys.exit(0 if (ok and chat_match) else 1)


if __name__ == "__main__":
    main()

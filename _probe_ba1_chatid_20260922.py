"""BA1 · so chat_id giữa AY1 script (TELEGRAM_CHAT_ID) và master (TG_CHAT_ID_DAILY).

Nếu KHÁC → msg_id=8852 đã gửi sai kênh · phải gửi lại đúng kênh master.
"""
import os, sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

# Reset + load both env files
os.environ.pop("TELEGRAM_CHAT_ID", None)
os.environ.pop("TG_CHAT_ID_DAILY", None)
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
os.environ.pop("TG_BOT_TOKEN", None)

for f in ["/root/Data_back_test/whale_data/.env", "/root/.env_tg"]:
    if not os.path.exists(f): continue
    for line in open(f).read().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            k = k.strip(); v = v.strip()
            os.environ.setdefault(k, v)

c_ay1 = os.environ.get("TELEGRAM_CHAT_ID", "?")
c_master = os.environ.get("TG_CHAT_ID_DAILY", "?")
tok_ay1 = os.environ.get("TELEGRAM_BOT_TOKEN", "?")
tok_master = os.environ.get("TG_BOT_TOKEN", "?")

def tail(s): return f"...{s[-8:]}" if len(s) > 8 else s

print(f"TELEGRAM_CHAT_ID (AY1 · watchlist · gom):   {tail(c_ay1)}")
print(f"TG_CHAT_ID_DAILY (master_preview_send):     {tail(c_master)}")
print(f"SAME chat_id: {c_ay1 == c_master}")
print()
print(f"TELEGRAM_BOT_TOKEN (AY1):                   {tail(tok_ay1)}")
print(f"TG_BOT_TOKEN (master):                      {tail(tok_master)}")
print(f"SAME bot token: {tok_ay1 == tok_master}")

if c_ay1 != c_master:
    print()
    print("⚠ BA1 · msg_id=8852 gửi vào chat KHÁC master channel")
    print(f"→ phải gửi lại đúng kênh: TG_CHAT_ID_DAILY (…{c_master[-8:]}) với bot TG_BOT_TOKEN")

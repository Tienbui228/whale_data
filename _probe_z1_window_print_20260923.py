"""Z1 · IN từ CODE các biến cửa sổ + regex (không tính tay)."""
import sys, os
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

# Reproduce master_preview_send.py:463-474 window logic (giữ nguyên constants)
_CRON_HOUR = 1; _CRON_MIN = 46; _CRON_BUFFER_MIN = 5

for tgt_str in ["2026-09-21", "2026-09-22", "2026-09-24"]:
    tgt_d = datetime.strptime(tgt_str, "%Y-%m-%d").date()
    cron_close_T = datetime.combine(tgt_d + timedelta(days=1),
                                     datetime.strptime(f"{_CRON_HOUR:02d}:{_CRON_MIN:02d}", "%H:%M").time(),
                                     tzinfo=timezone.utc)
    cron_close_T_minus_1 = cron_close_T - timedelta(days=1)
    window_start = cron_close_T_minus_1 + timedelta(minutes=_CRON_BUFFER_MIN)
    window_end   = cron_close_T + timedelta(minutes=_CRON_BUFFER_MIN)
    print(f"target={tgt_str}")
    print(f"  cron_close(T)      = {cron_close_T.isoformat()}")
    print(f"  cron_close(T-1)    = {cron_close_T_minus_1.isoformat()}")
    print(f"  _window_start      = {window_start.isoformat()}")
    print(f"  _window_end        = {window_end.isoformat()}")
    print()

# Print master log_map watchlist regex (line 362)
target_example = "2026-09-22"
watchlist_pat = rf"\[SENT\] watchlist ok=True.*target={target_example}"
print(f"master log_map['watchlist'] regex (master_preview_send.py:362):")
print(f"  path = data/export/watchlist_cron.log")
print(f"  pat  = {watchlist_pat!r}")

# Print bell_journal filter (line 344-346)
print()
print(f"master bell_journal filter (master_preview_send.py:344-346):")
print(f"  e['renderer'] == 'watchlist' AND e['target_date'] == target AND e['ok'] == True")

# Print full_pair check (line 323-329)
print()
print(f"master full_pair check (master_preview_send.py:323-329):")
print(f"  txt   = data/artifacts/tg_final_watchlist_<T>.txt")
print(f"  jsonl = data/artifacts/tg_final_watchlist_<T>.jsonl")
print(f"  Both must exist → status = {{txt: size, jsonl_rows: count}}")
print(f"  Either missing → status = {{missing: True}}")

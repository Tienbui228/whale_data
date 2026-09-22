import sys, json
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK
from master_preview_send import compute_night_verdict

v = compute_night_verdict("2026-09-21", dry=True)
print(json.dumps(v, ensure_ascii=False, indent=2, default=str)[:3000])

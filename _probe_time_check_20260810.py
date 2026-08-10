"""_probe_time_check_20260810.py — print current UTC time."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import datetime, timezone
NOW = datetime.now(timezone.utc)
print(NOW.strftime("%H:%M UTC"))
print(f"gate_btw={'PASS' if (NOW.hour>12 or (NOW.hour==12 and NOW.minute>=1)) else 'WAIT'}")
print(f"gate_on={'PASS' if (NOW.hour>13 or (NOW.hour==13 and NOW.minute>=2)) else 'WAIT'}")

"""AX1 · chứng minh HEDGE_V2 flag đọc được dưới môi trường cron (env -i)."""
import sys, os
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

before = os.environ.get("HEDGE_V2", "UNSET")
print(f"HEDGE_V2 BEFORE import watchlist_daily: {before}")

import watchlist_daily   # triggers .env load at module top (lines 21-27)

after = os.environ.get("HEDGE_V2", "UNSET")
print(f"HEDGE_V2 AFTER  import watchlist_daily: {after}")

# Verify the exact code branch that reads flag
import inspect
src = inspect.getsource(watchlist_daily.main)
if "os.environ.get(\"HEDGE_V2\", \"0\") == \"1\"" in src:
    print("FLAG-READ code: os.environ.get(\"HEDGE_V2\", \"0\") == \"1\" · line 666")
else:
    print("FLAG-READ code: NOT FOUND · unexpected")

# Branch simulation
_hedge_v2 = os.environ.get("HEDGE_V2", "0") == "1"
print(f"BRANCH TAKEN: {'HEDGE_V2 path' if _hedge_v2 else 'OLD watchlist v1.4 path'}")

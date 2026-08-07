#!/usr/bin/env python3
"""Collector polling gap — read repair_gaps.py + propose fix. READ-ONLY."""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=30):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

# Read repair_gaps.py
print("=== repair_gaps.py ===")
out, _, _ = ssh(f"cat {BASE}/scripts/repair_gaps.py")
print(out[:3000])

# Check if repair_gaps.py has been run / is in cron
print("\n=== repair_gaps.py in cron? ===")
out2, _, _ = ssh("crontab -l 2>/dev/null | grep repair")
print(out2 or "(not in crontab)")

# Funding collector schedule analysis
print("\n=== SCHEDULE ANALYSIS: coverage per interval type ===")
analysis_py = """
# Funding collector: 10 0,8,16 * * * (cron) = runs at 00:10, 08:10, 16:10 UTC
# lookback_h = 16h → window = [now - 16h, now]
#
# Coverage analysis for 4h-interval symbols (settlements at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC):
#
# 00:10 poll window: [prev-day 08:10, today 00:10]
#   Settlements captured from TODAY: 00:00 (fundingTime 00:00:00.Xms > startTime 08:10 prev day) ✓
#   Note: 00:00 settlement fundingTime ~= 00:00:00.01x UTC
#
# 08:10 poll window: [prev-day 16:10, today 08:10]
#   Settlements: 04:00, 08:00 ✓ (04:00 and 08:00 are within window)
#   Note: 00:00 also captured here (lookback covers it) — dedup keeps one
#
# 16:10 poll window: [today 00:10, today 16:10]
#   Settlements: 04:00 (if fundingTime > 00:10), 08:00, 12:00, 16:00 ✓
#   Note: 00:00 (00:00:01 < 00:10) → MISSED by 16:10 poll, covered by 00:10
#
# NEXT DAY 00:10 poll window: [yesterday 08:10, today 00:10]
#   Captures yesterday 20:00 settlement ✓
#
# CONCLUSION: For 4h interval, all 6 settlements ARE covered across the 3 daily polls
#             (20:00 is covered by next-day's 00:10 poll, written to yesterday's date partition)
#
# ROOT CAUSE of BANK 27/07 fn=1:
#   BANKUSDT was likely NOT in the universe at the time of the 07-27 00:10, 08:10, 16:10 polls
#   First poll that included BANK: 07-28 00:10 (lookback covers 07-27 08:10 onward)
#   → Only captures 07-27 12:00, 16:00, 20:00 — BUT these 3 should give fn=3, not fn=1
#
#   Alternative: BANK was in universe but fapi returned 1 result (BANK newly listed on 07-27?)
#   Binance BANK perp listing date: need to verify
#
# CURRENT STATE post-regen: fn=6 ✓ (store now has all 6, regen reads store correctly)
#
# LONG-TERM FIX:
#   Option A: Add repair_gaps.py as weekly cron to backfill any missed settlements
#   Option B: Change collect_funding.py to use cursor (since_last_ts) instead of fixed lookback
#   Option A is safer (no code change to hot path)

print('Collector design: 3 polls/day (00:10, 08:10, 16:10) with 16h lookback')
print('Coverage: sufficient for 8h-interval symbols; 4h-interval also covered via dedup')
print('Root cause of BANK 27/07: universe addition timing (BANK not in universe at 07-27 poll times)')
print()
print('Proposed fix: add repair_gaps.py as weekly cron (e.g., Sunday 02:00 UTC)')
print('  - repair_gaps.py backfills any missed settlements retroactively')
print('  - Zero change to hot path (collect_funding.py)')
print('  - Until repair_gaps.py is scheduled, manual backfill is the fallback')
"""
ssh("cat > /tmp/analysis.py << 'AEOF'\n" + analysis_py + "\nAEOF")
out3, _, _ = ssh("python3 /tmp/analysis.py 2>&1")
print(out3)

# Check BANKUSDT listing date on Binance perp
print("\n=== BANKUSDT perp listing date (fapi) ===")
listing_py = """
import urllib.request, json
url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
resp = urllib.request.urlopen(url, timeout=20)
info = json.loads(resp.read())
for sym in info['symbols']:
    if sym['symbol'] == 'BANKUSDT':
        print('BANKUSDT onboardDate:', sym.get('onboardDate', 'N/A'))
        print('BANKUSDT status:', sym.get('status'))
        print('BANKUSDT deliveryDate:', sym.get('deliveryDate', 'N/A'))
        print('BANKUSDT listingType:', sym.get('listingType', 'N/A'))
        print('Full:', {k:v for k,v in sym.items() if k in ['symbol','onboardDate','status','fundingIntervalHours','deliveryDate']})
        break
"""
ssh("cat > /tmp/listing.py << 'LEOF'\n" + listing_py + "\nLEOF")
out4, _, _ = ssh("python3 /tmp/listing.py 2>&1", timeout=30)
print(out4 or "(fapi timeout)")

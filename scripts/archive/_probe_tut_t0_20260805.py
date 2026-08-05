"""T0: Verify TUT pos_r 05/08 fn=6 + funding + gLSR from freshwatch export."""
import subprocess
import sys
import json
from datetime import datetime

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=20):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.stderr.strip()

print("=" * 60)
print(f"T0 CHECK — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
print("=" * 60)

# Check 1: VPS time + export file existence
print("\n[1] VPS time + daily export status")
out, err = ssh("date -u && ls -la /root/Data_back_test/whale_data/data/daily_2026*.csv 2>/dev/null || echo NO_EXPORT")
print(out)
if err:
    print("ERR:", err[:200])

# Check 2: TUT row in latest export — look for 2026-08-05 row
print("\n[2] TUT row in daily export (grep 2026-08-05)")
out, err = ssh("ls /root/Data_back_test/whale_data/data/daily_2026*.csv 2>/dev/null | tail -1 | xargs -I{} grep -E 'TUT.*2026-08-05|2026-08-05.*TUT' {} 2>/dev/null | head -5 || echo NO_ROW")
print(out if out else "NO OUTPUT")
if err:
    print("ERR:", err[:200])

# Check 3: Look for the export more broadly
print("\n[3] Find daily export files on VPS")
out, err = ssh("find /root/Data_back_test -name 'daily_2026*.csv' -o -name 'snapshot_*.csv' 2>/dev/null | head -10")
print(out if out else "NONE FOUND")

# Check 4: Look at freshwatch export path
print("\n[4] Check freshwatch P1 screener output path")
out, err = ssh("ls /root/Data_back_test/whale_data/data/ 2>/dev/null")
print(out if out else "NO DATA DIR")

# Check 5: Any CSV with TUT data updated today
print("\n[5] CSV files modified in last 12h on VPS")
out, err = ssh("find /root/Data_back_test -name '*.csv' -newer /root/Data_back_test/whale_data/data/raw/.keep 2>/dev/null | head -10 || find /root/Data_back_test -name '*.csv' -mmin -720 2>/dev/null | head -10")
print(out if out else "NONE")

# Check 6: Check VPS for any TUTUSDT freshwatch
print("\n[6] Latest TUTUSDT data on VPS")
out, err = ssh("find /root/Data_back_test -name '*TUTUSDT*' -o -name '*tut*' 2>/dev/null | head -10")
print(out if out else "NONE")

# Fallback: Pull from fapi directly to get latest TUT pos_r proxy
print("\n[7] fapi TUTUSDT latest OI + funding (as pos_r proxy)")
import urllib.request
import json as _json

try:
    url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=TUTUSDT"
    with urllib.request.urlopen(url, timeout=10) as r:
        d = _json.loads(r.read())
    print(f"  markPrice:    {d.get('markPrice','?')}")
    print(f"  lastFundingRate: {d.get('lastFundingRate','?')}")
    print(f"  nextFundingTime: {d.get('nextFundingTime','?')}")
    print(f"  time: {d.get('time','?')}")
except Exception as e:
    print(f"  fapi error: {e}")

# Latest OI
try:
    url = "https://fapi.binance.com/fapi/v1/openInterest?symbol=TUTUSDT"
    with urllib.request.urlopen(url, timeout=10) as r:
        d = _json.loads(r.read())
    oi = float(d.get('openInterest', 0))
    px_ref = 0.02403
    oi_usd = oi * px_ref
    print(f"  OI tokens:    {oi:,.0f}")
    print(f"  OI USD @{px_ref}: ${oi_usd/1e6:.3f}M")
    print(f"  time: {d.get('time','?')}")
except Exception as e:
    print(f"  OI error: {e}")

# Latest funding rates (most recent 3)
try:
    url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=TUTUSDT&limit=3"
    with urllib.request.urlopen(url, timeout=10) as r:
        fds = _json.loads(r.read())
    print(f"\n  Latest funding rates:")
    for fd in fds:
        ts = datetime.utcfromtimestamp(fd['fundingTime']/1000).strftime('%m/%d %H:%M')
        print(f"    {ts}: {float(fd['fundingRate']):.6f}")
except Exception as e:
    print(f"  funding error: {e}")

print("\n" + "=" * 60)
print("DONE")

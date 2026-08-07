#!/usr/bin/env python3
"""Count actual funding settlement rows for BANK 27/07 in VPS parquet store.
READ-ONLY.
"""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=40):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

py_body = (
    "import pandas as pd\n"
    "from datetime import datetime, timezone\n"
    "\n"
    "def day_ms(d):\n"
    "    dt = datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc)\n"
    "    s = int(dt.timestamp() * 1000)\n"
    "    return s, s + 86400000 - 1\n"
    "\n"
    "df7 = pd.read_parquet('/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-07/part-0.parquet')\n"
    "df8 = pd.read_parquet('/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-08/part-0.parquet')\n"
    "\n"
    "s0, e0 = day_ms('2026-07-01')\n"
    "print('Verify 2026-07-01 start_ms=' + str(s0))\n"
    "\n"
    "def count(df, sym, d):\n"
    "    s, e = day_ms(d)\n"
    "    sub = df[(df['symbol']==sym) & (df['as_of_ts_ms']>=s) & (df['as_of_ts_ms']<=e)]\n"
    "    n = len(sub)\n"
    "    r = '  ' + sym + ' ' + d + ': ' + str(n) + ' rows'\n"
    "    if n:\n"
    "        ut = sorted(sub['as_of_ts_ms'].unique().tolist())\n"
    "        st = [t for t in ut if t%(4*3600000)==0]\n"
    "        th = [datetime.utcfromtimestamp(t/1000).strftime('%H:%M') for t in st]\n"
    "        r += ' | unique_ts=' + str(len(ut)) + ' | 4h-settle=' + str(len(st)) + ' ' + str(th)\n"
    "    return r\n"
    "\n"
    "print('\\n  === BANKUSDT Jul 26-27 ===')\n"
    "print(count(df7, 'BANKUSDT', '2026-07-26'))\n"
    "print(count(df7, 'BANKUSDT', '2026-07-27'))\n"
    "\n"
    "print('\\n  === BRUSDT Jul 24-26 ===')\n"
    "for d in ['2026-07-24','2026-07-25','2026-07-26']:\n"
    "    print(count(df7, 'BRUSDT', d))\n"
    "\n"
    "print('\\n  === Aug-05 trio ===')\n"
    "for sym in ['BANKUSDT','IDOLUSDT','XPINUSDT']:\n"
    "    print(count(df8, sym, '2026-08-05'))\n"
    "\n"
    "bk = df7[df7['symbol']=='BANKUSDT'].sort_values('as_of_ts_ms')\n"
    "if len(bk):\n"
    "    f = datetime.utcfromtimestamp(bk['as_of_ts_ms'].iloc[0]/1000).strftime('%Y-%m-%d %H:%M UTC')\n"
    "    l = datetime.utcfromtimestamp(bk['as_of_ts_ms'].iloc[-1]/1000).strftime('%Y-%m-%d %H:%M UTC')\n"
    "    print('\\n  BANKUSDT Jul total=' + str(len(bk)) + ' first=' + f + ' last=' + l)\n"
)

write_cmd = "cat > /tmp/cf2.py << 'XEOF'\n" + py_body + "XEOF"
ssh(write_cmd)

print("=" * 68)
print("Funding settlement count (corrected)")
print("=" * 68)
out, err, rc = ssh("python3 /tmp/cf2.py", timeout=45)
if out:
    for ln in out.splitlines():
        print(f"  {ln}")
if err and rc != 0:
    print(f"  stderr: {err[:400]}")

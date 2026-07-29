#!/usr/bin/env python3
"""Upload and run _remote_oi_trace.py on VPS + get TAG Jul29 price."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import paramiko, pathlib

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
LOCAL = pathlib.Path(r"D:\Data back test\whale_data\_remote_oi_trace.py")
REMOTE = f"{WHALE_DIR}/_remote_oi_trace.py"
SEP = "=" * 60

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
    ssh.connect(HOST, username=USER, pkey=pkey, timeout=30)
    return ssh

def run(ssh, cmd, timeout=60):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    return o.read().decode("utf-8", errors="replace"), e.read().decode("utf-8", errors="replace")

def main():
    ssh = ssh_connect()
    print("Connected.")
    sftp = ssh.open_sftp()
    sftp.put(str(LOCAL), REMOTE)
    sftp.close()

    venv_py = f"{WHALE_DIR}/.venv/bin/python3"
    out, err = run(ssh, f"cd {WHALE_DIR} && {venv_py} {REMOTE}", timeout=60)
    print(out)
    if err.strip():
        print("STDERR:", err[:800])
    run(ssh, f"rm -f {REMOTE}")

    # Get TAG Jul 29 price from Binance kline API
    print(f"\n{SEP}\nTAGUSDT kline Jul27-29 (1d candle close)\n{SEP}")
    PRICE_SCRIPT = '''
import urllib.request, json
# Binance FAPI klines for TAGUSDT, 1d interval, last 5 candles
url = "https://fapi.binance.com/fapi/v1/klines?symbol=TAGUSDT&interval=1d&limit=5"
with urllib.request.urlopen(url, timeout=10) as r:
    data = json.loads(r.read())
print("TAGUSDT 1d klines (last 5):")
for c in data:
    import datetime
    ts = datetime.datetime.fromtimestamp(c[0]/1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    print(f"  {ts}: open={c[1]} high={c[2]} low={c[3]} close={c[4]} vol={float(c[5]):.0f}")
'''
    # Write to temp file and run
    sftp = ssh.open_sftp()
    import tempfile; tmp = f"{WHALE_DIR}/_tmp_px.py"
    with sftp.open(tmp, 'w') as f:
        f.write(PRICE_SCRIPT)
    sftp.close()
    out, err = run(ssh, f"cd {WHALE_DIR} && {venv_py} {tmp}", timeout=30)
    print(out)
    if err.strip():
        print("STDERR:", err[:300])
    run(ssh, f"rm -f {tmp}")

    # Also check OI methodology in whale_collector
    print(f"\n{SEP}\nwhale_collector OI source method\n{SEP}")
    out, _ = run(ssh, f"grep -rn 'oi_usd\\|openInterest\\|open_interest\\|OI' {WHALE_DIR}/whale_collector/ 2>&1 | grep -v '.pyc' | head -30")
    print(out)

    # Check export pipeline for OI timestamp methodology
    print(f"\n{SEP}\nwc storage writer — oi field\n{SEP}")
    out, _ = run(ssh, f"grep -n 'oi_usd\\|oi_contracts\\|mark_price\\|timestamp\\|close_time' {WHALE_DIR}/whale_collector/storage/writer.py 2>&1 | head -20")
    print(out)
    out, _ = run(ssh, f"grep -n 'oi_usd\\|oi_contracts\\|mark_price\\|openInterest' {WHALE_DIR}/whale_collector/binance/*.py 2>&1 | head -30")
    print(out)

    ssh.close()
    print(f"\n{SEP}\nDone.\n{SEP}")

if __name__ == "__main__":
    main()

"""Get TUT May row and check what date it is."""
import subprocess

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=20):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.stderr.strip()

print("[TUT ROWS May export]")
out, _ = ssh("grep 'TUTUSDT' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-05.csv")
print(repr(out[:500]))
print(out)

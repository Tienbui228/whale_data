"""Get TUT rows from July freshwatch export on VPS."""
import subprocess

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.stderr.strip()

print("[HEADER July export]")
out, _ = ssh("head -1 /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv")
print(out)

print("\n[TUT ROWS July]")
out, _ = ssh("grep 'TUTUSDT' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv")
rows = out.strip().split("\n")
print(f"Total: {len(rows)} rows")
for row in rows:
    print(row)

print("\n[TUT ROWS June]")
out, _ = ssh("grep 'TUTUSDT' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-06.csv")
rows6 = out.strip().split("\n")
print(f"Total: {len(rows6)} rows")
for row in rows6:
    print(row)

print("\n[TUT ROWS May]")
out, _ = ssh("grep 'TUTUSDT' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-05.csv")
rows5 = out.strip().split("\n")
print(f"Total: {len(rows5)} rows")
for row in rows5:
    print(row)

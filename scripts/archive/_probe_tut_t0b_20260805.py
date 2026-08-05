"""T0b: Check VPS export dir for freshwatch daily export, get TUT pos_r 05/08."""
import subprocess
import json
from datetime import datetime, timezone

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=20):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.stderr.strip()

print("=" * 60)

# Check export dir structure
print("[A] VPS export dir:")
out, _ = ssh("ls -la /root/Data_back_test/whale_data/data/export/ 2>/dev/null | head -30")
print(out if out else "EMPTY/NO DIR")

print("\n[B] Latest files in export dir:")
out, _ = ssh("ls -lt /root/Data_back_test/whale_data/data/export/ 2>/dev/null | head -20")
print(out if out else "NONE")

print("\n[C] Check for TUT in any export file modified today:")
out, _ = ssh("find /root/Data_back_test/whale_data/data/export -newer /root/Data_back_test/whale_data/data/export 2>/dev/null | head -10 || ls -lt /root/Data_back_test/whale_data/data/export/ 2>/dev/null | head -5")
print(out if out else "NONE")

# Try reading the latest export file and find TUT
print("\n[D] TUT row in latest export (any format):")
out, _ = ssh("ls -t /root/Data_back_test/whale_data/data/export/*.csv 2>/dev/null | head -1 | xargs -I{} grep -i 'tut' {} 2>/dev/null | tail -5")
if not out:
    out, _ = ssh("ls -t /root/Data_back_test/whale_data/data/export/ 2>/dev/null | head -1")
    print(f"  Latest file: {out}")
    out2, _ = ssh(f"head -3 /root/Data_back_test/whale_data/data/export/{out} 2>/dev/null")
    print(f"  Header: {out2[:300]}")
else:
    print(out[:500])

# Check for parquet exports
print("\n[E] Parquet/feather in export:")
out, _ = ssh("find /root/Data_back_test/whale_data/data/export -name '*.parquet' -o -name '*.feather' 2>/dev/null | head -10")
print(out if out else "NONE")

# Check if there's a daily snapshot specific location
print("\n[F] Daily snapshot location search:")
out, _ = ssh("find /root/Data_back_test/whale_data -name 'daily_2026*' -mtime -1 2>/dev/null | head -10")
print(out if out else "NONE RECENT")

out, _ = ssh("find /root/Data_back_test/whale_data -name 'daily_2026*' 2>/dev/null | head -10")
print("All daily_2026*:", out if out else "NONE")

# What is the actual snapshot the CLAUDE.md references?
print("\n[G] The 526-row snapshot file location:")
out, _ = ssh("find /root/Data_back_test -name 'daily_2026-07.csv' 2>/dev/null | head -5")
print(out if out else "NOT FOUND")

# Check P1 output fresh today
print("\n[H] VPS logs - last run time:")
out, _ = ssh("ls -lt /root/Data_back_test/whale_data/data/logs/ 2>/dev/null | head -10")
print(out if out else "NO LOGS DIR")

print("\n[I] Check raw export files by date:")
out, _ = ssh("ls -lt /root/Data_back_test/whale_data/data/export/ 2>/dev/null")
print(out[:1000] if out else "NONE")

print("\n" + "=" * 60)

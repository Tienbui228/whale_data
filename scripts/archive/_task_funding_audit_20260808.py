#!/usr/bin/env python3
"""Audit VPS funding_8h store: mọi symbol×date 01/07→08/08 có settle-count < expected.
Chạy audit trên VPS, ghi kết quả vào file VPS, SCP về local.
READ-ONLY (không ghi vào parquet).
"""
import sys, subprocess, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=120):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

def scp_from(remote_path, local_path):
    args = ["scp", "-o", "StrictHostKeyChecking=no",
            f"{VPS}:{remote_path}", local_path]
    r = subprocess.run(args, capture_output=True, timeout=30,
                      encoding="utf-8", errors="replace")
    return r.returncode == 0

# Step 1: write audit script to VPS
audit_script = r"""
import pandas as pd, json, sys
from datetime import datetime, timezone, timedelta

BASE = "/root/Data_back_test/whale_data"
PARQ_DIR = BASE + "/data/raw/funding_8h"
INTERVALS_JSON = BASE + "/data/config/funding_intervals.json"

with open(INTERVALS_JSON) as f:
    iv_raw = json.load(f)

def get_interval_h(sym):
    v = iv_raw.get(sym)
    if v is None:
        return 8
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, dict):
        return int(v.get("interval_h", v.get("interval", 8)))
    return 8

def expected_fn(ih):
    return 24 // ih

def iter_dates(start="2026-07-01", end="2026-08-08"):
    d = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    e = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    while d <= e:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)

def day_ms(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    s = int(dt.timestamp() * 1000)
    return s, s + 86_400_000 - 1

def settlement_ts(date_str, ih):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    base = int(dt.timestamp() * 1000)
    step = ih * 3600 * 1000
    return set(base + i * step for i in range(24 // ih))

# Load monthly parquets
dfs = {}
for m in ["2026-07", "2026-08"]:
    path = f"{PARQ_DIR}/month={m}/part-0.parquet"
    try:
        dfs[m] = pd.read_parquet(path)
    except Exception as e:
        print(f"WARN {path}: {e}", file=sys.stderr)

def get_df(date_str):
    return dfs.get(date_str[:7])

# All symbols with any data
all_syms = sorted(set(s for df in dfs.values() for s in df['symbol'].unique()))

out_lines = []
out_lines.append("symbol,date,interval_h,expected_fn,actual_fn,missing_hours")
gaps = []
total = 0

for sym in all_syms:
    ih = get_interval_h(sym)
    exp = expected_fn(ih)
    for d in iter_dates():
        df = get_df(d)
        if df is None:
            continue
        s, e = day_ms(d)
        sub = df[(df['symbol'] == sym) & (df['as_of_ts_ms'] >= s) & (df['as_of_ts_ms'] <= e)]
        if len(sub) == 0:
            continue
        total += 1
        exp_ts = settlement_ts(d, ih)
        actual_ts = set(sub['as_of_ts_ms'].unique())
        actual_settle = exp_ts & actual_ts
        n = len(actual_settle)
        if n < exp:
            missing = sorted(exp_ts - actual_ts)
            mh = [datetime.utcfromtimestamp(t/1000).strftime('%H:%M') for t in missing]
            gaps.append((sym, d, ih, exp, n, mh))
            out_lines.append(f"{sym},{d},{ih},{exp},{n},{mh}")

out_lines.append("")
out_lines.append(f"SUMMARY: sym_days_checked={total} gaps={len(gaps)} syms_affected={len(set(g[0] for g in gaps))}")
out_lines.append("")
out_lines.append("=== TOP AFFECTED SYMBOLS ===")
from collections import Counter
sym_cnt = Counter(g[0] for g in gaps)
for sym, cnt in sym_cnt.most_common(30):
    out_lines.append(f"  {sym}: {cnt} days")

with open("/tmp/funding_audit_out.txt", "w") as f:
    f.write("\n".join(out_lines))
print("DONE: " + str(len(gaps)) + " gaps written to /tmp/funding_audit_out.txt")
"""

# Write script via heredoc with unique delimiter
write_out, write_err, write_rc = ssh(
    "cat > /tmp/funding_audit.py << 'XEND'\n" + audit_script + "\nXEND"
)

print("=== Step 1: Run audit on VPS ===")
out, err, rc = ssh("python3 /tmp/funding_audit.py", timeout=120)
print(f"  {out or err}")

# Step 2: SCP result back
print("\n=== Step 2: SCP audit result ===")
local_report = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "docs", "reports", "_funding_audit_20260808.txt")
os.makedirs(os.path.dirname(local_report), exist_ok=True)

ok = scp_from("/tmp/funding_audit_out.txt", local_report)
if ok:
    print(f"  Saved to {local_report}")
else:
    print("  SCP failed — reading directly via SSH...")
    out2, _, _ = ssh("cat /tmp/funding_audit_out.txt | head -100")
    print(out2)

# Step 3: Print summary
if ok:
    with open(local_report, encoding="utf-8", errors="replace") as f:
        content = f.read()
    lines = content.splitlines()
    # Show header + summary + affected symbols
    gap_lines = [l for l in lines if l and not l.startswith("BANKUSDT,2026-07-2") and
                 not l.startswith("symbol,")]
    print()
    # Print first 5 gap rows as sample
    gap_data = [l for l in lines if ',' in l and not l.startswith("symbol")]
    print("=== Sample gaps (first 20) ===")
    for l in gap_data[:20]:
        print(f"  {l}")
    print()
    # Print summary section
    for l in lines:
        if "SUMMARY" in l or "===" in l or l.startswith("  "):
            print(l)

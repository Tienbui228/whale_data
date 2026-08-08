#!/usr/bin/env python3
# Item 2: A4/A5 code expressions + PARTI d_pos_3d series 07-01→09
import sys, subprocess, tempfile, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return r.returncode == 0

# 1. Get A4 and A5 code from gom_scan.py
print("=== A4 (pos_rerate) code ===")
out, _ = ssh(f"grep -n '_a4\\|pos_rerate\\|hedge_alive\\|hedge_struct\\|div_ratio\\|d_pos' {BASE}/scripts/gom_scan.py | head -40")
print(out)

print()
print("=== A5 (funding_unpin) code ===")
out2, _ = ssh(f"grep -n '_a5\\|funding_unpin\\|unpin\\|pin_streak' {BASE}/scripts/gom_scan.py | head -20")
print(out2)

# 2. Extract A4 function body
print()
print("=== _check_a4 function body ===")
out3, _ = ssh(f"grep -n 'def.*a4\\|def.*pos_rerate\\|def.*hedge' {BASE}/scripts/gom_scan.py")
print(out3)

INNER = r"""
import sys, math
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/root/Data_back_test/binance-bot-signals")

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, load_funding_intervals, build_token_days
from gom_scan import eval_gom, load_screen_cfg, _false_result
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
df  = load_fw_csvs(REPO / "data" / "export", "2026-08-07", lookback_days=60)
df  = taker_scale_check_df(df)
intervals = load_funding_intervals(REPO / "data" / "config")
days, suspect = build_token_days(df, "PARTIUSDT", "2026-06-08", "2026-08-07", intervals)

print(f"PARTI days: {len(days)}  (suspect: {len(suspect)})")
print()
# Print key fields for 07-01 to 07-09 (index range for that period)
print(f"{'date':<12} {'lsr_pos':>9} {'lsr_pos_prv':>12} {'d_pos_3d':>10} {'div_raw':>8} {'div_avg3':>9} {'hedge?':>7} {'A4':>4} {'A5':>4}")
print("-" * 90)

for i, d in enumerate(days):
    date = d.get("date", "")
    if len(date) == 5:
        date = "2026-" + date
    if date < "2026-07-01" or date > "2026-07-10":
        continue

    skip = d.get("_skip_eval") or d.get("_suspect")
    result = _false_result() if skip else eval_gom(days, i, cfg, sc)

    lsr_pos  = d.get("lsr_pos", float("nan"))
    lsr_prv  = days[i-1].get("lsr_pos", float("nan")) if i > 0 else float("nan")
    d_pos_3d = d.get("d_pos_3d", float("nan"))
    div_raw  = d.get("div_raw", float("nan"))
    div_avg3 = d.get("div_avg3", float("nan"))

    a = result.get("gom_a", {})
    A4 = "T" if a.get("A4") else "F"
    A5 = "T" if a.get("A5") else "F"

    # hedge_structure: div_ratio <= 0.5 → need div fields
    div_ratio = d.get("div_ratio", float("nan"))
    hedge = "?" if math.isnan(div_ratio) else ("Y" if div_ratio <= 0.5 else "N")

    print(f"{date:<12} {lsr_pos:>9.4f} {lsr_prv:>12.4f} {d_pos_3d:>10.4f} {div_raw:>8.4f} {div_avg3:>9.4f} {hedge:>7} {A4:>4} {A5:>4}")

print()
print("=== d_pos_3d formula check ===")
# d_pos_3d is defined how? Check the raw field
d0 = days[0]
print(f"Fields in day[0]: {sorted(d0.keys())[:30]}")
# Check d_pos vs d_pos_3d
for i, d in enumerate(days):
    date = d.get("date", "")
    if len(date) == 5: date = "2026-" + date
    if date < "2026-06-27" or date > "2026-07-05":
        continue
    print(f"  {date}: d_pos={d.get('d_pos','N/A')}  d_pos_3d={d.get('d_pos_3d','N/A')}")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
scp(tmp, f"{BASE}/_a4a5_inner.py")
os.unlink(tmp)

out4, err4 = ssh(f"python3 {BASE}/_a4a5_inner.py 2>&1", timeout=120)
print()
print("=== PARTI A4/A5 trace ===")
print(out4)
if err4 and ("Error" in err4 or "Traceback" in err4):
    print("STDERR:", err4[:500])

#!/usr/bin/env python3
# Item 4: G1 DIVERGE — BANK case exact diff, why replay gives 07-12 vs gate v7 06-29
import sys, subprocess, tempfile, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=180):
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

INNER = r"""
import sys, math
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/root/Data_back_test/binance-bot-signals")

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, load_funding_intervals, build_token_days
from gom_scan import eval_gom, update_chain, load_screen_cfg, _false_result
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
df  = load_fw_csvs(REPO / "data" / "export", "2026-08-07", lookback_days=60)
df  = taker_scale_check_df(df)
intervals = load_funding_intervals(REPO / "data" / "config")

days, suspect = build_token_days(df, "BANKUSDT", "2026-06-08", "2026-08-07", intervals)
print(f"BANK days: {len(days)} (suspect: {len(suspect)})")
print()

# GATE v7 says: chain-1 opens 06-29 (A1∧A2∧A3∧A4 in gate v7 spec)
# Current code: chain opens 07-12
# Show detail for 06-25 → 07-15
print(f"{'date':<12} {'gom':>4} {'A1':>3} {'A2':>3} {'A3':>3} {'A4':>3} {'A5':>3} {'B1':>3} {'B2':>3} {'B3':>3} {'B4':>3} {'OPEN':>5}  details")
print("-" * 100)

chain = {}
for i, d in enumerate(days):
    date = d.get("date","")
    if len(date) == 5: date = "2026-" + date
    if date < "2026-06-25" or date > "2026-07-15":
        # Still need to update chain state
        skip = d.get("_skip_eval") or d.get("_suspect")
        result = _false_result() if skip else eval_gom(days, i, cfg, sc)
        chain = update_chain(chain, "BANK", days, i, result, cfg, sc)
        continue

    skip = d.get("_skip_eval") or d.get("_suspect")
    result = _false_result() if skip else eval_gom(days, i, cfg, sc)
    chain = update_chain(chain, "BANK", days, i, result, cfg, sc)

    g  = result.get("gom_day", False)
    a  = result.get("gom_a", {})
    b  = result.get("gom_b", {})
    bf = result.get("gom_b_fire", False)

    T = lambda v: "T" if v else "."
    c_open = chain.get("chain_open")
    nd = chain.get("n_days", 0) if c_open else 0

    # Extra detail for non-firing days near 06-29
    details = []
    if not a.get("A1"):
        glsr = d.get("lsr_global_r", float("nan"))
        details.append(f"A1_fail:glsr={glsr:.3f}")
    if not a.get("A2"):
        avg5 = d.get("lsr_global_avg5", float("nan"))
        details.append(f"A2_fail:avg5={avg5:.3f}")
    if not a.get("A3"):
        details.append(f"A3_fail")
    if not b.get("B1"):
        details.append(f"B1_fail")

    print(f"{date:<12} {T(g):>4} {T(a.get('A1')):>3} {T(a.get('A2')):>3} {T(a.get('A3')):>3} "
          f"{T(a.get('A4')):>3} {T(a.get('A5')):>3} "
          f"{T(b.get('B1')):>3} {T(b.get('B2')):>3} {T(b.get('B3')):>3} {T(b.get('B4')):>3} "
          f"{'OPEN' if c_open else '----':>5}  {' '.join(details)}")

print()
print("=== GATE v7 expected chain-1 open = 06-29 ===")
print("Gate v7 conditions (old spec): A1 ∧ A2_old ∧ A3 ∧ (A4 or A5)")
print("A2_old was: stealth_grind (same as A1 in old code)")
print("Current A2: avg5(lsr_global) > threshold")
print()
# Check 06-29 values
for i, d in enumerate(days):
    date = d.get("date","")
    if len(date) == 5: date = "2026-" + date
    if date == "2026-06-29":
        print(f"06-29 raw fields:")
        print(f"  lsr_global_r:    {d.get('lsr_global_r', 'N/A')}")
        print(f"  lsr_global_avg5: {d.get('lsr_global_avg5', 'N/A')}")
        print(f"  lsr_pos_r:       {d.get('lsr_pos_r', 'N/A')}")
        print(f"  lsr_pos_avg5:    {d.get('lsr_pos_avg5', 'N/A')}")
        print(f"  d_oi_net:        {d.get('d_oi_net', 'N/A')}")
        print(f"  oi_vs_med14:     {d.get('oi_vs_med14', 'N/A')}")
        print(f"  div_ratio:       {d.get('div_ratio', 'N/A')}")
        print(f"  _suspect:        {d.get('_suspect', False)}")
        print(f"  _skip_eval:      {d.get('_skip_eval', False)}")
        result_629 = eval_gom(days, i, cfg, sc)
        print(f"  eval_gom result: {result_629.get('gom_a')} gom_day={result_629.get('gom_day')}")
        break
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
scp(tmp, f"{BASE}/_g1bank_inner.py")
os.unlink(tmp)

out, err = ssh(f"python3 {BASE}/_g1bank_inner.py 2>&1", timeout=180)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("STDERR:", err[:600])

#!/usr/bin/env python3
# Item 3 (final): GOM-C β with correct C3=taker∈[40,55] + Item 5 fw vs UM diff
import sys, subprocess
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

import tempfile, os

INNER = r"""
import sys, math, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/root/Data_back_test/binance-bot-signals")

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, load_funding_intervals, build_token_days
from gom_scan import eval_gom, load_screen_cfg, _false_result, _gomc_beta_check, stealth_grind
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
fp  = cfg.get("funding_pinned", {})
rate_min = fp.get("rate_min", 4e-5)

# Use the same date as the 08-07 cron run: target_date=08-07 means evaluate last complete day
# run_gom_daily at 01:25 UTC on 08-07 → export through 08-06 → last eval day = 08-06
# But probe uses load_fw_csvs("2026-08-07", lookback=60) — loads through 08-07
# We'll run both: evaluate last day and evaluate second-to-last day

df07  = load_fw_csvs(REPO / "data" / "export", "2026-08-07", lookback_days=60)
df07  = taker_scale_check_df(df07)
intervals = load_funding_intervals(REPO / "data" / "config")

# Use actual _gomc_beta_check function
TARGETS = ["AVAUSDT", "GRIFFAINUSDT", "GTCUSDT", "MAVIAUSDT", "NOMUSDT",
           "COOKIEUSDT", "CYSUSDT", "TUTUSDT"]

print(f"=== GOM-C β FINAL per-token (using actual _gomc_beta_check + eval_gom) ===")
print(f"{'token':<14} {'C1':>3} {'C2':>3} {'C3':>3} {'guard':>6} {'slope':>6} {'supp':>5} {'FIRE-d7':>8} {'FIRE-d6':>8}  taker  f_avg   ih")
print("-" * 105)

for sym in TARGETS:
    sym_df = df07[df07["symbol"] == sym]
    if len(sym_df) == 0:
        print(f"{sym.replace('USDT',''):<14}  NO DATA"); continue

    days, _ = build_token_days(df07, sym, "2026-06-08", "2026-08-07", intervals)
    if not days:
        print(f"{sym.replace('USDT',''):<14}  NO DAYS"); continue

    results = {}
    for label, idx_offset in [("d7", 0), ("d6", 1)]:
        i = len(days) - 1 - idx_offset
        while i >= 0 and (days[i].get("_skip_eval") or days[i].get("_suspect")):
            i -= 1
        if i < 0:
            results[label] = ("N/A", {})
            continue
        d = days[i]
        result = eval_gom(days, i, cfg, sc)
        fire = _gomc_beta_check(days, i, cfg, sc, result, check_cooldown=True)
        results[label] = (fire, d)

    # Detailed breakdown for d7 (last day = 08-07)
    i = len(days) - 1
    while i >= 0 and (days[i].get("_skip_eval") or days[i].get("_suspect")):
        i -= 1
    if i < 0:
        continue
    d = days[i]
    result = eval_gom(days, i, cfg, sc)

    c1_ok = stealth_grind(days, i, cfg)
    f_avg = d.get("funding_avg", float("nan"))
    ih = d.get("_interval_h", 8)
    c2_thr = max(2.0 * rate_min, 1e-4) * ih / 4
    c2_ok = not math.isnan(f_avg) and f_avg <= c2_thr
    tkr = d.get("taker_buy_pct", float("nan"))
    c3_ok = not math.isnan(tkr) and (40.0 <= tkr <= 55.0)
    p_now = d.get("lsr_pos", float("nan"))
    p_prv = days[i-1].get("lsr_pos", float("nan")) if i > 0 else float("nan")
    g_ok = not (math.isnan(p_now) or math.isnan(p_prv) or (p_now - p_prv) < 0)
    supp_any = any(v for v in result.get("supp_dq", {}).values())

    from gom_scan import _a3_slope_ok
    slope_bad = sum(1 for j in range(max(0, i-2), i+1) if not _a3_slope_ok(days, j, sc))
    slope_ok = slope_bad < 3

    fire_d7 = results["d7"][0]
    fire_d6 = results["d6"][0] if isinstance(results["d6"][0], bool) else "N/A"

    tok = sym.replace("USDT","")
    print(f"{tok:<14} {'T' if c1_ok else 'F':>3} {'T' if c2_ok else 'F':>3} {'T' if c3_ok else 'F':>3} {'T' if g_ok else 'F':>6} {'T' if slope_ok else 'F':>6} {'T' if not supp_any else 'F':>5}  {'FIRE' if fire_d7 else '----':>8}  {'FIRE' if fire_d6 else '----':>8}  {tkr:5.1f}  {f_avg:.2e}  {ih}h")

print()
print("=== universe_master.csv active symbols vs fw-filter diff ===")
import csv
um_active = set()
with open(REPO / "data" / "config" / "universe_master.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("status") == "active":
            sym = row["symbol"].replace("USDT","")
            um_active.add(sym)

# Load freshwatch_symbols.txt from VPS
fw_path = REPO / "data" / "config" / "freshwatch_symbols.txt"
if fw_path.exists():
    fw_set = set(l.strip() for l in fw_path.read_text().splitlines() if l.strip())
    # Strip USDT if present
    fw_base = set(s[:-4] if s.endswith("USDT") else s for s in fw_set)
    print(f"fw-filter: {len(fw_base)} entries, universe_master active: {len(um_active)}")
    fw_not_um = sorted(fw_base - um_active)
    um_not_fw = sorted(um_active - fw_base)
    print(f"\nIn fw-filter NOT in universe_master active ({len(fw_not_um)}): {fw_not_um[:10]}{'...' if len(fw_not_um)>10 else ''}")
    print(f"\nIn universe_master active NOT in fw-filter ({len(um_not_fw)}): showing first 20")
    for s in um_not_fw[:20]:
        print(f"  {s}")
    # Check specifically APR/ARX/PIEVERSE/Q/STAR
    print()
    for s in ["APR","ARX","PIEVERSE","Q","STAR"]:
        print(f"  {s}: in_UM={s in um_active}  in_fw={s in fw_base}")
    # Check B/GRVT/VELVET
    for s in ["B","GRVT","VELVET"]:
        print(f"  {s}: in_UM={s in um_active}  in_fw={s in fw_base}")
else:
    print(f"freshwatch_symbols.txt NOT FOUND at {fw_path}")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
scp(tmp, f"{BASE}/_gomc_c3_fw_inner.py")
os.unlink(tmp)

out, err = ssh(f"python3 {BASE}/_gomc_c3_fw_inner.py 2>&1", timeout=180)
print(out)
if err and ("Error" in err or "Traceback" in err):
    print("STDERR:", err[:600])

#!/usr/bin/env python3
# Item 3: gom_state.json C-chains + breakdown 5 fires mất ngày-3
# (8 fires session-13 probe vs 3 fires clean-state reconstruction)
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

# Dump gom_state.json
print("=== gom_state.json (full) ===")
out, _ = ssh(f"cat {BASE}/data/gom_state.json")
print(out[:8000])

INNER = r"""
import sys, math
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/root/Data_back_test/binance-bot-signals")

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, load_funding_intervals, build_token_days
from gom_scan import eval_gom, load_screen_cfg, _false_result, _gomc_beta_check, _gomc_c_cooldown_info
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
df  = load_fw_csvs(REPO / "data" / "export", "2026-08-07", lookback_days=60)
df  = taker_scale_check_df(df)
intervals = load_funding_intervals(REPO / "data" / "config")

# The 5 missing: AVA, GRIFFAIN, GTC, MAVIA, NOM (were in 8-fire session 13, not in 3-fire clean)
TARGETS = ["AVAUSDT", "GRIFFAINUSDT", "GTCUSDT", "MAVIAUSDT", "NOMUSDT",
           "COOKIEUSDT", "CYSUSDT", "TUTUSDT"]  # also the 3 that DID fire

print("=== GOM-C β per-token diagnosis for date=2026-08-07 ===")
print(f"{'token':<14} {'C1':>3} {'C2':>3} {'C3':>3} {'C4':>3} {'guard':>6} {'cd_blk':>7} {'FIRE':>5}  notes")
print("-" * 80)

for sym in TARGETS:
    sym_df = df[df["symbol"] == sym]
    if len(sym_df) == 0:
        print(f"{sym.replace('USDT',''):<14}  NO DATA IN CSV")
        continue

    days, suspect = build_token_days(df, sym, "2026-06-08", "2026-08-07", intervals)
    if not days:
        print(f"{sym.replace('USDT',''):<14}  NO DAYS LOADED")
        continue

    # Get the last non-skip day (2026-08-07)
    i = len(days) - 1
    while i >= 0 and (days[i].get("_skip_eval") or days[i].get("_suspect")):
        i -= 1
    if i < 0:
        print(f"{sym.replace('USDT',''):<14}  ALL DAYS SKIP")
        continue

    d = days[i]
    date = d.get("date","?")
    if len(date) == 5: date = "2026-" + date
    result = eval_gom(days, i, cfg, sc)

    # Check each GOM-C β sub-condition
    # C1: stealth_grind (A1 in GOM-A terms = same field)
    c1 = result.get("gom_a", {}).get("A1", False)

    # C2: f_avg quiet — check manually
    fp = d.get("funding_params", {}) or {}
    if not fp:
        # Try to get from day data
        f_avg = d.get("f_avg", float("nan"))
        interval_h = d.get("funding_interval_h", 8.0)
    else:
        f_avg = fp.get("f_avg", float("nan"))
        interval_h = fp.get("interval_h", 8.0)

    rate_min = fp.get("rate_min", 4e-5) if fp else 4e-5
    c2_thr_8h = max(2.0 * rate_min, 1e-4)
    c2_thr = c2_thr_8h * interval_h / 4
    c2_ok = not math.isnan(f_avg) and f_avg <= c2_thr

    # C3: lsr_global_r > 1 (lax)
    glsr = d.get("lsr_global_r", float("nan"))
    c3_ok = not math.isnan(glsr) and glsr > 1.0

    # C4: slope OK (no sustained slope > 1.15 for ≥3d)
    from gom_scan import _a3_slope_ok
    slope_bad_count = sum(1 for j in range(max(0, i-2), i+1) if not _a3_slope_ok(days, j, sc))
    c4_ok = slope_bad_count < 3

    # Guard: d_pos ≥ 0 (lsr_pos non-declining)
    lsr_now = d.get("lsr_pos", float("nan"))
    lsr_prv = days[i-1].get("lsr_pos", float("nan")) if i > 0 else float("nan")
    guard_ok = not (math.isnan(lsr_now) or math.isnan(lsr_prv) or (lsr_now - lsr_prv) < 0)

    # supp_dq today
    supp = result.get("supp_dq", {})
    supp_today = any(v for v in supp.values())

    # 13d backward scan for supp_dq (cooldown check)
    cd_blocked = False
    cd_info = ""
    if c1 and c2_ok and c3_ok and c4_ok and guard_ok and not supp_today:
        for j in range(max(0, i - 13), i):
            dj = days[j]
            if dj.get("_skip_eval") or dj.get("_suspect"):
                continue
            rj = eval_gom(days, j, cfg, sc)
            if any(v for v in rj.get("supp_dq", {}).values()):
                cd_blocked = True
                dj_date = dj.get("date","?")
                if len(dj_date) == 5: dj_date = "2026-" + dj_date
                cd_info = f"cd@{dj_date}"
                break

    fire = c1 and c2_ok and c3_ok and c4_ok and guard_ok and not supp_today and not cd_blocked

    tok = sym.replace("USDT","")
    notes = []
    if not c2_ok: notes.append(f"f_avg={f_avg:.2e}>thr={c2_thr:.2e}")
    if not c3_ok: notes.append(f"glsr={glsr:.3f}")
    if not c4_ok: notes.append(f"slope_bad={slope_bad_count}")
    if not guard_ok: notes.append(f"d_pos↓({lsr_now:.4f}<{lsr_prv:.4f})")
    if supp_today: notes.append(f"supp_today:{[k for k,v in supp.items() if v]}")
    if cd_blocked: notes.append(cd_info)

    print(f"{tok:<14} {'T' if c1 else 'F':>3} {'T' if c2_ok else 'F':>3} {'T' if c3_ok else 'F':>3} {'T' if c4_ok else 'F':>3} {'T' if guard_ok else 'F':>6} {'BLKD' if cd_blocked else 'OK':>7} {'FIRE' if fire else '----':>5}  {' '.join(notes)}")

print()
print("=== supp_dq history for 5 missing (last 14 days) ===")
for sym in ["AVAUSDT", "GRIFFAINUSDT", "GTCUSDT", "MAVIAUSDT", "NOMUSDT"]:
    sym_df = df[df["symbol"] == sym]
    if len(sym_df) == 0:
        print(f"{sym.replace('USDT','')}: NO DATA")
        continue
    days2, _ = build_token_days(df, sym, "2026-06-08", "2026-08-07", intervals)
    if not days2:
        continue
    fires = []
    for i2, d2 in enumerate(days2):
        date2 = d2.get("date","?")
        if len(date2) == 5: date2 = "2026-" + date2
        if date2 < "2026-07-25":
            continue
        if d2.get("_skip_eval") or d2.get("_suspect"):
            continue
        r2 = eval_gom(days2, i2, cfg, sc)
        sq = {k: v for k, v in r2.get("supp_dq", {}).items() if v}
        if sq:
            fires.append(f"{date2}:{list(sq.keys())}")
    print(f"{sym.replace('USDT','')}: supp_dq fires (last 14d) = {fires if fires else 'NONE'}")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
scp(tmp, f"{BASE}/_gstate_inner.py")
os.unlink(tmp)

out2, err2 = ssh(f"python3 {BASE}/_gstate_inner.py 2>&1", timeout=180)
print()
print("=== GOM-C β per-token diagnosis ===")
print(out2)
if err2 and ("Error" in err2 or "Traceback" in err2):
    print("STDERR:", err2[:600])

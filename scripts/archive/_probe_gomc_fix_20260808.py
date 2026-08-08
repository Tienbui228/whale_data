#!/usr/bin/env python3
# Item 3 (corrected): GOM-C β breakdown — fix field names (funding_avg, lsr_global, _interval_h)
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

# First dump gom_state.json C-related entries
print("=== gom_state.json C-chain entries ===")
out, _ = ssh(f"python3 -c \"import json; d=json.load(open('{BASE}/data/gom_state.json')); print(json.dumps(d, indent=2))\" 2>&1 | head -200")
print(out[:6000])

INNER = r"""
import sys, math, json
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

# First: show actual field names for a representative token
sym0 = "AVAUSDT"
days0, _ = build_token_days(df, sym0, "2026-06-08", "2026-08-07", intervals)
if days0:
    d0 = days0[-1]
    print(f"=== Field names in last day of {sym0} ===")
    print(sorted(d0.keys()))
    print(f"  funding_avg={d0.get('funding_avg', 'MISSING')}")
    print(f"  _interval_h={d0.get('_interval_h', 'MISSING')}")
    print(f"  lsr_global={d0.get('lsr_global', 'MISSING')}")
    print(f"  lsr_pos={d0.get('lsr_pos', 'MISSING')}")
    print()

# C2 threshold: max(2*rate_min, 1e-4) * interval_h / 4
# rate_min from gom_scan config
RATE_MIN_DEFAULT = 4e-5  # standard 8h

TARGETS = ["AVAUSDT", "GRIFFAINUSDT", "GTCUSDT", "MAVIAUSDT", "NOMUSDT",
           "COOKIEUSDT", "CYSUSDT", "TUTUSDT"]

print(f"=== GOM-C β corrected per-token diagnosis (date=2026-08-07) ===")
print(f"{'token':<14} {'C1':>3} {'C2':>3} {'C3':>3} {'C4':>3} {'guard':>6} {'cd_blk':>7} {'FIRE':>5}  notes")
print("-" * 90)

for sym in TARGETS:
    sym_df = df[df["symbol"] == sym]
    if len(sym_df) == 0:
        print(f"{sym.replace('USDT',''):<14}  NO DATA IN CSV")
        continue

    days, suspect = build_token_days(df, sym, "2026-06-08", "2026-08-07", intervals)
    if not days:
        print(f"{sym.replace('USDT',''):<14}  NO DAYS LOADED")
        continue

    # Get last non-skip day
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

    # C1: A1 from GOM-A (stealth_grind)
    c1 = result.get("gom_a", {}).get("A1", False)

    # C2: funding_avg quiet — use correct field names
    f_avg = d.get("funding_avg", float("nan"))
    interval_h = d.get("_interval_h", 8.0)
    if math.isnan(interval_h): interval_h = 8.0

    rate_min = RATE_MIN_DEFAULT
    c2_thr_8h = max(2.0 * rate_min, 1e-4)
    c2_thr = c2_thr_8h * interval_h / 8.0  # scale to actual interval
    c2_ok = not math.isnan(f_avg) and abs(f_avg) <= c2_thr

    # C3: lsr_global > 1 — use correct field name
    glsr = d.get("lsr_global", float("nan"))
    c3_ok = not math.isnan(glsr) and glsr > 1.0

    # C4: slope OK (no sustained slope > 1.15 for >=3d)
    try:
        from gom_scan import _a3_slope_ok
        slope_bad_count = sum(1 for j in range(max(0, i-2), i+1) if not _a3_slope_ok(days, j, sc))
        c4_ok = slope_bad_count < 3
    except Exception as e:
        c4_ok = True
        slope_bad_count = -1

    # Guard: lsr_pos non-declining
    lsr_now = d.get("lsr_pos", float("nan"))
    lsr_prv = days[i-1].get("lsr_pos", float("nan")) if i > 0 else float("nan")
    guard_ok = not (math.isnan(lsr_now) or math.isnan(lsr_prv) or (lsr_now - lsr_prv) < 0)

    # supp_dq today
    supp = result.get("supp_dq", {})
    supp_today = any(v for v in supp.values())

    # 13d backward cooldown scan
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
    if not c1: notes.append("C1_fail")
    if not c2_ok: notes.append(f"f_avg={f_avg:.2e}>thr={c2_thr:.2e}(ih={interval_h}h)")
    if not c3_ok: notes.append(f"glsr={glsr:.3f}")
    if not c4_ok: notes.append(f"slope_bad={slope_bad_count}")
    if not guard_ok: notes.append(f"pos↓({lsr_now:.4f}<{lsr_prv:.4f})")
    if supp_today: notes.append(f"supp:{[k for k,v in supp.items() if v]}")
    if cd_blocked: notes.append(cd_info)

    print(f"{tok:<14} {'T' if c1 else 'F':>3} {'T' if c2_ok else 'F':>3} {'T' if c3_ok else 'F':>3} {'T' if c4_ok else 'F':>3} {'T' if guard_ok else 'F':>6} {'BLKD' if cd_blocked else 'OK':>7} {'FIRE' if fire else '----':>5}  {' '.join(notes)}")

print()
print("=== Also: gom_state.json C-chain token list ===")
gs = json.load(open(REPO / "data" / "gom_state.json"))
for tok, v in gs.items():
    c_keys = {k: val for k, val in v.items() if 'c_' in k.lower() or 'gomc' in k.lower() or 'chain' in k.lower()}
    if c_keys or any('fire' in k for k in v):
        print(f"  {tok}: {c_keys}")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
scp(tmp, f"{BASE}/_gomc_fix_inner.py")
os.unlink(tmp)

out2, err2 = ssh(f"python3 {BASE}/_gomc_fix_inner.py 2>&1", timeout=180)
print()
print(out2)
if err2 and ("Error" in err2 or "Traceback" in err2):
    print("STDERR:", err2[:800])

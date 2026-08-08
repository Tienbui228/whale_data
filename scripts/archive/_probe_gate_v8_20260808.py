#!/usr/bin/env python3
# Item 1: GATE §6 v8 — run_backtest6 + PARTI/ZBT/GOM-C on current code
import sys, subprocess, os
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
BOT_VPS = "/root/Data_back_test/binance-bot-signals"
LOCAL_CASES = Path(r"D:\Data back test\binance-bot-signals\docs\case study")

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

def scp_file(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", str(local), f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return r.returncode == 0

# 1. SCP calib result files to VPS
print("=== Uploading calib files to VPS ===")
ssh(f"mkdir -p '{BOT_VPS}/docs/case study'")
case_dir_vps = f"{BOT_VPS}/docs/case study"
for f in sorted(LOCAL_CASES.glob("*_result.txt")):
    ok = scp_file(f, f"'{case_dir_vps}/{f.name}'")
    print(f"  {f.name}: {'OK' if ok else 'FAIL'}")

# 2. Run --backfill (calls run_backfill + run_backtest6)
print()
print("=== run_backtest6 §6 v8 ===")
out, err = ssh(
    f"cd {BASE} && .venv/bin/python3 scripts/gom_scan.py --backfill 2>&1",
    timeout=300
)
print(out)
if err:
    print("STDERR:", err[:400])

# 3. PARTI + ZBT + GOM-C on freshwatch CSV
import tempfile
INNER = r"""
import sys, math, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/root/Data_back_test/binance-bot-signals")

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, load_funding_intervals, build_token_days
from gom_scan import eval_gom, load_screen_cfg, _false_result, update_chain, _gomc_beta_check, stealth_grind
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
df07  = load_fw_csvs(REPO / "data" / "export", "2026-08-07", lookback_days=90)
df07  = taker_scale_check_df(df07)
intervals = load_funding_intervals(REPO / "data" / "config")

def run_chain(sym, start="2026-06-01", end="2026-08-07"):
    days, _ = build_token_days(df07, sym, start, end, intervals)
    chain = {}
    opens = []
    chapters = []
    closes = []
    gomc_fires = []
    for i, d in enumerate(days):
        date = d.get("date","?")
        if len(date)==5: date="2026-"+date
        skip = d.get("_skip_eval") or d.get("_suspect")
        result = _false_result() if skip else eval_gom(days, i, cfg, sc)
        was_open = chain.get("chain_open",False)
        was_ch   = chain.get("chapter",1)
        chain    = update_chain(chain, sym.replace("USDT",""), days, i, result, cfg, sc)
        if not was_open and chain.get("chain_open"): opens.append(date)
        if was_open and chain.get("chain_open") and chain.get("chapter",1)>was_ch:
            chapters.append(date)
        if was_open and not chain.get("chain_open"):
            closes.append((date, chain.get("close_reason","?")))
        # GOM-C β
        if not skip and _gomc_beta_check(days, i, cfg, sc, result, check_cooldown=True):
            gomc_fires.append(date)
    return opens, chapters, closes, gomc_fires, days

print()
print("=== §6 v8 freshwatch-based rows ===")
print()

# P — PARTI open+close
print("--- PARTI (row P) ---")
op, ch, cl, gcf, days_p = run_chain("PARTIUSDT", "2026-06-01", "2026-08-07")
print(f"  opens:   {op}")
print(f"  chapters:{ch}")
print(f"  closes:  {cl}")
print(f"  Expected: chain2=07-01→07-11(rule-iv 59%)")
# v8 result
if op:
    open_d = op[0]
    for d_str, reason in cl:
        if "pos_r_drop" in reason and "07-1" in d_str:
            print(f"  v8: PASS? chain_open={open_d}, close={d_str} ({reason})")
            break
    else:
        print(f"  v8: FAIL? opens={op} closes={cl}")
else:
    print(f"  v8: FAIL — no chain open (Bug #9: div fields missing)")

# T2 — TAG wrong-side 07-28→31
print()
print("--- TAG T2 (wrong-side 07-28→31) ---")
_, _, _, _, days_tag = run_chain("TAGUSDT", "2026-06-01", "2026-08-07")
for i, d in enumerate(days_tag):
    date = d.get("date","?")
    if len(date)==5: date="2026-"+date
    if "07-28" <= date <= "07-31":
        skip = d.get("_skip_eval") or d.get("_suspect")
        result = _false_result() if skip else eval_gom(days_tag, i, cfg, sc)
        lsg_vals = [days_tag[j].get("lsr_global",float("nan")) for j in range(max(0,i-4),i+1)]
        avg5 = sum(v for v in lsg_vals if not math.isnan(v))/max(1,len([v for v in lsg_vals if not math.isnan(v)]))
        print(f"  {date}: gom_day={result['gom_day']} avg5_glsr={avg5:.3f} A2_ok={avg5<=1.1}")

# ZBT
print()
print("--- ZBT ---")
zbt_df = df07[df07["symbol"]=="ZBTUSDT"]
print(f"  ZBTUSDT rows in export: {len(zbt_df)}")
if len(zbt_df)>0:
    op_z, ch_z, cl_z, _, _ = run_chain("ZBTUSDT","2026-06-01","2026-08-07")
    print(f"  opens={op_z} closes={cl_z}")
else:
    print(f"  ZBT: NO DATA in freshwatch (delisted — PASS* carried forward)")

# GOM-C rows
print()
print("--- GOM-C β rows ---")

# C1: TUT — fire 07-13 AND 07-21→23
print("C1 (TUT GOM-C β fire 07-13 + 07-21→23):")
_, _, _, tut_c, days_tut = run_chain("TUTUSDT","2026-06-01","2026-08-07")
fires_07 = [d for d in tut_c if "07-13"<=d<="07-23"]
print(f"  GOM-C fires (07-13→07-23): {fires_07}")
if any("07-13" in d for d in fires_07):
    print("  v8: PASS (fire on 07-13)")
else:
    print("  v8: FAIL (no 07-13 fire)")

# C2: BULLA — GOM-C block 07-17→21
print()
print("C2 (BULLA GOM-C β block 07-17→21):")
_, _, _, bulla_c, days_bulla = run_chain("BULLAUSDT","2026-06-01","2026-08-07")
block_07 = [d for d in bulla_c if "07-17"<=d<="07-21"]
if not block_07:
    print(f"  v8: PASS (no GOM-C fire 07-17→21)")
else:
    print(f"  v8: FAIL (GOM-C fires: {block_07})")

# C3: BANK — pos_r harvest (d_pos<0 → block)
print()
print("C3 (BANK pos_r harvest — close 07-16 rule-iv, post-close OI surge blocked):")
# Check BANK GOM-C around 07-16+
_, _, _, bank_c, days_bank = run_chain("BANKUSDT","2026-06-01","2026-08-07")
post_close = [d for d in bank_c if d>"07-16"]
print(f"  GOM-C fires post 07-16: {post_close[:5]}")
# Also check that d_pos<0 blocks around close
for i, d in enumerate(days_bank):
    date = d.get("date","?")
    if len(date)==5: date="2026-"+date
    if "07-14"<=date<="07-18":
        result = eval_gom(days_bank, i, cfg, sc)
        p_now = d.get("lsr_pos",float("nan"))
        p_prv = days_bank[i-1].get("lsr_pos",float("nan")) if i>0 else float("nan")
        d_pos = p_now - p_prv if not (math.isnan(p_now) or math.isnan(p_prv)) else float("nan")
        print(f"  {date}: lsr_pos={p_now:.4f} d_pos={d_pos:+.4f} gomc={'FIRE' if date in bank_c else '----'}")

# C4: BANANAS31 — PENDING 15/08
print()
print("C4 (BANANAS31 negative test — PENDING 15/08):")
bn_df = df07[df07["symbol"]=="BANANAS31USDT"]
if len(bn_df)>0:
    _, _, _, bn_c, _ = run_chain("BANANAS31USDT","2026-06-01","2026-08-07")
    print(f"  GOM-C fires: {bn_c}")
    if bn_c:
        print(f"  v8: FAIL (GOM-C fires on BANANAS31 — negative test)")
    else:
        print(f"  v8: PASS early signal (no fires yet)")
else:
    print("  BANANAS31USDT: NO DATA in export (test pending 15/08)")

# C5: COOKIE/CYS/TST live fires 08-07
print()
print("C5 (COOKIE/CYS/TST live fires 08-07):")
for s in ["COOKIEUSDT","CYSUSDT","TSTUSDT"]:
    s_df = df07[df07["symbol"]==s]
    if len(s_df)==0:
        print(f"  {s.replace('USDT','')}: NO DATA")
        continue
    _, _, _, c_fires, _ = run_chain(s,"2026-06-01","2026-08-07")
    fires_aug = [d for d in c_fires if d>="2026-08-06"]
    print(f"  {s.replace('USDT','')}: GOM-C fires Aug: {fires_aug}")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name

def scp_file2(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return r.returncode == 0

scp_file2(tmp, f"{BASE}/_gate_v8_inner.py")
os.unlink(tmp)

out2, err2 = ssh(f"cd {BASE} && .venv/bin/python3 {BASE}/_gate_v8_inner.py 2>&1", timeout=240)
print()
print(out2)
if err2 and ("Error" in err2 or "Traceback" in err2):
    print("STDERR:", err2[:600])

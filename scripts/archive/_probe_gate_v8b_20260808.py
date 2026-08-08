#!/usr/bin/env python3
# Item 1: GATE §6 v8 — fix SCP space path + use python3 not venv
import sys, subprocess, os, tempfile
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

# 1. Create VPS case dir + upload files via heredoc (avoid SCP space issue)
print("=== Uploading calib files to VPS ===")
# Use mkdir with escaped path
ssh(r"mkdir -p '/root/Data_back_test/binance-bot-signals/docs/case study'")

for fpath in sorted(LOCAL_CASES.glob("*_result.txt")):
    content = fpath.read_text(encoding="utf-8", errors="replace")
    # Escape single quotes in content (shouldn't be any in result.txt files)
    content_safe = content.replace("'", "'\\''")
    remote_path = f"/root/Data_back_test/binance-bot-signals/docs/case study/{fpath.name}"
    # Use cat via stdin approach
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS,
         f"cat > '{remote_path}'"],
        input=content, capture_output=True, encoding="utf-8", errors="replace", timeout=30,
    )
    print(f"  {fpath.name}: {'OK' if r.returncode==0 else 'FAIL rc='+str(r.returncode)}")

# Verify
out_ls, _ = ssh(r"ls '/root/Data_back_test/binance-bot-signals/docs/case study/' | wc -l")
print(f"  VPS case study count: {out_ls}")

# 2. Run --backfill using system python3 (has pyyaml)
print()
print("=== run_backtest6 §6 v8 (system python3) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --backfill 2>&1",
    timeout=300
)
print(out[-8000:] if len(out)>8000 else out)
if err and ("Error" in err or "Traceback" in err):
    print("BACKFILL STDERR:", err[:400])

# 3. Freshwatch-based rows (PARTI, ZBT, TAG T2, GOM-C)
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
    opens, chapters, closes, gomc_fires = [], [], [], []
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
        if not skip and _gomc_beta_check(days, i, cfg, sc, result, check_cooldown=True):
            gomc_fires.append(date)
    return opens, chapters, closes, gomc_fires, days

print()
print("=" * 70)
print("§6 v8 freshwatch-based rows")
print("=" * 70)

# P — PARTI
print()
print("--- Row P: PARTI open+close ---")
print("  Expected: chain2=07-01→07-11 (rule-iv 59%)")
op_p, ch_p, cl_p, gc_p, days_p = run_chain("PARTIUSDT","2026-06-01","2026-08-07")
print(f"  opens={op_p} chapters={ch_p} closes={cl_p}")
pass_p = False
if op_p:
    for d_str, reason in cl_p:
        if "pos_r_drop" in reason:
            pass_p = True
            print(f"  v8: PASS chain_open={op_p[0]}, close={d_str} ({reason})")
            break
    if not pass_p:
        print(f"  v8: FAIL — opens={op_p} but no pos_r_drop close. closes={cl_p}")
else:
    print(f"  v8: FAIL — no chain open (Bug #9: div_* fields missing, A4=always-F)")

# T2 — TAG wrong-side
print()
print("--- Row T2: TAG wrong-side 07-28→31 ---")
print("  Expected: GOM NOT fire 07-28→31 (A2=avg5(gLSR)>1.1)")
_, _, _, _, days_tag = run_chain("TAGUSDT","2026-06-01","2026-08-07")
t2_results = []
for i, d in enumerate(days_tag):
    date = d.get("date","?")
    if len(date)==5: date="2026-"+date
    if "2026-07-28" <= date <= "2026-07-31":
        skip = d.get("_skip_eval") or d.get("_suspect")
        result = _false_result() if skip else eval_gom(days_tag, i, cfg, sc)
        lsg = [days_tag[j].get("lsr_global",float("nan")) for j in range(max(0,i-4),i+1)]
        lsg_ok = [v for v in lsg if not math.isnan(v)]
        avg5 = sum(lsg_ok)/len(lsg_ok) if lsg_ok else float("nan")
        t2_results.append((date, result["gom_day"], avg5))
        print(f"  {date}: gom_day={result['gom_day']} avg5_glsr={avg5:.3f}")
no_fire = all(not r[1] for r in t2_results)
print(f"  v8: {'PASS' if no_fire else 'FAIL'} (gom_day all False={no_fire})")

# ZBT
print()
print("--- Row Z1/Z2: ZBT ---")
zbt_rows = df07[df07["symbol"]=="ZBTUSDT"]
if len(zbt_rows)==0:
    print("  ZBT: NO DATA in freshwatch (delisted) → PASS* carried (v4 calib)")
else:
    op_z, _, cl_z, _, _ = run_chain("ZBTUSDT","2026-06-01","2026-08-07")
    print(f"  opens={op_z} closes={cl_z}")

# GOM-C rows
print()
print("--- GOM-C β rows ---")

# C1: TUT
print("C1 TUT (fire 07-13 AND 07-21→23):")
_, _, _, tut_c, _ = run_chain("TUTUSDT","2026-06-01","2026-08-07")
t13 = [d for d in tut_c if d=="2026-07-13"]
t21_23 = [d for d in tut_c if "2026-07-21"<=d<="2026-07-23"]
print(f"  07-13 fire: {t13} | 07-21→23 fires: {t21_23}")
print(f"  v8: {'PASS' if t13 and t21_23 else 'FAIL'}")

# C2: BULLA blocked
print("C2 BULLA (GOM-C block 07-17→21):")
_, _, _, bulla_c, _ = run_chain("BULLAUSDT","2026-06-01","2026-08-07")
bl = [d for d in bulla_c if "2026-07-17"<=d<="2026-07-21"]
print(f"  GOM-C fires 07-17→21: {bl}")
print(f"  v8: {'PASS (no fire)' if not bl else 'FAIL (fires: '+str(bl)+')'}")

# C3: BANK d_pos<0 blocks after close
print("C3 BANK (d_pos<0 after close 07-16 blocks GOM-C):")
_, _, _, bank_c, days_bank = run_chain("BANKUSDT","2026-06-01","2026-08-07")
post_c = [d for d in bank_c if d>"2026-07-16"]
# Check d_pos around close
dpos_check = []
for i, d in enumerate(days_bank):
    date = d.get("date","?")
    if len(date)==5: date="2026-"+date
    if "2026-07-14"<=date<="2026-07-19":
        p_now = d.get("lsr_pos",float("nan"))
        p_prv = days_bank[i-1].get("lsr_pos",float("nan")) if i>0 else float("nan")
        d_pos = (p_now-p_prv) if not math.isnan(p_now+p_prv) else float("nan")
        dpos_check.append(f"{date}:d_pos={d_pos:+.4f}")
print(f"  d_pos around close: {dpos_check}")
print(f"  GOM-C post-close fires: {post_c}")
print(f"  v8: {'PASS' if not post_c else 'CHECK (post-close fires: '+str(post_c)+')'}")

# C4: BANANAS31
print("C4 BANANAS31 (negative — PENDING 15/08):")
bn_rows = df07[df07["symbol"]=="BANANAS31USDT"]
if len(bn_rows)==0:
    print("  NO DATA → PENDING 15/08")
else:
    _, _, _, bn_c, _ = run_chain("BANANAS31USDT","2026-06-01","2026-08-07")
    print(f"  GOM-C fires: {bn_c}")
    print(f"  v8: {'FAIL (fires)' if bn_c else 'PASS (no fires)'}")

# C5: COOKIE/CYS/TST 08-07
print("C5 COOKIE/CYS/TST (live fires 08-07):")
for s in ["COOKIEUSDT","CYSUSDT","TSTUSDT"]:
    s_rows = df07[df07["symbol"]==s]
    if len(s_rows)==0:
        print(f"  {s.replace('USDT','')}: NO DATA")
        continue
    _, _, _, c_fires, _ = run_chain(s,"2026-06-01","2026-08-07")
    fires_aug = [d for d in c_fires if d>="2026-08-06"]
    print(f"  {s.replace('USDT','')}: GOM-C fires Aug: {fires_aug}")
print(f"  v8: PENDING D2 triage (live verification 08-06/07)")
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(INNER)
    tmp = f.name
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS,
     f"cat > {BASE}/_gate_fw_inner.py"],
    input=open(tmp).read(), capture_output=True, encoding="utf-8", errors="replace", timeout=30,
)
os.unlink(tmp)

out3, err3 = ssh(f"python3 {BASE}/_gate_fw_inner.py 2>&1", timeout=240)
print()
print(out3)
if err3 and ("Error" in err3 or "Traceback" in err3):
    print("STDERR:", err3[:600])

#!/usr/bin/env python3
"""Verbose per-day probe for TUT (07-01→07-20), ZBT (07-15→07-31), IDOL (07-25→08-01)."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def scp(local_path, remote_path):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local_path, f"{VPS}:{remote_path}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return r.returncode == 0

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

inner = r"""#!/usr/bin/env python3
import sys, math
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO    = Path('/root/Data_back_test/whale_data')
BOT_ROOT = Path('/root/Data_back_test/binance-bot-signals')
sys.path.insert(0, str(REPO / 'scripts'))
sys.path.insert(0, str(BOT_ROOT))

# cfg = SIGNALS thresholds (binance-bot-signals/thresholds.yaml)
# sc  = SCREEN thresholds (screen_thresholds.yaml)
from scanner.screener.signals import load_thresholds
from gom_scan import (eval_gom, update_chain, load_screen_cfg, _scfg, _false_result)
from fw_loader_utils import (taker_scale_check_df, load_fw_csvs,
                             load_funding_intervals, build_token_days)

cfg = load_thresholds()
sc  = load_screen_cfg()
g   = _scfg(sc)

STORE      = REPO / 'data' / 'export'
CONFIG_DIR = REPO / 'data' / 'config'
intervals  = load_funding_intervals(CONFIG_DIR)

PROBES = [
    ("TUTUSDT",  "TUT",  "2026-07-20", "2026-07-01", "2026-07-20"),
    ("ZBTUSDT",  "ZBT",  "2026-07-31", "2026-07-15", "2026-07-31"),
    ("IDOLUSDT", "IDOL", "2026-08-01", "2026-07-25", "2026-08-01"),
]

for sym, token, target_date, print_from, print_to in PROBES:
    print(f"\n{'='*90}")
    print(f"PROBE: {token} ({sym})  verbose {print_from}→{print_to}  (target={target_date})")
    print(f"{'='*90}")

    df_all = load_fw_csvs(STORE, target_date, lookback_days=60)
    if df_all.empty:
        print("  NO CSV DATA"); continue
    df_all = taker_scale_check_df(df_all)

    date_to = target_date
    date_from_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=60)
    date_from = date_from_dt.strftime("%Y-%m-%d")
    csv_start = str(df_all["date"].min())
    if csv_start > date_from:
        date_from = csv_start

    days, suspect_dates = build_token_days(df_all, sym, date_from, date_to, intervals)
    if not days:
        print(f"  NO DAYS for {sym}"); continue

    print(f"  Days: {len(days)}  Window: {date_from}→{date_to}")
    print(f"  Suspect ({len(suspect_dates)}): {suspect_dates[:6]}{'...' if len(suspect_dates)>6 else ''}")
    print()
    print(f"  {'Date':<12} A1  A2  A3  A4  A5  B1  B2  B3  B4  DQ/note              GOM    State")
    print(f"  {'-'*100}")

    chain: dict = {}
    for i, d in enumerate(days):
        date = d.get("date", "??")
        skip = d.get("_skip_eval") or d.get("_suspect")

        if skip:
            result = _false_result()
        else:
            result = eval_gom(days, i, cfg, sc)

        chain = update_chain(chain, token, days, i, result, cfg, sc)

        if date < print_from or date > print_to:
            continue

        a = result["gom_a"]
        b = result["gom_b"]
        dq  = [k for k, v in result.get("disqualifier", {}).items() if v]
        gom = result.get("gom_day", False)
        lc  = result.get("low_conf", False)

        def f(v): return "T" if v else "."

        sig = (f"{f(a.get('A1'))} {f(a.get('A2'))} {f(a.get('A3'))} {f(a.get('A4'))} {f(a.get('A5'))}"
               f" | {f(b.get('B1'))} {f(b.get('B2'))} {f(b.get('B3'))} {f(b.get('B4'))}")

        if skip:
            note = "[SUSP]"
            sig = ". . . . . | . . . ."
        elif dq:
            note = "DQ:"+"+".join(dq[:2])
        elif lc:
            note = "low_conf"
        else:
            note = ""

        gom_s = "GOM-A" if result.get("gom_a_fire") else ("GOM-B" if result.get("gom_b_fire") else ("GOM?" if gom else "   "))

        if chain.get("chain_open"):
            nd = chain.get("n_days", 0)
            bk = chain.get("break_streak", 0)
            q1 = chain.get("Q1_cum_usd", 0)
            pr = chain.get("peak_pos_r", math.nan)
            pr_s = f" pr={pr:.2f}" if not math.isnan(pr) else ""
            state_s = f"OPEN n={nd} brk={bk} Q1=${q1:,.0f}{pr_s}"
        elif chain.get("close_date","") == date:
            reason = chain.get("close_reason", "?")
            note2  = chain.get("close_note","")
            state_s = f"CLOSED[{reason[:25]}]{' '+note2 if note2 else ''}"
        elif not chain:
            state_s = "no-chain"
        else:
            close_d = chain.get("close_date","?")
            state_s = f"(closed {close_d})"

        px = d.get("px_avg", math.nan)
        lsr_g = d.get("lsr_global_r", math.nan)
        extra = f" px=${px:.4f}" if not math.isnan(px) else ""
        extra += f" gLSR={lsr_g:.2f}" if not math.isnan(lsr_g) else ""

        print(f"  {date:<12} {sig}  {note:<20}  {gom_s:<6} {state_s}{extra}")

    print()
    co = chain.get("chain_open", False)
    cd = chain.get("close_date","")
    cr = chain.get("close_reason","")
    q1f = chain.get("Q1_cum_usd",0)
    prf = chain.get("peak_pos_r", float("nan"))
    prf_s = f"{prf:.2f}" if not math.isnan(prf) else "nan"
    print(f"  END STATE: open={co}  close_date={cd}  reason={cr}")
    print(f"             Q1=${q1f:,.0f}  peak_pr={prf_s}")

    # ZBT extra: check production Jul CSV for 07-24..07-26
    if token == "ZBT":
        import pandas as pd
        df_j = pd.read_csv(STORE / "freshwatch_daily_2026-07.csv")
        zbt_rows = df_j[df_j["symbol"]==sym]
        gap_rows = zbt_rows[zbt_rows["date"].isin(["2026-07-24","2026-07-25","2026-07-26"])]
        print(f"\n  ZBT gap-dates in production Jul CSV: {len(gap_rows)} rows (expect 0 if MISSING)")
        if not gap_rows.empty:
            print(gap_rows[["date","px_avg","oi_usd","funding_avg","data_ok"]].to_string(index=False))
"""

probe_file = r"D:\Data back test\whale_data\_vps_inner_probe_tut_zbt_idol.py"
with open(probe_file, "w", encoding="utf-8") as f:
    f.write(inner)

print("Deploying probe...")
scp(probe_file, f"{BASE}/_vps_inner_probe_tut_zbt_idol.py")

print("Running probe...")
out, err = ssh(f"python3 {BASE}/_vps_inner_probe_tut_zbt_idol.py 2>&1", timeout=300)
print(out[:15000])
if err:
    print("\n--- STDERR ---")
    print(err[:500])

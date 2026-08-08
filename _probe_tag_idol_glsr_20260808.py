"""Phan xu TAG + IDOL: so sanh lsr_global_r fw CSV vs CASE xlsx gLSR 07-06->20.
Paste series + avg5 + column name, ket luan: bug-col / an-L25 / OK.
"""
import sys, math, json
from pathlib import Path
import pandas as pd

sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals

STORE  = Path("D:/Check onchain fresh wallets/data/export")
CONFIG = Path("data/config")
CASES  = Path("docs/case_files")

intervals = load_funding_intervals(CONFIG)

# Load fw CSV for July
df_jul = pd.read_csv(STORE / "freshwatch_daily_2026-07.csv")
df_aug = pd.read_csv(STORE / "freshwatch_daily_2026-08.csv")
df_all_raw = pd.concat([df_jul, df_aug])

# ── Function: print series for a token ───────────────────────────────────────
def analyze_token(sym, tok, start="2026-07-06", end="2026-07-20"):
    print(f"\n{'='*70}")
    print(f"TOKEN: {tok}  (symbol={sym})")
    print(f"Column read: df['lsr_global_r']  -> day['lsr_global'] -> avg5 in eval_gom")
    print(f"{'='*70}")

    # fw CSV raw values
    df_tok = df_all_raw[df_all_raw["symbol"]==sym].copy()
    df_tok = df_tok[(df_tok["date"]>=start) & (df_tok["date"]<=end)].sort_values("date")

    print(f"\n[FW CSV] {sym} {start}->{end}:")
    print(f"  {'date':<12} {'lsr_pos_r':>10} {'lsr_global_r':>13} {'lsr_acc_r':>10}")
    print(f"  {'-'*50}")
    for _, r in df_tok.iterrows():
        lp  = r.get("lsr_pos_r",   float("nan"))
        lg  = r.get("lsr_global_r", float("nan"))
        la  = r.get("lsr_acc_r",   float("nan"))
        lp  = float(lp)  if not pd.isna(lp) else float("nan")
        lg  = float(lg)  if not pd.isna(lg) else float("nan")
        la  = float(la)  if not pd.isna(la) else float("nan")
        print(f"  {r['date']:<12} {lp:>10.4f} {lg:>13.4f} {la:>10.4f}")

    # build day dicts and compute avg5
    df_fw = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
    from fw_loader_utils import taker_scale_check_df
    df_fw = taker_scale_check_df(df_fw)
    days, _ = build_token_days(df_fw, sym, "2026-06-01", "2026-07-25", intervals)
    enrich_token_days(days)

    # avg5 computation (replicate _avg5_glsr)
    print(f"\n[AVG5 gLSR — from day dicts] {sym} (A2 threshold=1.1):")
    print(f"  {'date':<12} {'lsr_global':>11} {'avg5_gLSR':>11} {'A2=ok?':>8}")
    print(f"  {'-'*48}")
    for d in days:
        dt = d.get("date","")
        if dt < start or dt > end:
            continue
        lg = d.get("lsr_global", float("nan"))
        # compute avg5
        i = days.index(d)
        s = max(0, i-4)
        vals = [days[j].get("lsr_global", float("nan")) for j in range(s, i+1)]
        vals = [v for v in vals if not math.isnan(v)]
        avg5 = sum(vals)/len(vals) if vals else float("nan")
        a2 = "PASS" if not math.isnan(avg5) and avg5 <= 1.1 else "FAIL"
        print(f"  {dt:<12} {lg:>11.4f} {avg5:>11.4f} {a2:>8}")

    # Try to read CASE xlsx
    case_path = CASES / f"CASE_{tok}.xlsx"
    if not case_path.exists():
        print(f"\n  CASE_{tok}.xlsx NOT FOUND at {case_path}")
        return

    try:
        df_case = pd.read_excel(case_path, sheet_name="DAILY", header=1)
        # Find gLSR column
        glsr_col = None
        for col in df_case.columns:
            if "global" in str(col).lower() or "gLSR" in str(col) or "lsr_global" in str(col).lower():
                glsr_col = col
                break
        pos_col = None
        for col in df_case.columns:
            if "pos_r" in str(col).lower() and "lsr" in str(col).lower():
                pos_col = col
                break
        date_col = df_case.columns[0]
        print(f"\n[CASE_{tok}.xlsx DAILY] date_col={date_col}  gLSR_col={glsr_col}  pos_col={pos_col}")
        print(f"  Cols sample: {list(df_case.columns[:15])}")

        # Filter rows
        df_case["_date"] = pd.to_datetime(df_case[date_col], errors="coerce")
        df_filt = df_case[(df_case["_date"] >= pd.Timestamp(start)) &
                          (df_case["_date"] <= pd.Timestamp(end))].copy()
        print(f"\n[CASE xlsx] {tok} {start}->{end}:")
        if glsr_col:
            print(f"  {'date':<12} {'gLSR_xlsx':>10} {'pos_r_xlsx':>11}")
            print(f"  {'-'*38}")
            for _, r in df_filt.iterrows():
                dt_s  = r["_date"].strftime("%Y-%m-%d") if pd.notna(r["_date"]) else "?"
                glsr  = r.get(glsr_col, float("nan"))
                posr  = r.get(pos_col, float("nan")) if pos_col else float("nan")
                glsr  = float(glsr)  if not pd.isna(glsr) else float("nan")
                posr  = float(posr)  if not pd.isna(posr) else float("nan")
                print(f"  {dt_s:<12} {glsr:>10.4f} {posr:>11.4f}")
        else:
            print(f"  gLSR column NOT FOUND. Columns: {list(df_case.columns[:20])}")
    except Exception as e:
        print(f"  ERROR reading xlsx: {e}")

analyze_token("TAGUSDT", "TAG")
analyze_token("IDOLUSDT", "IDOL")
print("\nDone.")

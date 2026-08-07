#!/usr/bin/env python3
"""Check PARTI in local stores + AKE G1 decay series."""
import sys
from pathlib import Path
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WHALE = Path(r"D:\Data back test\whale_data")
BOT   = Path(r"D:\Data back test\binance-bot-signals")

print("=" * 60)
print("PARTI -- local store check")
print("=" * 60)

raw = WHALE / "data" / "raw" / "spot_klines_1d"
dates = sorted([d.name.replace("date=", "") for d in raw.iterdir() if d.is_dir()])
print(f"spot_klines_1d date range: {dates[0]} -> {dates[-1]}, {len(dates)} partitions")

# sample schema
first = next(raw.rglob("*.parquet"), None)
if first:
    df0 = pd.read_parquet(first)
    print("Columns:", list(df0.columns))
    if "symbol" in df0.columns:
        print("Sample symbols:", list(df0["symbol"].unique())[:5])
    elif "venue" in df0.columns:
        print("Venues:", df0["venue"].unique())

# scan all partitions for PARTI
print("\nScanning all partitions for PARTI...")
parti_rows = 0
parti_dates = []
for p in sorted(raw.rglob("*.parquet")):
    try:
        df = pd.read_parquet(p)
        for col in ("symbol", "token"):
            if col in df.columns:
                mask = df[col].str.upper().str.contains("PARTI", na=False)
                if mask.any():
                    parti_rows += mask.sum()
                    date_val = p.parent.name.replace("date=", "")
                    parti_dates.append(date_val)
                break
    except Exception:
        pass

print(f"PARTI rows found: {parti_rows}")
print(f"PARTI dates: {parti_dates[:5]}" if parti_dates else "PARTI dates: none")

# check freshwatch daily CSV (if synced)
fw_files = list(WHALE.glob("**/freshwatch_daily*.csv")) + list(WHALE.glob("scratch/*.csv"))
print(f"\nfreshwatch CSV local: {fw_files}")

print()
print("=" * 60)
print("PARTI -- case file check")
print("=" * 60)
case_parti = WHALE / "docs" / "case_files" / "CASE_PARTI.xlsx"
result_parti = BOT / "docs" / "case study" / "PARTI_result.txt"
print(f"CASE_PARTI.xlsx exists: {case_parti.exists()}")
print(f"PARTI_result.txt exists: {result_parti.exists()}")

# look for any PARTI mention in case study dir
for f in (BOT / "docs" / "case study").glob("*PARTI*"):
    print(f"  Found: {f}")

print()
print("=" * 60)
print("AKE -- G1 decay series check (07-05 to 07-12)")
print("=" * 60)

sys.path.insert(0, str(BOT))
sys.path.insert(0, str(WHALE))
from scanner.screener.signals import load_thresholds, decay as decay_fn
import importlib.util
_spec_m = importlib.util.spec_from_file_location("replay", BOT / "replay.py")
_mod    = importlib.util.module_from_spec(_spec_m); _spec_m.loader.exec_module(_mod)
parse_result_file = _mod.parse_result_file
build_days        = _mod.build_days
_token_from_path  = _mod._token_from_path

cfg = load_thresholds()

def load_txt(token_stem):
    for fp in (BOT / "docs" / "case study").glob("*_result.txt"):
        tok = _token_from_path(fp)
        if tok.upper() == token_stem.upper():
            f, o, r, k = parse_result_file(fp)
            return build_days(f, o, r, k)
    return []

ake_days = load_txt("AKE")
if not ake_days:
    print("AKE result.txt not found")
else:
    print(f"AKE data range: {ake_days[0]['date']} -> {ake_days[-1]['date']}, {len(ake_days)} days")
    print(f"\n  {'date':>6}  {'taker_buy%':>10}  {'decay':>6}  note")
    for i, d in enumerate(ake_days):
        if d["date"] < "07-03" or d["date"] > "07-12":
            continue
        dec = decay_fn(ake_days, i, cfg)
        tb = d.get("taker_buy_pct", float("nan"))
        note = ""
        if d["date"] == "07-08":
            note = "<-- alleged mis-fire date (flash-crash?)"
        print(f"  {d['date']:>6}  {tb:>10.1f}  {'Y' if dec else '.':>6}  {note}")

    # Also show the decay threshold
    decay_cfg = cfg.get("decay", {})
    print(f"\n  decay config: taker_buy_max={decay_cfg.get('taker_buy_max')}, decay_days_min={decay_cfg.get('decay_days_min')}")
    # Show raw taker values 07-04 to 07-12
    print(f"\n  Raw taker_buy_pct 07-04->07-12:")
    for d in ake_days:
        if "07-04" <= d["date"] <= "07-12":
            print(f"    {d['date']}: {d.get('taker_buy_pct', 'nan'):.1f}%")

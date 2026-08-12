"""
C4-readiness: BANANAS31 taker_buy_pct — perp futures source check.
GOM-C backtest reads from fw_loader (perp daily store), not Alpha spot_klines.
Check taker_buy_pct in daily_2026-07.csv (canonical local snapshot).
"""
import pathlib
import pandas as pd
import sys

# Source 1: daily snapshot CSV (perp futures canonical)
snap_path = pathlib.Path("data/daily_2026-07.csv")
if snap_path.exists():
    df = pd.read_csv(snap_path, low_memory=False)
    b31 = df[df["symbol"].str.upper().str.contains("BANANAS31", na=False)]
    print(f"[daily_2026-07.csv] rows for BANANAS31: {len(b31)}")
    if not b31.empty:
        cols = [c for c in ["symbol","date","taker_buy_pct","taker_abstain"] if c in b31.columns]
        print(b31[cols].to_string())
    else:
        print("  → not found")
else:
    print(f"[SKIP] {snap_path} not found")

# Source 2: gom_state.json — check if BANANAS31 in fw universe
state_path = pathlib.Path("data/gom_state.json")
if state_path.exists():
    import json
    with open(state_path) as f:
        state = json.load(f)
    symbols = list(state.keys()) if isinstance(state, dict) else []
    b31_keys = [s for s in symbols if "BANANAS31" in s.upper()]
    print(f"\n[gom_state.json] BANANAS31 keys: {b31_keys}")
else:
    print(f"\n[SKIP] gom_state.json not found")

# Source 3: fw_universe list (fw139)
fw_path = pathlib.Path("data/config/freshwatch_symbols.txt")
if fw_path.exists():
    syms = fw_path.read_text().strip().splitlines()
    b31_fw = [s for s in syms if "BANANAS31" in s.upper()]
    print(f"\n[fw139] BANANAS31: {b31_fw}")
else:
    print(f"\n[SKIP] freshwatch_symbols.txt not found")

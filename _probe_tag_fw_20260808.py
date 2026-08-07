#!/usr/bin/env python3
"""Check if TAGUSDT exists in freshwatch CSVs and find 07-28→31 data."""
import sys, csv, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD = Path(r"D:\Data back test\whale_data")

for csv_file in sorted(WD.glob("scratch/freshwatch_daily_2026-*.csv")):
    print(f"\n=== {csv_file.name} ===")
    try:
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        tag_rows = [r for r in rows if r.get("symbol","").upper() in ("TAG","TAGUSDT")]
        print(f"  TAG rows found: {len(tag_rows)}")
        for r in tag_rows:
            date = r.get("date","?")
            glsr = r.get("lsr_global_r","?")
            pos_r = r.get("lsr_pos_r","?")
            print(f"  {date}  gLSR={glsr}  lsr_pos_r={pos_r}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Also check gom_state.json for any TAG history
import json
state_file = WD / "data" / "gom_state.json"
if state_file.exists():
    try:
        with open(state_file) as f:
            state = json.load(f)
        tag_state = {k: v for k, v in state.items() if "TAG" in k.upper()}
        if tag_state:
            print(f"\nGOM state TAG entries: {json.dumps(tag_state, indent=2)[:500]}")
        else:
            print(f"\nNo TAG in gom_state.json")
    except Exception as e:
        print(f"\ngom_state.json error: {e}")

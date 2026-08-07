#!/usr/bin/env python3
"""PARTI onboard date + early data check."""
import sys, json, math, csv
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import urllib.request

WD = Path(r"D:\Data back test\whale_data")

# 1. Fapi exchangeInfo — onboardDate for PARTIUSDT
print("=== PARTI fapi exchangeInfo ===")
url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
try:
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())
    symbols = data.get("symbols", [])
    parti = next((s for s in symbols if s.get("symbol") == "PARTIUSDT"), None)
    if parti:
        onboard_ms = parti.get("onboardDate", 0)
        onboard_dt = datetime.fromtimestamp(onboard_ms / 1000, tz=timezone.utc)
        print(f"  symbol:       {parti['symbol']}")
        print(f"  onboardDate:  {onboard_ms} → {onboard_dt.strftime('%Y-%m-%d')} UTC")
        print(f"  status:       {parti.get('status')}")
        print(f"  contractType: {parti.get('contractType')}")
    else:
        print("  PARTIUSDT NOT FOUND in fapi exchangeInfo (possibly delisted)")
except Exception as e:
    print(f"  ERROR: {e}")

# 2. Check all freshwatch CSVs in scratch for PARTI rows
print()
print("=== PARTI rows in scratch/ freshwatch CSVs ===")
for csv_file in sorted(WD.glob("scratch/freshwatch_daily_2026-*.csv")):
    try:
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        parti_rows = [r for r in rows if r.get("symbol","").upper() in ("PARTI","PARTIUSDT")]
        if parti_rows:
            first = parti_rows[0].get("date","?")
            last  = parti_rows[-1].get("date","?")
            print(f"  {csv_file.name}: {len(parti_rows)} rows  {first} → {last}")
            # Show first 5
            for r in parti_rows[:5]:
                taker = r.get("taker_buy_pct","?")
                glsr  = r.get("lsr_global_r","?")
                posr  = r.get("lsr_pos_r","?")
                print(f"    {r['date']}  taker={taker}  gLSR={glsr}  pos_r={posr}")
            if len(parti_rows) > 5:
                print(f"    ... ({len(parti_rows)-5} more rows)")
        else:
            print(f"  {csv_file.name}: 0 PARTI rows")
    except Exception as e:
        print(f"  {csv_file.name}: ERROR {e}")

# 3. Check universe store for PARTI entry date
print()
print("=== PARTI in universe/config files ===")
for pat in ["data/config/*.json", "data/config/*.yaml", "data/config/*.csv"]:
    for f in WD.glob(pat):
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
            if "PARTI" in txt.upper():
                print(f"  Found in {f.name}")
                # Show relevant lines
                for i, line in enumerate(txt.splitlines()):
                    if "PARTI" in line.upper():
                        print(f"    L{i+1}: {line.strip()[:120]}")
                        break
        except Exception:
            pass

# 4. Check if there's a daily store partition for PARTI
print()
print("=== PARTI in data/raw partitions ===")
parti_parts = sorted(WD.glob("data/raw/*/PARTIUSDT*"))[:10]
if parti_parts:
    for p in parti_parts[:5]:
        print(f"  {p}")
else:
    print("  No PARTIUSDT partitions found in data/raw/")

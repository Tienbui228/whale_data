#!/usr/bin/env python3
"""Probe: TAG alpha store — check all available data."""
import io, sys
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

store = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")
partitions = sorted(store.glob("date=2026-*"))

tag_records = []

for p in partitions:
    files = list(p.glob("*.parquet"))
    if not files:
        continue
    try:
        df = pd.read_parquet(files[0])
        # TAG in alpha store is symbol='TAG', venue='binance_alpha'
        tag = df[df['symbol'] == 'TAG'] if 'symbol' in df.columns else pd.DataFrame()
        if len(tag):
            row = tag.iloc[0]
            tag_records.append({
                'date': p.name.replace("date=", ""),
                'open': row.get('open'),
                'close': row.get('close'),
                'high': row.get('high'),
                'low': row.get('low'),
                'quote_vol': row.get('quote_vol', row.get('vol_quote', row.get('volume_quote'))),
                'taker_abstain': row.get('taker_abstain'),
                'venue': row.get('venue'),
            })
    except Exception as e:
        pass

print(f"TAG alpha records: {len(tag_records)}")
if tag_records:
    print(f"Date range: {tag_records[0]['date']} → {tag_records[-1]['date']}")
    print("\nAll columns in store:")
    # Re-read one file for full schema
    p = sorted(store.glob("date=2026-07-*"))[0]
    df = pd.read_parquet(list(p.glob("*.parquet"))[0])
    tag_row = df[df['symbol'] == 'TAG'].iloc[0]
    print(dict(tag_row))

    print(f"\nLast 10 dates:")
    for r in tag_records[-10:]:
        qv = r['quote_vol']
        qv_m = f"{qv/1e6:.2f}M" if qv else "None"
        print(f"  {r['date']}: open={r['open']}, close={r['close']}, vol={qv_m}, taker_abstain={r['taker_abstain']}")

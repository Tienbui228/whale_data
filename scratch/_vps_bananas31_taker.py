"""Full BANANAS31 taker_buy_pct from freshwatch_daily store on VPS."""
import csv, pathlib

store = pathlib.Path('/root/Data_back_test/whale_data/data/export')
files = sorted(store.glob('freshwatch_daily_*.csv'))

rows_b31 = []
for fpath in files:
    with open(fpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'BANANAS31' in row.get('symbol','').upper():
                rows_b31.append(row)

print('Source: /data/export/freshwatch_daily_*.csv')
print('Files searched:', [f.name for f in files])
print('Total rows:', len(rows_b31))
print()

floats = []
for r in rows_b31:
    t_raw = r.get('taker_buy_pct','')
    t_pct = float(t_raw)*100.0 if t_raw else float('nan')
    floats.append(t_pct)
    print('%s  taker_raw=%-8s  taker_pct(x100)=%.2f%%' % (
        r.get('date','?'), t_raw[:8], t_pct))

print()
valid = [v for v in floats if v==v]
if valid:
    print('min=%.2f%%  max=%.2f%%  mean=%.2f%%' % (min(valid), max(valid), sum(valid)/len(valid)))
    print('rows >= 99.9%%: %d / %d' % (sum(1 for v in valid if v>=99.9), len(valid)))

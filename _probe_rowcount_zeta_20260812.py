"""
[1] Chốt BANANAS31 row-count: head/tail/count thật từ freshwatch_daily_*.csv
[2] ZETA 92.74%: bao nhiêu ngày > 55% raw (= >55% sau ×100)?
"""
import sys, pathlib, csv
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
from fw_loader_utils import load_fw_csvs

EXPORT_DIR = pathlib.Path("data/export")

# ── [1] BANANAS31 raw CSV rows ─────────────────────────────────────────────────
rows_b31 = []
for fpath in sorted(EXPORT_DIR.glob("freshwatch_daily_*.csv")):
    with open(fpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("symbol", "") == "BANANAS31USDT":
                rows_b31.append(row)
rows_b31.sort(key=lambda r: r.get("date", ""))

print("=== BANANAS31 CSV rows (freshwatch_daily_*.csv) ===")
print(f"Total: {len(rows_b31)}")
print(f"Start: {rows_b31[0]['date']}   End: {rows_b31[-1]['date']}")
print()
print("HEAD (5):")
for r in rows_b31[:5]:
    print(f"  {r['date']}  taker_raw={r.get('taker_buy_pct','?')}")
print("TAIL (5):")
for r in rows_b31[-5:]:
    print(f"  {r['date']}  taker_raw={r.get('taker_buy_pct','?')}")
print()

# Which May dates exist?
may_rows = [r for r in rows_b31 if r["date"].startswith("2026-05")]
print(f"May 2026 rows ({len(may_rows)}): {[r['date'] for r in may_rows]}")
jun_onwards = [r for r in rows_b31 if r["date"] >= "2026-06-01"]
print(f"Jun 1 onwards: {len(jun_onwards)} CSV rows")
print()

# Evaluable window: build_token_days Jun 1 - Aug 11 → 72 calendar days
# i=0=Jun-01, i_min_eval=18 → Jun-01 + 18 days = ?
import datetime
d0 = datetime.date(2026, 6, 1)
i_min = d0 + datetime.timedelta(days=18)
print(f"build_token_days Jun-01 to Aug-11: 72 calendar days")
print(f"i=0 = 2026-06-01")
print(f"i_min_eval = 18 → {i_min.isoformat()}")
# Confirm Jul 24/25/26 missing
jul_missing = [f"2026-07-{d:02d}" for d in [24,25,26]]
found_missing = [d for d in jul_missing if d in [r["date"] for r in rows_b31]]
print(f"Jul 24/25/26 in CSV? {found_missing if found_missing else 'ABSENT — 3 synthetic NaN days'}")
print()

# ── [2] ZETA: how many raw days > 0.55 (= >55% post-scale) ───────────────────
rows_zeta = []
for fpath in sorted(EXPORT_DIR.glob("freshwatch_daily_*.csv")):
    with open(fpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("symbol", "") == "ZETAUSDT":
                rows_zeta.append(row)
rows_zeta.sort(key=lambda r: r.get("date", ""))

above55 = [(r["date"], float(r["taker_buy_pct"])) for r in rows_zeta
           if r.get("taker_buy_pct") and float(r["taker_buy_pct"]) > 0.55]
print("=== ZETAUSDT: days with raw taker > 0.55 (= >55% post-scale) ===")
print(f"Total ZETA CSV rows: {len(rows_zeta)}")
print(f"Days > 0.55 raw: {len(above55)}")
for date, val in above55:
    print(f"  {date}  raw={val:.4f}  post×100={val*100:.2f}%")

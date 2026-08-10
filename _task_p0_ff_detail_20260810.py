"""P0: FF full chain detail from VPS state + A1-A5 per-day on current data."""
from __future__ import annotations
import sys, io, json, csv
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT  = Path("/root/Data_back_test/whale_data")
STATE = ROOT / "data" / "gom_state.json"
STORE = ROOT / "data" / "export"

st = json.loads(STATE.read_text(encoding="utf-8"))

print("=== FF FULL STATE ENTRY (VPS current) ===")
ff = st.get("FF", {})
for k, v in sorted(ff.items()):
    print(f"  {k}: {v}")

print()
print("=== 1 OPEN CHAIN (still in fw universe) ===")
# Load fw symbols
fw_path = ROOT / "data" / "config" / "freshwatch_symbols.txt"
fw_syms = set()
if fw_path.exists():
    fw_syms = {l.strip() for l in fw_path.read_text().splitlines() if l.strip()}
fw_base = {s[:-4] if s.endswith("USDT") else s for s in fw_syms}
open_in_fw = {t: c for t, c in st.items() if c.get("chain_open") and t in fw_base}
print(f"Open AND in fw: {sorted(open_in_fw.keys())}")

print()
print("=== FF A1-A5 per-day (last 30d) ===")
# Load freshwatch CSVs for last 60 days
import itertools
from datetime import datetime, timezone, timedelta
today = datetime(2026, 8, 10, tzinfo=timezone.utc)
months = sorted(set(
    (today - timedelta(days=d)).strftime("%Y-%m")
    for d in range(61)
))

rows_all = []
for m in months:
    p = STORE / f"freshwatch_daily_{m}.csv"
    if p.exists():
        with open(p, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("symbol") in ("FFUSDT",):
                    rows_all.append(row)

# Sort by date
rows_all.sort(key=lambda r: r.get("date", ""))
rows_by_date = {r["date"]: r for r in rows_all}

# Load thresholds
import yaml
try:
    thr_raw = yaml.safe_load((ROOT / "screen_thresholds.yaml").read_text())
    g = thr_raw.get("gom", thr_raw)
    A1_OI_MULT = float(g.get("oi_vs_med14_min", 1.5))
    A2_LSR_MIN = float(g.get("lsr_min", 1.1))
    A3_SLOPE   = float(g.get("glsr_slope_min", 1.0))
    A4_TAKER   = float(g.get("taker_buy_pct_min", 50.0))
    A5_VOL     = float(g.get("vol_vs_med14_min", 1.0))
    print(f"Thresholds: A1 oi_mult≥{A1_OI_MULT} A2 lsr≥{A2_LSR_MIN} A3 slope≥{A3_SLOPE} A4 taker≥{A4_TAKER} A5 vol≥{A5_VOL}")
except Exception as e:
    print(f"Threshold load failed: {e}")
    A1_OI_MULT, A2_LSR_MIN, A3_SLOPE, A4_TAKER, A5_VOL = 1.5, 1.1, 1.0, 50.0, 1.0

def sf(v):
    try: return float(v) if v not in (None, "", "N/A") else None
    except: return None

print(f"\n{'date':<12} {'px':>8} {'oi_mult':>8} {'pos_r':>7} {'slope':>7} {'taker':>7} {'vol_mult':>8} A1 A2 A3 A4 A5 FIRE")
print("-" * 90)

last30_dates = sorted(rows_by_date.keys())[-30:]
for dt in last30_dates:
    r = rows_by_date[dt]
    px      = sf(r.get("px_avg"))
    oi_mult = sf(r.get("oi_vs_med14"))
    pos_r   = sf(r.get("pos_r"))
    slope   = sf(r.get("glsr_slope_5d"))
    taker   = sf(r.get("taker_buy_pct"))
    vol_mult= sf(r.get("vol_vs_med14"))

    a1 = oi_mult is not None and oi_mult >= A1_OI_MULT
    a2 = pos_r   is not None and pos_r   >= A2_LSR_MIN
    a3 = slope   is not None and slope   >= A3_SLOPE
    a4 = taker   is not None and taker   >= A4_TAKER
    a5 = vol_mult is not None and vol_mult>= A5_VOL

    def fmt(v, prec=2): return f"{v:.{prec}f}" if v is not None else "N/A"
    fire = all([a1, a2, a3, a4, a5])
    row = (f"  {dt:<12} {fmt(px,6):>8} {fmt(oi_mult):>8} {fmt(pos_r):>7} {fmt(slope):>7} "
           f"{fmt(taker,1):>7} {fmt(vol_mult):>8} "
           f"{'✓' if a1 else '✗'} {'✓' if a2 else '✗'} {'✓' if a3 else '✗'} "
           f"{'✓' if a4 else '✗'} {'✓' if a5 else '✗'} {'FIRE' if fire else '-'}")
    print(row)

print(f"\n[FF A1-A5 done — {len(last30_dates)} days checked]")

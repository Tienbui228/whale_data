#!/usr/bin/env python3
"""PARTI gate fix v2:
  (1) toi_dq = symbol age from onboard date (2025-03-25), NOT window index
  (2) taker_buy_pct: freshwatch stores decimal (0.47), signals.py expects pct (47.0) → ×100
  (3) Rerun PARTI 06-27→07-31 with fixes
  (4) Taker series 07-01→09 for decay analysis
"""
import sys, math, csv
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD  = Path(r"D:\Data back test\whale_data")
BOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(WD))
sys.path.insert(0, str(BOT))

import importlib.util as _ilu
import yaml

# Load gom_scan module
_gs = _ilu.spec_from_file_location("gom_scan", WD / "scripts" / "gom_scan.py")
_gm = _ilu.module_from_spec(_gs); _gs.loader.exec_module(_gm)
eval_gom    = _gm.eval_gom
update_chain = _gm.update_chain
cfg = _gm.load_thresholds()
sc  = yaml.safe_load((WD / "screen_thresholds.yaml").read_text(encoding="utf-8"))

PARTI_ONBOARD = datetime(2025, 3, 25)
FW = [WD / "scratch" / "freshwatch_daily_2026-06.csv",
      WD / "scratch" / "freshwatch_daily_2026-07.csv"]

def norm(d):
    return "2026-" + d if d and len(d) == 5 else d

def _flt(row, key, fallback=float("nan")):
    try:
        v = row.get(key, "")
        return float(v) if v not in ("", None, "nan") else fallback
    except Exception:
        return fallback

# ── Load PARTI with FIXED taker_buy_pct (×100: decimal→percent) ───────────
def load_parti():
    rows_raw = []
    for csv_file in FW:
        if not csv_file.exists():
            continue
        with open(csv_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("symbol","").upper() in ("PARTI","PARTIUSDT"):
                    rows_raw.append(row)
    rows_raw.sort(key=lambda r: r.get("date",""))

    days = []
    prev_px = float("nan")
    for row in rows_raw:
        px = _flt(row, "px_avg")
        ret = (px - prev_px) / prev_px if not math.isnan(prev_px) and prev_px > 0 else float("nan")
        taker_raw = _flt(row, "taker_buy_pct")
        d = {
            "date":          str(row.get("date",""))[-5:],
            "listing_date":  "2025-03-25",  # fapi onboardDate for PARTIUSDT → toi_dq uses age
            "avg_px":        px,
            "ret_1d":        ret,
            "vol_quote":     _flt(row, "vol_quote"),
            "taker_buy_pct": taker_raw * 100 if not math.isnan(taker_raw) else float("nan"),  # ×100: decimal→pct
            "funding_avg":   _flt(row, "funding_avg"),
            "funding_min":   _flt(row, "funding_min"),
            "funding_max":   _flt(row, "funding_max"),
            "funding_n":     _flt(row, "funding_n"),
            "oi_usd":        _flt(row, "oi_usd"),
            "lsr_pos":       _flt(row, "lsr_pos_r"),
            "lsr_acc":       _flt(row, "lsr_acc_r"),
            "lsr_global":    _flt(row, "lsr_global_r"),
        }
        prev_px = px
        days.append(d)
    return days

days_parti = load_parti()
print(f"PARTI data: {len(days_parti)} rows  {days_parti[0]['date']} → {days_parti[-1]['date']}")
print(f"PARTI onboard: 2025-03-25  Age at 06-27: {(datetime(2026,6,27)-PARTI_ONBOARD).days}d → toi_dq CLEAR")
print()

# ── Taker series 06-27→07-14 with corrected units ─────────────────────────
print("=== Taker series 06-27→07-14 (FIXED ×100) ===")
print(f"  {'date':>10}  {'taker%':>7}  {'<48%':>5}  decay_window(5d)")
tb_max = cfg["decay"]["taker_buy_max"]
for i, d in enumerate(days_parti):
    date = d.get("date","?")
    if date > "07-14":
        continue
    t = d.get("taker_buy_pct", float("nan"))
    below = not math.isnan(t) and t < tb_max
    start5 = max(0, i - 4)
    w5 = [days_parti[j].get("taker_buy_pct", float("nan")) for j in range(start5, i + 1)]
    consec = len([v for v in w5 if not math.isnan(v)]) == 5 and all(v < tb_max for v in w5 if not math.isnan(v))
    flag = " ← DECAY_FIRE" if consec else ""
    print(f"  {norm(date):>10}  {t:>6.1f}%  {'Y' if below else 'N':>5}  {[round(v,1) for v in w5]}{flag}")
print()

# ── Run PARTI with fixes in gom_scan.py ──────────────────────────────────
# DayData has listing_date="2025-03-25" → toi_dq uses age (459d >> 14d → CLEAR)
# taker_buy_pct already ×100 in loader
state, closes = {}, []
history = []
for i, d in enumerate(days_parti):
    res = eval_gom(days_parti, i, cfg, sc)
    was_open = state.get("chain_open", False)
    state = update_chain(state, "PARTI", days_parti, i, res, cfg, sc)
    is_open = state.get("chain_open", False)
    date = norm(d.get("date","??"))
    if was_open and not is_open:
        closes.append((date, state.get("close_reason",""), state.get("close_note","")))

    age_days = (datetime.strptime(date, "%Y-%m-%d") - PARTI_ONBOARD).days
    history.append({
        "date": date,
        "gom":  res["gom_day"],
        "a1":   res["gom_a"]["A1"],
        "a2":   res["gom_a"]["A2"],
        "b1":   res["gom_b"]["B1"],
        "b3":   res["gom_b"]["B3"],
        "b4":   res["gom_b"]["B4"],
        "supp":   {k: v for k, v in res["supp_dq"].items() if v},
        "perday": {k: v for k, v in res["perday_dq"].items() if v},
        "chain_open": is_open,
        "age_d": age_days,
        "pos_r": d.get("lsr_pos", float("nan")),
        "glsr":  d.get("lsr_global", float("nan")),
    })

print("=== PARTI GOM series (toi_dq=age-based, taker=pct-fixed) ===")
print(f"  {'date':>10}  {'gom':>5}  {'A1':>4}  {'A2':>4}  {'age_d':>6}  {'supp':<30}  {'perday':<25}  pos_r")
for h in history:
    if h["date"] <= "2026-07-15":
        s_str = str(list(h["supp"].keys())) if h["supp"] else "-"
        p_str = str(list(h["perday"].keys())) if h["perday"] else "-"
        print(f"  {h['date']:>10}  {str(h['gom']):>5}  {str(h['a1']):>4}  {str(h['a2']):>4}  "
              f"{h['age_d']:>6}  {s_str:<30}  {p_str:<25}  {h['pos_r']:.4f}")
print()

chain_opens = [h["date"] for h in history if h["chain_open"]]
parti_open  = chain_opens[0] if chain_opens else None
print(f"Chain opens: {parti_open or 'NEVER'}")
print(f"Chain closes: {closes}")
print()

# ── Summary of gate result ────────────────────────────────────────────────
print("=== GATE ROW P (fixed) ===")
if parti_open and closes:
    cl_d, cl_r, cl_n = closes[0]
    print(f"  PASS: open={parti_open}  close={cl_d}  reason={cl_r}  note={cl_n}")
elif parti_open:
    last = history[-1]["date"]
    print(f"  PARTIAL: open={parti_open}  still open at {last}")
else:
    # Show why it never opened
    print("  FAIL/PARTIAL: chain never opened")
    print("  First blocker per day 06-27→07-10:")
    for h in history:
        if h["date"] <= "2026-07-10":
            blocker = []
            if h["supp"]: blocker.append(f"SUPP:{list(h['supp'].keys())}")
            if h["perday"]: blocker.append(f"PERDAY:{list(h['perday'].keys())}")
            if not h["a1"] and not h["a2"]: blocker.append("no-A-signal")
            print(f"    {h['date']}  gom={h['gom']}  {' | '.join(blocker)}")

print()
print("=== DATA START EXPLANATION ===")
print("  PARTI onboard fapi: 2025-03-25 (459d before 06-27)")
print("  freshwatch_daily_2026-06.csv first PARTI row: 2026-06-27")
print("  Reason: PARTI was added to FreshWatch universe ~2026-06-27")
print("  (backfill ran 05-18→ but PARTI first in u50 filter ~06-27 entry)")
print("  No earlier PARTI data exists in local scratch/ — VPS SCP only has 06-27+")
print("  toi_dq at 06-27: age=459d >> 14d → CLEAR (fix removes spurious i<13 block)")

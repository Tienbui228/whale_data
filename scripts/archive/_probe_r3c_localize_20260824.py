#!/usr/bin/env python3
"""[R3-c localize] BULLA 06-29→07-15 per-day b1/b2/b3/b4 trên STORE + div_avg3
song song (store vs _result.txt) + taker (store vs _result.txt).

KHÔNG sửa gì — chỉ paste bảng.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT))

from replay import parse_result_file, build_days
import scripts.gom_scan as gom_scan

cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)
sc = {}

# ─── STORE (freshwatch canonical) ───
rows_store = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if not p.exists(): continue
    df = pd.read_csv(p)
    df = df[df["symbol"] == "BULLAUSDT"].sort_values("date")
    for _, r in df.iterrows():
        rows_store.append(r)

def _f(r, k):
    try: return float(r[k])
    except: return float("nan")

funding_new, oi_new, ratio_new, klines_new = {}, {}, {}, {}
store_by_date = {}
for r in rows_store:
    d = r["date"]
    mmdd = d[5:]
    # build_days expects: f["avg"], f["min"], f["max"] for funding; o (float) for oi;
    # r["lsr_pos","lsr_acc","lsr_global","taker_ratio"] for ratio;
    # k["avg_px","vol_quote","taker_buy_pct"] for klines
    funding_new[mmdd] = {"avg": _f(r,"funding_avg"), "min": _f(r,"funding_min"), "max": _f(r,"funding_max")}
    oi_new[mmdd] = _f(r,"oi_usd")
    ratio_new[mmdd] = {
        "lsr_pos": _f(r,"lsr_pos_r"),
        "lsr_acc": _f(r,"lsr_acc_r"),
        "lsr_global": _f(r,"lsr_global_r"),
        "taker_ratio": _f(r,"taker_ratio"),
    }
    klines_new[mmdd] = {
        "avg_px": _f(r,"px_avg"),
        "vol_quote": _f(r,"vol_quote"),
        "taker_buy_pct": _f(r,"taker_buy_pct") * 100 if _f(r,"taker_buy_pct") == _f(r,"taker_buy_pct") else float("nan"),
    }
    store_by_date[mmdd] = {"pos_r": _f(r,"lsr_pos_r"), "acc_r": _f(r,"lsr_acc_r"), "gLSR": _f(r,"lsr_global_r"), "taker": _f(r,"taker_ratio")}

days_store = build_days(funding_new, oi_new, ratio_new, klines_new)

# ─── _result.txt (bulla_result.txt) ───
fps = list((BOT / "docs" / "case study").glob("bulla*_result.txt"))
fpath = fps[0]
funding_r, oi_r, ratio_r, klines_r = parse_result_file(fpath)
days_result = build_days(funding_r, oi_r, ratio_r, klines_r)
result_by_date = {}
for d in days_result:
    mmdd = d.get("date", "")
    if len(mmdd) == 10: mmdd = mmdd[5:]
    if not mmdd: continue
    result_by_date[mmdd] = {
        "pos_r": d.get("lsr_pos"),
        "acc_r": d.get("lsr_acc"),
        "gLSR": d.get("lsr_global"),
        "taker": d.get("taker_ratio"),
    }

# ─── div_avg3 helper (avg of past 3 days including current) ───
def _div_avg3(days, i, key):
    if i < 2: return float("nan")
    vals = []
    for j in range(max(0,i-2), i+1):
        v = days[j].get(key)
        try: vals.append(float(v))
        except: pass
    if not vals: return float("nan")
    return sum(vals) / len(vals)

# ─── Compute per-day b1/b2/b3/b4 on STORE ───
dates_window = ["06-29","06-30","07-01","07-02","07-03","07-04","07-05","07-06","07-07",
                "07-08","07-09","07-10","07-11","07-12","07-13","07-14","07-15"]

print("═" * 130)
print(" [R3-c localize] BULLA per-day b1/b2/b3/b4 trên STORE + div_avg3(store vs _result) + taker(store vs _result)")
print("═" * 130)
print(f"  {'date':>6}  {'i_st':>4}  {'b1':>3} {'b2':>3} {'b3':>3} {'b4':>3}  {'HBS':>4}  "
      f"{'div3_st':>8} {'div3_rt':>8}   {'taker_st':>9} {'taker_rt':>9}   {'note':<25}")
print("  " + "─" * 125)

# Build i index for store days
store_i_by_date = {}
for i in range(len(days_store)):
    d = days_store[i]
    mmdd = d.get("date","")
    if len(mmdd) == 10: mmdd = mmdd[5:]
    if mmdd:
        store_i_by_date[mmdd] = i

# Build i index for result days
result_i_by_date = {}
for i in range(len(days_result)):
    d = days_result[i]
    mmdd = d.get("date","")
    if len(mmdd) == 10: mmdd = mmdd[5:]
    if mmdd:
        result_i_by_date[mmdd] = i

for date_str in dates_window:
    i_st = store_i_by_date.get(date_str)
    i_rt = result_i_by_date.get(date_str)
    if i_st is None:
        print(f"  {date_str:>6}  <not in store>")
        continue
    try:
        r = gom_scan.eval_gom(days_store, i_st, cfg, sc)
    except Exception as e:
        print(f"  {date_str:>6}  ERROR: {type(e).__name__}: {e}")
        continue
    gb = r.get("gom_b", {})
    b1, b2, b3, b4 = gb.get("B1",False), gb.get("B2",False), gb.get("B3",False), gb.get("B4",False)
    hbs = r.get("hedge_base_strict", False)
    # [BUGFIX-BACKFILL-20260824] Canonical M1 spec: div_ratio = avg3(pos)/avg3(acc)
    # per signals.py:106-124 + lib/hedge_episode.py:45-51 calc_div. Bản gốc R3-c
    # archive (pre-backfill) tính nghịch acc/pos → display column 2.818 = 1/0.355.
    # HBS/B1-B4 decisions không ảnh hưởng (eval_gom internal dùng canonical).
    def _div_ratio(d):
        pos = d.get("lsr_pos"); acc = d.get("lsr_acc")
        try:
            pos, acc = float(pos), float(acc)
            return pos / acc if acc > 0 else float("nan")
        except: return float("nan")
    # avg3 rolling
    def _avg3_div(days, i):
        if i < 2: return float("nan")
        vals = []
        for j in range(i-2, i+1):
            v = _div_ratio(days[j])
            if v == v: vals.append(v)
        return sum(vals)/len(vals) if vals else float("nan")
    div3_st = _avg3_div(days_store, i_st)
    div3_rt = _avg3_div(days_result, i_rt) if i_rt is not None else float("nan")
    tk_st = store_by_date.get(date_str, {}).get("taker", float("nan"))
    tk_rt = result_by_date.get(date_str, {}).get("taker", float("nan"))
    # note: which leg chết most likely
    legs = f"B1={'T' if b1 else 'F'} B3={'T' if b3 else 'F'}"
    note = ""
    if not hbs:
        if not b1: note = "*B1 dead"
        if not b3: note += "/*B3 dead" if note else "*B3 dead"
    def _fmt(x, n=4):
        try:
            if x is None or x != x: return "  nan  "
            return f"{x:.{n}f}"
        except Exception: return "  nan  "
    print(f"  {date_str:>6}  {i_st:>4}  {'T' if b1 else 'F':>3} {'T' if b2 else 'F':>3} {'T' if b3 else 'F':>3} {'T' if b4 else 'F':>3}  "
          f"{'T' if hbs else 'F':>4}  {_fmt(div3_st):>8} {_fmt(div3_rt):>8}   "
          f"{_fmt(tk_st):>9} {_fmt(tk_rt):>9}   {note:<25}")

# ─── Extra: raw per-day pos/acc/gLSR store vs _result (compare 07-05→09) ───
print(f"\n──── Raw pos_r / acc_r / gLSR STORE vs _result.txt (07-05→09 spot) ────")
def _fnum(x, n=3):
    try:
        if x is None or x != x: return "  nan  "
        return f"{float(x):.{n}f}"
    except Exception: return "  nan  "
print(f"  {'date':>6}  {'pos_st':>7} {'pos_rt':>7}  {'acc_st':>7} {'acc_rt':>7}  {'gLSR_st':>8} {'gLSR_rt':>8}")
for d in ["07-05","07-06","07-07","07-08","07-09"]:
    s = store_by_date.get(d, {})
    r = result_by_date.get(d, {})
    print(f"  {d:>6}  "
          f"{_fnum(s.get('pos_r'),3):>7} {_fnum(r.get('pos_r'),3):>7}  "
          f"{_fnum(s.get('acc_r'),3):>7} {_fnum(r.get('acc_r'),3):>7}  "
          f"{_fnum(s.get('gLSR'),4):>8} {_fnum(r.get('gLSR'),4):>8}")

# Additional debug: what days_store fields look like at 07-05
print(f"\n──── DEBUG: days_store[8] (07-05) fields ────")
if len(days_store) > 8:
    for k, v in days_store[8].items():
        print(f"    {k} = {v}")

print(f"\n──── DEBUG: days_result index of 07-05 fields ────")
i_rt_dbg = result_i_by_date.get("07-05")
if i_rt_dbg is not None and i_rt_dbg < len(days_result):
    for k, v in days_result[i_rt_dbg].items():
        print(f"    {k} = {v}")

print(f"\n[STORE data range for BULLA]:")
print(f"  min date = {min(store_by_date.keys())}  max date = {max(store_by_date.keys())}  n_rows = {len(store_by_date)}")
print(f"[_result.txt data range for BULLA]:")
print(f"  min date = {min(result_by_date.keys())}  max date = {max(result_by_date.keys())}  n_rows = {len(result_by_date)}")

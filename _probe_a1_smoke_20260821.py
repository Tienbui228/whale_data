#!/usr/bin/env python3
"""[A1 smoke] lib.registry_events import + call trên HEMI/ON/GUA/ARIA/CARV/SHELL/SIGN.

Không assert giá trị — chỉ chứng import + call KHÔNG crash + in shape output.
Giá trị đúng/sai sẽ chấm ở A3 fixture PASS.
"""
from __future__ import annotations
import sys, io, csv
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, NaN, ok
from lib.registry_events import (
    _detect_ev, _pos_ok, _px_ok, _cur_ep_min,
    window_prefilter_and_detect, CFG_DEFAULT,
    DRIFT_THR, DRIFT_WIN, POS_HOLD, PX_HOLD, POST_BREAK_MAX_DAYS,
)

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
TARGETS = ["HEMIUSDT","ONUSDT","GUAUSDT","ARIAUSDT","CARVUSDT","SHELLUSDT","SIGNUSDT"]
WINDOW_START = "2026-06-21"; WINDOW_END = "2026-08-19"

td = {}
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","")
            if sym not in TARGETS: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
            })
for s in td: td[s].sort(key=lambda r: r["date"])

print(f"[smoke] loaded {len(td)} targets")
print(f"[smoke] using window_prefilter_and_detect(WINDOW_START={WINDOW_START})")

for sym in sorted(td):
    arr_full = td[sym]
    arr_win, ep_win = window_prefilter_and_detect(arr_full, WINDOW_START)
    print(f"\n  {sym}: full={len(arr_full)}d → win={len(arr_win)}d (cutoff = {WINDOW_START} - 5d)")
    events = []
    for i in range(len(arr_win)):
        ev = _detect_ev(arr_win, ep_win, i, sn_min=3,
                        window_start=WINDOW_START, window_end=WINDOW_END)
        if ev:
            events.append(ev)
    print(f"    events (sn_min=3): {len(events)}")
    for ev in events[:3]:
        print(f"      {ev['date']} trig={ev['trig']} sn={ev['sn']} rel={ev['rel_ep_kind']} ep_min={ev['ep_min']:.3f}")
print(f"\n[smoke] DONE — module import + call OK")

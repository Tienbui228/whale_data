"""GREP nạn nhân H1-step câm · fw-139 × 26/06→22/08 · read-only.

Tìm mọi (token, ngày) có 3d-best ≥10% (spec §5 inclusive, N/A-leg bỏ leg)
mà prod-1d h1_raw=False. Đích danh + count.

Đánh dấu đặc biệt:
  (i)   token trong 12 PERP-CÂM SÓT (từ v3 SÓT-vs-cross) — lật thành có-fire
  (ii)  TUT full trace 3d-best xem có ngày ≥10% không
  (iii) XAN 07-03 xác nhận (đã trace nhưng lặp lại đây tổng thể)
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td
import pandas as pd

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

from gom_h_daily import _load_cfg, _load_universe

SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

cfg_all = _load_cfg()
THR = cfg_all["gom_h"]["h1"]["balance_delta_abs_min"]  # 0.10 = 10%

# 12 PERP-CÂM tokens từ v3 SÓT-vs-cross (đã screening từ output trước):
PERP_CAM_12 = {"ACU","ARIA","ENSO","FF","FHE","LIGHT","MUBARAK","SQD","TRADOOR","TUT","XNY","XPIN"}
# PIEVERSE có NO-KHO-DATA (không xét kho)

WINDOW_START = _date(2026, 6, 26)
WINDOW_END   = _date(2026, 8, 22)

symbols = _load_universe()
tokens = [s[:-4] if s.endswith("USDT") else s for s in symbols]

# Load balance series toàn universe
BAL = {}  # {token: {ingest_date_str: balance}}
for p in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if not r: continue
        sym_u = (r.get("symbol") or "").upper()
        if not sym_u: continue
        bal = r.get("exchange_balance_tokens")
        if bal is not None:
            try: BAL.setdefault(sym_u, {})[p.stem] = float(bal)
            except: pass

def step_1d_pct(tok, target_date_str):
    """Prod semantic: 1-day Δ signed %."""
    ingest = (_date.fromisoformat(target_date_str) + _td(days=1)).isoformat()
    ingest_prev = (_date.fromisoformat(target_date_str)).isoformat()
    series = BAL.get(tok, {})
    b_now = series.get(ingest)
    b_prev = series.get(ingest_prev)
    if b_now is None or b_prev is None or b_prev <= 0: return None
    return (b_now - b_prev) / b_prev * 100.0  # signed %

def step_3d_best_pct(tok, target_date_str):
    """Spec §5 inclusive: max |Δ|/prev over lb ∈ {1,2,3}, skip N/A-leg."""
    ingest = (_date.fromisoformat(target_date_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_now = series.get(ingest)
    if b_now is None or b_now <= 0: return None, None
    best = None; best_lb = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - _td(days=lb)).isoformat()
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue  # N/A-leg bỏ
        dp = abs(b_now - b_start) / b_start * 100.0
        if best is None or dp > best:
            best = dp; best_lb = lb
    return best, best_lb  # (pct, lb)

# ─── Scan full universe ───
print("═" * 100)
print(f"[GREP H1 VICTIMS · fw-{len(tokens)} × {WINDOW_START}..{WINDOW_END}]")
print(f"  Dao 3d-best ≥ 10% AND prod 1d |Δ| < 10% → victim (câm sai spec §3)")
print("═" * 100)

victims = []  # list of (token, date, best_pct, lb, 1d_pct)
n_scanned = 0
cur = WINDOW_START
while cur <= WINDOW_END:
    d_str = cur.isoformat()
    for tok in tokens:
        n_scanned += 1
        best, lb = step_3d_best_pct(tok, d_str)
        if best is None or best < THR * 100.0: continue  # not-≥10% 3d-best
        # Check prod 1d
        p1d = step_1d_pct(tok, d_str)
        if p1d is None: continue
        if abs(p1d) < THR * 100.0:  # prod câm
            victims.append({
                "token": tok, "date": d_str,
                "best_3d_pct": best, "best_lb": lb,
                "step_1d_pct": p1d,
            })
    cur += _td(days=1)

print(f"\n[SUMMARY] scanned {n_scanned} (token,day) · victims câm = {len(victims)}")
print()

# In danh sách đích danh
print(f"[VICTIMS đích danh]")
print(f"  {'token':10} {'date':10} {'best_3d%':>9} {'lb':>3} {'1d%':>8} {'mark':<30}")
print(f"  {'-'*10} {'-'*10} {'-'*9} {'-'*3} {'-'*8} {'-'*30}")
mark_stats = {"PERP-CÂM SÓT": 0, "TUT-verify": 0, "XAN-verify": 0, "other": 0}
per_token_victim = {}
for v in victims:
    mark = ""
    if v["token"] in PERP_CAM_12: mark = "★ PERP-CÂM-SÓT lật"; mark_stats["PERP-CÂM SÓT"] += 1
    elif v["token"] == "TUT": mark = "TUT-verify"; mark_stats["TUT-verify"] += 1
    elif v["token"] == "XAN": mark = "XAN"; mark_stats["XAN-verify"] += 1
    else: mark_stats["other"] += 1
    print(f"  {v['token']:10} {v['date']:10} {v['best_3d_pct']:>8.2f}% {v['best_lb']:>3d} {v['step_1d_pct']:>+7.2f}% {mark:<30}")
    per_token_victim.setdefault(v["token"], []).append(v)

print()
print(f"[Mark stats] PERP-CÂM-SÓT lật: {mark_stats['PERP-CÂM SÓT']} · TUT: {mark_stats['TUT-verify']} · XAN: {mark_stats['XAN-verify']} · other: {mark_stats['other']}")

# (i) 12 PERP-CÂM SÓT — count how many have any victim day
print(f"\n[i] Trong 12 PERP-CÂM SÓT, con nào có ngày victim (3d-best ≥10% mà prod câm)?")
for tok in sorted(PERP_CAM_12):
    if tok in per_token_victim:
        vd = per_token_victim[tok]
        first = min(vd, key=lambda x: x["date"])
        print(f"  {tok:10} FIRST victim day: {first['date']} best_3d={first['best_3d_pct']:.2f}% (lb={first['best_lb']}) · n_victim_days={len(vd)}")
    else:
        print(f"  {tok:10} không có victim day (thực sự kho phẳng)")

# (ii) TUT trace all days
print(f"\n[ii] TUT full trace 3d-best across window (any day ≥10%?):")
tut_days = []
cur = WINDOW_START
while cur <= WINDOW_END:
    d = cur.isoformat()
    best, lb = step_3d_best_pct("TUT", d)
    p1d = step_1d_pct("TUT", d)
    if best is not None:
        tut_days.append({"date": d, "best": best, "lb": lb, "p1d": p1d})
    cur += _td(days=1)
if tut_days:
    max_day = max(tut_days, key=lambda x: x["best"])
    print(f"  n_eval_days={len(tut_days)} · max_3d_best={max_day['best']:.2f}% @{max_day['date']} (lb={max_day['lb']})")
    tut_ge10 = [x for x in tut_days if x["best"] >= 10.0]
    print(f"  Days với 3d-best ≥10%: {len(tut_ge10)}")
    for x in tut_ge10[:10]:
        print(f"    {x['date']} best={x['best']:.2f}% (lb={x['lb']}) 1d={x['p1d']:+.2f}%")
    if not tut_ge10:
        print(f"  → TUT thực sự kho phẳng — ruling operator ĐÚNG (không phải 1d-metric bug)")
else:
    print(f"  n_eval_days=0 (TUT không có snapshot trong window)")

# (iii) XAN 07-03 confirm
print(f"\n[iii] XAN 07-03 confirm:")
xan_best, xan_lb = step_3d_best_pct("XAN", "2026-07-03")
xan_1d = step_1d_pct("XAN", "2026-07-03")
print(f"  XAN 07-03 · 3d-best={xan_best:.2f}% (lb={xan_lb}) · 1d={xan_1d:+.2f}% → victim: {(xan_best or 0) >= 10 and abs(xan_1d or 0) < 10}")

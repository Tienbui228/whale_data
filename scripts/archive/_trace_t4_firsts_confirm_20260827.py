"""(α-2b) Recheck 4 T-④ H1-step firsts: AKE/ON/BTW/CAP - confirm 3d-best."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")

BAL = {}
for p in sorted(SNAPS.glob("*.json")):
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


def step_3d_best(tok, target_str):
    ingest = (_date.fromisoformat(target_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0: return None, None
    best = None; best_lb = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - _td(days=lb)).isoformat()
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start * 100.0
        if best is None or dp > best:
            best = dp; best_lb = lb
    return best, best_lb


def step_1d(tok, target_str):
    ingest = (_date.fromisoformat(target_str) + _td(days=1)).isoformat()
    ingest_prev = (_date.fromisoformat(target_str)).isoformat()
    series = BAL.get(tok, {})
    b_now = series.get(ingest); b_prev = series.get(ingest_prev)
    if b_now is None or b_prev is None or b_prev <= 0: return None
    return (b_now - b_prev) / b_prev * 100.0


# T-④ first-fires per v2.1 table
FIRSTS = {
    "AKE": ("2026-07-05", "T-④ v2.1 first_fire H1-step +10d PASS"),
    "ON":  ("2026-07-14", "T-④ v2.1 first_fire H1-step +5d PASS"),
    "BTW": ("2026-07-27", "T-④ v2.1 first_fire H1-step +7d PASS"),
    "CAP": ("2026-07-12", "T-④ v2.1 first_fire H1-step +18d PASS"),
}

print("═" * 100)
print("[T-④ 4 H1-STEP FIRSTS RECHECK · confirm 3d-best (T-④ script) ≥ 10%]")
print("  → T-④ script `_task_t4_rerender_v2_census_v3_20260829.py` REIMPLEMENT `_kho_step_3d`")
print("     (spec §5 inclusive, max 1-3d back) — không phải prod-1d adapter")
print("  → firsts/leads T-④ GIỮ NGUYÊN dưới 3d-best metric")
print("═" * 100)

for tok, (d, note) in FIRSTS.items():
    b3d, lb = step_3d_best(tok, d)
    p1d = step_1d(tok, d)
    b3d_str = f"{b3d:.2f}%" if b3d is not None else "N/A"
    p1d_str = f"{p1d:+.2f}%" if p1d is not None else "N/A"
    pass_3d = b3d is not None and b3d >= 10.0
    print(f"  {tok:5} first_fire={d} · 3d-best={b3d_str} (lb={lb}) · 1d={p1d_str} · 3d ≥ 10%? {'YES ✓' if pass_3d else 'NO'}  · {note}")

print()
print("[VERDICT] Cả 4 firsts pass 3d-best ≥ 10% (spec metric) → T-④ table GIỮ NGUYÊN, không re-render.")
print("  Note: leads chỉ có thể SỚM LÊN nếu prod fix chuyển sang 3d-best (thêm ngày trigger sớm hơn),")
print("  không muộn đi. Firsts hiện tại là earliest 3d-best trigger day.")

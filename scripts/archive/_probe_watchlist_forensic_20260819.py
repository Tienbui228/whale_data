#!/usr/bin/env python3
"""[W2][W3] Watchlist staleness forensic — recompute vs logged.

READ-ONLY. Uses VPS freshwatch csv (backup at /tmp/) as authoritative source.
Recomputes oi_trend/pos_trend/oi_note per (sym, run_date) with:
  1. Original target=run_date (sanity check — should match logged 100%)
  2. target=max_avail (latest freshwatch — what SHOULD be if timing fixed)
Counts oi_note flips (B1 short-cover ↔ B2 long-mới) — nhãn operator trade theo.

NO writes to CSV/threshold. Output paste + JSON to /tmp/.
"""
import sys, io, csv, math, json
from pathlib import Path
from statistics import mean

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\watchlist_forensic_20260819")
FW = _TMP / "freshwatch_daily_2026-08_vps.csv.bak"
LOG = _TMP / "watchlist_log_2026-08_vps.csv.bak"
OUT = _TMP / "w3_audit_result.json"

# Config canonical (watchlist_daily.py:36-45)
POS_THR = 0.01
OI_THR = 0.02
LOW_CONF = 1_000_000.0
DIV_MAX = 0.5

NaN = float("nan")
def ok(x): return x == x and not math.isinf(x)

# ─── Load freshwatch + also older months for lookback ────────────────────
td = {}
for fw_month in [Path(str(FW).replace("2026-08", m))
                 for m in ["2026-05","2026-06","2026-07","2026-08"]]:
    # only 2026-08 exists in backup; skip others silently
    if not fw_month.exists():
        continue
    with open(fw_month, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol", "")
            if not sym: continue
            def _f(k):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date", ""),
                "px":   _f("px_avg"),
                "pos":  _f("lsr_pos_r"),
                "acc":  _f("lsr_acc_r"),
                "oi":   _f("oi_usd"),
                "fund": _f("funding_avg"),
            })
for sym in td:
    td[sym].sort(key=lambda r: r["date"])

# Load older 07 for min-history via SSH pull? Skip — use in-Aug window.
# Actually we need history for lookback of avg3(i-2..i) which needs 3 rows.
# For 08-11 target, i=index of 08-11 which is ~10 in the aug-only slice.
# 08-11 index = day 10 of Aug → has enough lookback within Aug alone (need i-5=5 → 08-06 available).
# For earliest run_date 08-11, we need dates 08-06..08-11 → ALL in Aug slice ✓.

print(f"[fw] tokens loaded: {len(td)}")

# ─── Canonical calcs (mirror watchlist_daily.py:108-174) ─────────────────
def avg3(arr, i, field):
    vals = [arr[j][field] for j in range(max(0, i-2), i+1) if ok(arr[j][field])]
    return mean(vals) if vals else NaN

def calc_div(arr, i):
    a3p = avg3(arr, i, "pos"); a3a = avg3(arr, i, "acc")
    if not ok(a3p) or not ok(a3a) or a3a == 0: return NaN
    return a3p / a3a

def pos_trend(arr, i):
    now = avg3(arr, i, "pos"); prev = avg3(arr, max(0, i-5), "pos")
    if not ok(now) or not ok(prev) or prev == 0: return "NaN"
    chg = (now - prev) / prev
    return "BẬT" if chg >= POS_THR else ("GIẢM" if chg <= -POS_THR else "PHẲNG")

def oi_trend(arr, i):
    raw = arr[i].get("oi", NaN)
    if not ok(raw) or raw < LOW_CONF: return "LOW_CONF"
    now = avg3(arr, i, "oi"); prev = avg3(arr, max(0, i-5), "oi")
    if not ok(now) or not ok(prev) or prev == 0: return "NaN"
    chg = (now - prev) / prev
    return "TĂNG" if chg >= OI_THR else ("GIẢM" if chg <= -OI_THR else "PHẲNG")

_OI_NOTE = {
    "GIẢM":     "short cover thật (OI rút)",
    "TĂNG":     "long mới (không phải short rút)",
    "PHẲNG":    "",
    "LOW_CONF": "OI<$1M, bỏ qua",
    "NaN":      "OI NaN",
}

def _idx_for_date(arr, dstr):
    for i, r in enumerate(arr):
        if r["date"] == dstr: return i
    return None

# ─── Load watchlist_log ──────────────────────────────────────────────────
log_rows = []
with open(LOG, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        log_rows.append(r)

print(f"[log] rows loaded: {len(log_rows)}")

# max avail date in freshwatch
all_dates = sorted({r["date"] for arr in td.values() for r in arr})
max_avail = all_dates[-1]
print(f"[fw] date range: {all_dates[0]} → {max_avail} ({len(all_dates)} days)")

# ─── W2: row counts + missing ────────────────────────────────────────────
print(f"\n═══ W2: rows per run_date + delta ═══")
by_date = {}
for r in log_rows:
    by_date.setdefault(r["run_date"], set()).add(r["symbol"])
for d in sorted(by_date):
    print(f"  {d}: {len(by_date[d])} unique symbols "
          f"({sum(1 for x in log_rows if x['run_date']==d)} rows w/ dup)")

# ─── W3: audit — recompute for each (sym, run_date) ──────────────────────
print(f"\n═══ W3: audit ngược — sanity + label-flip test ═══")
print(f"  sanity: recompute@target=run_date should match logged (bot ran correctly at time)")
print(f"  test  : recompute@target=max_avail ({max_avail}) = what SHOULD be if timing fixed\n")

n_total = 0
n_sanity_match = 0
n_sanity_diff_oi = 0
n_sanity_diff_pos = 0
n_flip = 0                # B1↔B2 flip in oi_note
n_flip_direction = {"GIAM_to_TANG": 0, "TANG_to_GIAM": 0, "GIAM_to_PHANG": 0,
                    "TANG_to_PHANG": 0, "PHANG_to_TANG": 0, "PHANG_to_GIAM": 0,
                    "other": 0}
flip_rows = []      # for detailed print

for lr in log_rows:
    sym = lr["symbol"]; rd = lr["run_date"]
    if sym not in td: continue
    arr = td[sym]

    # sanity: recompute for target=rd
    i_orig = _idx_for_date(arr, rd)
    if i_orig is None or i_orig < 5:  # need lookback
        continue

    oi_orig_re = oi_trend(arr, i_orig)
    pos_orig_re = pos_trend(arr, i_orig)

    logged_oi = lr["oi_trend"]
    logged_pos = lr["pos_trend"]

    n_total += 1
    sanity_ok = (oi_orig_re == logged_oi and pos_orig_re == logged_pos)
    if sanity_ok:
        n_sanity_match += 1
    else:
        if oi_orig_re != logged_oi: n_sanity_diff_oi += 1
        if pos_orig_re != logged_pos: n_sanity_diff_pos += 1

    # test: recompute for target=max_avail
    i_new = _idx_for_date(arr, max_avail)
    if i_new is None: continue

    oi_new = oi_trend(arr, i_new)
    pos_new = pos_trend(arr, i_new)

    # oi_note flip detection
    oi_note_old = _OI_NOTE.get(oi_orig_re, "")
    oi_note_new = _OI_NOTE.get(oi_new, "")

    if oi_orig_re != oi_new:
        n_flip += 1
        key = f"{oi_orig_re.replace(chr(0x1EA2)+chr(0x1EA2),'')}_to_{oi_new}"
        # simpler key
        pair = f"{oi_orig_re}→{oi_new}"
        # tally by direction
        m = {
            "GIẢM→TĂNG": "GIAM_to_TANG",
            "TĂNG→GIẢM": "TANG_to_GIAM",
            "GIẢM→PHẲNG": "GIAM_to_PHANG",
            "TĂNG→PHẲNG": "TANG_to_PHANG",
            "PHẲNG→TĂNG": "PHANG_to_TANG",
            "PHẲNG→GIẢM": "PHANG_to_GIAM",
        }.get(pair, "other")
        n_flip_direction[m] += 1
        flip_rows.append({
            "sym": sym, "run_date": rd, "list": lr["list"],
            "oi_old": oi_orig_re, "oi_new": oi_new,
            "note_old": oi_note_old, "note_new": oi_note_new,
            "pair": pair,
        })

print(f"[sanity] {n_sanity_match}/{n_total} rows match bot's logged output "
      f"({n_sanity_match/n_total*100:.1f}%)")
print(f"  oi_trend differ:  {n_sanity_diff_oi}")
print(f"  pos_trend differ: {n_sanity_diff_pos}")

print(f"\n[flip test] recompute@max_avail={max_avail} vs recompute@run_date:")
print(f"  Total flips (oi_trend changed): {n_flip}/{n_total} = {n_flip/n_total*100:.1f}%")
for k, v in sorted(n_flip_direction.items(), key=lambda x: -x[1]):
    if v == 0: continue
    print(f"    {k:<20}: {v}")

# B1↔B2 flip specifically: GIẢM (short-cover=B1) ↔ TĂNG (long-mới=B2)
b1_to_b2 = n_flip_direction["GIAM_to_TANG"]
b2_to_b1 = n_flip_direction["TANG_to_GIAM"]
print(f"\n  ⚠ B1↔B2 flip (nhãn operator trade theo):")
print(f"    B1(GIẢM short-cover) → B2(TĂNG long-mới): {b1_to_b2}")
print(f"    B2(TĂNG long-mới) → B1(GIẢM short-cover): {b2_to_b1}")
print(f"    Tổng B1↔B2 đảo nghĩa: {b1_to_b2 + b2_to_b1}")

# STBL specific
print(f"\n[STBL trace] all log rows + recompute@max_avail:")
for r in log_rows:
    if r["symbol"] != "STBLUSDT": continue
    sym = "STBLUSDT"; rd = r["run_date"]
    i_orig = _idx_for_date(td[sym], rd)
    i_new = _idx_for_date(td[sym], max_avail)
    oi_o = oi_trend(td[sym], i_orig) if i_orig else "?"
    oi_n = oi_trend(td[sym], i_new) if i_new else "?"
    print(f"  {rd} list={r['list']} logged oi_trend={r['oi_trend']:>8} "
          f"recompute@rd={oi_o:>8} recompute@{max_avail}={oi_n:>8}")

# TRIA specific
print(f"\n[TRIA trace] all log rows + recompute@max_avail:")
for r in log_rows:
    if r["symbol"] != "TRIAUSDT": continue
    sym = "TRIAUSDT"; rd = r["run_date"]
    i_orig = _idx_for_date(td[sym], rd)
    i_new = _idx_for_date(td[sym], max_avail)
    oi_o = oi_trend(td[sym], i_orig) if i_orig else "?"
    oi_n = oi_trend(td[sym], i_new) if i_new else "?"
    print(f"  {rd} list={r['list']} logged oi_trend={r['oi_trend']:>8} "
          f"recompute@rd={oi_o:>8} recompute@{max_avail}={oi_n:>8}")

# Save details JSON
OUT.write_text(json.dumps({
    "total_rows_audited": n_total,
    "sanity_match": n_sanity_match,
    "sanity_diff_oi": n_sanity_diff_oi,
    "sanity_diff_pos": n_sanity_diff_pos,
    "total_flips_oi_trend": n_flip,
    "flip_directions": n_flip_direction,
    "b1_to_b2_flip": b1_to_b2,
    "b2_to_b1_flip": b2_to_b1,
    "max_avail_date": max_avail,
    "flip_rows_sample": flip_rows[:100],
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n[saved] {OUT}")

#!/usr/bin/env python3
"""[W-D 19/08] Build watchlist_corrections_2026-08.csv from W3 audit.

Reads:
  - VPS watchlist_log_2026-08.csv (logged rows)
  - VPS freshwatch_daily_2026-08.csv (authoritative)
Writes:
  data/export/watchlist_corrections_2026-08.csv (append-only lớp đính chính)

CẤM sửa watchlist_log_*.csv lịch sử. File này là LỚP đính chính riêng.
Chạy 1 lần — 226 dòng đảo nghĩa B1↔B2 + 27 dòng other flips.
"""
import sys, io, csv, math
from pathlib import Path
from statistics import mean
from datetime import date

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\watchlist_forensic_20260819")
FW = _TMP / "freshwatch_daily_2026-08_vps.csv.bak"
LOG = _TMP / "watchlist_log_2026-08_vps.csv.bak"
OUT = Path(r"D:\Data back test\whale_data\data\export\watchlist_corrections_2026-08.csv")

POS_THR = 0.01; OI_THR = 0.02; LOW_CONF = 1_000_000.0

NaN = float("nan")
def ok(x): return x == x and not math.isinf(x)

def avg3(arr, i, field):
    vals = [arr[j][field] for j in range(max(0, i-2), i+1) if ok(arr[j][field])]
    return mean(vals) if vals else NaN

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

# Load freshwatch
td = {}
with open(FW, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        sym = r.get("symbol", "")
        if not sym: continue
        def _f(k):
            try: return float(r[k])
            except: return NaN
        td.setdefault(sym, []).append({
            "date": r.get("date", ""),
            "oi":   _f("oi_usd"),
        })
for sym in td: td[sym].sort(key=lambda r: r["date"])

all_dates = sorted({r["date"] for arr in td.values() for r in arr})
max_avail = all_dates[-1]
print(f"[fw] {len(td)} tokens, date range: {all_dates[0]}..{max_avail}")

def _idx(arr, dstr):
    for i, r in enumerate(arr):
        if r["date"] == dstr: return i
    return None

# Load log + build corrections
rows_out = []
with open(LOG, encoding="utf-8", errors="replace") as f:
    for lr in csv.DictReader(f):
        sym = lr["symbol"]; rd = lr["run_date"]
        if sym not in td: continue
        arr = td[sym]
        i_orig = _idx(arr, rd)
        i_new = _idx(arr, max_avail)
        if i_orig is None or i_new is None: continue

        oi_logged = lr["oi_trend"]
        oi_new    = oi_trend(arr, i_new)
        if oi_logged == oi_new: continue      # no flip → không cần correction

        # stale delta
        try:
            stale_d = (date.fromisoformat(max_avail) - date.fromisoformat(rd)).days
        except Exception:
            stale_d = -1

        # [W-D 19/08 v3] LOẠI classifier per operator (chốt 315 dòng):
        #   đảo   : B1↔B2 (logged {GIẢM,TĂNG} ↔ recompute {TĂNG,GIẢM}) — nhãn NGƯỢC hoàn toàn
        #   phồng : biên phồng — bot inflate/deflate signal về noise:
        #           · GIẢM→PHẲNG  (short-cover chế ở đuôi episode, real flat)
        #           · LOW_CONF→PHẲNG (bot skip OI<$1M, real flat legit)
        #           · TĂNG→LOW_CONF (bot fake long-mới, real OI cực nhỏ = noise)
        #   Rows KHÔNG thuộc {đảo, phồng} → SKIP khỏi corrections CSV (hụt/khác
        #   là "bot bỏ sót", không phải "bot chế nhãn sai" — operator không trade
        #   theo signal không phát ra).
        pair = (oi_logged, oi_new)
        if oi_logged in {"GIẢM","TĂNG"} and oi_new in {"GIẢM","TĂNG"} and oi_logged != oi_new:
            loai = "đảo"
        elif pair in {("GIẢM","PHẲNG"), ("LOW_CONF","PHẲNG"), ("TĂNG","LOW_CONF")}:
            loai = "phồng"
        else:
            continue    # skip — không thuộc corrections scope (đảo+phồng)

        rows_out.append({
            "run_date":     rd,
            "symbol":       sym,
            "list":         lr["list"],
            "field":        "oi_trend",
            "logged":       oi_logged,
            "logged_note":  lr.get("oi_note", ""),
            "corrected":    oi_new,
            "corrected_note": _OI_NOTE.get(oi_new, ""),
            "loại":         loai,
            "flip_type":    ("B1_to_B2" if (oi_logged=="GIẢM" and oi_new=="TĂNG")
                             else "B2_to_B1" if (oi_logged=="TĂNG" and oi_new=="GIẢM")
                             else f"{oi_logged}_to_{oi_new}"),
            "stale_days":   stale_d,
            "reason":       f"freshwatch stale {stale_d}d (timing bug cron 01:00 < freshwatch 01:20) — "
                            f"target logged={rd}, max_avail@audit={max_avail}",
            "ref":          "_watchlist_staleness_forensic_20260819.md",
            "correction_date": "2026-08-19",
        })

print(f"[out] {len(rows_out)} correction rows")

# Loại classifier tally (operator canonical: đảo + phồng first)
loai_counts = {}
for r in rows_out:
    loai_counts[r["loại"]] = loai_counts.get(r["loại"], 0) + 1
print(f"\n═══ By LOẠI (operator canonical) ═══")
for k in ["đảo", "phồng", "hụt", "low_conf", "khác"]:
    v = loai_counts.get(k, 0)
    print(f"  {k:>10}: {v}")

# Fine-grained flip breakdown
print(f"\n═══ By flip_type (fine-grained) ═══")
flip_counts = {}
for r in rows_out:
    flip_counts[r["flip_type"]] = flip_counts.get(r["flip_type"], 0) + 1
for k, v in sorted(flip_counts.items(), key=lambda x: -x[1]):
    print(f"  {k:>25}: {v}")

# CLO trace (biên phồng exemplar)
print(f"\n═══ CLO trace (biên phồng ví dụ operator) ═══")
for r in rows_out:
    if r["symbol"] == "CLOUSDT":
        print(f"  {r['run_date']} list={r['list']} logged={r['logged']:>8} "
              f"→ corrected={r['corrected']:>8}  loại={r['loại']}")

# Write
OUT.parent.mkdir(parents=True, exist_ok=True)
fieldnames = ["run_date","symbol","list","field","logged","logged_note",
              "corrected","corrected_note","loại","flip_type","stale_days","reason",
              "ref","correction_date"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows_out:
        w.writerow(r)
print(f"\n[saved] {OUT}")

# md5
import hashlib
h = hashlib.md5(OUT.read_bytes()).hexdigest()
print(f"[md5] {h}")

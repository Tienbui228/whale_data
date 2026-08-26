#!/usr/bin/env python3
"""[R1-R4 RET-TABLE — nguyên văn ANALYSIS · fapi k[4] fresh · 63 dòng]

R1: fetch fapi k[4] fresh 1d klines cho mỗi (token, fire_date), window D0..today
    (cap D+30 nếu đủ tuổi). k[4] = close.
R2: compute close_D0, max_close (D0..D+min(30,age)), ret_max, days_to_max
R3: age gating — age<30d → data_through partial, không PENDING grade (chỉ report)
R4: xuất census_ret_63.csv · KHÔNG điền TP_FP (ANALYSIS chấm)

N/A-NO-KLINES: nếu fapi trả không có data cho (token, date), ghi CHỮ "N/A-NO-KLINES",
không bỏ dòng.

Sanity: 3 dòng close D0..D+5 raw cho verify (BANANAS31 07-04 · GENIUS 07-03 · COAI 07-23).
"""
from __future__ import annotations
import sys, io, csv, hashlib, time, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta, timezone
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
CSV_63 = REPO / "scratch/e2_census_perfire_v2_20260828.csv"
OUT = REPO / "scratch/census_ret_63_20260828.csv"

# Read 63 fires
fires = []
with open(CSV_63, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("token,") or not line.strip():
            continue
        cells = [c.strip() for c in line.split(",")]
        if len(cells) < 8: continue
        # Handle h2_vé column that might have non-ascii issues
        fires.append({
            "token": cells[0], "date": cells[1], "t01": cells[2],
            "h1_kho": cells[3], "h1_fx": cells[4], "h1_shadow": cells[5],
            "h2": cells[6], "h2_ve": cells[7], "h3": cells[8],
            "active": cells[9], "conf": cells[10], "age_days": cells[11],
        })

print(f"[R1] Loaded {len(fires)} fires from CSV-63")

# Fetch fapi klines per unique token
tokens = sorted(set(f["token"] for f in fires))
print(f"[R1] Unique tokens: {len(tokens)}")

FAPI = "https://fapi.binance.com/fapi/v1/klines"
kline_cache = {}  # {token: {date: close}}

TODAY = datetime.now(timezone.utc).date()

for tok in tokens:
    sym = tok + "USDT"
    # Find earliest fire date for this token
    dates = [f["date"] for f in fires if f["token"] == tok]
    d_min = min(dates)
    d_max_dt = min(datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=32),
                    datetime.combine(TODAY, datetime.min.time()))
    d_min_dt = datetime.strptime(d_min, "%Y-%m-%d")
    start_ms = int(d_min_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(d_max_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    params = {"symbol": sym, "interval": "1d", "startTime": start_ms,
              "endTime": end_ms, "limit": 500}
    url = FAPI + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        # Kline[6] = close_time_ms (ms), Kline[4] = close_price (str)
        cache = {}
        for k in data:
            dt = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date()
            cache[dt.strftime("%Y-%m-%d")] = float(k[4])
        kline_cache[tok] = cache
        print(f"  [k[4] fresh] {sym}: {len(cache)} rows ({d_min}→{d_max_dt.strftime('%Y-%m-%d')})")
        time.sleep(0.15)
    except Exception as e:
        print(f"  [k[4] FAIL] {sym}: {e}")
        kline_cache[tok] = {}

# R2-R3: compute per-fire
print(f"\n[R2-R3] Compute per-fire ret_max D0..D+min(30,age)")
rows_out = []
for f in fires:
    tok, d0 = f["token"], f["date"]
    d0_dt = datetime.strptime(d0, "%Y-%m-%d").date()
    age = (TODAY - d0_dt).days
    window_end = min(d0_dt + timedelta(days=30), TODAY)
    data_through = window_end.strftime("%Y-%m-%d")
    n_days = (window_end - d0_dt).days + 1

    cache = kline_cache.get(tok, {})
    close_D0 = cache.get(d0)
    if close_D0 is None:
        rows_out.append({**f, "close_D0": "N/A-NO-KLINES", "max_close": "N/A-NO-KLINES",
                          "ret_max": "N/A-NO-KLINES", "days_to_max": "N/A-NO-KLINES",
                          "data_through": data_through, "window_days": n_days,
                          "note": "no k[4] for D0"})
        continue

    # scan D0..window_end
    max_close = close_D0
    max_date = d0
    cur = d0_dt
    while cur <= window_end:
        cs = cache.get(cur.strftime("%Y-%m-%d"))
        if cs is not None and cs > max_close:
            max_close = cs
            max_date = cur.strftime("%Y-%m-%d")
        cur += timedelta(days=1)

    ret_max = (max_close - close_D0) / close_D0 if close_D0 > 0 else None
    days_to_max = (datetime.strptime(max_date, "%Y-%m-%d").date() - d0_dt).days

    rows_out.append({**f,
        "close_D0": f"{close_D0:.8g}", "max_close": f"{max_close:.8g}",
        "ret_max": f"{ret_max:.6f}" if ret_max is not None else "N/A",
        "days_to_max": days_to_max,
        "data_through": data_through, "window_days": n_days,
        "note": "OK" if age >= 30 else f"PARTIAL age={age}<30",
    })

# R4: write CSV
header = ["token","date","t01","h1_kho","h1_fx","h1_shadow","h2","h2_ve","h3","active","conf",
           "age_days","close_D0","max_close","ret_max","days_to_max","data_through",
           "window_days","note","TP_FP"]
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    # Rule header
    f.write("# census_ret_63 — fapi k[4] fresh · 63 dòng · KHÔNG điền TP_FP (ANALYSIS chấm)\n")
    f.write("# ret_max = (max_close D0..D+min(30,age)) / close_D0 − 1 · days_to_max = ngày đạt max\n")
    f.write("# window_days = số ngày trong D0..data_through · PARTIAL nếu age<30\n")
    f.write("# N/A-NO-KLINES: fapi k[4] không có data cho date đó, KHÔNG bỏ dòng.\n")
    f.write(f"# generated_at: {datetime.now(timezone.utc).isoformat()}\n")
    f.write("#\n")
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    for r in rows_out:
        r_out = {k: r.get(k, "") for k in header}
        r_out["TP_FP"] = ""
        w.writerow(r_out)

md5 = hashlib.md5(open(OUT, "rb").read()).hexdigest()
print(f"\n[R4] Output: {OUT.name}")
print(f"     wc -l: {sum(1 for _ in open(OUT, encoding='utf-8'))}")
print(f"     md5  : {md5}")
print(f"     mtime: {datetime.fromtimestamp(OUT.stat().st_mtime, tz=timezone.utc).isoformat()}")

# Head
print(f"\n[head -5]:")
with open(OUT, encoding="utf-8") as fh:
    for i, line in enumerate(fh):
        if i >= 10: break
        print(f"  {line.rstrip()}")

# SANITY 3 rows close D0..D+5
print(f"\n{'═'*80}\n[SANITY 3 rows close D0..D+5 fapi k[4] fresh]\n{'═'*80}")
sanity_targets = [("BANANAS31", "2026-07-04"), ("GENIUS", "2026-07-03"), ("COAI", "2026-07-23")]
for tok, d in sanity_targets:
    cache = kline_cache.get(tok, {})
    d0_dt = datetime.strptime(d, "%Y-%m-%d").date()
    print(f"\n  {tok} D0={d}:")
    for i in range(6):
        dd = (d0_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        cs = cache.get(dd)
        if cs is None:
            print(f"    {dd} (D+{i}) : N/A-NO-KLINES")
        else:
            print(f"    {dd} (D+{i}) : close={cs:.8g}")

print(f"\n{'═'*80}\n[DỪNG] R1-R4 RET-TABLE done · R5 validator commit tiếp.\n{'═'*80}")

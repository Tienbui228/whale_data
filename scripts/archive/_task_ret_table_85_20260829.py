#!/usr/bin/env python3
"""[RET-TABLE-85 · GOI-NHE-20260829] fapi k[4] fresh cho 85 kept fires.
R1-R4 khuôn: R1 fetch klines · R2 compute ret_max · R3 age gating · R4 CSV out.
"""
from __future__ import annotations
import sys, io, csv, hashlib, time, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta, timezone
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
INPUT_CSV = REPO / "scratch/census_63_grades_v3_input_20260829.csv"
OUT = REPO / "scratch/census_ret_85_20260829.csv"

# Load kept fires from v3-input
fires = []
with open(INPUT_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("token,") or not line.strip(): continue
        cells = [c.strip() for c in line.split(",")]
        if len(cells) < 8: continue
        fires.append({
            "token": cells[0], "date": cells[1], "trigger": cells[2],
            "h2_ve": cells[3], "conf": cells[4],
            "step_pct": cells[5], "ramp_pct": cells[6], "age_days": cells[7],
        })

print(f"[R1] Loaded {len(fires)} kept fires from v3-input")

# Fetch fapi klines per unique token
tokens = sorted(set(f["token"] for f in fires))
print(f"[R1] Unique tokens: {len(tokens)}")

FAPI = "https://fapi.binance.com/fapi/v1/klines"
kline_cache = {}
TODAY = datetime.now(timezone.utc).date()

for tok in tokens:
    sym = tok + "USDT"
    dates = [f["date"] for f in fires if f["token"] == tok]
    d_min_dt = datetime.strptime(min(dates), "%Y-%m-%d")
    d_max_dt = min(datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=32),
                    datetime.combine(TODAY, datetime.min.time()))
    start_ms = int(d_min_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(d_max_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    params = {"symbol": sym, "interval": "1d", "startTime": start_ms,
              "endTime": end_ms, "limit": 500}
    url = FAPI + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        cache = {}
        for k in data:
            dt = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date()
            cache[dt.strftime("%Y-%m-%d")] = float(k[4])
        kline_cache[tok] = cache
        print(f"  [k[4]] {sym}: {len(cache)} rows ({min(dates)}→{d_max_dt.strftime('%Y-%m-%d')})")
        time.sleep(0.12)
    except Exception as e:
        print(f"  [k[4] FAIL] {sym}: {e}")
        kline_cache[tok] = {}

# R2-R3 compute
print(f"\n[R2-R3] Compute ret_max D0..D+min(30,age)")
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
                          "note": "no k[4] for D0", "TP_FP": ""})
        continue
    max_close = close_D0; max_date = d0
    cur = d0_dt
    while cur <= window_end:
        cs = cache.get(cur.strftime("%Y-%m-%d"))
        if cs is not None and cs > max_close:
            max_close = cs; max_date = cur.strftime("%Y-%m-%d")
        cur += timedelta(days=1)
    ret_max = (max_close - close_D0) / close_D0 if close_D0 > 0 else None
    days_to_max = (datetime.strptime(max_date, "%Y-%m-%d").date() - d0_dt).days
    note = "OK" if age >= 30 else f"PENDING age={age}<30"
    rows_out.append({**f,
        "close_D0": f"{close_D0:.8g}", "max_close": f"{max_close:.8g}",
        "ret_max": f"{ret_max:.6f}" if ret_max is not None else "N/A",
        "days_to_max": days_to_max,
        "data_through": data_through, "window_days": n_days,
        "note": note, "TP_FP": ""})

# R4 write CSV
header = ["token","date","trigger","h2_ve","conf","step_pct","ramp_pct","age_days",
          "close_D0","max_close","ret_max","days_to_max","data_through","window_days","note","TP_FP"]
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write("# census_ret_85 · GOI-NHE-20260829 · fapi k[4] fresh · 85 kept fires\n")
    f.write("# ret_max = (max_close D0..D+min(30,age)) / close_D0 − 1\n")
    f.write("# note: OK=age≥30 fully graded / PENDING=age<30 / N/A-NO-KLINES=missing data\n")
    f.write("# TP_FP: TRỐNG (ANALYSIS chấm, HIGH-9 ưu tiên trước)\n")
    f.write(f"# generated_at: {datetime.now(timezone.utc).isoformat()}\n")
    f.write("#\n")
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    for r in rows_out: w.writerow(r)
md5 = hashlib.md5(open(OUT, "rb").read()).hexdigest()
print(f"\n[R4] {OUT.name}  wc={sum(1 for _ in open(OUT, encoding='utf-8'))}  md5: {md5}")

# HIGH-9 summary
high_9 = [r for r in rows_out if r["conf"].startswith("HIGH")]
print(f"\n[HIGH-9 ret_max summary]:")
print(f"  {'token':<10} {'date':>12} {'trigger':>10} {'ret_max':>10} {'days_to_max':>4} {'note':>25}")
for r in sorted(high_9, key=lambda x: (x["token"], x["date"])):
    rm = r["ret_max"]
    rm_disp = f"{float(rm)*100:+.1f}%" if rm not in ("N/A", "N/A-NO-KLINES") else rm
    print(f"  {r['token']:<10} {r['date']:>12} {r['trigger']:>10} {rm_disp:>10} {r['days_to_max']:>4}  {r['note'][:24]}")

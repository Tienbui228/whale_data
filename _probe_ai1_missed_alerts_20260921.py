"""AI1 · liệt fires bị cắt 09-09..09-20 + ret_max 7d/14d/30d + dd sau ngày bắn."""
import sys, csv, os
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
CSV_PATH = REPO / "data/logs/gom_e_t1_alerts.csv"
KLINES_DIR = REPO / "data/raw/spot_klines_1d"

def _load_daily_closes(sym: str, d_start, d_end) -> dict:
    """Trả dict {date_iso: close_px}. Bỏ trống nếu không có data."""
    out = {}
    import pandas as pd
    for k in range((d_end - d_start).days + 1):
        d = d_start + timedelta(days=k)
        p = KLINES_DIR / f"date={d.isoformat()}" / "part-0.parquet"
        if not p.exists(): continue
        try:
            df = pd.read_parquet(p, columns=["symbol", "close", "high", "low"])
            r = df[df["symbol"] == sym]
            if not r.empty:
                out[d.isoformat()] = (float(r.iloc[0]["close"]), float(r.iloc[0]["high"]), float(r.iloc[0]["low"]))
        except Exception:
            continue
    return out


def _compute_ret_dd(sym: str, fire_date: str, forward_days: int) -> tuple:
    """Trả (ret_max_pct, dd_pct, days_from_fire_to_peak) trong forward_days sau fire.
    ret_max = max(high/close_fire) - 1
    dd = min(low/close_fire) - 1"""
    fd = datetime.strptime(fire_date, "%Y-%m-%d").date()
    d_end = fd + timedelta(days=forward_days)
    data = _load_daily_closes(sym, fd, d_end)
    if fire_date not in data:
        return (None, None, None)
    close_fire = data[fire_date][0]
    if close_fire <= 0: return (None, None, None)
    ret_max = None; dd = None; d_peak = None
    for d_iso, (close_d, high_d, low_d) in data.items():
        if d_iso <= fire_date: continue
        # ret_max: high vs close_fire
        r = high_d / close_fire - 1
        if ret_max is None or r > ret_max:
            ret_max = r
            d_peak = (datetime.strptime(d_iso, "%Y-%m-%d").date() - fd).days
        # dd: low vs close_fire
        d = low_d / close_fire - 1
        if dd is None or d < dd:
            dd = d
    return (ret_max, dd, d_peak)


# Load fires
fires = []
with CSV_PATH.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["fire"] != "True": continue
        if row["cooldown_blocked"] == "True": continue
        d = row["date"]
        if not ("2026-09-09" <= d <= "2026-09-20"): continue
        fires.append({"date": d, "sym": row["symbol"], "tags": row["tags"]})

# Dedupe
seen = set()
uniq = []
for f in fires:
    k = (f["date"], f["sym"])
    if k in seen: continue
    seen.add(k)
    uniq.append(f)

print(f"[GỬI TAY · {len(uniq)} cảnh báo GOM-E bị cắt 09-09..09-20]")
print(f"Nguồn: data/logs/gom_e_t1_alerts.csv · fire=True cooldown_blocked=False")
print(f"{'date':11s} | {'symbol':18s} | {'tags':28s} | {'ret_max_7d':>10s} | {'ret_max_14d':>11s} | {'ret_max_30d':>11s} | {'dd_30d':>7s} | {'d_peak_30d':>10s}")
print(f"{'-'*11} | {'-'*18} | {'-'*28} | {'-'*10} | {'-'*11} | {'-'*11} | {'-'*7} | {'-'*10}")
for f in sorted(uniq, key=lambda x: (x["date"], x["sym"])):
    r7, dd7, d7 = _compute_ret_dd(f["sym"], f["date"], 7)
    r14, dd14, d14 = _compute_ret_dd(f["sym"], f["date"], 14)
    r30, dd30, d30 = _compute_ret_dd(f["sym"], f["date"], 30)
    import math as _m
    def _p(x):
        if x is None or (isinstance(x, float) and _m.isnan(x)): return "N/A"
        return f"{x*100:+.1f}%"
    def _d(x): return str(x) if x is not None else "-"
    print(f"{f['date']:11s} | {f['sym']:18s} | {f['tags']:28s} | {_p(r7):>10s} | {_p(r14):>11s} | {_p(r30):>11s} | {_p(dd30):>7s} | {_d(d30):>10s}")

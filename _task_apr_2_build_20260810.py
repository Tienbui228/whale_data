"""
_task_apr_2_build_20260810.py
A-2b: Prep CSVs → run build_case.py → verify-tay 5 rows.
APR = standard perp, NOT Alpha. No LSR data (all 404).
"""
import sys, io, csv, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM     = "APRUSDT"
SYM_BASE = "APR"
SYM_LOWER = "apr"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-2b BUILD PREP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None, "", "None") else d
    except: return d

# ── 1. Prep perp CSV (from klines) ────────────────────────────────────────
log("\n=== 1. Prep apr_perp_20260810.csv ===")
raw_klines = SCRATCH / f"apr_klines_{DATE_TAG}.csv"
perp_out = SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv"

rows_klines = []
with open(raw_klines, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows_klines.append(row)

log(f"  Klines raw: {len(rows_klines)} rows")

# Exclude today's partial candle (L-21: last complete = 2026-08-09)
perp_rows = []
prev_close = None
for row in rows_klines:
    ot = int(row["open_time"])
    d = datetime.fromtimestamp(ot/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    if d >= "2026-08-10":  # exclude today's partial
        continue
    o  = safe_float(row["open"])
    h  = safe_float(row["high"])
    l  = safe_float(row["low"])
    c  = safe_float(row["close"])
    qv = safe_float(row["quote_vol"])  # quote volume in USDT
    tb = safe_float(row["taker_buy_base"])
    vol_b = safe_float(row["volume"])
    taker_pct = round(tb/vol_b*100, 4) if (tb and vol_b and vol_b > 0) else None
    ret_1d = round((c - prev_close)/prev_close*100, 6) if (c and prev_close) else None
    perp_rows.append({
        "date": d,
        "open": o, "o": o,
        "high": h, "h": h,
        "low":  l, "l": l,
        "close": c, "c": c,
        "vol_quote_usd": qv,
        "taker_pct": taker_pct,
        "ret_1d": ret_1d,
    })
    prev_close = c

PERP_COLS = ["date","open","o","high","h","low","l","close","c","vol_quote_usd","taker_pct","ret_1d"]
with open(perp_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=PERP_COLS)
    w.writeheader(); w.writerows(perp_rows)
log(f"  Saved: {perp_out.name} ({len(perp_rows)} rows)")
log(f"  Date range: {perp_rows[0]['date']} → {perp_rows[-1]['date']}")

# ── 2. Prep funding CSV ────────────────────────────────────────────────────
log("\n=== 2. Prep apr_funding_20260810.csv ===")
raw_fund = SCRATCH / f"apr_funding_{DATE_TAG}.csv"
fund_out = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"

fund_rows = []
with open(raw_fund, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ft = int(row["fundingTime"])
        d = datetime.fromtimestamp(ft/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        fund_rows.append({
            "date": d,
            "fundingRate": row["fundingRate"],
            "markPrice": row.get("markPrice",""),
        })

with open(fund_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","fundingRate","markPrice"])
    w.writeheader(); w.writerows(fund_rows)
log(f"  Saved: {fund_out.name} ({len(fund_rows)} rows)")

# ── 3. Prep OI hist CSV ────────────────────────────────────────────────────
log("\n=== 3. Prep apr_oi_hist_20260810.csv ===")
raw_oi = SCRATCH / f"apr_oi_hist_{DATE_TAG}.csv"
oi_out = SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"

oi_rows = []
with open(raw_oi, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ts = int(row["timestamp"])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_rows.append({
            "date": d,
            "oi_usd": row["sumOpenInterestValue"],
            "oi_token": row["sumOpenInterest"],
        })

with open(oi_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
    w.writeheader(); w.writerows(oi_rows)
log(f"  Saved: {oi_out.name} ({len(oi_rows)} rows)")

# ── 4. Run build_case.py ──────────────────────────────────────────────────
log("\n=== 4. Run build_case.py ===")
CASE_Q = "Co luc gom khong? Neu co: gom tu bao gio, bao nhieu (§3), pha nao vong doi? Neu khong: farm hay xac hay ban-vua-lau?"
cmd = [sys.executable, str(ROOT / "build_case.py"), SYM, DATE_TAG, CASE_Q]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), encoding="utf-8", errors="replace")
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:2000])
log(f"  Exit code: {result.returncode}")

# ── 5. Verify-tay 5 rows (perp CSV fallback — guard-câm workaround) ───────
log("\n=== 5. VERIFY-TAY 5 rows (từ apr_klines CSV) ===")
log("  [Last 5 complete candles, 2026-08-05 → 2026-08-09]")
log(f"  {'date':<12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'ret_1d':>8} {'vol_usd':>14} {'taker':>7}")
log(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*14} {'-'*7}")
tail5 = [r for r in perp_rows if r["date"] >= "2026-08-05"]
for r in tail5:
    vol = safe_float(r["vol_quote_usd"])
    ret = safe_float(r["ret_1d"])
    tk  = safe_float(r["taker_pct"])
    log(f"  {r['date']:<12} {r['open']:>10} {r['h']:>10} {r['l']:>10} {r['close']:>10} "
        f"  {('+' if ret and ret>0 else '')}{ret:.2f}%  ${vol:>12,.0f} {tk:>6.1f}%")

log(f"\n[A-2b BUILD DONE]")

"""
_task_on_2_build_20260810.py
N-2b: Prep CSVs → build_case.py → verify-tay 5 rows.
ON = ALPHA_444. OI UNCALIBRATED ($24.8M peak > $18M).
"""
import sys, io, csv, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM     = "ONUSDT"
SYM_BASE = "ON"
SYM_LOWER = "on"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-2b BUILD PREP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None,"","None") else d
    except: return d

# ── 1. Prep perp CSV ──────────────────────────────────────────────────────────
log("\n=== 1. Prep on_perp CSV ===")
raw_klines = SCRATCH / f"{SYM_LOWER}_klines_{DATE_TAG}.csv"
perp_out = SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv"

rows_k = []
with open(raw_klines, encoding="utf-8") as f:
    for r in csv.DictReader(f): rows_k.append(r)
log(f"  Raw klines: {len(rows_k)} rows")

perp_rows = []; prev_close = None
for row in rows_k:
    ot = int(row["open_time"])
    d = datetime.fromtimestamp(ot/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    if d >= "2026-08-10": continue  # L-21: exclude today's partial
    o = safe_float(row["open"]); h = safe_float(row["high"])
    l = safe_float(row["low"]);  c = safe_float(row["close"])
    qv = safe_float(row["quote_vol"])
    tb = safe_float(row["taker_buy_base"]); vol_b = safe_float(row["volume"])
    taker_pct = round(tb/vol_b*100, 4) if (tb and vol_b and vol_b > 0) else None
    ret_1d = round((c-prev_close)/prev_close*100, 6) if (c and prev_close) else None
    perp_rows.append({
        "date": d, "open": o, "o": o, "high": h, "h": h,
        "low": l, "l": l, "close": c, "c": c,
        "vol_quote_usd": qv, "taker_pct": taker_pct, "ret_1d": ret_1d,
    })
    prev_close = c

PERP_COLS = ["date","open","o","high","h","low","l","close","c","vol_quote_usd","taker_pct","ret_1d"]
with open(perp_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=PERP_COLS)
    w.writeheader(); w.writerows(perp_rows)
log(f"  Saved: {perp_out.name} ({len(perp_rows)} rows)")
log(f"  Range: {perp_rows[0]['date']} → {perp_rows[-1]['date']}")

# ── 2. Prep funding CSV ────────────────────────────────────────────────────────
log("\n=== 2. Prep on_funding CSV ===")
raw_fund = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"
fund_out = SCRATCH / f"{SYM_LOWER}_fund_prep_{DATE_TAG}.csv"
fund_rows = []
with open(raw_fund, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ft = int(row["fundingTime"])
        d = datetime.fromtimestamp(ft/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        fund_rows.append({"date": d, "fundingRate": row["fundingRate"], "markPrice": row.get("markPrice","")})
with open(fund_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","fundingRate","markPrice"])
    w.writeheader(); w.writerows(fund_rows)
log(f"  Saved: {fund_out.name} ({len(fund_rows)} rows)")

# ── 3. Prep OI hist CSV ────────────────────────────────────────────────────────
log("\n=== 3. Prep on_oi_hist CSV ===")
raw_oi = SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"
oi_out = SCRATCH / f"{SYM_LOWER}_oi_hist_prep_{DATE_TAG}.csv"
oi_rows = []
with open(raw_oi, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ts = int(row["timestamp"])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_rows.append({"date": d, "oi_usd": row["sumOpenInterestValue"], "oi_token": row["sumOpenInterest"]})
with open(oi_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
    w.writeheader(); w.writerows(oi_rows)
log(f"  Saved: {oi_out.name} ({len(oi_rows)} rows)")

# ── 4. Alpha vol from store ────────────────────────────────────────────────────
log("\n=== 4. Alpha vol from store ===")
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
alpha_by_d = {}
try:
    import pandas as pd
    for p in alpha_store.rglob("*.parquet"):
        try:
            df = pd.read_parquet(p)
            sub = df[df["symbol"] == SYM_BASE] if "symbol" in df.columns else pd.DataFrame()
            for _, row in sub.iterrows():
                d_col = next((c for c in ["date","open_time","ts"] if c in sub.columns), None)
                d_val = str(row.get(d_col,""))[:10] if d_col else None
                if not d_val: continue
                vol = safe_float(row.get("quote_vol") or row.get("volume"))
                alpha_by_d[d_val] = vol
        except: pass
    log(f"  Alpha rows found: {len(alpha_by_d)}")
    if alpha_by_d:
        sorted_a = sorted(alpha_by_d.items())
        log(f"  Range: {sorted_a[0][0]} → {sorted_a[-1][0]}")
        log(f"  Last 5 alpha vol:")
        for d,v in sorted_a[-5:]:
            log(f"    {d}: ${v:,.0f}" if v else f"    {d}: N/A")
except Exception as e:
    log(f"  Alpha store error: {e}")

# ── 5. Run build_case.py ──────────────────────────────────────────────────────
log("\n=== 5. Run build_case.py ===")
CASE_Q = ("Co luc gom khong? Dang o stage nao neu chieu theo template BTW "
          "(S0 ghe-nen → S0.5 xu-crowd → S1 staging-ke → S2 cau-thang → "
          "S3 xa-vung-nho → S4 xac)? "
          "Cum vi van hanh co dau vet trung BTW/AGT khong?")
cmd = [sys.executable, str(ROOT/"build_case.py"), SYM, DATE_TAG, CASE_Q]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT),
                        encoding="utf-8", errors="replace")
print(result.stdout)
if result.stderr: print("STDERR:", result.stderr[:2000])
log(f"  Exit code: {result.returncode}")

# ── 6. Verify-tay 5 rows ──────────────────────────────────────────────────────
log("\n=== 6. VERIFY-TAY 5 rows (từ on_klines CSV — L-21) ===")
tail5 = [r for r in perp_rows if r["date"] >= "2026-08-05"]
log(f"  {'date':<12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'ret_1d':>9} {'vol_usd':>14} {'taker':>7}")
log(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*9} {'-'*14} {'-'*7}")
for r in tail5:
    vol = safe_float(r["vol_quote_usd"]); ret = safe_float(r["ret_1d"]); tk = safe_float(r["taker_pct"])
    ret_s = f"{'+' if ret and ret>0 else ''}{ret:.2f}%" if ret is not None else "N/A"
    log(f"  {r['date']:<12} {r['open']:>10} {r['h']:>10} {r['l']:>10} {r['close']:>10} "
        f"  {ret_s:>8}  ${vol:>12,.0f} {tk:>6.1f}%")

log(f"\n[N-2b BUILD DONE]")

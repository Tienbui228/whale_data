"""
_probe_apr_1_lsr_20260810.py
A-1: LSR + OI persist — APRUSDT. 4 endpoints + openInterestHist. Verify row-count.
"""
import sys, io, json, csv, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-1 LSR+OI PERSIST  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}"); return None

def save_csv(path, rows, keys):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    log(f"  Saved: {path.name} ({path.stat().st_size:,} bytes, {len(rows)} rows)")
    if len(rows) == 0:
        raise RuntimeError(f"RAISE: 0 rows in {path.name} — abort")

# ── 1. Global LSR ─────────────────────────────────────────────────────────
log(f"\n=== 1. globalLongShortAccountRatio (period=1d, limit=30) ===")
url1 = f"{FAPI}/fapi/v1/globalLongShortAccountRatio?symbol={SYM}&period=1d&limit=30"
glsr = fetch_json(url1)
log(f"  raw count: {len(glsr) if glsr else 'ERROR'}")
if glsr:
    for r in glsr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: longShortRatio={r.get('longShortRatio')} longAccount={r.get('longAccount')} shortAccount={r.get('shortAccount')}")
    out1 = SCRATCH / f"apr_glsr_{DATE_TAG}.csv"
    save_csv(out1, glsr, ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 2. Top Trader Account LSR ─────────────────────────────────────────────
log(f"\n=== 2. topLongShortAccountRatio (period=1d, limit=30) ===")
url2 = f"{FAPI}/fapi/v1/topLongShortAccountRatio?symbol={SYM}&period=1d&limit=30"
tlasr = fetch_json(url2)
log(f"  raw count: {len(tlasr) if tlasr else 'ERROR'}")
if tlasr:
    for r in tlasr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: longShortRatio={r.get('longShortRatio')} longAccount={r.get('longAccount')} shortAccount={r.get('shortAccount')}")
    out2 = SCRATCH / f"apr_tlasr_{DATE_TAG}.csv"
    save_csv(out2, tlasr, ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 3. Top Trader Position LSR ────────────────────────────────────────────
log(f"\n=== 3. topLongShortPositionRatio (period=1d, limit=30) ===")
url3 = f"{FAPI}/fapi/v1/topLongShortPositionRatio?symbol={SYM}&period=1d&limit=30"
tlpsr = fetch_json(url3)
log(f"  raw count: {len(tlpsr) if tlpsr else 'ERROR'}")
if tlpsr:
    for r in tlpsr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: longShortRatio={r.get('longShortRatio')} longAccount={r.get('longAccount')} shortAccount={r.get('shortAccount')}")
    out3 = SCRATCH / f"apr_tlpsr_{DATE_TAG}.csv"
    save_csv(out3, tlpsr, ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 4. Taker Long/Short Ratio ─────────────────────────────────────────────
log(f"\n=== 4. takerlongshortRatio (period=1d, limit=30) ===")
url4 = f"{FAPI}/fapi/v1/takerlongshortRatio?symbol={SYM}&period=1d&limit=30"
tkr = fetch_json(url4)
log(f"  raw count: {len(tkr) if tkr else 'ERROR'}")
if tkr:
    for r in tkr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: buySellRatio={r.get('buySellRatio')} buyVol={r.get('buyVol')} sellVol={r.get('sellVol')}")
    out4 = SCRATCH / f"apr_taker_lsr_{DATE_TAG}.csv"
    save_csv(out4, tkr, ["symbol","buySellRatio","buyVol","sellVol","timestamp"])

# ── 5. openInterestHist ───────────────────────────────────────────────────
log(f"\n=== 5. openInterestHist (period=1d, limit=30) ===")
url5 = f"{FAPI}/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=30"
oih = fetch_json(url5)
log(f"  raw count: {len(oih) if oih else 'ERROR'}")
if oih:
    oi_vals = []
    for r in oih:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_v = float(r.get("sumOpenInterestValue", 0))
        oi_vals.append(oi_v)
        if r == oih[-1] or r == oih[-2] or r == oih[-3] or r == oih[0]:
            log(f"  {ts}: OI_contracts={r.get('sumOpenInterest')} OI_value=${oi_v:,.0f}")
    log(f"  OI range: ${min(oi_vals):,.0f} → ${max(oi_vals):,.0f}")
    log(f"  OI latest: ${oi_vals[-1]:,.0f}")
    flag_uncalib = max(oi_vals) > 18_000_000
    log(f"  UNCALIBRATED: {'YES (OI_max>${18M})' if flag_uncalib else 'NO'}")
    out5 = SCRATCH / f"apr_oi_hist_{DATE_TAG}.csv"
    save_csv(out5, oih, ["symbol","sumOpenInterest","sumOpenInterestValue","timestamp"])

# ── 6. FW Universe check ──────────────────────────────────────────────────
log(f"\n=== 6. FW universe APRUSDT rows ===")
fw_dir = ROOT / "data" / "raw" / "perp_klines_1d"
apr_parts = sorted(fw_dir.glob("*") ) if fw_dir.exists() else []
# count rows for APRUSDT in parquet
try:
    import pandas as pd
    count = 0
    files_found = []
    for p in apr_parts:
        if p.is_dir():
            for f in p.glob("*.parquet"):
                try:
                    df = pd.read_parquet(f, columns=["symbol"])
                    c = (df["symbol"] == SYM).sum()
                    if c > 0:
                        count += c
                        files_found.append(f.name)
                except: pass
    log(f"  APRUSDT rows in FW: {count} across {len(files_found)} partitions")
    if files_found:
        log(f"  First partitions: {files_found[:3]}")
except ImportError:
    log(f"  pandas not available — skip FW count")
except Exception as e:
    log(f"  FW count error: {e}")

# ── Summary ───────────────────────────────────────────────────────────────
log(f"\n=== A-1 SUMMARY ===")
log(f"  glsr:   {len(glsr) if glsr else 0} rows")
log(f"  tlasr:  {len(tlasr) if tlasr else 0} rows")
log(f"  tlpsr:  {len(tlpsr) if tlpsr else 0} rows")
log(f"  taker:  {len(tkr) if tkr else 0} rows")
log(f"  OI:     {len(oih) if oih else 0} rows")
log(f"\n[A-1 DONE]")

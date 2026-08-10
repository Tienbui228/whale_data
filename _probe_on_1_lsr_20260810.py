"""
_probe_on_1_lsr_20260810.py
N-1: LSR 4 endpoints + OI hist 30d — ONUSDT.
Persist NGAY, verify row-count. Khai nguồn L-25.
"""
import sys, io, json, csv, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"
SYM_LOWER = "on"
FAPI = "https://fapi.binance.com"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-1 LSR+OI ONUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
# DATA PROVENANCE (L-25/L-48): source=fapi.binance.com, machine=local scratch, date=now
log(f"  data-source: fapi.binance.com endpoints (public, no auth)")
log(f"  machine: local scratch D:\\Data back test\\whale_data\\scratch")
log(f"  date: {NOW.strftime('%Y-%m-%d')} UTC")

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:90]}: {e}"); return None

def save_csv(path, rows, keys):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    n = len(rows)
    log(f"  Saved: {path.name} ({path.stat().st_size:,} bytes, {n} rows)")
    return n

# ── 1. Global LSR ─────────────────────────────────────────────────────────────
log(f"\n=== 1. globalLongShortAccountRatio ===")
glsr = fetch_json(f"{FAPI}/fapi/v1/globalLongShortAccountRatio?symbol={SYM}&period=1d&limit=30")
log(f"  count: {len(glsr) if glsr else 'ERROR/404'}")
if glsr:
    for r in glsr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: ratio={r.get('longShortRatio')} long={r.get('longAccount')} short={r.get('shortAccount')}")
    save_csv(SCRATCH/f"{SYM_LOWER}_glsr_{DATE_TAG}.csv", glsr,
             ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 2. Top Account LSR ────────────────────────────────────────────────────────
log(f"\n=== 2. topLongShortAccountRatio ===")
tlasr = fetch_json(f"{FAPI}/fapi/v1/topLongShortAccountRatio?symbol={SYM}&period=1d&limit=30")
log(f"  count: {len(tlasr) if tlasr else 'ERROR/404'}")
if tlasr:
    for r in tlasr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: ratio={r.get('longShortRatio')} long={r.get('longAccount')} short={r.get('shortAccount')}")
    save_csv(SCRATCH/f"{SYM_LOWER}_tlasr_{DATE_TAG}.csv", tlasr,
             ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 3. Top Position LSR ───────────────────────────────────────────────────────
log(f"\n=== 3. topLongShortPositionRatio ===")
tlpsr = fetch_json(f"{FAPI}/fapi/v1/topLongShortPositionRatio?symbol={SYM}&period=1d&limit=30")
log(f"  count: {len(tlpsr) if tlpsr else 'ERROR/404'}")
if tlpsr:
    for r in tlpsr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: ratio={r.get('longShortRatio')} long={r.get('longAccount')} short={r.get('shortAccount')}")
    save_csv(SCRATCH/f"{SYM_LOWER}_tlpsr_{DATE_TAG}.csv", tlpsr,
             ["symbol","longShortRatio","longAccount","shortAccount","timestamp"])

# ── 4. Taker ratio ────────────────────────────────────────────────────────────
log(f"\n=== 4. takerlongshortRatio ===")
tkr = fetch_json(f"{FAPI}/fapi/v1/takerlongshortRatio?symbol={SYM}&period=1d&limit=30")
log(f"  count: {len(tkr) if tkr else 'ERROR/404'}")
if tkr:
    for r in tkr[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: buySellRatio={r.get('buySellRatio')} buy={r.get('buyVol')} sell={r.get('sellVol')}")
    save_csv(SCRATCH/f"{SYM_LOWER}_taker_lsr_{DATE_TAG}.csv", tkr,
             ["symbol","buySellRatio","buyVol","sellVol","timestamp"])

# ── 5. OI hist 30d ────────────────────────────────────────────────────────────
log(f"\n=== 5. openInterestHist 30d ===")
oih = fetch_json(f"{FAPI}/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=30")
log(f"  count: {len(oih) if oih else 'ERROR/404'}")
if oih:
    oi_vals = [float(r.get("sumOpenInterestValue", 0)) for r in oih]
    oi_token_vals = [float(r.get("sumOpenInterest", 0)) for r in oih]
    log(f"  OI USD range: ${min(oi_vals):,.0f} → ${max(oi_vals):,.0f}")
    log(f"  OI token range: {min(oi_token_vals):,.0f} → {max(oi_token_vals):,.0f}")
    log(f"  OI latest: ${oi_vals[-1]:,.0f}")
    flag_uncalib = max(oi_vals) > 18_000_000
    log(f"  UNCALIBRATED (>$18M): {flag_uncalib}")
    log(f"\n  First + last 4 rows:")
    for r in [oih[0]] + oih[-3:]:
        ts = datetime.fromtimestamp(int(r["timestamp"])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        log(f"  {ts}: OI={float(r.get('sumOpenInterest',0)):,.2f} OI_usd=${float(r.get('sumOpenInterestValue',0)):,.0f}")
    n = save_csv(SCRATCH/f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv", oih,
                 ["symbol","sumOpenInterest","sumOpenInterestValue","timestamp"])
    log(f"  VERIFY row-count: {n} (expected 30)")

# ── 6. Current OI + premiumIndex ─────────────────────────────────────────────
log(f"\n=== 6. Current OI + mark ===")
oi_now = fetch_json(f"{FAPI}/fapi/v1/openInterest?symbol={SYM}")
pm = fetch_json(f"{FAPI}/fapi/v1/premiumIndex?symbol={SYM}")
if oi_now: log(f"  OI now: {float(oi_now.get('openInterest',0)):,.2f} contracts")
if pm:
    log(f"  markPrice={pm.get('markPrice')} lastFundingRate={pm.get('lastFundingRate')}")
    next_ft = int(pm.get("nextFundingTime", 0))
    log(f"  nextFundingTime: {datetime.fromtimestamp(next_ft/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

# ── 7. Build merged LSR CSV ───────────────────────────────────────────────────
log(f"\n=== 7. Merge LSR → {SYM_LOWER}_lsr_raw_{DATE_TAG}.csv ===")
merged = {}
for ep_name, data, pos_col, acc_col in [
    ("tlpsr", tlpsr, "longAccount", "shortAccount"),
    ("tlasr", tlasr, "longAccount", "shortAccount"),
    ("glsr",  glsr,  "longAccount", "shortAccount"),
]:
    if not data: continue
    for r in data:
        ts = int(r["timestamp"])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        merged.setdefault(d, {})["timestamp"] = ts
        if ep_name == "tlpsr":
            merged[d]["pos_r"] = float(r.get("longShortRatio", 0))
            merged[d]["pos_long"] = float(r.get(pos_col, 0))
            merged[d]["pos_short"] = float(r.get(acc_col, 0))
        elif ep_name == "tlasr":
            merged[d]["acc_r"] = float(r.get("longShortRatio", 0))
            merged[d]["acc_long"] = float(r.get(pos_col, 0))
            merged[d]["acc_short"] = float(r.get(acc_col, 0))
        elif ep_name == "glsr":
            merged[d]["glsr"] = float(r.get("longShortRatio", 0))

if tkr:
    for r in tkr:
        ts = int(r["timestamp"])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        merged.setdefault(d, {})
        merged[d]["taker_lsr"] = float(r.get("buySellRatio", 0))

lsr_rows = []
for d in sorted(merged.keys()):
    row = merged[d]
    pos_r = row.get("pos_r"); acc_r = row.get("acc_r")
    div_raw = round(pos_r/acc_r, 4) if (pos_r and acc_r and acc_r > 0) else None
    lsr_rows.append({
        "date": d, "pos_r_raw": pos_r, "acc_r_raw": acc_r,
        "glsr_raw": row.get("glsr"), "taker_lsr_raw": row.get("taker_lsr"),
        "div_raw": div_raw, "_src": "fapi_LSR_30d",
    })

out_lsr = SCRATCH / f"{SYM_LOWER}_lsr_raw_{DATE_TAG}.csv"
with open(out_lsr, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw","div_raw","_src"])
    w.writeheader(); w.writerows(lsr_rows)
log(f"  Merged LSR: {len(lsr_rows)} rows → {out_lsr.name}")
if lsr_rows:
    log(f"  Range: {lsr_rows[0]['date']} → {lsr_rows[-1]['date']}")
    log(f"  Last 5:")
    for r in lsr_rows[-5:]:
        log(f"    {r['date']}: pos_r={r['pos_r_raw']} acc_r={r['acc_r_raw']} glsr={r['glsr_raw']} div={r['div_raw']}")

# ── 8. Freshwatch merge check ─────────────────────────────────────────────────
log(f"\n=== 8. FreshWatch LSR availability ===")
import csv as csvmod
fw_lsr = {}
for fw_csv in sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csvmod.DictReader(f):
            if row.get("symbol","").upper() == SYM:
                d = row.get("date","")[:10]
                fw_lsr[d] = {
                    "pos_r": row.get("lsr_pos_r"),
                    "acc_r": row.get("lsr_acc_r"),
                    "glsr": row.get("lsr_global_r"),
                }
if fw_lsr:
    fw_dates = sorted(fw_lsr.keys())
    log(f"  FW LSR rows: {len(fw_lsr)}")
    log(f"  Range: {fw_dates[0]} → {fw_dates[-1]}")
    log(f"  Last 3: {[(d, fw_lsr[d]) for d in fw_dates[-3:]]}")
else:
    log(f"  FW LSR: 0 rows for {SYM}")

log(f"\n[N-1 DONE]")
log(f"  LSR endpoints: {4 - sum([glsr is None, tlasr is None, tlpsr is None, tkr is None])}/4 FOUND")
log(f"  OI rows: {len(oih) if oih else 0}")
log(f"  FW LSR supplement: {len(fw_lsr)} rows")

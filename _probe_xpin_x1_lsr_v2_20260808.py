"""
_probe_xpin_x1_lsr_v2_20260808.py
X-1 v2: LSR persist XPINUSDT — freshwatch tất cả tháng (FAPI 404 đã confirm).
Merge Jun + Jul + Aug freshwatch. Save CSV + verify.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-1 LSR v2  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")
log("NOTE: FAPI LSR 404 confirmed (XPIN LSR not served by FAPI)")
log("Source: freshwatch export (derived_1h canonical)")

SYM = "XPINUSDT"

FW_FILES = [
    SCRATCH / "freshwatch_daily_2026-06.csv",
    SCRATCH / "freshwatch_daily_2026-07.csv",
    VPS_EXPORT / "freshwatch_daily_2026-08.csv",
]

def safe_float(v):
    if v in (None, "", "nan", "NaN", "None"):
        return None
    try:
        return round(float(v), 6)
    except:
        return None

all_by_date = {}

for fw_path in FW_FILES:
    if not fw_path.exists():
        log(f"  {fw_path.name}: NOT FOUND (skip)")
        continue
    with open(fw_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cnt = 0
        for row in reader:
            sym_col = row.get("symbol", row.get("sym", "")).upper()
            if sym_col != SYM:
                continue
            dt = str(row.get("date", "")).strip()
            if not dt:
                continue

            pr = None
            for k in ("lsr_pos_r", "lsr_pos", "pos_r"):
                v = row.get(k)
                pr = safe_float(v)
                if pr is not None: break

            ar = None
            for k in ("lsr_acc_r", "lsr_acc", "acc_r"):
                v = row.get(k)
                ar = safe_float(v)
                if ar is not None: break

            gr = None
            for k in ("lsr_global_r", "lsr_global", "glsr_raw", "gLSR"):
                v = row.get(k)
                gr = safe_float(v)
                if gr is not None: break

            tlsr = None
            for k in ("taker_lsr_raw", "taker_lsr", "lsr_taker_r"):
                v = row.get(k)
                tlsr = safe_float(v)
                if tlsr is not None: break

            all_by_date[dt] = {
                "date": dt,
                "pos_r_raw": pr,
                "acc_r_raw": ar,
                "glsr_raw": gr,
                "taker_lsr_raw": tlsr,
                "_src": f"freshwatch_{fw_path.stem}",
            }
            cnt += 1
    log(f"  {fw_path.name}: {cnt} XPIN rows loaded")

sorted_dates = sorted(all_by_date.keys())
log(f"\n=== MERGED ===")
log(f"  Total dates: {len(sorted_dates)}")
if sorted_dates:
    log(f"  Range: {sorted_dates[0]} → {sorted_dates[-1]}")

# Save CSV
DATE_TAG = "20260808"
csv_path = SCRATCH / f"xpin_lsr_raw_{DATE_TAG}.csv"
COLS = ["date", "pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw", "_src"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    writer.writeheader()
    for dt in sorted_dates:
        row = all_by_date[dt]
        writer.writerow({k: row.get(k, "") for k in COLS})
log(f"  Saved: {csv_path.name}")

# Coverage check — last 30 dates
last30 = sorted_dates[-30:] if len(sorted_dates) >= 30 else sorted_dates
log(f"\n=== COVERAGE CHECK (last 30 dates: {last30[0] if last30 else 'N/A'} → {last30[-1] if last30 else 'N/A'}) ===")
for fld in ["pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw"]:
    non_null = sum(1 for dt in last30
                   if all_by_date[dt].get(fld) not in (None, "", "nan"))
    status = "PASS" if non_null > len(last30) * 0.5 else "FAIL"
    log(f"  {fld}: {non_null}/{len(last30)} — {status}")

# Last 10 rows table
log(f"\n=== LAST 10 ROWS ===")
log(f"  {'date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'taker':>7} {'src'}")
for dt in sorted_dates[-10:]:
    r = all_by_date[dt]
    src_short = r.get("_src","")[-12:]
    log(f"  {dt:<12} "
        f"{str(r.get('pos_r_raw',''))[:7]:>7} "
        f"{str(r.get('acc_r_raw',''))[:7]:>7} "
        f"{str(r.get('glsr_raw',''))[:7]:>7} "
        f"{str(r.get('taker_lsr_raw',''))[:7]:>7} "
        f"  {src_short}")

log("\n[X-1 LSR v2 DONE]")

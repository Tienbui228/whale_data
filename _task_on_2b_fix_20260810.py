"""_task_on_2b_fix_20260810.py — rename prep CSVs to match build_case.py expected names, rebuild."""
import sys, io, csv, json, subprocess, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "ONUSDT"
SYM_LOWER = "on"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-2b FIX  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# Overwrite on_funding_20260810.csv with date-indexed prep (date,fundingRate,markPrice)
src_fund = SCRATCH / f"{SYM_LOWER}_fund_prep_{DATE_TAG}.csv"
dst_fund = SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv"
shutil.copy2(src_fund, dst_fund)
log(f"  Copied: {src_fund.name} → {dst_fund.name}")

# Overwrite on_oi_hist_20260810.csv with date-indexed prep (date,oi_usd,oi_token)
src_oi = SCRATCH / f"{SYM_LOWER}_oi_hist_prep_{DATE_TAG}.csv"
dst_oi = SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"
shutil.copy2(src_oi, dst_oi)
log(f"  Copied: {src_oi.name} → {dst_oi.name}")

# Verify
def sf(v):
    try: return float(v) if v else None
    except: return None

with open(dst_fund, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
log(f"  on_funding: {len(rows)} rows, headers={list(rows[0].keys()) if rows else []}")

with open(dst_oi, encoding="utf-8") as f:
    rows_oi = list(csv.DictReader(f))
log(f"  on_oi_hist: {len(rows_oi)} rows, headers={list(rows_oi[0].keys()) if rows_oi else []}")

# Run build_case.py again
log(f"\n=== Run build_case.py ===")
CASE_Q = ("Co luc gom khong? Dang o stage nao neu chieu theo template BTW "
          "(S0 ghe-nen → S0.5 xu-crowd → S1 staging-ke → S2 cau-thang → "
          "S3 xa-vung-nho → S4 xac)? "
          "Cum vi van hanh co dau vet trung BTW/AGT khong?")
cmd = [sys.executable, str(ROOT/"build_case.py"), SYM, DATE_TAG, CASE_Q]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT),
                        encoding="utf-8", errors="replace")
print(result.stdout)
if result.stderr: print("STDERR:", result.stderr[:3000])
log(f"  Exit code: {result.returncode}")

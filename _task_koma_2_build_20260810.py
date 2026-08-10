"""
_task_koma_2_build_20260810.py
K-2b: Rename koma_* → koma naming convention + run build_case.py + verify
"""
import sys, io, json, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
DATE_TAG = "20260810"
SYM_PERP = "KOMAUSDT"
SYM_BASE = "KOMA"
SYM_LOWER = "koma"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-2b BUILD  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

CASE_Q = ("Có ai gom hàng không? Gom từ bao giờ, bao nhiêu "
          "(§3 ba phương pháp), đang ở pha nào vòng đời?")

# ── Step 1: input files already named koma_* — verify ────────────────────
log("\n=== Step 1: Verify input files (koma_* naming) ===")
inputs_needed = [
    (f"koma_perp_{DATE_TAG}.csv",        f"{SYM_LOWER}_perp_{DATE_TAG}.csv"),
    (f"koma_lsr_raw_{DATE_TAG}.csv",     f"{SYM_LOWER}_lsr_raw_{DATE_TAG}.csv"),
    (f"koma_funding_{DATE_TAG}.csv",     f"{SYM_LOWER}_funding_{DATE_TAG}.csv"),
    (f"koma_oi_hist_{DATE_TAG}.csv",     f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv"),
    (f"koma_spot_{DATE_TAG}.csv",        f"{SYM_LOWER}_spot_{DATE_TAG}.csv"),
    (f"koma_bapi_{DATE_TAG}.json",       f"{SYM_LOWER}_bapi_{DATE_TAG}.json"),
    (f"koma_perp_info_{DATE_TAG}.json",  f"{SYM_LOWER}_perp_info_{DATE_TAG}.json"),
]
# Files are already named koma_* which matches SYM_LOWER=koma — no copy needed
# Just verify they all exist
for src_name, dst_name in inputs_needed:
    p = SCRATCH / src_name
    # src and dst are same in this case (SYM_LOWER=koma=prefix)
    if p.exists():
        log(f"  OK: {p.name} ({p.stat().st_size:,} bytes)")
    else:
        log(f"  MISSING: {p.name}")

# ── Step 2: L-34 backup ────────────────────────────────────────────────────
log("\n=== Step 2: L-34 backup ===")
case_xlsx = CASE_DIR / f"CASE_{SYM_BASE}.xlsx"
if case_xlsx.exists():
    bkp = SCRATCH / f"CASE_{SYM_BASE}_bak_{NOW.strftime('%Y%m%d_%H%M%S')}.xlsx"
    shutil.copy2(case_xlsx, bkp)
    log(f"  Backup: {bkp.name}")
else:
    log(f"  No existing CASE_{SYM_BASE}.xlsx — fresh build")

# ── Step 3: build_case.py ─────────────────────────────────────────────────
log("\n=== Step 3: build_case.py ===")
cmd = [sys.executable, str(ROOT / "build_case.py"), SYM_PERP, DATE_TAG, CASE_Q]
log(f"  CMD: {' '.join(cmd[:3])} ...")
result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", cwd=str(ROOT))
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])
log(f"  BUILD exit={result.returncode}")

# ── Step 4: Verify CASE_KOMA.xlsx ─────────────────────────────────────────
log(f"\n=== Step 4: Verify CASE_{SYM_BASE}.xlsx ===")
if case_xlsx.exists():
    wb = openpyxl.load_workbook(str(case_xlsx), read_only=True)
    log(f"  Sheets: {wb.sheetnames}")
    ws = wb["DAILY"]
    max_row = ws.max_row
    log(f"  DAILY: {max_row} rows × {ws.max_column} cols")
    headers = [c.value for c in next(ws.iter_rows(min_row=2, max_row=2))]
    log(f"  Headers (row 2): {headers}")
    data_rows = list(ws.iter_rows(min_row=3, values_only=True))
    log(f"  Total data rows: {len(data_rows)}")

    log(f"\n  === LAST 5 DAILY ROWS FULL (verify tay — guard-câm check) ===")
    for row in data_rows[-5:]:
        row_dict = {h: v for h, v in zip(headers, row)}
        log(f"\n  ── Row (date={row[0]}) ──")
        for h, v in zip(headers, row):
            if v is not None:
                log(f"    {h}: {v}")
            else:
                log(f"    {h}: None")

    # Check CASE sheet
    log(f"\n  === CASE sheet ===")
    cs = wb["CASE"]
    for r in cs.iter_rows(values_only=True):
        if r[0]:
            log(f"  {r[0]}: {str(r[1])[:100] if r[1] else ''}")
    wb.close()
    log(f"\n  File size: {case_xlsx.stat().st_size:,} bytes")

    # A.5: performance table (7/14/21/28d + %chg from 28d high)
    log(f"\n  === A.5: Performance table (last 28d) ===")
    wb2 = openpyxl.load_workbook(str(case_xlsx), read_only=True)
    ws2 = wb2["DAILY"]
    d_rows = list(ws2.iter_rows(min_row=3, values_only=True))
    hdrs2 = [c.value for c in next(ws2.iter_rows(min_row=2, max_row=2))]
    wb2.close()
    # Find close col index
    close_idx = None
    for i, h in enumerate(hdrs2):
        if h in ("c","close","px_avg"):
            close_idx = i; break
    if close_idx is not None and len(d_rows) >= 28:
        px_now  = d_rows[-1][close_idx]
        px_7d   = d_rows[-8][close_idx]  if len(d_rows)>=8  else None
        px_14d  = d_rows[-15][close_idx] if len(d_rows)>=15 else None
        px_21d  = d_rows[-22][close_idx] if len(d_rows)>=22 else None
        px_28d  = d_rows[-29][close_idx] if len(d_rows)>=29 else None
        high_28 = max(r[close_idx] for r in d_rows[-28:] if r[close_idx] is not None)
        def pct(a,b): return f"{(a/b-1)*100:+.1f}%" if a and b else "N/A"
        log(f"  Current (08-09): {px_now}")
        log(f"  7d ago  (08-02): {px_7d}  chg={pct(px_now,px_7d)}")
        log(f"  14d ago (07-26): {px_14d} chg={pct(px_now,px_14d)}")
        log(f"  21d ago (07-19): {px_21d} chg={pct(px_now,px_21d)}")
        log(f"  28d ago (07-12): {px_28d} chg={pct(px_now,px_28d)}")
        log(f"  28d high:        {high_28}  px-vs-28dH={pct(px_now,high_28)}")
    else:
        log(f"  close_idx={close_idx} — OHLC may be None (guard-câm bug)")
        # Fallback: compute from perp CSV
        log(f"  Fallback: reading perp CSV directly...")
        import csv as csvmod
        perp_csv = SCRATCH / f"koma_perp_{DATE_TAG}.csv"
        with open(perp_csv, encoding="utf-8") as f:
            p_rows = list(csvmod.DictReader(f))
        if p_rows:
            def get_c(r): return float(r.get("close",r.get("c",0)) or 0)
            closes = [(r['date'], get_c(r)) for r in p_rows]
            c_now  = closes[-1]
            c_7d   = closes[-8]  if len(closes)>=8  else None
            c_14d  = closes[-15] if len(closes)>=15 else None
            c_21d  = closes[-22] if len(closes)>=22 else None
            c_28d  = closes[-29] if len(closes)>=29 else None
            high_28 = max(c for d,c in closes[-28:])
            def pct2(a,b): return f"{(a/b-1)*100:+.1f}%" if a and b else "N/A"
            log(f"  [from perp CSV]")
            log(f"  Current ({c_now[0]}): {c_now[1]:.6f}")
            if c_7d:  log(f"  7d  ({c_7d[0]}): {c_7d[1]:.6f}  chg={pct2(c_now[1],c_7d[1])}")
            if c_14d: log(f"  14d ({c_14d[0]}): {c_14d[1]:.6f}  chg={pct2(c_now[1],c_14d[1])}")
            if c_21d: log(f"  21d ({c_21d[0]}): {c_21d[1]:.6f}  chg={pct2(c_now[1],c_21d[1])}")
            if c_28d: log(f"  28d ({c_28d[0]}): {c_28d[1]:.6f}  chg={pct2(c_now[1],c_28d[1])}")
            log(f"  28d high: {high_28:.6f}  px-vs-28dH={pct2(c_now[1],high_28)}")
else:
    log(f"  CASE_{SYM_BASE}.xlsx NOT CREATED")

log(f"\n[K-2b BUILD DONE]")

"""
_probe_apr_6_crossref_20260810.py
A-6: Sổ chéo crossref — APRUSDT.
grep agent_log, FW count, gom_scan, case_index
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
DATE_TAG = "20260810"
SYM = "APRUSDT"
SYM_BASE = "APR"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-6 CROSSREF  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# ── 1. agent_log mentions ─────────────────────────────────────────────────
log(f"\n=== 1. agent_log.md mentions of APR ===")
agent_log = ROOT / "agent_log.md"
if agent_log.exists():
    lines = agent_log.read_text(encoding="utf-8").splitlines()
    hits = [(i+1, l) for i,l in enumerate(lines) if "APR" in l.upper() or "APRUSDT" in l.upper()]
    log(f"  Total mentions: {len(hits)}")
    for n,l in hits[:20]:
        log(f"  L{n}: {l[:100]}")
else:
    log(f"  agent_log.md not found")

# ── 2. FW universe APRUSDT ────────────────────────────────────────────────
log(f"\n=== 2. FW freshwatch row count for APRUSDT ===")
scratch = ROOT / "scratch"
fw_count = 0
for fw_csv in sorted(scratch.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == SYM:
                fw_count += 1
log(f"  APRUSDT rows in freshwatch: {fw_count}")

# ── 3. gom_scan ────────────────────────────────────────────────────────────
log(f"\n=== 3. gom_scan.csv check ===")
gom_scan = ROOT / "scratch" / "gom_scan.csv"
if gom_scan.exists():
    with open(gom_scan, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    apr_gom = [r for r in rows if SYM_BASE in (r.get("symbol","") or "").upper()]
    log(f"  gom_scan rows for APR: {len(apr_gom)}")
    for r in apr_gom[:5]:
        log(f"    {r}")
else:
    log(f"  gom_scan.csv not found")

# ── 4. CASE_INDEX check ────────────────────────────────────────────────────
log(f"\n=== 4. CASE_INDEX — APR registered? ===")
import openpyxl
idx = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
if idx.exists():
    wb = openpyxl.load_workbook(str(idx), read_only=True)
    ws = wb["INDEX"]
    found = False
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        row_str = " ".join(str(c) for c in row if c).upper()
        if "APR" in row_str and "CASE_APR" in row_str:
            log(f"  Row {i} (APR already registered): {[str(c)[:30] if c else None for c in row]}")
            found = True
    if not found:
        log(f"  APR not yet in CASE_INDEX (expected — not registered yet)")
    wb.close()

# ── 5. Other APR* in FW ────────────────────────────────────────────────────
log(f"\n=== 5. Other APR* symbols in FW ===")
apr_variants_fw = set()
for fw_csv in sorted(scratch.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","").upper()
            if sym.startswith("APR") and sym != SYM:
                apr_variants_fw.add(sym)
log(f"  APR* variants in FW: {sorted(apr_variants_fw)}")

# ── 6. Alpha store check ───────────────────────────────────────────────────
log(f"\n=== 6. Alpha klines store check ===")
alpha_dir = ROOT / "data" / "raw" / "spot_klines_1d"
if alpha_dir.exists():
    try:
        import pandas as pd
        count = 0
        for p in alpha_dir.rglob("*.parquet"):
            try:
                df = pd.read_parquet(p, columns=["symbol"])
                c = (df["symbol"] == SYM_BASE).sum()
                if c > 0: count += c
            except: pass
        log(f"  APR in alpha spot store: {count} rows")
    except Exception as e:
        log(f"  Alpha store check: {e}")
else:
    log(f"  Alpha spot store not found (expected — APR not Alpha)")

log(f"\n[A-6 CROSSREF DONE]")

"""
_probe_on_6_crossref_20260810.py
N-6: Cross-ref grep ONUSDT / ON in ledger, u50, EVENTS, MM_BOOK, gom_scan.
data-source: local files (docs/case_files, data, scratch)
machine: local
date: 2026-08-10
"""
import sys, io, csv, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
DATE_TAG = "20260810"
SYM = "ONUSDT"; SYM_BASE = "ON"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"N-6 CROSS-REF ON  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def grep_csv(path, sym_variants, label, cols_check=None, limit=10):
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_str = " ".join(str(v) for v in row.values()).upper()
                if any(v.upper() in row_str for v in sym_variants):
                    hits.append(row)
        log(f"  [{label}] {path.name}: {len(hits)} hits")
        for r in hits[:limit]:
            if cols_check:
                line = {k: r.get(k,"") for k in cols_check if k in r}
            else:
                line = dict(list(r.items())[:6])
            log(f"    {line}")
    except Exception as e:
        log(f"  [{label}] {path.name}: ERROR {e}")
    return hits

def grep_json(path, sym_variants, label, limit=5):
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        txt = json.dumps(data)
        for v in sym_variants:
            if v.upper() in txt.upper():
                log(f"  [{label}] {path.name}: FOUND '{v}'")
                hits.append(v)
                break
        if not hits:
            log(f"  [{label}] {path.name}: not found")
    except Exception as e:
        log(f"  [{label}] {path.name}: ERROR {e}")
    return hits

VARIANTS = ["ONUSDT", "ON/USDT", " ON ", '"ON"', "'ON'"]

# ── 1. gom_state.json ─────────────────────────────────────────────────────────
log("\n=== 1. gom_state.json ===")
gom_state = ROOT / "gom_state.json"
if gom_state.exists():
    try:
        with open(gom_state, encoding="utf-8", errors="replace") as f:
            gs = json.load(f)
        # gom_state keys are symbols
        found_keys = [k for k in gs if "ON" in k.upper() and "ONUSDT" in k.upper()]
        log(f"  gom_state keys matching ON: {found_keys}")
        if found_keys:
            for k in found_keys:
                log(f"    {k}: {json.dumps(gs[k])[:200]}")
        else:
            log(f"  ONUSDT NOT in gom_state.json (confirmed from N-0)")
    except Exception as e:
        log(f"  gom_state error: {e}")
else:
    log("  gom_state.json not found")

# ── 2. FreshWatch daily CSVs ──────────────────────────────────────────────────
log("\n=== 2. FreshWatch daily CSVs ===")
fw_files = sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv"))
log(f"  Found: {len(fw_files)} FW files")
fw_hits = []
for fw in fw_files:
    try:
        with open(fw, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("symbol","").upper() == "ONUSDT":
                    fw_hits.append(row)
    except: pass
log(f"  ONUSDT rows in FW: {len(fw_hits)}")
if fw_hits:
    dates = [r.get("date","")[:10] for r in fw_hits]
    log(f"  Range: {min(dates)} → {max(dates)}")
    log(f"  Last 5:")
    for r in fw_hits[-5:]:
        log(f"    {r.get('date','')[:10]}: pos_r={r.get('lsr_pos_r','')} acc_r={r.get('lsr_acc_r','')} "
            f"glsr={r.get('lsr_global_r','')} taker={r.get('taker_lsr_raw','')}")

# ── 3. CASE_INDEX.xlsx ────────────────────────────────────────────────────────
log("\n=== 3. CASE_INDEX.xlsx ===")
case_idx = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
if case_idx.exists():
    try:
        import openpyxl
        wb = openpyxl.load_workbook(case_idx, read_only=True, data_only=True)
        for sh_name in wb.sheetnames:
            sh = wb[sh_name]
            rows_all = list(sh.iter_rows(values_only=True))
            for row in rows_all:
                row_str = " ".join(str(v) for v in row if v).upper()
                if "ONUSDT" in row_str or (" ON " in row_str and "USDT" in row_str):
                    log(f"  Sheet={sh_name}: {row}")
    except Exception as e:
        log(f"  CASE_INDEX error: {e}")
else:
    log("  CASE_INDEX.xlsx not found")

# ── 4. ledger_v2 / Zone A check ──────────────────────────────────────────────
log("\n=== 4. Zone A / Ledger check ===")
# Check docs/case_files for any CASE_ON
case_on = ROOT / "docs" / "case_files" / "CASE_ON.xlsx"
log(f"  CASE_ON.xlsx exists: {case_on.exists()}")

ledger_candidates = list((ROOT/"docs").rglob("ledger*.xlsx")) + list((ROOT/"docs").rglob("ledger*.csv"))
log(f"  Ledger files found: {[p.name for p in ledger_candidates]}")
for lp in ledger_candidates[:3]:
    if lp.suffix == ".csv":
        grep_csv(lp, [SYM, SYM_BASE], "ledger", limit=5)
    elif lp.suffix == ".xlsx":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(lp, read_only=True, data_only=True)
            hits = 0
            for sh_name in wb.sheetnames:
                sh = wb[sh_name]
                for row in sh.iter_rows(values_only=True):
                    rs = " ".join(str(v) for v in row if v).upper()
                    if "ONUSDT" in rs or (SYM_BASE in rs.split()):
                        hits += 1
                        if hits <= 3: log(f"  ledger sheet={sh_name}: {row[:6]}")
            log(f"  ledger {lp.name}: {hits} rows matching")
        except Exception as e:
            log(f"  ledger error: {e}")

# ── 5. u50 data / gom_scan scratch ───────────────────────────────────────────
log("\n=== 5. u50 / gom_scan scratch ===")
scratch_csvs = list((ROOT/"scratch").glob("*.csv"))
log(f"  Scratch CSVs: {len(scratch_csvs)}")
gom_scan_files = [p for p in scratch_csvs if "gom" in p.name.lower() or "scan" in p.name.lower()]
log(f"  GOM/scan files: {[p.name for p in gom_scan_files]}")
for p in gom_scan_files[:5]:
    grep_csv(p, [SYM, SYM_BASE], "gom_scan", limit=3)

# ── 6. MM_BOOK / signals logs ─────────────────────────────────────────────────
log("\n=== 6. MM_BOOK / signals / agent_log ===")
agent_log = ROOT / "agent_log.md"
if agent_log.exists():
    with open(agent_log, encoding="utf-8", errors="replace") as f:
        content = f.read()
    # find lines mentioning ON
    lines = content.split("\n")
    on_lines = [l for l in lines if re.search(r'\bON\b|\bONUSDT\b', l)]
    log(f"  agent_log ON mentions: {len(on_lines)}")
    for l in on_lines[-10:]:
        log(f"    {l[:120]}")

# ── 7. events / EVENTS files ──────────────────────────────────────────────────
log("\n=== 7. EVENTS files (scratch) ===")
event_files = [(ROOT/"scratch").glob("*event*"), (ROOT/"scratch").glob("*EVENTS*"),
               (ROOT/"docs").rglob("*event*")]
found_ev = []
for gen in event_files:
    found_ev.extend(list(gen))
log(f"  Event files: {[p.name for p in found_ev[:10]]}")
for p in found_ev[:5]:
    if p.suffix == ".csv":
        grep_csv(p, [SYM, SYM_BASE], "events", limit=3)

log(f"\n[N-6 DONE]")

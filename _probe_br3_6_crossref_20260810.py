"""
_probe_br3_6_crossref_20260810.py
BR3-6: Sổ chéo — grep BROCCOLIF3B AND BROCCOLI714 separately
Sources: ledger_v2, EVENTS, agent_log, gom_scan, freshwatch, CASE_INDEX
"""
import sys, io, json, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BR3-6 CROSSREF  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def grep_file(path, patterns, context=1):
    """Search file for patterns, return list of (line_no, line) matches."""
    results = {p: [] for p in patterns}
    if not path.exists():
        return results, f"NOT FOUND: {path}"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            for p in patterns:
                if p.upper() in line.upper():
                    ctx_start = max(0, i - context)
                    ctx_end   = min(len(lines), i + context + 1)
                    results[p].append((i+1, line.strip()))
        return results, f"OK ({len(lines)} lines)"
    except Exception as e:
        return results, f"ERROR: {e}"

def grep_text(text, patterns):
    results = {p: [] for p in patterns}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for p in patterns:
            if p.upper() in line.upper():
                results[p].append((i+1, line.strip()))
    return results

TARGETS = ["BROCCOLIF3B", "BROCCOLI714"]

# ── 1. agent_log.md ─────────────────────────────────────────────────────────
log("\n=== 1. agent_log.md ===")
ag_path = ROOT / "agent_log.md"
res, status = grep_file(ag_path, TARGETS)
log(f"  Status: {status}")
for t in TARGETS:
    hits = res[t]
    log(f"  {t}: {len(hits)} mentions")
    for ln, line in hits[-5:]:
        log(f"    L{ln}: {line[:120]}")

# ── 2. CASE_INDEX.xlsx → sheet LESSONS + scan all sheets ─────────────────
log("\n=== 2. CASE_INDEX.xlsx ===")
try:
    import openpyxl
    idx_path = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
    if idx_path.exists():
        wb = openpyxl.load_workbook(str(idx_path), read_only=True)
        log(f"  Sheets: {wb.sheetnames}")
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            hits_f3b = []; hits_714 = []
            for r in ws.iter_rows(values_only=True):
                row_str = " | ".join(str(c) for c in r if c is not None)
                if "BROCCOLIF3B" in row_str.upper():
                    hits_f3b.append(row_str[:150])
                if "BROCCOLI714" in row_str.upper():
                    hits_714.append(row_str[:150])
            if hits_f3b:
                log(f"  [{sheet_name}] BROCCOLIF3B: {len(hits_f3b)} rows")
                for h in hits_f3b[:3]:
                    log(f"    {h}")
            if hits_714:
                log(f"  [{sheet_name}] BROCCOLI714: {len(hits_714)} rows")
                for h in hits_714[:3]:
                    log(f"    {h}")
            if not hits_f3b and not hits_714:
                log(f"  [{sheet_name}]: no BROCCOLI hits")
        wb.close()
    else:
        log(f"  CASE_INDEX.xlsx not found")
except Exception as e:
    log(f"  ERROR: {e}")

# ── 3. ledger_v2.xlsx ─────────────────────────────────────────────────────
log("\n=== 3. ledger_v2.xlsx ===")
ledger_candidates = [
    ROOT / "docs" / "ledger_v2.xlsx",
    ROOT / "ledger_v2.xlsx",
    ROOT / "data" / "ledger_v2.xlsx",
]
ledger_path = None
for p in ledger_candidates:
    if p.exists():
        ledger_path = p; break
if ledger_path:
    try:
        wb2 = openpyxl.load_workbook(str(ledger_path), read_only=True)
        log(f"  Found: {ledger_path.relative_to(ROOT)}, sheets: {wb2.sheetnames}")
        for sheet_name in wb2.sheetnames:
            ws2 = wb2[sheet_name]
            hits_f3b = []; hits_714 = []
            for r in ws2.iter_rows(values_only=True):
                row_str = " | ".join(str(c) for c in r if c is not None)
                if "BROCCOLIF3B" in row_str.upper():
                    hits_f3b.append(row_str[:150])
                if "BROCCOLI714" in row_str.upper():
                    hits_714.append(row_str[:150])
            if hits_f3b:
                log(f"  [{sheet_name}] BROCCOLIF3B: {len(hits_f3b)} rows")
                for h in hits_f3b[:5]:
                    log(f"    {h}")
            if hits_714:
                log(f"  [{sheet_name}] BROCCOLI714: {len(hits_714)} rows")
                for h in hits_714[:5]:
                    log(f"    {h}")
        wb2.close()
    except Exception as e:
        log(f"  ERROR: {e}")
else:
    log(f"  ledger_v2.xlsx NOT FOUND in any candidate path")
    log(f"  Candidates checked: {[str(p) for p in ledger_candidates]}")

# ── 4. EVENTS CSV / parquet ───────────────────────────────────────────────
log("\n=== 4. EVENTS data ===")
events_candidates = list(ROOT.glob("data/raw/events*.csv")) + \
                    list(ROOT.glob("data/events*.csv")) + \
                    list(ROOT.glob("scratch/events*.csv"))
for ep in events_candidates[:5]:
    res2, st = grep_file(ep, TARGETS)
    log(f"  {ep.name}: {st}")
    for t in TARGETS:
        if res2[t]:
            log(f"    {t}: {len(res2[t])} hits")
            for ln, line in res2[t][:3]:
                log(f"      L{ln}: {line[:100]}")
if not events_candidates:
    log(f"  No EVENTS CSV files found")

# ── 5. freshwatch / freshwatch_daily ─────────────────────────────────────
log("\n=== 5. Freshwatch daily ===")
fw_candidates = list(SCRATCH.glob("freshwatch_daily*.csv")) + \
                list((ROOT / "data" / "raw").glob("freshwatch_daily*.csv"))
for fp in fw_candidates[:5]:
    res3, st = grep_file(fp, TARGETS)
    log(f"  {fp.name}: {st}")
    for t in TARGETS:
        hits3 = res3[t]
        if hits3:
            log(f"    {t}: {len(hits3)} rows")
            for ln, line in hits3[:3]:
                log(f"      L{ln}: {line[:120]}")
if not fw_candidates:
    log(f"  No freshwatch CSVs found in scratch/ or data/raw/")

# ── 6. gom_scan.py / gom_state / signals.py ──────────────────────────────
log("\n=== 6. GOM scripts ===")
gom_candidates = list(ROOT.glob("gom_scan*.py")) + \
                 list(ROOT.glob("scripts/gom_scan*.py")) + \
                 list(ROOT.glob("scripts/signals.py")) + \
                 list((ROOT / "binance-bot-signals").glob("*.py") if (ROOT / "binance-bot-signals").exists() else []) + \
                 list(Path(r"D:\Data back test\binance-bot-signals").glob("*.py") if Path(r"D:\Data back test\binance-bot-signals").exists() else [])
gom_state_files = list(ROOT.glob("gom_state*.json")) + list(ROOT.glob("scratch/gom_state*.json"))

for gf in gom_candidates[:6]:
    res4, st = grep_file(gf, TARGETS)
    log(f"  {gf.name}: {st}")
    for t in TARGETS:
        if res4[t]:
            log(f"    {t}: {len(res4[t])} mentions")
            for ln, line in res4[t][:3]:
                log(f"      L{ln}: {line[:100]}")

for gf in gom_state_files[:3]:
    try:
        data = json.loads(gf.read_text(encoding="utf-8"))
        text = json.dumps(data)
        for t in TARGETS:
            if t.upper() in text.upper():
                log(f"  {gf.name}: contains {t}")
    except Exception as e:
        log(f"  {gf.name}: ERROR {e}")

if not gom_candidates and not gom_state_files:
    log(f"  No GOM scripts or state files found")

# ── 7. MM_BOOK / u50 / universe files ─────────────────────────────────────
log("\n=== 7. MM_BOOK / universe files ===")
mm_candidates = list(ROOT.glob("MM_BOOK*.xlsx")) + \
                list(ROOT.glob("docs/*.xlsx")) + \
                list(ROOT.glob("data/config/*.json"))
for mf in mm_candidates[:10]:
    if mf.suffix == ".xlsx":
        try:
            wb3 = openpyxl.load_workbook(str(mf), read_only=True)
            for sheet_name in wb3.sheetnames:
                ws3 = wb3[sheet_name]
                hits_f3b = []; hits_714 = []
                for r in ws3.iter_rows(values_only=True):
                    row_str = " | ".join(str(c) for c in r if c is not None)
                    if "BROCCOLIF3B" in row_str.upper():
                        hits_f3b.append(row_str[:150])
                    if "BROCCOLI714" in row_str.upper():
                        hits_714.append(row_str[:150])
                if hits_f3b or hits_714:
                    log(f"  {mf.name}[{sheet_name}]:")
                    for h in hits_f3b[:3]:
                        log(f"    BROCCOLIF3B: {h}")
                    for h in hits_714[:3]:
                        log(f"    BROCCOLI714: {h}")
            wb3.close()
        except Exception as e:
            log(f"  {mf.name}: ERROR {e}")
    elif mf.suffix == ".json":
        try:
            text = mf.read_text(encoding="utf-8", errors="replace")
            for t in TARGETS:
                if t.upper() in text.upper():
                    log(f"  {mf.name}: contains {t}")
        except Exception as e:
            log(f"  {mf.name}: ERROR {e}")

# ── 8. CASE_BROCCOLIF3B.xlsx (just built) ─────────────────────────────────
log("\n=== 8. CASE_BROCCOLIF3B.xlsx (sanity check sheets) ===")
case_path = ROOT / "docs" / "case_files" / "CASE_BROCCOLIF3B.xlsx"
if case_path.exists():
    try:
        wb4 = openpyxl.load_workbook(str(case_path), read_only=True)
        log(f"  Sheets: {wb4.sheetnames}")
        # Check CASE sheet
        cs = wb4["CASE"]
        for r in cs.iter_rows(values_only=True):
            if r[0]:
                log(f"  CASE: {r[0]}: {str(r[1])[:80] if r[1] else ''}")
        wb4.close()
    except Exception as e:
        log(f"  ERROR: {e}")
else:
    log(f"  CASE_BROCCOLIF3B.xlsx NOT FOUND")

# ── 9. Sổ chéo summary ────────────────────────────────────────────────────
log("\n=== CROSSREF SUMMARY ===")
log(f"  BROCCOLIF3B: target for this case")
log(f"  BROCCOLI714: disambiguation check — verify not mixed in ledger/events")
log(f"  Check: no BROCCOLI714 rows in CASE_BROCCOLIF3B or its data feed")
log(f"  Check: BROCCOLIF3B in agent_log (any prior GOM context?)")

log(f"\n[BR3-6 CROSSREF DONE]")

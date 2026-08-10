"""
_probe_koma_6_crossref_20260810.py
K-6: Sổ chéo — grep KOMA in ledger/u50/EVENTS/MM_BOOK/gom_scan/fresh-wallets
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-6 CROSSREF  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

TARGETS = ["KOMA"]

def grep_xlsx_for(path, targets):
    try:
        import openpyxl
        if not path.exists(): return {t: [] for t in targets}, f"NOT FOUND: {path}"
        wb = openpyxl.load_workbook(str(path), read_only=True)
        results = {t: [] for t in targets}
        for sn in wb.sheetnames:
            ws = wb[sn]
            for r in ws.iter_rows(values_only=True):
                row_str = " | ".join(str(c) for c in r if c is not None)
                for t in targets:
                    if t.upper() in row_str.upper():
                        results[t].append((sn, row_str[:160]))
        wb.close()
        return results, "OK"
    except Exception as e:
        return {t: [] for t in targets}, f"ERROR: {e}"

def grep_csv_for(path, targets):
    try:
        if not path.exists(): return {t: [] for t in targets}, f"NOT FOUND"
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        results = {t: [] for t in targets}
        for i, line in enumerate(lines):
            for t in targets:
                if t.upper() in line.upper():
                    results[t].append((i+1, line[:160]))
        return results, f"OK ({len(lines)} lines)"
    except Exception as e:
        return {t: [] for t in targets}, f"ERROR: {e}"

import openpyxl

# ── 1. agent_log.md ─────────────────────────────────────────────────────
log("\n=== 1. agent_log.md ===")
ag_path = ROOT / "agent_log.md"
res, st = grep_csv_for(ag_path, TARGETS)
log(f"  Status: {st}")
for t in TARGETS:
    hits = res[t]
    log(f"  {t}: {len(hits)} mentions")
    for ln, line in hits[:5]:
        log(f"    L{ln}: {line}")

# ── 2. CASE_INDEX.xlsx ───────────────────────────────────────────────────
log("\n=== 2. CASE_INDEX.xlsx ===")
idx_path = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
res2, st2 = grep_xlsx_for(idx_path, TARGETS)
log(f"  Status: {st2}")
for t in TARGETS:
    hits = res2[t]
    log(f"  {t}: {len(hits)} hits")
    for sn, row in hits[:5]:
        log(f"    [{sn}]: {row[:120]}")

# ── 3. ledger_v2.xlsx ────────────────────────────────────────────────────
log("\n=== 3. ledger_v2.xlsx ===")
ledger_cands = [ROOT/"docs"/"ledger_v2.xlsx", ROOT/"ledger_v2.xlsx", ROOT/"data"/"ledger_v2.xlsx"]
ledger_found = None
for p in ledger_cands:
    if p.exists(): ledger_found = p; break
if ledger_found:
    res3, st3 = grep_xlsx_for(ledger_found, TARGETS)
    log(f"  Status: {st3}")
    for t in TARGETS:
        log(f"  {t}: {len(res3[t])} hits")
        for sn, row in res3[t][:5]:
            log(f"    [{sn}]: {row[:120]}")
else:
    log(f"  ledger_v2.xlsx NOT FOUND in candidates: {[str(p) for p in ledger_cands]}")
    log(f"  Đã kiểm, không có")

# ── 4. EVENTS CSV ────────────────────────────────────────────────────────
log("\n=== 4. EVENTS CSV ===")
events_found = list(ROOT.glob("data/raw/events*.csv")) + list(ROOT.glob("data/events*.csv"))
if events_found:
    for ep in events_found[:3]:
        r4, s4 = grep_csv_for(ep, TARGETS)
        log(f"  {ep.name}: {s4}")
        for t in TARGETS:
            if r4[t]:
                log(f"    {t}: {len(r4[t])} hits")
                for ln, line in r4[t][:3]: log(f"      L{ln}: {line[:100]}")
else:
    log(f"  Đã kiểm, không có EVENTS CSV")

# ── 5. Freshwatch daily ──────────────────────────────────────────────────
log("\n=== 5. Freshwatch daily (KOMA rows) ===")
fw_cands = list(SCRATCH.glob("freshwatch_daily*.csv")) + \
           list((ROOT/"data"/"raw").glob("freshwatch_daily*.csv"))
fw_total = {}
for t in TARGETS: fw_total[t] = 0
for fp in sorted(fw_cands):
    r5, s5 = grep_csv_for(fp, TARGETS)
    for t in TARGETS:
        hits5 = r5[t]
        fw_total[t] += len(hits5)
        if hits5:
            log(f"  {fp.name}: {t} — {len(hits5)} rows")
            for ln, line in hits5[:2]: log(f"    L{ln}: {line[:120]}")
if not any(fw_total.values()):
    log(f"  Đã kiểm freshwatch: KOMA không có row")

# ── 6. gom_scan.py / gom_state ──────────────────────────────────────────
log("\n=== 6. GOM scripts ===")
gom_cands = list(ROOT.glob("gom_scan*.py")) + list(ROOT.glob("scripts/gom_scan*.py"))
signals_cands = list(ROOT.glob("scripts/signals.py"))
for gc in gom_cands + signals_cands:
    rg, sg = grep_csv_for(gc, TARGETS)
    log(f"  {gc.name}: {sg}")
    for t in TARGETS:
        if rg[t]:
            log(f"    {t}: {len(rg[t])} mentions")
            for ln, line in rg[t][:3]: log(f"      L{ln}: {line[:100]}")
if not gom_cands and not signals_cands:
    log(f"  Đã kiểm: gom_scan.py không tìm thấy")
# gom_state json
for gf in list(ROOT.glob("gom_state*.json")) + list(ROOT.glob("scratch/gom_state*.json")):
    try:
        text = gf.read_text(encoding="utf-8")
        for t in TARGETS:
            if t.upper() in text.upper():
                log(f"  {gf.name}: contains {t}")
    except: pass

# ── 7. MM_BOOK (CASE_INDEX sheet) + CASE files ──────────────────────────
log("\n=== 7. MM_BOOK / other CASE files ===")
for mf in (ROOT/"docs"/"case_files").glob("CASE_*.xlsx"):
    if "KOMA" in mf.name: continue  # skip self
    rm, sm = grep_xlsx_for(mf, TARGETS)
    for t in TARGETS:
        if rm[t]:
            log(f"  {mf.name}: {t} — {len(rm[t])} hits")
            for sn, row in rm[t][:3]: log(f"    [{sn}]: {row[:120]}")

# ── 8. alpha_id_map.json ────────────────────────────────────────────────
log("\n=== 8. alpha_id_map.json ===")
map_path = ROOT / "data" / "config" / "alpha_id_map.json"
if map_path.exists():
    amap = json.loads(map_path.read_text(encoding="utf-8"))
    koma_entries = {k:v for k,v in amap.items() if "KOMA" in k.upper()}
    log(f"  KOMA entries: {koma_entries}")
else:
    log(f"  alpha_id_map not found")

# ── Summary ──────────────────────────────────────────────────────────────
log("\n=== K-6 CROSSREF SUMMARY ===")
log(f"  KOMA in agent_log: {res[TARGETS[0]]} mention(s)")
log(f"  KOMA in CASE_INDEX: {len(res2[TARGETS[0]])} hits")
log(f"  ledger_v2: {'found' if ledger_found else 'NOT FOUND'}")
log(f"  KOMA in freshwatch total rows: {fw_total[TARGETS[0]]}")

log(f"\n[K-6 CROSSREF DONE]")

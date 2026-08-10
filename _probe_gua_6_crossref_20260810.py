"""
_probe_gua_6_crossref_20260810.py
G-6: Cross-ref GUA in ledger/u50/EVENTS/gom_scan/freshwatch/agent_log.
Tìm dấu vết GUA trong các file hiện có.
machine: local
date: 2026-08-10
"""
import sys, io, csv, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "GUAUSDT"; SYM_LOWER = "gua"; CONTRACT = "0xa5c8e1513b6a08334b479fe4d71f1253259469be"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-6 CROSSREF GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# ── 1. FreshWatch daily ───────────────────────────────────────────────────────
log(f"\n=== 1. FreshWatch daily rows (GUA) ===")
fw_rows = []
for fw in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == SYM:
                fw_rows.append(row)
log(f"  FW rows: {len(fw_rows)}")
if fw_rows:
    dates_fw = [r.get("date","")[:10] for r in fw_rows]
    log(f"  Range: {min(dates_fw)} → {max(dates_fw)}")
    log(f"  Last 5:")
    for r in fw_rows[-5:]:
        d = r.get("date","")[:10]
        glsr = r.get("lsr_global_r","N/A"); pos_r = r.get("lsr_pos_r","N/A")
        log(f"    {d}: gLSR={glsr} pos_r={pos_r}")

# ── 2. gom_state.json ─────────────────────────────────────────────────────────
log(f"\n=== 2. gom_state.json ===")
gom_state = ROOT / "data" / "gom_state.json"
gom_found = False
if gom_state.exists():
    with open(gom_state, encoding="utf-8") as f:
        gs = json.load(f)
    tokens = gs if isinstance(gs, dict) else {}
    if SYM in tokens or SYM_LOWER.upper() in str(tokens):
        log(f"  FOUND GUA in gom_state.json")
        if SYM in tokens:
            log(f"    entry: {json.dumps(tokens[SYM], ensure_ascii=False)[:200]}")
        gom_found = True
    else:
        log(f"  GUA not in gom_state.json ({len(tokens)} tokens)")
else:
    log(f"  gom_state.json not found at {gom_state}")

# ── 3. agent_log.md ───────────────────────────────────────────────────────────
log(f"\n=== 3. agent_log.md mentions ===")
agent_log = ROOT / "agent_log.md"
al_hits = []
if agent_log.exists():
    with open(agent_log, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "GUA" in line.upper() or "gua" in line.lower() or "SUPERFORTUNE" in line:
            al_hits.append((i+1, line.rstrip()))
    log(f"  Hits: {len(al_hits)}")
    for ln, txt in al_hits[-10:]:
        log(f"    L{ln}: {txt[:120]}")
else:
    log(f"  agent_log.md not found")

# ── 4. u50 CSV / FW universe ─────────────────────────────────────────────────
log(f"\n=== 4. u50 / universe lists ===")
u50_hits = []
for p in sorted(ROOT.rglob("u50*.csv")) + sorted(ROOT.rglob("freshwatch_symbols*")):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            content = f.read()
        if SYM in content or SYM_LOWER.upper() in content:
            u50_hits.append(p.name)
            log(f"  FOUND in {p.relative_to(ROOT)}")
    except: pass
if not u50_hits:
    log(f"  GUA not found in u50/universe files")

# ── 5. CASE_INDEX.xlsx ────────────────────────────────────────────────────────
log(f"\n=== 5. CASE_INDEX.xlsx check ===")
case_index = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
case_idx_found = False
if case_index.exists():
    try:
        import openpyxl
        wb = openpyxl.load_workbook(case_index, data_only=True)
        for sh_name in wb.sheetnames:
            sh = wb[sh_name]
            for row in sh.iter_rows(values_only=True):
                for cell in row:
                    if cell and "GUA" in str(cell).upper():
                        log(f"  FOUND in CASE_INDEX sheet '{sh_name}': {str(row)[:120]}")
                        case_idx_found = True
                        break
        if not case_idx_found:
            log(f"  GUA not in CASE_INDEX.xlsx")
    except Exception as e:
        log(f"  ERROR reading CASE_INDEX: {e}")
else:
    log(f"  CASE_INDEX.xlsx not found")

# ── 6. Alpha store check ──────────────────────────────────────────────────────
log(f"\n=== 6. Alpha store (data/raw/spot_klines_1d) ===")
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
alpha_cnt = 0
alpha_range = []
if alpha_store.exists():
    try:
        import pandas as pd
        for p in sorted(alpha_store.rglob("*.parquet")):
            try:
                df = pd.read_parquet(p)
                if "symbol" in df.columns:
                    mask = df["symbol"] == "GUA"
                    n = mask.sum()
                    if n > 0:
                        alpha_cnt += n
                        dates_a = df.loc[mask, "date"].tolist() if "date" in df.columns else []
                        alpha_range.extend(dates_a)
            except: pass
        if alpha_cnt:
            log(f"  GUA in alpha store: {alpha_cnt} rows")
            if alpha_range:
                log(f"  Date range: {min(alpha_range)} → {max(alpha_range)}")
        else:
            log(f"  GUA: 0 rows in alpha store")
    except Exception as e:
        log(f"  Alpha store check error: {e}")
else:
    log(f"  Alpha store not found: {alpha_store}")

# ── 7. Ledger / EVENTS files ──────────────────────────────────────────────────
log(f"\n=== 7. Ledger / MM_BOOK / gom_scan files ===")
ledger_hits = []
search_dirs = [ROOT/"docs", ROOT/"data"]
search_terms = ["GUA", "GUAUSDT", CONTRACT[:12], "SUPERFORTUNE"]
for d in search_dirs:
    if not d.exists(): continue
    for p in d.rglob("*.csv"):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                content = f.read(50000)  # first 50KB
            if any(t in content for t in search_terms):
                ledger_hits.append(p.relative_to(ROOT))
        except: pass
    for p in d.rglob("*.json"):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                content = f.read(50000)
            if any(t in content for t in search_terms):
                ledger_hits.append(p.relative_to(ROOT))
        except: pass

if ledger_hits:
    log(f"  FOUND in {len(ledger_hits)} files:")
    for p in ledger_hits:
        log(f"    {p}")
else:
    log(f"  GUA not found in docs/data ledger files")

# ── Summary ───────────────────────────────────────────────────────────────────
log(f"\n=== CROSSREF SUMMARY ===")
log(f"  FW daily rows: {len(fw_rows)} (range Jun1-Aug7)")
log(f"  gom_state: {'FOUND' if gom_found else 'NOT FOUND'}")
log(f"  agent_log hits: {len(al_hits)}")
log(f"  u50/universe: {'FOUND' if u50_hits else 'NOT FOUND'}")
log(f"  CASE_INDEX: {'REGISTERED' if case_idx_found else 'NOT YET (G-8 pending)'}")
log(f"  alpha store: {alpha_cnt} rows")
log(f"  ledger/docs: {len(ledger_hits)} file hits")

log(f"\n[G-6 DONE]")

"""_probe_lsr_merge_20260817.py
Forensic data extraction for LSR-merge report.
Reads backup files + current files + scratch CSVs.
Output: raw row data for docs/reports/_probe_lsr_merge_20260817.md
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES   = ROOT / "docs" / "case_files"

# ── helpers ───────────────────────────────────────────────────────────────────
def read_daily(xlsx_path):
    """Return (col_map, rows) from DAILY sheet. row2=fieldnames, data from row3+."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["DAILY"]
    rows = list(ws.iter_rows(values_only=True))
    # row index 0 = section titles, 1 = field names, 2+ = data
    if len(rows) < 3:
        return {}, []
    fields = [str(c).strip() if c else "" for c in rows[1]]
    col_map = {f: i for i, f in enumerate(fields) if f}
    data = []
    for r in rows[2:]:
        if not any(r):
            continue
        d = {fields[i]: r[i] for i in range(len(fields)) if i < len(r)}
        data.append(d)
    wb.close()
    return col_map, data

def show_lsr_rows(rows, col_map, filter_range, label):
    """Print 5 rows in date range showing LSR columns."""
    lsr_cols = ["pos_r", "acc_r", "gLSR", "taker_lsr", "lsr_pos_r", "lsr_acc_r",
                "lsr_global_r", "data_source_lsr", "_src", "date"]
    # find actual col names
    present = [c for c in lsr_cols if c in col_map]
    print(f"\n  {label}")
    print(f"  LSR cols found: {present}")
    lo, hi = filter_range
    hits = [r for r in rows if lo <= str(r.get("date","")) <= hi]
    # pick 5 spread across range
    if len(hits) > 5:
        step = max(1, len(hits)//5)
        hits = hits[::step][:5]
    for r in hits:
        vals = {c: r.get(c) for c in present}
        print(f"    {r.get('date','')} | {vals}")
    return hits

# ── §1 backup files ───────────────────────────────────────────────────────────
print("="*70)
print("§1 BACKUP FILES")
print("="*70)

GUA_BAK  = SCRATCH / "CASE_GUA_BACKUP_20260817_0315.xlsx"
APR_BAK1 = SCRATCH / "CASE_APR_bak_reg_20260810_034444.xlsx"
APR_BAK2 = SCRATCH / "CASE_APR_BACKUP_20260817_0315.xlsx"

for p in [GUA_BAK, APR_BAK1, APR_BAK2]:
    exists = p.exists()
    size   = p.stat().st_size if exists else 0
    print(f"  {p.name}: exists={exists}, size={size}")

# ── §2 counter-evidence from backups ─────────────────────────────────────────
print("\n" + "="*70)
print("§2 COUNTER-EVIDENCE FROM BACKUPS")
print("="*70)

# GUA backup — window 27/06→07/08
if GUA_BAK.exists():
    try:
        col_map, rows = read_daily(GUA_BAK)
        show_lsr_rows(rows, col_map, ("2026-06-27","2026-08-07"), f"GUA backup {GUA_BAK.name}")
    except Exception as e:
        print(f"  ERROR reading GUA backup: {e}")

# APR bak_0810 — window 01/06→07/08
if APR_BAK1.exists():
    try:
        col_map, rows = read_daily(APR_BAK1)
        show_lsr_rows(rows, col_map, ("2026-06-01","2026-08-07"), f"APR backup {APR_BAK1.name}")
    except Exception as e:
        print(f"  ERROR reading APR bak_0810: {e}")

# ── §3 current files — confirm null ──────────────────────────────────────────
print("\n" + "="*70)
print("§3 CURRENT FILES — DAILY LSR state")
print("="*70)

for sym, fname in [("GUA","CASE_GUA.xlsx"), ("APR","CASE_APR.xlsx")]:
    p = CASES / fname
    if not p.exists():
        print(f"  {fname}: NOT FOUND")
        continue
    try:
        col_map, rows = read_daily(p)
        print(f"\n  {fname}: {len(rows)} data rows, last={rows[-1].get('date','?') if rows else 'N/A'}")
        # count null LSR
        pos_col = "pos_r" if "pos_r" in col_map else ("lsr_pos_r" if "lsr_pos_r" in col_map else None)
        if pos_col:
            null_ct = sum(1 for r in rows if r.get(pos_col) is None or r.get(pos_col) == "")
            print(f"  {pos_col} null: {null_ct}/{len(rows)} ({null_ct/len(rows)*100:.1f}%)")
        lo = "2026-06-27" if sym == "GUA" else "2026-06-01"
        show_lsr_rows(rows, col_map, (lo,"2026-08-07"), f"  {sym} current, window")
    except Exception as e:
        print(f"  ERROR reading {fname}: {e}")

# ── §4 scratch LSR CSVs ───────────────────────────────────────────────────────
print("\n" + "="*70)
print("§4 SCRATCH LSR CSVs (gua + apr)")
print("="*70)

for pat in ["gua_lsr_raw_*.csv", "apr_lsr_raw_*.csv"]:
    for p in sorted(SCRATCH.glob(pat)):
        size = p.stat().st_size
        try:
            with open(p, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data_rows = list(reader)
            fields = reader.fieldnames or []
            dates  = [r.get("date","") for r in data_rows if r.get("date")]
            rng    = f"{dates[0]}→{dates[-1]}" if dates else "EMPTY"
            print(f"  {p.name} ({size}B): cols={fields}, rows={len(data_rows)}, range={rng}")
            if data_rows:
                print(f"    sample row 1: {data_rows[0]}")
        except Exception as e:
            print(f"  {p.name}: ERROR {e}")

# ── §5 build_case.py code path summary ───────────────────────────────────────
print("\n" + "="*70)
print("§5 BUILD_CASE.PY — KEY LINE RANGES")
print("="*70)
bc = ROOT / "build_case.py"
with open(bc, encoding="utf-8") as f:
    lines = f.readlines()

key_ranges = {
    "Load LSR CSV (lsr_rows)": (119, 125),
    "Build lsr_by_d from CSV (A-0a)": (141, 153),
    "Freshwatch extend loop (blocking guard)": (154, 171),
    "A-0b coverage guard": (857, 871),
}
for label, (lo, hi) in key_ranges.items():
    print(f"\n  [{label}] lines {lo}–{hi}:")
    for i, ln in enumerate(lines[lo-1:hi], start=lo):
        print(f"    {i:4d}  {ln}", end="")

print("\n\n[DONE]")

"""_task_r1_refresh_20260821.py — R1 refresh 4 file DAILY to D-1 (2026-08-20).
In-memory build → guard → write (L-61).
"""
import sys, io, pickle
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date as _date, timedelta
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES = ROOT / "docs" / "case_files"

with open(SCRATCH / "r_nhip1_fetch_20260821.pkl", "rb") as f:
    ALL = pickle.load(f)

END = "2026-08-20"

def safe_float(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None

# Column mapping per token (v1 vs v2)
COL_MAP_V1 = {
    "px_avg": ["px_avg"], "ret_1d": ["ret_1d"],
    "vol_perp": ["vol_perp_usd"], "taker_buy_pct": ["taker_buy_pct"],
    "f_avg": ["f_avg"], "f_min": ["f_min"], "f_max": ["f_max"], "f_n": ["f_n","fn (4h=6/day)"],
    "funding_regime": ["funding_regime"], "pin_streak": ["pin_streak"],
    "oi_usd": ["oi_usd"], "oi_vs_med14": ["oi_vs_med14"], "oi_cycle_pos": ["oi_cycle_pos"],
    "lsr_pos_r": ["lsr_pos_r","pos_r"], "lsr_acc_r": ["lsr_acc_r","acc_r"], "lsr_global_r": ["lsr_global_r","gLSR"],
}
COL_MAP_V2 = {
    "px_avg": ["px_avg (H+L+C)/3"], "o": ["o"], "h": ["h"], "l": ["l"], "c": ["c"],
    "ret_1d": ["ret_1d (close-to-close)"],
    "vol_perp": ["vol_perp_usd"], "taker_buy_pct": ["taker_buy_pct (k[10]/k[7])"],
    "f_avg": ["f_avg"], "f_min": ["f_min"], "f_max": ["f_max"], "f_n": ["fn (4h=6/day)"],
    "oi_usd": ["oi_usd"], "oi_token": ["oi_token"],
    "lsr_pos_r": ["pos_r"], "lsr_acc_r": ["acc_r"], "lsr_global_r": ["gLSR"],
    "taker_lsr": ["taker_lsr"],
    "data_source_lsr": ["data_source_lsr"],
}

def get_col(ci, cands):
    for c in cands:
        if c in ci: return ci[c]
    return None

def refresh_file(sym):
    fp = CASES / f"CASE_{sym}.xlsx"
    if not fp.exists():
        print(f"  {sym}: file missing"); return None
    d = ALL.get(sym)
    if not d:
        print(f"  {sym}: no fetch data"); return None

    wb = openpyxl.load_workbook(fp)
    ws = wb["DAILY"]
    row2 = [c.value for c in ws[2]]
    ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
    n_cols = len(row2)
    is_v2 = "c" in ci  # v2 has separate o/h/l/c cols; v1 only px_avg
    cmap = COL_MAP_V2 if is_v2 else COL_MAP_V1
    print(f"\n[{sym}] schema={'v2' if is_v2 else 'v1'} cols={n_cols}")

    # Read existing dates → row map
    existing = {}
    max_row_used = 2
    for r in range(3, ws.max_row + 1):
        dd = ws.cell(r, 1).value
        if dd:
            d_str = str(dd)[:10]
            existing[d_str] = r
            max_row_used = max(max_row_used, r)
    print(f"  existing rows: {len(existing)} · max row used: {max_row_used}")

    # Build all dates from fetch (union klines+funding+OI+LSR keys)
    all_new_dates = set(d["klines"].keys()) | set(d["fund_by_d"].keys()) | set(d["oi"].keys()) | set(d["lsr"].keys())
    # Add all dates within [existing_min, END] that we have data for
    all_dates = set(existing.keys()) | all_new_dates
    all_dates_sorted = sorted(all_dates)

    # Determine which dates need new row
    new_dates = [x for x in all_dates_sorted if x not in existing and x <= END]
    print(f"  new dates to append: {len(new_dates)}" +
          (f" ({new_dates[0]}..{new_dates[-1]})" if new_dates else ""))

    # Assign row numbers for new dates
    next_r = max_row_used + 1
    for d_str in new_dates:
        existing[d_str] = next_r
        next_r += 1

    # Fill data (both new + existing that are stale)
    writes = 0
    for d_str in sorted(existing.keys()):
        if d_str > END: continue
        r = existing[d_str]
        # Write date if new
        if ws.cell(r, 1).value is None:
            ws.cell(r, 1).value = d_str
            writes += 1
        klines = d["klines"].get(d_str)
        oi_data = d["oi"].get(d_str)
        lsr_data = d["lsr"].get(d_str)
        frs = d["fund_by_d"].get(d_str, [])

        def write_cell(field_key, value):
            nonlocal writes
            cix = get_col(ci, cmap.get(field_key, []))
            if cix and value is not None:
                cur = ws.cell(r, cix).value
                if cur != value:
                    ws.cell(r, cix).value = value
                    writes += 1

        if klines:
            if is_v2:
                write_cell("px_avg", round((klines["h"]+klines["l"]+klines["c"])/3, 8))
                write_cell("o", klines["o"]); write_cell("h", klines["h"])
                write_cell("l", klines["l"]); write_cell("c", klines["c"])
            else:
                # v1: only px_avg (approx close)
                write_cell("px_avg", klines["c"])
            write_cell("vol_perp", klines["vol_quote_usd"])
            write_cell("taker_buy_pct", klines["taker_buy_pct"])

        if frs:
            f_avg = round(sum(frs)/len(frs), 8)
            write_cell("f_avg", f_avg)
            write_cell("f_min", min(frs))
            write_cell("f_max", max(frs))
            write_cell("f_n", len(frs))

        if oi_data:
            write_cell("oi_usd", oi_data["oi_usd"])
            if is_v2:
                write_cell("oi_token", oi_data["oi_token"])

        if lsr_data:
            write_cell("lsr_pos_r", lsr_data.get("pos_r"))
            write_cell("lsr_acc_r", lsr_data.get("acc_r"))
            write_cell("lsr_global_r", lsr_data.get("gLSR"))
            if is_v2:
                write_cell("taker_lsr", lsr_data.get("taker_lsr"))
                write_cell("data_source_lsr", lsr_data.get("src", ""))

    print(f"  cells written: {writes}")

    # Guard: pos_r null in coverage window (freshwatch first_seen → END)
    fw_first = min(d["lsr"].keys()) if d["lsr"] else None
    if fw_first:
        pos_col = get_col(ci, cmap["lsr_pos_r"])
        total = 0; nulls = 0
        for d_str, r in existing.items():
            if d_str < fw_first or d_str > END: continue
            total += 1
            if safe_float(ws.cell(r, pos_col).value) is None:
                nulls += 1
        pct = nulls/total*100 if total else 0
        print(f"  Guard pos_r null in [{fw_first}..{END}]: {nulls}/{total} = {pct:.1f}%")
        if pct > 50:
            print(f"  ⚠ GUARD FAIL (>50%) — DỪNG file này, không save")
            return None

    wb.save(fp)
    print(f"  SAVED: {fp}")

    return {"writes": writes, "existing_count": len(existing)}

# ── RUN R1 ──
print("="*70)
print("R1 REFRESH — write 4 file to D-1 (post-guard)")
print("="*70)

results = {}
for sym in ["BANK","TUT","BTW","CYS"]:
    results[sym] = refresh_file(sym)

# Summary
print("\n" + "="*70)
print("SUMMARY R1 write")
print("="*70)
for sym, r in results.items():
    if r is None:
        print(f"  {sym}: FAIL / SKIP")
    else:
        print(f"  {sym}: {r['writes']} cell writes · {r['existing_count']} dates total")

print("\n[DONE R1]")

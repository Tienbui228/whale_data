"""_task_unhedge_registry_calib_20260820.py
Calibration test: add struct_n ≥ 3 filter (real episode requirement).
Re-run E-R7 gates + report.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")
IN_CSV = ROOT / "data" / "registry" / "unhedge_registry_backfill_20260820.csv"
OUT_CSV = ROOT / "data" / "registry" / "unhedge_registry_calib_struct3_20260820.csv"

# Load original
all_entries = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
print(f"Original: {len(all_entries)} entries")

# Apply struct_n ≥ 3 filter
def calib(row):
    return int(row["struct_n"]) >= 3

filtered = [r for r in all_entries if calib(r)]
print(f"After struct_n ≥ 3: {len(filtered)} entries "
      f"({len(filtered)/len(all_entries)*100:.1f}% retained)")

n_break = sum(1 for r in filtered if r["trigger"] == "a")
n_drift = sum(1 for r in filtered if r["trigger"] == "b")
n_ignited = sum(1 for r in filtered if r.get("ignite_date"))
print(f"  break: {n_break} · drift: {n_drift}")
print(f"  ignited within 90d: {n_ignited} ({n_ignited/len(filtered)*100:.1f}%)")

unique_tokens = set(r["symbol"] for r in filtered)
universe_size = 527
pct = len(unique_tokens)/universe_size*100
print(f"\n  Unique tokens: {len(unique_tokens)}/{universe_size} = {pct:.1f}%")
print(f"  Gate (iv) with struct_n≥3: {'PASS' if pct <= 25 else 'FAIL'}")

# Try stricter: struct_n ≥ 5
filtered_5 = [r for r in all_entries if int(r["struct_n"]) >= 5]
unique_5 = set(r["symbol"] for r in filtered_5)
pct_5 = len(unique_5)/universe_size*100
n_ig5 = sum(1 for r in filtered_5 if r.get("ignite_date"))
print(f"\n  With struct_n ≥ 5: {len(filtered_5)} entries · {len(unique_5)}/{universe_size}={pct_5:.1f}% · ignited={n_ig5} ({n_ig5/len(filtered_5)*100:.1f}%)")

# Try struct_n ≥ 3 AND px_dist_pct >= -5% (loại các case đã sập)
filtered_pxguard = []
for r in filtered:
    try:
        px_d = float(r.get("px_dist_pct") or 0)
        if px_d >= -5:  # px giữ trong 5% dưới hedge_start
            filtered_pxguard.append(r)
    except: pass
unique_pxg = set(r["symbol"] for r in filtered_pxguard)
pct_pxg = len(unique_pxg)/universe_size*100
n_ig_pxg = sum(1 for r in filtered_pxguard if r.get("ignite_date"))
print(f"\n  With struct_n≥3 AND px_dist≥-5%: {len(filtered_pxguard)} entries · {len(unique_pxg)}/{universe_size}={pct_pxg:.1f}% · ignited={n_ig_pxg} ({n_ig_pxg/len(filtered_pxguard)*100:.1f}%)")

# Save struct_n≥3 filtered
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    if filtered:
        fields = list(filtered[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in filtered: w.writerow(r)
print(f"\nWritten: {OUT_CSV}")

# Gate check on calibrated
print("\n" + "="*70)
print("GATE CHECKS (struct_n ≥ 3 calibration)")
print("="*70)

for target_sym, expected_note in [
    ("HEMIUSDT", "Jul09-12 registry · ignite ideal Aug15 (machine may catch earlier Jul20 spike)"),
    ("ONUSDT",   "Jul17 registry · ignite T+1"),
    ("TRIAUSDT", "Aug NOT in registry (still hedged)"),
    ("STBLUSDT", "Aug NOT in registry (still hedged)"),
]:
    entries = [r for r in filtered if r["symbol"] == target_sym]
    print(f"\n{target_sym} ({expected_note}):")
    if not entries:
        print(f"  0 entries")
    for e in entries:
        print(f"  unhedge={e['unhedge_date']} trg={e['trigger']} struct_n={e['struct_n']} "
              f"div_min={e['div_min']} px_dist={e['px_dist_pct']}% "
              f"ignite={e.get('ignite_date') or 'none'} d2i={e.get('days_to_ignite') or '-'} "
              f"reason={e.get('ignite_reason') or '-'}")

# Top ignited entries hit-rate
print("\n" + "="*70)
print("HIT-RATE ANALYSIS")
print("="*70)
# Split by trigger
for trg in ["a", "b"]:
    subset = [r for r in filtered if r["trigger"] == trg]
    if not subset: continue
    ig_days = [int(r["days_to_ignite"]) for r in subset if r.get("days_to_ignite")]
    print(f"\nTrigger '{trg}' ({len(subset)} entries):")
    print(f"  ignited: {len(ig_days)}/{len(subset)} = {len(ig_days)/len(subset)*100:.1f}%")
    if ig_days:
        print(f"  days_to_ignite: min={min(ig_days)} · median={sorted(ig_days)[len(ig_days)//2]} · "
              f"max={max(ig_days)}")

print("\n[DONE calib]")

"""R3 analysis: TST GOM screen status across all DAILY history."""
import openpyxl
from pathlib import Path
import sys

path = Path("docs/case_files/CASE_TST.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
ws = wb["DAILY"]
rows = list(ws.iter_rows(values_only=True))
wb.close()

# col indices from probe: date=0, taker_buy_pct=7, oi_usd=12, ret_1d=16
# pos_r=26, acc_r=27, gLSR=28, taker_lsr=29
# vol_alpha=34, taker_alpha=35, on_chain_source=36
# gom_A_screen=37, gom_B_screen=38, gom_note=39
# oi_cycle_pos=42

data = rows[2:]  # skip 2 header rows

total = 0
gom_a_true = 0
gom_b_true = 0
alpha_abstain = 0
onchain_abstain = 0
both_abstain = 0  # alpha AND onchain both ABSTAIN

pos_r_days = []  # days where pos_r is not None
lsr_days = []

for r in data:
    if not r[0]:
        continue
    total += 1
    date = r[0]
    alpha_v = str(r[34]).upper() if r[34] is not None else ""
    onchain_v = str(r[36]).upper() if r[36] is not None else ""
    gom_a = str(r[37]).upper() if r[37] is not None else ""
    gom_b = str(r[38]).upper() if r[38] is not None else ""

    is_alpha_abstain = "ABSTAIN" in alpha_v or "BANNED" in alpha_v
    is_onchain_abstain = "ABSTAIN" in onchain_v or "LOCK" in onchain_v

    if is_alpha_abstain:
        alpha_abstain += 1
    if is_onchain_abstain:
        onchain_abstain += 1
    if is_alpha_abstain and is_onchain_abstain:
        both_abstain += 1
    if gom_a == "TRUE":
        gom_a_true += 1
    if gom_b == "TRUE":
        gom_b_true += 1

    pos_r = r[26]
    lsr = r[28]
    if pos_r is not None:
        pos_r_days.append((date, pos_r))
    if lsr is not None:
        lsr_days.append((date, lsr))

print(f"=== TST GOM Analysis ===")
print(f"Total DAILY rows: {total}")
print(f"Date range: {data[0][0] if data else 'N/A'} to {[r[0] for r in data if r[0]][-1]}")
print()
print(f"GOM-A fire (TRUE):   {gom_a_true} / {total} days")
print(f"GOM-B fire (TRUE):   {gom_b_true} / {total} days")
print(f"Alpha ABSTAIN:       {alpha_abstain} / {total} days ({100*alpha_abstain/total:.1f}%)")
print(f"On-chain ABSTAIN:    {onchain_abstain} / {total} days ({100*onchain_abstain/total:.1f}%)")
print(f"Both ABSTAIN:        {both_abstain} / {total} days ({100*both_abstain/total:.1f}%)")
print()
print(f"pos_r populated:     {len(pos_r_days)} days")
print(f"gLSR populated:      {len(lsr_days)} days")
print()
print("Last 5 pos_r values:")
for d, v in pos_r_days[-5:]:
    print(f"  {d}: pos_r={v:.4f}")
print()
print("Last 5 gLSR values:")
for d, v in lsr_days[-5:]:
    print(f"  {d}: gLSR={v:.4f}")

# Show GOM-A fire days if any
if gom_a_true > 0:
    print()
    print("GOM-A fire days:")
    for r in data:
        if r[0] and str(r[37]).upper() == "TRUE":
            print(f"  {r[0]}: pos_r={r[26]}, gLSR={r[28]}, ret={r[16]}, oi_usd={r[12]}")

# Check freshwatch output
import csv
from pathlib import Path as P
fw_path = P("data/freshwatch_daily_2026-08.csv")
if fw_path.exists():
    with open(fw_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tst_rows = [row for row in reader if row.get("symbol") == "TSTUSDT"]
    if tst_rows:
        last = tst_rows[-1]
        print()
        print(f"Freshwatch latest TST ({last.get('date')}):")
        for k in ["symbol","date","pos_r","acc_r","lsr_pos_r","oi_usd","px_close","gom_a_fire","gom_b_fire"]:
            print(f"  {k}: {last.get(k,'N/A')}")

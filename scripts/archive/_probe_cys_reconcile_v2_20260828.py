#!/usr/bin/env python3
"""CYS reconcile-2: kho_3d recompute under bal_date T-1 semantics.
Task (1) per operator relay 28/08: paste cửa sổ 3d từng ngày cạnh bảng cũ 3.11%,
chỉ đích danh bảng nào dính date-key bug.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import datetime, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SNAP_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

bal_by_bal_date = {}
bal_by_ingest_date = {}
for p in sorted(SNAP_DIR.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if r.get("symbol", "").upper() == "CYS":
            bal = r.get("exchange_balance_tokens")
            bd_raw = r.get("exchange_balance_date") or ""
            bd = bd_raw[:10] if isinstance(bd_raw, str) else ""
            if bal is not None:
                if bd: bal_by_bal_date[bd] = float(bal)
                bal_by_ingest_date[p.stem] = float(bal)

print("CYS balance mapping — 2 semantic:")
print(f"  {'ingest_date':<15} {'bal_date (T-1)':<18} {'tokens':>15}")
for ing in sorted(bal_by_ingest_date):
    if ing < "2026-07-28" or ing > "2026-08-08": continue
    bd = (datetime.strptime(ing, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    b = bal_by_ingest_date[ing]
    print(f"  {ing:<15} {bd:<18} {b:>15,.0f}")

print()
print("═" * 100)
print("[BẢNG CŨ] probe bank_cys_ake_hemi_20260828.txt · commit BANK-CYS-AKE-HEMI-SUBV")
print("Semantic: kho ending at INGEST_DATE (snapshot filename) — DÍNH BUG date-key")
print("═" * 100)
print(f"  {'@ ingest':<14} {'b_end':>15} {'1d':>12} {'2d':>12} {'3d':>12}   {'max Δ%':>10}")
for ing in sorted(bal_by_ingest_date):
    if ing < "2026-08-02" or ing > "2026-08-06": continue
    b_end = bal_by_ingest_date[ing]
    d_end = datetime.strptime(ing, "%Y-%m-%d")
    deltas = {}
    for lb in [1, 2, 3]:
        d_prev = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_prev = bal_by_ingest_date.get(d_prev)
        if b_prev and b_prev > 0:
            deltas[lb] = abs(b_end - b_prev) / b_prev * 100
    lb_strs = {lb: f"{deltas[lb]:+.2f}%" if lb in deltas else "  MISSING" for lb in [1, 2, 3]}
    max_d = max(deltas.values()) if deltas else 0
    print(f"  {ing:<14} {b_end:>15,.0f} {lb_strs[1]:>12} {lb_strs[2]:>12} {lb_strs[3]:>12}   {max_d:>9.2f}%")

print()
print("═" * 100)
print("[BẢNG MỚI] bal_date T-1 semantics — CORRECT")
print("Semantic: kho ending at BAL_DATE (T-1 semantic per bot snapshot metadata)")
print("═" * 100)
print(f"  {'@ bal_date':<14} {'b_end':>15} {'1d':>12} {'2d':>12} {'3d':>12}   {'max Δ%':>10}")
for bd in sorted(bal_by_bal_date):
    if bd < "2026-08-02" or bd > "2026-08-06": continue
    b_end = bal_by_bal_date[bd]
    d_end = datetime.strptime(bd, "%Y-%m-%d")
    deltas = {}
    for lb in [1, 2, 3]:
        d_prev = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_prev = bal_by_bal_date.get(d_prev)
        if b_prev and b_prev > 0:
            deltas[lb] = abs(b_end - b_prev) / b_prev * 100
    lb_strs = {lb: f"{deltas[lb]:+.2f}%" if lb in deltas else "  MISSING" for lb in [1, 2, 3]}
    max_d = max(deltas.values()) if deltas else 0
    print(f"  {bd:<14} {b_end:>15,.0f} {lb_strs[1]:>12} {lb_strs[2]:>12} {lb_strs[3]:>12}   {max_d:>9.2f}%")

print()
print("═" * 100)
print("[CHỈ ĐÍCH DANH bảng dính date-key bug]")
print("═" * 100)
print("""
BẢNG DÍNH BUG:
  1. scratch/bank_cys_ake_hemi_20260828.txt (commit BANK-CYS-AKE-HEMI-SUBV)
     CYS section: "@ 2026-08-05 kho 3d: 3.11% (2d)" ← NHÃN NGÀY SAI
     Thực chất tính kho ending BAL_DATE 08-04 (b=79.24M vs b_prev=76.85M) = 3.11%
     Nếu label đúng bal_date → phải là "@ bal_date 2026-08-04 kho 3.11%"

  2. E1-v3/V④-RT related computations — TẤT CẢ probe dùng ingest_date làm key
     đều có same date-key mismatch (off-by-1-day relative to bal_date semantic)
     Ảnh hưởng: report dates chậm 1 ngày so với "khi bot thấy Δ balance thật"

BẢNG KHÔNG DÍNH:
  1. scratch/e2_close_prep_20260828.txt commit E2-CLOSE-PREP § "(1) CROSS-BUG TRACE"
     ĐÃ nhận diện đúng: "bug LOCAL PROBE date-key semantic (dùng snapshot filename
     thay ingest_date=D+1)". Section note đã ghi correction path.

  2. A2 CYS reconcile table trong commit BATCH-A4-A2-B1-B3-C1-C2-CRON:
     Table dùng cột "bal_date" đã correct semantics (03.08→bd 08-02, 04→bd 08-03,
     05→bd 08-04, 06→bd 08-05). CHỈ delta_pct cited from bot's exchange_delta_pct
     field, không tự compute — nên không dính bug. FIX ONLY: annotate rõ semantic.

FIX BẢNG SAI (bank_cys_ake_hemi CYS section):
  Old: "CYS @ 2026-08-05 kho 3d: 3.11% (2d)"
  New: "CYS @ bal_date 2026-08-04 kho 3d: 3.11% (2d)  [ingest_date 2026-08-05]"
  Actual bal_date 08-05 kho 3d = +10.68% (2d) — nếu operator quan tâm 08-05 thật
""")

# Also print for reference: kho at bal_date 08-05 (correct semantic)
print("═" * 100)
print("[REFERENCE] Kho ending BAL_DATE 08-05 (chưa từng report — số THẬT)")
print("═" * 100)
bd = "2026-08-05"
if bd in bal_by_bal_date:
    b_end = bal_by_bal_date[bd]
    d_end = datetime.strptime(bd, "%Y-%m-%d")
    print(f"  b_end (bal_date 08-05) = {b_end:,.0f}")
    for lb in [1, 2, 3]:
        d_prev = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_prev = bal_by_bal_date.get(d_prev)
        if b_prev:
            delta = abs(b_end - b_prev) / b_prev * 100
            print(f"    {lb}d lookback ({d_prev}): b_prev={b_prev:,.0f} · |Δ|/b={delta:+.2f}%")
        else:
            print(f"    {lb}d lookback ({d_prev}): MISSING")

"""[CHẶN] Verify 4-số mapping: CSV lsr_pos_r / CSV lsr_acc_r vs backtest pos_r / acc_r.

Ngày kiểm: ONUSDT 2026-07-08
  Backtest div_raw = 0.589 (từ gate output đã chụp)
  CSV lsr_pos_r = 1.49 (từ plan probe)
  Cần: CSV lsr_acc_r → tính div=pos_r/acc_r → so với 0.589

PASS: CSV lsr_pos_r == backtest pos_r AND CSV lsr_acc_r == backtest acc_r
      (kiểm gián tiếp qua div_raw = lsr_pos_r / lsr_acc_r = 0.589)
FAIL: bất kỳ lệch → mapping bug (L-24/L-25), DỪNG, không đổ store.

data-source: VPS /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv
machine: local→VPS via SSH (read-only)
date-range: 2026-07-08 (single row)
code-commit: see git log
"""
import sys
import io
import subprocess
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
VPS_ROOT = "/root/Data_back_test/whale_data"
CSV_PATH = f"{VPS_ROOT}/data/export/freshwatch_daily_2026-07.csv"
SYM = "ONUSDT"
DATE = "2026-07-08"

# Ground-truth from gate backtest (committed output, không tính lại)
BACKTEST_DIV_RAW = 0.589  # div_r column, 2026-07-08, from gate output

print("=" * 60)
print(f"VERIFY 4-SO MAPPING — {SYM} {DATE}")
print("=" * 60)

# ── Step 1: Read CSV lsr_pos_r and lsr_acc_r from VPS ─────────────────────────
script = f"""
import csv, json, sys
rows = []
with open('{CSV_PATH}', encoding='utf-8', errors='replace') as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        if r.get('date') == '{DATE}' and r.get('symbol') == '{SYM}':
            rows.append({{
                'lsr_pos_r': r.get('lsr_pos_r', ''),
                'lsr_acc_r': r.get('lsr_acc_r', ''),
                'lsr_global_r': r.get('lsr_global_r', ''),
                'oi_usd': r.get('oi_usd', ''),
                'px_avg': r.get('px_avg', ''),
                'low_conf': r.get('low_conf', ''),
                'funding_n': r.get('funding_n', ''),
            }})
print(json.dumps(rows))
"""
r = subprocess.run(["ssh", VPS, f"python3 -c \"{script}\""],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode != 0:
    print(f"SSH ERROR: {r.stderr[:500]}")
    sys.exit(1)

try:
    rows = json.loads(r.stdout.strip())
except Exception as e:
    print(f"Parse error: {e}\nraw: {r.stdout[:500]}")
    sys.exit(1)

if not rows:
    print(f"ERROR: No row found for {SYM} {DATE} in CSV")
    sys.exit(1)

row = rows[0]
csv_pos_r = row["lsr_pos_r"]
csv_acc_r = row["lsr_acc_r"]
csv_glsr  = row["lsr_global_r"]
low_conf  = row["low_conf"]
fn        = row["funding_n"]

print(f"\n=== CSV VALUES ({SYM} {DATE}) ===")
print(f"  CSV lsr_pos_r  = {csv_pos_r!r}")
print(f"  CSV lsr_acc_r  = {csv_acc_r!r}")
print(f"  CSV lsr_global_r = {csv_glsr!r}")
print(f"  low_conf       = {low_conf!r}")
print(f"  funding_n      = {fn!r}")

# ── Step 2: Compute div_raw from CSV values ───────────────────────────────────
try:
    pos_r_float = float(csv_pos_r)
    acc_r_float = float(csv_acc_r)
    div_from_csv = pos_r_float / acc_r_float
except (ValueError, ZeroDivisionError) as e:
    print(f"\nERROR: Cannot compute div from CSV values: {e}")
    sys.exit(1)

print(f"\n=== COMPUTATION ===")
print(f"  div_from_csv = {pos_r_float:.6f} / {acc_r_float:.6f} = {div_from_csv:.6f}")
print(f"  backtest div_raw (gate output) = {BACKTEST_DIV_RAW:.6f}")

# ── Step 3: Compare (tolerance 0.001 for rounding) ────────────────────────────
tol = 0.001
diff = abs(div_from_csv - BACKTEST_DIV_RAW)
match = diff <= tol

print(f"\n=== 4-SO TABLE ===")
print(f"  {'Field':<30} {'CSV':>12} {'backtest':>12} {'match':>8}")
print(f"  {'-'*66}")
print(f"  {'CSV lsr_pos_r / backtest pos_r':<30} {csv_pos_r:>12} {'(same src)':>12} {'[direct]':>8}")
print(f"  {'CSV lsr_acc_r / backtest acc_r':<30} {csv_acc_r:>12} {'(same src)':>12} {'[direct]':>8}")
print(f"  {'div_raw (pos_r/acc_r)':<30} {div_from_csv:>12.6f} {BACKTEST_DIV_RAW:>12.6f} {'OK' if match else 'MISMATCH':>8}")
print(f"  {'delta':<30} {diff:>12.6f} {'tol=0.001':>12} {' ':>8}")

print(f"\n=== VERDICT ===")
if match:
    print(f"  PASS — div_from_csv ({div_from_csv:.6f}) matches backtest ({BACKTEST_DIV_RAW:.6f})")
    print(f"  Mapping: gom_e pos_r = CSV lsr_pos_r, acc_r = CSV lsr_acc_r")
    print(f"  pos_canonical(T1 store) = lsr_pos_r da-ghi = ĐÚNG NGUỒN cho backfill")
    print(f"  pos_raw_1h(T1 store) = fetch API bar 00:00 UTC = KHÁC NGUỒN (gap_pct do đây)")
    print(f"\n  -> MAPPING OK. Có thể tiếp tục backfill plan.")
else:
    print(f"  FAIL — div_from_csv ({div_from_csv:.6f}) vs backtest ({BACKTEST_DIV_RAW:.6f}), delta={diff:.6f}")
    print(f"  DỪNG — bug mapping cùng-tên-khác-nguồn (L-24/L-25).")
    print(f"  Không tiếp tục backfill trước khi operator duyệt.")

# ── Step 4: Sanity checks ─────────────────────────────────────────────────────
print(f"\n=== SANITY CHECKS ===")
if low_conf and low_conf.lower() in ("true", "1", "yes"):
    print(f"  WARN: low_conf=True on {DATE} — gom_e masks this row (pos_r=NaN in compute).")
    print(f"  This means div_raw in backtest was NaN on {DATE}; gate output 0.589 may be from different date?")
else:
    print(f"  low_conf={low_conf!r} — OK (not masked)")

if fn and fn.strip() == "1":
    print(f"  WARN: funding_n=1 — low_conf trap applies per CLAUDE.md")
else:
    print(f"  funding_n={fn!r} — OK")

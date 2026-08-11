"""COMMIT GATE — ON 17-18/07: run GOM-E T1 backtest trên VPS data, verify fire.

GATE CONDITION (spec §3):
  ONUSDT phải fire đúng cửa sổ 2026-07-17 hoặc 2026-07-18 với tag [NUM-DRIVEN].
  Ground truth: pos +30%/1d, oi_token ↓2 ngày, pin-47d vỡ cùng ngày → E1✓E2✓E3✓E4✓

CHƯA XANH CHƯA COMMIT.

data-source: VPS /root/Data_back_test/whale_data/data/export/ (canonical)
machine: VPS 5.223.67.21 (gate chạy trên VPS data canonical)
date-range: 2026-06-15 → 2026-07-25
code-commit: see git log
"""
import sys
import io
import subprocess
import textwrap
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS       = "root@5.223.67.21"
VPS_ROOT  = "/root/Data_back_test/whale_data"
LOCAL_ROOT = Path(__file__).resolve().parent

# Files to SCP to VPS (new scripts not yet committed/pushed)
SCP_FILES = [
    (LOCAL_ROOT / "scripts" / "gom_e.py",           f"{VPS_ROOT}/scripts/gom_e.py"),
    (LOCAL_ROOT / "scripts" / "fw_loader_utils.py", f"{VPS_ROOT}/scripts/fw_loader_utils.py"),
]

DATE_FROM = "2026-06-15"
DATE_TO   = "2026-07-25"
GATE_DATES = {"2026-07-17", "2026-07-18"}
SYM       = "ONUSDT"


def run(cmd: list, label: str) -> tuple[int, str, str]:
    print(f"\n>>> {label}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip():
        print(r.stdout[:8000])
    if r.stderr.strip():
        print(f"[STDERR] {r.stderr[:2000]}")
    return r.returncode, r.stdout, r.stderr


print("=" * 70)
print(f"GOM-E COMMIT GATE — ONUSDT 17-18/07 backtest — 2026-08-12")
print("=" * 70)

# ── STEP 1: SCP scripts to VPS ────────────────────────────────────────────────
print("\n=== STEP 1: SCP scripts to VPS ===")
for local_path, remote_path in SCP_FILES:
    if not local_path.exists():
        print(f"  ERROR: {local_path} not found — abort")
        sys.exit(1)
    rc, _, err = run(
        ["scp", str(local_path), f"{VPS}:{remote_path}"],
        f"scp {local_path.name} → VPS"
    )
    if rc != 0:
        print(f"  SCP FAILED rc={rc}: {err[:500]}")
        sys.exit(1)
    print(f"  OK: {local_path.name}")

# ── STEP 2: Verify VPS Python env ─────────────────────────────────────────────
print("\n=== STEP 2: VPS python env check ===")
rc, out, err = run(
    ["ssh", VPS, f"cd {VPS_ROOT} && python3 -c \"import pandas, requests; print('deps OK')\""],
    "check pandas+requests"
)
if rc != 0 or "deps OK" not in out:
    print(f"  WARN: deps check failed — may still work if env OK")

# ── STEP 3: Run backtest on VPS ───────────────────────────────────────────────
print("\n=== STEP 3: GOM-E backtest ONUSDT on VPS ===")
bt_cmd = (
    f"cd {VPS_ROOT} && "
    f"python3 scripts/gom_e.py "
    f"--backtest {SYM} "
    f"--store data/export "
    f"--date-from {DATE_FROM} "
    f"--date-to {DATE_TO} "
    f"--no-store"
)
rc, out, err = run(["ssh", VPS, bt_cmd], "backtest ONUSDT")
if rc != 0:
    print(f"\n  BACKTEST ERROR rc={rc}")
    print(f"  stderr: {err[:1000]}")
    sys.exit(1)

# ── STEP 4: Parse output for gate verdict ─────────────────────────────────────
print("\n=== STEP 4: GATE VERDICT PARSE ===")
lines = out.split("\n")

fire_in_gate   = False
fire_dates     = []
has_num_driven = False
gate_rows      = []

for line in lines:
    # Look for date rows in the table
    # Format: "  2026-07-17 | Y/N | div_r | ... | *** FIRE *** ◀ GATE CHECK"
    stripped = line.strip()
    date_hit = None
    for gd in GATE_DATES:
        if stripped.startswith(gd):
            date_hit = gd
            break

    if date_hit:
        gate_rows.append(stripped)
        if "FIRE" in line:
            fire_in_gate = True
            fire_dates.append(date_hit)
            if "NUM-DRIVEN" in line:
                has_num_driven = True

    # Also check any fire outside gate window for completeness
    if "*** FIRE ***" in line and not any(gd in line for gd in GATE_DATES):
        gate_rows.append(f"[OUT-OF-GATE] {stripped}")

print("\n  Gate window rows (2026-07-17 and 2026-07-18):")
if gate_rows:
    for r in gate_rows:
        print(f"    {r}")
else:
    print("    (no rows found for gate dates — data may not reach those dates)")

# ── STEP 5: Final verdict ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("GATE VERDICT:")

conds = [
    ("fire in gate window",  fire_in_gate),
    ("[NUM-DRIVEN] tag",     has_num_driven),
]

all_pass = all(v for _, v in conds)
for label, passed in conds:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}  {label}")

if fire_dates:
    print(f"  Fire dates: {fire_dates}")

if all_pass:
    print("\n  ✅ GATE GREEN — commit ở bước tiếp theo.")
else:
    print("\n  ❌ GATE RED — DỪNG. Paste output + báo operator. KHÔNG tự sửa spec đã freeze.")
    print("  Gợi ý debug:")
    if not fire_in_gate:
        print("    → Kiểm tra H1/H2 entry date; ON có vào registry trước 17/07?")
        print("    → Kiểm tra E1 (min5d) và E2 (d_pos_2d) thoả trên ngày nào?")
    if fire_in_gate and not has_num_driven:
        print("    → Fire xảy ra nhưng tag KHÔNG phải NUM-DRIVEN")
        print("    → Kiểm tra d_oitok_2d: phải ≤0 (OI giảm 2 ngày)")

print("=" * 70)

"""Q1 — Option 2: Run T1 --dry-run --daily trên VPS để đọc registry thật.

Xác nhận trước khi chạy:
  --dry-run = skip ALL writes: state.json + T1-STORE + log. Read-only hoàn toàn.
  Cố định: gom_e.py line 638 wrapped `if not dry_run: _save_state(state)`
           T1-STORE skip: `if do_t1_store and capture_set and not dry_run`
  TG-alert: run_gom_daily.py KHÔNG được gọi — gom_e.py chỉ print stdout.

Kỳ vọng output: Bảng A (registry) với AGT + vài con theo calib §3.
DỪNG sau khi paste bảng — chờ operator duyệt trước backfill.

data-source: VPS /root/Data_back_test/whale_data/data/export/ (canonical)
machine: VPS 5.223.67.21
date-range: 2026-08-10 (EVAL = D_run-1 = hôm qua)
code-commit: see git log
"""
import sys
import io
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
VPS_ROOT = "/root/Data_back_test/whale_data"
LOCAL_SCRIPTS = Path(__file__).resolve().parent / "scripts"

# ── Step 1: SCP updated gom_e.py (dry-run fix) to VPS ────────────────────────
print("=== STEP 1: SCP updated gom_e.py to VPS ===")
r_scp = subprocess.run(
    ["scp", str(LOCAL_SCRIPTS / "gom_e.py"), f"{VPS}:{VPS_ROOT}/scripts/gom_e.py"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if r_scp.returncode != 0:
    print(f"SCP FAILED: {r_scp.stderr[:300]}")
    sys.exit(1)
print("  OK: gom_e.py uploaded (dry-run fix included)")

# ── Step 2: Confirm --dry-run guard on VPS ────────────────────────────────────
print("\n=== STEP 2: Confirm --dry-run is read-only (grep check) ===")
r_grep = subprocess.run(
    ["ssh", VPS, f"grep -n 'dry_run' {VPS_ROOT}/scripts/gom_e.py | head -20"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(r_grep.stdout[:1000])
# Must see: "if not dry_run: _save_state" and "not dry_run" in T1-STORE block
if "dry_run" not in r_grep.stdout:
    print("ERROR: dry_run not found in remote gom_e.py — SCP may have failed")
    sys.exit(1)
print("  dry_run guard confirmed in remote script")

# ── Step 3: Run T1 --dry-run --daily on VPS ───────────────────────────────────
print("\n=== STEP 3: T1 --dry-run --daily (EVAL = 2026-08-10) ===")
print("  (skips state write, T1-STORE, log — read-only)\n")
cmd = (
    f"cd {VPS_ROOT} && "
    f"python3 scripts/gom_e.py "
    f"--daily --dry-run "
    f"--store data/export "
    f"--fw-filter data/config/freshwatch_symbols.txt"
)
r_run = subprocess.run(
    ["ssh", VPS, cmd],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    timeout=120
)
stdout = r_run.stdout or ""
stderr = r_run.stderr or ""

print(stdout[:8000])
if stderr.strip():
    print(f"\n[STDERR]\n{stderr[:2000]}")

if r_run.returncode != 0:
    print(f"\nEXIT={r_run.returncode} — check stderr above")

# ── Step 4: Confirm state.json NOT written ────────────────────────────────────
print("\n=== STEP 4: Confirm gom_e_state.json NOT created ===")
r_check = subprocess.run(
    ["ssh", VPS, f"ls -la {VPS_ROOT}/data/gom_e_state.json 2>/dev/null || echo MISSING"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if "MISSING" in r_check.stdout:
    print("  CONFIRMED: gom_e_state.json still MISSING — dry-run did not write state")
else:
    print(f"  WARN: {r_check.stdout.strip()} — state file exists (was it pre-existing?)")

# ── Step 5: Extract registry from stdout ─────────────────────────────────────
print("\n=== STEP 5: REGISTRY SUMMARY ===")
lines = stdout.splitlines()
banga_lines = [l for l in lines if "BANG A" in l or "HEDGE-FARM" in l or
               l.strip().startswith("—") or "NEW" in l or
               (l.strip().startswith("[GOM-E") and "registry=" in l)]
for l in banga_lines:
    print(f"  {l}")

print("\nDUNG — doi operator duyet registry truoc backfill.")

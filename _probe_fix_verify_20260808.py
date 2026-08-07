#!/usr/bin/env python3
"""Probe: (1) Verify GOM-A compose + A3 fix — FF gLSR series + slope.
          (2) S-MISSING scope — check how many freshwatch tokens have 0 rows for 24-26/07.
          (3) Regen 24-26/07 từ top_pos_1h on VPS → inject into filtered CSV.
          (4) Re-run --daily with corrected formula + regen'd CSV.
"""
import sys, subprocess, json, math
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd

REPO      = Path(__file__).resolve().parent
FW137_DIR = REPO / "scratch" / "fw137_test"
GOM       = REPO / "scripts" / "gom_scan.py"
VPS       = "root@5.223.67.21"
BASE      = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# ── 1. FF gLSR series + slope check ──────────────────────────────────────────
print("=== 1. FF gLSR series 07-24 → 07-31 + A3 slope check ===")
df_jul = pd.read_csv(FW137_DIR / "freshwatch_daily_2026-07.csv")
ff = df_jul[df_jul["symbol"] == "FFUSDT"][["date", "lsr_global_r"]].sort_values("date")
ff_window = ff[(ff["date"] >= "2026-07-20") & (ff["date"] <= "2026-08-01")]
print(ff_window.to_string(index=False))

# Compute slope_5d for 07-30: lsr_global[07-30] / lsr_global[07-25]
ff_dict = dict(zip(ff["date"], ff["lsr_global_r"]))
g_30 = ff_dict.get("2026-07-30", float("nan"))
g_25 = ff_dict.get("2026-07-25", float("nan"))
print(f"\nFF lsr_global 07-30={g_30}, 07-25={g_25}")
if not math.isnan(g_30) and not math.isnan(g_25) and g_25 > 0:
    slope = g_30 / g_25
    print(f"slope_5d = {slope:.4f}  (≤1.15 → A3=True, >1.15 → A3=False)")
else:
    print("g_25 is NaN (S-MISSING day) → slope_dq returns False → A3=True (no-DQ default)")

print()

# ── 2. S-MISSING scope: how many freshwatch tokens have 0 rows for 24-26/07 ──
print("=== 2. S-MISSING scope: freshwatch tokens with 0 rows for 24-26/07 ===")
fw_sym = Path(REPO / "scratch" / "freshwatch_symbols.txt")
fw_list = [l.strip() for l in fw_sym.read_text(encoding="utf-8").splitlines() if l.strip()]

df_aug = pd.read_csv(FW137_DIR / "freshwatch_daily_2026-08.csv")
df_all_months = pd.concat([df_jul, df_aug], ignore_index=True)

missing_24_26 = []
has_data_24_26 = []
for sym in fw_list:
    rows = df_all_months[
        (df_all_months["symbol"] == sym) &
        (df_all_months["date"].isin(["2026-07-24", "2026-07-25", "2026-07-26"]))
    ]
    if len(rows) == 0:
        missing_24_26.append(sym)
    else:
        has_data_24_26.append((sym, len(rows)))

print(f"Freshwatch total: {len(fw_list)}")
print(f"Have data 24-26/07: {len(has_data_24_26)} — {[s for s, _ in has_data_24_26]}")
print(f"S-MISSING 24-26/07: {len(missing_24_26)} tokens")
print(f"  (first 10): {missing_24_26[:10]}")

print()

# ── 3. Regen 24-26/07 from top_pos_1h on VPS ──────────────────────────────────
print("=== 3. Regen 24-26/07 from top_pos_1h on VPS ===")
REGEN_SCRIPT = REPO / "_task_regen_24_26jul.py"
REGEN_SCRIPT.write_text(r'''#!/usr/bin/env python3
"""Run on VPS: aggregate top_pos_1h → daily rows for 2026-07-24/25/26.
Output: /tmp/regen_24_26jul.csv (appended rows for those 3 dates).
"""
import sys, glob, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
import numpy as np

BASE = "/root/Data_back_test/whale_data"
DATES = ["2026-07-24", "2026-07-25", "2026-07-26"]
FW_SYM = BASE + "/data/config/freshwatch_symbols.txt"

# Load freshwatch symbols
with open(FW_SYM, encoding="utf-8") as f:
    fw_syms = set(l.strip() for l in f if l.strip())

rows = []
for d in DATES:
    files = glob.glob(f"{BASE}/data/raw/top_pos_1h/date={d}/*.parquet")
    if not files:
        print(f"  {d}: no 1h files — skip")
        continue
    df1h = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    # Filter to freshwatch symbols
    if "symbol" in df1h.columns:
        df1h = df1h[df1h["symbol"].isin(fw_syms)]
    print(f"  {d}: {len(files)} parquet files, {len(df1h)} 1h rows, {df1h['symbol'].nunique()} syms")
    print(f"    columns: {list(df1h.columns)[:15]}")
    rows.append(df1h.assign(_date=d))

if not rows:
    print("No data found — exiting")
    sys.exit(1)

dfall = pd.concat(rows, ignore_index=True)
print(f"\nAll 3 dates combined: {len(dfall)} rows")
print(f"Sample columns: {list(dfall.columns)}")
''', encoding="utf-8")

r_scp = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no",
     str(REGEN_SCRIPT), f"{VPS}:/tmp/_task_regen_24_26jul.py"],
    capture_output=True, encoding="utf-8", timeout=30,
)
print(f"SCP script rc={r_scp.returncode}")

out_r, err_r = ssh("python3 /tmp/_task_regen_24_26jul.py 2>&1", timeout=120)
print(out_r or err_r or "(no output)")

print()

# ── 4. After diagnosing VPS columns, regen actual daily CSV rows ──────────────
print("=== 4. Full regen logic (depends on step 3 column output) ===")
print("  → Run this probe first; step 4 written after knowing 1h column names.")
print("  → If columns available, will generate daily aggregates and inject into fw137_test/.")
print("\n=== DỪNG — duyệt output step 3 trước khi tiếp regen inject ===")

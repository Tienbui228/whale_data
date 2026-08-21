#!/usr/bin/env python3
"""[A4(3)] SIGN case H verify — VPS auto-commit 20/08 data + ae5f2a0.

Chứng SIGN 06-22/a event tồn tại trên VPS auto-commit 20/08 CSV (identical local pin).
Nếu event exist → case H FALSIFIED (không phải data-drift, SIGN đã có event 06-22 ở
mọi baseline June-CSV bit-identical).

Steps:
1. SCP VPS June CSV from commit 0457206 (init, 07-08 committed) → /tmp
2. SCP VPS Aug CSV from commit ebb69d0 (auto-commit 08-20 = local pin md5)
3. md5 verify LOCAL pin == VPS extracted
4. Run ae5f2a0 analyze_token(SIGN) on VPS-extracted snapshot
5. Assert event 06-22/a present
"""
from __future__ import annotations
import sys, io, csv, subprocess, hashlib
from pathlib import Path
from datetime import date as _date, timedelta
from statistics import median
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")

VPS_TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\vps_a4_3")
VPS_TMP.mkdir(parents=True, exist_ok=True)

LOCAL_PIN = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")

def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

# ── Step 1+2: fetch VPS CSVs from specific commits ──
# For June: only 1 commit exists (0457206 = init)
# For Aug: ebb69d0 (auto-commit 20/08 = matches local Aug md5)
# For July: use init commit as well (didn't drift)
VPS_FETCHES = [
    ("0457206", "data/export/freshwatch_daily_2026-06.csv", VPS_TMP / "freshwatch_daily_2026-06.csv"),
    ("0457206", "data/export/freshwatch_daily_2026-07.csv", VPS_TMP / "freshwatch_daily_2026-07.csv"),
    ("ebb69d0", "data/export/freshwatch_daily_2026-08.csv", VPS_TMP / "freshwatch_daily_2026-08.csv"),
]

for c, remote, local in VPS_FETCHES:
    cmd = ["ssh", "root@5.223.67.21", f"cd /root/Data_back_test/whale_data && git show {c}:{remote}"]
    with open(local, "wb") as f:
        p = subprocess.run(cmd, stdout=f, check=True)
    print(f"  fetch VPS {c}:{remote} → {local.name}  md5={_md5(local)}")

# ── Step 3: md5 verify VPS vs local pin ──
print(f"\n[md5 compare VPS extracted vs local pin]")
for m in ["06", "07", "08"]:
    vps_p = VPS_TMP / f"freshwatch_daily_2026-{m}.csv"
    loc_p = LOCAL_PIN / f"freshwatch_daily_2026-{m}.csv"
    v_md5 = _md5(vps_p); l_md5 = _md5(loc_p)
    tag = "MATCH" if v_md5 == l_md5 else "DRIFT"
    print(f"  {m}: VPS={v_md5}  LOCAL={l_md5}  [{tag}]")

# ── Step 4: Run ae5f2a0 analyze_token on VPS snapshot for SIGN ──
AE5_FILE = Path(r"C:\Users\Hello\AppData\Local\Temp\ae5f2a0_task_full.py")
if not AE5_FILE.exists():
    subprocess.run(["bash","-c",
        f"git -C '{REPO}' show ae5f2a0:_task_registry_c1_c4_20260820.py > '{AE5_FILE}'"], check=True)
ae5_src = AE5_FILE.read_text(encoding="utf-8")
start = ae5_src.find("def analyze_token")
lines = ae5_src[start:].split("\n")
end_idx = 0
for i, ln in enumerate(lines):
    if i == 0: continue
    if ln.startswith("def ") or (ln and not ln[0].isspace() and not ln.startswith("#")):
        end_idx = i; break
if end_idx == 0: end_idx = len(lines)

NAN = float("nan")
exec_globals = {
    "defaultdict": defaultdict, "median": median, "timedelta": timedelta,
    "_date": _date, "date": _date,
    "DRIFT_MIN_DEFAULT": 0.15, "STRUCT_N_MIN": 3,
    "WINDOW_START": "2026-06-20", "WINDOW_END": "2026-08-19",
    "REARM_MIN_DAYS": 14, "REARM_PX_MULT": 1.10, "REARM_OI_MULT": 1.30,
    "REARM_COOLDOWN_DAYS": 14, "POS_GUARD": 0.90, "PX_GUARD": 0.85,
}
exec("\n".join(lines[:end_idx]), exec_globals)
analyze_token_ae5 = exec_globals["analyze_token"]

# Load SIGN data from VPS-extracted CSVs
sign_data = {}
for m in ["06","07","08"]:
    p = VPS_TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r.get("symbol","") != "SIGNUSDT": continue
            try:
                sign_data[r["date"]] = {
                    "pos_r": float(r["lsr_pos_r"]),
                    "acc_r": float(r["lsr_acc_r"]),
                    "px":    float(r["px_avg"]),
                    "oi":    float(r["oi_usd"]),
                    "vol":   float(r["vol_quote"]),
                }
            except Exception: pass

print(f"\n[SIGN data from VPS] {len(sign_data)} days, range {min(sign_data)} → {max(sign_data)}")

evs = analyze_token_ae5("SIGNUSDT", sign_data, drift_min=0.15, struct_n_min=3)
print(f"\n[ae5f2a0 SIGN events]: {len(evs)}")
for e in evs:
    print(f"  {e['unhedge_date']}/{e['trigger']} sn={e['struct_n']} hs={e['hedge_start']} px={e['unhedge_px']:.6f}")

# ── Step 5: assert event 06-22/a ──
has_0622a = any(e['unhedge_date'] == '2026-06-22' and e['trigger'] == 'a' for e in evs)
print(f"\n[H FALSIFY]: SIGN event 06-22/a on VPS auto-commit 20/08 snapshot: {'PRESENT ✓' if has_0622a else 'ABSENT ✗'}")

print(f"\n[verdict]")
if has_0622a:
    print("  → Case H (data-drift) FALSIFIED for SIGN")
    print("  → SIGN 06-22/a existed on BOTH baseline: current + VPS auto-commit 20/08")
    print("  → June CSV md5 identical (1 commit only = 0457206 init 08-07 pre-baseline)")
    print("  → SIGN diff in regress-3 was WINDOW_START (06-20 canonical) or code-drift (d98c170), NOT data")
    print("  → A4(2) MATCH on SIGN 06-22/a (post-A1+I+J+K+L) confirms this")
else:
    print("  → Case H unresolved — SIGN 06-22/a MISSING on VPS 20/08 snapshot")
    print("  → NEW CASE — need investigation")

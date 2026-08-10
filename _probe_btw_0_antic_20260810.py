"""
_probe_btw_0_antic_20260810.py
W-0: Nạp án tích BTW — calib #6.
Trích twelve_cases_reference §6, btw_result.txt, grep ledger/gom_state.
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SIGNALS = Path(r"D:\Data back test\binance-bot-signals")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
SYM_BASE = "BTW"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"W-0 ÁN TÍCH BTW  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
SCRATCH.mkdir(exist_ok=True)

# ── §6 BTW from twelve_cases_reference.md ────────────────────────────────
log(f"\n=== §6 BTW — twelve_cases_reference.md ===")
ref_path = SIGNALS / "docs" / "twelve_cases_reference.md"
if ref_path.exists():
    lines = ref_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_btw = False; btw_lines = []
    for i, l in enumerate(lines):
        if "## 6. BTW" in l or "§6" in l:
            in_btw = True
        if in_btw:
            btw_lines.append(l)
            if len(btw_lines) > 5 and ("## 7." in l or "## 8." in l):
                btw_lines = btw_lines[:-1]; break
    for l in btw_lines:
        log(f"  {l}")
else:
    log(f"  twelve_cases_reference.md not found: {ref_path}")

# ── btw_result.txt ────────────────────────────────────────────────────────
log(f"\n=== btw_result.txt (calib data) ===")
btw_result = SIGNALS / "docs" / "case study" / "btw_result.txt"
if btw_result.exists():
    log(btw_result.read_text(encoding="utf-8", errors="replace"))
else:
    log(f"  btw_result.txt not found")

# ── gom_state BTW ─────────────────────────────────────────────────────────
log(f"\n=== gom_state.json — BTW ===")
state_p = ROOT / "data" / "gom_state.json"
if state_p.exists():
    state = json.loads(state_p.read_text(encoding="utf-8"))
    btw_st = state.get("BTW", {})
    log(json.dumps(btw_st, indent=2, default=str))
else:
    log(f"  gom_state.json not found")

# ── Alpha ID ──────────────────────────────────────────────────────────────
log(f"\n=== Alpha ID ===")
alpha_map_p = ROOT / "data" / "config" / "alpha_id_map.json"
if alpha_map_p.exists():
    alpha_map = json.loads(alpha_map_p.read_text(encoding="utf-8"))
    aid = alpha_map.get(SYM_BASE, alpha_map.get("BTW"))
    log(f"  BTW alpha_id: {aid}")
else:
    log(f"  alpha_id_map.json not found")

# ── Freshwatch history ────────────────────────────────────────────────────
log(f"\n=== Freshwatch BTW rows ===")
fw_count = 0; fw_dates = []
for fw_csv in sorted((ROOT/"scratch").glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == SYM:
                fw_count += 1; fw_dates.append(row.get("date","")[:10])
log(f"  {SYM} rows in freshwatch (scratch): {fw_count}")
if fw_dates:
    log(f"  Date range: {min(fw_dates)} → {max(fw_dates)}")

# Also check export CSVs
export_dir = ROOT / "data" / "export"
if export_dir.exists():
    fw_exp_count = 0; fw_exp_dates = []
    for fw_csv in sorted(export_dir.glob("freshwatch_daily_*.csv")):
        with open(fw_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("symbol","").upper() == SYM:
                    fw_exp_count += 1; fw_exp_dates.append(row.get("date","")[:10])
    log(f"  Export CSVs: {fw_exp_count} rows, {min(fw_exp_dates) if fw_exp_dates else 'N/A'} → {max(fw_exp_dates) if fw_exp_dates else 'N/A'}")

# ── grep agent_log for key BTW lines ─────────────────────────────────────
log(f"\n=== agent_log BTW key events ===")
agent_log = ROOT / "agent_log.md"
if agent_log.exists():
    lines = agent_log.read_text(encoding="utf-8").splitlines()
    key_lines = [
        (i+1, l) for i,l in enumerate(lines)
        if "BTW" in l and any(kw in l for kw in ["7.5M","48.8M","SUPP","ALPHA_778","DQ","chapter","08-08","decay","neg_div","wake","thức"])
    ]
    for n,l in key_lines[:20]:
        log(f"  L{n}: {l[:120]}")

log(f"\n[W-0 DONE]")

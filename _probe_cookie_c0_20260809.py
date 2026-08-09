"""
_probe_cookie_c0_20260809.py
COOKIE C-0: Truy alert — gom_state + agent_log + gom_scan GOM-C conditions
"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRIPTS = ROOT / "scripts"
DATE_TAG = "20260809"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-0  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# ── 1. gom_state_v8.json ─────────────────────────────────────────────────────
log("\n=== gom_state_v8.json — COOKIE chain ===")
gsv8_path = ROOT / "data" / "gom_state_v8.json"
gsv8 = json.loads(gsv8_path.read_text(encoding="utf-8"))
cc = gsv8.get("COOKIE", gsv8.get("COOKIEUSDT", {}))
log(f"  chain_open:      {cc.get('chain_open')}")
log(f"  start_date:      {cc.get('start_date')}")
log(f"  chapter:         {cc.get('chapter')}")
log(f"  n_days:          {cc.get('n_days')}")
log(f"  Q1_cum_usd:      {cc.get('Q1_cum_usd')}")
log(f"  vwap_num:        {cc.get('vwap_num')}")
log(f"  vwap_den:        {cc.get('vwap_den')}")
vwap = cc.get("vwap_num", 0) / cc.get("vwap_den", 1) if cc.get("vwap_den") else None
log(f"  VWAP (calc):     {vwap:.8f}" if vwap else "  VWAP: N/A")
log(f"  peak_pos_r:      {cc.get('peak_pos_r')}")
log(f"  break_streak:    {cc.get('break_streak')}")
log(f"  last_gom_date:   {cc.get('last_gom_date')}")
log(f"  close_date:      {cc.get('close_date')}")
log(f"  close_reason:    {cc.get('close_reason')}")
log(f"  vwap_fallback:   {cc.get('vwap_fallback_used')}")
log(f"  updated_at:      {cc.get('updated_at')}")

# ── 2. production gom_state.json ────────────────────────────────────────────
log("\n=== production gom_state.json — COOKIE ===")
gs_path = ROOT / "data" / "gom_state.json"
if gs_path.exists():
    gs = json.loads(gs_path.read_text(encoding="utf-8"))
    cp = gs.get("COOKIE", gs.get("COOKIEUSDT", {}))
    if cp:
        log(f"  chain_open: {cp.get('chain_open')}")
        log(f"  start_date: {cp.get('start_date')}")
        log(f"  n_days: {cp.get('n_days')}")
        log(f"  Q1_cum_usd: {cp.get('Q1_cum_usd')}")
        log(f"  close_date: {cp.get('close_date')}")
        log(f"  close_reason: {cp.get('close_reason')}")
    else:
        log("  COOKIE: {} (empty / not in production state)")
else:
    log("  gom_state.json not found")

# ── 3. alpha_id_map.json ─────────────────────────────────────────────────────
log("\n=== alpha_id_map ===")
aim = json.loads((ROOT / "data" / "config" / "alpha_id_map.json").read_text(encoding="utf-8"))
alpha_id = aim.get("COOKIE", "NOT FOUND")
log(f"  COOKIE → {alpha_id}")

# ── 4. agent_log grep ────────────────────────────────────────────────────────
log("\n=== agent_log grep COOKIE (last 20 hits) ===")
al_path = ROOT / "agent_log.md"
hits = []
for i, line in enumerate(al_path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
    if "COOKIE" in line:
        hits.append((i, line.strip()))
log(f"  Total COOKIE mentions: {len(hits)}")
for i, (ln, txt) in enumerate(hits[-20:]):
    log(f"  L{ln}: {txt[:120]}")

# ── 5. GOM-C conditions check ────────────────────────────────────────────────
log("\n=== GOM-C CONDITIONS (spec inference from gom_scan.py) ===")
# GOM-C = campaign-track: fire when GOM-A fires AND a separate C-series condition
# Read gom_scan to find GOM-C gate
gs_py = SCRIPTS / "gom_scan.py"
if gs_py.exists():
    src = gs_py.read_text(encoding="utf-8", errors="replace")
    # Find C1/C2/C3 conditions around "campaign" or "gom_c"
    lines = src.splitlines()
    c_lines = []
    for i, l in enumerate(lines):
        if any(kw in l.lower() for kw in ["gom_c", "campaign", "c1_", "c2_", "c3_", "c4_"]):
            c_lines.append((i+1, l.rstrip()))
    log(f"  GOM-C related lines in gom_scan.py: {len(c_lines)}")
    for ln, txt in c_lines[:40]:
        log(f"  {ln}: {txt[:120]}")
else:
    log("  gom_scan.py not found in scripts/")

# ── 6. freshwatch COOKIE data check ──────────────────────────────────────────
log("\n=== freshwatch COOKIE rows ===")
import csv
total_fw = 0
for fname in ["freshwatch_daily_2026-06.csv", "freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    fpath = ROOT / "scratch" / fname
    if not fpath.exists():
        log(f"  {fname}: NOT FOUND in scratch")
        continue
    rows = []
    with open(fpath, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol", r.get("Symbol", ""))
            if sym in ("COOKIEUSDT", "COOKIE"):
                rows.append(r)
    total_fw += len(rows)
    log(f"  {fname}: {len(rows)} COOKIE rows")
    if rows:
        dates = [r.get("date", r.get("Date","?")) for r in rows]
        log(f"    Range: {dates[0]} → {dates[-1]}")
        last = rows[-1]
        log(f"    Last: pos_r={last.get('pos_r',last.get('pos_r_raw','?'))} "
            f"acc_r={last.get('acc_r',last.get('acc_r_raw','?'))} "
            f"gLSR={last.get('glsr_raw',last.get('gLSR','?'))} "
            f"oi_usd={last.get('oi_usd','?')}")
log(f"  Total FW rows: {total_fw}")

log(f"\n[C-0 DONE]")

"""Verify Bug1 (BANK in rule-iv) and Bug2 (Q2 gate) fixes post-patch."""
import sys, json, math
from pathlib import Path
sys.path.insert(0, "scripts")

# ── Bug 1: BANK category in _closed_section ────────────────────────────────
STATE = Path("data/gom_state.json")
state = json.loads(STATE.read_text(encoding="utf-8"))

bank = state.get("BANK", {})
print("=== Bug 1: BANK state entry ===")
print(f"  close_date   : {bank.get('close_date')}")
print(f"  close_reason : {bank.get('close_reason')}")
print(f"  close_note   : {bank.get('close_note')}")
print(f"  retro_tag    : {bank.get('retro_tag')}")
print(f"  retro_tag_note: {bank.get('retro_tag_note')}")

# Simulate _cat() OLD logic
def _cat_old(ch):
    reason_raw = ch.get("close_reason", "")
    if ch.get("close_note") == "chuyển pha phân phối" or "pos_r_drop" in reason_raw:
        return "rule-iv"
    if "suppressor" in reason_raw or "dq_cooldown" in reason_raw:
        return "supp"
    return "gap"

# Simulate _cat() NEW logic
def _cat_new(ch):
    reason_raw = ch.get("close_reason", "")
    if (ch.get("close_note") == "chuyển pha phân phối"
            or "pos_r_drop" in reason_raw
            or ch.get("retro_tag")):
        return "rule-iv"
    if "suppressor" in reason_raw or "dq_cooldown" in reason_raw:
        return "supp"
    return "gap"

print(f"\n  _cat OLD → '{_cat_old(bank)}'  (expect: gap)")
print(f"  _cat NEW → '{_cat_new(bank)}'  (expect: rule-iv)")

# ── Bug 2: Q2 gate for CYS/TUT/COOKIE ────────────────────────────────────
print("\n=== Bug 2: Q2 gate check (div_raw=pos_r/lsr_acc ≥3 AND lsr_acc ≤1) ===")

from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals

STORE   = Path("data/export")
CONFIG  = Path("data/config")
intervals = load_funding_intervals(CONFIG)
import gom_scan as gs
from scanner.screener.signals import load_thresholds
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-08-07", lookback_days=30)

for sym in ["COOKIE", "CYS", "TUT"]:
    build_sym = sym + "USDT"
    try:
        days_tok, _ = build_token_days(df, build_sym, "2026-07-01", "2026-08-07", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        print(f"{sym}: BUILD ERR {e}")
        continue
    if not days_tok:
        print(f"{sym}: NO DAYS")
        continue
    d = days_tok[-1]
    pos_r    = d.get("lsr_pos", float("nan"))
    lsr_acc  = d.get("lsr_acc", float("nan"))
    oi_now   = d.get("oi_usd", float("nan"))
    _div     = pos_r / lsr_acc if (not math.isnan(lsr_acc) and lsr_acc != 0) else float("nan")
    gate_ok  = not math.isnan(_div) and _div >= 3 and not math.isnan(lsr_acc) and lsr_acc <= 1
    if gate_ok and not math.isnan(pos_r) and pos_r > 0 and not math.isnan(oi_now):
        tilt  = (pos_r - 1) / (pos_r + 1)
        q2_lo = oi_now * 0.5 * tilt
        q2_hi = oi_now * 0.8 * tilt
        q2_s  = f"${q2_lo/1e6:.1f}-{q2_hi/1e6:.1f}M"
    else:
        q2_s  = "N/A [ngoài heuristic]"
    print(f"  {sym}: pos_r={pos_r:.4f} lsr_acc={lsr_acc:.4f} div_raw={_div:.2f}  gate={gate_ok}  Q2→{q2_s}")

"""Probe: CHƯƠNG ĐÃ ĐÓNG 60d + GOM-C detail for 2026-08-07.

Reads gom_state.json (post-swap v8) and reprints:
1. All closed chains with close_reason (rule-iv lên đầu)
2. GOM-C fires on 2026-08-07 + why ARIA/FHE/TRADOOR missing
"""
import sys, json, math
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE    = Path("data/export")
CONFIG   = Path("data/config")
STATE    = Path("data/gom_state.json")
THRESH   = Path("screen_thresholds.yaml")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

state = json.loads(STATE.read_text(encoding="utf-8"))
TARGET = "2026-08-07"
cutoff = (datetime.strptime(TARGET, "%Y-%m-%d") - timedelta(days=60)).strftime("%Y-%m-%d")

print(f"State loaded. Target={TARGET}. 60d window >= {cutoff}")
print()

# ── CHƯƠNG ĐÃ ĐÓNG 60d ──────────────────────────────────────────────────────
rule_iv = []   # pos_r_drop
gom_gap = []   # gom_gap>2d
other   = []

for sym, v in state.items():
    if sym.startswith("_"):
        continue
    if v.get("chain_open"):
        continue
    cd = v.get("close_date","")
    if not cd or cd < cutoff:
        continue
    reason = v.get("close_reason","")
    drop   = v.get("peak_pos_r_drop_str", v.get("close_pos_r_drop",""))
    peak   = v.get("peak_pos_r", float("nan"))
    retro  = v.get("retro_tag_note","")
    row = {"sym": sym, "close_date": cd, "reason": reason, "peak": peak, "drop": drop, "retro": retro}
    if "pos_r_drop" in reason:
        rule_iv.append(row)
    elif "gom_gap" in reason:
        gom_gap.append(row)
    else:
        other.append(row)

rule_iv.sort(key=lambda x: float(x["drop"].replace("%","").split(":")[1] if ":" in str(x.get("drop","")) else x.get("drop","0").replace("%","") or "0"), reverse=True) if rule_iv else None

print("── RULE-IV CLOSED (pos_r_drop) ──")
print(f"{'sym':<14} {'close':<12} {'reason':<35} {'retro'}")
print("-"*75)
for r in sorted(rule_iv, key=lambda x: x["close_date"]):
    print(f"{r['sym']:<14} {r['close_date']:<12} {r['reason']:<35} {r['retro']}")

print()
print("── GOM_GAP CLOSED ──")
for r in sorted(gom_gap, key=lambda x: x["close_date"]):
    print(f"{r['sym']:<14} {r['close_date']:<12} {r['reason']:<35} {r['retro']}")

print()
print("── OTHER CLOSED ──")
for r in sorted(other, key=lambda x: x["close_date"]):
    print(f"{r['sym']:<14} {r['close_date']:<12} {r['reason']:<35}")

print()
print(f"Counts: rule-iv={len(rule_iv)} gom_gap={len(gom_gap)} other={len(other)}")

# ── GOM-C CHECK: ARIA / FHE / TRADOOR on 08-07 ──────────────────────────────
print()
print("── GOM-C MISSING: ARIA / FHE / TRADOOR on 08-07 ──")

df = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df = taker_scale_check_df(df)

for sym in ["ARIA", "FHE", "TRADOOR"]:
    build_sym = sym + "USDT"
    st = state.get(sym, {})
    dq_ep  = st.get("dq_episode_start","")
    dq_end = st.get("dq_cooldown_end","")
    chain_open = st.get("chain_open", False)
    close_date = st.get("close_date","")
    print(f"\n{sym}: dq_ep={dq_ep} dq_end={dq_end} chain_open={chain_open} close={close_date}")

    try:
        days_tok, _ = build_token_days(df, build_sym, "2026-07-01", "2026-08-07", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        print(f"  BUILD ERROR: {e}")
        continue

    # Scan loop to 08-07
    chain = {}
    for i, d in enumerate(days_tok):
        result = gs.eval_gom(days_tok, i, cfg, sc)
        chain  = gs.update_chain(chain, build_sym, days_tok, i, result, cfg, sc)

    # Check GOM-C eligibility on 08-07 (last day)
    if not days_tok:
        print("  NO DAYS")
        continue

    d_last   = days_tok[-1]
    i_last   = len(days_tok) - 1
    dt_last  = d_last.get("date","")
    result   = gs.eval_gom(days_tok, i_last, cfg, sc)
    ga       = result.get("gom_a", {})
    supp     = result.get("any_supp_dq", False)
    perday   = result.get("any_perday_dq", False)
    gom_day  = result.get("gom_day", False)
    cd_end   = chain.get("dq_cooldown_end","")
    in_cooldown = bool(cd_end and cd_end >= dt_last)

    # GOM-C: fires when (A1∨A2∨A3) and d_pos_3d ≥ 0 and not in cooldown and not chain_open
    a1,a2,a3 = ga.get("A1"),ga.get("A2"),ga.get("A3")
    d3 = d_last.get("d_pos_3d", float("nan"))
    gomc_eligible = (a1 or a2 or a3) and (not math.isnan(d3) and d3 >= 0) and not in_cooldown and not chain.get("chain_open")

    print(f"  {dt_last}: A1={a1} A2={a2} A3={a3} supp={supp} perday={perday} gom_day={gom_day}")
    print(f"  cd_end={cd_end} in_cooldown={in_cooldown} chain_open={chain.get('chain_open')} d_pos_3d={d3:.4g}")
    print(f"  GOM-C eligible: {gomc_eligible}")
    print(f"  Suppressor fires: {[k for k,v in result.get('supp_dq',{}).items() if v]}")

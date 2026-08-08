"""Suppressor distribution — FINAL (symbol format fix: state uses short keys, build needs USDT suffix).

For each suppressed token (dq_episode_start set, chain_open=False):
- Run fresh scan loop with correct USDT-suffixed symbol
- If dq sets in scan: record suppressor(s) that fired
- If dq never sets: "prior-state-carry" (episode carried from prod state, not reproducible from fw)

PC characterization: wash (no prior pump 21d) vs blowoff (had pump).
"""
import sys, math, json
from pathlib import Path
sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE    = Path("D:/Check onchain fresh wallets/data/export")
CONFIG   = Path("data/config")
STATE_V8 = Path("data/gom_state_v8.json")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

# Load fw data covering both Jul and Aug
df_jul = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df_jul = taker_scale_check_df(df_jul)
df_aug = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df_aug = taker_scale_check_df(df_aug)

state_all = json.loads(STATE_V8.read_text(encoding="utf-8"))

# Collect suppressed tokens: dq episode present, chain not open
supp_tokens = {}
for sym, v in state_all.items():
    if sym.startswith("_"):
        continue
    if isinstance(v, dict) and v.get("dq_episode_start") and not v.get("chain_open", False):
        supp_tokens[sym] = v.get("dq_episode_start", "")

print(f"Suppressed tokens in state: {len(supp_tokens)}")
print()

def had_prior_pump(days, fire_i, lookback=21, pump_thr=0.20):
    for j in range(max(1, fire_i - lookback), fire_i):
        p0 = days[j-1].get("avg_px", float("nan"))
        p1 = days[j].get("avg_px", float("nan"))
        if not math.isnan(p0) and not math.isnan(p1) and p0 > 0:
            if (p1 - p0) / p0 >= pump_thr:
                return True
    return False

results_fw  = []  # dq reproduced from fw scan
results_cs  = []  # prior-state-carry (not reproduced)
errors      = []

for sym in sorted(supp_tokens.keys()):
    dq_exp = supp_tokens[sym]
    # FIX: state uses short names, build_token_days needs USDT suffix
    build_sym = sym if sym.endswith("USDT") else sym + "USDT"

    # Choose df/end by dq date
    if dq_exp <= "2026-07-25":
        df       = df_jul
        start_d  = "2026-05-01"
        end_d    = "2026-07-25"
    else:
        df       = df_aug
        start_d  = "2026-05-01"
        end_d    = "2026-08-07"

    try:
        days_tok, _ = build_token_days(df, build_sym, start_d, end_d, intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        errors.append((sym, f"BUILD: {e}"))
        continue

    if not days_tok:
        errors.append((sym, "NO DAYS"))
        continue

    # Scan loop — find when dq_episode_start is newly set
    chain    = {}
    prev_ep  = ""
    dq_date  = None
    fired_dq = []
    fire_idx = None

    for i, d in enumerate(days_tok):
        result = gs.eval_gom(days_tok, i, cfg, sc)
        chain  = gs.update_chain(chain, build_sym, days_tok, i, result, cfg, sc)
        cur_ep = chain.get("dq_episode_start", "")
        if cur_ep and cur_ep != prev_ep:
            dq_date  = d.get("date", "")
            fired_dq = [k for k, v in result.get("supp_dq", {}).items() if v]
            fire_idx = i
            prev_ep  = cur_ep

    if dq_date is None:
        results_cs.append({"sym": sym, "dq_exp": dq_exp})
        continue

    is_pc   = "post_climax" in fired_dq
    pc_wash = None
    if is_pc and fire_idx is not None:
        pump    = had_prior_pump(days_tok, fire_idx)
        pc_wash = not pump  # wash = no prior pump

    results_fw.append({
        "sym":        sym,
        "dq_exp":     dq_exp,
        "dq_actual":  dq_date,
        "match":      dq_date == dq_exp,
        "suppressors": "|".join(fired_dq) if fired_dq else "NONE",
        "is_pc":      is_pc,
        "pc_wash":    pc_wash,
    })

# ── Print table ───────────────────────────────────────────────────────────────
print(f"DQ REPRODUCED FROM FW SCAN ({len(results_fw)} tokens):")
print(f"{'sym':<14} {'dq_exp':<12} {'dq_actual':<12} {'M':>2} {'suppressors':<30} {'pc_wash':>9}")
print("-" * 85)
for r in sorted(results_fw, key=lambda x: x["dq_exp"]):
    m        = "Y" if r["match"] else "N"
    wash_str = ""
    if r["is_pc"]:
        wash_str = "WASH" if r["pc_wash"] else "blowoff"
    flag = " <--PC-WASH" if r["pc_wash"] else (" <--blowoff" if r["is_pc"] else "")
    print(f"{r['sym']:<14} {r['dq_exp']:<12} {r['dq_actual']:<12} {m:>2} {r['suppressors']:<30} {wash_str:>9}{flag}")

print()
print(f"PRIOR-STATE-CARRY ({len(results_cs)} tokens — dq carried from prod, not reproducible from fw):")
from collections import Counter
months = Counter(r["dq_exp"][:7] for r in results_cs)
for m, c in sorted(months.items()):
    toks = [r["sym"] for r in results_cs if r["dq_exp"].startswith(m)]
    print(f"  {m}: {c}  [{', '.join(toks[:10])}{'...' if len(toks)>10 else ''}]")

print()
if errors:
    print(f"ERRORS ({len(errors)}):")
    for sym, e in errors[:20]:
        print(f"  {sym}: {e}")
    if len(errors) > 20:
        print(f"  ...{len(errors)-20} more")
    print()

# ── Summary ───────────────────────────────────────────────────────────────────
total_fw  = len(results_fw)
total_cs  = len(results_cs)
total_err = len(errors)
total_all = total_fw + total_cs + total_err

pc_fw      = sum(1 for r in results_fw if r["is_pc"])
pc_wash_fw = sum(1 for r in results_fw if r["pc_wash"] is True)
pc_blow_fw = sum(1 for r in results_fw if r["pc_wash"] is False and r["is_pc"])
cf_fw      = sum(1 for r in results_fw if "crowd_flush" in r["suppressors"] and not r["is_pc"])
decay_fw   = sum(1 for r in results_fw if "decay" in r["suppressors"] and not r["is_pc"] and "crowd_flush" not in r["suppressors"])
other_fw   = total_fw - pc_fw - cf_fw - decay_fw

print("=" * 85)
print(f"SUMMARY — suppressor distribution ({total_all} suppressed tokens total)")
print(f"  Reproduced from fw scan  : {total_fw}")
print(f"  Prior-state-carry        : {total_cs}")
print(f"  Build errors / no data   : {total_err}")
print()
if total_fw > 0:
    print(f"Among reproducible ({total_fw}):")
    print(f"  post_climax  : {pc_fw:3d}  ({pc_fw/total_fw*100:.0f}%)")
    print(f"    PC-wash    :   {pc_wash_fw}  (no prior pump 21d — mechanism = TAG)")
    print(f"    PC-blowoff :   {pc_blow_fw}  (had prior pump)")
    print(f"  crowd_flush  : {cf_fw:3d}  ({cf_fw/total_fw*100:.0f}%)")
    print(f"  decay        : {decay_fw:3d}  ({decay_fw/total_fw*100:.0f}%)")
    print(f"  other/NONE   : {other_fw:3d}")
    print()
    if pc_wash_fw >= 2:
        print(f"WARN: {pc_wash_fw} PC-wash tokens — TAG không phải ngoại lệ, PC mechanism đang suppress oan từ-nền-phẳng.")
    else:
        print(f"PC-wash in reproducible set: {pc_wash_fw} — TAG {'là sole case' if pc_wash_fw<=1 else 'không đơn độc'}.")

print()
print("NOTE: 'prior-state-carry' = dq_episode_start was carried forward from production")
print("  gom_state.json before v8 rescan; fw data alone cannot reproduce these episodes.")
print("  Only reproduced episodes can have suppressor identified from fw scan.")

"""TAG 07-08 post_climax: fw conditions + suppressor distribution across 44 SUPPRESSED tokens.

Questions:
  1. Why does fw scan fire PC on TAG 07-08 when LOCKED replay showed CF?
     -> Print avg_px + price_change + funding_extreme conditions 07-05->09
     -> Print crowd_flush conditions (CF was the LOCKED signal)
  2. PC distribution among 44 SUPPRESSED-only tokens
     -> How many have PC as their firing suppressor?
"""
import sys, math, json
from pathlib import Path
sys.path.insert(0, "scripts")

from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds, post_climax, crowd_flush, funding_extreme, decay

STORE   = Path("D:/Check onchain fresh wallets/data/export")
CONFIG  = Path("data/config")
STATE_V8 = Path("data/gom_state_v8.json")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df = taker_scale_check_df(df)

# ── PART 1: TAG 07-05->09 fw conditions ──────────────────────────────────────
print("=" * 72)
print("PART 1 — TAG post_climax conditions 07-05→07-09 (fw data)")
print("=" * 72)
print()
print("post_climax def: price_change(j-1→j) <= -0.25  OR  funding_extreme(j)")
print(f"  crash_pct   = {cfg['post_climax']['price_crash_pct']}")
print(f"  cooldown    = {cfg['post_climax']['cooldown_days']}d")
print(f"  fe_abs_rate = {cfg['funding_extreme']['abs_rate_min']}")
print()

days_tag, _ = build_token_days(df, "TAGUSDT", "2026-06-01", "2026-07-25", intervals)
enrich_token_days(days_tag)

print(f"{'date':<12} {'avg_px':>10} {'px_chg%':>9} {'crash?':>7} {'fund_max':>10} {'fund_min':>10} {'fe?':>5} {'PC?':>5} {'CF?':>5}")
print("-" * 75)
for i, d in enumerate(days_tag):
    dt = d.get("date", "")
    if dt < "2026-07-05" or dt > "2026-07-10":
        continue
    px   = d.get("avg_px",      float("nan"))
    fmax = d.get("funding_max", float("nan"))
    fmin = d.get("funding_min", float("nan"))

    # price change from prev day
    if i > 0:
        p0 = days_tag[i-1].get("avg_px", float("nan"))
        if not math.isnan(p0) and not math.isnan(px) and p0 > 0:
            chg = (px - p0) / p0
            chg_str = f"{chg:+.1%}"
            crash = chg <= cfg["post_climax"]["price_crash_pct"]
        else:
            chg_str = "NaN"
            crash = False
    else:
        chg_str = "N/A"
        crash = False

    fe_thr = cfg["funding_extreme"]["abs_rate_min"]
    fe = (not math.isnan(fmax) and abs(fmax) >= fe_thr) or \
         (not math.isnan(fmin) and abs(fmin) >= fe_thr)

    pc = post_climax(days_tag, i, cfg)
    cf = crowd_flush(days_tag, i, cfg)

    px_str   = f"{px:.6f}"   if not math.isnan(px)   else "NaN"
    fmax_str = f"{fmax:.6f}" if not math.isnan(fmax) else "NaN"
    fmin_str = f"{fmin:.6f}" if not math.isnan(fmin) else "NaN"
    print(f"{dt:<12} {px_str:>10} {chg_str:>9} {str(crash):>7} {fmax_str:>10} {fmin_str:>10} {str(fe):>5} {str(pc):>5} {str(cf):>5}")

# Also show the full PC scan window from 07-08 perspective
print()
print("PC scan from 07-08 looking back (what triggered it):")
for i, d in enumerate(days_tag):
    if d.get("date", "") != "2026-07-08":
        break_flag = False
    if d.get("date", "") == "2026-07-08":
        target_i = i
        break

try:
    target_i
    cooldown = cfg["post_climax"]["cooldown_days"]
    crash_pct = cfg["post_climax"]["price_crash_pct"]
    print(f"  Scanning back {cooldown+1} days from i={target_i} (date=2026-07-08):")
    for k in range(0, min(cooldown+1, target_i+1)):
        j = target_i - k
        dj = days_tag[j]
        dtj = dj.get("date","")
        # crash check
        crash_j = False
        chg_j_str = "N/A"
        if j > 0:
            p0 = days_tag[j-1].get("avg_px", float("nan"))
            p1 = dj.get("avg_px", float("nan"))
            if not math.isnan(p0) and not math.isnan(p1) and p0 > 0:
                chg_j = (p1 - p0) / p0
                chg_j_str = f"{chg_j:+.1%}"
                crash_j = chg_j <= crash_pct
        fe_j = funding_extreme(days_tag, j, cfg)
        triggered = crash_j or fe_j
        if triggered:
            print(f"  k={k:2d} j={j:3d} date={dtj} px_chg={chg_j_str} crash={crash_j} fe={fe_j} -> TRIGGERED")
        if k <= 5:  # print first 5 anyway
            print(f"  k={k:2d} j={j:3d} date={dtj} px_chg={chg_j_str} crash={crash_j} fe={fe_j}")
except NameError:
    print("  2026-07-08 not found in days_tag")

# ── PART 2: Suppressor distribution across 44 SUPPRESSED tokens ──────────────
print()
print("=" * 72)
print("PART 2 — Suppressor distribution: 44 SUPPRESSED-only tokens")
print("=" * 72)
print()

state = json.loads(STATE_V8.read_text(encoding="utf-8"))

# Collect suppressed tokens (have dq_episode_start, no open chain)
supp_tokens = []
for sym, v in state.items():
    if sym.startswith("_"):
        continue
    # Has dq episode but no open chain
    has_dq = "dq_episode_start" in v and v["dq_episode_start"]
    chain_open = v.get("chain_open", False)
    if has_dq and not chain_open:
        supp_tokens.append(sym)

print(f"Tokens with dq episode + no open chain: {len(supp_tokens)}")
print()

# Now probe each suppressed token: which suppressor fired?
SUPPRESSORS = ["post_climax", "decay", "dist_wall", "lsr_dist", "funding_neg_div",
               "funding_extreme", "crowd_flush"]

# We need to find the fire date (dq_episode_start) and check which suppressor fired
from scanner.screener.signals import dist_wall, lsr_dist, funding_neg_div

supp_fn_map = {
    "post_climax":    lambda days, i: post_climax(days, i, cfg),
    "crowd_flush":    lambda days, i: crowd_flush(days, i, cfg),
    "decay":          lambda days, i: decay(days, i, cfg),
    "dist_wall":      lambda days, i: dist_wall(days, i, cfg),
    "lsr_dist":       lambda days, i: lsr_dist(days, i, cfg),
    "funding_neg_div":lambda days, i: funding_neg_div(days, i, cfg),
    "funding_extreme":lambda days, i: funding_extreme(days, i, cfg),
}

pc_count   = 0
cf_count   = 0
decay_count = 0
other_count = 0
dq_results = []

for sym in sorted(supp_tokens):
    tok = sym.replace("USDT","")
    dq_start = state[sym].get("dq_episode_start","")
    # build days for this token
    try:
        days_tok, _ = build_token_days(df, sym, "2026-06-01", "2026-07-25", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        dq_results.append((sym, dq_start, "BUILD_ERR", str(e)[:30]))
        continue

    # find the fire date index
    fire_i = None
    for idx, d in enumerate(days_tok):
        if d.get("date","") == dq_start:
            fire_i = idx
            break

    if fire_i is None:
        dq_results.append((sym, dq_start, "DATE_NOT_FOUND", ""))
        continue

    fired_supps = []
    for sname, sfn in supp_fn_map.items():
        try:
            v = sfn(days_tok, fire_i)
        except Exception:
            v = False
        if v:
            fired_supps.append(sname)

    if "post_climax" in fired_supps:
        pc_count += 1
    elif "crowd_flush" in fired_supps:
        cf_count += 1
    elif "decay" in fired_supps:
        decay_count += 1
    else:
        other_count += 1

    dq_results.append((sym, dq_start, "|".join(fired_supps) if fired_supps else "NONE", ""))

# Print full table
print(f"{'symbol':<14} {'dq_start':<12} {'fired_suppressors'}")
print("-" * 60)
for sym, dqs, fired, note in sorted(dq_results, key=lambda x: x[1]):
    flag = " <-- PC" if "post_climax" in fired else ""
    print(f"{sym:<14} {dqs:<12} {fired}{flag}")

print()
print(f"SUMMARY — suppressor distribution ({len(supp_tokens)} tokens):")
print(f"  post_climax dominates   : {pc_count} ({pc_count/len(supp_tokens)*100:.0f}%)")
print(f"  crowd_flush             : {cf_count} ({cf_count/len(supp_tokens)*100:.0f}%)")
print(f"  decay                   : {decay_count} ({decay_count/len(supp_tokens)*100:.0f}%)")
print(f"  other/NONE              : {other_count} ({other_count/len(supp_tokens)*100:.0f}%)")
print()
if pc_count > len(supp_tokens) * 0.5:
    print("WARN: PC dominates >50% of SUPPRESSED — loose PC on fw data may be suppressing oan universe")
else:
    print("OK: PC not dominant — distribution mixed")

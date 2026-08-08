"""TAG PC v2: fw avg_px vs CASE_TAG.xlsx price 07-05->09 + supp44 via eval_gom."""
import sys, math, json
from pathlib import Path
sys.path.insert(0, "scripts")

import pandas as pd
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE    = Path("D:/Check onchain fresh wallets/data/export")
CONFIG   = Path("data/config")
CASES    = Path("docs/case_files")
STATE_V8 = Path("data/gom_state_v8.json")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df = taker_scale_check_df(df)

# ── PART 1: avg_px fw vs CASE_TAG.xlsx 07-05->10 ─────────────────────────────
print("=" * 70)
print("PART 1 — TAG avg_px fw CSV vs CASE_TAG.xlsx 07-05→07-10")
print("(verify -45.5% crash is in calib data too, or diverge)")
print("=" * 70)

# fw raw avg_px
df_jul = pd.read_csv(STORE / "freshwatch_daily_2026-07.csv")
df_tag = df_jul[df_jul["symbol"] == "TAGUSDT"].copy()
df_tag = df_tag[(df_tag["date"] >= "2026-07-05") & (df_tag["date"] <= "2026-07-10")].sort_values("date")

print("\n[FW CSV] TAGUSDT avg_px + price change:")
print(f"  {'date':<12} {'avg_px':>10} {'px_change':>10}")
prev_px = float("nan")
for _, r in df_tag.iterrows():
    px = float(r.get("avg_px", float("nan"))) if not pd.isna(r.get("avg_px")) else float("nan")
    if not math.isnan(prev_px) and not math.isnan(px) and prev_px > 0:
        chg = f"{(px-prev_px)/prev_px:+.1%}"
    else:
        chg = "N/A"
    print(f"  {r['date']:<12} {px:>10.6f} {chg:>10}")
    prev_px = px

# CASE_TAG.xlsx
case_path = CASES / "CASE_TAG.xlsx"
if case_path.exists():
    try:
        df_case = pd.read_excel(case_path, sheet_name="DAILY", header=1)
        date_col = df_case.columns[0]
        # find px column
        px_cols = [c for c in df_case.columns if "px" in str(c).lower() or "price" in str(c).lower() or "avg" in str(c).lower()]
        print(f"\n[CASE_TAG.xlsx] px columns found: {px_cols[:8]}")
        print(f"  All DAILY cols: {list(df_case.columns[:20])}")

        df_case["_date"] = pd.to_datetime(df_case[date_col], errors="coerce")
        mask = (df_case["_date"] >= pd.Timestamp("2026-07-05")) & (df_case["_date"] <= pd.Timestamp("2026-07-10"))
        df_filt = df_case[mask].copy()

        if px_cols:
            print(f"\n[CASE_TAG.xlsx] px 07-05→07-10 ({px_cols[0]}):")
            prev_px = float("nan")
            for _, r in df_filt.iterrows():
                dt = r["_date"].strftime("%Y-%m-%d") if pd.notna(r["_date"]) else "?"
                px_raw = r.get(px_cols[0])
                px = float(px_raw) if not pd.isna(px_raw) else float("nan")
                if not math.isnan(prev_px) and not math.isnan(px) and prev_px > 0:
                    chg = f"{(px-prev_px)/prev_px:+.1%}"
                else:
                    chg = "N/A"
                print(f"  {dt:<12} {px:>10.6f} {chg:>10}")
                prev_px = px
    except Exception as e:
        print(f"  ERROR reading CASE_TAG.xlsx: {e}")
else:
    print("  CASE_TAG.xlsx NOT FOUND")

# ── PART 2: supp44 via eval_gom ──────────────────────────────────────────────
print()
print("=" * 70)
print("PART 2 — 44 SUPPRESSED: suppressor via eval_gom at dq_episode_start")
print("=" * 70)

state = json.loads(STATE_V8.read_text(encoding="utf-8"))

# Get suppressed tokens
supp_tokens = {}
for sym, v in state.items():
    if sym.startswith("_"):
        continue
    has_dq  = bool(v.get("dq_episode_start",""))
    chain_open = v.get("chain_open", False)
    # also skip tokens that have both (they're suppressed but opened later)
    # we want "no open chain" at end of scan
    if has_dq and not chain_open:
        supp_tokens[sym] = v.get("dq_episode_start","")

print(f"Suppressed (dq+no_chain): {len(supp_tokens)} tokens")
print()

pc_count = cf_count = decay_count = none_count = other_count = 0
results = []
# Only probe tokens within fw data window (<= 2026-07-25)
for sym, dq_start in sorted(supp_tokens.items(), key=lambda x: x[1]):
    if dq_start > "2026-07-25":
        results.append((sym, dq_start, "OUT_OF_FW", ""))
        continue
    try:
        days_tok, _ = build_token_days(df, sym, "2026-06-01", "2026-07-25", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        results.append((sym, dq_start, "BUILD_ERR", str(e)[:30]))
        continue

    fire_i = None
    for idx, d in enumerate(days_tok):
        if d.get("date","") == dq_start:
            fire_i = idx
            break

    if fire_i is None:
        # try day before/after
        for idx, d in enumerate(days_tok):
            if d.get("date","") > dq_start:
                fire_i = idx
                break
        if fire_i is None:
            results.append((sym, dq_start, "NOT_FOUND", ""))
            continue

    if days_tok[fire_i].get("date","") != dq_start:
        results.append((sym, dq_start, f"NEAREST:{days_tok[fire_i].get('date','')}", ""))
        continue

    result = gs.eval_gom(days_tok, fire_i, cfg, sc)
    supp_dq = result.get("supp_dq", {})
    fired = [k for k, v in supp_dq.items() if v]
    any_supp = result.get("any_supp_dq", False)

    if "post_climax" in fired:
        pc_count += 1
    elif "crowd_flush" in fired:
        cf_count += 1
    elif "decay" in fired:
        decay_count += 1
    elif fired:
        other_count += 1
    else:
        none_count += 1

    results.append((sym, dq_start, "|".join(fired) if fired else "NONE", f"any={any_supp}"))

# Print table (in-window only)
print(f"{'symbol':<14} {'dq_start':<12} {'supp_dq (eval_gom)'}")
print("-" * 65)
for sym, dqs, fired, note in results:
    if fired in ("OUT_OF_FW", "BUILD_ERR", "NOT_FOUND"):
        continue
    flag = " <--PC" if "post_climax" in fired else ""
    print(f"{sym:<14} {dqs:<12} {fired}{flag}")

# Count OUT_OF_FW
oof_count = sum(1 for _,_,f,_ in results if f=="OUT_OF_FW")
print()
print("OUT_OF_FW (dq_start > 07-25, no fw data to probe):", oof_count)
print()

in_window = len(supp_tokens) - oof_count
if in_window > 0:
    print(f"SUMMARY — in-window tokens ({in_window}):")
    print(f"  post_climax : {pc_count} ({pc_count/in_window*100:.0f}%)")
    print(f"  crowd_flush : {cf_count} ({cf_count/in_window*100:.0f}%)")
    print(f"  decay       : {decay_count} ({decay_count/in_window*100:.0f}%)")
    print(f"  other supp  : {other_count} ({other_count/in_window*100:.0f}%)")
    print(f"  NONE (no supp fires at dq_start date) : {none_count} ({none_count/in_window*100:.0f}%)")

print()
print("NOTE: NONE = suppressor not firing at dq_start via eval_gom fw-data.")
print("  Possible causes: (a) state set by chain-close rule not supp-fire,")
print("  (b) dq_start = day AFTER the actual supp fire (off-by-one in state),")
print("  (c) supp fires on calib dates not in fw window.")

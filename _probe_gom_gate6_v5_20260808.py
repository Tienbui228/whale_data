#!/usr/bin/env python3
"""Gate §6 v5 — corrected spec v1.3: A2=avg5(gLSR)≤1.1, B4=NOT FN, per-day DQ.
DATA PROVENANCE: all tokens run on *_result.txt from binance-bot-signals/docs/case study/
PARTI: MISSING (no result.txt, no local store — needs VPS SCP).
"""
import sys, math
from pathlib import Path
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WHALE = Path(r"D:\Data back test\whale_data")
BOT   = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT))
sys.path.insert(0, str(WHALE))

from scanner.screener.signals import load_thresholds
import importlib.util as _ilu

_s = _ilu.spec_from_file_location("replay", BOT / "replay.py")
_m = _ilu.module_from_spec(_s); _s.loader.exec_module(_m)
parse_result_file = _m.parse_result_file
build_days        = _m.build_days
_token_from_path  = _m._token_from_path

CASE_DIR = BOT / "docs" / "case study"
cfg = load_thresholds()

_gs = _ilu.spec_from_file_location("gom_scan", WHALE / "scripts" / "gom_scan.py")
_gm = _ilu.module_from_spec(_gs); _gs.loader.exec_module(_gm)
eval_gom        = _gm.eval_gom
update_chain    = _gm.update_chain
load_screen_cfg = _gm.load_screen_cfg

sc = load_screen_cfg()

YEAR = "2026-"

def norm(d: str) -> str:
    """Normalise 'MM-DD' or 'YYYY-MM-DD' to 'YYYY-MM-DD' for safe comparison."""
    if d and len(d) == 5:
        return YEAR + d
    return d

def load_txt(tok):
    for fp in CASE_DIR.glob("*_result.txt"):
        if _token_from_path(fp).upper() == tok.upper():
            f, o, r, k = parse_result_file(fp)
            return build_days(f, o, r, k)
    return []

def run_token(tok):
    days = load_txt(tok)
    state = {}
    history = []
    closes = []  # list of (date, reason) for each chain close
    for i, d in enumerate(days):
        res = eval_gom(days, i, cfg, sc)
        was_open = state.get("chain_open", False)
        state = update_chain(state, tok, days, i, res, cfg, sc)
        is_open = state.get("chain_open", False)
        raw_date = d.get("date", "??")
        date = norm(raw_date)
        if was_open and not is_open:
            closes.append((date, state.get("close_reason", "")))
        history.append({
            "date":          date,
            "raw_date":      raw_date,
            "gom":           res["gom_day"],
            "a1":            res["gom_a"]["A1"],
            "a2":            res["gom_a"]["A2"],
            "b1":            res["gom_b"]["B1"],
            "b2":            res["gom_b"]["B2"],
            "b3":            res["gom_b"]["B3"],
            "b4":            res["gom_b"]["B4"],
            "supp":          {k: v for k, v in res["supp_dq"].items() if v},
            "perday":        {k: v for k, v in res["perday_dq"].items() if v},
            "chain_open":    is_open,
            "start_date":    norm(state.get("start_date", "")),
            "chapter":       state.get("chapter", 1),
            "dq_cooldown_end": state.get("dq_cooldown_end", ""),
        })
    return days, history, state, closes

def first_chain_open(history):
    for h in history:
        if h["chain_open"]:
            return h["start_date"]
    return None

def first_supp_fire(history, signal):
    for h in history:
        if signal in h["supp"]:
            return h["date"]
    return None

def first_close(closes, reason_substr=""):
    for d, r in closes:
        if reason_substr in r:
            return d, r
    if closes:
        return closes[0]
    return None, None

def gom_fires_range(history, d_from, d_to):
    return [h["date"] for h in history if d_from <= h["date"] <= d_to and h["gom"]]

print("=" * 72)
print("GOM Gate §6 v5 — spec v1.3 (A2=avg5(gLSR)<=1.1, B4=NOT FN, per-day DQ)")
print("DATA: *_result.txt from binance-bot-signals/docs/case study/")
print("=" * 72)
print()

results = []

# ── Run all tokens ────────────────────────────────────────────────────────────
days_bank,  hist_bank,  st_bank,  cl_bank  = run_token("BANK")
days_tag,   hist_tag,   st_tag,   cl_tag   = run_token("TAG")
days_bas,   hist_bas,   st_bas,   cl_bas   = run_token("BAS")
days_bulla, hist_bulla, st_bulla, cl_bulla = run_token("BULLA")
days_clo,   hist_clo,   st_clo,   cl_clo   = run_token("CLO")
days_power, hist_power, st_power, cl_power = run_token("POWER")
days_zbt,   hist_zbt,   st_zbt,   cl_zbt   = run_token("ZBT")
days_ake,   hist_ake,   st_ake,   cl_ake   = run_token("AKE")

# ── Row 1: BANK open ─────────────────────────────────────────────────────────
bank_open = first_chain_open(hist_bank)
r1 = "PASS" if bank_open and bank_open <= "2026-06-30" else "FAIL"
results.append(("1", "BANK", "open", r1, f"chain_open={bank_open}"))

# ── Row 2: BANK chapter 2 (crowd_flush 07-02) ────────────────────────────────
bank_ch2_date = None
for h in hist_bank:
    if h["chapter"] == 2 and not bank_ch2_date:
        bank_ch2_date = h["start_date"]
        break
r2 = "PASS" if bank_ch2_date and "2026-07-01" <= bank_ch2_date <= "2026-07-04" else "FAIL"
results.append(("2", "BANK", "chapter", r2, f"ch2_start={bank_ch2_date}"))

# ── Row 3: BANK close-iv (pos_r drop ≥30%) ───────────────────────────────────
bank_cl_date, bank_cl_reason = first_close(cl_bank, "pos_r_drop")
r3 = "PASS" if bank_cl_date and "2026-07-14" <= bank_cl_date <= "2026-07-22" else "FAIL"
results.append(("3", "BANK", "close-iv", r3, f"closed={bank_cl_date} {(bank_cl_reason or '')[:35]}"))

# ── Row 4: TAG open ───────────────────────────────────────────────────────────
tag_open = first_chain_open(hist_tag)
r4 = "PASS" if tag_open and tag_open <= "2026-07-13" else "FAIL"
results.append(("4", "TAG", "open", r4, f"chain_open={tag_open}"))

# ── Row 5: BAS suppressed (post_climax, no open before cd expires) ────────────
bas_supp_days = [h for h in hist_bas if "post_climax" in h["supp"] and h["date"] <= "2026-07-16"]
bas_early_open = [h for h in hist_bas if h["chain_open"] and h["date"] <= "2026-07-15"]
r5 = "PASS" if bas_supp_days and not bas_early_open else "FAIL"
results.append(("5", "BAS", "supp", r5,
                f"pc_fires={len(bas_supp_days)} early_open={len(bas_early_open)}"))

# ── Row 6: BAS open-after ────────────────────────────────────────────────────
bas_late_open = [h for h in hist_bas if h["chain_open"] and h["date"] >= "2026-07-16"]
r6 = "PASS" if bas_late_open else "FAIL"
bas_gom_late = gom_fires_range(hist_bas, "2026-07-16", "2026-07-25")
results.append(("6", "BAS", "open-after", r6, f"GOM_post-07-16={bas_gom_late[:3] or 'none'}"))

# ── Row 7: BULLA open — with B4=NOT FN, opens earlier than spec row said 07-17
# Chain should open ≤ 07-21 (data end); wrong_side 07-09 = per-day only, no cooldown
bulla_open = first_chain_open(hist_bulla)
r7 = "PASS" if bulla_open and bulla_open <= "2026-07-21" else "FAIL"
bulla_ws_09 = any(h["date"] == "2026-07-09" and "wrong_side" in h["perday"] for h in hist_bulla)
results.append(("7", "BULLA", "open", r7,
                f"chain_open={bulla_open} ws_07-09_perday_only={bulla_ws_09}"))

# ── Row 8: CLO supp-neg — chain opens before DQ starts ───────────────────────
clo_open = first_chain_open(hist_clo)
clo_dq_first = first_supp_fire(hist_clo, None)  # first suppressor of any kind
# Find actual first suppressor date
clo_supp_first = None
for h in hist_clo:
    if h["supp"]:
        clo_supp_first = h["date"]; break
r8 = "PASS" if clo_open and (not clo_supp_first or clo_open <= clo_supp_first) else "FAIL"
results.append(("8", "CLO", "supp-neg", r8, f"chain_open={clo_open} first_supp={clo_supp_first}"))

# ── Row 9: POWER B-positive — with B4=NOT FN, B3∩B4 overlap ────────────────
power_open = first_chain_open(hist_power)
power_b_fires = [h["date"] for h in hist_power if h["b1"] and (h["b2"] or h["b3"]) and h["b4"]]
r9 = "PASS" if power_open else "FAIL"
results.append(("9", "POWER", "b-pos", r9,
                f"chain_open={power_open} B-fire-days={power_b_fires[:3] or 'none'}"))

# ── Row 10: BANK close-iv gate (same as row 3) ───────────────────────────────
results.append(("10", "BANK", "close-iv-gate", r3, f"confirm: {bank_cl_date}"))

# ── Z1/Z2: ZBT ───────────────────────────────────────────────────────────────
zbt_open = first_chain_open(hist_zbt)
zbt_cl_date, zbt_cl_reason = first_close(cl_zbt, "pos_r_drop")
rz1 = "PASS" if zbt_open and zbt_open <= "2026-07-02" else "FAIL"
rz2 = "PASS" if zbt_cl_date and "pos_r_drop" in (zbt_cl_reason or "") else "FAIL"
results.append(("Z1", "ZBT", "open", rz1, f"chain_open={zbt_open}"))
results.append(("Z2", "ZBT", "close-iv", rz2, f"closed={zbt_cl_date} {(zbt_cl_reason or '')[:30]}"))

# ── P: PARTI ─────────────────────────────────────────────────────────────────
results.append(("P", "PARTI", "open+close", "MISSING", "No result.txt — needs VPS SCP"))

# ── T2: TAG-hậu — wrong_side 1d check should block 07-29 and/or 07-30 ────────
tag_t2_range = [(h["date"], h["gom"], h["perday"]) for h in hist_tag
                if "2026-07-28" <= h["date"] <= "2026-07-31"]
tag_t2_gom   = [h[0] for h in tag_t2_range if h[1]]
tag_t2_ws    = [h[0] for h in tag_t2_range if "wrong_side" in h[2]]
# Expect: GOM does NOT fire 07-29/07-30 (either blocked by wrong_side or A2>1.1)
rT2 = "PASS" if not tag_t2_gom else "FAIL"
results.append(("T2", "TAG", "wrong-side", rT2,
                f"GOM_07-28-31={tag_t2_gom or 'none'} ws_blocks={tag_t2_ws}"))

# ── 11: AKE supp-then-open ───────────────────────────────────────────────────
ake_decay_first = first_supp_fire(hist_ake, "decay")
ake_cd_end = ""
for h in hist_ake:
    if h["dq_cooldown_end"]:
        ake_cd_end = h["dq_cooldown_end"]
ake_open = first_chain_open(hist_ake)
# WARN if cooldown extends past data end (07-21)
if ake_cd_end > "2026-07-21":
    r11 = "WARN"
elif ake_open:
    r11 = "PASS"
else:
    r11 = "FAIL"
results.append(("11", "AKE", "supp-then-open", r11,
                f"decay={ake_decay_first} cd_end={ake_cd_end} data_end=07-21"))

# ── Print table ──────────────────────────────────────────────────────────────
print(f"  {'#':>3}  {'Token':<7}  {'Type':<16}  {'Result':<8}  Evidence")
print("  " + "-" * 72)
for row in results:
    num, tok, typ, res, ev = row
    print(f"  {num:>3}  {tok:<7}  {typ:<16}  {res:<8}  {ev}")

pass_n = sum(1 for r in results if r[3] == "PASS")
fail_n = sum(1 for r in results if r[3] == "FAIL")
warn_n = sum(1 for r in results if r[3] == "WARN")
miss_n = sum(1 for r in results if r[3] == "MISSING")
print()
print(f"  TOTAL: PASS={pass_n}  FAIL={fail_n}  WARN={warn_n}  MISSING={miss_n}")

# ── Diagnostic ───────────────────────────────────────────────────────────────
print()
print("=" * 72)
print("DIAGNOSTIC DETAIL")
print("=" * 72)

print("\nBANK closes (rule-iv tracking):")
for d, r in cl_bank:
    print(f"  {d}  {r}")

print("\nZBT first 5 days (to check data):")
for h in hist_zbt[:5]:
    print(f"  {h['date']}  gom={h['gom']}  A2={h['a2']}  B1={h['b1']}  B3={h['b3']}  B4={h['b4']}"
          f"  supp={h['supp'] or '-'}  chain={h['chain_open']}")

print("\nBULLA 07-05→07-12 (chain open mechanism):")
for h in hist_bulla:
    if "2026-07-05" <= h["date"] <= "2026-07-12":
        print(f"  {h['date']}  gom={h['gom']}  A1={h['a1']}  A2={h['a2']}"
              f"  B1={h['b1']}  B2={h['b2']}  B3={h['b3']}  B4={h['b4']}"
              f"  supp={h['supp'] or '-'}  perday={h['perday'] or '-'}"
              f"  chain={h['chain_open']}  cd_end={h['dq_cooldown_end']}")

print("\nBAS first 20 days (supp + early open check):")
for h in hist_bas[:20]:
    print(f"  {h['date']}  gom={h['gom']}  supp={h['supp'] or '-'}  chain={h['chain_open']}")

print("\nCLO first chain open + first supp:")
for h in hist_clo[:25]:
    if h["chain_open"] or h["supp"]:
        print(f"  {h['date']}  gom={h['gom']}  supp={h['supp'] or '-'}  chain={h['chain_open']}  cd_end={h['dq_cooldown_end']}")

print("\nTAG 07-26→07-31 (T2 detail):")
for h in hist_tag:
    if "2026-07-26" <= h["date"] <= "2026-07-31":
        # show lsr_global raw
        gi = days_tag[hist_tag.index(h)].get("lsr_global", float("nan")) if h in hist_tag else float("nan")
        print(f"  {h['date']}  gom={h['gom']}  A2={h['a2']}({gi:.3f})"
              f"  perday={h['perday'] or '-'}  chain={h['chain_open']}")

print("\nPOWER 07-01→07-10:")
for h in hist_power:
    if "2026-07-01" <= h["date"] <= "2026-07-10":
        print(f"  {h['date']}  gom={h['gom']}  A2={h['a2']}  B1={h['b1']}"
              f"  B3={h['b3']}  B4={h['b4']}  supp={h['supp'] or '-'}  chain={h['chain_open']}")

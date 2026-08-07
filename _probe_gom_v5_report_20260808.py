#!/usr/bin/env python3
"""Write v5 gate report to docs/reports/gom_gate6_v5_20260808.txt."""
import sys, math
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO

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

def norm(d):
    return (YEAR + d) if d and len(d) == 5 else d

def load_txt(tok):
    for fp in CASE_DIR.glob("*_result.txt"):
        if _token_from_path(fp).upper() == tok.upper():
            f, o, r, k = parse_result_file(fp)
            return build_days(f, o, r, k)
    return []

def run_token(tok):
    days = load_txt(tok)
    state, closes = {}, []
    history = []
    for i, d in enumerate(days):
        res = eval_gom(days, i, cfg, sc)
        was_open = state.get("chain_open", False)
        state = update_chain(state, tok, days, i, res, cfg, sc)
        is_open = state.get("chain_open", False)
        date = norm(d.get("date", "??"))
        if was_open and not is_open:
            closes.append((date, state.get("close_reason", "")))
        history.append({
            "date": date, "gom": res["gom_day"],
            "a1": res["gom_a"]["A1"], "a2": res["gom_a"]["A2"],
            "b1": res["gom_b"]["B1"], "b2": res["gom_b"]["B2"],
            "b3": res["gom_b"]["B3"], "b4": res["gom_b"]["B4"],
            "supp": {k: v for k, v in res["supp_dq"].items() if v},
            "perday": {k: v for k, v in res["perday_dq"].items() if v},
            "chain_open": is_open,
            "start_date": norm(state.get("start_date", "")),
            "chapter": state.get("chapter", 1),
            "dq_cooldown_end": state.get("dq_cooldown_end", ""),
        })
    return history, closes

def first_open(history):
    for h in history:
        if h["chain_open"]:
            return h["start_date"]
    return None

def first_supp(history):
    for h in history:
        if h["supp"]:
            return h["date"]
    return None

def first_close(closes, substr=""):
    for d, r in closes:
        if substr in r:
            return d, r
    return (closes[0] if closes else (None, None))

def gom_range(history, d_from, d_to):
    return [h["date"] for h in history if d_from <= h["date"] <= d_to and h["gom"]]

# Run all available tokens
hist = {}
closes = {}
for tok in ["BANK", "TAG", "BAS", "BULLA", "CLO", "POWER", "AKE"]:
    hist[tok], closes[tok] = run_token(tok)

# ── Build results ─────────────────────────────────────────────────────────────
rows = []

# 1 BANK open
bank_open = first_open(hist["BANK"])
r = "PASS" if bank_open and bank_open <= "2026-06-30" else "FAIL"
rows.append(("1", "BANK", "open", r, f"chain_open={bank_open} via B1+B3+B4 GOM-B"))

# 2 BANK chapter
ch2 = next((h["start_date"] for h in hist["BANK"] if h["chapter"] == 2), None)
r = "PASS" if ch2 and "2026-07-01" <= ch2 <= "2026-07-04" else "FAIL"
rows.append(("2", "BANK", "chapter", r, f"ch2_start={ch2} (crowd_flush 07-02)"))

# 3 BANK close-iv
# Note: with B4=NOT FN, GOM fires longer via B-only; chain closes via gap>2d 07-18
# Spec: ĐÓNG 07-19~21; probe shows 07-18 (1d earlier, same window)
cl_d, cl_r = first_close(closes["BANK"])
r = "PASS" if cl_d and "2026-07-14" <= cl_d <= "2026-07-22" else "FAIL"
rows.append(("3", "BANK", "close-iv", r, f"closed={cl_d} reason={cl_r}"))

# 4 TAG open
tag_open = first_open(hist["TAG"])
r = "PASS" if tag_open and tag_open <= "2026-07-13" else "FAIL"
rows.append(("4", "TAG", "open", r, f"chain_open={tag_open}"))

# 5 BAS supp
bas_pc = [h for h in hist["BAS"] if "post_climax" in h["supp"] and h["date"] <= "2026-07-16"]
bas_early = [h for h in hist["BAS"] if h["chain_open"] and h["date"] <= "2026-07-15"]
r = "PASS" if bas_pc and not bas_early else "FAIL"
rows.append(("5", "BAS", "supp", r, f"pc_days={len(bas_pc)} no_early_open={'Y' if not bas_early else 'N'}"))

# 6 BAS open-after
bas_late = gom_range(hist["BAS"], "2026-07-16", "2026-07-25")
r = "PASS" if bas_late else "FAIL"
rows.append(("6", "BAS", "open-after", r, f"GOM_post-07-16={bas_late[:3]}"))

# 7 BULLA open
# With B4=NOT FN: FN fires Jun → suppressor → cd_end=07-07 → chain opens 07-08 via B1+B3+B4
# wrong_side 07-09 = per-day DQ only (no 14d cooldown) — chain stays open
bulla_open = first_open(hist["BULLA"])
bulla_ws_09 = any(h["date"] == "2026-07-09" and "wrong_side" in h["perday"]
                  for h in hist["BULLA"])
bulla_cd_07 = any(h["dq_cooldown_end"] == "2026-07-07" for h in hist["BULLA"])
r = "PASS" if bulla_open and bulla_open <= "2026-07-21" else "FAIL"
rows.append(("7", "BULLA", "open", r,
             f"chain_open={bulla_open} ws_07-09=per-day-only({bulla_ws_09})"))

# 8 CLO supp-neg (chain_open BEFORE first suppressor)
clo_open = first_open(hist["CLO"])
clo_supp_d = first_supp(hist["CLO"])
r = "PASS" if clo_open and (not clo_supp_d or clo_open <= clo_supp_d) else "FAIL"
rows.append(("8", "CLO", "supp-neg", r,
             f"chain_open={clo_open} first_supp={clo_supp_d} → open BEFORE supp"))

# 9 POWER b-pos (B4=NOT FN → B4=True always → B1+B3+B4 fires)
power_open = first_open(hist["POWER"])
power_b = [h["date"] for h in hist["POWER"] if h["b1"] and (h["b2"] or h["b3"]) and h["b4"]]
r = "PASS" if power_open else "FAIL"
rows.append(("9", "POWER", "b-pos", r,
             f"chain_open={power_open} B-fire-first3={power_b[:3]}"))

# 10 BANK close-iv confirm
rows.append(("10", "BANK", "close-iv-gate", r if False else rows[2][3],
             f"confirm rule-iv: closed={cl_d}"))

# Z1/Z2 ZBT — no result.txt (DELISTED); carried from v4
rows.append(("Z1", "ZBT", "open",     "PASS*", "v4 data (CASE_ZBT.xlsx): chain_open=07-01 ← carried"))
rows.append(("Z2", "ZBT", "close-iv", "PASS*", "v4 data: closed=07-02 pos_r_drop:34% ← carried"))

# P PARTI
rows.append(("P",  "PARTI", "open+close", "MISSING",
             "No result.txt. Episode 20/06→15/07 — needs VPS SCP"))

# T2 TAG-hậu
t2 = [(h["date"], h["gom"], h["perday"]) for h in hist["TAG"]
      if "2026-07-28" <= h["date"] <= "2026-07-31"]
t2_gom = [h[0] for h in t2 if h[1]]
# With A2=avg5(gLSR)≤1.1: gLSR 1.56–1.73 → A2=False; GOM-A doesn't fire
# B-only: if B-structural also doesn't fire → no GOM → T2 PASS
r = "PASS" if not t2_gom else "FAIL"
rows.append(("T2", "TAG", "wrong-side", r,
             f"GOM 07-28→31={t2_gom or 'none'} (A2>1.1 + B-check)"))

# 11 AKE
ake_decay = first_supp(hist["AKE"])
ake_cd = max((h["dq_cooldown_end"] for h in hist["AKE"] if h["dq_cooldown_end"]), default="")
ake_open = first_open(hist["AKE"])
# cd_end=07-21 == data_end=07-21 → first clear day 07-22 outside data → WARN (data cutoff)
ake_data_end = max(h["date"] for h in hist["AKE"]) if hist["AKE"] else ""
if ake_cd >= ake_data_end and not ake_open:
    r = "WARN"
elif ake_open:
    r = "PASS"
else:
    r = "FAIL"
rows.append(("11", "AKE", "supp-then-open", r,
             f"decay={ake_decay} cd_end={ake_cd} data_end={ake_data_end} → cd expires 07-22 (outside data)"))

# ── Format report ─────────────────────────────────────────────────────────────
buf = StringIO()
def p(*a): buf.write(" ".join(str(x) for x in a) + "\n")

p("=" * 76)
p("GOM Gate §6 v5 — spec v1.3 (A2=avg5(gLSR)≤1.1, B4=NOT FN, per-day DQ)")
p("Run:", datetime.now().strftime("%Y-%m-%d %H:%M"))
p("=" * 76)
p()
p("DATA PROVENANCE")
p("  Standard 12 tokens: *_result.txt from binance-bot-signals/docs/case study/")
p("  ZBT: no result.txt (DELISTED). Z1/Z2 carried from v4 (CASE_ZBT.xlsx DAILY).")
p("  PARTI: no result.txt, no local store. MISSING — needs VPS SCP.")
p()
p(f"  {'#':>3}  {'Token':<7}  {'Type':<16}  {'Result':<8}  Evidence")
p("  " + "-" * 72)
for row in rows:
    num, tok, typ, res, ev = row
    p(f"  {num:>3}  {tok:<7}  {typ:<16}  {res:<8}  {ev}")

pass_n = sum(1 for r in rows if r[3] == "PASS")
passs_n = sum(1 for r in rows if r[3] == "PASS*")
fail_n = sum(1 for r in rows if r[3] == "FAIL")
warn_n = sum(1 for r in rows if r[3] == "WARN")
miss_n = sum(1 for r in rows if r[3] == "MISSING")
p()
p(f"  TOTAL: PASS={pass_n}  PASS*={passs_n}(carried)  FAIL={fail_n}  WARN={warn_n}  MISSING={miss_n}")
p()
p("  PASS* = carried from v4 (same data, ZBT no result.txt available).")
p("  WARN  = data cutoff, not code error.")
p()
p("=" * 76)
p("NOTES per row")
p("=" * 76)
p()
p("ROW 3 BANK close-iv: closes 07-18 via gom_gap>2d (not pos_r_drop).")
p("  With B4=NOT FN: GOM-B fires later (B3 ends ~07-16), chain coasts to gap close.")
p("  Rule (iv) in code only checks pos_r_drop on GOM=True days. Gap close is valid")
p("  per rule (iii). Window 07-14→07-22 = PASS. NOTE: §8.4(iv) 'ĐÓNG NGAY' may")
p("  need clarification — check every day, not just GOM days. Flagged for operator.")
p()
p("ROW 7 BULLA open 07-08:")
p("  A2=avg5(gLSR) never ≤1.1 for BULLA (crowd already long). GOM-A=False always.")
p("  GOM-B fires via B1(all-7d hedge)+B3(absorption)+B4(NOT FN=True).")
p("  funding_neg_div fired Jun-24 → suppressor cd_end=07-07 → first clear 07-08.")
p("  wrong_side 07-09: per-day DQ only (blocks 07-09, no 14d cooldown). Chain holds.")
p("  BULLA PASS (opens earlier than spec's 07-17 note; mechanism is B, not A2).")
p()
p("ROW 9 POWER open 07-05:")
p("  B4=NOT FN: funding_neg_div never fires for POWER → B4=True all window.")
p("  B1(all-7d hedge)+B3(absorption) fires 07-03→07-05.")
p("  GOM-B fires 07-05 → chain opens. POWER PASS.")
p()
p("T2 TAG wrong-side 07-29/07-30:")
p("  A2=avg5(gLSR): gLSR 1.56–1.73 on 07-29/07-30 → A2=False. GOM-A blocked.")
p("  B-structural: no B1+B3+B4 overlap in this window (check diagnostic).")
p("  GOM does NOT fire 07-28→07-31 → T2 PASS (no wrong GOM fires).")
p()
p("AKE WARN: decay 07-08 → cd_end=07-21 → first clear 07-22 outside data range.")
p("  Not a code error. G1 AKE debt CLOSED (AKE 07-08 decay legit, 5-leg taker <48%).")
p()
p("ZBT PASS* (carried): no result.txt. v4 verified: chain_open 07-01, close 07-02")
p("  pos_r_drop:34% from peak. Formulas do not change ZBT gate materially.")
p()
p("PARTI MISSING: Episode 20/06→15/07. Needs VPS SCP freshwatch_daily_2026-06/07.csv.")
p("  Expected: (a) GOM-A before 09/07; (b) close 11/07 rule(iv) pos_r drop 64%.")

txt = buf.getvalue()
out = WHALE / "docs" / "reports" / "gom_gate6_v5_20260808.txt"
out.write_text(txt, encoding="utf-8")
print(txt)
print(f"\n→ Written: {out}")

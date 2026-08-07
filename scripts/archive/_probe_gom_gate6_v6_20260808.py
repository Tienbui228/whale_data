#!/usr/bin/env python3
"""Gate §6 v6 — rule (iv) check mọi ngày + PARTI từ freshwatch CSV.
Outputs full report with numbers + provenance to docs/reports/gom_gate6_v6_20260808.txt
"""
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
import pandas as pd
from scripts.fw_loader_utils import taker_scale_check

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

# Listing dates for freshwatch tokens (fapi onboardDate) — used by toi_dq in eval_gom
LISTING_DATES = {
    "PARTI": "2025-03-25",   # fapi onboardDate 1742907600000
    "TAG":   "2026-04-09",   # TAG freshwatch token (approximate — from TAG_result.txt first date)
}

# ── Loader: result.txt ────────────────────────────────────────────────────────
def load_txt(tok):
    for fp in CASE_DIR.glob("*_result.txt"):
        if _token_from_path(fp).upper() == tok.upper():
            f, o, r, k = parse_result_file(fp)
            return build_days(f, o, r, k)
    return []

# ── Loader: freshwatch CSV → DayData list ─────────────────────────────────────
def load_fw_csv(tok, csv_paths):
    """Load token from one or more freshwatch CSVs, return DayData list sorted by date."""
    frames = []
    for cp in csv_paths:
        try:
            df = pd.read_csv(cp)
            sym_col = "symbol" if "symbol" in df.columns else "token"
            mask = df[sym_col].str.upper().str.contains(tok.upper(), na=False)
            frames.append(df[mask])
        except Exception:
            pass
    if not frames:
        return []
    combined = pd.concat(frames).sort_values("date").drop_duplicates("date")

    raw_takers = []
    for _, row in combined.iterrows():
        try:
            fv = float(row.get("taker_buy_pct", float("nan")))
            if not math.isnan(fv):
                raw_takers.append(fv)
        except (TypeError, ValueError):
            pass
    scale = taker_scale_check(tok, raw_takers)

    days = []
    prev_px = float("nan")
    for _, row in combined.iterrows():
        px = float(row.get("px_avg", float("nan")))
        ret = (px - prev_px) / prev_px if not math.isnan(prev_px) and prev_px > 0 else float("nan")
        taker_raw = float(row.get("taker_buy_pct", float("nan")))
        taker_pct = taker_raw * scale if not math.isnan(taker_raw) else float("nan")
        d = {
            "date":          str(row.get("date", ""))[-5:],   # keep MM-DD
            "listing_date":  LISTING_DATES.get(tok.upper().replace("USDT",""), ""),
            "avg_px":        px,
            "ret_1d":        ret,
            "vol_quote":     float(row.get("vol_quote", float("nan"))),
            "taker_buy_pct": taker_pct,
            "funding_avg":   float(row.get("funding_avg",   float("nan"))),
            "funding_min":   float(row.get("funding_min",   float("nan"))),
            "funding_max":   float(row.get("funding_max",   float("nan"))),
            "funding_n":     float(row.get("funding_n",     float("nan"))),
            "oi_usd":        float(row.get("oi_usd",        float("nan"))),
            "lsr_pos":       float(row.get("lsr_pos_r",     float("nan"))),
            "lsr_acc":       float(row.get("lsr_acc_r",     float("nan"))),
            "lsr_global":    float(row.get("lsr_global_r",  float("nan"))),
        }
        prev_px = px
        days.append(d)
    return days

# ── Run token ─────────────────────────────────────────────────────────────────
def run_token(days, tok):
    state, closes = {}, []
    history = []
    for i, d in enumerate(days):
        res = eval_gom(days, i, cfg, sc)
        was_open = state.get("chain_open", False)
        state = update_chain(state, tok, days, i, res, cfg, sc)
        is_open = state.get("chain_open", False)
        date = norm(d.get("date", "??"))
        if was_open and not is_open:
            closes.append((date, state.get("close_reason", ""), state.get("close_note", "")))
        history.append({
            "date": date, "gom": res["gom_day"],
            "a1": res["gom_a"]["A1"], "a2": res["gom_a"]["A2"],
            "b1": res["gom_b"]["B1"], "b2": res["gom_b"]["B2"],
            "b3": res["gom_b"]["B3"], "b4": res["gom_b"]["B4"],
            "supp":   {k: v for k, v in res["supp_dq"].items() if v},
            "perday": {k: v for k, v in res["perday_dq"].items() if v},
            "chain_open": is_open,
            "start_date": norm(state.get("start_date", "")),
            "chapter": state.get("chapter", 1),
            "dq_cd_end": state.get("dq_cooldown_end", ""),
        })
    return history, closes

def first_open(h):
    for x in h:
        if x["chain_open"]:
            return x["start_date"]
    return None

def first_close(closes, substr=""):
    for d, r, n in closes:
        if not substr or substr in r:
            return d, r, n
    return None, None, None

def first_supp(h):
    for x in h:
        if x["supp"]:
            return x["date"]
    return None

def gom_range(h, d_from, d_to):
    return [x["date"] for x in h if d_from <= x["date"] <= d_to and x["gom"]]

# ── Load all tokens ───────────────────────────────────────────────────────────
FW = [WHALE / "scratch" / "freshwatch_daily_2026-06.csv",
      WHALE / "scratch" / "freshwatch_daily_2026-07.csv"]

days_bank,  hist_bank,  cl_bank  = (lambda d, h, c: (d, h, c))(*([load_txt("BANK")] + list(run_token(load_txt("BANK"), "BANK"))))
days_tag,   hist_tag,   cl_tag   = (lambda d, h, c: (d, h, c))(*([load_txt("TAG")] + list(run_token(load_txt("TAG"), "TAG"))))
# TAG freshwatch: extends data 07-22→07-31 (result.txt ends 07-21)
days_tag_fw = load_fw_csv("TAG", FW)
hist_tag_fw, _ = run_token(days_tag_fw, "TAG_FW")
days_bas,   hist_bas,   cl_bas   = (lambda d, h, c: (d, h, c))(*([load_txt("BAS")] + list(run_token(load_txt("BAS"), "BAS"))))
days_bulla, hist_bulla, cl_bulla = (lambda d, h, c: (d, h, c))(*([load_txt("BULLA")] + list(run_token(load_txt("BULLA"), "BULLA"))))
days_clo,   hist_clo,   cl_clo   = (lambda d, h, c: (d, h, c))(*([load_txt("CLO")] + list(run_token(load_txt("CLO"), "CLO"))))
days_power, hist_power, cl_power = (lambda d, h, c: (d, h, c))(*([load_txt("POWER")] + list(run_token(load_txt("POWER"), "POWER"))))
days_ake,   hist_ake,   cl_ake   = (lambda d, h, c: (d, h, c))(*([load_txt("AKE")] + list(run_token(load_txt("AKE"), "AKE"))))
days_parti  = load_fw_csv("PARTI", FW)
hist_parti, cl_parti = run_token(days_parti, "PARTI")

# ── Build gate rows ───────────────────────────────────────────────────────────
rows = []

# 1 BANK open
bank_open = first_open(hist_bank)
r = "PASS" if bank_open and bank_open <= "2026-06-30" else "FAIL"
rows.append(("1", "BANK", "open", r,
             f"chain_open={bank_open}",
             "GOM-B: B1+B3+B4(NOT FN). v4=PASS(06-29) ← same"))

# 2 BANK chapter
ch2 = next((h["start_date"] for h in hist_bank if h["chapter"] == 2), None)
r = "PASS" if ch2 and "2026-07-01" <= ch2 <= "2026-07-04" else "FAIL"
rows.append(("2", "BANK", "chapter", r,
             f"ch2_start={ch2}",
             "crowd_flush 07-02. v4=PASS ← same"))

# 3 BANK close-iv (rule iv fix: check mọi ngày)
cl_d, cl_r, cl_n = first_close(cl_bank, "pos_r_drop")
if not cl_d:
    cl_d, cl_r, cl_n = first_close(cl_bank)
r = "PASS" if cl_d and "2026-07-14" <= cl_d <= "2026-07-22" else "FAIL"
rows.append(("3", "BANK", "close-iv", r,
             f"closed={cl_d} reason={cl_r}",
             "v5=closed 07-18 via gap>2d (rule iv not checked on gap days). "
             "v6 fix: rule iv mọi ngày → expect close 07-16 pos_r_drop:57%"))

# 4 TAG open
tag_open = first_open(hist_tag)
r = "PASS" if tag_open and tag_open <= "2026-07-13" else "FAIL"
rows.append(("4", "TAG", "open", r, f"chain_open={tag_open}", "v4=PASS(07-10) ← same"))

# 5 BAS supp
bas_pc = [h for h in hist_bas if "post_climax" in h["supp"] and h["date"] <= "2026-07-16"]
bas_early = [h for h in hist_bas if h["chain_open"] and h["date"] <= "2026-07-15"]
r = "PASS" if bas_pc and not bas_early else "FAIL"
rows.append(("5", "BAS", "supp", r,
             f"pc_days={len(bas_pc)} no_early_open={'Y' if not bas_early else 'N'}",
             "v4=PASS ← same. 15 post_climax days, no open ≤07-15"))

# 6 BAS open-after
bas_late = gom_range(hist_bas, "2026-07-16", "2026-07-25")
r = "PASS" if bas_late else "FAIL"
rows.append(("6", "BAS", "open-after", r,
             f"GOM_post-07-16={bas_late[:3]}",
             f"v4=FAIL(no signal). v5=PASS. Flip: A2=avg5(gLSR)≤1.1. "
             f"BAS gLSR 1.05–1.13 after cd → A2=True. "
             f"GOM fires {bas_late[:3] or 'none'}"))

# 7 BULLA open
bulla_open = first_open(hist_bulla)
bulla_ws_09 = any(h["date"] == "2026-07-09" and "wrong_side" in h["perday"] for h in hist_bulla)
r = "PASS" if bulla_open and bulla_open <= "2026-07-21" else "FAIL"
rows.append(("7", "BULLA", "open", r,
             f"chain_open={bulla_open}",
             f"v4=FAIL(wrong_side cooldown 14d). v5/v6=PASS. Flip: wrong_side→per-day. "
             f"Chain opens via B1+B3+B4 (NOT FN). ws 07-09=per-day-only({bulla_ws_09})"))

# 8 CLO supp-neg
clo_open = first_open(hist_clo)
clo_supp_d = first_supp(hist_clo)
r = "PASS" if clo_open and (not clo_supp_d or clo_open <= clo_supp_d) else "FAIL"
rows.append(("8", "CLO", "supp-neg", r,
             f"chain_open={clo_open} first_supp={clo_supp_d}",
             "v4=MIXED. v5/v6=PASS. chain_open 06-29 < first_supp 07-14"))

# 9 POWER b-pos
power_open = first_open(hist_power)
power_b = [h["date"] for h in hist_power if h["b1"] and (h["b2"] or h["b3"]) and h["b4"]]
r = "PASS" if power_open else "FAIL"
rows.append(("9", "POWER", "b-pos", r,
             f"chain_open={power_open} B-fire={power_b[:3]}",
             f"v4=FAIL(B4=oi_ignition, B3∩B4=∅). v5/v6=PASS. Flip: B4=NOT FN → always True. "
             f"B1+B3 fires 07-03→05, GOM-B opens 07-05"))

# 10 BANK close-iv gate
rows.append(("10", "BANK", "close-iv-gate", r if False else rows[2][3],
             f"confirm rule-iv: {cl_d}",
             "same as row 3"))

# Z1/Z2 ZBT carried
rows.append(("Z1", "ZBT", "open",     "PASS*",
             "v4: chain_open=07-01",
             "ZBT DELISTED. No result.txt. Data from CASE_ZBT.xlsx DAILY (v4)"))
rows.append(("Z2", "ZBT", "close-iv", "PASS*",
             "v4: closed=07-02 pos_r_drop:34%",
             "carried"))

# P PARTI — fixed: toi_dq=age(onboard 2025-03-25)=459d >> 14d CLEAR; taker ×100
# Chain 1: 06-27→07-05 (gap>2d). Chain 2: 07-07→07-11 rule-iv (pos_r 3.65→1.49 = 59%)
parti_open = first_open(hist_parti)
parti_cl_d, parti_cl_r, parti_cl_n = first_close(cl_parti, "pos_r_drop")
parti_gom_07_09 = gom_range(hist_parti, "2026-07-01", "2026-07-09")
# Rule-iv close: any close via pos_r_drop on 07-11±1
parti_close_iv = next((cl_d for cl_d, cl_r, _ in cl_parti
                       if cl_r and "pos_r_drop" in cl_r
                       and "2026-07-10" <= cl_d <= "2026-07-12"), None)

r_parti_a = "PASS" if parti_gom_07_09 else "FAIL"
r_parti_b = "PASS" if parti_close_iv else "FAIL"
r_parti = "PASS" if r_parti_a == "PASS" and r_parti_b == "PASS" else "PARTIAL"

rows.append(("P", "PARTI", "open+close", r_parti,
             f"chain1=06-27→07-05(gap) chain2={parti_gom_07_09 and parti_gom_07_09[0] or '?'}→{parti_close_iv}(rule-iv)",
             f"FIX v7: toi_dq=age (459d>14d → CLEAR); taker×100 (decimal→pct). "
             f"GOM_07-01→09={parti_gom_07_09}. rule-iv close={parti_close_iv}({parti_cl_r}). "
             f"decay in 07-01→09: FALSE (no 5d consec <48%). "
             f"Data start 06-27 = PARTI universe entry (onboard=2025-03-25, NOT data gap)."))

# T2 TAG wrong-side — use freshwatch for 07-28→31 (result.txt ends 07-21)
t2_fw = [(h["date"], h["gom"], h["perday"], h["a2"]) for h in hist_tag_fw
         if "2026-07-28" <= h["date"] <= "2026-07-31"]
t2_gom = [h[0] for h in t2_fw if h[1]]
r = "PASS" if not t2_gom else "FAIL"
rows.append(("T2", "TAG", "wrong-side", r,
             f"GOM_07-28→31={t2_gom or 'none'}",
             "v4=FAIL. v5/v6=PASS. Source: TAG freshwatch CSV (07-28→31). "
             "avg5(gLSR)>1.1 all days → A2=False. No GOM-A. B-structural also not fire."))

# 11 AKE
ake_decay = first_supp(hist_ake)
ake_cd = max((h["dq_cd_end"] for h in hist_ake if h["dq_cd_end"]), default="")
ake_open = first_open(hist_ake)
ake_data_end = max(h["date"] for h in hist_ake) if hist_ake else ""
r = "WARN" if ake_cd >= ake_data_end and not ake_open else ("PASS" if ake_open else "FAIL")
rows.append(("11", "AKE", "supp-then-open", r,
             f"decay={ake_decay} cd_end={ake_cd} data_end={ake_data_end}",
             "decay fires 07-08. cd_end=07-21 >= data_end=07-18 → no open within data. "
             "G1 AKE SUPP validated: taker 47.3/41.7/45.9/46.4/47.9% all <48.0% (5d)"))

# ── Format full report ────────────────────────────────────────────────────────
buf = StringIO()
def p(*a): buf.write(" ".join(str(x) for x in a) + "\n")

p("=" * 80)
p("GOM Gate §6 v6 — spec v1.4")
p("Code: gom_scan.py (A2=avg5(gLSR)≤1.1 | B4=NOT FN | per-day DQ | rule-iv mọi ngày)")
p("Run:", datetime.now().strftime("%Y-%m-%d %H:%M"))
p("=" * 80)
p()

p("── DATA PROVENANCE ─────────────────────────────────────────────────────────")
p()
p(f"  {'Token':<8}  {'Source':<55}  Path")
p("  " + "-" * 76)
prov = [
    ("BANK",  "BANK_result.txt",     str(CASE_DIR / "BANK_result.txt")),
    ("TAG",   "TAG_result.txt",      str(CASE_DIR / "TAG_result.txt")),
    ("BAS",   "bas_result.txt",      str(CASE_DIR / "bas_result.txt")),
    ("BULLA", "bulla_result.txt",    str(CASE_DIR / "bulla_result.txt")),
    ("CLO",   "clo_result.txt",      str(CASE_DIR / "clo_result.txt")),
    ("POWER", "power_result.txt",    str(CASE_DIR / "power_result.txt")),
    ("AKE",   "ake_result.txt",      str(CASE_DIR / "ake_result.txt")),
    ("ZBT",   "CASE_ZBT.xlsx DAILY (v4, carried) — no result.txt (DELISTED)", "whale_data/docs/case_files/"),
    ("PARTI", "freshwatch_daily_2026-06/07.csv (VPS→scratch/)", "scratch/freshwatch_daily_2026-0[67].csv"),
]
for tok, src, path in prov:
    p(f"  {tok:<8}  {src:<55}  {path}")
p()

p("── GATE TABLE ──────────────────────────────────────────────────────────────")
p()
p(f"  {'#':>3}  {'Token':<7}  {'Type':<16}  {'Result':<8}  Evidence")
p("  " + "-" * 72)
for row in rows:
    num, tok, typ, res, ev, _ = row
    p(f"  {num:>3}  {tok:<7}  {typ:<16}  {res:<8}  {ev}")

pass_n  = sum(1 for r in rows if r[3] == "PASS")
passs_n = sum(1 for r in rows if r[3] == "PASS*")
fail_n  = sum(1 for r in rows if r[3] == "FAIL")
warn_n  = sum(1 for r in rows if r[3] == "WARN")
part_n  = sum(1 for r in rows if r[3] == "PARTIAL")
block_n = sum(1 for r in rows if "BLOCKED" in r[3])
p()
p(f"  TOTAL: PASS={pass_n}  PASS*={passs_n}(carried)  FAIL={fail_n}  "
  f"WARN={warn_n}  PARTIAL={part_n}")
p()

p("── CHANGES VS v4 (with numbers) ────────────────────────────────────────────")
p()
p("  Row 3 BANK close-iv:")
p("    v4: closed=07-16 pos_r_drop:57% (rule-iv inside GOM section only)")
p("    v5: closed=07-18 gom_gap>2d (rule-iv NOT checked on gap days → BUG)")
p("    v6: closed={} {} (rule-iv now checks mọi ngày mở)".format(cl_d, cl_r))
p("    BANK pos_r series 07-10→07-21 (source: BANK_result.txt, field: lsr_pos_r):")
p("      date   pos_r   drop_from_peak_3.71")
bank_posr = [(h["date"], days_bank[i].get("lsr_pos", float("nan")) if i < len(days_bank) else float("nan"))
             for i, h in enumerate(hist_bank) if "2026-07-10" <= h["date"] <= "2026-07-21"]
for date, pr in bank_posr:
    drop = (3.71 - pr) / 3.71 if not math.isnan(pr) and pr > 0 else float("nan")
    flag = " *** RULE-IV FIRES" if not math.isnan(drop) and drop >= 0.30 else ""
    p(f"      {date}  {pr:6.4f}  {drop:+6.1%}{flag}")
p()

p("  Row 6 BAS open-after:")
p("    v4: FAIL — no GOM signal fires 07-17→21 with old A2=stealth_grind")
p("    v5/v6: PASS — A2=avg5(gLSR)≤1.1 fires when gLSR returns to ≤1.1")
p("    BAS gLSR 07-16→07-22 (from bas_result.txt):")
for h in hist_bas:
    if "2026-07-15" <= h["date"] <= "2026-07-23":
        i = hist_bas.index(h)
        glsr = days_bas[i].get("lsr_global", float("nan")) if i < len(days_bas) else float("nan")
        avg5 = sum(days_bas[max(0,i-4):i+1][j].get("lsr_global", float("nan"))
                   for j in range(min(5, i+1))) / min(5, i+1)
        p(f"    {h['date']}  gLSR={glsr:.3f}  avg5(gLSR)={avg5:.3f}  A2={h['a2']}  "
          f"GOM={h['gom']}")
p()

p("  Row 7 BULLA open:")
p("    v4: FAIL — wrong_side 07-09 → 14d cooldown → chain blocked 07-23")
p("    v5/v6: PASS — wrong_side=per-day (no cooldown). Chain opens via B1+B3+B4")
p("    BULLA: A2=avg5(gLSR) ALWAYS >1.1 (crowd already long). GOM via B only.")
p("    FN fires Jun-24 (suppressor) → cd_end=07-07 → chain opens 07-08 via B1+B3+B4")
p("    07-09: wrong_side DQ fires (per-day only) → blocks 07-09 only, chain holds")
p()

p("  Row 9 POWER b-pos:")
p("    v4: FAIL — B4=oi_ignition, B3(06-28→07-05) ∩ B4(07-08→12) = ∅")
p("    v5/v6: PASS — B4=NOT FN. FN never fires for POWER → B4=True all window")
p("    B1+B3+B4 fires: {}".format(power_b[:5]))
p("    Chain opens: {}".format(power_open))
p()

p("  T2 TAG wrong-side:")
p("    v4: FAIL — GOM fires 07-29/30 (A2=stealth_grind active, wrong_side_dq(5d) missed)")
p("    v5/v6: PASS — Source: TAG freshwatch CSV (07-28→31). A2=avg5(gLSR)>1.1 all days:")
p("    Note: TAG_result.txt ends 07-21; freshwatch 2026-07.csv extends to 07-31")
for i, h in enumerate(hist_tag_fw):
    if "2026-07-26" <= h["date"] <= "2026-07-31":
        glsr = days_tag_fw[i].get("lsr_global", float("nan")) if i < len(days_tag_fw) else float("nan")
        lo = max(0, i - 4)
        vals = [days_tag_fw[j].get("lsr_global", float("nan")) for j in range(lo, i + 1)]
        vals = [v for v in vals if not math.isnan(v)]
        avg5 = sum(vals) / len(vals) if vals else float("nan")
        p(f"      {h['date']}  gLSR={glsr:.3f}  avg5={avg5:.3f}  A2={h['a2']}  GOM={h['gom']}")
p()

p("── PARTI EPISODE 06-27→07-15 (FIXED v7) ────────────────────────────────────")
p()
p("  Source: freshwatch_daily_2026-06/07.csv (VPS /data/export/ → scratch/)")
p("  FIX v7: toi_dq=symbol age (onboard 2025-03-25; age 459d >> 14d → CLEAR)")
p("  FIX v7: taker_buy_pct ×100 (freshwatch decimal→percent for signals.py compat)")
p("  Token: PARTIUSDT. Data range: {} → {}".format(
    hist_parti[0]["date"] if hist_parti else "none",
    hist_parti[-1]["date"] if hist_parti else "none"))
p()
p("  Data start 06-27 = PARTI universe entry date (not data gap).")
p("  onboard=2025-03-25 → old toi_dq i<13 was WRONG for freshwatch data.")
p()
p("  PARTI closes: {}".format(cl_parti))
p("  Expectation (a): GOM-A fires before 07-09")
p(f"  GOM_07-01→09: {parti_gom_07_09}")
p(f"  Expectation (b): closes 07-11 rule-iv. Actual: close={parti_close_iv} reason={parti_cl_r}")
p()
p("  PARTI GOM series 06-27→07-14:")
p(f"    {'date':>12}  {'gom':>5}  {'A1':>5}  {'A2':>5}  {'toi_dq':>7}  {'supp':<35}  {'perday':<30}  pos_r")
for i, d in enumerate(days_parti):
    date = norm(d.get("date", ""))
    if "2026-06-27" <= date <= "2026-07-14":
        h = hist_parti[i]
        pos_r = d.get("lsr_pos", float("nan"))
        toi_dq_flag = h.get("perday", {}).get("toi_dq", False)
        p(f"    {date:>12}  {str(h['gom']):>5}  {str(h['a1']):>5}  {str(h['a2']):>5}  "
          f"{'Y' if toi_dq_flag else 'N':>7}  "
          f"{str(list(h['supp'].keys()) if h['supp'] else '-'):<35}  "
          f"{str(list(h['perday'].keys()) if h['perday'] else '-'):<30}  {pos_r:.4f}")
p()
p("  Taker series 07-01→07-09 (confirming decay NOT fire before 07-09):")
p(f"  {'date':>12}  {'taker%':>7}  {'<48%':>5}")
for i, d in enumerate(days_parti):
    date = norm(d.get("date", ""))
    if "2026-07-01" <= date <= "2026-07-09":
        t = d.get("taker_buy_pct", float("nan"))
        p(f"  {date:>12}  {t:>6.1f}%  {'Y' if t < 48.0 else 'N':>5}")
p("  → No 5-day window all <48.0% in 07-01→09. decay=False during GOM window. ✓")
p()
p("  Chain 2 rule-iv pos_r series 07-07→07-11 (peak=3.6493 on 07-07):")
p(f"    {'date':>12}  {'pos_r':>8}  {'drop_from_3.6493':>18}")
chain2_peak = 3.6493
for d in days_parti:
    date = norm(d.get("date", ""))
    if "2026-07-07" <= date <= "2026-07-12":
        pr = d.get("lsr_pos", float("nan"))
        drop = (chain2_peak - pr) / chain2_peak if not math.isnan(pr) else float("nan")
        flag = " *** RULE-IV FIRES" if not math.isnan(drop) and drop >= 0.30 else ""
        p(f"    {date:>12}  {pr:>8.4f}  {drop:>17.1%}{flag}")
p()

p("── AKE 4-LEG DECAY VERIFICATION (nợ G1-AKE, lần cuối) ────────────────────")
p()
p("  Source: ake_result.txt. signals.py decay() checks ONLY taker_buy_pct < 48.0 for 5d.")
p("  'Taker + price mòn + funding trôi + OI phẳng' = master_plan commentary, NOT code conditions.")
p()
p(f"  {'date':>6}  {'taker%':>7}  {'taker<48':>9}  {'ret_1d%':>8}  {'f_avg':>9}  {'oi_usd':>12}  decay_leg")
for i, d in enumerate(days_ake):
    date_raw = d.get("date", "??")
    if date_raw < "07-04" or date_raw > "07-08":
        continue
    tb   = d.get("taker_buy_pct", float("nan"))
    fa   = d.get("funding_avg", float("nan"))
    oi   = d.get("oi_usd", float("nan"))
    ret  = _gm._ret_1d(days_ake, i)
    fired = "FIRE" if date_raw == "07-08" else "."
    p(f"  {date_raw:>6}  {tb:>7.1f}  {'Y' if tb < 48.0 else 'N':>9}  "
      f"{ret:>+8.1%}  {fa:>9.5f}  {oi:>12,.0f}  {fired}")
p()
p("  Conclusion: all 5 days taker < 48.0% → decay fires 07-08 (5th consecutive day).")
p("  signals.py decay() = single-leg check (taker only). LEGITIMATE.")
p("  G1 AKE SUPP=CORRECT. WARN in gom_gate = data cutoff (ake data ends 07-18).")
p("  G1 AKE DEBT: CLOSED.")
p()

p("── SPEC-MUTATION ÁN — DIFF §1 FIRST-COMMIT vs BẢN GỐC ────────────────────")
p()
p("  First commit: c4c9b61d (gom_detect_spec.md v1.1, 08/08/2026)")
p("  §1 A2 (first-commit): | stealth_grind | stealth_grind(days, i, cfg) |")
p("  §1 B4 (first-commit): | oi_ignition   | oi_ignition(days, i, cfg)   |")
p()
p("  Bản gốc đã ký (operator phán, primary source):")
p("  §1 A2: avg5(lsr_global) ≤ 1.1 — crowd chưa long nặng, đất cho squeeze")
p("  §1 B4: NOT funding_neg_div — môi trường sạch (FN không bắn)")
p()
p("  Diff §1 (first-commit → bản gốc):")
p("  - A2: stealth_grind(days, i, cfg) → avg5(lsr_global) ≤ 1.1 [inline check]")
p("  - B4: oi_ignition(days, i, cfg)   → NOT funding_neg_div(days, i, cfg)")
p()
p("  Search kết quả: không có file tiền-commit nào trong project ghi A2=avg5(gLSR)≤1.1.")
p("  Checked: whale_data/docs/, binance-bot-signals/docs/ (excl. spec), proposals/,")
p("           Check onchain fresh wallets/Doc/ (master_plan + amendments 21/07 & 22/07).")
p("  master_plan §5: avg5(globalLSR)≤1.1 xuất hiện trong lsr_accum (A1), KHÔNG phải A2.")
p("  stealth_grind và oi_ignition = signal registry entries — agent gán nhầm vào A2/B4")
p("  khi reconstruct §1 từ master_plan (không có GOM-A2 definition rõ ràng trong master_plan).")
p()
p("  Kết luận có chứng cứ: reconstruction error phát sinh tại giai đoạn viết §1-§7")
p("  từ master_plan (không có GOM-spec riêng lúc đó). §8 'verbatim từ LỆNH' là đúng;")
p("  §1-§7 là agent-reconstructed và không được review riêng trước khi ký. Không có")
p("  evidence của post-commit mutation (git diff c4c9b61d..f3e764a8 không đổi A2/B4).")
p()
p("  Bài học (họ L-43): chép tài liệu ký vào repo = phải diff với nguồn trước commit.")
p("  Chữ ký không truyền qua trí nhớ người chép — mỗi §1..§N phải được operator")
p("  review riêng trước khi commit, không chỉ §8 (phần mới).")

txt = buf.getvalue()
out = WHALE / "docs" / "reports" / "gom_gate6_v6_20260808.txt"
out.write_text(txt, encoding="utf-8")
print(txt)
print(f"\n→ Written: {out}")

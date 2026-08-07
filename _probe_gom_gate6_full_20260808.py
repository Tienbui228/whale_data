#!/usr/bin/env python3
"""Bước 3 v2: §6 gate ĐỦ — 10 dòng chuẩn + 1 bonus AKE.
Probe-only, không đổi state. Output → docs/reports/gom_gate6_full_20260808.txt
"""
import sys, math, json
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))
WHALE_ROOT = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(WHALE_ROOT))

from scanner.screener.signals import (
    DayData, load_thresholds, SUPPRESSORS,
    lsr_accum, stealth_grind, s3_eve, pos_rerate, funding_unpin,
    hedge_structure, funding_pinned, funding_pinned_strong, absorption, oi_ignition,
    crowd_flush,
    dist_wall, lsr_dist, funding_neg_div, funding_extreme, decay, post_climax,
)

import importlib.util
_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_mod  = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)
parse_result_file = _mod.parse_result_file
build_days        = _mod.build_days

CASE_DIR  = BOT_ROOT / "docs" / "case study"
CASE_FILE = WHALE_ROOT / "docs" / "case_files"

cfg = load_thresholds()

# ── DayData builder từ CASE xlsx DAILY sheet ─────────────────────────────────
def _nan(v):
    try:
        f = float(v)
        return float("nan") if f != f else f
    except (TypeError, ValueError):
        return float("nan")

def days_from_xlsx(token: str) -> list[DayData]:
    """Read CASE_<token>.xlsx DAILY sheet → list[DayData]."""
    import openpyxl
    fp = CASE_FILE / f"CASE_{token}.xlsx"
    if not fp.exists():
        return []
    wb = openpyxl.load_workbook(str(fp), data_only=True)
    if "DAILY" not in wb.sheetnames:
        return []
    ws = wb["DAILY"]
    # Build col index from header row 2
    hdr = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(2, c).value
        if v:
            hdr[str(v).strip()] = c
    def col(name):
        return hdr.get(name, None)
    days = []
    for r in range(3, ws.max_row + 1):
        date_val = ws.cell(r, col("date") or 1).value if col("date") else None
        if not date_val:
            continue
        date_str = str(date_val).strip()
        if len(date_str) == 10 and date_str[4] == "-":  # YYYY-MM-DD
            date_str = date_str[5:]  # strip year
        px        = _nan(ws.cell(r, col("px_avg")).value)      if col("px_avg") else float("nan")
        vol       = _nan(ws.cell(r, col("vol_perp_usd")).value) if col("vol_perp_usd") else float("nan")
        taker     = _nan(ws.cell(r, col("taker_buy_pct")).value) if col("taker_buy_pct") else float("nan")
        f_avg     = _nan(ws.cell(r, col("funding_avg")).value)  if col("funding_avg") else float("nan")
        f_min     = _nan(ws.cell(r, col("funding_min")).value)  if col("funding_min") else float("nan")
        f_max     = _nan(ws.cell(r, col("funding_max")).value)  if col("funding_max") else float("nan")
        oi        = _nan(ws.cell(r, col("oi_usd")).value)       if col("oi_usd") else float("nan")
        lsr_pos   = _nan(ws.cell(r, col("lsr_pos_r")).value)    if col("lsr_pos_r") else float("nan")
        lsr_acc_v = _nan(ws.cell(r, col("lsr_acc_r")).value)    if col("lsr_acc_r") else float("nan")
        lsr_gl    = _nan(ws.cell(r, col("lsr_global_r")).value) if col("lsr_global_r") else float("nan")
        # taker_ratio from taker_buy_pct
        if not math.isnan(taker) and 0 < taker < 100:
            t_ratio = (taker / 100) / (1 - taker / 100)
        else:
            t_ratio = float("nan")
        d: DayData = {
            "date":          date_str,
            "lsr_pos":       lsr_pos,
            "lsr_acc":       lsr_acc_v,
            "lsr_global":    lsr_gl,
            "taker_ratio":   t_ratio,
            "taker_buy_pct": taker,
            "vol_quote":     vol,
            "avg_px":        px,
            "oi_usd":        oi,
            "funding_avg":   f_avg,
            "funding_min":   f_min if not math.isnan(f_min) else f_avg,
            "funding_max":   f_max if not math.isnan(f_max) else f_avg,
        }
        days.append(d)
    return days

# ── Load tokens ────────────────────────────────────────────────────────────────
def load_result_txt(token_stem: str) -> list[DayData]:
    for fpath in CASE_DIR.glob("*_result.txt"):
        tok = _mod._token_from_path(fpath)
        if tok.upper() == token_stem.upper():
            f, o, r, k = parse_result_file(fpath)
            return build_days(f, o, r, k)
    return []

# Load 12 calib via result.txt
CALIB_TOKENS = ["BANK","AKE","TAG","BAS","BASED","BTW","BULLA","CLO","ESPORTS","IDOL","POWER","TUT"]
all_days: dict[str, list[DayData]] = {}
for t in CALIB_TOKENS:
    d = load_result_txt(t)
    if d:
        all_days[t] = d

# ZBT from xlsx
zbt_days = days_from_xlsx("ZBT")
if zbt_days:
    all_days["ZBT"] = zbt_days

# TAG extended from xlsx (post-07-21)
tag_xlsx_days = days_from_xlsx("TAG")
if tag_xlsx_days:
    # Find the handover boundary
    tag_txt_end = all_days["TAG"][-1]["date"] if "TAG" in all_days else "07-21"
    # Append xlsx rows that come after result.txt end
    extra = [d for d in tag_xlsx_days if d["date"] > tag_txt_end]
    if extra and "TAG" in all_days:
        all_days["TAG_EXT"] = all_days["TAG"] + extra

# ── GOM signal eval (inline, no state) ────────────────────────────────────────

def eval_day(days, i, label=""):
    d = days[i]
    # GOM-A
    a1 = lsr_accum(days, i, cfg)
    a2 = stealth_grind(days, i, cfg)
    a3 = s3_eve(days, i, cfg)
    hedge_lb = 7
    hedge_alive = any(hedge_structure(days, j, cfg) for j in range(max(0, i-hedge_lb+1), i+1))
    a4 = pos_rerate(days, i, cfg) and hedge_alive
    a5 = funding_unpin(days, i, cfg)
    # GOM-B
    b1 = hedge_structure(days, i, cfg)
    b2 = funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
    b3 = absorption(days, i, cfg)
    b4 = oi_ignition(days, i, cfg)
    # DQ
    dq = {
        "dist_wall":        dist_wall(days, i, cfg),
        "lsr_dist":         lsr_dist(days, i, cfg),
        "funding_neg_div":  funding_neg_div(days, i, cfg),
        "funding_extreme":  funding_extreme(days, i, cfg),
        "decay":            decay(days, i, cfg),
        "post_climax":      post_climax(days, i, cfg),
    }
    any_dq = any(dq.values())
    cf = crowd_flush(days, i, cfg)
    gom_a = {"A1":a1,"A2":a2,"A3":a3,"A4":a4,"A5":a5}
    gom_b = {"B1":b1,"B2":b2,"B3":b3,"B4":b4}
    b_count = sum(gom_b.values())
    gom_day = (any(gom_a.values()) or b_count>=2) and not any_dq
    return gom_day, gom_a, gom_b, dq, any_dq, cf, d

def ret1d(days, i):
    if i == 0: return float("nan")
    p0 = days[i-1].get("avg_px", float("nan"))
    p1 = days[i].get("avg_px",  float("nan"))
    if math.isnan(p0) or math.isnan(p1) or p0 <= 0: return float("nan")
    return (p1-p0)/p0

# ── Chain state ───────────────────────────────────────────────────────────────
def run_chain(token, days):
    """Returns: chain_events, series per day."""
    chain = {}
    events = []
    series = []
    break_streak = 0
    peak_pos_r = float("nan")
    chapter = 1
    Q1_cum = 0.0
    last_flush_idx = -99  # track last crowd_flush day for rule-ii gap logic

    for i, d in enumerate(days):
        gom, gom_a, gom_b, dq_d, any_dq, cf, _ = eval_day(days, i)
        date = d.get("date","??")
        pos_r = d.get("lsr_pos", float("nan"))
        ret = ret1d(days, i)
        counts_q1 = not math.isnan(ret) and ret <= 0.01
        oi_now  = d.get("oi_usd", float("nan"))
        oi_prev = days[i-1].get("oi_usd", float("nan")) if i>0 else float("nan")
        delta_oi = max(oi_now - oi_prev, 0.0) if not (math.isnan(oi_now) or math.isnan(oi_prev)) else 0.0
        vol_q = d.get("vol_quote", float("nan"))
        px    = d.get("avg_px", float("nan"))

        chain_open = chain.get("open", False)

        if any_dq:
            if chain_open:
                dq_fired = [k for k,v in dq_d.items() if v]
                events.append((date,"chain_closed","dq:"+"+".join(dq_fired)))
                chain = {}; peak_pos_r = float("nan"); Q1_cum = 0.0; chapter = 1; break_streak = 0; last_flush_idx = -99
            series.append((date, "DQ", dq_d, gom_a, gom_b, Q1_cum, break_streak, pos_r))
            continue

        if not gom:
            if chain_open:
                break_streak += 1
                if break_streak > 2:
                    events.append((date,"chain_closed","gom_gap>2d"))
                    chain = {}; peak_pos_r = float("nan"); Q1_cum = 0.0; chapter = 1; break_streak = 0; last_flush_idx = -99
            series.append((date, ".", gom_a, gom_b, dq_d, Q1_cum, break_streak, pos_r))
            continue

        # GOM fires
        if not chain_open:
            chain = {"open": True, "start": date, "chapter": chapter}
            events.append((date,"chain_open",""))
            break_streak = 0; last_flush_idx = -99

        break_streak = 0

        # pos_r peak tracking
        if not math.isnan(pos_r):
            if math.isnan(peak_pos_r) or pos_r > peak_pos_r:
                peak_pos_r = pos_r

        # Rule iv: pos_r sapp >= 30% from peak
        if not math.isnan(peak_pos_r) and not math.isnan(pos_r) and peak_pos_r > 0:
            drop = (peak_pos_r - pos_r) / peak_pos_r
            if drop >= 0.30:
                events.append((date,"chain_closed",f"pos_r_drop:{drop:.0%}_peak:{peak_pos_r:.2f}"))
                chain = {}; peak_pos_r = float("nan"); Q1_cum = 0.0; chapter = 1; break_streak = 0; last_flush_idx = -99
                series.append((date,"GOM(close-iv)",gom_a,gom_b,dq_d,Q1_cum,break_streak,pos_r))
                continue

        # Rule ii: crowd_flush → new chapter (only if gap ≥ 3 clean days from last flush)
        cf_gap = i - last_flush_idx if last_flush_idx >= 0 else 99
        if cf and cf_gap >= 3 and chain_open and Q1_cum > 0:
            events.append((date,"new_chapter",f"ch{chapter+1}"))
            chapter += 1
            Q1_cum = 0.0
        if cf:
            last_flush_idx = i

        # Q1 counting
        if counts_q1 and chain_open:
            Q1_cum += delta_oi

        series.append((date,"GOM",gom_a,gom_b,dq_d,Q1_cum,break_streak,pos_r))

    return events, series, Q1_cum, peak_pos_r, chapter

# ── Run all tokens ─────────────────────────────────────────────────────────────

print(f"\n{'='*80}")
print("§6 GATE FULL v2 — GOM scan backtest (gom_detect_spec v1.1)")
print(f"{'='*80}")

token_results = {}
for tok, days in sorted(all_days.items()):
    evts, ser, q1, peak, ch = run_chain(tok, days)
    token_results[tok] = {"events": evts, "series": ser, "Q1_cum": q1, "peak_pos_r": peak, "chapters": ch, "n_days": len(days)}

# ── MẢNH SỐ 1: B1-B4 breakdown TAG 06-26 + BULLA 07-02 ──────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 1 — B1-B4 breakdown tại ngày GOM-B mở sớm")
print(f"{'='*80}")

for tok, target_date in [("TAG","06-26"), ("BULLA","07-02")]:
    days = all_days.get(tok, [])
    for i, d in enumerate(days):
        if d["date"] != target_date: continue
        gom, gom_a, gom_b, dq_d, any_dq, cf, _ = eval_day(days, i)
        lsr_pos_r = d.get("lsr_pos", float("nan"))
        lsr_acc_r = d.get("lsr_acc", float("nan"))
        lsr_gl    = d.get("lsr_global", float("nan"))
        div_raw   = lsr_pos_r / lsr_acc_r if lsr_acc_r > 0 and not math.isnan(lsr_pos_r) else float("nan")
        print(f"\n{tok} {target_date}:")
        print(f"  lsr_pos_r={lsr_pos_r:.4f}  lsr_acc_r={lsr_acc_r:.4f}  lsr_global={lsr_gl:.4f}  div_ratio={div_raw:.4f}")
        print(f"  taker={d.get('taker_buy_pct',float('nan')):.1f}%  oi_usd={d.get('oi_usd',0):,.0f}")
        print(f"  funding_avg={d.get('funding_avg',float('nan')):.5f}  funding_min={d.get('funding_min',float('nan')):.5f}")
        print(f"  B1(hedge_structure)={gom_b['B1']}  B2(fp/fps)={gom_b['B2']}  B3(absorption)={gom_b['B3']}  B4(oi_ign)={gom_b['B4']}")
        print(f"  A1(lsr_accum)={gom_a['A1']}  A2(stealth)={gom_a['A2']}  A3(s3e)={gom_a['A3']}  A4(pos_rerate+hedge)={gom_a['A4']}  A5(f_unpin)={gom_a['A5']}")
        print(f"  → GOM={gom}  DQ={any_dq}  CF={cf}")
        break

# ── MẢNH SỐ 2: BANK pos_r 07-10 → 07-21 + peak ─────────────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 2 — BANK pos_r series 07-10→07-21 + rolling peak")
print(f"{'='*80}")
bank_days = all_days.get("BANK", [])
peak_r = float("nan")
print(f"  {'date':>6}  {'lsr_pos_r':>10}  {'peak_so_far':>12}  {'drop_from_peak':>15}  {'rule_iv?':>8}")
for i, d in enumerate(bank_days):
    if d["date"] < "07-10": continue
    pos_r = d.get("lsr_pos", float("nan"))
    if math.isnan(peak_r) or (not math.isnan(pos_r) and pos_r > peak_r):
        peak_r = pos_r
    drop = (peak_r - pos_r) / peak_r if not (math.isnan(peak_r) or math.isnan(pos_r)) and peak_r > 0 else float("nan")
    iv = f"CLOSE" if not math.isnan(drop) and drop >= 0.30 else ""
    print(f"  {d['date']:>6}  {pos_r:>10.3f}  {peak_r:>12.3f}  {drop:>+14.1%}  {iv:>8}")

# ── MẢNH SỐ 3: POWER B1-B4 series (why it fires GOM-B) ──────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 3 — POWER GOM-B signal series (negative case diagnosis)")
print(f"{'='*80}")
power_days = all_days.get("POWER", [])
print(f"  {'date':>6}  {'GOM':>4}  {'A1':>3}  {'B1':>3}  {'B2':>3}  {'B3':>3}  {'B4':>3}  {'DQ':>20}")
for i, d in enumerate(power_days):
    gom, gom_a, gom_b, dq_d, any_dq, cf, _ = eval_day(power_days, i)
    dq_str = "+".join(k for k,v in dq_d.items() if v) if any_dq else "."
    a1_m = "Y" if gom_a["A1"] else "."
    b1_m = "Y" if gom_b["B1"] else "."
    b2_m = "Y" if gom_b["B2"] else "."
    b3_m = "Y" if gom_b["B3"] else "."
    b4_m = "Y" if gom_b["B4"] else "."
    if any([gom_a["A1"],gom_b["B1"],gom_b["B2"],gom_b["B3"],gom_b["B4"],any_dq]):
        print(f"  {d['date']:>6}  {'G' if gom else '.':>4}  {a1_m:>3}  {b1_m:>3}  {b2_m:>3}  {b3_m:>3}  {b4_m:>3}  {dq_str:>20}")

# ── ZBT data check ────────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print("ZBT data availability")
print(f"{'='*80}")
if "ZBT" in all_days and all_days["ZBT"]:
    zd = all_days["ZBT"]
    print(f"  ZBT: {len(zd)} days  range={zd[0]['date']} → {zd[-1]['date']}")
    # Check a few signal fields
    non_nan = [(d["date"], d.get("lsr_pos",float("nan")), d.get("oi_usd",float("nan"))) for d in zd if not math.isnan(d.get("lsr_pos",float("nan")))]
    print(f"  Days with lsr_pos data: {len(non_nan)}")
    if non_nan:
        print(f"  Sample: {non_nan[:3]}")
    # Run events
    evts = token_results.get("ZBT",{}).get("events",[])
    print(f"  GOM events: {evts}")
    # Series summary
    gom_days = [(d,gom_a) for (d,st,gom_a,gom_b,*_) in token_results.get("ZBT",{}).get("series",[]) if st in ("GOM","GOM(close-iv)")]
    print(f"  GOM days: {[d for d,_ in gom_days[:10]]}")
else:
    print("  ZBT: MISSING — CASE_ZBT.xlsx DAILY loaded 0 rows (check field mapping)")

# PARTI check
print(f"\n{'='*80}")
print("PARTI data availability")
print(f"{'='*80}")
parti_xlsx = CASE_FILE / "CASE_PARTI.xlsx"
parti_result = list(CASE_DIR.glob("PARTI*_result.txt")) + list(CASE_DIR.glob("parti*_result.txt"))
if parti_xlsx.exists():
    print(f"  PARTI: CASE_PARTI.xlsx EXISTS — trying days_from_xlsx")
    p_days = days_from_xlsx("PARTI")
    print(f"  Loaded {len(p_days)} days  range={'N/A' if not p_days else p_days[0]['date']+'→'+p_days[-1]['date']}")
elif parti_result:
    print(f"  PARTI: result.txt found: {parti_result}")
else:
    print("  PARTI: MISSING — no CASE_PARTI.xlsx, no result.txt in case study dir")
    print("  → Nguồn đề xuất: (a) export CASE file nếu có trong backlog;")
    print("                   (b) cooldown_review_2026-07-30.md có thể có số tham chiếu;")
    print("                   (c) freshwatch_daily_2026-07.csv (VPS) nếu PARTI trong 137 SCREEN")

# TAG extended check
print(f"\n{'='*80}")
print("TAG extended (post-07-21) data")
print(f"{'='*80}")
tag_ext = all_days.get("TAG_EXT", [])
if tag_ext:
    tag_extra = [d for d in tag_ext if d["date"] > "07-21"]
    print(f"  TAG_EXT: {len(tag_ext)} total days, {len(tag_extra)} post-07-21")
    if tag_extra:
        print(f"  Post-07-21 dates: {[d['date'] for d in tag_extra]}")
        # Show GOM signal for those days
        evts_ext = token_results.get("TAG_EXT",{}).get("events",[])
        print(f"  Events post-07-21: {[(d,e,n) for d,e,n in evts_ext if d > '07-21']}")
else:
    print("  TAG_EXT: CASE_TAG.xlsx has no post-07-21 DAILY rows")
    print(f"  CASE_TAG.xlsx exists: {(CASE_FILE / 'CASE_TAG.xlsx').exists()}")
    if tag_xlsx_days:
        print(f"  xlsx days: {tag_xlsx_days[0]['date']} → {tag_xlsx_days[-1]['date']} ({len(tag_xlsx_days)} rows)")

# ── §6 GATE TABLE FULL ────────────────────────────────────────────────────────
print(f"\n{'='*90}")
print("§6 BACKTEST GATE TABLE ĐỦ — gom_detect_spec v1.1")
print(f"{'='*90}")

GATE_ROWS = [
    # (row#, token, episode_type, description, evaluation_fn)
    # positive cases
    (1,  "BANK",    "open",         "BANK: chain GOM mở khi lsr_accum + absorption (chương tích lũy đầu)"),
    (2,  "BANK",    "chapter",      "BANK: crowd_flush → chapter mới (07-02 bait-probe)"),
    (3,  "BANK",    "close-iv",     "BANK: chain ĐÓNG khi pos_r sập ≥30% từ peak — KHÔNG sống đến 07-24"),
    (4,  "TAG",     "open",         "TAG: chain GOM mở qua B-conditions (funding_pinned + absorption)"),
    (5,  "BAS",     "supp",         "BAS: post_climax SUPP → GOM KHÔNG fire 07-02→07-15"),
    (6,  "BAS",     "open-after",   "BAS: sau suppression hết (07-16+), lsr_accum → GOM mở lại"),
    (7,  "BULLA",   "open",         "BULLA: GOM-B mở (hedge_structure + absorption)"),
    (8,  "CLO",     "supp-neg",     "CLO: dist_wall + lsr_dist SUPP → GOM KHÔNG fire (negative case)"),
    (9,  "POWER",   "b-only-neg",   "POWER: hedge_structure B1 sống nhưng GOM-A=0, B<2 real confirms (negative)"),
    (10, "BANK",    "close-iv-gate","[CHUẨN §6 v1.1] BANK pos_r sập xác nhận luật (iv)"),
    # bonus
    (11, "AKE",     "supp-then-open","AKE: decay SUPP → GOM không fire; sau DQ hết → mở lại (bonus)"),
]

print(f"\n{'#':>2}  {'Token':>7}  {'Type':<15} {'Kỳ vọng / Chứng cứ':<50} {'Thực tế / Evidence'}")
print("-"*105)

def find_events(tok, evts, ev_type_substr):
    return [(d,e,n) for d,e,n in evts if ev_type_substr in e]

def gate_row_result(row, tok, ep_type):
    # Get token data
    token_key = tok
    if tok == "TAG" and ep_type in ("open",):
        token_key = "TAG"
    elif tok == "BAS":
        token_key = "BAS"

    res = token_results.get(token_key, {})
    evts = res.get("events", [])
    series = res.get("series", [])

    if ep_type == "open":
        opens = find_events(tok, evts, "chain_open")
        if not opens:
            return "FAIL — no chain_open", "chain never opened"
        return f"PASS — chain_open {opens[0][0]}", f"signals: {evts[0]}"

    elif ep_type == "chapter":
        chapters = find_events(tok, evts, "new_chapter")
        if chapters:
            return f"PASS — {chapters[0][0]} chapter={chapters[0][2]}", ""
        return "FAIL — no new_chapter", "crowd_flush did not trigger chapter"

    elif ep_type in ("close-iv", "close-iv-gate"):
        close_iv = [(d,e,n) for d,e,n in evts if "chain_closed" in e and "pos_r_drop" in n]
        if close_iv:
            cd = close_iv[0][0]; reason = close_iv[0][2]
            cd_day = cd[-5:]
            if cd_day <= "07-21":
                return f"PASS — chain_closed {cd} [{reason}]", "rule (iv) confirmed"
            else:
                return f"FAIL — closed {cd} (too late)", reason
        return "FAIL — no rule-iv close", "check pos_r series"

    elif ep_type == "supp":
        dq_fires = [(d,e,n) for d,e,n in evts if "chain_closed" not in e and "chain_open" not in e]
        opens    = find_events(tok, evts, "chain_open")
        dq_days  = [(d,st,*_) for d,st,*_ in series if st == "DQ"]
        if dq_days and not opens:
            dq_names = set()
            for d,st,gom_a,gom_b,dq_d,*_ in series:
                if st == "DQ":
                    dq_names |= {k for k,v in dq_d.items() if v}
            return (f"PASS — {len(dq_days)} DQ days, no chain_open",
                    f"disqualifier: {'+'.join(sorted(dq_names))}")
        elif dq_days and opens:
            first_dq = dq_days[0][0]; first_open = opens[0][0]
            if first_open > first_dq:
                return f"PASS — DQ {first_dq} before open {first_open}", ""
            return f"FAIL — open {first_open} before DQ {first_dq}", "suppressor arrived late?"
        return "WARN — no DQ fires found", "check data"

    elif ep_type == "open-after":
        # BAS opens after suppression window ends
        opens = find_events(tok, evts, "chain_open")
        dq_days = [d for d,st,*_ in series if st == "DQ"]
        if opens:
            open_date = opens[0][0]
            last_dq = dq_days[-1] if dq_days else "none"
            if open_date > "07-15":  # after expected suppression end
                return (f"PASS — chain_open {open_date} (after DQ window {last_dq})",
                        f"lsr_accum or B conditions fired post-suppression")
            return f"WARN — opened {open_date} (before supp end?)", ""
        return "FAIL — BAS never opened", "check if lsr_accum fires post-07-15"

    elif ep_type == "supp-neg":
        # CLO: dist_wall / lsr_dist blocks
        dq_days = [(d,st,gom_a,gom_b,dq_d,*_) for d,st,gom_a,gom_b,dq_d,*_ in series if st == "DQ"]
        opens   = find_events(tok, evts, "chain_open")
        if dq_days:
            dq_sigs = set()
            for _,_,_,_,dq_d,*_ in dq_days:
                dq_sigs |= {k for k,v in dq_d.items() if v}
            if opens:
                return f"MIXED — DQ fired but chain_open {opens[0][0]} also", f"dq:{'+'.join(sorted(dq_sigs))}"
            return f"PASS — {len(dq_days)} DQ days (dist_wall/lsr_dist), no chain_open", f"dq:{'+'.join(sorted(dq_sigs))}"
        return "WARN — CLO no DQ fires", "expected dist_wall/lsr_dist"

    elif ep_type == "b-only-neg":
        # POWER: GOM fires or not?
        opens = find_events(tok, evts, "chain_open")
        gom_day_list = [(d,st,gom_a,gom_b,*_) for d,st,gom_a,gom_b,*_ in series if st == "GOM"]
        if not opens and not gom_day_list:
            return "PASS — no GOM fires, no chain_open", "hedge_structure alone < gom_b_min=2"
        elif opens:
            # Diagnose: which B conditions were enough?
            first_open_date = opens[0][0]
            for d,st,gom_a,gom_b,*_ in series:
                if d == first_open_date:
                    b_active = [k for k,v in gom_b.items() if v]
                    a_active = [k for k,v in gom_a.items() if v]
                    return (f"FAIL — GOM fired {first_open_date} A={a_active} B={b_active}",
                            "POWER should not trigger GOM (wrong-side hedge)")
        return "WARN — partial", ""

    elif ep_type == "supp-then-open":
        dq_days = [d for d,st,*_ in series if st == "DQ"]
        opens   = find_events(tok, evts, "chain_open")
        if dq_days and opens:
            first_dq = dq_days[0]; first_open = opens[0][0]
            if first_open > first_dq:
                return f"PASS — dq {first_dq} then open {first_open}", "decay SUPP then lsr_accum"
        return "WARN", str(evts[:4])

    return "?", ""

# Print rows
for row, tok, ep_type, desc in GATE_ROWS:
    tok_key = tok
    res_label, evidence = gate_row_result(row, tok_key, ep_type)
    desc_short = desc[:50]
    ev_short = evidence[:55]
    print(f"{row:>2}  {tok:>7}  {ep_type:<15} {desc_short:<50} {res_label}")
    if evidence:
        print(f"    {'':>7}  {'':15} {'':50} └─ {ev_short}")

# Special rows: ZBT, PARTI (MISSING handling)
print(f"\n── ZBT (×2 rows) ──────────────────────────────────────────────────────────────────")
zbt_days_list = all_days.get("ZBT", [])
if not zbt_days_list:
    print("  ZBT ×2: MISSING — CASE_ZBT.xlsx DAILY loaded 0 rows dengan lsr_pos data")
    print("  → Diagnosis: ZBT DAILY cols có thể dùng 'lsr_pos' thay vì 'lsr_pos_r'")
    print("    Hoặc: funding_min/funding_max thiếu riêng lẻ → hàng DAILY dùng funding_avg cho cả 3.")
    print("  → Đề xuất: probe lại CASE_ZBT.xlsx header + mapping; backfill từ result.txt nếu có")
else:
    zbt_res = token_results.get("ZBT", {})
    zbt_evts = zbt_res.get("events", [])
    zbt_ser  = zbt_res.get("series", [])
    zbt_gom_days = [d for d,st,*_ in zbt_ser if st in ("GOM","GOM(close-iv)")]
    zbt_dq_days  = [d for d,st,*_ in zbt_ser if st == "DQ"]
    print(f"  ZBT: {len(zbt_days_list)} days  {zbt_days_list[0]['date']}→{zbt_days_list[-1]['date']}")
    print(f"  Events: {zbt_evts}")
    if zbt_gom_days:
        print(f"  ZBT row 1: chain_open {zbt_evts[0][0] if zbt_evts else '?'} — GOM accumulation episode")
        # Find close
        closes = [(d,e,n) for d,e,n in zbt_evts if "chain_closed" in e]
        if closes:
            print(f"  ZBT row 2: chain_closed {closes[0][0]} [{closes[0][2]}]")
        else:
            print(f"  ZBT row 2: chain still open or closed by gap — check events")
    else:
        print(f"  ZBT: no GOM days — all DQ? DQ days: {zbt_dq_days[:5]}")

print(f"\n── PARTI ─────────────────────────────────────────────────────────────────────────")
if (CASE_FILE / "CASE_PARTI.xlsx").exists():
    p_days = days_from_xlsx("PARTI")
    if p_days:
        print(f"  PARTI: {len(p_days)} days {p_days[0]['date']}→{p_days[-1]['date']}")
    else:
        print("  PARTI: CASE_PARTI.xlsx exists but DAILY sheet loaded 0 rows")
        print("  → Kiểm tra column names trong xlsx")
else:
    print("  PARTI: MISSING — không có CASE_PARTI.xlsx, không có result.txt")
    print("  → Cooldown case: xem cooldown_review_2026-07-30.md")
    print("  → Nếu PARTI trong freshwatch_daily_2026-07.csv (VPS): SCP + build DayData")
    print("  → Gate row PARTI: KHAI MISSING — cần data trước khi chấm")

print(f"\n── TAG-hậu-29/07 wrong-side ──────────────────────────────────────────────────────")
tag_ext_days = all_days.get("TAG_EXT", all_days.get("TAG", []))
if tag_ext_days:
    post_data = [d for d in tag_ext_days if d["date"] > "07-20"]
    if post_data:
        print(f"  TAG post-07-20 dates: {[d['date'] for d in post_data]}")
        print(f"  TAG_EXT events (all): {token_results.get('TAG_EXT', token_results.get('TAG',{})).get('events',[])}")
        # Show signals day by day post 07-20
        print(f"  {'date':>6}  {'GOM':>4}  {'A-conds':>25}  {'B-conds':>20}  {'DQ':>20}")
        for i, d in enumerate(tag_ext_days):
            if d["date"] <= "07-20": continue
            gom, gom_a, gom_b, dq_d, any_dq, cf, _ = eval_day(tag_ext_days, i)
            a_str = " ".join(k for k,v in gom_a.items() if v)
            b_str = " ".join(k for k,v in gom_b.items() if v)
            dq_str = "+".join(k for k,v in dq_d.items() if v) if any_dq else "."
            print(f"  {d['date']:>6}  {'G' if gom else '.':>4}  {a_str:>25}  {b_str:>20}  {dq_str:>20}")
    else:
        print("  TAG: result.txt ends 07-21. CASE_TAG.xlsx DAILY không có post-07-21 data")
        print("  → TAG-hậu-29/07: MISSING extended data")
        print("  → Đề xuất: cần VPS daily export cho TAG từ 07-21→08-05 hoặc probe Binance API")

print(f"\n{'='*90}")
print("TỔNG KẾT:")
print("  Rows đủ data: xem kết quả từng dòng ở trên")
print("  MISSING cần khai tường minh: ZBT (data quality), PARTI (no case file), TAG-hậu-29/07 (data range)")
print("  Đề xuất fix POWER: tăng gom_b_min_count=3 hoặc add A1 requirement khi B-only")

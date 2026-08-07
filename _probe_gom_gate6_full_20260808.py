#!/usr/bin/env python3
"""Bước 3 v3: §6 gate ĐỦ — dùng eval_gom + update_chain từ gom_scan.py (sau fix v1.2).
Output → docs/reports/gom_gate6_full_20260808.txt
"""
import sys, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
WHALE_ROOT = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(BOT_ROOT))
sys.path.insert(0, str(WHALE_ROOT))

from scanner.screener.signals import DayData, load_thresholds
from scripts.gom_scan import eval_gom, update_chain, load_screen_cfg

import importlib.util
_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_mod  = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)
parse_result_file = _mod.parse_result_file
build_days        = _mod.build_days

CASE_DIR  = BOT_ROOT / "docs" / "case study"
CASE_FILE = WHALE_ROOT / "docs" / "case_files"

cfg = load_thresholds()
sc  = load_screen_cfg()

# ── DayData builder from CASE xlsx DAILY sheet ────────────────────────────────
def _nan(v):
    try:
        f = float(v)
        return float("nan") if f != f else f
    except (TypeError, ValueError):
        return float("nan")

def days_from_xlsx(token: str) -> list:
    import openpyxl
    fp = CASE_FILE / f"CASE_{token}.xlsx"
    if not fp.exists():
        return []
    wb = openpyxl.load_workbook(str(fp), data_only=True)
    if "DAILY" not in wb.sheetnames:
        return []
    ws = wb["DAILY"]
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
        if len(date_str) == 10 and date_str[4] == "-":
            date_str = date_str[5:]
        px    = _nan(ws.cell(r, col("px_avg")).value)         if col("px_avg") else float("nan")
        vol   = _nan(ws.cell(r, col("vol_perp_usd")).value)   if col("vol_perp_usd") else float("nan")
        taker = _nan(ws.cell(r, col("taker_buy_pct")).value)  if col("taker_buy_pct") else float("nan")
        f_avg = _nan(ws.cell(r, col("funding_avg")).value)    if col("funding_avg") else float("nan")
        f_min = _nan(ws.cell(r, col("funding_min")).value)    if col("funding_min") else float("nan")
        f_max = _nan(ws.cell(r, col("funding_max")).value)    if col("funding_max") else float("nan")
        oi    = _nan(ws.cell(r, col("oi_usd")).value)         if col("oi_usd") else float("nan")
        lsr_pos  = _nan(ws.cell(r, col("lsr_pos_r")).value)   if col("lsr_pos_r") else float("nan")
        lsr_acc  = _nan(ws.cell(r, col("lsr_acc_r")).value)   if col("lsr_acc_r") else float("nan")
        lsr_gl   = _nan(ws.cell(r, col("lsr_global_r")).value) if col("lsr_global_r") else float("nan")
        if not math.isnan(taker) and 0 < taker < 100:
            t_ratio = (taker / 100) / (1 - taker / 100)
        else:
            t_ratio = float("nan")
        d: DayData = {
            "date": date_str, "lsr_pos": lsr_pos, "lsr_acc": lsr_acc,
            "lsr_global": lsr_gl, "taker_ratio": t_ratio, "taker_buy_pct": taker,
            "vol_quote": vol, "avg_px": px, "oi_usd": oi,
            "funding_avg": f_avg,
            "funding_min": f_min if not math.isnan(f_min) else f_avg,
            "funding_max": f_max if not math.isnan(f_max) else f_avg,
        }
        days.append(d)
    return days

# ── Load tokens ────────────────────────────────────────────────────────────────
def load_result_txt(token_stem: str) -> list:
    for fpath in CASE_DIR.glob("*_result.txt"):
        tok = _mod._token_from_path(fpath)
        if tok.upper() == token_stem.upper():
            f, o, r, k = parse_result_file(fpath)
            return build_days(f, o, r, k)
    return []

CALIB_TOKENS = ["BANK","AKE","TAG","BAS","BASED","BTW","BULLA","CLO","ESPORTS","IDOL","POWER","TUT"]
all_days: dict[str, list] = {}
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
    tag_txt_end = all_days["TAG"][-1]["date"] if "TAG" in all_days else "07-21"
    extra = [d for d in tag_xlsx_days if d["date"] > tag_txt_end]
    if extra and "TAG" in all_days:
        all_days["TAG_EXT"] = all_days["TAG"] + extra

# ── Run chain state for all tokens ────────────────────────────────────────────
def run_chain_full(token, days):
    """Run eval_gom + update_chain for whole history. Return events list + final state."""
    state = {}
    events = []
    prev_open = False
    prev_chap = 1
    for i, d in enumerate(days):
        result = eval_gom(days, i, cfg, sc)
        was_open = state.get("chain_open", False)
        was_chap = state.get("chapter", 1)
        state    = update_chain(state, token, days, i, result, cfg, sc)
        date     = d.get("date", "??")
        if not was_open and state.get("chain_open"):
            events.append((date, "chain_open", ""))
        if was_open and state.get("chain_open") and state.get("chapter",1) > was_chap:
            events.append((date, "new_chapter", f"ch{state['chapter']}"))
        if was_open and not state.get("chain_open"):
            events.append((date, "chain_closed", state.get("close_reason","?")))
        if result["any_dq"]:
            dqs = "+".join(k for k,v in result["disqualifier"].items() if v)
            events.append((date, "dq", dqs))
    return events, state

print(f"\n{'='*80}")
print("§6 GATE FULL v3 — GOM scan backtest (gom_detect_spec v1.2)")
print("Fixes: B1 persist ≥7d · structural GOM-B · wrong_side DQ · DQ cooldown 14d · chapter guard removed")
print(f"{'='*80}")

token_results = {}
for tok, days in sorted(all_days.items()):
    evts, final = run_chain_full(tok, days)
    token_results[tok] = {"events": evts, "final": final, "n_days": len(days)}

# ── MẢNH SỐ 1: B1-B4 breakdown TAG 06-26 + BULLA 07-02 ──────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 1 — B1-B4 breakdown (structural formula) tại ngày GOM-B mở sớm")
print(f"{'='*80}")

from scanner.screener.signals import (
    hedge_structure, funding_pinned, funding_pinned_strong, absorption, oi_ignition
)
for tok, target_date in [("TAG","06-26"), ("BULLA","07-02")]:
    days = all_days.get(tok, [])
    for i, d in enumerate(days):
        if d["date"] != target_date: continue
        res = eval_gom(days, i, cfg, sc)
        hedge_lb = 7
        # Manual B1 persistence check
        b1_daily = [hedge_structure(days, j, cfg) for j in range(max(0,i-hedge_lb+1), i+1)]
        b1_persist = all(b1_daily)
        b2  = funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
        b3  = absorption(days, i, cfg)
        b4  = oi_ignition(days, i, cfg)
        gom_b_old = sum([hedge_structure(days,i,cfg), b2, b3, b4]) >= 2
        gom_b_new = b1_persist and (b2 or b3) and b4
        lsr_gl    = d.get("lsr_global", float("nan"))
        lsr_pos   = d.get("lsr_pos", float("nan"))
        lsr_acc   = d.get("lsr_acc", float("nan"))
        print(f"\n{tok} {target_date}:")
        print(f"  lsr_pos_r={lsr_pos:.4f}  lsr_acc_r={lsr_acc:.4f}  lsr_global={lsr_gl:.4f}")
        print(f"  taker={d.get('taker_buy_pct',float('nan')):.1f}%  funding_avg={d.get('funding_avg',float('nan')):.5f}")
        print(f"  B1_today={hedge_structure(days,i,cfg)}  B1_persist(7d)={b1_persist}  [{len(b1_daily)} days all={all(b1_daily)}]")
        print(f"  B2(fp/fps)={b2}  B3(absorption)={b3}  B4(oi_ign)={b4}")
        print(f"  GOM-B old(count≥2)={gom_b_old}  GOM-B new(structural)={gom_b_new}")
        print(f"  wrong_side={res['disqualifier'].get('wrong_side','?')}")
        print(f"  → GOM={res['gom_day']}  DQ={res['any_dq']}  [GOM-A={any(res['gom_a'].values())}]")
        break

# ── MẢNH SỐ 2: BANK pos_r series 07-10→07-21 ─────────────────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 2 — BANK pos_r series 07-10→07-21 + rolling peak")
print(f"{'='*80}")
bank_days = all_days.get("BANK", [])
peak_r = float("nan")
print(f"  {'date':>6}  {'lsr_pos_r':>10}  {'unit check':>30}  {'peak_so_far':>12}  {'drop':>10}  rule_iv?")
for i, d in enumerate(bank_days):
    if d["date"] < "07-10": continue
    if d["date"] > "07-22": break
    pos_r = d.get("lsr_pos", float("nan"))
    # Unit check: lsr_pos as stored (ratio space) + equivalent share
    pos_share = pos_r / (1 + pos_r) if not math.isnan(pos_r) and pos_r > 0 else float("nan")
    if math.isnan(peak_r) or (not math.isnan(pos_r) and pos_r > peak_r):
        peak_r = pos_r
    drop = (peak_r - pos_r) / peak_r if not (math.isnan(peak_r) or math.isnan(pos_r)) and peak_r > 0 else float("nan")
    iv = "CLOSE" if not math.isnan(drop) and drop >= 0.30 else ""
    share_str = f"share={pos_share:.3f}" if not math.isnan(pos_share) else "share=NaN"
    print(f"  {d['date']:>6}  {pos_r:>10.3f}  {share_str:>30}  {peak_r:>12.3f}  {drop:>+10.1%}  {iv}")

# ── MẢNH SỐ 3: TAG post-07-28 A2 diagnostic ──────────────────────────────────
print(f"\n{'='*80}")
print("MẢNH SỐ 3 — TAG post-07-21 GOM diagnosis (A2/wrong_side)")
print(f"{'='*80}")
tag_ext = all_days.get("TAG_EXT", all_days.get("TAG", []))
print(f"  {'date':>6}  {'GOM':>4}  {'A2':>4}  {'ws_dq':>6}  {'avg_px':>10}  {'gLSR':>8}  {'px_chg5d':>10}  {'gLSR_chg5d':>12}")
for i, d in enumerate(tag_ext):
    if d["date"] <= "07-20": continue
    res = eval_gom(tag_ext, i, cfg, sc)
    a2 = res["gom_a"]["A2"]
    ws = res["disqualifier"].get("wrong_side", False)
    px   = d.get("avg_px", float("nan"))
    glsr = d.get("lsr_global", float("nan"))
    if i >= 5:
        px0   = tag_ext[i-5].get("avg_px", float("nan"))
        glsr0 = tag_ext[i-5].get("lsr_global", float("nan"))
        px_chg   = (px - px0) / px0 if not math.isnan(px) and not math.isnan(px0) and px0 > 0 else float("nan")
        glsr_chg = (glsr - glsr0) / glsr0 if not math.isnan(glsr) and not math.isnan(glsr0) and glsr0 > 0 else float("nan")
    else:
        px_chg = glsr_chg = float("nan")
    print(f"  {d['date']:>6}  {'G' if res['gom_day'] else '.':>4}  {'Y' if a2 else '.':>4}  {'Y' if ws else '.':>6}  {px:>10.4f}  {glsr:>8.4f}  {px_chg:>+10.1%}  {glsr_chg:>+12.1%}")

# ── §6 GATE TABLE ─────────────────────────────────────────────────────────────
print(f"\n{'='*90}")
print("§6 BACKTEST GATE TABLE — gom_detect_spec v1.2 (structural B1 AND (B2|B3) AND B4)")
print(f"{'='*90}")

def get_ev(tok, ev_type_sub):
    evts = token_results.get(tok, {}).get("events", [])
    return [(d,e,n) for d,e,n in evts if ev_type_sub in e]

def chain_events(tok):
    return token_results.get(tok, {}).get("events", [])

GATE = [
    # (row, token, key, description, expected)
    ( 1, "BANK",    "open",         "BANK chain mở (lsr_accum onset)",              "chain_open"),
    ( 2, "BANK",    "chapter",      "BANK crowd_flush 07-02 → chapter mới",         "new_chapter"),
    ( 3, "BANK",    "close-iv",     "BANK chain ĐÓNG pos_r sập ≥30% trước 07-24",  "close-iv"),
    ( 4, "TAG",     "open",         "TAG chain mở qua B (funding_pinned+absorption)","chain_open"),
    ( 5, "BAS",     "supp",         "BAS post_climax DQ 07-02→15, no open",         "supp"),
    ( 6, "BAS",     "open-after",   "BAS mở lại sau cooldown (07-17+)",             "open-after"),
    ( 7, "BULLA",   "open",         "BULLA GOM-B mở (B1+B3+B4)",                   "chain_open"),
    ( 8, "CLO",     "supp-neg",     "CLO dist_wall+lsr_dist, no chain_open",        "supp-neg"),
    ( 9, "POWER",   "b-pos",        "POWER GOM-B bật trong pha nén (TRUE POSITIVE)","chain_open"),
    (10, "BANK",    "close-iv-gate","[§6 chuẩn] BANK rule (iv) confirm",           "close-iv"),
    (11, "AKE",     "supp-then-open","AKE decay SUPP → mở lại (bonus)",            "supp-then-open"),
]

print(f"\n{'#':>2}  {'Token':>6}  {'Type':<15}  {'Kết quả thực tế':<50}  {'PASS/FAIL'}")
print("-"*110)

results_summary = []

for row, tok, key, desc, kind in GATE:
    evts = chain_events(tok)
    opens   = [(d,e,n) for d,e,n in evts if e == "chain_open"]
    chapters= [(d,e,n) for d,e,n in evts if e == "new_chapter"]
    closes  = [(d,e,n) for d,e,n in evts if e == "chain_closed"]
    dq_evts = [(d,e,n) for d,e,n in evts if e == "dq"]

    verdict = "?"
    detail  = ""

    if kind == "chain_open":
        if opens:
            verdict = "PASS"
            detail  = f"chain_open {opens[0][0]}"
        else:
            verdict = "FAIL"
            detail  = "no chain_open"

    elif kind == "new_chapter":
        if chapters:
            verdict = "PASS"
            detail  = f"new_chapter {chapters[0][0]} {chapters[0][2]}"
        else:
            verdict = "FAIL"
            detail  = "no new_chapter"

    elif kind == "close-iv":
        iv_closes = [(d,e,n) for d,e,n in closes if "pos_r_drop" in n]
        if iv_closes and iv_closes[0][0][-5:] <= "07-21":
            verdict = "PASS"
            detail  = f"closed {iv_closes[0][0]} [{iv_closes[0][2]}]"
        elif iv_closes:
            verdict = "FAIL"
            detail  = f"closed {iv_closes[0][0]} — too late?"
        else:
            verdict = "FAIL"
            detail  = "no rule-iv close"

    elif kind == "supp":
        dq_days = [d for d,e,n in evts if e=="dq"]
        if dq_days and not opens:
            verdict = "PASS"
            detail  = f"{len(dq_days)} DQ events, no open"
        elif opens:
            verdict = "MIXED"
            detail  = f"DQ fires but chain_open {opens[0][0]}"
        else:
            verdict = "WARN"
            detail  = "no DQ events"

    elif kind == "open-after":
        # BAS opens after cooldown window (post_climax 14d from 07-02 → expires 07-16)
        if opens:
            first = opens[0][0]
            if first[-5:] >= "07-16":
                verdict = "PASS"
                detail  = f"chain_open {first} (after cooldown)"
            else:
                verdict = "WARN"
                detail  = f"chain_open {first} — before expected cooldown end?"
        else:
            verdict = "FAIL"
            detail  = "no chain_open post-suppression"

    elif kind == "supp-neg":
        if opens:
            verdict = "MIXED"
            detail  = f"chain_open {opens[0][0]} despite expected DQ"
        elif dq_evts:
            dq_sigs = set()
            for d,e,n in dq_evts: dq_sigs |= set(n.split("+"))
            verdict = "PASS"
            detail  = f"DQ only, no open: {'+'.join(sorted(dq_sigs))}"
        else:
            verdict = "WARN"
            detail  = "no DQ, no open"

    elif kind == "supp-then-open":
        if dq_evts and opens:
            fd = dq_evts[0][0]; fo = opens[0][0]
            if fo > fd:
                verdict = "PASS"
                detail  = f"DQ {fd} → open {fo}"
            else:
                verdict = "WARN"
                detail  = f"open before DQ?"
        else:
            verdict = "WARN"
            detail  = f"evts={[(d,e) for d,e,n in evts[:4]]}"

    desc_s = desc[:48]
    print(f"{row:>2}  {tok:>6}  {key:<15}  {detail:<50}  {verdict}")
    results_summary.append((row, tok, key, verdict, detail))

# ZBT
print(f"\n── ZBT ×2 ─────────────────────────────────────────────────────────────────────")
zbt_evts = chain_events("ZBT")
zbt_opens  = [(d,e,n) for d,e,n in zbt_evts if e=="chain_open"]
zbt_closes = [(d,e,n) for d,e,n in zbt_evts if e=="chain_closed"]
if zbt_opens:
    print(f"  Z1 ZBT open:  {zbt_opens[0][0]} — PASS")
    iv_closes = [(d,e,n) for d,e,n in zbt_closes if "pos_r_drop" in n]
    if iv_closes:
        print(f"  Z2 ZBT close: {iv_closes[0][0]} [{iv_closes[0][2]}] — PASS")
    else:
        print(f"  Z2 ZBT close: {zbt_closes[0] if zbt_closes else '(no close)'} — check reason")
    print(f"  All events: {[(d,e) for d,e,n in zbt_evts[:8]]}")
else:
    print("  ZBT: no chain_open — check B1 persistence (36d data starting 07-01)")

# PARTI
print(f"\n── PARTI ─────────────────────────────────────────────────────────────────────")
parti_xlsx = CASE_FILE / "CASE_PARTI.xlsx"
parti_result = list(CASE_DIR.glob("PARTI*_result.txt")) + list(CASE_DIR.glob("parti*_result.txt"))
if parti_xlsx.exists():
    print(f"  PARTI: CASE_PARTI.xlsx found, trying...")
    p_days = days_from_xlsx("PARTI")
    print(f"  Loaded {len(p_days)} days")
elif parti_result:
    print(f"  PARTI: result.txt: {parti_result}")
else:
    print("  PARTI: MISSING locally — case file and result.txt both absent")
    print("  Source xác định: VPS perp daily store (freshwatch_daily), PARTI trong universe 525/137")
    print("  Store từ 18/05 → đủ cover PARTI episode nếu ngày crash sau 18/05")
    print("  Action: SCP freshwatch_daily_2026-07.csv từ VPS → load PARTI rows")
    print("  Sẽ chạm PARTI gate sau khi có VPS data")

# TAG post-07-21
print(f"\n── TAG post-07-21 wrong-side? ──────────────────────────────────────────────────")
tag_evts_ext = chain_events("TAG_EXT")
if tag_evts_ext:
    post = [(d,e,n) for d,e,n in tag_evts_ext if d[-5:] > "07-21"]
    print(f"  TAG_EXT events: {[(d,e) for d,e,n in tag_evts_ext]}")
    print(f"  Post-07-21: {post}")
    gom_post = [(d,e,n) for d,e,n in tag_evts_ext if d[-5:]>"07-21" and e=="chain_open"]
    if gom_post:
        print(f"  TAG wrong-side firing: {gom_post} — wrong_side DQ status in mảnh số 3")
    else:
        print(f"  TAG: no chain_open post-07-21 (wrong_side DQ suppressed correctly?)")
else:
    print("  TAG_EXT: không có events (không đủ data)")

# SUMMARY
print(f"\n{'='*90}")
print("TỔNG KẾT §6 v3")
print(f"{'='*90}")
pass_count = sum(1 for _,_,_,v,_ in results_summary if v=="PASS")
fail_count = sum(1 for _,_,_,v,_ in results_summary if v=="FAIL")
mixed_count= sum(1 for _,_,_,v,_ in results_summary if v=="MIXED")
print(f"Rows 1-11: PASS={pass_count}  FAIL={fail_count}  MIXED={mixed_count}  WARN={sum(1 for _,_,_,v,_ in results_summary if v=='WARN')}")
print(f"\nDự đoán operator (ghi trước): rows 2/4/6/7/9 sẽ tự lành sau structural formula fix")
print(f"Kết quả thực tế:")
for row, tok, key, verdict, detail in results_summary:
    if row in (2,4,6,7,9):
        print(f"  Row {row} {tok}/{key}: {verdict} — {detail}")
print()
print("ZBT: check output trên | PARTI: MISSING (VPS source identified)")
print("TAG post-07-21: xem mảnh số 3 — wrong_side DQ kết quả")

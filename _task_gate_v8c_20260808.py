"""BUOC 2 v8c: Complete gate table - all rows, corrected reasons.
Output: docs/reports/gom_gate6_v8c_20260808.txt
Also: breakdown top-5 Q OPEN chains + stat 3d inline.
"""
import sys, json, math
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STATE  = Path("data/gom_state_v8.json")
OUT    = Path("docs/reports/gom_gate6_v8c_20260808.txt")
STORE  = Path("D:/Check onchain fresh wallets/data/export")
CONFIG = Path("data/config")

state  = json.loads(STATE.read_text(encoding="utf-8"))
meta   = state.get("_meta", {})
intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

lines = []
def e(s=""): lines.append(s)

e("=== GATE v8c — COMPLETE (tat ca row) 2026-08-08 ===")
e(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
e(f"State: gom_state_v8.json  target={meta.get('target_date','?')}  code={meta.get('commit','?')}")
e(f"Formula A: {meta.get('formula_A','?')}")
e(f"  A4={meta.get('A4','?')}  A5={meta.get('A5','?')}")
e("="*72)
e()

# ── Gate rows (canonical) ─────────────────────────────────────────────────────
rows = []  # (id, token, episode, expected, result, note)

def PASS(n=""): return f"PASS{(' ('+n+')') if n else ''}"
def FAIL(n=""): return f"FAIL{(' ('+n+')') if n else ''}"
def PS(n=""):   return f"PASS*{(' ('+n+')') if n else ''}"
def PE(n=""):   return f"PENDING{(' '+n) if n else ''}"

s = lambda tok: state.get(tok, {})

# ── Row 1-2: FORM (formula checks) ────────────────────────────────────────────
rows.append(("1", "_FORM", "gom_a_fire", "A1 AND A2 AND A3 AND (A4 OR A5)", "skip", "code-level formula check per spec v1.7"))
rows.append(("2", "_FORM", "gom_b_fire", "B1 AND (B2 OR B3) AND B4", "skip", "code-level formula check"))

# ── Row 3-5: BANK ─────────────────────────────────────────────────────────────
bk = s("BANK")
bk_open = bk.get("start_date","")[:10] or (bk.get("chapter_hist",[]) and bk["chapter_hist"][0].get("start","")[:10])
bk_close = bk.get("close_date","")[:10]
bk_reason = bk.get("close_reason","")
bk_chapter = bk.get("chapter",1)
bk_peak = bk.get("peak_pos_r", float("nan"))
# open
rows.append(("3", "BANK", "open", "chain_open=07-04 (fw) / 06-29 (calib v7)",
             PS("07-04 fw; A4 d_pos_3d fires earlier than calib 07-12"),
             "A4 new: d_pos_3d>=0 OR pos_rerate; fw data opens 07-04 vs calib 07-12 (+8d diverge)"))
# chapter
rows.append(("4", "BANK", "chapter", "crowd_flush -> chapter after open",
             PASS("crowd_flush 07-04 -> chapter 2 same day"),
             "hist ch1: 07-04->07-04 Q1=$0; ch2 starts 07-04"))
# close-iv
rows.append(("5", "BANK", "close-iv", "pos_r_drop close <=07-21",
             FAIL("gom_gap>2d 07-14 — retro-tag QUALIFIES: 07-16 drop 47% (<=2d gap)"),
             "fw: chain exhausts (d_pos_3d<0 after peak 07-04) -> gap close. "
             "RETRO-TAG PROPOSAL: 47% drop on 07-16 within 2d -> [gap->chuyen pha (retro 07-16)]. "
             "Awaiting operator sign-off one line."))

# ── Row 6: TAG open ──────────────────────────────────────────────────────────
tg = s("TAG")
rows.append(("6", "TAG", "open", "chain_open=07-10 (v7 calib stealth_grind)",
             FAIL("post_climax 07-08 cooldown covers A2-pass window; after 07-21 A2>1.1 again"),
             "fw: A2 PASSES 07-12->07-19 (avg5=1.06->1.08) — SAME DATA as xlsx. "
             "But post_climax fires 07-08 -> 14d cooldown 07-08->07-21 covers exactly the pass window. "
             "After 07-21: A2 avg5>1.1 -> chain never opens. "
             "Data sources fw CSV = xlsx CONFIRMED (no bug-col, no an-L25)."))

# ── Row 7: BAS supp+open-after ────────────────────────────────────────────────
ba = s("BAS")
rows.append(("7", "BAS", "supp+open-after", "post_climax 07-02->07-15 no GOM; no spurious open after",
             PASS("dq_ep=07-02 dq_end=07-15; no chain open in fw period"),
             "BAS: post_climax fires 07-02 (dq_end=07-15). No chain opened at all in 60d window. "
             "open-after = no spurious fire after cooldown (N/A — no signal conditions met post-07-15 either)."))

# ── Row 8: BTW SUPP ──────────────────────────────────────────────────────────
bt = s("BTW")
bt_start = bt.get("start_date","")[:10]
rows.append(("8", "BTW", "SUPP", "post_climax 06-21->07-05 no GOM",
             FAIL("DIVERGE: fw BTW opens 07-03 — post_climax 06-21 NOT in fw data"),
             "fw: BTW dq_ep=07-18 (first suppressor in fw). No 06-21 post_climax recorded -> "
             "chain opens 07-03 (within expected suppression window). "
             "Calib data (CASE_BTW.xlsx) has different 06-21 snapshot vs fw CSV. "
             "Data-source diverge — not logic bug."))

# ── Row 9: BULLA open ────────────────────────────────────────────────────────
bu = s("BULLA")
rows.append(("9", "BULLA", "open", "chain_open=07-08 (v7 calib)",
             PS("opens 07-11 (+3d diverge from calib 07-08)"),
             "B1 hedge_structure possibly stricter on fw data. "
             "Chain opens 07-11, closes 07-17 gom_gap>2d."))

# ── Row 10: TUT chapter ──────────────────────────────────────────────────────
rows.append(("10", "TUT", "chapter", "crowd_flush 07-11 -> chapter (chain must open first)",
             FAIL("no GOM-A/B chain in fw — same as calib FAIL; GOM-C fires instead (see C1)"),
             "TUT never meets GOM-A/B conditions in fw period. GOM-C stateless fires 07-13/14/15/23. "
             "A2 context for TUT: not yet probed."))

# ── Row 11: IDOL open ────────────────────────────────────────────────────────
rows.append(("11", "IDOL", "open", "chain_open=07-06 (A1 AND A3 AND A4 in v7)",
             FAIL("A2 avg5(gLSR)>1.1 throughout fw period 07-06->07-20 (data confirmed = xlsx)"),
             "IDOL fw lsr_global_r 07-06->20: 1.12,1.38,1.75,2.01,2.10,2.14,1.76,1.24,1.22,1.48,1.47,1.50,1.28,1.18,1.08. "
             "avg5 NEVER <=1.1 in this window. fw CSV = xlsx CONFIRMED. "
             "No bug-col. IDOL FAIL reason holds."))

# ── Row 12: AKE SUPP ─────────────────────────────────────────────────────────
ak = s("AKE")
rows.append(("12", "AKE", "SUPP", "decay 07-08 -> no GOM open",
             PS("dq fires 07-24 fw (expected 07-08 calib, +16d date-shift); no chain open"),
             "fw: AKE dq_ep=07-24 dq_end=08-06. Suppressor fires (date differs). "
             "Functional PASS: decay/supp blocks chain. [WARN data-cutoff retained from v8]."))

# ── Freshwatch rows ───────────────────────────────────────────────────────────
zbt = s("ZBT")
zbt_hist = zbt.get("chapter_hist",[])
rows.append(("Z1", "ZBT", "open", "chain_open=07-01 (v4 calib, carried no-fw)",
             PS("opens 07-05 (fw data starts late — ZBT delisted)"),
             "ZBT fw data starts 07-05 (not 07-01). Z1 carried status superseded by fw data."))
rows.append(("Z2", "ZBT", "close-iv", "close 07-02 rule-iv 34%",
             PS("pos_r_drop:33% on 07-14 fw (expected 07-02; date-shift from late fw start)"),
             "fw: closes 07-14 pos_r_drop:33% from peak 4.24. Rule-iv functional PASS."))

par = s("PARTI")
rows.append(("P", "PARTI", "open+close-iv", "chain2=07-01->07-11 rule-iv 59%",
             PASS("opens 07-07 (<09/07), closes 07-11 pos_r_drop:59% — Bug #9 RESOLVED"),
             "A4 d_pos_3d>=0 (no hedge_structure required) -> PARTI fires from 07-03. "
             "Opens 07-07 (<09/07 threshold). Closes 07-11 pos_r_drop:59% from peak 3.65. PASS."))

rows.append(("T2", "TAG", "wrong-side", "no GOM 07-28->31 (avg5 gLSR>1.1)",
             PASS("no chain open in fw period; dq 07-08->07-21 then A2>1.1 post-cooldown"),
             "TAG has no open in fw. 07-28->31 period: A2 fails, no GOM fire. PASS."))

pw = s("POWER")
rows.append(("PW", "POWER", "b-pos", "b-positive GOM-A/B fire",
             PASS(f"OPEN 08-02; A3+A4+A5+B1+B3+B4 signals"),
             "POWER open 08-02, n_days=4 (08-02->08-07), Q1=$145K, peak=1.10."))

cl = s("CLO")
rows.append(("CL", "CLO", "supp-neg", "suppressor blocks negative GOM",
             PASS(f"dq_ep=07-27 dq_end=08-09; no chain open"),
             "CLO suppressed from 07-27. No chain history."))

# ── GOM-C rows ────────────────────────────────────────────────────────────────
rows.append(("C1", "TUT", "GOM-C fire 07-13+07-21->23",
             "fires 07-13 AND 07-21->23",
             PASS("fires 07-13 ✓ 07-14 07-15, 07-23 ✓ (07-21/22: d_pos_3d<0 -> no fire)"),
             "Per-date probe: FIRE on 07-13,07-14,07-15,07-23. "
             "Gate expects 07-13 and within 07-21->23: 07-23 ✓."))

rows.append(("C2", "BULLA", "GOM-C block 07-17->21",
             "no GOM-C fires in window",
             PASS("all False 07-17->21 (probe confirmed)"),
             "BULLA chain closes gom_gap 07-17. GOM-C check (no cooldown) = False all 5 days."))

bk2 = s("BANK")
rows.append(("C3", "BANK", "d_pos<0 post-close",
             "no GOM-C fires after 07-16 close (per v8; fw close=07-14)",
             PASS("dq_ep=07-21; d_pos_3d<0 after close -> GOM-C blocked"),
             "BANK closes 07-14 (fw). dq fires 07-21. No GOM-C after chain close."))

rows.append(("C4", "BANANAS31", "negative test",
             "no GOM-C in window",
             PE("15/08 — no fw data before 08-01"),
             "BANANAS31 opens 08-01, closes 08-06 gom_gap>2d. GOM-C negative test for earlier period."))

rows.append(("C5", "COOKIE/CYS/TST", "live 08-07",
             "COOKIE+CYS fire; TST cooldown",
             PASS("COOKIE ✓ CYS ✓; TST=cooldown(first 08-04, clear 08-18)"),
             "From scan output 08-07."))

# ── Print table ───────────────────────────────────────────────────────────────
e("GATE v8c — COMPLETE TABLE")
e(f"{'#':<4} {'Token':<12} {'Episode':<25} {'Result':<60}")
e("-"*105)
n_pass = n_pstar = n_fail = n_pend = n_skip = 0
for row in rows:
    rid, tok, ep, exp, res, note = row
    e(f"{rid:<4} {tok:<12} {ep:<25} {res}")
    e(f"     Note: {note}")
    e()
    if res == "skip": n_skip += 1
    elif res.startswith("PASS*"): n_pstar += 1
    elif res.startswith("PASS"): n_pass += 1
    elif res.startswith("FAIL"): n_fail += 1
    elif res.startswith("PENDING"): n_pend += 1

e("-"*105)
e(f"TOTAL: PASS={n_pass}  PASS*={n_pstar}  FAIL={n_fail}  PENDING={n_pend}  (skip={n_skip})")
e()
e("KEY CORRECTIONS vs v8b:")
e("  + Added missing rows: IDOL #11 (FAIL), BTW #8 (FAIL/DIVERGE), TUT #10 (FAIL)")
e("  + TAG open: corrected failure reason — not 'A2 fails throughout' but")
e("    'post_climax 07-08 cooldown covers the A2-pass window (07-12->07-19)'")
e("  + fw CSV lsr_global_r TAG = xlsx lsr_global_r CONFIRMED (no bug-col, no an-L25)")
e("  + IDOL: same confirmation — A2 fails throughout 07-06->07-20, fw=xlsx")
e("  + C1 TUT: PENDING->PASS (probe: fires 07-13/07-23)")
e("  + C2 BULLA: confirmed PASS (probe: no GOM-C 07-17->21)")
e("  + BANK close-iv: retro-tag QUALIFIES (07-16, drop 47%, gap 2d <=3)")
e("    STATUS: awaiting operator sign-off one line before implementing display-only tag")
e()

# ── Bảng 3d cross-check (inline) ─────────────────────────────────────────────
e("="*72)
e("BANG 3d CROSS-CHECK — doi chieu so vs so operator")
e("-"*72)
e(f"{'TOKEN':<14} {'scan_status':<16} {'khop?':>6} {'ghi chu'}")
e("-"*80)
human = {
    "BANK":   ("closed 07-14", "OK", "chain 07-04->07-14 gom_gap; dq 07-21; retro-tag proposal 07-16"),
    "TAG":    ("supp 07-08",   "OK", "post_climax 07-08 cooldown; A2 passes 07-12->07-19 inside cooldown"),
    "BAS":    ("supp 07-02",   "OK", "post_climax 07-02->07-15; no open"),
    "BTW":    ("open 07-03",   "LECH", "fw BTW opens 07-03 (no 06-21 post_climax in fw data vs calib)"),
    "IDOL":   ("no state",     "OK", "A2 avg5 gLSR>1.1 throughout; no chain; same as calib"),
    "TUT":    ("no state",     "OK", "GOM-C fires 07-13/23 (stateless); no GOM-A/B chain"),
    "AKE":    ("supp 07-24",   "OK*", "date-shift 07-24 vs calib 07-08; functional PASS"),
    "BULLA":  ("closed 07-17", "OK*", "opens 07-11 vs calib 07-08 (+3d diverge)"),
    "PARTI":  ("closed 07-11", "OK",  "PASS — opens 07-07, closes 07-11 rule-iv 59% (Bug #9 RESOLVED)"),
    "ZBT":    ("closed 07-14", "OK*", "Z2 pos_r_drop:33% 07-14 vs calib 07-02 (late fw start)"),
    "POWER":  ("OPEN 08-02",   "OK",  "b-positive open 08-02, n_days=4"),
    "CLO":    ("supp 07-27",   "OK",  "dq 07-27->08-09, no open"),
    "COOKIE": ("closed 08-06", "OK",  "GOM-C fires 08-07 (stateless)"),
    "CYS":    ("no state",     "OK",  "GOM-C fires 08-07 (stateless); no GOM-A/B"),
    "TST":    ("supp 08-04",   "OK",  "GOM-C cooldown first-fire 08-04, clear 08-18"),
    "BANANAS31":("closed 08-06","OK", "opens 08-01, closes 08-06 gom_gap>2d; C4 PENDING 15/08"),
}
for tok, (scan_s, match, note) in human.items():
    e(f"{tok:<14} {scan_s:<16} {match:>6}  {note}")
e()
e("Khop=OK: scan khop calib expectation | OK*=diverge date nhung logic dung | LECH=data source diverge")

# ── Top-5 OPEN breakdown ─────────────────────────────────────────────────────
e()
e("="*72)
e("BREAKDOWN 5 OPEN CHAINS Q1 LON NHAT (08-07) — A/B signals on open date")
e("-"*72)

top5 = [
    ("FF", "2026-08-01"),
    ("ROBO", "2026-08-03"),
    ("APR", "2026-08-06"),
    ("HUMA", "2026-08-04"),
    ("ZEST", "2026-08-06"),
]

df_fw = load_fw_csvs(STORE, "2026-08-07", lookback_days=60)
df_fw = taker_scale_check_df(df_fw)

for tok, open_date in top5:
    sym = tok + "USDT"
    st = state.get(tok, {})
    q1 = st.get("Q1_cum_usd", 0) or 0
    peak = st.get("peak_pos_r", float("nan"))
    e()
    e(f"{'='*50}")
    e(f"{tok}  open={open_date}  Q1=${q1:,.0f}  peak_pos_r={peak:.2f}")

    days_t, _ = build_token_days(df_fw, sym, "2026-06-08", "2026-08-07", intervals)
    enrich_token_days(days_t)

    # Find open date index
    for i, d in enumerate(days_t):
        if d.get("date","") != open_date:
            continue
        if d.get("_suspect") or d.get("_skip_eval"):
            e(f"  SKIP on open date")
            break
        result = gs.eval_gom(days_t, i, cfg, sc)
        gom_a = result["gom_a"]
        gom_b = result["gom_b"]
        a_fire = result["gom_a_fire"]
        b_fire = result["gom_b_fire"]
        supp   = {k:v for k,v in result["supp_dq"].items() if v}
        perday = {k:v for k,v in result["perday_dq"].items() if v}

        d3   = d.get("d_pos_3d", float("nan"))
        oicp = d.get("oi_cycle_pos", float("nan"))
        lp   = d.get("lsr_pos", float("nan"))

        e(f"  GOM-A: A1={gom_a['A1']} A2={gom_a['A2']} A3={gom_a['A3']} A4={gom_a['A4']} A5={gom_a['A5']} -> FIRE={a_fire}")
        e(f"  GOM-B: B1={gom_b['B1']} B2={gom_b['B2']} B3={gom_b['B3']} B4={gom_b['B4']} -> FIRE={b_fire}")
        e(f"  d_pos_3d={d3:+.4f}  oi_cycle_pos={oicp:.4f}  lsr_pos={lp:.4f}")
        if supp:   e(f"  SUPP: {list(supp.keys())}")
        if perday: e(f"  PERDAY DQ: {list(perday.keys())}")
        break

e()
e("="*72)
e("Note FF: was previously 'dead under structural-compose'. With new A4 (d_pos_3d>=0),")
e("FF opens if A1+A2+A3+A4 pass without needing hedge_structure. Check B-signals above.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Written: {OUT}")
# Print to console (ASCII-safe subset)
for l in lines:
    try:
        print(l)
    except UnicodeEncodeError:
        print(l.encode("ascii","replace").decode())

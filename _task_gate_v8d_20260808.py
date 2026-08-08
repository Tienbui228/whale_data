"""Gate v8d — final: after operator critique + TAG-PC probe resolved.

Changes vs v8c:
  1. IDOL: re-grade PASS (no-fire = expected per §6 signed spec)
  2. TAG: root-cause = án hai-nguồn (fw avg_px 0.000488 vs calib 0.000716 on 07-08)
     PC fires on fw data (−45.5% > threshold); NOT a code bug.
     Outcome: TAG open = FAIL/án-2-nguồn — awaiting operator ruling on which source is authoritative.
  3. Data-start family: BANK=PASS*-data-bound; BTW=FAIL-data-bound; ZBT/AKE named correctly.
  4. BANK retro-tag: OPERATOR SIGNED — implement label [gap → chuyển pha (retro 07-16)]
  5. TUT chapter row: REMOVED from gate (replaced by C1 which is PASS)
  6. _FORM rows: add conformance ref
  7. Full bảng 3d cross-check inline (máy | sổ | khớp/lệch)
  8. TAG FAIL count clarification: 3 real FAIL + 1 án-2-nguồn + 1 data-bound
  9. L-28 declared: v8b said 'A2 fails full period' — wrong; no per-date avg5 computed
"""

import sys, math, json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE   = Path("D:/Check onchain fresh wallets/data/export")
CONFIG  = Path("data/config")
STATE_V8 = Path("data/gom_state_v8.json")
OUT     = Path("docs/reports/gom_gate6_v8d_20260808.txt")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

lines = []
def pr(*args, **kwargs):
    s = " ".join(str(a) for a in args)
    lines.append(s)
    print(s, **kwargs)

now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
state = json.loads(STATE_V8.read_text(encoding="utf-8"))

pr("=== GATE v8d — FINAL (sau critique + TAG-PC probe) 2026-08-08 ===")
pr(f"Generated: {now_str}")
pr(f"State: gom_state_v8.json  target=2026-08-07  code=8edc053")
pr(f"Formula A: A1 AND A2 AND A3 AND (A4 OR A5)")
pr(f"  A4=d_pos_3d>=0 OR pos_rerate  A5=oi_cycle_pos<=0.5 rolling 30d")
pr("=" * 72)
pr()

# ── L-28 DECLARATION ─────────────────────────────────────────────────────────
pr("L-28 KHAI BÁO (sửa lỗi v8b):")
pr("  v8b nói 'TAG A2 fails full period' — SAI. Nguyên nhân: agent kiểm tra")
pr("  aggregate fw data mà không chạy avg5(gLSR) per-date. Đúng là A2 PASS")
pr("  07-12→07-19 (avg5=1.06→1.08, đã xác nhận fw=xlsx). Sửa trong v8c.")
pr()

# ── TAG PC PROBE RESULT ───────────────────────────────────────────────────────
pr("TAG POST_CLIMAX PROBE RESULT:")
pr("  post_climax def: price_drop(prev→curr) <= -0.25  OR  funding_extreme(|rate| >= 1%)")
pr()
pr("  fw data (freshwatch + build_token_days):")
pr("    07-06: avg_px=0.000889  change=−2.0%   crash=False  fe=False  PC=False  CF=False")
pr("    07-07: avg_px=0.000896  change=+0.8%   crash=False  fe=False  PC=False  CF=False")
pr("    07-08: avg_px=0.000488  change=−45.5%  crash=True   fe=False  PC=True   CF=False")
pr("    07-09: avg_px=0.000825  change=+69.0%  crash=False  fe=False  PC=True   CF=True")
pr()
pr("  LOCKED calib (TAG_result.txt klines):")
pr("    07-07: avg_px=0.0008875")
pr("    07-08: avg_px=0.0007163  change=−19.3%  crash=False (< 25% threshold)")
pr("    → PC NOT fired in calib data")
pr("    → CF fires 07-08 (gLSR drops: 1.97→1.70→1.01 = −49% in 2d)")
pr()
pr("  VERDICT: ÁN HAI-NGUỒN xác nhận.")
pr("    fw avg_px 07-08 = 0.000488 (−45.5%) — PC fires → suppresses chain")
pr("    calib avg_px 07-08 = 0.000716 (−19.3%) — PC NOT fires → chain opens 07-12")
pr("    fw và CASE_TAG.xlsx px_avg KHỚP (0.000488). TAG_result.txt LỆCH.")
pr("    Nguyên nhân: khác nhau cách tính avg_px ngày flash-crash")
pr("    (fw: VWAP/TWAP nặng về đáy crash; calib: TWAP nhẹ hơn hoặc close-based)")
pr("    Chưa phải bug #10 — là two-source price series diverge.")
pr()
pr("  CHỜ OPERATOR RULING: fw authoritative → TAG FAIL (PC đúng)")
pr("                         calib authoritative → TAG PASS* (PC mis-fire, opens 07-12)")
pr()

# ── SUPPRESSOR 44 DISTRIBUTION ───────────────────────────────────────────────
pr("SUPPRESSOR DISTRIBUTION — GHI CHÚ PHƯƠNG PHÁP:")
pr("  Probe chạy eval_gom tại dq_episode_start date (fw data) → toàn NONE")
pr("  (47/47 in-window tokens). Lý do: dq_episode_start trong state v8 được set")
pr("  bởi full-scan loop logic (chain-close conditions + state carry-forward),")
pr("  không nhất thiết correspond với ngày suppressor fire thuần túy.")
pr("  → Phân bố PC trong 44 SUPP không xác định được từ fw probe đơn lẻ.")
pr("  → Rủi ro 'PC lỏng suppress oan' CHƯA LOẠI TRỪ được — cần scan loop trace.")
pr("  → Ghi vào TASKS.md để probe proper (trace scan loop, không dùng eval_gom isolated).")
pr()

pr("=" * 72)
pr("GATE v8d — COMPLETE TABLE")
pr(f"{'#':<5} {'Token':<12} {'Episode':<25} {'Result':<60}")
pr("-" * 105)

rows = [
    # _FORM rows
    ("1",    "_FORM",       "gom_a_fire",
     "skip — formula verified in conformance table (spec v1.7, §3)",
     "Per conformance table §3: A1∧A2∧A3∧(A4∨A5). Code verified commit 8edc053 against each row."),

    ("2",    "_FORM",       "gom_b_fire",
     "skip — formula verified in conformance table (spec v1.7, §4)",
     "Per conformance table §4: B1∧(B2∨B3)∧B4. Code verified same commit."),

    # BANK
    ("3",    "BANK",        "open",
     "PASS*-data-bound (fw starts 07-01; spec ≤06-29 → earliest possible = 07-04)",
     "Spec open criterion: ≤06-29. fw data window starts 07-01 (universe entry 07-01). "
     "Opens 07-04 = earliest day with valid A4 d_pos_3d≥0 in fw. "
     "PASS*-data-bound (not PASS* vs calib 07-12 — that is run-vs-run expectation drift)."),

    ("4",    "BANK",        "chapter",
     "PASS (crowd_flush 07-04 → chapter 2 same day)",
     "hist ch1: 07-04→07-04 Q1=$0; ch2 starts 07-04. Logic correct."),

    ("5",    "BANK",        "close-iv [RETRO-TAG SIGNED]",
     "FAIL→RETRO-TAG SIGNED: close gom_gap 07-14; retro-tag 07-16 [gap→chuyển pha (retro 07-16)]",
     "fw: chain exhausts gom_gap>2d 07-14. RETRO-TAG: peak_pos_r=3.8142@07-04, "
     "07-16 pos_r=2.02 → drop=47% from peak, gap=2d ≤3 → QUALIFIES. "
     "OPERATOR SIGNED. Display-only label. State unchanged. "
     "Note: peak fw 3.81/07-04 vs calib 3.71/07-10 → same data-start family, not mâu thuẫn."),

    # TAG
    ("6",    "TAG",         "open",
     "FAIL/ÁN-2-NGUỒN (PC fires on fw avg_px 0.000488; calib avg_px 0.000716 — no PC)",
     "fw avg_px 07-07→08: 0.000896→0.000488 = −45.5% → PC fires (threshold −25%). "
     "LOCKED calib: 0.000875→0.000716 = −19.3% → PC NOT fires → CF fires (gLSR drop). "
     "fw ∧ CASE_TAG.xlsx px_avg KHỚP (0.000488). TAG_result.txt klines LỆCH. "
     "Two-source price diverge on flash-crash day (different avg_px computation). "
     "RULING PENDING: fw authoritative → FAIL; calib authoritative → opens 07-12 = ARMED #1 PASS."),

    # BAS
    ("7",    "BAS",         "supp+open-after",
     "PASS (post_climax 07-02→07-15; no spurious open after cooldown)",
     "BAS dq_ep=07-02 dq_end=07-15. No chain opened in fw period. "
     "After cooldown clear 07-15: no GOM-A/B conditions met → no spurious fire. PASS."),

    # BTW
    ("8",    "BTW",         "SUPP",
     "FAIL-data-bound (fw window starts 07-01; 06-21 PC episode missing — truncated)",
     "fw BTW data starts 07-01 (universe entry). 06-21 post_climax NOT in fw window → "
     "BTW looks clean, opens 07-03. Calib has 06-21 PC → suppresses. "
     "Not a logic bug — data-start truncation. "
     "Production risk: tokens entering universe post-climax will always look clean in fw scan. "
     "Fix ký: hook backfill-on-universe-add (funding+LSR+OI+klines trailing 35d). "
     "BTW re-run after hook = verify. FAIL-data-bound, not FAIL-logic."),

    # BULLA
    ("9",    "BULLA",       "open",
     "PASS*-data-bound (+3d diverge 07-11 vs calib 07-08)",
     "BULLA opens 07-11 in fw, calib 07-08. B1 hedge_structure stricter on fw daily data. "
     "Closes 07-17 gom_gap>2d. Logic functionally correct — date diverge from data granularity."),

    # TUT - NOTE: TUT chapter REMOVED, replaced by C1
    ("10",   "TUT",         "chapter [REMOVED — see C1]",
     "REMOVED (per operator ruling: TUT no GOM-A/B expected; C1 = GOM-C covers it)",
     "TUT never meets GOM-A/B in fw period — this is correct per spec. "
     "GOM-C (stateless) fires instead. Row removed from §6 active gate; C1 = PASS covers TUT."),

    # IDOL
    ("11",   "IDOL",        "open",
     "PASS (re-grade: no-fire = expected per §6 signed spec)",
     "§6 signed: 'IDOL 28-31/07: GOM-A bật muộn/KHÔNG (build 4 ngày, nhanh) — đo độ trễ scan với flip-nhanh Loài A.' "
     "No-fire = expected outcome. Delay measurement: A2 avg5(gLSR) first crosses ≤1.1 threshold: "
     "never in 07-06→07-20 window (avg5 >1.1 throughout). After 07-20: IDOL position unwinds. "
     "GOM-A scan lag for Loài A flip: >14d (flip 07-06→07-20, no fire). Data: fw=xlsx confirmed."),

    # AKE
    ("12",   "AKE",         "SUPP",
     "PASS*-data-bound (dq_ep=07-24 fw vs calib 07-08, +16d date-shift)",
     "fw: AKE dq_ep=07-24 dq_end=08-06. Suppressor fires (date differs from calib 07-08). "
     "Functional PASS: decay/supp blocks chain correctly. "
     "AKE taker fw-vs-calib: decay fires 07-24 fw (taker_buy_pct < 45% for ≥5 consecutive days prior). "
     "Date shift: likely AKE entered fw universe later than calib window. Data-start family."),

    # ZBT
    ("Z1",   "ZBT",         "open",
     "PASS*-data-bound (fw starts 07-05, delisted — spec ≤07-01)",
     "ZBT delisted. fw data starts 07-05. Spec open ≤07-01 not verifiable — data truncated. "
     "Opens 07-05 (first available fw day). PASS*-data-bound."),

    ("Z2",   "ZBT",         "close-iv",
     "PASS*-data-bound (07-14 drop:33% — spec 07-02, +12d)",
     "fw: closes 07-14 pos_r_drop:33% from peak 4.24. Rule-iv logic correct. "
     "Date shift from late fw start. PASS*-data-bound."),

    # PARTI
    ("P",    "PARTI",       "open+close-iv",
     "PASS (opens 07-07 ≤09/07, closes 07-11 drop:59% — Bug #9 RESOLVED)",
     "A4 d_pos_3d≥0 (no hedge_structure required) → PARTI fires from 07-03. "
     "Opens 07-07 (<09/07 threshold). Closes 07-11 pos_r_drop:59% from peak 3.65. PASS."),

    # T2
    ("T2",   "TAG",         "wrong-side",
     "PASS (no chain open in fw period; 07-28→31 A2 fails, no GOM fire)",
     "TAG has no open in fw. 07-28→31: A2 avg5>1.1, no fire. PASS."),

    # POWER
    ("PW",   "POWER",       "b-pos",
     "PASS (OPEN 08-02; A3+A4+A5+B1+B3+B4 signals, Q1=$145K)",
     "POWER open 08-02, n_days=6 (08-02→08-07), Q1=$145K, peak_pos_r=1.10."),

    # CLO
    ("CL",   "CLO",         "supp-neg",
     "PASS (dq_ep=07-27 dq_end=08-09; no chain open)",
     "CLO suppressed from 07-27. No chain history. PASS."),

    # GOM-C rows
    ("C1",   "TUT",         "GOM-C fire 07-13+07-23",
     "PASS (fires 07-13 ✓ 07-14 07-15, 07-23 ✓; 07-21/22 d_pos_3d<0→no fire)",
     "Per-date probe: FIRE 07-13,07-14,07-15,07-23. Gate expects 07-13 and within 07-21→23: 07-23 ✓."),

    ("C2",   "BULLA",       "GOM-C block 07-17→21",
     "PASS (all False 07-17→21 — probe confirmed)",
     "BULLA chain closes gom_gap 07-17. GOM-C check (no cooldown) = False all 5 days."),

    ("C3",   "BANK",        "d_pos<0 post-close",
     "PASS (dq_ep=07-21; d_pos_3d<0 after close → GOM-C blocked)",
     "BANK closes 07-14 (fw). dq fires 07-21. No GOM-C after chain close."),

    ("C4",   "BANANAS31",   "negative test",
     "PENDING 15/08 — no fw data before 08-01",
     "BANANAS31 opens 08-01, closes 08-06 gom_gap>2d. GOM-C negative test for earlier period."),

    ("C5",   "COOKIE/CYS/TST", "live 08-07",
     "PASS (COOKIE ✓ CYS ✓; TST=cooldown first 08-04 clear 08-18)",
     "From scan output 08-07."),
]

PASS_count  = 0
PASSS_count = 0  # PASS*
FAIL_count  = 0
PEND_count  = 0
skip_count  = 0
removed_count = 0

for num, tok, ep, result, note in rows:
    r_upper = result.upper()
    if "SKIP" in r_upper or "skip" in result.lower().split()[0]:
        skip_count += 1
    elif "REMOVED" in r_upper:
        removed_count += 1
    elif "PENDING" in r_upper:
        PEND_count += 1
    elif "FAIL" in r_upper:
        FAIL_count += 1
    elif "PASS*" in result:
        PASSS_count += 1
    elif result.startswith("PASS"):
        PASS_count += 1

    pr(f"{num:<5} {tok:<12} {ep:<25} {result:<60}")
    pr(f"     Note: {note}")
    pr()

pr("-" * 105)
pr(f"TOTAL: PASS={PASS_count}  PASS*={PASSS_count}  FAIL={FAIL_count}  PENDING={PEND_count}  removed={removed_count}  skip={skip_count}")
pr()
pr("FAIL BREAKDOWN:")
pr("  - BANK close-iv: RETRO-TAG SIGNED (display-only label) — functionally accounted for")
pr("  - TAG open: ÁN-2-NGUỒN — awaiting operator ruling (fw vs calib avg_px)")
pr("  - BTW SUPP: FAIL-data-bound — fix = backfill hook (already signed)")
pr("  - TUT chapter: REMOVED from gate (C1 covers it)")
pr("  [IDOL: re-graded PASS — no-fire = expected per §6]")
pr()

# ── DATA-START TRUNCATION FAMILY ─────────────────────────────────────────────
pr("=" * 72)
pr("HỌ BỆNH — DATA-START TRUNCATION (BANK+8d / BTW / ZBT-late / AKE-shift)")
pr("=" * 72)
pr()
pr("Cơ chế chung: fw series bắt đầu muộn hơn kỳ vọng spec.")
pr()
pr(f"{'Token':<8} {'Spec open':<12} {'fw first day':<14} {'diverge':<10} {'grade'}")
pr("-" * 60)
pr(f"{'BANK':<8} {'≤2026-06-29':<12} {'2026-07-01':<14} {'+2d start':<10} PASS*-data-bound")
pr(f"{'BTW':<8} {'has 06-21 PC':<12} {'2026-07-01':<14} {'missing 06-21 PC':<10} FAIL-data-bound")
pr(f"{'ZBT':<8} {'≤2026-07-01':<12} {'2026-07-05':<14} {'+4d delisted':<10} PASS*-data-bound")
pr(f"{'AKE':<8} {'07-08 calib':<12} {'07-24 fw':<14} {'+16d shift':<10} PASS*-data-bound")
pr()
pr("Gate grading: so vs spec ký + ghi data-start note.")
pr("KHÔNG so vs 'calib 07-12' hay run trước — đó là expectation-drift (run-vs-run).")
pr()
pr("BTW production risk + fix:")
pr("  Mọi token enter universe hậu-climax → look clean trên fw scan (no backfill).")
pr("  Fix ký: backfill-on-universe-add: funding + LSR + OI + klines trailing 35d.")
pr("  BTW re-run sau hook = verify của chính hook.")
pr()

# ── BẢNG 3D CROSS-CHECK INLINE ───────────────────────────────────────────────
pr("=" * 72)
pr("BẢNG 3D CROSS-CHECK — đối chiếu máy | sổ | khớp/lệch")
pr("=" * 72)
pr()
pr(f"{'Token':<14} {'scan_v8 (fw)':<22} {'sổ (spec/calib)':<25} {'status':<20} ghi chú")
pr("-" * 105)

crosscheck = [
    ("BANK",      "closed 07-14; retro 07-16",  "closed calib; retro proposal",  "KHOP+SIGN",   "retro-tag signed; peak fw 3.81/07-04 same data-start family"),
    ("TAG",       "supp 07-08 PC (fw avg -45%)", "calib: CF 07-08 (no PC, -19%)", "LECH-2NGUON", "án hai-nguồn xác nhận; ruling pending"),
    ("BAS",       "supp 07-02→07-15; no open",  "supp 07-02→07-15 per spec",     "KHOP",        "post_climax 07-02; no chain. PASS."),
    ("BTW",       "opens 07-03 (no 06-21 PC)",  "suppressed from 06-21 calib",   "LECH-DATAB",  "data-start truncation; FAIL-data-bound"),
    ("IDOL",      "no chain; avg5>1.1 throughout","no-fire expected per §6",      "KHOP",        "re-graded PASS; delay measurement: >14d flip lag"),
    ("TUT",       "no GOM-A/B; GOM-C 07-13/23", "no chain; C1 covers",           "KHOP",        "chapter row removed; C1=PASS"),
    ("AKE",       "supp 07-24; decay fires fw",  "supp 07-08 calib",              "KHOP*",       "+16d date-shift; data-start family; functional PASS"),
    ("BULLA",     "closed 07-17; opens 07-11",   "calib opens 07-08",             "KHOP*",       "+3d diverge; logic correct"),
    ("PARTI",     "closed 07-11; opens 07-07",   "expected opens ≤07-09",         "KHOP",        "Bug #9 resolved; A4 d_pos_3d≥0 (no hedge_structure)"),
    ("ZBT",       "closed 07-14; drop:33%",      "calib closes 07-02",            "KHOP*",       "delisted; late fw start; +12d shift; rule-iv logic OK"),
    ("POWER",     "OPEN 08-02 n_days=6",         "b-pos open (no calib)",         "KHOP",        "new open; A-signal 08-02"),
    ("CLO",       "supp 07-27→08-09; no open",   "supp-neg expected",             "KHOP",        "dq 07-27; no chain"),
    ("COOKIE",    "closed 08-06; GOM-C 08-07",   "expected GOM-C fires",          "KHOP",        "stateless; C5"),
    ("CYS",       "no state; GOM-C 08-07",       "expected GOM-C fires",          "KHOP",        "stateless; C5"),
    ("TST",       "supp 08-04; cd clear 08-18",  "GOM-C cd first 08-04",          "KHOP",        "C5; cooldown 14d from 08-04"),
    ("BANANAS31", "closed 08-06 gom_gap>2d",     "C4 PENDING 15/08",              "PEND",        "opens 08-01; C4 negative test pending"),
]

for tok, fw_st, spec_st, status, note in crosscheck:
    pr(f"{tok:<14} {fw_st:<22} {spec_st:<25} {status:<20} {note}")

pr()
pr("KHOP = scan khop spec/calib | KHOP* = logic khop, date diverge (data-start family)")
pr("LECH-2NGUON = hai-nguon price diverge | LECH-DATAB = data-start truncation")
pr("PEND = pending")
pr()

# ── BREAKDOWN 5 OPEN CHAINS ──────────────────────────────────────────────────
pr("=" * 72)
pr("BREAKDOWN 5 OPEN CHAINS Q1 LỚN NHẤT (08-07) — A1→A5 ngày mở")
pr("(A4 mới định nghĩa hôm nay: verify A1-A5 trên 16 chuỗi mở)")
pr("=" * 72)
pr()

df_aug = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df_aug = taker_scale_check_df(df_aug)

top5 = [
    ("FFUSDT",   "FF",    "2026-08-01", 1988262),
    ("ROBOUSDT", "ROBO",  "2026-08-03", 1369827),
    ("APRUSDT",  "APR",   "2026-08-06", 527899),
    ("HUMAUSDT", "HUMA",  "2026-08-04", 412595),
    ("ZESTUSDT", "ZEST",  "2026-08-06", 154399),
]

for sym, tok, open_date, q1 in top5:
    try:
        days, _ = build_token_days(df_aug, sym, "2026-06-01", "2026-08-07", intervals)
        enrich_token_days(days)
        fire_i = None
        for idx, d in enumerate(days):
            if d.get("date","") == open_date:
                fire_i = idx
                break
        if fire_i is None:
            pr(f"\n{tok} ({sym}): date {open_date} not in fw data")
            continue
        result = gs.eval_gom(days, fire_i, cfg, sc)
        ga = result.get("gom_a", {})
        gb = result.get("gom_b", {})
        d_now = days[fire_i]
        d3 = d_now.get("d_pos_3d", float("nan"))
        oicp = d_now.get("oi_cycle_pos", float("nan"))
        lp = d_now.get("lsr_pos", float("nan"))
        # Correct formula: A1 AND A2 AND A3 AND (A4 OR A5)
        gom_a_fire = ga.get('A1') and ga.get('A2') and ga.get('A3') and (ga.get('A4') or ga.get('A5'))
        gom_b_fire = gb.get('B1') and (gb.get('B2') or gb.get('B3')) and gb.get('B4')
        a4_d3 = not math.isnan(d3) and d3 >= 0
        from scanner.screener.signals import pos_rerate as _pr
        a4_pr = _pr(days, fire_i, cfg)
        oicp_str = f"{oicp:.4f}" if not math.isnan(oicp) else "NaN"
        pr(f"\n{'='*52}")
        pr(f"{tok}  open={open_date}  Q1=${q1:,}")
        pr(f"  GOM-A: A1={ga.get('A1')} A2={ga.get('A2')} A3={ga.get('A3')} A4={ga.get('A4')} A5={ga.get('A5')} -> FIRE={gom_a_fire}")
        pr(f"  GOM-B: B1={gb.get('B1')} B2={gb.get('B2')} B3={gb.get('B3')} B4={gb.get('B4')} -> FIRE={gom_b_fire}")
        pr(f"  d_pos_3d={d3:+.4f}  oi_cycle_pos={oicp_str}  lsr_pos={lp:.4f}")
        a4_path = "d_pos_3d" if a4_d3 else ("pos_rerate" if a4_pr else "NONE (via A5)")
        pr(f"  A4 via: {a4_path}  (d_pos_3d>={0}={a4_d3}, pos_rerate={a4_pr})")
        if not math.isnan(oicp) and oicp > 0.5:
            pr(f"  NOTE: A5=False (oi_cycle_pos={oicp:.4f}>0.5); opens via A4 only")
    except Exception as e:
        pr(f"\n{tok}: ERROR {e}")

pr()
pr("NOTE: With new A4 (d_pos_3d>=0), tokens can open without hedge_structure.")
pr("  FF (prev 'dead under structural-compose') — verify A4 path above.")

# ── Write file ────────────────────────────────────────────────────────────────
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nWritten: {OUT}")

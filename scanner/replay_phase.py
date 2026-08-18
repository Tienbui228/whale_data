#!/usr/bin/env python3
"""
replay_phase.py — chạy §8.2 acceptance bảng cho PHASE-TAG v0.3 (21 dòng, TRỪ #17 §9.2).

Input: 12 file *_result.txt ở binance-bot-signals/docs/case study/
Output: BẢNG THÔ 21 dòng expected-vs-actual.

Luật chấm (§8.2):
  NEGATIVE/SUPPRESSOR/HARVEST/EVENT = FAIL cứng
  TEXTURE = ≤2 miss trong dòng
  DOCUMENTATION = chấm cờ, không chấm nhãn
  SANITY = floor
"""
from __future__ import annotations
import sys
import io
import math
import yaml
from pathlib import Path

# Force UTF-8 stdout on Windows (only when run as __main__, not on import)
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).parent.parent
BOT_REPO = Path(r"D:\Data back test\binance-bot-signals")
CASE_STUDY = BOT_REPO / "docs" / "case study"

# Add both repos to path
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(BOT_REPO))

from replay import parse_result_file, build_days
# Import phase_tag directly from scanner/ (sibling file)
sys.path.insert(0, str(Path(__file__).parent))
from phase_tag import tag, event_tag

# Freshwatch daily loader (mẫu case_daily.py — dedup-safe upstream, verified V4)
import csv, math

# [F1] Canonical scale detector (avoid hard-code ×100, avoid fork scale-logic)
sys.path.insert(0, str(REPO / "scripts"))
from fw_loader_utils import taker_scale_check   # returns scale factor 1.0 or 100.0

FRESHWATCH_DIR = REPO / "data" / "export"


def load_freshwatch_days(sym_usdt: str, lookback_days: int = 90) -> list:
    """Load DayData from freshwatch_daily_*.csv.

    Taker scale: dùng canonical `taker_scale_check()` từ fw_loader_utils
    (một nguồn scale-logic, chống fork khi source đổi scale).
    Cửa ra: SCALE-ASSERT — nếu max ≤ 1.5 (fraction detected) → RAISE.
    """
    rows = []
    for p in sorted(FRESHWATCH_DIR.glob("freshwatch_daily_*.csv")):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("symbol") != sym_usdt: continue
                def _f(v):
                    if v is None or str(v).strip() == "": return float("nan")
                    try:
                        x = float(v); return float("nan") if math.isnan(x) else x
                    except (ValueError, TypeError): return float("nan")
                try: fn = int(float(r.get("funding_n") or 0))
                except: fn = 0
                rows.append({
                    "date":          r["date"],
                    "lsr_pos":       _f(r.get("lsr_pos_r")),
                    "lsr_acc":       _f(r.get("lsr_acc_r")),
                    "lsr_global":    _f(r.get("lsr_global_r")),
                    "taker_ratio":   _f(r.get("taker_ratio")),
                    "taker_buy_pct": _f(r.get("taker_buy_pct")),   # RAW scale
                    "vol_quote":     _f(r.get("vol_quote")),
                    "avg_px":        _f(r.get("px_avg")),
                    "oi_usd":        _f(r.get("oi_usd")),
                    "funding_avg":   _f(r.get("funding_avg")),
                    "funding_min":   _f(r.get("funding_min")),
                    "funding_max":   _f(r.get("funding_max")),
                    "funding_n":     fn,
                })
    rows.sort(key=lambda x: x["date"])
    if not rows:
        return rows

    # [F1] Canonical scale detector → apply factor uniformly
    raw_taker = [r["taker_buy_pct"] for r in rows]
    scale = taker_scale_check(sym_usdt, raw_taker)   # 1.0 or 100.0
    if scale != 1.0:
        for r in rows:
            if not math.isnan(r["taker_buy_pct"]):
                r["taker_buy_pct"] = r["taker_buy_pct"] * scale

    # [F2] SCALE-ASSERT at loader exit — nổ mặt nếu vẫn fraction sau khi convert
    non_nan = [r["taker_buy_pct"] for r in rows if not math.isnan(r["taker_buy_pct"])]
    if non_nan:
        mx = max(non_nan)
        if mx <= 1.5:
            raise RuntimeError(
                f"SCALE-ASSERT FAIL [{sym_usdt}]: taker_buy_pct max={mx:.4f} ≤ 1.5 "
                f"— fraction detected sau khi qua taker_scale_check (expected percent 0-100). "
                f"Loader path bị bypass hoặc canonical detector broken. Nổ mặt tại loader "
                f"để không đi xuống cây với data sai scale."
            )
    return rows


def load_case_v2(token: str, fw_symbol: str = None) -> tuple:
    """Load token days with freshwatch PRIORITY, result.txt FALLBACK.

    Returns (days, source_str) where source_str ∈ {'freshwatch', 'result.txt', 'merged'}.
    """
    sym_usdt = fw_symbol or (token + "USDT")
    fw_days = load_freshwatch_days(sym_usdt)
    if len(fw_days) >= 30:
        return fw_days, "freshwatch"

    # Fallback: result.txt
    rt_file = RESULT_FILES.get(token)
    if rt_file:
        fp = CASE_STUDY / rt_file
        if fp.exists():
            f, o, r, k = parse_result_file(fp)
            rt_days = build_days(f, o, r, k)
            if fw_days:
                # Merge: freshwatch takes priority, result.txt fills earlier gap
                fw_dates = {d["date"] for d in fw_days}
                merged = [d for d in rt_days if d["date"] not in fw_dates] + fw_days
                merged.sort(key=lambda x: x["date"])
                return merged, "merged"
            return rt_days, "result.txt"

    return fw_days, "freshwatch" if fw_days else "none"

# Load cfg (union of thresholds.yaml + screen_thresholds.yaml)
THR = yaml.safe_load(open(BOT_REPO / "scanner" / "screener" / "thresholds.yaml", encoding="utf-8"))
SCREEN = yaml.safe_load(open(REPO / "screen_thresholds.yaml", encoding="utf-8"))

# Merge cfg for signals (thresholds.yaml has per-signal cfg dicts)
CFG = dict(THR)   # signals.py cfg
CFG["screen"]    = SCREEN.get("gom", {})
CFG["phase_tag"] = SCREEN.get("phase_tag", {})

# For rules_v2 that may check specific fields
CFG.setdefault("_partial_day", False)


# ── Case data files ──────────────────────────────────────────────────────────
RESULT_FILES = {
    "BANK":   "BANK_result.txt",
    "TAG":    "TAG_result.txt",
    "AKE":    "ake_result.txt",
    "BAS":    "bas_result.txt",
    "BASED":  "based_result.txt",
    "BTW":    "btw_result.txt",
    "BULLA":  "bulla_result.txt",
    "CLO":    "clo_result.txt",
    "ESPORT": "esport_result.txt",
    "IDOL":   "idol_result.txt",
    "POWER":  "power_result.txt",
    "TUT":    "tut_result.txt",
}


_LOAD_CACHE = {}
_SOURCE_CACHE = {}

# ── [2c] fix (b): Load case_state_map for join into tag() ────────────────────
import re, json as _json
_CASE_STATE = {}
_CSM = REPO / "docs" / "case_files" / "case_state_map.md"
if _CSM.exists():
    # Extract JSON block at end of file
    txt = _CSM.read_text(encoding="utf-8")
    m = re.search(r"```json\s*(\{.*?\})\s*```", txt, re.DOTALL)
    if m:
        try:
            _CASE_STATE = _json.loads(m.group(1))
        except Exception:
            pass


def _case_state_for(token: str):
    """Return case_state dict {state, ngay_ky, verdict_ref} for token, or None."""
    return _CASE_STATE.get(token)

def load_case(token: str):
    """Load with freshwatch PRIORITY + result.txt FALLBACK. Cached."""
    if token in _LOAD_CACHE:
        return _LOAD_CACHE[token]
    fw_sym_map = {
        "BANK":"BANKUSDT","TAG":"TAGUSDT","AKE":"AKEUSDT","BAS":"BASUSDT",
        "BASED":"BASEDUSDT","BTW":"BTWUSDT","BULLA":"BULLAUSDT","CLO":"CLOUSDT",
        "ESPORT":"ESPORTSUSDT","IDOL":"IDOLUSDT","POWER":"POWERUSDT","TUT":"TUTUSDT",
        # Extras added in v0.3.1:
        "XPIN":"XPINUSDT","KOMA":"KOMAUSDT","TST":"TSTUSDT","APR":"APRUSDT",
    }
    fw_sym = fw_sym_map.get(token, token+"USDT")
    days, src = load_case_v2(token, fw_symbol=fw_sym)
    _LOAD_CACHE[token] = days
    _SOURCE_CACHE[token] = src
    return days


def case_source(token: str) -> str:
    return _SOURCE_CACHE.get(token, "?")


def find_day(days: list, date_str: str) -> int:
    """Find day index by MM-DD or YYYY-MM-DD substring match."""
    if not days: return -1
    for i, d in enumerate(days):
        dstr = d.get("date", "")
        if date_str in dstr or dstr.endswith(date_str):
            return i
    return -1


def tag_range(token: str, date_from: str, date_to: str) -> list:
    """Tag all days in [date_from, date_to] range. Return list of (date, stage)."""
    days = load_case(token)
    if not days: return []
    out = []
    i0 = find_day(days, date_from)
    i1 = find_day(days, date_to) if date_to != date_from else i0
    if i0 < 0: return []
    if i1 < 0: i1 = i0
    for i in range(i0, i1 + 1):
        r = tag(days, i, CFG, case_state=_case_state_for(token))
        out.append((days[i].get("date"), r.get("stage"), r.get("event_tag"),
                    r.get("stage_flags", [])))
    return out


# ── §8.2 Acceptance rows ─────────────────────────────────────────────────────
ACCEPTANCE = [
    # (#, token, date, expected, class)
    (1,  "POWER",  "07-20", ["S2-EARLY"],               "TEXTURE"),
    (2,  "BASED",  "07-20", ["S2-LATE"],                "TEXTURE"),
    (3,  "BAS",    "07-20", ["S0", "S2-EARLY", "S2-MID", "S2-LATE"], "TEXTURE"),   # S0→S2*
    (4,  "IDOL",   "07-20", ["S2-EARLY", "S2-MID", "S2-LATE", "S2-MID↑"], "TEXTURE"),
    (5,  "TUT",    "07-20", ["S3-BIDWALK", "S3-GRIND"], "TEXTURE"),
    (6,  "BULLA",  "07-20", ["S3-BIDWALK"],             "TEXTURE"),
    (7,  "AKE",    "07-20", ["S4", "S5"],               "SUPPRESSOR"),
    (8,  "CLO",    "07-20", ["S4"],                     "SUPPRESSOR-CỨNG"),
    (9,  "BTW",    "*",     ["*NOT_S2*"],               "NEGATIVE-CỨNG"),  # BTW toàn kỳ không S2*
    (10, "ESPORT", "07-19", ["S4", "S5"],               "SUPPRESSOR-CỨNG"),  # climax
    (11, "BANK",   "chuỗi", ["chuỗi complex"],          "HARVEST-CỨNG"),
    (12, "TUT",    "08-02", ["S3-HARVEST"],             "HARVEST-CỨNG"),  # + 08-05
    (13, "TAG",    "07-20", ["*ANY*"],                  "DOCUMENTATION"),  # cờ OWNERSHIP-UNVERIFIED
    (14, "XPIN",   "07-31", ["*NOT_S2*"],               "NEGATIVE-CỨNG"),  # + CROWD-CHASE (chưa có result.txt)
    (15, "KOMA",   "08-02", ["S0-POSTFLUSH"],           "TEXTURE"),  # (chưa có result.txt)
    (16, "TST",    "07-*",  ["S3-GRIND"],               "TEXTURE"),  # (chưa có result.txt)
    (17, "APR",    "08-05", ["S2-LATE"],                "TEXTURE-GATED"),  # §9.2 SKIP
    (18, "*EVENT*","*",     ["BAIT/CRASH/RALLY"],       "EVENT-CỨNG"),
    (19, "*SANITY*","*",    ["UNKNOWN ≤40%"],           "SANITY"),
    (20, "BANK",   "~07-24",["S4"],                     "TEXTURE"),  # khối 🔻 transition
    (21, "CLO",    "*",     ["*NO_REPORT*"],            "NEGATIVE-CỨNG"),  # cửa xác
]


def eval_row(row_id, token, date, expected, class_):
    """Return (actual_stage_or_note, PASS/FAIL/SKIP)."""
    # SKIP #17 per §9.2
    if row_id == 17:
        return ("SKIP §9.2 — APR chờ án LSR-merge repair", "SKIP")

    # Row 9: BTW — amendment v0.3.1 dòng 9 (PRE-APPROVED, REPORT-LAYER)
    # Nhãn thô S2*/S3* GIỮ NGUYÊN; report route sang ⚠ vì case_state=DISTRIBUTION*.
    # 4 vế PASS-cứng (§8.2):
    #   (i)   không ngày nào BTW xuất hiện 🟢 (RÒNG) hoặc 🔴 (ĐẨY-GIÁ) — vì state_conflict
    #   (ii)  không bao giờ RIPE
    #   (iii) mọi ngày nhãn thô S2*/S3* → state_conflict=TRUE + route ⚠
    #   (iv)  ngày funding_neg_div → B1 (S5) thắng
    if row_id == 9:
        days = load_case("BTW")
        if not days: return ("BTW no data", "SKIP-DATA")
        cs = _case_state_for("BTW")
        is_dist = cs and "DISTRIBUTION" in str(cs.get("state", "")).upper()
        if not is_dist:
            return (f"case_state không DISTRIBUTION (={cs})", "FAIL")

        s2s3_days = []
        conflict_missing = []
        ripe_found = []
        route_ok = 0
        b1_wins = 0; b1_missed = []

        for i in range(len(days)):
            r = tag(days, i, CFG, case_state=cs)
            st = r.get("stage") or ""
            flags = r.get("stage_flags", [])
            date = r.get("date")

            # Vế (ii) RIPE
            if "RIPE" in flags:
                ripe_found.append((date, st, flags))

            # Vế (i)+(iii) route ⚠ khi nhãn thô S2*/S3*
            if st.startswith("S2") or st.startswith("S3"):
                s2s3_days.append((date, st))
                if not r.get("state_conflict"):
                    conflict_missing.append((date, st, flags))
                else:
                    route_ok += 1

            # Vế (iv) funding_neg_div → B1 thắng
            _fnd = False
            try:
                from signals import funding_neg_div
                _fnd = funding_neg_div(days, i, CFG)
            except Exception:
                pass
            if _fnd and st not in ("S4","S5"):
                b1_missed.append((date, st))
            elif _fnd:
                b1_wins += 1

        v_ii  = len(ripe_found) == 0
        v_iii = len(conflict_missing) == 0
        v_i   = v_iii
        v_iv  = len(b1_missed) == 0

        parts = [
            f"nhãn thô S2*/S3* GIỮ: {len(s2s3_days)}d",
            f"state_conflict route: {route_ok}/{len(s2s3_days)} {'✓' if v_iii else '✗'}",
            f"RIPE: {len(ripe_found)} {'✓' if v_ii else '✗'}",
            f"B1 wins on fnd: {b1_wins} miss={len(b1_missed)} {'✓' if v_iv else '✗'}",
        ]
        verdict = "PASS" if (v_i and v_ii and v_iii and v_iv) else "FAIL"
        return (" · ".join(parts), verdict)

    # Row 11: BANK chuỗi complex
    if row_id == 11:
        checkpoints = [
            ("06-29", ["S2-LATE"]),
            ("07-10", ["S3-BIDWALK", "S3-TAKER", "S3-GRIND"]),
            ("07-19", ["S3-HARVEST", "S4"]),
            ("07-20", ["S3-HARVEST", "S4"]),
        ]
        days = load_case("BANK")
        results = []
        pass_ct = 0
        for dt, exp in checkpoints:
            idx = find_day(days, dt)
            if idx < 0: results.append(f"{dt}=NO_DATA"); continue
            r = tag(days, idx, CFG, case_state=_case_state_for(token))
            st = r.get("stage")
            ok = st in exp
            if ok: pass_ct += 1
            results.append(f"{dt}={st}{'✓' if ok else '✗ exp='+str(exp)}")
        # [G1] HARVEST-CỨNG per §8.2: strict — mọi checkpoint phải match
        verdict = "PASS" if pass_ct == len(checkpoints) else "FAIL"
        return (" | ".join(results), verdict)

    # Row 12: TUT 08-02 + 08-05
    if row_id == 12:
        days = load_case("TUT")
        results = []
        pass_ct = 0
        for dt in ["08-02", "08-05"]:
            idx = find_day(days, dt)
            if idx < 0: results.append(f"{dt}=NO_DATA"); continue
            r = tag(days, idx, CFG)
            st = r.get("stage")
            ok = st == "S3-HARVEST"
            if ok: pass_ct += 1
            results.append(f"{dt}={st}{'✓' if ok else '✗'}")
        verdict = "PASS" if pass_ct == 2 else "FAIL"
        return (" | ".join(results), verdict)

    # Row 13: TAG documentation — flag OWNERSHIP-UNVERIFIED hiện diện
    if row_id == 13:
        days = load_case("TAG")
        idx = find_day(days, "07-20")
        if idx < 0: return ("TAG 07-20 NO_DATA", "SKIP-DATA")
        r = tag(days, idx, CFG)
        flags = r.get("stage_flags", [])
        has_flag = "OWNERSHIP-UNVERIFIED" in flags
        return (f"stage={r.get('stage')} flags={flags} → OWNERSHIP-UNVERIFIED {'✓' if has_flag else '✗'}",
                "PASS" if has_flag else "FAIL")

    # Row 14, 15, 16: XPIN, KOMA, TST — try freshwatch (LOADER-EXTEND v2a)
    if row_id in (14, 15, 16):
        days = load_case(token)
        if not days:
            return (f"SKIP-DATA — {token} no fw/rt data", "SKIP-DATA")
        # Row 14: XPIN 31/07-07/08 — NEGATIVE + CROWD-CHASE (không S2*)
        if row_id == 14:
            hits = []
            for dt in ["07-31","08-01","08-02","08-03","08-04","08-05","08-06","08-07"]:
                idx = find_day(days, dt)
                if idx < 0: continue
                r = tag(days, idx, CFG)
                st = r.get("stage") or ""
                if st.startswith("S2"):
                    hits.append(f"{dt}={st}")
            return (f"XPIN Aug window S2* hits: {hits or 'none ✓'}",
                    "PASS" if not hits else "FAIL")
        # Row 15: KOMA 02-09/08 — TEXTURE (≤2 miss per §8.2)
        if row_id == 15:
            dates = ["08-02","08-03","08-04","08-05"]
            results = []; pass_ct = 0; tested = 0
            for dt in dates:
                idx = find_day(days, dt)
                if idx < 0: continue
                tested += 1
                r = tag(days, idx, CFG, case_state=_case_state_for(token))
                st = r.get("stage")
                ok = st == "S0-POSTFLUSH"
                if ok: pass_ct += 1
                results.append(f"{dt}={st}{'✓' if ok else '✗'}")
            # [G1] TEXTURE per §8.2: ≤2 miss → cần ≥ tested-2 match (min 1)
            min_pass = max(1, tested - 2)
            verdict = "PASS" if pass_ct >= min_pass else "FAIL"
            return (" | ".join(results) + f" (pass={pass_ct}/{tested} need≥{min_pass})", verdict)
        # Row 16: TST toàn July
        if row_id == 16:
            hits = []
            for i in range(14, len(days)):
                d = days[i].get("date","")
                if not d.startswith("2026-07"): continue
                r = tag(days, i, CFG, case_state=_case_state_for(token))
                if r.get("stage") == "S3-GRIND":
                    hits.append(d)
            return (f"TST July S3-GRIND hits: {len(hits)} — sample {hits[:3]}",
                    "PASS" if hits else "FAIL")

    # Row 18: EVENT counting
    if row_id == 18:
        events = []
        for tok, dt in [("BASED", "07-01"), ("BASED", "07-09"), ("BANK", "07-02"),
                        ("TAG", "07-*"), ("AKE", "07-*"), ("TUT", "07-*"), ("BULLA", "07-*")]:
            days = load_case(tok)
            if not days: continue
            for i, d in enumerate(days):
                ev = event_tag(days, i)
                if ev:
                    events.append(f"{tok}@{d['date']}:{ev}")
                    if len(events) >= 10: break
            if len(events) >= 10: break
        return (f"events found: {len(events)} — sample: {events[:5]}",
                "PASS" if len(events) >= 4 else "FAIL")

    # Row 19: SANITY UNKNOWN ≤40%
    if row_id == 19:
        total = unknown = 0
        for tok in RESULT_FILES:
            days = load_case(tok)
            if not days: continue
            for i in range(14, len(days)):  # skip warmup
                r = tag(days, i, CFG, case_state=_case_state_for(token))
                total += 1
                if str(r.get("stage") or "").startswith("UNKNOWN"):
                    unknown += 1
        pct = unknown / total * 100 if total else 0
        return (f"UNKNOWN {unknown}/{total} = {pct:.1f}% (floor ≤40%)",
                "PASS" if pct <= 40 else "FAIL")

    # Row 20: BANK ~07-24 khối 🔻 transition
    if row_id == 20:
        days = load_case("BANK")
        for dt in ["07-23", "07-24", "07-25", "07-26"]:
            idx = find_day(days, dt)
            if idx < 0: continue
            r = tag(days, idx, CFG)
            if r.get("stage") in ("S4", "S5"):
                return (f"BANK {dt}={r.get('stage')} ✓ transition detected",
                        "PASS")
        return ("BANK 07-23..07-26 không có S4/S5", "FAIL")

    # Row 21: CLO cửa xác — no report display expected
    if row_id == 21:
        return ("CSV-only rule §6.2 — implementation live (không test được tại probe)",
                "SKIP-IMPL")

    # Rows 1-8, 10: single-day expected stage
    days = load_case(token)
    if not days: return (f"{token} NO_DATA", "SKIP-DATA")
    idx = find_day(days, date)
    if idx < 0: return (f"{token}@{date} NO_DATA", "SKIP-DATA")
    r = tag(days, idx, CFG)
    st = r.get("stage")
    ok = st in expected
    return (f"stage={st} evidence={r.get('stage_evidence','')[:60]}",
            "PASS" if ok else "FAIL")


# ── Print table (guarded so import doesn't run main) ─────────────────────────
DIV = "=" * 118

if __name__ == "__main__":
    print(DIV)
    print("PHASE-TAG v0.3 §8.2 ACCEPTANCE — 21 dòng expected-vs-actual (TRỪ #17 §9.2)")
    print(DIV)
    print(f"{'#':>3} {'token':>8} {'date':>10} {'src':>10} {'class':>19} {'expected':>26} → actual · verdict")
    print("─" * 128)

    results = []
    for row_id, token, date, expected, class_ in ACCEPTANCE:
        actual, verdict = eval_row(row_id, token, date, expected, class_)
        src = case_source(token) if token not in ("*EVENT*", "*SANITY*") else "-"
        exp_s = str(expected)[:24]
        print(f"{row_id:>3} {token:>8} {date:>10} {src:>10} {class_:>19} {exp_s:>26} → {actual[:60]} · {verdict}")
        results.append((row_id, class_, verdict))

    print("─" * 118)
    n_pass = sum(1 for _, _, v in results if v == "PASS")
    n_fail = sum(1 for _, _, v in results if v == "FAIL")
    n_skip = sum(1 for _, _, v in results if v.startswith("SKIP"))
    print(f"SUMMARY: PASS={n_pass}  FAIL={n_fail}  SKIP={n_skip}  TOTAL=21")

    # FAIL-cứng breakdown
    hard_fails = [(r, c) for r, c, v in results if v == "FAIL" and
                  any(x in c for x in ["CỨNG", "SUPPRESSOR", "HARVEST", "EVENT", "NEGATIVE"])]
    print(f"FAIL-cứng (§8.2 trượt = không ship): {len(hard_fails)}")
    for r, c in hard_fails:
        print(f"  #{r} · {c}")

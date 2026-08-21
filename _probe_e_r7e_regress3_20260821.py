#!/usr/bin/env python3
"""[E-R7e-regress-3] F/G bảng + case E ep-detail + diff dự kiến on lib (no apply).

Spec v1.2-FINAL+doctrine-pack 22faf1f · probe 2ba669f.
Luật áp: tiền-extract theo consumer — registry = ae5f2a0 default, watchlist = lib.
KHÔNG sửa. Đo + soạn diff dự kiến.
"""
from __future__ import annotations
import sys, io, csv, math
from pathlib import Path
from statistics import mean, median
from datetime import date, timedelta

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
SPEC_FILE = REPO / "proposals" / "unhedge_registry_spec_v1.0.md"
AE5_FILE = Path(r"C:\Users\Hello\AppData\Local\Temp\ae5f2a0_probe.py")

DIV = "═"*96
print(f"{DIV}\n[HEADER] regress-3 · spec v1.2-FINAL+doctrine-pack 22faf1f · probe 2ba669f\n"
      f"          Luật: registry mặc-định-cũ (ae5f2a0) · watchlist mặc-định-cũ (lib bit-equal)\n{DIV}")

# ─── Load 9 tokens ────────────────────────────────────────────────────────
td = {}
TARGETS = ["HEMIUSDT","ONUSDT","GUAUSDT","CARVUSDT","ARIAUSDT","SHELLUSDT","SIGNUSDT"]
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","")
            if sym not in TARGETS: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
            })
for s in td: td[s].sort(key=lambda r: r["date"])
CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}

# ═══ (1) Bảng F/G + map A-G to 5 tokens ═════════════════════════════════
print(f"\n{DIV}\n[(1) Bảng F/G bổ sung — cùng format A-E]\n{DIV}")

print(f"""
  ── F. Eligibility trigger (b): ≤30d sau episode_break ──
    tiền-extract (ae5f2a0): L167-172  rel_ep matching:
      `if ep["start"] <= d_str <= ep.get("break_confirmed_at", ep["end"]): rel_ep = ep`
      `elif ep.get("break_confirmed_at") and ep["break_confirmed_at"] <= d_str:`
      `  gap = (d - _date.fromisoformat(ep["break_confirmed_at"])).days`
      `  if gap <= 30: rel_ep = ep`
      → Event vẫn "eligible" vào registry TRONG 30d sau episode_break, dùng episode
        vừa broken làm rel_ep để chấm (b) drift từ ep_min historic.
    lib 5c2f22d: KHÔNG có logic gap ≤30d.
      (a) chỉ fire tại flip-day. (b) chỉ fire khi ep[i]["in_hedge"]=True (còn trong hedge
      current). Post-break: không có rel_ep → 0 event.
    spec: L34-42 (§E-R1) — SPEC-IM-LẶNG cho window post-break eligibility.
    consumer: registry only. watchlist KHÔNG dùng rel_ep logic (chỉ dùng episode current).
    token/số đổi: ARIA (ep 06-27→OPEN, không break trong window → F không kích) ·
      SHELL (ep 06-27→OPEN, tương tự) · GUA (ep chuyển 07-05→07-09 → 07-16→OPEN, event
      07-10 = post-break gap=1d, ae5f2a0 dùng ep vừa broken tính (b))
    verdict: SPEC-IM-LẶNG → mặc-định-cũ (ae5f2a0) — CẦN-REVERT lib probe

  ── G. Episode window WINDOW_START-5d cutoff ──
    tiền-extract (ae5f2a0): L117-118  `d0 = _date.fromisoformat(WINDOW_START) - timedelta(days=5)`
      `filtered = [d for d in all_dates if _date.fromisoformat(d) >= d0]`
      → Episode detection CHỈ scan từ 06-16 (WINDOW_START=06-21 − 5d).
    lib 5c2f22d: (detect_episodes) scan TOÀN arr từ token first date (06-01 cho CARV/GUA/SIGN).
    spec: L153 (§E-R7) "backfill hồi tố 60d trên fw-139" — không quy định episode-detection
      scope, SPEC-IM-LẶNG.
    consumer: registry only (event detection). watchlist dùng detect_episodes trên toàn arr
      (cũng lib default) → nếu revert G → phải tách logic riêng cho registry, KHÔNG
      chạm watchlist path.
    token/số đổi: CARV (episode 06-01→08-10 có 20+d history pre-06-16 → sn khác, ep_min
      khác) · GUA (episode 06-01→06-30 pre-window → ae5f2a0 KHÔNG detect episode đó,
      lib CÓ) · SIGN (episode 06-01→06-21 pre-window)
    verdict: SPEC-IM-LẶNG → mặc-định-cũ (ae5f2a0) — CẦN-REVERT lib probe
""")

# Verify A-G explain 5 tokens: run both codes on each and map blocked reason
print(f"\n  ── Map A-G to 5 REMOVED tokens (ARIA/CARV/GUA/SHELL/SIGN) ──")

# Import ae5f2a0 analyze_token
import subprocess
if not AE5_FILE.exists():
    subprocess.run(["bash","-c",
        f"git -C '{REPO}' show ae5f2a0:_task_registry_c1_c4_20260820.py > '{AE5_FILE}'"], check=True)
ae5_src = AE5_FILE.read_text(encoding="utf-8")
start = ae5_src.find("def analyze_token")
lines = ae5_src[start:].split("\n")
end_idx = 0
for i, ln in enumerate(lines):
    if i == 0: continue
    if ln.startswith("def ") or (ln and not ln[0].isspace() and not ln.startswith("#")):
        end_idx = i; break
if end_idx == 0: end_idx = len(lines)
from datetime import date as _date, timedelta as _timedelta
exec_globals = {"defaultdict": __import__("collections").defaultdict,
                "_date": _date, "_timedelta": _timedelta, "timedelta": _timedelta,
                "median": median, "date": _date,
                "DRIFT_MIN_DEFAULT": 0.15, "STRUCT_N_MIN": 3,
                "WINDOW_START": "2026-06-21", "WINDOW_END": "2026-08-19",
                "REARM_MIN_DAYS": 14, "REARM_PX_MULT": 1.10, "REARM_OI_MULT": 1.30,
                "REARM_COOLDOWN_DAYS": 14,
                "POS_GUARD": 0.90, "PX_GUARD": 0.85}
exec("\n".join(lines[:end_idx]), exec_globals)
analyze_token_ae5 = exec_globals["analyze_token"]

def _to_dd(arr):
    return {r["date"]: {"pos_r":r["pos"], "acc_r":r["acc"], "oi":r["oi"], "px":r["px"], "vol":r["vol"]} for r in arr}

REMOVED = ["ARIAUSDT","CARVUSDT","GUAUSDT","SHELLUSDT","SIGNUSDT"]
print(f"  {'token':>12}  {'ae5f2a0 events':>14}  {'blocked case (lib 5c2f22d)':>50}")
print("  " + "─"*80)
for sym in REMOVED:
    if sym not in td: continue
    arr = td[sym]; ep = detect_episodes(arr, CFG)
    ae5_evs = analyze_token_ae5(sym, _to_dd(arr), drift_min=0.15, struct_n_min=3)
    # lib candidates: check each day if event triggers (before sn/pos/px)
    lib_blocks = []
    for i in range(5, len(arr)):
        d = arr[i]["date"]
        if not ("2026-06-21" <= d <= "2026-08-19"): continue
        trig=None; hspx=None
        if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
            trig="a"; hspx=ep[i-1]["hedge_start_px"]
        elif ep[i]["in_hedge"]:
            eid=ep[i]["episode_id"]; sj=i
            for k in range(i, max(-1,i-30)-1, -1):
                if ep[k].get("episode_id")==eid and ep[k]["in_hedge"]: sj=k
                else: break
            mn=None; mi=None
            for k in range(sj, i+1):
                dv=calc_div(arr,k)
                if ok(dv) and (mn is None or dv<mn): mn=dv; mi=k
            if mn is not None:
                cur=calc_div(arr,i)
                if ok(cur):
                    dr=cur-mn; ds=i-mi
                    if dr>=0.15 and 0<ds<=7:
                        trig="b"; hspx=ep[i]["hedge_start_px"]
        if trig is None: continue
        # pos check
        pos_cur = arr[i].get("pos", NaN)
        vs = [arr[j]["pos"] for j in range(max(0,i-5),i) if ok(arr[j]["pos"])]
        pos_ok_val = ok(pos_cur) and len(vs)>=3 and pos_cur >= 0.90*mean(vs)
        # px check
        px_cur = arr[i].get("px", NaN)
        px_ok_val = ok(px_cur) and hspx and ok(hspx) and px_cur >= 0.85*hspx
        if not pos_ok_val: block = f"C(pos) {d}"; break
        if not px_ok_val: block = f"D(px) {d}"; break
        lib_blocks.append(f"PASS {d}")
    else:
        block = "no event candidate (episode/drift/window logic)"
    n_ae5 = len(ae5_evs) if ae5_evs else 0
    ae5_str = f"{n_ae5} ({ae5_evs[0]['unhedge_date'] if n_ae5 else '-'} trig={ae5_evs[0]['trigger'] if n_ae5 else '-'})" if n_ae5 else "0"
    print(f"  {sym[:12]:>12}  {ae5_str:>14}  {block[:50]:>50}")

print(f"""
  ── Explains A-G (registry consumer) ──
    ARIA:  ae5f2a0 event 07-06 (trig=b, post-break gap ≤30d rel_ep) blocked by F (lib=no gap)
    CARV:  ae5f2a0 event 07-04 (trig=b, sn=48) blocked by D (px<0.85) in lib
    GUA:   ae5f2a0 event 07-10 (trig=b) blocked by F+G (lib G scans wider episode, F post-break)
    SHELL: ae5f2a0 event 07-06 (trig=b, post-break) blocked by F (lib=no gap logic)
    SIGN:  ae5f2a0 0 events (both same) — SIGN removal có thể do ae5f2a0 baseline PRE-08-18 data
           (data change) hoặc SIGN never in ae5f2a0 baseline. Cần verify — nghi CA-H (data-only)
    Còn dư SIGN → NGHI ca H (data-drift), không gom vào A-G.
""")

# ═══ (2) Case E struct_n detail HEMI/ON/GUA/CARV ep_start/end/gap/count/ep_len ═══
print(f"\n{DIV}\n[(2) struct_n dual-def detail HEMI/ON/GUA/CARV — ep boundaries]\n{DIV}")

def _episode_detail(arr, ep, event_idx):
    """Extract episode of interest at event_idx: start_i, end_i, gap_days, count_le050, ep_len."""
    # walk back
    if event_idx>=1 and ep[event_idx-1]["in_hedge"] and not ep[event_idx]["in_hedge"]:
        # (a) trigger — use ep[i-1] as anchor
        target_i = event_idx - 1
    elif ep[event_idx]["in_hedge"]:
        target_i = event_idx
    else:
        return None
    eid = ep[target_i]["episode_id"]; sj = target_i
    for k in range(target_i, -1, -1):
        if ep[k].get("episode_id")==eid and ep[k]["in_hedge"]: sj = k
        else: break
    ej = target_i
    count_le050 = 0; gap_days = 0
    for k in range(sj, ej+1):
        dv = calc_div(arr, k)
        if ok(dv):
            if dv <= 0.5: count_le050 += 1
            else: gap_days += 1
    ep_len = ej - sj + 1
    return {"start_date": arr[sj]["date"], "end_date": arr[ej]["date"],
            "gap_days": gap_days, "count_le050": count_le050, "ep_len": ep_len}

for sym in ["HEMIUSDT","ONUSDT","GUAUSDT","CARVUSDT"]:
    if sym not in td: continue
    arr = td[sym]; ep = detect_episodes(arr, CFG)
    print(f"\n  ── {sym} ──")
    print(f"    {'date':>12}  {'trig':>4}  {'ep_start':>10}  {'ep_end':>10}  "
          f"{'gap':>3}  {'≤0.50':>5}  {'ep_len':>6}  {'sn_ae5':>6}  {'sn_lib':>6}  {'Δ':>3}")
    events = []
    for i in range(5, len(arr)):
        d = arr[i]["date"]
        if not ("2026-06-21" <= d <= "2026-08-19"): continue
        trig=None
        if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
            trig="a"
        elif ep[i]["in_hedge"]:
            eid=ep[i]["episode_id"]; sj=i
            for k in range(i, max(-1,i-30)-1, -1):
                if ep[k].get("episode_id")==eid and ep[k]["in_hedge"]: sj=k
                else: break
            mn=None; mi=None
            for k in range(sj, i+1):
                dv=calc_div(arr,k)
                if ok(dv) and (mn is None or dv<mn): mn=dv; mi=k
            if mn is not None:
                cur=calc_div(arr,i)
                if ok(cur):
                    dr=cur-mn; ds=i-mi
                    if dr>=0.15 and 0<ds<=7:
                        trig="b"
        if trig is None: continue
        det = _episode_detail(arr, ep, i)
        if det is None: continue
        sn_ae5 = det["count_le050"]
        # sn_lib
        if trig=="a":
            sn_lib = ep[i-1]["struct_n"]
        else:
            sn_lib = ep[i]["struct_n"]
        delta = sn_lib - sn_ae5
        print(f"    {d:>12}  {trig:>4}  {det['start_date']:>10}  {det['end_date']:>10}  "
              f"{det['gap_days']:>3}  {det['count_le050']:>5}  {det['ep_len']:>6}  "
              f"{sn_ae5:>6}  {sn_lib:>6}  {delta:>+3}")

# ═══ (3) Diff dự kiến on lib for B/C/F/G — no apply, prove no watchlist touch ═══
print(f"\n{DIV}\n[(3) Diff dự kiến MẶC-ĐỊNH-CŨ (B/C/F/G) · CHƯA APPLY · chứng KHÔNG chạm watchlist]\n{DIV}")

print(f"""
  ── Watchlist consumer path (không được chạm) ──
    watchlist_daily.py imports:
      L107-158: def avg3, def calc_div, def detect_episodes  (INLINE, bit-equal lib)
    Watchlist DOES NOT call:
      _detect_ev  (probe registry only)
      _try_rearm  (probe registry only)
      _pos_ok / _px_ok  (probe registry only, name may differ in lib)
      _cur_ep_min  (probe registry only)
      rel_ep matching (registry only, absent from lib)
      WINDOW_START filtering (registry only)

  ── B. (b) trigger require v ≤ 0.5 ──
    Target: _probe_registry_backfill_e_r7e_20260821.py::_detect_ev  (registry probe only)
    Diff dự kiến (registry probe, KHÔNG chạm lib):
      Line ~180-190 in _detect_ev:
      -   if dr >= DRIFT_THR and 0 < ds <= DRIFT_WIN:
      -       trig="b"; sn=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
      +   if dr >= DRIFT_THR and 0 < ds <= DRIFT_WIN and cur <= 0.5:
      +       trig="b"; sn=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
    Watchlist touch: NONE (watchlist doesn't call _detect_ev)
    Chứng: grep -n "_detect_ev\\|trig.*=.*b" scripts/watchlist_daily.py → 0 matches

  ── C. avg5 pre-event calendar-based (thay index) ──
    Target: _probe_registry_backfill_e_r7e_20260821.py::_pos_ok  (registry probe only)
    Diff dự kiến:
      -   vs = [arr[j]["pos"] for j in range(max(0,i-5),i) if ok(arr[j]["pos"])]
      +   from datetime import date as _d, timedelta as _td
      +   event_d = _d.fromisoformat(arr[i]["date"])
      +   vs = []
      +   for k in range(1, 6):
      +       target_d = (event_d - _td(days=k)).isoformat()
      +       row = next((x for x in arr if x["date"] == target_d), None)
      +       if row and ok(row["pos"]): vs.append(row["pos"])
    Watchlist touch: NONE (watchlist has its own pos_trend not pos_hold)
    Chứng: grep -n "pos_hold\\|POS_HOLD\\|_pos_ok" scripts/watchlist_daily.py → 0 matches

  ── F. eligibility gap ≤30d post-break ──
    Target: _probe_registry_backfill_e_r7e_20260821.py::_detect_ev  (registry probe only)
    Diff dự kiến: thêm block sau (a)/(b) initial check
      +   # ae5f2a0 F: allow (b) trigger up to 30d after break
      +   if trig is None and i>=1:
      +       # walk back for last broken episode
      +       for j in range(i-1, max(-1, i-30)-1, -1):
      +           if ep[j]["in_hedge"] and (j==i-1 or not ep[j+1]["in_hedge"]):
      +               # j is last in_hedge day of previous episode
      +               eid_prev = ep[j]["episode_id"]
      +               # gap = i - j
      +               gap = i - j
      +               if gap <= 30:
      +                   # compute ep_min from that episode
      +                   ...
      +                   trig = "b"; hspx = ep[j]["hedge_start_px"]; sn = ep[j]["struct_n"]
      +                   break
    Watchlist touch: NONE (watchlist episodes are current only, no post-break tolerance)
    Chứng: grep -n "gap.*30\\|break_confirmed\\|rel_ep" scripts/watchlist_daily.py → 0 matches

  ── G. Episode window WINDOW_START-5d cutoff ──
    Target: _probe_registry_backfill_e_r7e_20260821.py — pre-episode filter
    Diff dự kiến (registry probe only):
      -   ep = detect_episodes(arr, CFG)
      +   from datetime import date as _d, timedelta as _td
      +   cutoff = (_d.fromisoformat(WINDOW_START) - _td(days=5)).isoformat()
      +   arr_win = [r for r in arr if r["date"] >= cutoff]
      +   ep_win = detect_episodes(arr_win, CFG)
      +   # then use arr_win + ep_win for _detect_ev calls
    Watchlist touch: **CAUTION** — watchlist calls `detect_episodes(arr, cfg)` on FULL arr,
      NOT windowed. If we introduce windowing to lib → watchlist LỆCH. So keep in registry
      probe only, DO NOT modify lib.
    Chứng: grep -n "detect_episodes" scripts/watchlist_daily.py → L241
       "ep = ep_cache[sym] if ep_cache else detect_episodes(arr, cfg)" — uses full arr
    Verdict: G diff registry-side ONLY, lib untouched.

  ── E. struct_n (TREO chờ ANALYSIS Q1) ──
    Nếu ANALYSIS chốt sn = count(div≤0.5) (ae5f2a0):
      Diff on lib.detect_episodes: THAY sn = i - ep_start_i + 1 BẰNG sn = count(days ≤0.5)
      → WATCHLIST CHẠM (watchlist inline copy sẽ diverge với lib nếu edit lib)
      → CẤM edit lib.detect_episodes trực tiếp
      → Fix: thêm computed field `sn_count_le050` trong lib.detect_episodes (mới, không xóa cũ)
        + registry probe dùng `sn_count_le050`; watchlist tiếp tục dùng `struct_n` cũ
    Nếu ANALYSIS chốt sn = ep_len (lib hiện tại): no diff cần.
""")

print(f"\n{DIV}\nDONE. Chờ ANALYSIS Q1-Q3 + operator ký revert.\n{DIV}")

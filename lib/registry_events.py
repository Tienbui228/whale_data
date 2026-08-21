"""lib/registry_events.py — SHARED registry event detection (A4(2) revision 21/08).

Consumer: registry backfill probes + phase-2 GOM-E cron. Watchlist KHÔNG import
module này (P0 SAFE — grep bằng chứng, xem docstring commit msg).

Canonical semantics per §E-R1 conformance-pack (proposals/unhedge_registry_spec_v1.0.md
v1.2-FINAL+doctrine-pack+conformance-pack, commit fe4e38c) + regress-3 A-H
(_probe_e_r7e_regress3_20260821.py 591b1cb) + A4(2) new cases I-K per ae5f2a0 diff.

Cases A-H (A1 21/08):
  B. (b) drift trigger REQUIRE cur_div ≤ div_ratio_max tại ngày event.
  C. pos_hold guard dùng avg5 CALENDAR d-k (k=1..5), KHÔNG index i-5..i-1.
  F. Eligibility hậu-break: ep vừa BREAK làm anchor cho (b) TRONG ≤30d hậu-break.
  G. Episode window pre-filter: cắt arr về `arr >= WINDOW_START - 5d` trước detect.

Cases I-L (A4(2) 21/08 — match ae5f2a0 backfill semantics):
  I. (b) drift baseline = LOCAL drift_win-day recent min (chỉ scan vv≤0.5 trong
     [i-drift_win, i)), KHÔNG dùng full-ep min với ds≤7 constraint. Fix diff:
     GUA 08-10, ARIA 07-21, SHELL 08-12 (mine full-ep min ds>7 nên skip; ae5 local trig).
  J. (b) sn = FULL ep count (backfill semantic — includes days AFTER event i lên đến
     ep_end / broken / open), KHÔNG dùng running sn_count_le050 tại i. Fix diff:
     CARV sn=49 vs 12 (mine running vs ae5 full ep).
  K. Episode detection REGISTRY-SPECIFIC: REQUIRE 3-sample div (skip first 2 rows of
     arr_win). Fix diff: SIGN ep_start 06-17 vs 06-16, ARIA 06-29 vs 06-27, CARV 06-17
     vs 06-16 (mine avg3 partial, ae5 requires 3). Impl in `_detect_episodes_registry`
     — NOT `lib.hedge_episode.detect_episodes` (giữ bit-equal watchlist inline).
  L. Dedup (b) events per (sym, hedge_start, trigger) — keep FIRST only per episode.
     Ae5f2a0 semantic: mỗi episode chỉ 1 event 'b'. Fix diff: CARV 06-27+28+30/b,
     GUA 08-10+11/b, SHELL 08-12..17/b → mỗi ep chỉ giữ 1 event 'b' đầu. Impl in
     `dedup_b_events()` helper — caller phải gọi sau khi scan _detect_ev qua all i.

Consumer split (§E-R1 conformance):
  registry: sn_count_le050 via `_detect_episodes_registry`
  watchlist: struct_n via `lib.hedge_episode.detect_episodes` (bit-equal inline)

D1-PHASE1-20260821 DEPRECATION NOTE (operator ký chat 21/08):
  Field `struct_n` DEPRECATED — target xóa Phase 3 cutover 2026-09-30.
  Canonical field: `ep_len` (semantics struct_n legacy) + `sn_count_le050` (canonical count).
  `_detect_ev` fallback `ep[i-1].get("sn_count_le050", ep[i-1]["struct_n"])` sẽ bị
  đổi sang fail-loud (đọc thẳng `ep[i-1]["sn_count_le050"]`, KeyError = bài L-51)
  trong Phase 2 (per D1-SIGNED-20260821 Sửa 2).
  Ref: proposals/d1_migration_struct_n_deprecate_20260821.md.
"""
from __future__ import annotations
import hashlib
import os
import subprocess
from pathlib import Path
from statistics import mean
from datetime import date as _date, timedelta as _td

from lib.hedge_episode import detect_episodes, calc_div, NaN, ok


# ── D4 header (ER-HOME 21/08 luật): mọi probe/gate BẮT BUỘC gọi _run_header() đầu run ──
SPEC_PATH_CANONICAL = "D:/Data back test/whale_data/proposals/unhedge_registry_spec.md"
SPEC_VERSION_CANONICAL = "v1.2-FINAL+doctrine-pack+conformance-pack"
AMENDMENTS_APPLIED = ["46db911", "fe4e38c"]   # E-R4b v1.2-FINAL + conformance-pack


def _md5(path):
    """MD5 of a file (utf-8 or binary), return None if not exist."""
    p = Path(path)
    if not p.exists():
        return None
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _git_short(repo_root, *paths):
    """Short SHA of last commit touching paths in repo_root."""
    try:
        args = ["git", "-C", str(repo_root), "log", "-1", "--format=%h", "--"] + list(paths)
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "?"


def _run_header(consumer, snapshot_date, fixture_path=None, extra=None,
                spec_path=SPEC_PATH_CANONICAL,
                spec_version=SPEC_VERSION_CANONICAL,
                amendments=None, repo_root=None):
    """Return dict + printable header for gate/probe run (D4-header canonical).

    Fields (per operator D4 21/08):
      spec_path         — path tuyệt đối tới spec canonical §E-R
      spec_version      — canonical version string
      amendments_applied — list of commit SHAs ký amendment (default [46db911, fe4e38c])
      lib_commit        — last commit touching lib/registry_events.py + hedge_episode.py
      fixture_md5       — md5 of tests/fixtures/<consumer>_conformance_*.json (nếu có)
      snapshot_date     — YYYY-MM-DD of data snapshot pin
      consumer          — 'registry' | 'watchlist' | 'phase_tag' | probe name

    Every consumer gate run MUST call:
        from lib.registry_events import _run_header, print_header
        hdr = _run_header(consumer='registry', snapshot_date='2026-08-19',
                          fixture_path='tests/fixtures/registry_conformance_20260821.json')
        print_header(hdr)

    Header printed at STDOUT top, dict returned for JSON provenance.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    if amendments is None:
        amendments = list(AMENDMENTS_APPLIED)
    lib_commit = _git_short(repo_root, "lib/registry_events.py", "lib/hedge_episode.py")
    fixture_md5 = _md5(fixture_path) if fixture_path else None
    hdr = {
        "consumer":            consumer,
        "spec_path":           spec_path,
        "spec_version":        spec_version,
        "amendments_applied":  amendments,
        "lib_commit":          lib_commit,
        "fixture_path":        str(fixture_path) if fixture_path else None,
        "fixture_md5":         fixture_md5,
        "snapshot_date":       snapshot_date,
    }
    if extra:
        hdr.update(extra)
    return hdr


def print_header(hdr):
    """Print run header to STDOUT (D4 canonical format)."""
    div = "═" * 96
    print(div)
    print(f"[D4 HEADER — {hdr.get('consumer','?')} gate run]")
    print(div)
    print(f"  spec_path           : {hdr.get('spec_path')}")
    print(f"  spec_version        : {hdr.get('spec_version')}")
    print(f"  amendments_applied  : {hdr.get('amendments_applied')}")
    print(f"  lib_commit          : {hdr.get('lib_commit')}")
    print(f"  fixture_path        : {hdr.get('fixture_path')}")
    print(f"  fixture_md5         : {hdr.get('fixture_md5')}")
    print(f"  snapshot_date       : {hdr.get('snapshot_date')}")
    for k, v in hdr.items():
        if k in ("consumer", "spec_path", "spec_version", "amendments_applied",
                 "lib_commit", "fixture_path", "fixture_md5", "snapshot_date"):
            continue
        print(f"  {k:<20}: {v}")
    print(div)


# ── Defaults (per spec v1.2-FINAL+doctrine-pack+conformance-pack) ───────────
DRIFT_THR = 0.15
DRIFT_WIN = 7
POS_HOLD  = 0.90
PX_HOLD   = 0.85
CFG_DEFAULT = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
POST_BREAK_MAX_DAYS = 30    # case F: (b) eligibility window post-break
WINDOW_PREFILTER_LB = 5     # case G: arr cutoff = WINDOW_START - 5d


# ── C. avg5 pre-event calendar-based ────────────────────────────────────────
def _pos_ok(arr, i, pos_hold=POS_HOLD):
    """Case C: pos_hold guard dùng avg5 CALENDAR d-k (k=1..5), không index.

    Rationale: khi arr có gap ngày (partial daily), i-5..i-1 index có thể trỏ ngày
    cách event >5d thực tế → lệch baseline. Calendar-based avg5 = trung bình pos_r
    của các ngày YYYY-MM-DD trong 5 ngày lịch trước ngày event, skip ngày thiếu.
    """
    cur = arr[i].get("pos", NaN)
    if not ok(cur):
        return False
    try:
        event_d = _date.fromisoformat(arr[i]["date"])
    except Exception:
        return False
    date_idx = {r["date"]: r for r in arr}
    vs = []
    for k in range(1, 6):
        td_s = (event_d - _td(days=k)).isoformat()
        row = date_idx.get(td_s)
        if row and ok(row.get("pos", NaN)):
            vs.append(row["pos"])
    if len(vs) < 3:
        return False
    return cur >= pos_hold * mean(vs)


def _px_ok(arr, i, hspx, px_hold=PX_HOLD):
    cur = arr[i].get("px", NaN)
    return ok(cur) and hspx is not None and ok(hspx) and cur >= px_hold * hspx


# ── Helper: ep_min from an episode window ───────────────────────────────────
def _ep_min_div(arr, ep, start_i, end_i, eid):
    """Return (min_div, min_i) trên các ngày in_hedge cùng eid trong [start_i, end_i]."""
    mn = None
    mi = None
    for j in range(start_i, end_i + 1):
        if ep[j].get("episode_id") != eid or not ep[j]["in_hedge"]:
            continue
        dv = calc_div(arr, j)
        if ok(dv) and (mn is None or dv < mn):
            mn = dv
            mi = j
    return mn, mi


def _cur_ep_min(arr, ep, i, lb=30):
    """Current-episode min div (walk back from i within same episode_id)."""
    if not ep[i]["in_hedge"]:
        return None
    eid = ep[i]["episode_id"]
    sj = i
    for j in range(i, max(-1, i - lb) - 1, -1):
        if ep[j].get("episode_id") == eid and ep[j]["in_hedge"]:
            sj = j
        else:
            break
    mn, mi = _ep_min_div(arr, ep, sj, i, eid)
    if mn is None:
        return None
    return {"start_i": sj, "min_i": mi, "min_div": mn}


# ── Case I. Local drift_win-day recent min (ae5f2a0 semantics) ──────────────
def _local_recent_min(arr, ep, i, drift_win, eid, div_ratio_max=0.5):
    """Case I: min(div_avg3) trên các ngày trong [i-drift_win, i) VỚI vv≤div_ratio_max
    cùng episode_id eid. Trả None nếu không có sample thỏa.

    Ae5f2a0 semantic: `recent = [(dd, vv) for dd, vv in rel_ep["vals"]
                              if lookback_start <= _date.fromisoformat(dd) < d and vv <= 0.5]`
    Ep vals include cả gap-days (vv>0.5) và in_hedge days. Filter vv≤0.5 → chỉ những
    ngày div_avg3 ≤ 0.5 tham gia. Mirror với `_ep_min_div` restricted to same ep and
    time-window [i-drift_win, i).
    """
    mn = None
    mi = None
    for j in range(max(0, i - drift_win), i):
        if ep[j].get("episode_id") != eid:
            continue
        # ae5 vals include gap-days but filters vv ≤ 0.5 for min. So we compute div and check.
        dv = calc_div(arr, j)
        if ok(dv) and dv <= div_ratio_max and (mn is None or dv < mn):
            mn = dv
            mi = j
    return mn, mi


# ── Case J. Full-ep sn count (backfill semantic — includes future days rel event) ──
def _full_ep_sn(ep, i, eid):
    """Return count(div ≤ div_ratio_max) trong TOÀN episode có id=eid.

    Walks both forward and backward from i within same eid to find ep boundaries,
    then returns sn_count_le050 at ep end (which is the running count at ep-end =
    full ep count).
    """
    # Walk forward to find end_i
    ej = i
    for j in range(i, len(ep)):
        if ep[j].get("episode_id") == eid and ep[j]["in_hedge"]:
            ej = j
        elif ep[j].get("episode_id") == eid:
            # gap-day in current ep, keep going
            continue
        else:
            break
    return ep[ej].get("sn_count_le050", 0)


# ── B + F. Event detection ─────────────────────────────────────────────────
def _detect_ev(arr, ep, i, sn_min, window_start, window_end,
               drift_thr=DRIFT_THR, drift_win=DRIFT_WIN,
               div_ratio_max=0.5, post_break_max_days=POST_BREAK_MAX_DAYS):
    """Detect (a)/(b) event tại arr[i], per canonical §E-R1 conformance.

    Returns dict {i, date, trig, sn, hspx, ep_min, rel_ep_id, rel_ep_kind} or None.

    - trig='a': flip in_hedge → break, chấm tại ngày flip. sn = sn_count_le050 của ep vừa broken.
    - trig='b': drift ≥ drift_thr trong ≤ drift_win ngày, cur_div ≤ div_ratio_max (case B).
        · rel_ep_kind='current'  → ep[i]["in_hedge"]=True, dùng current-ep min.
        · rel_ep_kind='post_break' (case F) → hậu-break ≤ post_break_max_days, dùng
          ep vừa broken làm anchor, ep_min tra từ episode broken.

    sn_min filter chỉ áp trigger 'a' (per operator instr E-R7d/E-R7e).
    """
    d = arr[i]["date"]
    if not (window_start <= d <= window_end):
        return None
    if i < 5:
        return None

    trig = None
    sn = None
    hspx = None
    ep_min = None
    rel_ep_id = None
    rel_ep_kind = None

    # (a) flip: yesterday in_hedge, today not → break at i
    if i >= 1 and ep[i - 1]["in_hedge"] and not ep[i]["in_hedge"]:
        trig = "a"
        sn = ep[i - 1].get("sn_count_le050", ep[i - 1]["struct_n"])
        hspx = ep[i - 1]["hedge_start_px"]
        rel_ep_id = ep[i - 1]["episode_id"]
        rel_ep_kind = "flip"
        eid = ep[i - 1]["episode_id"]
        vals = []
        for j in range(i - 1, -1, -1):
            if ep[j].get("episode_id") == eid and ep[j]["in_hedge"]:
                dv = calc_div(arr, j)
                if ok(dv):
                    vals.append(dv)
            else:
                break
        ep_min = min(vals) if vals else NaN

    # (b) drift: trong current episode — case I local drift_win-day recent min
    if trig is None and ep[i]["in_hedge"]:
        eid = ep[i]["episode_id"]
        mn, mi = _local_recent_min(arr, ep, i, drift_win, eid, div_ratio_max)
        if mn is not None and mi is not None:
            cur = calc_div(arr, i)
            if ok(cur):
                dr = cur - mn
                # Case B: require cur ≤ div_ratio_max. ds constraint implicit
                # trong _local_recent_min (only [i-drift_win, i)).
                if dr >= drift_thr and cur <= div_ratio_max:
                    trig = "b"
                    # Case J: sn = FULL ep count (backfill semantic)
                    sn = _full_ep_sn(ep, i, eid)
                    hspx = ep[i]["hedge_start_px"]
                    ep_min = mn
                    rel_ep_id = eid
                    rel_ep_kind = "current"

    # Case F: post-break eligibility ≤30d (only if not already trig'd + not in_hedge)
    if trig is None and not ep[i]["in_hedge"]:
        # walk back to find last day in previous episode
        last_in_j = None
        for j in range(i - 1, max(-1, i - post_break_max_days) - 1, -1):
            if ep[j]["in_hedge"]:
                last_in_j = j
                break
        if last_in_j is not None:
            gap = i - last_in_j
            if 0 < gap <= post_break_max_days:
                eid_prev = ep[last_in_j]["episode_id"]
                # Case I applied post-break: local drift_win min in prev ep
                mn, mi = _local_recent_min(arr, ep, i, drift_win, eid_prev, div_ratio_max)
                if mn is not None and mi is not None:
                    cur = calc_div(arr, i)
                    if ok(cur):
                        dr = cur - mn
                        if dr >= drift_thr and cur <= div_ratio_max:
                            trig = "b"
                            # Case J: sn = FULL ep count of the BROKEN episode
                            sn = _full_ep_sn(ep, last_in_j, eid_prev)
                            hspx = ep[last_in_j]["hedge_start_px"]
                            ep_min = mn
                            rel_ep_id = eid_prev
                            rel_ep_kind = "post_break"

    if trig is None:
        return None

    # sn_min filter: chỉ áp trigger 'a' (canonical §E-R1 conformance §note)
    if trig == "a" and sn is not None and sn < sn_min:
        return None

    if not (_pos_ok(arr, i) and _px_ok(arr, i, hspx)):
        return None

    return {
        "i": i, "date": d, "trig": trig, "sn": sn, "hspx": hspx, "ep_min": ep_min,
        "rel_ep_id": rel_ep_id, "rel_ep_kind": rel_ep_kind,
    }


# ── L. Dedup (b) events per (episode + trigger) — keep first ─────────────────
def dedup_b_events(events, sym=None):
    """Case L: dedup (b) trigger events per (sym, rel_ep_id, 'b') — keep FIRST only.

    Ae5f2a0 semantic: mỗi episode chỉ 1 event 'b' (drift). (a) trigger không dedup.
    Caller iterate all i, tích events; sau đó gọi hàm này để dedup trước khi ghi
    registry / append CSV.

    Args:
      events: list of dict (output từ _detect_ev), sorted by i ascending.
      sym: optional symbol str (nếu multi-token merge, cho vào key).

    Returns:
      list dedup'd giữ thứ tự.
    """
    dedup = []
    seen = set()
    for e in events:
        if e.get("trig") != "b":
            dedup.append(e)
            continue
        # Key = (sym, rel_ep_id, 'b'). Nếu rel_ep_id None (edge case), fallback hspx.
        rel_id = e.get("rel_ep_id")
        key = (sym, rel_id if rel_id is not None else e.get("hspx"), "b")
        if key in seen:
            continue
        seen.add(key)
        dedup.append(e)
    return dedup


# ── K. Registry-specific episode detection (require 3-sample div) ────────────
def _detect_episodes_registry(arr, cfg, skip_first=2):
    """Case K: episode detection matching ae5f2a0 semantics.

    Differences from `lib.hedge_episode.detect_episodes`:
    - Skip first `skip_first` rows (calc_div requires 3-sample, first 2 rows partial).
    - Require ALL 3 samples valid non-NaN for div_avg3 (ae5f2a0: `if i < 2: continue`).

    Otherwise same: gap-tolerance ep_break_days, hedge_start_px CỐ ĐỊNH per ep,
    sn_count_le050 count(div ≤ div_ratio_max in ep).

    D1-PHASE1-20260821 DEPRECATION NOTE: `struct_n` field trong output dict
    DEPRECATED — target xóa Phase 3 cutover 2026-09-30. Use `ep_len` canonical.

    Only used by registry consumer via `window_prefilter_and_detect`. Watchlist inline
    uses `lib.hedge_episode.detect_episodes` (bit-equal preserved).
    """
    div_max = cfg["hedge"]["div_ratio_max"]
    ep_break = cfg["hedge"]["episode_break_days"]

    out = []
    ep_id = 0
    ep_si = None
    ep_spx = None
    in_hedge = False
    n_above = 0
    sn_count = 0

    for i, row in enumerate(arr):
        # Case K: skip first N rows (no 3-sample div)
        if i < skip_first:
            out.append({
                "in_hedge": False, "episode_id": 0,
                "hedge_start_date": "", "hedge_start_px": None,
                "struct_n": 0, "ep_len": 0, "sn_count_le050": 0,
            })
            continue

        # Require full 3 samples for div (ae5f2a0 semantic)
        p3 = [arr[j]["pos"] for j in range(i - 2, i + 1) if ok(arr[j]["pos"])]
        a3 = [arr[j]["acc"] for j in range(i - 2, i + 1) if ok(arr[j]["acc"])]
        if len(p3) < 3 or len(a3) < 3:
            dr = NaN
        else:
            a3a = sum(a3) / 3
            dr = (sum(p3) / 3) / a3a if a3a > 0 else NaN

        if ok(dr) and dr <= div_max:
            if not in_hedge:
                ep_id += 1
                ep_si = i
                ep_spx = row["px"] if ok(row["px"]) else None
                sn_count = 0
            in_hedge = True
            n_above = 0
            sn_count += 1
        else:
            if in_hedge:
                n_above += 1
                if n_above >= ep_break:
                    in_hedge = False
                    n_above = 0
                    sn_count = 0

        sn = (i - ep_si + 1) if (in_hedge and ep_si is not None) else 0
        out.append({
            "in_hedge":         in_hedge,
            "episode_id":       ep_id if in_hedge else 0,
            "hedge_start_date": arr[ep_si]["date"] if (in_hedge and ep_si is not None) else "",
            "hedge_start_px":   ep_spx if in_hedge else None,
            "struct_n":         sn,
            "ep_len":           sn,
            "sn_count_le050":   sn_count if in_hedge else 0,
        })
    return out


# ── G + K. Window pre-filter + registry episode detection ────────────────────
def window_prefilter_and_detect(arr, window_start, cfg=None, lb_days=WINDOW_PREFILTER_LB):
    """Case G + K: cắt arr về `arr >= window_start - lb_days` TRƯỚC khi detect episodes,
    dùng `_detect_episodes_registry` (case K, 3-sample div requirement matching ae5).

    Returns (arr_win, ep_win). Consumer registry gọi hàm này thay vì
    `detect_episodes(arr_full, cfg)` — tránh lịch sử pre-window nuốt semantics + đảm
    bảo ep_start chỉ tại ngày có 3-sample div đầy đủ (match ae5f2a0 backfill).

    Watchlist KHÔNG gọi hàm này (uses full arr với lib.hedge_episode.detect_episodes).
    """
    if cfg is None:
        cfg = CFG_DEFAULT
    try:
        cutoff = (_date.fromisoformat(window_start) - _td(days=lb_days)).isoformat()
    except Exception:
        cutoff = window_start
    arr_win = [r for r in arr if r.get("date", "") >= cutoff]
    ep_win = _detect_episodes_registry(arr_win, cfg, skip_first=2)
    return arr_win, ep_win

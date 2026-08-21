"""lib/registry_events.py — SHARED registry event detection (A1 canonical revert 21/08).

Consumer: registry backfill probes + phase-2 GOM-E cron. Watchlist KHÔNG import
module này (P0 SAFE — grep bằng chứng, xem docstring commit msg).

Canonical semantics per §E-R1 conformance-pack (proposals/unhedge_registry_spec_v1.0.md
v1.2-FINAL+doctrine-pack+conformance-pack, commit fe4e38c) + regress-3 cases A-H
(_probe_e_r7e_regress3_20260821.py commit 591b1cb):

  B. (b) drift trigger REQUIRE cur_div ≤ 0.5 tại ngày event (tránh flip false-positive
     khi drift đo qua ngày gap-tolerated ep_break < 3d).
  C. pos_hold guard dùng avg5 CALENDAR d-k (k=1..5), KHÔNG index i-5..i-1 — tránh
     lệch khi có date-gap trong arr (partial daily).
  F. Eligibility hậu-break: episode vừa BREAK vẫn dùng làm anchor cho (b) drift TRONG
     ≤30d hậu-break — tra ep_min historic của episode broken để chấm drift, hspx/sn
     lấy từ ep vừa broken.
  G. Episode window pre-filter: registry gọi `window_prefilter_and_detect(arr, WINDOW_START)`
     → cắt arr về `arr >= WINDOW_START - 5d` TRƯỚC khi gọi detect_episodes → episode
     detection chỉ scan trong window (không nuốt lịch sử pre-window).

E. sn_min filter (chỉ áp cho trigger 'a', per operator spec §E-R1 conformance):
     dùng `sn_count_le050` (count(div_avg3 ≤ 0.5) trong ep), KHÔNG dùng `struct_n`
     (= ep_len legacy incl gap-days). Watchlist inline vẫn dùng struct_n cũ cho List A
     filter — split consumer canonical §E-R1.
"""
from __future__ import annotations
from statistics import mean
from datetime import date as _date, timedelta as _td

from lib.hedge_episode import detect_episodes, calc_div, NaN, ok


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

    # (b) drift: trong current episode
    if trig is None and ep[i]["in_hedge"]:
        info = _cur_ep_min(arr, ep, i)
        if info and info["min_i"] is not None and info["min_div"] is not None:
            cur = calc_div(arr, i)
            if ok(cur):
                dr = cur - info["min_div"]
                ds = i - info["min_i"]
                # Case B: require cur ≤ div_ratio_max
                if dr >= drift_thr and 0 < ds <= drift_win and cur <= div_ratio_max:
                    trig = "b"
                    sn = ep[i].get("sn_count_le050", ep[i]["struct_n"])
                    hspx = ep[i]["hedge_start_px"]
                    ep_min = info["min_div"]
                    rel_ep_id = ep[i]["episode_id"]
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
                # scan episode broken: find start_i by walking back within same eid
                sj = last_in_j
                for j in range(last_in_j, -1, -1):
                    if ep[j].get("episode_id") == eid_prev and ep[j]["in_hedge"]:
                        sj = j
                    else:
                        break
                mn, mi = _ep_min_div(arr, ep, sj, last_in_j, eid_prev)
                if mn is not None and mi is not None:
                    cur = calc_div(arr, i)
                    if ok(cur):
                        dr = cur - mn
                        ds = i - mi
                        # Case B still applies: cur ≤ div_ratio_max
                        if dr >= drift_thr and 0 < ds <= drift_win and cur <= div_ratio_max:
                            trig = "b"
                            sn = ep[last_in_j].get("sn_count_le050", ep[last_in_j]["struct_n"])
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


# ── G. Window pre-filter + episode detection ────────────────────────────────
def window_prefilter_and_detect(arr, window_start, cfg=None, lb_days=WINDOW_PREFILTER_LB):
    """Case G: cắt arr về `arr >= window_start - lb_days` TRƯỚC khi detect_episodes.

    Returns (arr_win, ep_win). Consumer registry gọi hàm này thay vì
    `detect_episodes(arr_full, cfg)` — tránh lịch sử pre-window nuốt semantics.

    Watchlist KHÔNG gọi hàm này (uses full arr).
    """
    if cfg is None:
        cfg = CFG_DEFAULT
    try:
        cutoff = (_date.fromisoformat(window_start) - _td(days=lb_days)).isoformat()
    except Exception:
        cutoff = window_start
    arr_win = [r for r in arr if r.get("date", "") >= cutoff]
    ep_win = detect_episodes(arr_win, cfg)
    return arr_win, ep_win

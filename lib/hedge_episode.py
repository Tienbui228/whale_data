"""lib/hedge_episode.py — SHARED hedge-episode detection (extracted 2026-08-19).

Canonical source for episode detection: watchlist v1.4 + registry backfill v1.0
(E-R7) MUST import from here — cấm re-implement.

Extraction ref: scripts/watchlist_daily.py:107-158 (bit-equal — verified commit
8e679d9 KHÔNG chạm hàm detect_episodes/avg3/calc_div).

R0 verify (mã án E-R7 §R0): diff 553552e→8e679d9 chỉ chạm run_date() line 240+
(skip-stale WARN), KHÔNG touch detect_episodes. Extract safe.

Conformance-pack amendment 21/08 (fe4e38c): thêm field `sn_count_le050`
(count(div_avg3 ≤ 0.5) trong episode, EXCLUDE gap-tolerated days) và alias
`ep_len` (= struct_n cũ, semantics i−ep_start+1 while in_hedge). GIỮ struct_n
để bit-equal watchlist inline (P0 SAFE 139-token 0 diffs) — cấm đổi/xóa.
Registry consumer BẮT BUỘC dùng `sn_count_le050` (canonical §E-R1 conformance).

Import example:
    from lib.hedge_episode import detect_episodes, avg3, calc_div, NaN, ok
"""
from __future__ import annotations
import math
from statistics import mean

NaN = float("nan")


def ok(x):
    """True if x is finite non-NaN."""
    return x == x and not math.isinf(x)


def avg3(arr, i, field):
    """3-day rolling mean (i-2, i-1, i) — skip NaN."""
    vals = [arr[j][field] for j in range(max(0, i - 2), i + 1) if ok(arr[j][field])]
    return mean(vals) if vals else NaN


def calc_div(arr, i):
    """div_avg3 = avg3(pos) / avg3(acc). NaN if either side is NaN or avg3(acc)=0."""
    a3p = avg3(arr, i, "pos")
    a3a = avg3(arr, i, "acc")
    if not ok(a3p) or not ok(a3a) or a3a == 0:
        return NaN
    return a3p / a3a


def detect_episodes(arr, cfg):
    """
    Returns list[dict] parallel to arr. Mỗi phần tử:
      in_hedge, episode_id, hedge_start_date, hedge_start_px (CỐ ĐỊNH),
      struct_n, ep_len, sn_count_le050

    Gap tolerance: div > div_max liên tục <= gap_tol ngày → noise, in_hedge stays True.
    Episode break: div > div_max liên tục >= ep_break ngày → in_hedge = False.
    hedge_start_px SET MỘT LẦN khi episode bắt đầu, không tính lại.

    Field semantics (conformance-pack 21/08):
      struct_n        = i - ep_si + 1 while in_hedge (LEGACY, incl gap-days) — bit-equal watchlist inline
      ep_len          = alias struct_n (tên canonical mới, cùng semantics)
      sn_count_le050  = count(div_avg3 ≤ 0.5 in episode) — canonical §E-R1 conformance
                        EXCLUDE gap-tolerated days. Registry consumer BẮT BUỘC dùng field này.

    cfg["hedge"]["div_ratio_max"]      default 0.5
    cfg["hedge"]["episode_break_days"] default 3
    """
    div_max = cfg["hedge"]["div_ratio_max"]
    ep_break = cfg["hedge"]["episode_break_days"]

    out = []
    ep_id = 0
    ep_si = None
    ep_spx = None
    in_hedge = False
    n_above = 0
    sn_count = 0   # count(div ≤ div_max) in current episode

    for i, row in enumerate(arr):
        dr = calc_div(arr, i)

        if ok(dr) and dr <= div_max:
            if not in_hedge:            # new episode starts
                ep_id += 1
                ep_si = i
                ep_spx = row["px"] if ok(row["px"]) else None
                sn_count = 0
            in_hedge = True
            n_above = 0
            sn_count += 1
        else:                           # div > max or NaN
            if in_hedge:
                n_above += 1
                if n_above >= ep_break:  # gap too long → episode ends
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

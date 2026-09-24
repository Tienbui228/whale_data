"""R1b · ĐỐI CHỨNG detector · code đóng băng tới 31/10.

Nguồn phán: docs/analysis_rulings_holdout_20260924.md · md5 04f2826b884bde92ceb994af75bc849d
  · mục 1 point 4 (detector đối chứng)
  · mục 2 R1b-2 (điều kiện thắng · nguyên văn)

Detector R1b-2:
  · Neo ngày ĐẦU div_avg3 vào [0.4, 0.5]
  · KHÔNG Δacc (chỉ dùng div_avg3)
  · Gộp 14d (y hệt chuông)
  · Cửa sổ 10d cross-check

"Thắng" chuông = precision_bell > precision_ctrl ∧ lead_to_cross_bell ≥ lead_ctrl
  (cả hai trên cùng cửa sổ 10d · cùng gộp 14d)

Kết luận 21/10 = HAI CÂU TÁCH:
  · pass/không pass (theo 3 vế đã ký R1)
  · thắng/không thắng đối chứng (theo detector này)

Pass mà không thắng → không ký ngưỡng · ghi "chuông ≈ vị trí div".

KHÔNG chạy trong file này · file được import bởi _probe_r1b_run_20260924.py.
"""
from __future__ import annotations
import csv, math, os
from pathlib import Path
from datetime import datetime, timedelta

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

# Tham số detector (đã ANALYSIS ký · KHÔNG sửa tới 31/10)
GAP_DAYS = 14
FORWARD_MIN = 1
FORWARD_MAX = 10
DIV_BAND_LO = 0.4
DIV_BAND_HI = 0.5  # inclusive
OUTAGE_DATES = {(2026, 7, 24), (2026, 7, 25), (2026, 7, 26)}


def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None


def _div_avg3(rows, target_date):
    """Copy species_tag._div_avg3 · pos_r/acc_r mean 3d."""
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    ratios = []
    for d in range(2, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        pos = None; acc = None
        for r in rows:
            if r["date"] == dt:
                pos = _flt(r.get("lsr_pos_r"))
                acc = _flt(r.get("lsr_acc_r"))
                break
        if pos is None or acc is None or acc <= 0: continue
        ratios.append(pos / acc)
    if len(ratios) < 3: return None
    return sum(ratios) / len(ratios)


def _find_cross(rows, d_start, d_end):
    """Trả date-str đầu tiên có vp≤0.5 · v>0.5 trong [d_start, d_end], None nếu không."""
    d = d_start
    while d <= d_end:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt)
        vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            return dt
        d += timedelta(days=1)
    return None


def _touches_outage(d):
    for i in range(-2, FORWARD_MAX + 1):
        dd = d + timedelta(days=i)
        if (dd.year, dd.month, dd.day) in OUTAGE_DATES:
            return True
    return False


def detect_ctrl_episodes(by_sym, universe, calib_start, calib_end):
    """Detector đối chứng:
      · Scan mọi token-night có div_avg3(D) ∈ [0.4, 0.5]
      · Nhóm consecutive nights (gap ≤14d) thành episodes
      · Neo D_first = ngày đầu episode
      · Cross-check [D_first+1, D_first+10]
      · Loại outage

    Trả list episodes: (tok, D_first, div_first, cross_date_or_None, excl)
    """
    d_start = datetime.strptime(calib_start, "%Y-%m-%d").date()
    d_end = datetime.strptime(calib_end, "%Y-%m-%d").date()
    result = []
    for tok in universe:
        if tok not in by_sym: continue
        rows = by_sym[tok]
        # Collect nights in-band
        in_band = []
        d = d_start
        while d <= d_end:
            div_D = _div_avg3(rows, d.isoformat())
            if div_D is not None and DIV_BAND_LO <= div_D <= DIV_BAND_HI:
                in_band.append((d, div_D))
            d += timedelta(days=1)
        # Group into episodes gap≤14d
        if not in_band: continue
        episodes = [[in_band[0]]]
        for date, div_D in in_band[1:]:
            prev_date = episodes[-1][-1][0]
            if (date - prev_date).days <= GAP_DAYS:
                episodes[-1].append((date, div_D))
            else:
                episodes.append([(date, div_D)])
        # Score each episode
        for ep in episodes:
            D_first, div_first = ep[0]
            cross = _find_cross(rows, D_first + timedelta(days=FORWARD_MIN),
                                     D_first + timedelta(days=FORWARD_MAX))
            excl = _touches_outage(D_first)
            result.append((tok, D_first.isoformat(), div_first, cross, excl))
    return result


def compute_precision_and_lead(episodes):
    """Trả (precision, lead_median) cho detector episodes.

    · precision = n_cross / n_ep (loại outage)
    · lead_median = median (D_cross − D_first) trên các hit
    · Cùng logic dùng cho chuông thực để "Thắng" compare.
    """
    valid = [e for e in episodes if not e[4]]  # loại outage
    n_ep = len(valid)
    hits = [(e, datetime.strptime(e[3], "%Y-%m-%d").date() - datetime.strptime(e[1], "%Y-%m-%d").date())
            for e in valid if e[3] is not None]
    n_hit = len(hits)
    precision = n_hit / n_ep if n_ep > 0 else 0.0
    if hits:
        leads = sorted([t.days for _, t in hits])
        mid = len(leads) // 2
        lead_median = leads[mid] if len(leads) % 2 == 1 else (leads[mid-1] + leads[mid]) / 2
    else:
        lead_median = None
    return {"n_ep": n_ep, "n_hit": n_hit, "precision": precision * 100, "lead_median": lead_median}


def is_bell_win(bell_result, ctrl_result):
    """'Thắng' = precision_bell > precision_ctrl ∧ lead_to_cross_bell ≥ lead_ctrl."""
    if bell_result["lead_median"] is None or ctrl_result["lead_median"] is None:
        return False
    return (bell_result["precision"] > ctrl_result["precision"] and
            bell_result["lead_median"] >= ctrl_result["lead_median"])


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("R1b · detector đối chứng · KHÔNG chạy trực tiếp (dùng module)")
    print(f"DIV_BAND=[{DIV_BAND_LO}, {DIV_BAND_HI}] · GAP={GAP_DAYS}d · FORWARD=[{FORWARD_MIN},{FORWARD_MAX}]d")
    print("Win = precision_bell > precision_ctrl AND lead_bell >= lead_ctrl")

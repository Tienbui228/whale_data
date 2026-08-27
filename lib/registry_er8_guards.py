"""lib/registry_er8_guards.py — §E-R8 falsifier forward guards runtime.

Per proposals/unhedge_registry_spec.md §E-R8 (v1.2-FINAL+doctrine-pack):
  ① Hit  : MFE_k7 = max(close[D+1..D+7])/close_D − 1 ≥ +10% cho ≥50% alerts wave-2+ 30d
  ② Noise: reg%_weekpeak = max ISO-week (unique tokens active / fw-139) ≤ 25%
           + alert E-R3 ≤ 40% total Telegram alerts/tuần
  ③ Miss-audit: pump ≥30%/2d trên token TỪNG CÓ row (kể cả đã đóng) không alert
                → autopsy ≤48h

REPORT-ONLY runtime. Return dict {guard: bool, detail}. Consumer (wrapper) quyết
block Telegram khi guard trip. KHÔNG mutate state ở đây.

Ngưỡng KHÔNG hardcode — đọc yaml unhedge_registry (nếu có) hoặc fallback default.
"""
from __future__ import annotations
from datetime import date as _date, timedelta as _td
from statistics import mean

# Default thresholds per §E-R8 v1.2-FINAL
_DEFAULT_MFE_K7_MIN = 0.10   # ≥+10%
_DEFAULT_MFE_HIT_RATE = 0.50 # ≥50% alerts wave-2+
_DEFAULT_REG_WEEKPEAK_MAX = 0.25  # ≤25%
_DEFAULT_ER3_ALERT_SHARE_MAX = 0.40  # ≤40% E-R3 tổng Telegram/tuần
_DEFAULT_PUMP_MISS_PCT = 0.30  # ≥30%/2d pump
_DEFAULT_PUMP_MISS_DAYS = 2


def check_mfe_k7(alerts, klines_by_token, min_ret=_DEFAULT_MFE_K7_MIN,
                  hit_rate_min=_DEFAULT_MFE_HIT_RATE, days_back=30):
    """§E-R8 ①: alerts wave-2+ trong 30d qua có ≥50% đạt MFE_k7 ≥+10%.

    Args:
      alerts: list of {sym, date, wave_n, close_D0}. Filter wave_n >=2.
      klines_by_token: {sym: {date: close}}. Consumer fetch fapi.
    Return: (pass: bool, detail: dict).
    """
    today = _date.today()
    cutoff = today - _td(days=days_back)
    wave2_alerts = [a for a in alerts
                     if a.get("wave_n", 1) >= 2
                     and _date.fromisoformat(a["date"]) >= cutoff]
    if not wave2_alerts:
        return True, {"n_wave2": 0, "hit_rate": None, "note": "no wave-2+ alerts trong 30d — vacuously pass"}

    hits = 0
    details = []
    for a in wave2_alerts:
        sym, dt = a["sym"], a["date"]
        close_D0 = a.get("close_D0")
        klines = klines_by_token.get(sym, {})
        if close_D0 is None or close_D0 <= 0 or not klines:
            details.append({"sym": sym, "date": dt, "mfe_k7": None, "note": "missing data"})
            continue
        d0 = _date.fromisoformat(dt)
        max_close = close_D0
        for k in range(1, 8):
            dk = (d0 + _td(days=k)).isoformat()
            if dk in klines: max_close = max(max_close, klines[dk])
        mfe = (max_close - close_D0) / close_D0
        hit = mfe >= min_ret
        if hit: hits += 1
        details.append({"sym": sym, "date": dt, "mfe_k7": mfe, "hit": hit})

    hit_rate = hits / len(wave2_alerts)
    return hit_rate >= hit_rate_min, {
        "n_wave2": len(wave2_alerts), "n_hits": hits, "hit_rate": hit_rate,
        "min_ret_threshold": min_ret, "hit_rate_min": hit_rate_min,
        "details": details[:20],
    }


def check_reg_weekpeak(open_rows_by_week, universe_size=139,
                        max_pct=_DEFAULT_REG_WEEKPEAK_MAX):
    """§E-R8 ②: reg%_weekpeak = max over ISO-weeks của unique tokens active / universe.
    "Active trong tuần" = row STILL-OPEN hoặc RE-ARMED trong tuần đó.

    Args:
      open_rows_by_week: {iso_week: set(tokens)}. Consumer compute từ state store.
      universe_size: fw universe (default 139).
    Return: (pass: bool, detail).
    """
    if not open_rows_by_week:
        return True, {"n_weeks": 0, "weekpeak_pct": 0, "note": "no open rows"}
    peaks = {wk: len(toks) / universe_size for wk, toks in open_rows_by_week.items()}
    weekpeak = max(peaks.values())
    return weekpeak <= max_pct, {
        "n_weeks": len(peaks), "weekpeak_pct": weekpeak,
        "max_allowed": max_pct,
        "worst_week": max(peaks, key=peaks.get),
        "per_week_pct": {wk: round(p, 4) for wk, p in peaks.items()},
    }


def check_er3_alert_share(alerts_by_type_week, max_share=_DEFAULT_ER3_ALERT_SHARE_MAX):
    """§E-R8 ② phụ trợ: alert E-R3 ≤40% tổng Telegram alerts/tuần.

    Args:
      alerts_by_type_week: {iso_week: {"E-R1": n1, "E-R3": n3, "E-R4": n4, ...}}.
    Return: (pass, detail).
    """
    if not alerts_by_type_week:
        return True, {"n_weeks": 0, "note": "no alerts"}
    shares = {}
    for wk, cnts in alerts_by_type_week.items():
        total = sum(cnts.values())
        if total == 0: continue
        shares[wk] = cnts.get("E-R3", 0) / total
    if not shares:
        return True, {"n_weeks": 0, "note": "zero alerts weeks"}
    worst = max(shares.values())
    return worst <= max_share, {
        "n_weeks": len(shares), "worst_share": worst, "max_allowed": max_share,
        "worst_week": max(shares, key=shares.get),
        "per_week_share": {wk: round(s, 4) for wk, s in shares.items()},
    }


def check_miss_audit(pump_events, alert_rows, days_check=2):
    """§E-R8 ③: pump ≥30%/2d trên token TỪNG CÓ row (kể cả đã đóng) không alert
    → autopsy ≤48h bắt buộc.

    Args:
      pump_events: list of {sym, pump_date, pump_pct} (pump ≥30%/2d detect từ px series).
      alert_rows: list of {sym, alert_date} (all registry rows kể cả closed).
    Return: (pass: bool, detail) — pass=False nếu có miss chưa autopsy trong 48h.
    """
    misses = []
    tokens_ever_seen = {r["sym"] for r in alert_rows}
    for p in pump_events:
        if p["sym"] not in tokens_ever_seen: continue
        pump_dt = _date.fromisoformat(p["pump_date"])
        alerts_near = [r for r in alert_rows
                       if r["sym"] == p["sym"]
                       and abs((_date.fromisoformat(r["alert_date"]) - pump_dt).days) <= 1]
        if not alerts_near:
            days_since = (_date.today() - pump_dt).days
            misses.append({"sym": p["sym"], "pump_date": p["pump_date"],
                            "pump_pct": p["pump_pct"], "days_since": days_since,
                            "autopsy_required": days_since <= 2})
    urgent = [m for m in misses if m["autopsy_required"]]
    return len(urgent) == 0, {
        "n_misses_ever": len(misses), "n_urgent_48h": len(urgent),
        "urgent_misses": urgent[:10],
    }


def check_all_guards(alerts, klines_by_token, open_rows_by_week,
                      alerts_by_type_week, pump_events, alert_rows,
                      universe_size=139):
    """Compose 4 guards §E-R8 ①②(reg+E-R3)③. Return (all_pass, per-guard details).
    Consumer wrapper decides: any FAIL → block Telegram, register ANALYSIS-ONLY 30d.
    """
    g1_pass, g1 = check_mfe_k7(alerts, klines_by_token)
    g2_pass, g2 = check_reg_weekpeak(open_rows_by_week, universe_size)
    g3_pass, g3 = check_er3_alert_share(alerts_by_type_week)
    g4_pass, g4 = check_miss_audit(pump_events, alert_rows)
    all_pass = g1_pass and g2_pass and g3_pass and g4_pass
    return all_pass, {
        "guard_1_mfe_k7":         {"pass": g1_pass, "detail": g1},
        "guard_2_reg_weekpeak":   {"pass": g2_pass, "detail": g2},
        "guard_3_er3_share":      {"pass": g3_pass, "detail": g3},
        "guard_4_miss_audit":     {"pass": g4_pass, "detail": g4},
        "all_pass": all_pass,
        "action_if_fail": "block Telegram, register ANALYSIS-ONLY 30d, autopsy for guard_4 misses",
    }

# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""Detector C · loài DUMP→GOM→ĐẨY · AUDIT-ONLY · KHÔNG WIRE.

Nguồn số S1 c1-c6 (sha 298bf565 · sổ, KHÔNG tự đặt số):
  c1 dd ≤ −40% trong ≤7d
  c2 nền ≥7d sau đáy, |ret| ≤15%
  c3 pos_r ≥1.5 giữ ±10%
  c4 acc_r ↑ ≥20%/7d
  c5 ΔOI 7d ≤ −15% ∨ kho-ramp ≥15%
  c6 pin ≥5d (tag phụ)

Vế nào sổ chỉ mô tả bằng lời → đánh dấu `[lời]`, KHÔNG gán số.
Blind → không tính, không giả vờ đạt (p38).

Ghi jsonl: data/logs/c_detect_audit.jsonl
KHÔNG vào bản tin · KHÔNG seed · KHÔNG ngưỡng ký.
Đọc lại khi ≥10 dương ∧ ≥10 âm.
"""
from __future__ import annotations
import os, sys, json, csv, math
from pathlib import Path
from datetime import datetime, timedelta, timezone

_SCRIPTS = Path(__file__).parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
AUDIT_LOG = REPO / "data/logs/c_detect_audit.jsonl"
FW_PATH = REPO / "data/config/freshwatch_symbols.txt"

# Constants (S1 c1-c6 · sổ)
C1_DD_MAX = -0.40      # ≤ -40% dd trong ≤7d
C1_WINDOW = 7
C2_NEN_MIN = 7         # ≥7d
C2_RET_MAX_ABS = 0.15  # |ret| ≤15%
C3_POS_MIN = 1.5       # pos_r ≥1.5
C3_POS_TOL = 0.10      # ±10%
C4_ACC_RISE = 0.20     # acc ↑ ≥20%/7d
C4_WINDOW = 7
C5_OI_DROP = -0.15     # ΔOI 7d ≤ −15%
C5_KHO_RAMP = 0.15     # kho-ramp ≥15%
C5_WINDOW = 7
C6_PIN_MIN_DAYS = 5    # ≥5d
C6_PIN_VALUE = 0.00005 # funding_avg pin


def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        if math.isnan(f): return None
        return f
    except (TypeError, ValueError):
        return None


def _get(rows, dt, field):
    for r in rows:
        if r["date"] == dt: return _flt(r.get(field))
    return None


def _load_rows(target, months=None):
    """Load fw_daily rows per token · kèm 60d trước target."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    if months is None:
        m1 = td.month
        m0 = m1 - 1 if m1 > 1 else 12
        m_1 = m0 - 1 if m0 > 1 else 12
        months = sorted({f"{m:02d}" for m in [m_1, m0, m1]})
    by_sym = {}
    for m in months:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if not p.exists(): continue
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                sym = r["symbol"]
                bare = sym[:-4] if sym.endswith("USDT") else sym
                by_sym.setdefault(bare, []).append(r)
    return by_sym


def _c1_dd_7d(rows, target):
    """c1: dd ≤ -40% trong 7d gần nhất."""
    px_T = _get(rows, target, "px_avg")
    if px_T is None: return "BLIND", None
    td = datetime.strptime(target, "%Y-%m-%d").date()
    px_max = px_T
    n_data = 1
    for k in range(1, C1_WINDOW + 1):
        dk = (td - timedelta(days=k)).isoformat()
        px_k = _get(rows, dk, "px_avg")
        if px_k is None: continue
        px_max = max(px_max, px_k)
        n_data += 1
    if n_data < 3 or px_max <= 0: return "BLIND", None
    dd = (px_T - px_max) / px_max
    return ("PASS" if dd <= C1_DD_MAX else "FAIL"), dd


def _c2_nen_7d(rows, target):
    """c2: nền ≥7d sau đáy · |ret| ≤15% (rolling)."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    # Tìm đáy trong 30d
    pxs = []
    for k in range(0, 30):
        dk = (td - timedelta(days=k)).isoformat()
        px_k = _get(rows, dk, "px_avg")
        if px_k is not None: pxs.append((dk, px_k))
    if len(pxs) < 10: return "BLIND", None
    min_dk, min_px = min(pxs, key=lambda x: x[1])
    min_date = datetime.strptime(min_dk, "%Y-%m-%d").date()
    # Đếm ngày sau đáy có |ret vs prev| ≤ 15%
    n_nen = 0
    prev = min_px
    for k in range((td - min_date).days + 1):
        dk = (min_date + timedelta(days=k)).isoformat()
        px_k = _get(rows, dk, "px_avg")
        if px_k is None: continue
        if prev > 0 and abs((px_k - prev) / prev) <= C2_RET_MAX_ABS:
            n_nen += 1
        prev = px_k
    return ("PASS" if n_nen >= C2_NEN_MIN else "FAIL"), n_nen


def _c3_pos_hold(rows, target):
    """c3: pos_r ≥ 1.5 giữ ±10% trong 7d."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    pos_vals = []
    for k in range(0, 7):
        dk = (td - timedelta(days=k)).isoformat()
        pos = _get(rows, dk, "lsr_pos_r")
        if pos is not None: pos_vals.append(pos)
    if len(pos_vals) < 5: return "BLIND", None
    mean_pos = sum(pos_vals) / len(pos_vals)
    if mean_pos < C3_POS_MIN:
        return "FAIL", mean_pos
    max_dev = max(abs((p - mean_pos) / mean_pos) for p in pos_vals if mean_pos > 0)
    return ("PASS" if max_dev <= C3_POS_TOL else "FAIL"), mean_pos


def _c4_acc_rise(rows, target):
    """c4: acc_r(T) / acc_r(T-7) ≥ 1.20 (rise ≥ 20%)."""
    acc_T = _get(rows, target, "lsr_acc_r")
    td = datetime.strptime(target, "%Y-%m-%d").date()
    acc_m7 = _get(rows, (td - timedelta(days=7)).isoformat(), "lsr_acc_r")
    if acc_T is None or acc_m7 is None or acc_m7 <= 0: return "BLIND", None
    rise = (acc_T - acc_m7) / acc_m7
    return ("PASS" if rise >= C4_ACC_RISE else "FAIL"), rise


def _c5_oi_drop(rows, target):
    """c5: ΔOI 7d ≤ −15% ∨ kho-ramp ≥15% · kho-ramp không đo được ở đây (Nansen) → chỉ OI."""
    oi_T = _get(rows, target, "oi_usd")
    td = datetime.strptime(target, "%Y-%m-%d").date()
    oi_m7 = _get(rows, (td - timedelta(days=7)).isoformat(), "oi_usd")
    if oi_T is None or oi_m7 is None or oi_m7 <= 0: return "BLIND", None
    d_oi = (oi_T - oi_m7) / oi_m7
    # Chỉ đo vế OI (kho-ramp cần Nansen · marked [lời])
    return ("PASS" if d_oi <= C5_OI_DROP else "FAIL"), d_oi


def _c6_pin(rows, target):
    """c6: funding_avg pin (≈0.00005) ≥5d liên tục · tag phụ."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    n_pin = 0
    for k in range(0, C6_PIN_MIN_DAYS + 3):
        dk = (td - timedelta(days=k)).isoformat()
        f = _get(rows, dk, "funding_avg")
        if f is None: continue
        if abs(f - C6_PIN_VALUE) <= 1e-6:
            n_pin += 1
        else:
            break
    return ("PASS" if n_pin >= C6_PIN_MIN_DAYS else "FAIL"), n_pin


def eval_c(rows, target):
    """Trả dict với 6 vế + k (đếm PASS) + n_blind."""
    checks = {
        "c1": _c1_dd_7d(rows, target),
        "c2": _c2_nen_7d(rows, target),
        "c3": _c3_pos_hold(rows, target),
        "c4": _c4_acc_rise(rows, target),
        "c5": _c5_oi_drop(rows, target),   # c5-oi only · kho-ramp [lời]
        "c6": _c6_pin(rows, target),
    }
    k = sum(1 for s, _ in checks.values() if s == "PASS")
    n_blind = sum(1 for s, _ in checks.values() if s == "BLIND")
    return {"checks": checks, "k": k, "n_blind": n_blind}


def _ret_outcome(rows, target, n_days):
    """Ret max trong [T+1, T+n]."""
    px0 = _get(rows, target, "px_avg")
    if px0 is None or px0 <= 0: return None
    td = datetime.strptime(target, "%Y-%m-%d").date()
    max_pct = None
    for k in range(1, n_days + 1):
        dk = (td + timedelta(days=k)).isoformat()
        px_k = _get(rows, dk, "px_avg")
        if px_k is None: continue
        pct = (px_k - px0) / px0
        if max_pct is None or pct > max_pct: max_pct = pct
    return max_pct


def audit_night(target: str, universe=None):
    """Chạy detector C toàn universe · append jsonl · trả stats."""
    if universe is None:
        universe = [l.strip()[:-4] if l.strip().endswith("USDT") else l.strip()
                    for l in FW_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_sym = _load_rows(target)
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries = []
    stats = {"k6": 0, "k5": 0, "k4": 0, "k_lt4": 0, "blind_only": 0}
    for tok in universe:
        rows = by_sym.get(tok, [])
        if not rows: continue
        res = eval_c(rows, target)
        # p38 · blind không tính · không giả vờ đạt
        if res["n_blind"] >= 3:
            stats["blind_only"] += 1
        else:
            k = res["k"]
            if k == 6: stats["k6"] += 1
            elif k == 5: stats["k5"] += 1
            elif k == 4: stats["k4"] += 1
            else: stats["k_lt4"] += 1
        # ret outcome
        ret30 = _ret_outcome(rows, target, 30)
        ret60 = _ret_outcome(rows, target, 60)
        entries.append({
            "target": target, "token": tok,
            "checks": {k: {"status": v[0], "value": v[1]} for k, v in res["checks"].items()},
            "k": res["k"], "n_blind": res["n_blind"],
            "ret30": ret30, "ret60": ret60,
            "computed_at": now_iso,
        })
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return stats, entries


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--tokens", help="Comma-separated tokens (default: full universe)")
    args = ap.parse_args()
    universe = args.tokens.split(",") if args.tokens else None
    stats, entries = audit_night(args.target, universe)
    print(f"[C-DETECT-AUDIT] target={args.target} stats={stats} · n_entries={len(entries)}")

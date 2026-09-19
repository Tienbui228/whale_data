# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""U0-BELL audit runner · AB0/19-09 · CALIBRATION-ONLY.

Đọc universe fw_symbols.txt · load daily rows per token · chạy u0_bell(target) ·
in audit stderr per token có BELL/NEAR/BLIND + tổng đêm ·
append data/logs/u0_bell_audit.jsonl.

TUYỆT ĐỐI KHÔNG chạm body bản tin · KHÔNG return gì để render dùng.
"""
from __future__ import annotations
import os, sys, json, csv
from pathlib import Path
from datetime import datetime, timezone

# Reuse fw store + species_tag from live scripts
_SCRIPTS = Path(__file__).parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from u0_bell import u0_bell
from species_tag import _div_avg3

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
AUDIT_LOG = REPO / "data/logs/u0_bell_audit.jsonl"
FW_PATH = REPO / "data/config/freshwatch_symbols.txt"


def _load_universe():
    if not FW_PATH.exists():
        return []
    return [l.strip() for l in FW_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_rows_per_token(months):
    """Load fw_daily rows keyed by bare token."""
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


def _months_needed(target):
    """Cần current month + 1 previous (Δacc_bwd dùng T-3)."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    cur = f"{td.month:02d}"
    prev_month = td.month - 1 if td.month > 1 else 12
    prev = f"{prev_month:02d}"
    return sorted({cur, prev})


def _format_dd_mm(target):
    td = datetime.strptime(target, "%Y-%m-%d").date()
    return f"{td.day:02d}/{td.month:02d}"


def collect_audit(target: str):
    """Tách logic thu thập — trả dict {bell: [(tok, dacc, dpos, div), ...], near: [...], blind: [...]}.
    Dùng bởi run_audit (log + jsonl) và render_unhedge_block (thân bản tin)."""
    universe = _load_universe()
    if not universe:
        return {"bell": [], "near": [], "blind": []}
    months = _months_needed(target)
    by_sym = _load_rows_per_token(months)
    tiers = {"bell": [], "near": [], "blind": []}
    for sym_full in universe:
        bare = sym_full[:-4] if sym_full.endswith("USDT") else sym_full
        rows = by_sym.get(bare, [])
        if not rows: continue
        res = u0_bell(rows, target, _div_avg3)
        status = res["status"]
        if status == "BELL":
            tiers["bell"].append((bare, res["dacc_bwd"], res["dpos_bwd"], res["div_D"]))
        elif status == "NEAR":
            tiers["near"].append((bare, res["dacc_bwd"], res["dpos_bwd"], res["div_D"]))
        elif status == "BLIND":
            tiers["blind"].append((bare, res.get("dacc_bwd"), res.get("dpos_bwd"), res.get("div_D")))
    return tiers


def run_audit(target: str, log_fn=None):
    """Chạy u0_bell trên universe, in audit stderr, append jsonl.
    Trả dict {n_bell, n_near, n_blind}."""
    def _log(msg):
        if log_fn: log_fn(msg)
        else: print(msg, file=sys.stderr)

    tiers = collect_audit(target)
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    dd_mm = _format_dd_mm(target)
    audit_entries = []

    for tok, dacc, dpos, div in tiers["bell"]:
        dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
        dpos_s = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
        _log(f"[U0-BELL {tok} D={dd_mm} · Δacc_bwd={dacc_s} · Δpos_bwd={dpos_s} desc] [CALIBRATION-ONLY]")
        audit_entries.append({"target": target, "token": tok, "tier": "bell",
                              "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div, "computed_at": now_iso})
    for tok, dacc, dpos, div in tiers["near"]:
        dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
        _log(f"[U0-NEAR {tok} D={dd_mm} · Δacc_bwd={dacc_s}]")
        audit_entries.append({"target": target, "token": tok, "tier": "near",
                              "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div, "computed_at": now_iso})
    for tok, dacc, dpos, div in tiers["blind"]:
        _log(f"[U0-BLIND {tok} D={dd_mm} · thiếu acc(D) hoặc acc(D−3)]")
        audit_entries.append({"target": target, "token": tok, "tier": "blind",
                              "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div, "computed_at": now_iso})

    n_bell, n_near, n_blind = len(tiers["bell"]), len(tiers["near"]), len(tiers["blind"])
    _log(f"[U0-BELL-COUNT target={target} · n_bell={n_bell} · n_near={n_near} · n_blind={n_blind}]")

    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        for e in audit_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"n_bell": n_bell, "n_near": n_near, "n_blind": n_blind}


def render_unhedge_block(target: str, drop_near: bool = False, drop_blind: bool = False) -> str:
    """AD1 · khối UNHEDGE gọn cho THÂN BẢN TIN · CALIBRATION-ONLY.

    HOLD-OUT 20/09→20/10: Tiên ĐỌC được nhưng CẤM chỉnh ngưỡng theo cái đọc được
    trước 21/10. Grid 8 ô đã khoá.

    Format (AD1-1):
      ── UNHEDGE ── (n) [CAL-ONLY]
         <TOK> −21 · <TOK> −22 · <TOK> −27      ← một dòng, tên + Δacc int, bỏ %
         near <m>                                ← chỉ đếm, KHÔNG tên
         blind <k>                               ← chỉ đếm, KHÔNG BAO GIỜ tên (AD1-6)
      Rỗng → `── UNHEDGE ── hôm nay: không chuông`

    Δacc: làm tròn nguyên, bỏ dấu %. Bỏ Δpos_bwd và div khỏi thân
    (vẫn ghi đủ trong u0_bell_audit.jsonl).

    AD1-6 (LOCK): blind luôn là số đếm, KHÔNG BAO GIỜ danh sách tên.
    Lý do: một đêm collector chậm → BLIND phình bằng cả universe → vỡ bản tin.

    AD1-3 cắt bậc thang khi chật: drop_near=True → bỏ near · drop_blind=True → bỏ blind.
    KHÔNG cắt tên chuông (bell) — chuông là thứ Tiên xin để đánh giá.
    """
    tiers = collect_audit(target)
    n_bell = len(tiers["bell"])
    n_near = len(tiers["near"])
    n_blind = len(tiers["blind"])

    if n_bell == 0 and n_near == 0 and n_blind == 0:
        return "── UNHEDGE ── hôm nay: không chuông"

    lines = [f"── UNHEDGE ── ({n_bell}) [CAL-ONLY]"]
    if n_bell > 0:
        parts = []
        for tok, dacc, _dpos, _div in tiers["bell"]:
            if dacc is None:
                parts.append(f"{tok} N/A")
            else:
                # Δacc int, bỏ %, giữ dấu (âm)
                parts.append(f"{tok} {int(round(dacc*100))}")
        lines.append("   " + " · ".join(parts))
    if n_near > 0 and not drop_near:
        lines.append(f"   near {n_near}")
    if n_blind > 0 and not drop_blind:
        lines.append(f"   blind {n_blind}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    run_audit(args.target)

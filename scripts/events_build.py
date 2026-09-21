"""events_build.py · AG3/21-09 · single source events file cho master + HEDGE v2.

Ghi 4 loại row vào `data/artifacts/events_<T>.jsonl` + `events_<T>.md5`:
  {type:"bell", tok, D, dacc_bwd, dpos_bwd, div}
  {type:"class", tok, d_cross, tier:L1|L2|L3, dacc, dpos}
  {type:"u1", tok, d_cross, v1, v2, verdict}
  {type:"btier", tok, tier, d_cross, k}

KHÔNG tính lead. KHÔNG định dạng hiển thị.
Consumer (master render, HEDGE v2) đọc file, KHÔNG tự tính.

Usage:
  python3 scripts/events_build.py --target 2026-09-20

Doctrine §KỶ-LUẬT #12: file phải chạy tay ≥2 đêm quá khứ khớp
với b_state_tracker + u0_bell_audit trước khi apply cron.
"""
from __future__ import annotations
import os, sys, json, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

ART_DIR = _REPO / "data/artifacts"

# Re-use prod modules · single source of truth
from u0_bell_audit import collect_audit as _collect_bell
from b_state_tracker import (
    build_b_state, _load_universe, _load_fw_rows,
    _find_latest_cross, _check_u0_class_L1, _check_u1_v2v1,
    CROSS_D_PLUS_MAX,
)


def _class_tier(is_l1: bool, dacc: float | None, dpos: float | None) -> str:
    """L1 pass | not L1 (blind/L2/L3 combined) · số thô chỉ ghi dacc/dpos."""
    if dacc is None or dpos is None:
        return "BLIND"
    if is_l1:
        return "L1"
    # Không tính L2/L3 phân biệt tại events_build · consumer đọc dacc/dpos tự phân
    return "L2_OR_L3"


def _u1_verdict(v1p: bool, v2p: bool) -> str:
    if v1p and v2p: return "PASS"
    if v1p or v2p:  return "PARTIAL"
    return "FAIL"


def build_events(target: str) -> tuple[list[dict], str]:
    """Trả (list_rows, md5_hex). Không ghi file · pure function."""
    universe = _load_universe()
    by_sym = _load_fw_rows(target)
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    # ── bell events (U0-BELL detect tại D=target) ──
    bell_res = _collect_bell(target)
    dd_target = datetime.strptime(target, "%Y-%m-%d")
    for tok, dacc, dpos, div in bell_res["bell"]:
        rows.append({
            "type": "bell", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })
    # NEAR + BLIND cũng ghi nhưng type khác để consumer phân
    for tok, dacc, dpos, div in bell_res["near"]:
        rows.append({
            "type": "bell_near", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })
    for tok, dacc, dpos, div in bell_res["blind"]:
        rows.append({
            "type": "bell_blind", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })

    # ── class + u1 events (per token có D_cross gần T) ──
    td = datetime.strptime(target, "%Y-%m-%d").date()
    for tok in universe:
        toks = by_sym.get(tok, [])
        if not toks: continue
        d_cross = _find_latest_cross(toks, target)
        if d_cross is None: continue

        is_l1, dacc, dpos = _check_u0_class_L1(toks, d_cross)
        tier = _class_tier(is_l1, dacc, dpos)
        rows.append({
            "type": "class", "tok": tok, "d_cross": d_cross, "tier": tier,
            "dacc": dacc, "dpos": dpos, "computed_at": now_iso,
        })

        dpk = (td - datetime.strptime(d_cross, "%Y-%m-%d").date()).days
        # U1 chấm tại D+5 · chỉ meaningful khi D+k ≥5
        if dpk >= 5:
            u1_pass, u1_ratios = _check_u1_v2v1(toks, d_cross)
            v1_pass = u1_ratios.get("v1") is not None and u1_ratios["v1"] <= 0.6
            v2_pass = u1_ratios.get("v2") is not None and u1_ratios["v2"] >= 1.5
            rows.append({
                "type": "u1", "tok": tok, "d_cross": d_cross,
                "v1": u1_ratios.get("v1"), "v2": u1_ratios.get("v2"),
                "verdict": _u1_verdict(v1_pass, v2_pass),
                "computed_at": now_iso,
            })

    # ── btier events (tier + k cho mỗi token trong build_b_state) ──
    state = build_b_state(target, universe=universe, by_sym=by_sym)
    for tok, s in state.items():
        rows.append({
            "type": "btier", "tok": tok, "tier": s["tier"],
            "d_cross": s.get("d_cross"),
            "k": s.get("d_plus_k"),
            "computed_at": now_iso,
        })

    # Serialize + md5
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    md5_hex = hashlib.md5(body.encode("utf-8")).hexdigest()
    return rows, md5_hex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--out-dir", default=str(ART_DIR))
    ap.add_argument("--dry-run", action="store_true",
                    help="Chỉ in số lượng events, không ghi file")
    args = ap.parse_args()

    rows, md5_hex = build_events(args.target)

    print(f"[events_build] target={args.target} · rows={len(rows)} · md5={md5_hex[:12]}")
    by_type = {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    for t, n in sorted(by_type.items()):
        print(f"  {t:16s} : {n}")

    if args.dry_run:
        print("[dry-run] no file written")
        return

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_p = out_dir / f"events_{args.target}.jsonl"
    md5_p = out_dir / f"events_{args.target}.md5"
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    out_p.write_text(body, encoding="utf-8")
    md5_p.write_text(md5_hex + "\n", encoding="utf-8")
    print(f"[events_build] wrote {out_p} · md5={md5_hex[:12]}")


if __name__ == "__main__":
    main()

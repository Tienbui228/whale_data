"""events_build.py · AG3/21-09 · AL1-AL2/22-09 · single source events file.

Ghi 2 kind row vào `data/artifacts/events_<T>.jsonl` + `events_<T>.md5`:

  · kind:"event" · GHI ĐÚNG MỘT LẦN, đúng ngày sự kiện:
    - {kind:"event", type:"bell", tok, D=<target>, dacc_bwd, dpos_bwd, div}
      → emit khi u0_bell fires tại D=target (D là ngày chuông).
    - {kind:"event", type:"class", tok, d_cross, tier:L1|L2_OR_L3|BLIND, dacc, dpos}
      → emit khi target == D_cross + 2 (2 ngày sau cross · quan sát ổn định).
    - {kind:"event", type:"u1", tok, d_cross, v1, v2, verdict:PASS|PARTIAL|FAIL}
      → emit khi target == D_cross + 5 VÀ class(D_cross) == L1 (AL2 gate).
      SOPH (L2) sẽ KHÔNG BAO GIỜ có dòng u1.

  · kind:"state" · GHI MỖI ĐÊM (snapshot trạng thái tại target):
    - {kind:"state", type:"btier", tok, tier, d_cross, k}
      → mỗi token trong build_b_state(target).

Tại sao tách?
  - event = fact về 1 ngày cụ thể · consumer (master, HEDGE) đọc event = biết
    "ngày X token Y có tín hiệu Z". Đọc lại forever giữ nguyên.
  - state = view của cohort tại 1 ngày · consumer đọc để render bản tin đêm ấy.

Consumer (master render, HEDGE v2) đọc file KHÔNG tự tính.

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


from lib.u0_class_tier import classify_tier

def _class_tier(is_l1: bool, dacc: float | None, dpos: float | None) -> str:
    """α1/22-09 · L1 | L2 | L3 | BLIND (dùng lib.u0_class_tier · shared).
    is_l1 param giữ cho backward-compat · classify_tier tự tính từ dacc/dpos."""
    return classify_tier(dacc, dpos)


def _u1_verdict(v1p: bool, v2p: bool) -> str:
    if v1p and v2p: return "PASS"
    if v1p or v2p:  return "PARTIAL"
    return "FAIL"


def build_events(target: str) -> tuple[list[dict], str]:
    """Trả (list_rows, md5_hex). Không ghi file · pure function.

    Rules per AL1-AL2 (22-09):
      · bell event: emit iff u0_bell(D=target) fires
      · class event: emit iff target == D_cross + 2 (per each token's D_cross)
      · u1 event: emit iff target == D_cross + 5 AND class(D_cross) == L1 (gated by AL2)
      · btier state: emit for every token in build_b_state(target)
    """
    universe = _load_universe()
    by_sym = _load_fw_rows(target)
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    td = datetime.strptime(target, "%Y-%m-%d").date()

    # ── EVENT: bell (D=target · fire hôm nay) ──
    bell_res = _collect_bell(target)
    for tok, dacc, dpos, div in bell_res["bell"]:
        rows.append({
            "kind": "event", "type": "bell", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })
    # NEAR + BLIND ghi kind="event" cùng phân type
    for tok, dacc, dpos, div in bell_res["near"]:
        rows.append({
            "kind": "event", "type": "bell_near", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })
    for tok, dacc, dpos, div in bell_res["blind"]:
        rows.append({
            "kind": "event", "type": "bell_blind", "tok": tok, "D": target,
            "dacc_bwd": dacc, "dpos_bwd": dpos, "div": div,
            "computed_at": now_iso,
        })

    # ── EVENT: class (target == D_cross + 2) · u1 (target == D_cross + 5 AND class=L1) ──
    for tok in universe:
        toks = by_sym.get(tok, [])
        if not toks: continue
        d_cross = _find_latest_cross(toks, target)
        if d_cross is None: continue
        dc_d = datetime.strptime(d_cross, "%Y-%m-%d").date()
        dpk = (td - dc_d).days

        # class · emit at D_cross+2
        if dpk == 2:
            is_l1, dacc, dpos = _check_u0_class_L1(toks, d_cross)
            tier = _class_tier(is_l1, dacc, dpos)
            rows.append({
                "kind": "event", "type": "class", "tok": tok, "d_cross": d_cross,
                "tier": tier, "dacc": dacc, "dpos": dpos,
                "computed_at": now_iso,
            })

        # u1 · emit at D_cross+5 · CHỈ KHI class(D_cross) == L1 (AL2 gate)
        if dpk == 5:
            is_l1, _, _ = _check_u0_class_L1(toks, d_cross)
            if is_l1:
                u1_pass_all, u1_ratios = _check_u1_v2v1(toks, d_cross)
                v1_pass = u1_ratios.get("v1") is not None and u1_ratios["v1"] <= 0.6
                v2_pass = u1_ratios.get("v2") is not None and u1_ratios["v2"] >= 1.5
                rows.append({
                    "kind": "event", "type": "u1", "tok": tok, "d_cross": d_cross,
                    "v1": u1_ratios.get("v1"), "v2": u1_ratios.get("v2"),
                    "verdict": _u1_verdict(v1_pass, v2_pass),
                    "computed_at": now_iso,
                })

    # ── STATE: btier snapshot mỗi đêm ──
    state = build_b_state(target, universe=universe, by_sym=by_sym)
    for tok, s in state.items():
        rows.append({
            "kind": "state", "type": "btier", "tok": tok, "tier": s["tier"],
            "d_cross": s.get("d_cross"),
            "k": s.get("d_plus_k"),
            "computed_at": now_iso,
        })

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
    by_kind_type = {}
    for r in rows:
        k = f"{r['kind']}:{r['type']}"
        by_kind_type[k] = by_kind_type.get(k, 0) + 1
    for kt, n in sorted(by_kind_type.items()):
        print(f"  {kt:24s} : {n}")

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

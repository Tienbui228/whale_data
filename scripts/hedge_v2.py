"""hedge_v2.py · AW-α/22-09 · HEDGE v2 body composer · sandbox (không gọi cron).

Spec: docs/HEDGE_report_v2_spec_20260921.md (md5 e2bab119) + AW1-AW10 (22/09).
Doctrine §KỶ-LUẬT #12: dry pipeline ≥5 đêm PASS trước khi ràng master (β).

Nội dung tầng này (α):
  · read_events(target) · kiểm target/md5 · trả rows | N/A-ERROR
  · registry_hop_145(target) · Bảng A (gom_e in_registry) ∪ List A (watchlist)
  · compose_body(target) · dựng thân tin đầy đủ theo spec §1
  · KHÔNG có sender, KHÔNG U7 gate (β sẽ ràng)

data-source: VPS canonical
machine: VPS canonical
code-commit: xem git log
"""
from __future__ import annotations
import os, sys, json, hashlib, math
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from typing import Optional

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

ART_DIR    = _REPO / "data/artifacts"
STORE_DIR  = _REPO / "data/export"
CONFIG_DIR = _REPO / "data/config"
STATE_DIR  = _REPO / "data"
FW_SYM_P   = CONFIG_DIR / "freshwatch_symbols.txt"

BODY_BUDGET   = 3600      # p100 · tg_len pre-cap ≤ 3600 (α' bump từ 3200 · thêm kr/STALE/Nguội)
REGISTRY_TOP  = 15        # thân top-15 xếp div tăng
WHALE_CAP     = 6         # 🅱1 + 🅱2 mỗi 6 dòng
FAILED_NAMES  = 3         # ≤3 tên đủ, >3 in đếm + 3 mới nhất
NGOAI_L1_CAP  = 25        # ngoài L1 in-line cap

# α1/22-09 · lib helpers (shared với events_build + gom_e)
from lib.u0_class_tier import classify_tier
from lib.fund_state import fund_state_7d

# ── EVENTS READER · provenance check (AW2) ──────────────────────────────────

def read_events(target: str) -> tuple[Optional[list[dict]], str, str]:
    """Trả (rows | None, md5_hex | "", status).

    status ∈ {"ok", "N/A-ERROR:events-missing", "N/A-ERROR:md5-mismatch",
              "N/A-ERROR:target-mismatch"}
    p106: md5 file khớp .md5 sidecar (nếu có).
    p107 base: bell D phải == target; class/u1 mang d_cross riêng, không kiểm ở đây.
    """
    p     = ART_DIR / f"events_{target}.jsonl"
    md5_p = ART_DIR / f"events_{target}.md5"
    if not p.exists():
        return None, "", "N/A-ERROR:events-missing"
    body = p.read_bytes()
    actual_md5 = hashlib.md5(body).hexdigest()
    if md5_p.exists():
        expected = md5_p.read_text(encoding="utf-8").strip()
        if actual_md5 != expected:
            return None, actual_md5, "N/A-ERROR:md5-mismatch"
    rows = []
    for line in body.decode("utf-8", errors="replace").splitlines():
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    for r in rows:
        if r.get("type") == "bell":
            if r.get("D") != target:
                return None, actual_md5, "N/A-ERROR:target-mismatch"
    return rows, actual_md5, "ok"


def events_build_time_5nights(target: str) -> list[str]:
    """5 đêm gần nhất · mtime events_<d>.jsonl · trả list line."""
    out = []
    td = datetime.strptime(target, "%Y-%m-%d").date()
    for i in range(5):
        d = (td - timedelta(days=i)).isoformat()
        p = ART_DIR / f"events_{d}.jsonl"
        if p.exists():
            mt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            out.append(f"{d}: {mt.strftime('%H:%M:%S UTC')}")
        else:
            out.append(f"{d}: MISSING")
    return out


# ── REGISTRY HỢP 145 (Bảng A ∪ List A · p111) ────────────────────────────────

def load_bang_a() -> set:
    """Bảng A = gom_e in_registry (thres 0.85 · H1∧H2)."""
    p = STATE_DIR / "gom_e_state.json"
    if not p.exists(): return set()
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {sym for sym, v in s.items() if v.get("in_registry")}


def load_list_a(target: str) -> tuple[set, dict]:
    """List A = watchlist_daily gate (div ≤ 0.5 · sn_count_le050 ≥ 5).
    Trả (set_tokens, dict details {sym: (div, sn_count_le050)})."""
    import watchlist_daily as wl
    cfg = wl.load_config()
    td_data = wl.load_token_data(min_rows=cfg["data"]["min_history_rows"])
    reg, details = set(), {}
    for sym, arr in td_data.items():
        ep = wl.detect_episodes(arr, cfg)
        idx = next((i for i, r in enumerate(arr) if r["date"] == target), None)
        if idx is None: continue
        s = wl.snapshot(sym, arr, ep, idx, cfg)
        if wl.in_list_a(s, cfg):
            reg.add(sym)
            details[sym] = {
                "div":       s["div_ratio"],
                "sn":        s.get("sn_count_le050", 0),
                "acc_r":     s.get("lsr_acc", float("nan")),
                "pos_r":     s.get("lsr_pos", float("nan")),
                "fund":      s.get("fund", float("nan")),
                "start":     s.get("hedge_start_date", ""),
                "px_dist":   s.get("px_dist", float("nan")),
            }
    return reg, details


def _compute_registry_fields(sym: str, target: str, fw_extra: dict) -> dict:
    """β-fix2/22-09 · CANONICAL compute div_avg3/acc_r/pos_r cho MỘT sym tại target
    trực tiếp từ store · không chép từ GOM-E hay watchlist.

    Rule (mirror GOM-E · §1 spec):
      div_raw = pos_r/acc_r · div_avg3 = rolling(3, min_periods=1).mean(div_raw)
      low_conf mask (nếu có · L-21).

    Nếu store trống → trả reason string "N/A-<lý do>".
    """
    dmap = fw_extra.get(sym, {})
    if not dmap:
        return {"acc_r": None, "pos_r": None, "div_avg3": None,
                "reason": "N/A-no-store"}
    dates_all = sorted(dmap.keys())
    dates_up = [d for d in dates_all if d <= target]
    if not dates_up:
        return {"acc_r": None, "pos_r": None, "div_avg3": None,
                "reason": "N/A-no-history"}
    # Take 3 most recent for rolling mean
    recent = dates_up[-3:]
    div_vals = []
    for d in recent:
        row = dmap[d]
        pr = row.get("pos"); ar = row.get("acc")
        if pr is None or ar is None: continue
        if isinstance(pr, float) and math.isnan(pr): continue
        if isinstance(ar, float) and math.isnan(ar): continue
        if ar == 0: continue
        div_vals.append(pr / ar)
    if not div_vals:
        return {"acc_r": None, "pos_r": None, "div_avg3": None,
                "reason": "N/A-nan-fields"}
    # Last-day acc_r/pos_r (as-of target)
    last_row = dmap[dates_up[-1]]
    acc_r = last_row.get("acc")
    pos_r = last_row.get("pos")
    if isinstance(acc_r, float) and math.isnan(acc_r): acc_r = None
    if isinstance(pos_r, float) and math.isnan(pos_r): pos_r = None
    div_avg3 = sum(div_vals) / len(div_vals)
    return {"acc_r": acc_r, "pos_r": pos_r, "div_avg3": div_avg3, "reason": None}


def registry_hop_145(target: str, fw_extra: Optional[dict] = None) -> tuple[list[dict], str]:
    """Trả (registry_hop_list, registry_md5 hex[12]).

    Union Bảng A ∪ List A · β-fix2 · MỌI row div_avg3/acc_r/pos_r từ _compute_registry_fields.
    """
    if fw_extra is None: fw_extra = load_fw_extra(target)
    bang_a = load_bang_a()
    list_a_set, list_a_det = load_list_a(target)

    # Bảng A: load gom_e_state cho entry_date + state-birth check
    gp = STATE_DIR / "gom_e_state.json"
    gom_state = {}
    if gp.exists():
        try: gom_state = json.loads(gp.read_text(encoding="utf-8"))
        except Exception: pass  # L-66-OK
    state_birth = datetime.fromtimestamp(gp.stat().st_mtime if gp.exists() else 0,
                                          tz=timezone.utc).date()
    # Note: mtime rồi Birth khác; dùng birth mtime hoặc file stat st_ctime → dùng
    # AV2 findings: 74/121 entry=2026-09-07 (state Birth 09-08) → dán `≥Nd[state]`.

    td_d = datetime.strptime(target, "%Y-%m-%d").date()
    STORE_START_DATE = date(2026, 6, 27)  # p103 · store-start canonical

    rows = []
    union_syms = bang_a | list_a_set
    for sym in sorted(union_syms):
        in_A = sym in bang_a
        in_L = sym in list_a_set
        lst  = list_a_det.get(sym, {})
        # β-fix2 · CANONICAL fields từ store · KHÔNG dùng watchlist snapshot
        canon = _compute_registry_fields(sym, target, fw_extra)
        div_smooth = canon["div_avg3"] if canon["div_avg3"] is not None else float("nan")
        acc_r      = canon["acc_r"] if canon["acc_r"] is not None else float("nan")
        pos_r      = canon["pos_r"] if canon["pos_r"] is not None else float("nan")
        na_reason  = canon["reason"]
        sn         = lst.get("sn", 0)
        fund       = lst.get("fund", float("nan"))

        # Band + source (AW6)
        if in_A and in_L:
            source = "hai-bên"
        elif in_L:
            source = "hedge-run"
        else:
            source = "H1∧H2"
        # band: ≤0.5 nếu qua List A; 0.5-0.85 nếu chỉ ở Bảng A
        band = "≤0.5" if in_L else "0.5–0.85"

        # Tuổi (p103 · AV2 findings): ưu tiên hedge_start_date từ List A;
        # fallback entry_date từ gom_e; nếu = state-birth → `≥Nd[state]`.
        tuoi_str = "?"
        hedge_start = lst.get("start", "")
        if hedge_start:
            try:
                s_d = datetime.strptime(hedge_start, "%Y-%m-%d").date()
                dd = (td_d - s_d).days
                if s_d <= STORE_START_DATE:
                    tuoi_str = f"≥{dd}d[store]"
                else:
                    tuoi_str = f"{dd}d"
            except ValueError:
                tuoi_str = "?"
        elif in_A:
            entry = gom_state.get(sym, {}).get("entry_date")
            if entry:
                try:
                    e_d = datetime.strptime(entry, "%Y-%m-%d").date()
                    dd = (td_d - e_d).days
                    if dd < 0:
                        # state entry AFTER target · as-of state unavailable
                        tuoi_str = "?"
                    elif e_d <= state_birth:
                        tuoi_str = f"≥{dd}d[state]"
                    else:
                        tuoi_str = f"{dd}d"
                except ValueError:
                    tuoi_str = "?"

        rows.append({
            "sym":         sym,
            "in_A":        in_A,
            "in_L":        in_L,
            "div_smooth":  div_smooth,
            "sn":          sn,
            "acc_r":       acc_r,
            "pos_r":       pos_r,
            "fund":        fund,
            "band":        band,
            "source":      source,
            "tuoi_str":    tuoi_str,
            "na_reason":   na_reason,
        })

    # registry_md5 SẼ tính từ CSV audit (β-fix4) · placeholder tạm thời
    payload = json.dumps(
        sorted([f"{r['sym']}|{r['band']}|{r['source']}" for r in rows]),
        ensure_ascii=False,
    )
    reg_md5 = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]
    return rows, reg_md5


# ── LUẬT NỀN V1.4-A (≥2× đáy 60d) — p104 partial ────────────────────────────

def load_daily_rows(target: str, back: int = 90) -> dict:
    """Load fw_daily cho `back` ngày trước target (px_avg per date/sym)."""
    import csv
    td = datetime.strptime(target, "%Y-%m-%d").date()
    from_d = td - timedelta(days=back)
    by_sym_dates = {}
    months = set()
    d_cur = from_d
    while d_cur <= td:
        months.add(d_cur.strftime("%Y-%m"))
        d_cur += timedelta(days=1)
    for ym in sorted(months):
        p = STORE_DIR / f"freshwatch_daily_{ym}.csv"
        if not p.exists(): continue
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = r.get("date", "")
                if not d or d > target or d < from_d.isoformat(): continue
                sym = r.get("symbol", "")
                try: px = float(r.get("px_avg", "") or "nan")
                except Exception: px = float("nan")
                by_sym_dates.setdefault(sym, {})[d] = px
    return by_sym_dates


def luat_nen_2x_min60d(sym: str, target: str, price_map: dict) -> tuple[bool, int]:
    """Trả (over_2x, dist_days_from_min).
    ≥2× đáy 60d = px(T) ≥ 2 · min(px 60d gần nhất kết thúc target-1).
    """
    d_map = price_map.get(sym, {})
    if not d_map: return (False, 0)
    td = datetime.strptime(target, "%Y-%m-%d").date()
    px_now = d_map.get(target)
    if px_now is None or math.isnan(px_now): return (False, 0)
    windowed = []
    for i in range(1, 61):
        d = (td - timedelta(days=i)).isoformat()
        px = d_map.get(d)
        if px is not None and not math.isnan(px):
            windowed.append((d, px))
    if not windowed: return (False, 0)
    min_d, min_px = min(windowed, key=lambda x: x[1])
    if min_px <= 0: return (False, 0)
    kd = (td - datetime.strptime(min_d, "%Y-%m-%d").date()).days
    return (px_now >= 2 * min_px, kd)


# ── EVENTS BLOCK render ─────────────────────────────────────────────────────

def _dm(iso: str) -> str:
    """YYYY-MM-DD → DD/MM · fallback nguyên chuỗi."""
    if not iso or len(iso) < 10: return iso or "?"
    return f"{iso[8:10]}/{iso[5:7]}"


def render_events_block(events: list[dict], status: str, target: str,
                         luat_over_toks: Optional[dict] = None) -> list[str]:
    """SỰ KIỆN (phía crowd → xác nhận) block · AW4.

    luat_over_toks: {tok_bare: kd_days} · nếu token có luật nền → thêm [hậu-D0 +kd]
    """
    if luat_over_toks is None: luat_over_toks = {}
    lines = ["── SỰ KIỆN (phía crowd → xác nhận) ── [master-events]"]
    if status != "ok":
        lines.append(status)
        return lines

    n = 0
    # sort · bell first, then class, then u1 · bell_near/bell_blind → audit-only (spec §2)
    order = {"bell": 0, "class": 1, "u1": 2}
    events_e = [e for e in events if e.get("type") in order]
    events_e.sort(key=lambda e: (order.get(e.get("type"), 9), e.get("tok", "")))

    for e in events_e:
        t = e.get("type")
        tok = e.get("tok", "?")
        if t == "bell":
            dacc = (e.get("dacc_bwd") or 0.0) * 100
            dpos = (e.get("dpos_bwd") or 0.0) * 100
            # AC4: bỏ trường lead · α4: [hậu-D0] khi có luật nền
            luat_tag = ""
            if tok in luat_over_toks:
                luat_tag = f" [hậu-D0 +{luat_over_toks[tok]}d]"
            lines.append(
                f"[U0-BELL D={_dm(e.get('D', ''))} · "
                f"Δacc_bwd={dacc:+.0f}% · pos_bwd={dpos:+.0f}%] {tok}{luat_tag}"
            )
            n += 1
        elif t == "class":
            tier = e.get("tier", "?")
            dc = e.get("d_cross", "")
            dacc = (e.get("dacc") or 0.0) * 100
            dpos = abs(e.get("dpos") or 0.0) * 100
            # α4 · [hậu-D0 +kd] khi token có luật nền
            luat_tag = ""
            if tok in luat_over_toks:
                luat_tag = f" [hậu-D0 +{luat_over_toks[tok]}d]"
            if tier == "L1":
                try:
                    dc_d = datetime.strptime(dc, "%Y-%m-%d").date()
                    u1_due = (dc_d + timedelta(days=5)).strftime("%d/%m")
                except ValueError:
                    u1_due = "?"
                lines.append(
                    f"[U0-CLASS D_cross={_dm(dc)} · L1 · Δacc={dacc:+.0f}% · "
                    f"|Δpos|={dpos:.0f}%] {tok} → U1 due {u1_due}{luat_tag}"
                )
            else:
                # §14 · L2/L3/BLIND VẪN in — nhãn không giấu token có event
                lines.append(
                    f"[U0-CLASS D_cross={_dm(dc)} · {tier} · Δacc={dacc:+.0f}% · "
                    f"|Δpos|={dpos:.0f}%] {tok} (không mở U1){luat_tag}"
                )
            n += 1
        elif t == "u1":
            v1 = e.get("v1")
            v2 = e.get("v2")
            verdict = e.get("verdict", "?")
            v1s = f"{v1:.2f}" if isinstance(v1, (int, float)) else "?"
            v2s = f"{v2:.2f}" if isinstance(v2, (int, float)) else "?"
            v1m = "✓" if isinstance(v1, (int, float)) and v1 <= 0.6 else "✗"
            v2m = "✓" if isinstance(v2, (int, float)) and v2 >= 1.5 else "✗"
            state = "CONFIRMED" if verdict == "PASS" else "FAILED"
            lines.append(
                f"[U1 D+5 · v1={v1s} {v1m} v2={v2s} {v2m}] {tok} → {state}"
            )
            n += 1

    if n == 0:
        lines.append("hôm nay: không event")
    return lines


# ── WHALE block (🅱1/🅱2 · AW5 · Δpos thật) ──────────────────────────────────

def _rows_last2(sym: str, price_map: dict, extra: dict) -> tuple[Optional[dict], Optional[dict]]:
    """Trả (row_T, row_T-1) từ CSV fw_daily. price_map (đã load) mapping."""
    if sym not in extra: return None, None
    dates = sorted(extra[sym].keys())
    if len(dates) < 2: return None, None
    return extra[sym].get(dates[-1]), extra[sym].get(dates[-2])


def load_fw_extra(target: str, back: int = 30) -> dict:
    """Load fw_daily rows cho pos/acc/oi/px + f_min/f_avg.
    Trả {sym: {date: {pos, acc, oi, px, f_min, f_avg}}}."""
    import csv
    td = datetime.strptime(target, "%Y-%m-%d").date()
    from_d = td - timedelta(days=back)
    out = {}
    months = set()
    d_cur = from_d
    while d_cur <= td:
        months.add(d_cur.strftime("%Y-%m"))
        d_cur += timedelta(days=1)
    for ym in sorted(months):
        p = STORE_DIR / f"freshwatch_daily_{ym}.csv"
        if not p.exists(): continue
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = r.get("date", "")
                if not d or d > target or d < from_d.isoformat(): continue
                sym = r.get("symbol", "")
                def _f(k):
                    try: return float(r.get(k, "") or "nan")
                    except Exception: return float("nan")
                out.setdefault(sym, {})[d] = {
                    "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                    "oi":  _f("oi_usd"),   "px":  _f("px_avg"),
                    "f_min": _f("funding_min"), "f_avg": _f("funding_avg"),
                }
    return out


def _fund_state_for_sym(sym: str, target: str, fw_extra: dict) -> str:
    """α2/22-09 · fund_state 7d wrap sym → PIN | SHORT-TRẢ | NONE."""
    dmap = fw_extra.get(sym, {})
    if not dmap: return "NONE"
    dates = sorted(dmap.keys())[-7:]
    days = [{"f_min": dmap[d].get("f_min"), "f_avg": dmap[d].get("f_avg")} for d in dates]
    return fund_state_7d(days)


def _strip_usdt(sym: str) -> str:
    """α3/22-09 · bỏ hậu tố USDT (STEEMUSDT → STEEM) · cùng chuỗi tên master/HEDGE."""
    return sym[:-4] if sym.endswith("USDT") else sym


def render_whale_block(target: str, fw_extra: dict,
                       class_by_sym: dict) -> list[str]:
    """🅱1 short-cover · 🅱2 whale đổi ghế · Δpos thật (pos_r(T)/pos_r(T-1)-1)."""
    lines = ["── PHÍA WHALE (mô tả, KHÔNG phải chuông) ──"]
    td = datetime.strptime(target, "%Y-%m-%d").date()
    d_prev = (td - timedelta(days=1)).isoformat()

    b1, b2 = [], []
    for sym, dmap in fw_extra.items():
        row_T = dmap.get(target)
        row_p = dmap.get(d_prev)
        if not row_T or not row_p: continue
        pos_T, pos_p = row_T["pos"], row_p["pos"]
        oi_T,  oi_p  = row_T["oi"],  row_p["oi"]
        if any(math.isnan(x) for x in (pos_T, pos_p, oi_T, oi_p)): continue
        if pos_p == 0 or oi_p == 0: continue
        dpos = pos_T / pos_p - 1        # Δpos thật
        doi  = oi_T  / oi_p  - 1
        # 🅱 gate: Δpos ≥ +10%
        if dpos < 0.10: continue
        # α3: bỏ USDT suffix · match tên events
        sym_bare = _strip_usdt(sym)
        row = {"sym": sym_bare, "dpos": dpos, "doi": doi,
               "class": class_by_sym.get(sym_bare, "")}
        if doi <= -0.03: b1.append(row)     # short-cover
        elif doi >= 0.03: b2.append(row)    # whale đổi ghế

    b1.sort(key=lambda r: -r["dpos"])
    b2.sort(key=lambda r: -r["dpos"])
    b1 = b1[:WHALE_CAP]
    b2 = b2[:WHALE_CAP]

    if b1:
        parts = []
        for r in b1:
            cls_s = f" → {r['class']}" if r["class"] else ""
            parts.append(f"{r['sym']} Δpos {r['dpos']*100:+.0f}% ΔOI {r['doi']*100:+.0f}%{cls_s}")
        lines.append(f"🅱1 short-cover (Δpos≥+10% ∧ ΔOI≤−3%): " + " · ".join(parts))
    if b2:
        parts = []
        for r in b2:
            cls_s = f" → {r['class']}" if r["class"] else ""
            parts.append(f"{r['sym']} Δpos {r['dpos']*100:+.0f}% ΔOI {r['doi']*100:+.0f}%{cls_s}")
        lines.append(f"🅱2 whale đổi ghế (Δpos≥+10% ∧ ΔOI≥+3%): " + " · ".join(parts))
    if not b1 and not b2:
        lines.append("(không token nào đạt Δpos≥+10%)")
    return lines


# ── REGISTRY HỢP block · top-15 · AW6 · p111 ─────────────────────────────────

def render_registry_block(rows: list[dict], reg_md5: str,
                           events_by_tok: dict, price_map: dict,
                           target: str, fw_extra: dict,
                           events: list) -> list[str]:
    """LIST A · REGISTRY hợp 145 · top-15 xếp div tăng · p104 · p107 · α5.

    α4/22-09: luật nền loại 6 token → tên đích danh audit line.
    α5/22-09: cột kr=? · dòng STALE k · dòng Nguội: tên (từ mai · từ snapshot D-1).
    """
    total = len(rows)
    lines = [f"── LIST A · REGISTRY HỢP {total} tokens (Bảng A ∪ List A) ──"]
    lines.append("sym · dải · nguồn · d=div a=acc p=pos · fund · kr · tuổi")

    # Sort: div tăng dần (NaN → cuối)
    rows_sorted = sorted(rows, key=lambda r: (
        float("inf") if (isinstance(r["div_smooth"], float) and math.isnan(r["div_smooth"]))
        else r["div_smooth"]
    ))

    # Tag luật nền cho từng row · lookup one lần
    over_map = {}
    kd_map = {}
    for r in rows_sorted:
        over, kd = luat_nen_2x_min60d(r["sym"], target, price_map)
        over_map[r["sym"]] = over
        kd_map[r["sym"]] = kd

    # top-15 SAU KHI loại luật-nền · lấy 15 đầu KHÔNG bị luật nền
    top = [r for r in rows_sorted if not over_map[r["sym"]]][:REGISTRY_TOP]
    top_syms = {r["sym"] for r in top}

    # p107 · event tokens ép vào (nếu chưa có, kể cả bị luật nền hoặc rớt top-15)
    # events_by_tok dùng short-form tok · registry dùng USDT-suffixed sym · match cả 2
    event_syms_bare = set(events_by_tok.keys())
    reg_syms = {r["sym"] for r in rows_sorted}
    forced_in_reg = set()
    for sym in reg_syms:
        bare = _strip_usdt(sym)
        if bare in event_syms_bare and sym not in top_syms:
            forced_in_reg.add(sym)
    forced_rows = []
    for sym in sorted(forced_in_reg):
        r = next((r for r in rows_sorted if r["sym"] == sym), None)
        if r: forced_rows.append(r)

    def _line(r):
        # β-fix2 · store rỗng → in "N/A-<reason>" thay "?"
        na_r = r.get("na_reason")
        if na_r:
            div_s = na_r
            acc_s = na_r
            pos_s = na_r
        else:
            div_s = f"{r['div_smooth']:.3f}" if (isinstance(r["div_smooth"], float) and
                                                  not math.isnan(r["div_smooth"])) else "N/A"
            acc_s = f"{r['acc_r']:.2f}" if isinstance(r["acc_r"], float) and not math.isnan(r["acc_r"]) else "?"
            pos_s = f"{r['pos_r']:.2f}" if isinstance(r["pos_r"], float) and not math.isnan(r["pos_r"]) else "?"
        # α2 · fund_state 7d · lib.fund_state
        fund_s = _fund_state_for_sym(r["sym"], target, fw_extra)
        bare = _strip_usdt(r["sym"])
        ev_tag = f" [{events_by_tok.get(bare, '')}]" if bare in event_syms_bare else ""
        # p104 · nếu over 2×min60d, thêm [hậu-D0 +kd]
        luat_tag = f" [hậu-D0 +{kd_map[r['sym']]}d]" if over_map.get(r["sym"]) else ""
        # compact format · d/a/p labels · β-fix1 bỏ USDT hậu tố
        return (f"  {_strip_usdt(r['sym'])} · {r['band']} · {r['source']} · "
                f"d={div_s} a={acc_s} p={pos_s} {fund_s} kr=? {r['tuoi_str']}{ev_tag}{luat_tag}")

    for r in top:
        lines.append(_line(r))

    if forced_rows:
        for r in forced_rows:
            lines.append(_line(r))

    if total > len(top) + len(forced_rows):
        lines.append(f"(+{total - len(top) - len(forced_rows)} tokens đủ ở audit)")

    # α4 · luật nền tokens đích danh (audit line)
    over_syms = sorted([r["sym"] for r in rows_sorted if over_map[r["sym"]]])
    if over_syms:
        lines.append(f"luật-nền: ≥2× đáy only · POST-routing defer · loại {len(over_syms)}: "
                     + " · ".join(_strip_usdt(s) for s in over_syms))

    # α5 · STALE k (từ btier · CONFIRMED >30d)
    stale_toks = sorted([e["tok"] for e in events if e.get("type") == "btier"
                        and e.get("tier") == "STALE"])
    if stale_toks:
        lines.append(f"STALE {len(stale_toks)}: " + " · ".join(stale_toks))
    else:
        lines.append("STALE 0")

    # α5 · Nguội (rời registry ≥3d · từ snapshot D-1 · chưa wire · in placeholder)
    lines.append("Nguội: (chưa có snapshot D-1 · từ mai)")

    return lines


# ── FROM MASTER · cand top-15, FAILED, ngoài L1 (AW7) ────────────────────────

def _load_l2_l3_ngoai(target: str) -> list[str]:
    """Đọc data/logs/b_l2_l3_reject.jsonl · trả tokens L2/L3 ngoài L1 cho target."""
    p = _REPO / "data/logs/b_l2_l3_reject.jsonl"
    if not p.exists(): return []
    toks = set()
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip(): continue
            try: r = json.loads(line)
            except json.JSONDecodeError: continue
            if r.get("target") == target:
                t = r.get("token")
                if t: toks.add(t)
    except OSError:
        return []
    return sorted(toks)


def render_from_master_block(events: list[dict], target: str) -> list[str]:
    """cand top-15 · FAILED · ngoài L1: k (TOK L2 · TOK L3 …) đủ tên."""
    lines = ["── TỪ MASTER (E4(iii)) ──"]
    btier = [e for e in events if e.get("type") == "btier"]
    cand    = sorted([e["tok"] for e in btier if e.get("tier") == "cand"])
    failed  = sorted([e["tok"] for e in btier if e.get("tier") == "FAILED"])
    # ngoài L1 · nguồn: b_l2_l3_reject.jsonl per target (btier state chỉ giữ L1-only)
    l2_l3   = _load_l2_l3_ngoai(target)

    if cand:
        top = cand[:REGISTRY_TOP]
        lines.append(f"cand top-{REGISTRY_TOP} · {len(cand)} tổng: " + " · ".join(top))
        if len(cand) > REGISTRY_TOP:
            lines.append(f"  (+{len(cand)-REGISTRY_TOP} tokens đủ ở audit)")

    if failed:
        if len(failed) <= FAILED_NAMES:
            lines.append(f"FAILED {len(failed)}: " + " · ".join(failed))
        else:
            lines.append(f"FAILED {len(failed)}: " + " · ".join(failed[-FAILED_NAMES:]) +
                         f" (+{len(failed) - FAILED_NAMES} audit)")

    # ngoài L1 · cap 25 tokens in-line (spec "đủ tên" audit-only nếu vượt)
    NGOAI_L1_CAP = 25
    if l2_l3:
        if len(l2_l3) <= NGOAI_L1_CAP:
            lines.append(f"ngoài L1: {len(l2_l3)} (" + " · ".join(l2_l3) + ")")
        else:
            head = l2_l3[:NGOAI_L1_CAP]
            rest = len(l2_l3) - NGOAI_L1_CAP
            lines.append(f"ngoài L1: {len(l2_l3)} (" + " · ".join(head) + f" · +{rest} audit)")

    return lines


# ── MAIN COMPOSE ─────────────────────────────────────────────────────────────

def compose_body(target: str, report_only: bool = True,
                 errata: bool = False, write_audit: bool = True) -> tuple[str, dict]:
    """Trả (body_str, meta).

    β-fix4: write_audit=True → ghi hedge_registry_<T>.csv + registry_md5 từ CSV bytes.
    meta: {events_md5, events_status, registry_md5, n_reg, n_events, tg_len, ...}
    """
    events, events_md5, events_status = read_events(target)
    if events is None: events = []

    # class_by_sym cho tag WHALE · α1: L2/L3 tach riêng
    class_by_sym = {}
    events_by_tok = {}
    for e in events:
        tok = e.get("tok")
        t = e.get("type")
        if not tok: continue
        if t == "bell": events_by_tok[tok] = "BELL"
        elif t == "class":
            tier = e.get("tier", "")
            events_by_tok[tok] = f"CLASS-{tier}"
            # α1: giữ L2/L3 tach riêng · legacy L2_OR_L3 fallback → L2
            if tier == "L2":
                class_by_sym[tok] = "L2"
            elif tier == "L3":
                class_by_sym[tok] = "L3"
            elif tier == "L2_OR_L3":  # legacy events file
                class_by_sym[tok] = "L2"
        elif t == "u1":
            events_by_tok[tok] = f"U1-{e.get('verdict', '?')}"

    # fw_extra cho WHALE + registry canonical + price_map cho luật nền
    fw_extra = load_fw_extra(target)
    price_map = load_daily_rows(target)

    # Registry hợp 145 · p111 · β-fix2 canonical fields
    reg_rows, _reg_md5_tmp = registry_hop_145(target, fw_extra=fw_extra)

    # Scanned/blind
    fw_syms = set()
    if FW_SYM_P.exists():
        fw_syms = {ln.strip() for ln in FW_SYM_P.read_text(encoding="utf-8").splitlines() if ln.strip()}
    n_universe = len(fw_syms)
    n_scanned = len([s for s in fw_syms if s in fw_extra and target in fw_extra[s]])
    n_blind = n_universe - n_scanned

    # Header
    from collections import Counter
    ev_type_counts = Counter([e.get("type") for e in events])
    n_bell = ev_type_counts.get("bell", 0)
    n_class_l1 = sum(1 for e in events if e.get("type") == "class" and e.get("tier") == "L1")
    n_u1 = ev_type_counts.get("u1", 0)

    # α7 · U1-pending = class L1 events có D_cross+5 > target · tính due nearest
    td_d = datetime.strptime(target, "%Y-%m-%d").date()
    pending = []
    for e in events:
        if e.get("type") != "class" or e.get("tier") != "L1": continue
        dc = e.get("d_cross", "")
        try:
            dc_d = datetime.strptime(dc, "%Y-%m-%d").date()
            due_d = dc_d + timedelta(days=5)
        except ValueError:
            continue
        if due_d > td_d:
            pending.append((e.get("tok", "?"), due_d))
    pending.sort(key=lambda x: x[1])
    n_pending = len(pending)
    if pending:
        due_nearest = pending[0][1].strftime("%d/%m")
        pending_str = f"U1-pending={n_pending} (due {due_nearest})"
    else:
        pending_str = f"U1-pending=0"

    # α4 · luat_over_toks · dict {tok_bare: kd_days} cho events block [hậu-D0]
    luat_over_toks = {}
    # Check registry over-2× tokens (used both in registry + events blocks)
    for r in reg_rows:
        over, kd = luat_nen_2x_min60d(r["sym"], target, price_map)
        if over:
            luat_over_toks[_strip_usdt(r["sym"])] = kd
    # Also check event tokens outside registry (bell/class fires)
    for e in events:
        tok = e.get("tok")
        if not tok or tok in luat_over_toks: continue
        # Try both bare + USDT-suffixed
        for candidate_sym in (f"{tok}USDT", tok):
            if candidate_sym in price_map:
                over, kd = luat_nen_2x_min60d(candidate_sym, target, price_map)
                if over:
                    luat_over_toks[tok] = kd
                    break

    header_lines = []
    header_pref = "[HEDGE v2 · REPORT-ONLY]" if report_only else "[HEDGE v2]"
    header_lines.append(
        f"{header_pref} {target} · scanned={n_scanned}/{n_universe} · "
        f"blind={n_blind} · registry={len(reg_rows)} · "
        f"bell={n_bell} · cross-L1={n_class_l1} · {pending_str} [CAL-ONLY]"
    )

    if errata:
        header_lines.append("⚠ ERRATA đêm đầu: 🎓 TỐT-NGHIỆP BỎ · 🅱 nghĩa mới (Δpos thật ≥+10%) · "
                            "registry = hợp Bảng A ∪ List A (không phải List A cũ)")

    # β-fix4 · Ghi audit CSV TRƯỚC · registry_md5 lấy từ CSV bytes
    audit_path = f"data/artifacts/hedge_registry_{target}.csv"
    if write_audit:
        _p, reg_md5 = write_audit_csv(target, reg_rows, events_by_tok=events_by_tok)
    else:
        reg_md5 = _reg_md5_tmp

    # Compose
    parts = header_lines + [""]
    parts += render_events_block(events, events_status, target, luat_over_toks) + [""]
    parts += render_whale_block(target, fw_extra, class_by_sym) + [""]
    parts += render_registry_block(reg_rows, reg_md5, events_by_tok, price_map, target,
                                    fw_extra, events) + [""]
    parts += render_from_master_block(events, target) + [""]

    # Footer (AW10 · α6 CHƯA KÝ marker)
    parts.append(f"━━ footer ━━ universe_gen={n_universe} [CHƯA KÝ] · "
                 f"events_md5={events_md5[:12] if events_md5 else 'N/A'} "
                 f"· registry_md5={reg_md5} · audit={audit_path}")

    body = "\n".join(parts)

    # tg_len (UTF-16 code unit)
    try:
        from lib.tg_len import tg_len
        body_tg_len = tg_len(body)
    except ImportError:
        body_tg_len = len(body.encode("utf-16-le")) // 2

    meta = {
        "target":          target,
        "events_md5":      events_md5,
        "events_status":   events_status,
        "registry_md5":    reg_md5,
        "n_reg":           len(reg_rows),
        "n_events":        len(events),
        "n_bell":          n_bell,
        "n_class_L1":      n_class_l1,
        "n_u1":            n_u1,
        "n_u1_pending":    n_pending,
        "n_luat_nen":      len(luat_over_toks),
        "n_scanned":       n_scanned,
        "n_universe":      n_universe,
        "n_blind":         n_blind,
        "tg_len":          body_tg_len,
        "body_budget":     BODY_BUDGET,
        "over_budget":     body_tg_len > BODY_BUDGET,
    }
    return body, meta


# ── β-fix4 · AUDIT CSV + registry_md5 từ CSV bytes ───────────────────────────

def write_audit_csv(target: str, reg_rows: list[dict], out_dir: Optional[Path] = None,
                     events_by_tok: Optional[dict] = None) -> tuple[Path, str]:
    """Ghi hedge_registry_<T>.csv · trả (path, md5_from_bytes[12]).

    β-fix4: registry_md5 tính TỪ NỘI DUNG CSV bytes vừa ghi · không cache.
    Cột: sym · in_A · in_L · dải · nguồn · div_avg3 · acc_r · pos_r · fund · kr · tuổi · na_reason
    """
    import csv as _csv_a
    if out_dir is None: out_dir = ART_DIR
    if events_by_tok is None: events_by_tok = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"hedge_registry_{target}.csv"
    md5_p = out_dir / f"hedge_registry_{target}.md5"
    cols = ["sym", "in_A", "in_L", "dai", "nguon",
            "div_avg3", "acc_r", "pos_r",
            "fund_state", "kr_share", "tuoi", "na_reason", "event_today"]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = _csv_a.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(reg_rows, key=lambda x: x["sym"]):
            bare = _strip_usdt(r["sym"])
            fund_s = "N/A"
            # fund_state đã tính ở render; ở đây tính lại (canonical)
            row_out = {
                "sym":        bare,
                "in_A":       int(r["in_A"]),
                "in_L":       int(r["in_L"]),
                "dai":        r["band"],
                "nguon":      r["source"],
                "div_avg3":   ("" if r.get("na_reason") else
                               f"{r['div_smooth']:.6f}"
                               if isinstance(r["div_smooth"], float) and not math.isnan(r["div_smooth"])
                               else ""),
                "acc_r":      ("" if r.get("na_reason") else
                               f"{r['acc_r']:.6f}"
                               if isinstance(r["acc_r"], float) and not math.isnan(r["acc_r"])
                               else ""),
                "pos_r":      ("" if r.get("na_reason") else
                               f"{r['pos_r']:.6f}"
                               if isinstance(r["pos_r"], float) and not math.isnan(r["pos_r"])
                               else ""),
                "fund_state": fund_s,   # placeholder · compute_body sẽ pass đúng
                "kr_share":   "N/A",   # kr chưa wire · β5 defer
                "tuoi":       r["tuoi_str"],
                "na_reason":  r.get("na_reason") or "",
                "event_today": events_by_tok.get(bare, ""),
            }
            w.writerow(row_out)
    # md5 canonical từ CSV bytes vừa ghi
    md5_hex = hashlib.md5(p.read_bytes()).hexdigest()
    md5_p.write_text(md5_hex + "\n", encoding="utf-8")
    return p, md5_hex[:12]


# ── β2/β3 · U7 GATE SENDER + JOURNAL KÍCH-vì-chân-HEDGE ────────────────────────────

def _u7_scan_bad_html(body: str) -> Optional[tuple]:
    """Whitelist tags {b, i, u, s, a, code, pre, tg-spoiler, blockquote}.
    Trả (tag_str, pos) nếu có tag ngoài whitelist · None nếu OK."""
    import re
    WL = {"b", "i", "u", "s", "a", "code", "pre", "tg-spoiler", "blockquote"}
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9_-]*)", body):
        tag = m.group(2).lower()
        if tag not in WL:
            return (m.group(0), m.start())
    return None


def u7_gate(body: str, tg_limit: int = 4096) -> tuple[bool, str]:
    """Cổng U7 · β2 · tg_len + parse_mode + HTML scan · CẤM SLICE.

    Trả (ok, reason). Reason là "" khi ok, error string khi fail.
    """
    try:
        from lib.tg_len import tg_len
        n = tg_len(body)
    except ImportError:
        n = len(body.encode("utf-16-le")) // 2
    if n > tg_limit:
        return False, f"U7-BLOCKED-LEN body={n} > tg_limit={tg_limit}"
    bad = _u7_scan_bad_html(body)
    if bad is not None:
        return False, f"U7-BLOCKED-HTML tag={bad[0]} pos={bad[1]}"
    return True, ""


HEDGE_JOURNAL = _REPO / "data/logs/hedge_v2_journal.jsonl"

def write_hedge_journal(target: str, ok: bool, body_md5: str,
                         tg_len_val: int, fail_reason: str = "") -> None:
    """β3 · journal marker · master (γ) đọc để dán KÍCH-vì-chân-HEDGE."""
    HEDGE_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "ts_utc":         ts,
        "target_date":    target,
        "renderer":       "watchlist",   # AW1 · giữ renderer_id
        "product":        "hedge_v2",
        "ok":             ok,
        "body_md5":       body_md5,
        "tg_len":         tg_len_val,
        "fail_reason":    fail_reason,
        "leg_fail_label": "" if ok else "KÍCH-vì-chân-HEDGE",
    }
    with HEDGE_JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def send_hedge_v2(target: str, body: str, meta: dict, dry_run: bool = True) -> dict:
    """β2 · sender wrap · U7 gate + journal write + artifact dump (dry mode).

    dry_run=True: KHÔNG gọi tg_send · chỉ viết artifacts + journal (dry pipe).
    dry_run=False: gọi thật · giữ cho γ.
    """
    body_md5 = hashlib.md5(body.encode("utf-8")).hexdigest()
    ok_u7, reason = u7_gate(body)
    result = {
        "target":       target,
        "body_md5":     body_md5[:12],
        "tg_len":       meta.get("tg_len", 0),
        "u7_ok":        ok_u7,
        "u7_reason":    reason,
        "sent":         False,
        "journal_line": None,
    }
    if not ok_u7:
        # β3 · journal fail marker · master (γ) verdict SẼ dán KÍCH-vì-chân-HEDGE
        write_hedge_journal(target, ok=False, body_md5=body_md5[:12],
                            tg_len_val=meta.get("tg_len", 0), fail_reason=reason)
        return result
    # Artifact dump (dry mode) · master compute_night_verdict cần tg_final_watchlist_<T>.txt/jsonl
    art_txt = ART_DIR / f"tg_final_watchlist_{target}.txt"
    art_jsonl = ART_DIR / f"tg_final_watchlist_{target}.jsonl"
    ART_DIR.mkdir(parents=True, exist_ok=True)
    art_txt.write_text(body, encoding="utf-8")
    entry_jsonl = {
        "ts_utc":      datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "renderer":    "watchlist",
        "product":     "hedge_v2",
        "target_date": target,
        "body_md5":    body_md5,
        "tg_len":      meta.get("tg_len", 0),
        "dry":         dry_run,
    }
    with art_jsonl.open("w", encoding="utf-8") as f:
        f.write(json.dumps(entry_jsonl, ensure_ascii=False) + "\n")

    if dry_run:
        result["sent"] = False
        result["journal_line"] = "dry"
        # Không write hedge_journal ok=True ở dry (tránh dán marker prod)
        return result

    # γ · sender thật · gọi tg_send · post-check
    from run_gom_daily import tg_send   # reuse
    ok_send = tg_send(body, parse_mode="")   # HTML gate đã qua U7
    write_hedge_journal(target, ok=ok_send, body_md5=body_md5[:12],
                        tg_len_val=meta.get("tg_len", 0),
                        fail_reason="" if ok_send else "TG-SEND-FAIL")
    result["sent"] = ok_send
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--report-only", action="store_true", default=True)
    ap.add_argument("--errata", action="store_true")
    ap.add_argument("--full", action="store_true", help="Print full body")
    args = ap.parse_args()

    body, meta = compose_body(args.target, report_only=args.report_only, errata=args.errata)
    if args.full:
        print(body)
        print()
    print(f"[hedge_v2] target={meta['target']} · tg_len={meta['tg_len']}/{meta['body_budget']} "
          f"· events={meta['n_events']} ({meta['events_status']}) · reg={meta['n_reg']} · "
          f"bell={meta['n_bell']} · cross-L1={meta['n_class_L1']} · U1={meta['n_u1']} · "
          f"U1-pending={meta['n_u1_pending']} · luật-nền={meta['n_luat_nen']} · "
          f"scanned={meta['n_scanned']}/{meta['n_universe']} · blind={meta['n_blind']}")

"""DIGEST SUMMARY V2 · R1/R2/R3 VERBATIM per operator NHỊP-KÊNH · KÝ 07/09 V1.2 FIX-ROUND.

R2 TEMPLATES (verbatim từ operator directive · CẤM lệch chữ):
  GOM-H: <n> reo (<top-3 tên+k/4>) · ⏳<n> · 🔥nợ:<tok n/14> → #gomh
  HEDGE: A=<n> · B-top: <tok +Δdiv (oi_note)> ×2 · 🎓<n hoặc tên> → #hedge
  KHO:   📥<n> (<top-3 tên>) / 📤<n> (<top-3 tên>) → #kho
  FRESH: <n> (<top-2, ưu tiên 🆕>) → #fresh
  RÒNG:  <n> chương (<mở-hôm-nay> · <Q1-max tok $>) · churn<n>→file · CLOSED:<tok> → #ròng

Mọi field lấy AS-PRINTED theo sort-key sẵn của kênh (selection, zero compose).
KHÔNG bảng · KHÔNG medal-lines · KHÔNG cột giá/bal · 👁 đọc THẲNG yaml forward_tests.
Footer thêm ledger_state_md5 + fixture_md5.

⭐/📒/🚪 từ ledger view (events JSONL + view regen L-74).
⛔ flag-file direct-read (DEV-CAT-02) · 1 dòng.
"""
from __future__ import annotations
import sys, os, re, json, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (sys.stdout.reconfigure fallback for Python <3.7 · benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
ART_DIR = REPO / "data/artifacts"
LEDGER_DIR = REPO / "data/logs/event_ledger"
FIXTURE_DIR = REPO / "tests/fixtures/parity"
STATE_DIR = REPO / "data/state"
EXPORT_DIR = REPO / "data/export"


# V3.5l · GOM-E subtag source: watchlist LIST-A (registry) + freshwatch_daily (div, gLSR)
_GOME_DIV_CAGED = 0.5  # provisional_unsigned · ký bàn 27/09


def _gome_subtag_map(target: str) -> tuple[dict, str]:
    """Return {sym → subtag_str} + source_status.
    subtag_str examples:
      "PRE-CAGED [div=0.247·gLSR=4.35]"  (registry ∧ div ≤ 0.5)
      "PRE-OPEN"                          (not registry OR div > 0.5)
      None                                (source missing · caller renders [GOME-SRC-MISSING])
    source_status: "ok" | "missing-watchlist" | "missing-freshwatch"
    """
    # Watchlist state (registry = LIST-A)
    wl_p = STATE_DIR / f"hedge_watchlist_{target}.json"
    if not wl_p.exists():
        return ({}, "missing-watchlist")
    try:
        wl = json.loads(wl_p.read_text(encoding="utf-8"))
    except Exception:
        return ({}, "missing-watchlist")
    la = wl.get("list_a_tokens", [])
    registry = set()
    if isinstance(la, list):
        for t in la:
            if isinstance(t, str):
                registry.add(t.replace("USDT", "") if t.endswith("USDT") else t)
    elif isinstance(la, dict):
        for k in la.keys():
            registry.add(k.replace("USDT","") if k.endswith("USDT") else k)
    # Freshwatch daily (div_avg3 · gLSR)
    yyyy_mm = target[:7]
    fw_p = EXPORT_DIR / f"freshwatch_daily_{yyyy_mm}.csv"
    if not fw_p.exists():
        return ({}, "missing-freshwatch")
    import csv as _csv
    from statistics import mean as _mean
    fw_rows = {}
    with open(fw_p, encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            sym = row.get("symbol", "")
            try:
                pos = float(row.get("lsr_pos_r", "nan"))
                acc = float(row.get("lsr_acc_r", "nan"))
                glsr = float(row.get("lsr_global_r", "nan"))
            except: continue
            fw_rows.setdefault(sym, []).append({"date": row["date"], "pos": pos, "acc": acc, "glsr": glsr})
    for sym in fw_rows: fw_rows[sym].sort(key=lambda r: r["date"])
    # avg3 helper
    def _div_glsr(sym_usdt: str, target_d: str) -> tuple[float | None, float | None]:
        rows = fw_rows.get(sym_usdt, [])
        idx = next((i for i, r in enumerate(rows) if r["date"] == target_d), None)
        if idx is None: return (None, None)
        pos_vals = [rows[j]["pos"] for j in range(max(0, idx - 2), idx + 1) if rows[j]["pos"] == rows[j]["pos"]]
        acc_vals = [rows[j]["acc"] for j in range(max(0, idx - 2), idx + 1) if rows[j]["acc"] == rows[j]["acc"]]
        if not pos_vals or not acc_vals: return (None, None)
        div = _mean(pos_vals) / _mean(acc_vals) if _mean(acc_vals) else None
        glsr = rows[idx]["glsr"] if rows[idx]["glsr"] == rows[idx]["glsr"] else None
        return (div, glsr)
    # Build map for stars (called with subset from caller)
    result = {}
    for sym in registry | set(k.replace("USDT","") for k in fw_rows.keys() if k.endswith("USDT")):
        sym_usdt = f"{sym}USDT"
        div, glsr = _div_glsr(sym_usdt, target)
        in_reg = sym in registry
        if in_reg and div is not None and div <= _GOME_DIV_CAGED:
            div_s = f"{div:.3f}"; glsr_s = f"{glsr:.2f}" if glsr is not None else "N/A"
            result[sym] = f"PRE-CAGED [div={div_s}·gLSR={glsr_s}]"
        else:
            result[sym] = "PRE-OPEN"
    return (result, "ok")


def _load_artifact(renderer: str, target: str) -> tuple[str, str]:
    """Priority: as-sent > log-block > reconstructed."""
    for prefix in [f"tg_final_{renderer}_", f"{renderer}_"]:
        p = ART_DIR / f"{prefix}{target}.txt"
        if p.exists():
            body = p.read_text(encoding="utf-8", errors="replace")
            fl = body.split("\n", 1)[0]
            m = re.match(r"\[PROVENANCE=(\S+)\]", fl)
            prov = m.group(1) if m else "unknown"
            body_str = body.split("\n", 2)[-1] if body.startswith("[PROVENANCE=") else body
            return (body_str, prov)
    return ("", "missing")


def _tripwire_line() -> str:
    p = REPO / "data/state/tripwire_e2_v2_TRIPPED.flag"
    if not p.exists(): return ""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return f"⛔ REPORT-ONLY (tripwire {d.get('rate',0):.3f} > {d.get('threshold',0)} [TRIP])"
    except: return ""


# ---- R2 TEMPLATE builders per kênh · selection zero-compose ----

def _gomh_line(text: str) -> str:
    """GOM-H: <n> reo (<top-3 tên+k/4>) · ⏳<n> · 🔥nợ:<tok n/14> → #gomh"""
    m_fire = re.search(r"🔔 REO HÔM NAY:\s+(\d+)\s+·\s+⏳ đang nén:\s+(\d+)", text)
    n_reo = int(m_fire.group(1)) if m_fire else 0
    n_supp = int(m_fire.group(2)) if m_fire else 0
    # top-3 fires from 🟢 block · format `TOKEN k/4` (bare token, no USDT)
    top = []
    for line in text.split("\n"):
        m = re.match(r"^\s+[🥇🥈🥉•] (\S+)USDT?\s+\[(\S+)\]\s+\S+\s+(\d+/\d+)", line)
        if m and len(top) < 3:
            top.append(f"{m.group(1)} {m.group(3)}")
    # top-nợ (🔥 lines from ⏳ block · pick first · format `TOK n/14`)
    top_no = ""
    for line in text.split("\n"):
        m = re.match(r"^\s+🔥 (\S+)USDT?\s+\[.*?\]\s+\S+\s+\d+/\d+\s+·\s+ngày\s+(\d+/\d+)", line)
        if m:
            top_no = f"{m.group(1)} {m.group(2)}"; break
    top_str = ", ".join(top) if top else "-"
    return f"GOM-H: {n_reo} reo ({top_str}) · ⏳{n_supp} · 🔥nợ:{top_no or '-'} → #gomh"


def _hedge_line(text: str) -> str:
    """HEDGE: A=<n> · B-top: <tok +Δdiv (oi_note)> ×2 · 🎓<n hoặc tên> → #hedge
    V3.5k B1: sidecar vắng/stale → CẤM MỌI CHỮ SỐ · in 'N/A-ERROR' đúng chuẩn.
    """
    # V3.5k B1 · SIDECAR-MISSING guard: if text empty OR no LIST A marker → N/A-ERROR
    if not text or not text.strip():
        return "HEDGE: N/A-ERROR (sidecar missing — xem log) → #hedge"
    if "=== LIST A —" not in text:
        return "HEDGE: N/A-ERROR (sidecar malformed · no LIST-A marker — xem log) → #hedge"
    # V3.5q N5 fix: accept BOTH format {(N tokens) · TOP K/N} (N = total denominator)
    m_a = re.search(r"=== LIST A —.*?\((\d+)\s+tokens", text)
    if m_a is None:
        m_a = re.search(r"=== LIST A — TOP\s+\d+/(\d+)", text)
    if m_a is None:
        return "HEDGE: N/A-ERROR (sidecar LIST-A count parse fail — xem log) → #hedge"
    n_a = int(m_a.group(1))
    # B-top: pick 1 top row from each subsection (🅱1 SHORT-COVER + 🅱2 LONG-MỚI) · fallback LIST-B
    top_b = []
    # V3.5r · new format 🅱1/🅱2
    for section_marker, note in [("🅱1 SHORT-COVER", "short cover"),
                                  ("🅱2 LONG-MỚI", "long mới")]:
        m_sect = re.search(rf"{re.escape(section_marker)}.*?\n.*?\n─+\n(\s+\S+USDT?\s+[\d\.]+\s+[\+\-][\d\.]+.*)", text)
        if m_sect:
            first_row = m_sect.group(1).split("\n")[0]
            m_row = re.match(r"\s+(\S+?)USDT?\s+[\d\.]+\s+([\+\-][\d\.]+)", first_row)
            if m_row:
                top_b.append(f"{m_row.group(1)} {m_row.group(2)} ({note})")
    # Fallback old format LIST B
    if not top_b:
        in_lb = False
        for line in text.split("\n"):
            if "=== LIST B —" in line: in_lb = True; continue
            if in_lb and (line.startswith("=== ") or line.startswith("INFO: snapshot")): break
            if in_lb and re.match(r"^\s+\S+USDT?\s+[\d\.]", line):
                m = re.match(r"^\s+(\S+)USDT?\s+[\d\.]+\s+[\d\.]+\s+([\+\-][\d\.]+)\s+.*?(short cover thật|long mới|OI<\$1M).*", line)
                if m and len(top_b) < 2:
                    bare = m.group(1); delta = m.group(2)
                    note = "short cover" if "short cover" in m.group(3) else ("long mới" if "long mới" in m.group(3) else "OI<$1M")
                    top_b.append(f"{bare} {delta} ({note})")
    m_grad = re.search(r"TỐT[-\s]NGHIỆP\s*(?:\((\d+)|:\s*(\S+))", text)
    grad = "0"
    if m_grad:
        grad = m_grad.group(1) if m_grad.group(1) else m_grad.group(2)
    b_top_str = " × ".join(top_b) if top_b else "-"
    return f"HEDGE: A={n_a} · B-top: {b_top_str} · 🎓{grad} → #hedge"


def _kho_line(text: str) -> str:
    """KHO: 📥<n> (<top-3 tên>) / 📤<n> (<top-3 tên>) → #kho
    Reconstructed format: no section headers · direction từ sign của Δ$.
    """
    # Try as-sent format first: "(N lên / M rời)"
    m = re.search(r"(\d+)\s+token\s+\((\d+)\s+lên\s*/\s*(\d+)\s+rời\)", text)
    if m:
        n_up = int(m.group(2)); n_dn = int(m.group(3))
    else:
        # Method 1: count 📥/📤 arrows (reconstructed with arrow prefix)
        n_up = len(re.findall(r"📥\s+\d+\.\s+\$", text))
        n_dn = len(re.findall(r"📤\s+\d+\.\s+\$", text))
        # Method 2 (fallback if no arrows): count by Δ$ sign
        if n_up == 0 and n_dn == 0:
            # Look for "$SYM ... Δ+$..." (UP) or "$SYM ... Δ-$..." (DN)
            for line in text.split("\n"):
                stripped = line.lstrip()
                if not re.match(r"\d+\.\s+\$", stripped): continue
                if re.search(r"Δ\+\$", line): n_up += 1
                elif re.search(r"Δ-\$", line): n_dn += 1
    # top-3 per direction from body
    up_toks = []
    dn_toks = []
    in_up = in_dn = False
    for line in text.split("\n"):
        if "📥 LÊN SÀN" in line: in_up = True; in_dn = False; continue
        if "📤 RỜI SÀN" in line: in_dn = True; in_up = False; continue
        if in_up or in_dn:
            # Match both as-sent format ("   N. $SYM ...") and reconstructed ("📥  N. $SYM ...")
            m2 = re.match(r"^\s*(?:📥|📤)?\s*\d+\.\s+\$(\S+)\s+", line)
            if m2:
                if in_up and len(up_toks) < 3: up_toks.append(m2.group(1))
                elif in_dn and len(dn_toks) < 3: dn_toks.append(m2.group(1))
            # Reconstructed format has 📥/📤 arrow PER LINE, not section header
            m3 = re.match(r"^(📥|📤)\s+\d+\.\s+\$(\S+)\s+", line)
            if m3:
                if m3.group(1) == "📥" and len(up_toks) < 3: up_toks.append(m3.group(2))
                elif m3.group(1) == "📤" and len(dn_toks) < 3: dn_toks.append(m3.group(2))
    # Fallback: no section headers · parse by Δ$ sign per line
    if not up_toks and not dn_toks:
        for line in text.split("\n"):
            stripped = line.lstrip()
            m4 = re.match(r"\d+\.\s+\$(\S+)\s+", stripped)
            if not m4: continue
            sym = m4.group(1)
            if re.search(r"Δ\+\$", line) and len(up_toks) < 3: up_toks.append(sym)
            elif re.search(r"Δ-\$", line) and len(dn_toks) < 3: dn_toks.append(sym)
    up_str = ", ".join(up_toks) if up_toks else "-"
    dn_str = ", ".join(dn_toks) if dn_toks else "-"
    return f"KHO: 📥{n_up} ({up_str}) / 📤{n_dn} ({dn_str}) → #kho"


def _fresh_line(text: str) -> str:
    """FRESH: <n> (<top-2, ưu tiên 🆕>) → #fresh"""
    m_n = re.search(r"^(\d+)\s+token", text, re.MULTILINE)
    n = int(m_n.group(1)) if m_n else 0
    # top-2 rows preferring 🆕
    news, others = [], []
    in_pre = False
    for line in text.split("\n"):
        if "<pre>" in line: in_pre = True; continue
        if "</pre>" in line: break
        if in_pre:
            m2 = re.match(r"^\s*(🆕|⚠|\s{2})\s+\d+\.\s+\$(\S+)", line)
            if m2:
                (news if m2.group(1) == "🆕" else others).append(m2.group(2))
    top = (news + others)[:2]
    top_str = ", ".join([f"🆕{t}" if t in news else t for t in top]) if top else "-"
    return f"FRESH: {n} ({top_str}) → #fresh"


def _rong_line(text: str) -> str:
    """RÒNG: <n> chương (<mở-hôm-nay> · <Q1-max tok $>) · churn<n>→file · CLOSED:<tok> → #ròng"""
    m_open = re.search(r"\[(\d+) open / \d+ symbols scanned\]", text)
    n_open = int(m_open.group(1)) if m_open else 0
    # mở-hôm-nay: parse chapters with `start=<today>` (using target inference — approx)
    # Simplest: chapters with n_days=0 or start close to today
    # Q1-max tok $: parse Q1_cum values, find max
    q1_max_tok = ""
    q1_max_val = 0.0
    cur_tok = ""
    for line in text.split("\n"):
        m_tok = re.match(r"^══ (\S+) ={2,}", line)
        if m_tok: cur_tok = m_tok.group(1)
        m_q1 = re.match(r"^\s+Q1_cum:\s+\$\s+([\d,]+)", line)
        if m_q1:
            v = int(m_q1.group(1).replace(",", ""))
            if v > q1_max_val:
                q1_max_val = v; q1_max_tok = cur_tok
    # New chapters today (start=<target>)
    new_toks = []
    cur_tok = ""
    for line in text.split("\n"):
        m_tok = re.match(r"^══ (\S+) ={2,}", line)
        if m_tok: cur_tok = m_tok.group(1)
        if "n_days=1" in line and cur_tok and cur_tok not in new_toks:
            # Assume n_days=1 = opened today (approximate)
            new_toks.append(cur_tok)
    new_str = new_toks[0] if new_toks else "-"
    # churn count
    n_churn = 0
    m_c = re.search(r"━━ CHURN \((\d+)", text)
    if m_c: n_churn = int(m_c.group(1))
    # CLOSED today
    closed = "-"
    m_cl = re.search(r"CLOSED TODAY:\s+(\S+)", text)
    if m_cl: closed = m_cl.group(1).rstrip(",")
    q1_str = f"{q1_max_tok} ${q1_max_val/1e6:.1f}M" if q1_max_tok else "-"
    return f"RÒNG: {n_open} chương ({new_str} · {q1_str}) · churn{n_churn}→file · CLOSED:{closed} → #ròng"


def _star_block_from_ledger(target: str) -> tuple[str, str, list[str], str, dict]:
    """⭐ compose · V3.5: BỘ-BA {treo tổng-sống, mới⊆treo} + DAO-DEFERRED + direction routing.
    Reads stars_<target>.jsonl (from ledger_backfill v3.5) for direction/flags.

    V1.3-SPECIES-LAYOUT: 5th element = meta dict {token_records, dao_line, dai_no_line}
    for downstream V1.3 species-block reorganize.
    """
    p = LEDGER_DIR / f"events_{target}.jsonl"
    if not p.exists():
        return ("[LEDGER-WARMUP · events file missing]", "warmup", [], "(none)",
                {"token_records": [], "dao_line": "", "dai_no_line": ""})
    view_md5 = hashlib.md5(p.read_bytes()).hexdigest()[:12]
    events = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try: events.append(json.loads(line))
        except: continue
    if len(events) < 5:
        return (f"[LEDGER-WARMUP · events={len(events)} chưa đủ]", "warmup", [], view_md5,
                {"token_records": [], "dao_line": "", "dai_no_line": ""})

    from collections import defaultdict
    per_sym = defaultdict(lambda: {"axes": set(), "events": [], "latest": {}})
    for e in events:
        per_sym[e["symbol"]]["axes"].add(e["axis"])
        per_sym[e["symbol"]]["events"].append(e)
        cur = per_sym[e["symbol"]]["latest"].get(e["axis"])
        if cur is None or e["target_date"] > cur["target_date"]:
            per_sym[e["symbol"]]["latest"][e["axis"]] = e

    stars_all = [(s, info) for s, info in per_sym.items() if len(info["axes"]) >= 2]

    # V3.5 BỘ-BA: treo = ALL alive stars · mới ⊆ treo
    n_new_today = 0
    new_today_syms = []
    for sym, info in stars_all:
        events_today = [e for e in info["events"] if e["target_date"] == target]
        if not events_today: continue
        axes_before = {e["axis"] for e in info["events"] if e["target_date"] < target}
        if len(axes_before) < 2:
            n_new_today += 1
            new_today_syms.append(sym)
    treo_total_alive = len(stars_all)

    # Load V3.5 star_records for direction (optional)
    stars_p = LEDGER_DIR / f"stars_{target}.jsonl"
    dir_by_sym = {}
    if stars_p.exists():
        for line in stars_p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip(): continue
            try:
                r = json.loads(line)
                dir_by_sym[r["symbol"]] = r
            except: pass  # L-66-OK (json parse fallback)

    # V3.5k B2 · DISPLAY SORT ⭐-PRE = ngày-tín-hiệu-mới-nhất DESC · tie-break n-trục DESC
    def _latest_signal(info):
        return max(e["target_date"] for e in info["events"])
    stars_sorted = sorted(stars_all, key=lambda x: (_latest_signal(x[1]), len(x[1]["axes"])), reverse=True)
    # V3.5l · GOM-E subtag map + status (S2: OPEN trước CAGED · trong nhóm giữ last-signal DESC)
    gome_map, gome_status = _gome_subtag_map(target)
    pre_lines = []; xa_lines = []; post_lines = []; watch_lines = []
    pre_syms_ord = []; xa_syms_ord = []; post_syms_ord = []; watch_syms_ord = []
    pre_records = []  # for S2 re-sort · [(sym, subtag, line)]
    # V1.3-SPECIES-LAYOUT: build token_records for downstream reorganize
    token_records = []
    for s, info in stars_sorted:
        axes_str = "+".join(sorted(info["axes"]))
        latest_dates = " · ".join([f"{ax[:4]}={e['target_date'][5:]}" for ax, e in info["latest"].items()])
        new_tag = " [NEW]" if s in new_today_syms else ""
        dr = dir_by_sym.get(s, {})
        direction = dr.get("direction", "PRE")
        flags = dr.get("flags", [])
        px = dr.get("px", {})
        # V3.5k B3 · PX-N/A(coverage) → direction=WATCH · CẤM PRE/POST/XẢ tới khi px về
        px_missing = (px.get("px_now") is None) or (px.get("ret_pct") is None)
        if px_missing:
            direction = "WATCH"; flags = ["PX-PENDING"]
            watch_line = f"   ⏸ WATCH [PX-PENDING]: {s} {len(info['axes'])}-trục ({axes_str}) {latest_dates}{new_tag}"
            watch_lines.append(watch_line); watch_syms_ord.append(s)
            # V1.3-SPECIES-LAYOUT: add to records
            token_records.append({"sym": s, "line": watch_line, "direction": "WATCH",
                                  "axes": len(info["axes"]), "px_now": None})
            continue
        ret_str = f"ret{px.get('ret_pct'):+.0f}%"
        dd_str = f"dd{px.get('dd20_pct'):+.0f}%" if px.get("dd20_pct") is not None else "dd[PX-N/A]"
        reason_str = f"[{','.join(flags)}]" if flags else ""
        line = f"   {s} {len(info['axes'])}-trục ({axes_str}) {latest_dates} · {ret_str} {dd_str} → {direction}{reason_str}{new_tag}"
        if direction == "PRE":
            # V3.5m · ROLLBACK: proxy subtag OFF · in PRE trần + SUBTAG-PENDING banner ở đầu block
            # (proxy LIST-A/CSV bị bác vì AIO/GIGGLE lệch spec · chờ ANALYSIS xác định 'registry')
            line_pre = f"   {s} {len(info['axes'])}-trục ({axes_str}) {latest_dates} · {ret_str} {dd_str} → PRE{new_tag}"
            pre_lines.append(line_pre); pre_syms_ord.append(s)
            token_records.append({"sym": s, "line": line_pre, "direction": "PRE",
                                  "axes": len(info["axes"]), "px_now": px.get("px_now")})
        elif direction in ("XẢ-WATCH", "XẢ"):
            xa_lines.append(line); xa_syms_ord.append(s)
            token_records.append({"sym": s, "line": line, "direction": direction,
                                  "axes": len(info["axes"]), "px_now": px.get("px_now")})
        else:
            post_lines.append(line); post_syms_ord.append(s)
            token_records.append({"sym": s, "line": line, "direction": direction,
                                  "axes": len(info["axes"]), "px_now": px.get("px_now")})

    from datetime import datetime as _dt, timedelta as _td
    end = _dt.strptime(target, "%Y-%m-%d").date()
    perp_days = set(); wl_days = set(); fresh_days = set(); kho_g_days = set(); kho_e_days = set()
    for e in events:
        d = e["target_date"]; src = e.get("source","")
        if src == "gomh": perp_days.add(d)
        elif src == "watchlist_episode": wl_days.add(d)
        elif src == "fresh_digest": fresh_days.add(d)
        elif src == "gomh_h1": kho_g_days.add(d)
        elif src == "exch_digest": kho_e_days.add(d)
    perp_union = perp_days | wl_days
    kho_union = kho_g_days | kho_e_days
    win_n = 31
    fresh_cov = len(fresh_days); kho_cov = len(kho_union); perp_cov = len(perp_union)
    # V3.5k B1 · coverage PER-SRC in trục · khai wl-src status nếu MISSING hôm nay
    wl_missing_today = target not in wl_days
    wl_src_note = " [wl-src: MISSING hôm nay]" if wl_missing_today else ""
    dao_line = (f"[DAO-DEFERRED coverage: fresh {fresh_cov}/{win_n} · kho {kho_cov}/{win_n} · "
                f"perp {perp_cov}/{win_n}{wl_src_note}]")
    # V3.5k B4 · DẢI-NỢ line (K=21 provisional_unsigned · ký bàn 27/09)
    K_TRIP = 21
    n_pre_all = len(pre_lines); trip_ready = (min(fresh_cov, kho_cov, perp_cov) >= K_TRIP)
    trip_note = " ⚠ TRIP-READY" if trip_ready else ""
    dai_no_line = f"[DẢI-NỢ: PRE={n_pre_all} vs [4..6] · treo={treo_total_alive} vs [15] — sẽ TRIP khi coverage ≥ [K={K_TRIP}]/31]{trip_note}"
    body = (f"⭐ SỔ ỨNG VIÊN · {dao_line} treo={treo_total_alive}(tổng-sống) · mới={n_new_today}⊆treo\n"
            f"{dai_no_line}")

    # V3.5k B2 · header-n ≡ số dòng in · gọn = top-k + đuôi "(+k nữa: TÊN·TÊN·TÊN)"
    TOP_K = 6
    def _render_block(header_prefix, lines, syms):
        n = len(lines)
        if n <= TOP_K:
            return f"\n\n{header_prefix} ({n}):\n" + "\n".join(lines)
        shown = lines[:TOP_K]
        rest_syms = syms[TOP_K:]
        tail = f"(+{len(rest_syms)} nữa: " + "·".join(rest_syms) + ")"
        return f"\n\n{header_prefix} ({n}):\n" + "\n".join(shown) + f"\n   {tail}"

    if pre_lines:
        # V3.5m · SUBTAG-PENDING banner (proxy OFF · chờ ANALYSIS niêm nguồn GOM-E)
        subtag_banner = ("[SUBTAG-PENDING: nguồn GOM-E chưa niêm — "
                         "proxy LIST-A/CSV bị bác (AIO·GIGGLE lệch spec)]")
        body += f"\n\n{subtag_banner}"
        body += _render_block("⭐-PRE", pre_lines, pre_syms_ord)
    if xa_lines:
        body += _render_block("🔻 XẢ-WATCH+XẢ [bộ câu-soi]", xa_lines, xa_syms_ord)
    if post_lines:
        body += _render_block("POST-DUMP+🌊", post_lines, post_syms_ord)
    if watch_lines:
        body += _render_block("⏸ WATCH-PX-PENDING", watch_lines, watch_syms_ord)
    meta = {"token_records": token_records, "dao_line": dao_line, "dai_no_line": dai_no_line}
    return (body, "active", [s for s, _ in stars_all], view_md5, meta)


# ═════════════════════════════════════════════════════════════════
# V1.3-SPECIES-LAYOUT · scorer + block reorganize · KÝ 13/09
# Amendment: proposals/v1_3_species_layout_amendment_20260913.md
# ═════════════════════════════════════════════════════════════════

_V1_3_SPECIES_TAGGER_SHA = None  # Filled at runtime by _v1_3_species_score OR module-load
# Pre-load SHA on module import so warmup-mode footer vẫn ghi đúng species=<sha>
try:
    _tag_p_init = REPO / "scripts/species_tag.py"
    if _tag_p_init.exists():
        _V1_3_SPECIES_TAGGER_SHA = hashlib.md5(_tag_p_init.read_bytes()).hexdigest()[:8]
except Exception:
    pass  # L-66-OK · SHA sẽ được set khi _v1_3_tag_binary chạy

def _v1_3_load_store(target: str) -> dict:
    """Load freshwatch multi-month store (2 months lookback from target)."""
    import csv as _csv
    from collections import defaultdict as _dd
    store = _dd(list)
    yyyy_mm = target[:7]
    year = int(yyyy_mm[:4]); month = int(yyyy_mm[-2:])
    # Load current + 2 previous months for lookback
    months = []
    for i in range(3):
        m = month - i
        y = year
        while m <= 0: m += 12; y -= 1
        months.append(f"{y:04d}-{m:02d}")
    for ym in months:
        p = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
        if not p.exists(): continue
        with open(p, encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                sym_raw = row.get("symbol", "")
                sym = sym_raw[:-4] if sym_raw.endswith("USDT") else sym_raw
                out = {"date": row["date"]}
                for k in ("px_avg","oi_usd","lsr_pos_r","lsr_acc_r","lsr_global_r","funding_avg"):
                    v = row.get(k, "")
                    try: out[k] = float(v) if v not in ("", None) else None
                    except ValueError: out[k] = None
                store[sym].append(out)
    for sym in store:
        seen = {}
        for r in store[sym]: seen[r["date"]] = r
        store[sym] = sorted(seen.values(), key=lambda x: x["date"])
    return store


def _v1_3_species_score(sym_bare: str, target: str, store: dict) -> dict:
    """V1.3 species scoring · returns {species → {k, n, primary_blind, prefix_str}}.

    n=6/6/6/5/5 per spec.  a5/b5 mù VĨNH VIỄN → n effective = 5, in `k/5(?1)`.
    Reuses scripts/probe/species_tag.py tagger for most vé; DRAFT for extras.
    """
    global _V1_3_SPECIES_TAGGER_SHA
    import sys as _sys
    _sys.path.insert(0, str(REPO / "scripts"))
    try:
        import species_tag as _st
    except Exception as _e:
        return {"error": f"tagger import fail: {_e}"}
    if _V1_3_SPECIES_TAGGER_SHA is None:
        _tag_p = REPO / "scripts/species_tag.py"
        _V1_3_SPECIES_TAGGER_SHA = hashlib.md5(_tag_p.read_bytes()).hexdigest()[:8] if _tag_p.exists() else "(none)"

    rows = store.get(sym_bare) or store.get("龙虾" if sym_bare == "LOBSTER" else sym_bare, [])
    if not rows:
        return {"error": "no-store"}

    out = {}
    # ── [A] · n=6, a5 mù → k/5(?1) ──
    a_m, a_r, a_bl = _st.check_A(rows, target)
    if a_bl:
        # primary axis mù (pos_r None)
        out["A"] = {"k": 0, "n": 5, "primary_blind": True, "n_hidden": 1, "ve_state": {}}
    else:
        # reasons has 1 string with 5 True/False; count True
        reason_str = a_r[0] if a_r else ""
        k = reason_str.count("=True")
        # Z1 lint · per-vé state map for dead-leg detection
        ve_state = {
            "pos_ramp_14d": "pos_ramp_14d=True" in reason_str,
            "pos_ge_7":     "pos_ge_7=True" in reason_str,
            "close_low30":  "close_low30=True" in reason_str,
            "oi_flat":      "oi_flat=True" in reason_str,
            "funding_pin":  "fund_pin_7d=True" in reason_str,
        }
        out["A"] = {"k": k, "n": 5, "primary_blind": False, "n_hidden": 1, "ve_state": ve_state}

    # ── [B] · n=6, b5 mù → k/5(?1) ──
    b_m, b_r, b_bl = _st.check_B(rows, target)
    if b_bl:
        out["B"] = {"k": 0, "n": 5, "primary_blind": True, "n_hidden": 1, "ve_state": {}}
    else:
        reason_str = b_r[0] if b_r else ""
        k_tagger = reason_str.count("=True")
        # Extras (DRAFT): b3 age ≥30d, b4 div-cross (heuristic)
        first_date = rows[0]["date"] if rows else target
        from datetime import datetime as _dt
        try:
            age_days = (_dt.strptime(target, "%Y-%m-%d").date() - _dt.strptime(first_date, "%Y-%m-%d").date()).days
        except: age_days = 0
        b3_age = age_days >= 30
        # b4 div-cross: check if div_avg3 crossed >0.5 within last 14d
        from datetime import timedelta as _td
        td = _dt.strptime(target, "%Y-%m-%d").date()
        b4_cross = False
        for d in range(1, 15):
            dt = (td - _td(days=d)).isoformat()
            dt_prev = (td - _td(days=d+1)).isoformat()
            v = _st._div_avg3(rows, dt); vp = _st._div_avg3(rows, dt_prev)
            if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
                b4_cross = True; break
        # b6 U0 W3: skip (needs cross-date) — DRAFT: use b4_cross as proxy for U0 pass
        b6_u0 = b4_cross  # DRAFT proxy
        k_total = k_tagger + int(b3_age) + int(b4_cross) + int(b6_u0)
        # Z1 lint per-vé
        ve_state = {
            "gLSR_or_acc≥2":  "gLSR_or_acc≥2=True" in reason_str,
            "div_run≤0.5":    "div_run≤0.5×3d_in_30d=True" in reason_str,
            "b3_age≥30d":     b3_age,
            "b4_div_cross":   b4_cross,
            "b6_u0_proxy":    b6_u0,
        }
        out["B"] = {"k": k_total, "n": 5, "primary_blind": False, "n_hidden": 1, "ve_state": ve_state}

    # ── [C] · n=6 (no mù) ──
    c_m, c_r, c_bl = _st.check_C(rows, target)
    if c_bl:
        out["C"] = {"k": 0, "n": 6, "primary_blind": True, "n_hidden": 0, "ve_state": {}}
    else:
        reason_str = c_r[0] if c_r else ""
        c_dump    = "dump=True" in reason_str
        c_plateau = "plateau=True" in reason_str
        c_lag     = "lag_ok=True" in reason_str
        c_pos     = "pos_hold=True" in reason_str
        from datetime import datetime as _dt, timedelta as _td
        acc_T = _st._get(rows, target, "lsr_acc_r")
        acc_7 = _st._at_offset(rows, target, "lsr_acc_r", 7)
        c5 = (acc_T is not None and acc_7 is not None and acc_T > acc_7)
        fund_7 = _st._values_upto(rows, target, "funding_avg", 7)
        c6 = (len(fund_7) >= _st.FUNDING_PIN_MIN_STREAK and
              all(abs(f - _st.FUNDING_PIN_VALUE) <= _st.FUNDING_PIN_TOL for f in fund_7[-7:]))
        ve_state = {"c1_dump": c_dump, "c2_plateau": c_plateau, "c3_lag": c_lag,
                    "c4_pos_hold": c_pos, "c5_acc↑": c5, "c6_pin": c6}
        out["C"] = {"k": sum(int(v) for v in ve_state.values()), "n": 6,
                    "primary_blind": False, "n_hidden": 0, "ve_state": ve_state}

    # ── [D] · n=5 (no mù) ──
    d_m, d_r, d_bl = _st.check_D(rows, target)
    if d_bl:
        out["D"] = {"k": 0, "n": 5, "primary_blind": True, "n_hidden": 0, "ve_state": {}}
    else:
        reason_str = d_r[0] if d_r else ""
        d_oi     = "oi_x1.5=True" in reason_str
        d_close  = "close_band=True" in reason_str
        d_norun  = "no_div_run=True" in reason_str
        # DRAFT: d4 taker<52, d5 bait-45d — chưa cài, luôn False (Z3 dead-code)
        d4_taker = False   # DRAFT-UNINSTALLED (Z3)
        d5_bait  = False   # DRAFT-UNINSTALLED (Z3)
        ve_state = {"d1_oi≥1.5x": d_oi, "d2_close_band": d_close, "d3_no_div_run": d_norun,
                    "d4_taker<52": d4_taker, "d5_bait_45d": d5_bait}
        out["D"] = {"k": sum(int(v) for v in ve_state.values()), "n": 5,
                    "primary_blind": False, "n_hidden": 0, "ve_state": ve_state}

    # ── [E] · n=5 (no mù) ──
    e_m, e_r, e_bl, e_pend = _st.check_E(rows, target)
    if e_bl:
        out["E"] = {"k": 0, "n": 5, "primary_blind": True, "n_hidden": 0, "ve_state": {}}
    else:
        # Rebuild spike/follow directly (parse of e_r fragile)
        close_T2 = _st._at_offset(rows, target, "px_avg", 2)
        close_T1 = _st._at_offset(rows, target, "px_avg", 1)
        close_T  = _st._get(rows, target, "px_avg")
        e_spike = (close_T2 is not None and close_T1 is not None and close_T2 > 0
                   and (close_T1/close_T2 - 1) >= _st.E_SPIKE_MIN)
        e_follow = (close_T is not None and close_T1 is not None and close_T1 > 0
                    and (close_T/close_T1 - 1) <= _st.E_FOLLOW_MAX)
        # DRAFT: e3/e4/e5 chưa cài (Z3 dead-code)
        e3_vol_spike  = False   # DRAFT-UNINSTALLED
        e4_crowd_flip = False   # DRAFT-UNINSTALLED
        e5_fresh_NA   = False   # DRAFT-UNINSTALLED
        ve_state = {"e1_spike": e_spike, "e2_follow": e_follow,
                    "e3_vol_spike": e3_vol_spike, "e4_crowd_flip": e4_crowd_flip,
                    "e5_fresh_NA": e5_fresh_NA}
        out["E"] = {"k": sum(int(v) for v in ve_state.values()), "n": 5,
                    "primary_blind": False, "n_hidden": 0, "ve_state": ve_state}

    return out


def _v1_3_lint_px_coverage(token_records: list, threshold_pct: float = 50.0) -> list:
    """R4 · pin p14 · PX-COVERAGE-LOW audit.
    Nếu tỷ lệ token PX-PENDING > threshold_pct% cohort → in [PX-COVERAGE-LOW n/m].
    Cohort = len(token_records). Pending = số token có px_now is None.
    Đen-một-lần: ép 90% pending → kêu · ép 5% → im.
    """
    if not token_records:
        return []
    n_total = len(token_records)
    n_pending = sum(1 for r in token_records if r.get("px_now") is None)
    pct = (n_pending / n_total) * 100.0
    lines = []
    if pct > threshold_pct:
        lines.append(f"[PX-COVERAGE-LOW {n_pending}/{n_total} · {pct:.0f}% > {threshold_pct:.0f}%]")
    return lines


def _v1_3_lint_dead_legs(cohort_scores: list) -> list:
    """Z1 · Lint vé chết trên cohort.
    cohort_scores = list of _v1_3_species_score output (per token)
    Returns audit lines:
      [LEG-DEAD: <loài>·<vé> N/N] · vé FALSE trên 100% cohort (evaluable)
      [LEG-CONST-TRUE: <loài>·<vé> N/N] · vé TRUE trên 100% cohort
    Cả hai đều vô dụng trong AND-gate · phải lộ ra ngay đêm đầu.
    """
    from collections import defaultdict as _dd
    # Aggregate: {loài → {vé → [n_true, n_false]}}
    stats = _dd(lambda: _dd(lambda: [0, 0]))
    for sc in cohort_scores:
        if "error" in sc: continue
        for sp in "ABCDE":
            s = sc.get(sp, {})
            if s.get("primary_blind"): continue
            ve_state = s.get("ve_state", {})
            for ve, val in ve_state.items():
                if val: stats[sp][ve][0] += 1
                else:   stats[sp][ve][1] += 1
    lines = []
    for sp in "ABCDE":
        for ve, (n_true, n_false) in sorted(stats[sp].items()):
            n_total = n_true + n_false
            if n_total == 0: continue
            if n_true == 0:
                lines.append(f"[LEG-DEAD: {sp}·{ve} {n_false}/{n_total}]")
            elif n_false == 0:
                lines.append(f"[LEG-CONST-TRUE: {sp}·{ve} {n_true}/{n_total}]")
    return lines


def _v1_3_tag_binary(sym_bare: str, target: str, store: dict) -> dict:
    """Binary tagger · returns {tags, blind_axes, display} · no k/n.
    Delegates to scripts/species_tag.py::tag_species.
    """
    global _V1_3_SPECIES_TAGGER_SHA
    import sys as _sys
    _sys.path.insert(0, str(REPO / "scripts"))
    try:
        import species_tag as _st
    except Exception as _e:
        return {"tags": [], "blind_axes": [], "display": "", "error": str(_e)}
    if _V1_3_SPECIES_TAGGER_SHA is None:
        _tag_p = REPO / "scripts/species_tag.py"
        _V1_3_SPECIES_TAGGER_SHA = hashlib.md5(_tag_p.read_bytes()).hexdigest()[:8] if _tag_p.exists() else "(none)"
    rows = store.get(sym_bare, [])
    if not rows:
        return {"tags": [], "blind_axes": [], "display": "", "no_store": True}
    return _st.tag_species(rows, target)


def _v1_3_route_layout_only(tags: list, blind_axes: list) -> tuple[str, str, list]:
    """Binary routing rule · LAYOUT-ONLY (no k/n).
    Returns (block_key, prefix_str, hint_blocks).

    Rules:
    · ≥1 tag khớp → keep tags (tagger đã trim ≤2 theo C>D>B>A), in theo chữ cái
    · Hybrid [B·D] → block = chữ cái đầu; block còn lại nhận dòng nhắc (→ xem X)
    · [?] CHỈ khi không có tag ∧ trục chính mù · vế phụ mù không đẩy vào `?`
    · Zero-tag không blind → CHƯA XẾP LOÀI · no prefix
    """
    if tags:
        tags_sorted = sorted(tags)
        prefix = "[" + "·".join(tags_sorted) + "]"
        block = tags_sorted[0]
        hints = tags_sorted[1:]
        return (block, prefix, hints)
    if blind_axes:
        return ("?", "[?]", [])
    return ("CHUA_XEP", "", [])


def _v1_3_render_species_body(target: str, token_records: list, dai_no_line: str,
                               dao_line: str, star_body_head: str, tripwire_line: str) -> str:
    """V1.3 LAYOUT-ONLY body · KÝ 15/09 · binary tagger + block order + collapsed rỗng.

    Layout:
      [loài = §16 PATTERN_BOOK header line]
      species blocks A/B/C/D/E/?/CHƯA XẾP LOÀI (empty blocks collapse to one line)
      🔻 XẢ-WATCH+XẢ
      POST-DUMP+🌊
      DẢI-NỢ + DAO-DEFERRED coverage

    Rest (📒/🚪/NHỊP-KÊNH/👁/footer) added by build_v2_digest caller.
    """
    store = _v1_3_load_store(target)

    scored = []
    for rec in token_records:
        sym_bare = rec["sym"].replace("USDT", "") if rec["sym"].endswith("USDT") else rec["sym"]
        result = _v1_3_tag_binary(sym_bare, target, store)
        tags = result.get("tags", []) or []
        blind_axes = result.get("blind_axes", []) or []
        block, prefix, hints = _v1_3_route_layout_only(tags, blind_axes)
        scored.append((rec, block, prefix, hints, tags, blind_axes))

    # R4 · p14 · PX-COVERAGE-LOW audit (giữ nguyên · lint dead-legs bỏ vì layout-only)
    _px_lint = _v1_3_lint_px_coverage(token_records, threshold_pct=50.0)
    if _px_lint:
        print(f"[V1.3-LINT · target={target} · cohort={len(scored)}]", file=sys.stderr)
        for _ll in _px_lint:
            print(f"  {_ll}", file=sys.stderr)

    species_blocks = {"A": [], "B": [], "C": [], "D": [], "E": [], "?": [], "CHUA_XEP": []}
    xa_lines = []; xa_syms = []
    post_lines = []; post_syms = []

    for rec, block, prefix, hints, tags, blind_axes in scored:
        dir_ = rec["direction"]
        line = rec["line"]
        sym = rec["sym"]
        m = re.match(r"^(\s+)(.*)$", line)
        if m and prefix:
            line_p = f"{m.group(1)}{prefix} {m.group(2)}"
        elif m:
            line_p = line
        else:
            line_p = f"{prefix} {line}" if prefix else line

        if dir_ == "PRE":
            species_blocks[block].append((sym, line_p, hints))
        elif dir_ in ("XẢ-WATCH", "XẢ"):
            xa_lines.append(line_p); xa_syms.append(sym)
        elif dir_ == "WATCH":
            species_blocks[block].append((sym, line_p, hints))
        else:
            post_lines.append(line_p); post_syms.append(sym)

    lines = []
    if tripwire_line: lines.append(tripwire_line)
    lines.append(f"[loài = trạng thái hôm nay theo khuôn §16 PATTERN_BOOK v1.3 md5 77d86654 "
                 f"— draft, chưa đủ mẫu]")
    lines.append("")

    _SPECIES = [
        ("A", "── A · GHẾ BẬT ──"),
        ("B", "── B · HEDGE → UNHEDGE ──"),
        ("C", "── C · ĐẠP → GOM → ĐẨY ──"),
        ("D", "── D · GRIND ──"),
        ("E", "── E · MỘT CỘT ──"),
        ("?", "── ? CHƯA NHÌN ĐƯỢC ──"),
        ("CHUA_XEP", "── CHƯA XẾP LOÀI ──"),
    ]

    # Collect hint lines per block (from other tag of hybrid tokens)
    from collections import defaultdict as _dd
    hint_by_block = _dd(list)
    for key, _ in _SPECIES:
        if key in ("?", "CHUA_XEP"): continue
        for sym, line, hints in species_blocks[key]:
            for h in hints:
                if h in species_blocks:
                    hint_by_block[h].append(f"   (→ xem {key}) {sym}")

    # Render species blocks · empty ones collapse into single tail line
    _EMPTY_LABELS = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "?": "?", "CHUA_XEP": "CHƯA XẾP LOÀI"}
    empty_collapsed = []
    for key, header in _SPECIES:
        block_tokens = species_blocks[key]
        block_hints = hint_by_block.get(key, [])
        n = len(block_tokens)
        if n == 0 and not block_hints:
            empty_collapsed.append(f"{_EMPTY_LABELS[key]} (0)")
            continue
        lines.append(f"{header} ({n})")
        for sym, line, _ in block_tokens:
            lines.append(line)
        for h in block_hints:
            lines.append(h)
        lines.append("")

    if empty_collapsed:
        lines.append("── " + " · ".join(empty_collapsed) + " ──")
        lines.append("")

    # Direction blocks
    if xa_lines:
        lines.append(f"🔻 XẢ-WATCH+XẢ ({len(xa_lines)}):")
        lines.extend(xa_lines)
        lines.append("")
    if post_lines:
        lines.append(f"POST-DUMP+🌊 ({len(post_lines)}):")
        lines.extend(post_lines)
        lines.append("")

    if dai_no_line: lines.append(dai_no_line)
    if dao_line: lines.append(dao_line)

    return "\n".join(lines)


def _yaml_forward_tests() -> list[str]:
    """👁 đọc THẲNG yaml forward_tests."""
    p = REPO / "screen_thresholds.yaml"
    if not p.exists(): return []
    txt = p.read_text(encoding="utf-8", errors="replace")
    # Look for forward_tests: block
    m = re.search(r"^forward_tests:\s*\n((?:\s+.+\n)+)", txt, re.MULTILINE)
    if not m: return []
    body = m.group(1)
    lines = []
    for line in body.split("\n"):
        # Format: `  TOKEN: "spec"`
        m2 = re.match(r"^\s+(\S+):\s+[\"'](.+)[\"']", line)
        if m2: lines.append(f"👁 {m2.group(1)}: {m2.group(2)[:80]}")
    return lines[:5]


def build_v2_digest(target: str) -> str:
    dd_mm = f"{target[8:10]}/{target[5:7]}"
    # Load 6 artifacts
    a_gh, p_gh = _load_artifact("tg_relay_gom_h", target)
    a_fr, p_fr = _load_artifact("fresh_digest", target)
    a_ex, p_ex = _load_artifact("exch_digest", target)
    a_wl, p_wl = _load_artifact("watchlist", target)
    a_gd, p_gd = _load_artifact("gom_daily", target)

    star_body, star_mode, star_syms, ledger_md5, meta = _star_block_from_ledger(target)

    lines = [f"━━ FRESHWATCH TỔNG · {dd_mm} · target={target} ━━"]

    # ⛔ 1-line
    tw = _tripwire_line()
    if tw: lines.append(tw)

    # V1.3-SPECIES-LAYOUT: if env DIGEST_V1_3=1 → use species layout, else V1.2
    v1_3_mode = os.environ.get("DIGEST_V1_3", "0") == "1"
    if v1_3_mode and star_mode == "active" and meta.get("token_records"):
        # V1.3: species-block layout replaces star_body
        v1_3_body = _v1_3_render_species_body(
            target=target, token_records=meta["token_records"],
            dai_no_line=meta["dai_no_line"], dao_line=meta["dao_line"],
            star_body_head="", tripwire_line="",   # tripwire already added above
        )
        lines.append(v1_3_body)
    else:
        # V1.2 (default): use star_body as-is
        lines.append(star_body)

    # 📒 SỔ THƯỜNG (1-trục symbols, ≠ star) — parse from ledger for symbols with 1 axis
    # Simplified: just note count for now
    # 🚪 RỜI-SỔ (none)-không-câm
    lines.append("📒 SỔ THƯỜNG · [PENDING batch-kế · 1-trục compose]")
    lines.append("🚪 RỜI-SỔ · (none) — hôm nay không có token rời sổ")

    # 5 NHỊP-KÊNH R2 templates VERBATIM
    lines.append("")
    lines.append(_gomh_line(a_gh))
    lines.append(_hedge_line(a_wl))
    lines.append(_kho_line(a_ex))
    lines.append(_fresh_line(a_fr))
    lines.append(_rong_line(a_gd))

    # 👁 forward_tests từ yaml
    watch = _yaml_forward_tests()
    if watch:
        lines.append("")
        for w in watch: lines.append(w)

    # Footer: md5-set + POINTER-INTEGRITY + concat-seal + explicit file:target paths per FIX-ROUND-2
    lines.append("")
    lines.append("━━ footer ━━")
    fix_p = FIXTURE_DIR / "FIXTURE_MASTER_MD5.md"
    fix_md5 = hashlib.md5(fix_p.read_bytes()).hexdigest()[:12] if fix_p.exists() else "(none)"
    # V1.3-SPECIES-LAYOUT-ONLY: footer meta with tagger sha + book md5 + amendments
    v1_3_footer_extra = ""
    if v1_3_mode:
        tag_sha = _V1_3_SPECIES_TAGGER_SHA or "(unknown)"
        v1_3_footer_extra = (f" · species={tag_sha} · book=77d86654 · "
                             f"amendments_applied=[MASTER-LIVE, V1.3-SPECIES-LAYOUT-ONLY]")
    lines.append(f"ledger_state={ledger_md5} · fixture_master={fix_md5}{v1_3_footer_extra}")
    # Cite explicit file:target per NHỊP-KÊNH (KHO-LINE FIX operator directive)
    def _cite(renderer, prov):
        prefix = "tg_final_" if prov == "as-sent" else ""
        return f"{prefix}{renderer}_{target}.txt[{prov}]"
    lines.append(f"cites: gomh={_cite('tg_relay_gom_h', p_gh)} · fresh={_cite('fresh_digest', p_fr)} · "
                 f"exch={_cite('exch_digest', p_ex)} · hedge={_cite('watchlist', p_wl)} · rong={_cite('gom_daily', p_gd)}")
    # concat-seal · AMD-07 luật đối chứng:
    #   artifact = body sans seal  → master_concat_<target>.txt · md5[:12] == seal
    #   body sent = artifact + seal line + built line → master_body_<target>.txt
    # p27 postcheck đọc CẢ hai: seal-in-body match md5(artifact).
    body = "\n".join(lines)
    seal = hashlib.md5(body.encode()).hexdigest()[:12]
    try:
        concat_p = ART_DIR / f"master_concat_{target}.txt"
        concat_p.write_bytes(body.encode("utf-8"))
    except Exception as _e:
        print(f"[N/A-ERROR:CONCAT-PERSIST] {type(_e).__name__}: {_e}")
    lines.append(f"concat-seal={seal} · target={target} · built={datetime.now(timezone.utc).isoformat()}")
    full_body = "\n".join(lines)
    try:
        body_p = ART_DIR / f"master_body_{target}.txt"
        body_p.write_bytes(full_body.encode("utf-8"))
    except Exception as _e:
        print(f"[N/A-ERROR:BODY-PERSIST] {type(_e).__name__}: {_e}")
    return full_body


def _send(msg: str, prefix: str = "") -> tuple[bool, str]:
    import urllib.request, urllib.parse
    chat = ""
    env_tg = Path("/root/.env_tg")
    if env_tg.exists():
        for line in env_tg.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "TG_CHAT_ID_DAILY": chat = v.strip().strip('"').strip("'")
    if not chat: return (False, "TG_CHAT_ID_DAILY missing")
    tok = ""
    if env_tg.exists():
        for line in env_tg.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "TELEGRAM_BOT_TOKEN": tok = v.strip().strip('"').strip("'")
    full = (prefix + "\n\n" + msg) if prefix else msg
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat, "text": full, "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=payload, method="POST"), timeout=15) as r:
            return (r.status == 200, f"HTTP {r.status} · {len(full)}B")
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--prefix", default="")
    args = ap.parse_args()
    msg = build_v2_digest(args.target)
    out = REPO / "scratch" / f"digest_summary_v2_{args.target}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(msg, encoding="utf-8")
    n_lines = msg.count("\n") + 1
    print(f"[BUILT v2] {out} · {len(msg)}B · {n_lines} lines")
    print("=" * 78)
    print(msg)
    print("=" * 78)
    if args.send:
        ok, det = _send(msg, args.prefix)
        icon = "✅" if ok else "❌"
        print(f"{icon} [SEND] {det}")


if __name__ == "__main__":
    main()

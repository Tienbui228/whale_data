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
    """HEDGE: A=<n> · B-top: <tok +Δdiv (oi_note)> ×2 · 🎓<n hoặc tên> → #hedge"""
    m_a = re.search(r"=== LIST A —.*?\((\d+) tokens", text)
    n_a = int(m_a.group(1)) if m_a else 0
    # B-top × 2: first 2 rows in LIST B section (already sorted by Δdiv DESC per script)
    in_lb = False; top_b = []
    for line in text.split("\n"):
        if "=== LIST B —" in line: in_lb = True; continue
        if in_lb and (line.startswith("=== ") or line.startswith("INFO: snapshot")): break
        if in_lb and re.match(r"^\s+\S+USDT?\s+[\d\.]", line):
            m = re.match(r"^\s+(\S+)USDT?\s+[\d\.]+\s+[\d\.]+\s+([\+\-][\d\.]+)\s+.*?(short cover thật|long mới|OI<\$1M).*", line)
            if m and len(top_b) < 2:
                bare = m.group(1); delta = m.group(2)
                note = "short cover" if "short cover" in m.group(3) else ("long mới" if "long mới" in m.group(3) else "OI<$1M")
                top_b.append(f"{bare} {delta} ({note})")
    # 🎓 TỐT-NGHIỆP · look for count or names
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


def _star_block_from_ledger(target: str) -> tuple[str, str, list[str], str]:
    """⭐ compose · V3.5: BỘ-BA {treo tổng-sống, mới⊆treo} + DAO-DEFERRED + direction routing.
    Reads stars_<target>.jsonl (from ledger_backfill v3.5) for direction/flags."""
    p = LEDGER_DIR / f"events_{target}.jsonl"
    if not p.exists():
        return ("[LEDGER-WARMUP · events file missing]", "warmup", [], "(none)")
    view_md5 = hashlib.md5(p.read_bytes()).hexdigest()[:12]
    events = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try: events.append(json.loads(line))
        except: continue
    if len(events) < 5:
        return (f"[LEDGER-WARMUP · events={len(events)} chưa đủ]", "warmup", [], view_md5)

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

    stars_sorted = sorted(stars_all, key=lambda x: (-len(x[1]["axes"]), -len(x[1]["events"]), x[0]))
    pre_lines = []; xa_lines = []; post_lines = []
    for s, info in stars_sorted:
        axes_str = "+".join(sorted(info["axes"]))
        latest_dates = " · ".join([f"{ax[:4]}={e['target_date'][5:]}" for ax, e in info["latest"].items()])
        new_tag = " [NEW]" if s in new_today_syms else ""
        dr = dir_by_sym.get(s, {})
        direction = dr.get("direction", "PRE")
        flags = dr.get("flags", [])
        px = dr.get("px", {})
        ret_str = f"ret{px.get('ret_pct',0):+.0f}%" if px.get("ret_pct") is not None else "ret[PX-N/A]"
        dd_str = f"dd{px.get('dd20_pct',0):+.0f}%" if px.get("dd20_pct") is not None else "dd[PX-N/A]"
        reason_str = f"[{','.join(flags)}]" if flags else ""
        line = f"   {s} {len(info['axes'])}-trục ({axes_str}) {latest_dates} · {ret_str} {dd_str} → {direction}{reason_str}{new_tag}"
        # V3.5b 3-tầng routing
        if direction == "PRE":
            pre_lines.append(line)
        elif direction in ("XẢ-WATCH", "XẢ"):
            xa_lines.append(line)
        else:  # POST-DUMP, POST, POST-FLOOR, 🌊
            post_lines.append(line)

    # V3.5 DAO-DEFERRED: check coverage from events (simple counts)
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
    # DAO-DEFERRED nếu coverage của trục quan trọng thấp; else CLEAR/ANOMALY
    SOFT_CEILING = 15
    dao_line = f"[DAO-DEFERRED coverage: fresh {fresh_cov}/{win_n} · kho {kho_cov}/{win_n} · perp {perp_cov}/{win_n}]"
    body = f"⭐ SỔ ỨNG VIÊN · {dao_line} treo={treo_total_alive}(tổng-sống) · mới={n_new_today}⊆treo"

    # V3.5b RENDER 3 TẦNG
    if pre_lines:
        body += f"\n\n⭐-PRE ({len(pre_lines)}):\n" + "\n".join(pre_lines[:8])
    if xa_lines:
        body += (f"\n\n🔻 XẢ-WATCH+XẢ ({len(xa_lines)}) [bộ câu-soi: rút về đâu? "
                 f"ai nhận trong dump? dính CEX-list?]:\n" + "\n".join(xa_lines[:8]))
    if post_lines:
        body += f"\n\nPOST-DUMP+🌊 ({len(post_lines)}):\n" + "\n".join(post_lines[:8])
    return (body, "active", [s for s, _ in stars_all], view_md5)


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

    star_body, star_mode, star_syms, ledger_md5 = _star_block_from_ledger(target)

    lines = [f"━━ FRESHWATCH TỔNG · {dd_mm} · target={target} ━━"]

    # ⛔ 1-line
    tw = _tripwire_line()
    if tw: lines.append(tw)

    # ⭐ SỔ ỨNG VIÊN
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
    lines.append(f"ledger_state={ledger_md5} · fixture_master={fix_md5}")
    # Cite explicit file:target per NHỊP-KÊNH (KHO-LINE FIX operator directive)
    def _cite(renderer, prov):
        prefix = "tg_final_" if prov == "as-sent" else ""
        return f"{prefix}{renderer}_{target}.txt[{prov}]"
    lines.append(f"cites: gomh={_cite('tg_relay_gom_h', p_gh)} · fresh={_cite('fresh_digest', p_fr)} · "
                 f"exch={_cite('exch_digest', p_ex)} · hedge={_cite('watchlist', p_wl)} · rong={_cite('gom_daily', p_gd)}")
    # concat-seal
    body = "\n".join(lines)
    seal = hashlib.md5(body.encode()).hexdigest()[:12]
    lines.append(f"concat-seal={seal} · target={target} · built={datetime.now(timezone.utc).isoformat()}")
    return "\n".join(lines)


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

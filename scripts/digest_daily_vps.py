"""P1 · digest_daily_vps.py · VPS-NATIVE · KÝ 01/09 · PARITY-FIX 02/09

Render + send 2 digests {Fresh-Wallets · EXCH-BAL} từ Nansen snapshot đã sync sang VPS.
Zero-Nansen-call (P2 riêng · caller Windows sinh snapshot · sync task đưa VPS).

RENDER FORMAT · KÝ 02/09 (PARITY-AUDIT · golden-master = Windows alerts.py):
  · Port verbatim Windows alerts.send_digest + send_exchange_digest (bless bảng
    deviation_table_20260902.md · L-77 PORT-PARITY discipline)
  · parse_mode=HTML + <pre> monospace (Telegram render fixed-width font)
  · html.escape() MỌI field động (symbol/label/note) — guard bất-biến
  · S6-digest (plain-text) SUPERSEDED · GOM-H tg_relay giữ plain (chữ ký sống nhà nó)

Cron interim: 25 1 * * * cd /root/... && .venv/bin/python3 scripts/digest_daily_vps.py

SIGNED-DEVIATIONS giữ (không thuộc verbatim Windows):
  · S1 · Fresh Δ = snapshot-pair 2d thay state-file delta_hours (bless 01/09)
  · S2 · stale/gap-note split · gap-note per-tin (Fresh: snapshot-pair · EXCH-BAL: Nansen-window)
  · S3 · UX 0-token first-line
  · S4 · SINGLE-SENDER VPS-NATIVE
  · S5 · [TEST]/[CATCH-UP] prefix
  (S6 plain-text digest RETIRED · GOM-H giữ)

Guards (họ TgRelayGomH):
  · html.escape all dynamic fields
  · staleness detect: snapshot mtime > 25h → stale_note
  · snapshot MISSING → skeleton stale
  · raw-save response L-59 · idempotent-hash · env /root/.env_tg (chmod 600)
  · [TEST-DIGEST] prefix qua --test flag (no idempotent · rõ prefix)
"""
from __future__ import annotations
import sys, io, os, json, hashlib, argparse, urllib.request, urllib.parse, html
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO = Path("/root/Data_back_test/whale_data")
SNAP_DIR = REPO / "data/raw/nansen_snapshots"
STATE_PATH = REPO / "data/state/digest_daily_vps_last.json"
LOG_PATH = REPO / "data/logs/digest_daily_vps.log"
RAW_PATH = REPO / "data/logs/digest_daily_vps_raw.log"
ENV_PATH = Path("/root/.env_tg")

STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

STALE_MAX_HOURS = 25
FRESH_CUM_THRESH = 500_000
FRESH_DELTA_THRESH = 50_000
EXCH_PCT_MIN = 1.0
EXCH_USD_MIN = 200_000

# Telegram cap = 4096; chừa biên cho dấu (k/N) + safety với HTML entity render.
TG_SAFE_LEN = 3800

# Env load
env = {}
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = env.get("TELEGRAM_CHAT_ID", "")


def _log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f: f.write(line + "\n")


def _save_raw(where, content):
    ts = datetime.now(timezone.utc).isoformat()
    with open(RAW_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n=== [{ts}] {where} ===\n{content}\n")


# -------- Format helpers · VERBATIM Windows alerts.py --------
def _fmt_usd(n):
    """Windows verbatim: >=1e6 → $X.XXM · >=1e3 → $Xk (int) · else → $X (int)."""
    n = float(n or 0)
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.0f}k"
    return f"${n:.0f}"


def _fmt_signed(n):
    """Windows verbatim: None → — · else s = +/-; s$X.XXM / s$Xk / s$X."""
    if n is None:
        return "—"
    n = float(n); a = abs(n); s = "+" if n >= 0 else "-"
    if a >= 1e6: return s + f"${a/1e6:.2f}M"
    if a >= 1e3: return s + f"${a/1e3:.0f}k"
    return s + f"${a:.0f}"


def _esc(s):
    """html.escape wrapper · guard bất-biến MỌI field động (không dựa 'u50 không có _')."""
    return html.escape(str(s if s is not None else ""), quote=False)


# -------- Telegram send · parse_mode=HTML (PARITY-FIX 02/09) --------
def send_telegram(text):
    """PARITY-FIX 02/09: parse_mode=HTML restored · verbatim Windows render."""
    if not BOT_TOKEN or not CHAT_ID:
        return (False, "MISSING_TOKEN_OR_CHAT_ID")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
            _save_raw(f"send_telegram HTTP {r.status}", body[:500])
            if r.status == 200:
                return (True, f"HTTP 200 · resp_len={len(body)}")
            return (False, f"HTTP {r.status} · body={body[:200]}")
    except Exception as e:
        _save_raw("send_telegram EXCEPTION", f"{type(e).__name__}: {e}")
        return (False, f"EXCEPTION {type(e).__name__}: {e}")


# -------- Multi-part splitter · VERBATIM Windows _split_into_messages --------
def _split_into_messages(warn_prefix, header_fn, footer, lines, limit=TG_SAFE_LEN):
    """Pack `lines` thành 1+ message HTML, mỗi message <= limit.
    header_fn(part_marker: str) -> str. "" cho single; " (k/N)" cho multi.
    Nội dung <pre>...</pre>, CẮT Ở RANH GIỚI DÒNG. Verbatim Windows.
    """
    PRE_OPEN, PRE_CLOSE = "<pre>\n", "\n</pre>"

    single = warn_prefix + header_fn("") + PRE_OPEN + "\n".join(lines) + PRE_CLOSE + footer
    if len(single) <= limit or not lines:
        return [single]

    marker_reserve = " (99/99)"
    fixed_overhead = (
        len(warn_prefix)
        + len(header_fn(marker_reserve))
        + len(PRE_OPEN)
        + len(PRE_CLOSE)
        + len(footer)
    )
    budget = max(1, limit - fixed_overhead)

    chunks, i = [], 0
    while i < len(lines):
        chunk, chunk_len = [], 0
        while i < len(lines):
            line = lines[i]
            added = len(line) + (1 if chunk else 0)
            if chunk and chunk_len + added > budget:
                break
            chunk.append(line)
            chunk_len += added
            i += 1
        chunks.append(chunk)

    n = len(chunks)
    return [
        warn_prefix + header_fn(f" ({k}/{n})") + PRE_OPEN + "\n".join(chunk) + PRE_CLOSE + footer
        for k, chunk in enumerate(chunks, 1)
    ]


# -------- Snapshot loader --------
def load_snapshot():
    """Load snapshot cho target D-1 UTC · trả {data, snap_path, stale_note, gap_note, gap_days}.

    [BASELINE-Δ KÝ 01/09 · S1] Compute Δ trực tiếp trên VPS từ cặp snapshot liên tiếp.
    [STALE-LABEL FIX KÝ 02/09 · S2] Tách 2 nhãn 2 nghĩa · không trộn:
      · stale_note = tuổi CỦA SNAPSHOT ĐANG DÙNG > STALE_MAX_HOURS (25h)
      · gap_note = snapshot ngày TARGET (D-1) missing · fallback ngày khác
    """
    now_utc = datetime.now(timezone.utc)
    # OPT-A/18-09 · đọc snapshot NGÀY HÔM NAY (thay D-1) để lấy Nansen mới nhất.
    # Cron 01:25 UTC chạy sau refresh 00:20 UTC 65 phút · snapshot cùng ngày mới ~1h,
    # tránh delay 24h (bug cũ: AIN $209K fresh không xuất hiện sáng 18/09 vì đọc snap 09-17).
    # Rollback: bak_pre_optA_20260918.
    target_date = now_utc.strftime("%Y-%m-%d")
    snap_path = SNAP_DIR / f"{target_date}.json"
    stale_note = None
    gap_note = None

    if not snap_path.exists():
        candidates = sorted(SNAP_DIR.glob("????-??-??.json"))
        if candidates:
            snap_path = candidates[-1]
            actual_date = snap_path.stem
            gap_note = f"[GAP: snapshot {target_date} missing · dùng {actual_date}]"
        else:
            return (None, None, f"[STALE: KHÔNG có snapshot nào trong {SNAP_DIR} · laptop-mắt offline hoặc sync chưa fire]", None, 0)

    mtime = datetime.fromtimestamp(snap_path.stat().st_mtime, tz=timezone.utc)
    age_h = (now_utc - mtime).total_seconds() / 3600
    if age_h > STALE_MAX_HOURS:
        stale_note = f"[STALE: snapshot {snap_path.stem} age {age_h:.1f}h > {STALE_MAX_HOURS}h · laptop-mắt offline]"

    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception as e:
        return (None, snap_path, f"[STALE: snapshot parse fail · {type(e).__name__}: {e}]", gap_note, 0)

    # [BASELINE-Δ S1] Find nearest-prior snapshot
    current_snap_date = datetime.strptime(snap_path.stem, "%Y-%m-%d").date()
    prev_data = None
    prev_snap_date = None
    for delta_days in range(1, 8):
        candidate = SNAP_DIR / f"{(current_snap_date - timedelta(days=delta_days)).strftime('%Y-%m-%d')}.json"
        if candidate.exists():
            try:
                prev_data = json.loads(candidate.read_text(encoding="utf-8"))
                prev_snap_date = candidate.stem
                break
            except Exception:
                continue

    gap_days = 0
    if prev_data is not None:
        gap_days = (current_snap_date - datetime.strptime(prev_snap_date, "%Y-%m-%d").date()).days
        prev_by_sym = {r.get("symbol", ""): r for r in prev_data.get("rows", [])}
        for row in data.get("rows", []):
            sym = row.get("symbol", "")
            p = prev_by_sym.get(sym, {})
            prev_usd = p.get("usd_1d")
            cur_usd = row.get("usd_1d")
            row["prev_usd_1d"] = prev_usd
            if prev_usd is not None and cur_usd is not None:
                try:
                    row["delta_usd"] = float(cur_usd) - float(prev_usd)
                except Exception:
                    row["delta_usd"] = None
            else:
                row["delta_usd"] = None
        data["has_delta"] = True
        data["_delta_gap_days"] = gap_days
        data["_delta_prev_snap"] = prev_snap_date
    else:
        for row in data.get("rows", []):
            row["prev_usd_1d"] = None
            row["delta_usd"] = None
        data["has_delta"] = False
        data["_delta_gap_days"] = 0
        data["_delta_prev_snap"] = None

    if gap_note is not None and gap_days > 1 and data.get("_delta_prev_snap"):
        gap_note = f"[GAP: snapshot {target_date} missing · dùng {snap_path.stem} · Δ tính {gap_days}d vs {data['_delta_prev_snap']}]"
    return (data, snap_path, stale_note, gap_note, gap_days)


# -------- Fresh digest · VERBATIM Windows send_digest --------
def render_fresh_digest(data, snap_path, stale_note, gap_note=None, test_mode=False):
    """Message 1 · Fresh wallets · VERBATIM Windows alerts.send_digest.
    SIGNED giữ: S1 (snapshot-pair sort-line label), S2 (stale/gap note), S3 (UX 0-token), S5 (prefix).
    """
    prefix = "[TEST-DIGEST · SMOKE · không mark hash]\n\n" if test_mode else ""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # S2 notes-block prefix · gap trước · stale sau
    notes = []
    if gap_note: notes.append(_esc(gap_note))
    if stale_note: notes.append(_esc(stale_note))
    warn_prefix = ("\n".join(notes) + "\n\n") if notes else ""

    if data is None:
        return (prefix + warn_prefix + f"📊 <b>FRESHWATCH Daily Digest</b> — {now_str}\n"
                f"(fresh digest unavailable · chờ laptop sync)")

    rows = data.get("rows", [])
    has_delta = data.get("has_delta", False)

    # Filter · VERBATIM Windows pick_eligible: cum >= FRESH_CUM_THRESH OR delta >= FRESH_DELTA_THRESH
    def _eligible(r):
        cum = r.get("usd_1d")
        delta = r.get("delta_usd")
        delta_pass = (delta is not None) and (float(delta) >= FRESH_DELTA_THRESH)
        cum_pass = (cum is not None) and (float(cum) >= FRESH_CUM_THRESH)
        return delta_pass or cum_pass
    eligible = [r for r in rows if _eligible(r)]

    # Sort · Windows: if DIGEST_SORT=delta AND has_delta → sort delta desc, else usd_1d desc
    if has_delta:
        def _k(r):
            d = r.get("delta_usd")
            return (1, 0) if d is None else (0, -float(d))
        eligible.sort(key=_k)
    else:
        eligible.sort(key=lambda r: float(r.get("usd_1d") or 0), reverse=True)

    if not eligible:
        # S3 · UX 0-token first-line (SIGNED)
        return (prefix + warn_prefix + f"📊 <b>FRESHWATCH — 0 token qua ngưỡng hôm nay</b> — {now_str}\n"
                f"<i>gom thêm ≥ {_fmt_usd(FRESH_DELTA_THRESH)} HOẶC tích lũy ≥ {_fmt_usd(FRESH_CUM_THRESH)}</i>")

    total = len(eligible)

    # Rows · VERBATIM Windows layout: "{badge} {rank:>2}. ${sym:<8} {cum:<8}Δ{signed}"
    # [SIDECAR §B · KÝ v1.1 03/09] emit per row · line_asprinted verbatim · assert n≡n cuối
    _sidecar = None
    try:
        _p = Path(__file__).resolve().parent / "lib" / "sidecar_emitter.py"
        if _p.exists():
            import importlib.util as _iu
            _sp = _iu.spec_from_file_location("sidecar_emitter", str(_p))
            _mod = _iu.module_from_spec(_sp); _sp.loader.exec_module(_mod)
            _target = data.get("_target_date_hint") if isinstance(data, dict) else None
            if _target is None and snap_path is not None:
                _target = snap_path.stem
            _sidecar = _mod.SidecarEmitter("fresh_digest", _target or "unknown-target")
    except Exception:
        _sidecar = None  # sidecar optional · KHÔNG block render nếu import fail

    pre_lines = []
    for i, r in enumerate(eligible, 1):
        sym = _esc(r.get("symbol") or "?")
        usd = r.get("usd_1d")
        prev = r.get("prev_usd_1d")
        dval = r.get("delta_usd")
        stale = bool(r.get("stale"))

        is_new = prev is None or (prev is not None and float(prev) < FRESH_CUM_THRESH)
        if stale:
            badge = "⚠ "
        elif is_new:
            badge = "🆕"
        else:
            badge = "  "
        delta_s = "Δ —" if dval is None else f"Δ{_fmt_signed(dval)}"
        rank_s = f"{i:>2}."
        sym_s = f"${sym}".ljust(9)
        cum_s = (_fmt_usd(usd) if usd is not None else "—").ljust(8)
        line_asprinted = f"{badge} {rank_s} {sym_s}{cum_s}{delta_s}"
        pre_lines.append(line_asprinted)
        if _sidecar is not None:
            try:
                _sidecar.emit(i, r.get("symbol", "?"), line_asprinted, {
                    "usd_1d": usd, "prev_usd_1d": prev, "delta_usd": dval,
                    "stale": stale, "badge": badge.rstrip(),
                })
            except Exception:
                pass  # emit fail should never block render

    # [SIDECAR §B assert p9 · ĐỘC-LẬP-2-VẾ KÝ 03/09 hậu-khớp] n_printed vs n_rows_reread từ JSONL
    if _sidecar is not None:
        try:
            _sidecar.assert_equal_independent(len(pre_lines))
        except Exception as _e:
            # Sidecar mismatch = [N/A-ERROR] per §B; don't crash render but log stderr
            import sys as _s
            print(f"[N/A-ERROR:SIDECAR-MISMATCH] fresh_digest · {type(_e).__name__}: {_e}", file=_s.stderr)

    # Header lines · VERBATIM Windows structure
    n_stale = sum(1 for r in eligible if r.get("stale"))
    stale_line = f" | ⚠ {n_stale} stale (API lỗi hôm nay)" if n_stale else ""

    criteria_line = (
        f"<i>gom thêm ≥ {_fmt_usd(FRESH_DELTA_THRESH)} HOẶC tích lũy ≥ {_fmt_usd(FRESH_CUM_THRESH)}</i>\n"
    )
    # S1 · sort-line SIGNED: snapshot-pair replaces state-file delta_hours
    if has_delta:
        prev_snap = data.get("_delta_prev_snap")
        gap_days = data.get("_delta_gap_days", 1)
        prev_ref = f"snapshot {_esc(prev_snap)} ({gap_days}d trước)" if prev_snap else "snapshot trước"
        sort_line = f"<i>xếp theo Δ gom thêm vs {prev_ref}</i>\n"
    else:
        sort_line = "<i>chưa có baseline — Δ sẽ có từ lần chạy thứ 2 trở đi</i>\n"

    def _header(part_marker=""):
        return (
            f"📊 <b>FRESHWATCH Daily Digest</b>{part_marker} — {now_str}\n"
            f"{criteria_line}"
            f"{sort_line}"
            f"{total} token{stale_line}\n\n"
        )
    footer = "\n\n<i>không phải lời khuyên đầu tư</i>"

    # Prefix + warn_prefix combined
    full_prefix = prefix + warn_prefix
    msgs = _split_into_messages(full_prefix, _header, footer, pre_lines)
    return "\n---MSG-BREAK---\n".join(msgs) if len(msgs) > 1 else msgs[0]


# -------- Exchange digest · VERBATIM Windows send_exchange_digest --------
def _pct_mcap(r):
    du = r.get("exchange_delta_usd")
    mc = r.get("market_cap")
    if du is None or mc is None or float(mc) <= 0:
        return None
    return float(du) / float(mc) * 100.0


def render_exchange_digest(data, snap_path, stale_note, gap_note=None, test_mode=False):
    """Message 2 · Exchange balance flow · VERBATIM Windows alerts.send_exchange_digest.
    Filter · VERBATIM Windows: (|Δ%mcap| ≥ EXCH_PCT_MIN) OR (|Δ$| ≥ EXCH_USD_MIN) — **OR** không AND.
    SIGNED giữ: S2 (Nansen-window note per-tin), S3 (UX 0-token), S5 (prefix).
    """
    prefix = "[TEST-DIGEST · SMOKE · không mark hash]\n\n" if test_mode else ""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # S2 · notes-block: EXCH-BAL Δ = native Nansen-window · Fresh gap-note KHÔNG dán
    notes = []
    if stale_note: notes.append(_esc(stale_note))
    notes.append("[Δ theo cửa sổ Nansen · field: exchange_prev_date → exchange_balance_date · KHÔNG phải snapshot-pair]")
    warn_prefix = "\n".join(notes) + "\n\n"

    if data is None:
        return (prefix + warn_prefix + f"📊 <b>EXCHANGE BALANCE Daily</b> — {now_str}\n"
                f"(exchange digest unavailable · chờ laptop sync)")

    rows = data.get("rows", [])

    # Filter · VERBATIM Windows pick_exchange_eligible: OR
    def _eligible(r):
        du = r.get("exchange_delta_usd")
        dt = r.get("exchange_delta_tokens")
        if du is None or dt is None:
            return False
        dpm = _pct_mcap(r)
        usd_pass = abs(float(du)) >= EXCH_USD_MIN
        pct_pass = dpm is not None and abs(dpm) >= EXCH_PCT_MIN
        return pct_pass or usd_pass
    qualified = [r for r in rows if _eligible(r)]

    # Split UP/DOWN, sort |Δ$| desc within each · VERBATIM Windows
    up = sorted([r for r in qualified if float(r["exchange_delta_tokens"]) > 0],
                key=lambda r: -abs(float(r["exchange_delta_usd"])))
    down = sorted([r for r in qualified if float(r["exchange_delta_tokens"]) < 0],
                  key=lambda r: -abs(float(r["exchange_delta_usd"])))

    if not up and not down:
        # S3 · UX 0-token first-line
        return (prefix + warn_prefix + f"📊 <b>EXCHANGE BALANCE Daily — 0 token qua ngưỡng</b> — {now_str}\n"
                f"<i>|Δ%mcap| ≥ {EXCH_PCT_MIN}% OR |Δ$| ≥ {_fmt_usd(EXCH_USD_MIN)}</i>")

    # Row · VERBATIM Windows: "  {rank:>2}. ${sym:<9}{pct:>8}  Δ{signed:<10}  bal {M:.1f}M"
    def _row_line(r, i):
        sym = _esc(r.get("symbol") or "?")
        usd = float(r["exchange_delta_usd"])
        bal = float(r.get("exchange_balance_tokens") or 0)
        dpm = _pct_mcap(r)
        pct_s = "—" if dpm is None else f"{'+' if dpm >= 0 else ''}{dpm:.2f}%"
        rank = f"{i:>2}."
        sym_s = f"${sym}".ljust(9)
        return f"  {rank} {sym_s}{pct_s:>8}  Δ{_fmt_signed(usd):<10}  bal {bal/1e6:.1f}M"

    # [SIDECAR §B · KÝ v1.1 03/09] emit per row EXCH-BAL · assert n_data_rows ≡ n_data_rows_printed
    _sidecar = None
    try:
        _p = Path(__file__).resolve().parent / "lib" / "sidecar_emitter.py"
        if _p.exists():
            import importlib.util as _iu
            _sp = _iu.spec_from_file_location("sidecar_emitter", str(_p))
            _mod = _iu.module_from_spec(_sp); _sp.loader.exec_module(_mod)
            _target = snap_path.stem if snap_path is not None else "unknown-target"
            _sidecar = _mod.SidecarEmitter("exch_digest", _target)
    except Exception:
        _sidecar = None

    pre_lines = []
    _row_idx = 0  # emit index (only data rows, not section headers)
    if up:
        pre_lines.append("📥 LÊN SÀN (áp lực bán):")
        for i, r in enumerate(up, 1):
            line = _row_line(r, i)
            pre_lines.append(line)
            _row_idx += 1
            if _sidecar is not None:
                try:
                    _sidecar.emit(_row_idx, r.get("symbol", "?"), line, {
                        "direction": "UP",
                        "exchange_delta_usd": r.get("exchange_delta_usd"),
                        "exchange_delta_tokens": r.get("exchange_delta_tokens"),
                        "exchange_balance_tokens": r.get("exchange_balance_tokens"),
                        "pct_mcap": _pct_mcap(r),
                    })
                except Exception:
                    pass
    if up and down:
        pre_lines.append("")
    if down:
        pre_lines.append("📤 RỜI SÀN (đang gom):")
        for i, r in enumerate(down, 1):
            line = _row_line(r, i)
            pre_lines.append(line)
            _row_idx += 1
            if _sidecar is not None:
                try:
                    _sidecar.emit(_row_idx, r.get("symbol", "?"), line, {
                        "direction": "DOWN",
                        "exchange_delta_usd": r.get("exchange_delta_usd"),
                        "exchange_delta_tokens": r.get("exchange_delta_tokens"),
                        "exchange_balance_tokens": r.get("exchange_balance_tokens"),
                        "pct_mcap": _pct_mcap(r),
                    })
                except Exception:
                    pass

    # [SIDECAR §B assert p9 · ĐỘC-LẬP-2-VẾ KÝ 03/09] n_printed(up+down) vs n_rows_reread từ JSONL
    if _sidecar is not None:
        try:
            _sidecar.assert_equal_independent(len(up) + len(down))
        except Exception as _e:
            import sys as _s
            print(f"[N/A-ERROR:SIDECAR-MISMATCH] exch_digest · {type(_e).__name__}: {_e}", file=_s.stderr)

    n_failed = sum(1 for r in rows if r.get("exchange_api_failed"))
    failed_note = f" | ⚠ {n_failed} fail" if n_failed else ""

    def _header(part_marker=""):
        return (
            f"📊 <b>EXCHANGE BALANCE Daily</b>{part_marker} — {now_str}\n"
            f"<i>Δ balance day-over-day · |Δ%mcap| ≥ {EXCH_PCT_MIN}% "
            f"OR |Δ$| ≥ {_fmt_usd(EXCH_USD_MIN)}</i>\n"
            f"{len(qualified)} token ({len(up)} lên / {len(down)} rời){failed_note}\n\n"
        )
    footer = "\n\n<i>data: Nansen /flows · không phải lời khuyên đầu tư</i>"

    full_prefix = prefix + warn_prefix
    msgs = _split_into_messages(full_prefix, _header, footer, pre_lines)
    return "\n---MSG-BREAK---\n".join(msgs) if len(msgs) > 1 else msgs[0]


# -------- Idempotent state --------
def idempotent_check(hash_val):
    if not STATE_PATH.exists(): return True
    try:
        s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return s.get("last_hash") != hash_val
    except Exception: return True


def mark_sent(hash_val):
    STATE_PATH.write_text(json.dumps({
        "last_hash": hash_val,
        "sent_at_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")


# -------- Main --------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="TEST-DIGEST mode: prefix rõ, no idempotent")
    args = ap.parse_args()

    _log(f"[DIGEST-VPS START] test={args.test}")
    if not BOT_TOKEN or not CHAT_ID:
        _log("[FAIL] BOT_TOKEN/CHAT_ID missing in /root/.env_tg"); sys.exit(1)

    data, snap_path, stale_note, gap_note, gap_days = load_snapshot()
    if snap_path:
        _has_delta = data.get("has_delta", False) if data else False
        _prev = data.get("_delta_prev_snap") if data else None
        _log(f"[LOAD] snapshot={snap_path.name} · stale={stale_note is not None} · gap={gap_note is not None} · has_delta={_has_delta} · prev={_prev} · gap_days={gap_days}d")
    else:
        _log(f"[LOAD] NO SNAPSHOT · stale_note={stale_note}")

    fresh_msg = render_fresh_digest(data, snap_path, stale_note, gap_note=gap_note, test_mode=args.test)
    exch_msg = render_exchange_digest(data, snap_path, stale_note, gap_note=gap_note, test_mode=args.test)

    # Multi-part support: split by MSG-BREAK sentinel
    def _split_multi(m):
        return m.split("\n---MSG-BREAK---\n")

    fresh_parts = _split_multi(fresh_msg)
    exch_parts = _split_multi(exch_msg)

    full_hash = hashlib.sha256((fresh_msg + exch_msg).encode()).hexdigest()[:12]
    if not args.test:
        if not idempotent_check(full_hash):
            _log(f"[SKIP-IDEMPOTENT] hash={full_hash} · đã gửi trước · bỏ qua")
            sys.exit(0)

    all_ok = True
    for i, part in enumerate(fresh_parts, 1):
        ok, det = send_telegram(part)
        _log(f"[SENT] Fresh-Wallets part={i}/{len(fresh_parts)} · ok={ok} · {det}")
        if not ok: all_ok = False
    # [ARTIFACT-DUMP as-sent · KÝ 07/09 P0] · dump full fresh_msg after all parts sent
    if all_ok:
        try:
            from lib.artifact_dump import dump_as_sent as _das
            _ok, _det = _das("fresh_digest", (snap_path.stem if snap_path else "unknown"), fresh_msg, channel="old")
            _log(f"[ARTIFACT-DUMP fresh_digest] {_ok} · {_det}")
        except Exception as _e: _log(f"[ARTIFACT-DUMP-ERR fresh_digest] {type(_e).__name__}: {_e}")
    for i, part in enumerate(exch_parts, 1):
        ok, det = send_telegram(part)
        _log(f"[SENT] EXCH-BAL part={i}/{len(exch_parts)} · ok={ok} · {det}")
        if not ok: all_ok = False
    # [ARTIFACT-DUMP as-sent · KÝ 07/09 P0]
    if all_ok:
        try:
            from lib.artifact_dump import dump_as_sent as _das
            _ok, _det = _das("exch_digest", (snap_path.stem if snap_path else "unknown"), exch_msg, channel="old")
            _log(f"[ARTIFACT-DUMP exch_digest] {_ok} · {_det}")
        except Exception as _e: _log(f"[ARTIFACT-DUMP-ERR exch_digest] {type(_e).__name__}: {_e}")

    if all_ok:
        if not args.test:
            mark_sent(full_hash)
        _log(f"[DIGEST-VPS DONE] all_ok=True · hash={full_hash}")
        sys.exit(0)
    else:
        _log(f"[DIGEST-VPS FAIL] some parts failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""MASTER-PREVIEW send · V3.5j · PIPELINE TỰ ĐỦ mỗi đêm.

Pipeline (từng bước fail → SKIP + sentinel to đùng · không half-send):
  1. Standing check (chỉ mở LẦN ĐẦU · sau đó tin pipeline mỗi-đêm)
  2. Rebuild ledger(target) → events_<target>.jsonl + stars_<target>.jsonl
  3. Render digest via digest_summary_v2.build_v2_digest(target)
  4. LABEL-LINT trên body (cửa mỗi-đêm · orphan >0 → SKIP)
  5. Concat-seal footer (recompute + verify)
  6. Send [MASTER-PREVIEW đêm N/2] → TG_CHAT_ID_DAILY

Standing conditions (LẦN ĐẦU MỞ · sau standing_active file created):
  · data/state/dem0_lan2_verdict.json = {verdict: "KHÔNG-KÍCH", evidence_pointer: "..."}
  · data/state/demo5_sent.marker exists
  · data/state/harness_labellint.marker exists  (chỉ vai điều-kiện-mở LẦN ĐẦU)
  · data/state/preview_veto.marker NOT exists (operator veto = "dừng preview")

Sau khi tạo standing_active.marker → standing check trở về chỉ kiểm veto + fresh
pipeline mỗi-đêm.

Verdict-file schema (dem0_lan2_verdict.json · V3.5j):
{
  "verdict": "KHÔNG-KÍCH" | "KÍCH",
  "evidence_pointer": "path or grep-hash cite",
  "date": "YYYY-MM-DD",
  "n_pin_fail_ngoai_khai": <int>,
  "n_sent_full_pair": "N/6",
  "notes": "optional"
}
"""
from __future__ import annotations
import os, sys, json, hashlib, subprocess, re
from pathlib import Path
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.parse

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
STATE = REPO / "data/state"
LOG_P = REPO / "data/logs/master_preview.log"

# V3.5j directive item 1: load /root/.env_tg (chmod 600 · outside repo · same as tg_relay)
_ENV_TG = Path("/root/.env_tg")
if _ENV_TG.exists():
    for _line in _ENV_TG.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

STANDING_FILES = {
    "dem0_verdict": STATE / "dem0_lan2_verdict.json",
    "demo5_marker": STATE / "demo5_sent.marker",
    "harness_lint_marker": STATE / "harness_labellint.marker",  # vestigial · gỡ V3.5p
    "veto_marker": STATE / "preview_veto.marker",
    # V3.5q · GỠ standing_active bypass (delete flag file trên VPS · code không đọc nữa)
}
COUNTER_FILE = STATE / "master_preview_counter.json"


def _log(msg):
    LOG_P.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_P.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg, file=sys.stderr)


def check_standing() -> tuple[bool, str]:
    """V3.5p (item 1) THUẦN MÁY: standing = {verdict==KHÔNG-KÍCH ∧ demo5_sent ∧ ¬veto}
    · KHÔNG dùng file-exists (kẻo verdict đỏ file tồn tại → tự mở nhầm)
    · KHÔNG bypass verdict check qua standing_active (verdict check MỖI đêm).
    """
    if STANDING_FILES["veto_marker"].exists():
        return (False, "[N/A-ERROR:VETO] operator dừng preview")
    # First-time open · PARSE VALUE (not exists-only)
    if not STANDING_FILES["dem0_verdict"].exists():
        return (False, "[N/A-ERROR:STANDING] dem0_lan2_verdict.json chưa có")
    try:
        v = json.loads(STANDING_FILES["dem0_verdict"].read_text(encoding="utf-8"))
    except Exception as e:
        return (False, f"[N/A-ERROR:STANDING] verdict parse: {e}")
    if v.get("verdict") != "KHÔNG-KÍCH":
        # V3.5o · CHƯA-THI treated as not-met (không đóng dấu KÍCH)
        return (False, f"[N/A-ERROR:STANDING-VERDICT] verdict='{v.get('verdict')}' · cần KHÔNG-KÍCH")
    if not v.get("evidence_pointer"):
        return (False, f"[N/A-ERROR:STANDING-EVIDENCE] verdict-file thiếu evidence_pointer")
    # Target date sanity: verdict must be for "recent" đêm (within past 2 days)
    verdict_date = v.get("date", "")
    try:
        vd = datetime.strptime(verdict_date, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        if (today - vd).days > 2:
            return (False, f"[N/A-ERROR:STANDING-STALE] verdict date={verdict_date} > 2d old vs today={today}")
    except Exception as e:
        return (False, f"[N/A-ERROR:STANDING-DATE] parse fail: {e}")
    # V3.5p (item 1) · gỡ harness_labellint.marker khỏi standing · vestigial
    # Lý do: LABEL-LINT đã là cửa-mỗi-đêm trong pipeline V3.5j (step_label_lint) ·
    # marker duplicate condition. Standing từ nay = {verdict==KHÔNG-KÍCH ∧ demo5_sent ∧ ¬veto}
    if not STANDING_FILES["demo5_marker"].exists():
        return (False, "[N/A-ERROR:STANDING] demo5_sent.marker chưa có")
    # V3.5s GATE-D · D4 (F3 · LOG-ONLY): postcheck_ok của target trước T-1 CHỈ LOG
    # KHÔNG chặn standing · KHÔNG bỏ vế postcheck khỏi NIGHT-COUNTER (D5 giữ)
    # Lý do F3: postcheck fail đêm trước không nên chặn đêm sau · log để operator quyết
    prev_pc_note = "n/a"
    try:
        prev_date = (vd - timedelta(days=1)).isoformat()
        for e in _journal_iter():
            if e.get("target_date") == prev_date and "postcheck_ok" in e:
                prev_pc = e.get("postcheck_ok")
                prev_flag = e.get("postcheck_flag", "")
                prev_pc_note = f"prev({prev_date})_postcheck_ok={prev_pc} flag={prev_flag}"
                # LOG-ONLY (F3): _log inline · không return False
                _log(f"[D4-LOG] {prev_pc_note}")
                break
    except Exception:
        pass  # L-66-OK
    # V3.5p · thuần máy · KHÔNG cache standing (verdict check mỗi đêm)
    return (True, f"standing OK · verdict={v.get('verdict')} date={verdict_date} · demo5-marker present · d4={prev_pc_note}")


def _load_counter():
    if not COUNTER_FILE.exists():
        return {"night_index": 0, "total_nights": 2, "started_at": None}
    try: return json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except: return {"night_index": 0, "total_nights": 2}  # L-66-OK (benign fallback)


def _save_counter(c):
    COUNTER_FILE.write_text(json.dumps(c, indent=2), encoding="utf-8")


def _increment_counter():
    c = _load_counter()
    c["night_index"] = int(c.get("night_index", 0)) + 1
    if c.get("started_at") is None:
        c["started_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save_counter(c)
    return (c["night_index"], int(c.get("total_nights", 2)))


# ═════ PIPELINE stages (V3.5j) ═════
def step_rebuild_ledger(target: str) -> tuple[bool, str]:
    """Rebuild ledger(target) via ledger_backfill_30d_v3_5.py."""
    script = REPO / "scripts/ledger_backfill_30d_v3_5.py"
    try:
        r = subprocess.run(
            [sys.executable, str(script), "--target", target, "--window", "30"],
            capture_output=True, text=True, timeout=120, cwd=str(REPO))
        if r.returncode != 0:
            return (False, f"[N/A-ERROR:REBUILD] returncode={r.returncode} · stderr={r.stderr[:200]}")
        # Verify ledger file updated
        ev = REPO / f"data/logs/event_ledger/events_{target}.jsonl"
        if not ev.exists():
            return (False, f"[N/A-ERROR:REBUILD] events file missing after rebuild")
        md5 = hashlib.md5(ev.read_bytes()).hexdigest()
        return (True, f"ledger rebuilt · md5={md5}")
    except subprocess.TimeoutExpired:
        return (False, "[N/A-ERROR:REBUILD] timeout 120s")
    except Exception as e:
        return (False, f"[N/A-ERROR:REBUILD] {type(e).__name__}: {e}")


def step_render_digest(target: str) -> tuple[bool, str]:
    """Render via digest_summary_v2.build_v2_digest."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from digest_summary_v2 import build_v2_digest
        body = build_v2_digest(target)
        if not body or len(body) < 100:
            return (False, f"[N/A-ERROR:RENDER] empty/too-short body · len={len(body) if body else 0}")
        return (True, body)
    except Exception as e:
        return (False, f"[N/A-ERROR:RENDER] {type(e).__name__}: {e}")


def step_label_lint(body: str) -> tuple[bool, str]:
    """Run label-lint on body TEXT · orphan > 0 → SKIP."""
    sys.path.insert(0, str(REPO / "tests/harness"))
    try:
        from label_claims_lint import lint_file
        tmp = REPO / "data/logs/master_preview_body.txt"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(body, encoding="utf-8")
        findings = lint_file(tmp)
        if findings:
            fnames = [f"L{f['line_no']}:'{f['claim']}'" for f in findings[:5]]
            return (False, f"[N/A-ERROR:LINT] {len(findings)} orphan claim(s) · sample: {fnames}")
        return (True, f"lint PASS · 0 orphan")
    except Exception as e:
        return (False, f"[N/A-ERROR:LINT] {type(e).__name__}: {e}")


def step_concat_seal(body: str) -> tuple[bool, str]:
    """V3.5p · AMD-07 concat-persist verify.
    build_v2_digest tự compute + persist seal-domain ra master_concat_<target>.txt.
    Ở đây verify: md5sum(persist file)[:12] ≡ concat-seal in footer.
    """
    m = re.search(r"concat-seal=([a-f0-9]{12}).*target=(\d{4}-\d{2}-\d{2})", body)
    if not m:
        return (False, f"[N/A-ERROR:SEAL] concat-seal line missing in body")
    footer_seal = m.group(1); target = m.group(2)
    concat_p = REPO / "data/artifacts" / f"master_concat_{target}.txt"
    if not concat_p.exists():
        return (False, f"[N/A-ERROR:SEAL-PERSIST-MISSING] {concat_p.name} không tồn tại")
    file_md5 = hashlib.md5(concat_p.read_bytes()).hexdigest()[:12]
    if file_md5 != footer_seal:
        return (False, f"[N/A-ERROR:SEAL-MISMATCH] file={file_md5} · footer={footer_seal} · AMD-07 broken")
    return (True, f"AMD-07 verify PASS · file[:12]={file_md5} ≡ footer-seal={footer_seal}")


TG_ALLOWED_HTML_TAGS = {"b", "i", "u", "s", "a", "code", "pre", "tg-spoiler", "blockquote"}
_TG_TAG_RE = re.compile(r"<([^<>]*)>")


def _tg_scan_bad_html(text: str):
    """AB1/U7/18-09 · quét <...> · trả (tag_str, pos) đầu tiên KHÔNG thuộc whitelist,
    hoặc None nếu toàn bộ hợp lệ. Tag rỗng hoặc tên lạ (ví dụ `<renderer>`, `<target>`)
    → BAD. Whitelist = {b,i,u,s,a,code,pre,tg-spoiler,blockquote} · TG parse_mode=HTML."""
    for m in _TG_TAG_RE.finditer(text):
        inner = m.group(1).strip()
        if not inner:
            return (m.group(0), m.start())
        name = inner.lstrip("/").split()[0].split(">")[0].lower()
        if name not in TG_ALLOWED_HTML_TAGS:
            return (m.group(0), m.start())
    return None


def send_telegram(text: str) -> tuple[bool, str]:
    # D3/17-09 · PRE-CHECK độ dài · TG limit=4096 chars · KHÔNG tự cắt (cắt = mất seal/cites)
    n_chars = len(text)
    if n_chars > 4096:
        _log(f"[N/A-ERROR:BODY-TOO-LONG] len={n_chars} limit=4096")
        return (False, f"BODY-TOO-LONG len={n_chars}")
    if n_chars > 3800:
        _log(f"[WARN:BODY-NEAR-LIMIT len={n_chars}]")
    # AB1/U7/18-09 · PRE-CHECK HTML tag whitelist · chặn thẻ lạ trước khi API nhận HTTP 400
    bad = _tg_scan_bad_html(text)
    if bad is not None:
        tag_str, pos = bad
        _log(f"[N/A-ERROR:BAD-HTML] tag={tag_str} pos={pos}")
        return (False, f"BAD-HTML tag={tag_str} pos={pos}")
    bot = os.getenv("TG_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TG_CHAT_ID_DAILY")
    if not bot or not chat:
        _log(f"[N/A-ERROR:SEND] missing TG_BOT_TOKEN or TG_CHAT_ID_DAILY env")
        return (False, "env-missing")
    url = f"https://api.telegram.org/bot{bot}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            resp = json.loads(r.read().decode())
            mid = resp.get("result", {}).get("message_id")
            return (r.status == 200 and resp.get("ok"), f"HTTP {r.status} · message_id={mid}")
    except Exception as e:
        _log(f"[N/A-ERROR:SEND] {type(e).__name__}: {e}")
        return (False, f"{type(e).__name__}: {e}")


# V3.5n · SENT-LEG evidence sources per leg
SENT_LEG_FORMAT = {
    "tg_relay_gom_h": "native: [SENT] all_ok=True + target_date=<T>",
    "fresh_digest": "native: [SENT] Fresh-Wallets ok=True + snapshot=<T>.json",
    "exch_digest": "native: [SENT] EXCH-BAL ok=True + snapshot=<T>.json",
    "gom_daily": "V3.5i: [SENT] gom_daily ok=True target=<T>",
    "phase_map": "V3.5i: [SENT] phase_map ok=True target=<T>",
    "watchlist": "V3.5i: [SENT] watchlist ok=True target=<T>",
}


def compute_night_verdict(target: str, dry: bool = False) -> dict:
    """V3.5n · compute verdict WITH bảng 6 chân đích danh (source per leg).
    · BỘ-PIN-ĐÃ-NIÊM p1-p22 (p23-p26 NGOÀI-niêm per fixture V3.5m)
    · SENT source priority: bell_journal > native-marker > log-fallback
    · Ghi verdict-file with evidence_pointers per leg.

    U5-1/19-09 · `dry=True`: compute và trả kết quả · KHÔNG ghi verdict_epoch
    · KHÔNG ghi dem0_lan2_verdict.json · KHÔNG _log sentinel · KHÔNG đụng state.
    Doctrine: xem không được để lại dấu. Công cụ chẩn đoán không được đổi
    thứ nó chẩn đoán.
    """
    # Local logger · nuốt sentinel khi dry
    def _log_local(msg):
        if not dry:
            _log(msg)
    art_dir = REPO / "data/artifacts"
    bell = REPO / "data/logs/bell_journal.jsonl"
    renderers = ["tg_relay_gom_h", "fresh_digest", "exch_digest", "gom_daily", "phase_map", "watchlist"]
    # 6/6 full-pair check
    # H1/19-09 · fresh/exch dùng snapshot filename (Opt-A shift) · KHÔNG khớp target=T
    # Scan artifact với PATTERN prefix + timestamp trong 30h window trước cron_close (J1/19-09 · nới từ 25h · biên 5h39m)
    from datetime import datetime as _dt_fp, timedelta as _td_fp, timezone as _tz_fp
    try:
        _tgt_d_fp = _dt_fp.strptime(target, "%Y-%m-%d").date()
        _cron_close_fp = _dt_fp.combine(_tgt_d_fp + _td_fp(days=1),
                                         _dt_fp.strptime("01:46", "%H:%M").time(),
                                         tzinfo=_tz_fp.utc)
    except Exception:
        _cron_close_fp = _dt_fp.now(_tz_fp.utc)

    def _has_recent_artifact(renderer, window_hours=30):
        """Trả True nếu có tg_final_<renderer>_*.txt với mtime trong (cron_close - window, cron_close)."""
        for p in art_dir.glob(f"tg_final_{renderer}_*.txt"):
            try:
                mtime = _dt_fp.fromtimestamp(p.stat().st_mtime, tz=_tz_fp.utc)
                lag_h = (_cron_close_fp - mtime).total_seconds() / 3600
                if 0 <= lag_h <= window_hours:
                    return True, p
            except Exception:
                continue
        return False, None

    full_pair_status = {}
    for r in renderers:
        txt = art_dir / f"tg_final_{r}_{target}.txt"
        jsonl = art_dir / f"tg_final_{r}_{target}.jsonl"
        if txt.exists() and jsonl.exists():
            n_rows = sum(1 for _ in open(jsonl, encoding="utf-8"))
            full_pair_status[r] = {"txt": txt.stat().st_size, "jsonl_rows": n_rows}
        elif r in ("fresh_digest", "exch_digest"):
            # H1 · Opt-A shift · check artifact trong window 30h thay khớp target-name (J1 · nới từ 25h)
            has_recent, p = _has_recent_artifact(r)
            if has_recent:
                full_pair_status[r] = {"txt": p.stat().st_size, "jsonl_rows": None, "source": "opt-a-shifted"}
            else:
                full_pair_status[r] = {"missing": True}
        else:
            full_pair_status[r] = {"missing": True}
    n_full = sum(1 for r in renderers if not full_pair_status[r].get("missing"))
    # SENT source per leg · priority: bell_journal > native/log-grep
    sent_leg = {r: {"ok": False, "source": None, "cite": None} for r in renderers}
    # 1. bell_journal (V3.5m wired: gom_daily·phase_map·watchlist · fresh/exch/relay use native)
    if bell.exists():
        for line in bell.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("target_date") == target and e.get("ok") and e.get("renderer") in sent_leg:
                    sent_leg[e["renderer"]] = {
                        "ok": True, "source": "bell_journal",
                        "cite": f"body_md5={e.get('body_md5','')[:12]} msg_id={e.get('message_id')}"
                    }
            except: pass  # L-66-OK (benign fallback)
    # 2. Native/log-grep fallback · H1/19-09 · LEG-SENT canonical marker cho fresh/exch
    # Verdict xác định leg bằng BẢN GHI, không bằng tên file:
    #   fresh/exch có LEG-SENT ts_utc trong 30h TRƯỚC cron_close · leg ok (không quan tâm snapshot target · J1 · nới từ 25h)
    #   → chấp nhận Opt-A shift · không hardcode <T+1>
    log_map = {
        "tg_relay_gom_h": (REPO / "data/logs/tg_relay.log", r"\[SENT\] all_ok=True", "target_date"),
        "fresh_digest": (REPO / "data/logs/digest_daily_vps.log", r"\[LEG-SENT renderer=fresh_digest.*ts_utc=([^\]]+)\]", "leg_sent_ts"),
        "exch_digest": (REPO / "data/logs/digest_daily_vps.log", r"\[LEG-SENT renderer=exch_digest.*ts_utc=([^\]]+)\]", "leg_sent_ts"),
        "gom_daily": (REPO / "data/logs/gom_daily.log", rf"\[SENT\] gom_daily ok=True.*target={target}", "target"),
        "phase_map": (REPO / "data/logs/phase_tag.log", rf"\[SENT\] phase_map ok=True.*target={target}", "target"),
        "watchlist": (REPO / "data/export/watchlist_cron.log", rf"\[SENT\] watchlist ok=True.*target={target}", "target"),
    }
    from datetime import datetime as _dt_ls, timedelta as _td_ls, timezone as _tz_ls
    # H1/H4/19-09 · anchor window vào target+1d 01:46 UTC (cron_close) · KHÔNG dùng now
    # Lý do: retroactive verdict compute (VD chấm 09-15 hôm 19/09) phải xét fresh SENT ngày 09-16 01:25
    # (đêm cron chấm target 09-15), không phải "SENT trong 25h qua so hôm nay"
    try:
        _tgt_d = _dt_ls.strptime(target, "%Y-%m-%d").date()
        _cron_close = _dt_ls.combine(_tgt_d + _td_ls(days=1),
                                      _dt_ls.strptime("01:46", "%H:%M").time(),
                                      tzinfo=_tz_ls.utc)
    except Exception:
        _cron_close = _dt_ls.now(_tz_ls.utc)
    _leg_sent_window_hours = 30   # H1/J1 · leg ok nếu SENT trong 30h TRƯỚC cron_close (nới từ 25h · lý do: fresh gửi 01:25 UTC, cron_close 01:46 UTC hôm sau ~24h21m — 25h chỉ dư 39min · 30h cho biên 5h39m)
    for r, (logf, pat, mark_type) in log_map.items():
        if sent_leg[r]["ok"]: continue
        if not logf.exists(): continue
        content = logf.read_text(encoding="utf-8", errors="replace")

        if mark_type == "leg_sent_ts":
            # H1/H2 · Ưu tiên LEG-SENT canonical · fallback [SENT] line với ts window
            latest_match = None; latest_ts = None; used_fallback = False
            for mm in re.finditer(pat, content):
                ts_str = mm.group(1)
                try:
                    ts_val = _dt_ls.fromisoformat(ts_str)
                    if ts_val.tzinfo is None: ts_val = ts_val.replace(tzinfo=_tz_ls.utc)
                except Exception:
                    continue
                lag_hours = (_cron_close - ts_val).total_seconds() / 3600
                if 0 <= lag_hours <= _leg_sent_window_hours:
                    if latest_ts is None or ts_val > latest_ts:
                        latest_ts = ts_val
                        latest_match = mm.group(0)
            # Fallback · legacy log SENT trong 30h window (không cần LEG-SENT marker)
            if latest_match is None:
                # H4/19-09 · backward compat cho log cũ (trước H2 wire)
                # Grep dòng [SENT] X · lấy ts từ prefix log line [YYYY-MM-DDTHH:MM:SS+00:00]
                legacy_pat = r"\[SENT\] Fresh-Wallets" if r == "fresh_digest" else r"\[SENT\] EXCH-BAL"
                # microseconds có thể có (VD 2026-09-15T01:25:02.323123+00:00)
                line_ts_re = re.compile(r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+\-]\d{2}:\d{2})?)\]")
                for line in content.splitlines():
                    if not re.search(legacy_pat, line): continue
                    if "ok=True" not in line: continue
                    m_ts = line_ts_re.match(line)
                    if not m_ts: continue
                    try:
                        ts_val = _dt_ls.fromisoformat(m_ts.group(1))
                        if ts_val.tzinfo is None: ts_val = ts_val.replace(tzinfo=_tz_ls.utc)
                    except Exception:
                        continue
                    lag_hours = (_cron_close - ts_val).total_seconds() / 3600
                    if 0 <= lag_hours <= _leg_sent_window_hours:
                        if latest_ts is None or ts_val > latest_ts:
                            latest_ts = ts_val; latest_match = line; used_fallback = True
            if latest_match is None: continue
            sent_leg[r] = {
                "ok": True,
                "source": "legacy-sent-fallback" if used_fallback else "leg-sent-marker",
                "cite": f"{logf.name}: {latest_match[:100]}",
            }
            continue

        m = re.search(pat, content)
        if not m: continue
        # target_date verify for tg_relay (block-scoped)
        if mark_type == "target_date":
            if f"target_date={target}" not in content: continue
        # For gom_daily/phase_map/watchlist: pattern already includes target
        sent_leg[r] = {
            "ok": True,
            "source": "native-marker" if r == "tg_relay_gom_h" else "log-grep",
            "cite": f"{logf.name}: {m.group(0)[:80]}",
        }
    n_sent = sum(1 for r in renderers if sent_leg[r]["ok"])
    # Missing legs (đích danh)
    missing_legs = [r for r in renderers if not sent_leg[r]["ok"]]
    # Pin-scan · V3.5s GATE-D · D1: chỉ chạy pre-ledger pins (p20) trong compute_verdict
    # · post-ledger pins (p21,p22) chuyển sang postcheck sau send · D2: enum rc 0=PASS/1=FAIL/2=N/A
    # · D8: log stdout+stderr harness vào master_preview.log (đêm trước exit-code nuốt lý do)
    import subprocess
    pin_result = None
    try:
        r = subprocess.run(
            [sys.executable, str(REPO / "tests/harness/harness_p20_p22_v3_5k.py"),
             "--target", target, "--only", "pre-ledger"],
            capture_output=True, text=True, timeout=60)
        if r.stdout: _log_local(f"[PIN-SCAN stdout]\n{r.stdout.rstrip()}")
        if r.stderr: _log_local(f"[PIN-SCAN stderr]\n{r.stderr.rstrip()}")
        pin_result = ("PASS" if r.returncode == 0
                      else ("N/A" if r.returncode == 2 else "FAIL"))
    except Exception as e:
        pin_result = f"ERR:{e}"
    # Sentinel scan (grep [N/A-ERROR:*] outside declared list)
    # AB2/U1/18-09 · CỬA-SỔ 26h · sentinel ngoài 26h TRƯỚC now → không tính (xanh);
    # trong → tính (đen). Bài học p23: sentinel 09-15 vẫn đen 09-17 → phải trượt cửa.
    declared_sentinels = {"N/A-ERROR:DUMP-HALF-FAIL", "N/A-ERROR:DUMP-FAIL",
                          "N/A-ERROR:STANDING", "N/A-ERROR:VETO"}
    from datetime import datetime as _dt2, timedelta as _td2, timezone as _tz2
    _now_utc = _dt2.now(_tz2.utc)
    _cutoff = _now_utc - _td2(hours=26)
    _line_ts_re = re.compile(r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+\-]\d{2}:\d{2})?)\]")
    unknown_sentinels = []
    _log_p = REPO / "data/logs/master_preview.log"
    if _log_p.exists():
        for line in _log_p.read_text(encoding="utf-8", errors="replace").splitlines():
            m_ts = _line_ts_re.match(line)
            if not m_ts: continue
            try:
                ts = _dt2.fromisoformat(m_ts.group(1))
                if ts.tzinfo is None: ts = ts.replace(tzinfo=_tz2.utc)
            except Exception:
                continue
            if ts < _cutoff: continue  # ngoài cửa sổ · KHÔNG tính
            for m in re.finditer(r"\[N/A-ERROR:([A-Z0-9\-_/]+)\]", line):
                tag = f"N/A-ERROR:{m.group(1)}"
                if not any(tag.startswith(d) for d in declared_sentinels):
                    unknown_sentinels.append(tag)
    # bell_journal.jsonl · ts_utc field · N/A-ERROR không xuất hiện trong record ok,
    # nhưng vẫn giữ scan để future-proof nếu bell ghi error record
    if bell.exists():
        for line in bell.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(line)
                ts = _dt2.fromisoformat(e.get("ts_utc", ""))
                if ts.tzinfo is None: ts = ts.replace(tzinfo=_tz2.utc)
                if ts < _cutoff: continue
            except Exception:
                continue
            for m in re.finditer(r"\[N/A-ERROR:([A-Z0-9\-_/]+)\]", line):
                tag = f"N/A-ERROR:{m.group(1)}"
                if not any(tag.startswith(d) for d in declared_sentinels):
                    unknown_sentinels.append(tag)
    # V3.5o · VERDICT enum += CHƯA-THI
    # target có cửa-cron chưa đóng (now < target+1d 01:46 UTC) ⇒ CHƯA-THI
    # (cấm đóng dấu KÍCH lên đêm chưa mở đề)
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    try:
        target_d = _dt.strptime(target, "%Y-%m-%d").date()
        cron_close = _dt.combine(target_d + _td(days=1),
                                  _dt.strptime("01:46", "%H:%M").time(),
                                  tzinfo=_tz.utc)
        chưa_thi = _dt.now(_tz.utc) < cron_close
    except Exception:
        chưa_thi = False
    # V3.5s GATE-D · D2: N/A pin ⇒ CHƯA-THI (khác FAIL · thiếu chủ thể chấm)
    if chưa_thi:
        verdict = "CHƯA-THI"
    elif pin_result == "N/A":
        verdict = "CHƯA-THI"
    elif n_full == 6 and n_sent == 6 and pin_result == "PASS" and not unknown_sentinels:
        verdict = "KHÔNG-KÍCH"
    else:
        verdict = "KÍCH"
    result = {
        "verdict": verdict,
        "date": target,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "evidence_pointer": f"bell_journal + logs · target={target} · {'6/6' if n_full==6 else str(n_full)+'/6-full-pair MISS'}",
        "n_full_pair": f"{n_full}/6",
        "n_sent": f"{n_sent}/6",
        "sent_leg_detail": sent_leg,        # V3.5n · per-leg source + cite
        "missing_legs": missing_legs,       # V3.5n · đích danh chân đỏ
        "pin_scan_p1_p22_bo_niem": pin_result,  # V3.5n · bộ-niêm scope
        "unknown_sentinels": unknown_sentinels[:10],
        "full_pair_detail": full_pair_status,
    }
    # V3.5q ĐIỂM-THI-BẤT-BIẾN (item 1): verdict(target) = compute ĐẦU TIÊN sau cửa 01:46
    # Recompute chỉ hợp lệ khi fix ở GRADER (compute/reader) · fix PERFORMER (sender) ⇒ điểm giữ
    # Store FIRST-COMPUTE tại verdict_epoch_<target>.json · verdict-file live chỉ mang forensic-note
    epoch_p = STATE / f"verdict_epoch_{target}.json"
    if not epoch_p.exists():
        # First compute after cron close = ĐIỂM THI · immutable
        if not dry:
            epoch_p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            _log_local(f"[EPOCH-STAMP] target={target} · first-compute stored · verdict={verdict}")
    else:
        # Subsequent recompute = forensic · không đổi điểm
        epoch_data = json.loads(epoch_p.read_text(encoding="utf-8"))
        if epoch_data.get("verdict") != verdict:
            result["forensic_note"] = f"post-fix recompute · điểm-thi bất-biến giữ verdict={epoch_data['verdict']} (fix ở performer/sender, không đổi grader)"
            result["verdict_at_stamp"] = epoch_data.get("verdict")
            result["stamped_at"] = epoch_data.get("computed_at")
            # Điểm-thi verdict LIVE = epoch verdict (unchanged)
            result["verdict"] = epoch_data["verdict"]
            _log_local(f"[EPOCH-BẤT-BIẾN] target={target} · epoch={epoch_data['verdict']} · new-compute={verdict} · forensic-only")
    if not dry:
        (STATE / "dem0_lan2_verdict.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # V3.5n directive item 2: verdict-computed IN LOG TRƯỚC standing-check
    _log_local(f"[COMPUTE-VERDICT] target={target} · {result['verdict']} · full={n_full}/6 · sent={n_sent}/6 · pin-bộ-niêm={pin_result} · missing_legs={missing_legs} · unk_sent={len(unknown_sentinels)}")
    return result


# V3.5q PREVIEW-JOURNAL + IDEMPOTENT (item 3)
# MASTER-LIVE cutover (KÝ 15/09): preview_journal đóng, master_journal mở từ target ≥ MASTER_LIVE_TARGET.
# Reads iterate cả hai file (union). Writes vào MASTER_JOURNAL sau cutover, PREVIEW_JOURNAL trước.
# Fields, seal, ledger_state giữ nguyên schema.
PREVIEW_JOURNAL = REPO / "data/logs/preview_journal.jsonl"
MASTER_JOURNAL = REPO / "data/logs/master_journal.jsonl"
MASTER_LIVE_TARGET = "2026-09-15"    # target đầu tiên chạy master live


def _journal_iter():
    """Iterate entries từ CẢ preview + master journal (union · idempotent-safe)."""
    for jf in (PREVIEW_JOURNAL, MASTER_JOURNAL):
        if not jf.exists(): continue
        for line in jf.read_text(encoding="utf-8").splitlines():
            try: yield json.loads(line)
            except: pass  # L-66-OK


def preview_journal_check(target: str) -> dict | None:
    """Return last journal entry for target (standing_ok=True) · else None.
    Reads BOTH preview + master journals · idempotent per (renderer=master_preview · target)."""
    last = None
    for e in _journal_iter():
        if e.get("target_date") == target and e.get("standing_ok"):
            last = e
    return last


def preview_journal_append(entry: dict) -> None:
    """Append entry · route by target: post-cutover → MASTER_JOURNAL, else PREVIEW_JOURNAL."""
    target = entry.get("target_date", "")
    jf = MASTER_JOURNAL if target >= MASTER_LIVE_TARGET else PREVIEW_JOURNAL
    jf.parent.mkdir(parents=True, exist_ok=True)
    with jf.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


PREVIEW_EPOCH = "2026-09-10"  # V3.5q item 0 · epoch cho night counter


def _ab3_stuck_check(target: str) -> tuple[int, str]:
    """AB3/U3/18-09 · AC1 fix: dùng _journal_iter() UNION preview+master (cutover 09-15).
    SKIP def: không có entry với sent_ok=True cho renderer master_* (preview hoặc live).
    Pre-D2 entries thiếu `sent_ok` field → mặc định True (giống counter filter L547).
    Đếm ngược từ `target` (inclusive). Đọc lý do từ master_preview.log 26h."""
    from datetime import datetime as _dt3, timedelta as _td3, timezone as _tz3
    sent_days = set()
    for e in _journal_iter():
        if not e.get("renderer", "").startswith("master"): continue
        if e.get("sent_ok", True):  # default True · legacy pre-D2 compat
            sent_days.add(e.get("target_date", ""))
    try:
        target_d = _dt3.strptime(target, "%Y-%m-%d").date()
    except Exception:
        return (0, "")
    streak = 0
    for i in range(0, 15):
        d = (target_d - _td3(days=i)).isoformat()
        if d in sent_days:
            break
        streak += 1
    reason = ""
    log_p = REPO / "data/logs/master_preview.log"
    if log_p.exists():
        _now = _dt3.now(_tz3.utc); _cutoff = _now - _td3(hours=26)
        _ts_re3 = re.compile(r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+\-]\d{2}:\d{2})?)\]")
        latest_ts = None
        for line in log_p.read_text(encoding="utf-8", errors="replace").splitlines():
            m_ts = _ts_re3.match(line)
            if not m_ts: continue
            try:
                ts = _dt3.fromisoformat(m_ts.group(1))
                if ts.tzinfo is None: ts = ts.replace(tzinfo=_tz3.utc)
            except Exception:
                continue
            if ts < _cutoff: continue
            m_err = re.search(r"\[N/A-ERROR:([A-Z0-9\-_/]+)\]", line)
            if m_err and (latest_ts is None or ts >= latest_ts):
                latest_ts = ts
                reason = f"N/A-ERROR:{m_err.group(1)}"
    return (streak, reason)


def _ab3_maybe_alert_stuck(target: str) -> None:
    """AB3/U3 · gọi ở finally · nếu streak ≥ 2, gửi [STUCK: ...]."""
    try:
        streak, reason = _ab3_stuck_check(target)
    except Exception as _e:
        _log(f"[STUCK-CHECK-ERR] {type(_e).__name__}: {_e}")
        return
    if streak < 2: return
    stuck_msg = f"[STUCK: {streak} đêm SKIP liên tiếp · lý do gần nhất: {reason or 'no-error-in-26h'}]"
    ok, det = send_telegram(stuck_msg)
    _log(f"[STUCK-BELL] streak={streak} reason={reason!r} sent={ok} det={det}")


def main():
    # V3.5s GATE-D · D6: header spec_version + amendments_applied
    _log("─── master_preview_send V3.5s pipeline start · spec_version=V3.5s · amendments_applied=[GATE-D] ───")
    # V3.5n · --target CLI override + T-1 default (T = current UTC date)
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", help="Override target date YYYY-MM-DD (default: T-1 UTC)")
    ap.add_argument("--resend", action="store_true", help="V3.5k idempotent override")
    args, _ = ap.parse_known_args()
    if args.target:
        target = args.target
    else:
        target = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    # V3.5n item 2: compute_night_verdict runs + logs BEFORE standing check
    compute_night_verdict(target)
    ok_standing, reason = check_standing()
    _log(f"standing: ok={ok_standing} · {reason}")
    if not ok_standing:
        _log("SKIP · standing not met")
        _ab3_maybe_alert_stuck(target)
        return 0

    target = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    # Pipeline steps · fail-fast
    ok, msg = step_rebuild_ledger(target)
    _log(f"[STEP 1/5 rebuild-ledger] ok={ok} · {msg}")
    if not ok: _log("SKIP · rebuild failed"); _ab3_maybe_alert_stuck(target); return 1

    # J4/17-09 · BẬT LẠI V1.3 · sau khi wire L1+L3+3-tier cap (budget=3680 body-only)
    # Full msg ước 3735-3844 chars · dưới 4096 mọi đêm sample · 09-15 T2 EXCEEDED 3844
    # 3 tầng có audit + D3 pre-check chặn tầng 3 · rollback: cp .bak_v12_run_019276a1
    os.environ["DIGEST_V1_3"] = "1"
    os.environ["DIGEST_U0_BELL_BLOCK"] = "1"   # AD2/19-09 · U0-BELL UNHEDGE block · CAL-ONLY · hold-out 21/10
    os.environ["DIGEST_B_TIER"] = "1"          # AE5-3/19-09 · Khối B ba tầng · CAL-ONLY · hold-out 21/10
    ok, res = step_render_digest(target)
    _log(f"[STEP 2/5 render-digest] ok={ok} · DIGEST_V1_3={os.environ.get('DIGEST_V1_3')} · "
         f"{res[:100] if isinstance(res,str) and ok else res}")
    if not ok: _log("SKIP · render failed"); _ab3_maybe_alert_stuck(target); return 1
    body = res

    ok, msg = step_label_lint(body)
    _log(f"[STEP 3/5 label-lint] ok={ok} · {msg}")
    if not ok: _log("SKIP · lint orphan found"); _ab3_maybe_alert_stuck(target); return 1

    ok, res = step_concat_seal(body)
    _log(f"[STEP 4/5 concat-seal] ok={ok} · {res[:100] if isinstance(res,str) and ok else res}")
    if not ok: _log("SKIP · seal failed"); _ab3_maybe_alert_stuck(target); return 1
    body_sealed = res if isinstance(res, str) and "━━ footer" in res else body

    # AB0/19-09 · U0-BELL audit-only · CALIBRATION · KHÔNG chạm body
    # HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho quyết định ngưỡng trước 21/10.
    try:
        from u0_bell_audit import run_audit as _u0_run_audit
        _body_md5_before = hashlib.md5(body_sealed.encode()).hexdigest()
        _u0_stats = _u0_run_audit(target, log_fn=_log)
        _body_md5_after = hashlib.md5(body_sealed.encode()).hexdigest()
        _log(f"[U0-BELL-AUDIT-CHECK] body_md5_before={_body_md5_before[:12]} · after={_body_md5_after[:12]} · match={_body_md5_before == _body_md5_after}")
        if _body_md5_before != _body_md5_after:
            _log(f"[N/A-ERROR:U0-BELL-AUDIT-MUTATED-BODY] · CRITICAL · DỪNG")
            return 1
    except Exception as _e_audit:
        _log(f"[U0-BELL-AUDIT-ERR] {type(_e_audit).__name__}: {_e_audit} · continue (audit is best-effort)")

    # V3.5q item 3 · IDEMPOTENT preview-sender per (renderer=master_preview · target)
    existing = preview_journal_check(target)
    if existing and not args.resend:
        _log(f"[IDEMPOTENT-SKIP] target={target} · already sent standing_ok · msg_id={existing.get('message_id')} · use --resend to override")
        return 0
    # V3.5q + V3.5s D5 + D2/17-09 · NIGHT-COUNTER filter:
    #   standing_ok ∧ postcheck_ok ∧ sent_ok (mặc định True nếu field vắng · backward-compat)
    #   → đêm send fail (sent_ok=False) KHÔNG tính distinct target.
    distinct_targets = set()
    for e in _journal_iter():
        if (e.get("standing_ok") and e.get("postcheck_ok")
                and e.get("sent_ok", True)   # default True cho entries cũ (pre-D2)
                and e.get("target_date", "") >= PREVIEW_EPOCH):
            distinct_targets.add(e.get("target_date", ""))
    n_after_this = len(distinct_targets | {target})
    # MASTER-LIVE cutover label logic (KÝ 15/09):
    #   target ≥ MASTER_LIVE_TARGET → "[MASTER · live từ 2026-09-15]" (KHÔNG đếm)
    #   target < cutover, n ≤ 2 → "[MASTER-PREVIEW đêm N/2]"
    #   target < cutover, n > 2 → "[ĐỦ 2/2 · CHỜ 'ok master live']" (bug counter chặn: KHÔNG in 3/2, 4/2)
    if target >= MASTER_LIVE_TARGET:
        prefix = "[MASTER · live từ 2026-09-15]\n"
    elif n_after_this <= 2:
        prefix = f"[MASTER-PREVIEW đêm {n_after_this}/2]\n"
    else:
        prefix = "[ĐỦ 2/2 · CHỜ \"ok master live\"]\n"
    full_msg = prefix + body_sealed
    _log(f"[STEP 5/5 send] label={prefix.strip()} · target={target} · night_index={n_after_this} · body_size={len(full_msg)}")
    ok_send, det = send_telegram(full_msg)
    hash12 = hashlib.md5(full_msg.encode()).hexdigest()[:12]
    _log(f"[SENT] master_preview ok={ok_send} {det} hash={hash12} night={n_after_this}/2 target={target}")

    # D2/17-09 · POSTCHECK + JOURNAL_APPEND chạy BẤT KỂ ok_send.
    # Lỗ cũ: nếu API trả 400 (body >4096) thì postcheck+journal bị bọc `if ok_send`
    # → verdict niêm nhưng đêm biến mất khỏi sổ, counter không biết. Sửa: luôn ghi
    # entry với sent_ok + send_error; postcheck vẫn chấm trên artifact có sẵn.
    import re as _re
    mid = None
    m = _re.search(r"message_id=(\d+)", det)
    if m: mid = int(m.group(1))
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from postcheck_gate_d import postcheck as _postcheck
        pc = _postcheck(target)
        _log(f"[POSTCHECK] target={target} · postcheck_ok={pc['postcheck_ok']} · "
             f"p21={pc['p21']} p22={pc['p22']} p27={pc.get('p27','?')} · flag={pc.get('flag','')}")
    except Exception as _e:
        _log(f"[POSTCHECK-ERR] {type(_e).__name__}: {_e}")
        pc = {"postcheck_ok": False, "p21": "ERR", "p22": "ERR", "p27": "ERR",
              "flag": "[POSTCHECK-FAIL exception]"}
    preview_journal_append({
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "renderer": "master_preview" if target < MASTER_LIVE_TARGET else "master_live",
        "target_date": target,
        "channel": "TG_CHAT_ID_DAILY",
        "ok": ok_send,                # legacy field · giữ tương thích
        "http_code": 200 if ok_send else 0,
        "message_id": mid,
        "body_md5": hashlib.md5(full_msg.encode()).hexdigest(),
        "standing_ok": True,
        "postcheck_ok": pc["postcheck_ok"],   # V3.5s D5 · counter filter
        "postcheck_flag": pc.get("flag", ""),
        "night_label": prefix.strip(),   # đúng nhãn in trên tin (đã handle cutover)
        "sent_ok": ok_send,                       # D2/17-09 · counter filter (mới)
        "send_error": "" if ok_send else str(det)[:200],
    })
    # AB3/U3/18-09 · STUCK bell · sau khi journal cập nhật, đếm streak (kể cả tối nay)
    _ab3_maybe_alert_stuck(target)
    return 0 if ok_send else 1


if __name__ == "__main__":
    sys.exit(main())

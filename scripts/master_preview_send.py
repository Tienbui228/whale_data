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
    "harness_lint_marker": STATE / "harness_labellint.marker",
    "veto_marker": STATE / "preview_veto.marker",
    "standing_active": STATE / "standing_active.marker",  # V3.5j · once-opened flag
}
COUNTER_FILE = STATE / "master_preview_counter.json"


def _log(msg):
    LOG_P.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_P.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg, file=sys.stderr)


def check_standing() -> tuple[bool, str]:
    """V3.5j directive item 5 FIX: parse VALUE (verdict==KHÔNG-KÍCH ∧ target đúng đêm)
    · KHÔNG dùng file-exists (kẻo verdict đỏ file tồn tại → tự mở nhầm).
    """
    if STANDING_FILES["veto_marker"].exists():
        return (False, "[N/A-ERROR:VETO] operator dừng preview")
    if STANDING_FILES["standing_active"].exists():
        return (True, "standing already active (pipeline mỗi-đêm)")
    # First-time open · PARSE VALUE (not exists-only)
    if not STANDING_FILES["dem0_verdict"].exists():
        return (False, "[N/A-ERROR:STANDING] dem0_lan2_verdict.json chưa có")
    try:
        v = json.loads(STANDING_FILES["dem0_verdict"].read_text(encoding="utf-8"))
    except Exception as e:
        return (False, f"[N/A-ERROR:STANDING] verdict parse: {e}")
    if v.get("verdict") != "KHÔNG-KÍCH":
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
    # 2 other markers
    if not STANDING_FILES["demo5_marker"].exists():
        return (False, "[N/A-ERROR:STANDING] demo5_sent.marker chưa có")
    if not STANDING_FILES["harness_lint_marker"].exists():
        return (False, "[N/A-ERROR:STANDING] harness_labellint.marker chưa có")
    # OPEN STANDING · create active marker
    STANDING_FILES["standing_active"].write_text(
        f"opened_at={datetime.now(timezone.utc).isoformat()}\n"
        f"verdict_date={verdict_date}\n"
        f"verdict={v.get('verdict')}\n", encoding="utf-8")
    return (True, f"standing FIRST-OPEN · verdict={v.get('verdict')} date={verdict_date} · markers 2/2 · standing_active created")


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
    """Recompute body md5 + verify footer seal khớp."""
    body_no_footer = body
    # Simple check: append recomputed seal to body
    seal = hashlib.md5(body_no_footer.encode("utf-8")).hexdigest()[:12]
    if "concat-seal=" in body:
        # Verify existing seal
        import re
        m = re.search(r"concat-seal=([a-f0-9]{12})", body)
        if m and m.group(1) != seal:
            return (False, f"[N/A-ERROR:SEAL] mismatch existing={m.group(1)} computed={seal}")
        return (True, f"seal verify PASS · {seal}")
    # No footer seal · append one
    body_sealed = body + f"\n\n━━ footer ━━\nconcat-seal={seal}"
    return (True, body_sealed)


def send_telegram(text: str) -> tuple[bool, str]:
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


# V3.5k directive item 6a · compute_night_verdict · máy tự tính+ghi
def compute_night_verdict(target: str) -> dict:
    """Compute verdict {6/6 full-pair · [SENT]×6 từ bell-journal · pin-scan gồm p20-22
    · zero sentinel ngoài khai}. Ghi verdict-file. Chạy đầu pipeline 01:46."""
    art_dir = REPO / "data/artifacts"
    bell = REPO / "data/logs/bell_journal.jsonl"
    renderers = ["tg_relay_gom_h", "fresh_digest", "exch_digest", "gom_daily", "phase_map", "watchlist"]
    # 6/6 full-pair check
    full_pair_status = {}
    for r in renderers:
        txt = art_dir / f"tg_final_{r}_{target}.txt"
        jsonl = art_dir / f"tg_final_{r}_{target}.jsonl"
        if txt.exists() and jsonl.exists():
            n_rows = sum(1 for _ in open(jsonl, encoding="utf-8"))
            full_pair_status[r] = {"txt": txt.stat().st_size, "jsonl_rows": n_rows}
        else:
            full_pair_status[r] = {"missing": True}
    n_full = sum(1 for r in renderers if not full_pair_status[r].get("missing"))
    # [SENT]×6 từ bell-journal
    sent_count = {}
    if bell.exists():
        for line in bell.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("target_date") == target and e.get("ok"):
                    sent_count[e["renderer"]] = True
            except: pass  # L-66-OK (benign fallback)
    n_sent = sum(1 for r in renderers if sent_count.get(r))
    # Pin-scan (p20-p22 harness result)
    import subprocess
    pin_result = None
    try:
        r = subprocess.run([sys.executable, str(REPO / "tests/harness/harness_p20_p22_v3_5k.py")],
                          capture_output=True, text=True, timeout=60)
        pin_result = "PASS" if r.returncode == 0 else "FAIL"
    except Exception as e:
        pin_result = f"ERR:{e}"
    # Sentinel scan (grep [N/A-ERROR:*] outside declared list)
    declared_sentinels = {"N/A-ERROR:DUMP-HALF-FAIL", "N/A-ERROR:DUMP-FAIL",
                          "N/A-ERROR:STANDING", "N/A-ERROR:VETO"}
    unknown_sentinels = []
    for logf in [REPO / "data/logs/master_preview.log", bell]:
        if not logf.exists(): continue
        content = logf.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\[N/A-ERROR:([A-Z0-9\-_/]+)\]", content):
            tag = f"N/A-ERROR:{m.group(1)}"
            if not any(tag.startswith(d) for d in declared_sentinels):
                unknown_sentinels.append(tag)
    # Verdict
    if n_full == 6 and n_sent == 6 and pin_result == "PASS" and not unknown_sentinels:
        verdict = "KHÔNG-KÍCH"
    else:
        verdict = "KÍCH"
    result = {
        "verdict": verdict,
        "evidence_pointer": f"bell_journal + artifacts · computed at {datetime.now(timezone.utc).isoformat()}",
        "date": target,
        "n_full_pair": f"{n_full}/6",
        "n_sent": f"{n_sent}/6",
        "pin_scan_p20_p22": pin_result,
        "unknown_sentinels": unknown_sentinels[:10],
        "full_pair_detail": full_pair_status,
    }
    (STATE / "dem0_lan2_verdict.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"[COMPUTE-VERDICT] {verdict} · full={n_full}/6 · sent={n_sent}/6 · pin={pin_result} · unk_sent={len(unknown_sentinels)}")
    return result


def main():
    _log("─── master_preview_send V3.5k pipeline start ───")
    # V3.5k 6a · compute_night_verdict TRƯỚC standing check (máy tự tính+ghi)
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    compute_night_verdict(yesterday)
    ok_standing, reason = check_standing()
    _log(f"standing: ok={ok_standing} · {reason}")
    if not ok_standing:
        _log("SKIP · standing not met")
        return 0

    target = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    # Pipeline steps · fail-fast
    ok, msg = step_rebuild_ledger(target)
    _log(f"[STEP 1/5 rebuild-ledger] ok={ok} · {msg}")
    if not ok: _log("SKIP · rebuild failed"); return 1

    ok, res = step_render_digest(target)
    _log(f"[STEP 2/5 render-digest] ok={ok} · {res[:100] if isinstance(res,str) and ok else res}")
    if not ok: _log("SKIP · render failed"); return 1
    body = res

    ok, msg = step_label_lint(body)
    _log(f"[STEP 3/5 label-lint] ok={ok} · {msg}")
    if not ok: _log("SKIP · lint orphan found"); return 1

    ok, res = step_concat_seal(body)
    _log(f"[STEP 4/5 concat-seal] ok={ok} · {res[:100] if isinstance(res,str) and ok else res}")
    if not ok: _log("SKIP · seal failed"); return 1
    body_sealed = res if isinstance(res, str) and "━━ footer" in res else body

    n, total = _increment_counter()
    prefix = f"[MASTER-PREVIEW đêm {n}/{total}]\n"
    full_msg = prefix + body_sealed
    _log(f"[STEP 5/5 send] night={n}/{total} · body_size={len(full_msg)}")
    ok_send, det = send_telegram(full_msg)
    hash12 = hashlib.md5(full_msg.encode()).hexdigest()[:12]
    _log(f"[SENT] master_preview ok={ok_send} {det} hash={hash12} night={n}/{total} target={target}")
    # V3.5j directive item 6: write demo5_sent.marker sau khi send OK (idempotent per target)
    if ok_send:
        marker = STATE / "demo5_sent.marker"
        marker.write_text(f"target={target}\nsent_at={datetime.now(timezone.utc).isoformat()}\nhash={hash12}\nnight={n}/{total}\n", encoding="utf-8")
    return 0 if ok_send else 1


if __name__ == "__main__":
    sys.exit(main())

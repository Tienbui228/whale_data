#!/usr/bin/env python3
"""
run_phase_tag.py — cron wrapper cho PHASE-TAG v0.3.3 (chuyến 01:00 UTC / 08:00 VN).

Điều kiện #1 verdict go-live: INCREMENTAL-ONLY.
Full-rebuild bị chặn CỨNG bằng env-var + assert (mẫu gom_scan §8.2, L-34/P0).

Nếu ai đó (bao gồm cron) muốn full-rebuild → phải set env `PHASE_TAG_ALLOW_FULL_REBUILD=1`
và pass flag `--full-rebuild` tường minh. Cron NÊN không bao giờ có flag đó.

Assert cứng ở đầu main() bắt full-rebuild lọt vào cron cmd → RAISE nổ mặt,
exit ≠ 0 → cron log ERROR (như L-44 pattern).
"""
from __future__ import annotations
import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scanner"))

# ── Load .env (same pattern as run_gom_daily.py) ────────────────────────────
_env_path = REPO / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def tg_send(text: str, parse_mode: str = "") -> bool:
    """Send Telegram message (same pattern as run_gom_daily.py::tg_send)."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("WARN: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skip send",
              file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload: dict = {"chat_id": TG_CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode())
            return bool(resp.get("ok"))
    except Exception as exc:
        print(f"TG send failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    now_utc = datetime.now(timezone.utc)
    target_date = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")

    # ── ASSERT §8.2-mirror: cron KHÔNG có quyền viết lại lịch sử ───────────
    # Same pattern as run_gom_daily.py:672 — sys.argv guard for full-rebuild
    argv = sys.argv[1:]

    # --date <YYYY-MM-DD> override + --dry-run (KHÔNG push Telegram)
    dry_run = "--dry-run" in argv
    if "--date" in argv:
        _idx = argv.index("--date")
        if _idx + 1 < len(argv):
            target_date = argv[_idx + 1]
    if "--full-rebuild" in argv:
        # Must have env-var to allow
        if os.environ.get("PHASE_TAG_ALLOW_FULL_REBUILD") != "1":
            print("ERROR: --full-rebuild yêu cầu env PHASE_TAG_ALLOW_FULL_REBUILD=1. "
                  "Cron KHÔNG có quyền full-rebuild (§8.2 mirror, L-34/P0).", file=sys.stderr)
            return 1

    # Cron cmd assert — chặn ai đó vô ý thêm flag vào crontab
    assert "--full-rebuild" not in argv, (
        "ASSERT §8.2 VIOLATED: cron entry (run_phase_tag.py) must never pass "
        "--full-rebuild. Full rebuilds require PHASE_TAG_ALLOW_FULL_REBUILD=1 "
        "và manual invocation."
    )

    # ── [L-74 VIEW-AUTO-REGEN enforcement (c) · KÝ 01/09] · consumer đối chiếu md5+age ─────
    # Was: mtime-only guard 3d (S3 D2). Nâng lên md5-based check per L-74 verbatim ANALYSIS.
    # Header source_md5 + generated_at in view (lắp bởi enforcement b tại _task_gen).
    # Consumer đối chiếu · nếu stale → in [VIEW-STALE age=Xd] inline (không block scan).
    _csm_path = REPO / "docs" / "case_files" / "case_state_map.md"
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from lib.view_stale_check import check_view_stale
        # VPS không có CASE_INDEX.xlsx (sống local Windows) · source_path=None → chỉ check age
        _stale_note = check_view_stale(view_path=_csm_path, source_path=None, max_age_hours=24)
        if _stale_note:
            print(f"WARNING ⚠ {_stale_note} — regen+SCP (state có thể lệch verdict ký).", file=sys.stderr)
            try:
                from whale_collector.alert import telegram_error
                telegram_error(f"case_state_map {_stale_note}")
            except Exception as _exc:
                print(f"  (telegram_error not wired: {_exc})", file=sys.stderr)
    except ImportError as _exc:
        # L-66 sentinel · fallback to mtime-only if view_stale_check unavailable
        print(f"[N/A-ERROR:VIEW-STALE-CHECK-IMPORT] {_exc} · fallback mtime-only guard", file=sys.stderr)
        if _csm_path.exists():
            import time as _t
            _age_d = (_t.time() - _csm_path.stat().st_mtime) / 86400.0
            if _age_d > 3:
                print(f"WARNING ⚠ [VIEW-STALE mtime-fallback age={_age_d:.1f}d]", file=sys.stderr)

    # ── Load state (case_state_map + freshwatch) ───────────────────────────
    # INCREMENTAL: chỉ chạy tag() cho target_date, KHÔNG rebuild history.
    # Import freshwatch loader trực tiếp (không qua replay_phase để tránh
    # bot-signals dependency).
    import yaml
    import csv
    import math
    from scanner.phase_tag import tag
    sys.path.insert(0, str(REPO / "scripts"))
    from fw_loader_utils import taker_scale_check, enrich_token_days

    # Locate bot-signals thresholds.yaml — try common paths (local Win / VPS Linux)
    _bot_candidates = [
        Path(r"D:\Data back test\binance-bot-signals"),
        Path("/root/Data_back_test/binance-bot-signals"),
        Path.home() / "Data_back_test" / "binance-bot-signals",
    ]
    BOT_REPO = next((p for p in _bot_candidates
                     if (p / "scanner" / "screener" / "thresholds.yaml").exists()), None)
    if BOT_REPO is None:
        print(f"ERROR: bot-signals thresholds.yaml not found in candidates: "
              f"{[str(p) for p in _bot_candidates]}", file=sys.stderr)
        return 1
    CFG = yaml.safe_load(open(BOT_REPO / "scanner" / "screener" / "thresholds.yaml",
                              encoding="utf-8"))

    def load_days(sym_usdt):
        rows = []
        for p in sorted((REPO / "data" / "export").glob("freshwatch_daily_*.csv")):
            with open(p, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get("symbol") != sym_usdt: continue
                    def _f(v):
                        if v is None or str(v).strip()=="": return float("nan")
                        try: x=float(v); return float("nan") if math.isnan(x) else x
                        except: return float("nan")
                    try: fn = int(float(r.get("funding_n") or 0))
                    except: fn = 0
                    rows.append({
                        "date":r["date"], "lsr_pos":_f(r.get("lsr_pos_r")),
                        "lsr_acc":_f(r.get("lsr_acc_r")), "lsr_global":_f(r.get("lsr_global_r")),
                        "taker_ratio":_f(r.get("taker_ratio")), "taker_buy_pct":_f(r.get("taker_buy_pct")),
                        "vol_quote":_f(r.get("vol_quote")), "avg_px":_f(r.get("px_avg")),
                        "oi_usd":_f(r.get("oi_usd")), "funding_avg":_f(r.get("funding_avg")),
                        "funding_min":_f(r.get("funding_min")), "funding_max":_f(r.get("funding_max")),
                        "funding_n":fn,
                    })
        rows.sort(key=lambda x: x["date"])
        if rows:
            raw = [r["taker_buy_pct"] for r in rows]
            scale = taker_scale_check(sym_usdt, raw)
            if scale != 1.0:
                for r in rows:
                    if not math.isnan(r["taker_buy_pct"]):
                        r["taker_buy_pct"] *= scale
            enrich_token_days(rows)
        return rows

    def find_day(days, dt):
        for i,d in enumerate(days):
            if dt in d.get("date","") or d.get("date","").endswith(dt): return i
        return -1

    # case_state map from JSON block in case_state_map.md
    import re, json as _json
    _CS = {}
    _csm = REPO / "docs" / "case_files" / "case_state_map.md"
    if _csm.exists():
        m = re.search(r"```json\s*(\{.*?\})\s*```", _csm.read_text(encoding="utf-8"), re.DOTALL)
        if m:
            try:
                _CS = _json.loads(m.group(1))
            except _json.JSONDecodeError as _cse_exc:
                # [F3.2 19/08] WARN + telegram + tiếp — KHÔNG nuốt câm.
                # JSON corrupt → _CS rỗng → STATE-CONFLICT block TRỐNG âm thầm.
                # KHÔNG raise: scan phải chạy tiếp (S2/S3 tags vẫn có ích).
                _msg = (f"⚠ case_state_map.md JSON parse FAIL: {_cse_exc}. "
                        f"STATE-CONFLICT block sẽ TRỐNG. Ký lại json trong "
                        f"case_state_map.md.")
                print(f"WARNING {_msg}", file=sys.stderr)
                try:
                    from whale_collector.alert import telegram_error
                    telegram_error(_msg)
                except Exception as _tg_exc:
                    print(f"  (telegram_error not wired: {_tg_exc})", file=sys.stderr)
    def _case_state_for(tok): return _CS.get(tok)

    # Universe: freshwatch fw-139 (per spec §2)
    fw_path = REPO / "data" / "config" / "freshwatch_symbols.txt"
    if not fw_path.exists():
        print(f"ERROR: {fw_path} missing — L-44 fail-loud (như L-41 pattern)",
              file=sys.stderr)
        return 1

    with open(fw_path, encoding="utf-8") as f:
        universe = [s.strip() for s in f if s.strip()]

    print(f"[phase_tag] date={target_date} universe={len(universe)} tokens INCREMENTAL")

    # Per-token tag for target_date only
    from scanner.tg_render import render_5_blocks   # NEW module
    from scanner.phase_tag import _herd_return       # [7d] AIN watch hook

    rows = []
    days_map = {}   # for hedge-split B1/B2 detection
    logs_dir = REPO / "data" / "logs"
    logs_dir.mkdir(exist_ok=True, parents=True)
    ain_watch_log      = logs_dir / "ain_herd_return_watch.log"
    s2_forward_log     = logs_dir / "s2_forward_watch.log"       # [H1] falsifier ①
    s2midup_validate_log = logs_dir / "s2midup_validate.log"     # [H2] falsifier ②

    # Initialize log headers if new files
    if not s2_forward_log.exists():
        s2_forward_log.write_text(
            "# S2* forward-watch — falsifier ① (§10): ≥3 case S2*→S4 hồi tố → ANALYSIS-ONLY\n"
            "# Format: date\\ttoken\\tstage\\toutcome_30d (TRỐNG chờ hồi tố)\n"
            "date\ttoken\tstage\toutcome_30d\n",
            encoding="utf-8")
    if not s2midup_validate_log.exists():
        s2midup_validate_log.write_text(
            "# S2-MID↑ validate — falsifier ② (v0.4 demote nếu không dẫn tới campaign)\n"
            "# Format: date\\ttoken\\tled_to_campaign (TRỐNG chờ 60d)\n"
            "date\ttoken\tled_to_campaign\n",
            encoding="utf-8")

    for sym_usdt in universe:
        tok = sym_usdt.replace("USDT", "")
        try:
            days = load_days(sym_usdt)
            if not days: continue
            i = find_day(days, target_date)
            if i < 0: continue
            r = tag(days, i, CFG, case_state=_case_state_for(tok))
            r["token"] = tok
            rows.append(r)
            days_map[tok] = (days, i)
            stage = r.get("stage") or ""

            # [7d] AIN watch — log herd_return live tuần đầu (điều kiện #4)
            if tok == "AIN":
                hr = _herd_return(days, i, threshold=0.80, window=14)
                with open(ain_watch_log, "a", encoding="utf-8") as f:
                    f.write(f"{target_date}\tAIN\therd_return={hr}\t"
                            f"stage={r.get('stage')}\tevent_tag={r.get('event_tag')}\n")

            # [H1] Falsifier hook ① — S2* outcome tracking (30d forward)
            # ANALYSIS đọc log 30d sau, bắn ① nếu ≥3 case S2*→S4 hồi tố
            if stage.startswith("S2"):
                with open(s2_forward_log, "a", encoding="utf-8") as f:
                    f.write(f"{target_date}\t{tok}\t{stage}\t\n")   # outcome_30d TRỐNG

            # [H2] Falsifier hook ② — S2-MID↑ validate (60d forward)
            # v0.4 demote nếu S2-MID↑ không dẫn tới campaign trong 60d
            if stage == "S2-MID↑":
                with open(s2midup_validate_log, "a", encoding="utf-8") as f:
                    f.write(f"{target_date}\t{tok}\t\n")   # led_to_campaign TRỐNG

        except Exception as exc:
            print(f"  [warn] {tok}: {exc}")

    # ── [F1-20260819] WRITE phase_tag_daily.csv (append-only, forward-only) ────
    # Spec canonical: docs/proposals/phase_tag_spec_v0.3.md:142
    # Cột: date · token · stage · stage_conf · stage_evidence · stage_flags
    #     · event_tag · wash_count_30d · herd_return · case_state · state_conflict
    # (operator_stage_hint = None per spec — máy KHÔNG đọc)
    # Chạy CẢ dry-run (verify được) — chỉ Telegram push mới skip. Dry-run ghi
    # vào file suffix _DRYRUN.csv để KHÔNG ô nhiễm sổ canonical.
    _csv_name = "phase_tag_daily_DRYRUN.csv" if dry_run else "phase_tag_daily.csv"
    csv_out = REPO / "data" / "screener" / _csv_name
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    _fields = ["date", "token", "stage", "stage_conf", "stage_evidence",
               "stage_flags", "event_tag", "wash_count_30d", "herd_return",
               "case_state", "state_conflict"]
    _is_new = not csv_out.exists()
    with open(csv_out, "a", newline="", encoding="utf-8") as _fp:
        _w = csv.DictWriter(_fp, fieldnames=_fields)
        if _is_new:
            _w.writeheader()
        for _r in rows:
            _row = {}
            for _k in _fields:
                _v = _r.get(_k)
                if isinstance(_v, list):
                    _v = "|".join(str(x) for x in _v)
                _row[_k] = _v if _v is not None else ""
            _w.writerow(_row)
    print(f"[csv] appended {len(rows)} rows → {csv_out}"
          + (" (created)" if _is_new else ""),
          file=sys.stderr)

    # Render Telegram 5-blocks
    msg = render_5_blocks(rows, target_date, days_map=days_map)
    print(msg)

    # [L1] Push Telegram thật (skip khi --dry-run)
    if dry_run:
        print("\n[dry-run] KHÔNG push Telegram — stdout only "
              "(CSV ghi vào _DRYRUN.csv để verify)", file=sys.stderr)
        return 0
    # Plain text (no parse_mode) — 5-block emoji render tốt hơn Markdown escape
    ok = tg_send(msg, parse_mode="")
    _target = target_date
    # V3.5i [SENT] MARKER CHUẨN (directive REV10 item 4 · L-59)
    import hashlib as _hl
    _tg_hash = _hl.md5(msg.encode("utf-8")).hexdigest()[:12]
    print(f"[SENT] phase_map ok={ok} HTTP {'200' if ok else 'X'} hash={_tg_hash} target={_target}")
        from lib.artifact_dump import log_bell
    try:
        log_bell("phase_map", _target, "old", ok, 200 if ok else 0, None, msg)
    except Exception as _e: print(f"[N/A-ERROR:LOG-BELL] {_e}")
    # [ARTIFACT-DUMP as-sent · V1.4 sentinel]
    if ok:
        try:
            sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
            from lib.artifact_dump import dump_as_sent as _das
            _ok, _det = _das("phase_map", _target, msg, channel="old")
            print(f"[ARTIFACT-DUMP phase_map] {_ok} · {_det}")
        except RuntimeError as _de: print(f"[ARTIFACT-DUMP-SENTINEL phase_map] {_de}", file=sys.stderr)
        except Exception as _e: print(f"[ARTIFACT-DUMP-ERR phase_map] {type(_e).__name__}: {_e}", file=sys.stderr)
    if not ok:
        print("ERROR: Telegram send failed", file=sys.stderr)
        return 1
    print(f"\n[telegram] sent to chat_id={TG_CHAT_ID} ({len(msg)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

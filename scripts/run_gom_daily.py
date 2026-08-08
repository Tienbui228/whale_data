#!/usr/bin/env python3
"""GOM daily runner — wraps gom_scan.py --daily + Telegram report.

Entry point for cron 01:00 UTC on VPS.
Missing dependency → ERROR + Telegram alert + exit 1  (L-44 spec).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent          # /root/Data_back_test/whale_data
SCRIPTS = REPO / "scripts"
STORE   = REPO / "data" / "export"
CONFIG  = REPO / "data" / "config"
STATE_PATH   = REPO / "data" / "gom_state.json"
THRESH_PATH  = REPO / "screen_thresholds.yaml"
FW_SYM_PATH  = CONFIG / "freshwatch_symbols.txt"
HB_PATH      = REPO / "data" / "gom_heartbeat.txt"
LOG_PATH     = REPO / "data" / "logs" / "gom_daily.log"

# ── Load .env ─────────────────────────────────────────────────────────────────
_env_path = REPO / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


# ── Telegram helpers ──────────────────────────────────────────────────────────

def tg_send(text: str, parse_mode: str = "") -> bool:
    """Send Telegram message. Returns True on success."""
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


def tg_error(msg: str) -> None:
    """Send error alert and exit 1."""
    tg_send(f"❌ GOM DAILY ERROR\n{msg}")
    print(f"ERROR: {msg}", file=sys.stderr)
    _log(f"ERROR: {msg}")
    sys.exit(1)


# ── Logging ───────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {msg}\n")


# ── Dependency gate ───────────────────────────────────────────────────────────

def check_deps(target_date: str) -> None:
    """Check all required dependencies. Any failure → tg_error (exits 1)."""
    errors = []

    # 1. screen_thresholds.yaml
    if not THRESH_PATH.exists():
        errors.append(f"screen_thresholds.yaml missing: {THRESH_PATH}")

    # 2. freshwatch_symbols.txt
    if not FW_SYM_PATH.exists():
        errors.append(f"freshwatch_symbols.txt missing: {FW_SYM_PATH}")

    # 3. freshwatch CSV for target month
    month_str = target_date[:7]
    csv_path = STORE / f"freshwatch_daily_{month_str}.csv"
    if not csv_path.exists():
        errors.append(f"freshwatch_daily_{month_str}.csv missing: {csv_path}")

    # 4. Previous month CSV (needed for lookback window)
    prev_month = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m")
    prev_csv = STORE / f"freshwatch_daily_{prev_month}.csv"
    if not prev_csv.exists():
        errors.append(f"prev-month CSV missing: {prev_csv} (needed for 60d lookback)")

    # 5. gom_scan.py
    gom_scan = SCRIPTS / "gom_scan.py"
    if not gom_scan.exists():
        errors.append(f"gom_scan.py missing: {gom_scan}")

    if errors:
        tg_error("Dependency gate FAIL:\n" + "\n".join(f"  • {e}" for e in errors))


# ── Report formatter ──────────────────────────────────────────────────────────

def _closed_section(state: dict, fw_base: set, target_date: str) -> str:
    """Format top 15 closed chains from last 60 days, sorted by Q1 desc."""
    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        cutoff = target_dt - timedelta(days=60)
    except ValueError:
        return ""

    # Current prices from freshwatch CSV (avg_px on target_date)
    px_map: dict[str, float] = {}
    try:
        month_str = target_date[:7]
        csv_path = STORE / f"freshwatch_daily_{month_str}.csv"
        if csv_path.exists():
            import csv as _csv
            with open(csv_path, encoding="utf-8") as f:
                for row in _csv.DictReader(f):
                    if row.get("date") == target_date:
                        sym = row.get("symbol", "")
                        base = sym[:-4] if sym.endswith("USDT") else sym
                        try:
                            px_map[base] = float(row.get("px_avg", "") or "nan")
                        except (ValueError, TypeError):
                            pass
    except Exception:
        pass

    closed: list[tuple[str, dict]] = []
    for tok, ch in state.items():
        if tok not in fw_base or ch.get("chain_open"):
            continue
        close_d = ch.get("close_date", "")
        if not close_d:
            continue
        try:
            if datetime.strptime(close_d[:10], "%Y-%m-%d") < cutoff:
                continue
        except ValueError:
            continue
        closed.append((tok, ch))

    if not closed:
        return ""

    closed.sort(key=lambda x: x[1].get("Q1_cum_usd", 0), reverse=True)
    closed = closed[:15]

    rows = ["", "CHƯƠNG ĐÃ ĐÓNG (60d):"]
    for tok, ch in closed:
        q1    = ch.get("Q1_cum_usd", 0.0)
        nd    = ch.get("n_days", 0)
        start = ch.get("start_date", "?")[-5:]
        close = ch.get("close_date", "?")[-5:]
        vnum  = ch.get("vwap_num", 0.0)
        vden  = ch.get("vwap_den", 0.0)
        vwap  = vnum / vden if vden > 0 else math.nan
        chp   = ch.get("chapter", 1)

        reason_raw = ch.get("close_reason", "")
        if ch.get("close_note") == "chuyển pha phân phối" or "pos_r_drop" in reason_raw:
            cat = "rule-iv"
        elif "suppressor" in reason_raw or "dq_cooldown" in reason_raw:
            cat = "supp"
        else:
            cat = "gap"

        q1s    = f"${q1/1_000:.0f}k" if q1 >= 1_000 else "$0"
        vwap_s = f"${vwap:.5f}" if not math.isnan(vwap) else "N/A"

        px_vs = ""
        if not math.isnan(vwap) and vwap > 0:
            px = px_map.get(tok, math.nan)
            if not math.isnan(px):
                pct = (px - vwap) / vwap * 100
                arrow = "↑" if pct >= 0 else "↓"
                px_vs = f" {arrow}{abs(pct):.1f}%vsVWAP"

        rows.append(
            f"  {tok} ch{chp} {start}→{close} n={nd} Q1={q1s} VWAP={vwap_s} [{cat}]{px_vs}"
        )

    return "\n".join(rows)


def format_tg_report(stdout: str, target_date: str, run_utc: str) -> str:
    """Parse gom_scan stdout → compact Telegram message."""
    lines = stdout.splitlines()

    # Extract open chains block
    open_chains: list[str] = []
    in_open = False
    closed_today: list[str] = []
    smissing_today_n: int = 0
    smissing_hist_n:  int = 0

    for line in lines:
        if "OPEN CHAINS" in line:
            in_open = True
            continue
        if line.startswith("━━ CLOSED TODAY:"):
            in_open = False
            closed_part = line.replace("━━ CLOSED TODAY:", "").strip()
            if closed_part:
                closed_today = [t.strip() for t in closed_part.split(",") if t.strip()]
            continue
        if line.startswith("━━ S-MISSING TODAY"):
            in_open = False
            # "━━ S-MISSING TODAY (N) ..." or "━━ S-MISSING TODAY: 0 ✓"
            import re as _re
            m = _re.search(r"S-MISSING TODAY[:\s]+(\d+)", line)
            if m:
                smissing_today_n = int(m.group(1))
            continue
        if line.startswith("━━ S-MISSING HIST"):
            in_open = False
            import re as _re
            m = _re.search(r"S-MISSING HIST[:\s]+\((\d+)\)", line)
            if m:
                smissing_hist_n = int(m.group(1))
            continue
        if line.startswith("━━ S-MISSING"):
            in_open = False
            continue
        if line.startswith("── NOTES"):
            in_open = False
            continue
        if in_open and line.startswith("══"):
            # Token header line
            token = line.replace("══", "").strip().rstrip("═").strip()
            open_chains.append(token)

    # Extract summary line
    summary = ""
    for line in lines:
        if "open /" in line and "symbols scanned" in line:
            summary = line.strip()
            break

    # Parse open chains from state to get Q1 / start / n
    chain_details: list[str] = []
    _state_full: dict = {}
    _fw_base: set = set()
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                _state_full = json.load(f)
            fw_list = [l.strip() for l in FW_SYM_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
            _fw_base = {s[:-4] if s.endswith("USDT") else s for s in fw_list}
            open_st = {t: c for t, c in _state_full.items()
                       if c.get("chain_open") and t in _fw_base}
            sorted_chains = sorted(open_st.items(),
                                   key=lambda x: x[1].get("Q1_cum_usd", 0), reverse=True)
            for tok, ch in sorted_chains:
                q1  = ch.get("Q1_cum_usd", 0.0)
                nd  = ch.get("n_days", 0)
                bk  = ch.get("break_streak", 0)
                st  = ch.get("start_date", "?")[-5:]  # MM-DD
                chp = ch.get("chapter", 1)
                q1s = f"${q1/1_000:.0f}k" if q1 >= 1000 else "$0"
                flag = "★" if q1 > 2_000_000 else " "
                bk_s = f" brk={bk}" if bk > 0 else ""
                chain_details.append(
                    f"{flag} {tok} ch{chp} start={st} n={nd}{bk_s} Q1={q1s}"
                )
        except Exception as exc:
            chain_details.append(f"(state parse error: {exc})")

    n_open = len(chain_details)
    stars = [l for l in chain_details if l.startswith("★")]

    msg_lines = [
        f"📊 GOM Daily — {target_date} ({run_utc} UTC)",
        f"Universe: fw137@139 | Formula: A1∧A2∧A3∧(A4∨A5) | B1∧(B2∨B3)∧B4",
        f"",
        f"OPEN ({n_open}/139):",
    ]
    msg_lines += [f"  {c}" for c in chain_details] if chain_details else ["  (none)"]

    if stars:
        msg_lines.append(f"★ Q1>$2M: {', '.join(t.split()[1] for t in stars)}")
    else:
        msg_lines.append("★ Q1>$2M: NONE")

    if closed_today:
        closed_str = ", ".join(closed_today[:10])
        if len(closed_today) > 10:
            closed_str += f" (+{len(closed_today)-10})"
        msg_lines.append(f"CLOSED TODAY: {closed_str}")

    if smissing_today_n > 0:
        msg_lines.append(f"⚠ S-MISS TODAY: {smissing_today_n} — check export timing!")
    else:
        msg_lines.append(f"S-MISS today: 0 ✓")
    if smissing_hist_n > 0:
        msg_lines.append(f"S-MISS hist: {smissing_hist_n} (short history, normal)")

    # Closed chains (60d window)
    closed_sec = _closed_section(_state_full, _fw_base, target_date)
    if closed_sec:
        msg_lines.append(closed_sec)

    msg_lines += [
        "",
        "PARTI [status pending] | ZBT perp sống",
        summary if summary else f"[{n_open} open / 139 scanned]",
    ]

    return "\n".join(msg_lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    run_utc = datetime.now(timezone.utc).strftime("%H:%M")
    target_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    _log(f"run_start date={target_date}")

    # Dependency gate
    check_deps(target_date)

    # Run gom_scan --daily
    gom_scan = SCRIPTS / "gom_scan.py"
    cmd = [
        sys.executable, str(gom_scan),
        "--daily",
        "--store", str(STORE),
        "--date", target_date,
        "--fw-filter", str(FW_SYM_PATH),
    ]

    _log(f"exec: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                            timeout=300)

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if result.returncode != 0:
        err_snippet = (stderr or stdout)[:500]
        tg_error(f"gom_scan exit={result.returncode}\n{err_snippet}")

    # Heartbeat
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    HB_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")

    # Format and send Telegram report
    report = format_tg_report(stdout, target_date, run_utc)
    ok = tg_send(report)

    _log(f"tg_send={'OK' if ok else 'FAIL'}  open_chains_reported={report.count(chr(10)+'  ')}")

    print(stdout)
    if stderr:
        print("STDERR:", stderr[:200], file=sys.stderr)

    _log(f"run_complete exit=0")


if __name__ == "__main__":
    main()

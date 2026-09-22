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

    def _cat(ch: dict) -> str:
        reason_raw = ch.get("close_reason", "")
        if (ch.get("close_note") == "chuyển pha phân phối"
                or "pos_r_drop" in reason_raw
                or ch.get("retro_tag")):  # retro-tagged gap → promoted to rule-iv tier
            return "rule-iv"
        if "suppressor" in reason_raw or "dq_cooldown" in reason_raw:
            return "supp"
        return "gap"

    # Sort: rule-iv first (bất kể Q1) — "gom xong rồi CHUYỂN PHA" là dòng anh cần thấy nhất
    # Within each category: sort by Q1 desc (seat-rotation tokens have low Q1 but still rule-iv)
    _cat_order = {"rule-iv": 0, "supp": 1, "gap": 2}
    closed.sort(key=lambda x: (_cat_order[_cat(x[1])], -x[1].get("Q1_cum_usd", 0)))
    closed = closed[:15]

    rows = ["", "CHƯƠNG ĐÃ ĐÓNG (60d):"]
    for tok, ch in closed:
        q1    = ch.get("Q1_cum_usd", 0.0)
        nd    = ch.get("n_days", 0)
        start = ch.get("start_date", "?")[-5:]
        close = ch.get("close_date", "?")[-5:]
        vnum  = ch.get("vwap_num", 0.0)
        vden  = ch.get("vwap_den", 0.0)
        ois   = ch.get("oi_start_usd", 0.0) or 0.0
        _t1ok = vden > 0 and (ois <= 0 or vden >= 0.05 * ois)
        if _t1ok:
            vwap    = vnum / vden
            vwap_t2 = False
        else:
            _vvn = ch.get("vwap_vol_num", 0.0)
            _vvd = ch.get("vwap_vol_den", 0.0)
            vwap    = _vvn / _vvd if _vvd > 0 else math.nan
            vwap_t2 = _vvd > 0
        chp   = ch.get("chapter", 1)
        cat   = _cat(ch)

        # peak_pos_r — proxy for "bao nhiêu long đã build vào"
        peak_pr = ch.get("peak_pos_r", math.nan)
        pr_s = f" pr={peak_pr:.2f}" if not math.isnan(peak_pr) else ""

        # Build-type: seat-rotation (Q1 nhỏ vì OI flat, nhưng pos_r leo) vs Q1-driven
        if not math.isnan(peak_pr) and peak_pr > 1.4 and q1 < 80_000:
            build_s = " [seat-rot]"
        else:
            build_s = ""

        q1s    = f"${q1/1_000:.0f}k" if q1 >= 1_000 else "$0"
        vwap_s = (f"${vwap:.5f}[vw-vol]" if (not math.isnan(vwap) and vwap_t2)
                  else f"${vwap:.5f}" if not math.isnan(vwap)
                  else "N/A")

        px_vs = ""
        if not math.isnan(vwap) and vwap > 0:
            px = px_map.get(tok, math.nan)
            if not math.isnan(px):
                pct = (px - vwap) / vwap * 100
                arrow = "↑" if pct >= 0 else "↓"
                px_vs = f" {arrow}{abs(pct):.1f}%vsVWAP"

        retro = ch.get("retro_tag", "")
        retro_s = f" [retro {retro[-5:]}]" if retro else ""
        rows.append(
            f"  {tok} ch{chp} {start}→{close} n={nd} Q1={q1s}{pr_s} VWAP={vwap_s} [{cat}]{retro_s}{build_s}{px_vs}"
        )

    return "\n".join(rows)


def format_tg_report(stdout: str, target_date: str, run_utc: str, run_date: str = "") -> str:
    """Parse gom_scan stdout → compact Telegram message."""
    lines = stdout.splitlines()

    # Extract open chains block
    open_chains: list[str] = []
    in_open = False
    closed_today: list[str] = []
    smissing_today_n: int = 0
    smissing_hist_n:  int = 0
    gomc_beta_line: str = ""
    gomc_beta_stats: list[str] = []
    gomc_beta_supp:  list[str] = []

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
        if line.startswith("━━ GOM-C β STAT:"):
            gomc_beta_stats.append(line.replace("━━ GOM-C β STAT:", "").strip())
            continue
        if line.startswith("━━ GOM-C β SUPP:"):
            gomc_beta_supp.append(line.replace("━━ GOM-C β SUPP:", "").strip())
            continue
        if "━━ GOM-C β" in line:
            in_open = False
            gomc_beta_line = line.strip().lstrip("━ ")
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

    # Parse open chains from state to get Q1 / VWAP / px
    chain_details: list[str] = []
    _state_full: dict = {}
    _fw_base: set = set()
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                _state_full = json.load(f)
            fw_list = [l.strip() for l in FW_SYM_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
            _fw_base = {s[:-4] if s.endswith("USDT") else s for s in fw_list}

            # px_map for target_date (for VWAP Δ% display)
            _px_map: dict[str, float] = {}
            try:
                import csv as _csv_tg
                _cp = STORE / f"freshwatch_daily_{target_date[:7]}.csv"
                if _cp.exists():
                    with open(_cp, encoding="utf-8") as _fc:
                        for _row in _csv_tg.DictReader(_fc):
                            if _row.get("date") == target_date:
                                _s = _row.get("symbol", "")
                                _b = _s[:-4] if _s.endswith("USDT") else _s
                                try:
                                    _px_map[_b] = float(_row.get("px_avg", "") or "nan")
                                except (ValueError, TypeError):
                                    pass
            except Exception:
                pass

            # M2: load rep-threshold from screen_thresholds.yaml (5% default)
            _vwap_rep_frac = 0.05
            try:
                import yaml as _yaml_tg
                _sc_raw = _yaml_tg.safe_load(THRESH_PATH.read_text(encoding="utf-8"))
                if isinstance(_sc_raw, dict):
                    _g = _sc_raw.get("gom", _sc_raw)
                    _vwap_rep_frac = float(_g.get("vwap_t1_min_rep_frac", 0.05))
            except Exception:
                pass

            open_st = {t: c for t, c in _state_full.items()
                       if c.get("chain_open") and t in _fw_base}

            # ── Build per-token info dict ─────────────────────────────────────
            # verdict 17/08 net-semantics (operator signed):
            #   net_oi_window_usd = ungated window [reality-check, KHÔNG lực gom]
            #   net_gated_usd     = gom-doctrine net (Σ ΔOI on counts_q1 days). n_q1=0 → NaN.
            # Legacy alias net_oi_delta_usd mirrors net_oi_window_usd (drop 2026-09-17).
            def _build_entry(tok, ch):
                q1      = ch.get("Q1_cum_usd", 0.0)
                net_win = ch.get("net_oi_window_usd", ch.get("net_oi_delta_usd", math.nan))
                net_gat = ch.get("net_gated_usd", math.nan)
                nd      = ch.get("n_days", 0)   # n_q1: qualifying-day count
                bk      = ch.get("break_streak", 0)
                chp     = ch.get("chapter", 1)
                q1s     = f"${q1/1_000:.0f}k" if q1 >= 1_000 else "$0"
                bk_s    = f" bk={bk}" if bk > 0 else ""

                def _fmt_money(v):
                    if math.isnan(v): return "N/A"
                    a = abs(v); s = "+" if v > 0 else ("-" if v < 0 else "")
                    return f"{s}${a/1_000:.0f}k" if a >= 1_000 else f"{s}${a:.0f}"

                net_win_s = _fmt_money(net_win)
                net_gat_s = "NaN" if math.isnan(net_gat) else _fmt_money(net_gat)
                _vn    = ch.get("vwap_num", 0.0)
                _vd    = ch.get("vwap_den", 0.0)
                _oi_st = ch.get("oi_start_usd", 0.0) or 0.0
                _t1_ok = _vd > 0 and (_oi_st <= 0 or _vd >= _vwap_rep_frac * _oi_st)
                if _t1_ok:
                    _vv = _vn / _vd
                else:
                    _vvn = ch.get("vwap_vol_num", 0.0)
                    _vvd = ch.get("vwap_vol_den", 0.0)
                    _vv  = _vvn / _vvd if _vvd > 0 else math.nan
                _px = _px_map.get(tok, math.nan)
                px_s = f"{_px:.4f}" if not math.isnan(_px) else "N/A"
                if not math.isnan(_px) and not math.isnan(_vv) and _vv > 0:
                    _pct = (_px - _vv) / _vv * 100
                    dpct_s = f"Δ={'+'if _pct>=0 else ''}{_pct:.1f}%vsVWAP"
                else:
                    dpct_s = "Δ=N/A"
                return dict(tok=tok, chp=chp, nd=nd, bk_s=bk_s,
                            q1=q1, q1s=q1s,
                            net_win=net_win, net_win_s=net_win_s,
                            net_gat=net_gat, net_gat_s=net_gat_s,
                            px_s=px_s, dpct_s=dpct_s)

            # verdict 17/08: classify by net_gated (n_q1≥1 required for "gom" wording).
            # n_q1=0 → NO-QUALIFIED bucket, CẤM chữ "gom" per template rule.
            ron_entries    = []   # n_q1≥1 AND net_gated>0
            churn_entries  = []   # n_q1≥1 AND net_gated≤0
            noqual_entries = []   # n_q1=0 (net_gated=NaN, chưa evaluable)

            for tok, ch in open_st.items():
                e = _build_entry(tok, ch)
                if e["nd"] == 0 or math.isnan(e["net_gat"]):
                    noqual_entries.append(e)
                elif e["net_gat"] > 0:
                    ron_entries.append(e)
                else:
                    churn_entries.append(e)

            ron_entries.sort(key=lambda x: -x["net_gat"])
            churn_entries.sort(key=lambda x: -x["net_gat"])
            noqual_entries.sort(key=lambda x: -(x["net_win"] if not math.isnan(x["net_win"]) else float("-inf")))

            def _ron_line(e):
                flags = " [Q1=0]" if e["q1"] == 0 else ""
                return (f"  {e['tok']}  ch{e['chp']} n={e['nd']}{e['bk_s']}"
                        f"  Q1={e['q1s']}  net_gated={e['net_gat_s']}"
                        f"  net_window={e['net_win_s']}"
                        f"  px={e['px_s']}  {e['dpct_s']}{flags}")

            def _churn_line(e):
                flags = "[Q1=0][churn]" if e["q1"] == 0 else "[churn]"
                star  = f"  ★Q1={e['q1s']}" if e["q1"] >= 2_000_000 else ""
                return (f"  {e['tok']}  ch{e['chp']} n={e['nd']}{e['bk_s']}"
                        f"  net_gated={e['net_gat_s']}  net_window={e['net_win_s']}"
                        f"  px={e['px_s']}  {e['dpct_s']}  {flags}{star}")

            def _noqual_line(e):
                # CẤM chữ "gom" — chain chưa ngày qualifying, chưa xét doctrine.
                return (f"  {e['tok']}  ch{e['chp']} n_q1=0{e['bk_s']}"
                        f"  net_window={e['net_win_s']} [reality-check, ungated]"
                        f"  net_gated=NaN"
                        f"  px={e['px_s']}  {e['dpct_s']}"
                        f"  [NO-QUALIFIED-DAYS]")

            ron_lines    = [_ron_line(e)    for e in ron_entries]
            churn_lines  = [_churn_line(e)  for e in churn_entries]
            noqual_lines = [_noqual_line(e) for e in noqual_entries]
            chain_details = ron_lines + churn_lines + noqual_lines
        except Exception as exc:
            ron_lines     = [f"(state parse error: {exc})"]
            churn_lines   = []
            noqual_lines  = []
            chain_details = ron_lines

    n_ron    = len(ron_lines)
    n_churn  = len(churn_lines)
    n_noqual = len(noqual_lines)
    n_open   = n_ron + n_churn + n_noqual

    msg_lines = [
        f"📊 GOM Daily — data={target_date}  run={run_date}T{run_utc}Z",
        f"Universe: fw139@139 | A1∧A2∧A3∧(A4∨A5) | B1∧(B2∨B3)∧B4 | C β-PROV",
        f"",
        f"OPEN GOM RÒNG (net_gated>0, n_q1≥1) — {n_ron}/{n_open}  ← soi trước",
    ]
    msg_lines += ron_lines if ron_lines else ["  (none)"]
    msg_lines += [
        f"",
        f"OPEN CHURN/ROTATION (net_gated≤0, n_q1≥1) — {n_churn}/{n_open}  ← tin cậy thấp",
    ]
    msg_lines += churn_lines if churn_lines else ["  (none)"]
    msg_lines += [
        f"",
        f"OPEN NO-QUALIFIED (n_q1=0) — {n_noqual}/{n_open}  ← chưa evaluable, KHÔNG xét doctrine",
    ]
    msg_lines += noqual_lines if noqual_lines else ["  (none)"]

    if closed_today:
        closed_str = ", ".join(closed_today[:10])
        if len(closed_today) > 10:
            closed_str += f" (+{len(closed_today)-10})"
        msg_lines.append(f"CLOSED TODAY: {closed_str}")
        msg_lines.append(f"xem đầy đủ: closed_chapters_{target_date[:7]}.csv (N chương)")

    # S-MISS — one line
    if smissing_today_n > 0:
        smiss_s = f"⚠ S-MISS TODAY: {smissing_today_n} — check export timing!"
    else:
        smiss_s = "S-MISS today: 0 ✓"
    if smissing_hist_n > 0:
        smiss_s += f"  |  hist: {smissing_hist_n} (known NaN gap, normal)"
    msg_lines.append(smiss_s)

    # GOM-C CAMPAIGN-TRACK section (D4: tách riêng, header, cột rõ ràng)
    # [v4.0 GOM-RESTRUCT-20260824 C1 formatter bỏ CAMPAIGN-TRACK — operator ký chat 24/08]
    # GOM-C decommissioned per bot-signals gom_detect_spec v4.0-draft (8a96eacc). Section
    # tắt vĩnh viễn; giữ code inline làm log để rollback nếu cần.
    _CAMPAIGN_TRACK_ENABLED = False   # Set True to restore CAMPAIGN-TRACK output
    if _CAMPAIGN_TRACK_ENABLED and ((gomc_beta_line and "0 fires" not in gomc_beta_line) or gomc_beta_supp):
        import re as _re2
        m_ct = _re2.search(r"\((\d+) fires", gomc_beta_line) if gomc_beta_line else None
        ct = int(m_ct.group(1)) if m_ct else 0
        ct_supp = len(gomc_beta_supp)
        msg_lines.append(f"")
        msg_lines.append(
            f"CAMPAIGN-TRACK [{ct} fires + {ct_supp} ⏸] [PROVISIONAL]:"
            if ct_supp else
            f"CAMPAIGN-TRACK (theo doi, khong vao) [{ct}] [PROVISIONAL]:"
        )
        if gomc_beta_stats:
            # Format: "TOKEN|n=N|gross=$Xk|net=$Yk[churn]|q2=...|vwap=...|px=$P|doi=±DM"
            for stat in gomc_beta_stats:
                parts = {p.split("=")[0]: p.split("=", 1)[1]
                         for p in stat.split("|") if "=" in p}
                tok    = stat.split("|")[0]
                n      = parts.get("n", "?")
                gross  = parts.get("gross", "")
                net    = parts.get("net", "")
                q2     = parts.get("q2", "NaN")
                vwap_c = parts.get("vwap", "N/A")
                px     = parts.get("px", "NaN")
                doi    = parts.get("doi", "NaN")
                cvr    = " [cover-drv]" if doi.startswith("-") and doi != "NaN" else ""
                # M4: show gross|net if available; churn tag already embedded in net string
                gn_s = f" {gross} gross|net={net}" if gross and net else ""
                msg_lines.append(f"  {tok} n={n}{gn_s} Q2={q2} VWAP={vwap_c} px={px} dOI={doi}{cvr}")
        elif ct > 0:
            m_toks = _re2.search(r"\):\s*(.+)$", gomc_beta_line) if gomc_beta_line else None
            toks_str = m_toks.group(1).strip() if m_toks else ""
            for ct_tok in toks_str.split():
                if not ct_tok.startswith("⏸"):
                    msg_lines.append(f"  {ct_tok}")
        for supp_raw in gomc_beta_supp:
            parts_s = {p.split("=")[0]: p.split("=", 1)[1]
                       for p in supp_raw.split("|") if "=" in p}
            tok_s  = supp_raw.split("|")[0]
            cd_s   = parts_s.get("cooldown", "?")
            first_s = parts_s.get("first", "?")[-5:]  # MM-DD
            msg_lines.append(f"  ⏸ {tok_s} cooldown {cd_s} (first-fire {first_s})")

    msg_lines += [
        "",
        "VWAP = giá vốn ước của build TRONG cửa sổ chuỗi — floor kinh tế + mốc invalidate, không phải điểm entry.",
        summary if summary else f"[{n_open} open / 139 scanned]",
    ]

    return "\n".join(msg_lines)


# ── TG message splitter ───────────────────────────────────────────────────────

_TG_LIMIT = 4096


def _tg_split(report: str) -> list:
    """Split report into ≤4096-char TG messages. Footer (VWAP line) always last."""
    if len(report) <= _TG_LIMIT:
        return [report]

    lines = report.split("\n")

    # Footer: from the blank line before "VWAP = " to end
    footer_start = next(
        (i for i in range(len(lines)) if lines[i].startswith("VWAP = ")),
        None
    )
    if footer_start is None:
        cut = report[:_TG_LIMIT - 25].rsplit("\n", 1)[0]
        return [cut + "\n[+overflow]"]

    fi = (footer_start - 1
          if footer_start > 0 and lines[footer_start - 1] == ""
          else footer_start)
    footer_str = "\n".join(lines[fi:])
    body_lines = lines[:fi]

    # Natural split: blank line before "OPEN CHURN" or "CAMPAIGN-TRACK"
    split_i = None
    for i in range(len(body_lines) - 1):
        if body_lines[i] == "" and (
            body_lines[i + 1].startswith("OPEN CHURN") or
            body_lines[i + 1].startswith("CAMPAIGN-TRACK")
        ):
            split_i = i
            break

    body_str = "\n".join(body_lines)

    if split_i is None:
        avail = _TG_LIMIT - len(footer_str) - 1
        if len(body_str) <= avail:
            return [body_str + "\n" + footer_str]
        cut = body_str[:avail].rsplit("\n", 1)[0]
        return [cut + "\n[+cont]\n" + footer_str]

    msg1 = "\n".join(body_lines[:split_i])
    msg2_lines = body_lines[split_i + 1:]

    if len(msg1) > _TG_LIMIT:
        msg1 = msg1[:_TG_LIMIT - 10].rsplit("\n", 1)[0] + "\n[+cont]"

    msg2_with_footer = "\n".join(msg2_lines) + "\n" + footer_str
    if len(msg2_with_footer) <= _TG_LIMIT:
        return [msg1, msg2_with_footer]

    msg2 = "\n".join(msg2_lines)
    if len(msg2) > _TG_LIMIT:
        msg2 = msg2[:_TG_LIMIT - 10].rsplit("\n", 1)[0] + "\n[+cont]"
    return [msg1, msg2, footer_str]


# ── Closed-chapters CSV writer ────────────────────────────────────────────────

def _write_closed_chapters_csv(target_date: str) -> int:
    """Write closed_chapters_{YYYY-MM}.csv for the target month. Returns row count."""
    import csv as _csv_w
    from datetime import datetime as _dt, timedelta as _td
    month = target_date[:7]
    out_path = STORE / f"closed_chapters_{month}.csv"
    # [F3.3 19/08] File missing = legit no-state case, trả 0 im lặng.
    # File tồn tại nhưng corrupt = BUG → WARN + telegram, NHƯNG return 0
    # để KHÔNG cascade cron gom_daily (Telegram push + chapter csv khác vẫn phải chạy).
    if not STATE_PATH.exists():
        return 0
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
    except json.JSONDecodeError as _st_exc:
        _msg = (f"⚠ gom_state.json CORRUPT: {_st_exc}. "
                f"closed_chapters CSV KHÔNG ghi ngày này. Repair state hoặc restore backup.")
        print(f"WARNING {_msg}", file=sys.stderr)
        try:
            tg_send(_msg, parse_mode="")
        except Exception:
            pass
        return 0
    fw_list = [l.strip() for l in FW_SYM_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    fw_base = {s[:-4] if s.endswith("USDT") else s for s in fw_list}
    rows = []
    for tok, ch in state.items():
        if tok not in fw_base or ch.get("chain_open"):
            continue
        close_d = (ch.get("close_date") or "")[:10]
        if not close_d or close_d[:7] != month:
            continue
        _nw = ch.get("net_oi_window_usd", ch.get("net_oi_delta_usd", float("nan")))
        _ng = ch.get("net_gated_usd", float("nan"))
        rows.append({
            "token":            tok,
            "chapter":          ch.get("chapter", 1),
            "start_date":       ch.get("start_date", ""),
            "close_date":       close_d,
            "close_reason":     ch.get("close_reason", ""),
            "n_days":           ch.get("n_days", 0),   # n_q1
            "Q1_cum_usd":       round(ch.get("Q1_cum_usd", 0.0), 2),
            # verdict 17/08 net-semantics: net_oi_window = ungated reality-check;
            # net_gated = gom doctrine (Σ ΔOI on counts_q1 days, NaN nếu n_q1=0).
            "net_oi_window_usd": round(_nw, 2),
            "net_gated_usd":     round(_ng, 2),   # 'nan' string preserved when n_q1=0
            "net_oi_delta":      round(_nw, 2),   # ALIAS (drop 2026-09-17)
            "peak_pos_r":       round(ch.get("peak_pos_r", float("nan")), 3),
        })
    rows.sort(key=lambda r: r["close_date"])
    if rows:
        fieldnames = ["token","chapter","start_date","close_date","close_reason",
                      "n_days","Q1_cum_usd","net_oi_window_usd","net_gated_usd",
                      "net_oi_delta","peak_pos_r"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = _csv_w.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    return len(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _now_utc = datetime.now(timezone.utc)
    run_utc  = _now_utc.strftime("%H:%M")
    run_date = _now_utc.strftime("%Y-%m-%d")
    target_date = (_now_utc - timedelta(days=1)).strftime("%Y-%m-%d")

    _log(f"run_start date={target_date}")

    # Dependency gate
    check_deps(target_date)

    # §8.2: cron không có quyền viết lại lịch sử — full-rebuild FORBIDDEN from cron
    # This assert fails loudly if anyone accidentally adds --full-rebuild to the cron cmd.
    # Full rebuilds require explicit operator invocation with GOM_ALLOW_FULL_REBUILD=1.
    gom_scan = SCRIPTS / "gom_scan.py"
    cmd = [
        sys.executable, str(gom_scan),
        "--daily",
        "--store", str(STORE),
        "--date", target_date,
        "--fw-filter", str(FW_SYM_PATH),
    ]
    assert "--full-rebuild" not in cmd, \
        "ASSERT §8.2 VIOLATED: cron entry (run_gom_daily.py) must never pass --full-rebuild to gom_scan. " \
        "Full rebuilds require GOM_ALLOW_FULL_REBUILD=1 and manual invocation."

    _log(f"exec: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                            timeout=300)

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if result.returncode != 0:
        err_snippet = (stderr or stdout)[:500]
        tg_error(f"gom_scan exit={result.returncode}\n{err_snippet}")

    # ── GOM-E T1 (mode-switch detector — §5 spec v0.9.2) ─────────────────────
    gom_e_script = SCRIPTS / "gom_e.py"
    if gom_e_script.exists():
        cmd_e = [
            sys.executable, str(gom_e_script),
            "--daily",
            "--store", str(STORE),
            "--date", target_date,
            "--fw-filter", str(FW_SYM_PATH),
        ]
        _log(f"exec gom_e: {' '.join(cmd_e)}")
        result_e = subprocess.run(cmd_e, capture_output=True, encoding="utf-8",
                                  errors="replace", timeout=180)
        gom_e_out = result_e.stdout or ""
        gom_e_err = result_e.stderr or ""
        if result_e.returncode != 0:
            _log(f"gom_e exit={result_e.returncode} stderr={gom_e_err[:300]}")
        else:
            _log(f"gom_e OK lines={gom_e_out.count(chr(10))}")
        # Send Bảng B alerts as additional TG message (Bảng A included for context)
        # AG2/21-09 · smart-truncate: cắt ranh dòng · tail line `(+n token Bảng A · đủ ở audit)`
        # thay vì cắt giữa chữ. Slice cap 4000 giữ (không đổi thành fail-closed U7 tới khi
        # AE3 order xong — xem §KỶ-LUẬT #13).
        # AH4/22-09 · đo len bằng tg_len (UTF-16 code unit sau strip HTML) · lib/tg_len.py
        if gom_e_out.strip():
            _SLICE_CAP = 4000
            try:
                sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
                from lib.tg_len import tg_len as _tg_len_ag2
            except ImportError:
                _tg_len_ag2 = len   # fallback
            # AV1/22-09 · tách footer trước slice · footer LUÔN ở cuối tin sau slice
            _footer_str = ""
            _body_lines = gom_e_out.split("\n")
            for _i in range(len(_body_lines) - 1, -1, -1):
                if _body_lines[_i].startswith("━━ footer ━━"):
                    _footer_str = "\n" + _body_lines[_i]
                    gom_e_out = "\n".join(_body_lines[:_i]).rstrip("\n")
                    break
            if _tg_len_ag2(gom_e_out) + _tg_len_ag2(_footer_str) > _SLICE_CAP:
                import re as _re_ag2
                # Đếm số dòng Bảng A còn lại sau char-slice (dòng bắt đầu "  SYM...")
                _tail = gom_e_out[_SLICE_CAP:]
                _remaining_a = len([l for l in _tail.split("\n") if _re_ag2.match(r"^  [A-Z0-9]+USDT?\s+\|", l)])
                _tail_note = f"\n(+{_remaining_a} token Bảng A · đủ ở audit)"
                # Reserve slice space cho BOTH tail_note VÀ footer
                _max_units = _SLICE_CAP - _tg_len_ag2(_tail_note) - _tg_len_ag2(_footer_str)
                _cut_at = gom_e_out.rfind("\n", 0, _max_units)
                if _cut_at < 0: _cut_at = _max_units
                while _cut_at > 0 and _tg_len_ag2(gom_e_out[:_cut_at] + _tail_note + _footer_str) > _SLICE_CAP:
                    _cut_at = gom_e_out.rfind("\n", 0, _cut_at - 1)
                    if _cut_at < 0: _cut_at = 0; break
                gome_msg = gom_e_out[:_cut_at] + _tail_note + _footer_str
            else:
                gome_msg = gom_e_out + _footer_str
            ok_e = tg_send(gome_msg)
            # V3.5o · GOM-E [SENT] marker + artifact_dump + log_bell (chuẩn chung)
            import hashlib as _hl_e
            _hash_e = _hl_e.md5(gome_msg.encode("utf-8")).hexdigest()[:12]
            print(f"[SENT] gom_e ok={ok_e} HTTP {"200" if ok_e else "X"} hash={_hash_e} target={target_date}")
            if ok_e:
                try:
                    sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
                    from lib.artifact_dump import dump_as_sent, log_bell
                    _ok_d, _det_d = dump_as_sent("gom_e", target_date, gome_msg, channel="old")
                    print(f"[ARTIFACT-DUMP gom_e] {_ok_d} · {_det_d}")
                    log_bell("gom_e", target_date, "old", ok_e, 200 if ok_e else 0, None, gome_msg)
                except Exception as _e_e: print(f"[ARTIFACT-DUMP-ERR gom_e] {_e_e}")
    else:
        _log("WARN: gom_e.py not found — skip")

    # Format and send Telegram report (split into ≤4096-char parts; footer always last)
    report   = format_tg_report(stdout, target_date, run_utc, run_date)
    messages = _tg_split(report)
    if len(messages) > 1:
        _log(f"tg_split parts={len(messages)} lens={[len(m) for m in messages]}")

    import re as _re_log
    _m = _re_log.search(r"OPEN \((\d+)/", report)
    n_open_fw = int(_m.group(1)) if _m else "?"

    all_ok = True
    fail_part = -1
    for i, msg in enumerate(messages):
        ok = tg_send(msg)
        # V3.5i [SENT] MARKER CHUẨN (directive REV10 item 4 · L-59 áp mọi sender)
        import hashlib as _hl
        _tg_hash = _hl.md5(msg.encode("utf-8")).hexdigest()[:12]
        print(f"[SENT] gom_daily ok={ok} HTTP {'200' if ok else 'X'} hash={_tg_hash} target={target_date} part={i+1}/{len(messages)}")
        from lib.artifact_dump import log_bell
        try:
            log_bell("gom_daily", target_date, "old", ok, 200 if ok else 0, None, msg)
        except Exception as _e: print(f"[N/A-ERROR:LOG-BELL] {_e}")
        # [ARTIFACT-DUMP as-sent · V1.4 sentinel]
        if ok:
            try:
                sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
                from lib.artifact_dump import dump_as_sent as _das
                _ok, _det = _das("gom_daily", target_date, msg, channel="old")
                print(f"[ARTIFACT-DUMP gom_daily] {_ok} · {_det}")
            except RuntimeError as _de: print(f"[ARTIFACT-DUMP-SENTINEL gom_daily] {_de}", file=sys.stderr)
            except Exception as _e: print(f"[ARTIFACT-DUMP-ERR gom_daily] {type(_e).__name__}: {_e}", file=sys.stderr)
        if not ok:
            all_ok = False
            fail_part = i + 1
            _log(f"tg_send_FAIL part={fail_part}/{len(messages)} len={len(msg)}")
            break

    _log(f"tg_send={'OK' if all_ok else 'FAIL'} parts={len(messages)} open_fw={n_open_fw}")

    if not all_ok:
        # Short ops ping (<200 chars) — won't hit length limit
        tg_send(f"[GOM DELIVER FAIL] {target_date} part {fail_part}/{len(messages)} — check gom_daily.log")
        _log("ERROR: tg deliver fail")
        print(f"ERROR: tg_send part {fail_part} failed", file=sys.stderr)
        sys.exit(1)

    # Heartbeat: only written after confirmed TG delivery (C1 watchdog leg)
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    HB_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")

    # Write closed_chapters_{YYYY-MM}.csv after each successful run
    _n_closed = _write_closed_chapters_csv(target_date)
    _log(f"closed_chapters_{target_date[:7]}.csv written: {_n_closed} rows")

    print(stdout)
    if stderr:
        print("STDERR:", stderr[:200], file=sys.stderr)

    _log(f"run_complete exit=0")


if __name__ == "__main__":
    main()

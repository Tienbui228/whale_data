#!/usr/bin/env python3
"""E5-job: Auto-append yesterday DAILY row for all OPEN cases in INDEX.

Runs after morning export ships (~01:00 UTC). Idempotent — skips dates already present.

Per-case logic:
  1. Open CASE_<TOKEN>.xlsx DAILY sheet, read existing dates
  2. If yesterday already present → skip
  3. Fetch yesterday's row from freshwatch_daily_YYYY-MM.csv (matched symbol+date)
  4. fn<6 (low_conf=True or funding_n<6) → ratio cols {15,16,17} get "SUSPECT fn<6" comment;
     taker/px/vol/OI always use native export value regardless of fn.
  5. Write raw fields + formula strings → append row → save xlsx
     File locked → RAISE (never silent-save to _NEW filename, per L-34)

After all cases: append §1 digest to agent_log.md.

Config: CASE_INDEX.xlsx INDEX sheet — rows where status contains OPEN or TRACKING,
        file column starts with CASE_.

Cron: 02:00 UTC daily.
Usage:
    python scripts/case_daily.py
    python scripts/case_daily.py --date 2026-07-29
    python scripts/case_daily.py --dry-run
"""
from __future__ import annotations

import csv
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import openpyxl
from openpyxl.comments import Comment
from openpyxl.cell.cell import MergedCell
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.alert import telegram_error

WHALE      = Path(r"D:\Data back test\whale_data")
CASE_DIR   = WHALE / "docs" / "case_files"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
AGENT_LOG  = WHALE / "agent_log.md"

FIRST_DATA_ROW = 3   # DAILY rows 1-2 are headers

# Export CSV field → xlsx column mapping
# key = xlsx col (1-based); value = (export_field, parse_type)
# "invert_bool": xlsx data_bad=1 when export data_ok=="False"
EXPORT_COL_MAP: dict[int, tuple[str, str]] = {
    1:  ("date",          "str"),
    2:  ("px_avg",        "float"),
    4:  ("vol_quote",     "float"),      # xlsx col label: vol_perp_usd
    5:  ("taker_buy_pct", "float"),
    6:  ("funding_avg",   "float"),
    7:  ("funding_min",   "float"),
    8:  ("funding_max",   "float"),
    9:  ("funding_n",     "int"),
    12: ("oi_usd",        "float"),
    15: ("lsr_pos_r",     "float"),
    16: ("lsr_acc_r",     "float"),
    17: ("lsr_global_r",  "float"),
    26: ("data_ok",       "invert_bool"),
}

FORMULA_COLS = {3, 18, 19, 20, 21, 22, 36}

# Ratio cols that get "SUSPECT fn<6" comment when fn_suspect=True.
# Taker (col 5) is intentionally excluded — always write native value.
_RATIO_COLS = {15, 16, 17}

# Bảo vệ mapping: mỗi col ratio chỉ được map đúng metric tương ứng.
_ASSERT_COL_METRIC: dict[int, str] = {
    5:  "taker_buy_pct",
    15: "lsr_pos_r",
    16: "lsr_acc_r",
    17: "lsr_global_r",
}
for _col, _expected in _ASSERT_COL_METRIC.items():
    _actual = EXPORT_COL_MAP.get(_col, (None,))[0]
    assert _actual == _expected, (
        f"MAPPING VIOLATION: col {_col} maps to {_actual!r}, expected {_expected!r}. "
        f"Sửa EXPORT_COL_MAP hoặc _ASSERT_COL_METRIC."
    )


def _parse_val(raw: str, parse_type: str):
    if raw is None or str(raw).strip() == "":
        return None
    raw = str(raw).strip()
    if parse_type == "str":
        return raw
    if parse_type == "float":
        try:
            v = float(raw); return None if v != v else v
        except ValueError:
            return None
    if parse_type == "int":
        try:
            return int(float(raw))
        except ValueError:
            return None
    if parse_type == "invert_bool":
        return 1 if raw == "False" else None
    return None


def _formulas_for_row(n: int) -> dict[int, str]:
    return {
        3:  f'=IFERROR(B{n}/B{n-1}-1,"")',
        18: f'=IFERROR(O{n}/P{n},"")',
        19: f'=IFERROR(AVERAGE(R{n-2}:R{n}),"")',
        20: f'=IFERROR(Q{n}/Q{n-5},"")',
        21: f'=IFERROR(O{n}/O{n-3}-1,"")',
        22: f'=IFERROR(P{n}/P{n-3}-1,"")',
        36: f'=IF(OR(AB{n}="",D{n}="",D{n}=0),"",AB{n}/D{n})',
    }


def _load_index(log=None) -> list[dict]:
    import structlog as _sl
    _log = log or _sl.get_logger()
    wb = openpyxl.load_workbook(str(CASE_DIR / "CASE_INDEX.xlsx"), data_only=True)
    ws = wb["INDEX"]
    cases = []
    for r in range(5, ws.max_row + 1):
        file_val = ws.cell(r, 1).value
        token    = ws.cell(r, 2).value
        status   = ws.cell(r, 3).value
        if not file_val or not token:
            continue
        # REGISTERED-NOT-OPEN: placeholder or non-xlsx file value
        if not str(file_val).endswith(".xlsx"):
            _log.info("case_registered_not_open",
                      token=str(token), file=str(file_val))
            continue
        if not status:
            continue
        status_s = str(status).upper()
        if "OPEN" in status_s or "TRACKING" in status_s:
            cases.append({
                "file":   str(file_val),
                "token":  str(token),
                "symbol": str(token).upper() + "USDT",
                "status": str(status),
            })
    return cases


def _load_export_csv(date_str: str, log=None) -> dict[str, dict]:
    """Load {symbol: row_dict} from freshwatch_daily_YYYY-MM.csv for given date.

    Raises RuntimeError if the monthly CSV is completely absent (missing-dependency,
    not just a missing row for this date — per L-44 missing-dep rule).
    """
    import structlog as _sl
    _log = log or _sl.get_logger()
    ym = date_str[:7]
    csv_path = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
    if not csv_path.exists():
        _log.error("export_csv_missing",
                   path=str(csv_path),
                   hint="export_freshwatch_daily_vps.py chưa chạy hoặc bị lỗi")
        raise RuntimeError(f"export_csv_missing: {csv_path}")
    result: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date") == date_str:
                result[row["symbol"]] = row
    return result


def _existing_dates_and_max_row(ws) -> tuple[set[str], int]:
    dates: set[str] = set()
    max_row = FIRST_DATA_ROW - 1
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v and isinstance(v, str) and len(v) == 10 and v[4] == "-":
            dates.add(v)
            max_row = r
    return dates, max_row


def _append_daily_row(
    ws,
    row_n: int,
    csv_row: dict,
    fn_suspect: bool,
    fn_n_str: str,
    src_ratio: str,
) -> None:
    formulas = _formulas_for_row(row_n)
    max_col = ws.max_column or 41

    for c in range(1, max_col + 1):
        cell = ws.cell(row_n, c)

        if isinstance(cell, MergedCell):
            continue

        if c in FORMULA_COLS:
            cell.value = formulas.get(c)
            continue

        if c not in EXPORT_COL_MAP:
            continue

        field, parse_type = EXPORT_COL_MAP[c]
        raw = csv_row.get(field, "")
        cell.value = _parse_val(raw, parse_type)

        # 2.5(a): taker_buy_pct (col 5) stored as percent; CSV is fraction r/(1+r)
        if c == 5 and isinstance(cell.value, (int, float)):
            cell.value = round(cell.value * 100, 6)

        # fn<6: ratio cols get SUSPECT comment; taker/px/vol/OI write native unchanged
        if fn_suspect and c in _RATIO_COLS:
            cell.comment = Comment(
                f"SUSPECT fn<6 (fn={fn_n_str}, src={src_ratio})",
                "case_daily.py",
            )


def _compute_digest_metrics(csv_row: dict, fn_suspect: bool) -> dict:
    def f(key: str) -> Optional[float]:
        v = csv_row.get(key, "")
        try:
            return float(v) if v else None
        except (ValueError, TypeError):
            return None

    pos_r = f("lsr_pos_r"); acc_r = f("lsr_acc_r"); glsr = f("lsr_global_r")
    div_raw = (pos_r / acc_r) if (pos_r and acc_r and acc_r != 0) else None
    taker   = f("taker_buy_pct")   # always native

    return {
        "px_avg":        f("px_avg"),
        "oi_usd":        f("oi_usd"),
        "lsr_pos_r":     pos_r,
        "lsr_acc_r":     acc_r,
        "lsr_global_r":  glsr,
        "div_raw":       div_raw,
        "funding_avg":   f("funding_avg"),
        "funding_n":     csv_row.get("funding_n", ""),
        "taker_buy_pct": taker,
        "data_ok":       csv_row.get("data_ok", ""),
        "low_conf":      csv_row.get("low_conf", ""),
        "fn_suspect":    fn_suspect,
    }


def _row_has_suspect(ws, row_n: int) -> bool:
    """Return True if any cell in row_n has a Comment containing 'SUSPECT'."""
    for c in range(1, (ws.max_column or 41) + 1):
        cell = ws.cell(row_n, c)
        if cell.comment and "SUSPECT" in str(cell.comment.text):
            return True
    return False


def _row_fn_low(ws, row_n: int) -> bool:
    """Return True if col 9 (funding_n) is None or < 6 — stale row needing overwrite."""
    fn_val = ws.cell(row_n, 9).value
    return fn_val is None or (isinstance(fn_val, (int, float)) and fn_val < 6)


def _read_row_values(ws, row_n: int) -> dict[int, object]:
    """Read raw cell values for all columns in row_n."""
    return {c: ws.cell(row_n, c).value for c in range(1, (ws.max_column or 41) + 1)}


def _clear_row(ws, row_n: int) -> None:
    """Clear values and comments from all cells in row_n."""
    for c in range(1, (ws.max_column or 41) + 1):
        cell = ws.cell(row_n, c)
        if isinstance(cell, MergedCell):
            continue
        cell.value = None
        cell.comment = None


app = typer.Typer(add_completion=False)


@app.command()
def main(
    date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default=yesterday UTC)"),
    dry_run: bool = typer.Option(False, help="Preview only — no xlsx writes"),
    force_overwrite: bool = typer.Option(
        False,
        "--force-overwrite",
        help="Overwrite existing rows that have SUSPECT comment; log old→new to agent_log.",
    ),
) -> None:
    """E5: Auto-append DAILY row for all OPEN cases + §1 digest to agent_log."""
    import structlog
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ])
    log = structlog.get_logger()

    if date:
        date_str = date
    else:
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    log.info("case_daily_start", date=date_str, dry_run=dry_run)

    cases = _load_index(log=log)
    log.info("case_daily_cases", count=len(cases), tokens=[c["token"] for c in cases])

    # Orphan check: xlsx in CASE_DIR not registered in INDEX
    indexed_files = {c["file"] for c in cases}
    for xlsx_f in sorted(CASE_DIR.glob("CASE_*.xlsx")):
        if xlsx_f.name == "CASE_INDEX.xlsx":
            continue
        if xlsx_f.name not in indexed_files:
            log.warning("orphan_case_file", path=str(xlsx_f))

    try:
        export_rows = _load_export_csv(date_str, log=log)
    except RuntimeError as e:
        log.error("case_daily_abort", reason=str(e))
        telegram_error(f"case_daily_abort: {e}")
        raise typer.Exit(1)
    log.info("case_daily_export", date=date_str, symbols_found=len(export_rows))

    digest_lines: list[str] = []
    digest_lines.append(f"\n## SESSION {datetime.now(timezone.utc).strftime('%Y-%m-%d')} — case_daily digest")
    digest_lines.append(f"\n**Target date:** {date_str}  **Run:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  **dry_run:** {dry_run}")
    digest_lines.append("")

    results: list[dict] = []
    n_missing_xlsx = 0

    for case in cases:
        token  = case["token"]
        sym    = case["symbol"]
        cfile  = case["file"]
        label  = f"{token} ({cfile})"
        log.info("case_daily_processing", case=label)

        xlsx_path = CASE_DIR / cfile
        if not xlsx_path.exists():
            log.error("case_daily_missing_xlsx", path=str(xlsx_path))
            telegram_error(f"case_daily_missing_xlsx: {cfile} không tồn tại — check CASE_DIR")
            n_missing_xlsx += 1
            results.append({"token": token, "status": "SKIP_NO_FILE", "note": str(xlsx_path)})
            continue

        wb = openpyxl.load_workbook(str(xlsx_path), data_only=False)
        if "DAILY" not in wb.sheetnames:
            log.warning("case_daily_no_daily_sheet", file=cfile)
            results.append({"token": token, "status": "SKIP_NO_SHEET"})
            continue
        ws = wb["DAILY"]

        existing_dates, last_row = _existing_dates_and_max_row(ws)

        if date_str in existing_dates:
            if force_overwrite:
                # Find the row number for date_str
                overwrite_row = None
                for r in range(FIRST_DATA_ROW, ws.max_row + 1):
                    if ws.cell(r, 1).value == date_str:
                        overwrite_row = r
                        break
                if overwrite_row and (_row_has_suspect(ws, overwrite_row) or _row_fn_low(ws, overwrite_row)):
                    log.info("case_daily_overwrite_suspect", token=token, date=date_str, row=overwrite_row)
                    # Capture old values for audit log
                    old_vals = _read_row_values(ws, overwrite_row)
                    # Fall through to write logic below with row_n = overwrite_row
                    row_n = overwrite_row
                    _clear_row(ws, row_n)
                    # Inject sentinel so the write logic runs
                    _overwrite_mode = True
                    _old_vals_for_log = old_vals
                else:
                    log.info("case_daily_skip_no_suspect", token=token, date=date_str)
                    results.append({"token": token, "status": "SKIP_NO_SUSPECT", "date": date_str})
                    continue
            else:
                log.info("case_daily_skip_existing", token=token, date=date_str)
                results.append({"token": token, "status": "SKIP_EXISTS", "date": date_str})
                continue
        else:
            _overwrite_mode = False
            _old_vals_for_log = {}

        csv_row = export_rows.get(sym)
        if csv_row is None:
            log.warning("case_daily_no_export_row", token=token, symbol=sym, date=date_str)
            results.append({"token": token, "status": "SKIP_NO_EXPORT", "symbol": sym})
            continue

        fn_n      = csv_row.get("funding_n", "")
        low_conf  = csv_row.get("low_conf", "False")
        src_ratio = csv_row.get("src_ratio", "")

        try:
            fn_suspect = int(fn_n) < 6 if fn_n else False
        except (ValueError, TypeError):
            fn_suspect = False
        fn_suspect = fn_suspect or (low_conf == "True")

        if fn_suspect:
            log.info("case_daily_fn_suspect", token=token, fn_n=fn_n, low_conf=low_conf, src_ratio=src_ratio)

        if not _overwrite_mode:
            row_n = last_row + 1

        if not dry_run:
            _append_daily_row(ws, row_n, csv_row, fn_suspect, fn_n, src_ratio)
            try:
                wb.save(str(xlsx_path))
                if _overwrite_mode:
                    log.info("case_daily_overwrite_saved", token=token, row=row_n, date=date_str)
                    status = "OVERWRITE_OK"
                    # Build diff log for agent_log
                    _diff_lines: list[str] = []
                    for c, old_v in _old_vals_for_log.items():
                        new_v = ws.cell(row_n, c).value
                        if str(old_v) != str(new_v):
                            _diff_lines.append(f"col{c}: {old_v!r} → {new_v!r}")
                    if _diff_lines:
                        log.info("case_daily_overwrite_diff", token=token, date=date_str, diffs=_diff_lines[:10])
                else:
                    log.info("case_daily_saved", token=token, row=row_n, date=date_str)
                    status = "OK"
            except PermissionError:
                # L-34: cấm silent-save sang tên khác — close xlsx rồi retry
                raise RuntimeError(
                    f"[L-34] File locked — close xlsx then retry: {xlsx_path}"
                ) from None
        else:
            if _overwrite_mode:
                status = "DRY_OVERWRITE"
                log.info("case_daily_dry_overwrite", token=token, row=row_n, date=date_str, has_suspect=True)
            else:
                status = "DRY_RUN"
                log.info("case_daily_dry_run", token=token, would_append_row=row_n, date=date_str)

        metrics = _compute_digest_metrics(csv_row, fn_suspect)
        results.append({
            "token":         token,
            "status":        status,
            "date":          date_str,
            "row":           row_n,
            "metrics":       metrics,
            "fn_suspect":    fn_suspect,
            "fn_n":          fn_n,
            "overwrite_mode": _overwrite_mode,
        })

    # §1 digest
    digest_lines.append("### §1 Handover digest")
    digest_lines.append("")
    digest_lines.append("| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | SUSPECT |")
    digest_lines.append("|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|---------|")

    for r in results:
        if "metrics" not in r:
            digest_lines.append(f"| {r['token']} | {r['status']} | — | — | — | — | — | — | — | — | — |")
            continue
        m = r["metrics"]
        def fmt(v, fmt_s=".4f"):
            return f"{v:{fmt_s}}" if v is not None else "—"
        suspect_label = f"fn<6(fn={r['fn_n']})" if r["fn_suspect"] else "no"
        digest_lines.append(
            f"| {r['token']} | {r['status']} | {r['row']} "
            f"| {fmt(m['lsr_pos_r'])} | {fmt(m['lsr_acc_r'])} "
            f"| {fmt(m['div_raw'])} | {fmt(m.get('taker_buy_pct'))} "
            f"| {fmt(m['funding_avg'], '.6f')} | {m['funding_n']} "
            f"| {fmt(m['oi_usd'], ',.0f')} "
            f"| {suspect_label} |"
        )

    digest_lines.append("")
    n_ok       = sum(1 for r in results if r.get("status", "") in ("OK", "OVERWRITE_OK"))
    n_skip     = sum(1 for r in results if "SKIP" in r.get("status", ""))
    n_dry      = sum(1 for r in results if "DRY" in r.get("status", ""))
    n_overwrite = sum(1 for r in results if r.get("status", "") == "OVERWRITE_OK")
    overwrite_note = f", {n_overwrite} overwrite" if n_overwrite else ""
    digest_lines.append(
        f"**Tổng:** {n_ok} OK{overwrite_note}, {n_skip} skip, {n_dry} dry_run"
    )
    digest_lines.append("")
    digest_lines.append("---")

    if not dry_run:
        with open(AGENT_LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(digest_lines) + "\n")
        log.info("case_daily_digest_written", path=str(AGENT_LOG))
    else:
        log.info("case_daily_digest_preview", lines=len(digest_lines))
        for dl in digest_lines:
            print(dl)

    log.info("case_daily_complete",
             ok=sum(1 for r in results if r.get("status", "").startswith("OK")),
             skip=sum(1 for r in results if "SKIP" in r.get("status", "")))

    raise typer.Exit(1 if n_missing_xlsx > 0 else 0)


if __name__ == "__main__":
    app()

"""case_guard.py — validate_written_pack(): one door for all CASE DAILY builders.

Post-write validation: reload XLSX from disk, check required columns ≥50% non-null
in last 30 data rows.

FAIL → raise RuntimeError (caller: exit≠0 + alert — L-44 compliant).
Cells with explicit ABSTAIN/MISSING markers count as valid (not null).

Usage:
    from scripts.case_guard import validate_written_pack
    validate_written_pack(xlsx_path)  # call after save, before exit
"""
from __future__ import annotations

import math
from pathlib import Path

import openpyxl
from openpyxl.cell.cell import MergedCell

# Columns that must be ≥50% non-null in last 30 data rows.
# These are the WRITTEN (non-formula) columns in DAILY sheet.
# Sorted by priority. Add new required cols here — one place.
REQUIRED_COLS: list[str] = [
    "px_avg",
    "vol_perp_usd",
    "taker_buy_pct",
    "f_avg",
    "fn",
    "oi_usd",
    "pos_r",
    "acc_r",
    "gLSR",
]

# Explicit absence markers — cells with these strings are NOT null failures.
# An operator may write ABSTAIN or MISSING with context; that's a valid note.
# Single-char markers ("-", "—") use EXACT match only to avoid false positives
# on scientific notation (e.g. "5e-05" contains "-" but is a valid float).
_VALID_ABSENCE_EXACT: frozenset[str] = frozenset({"ABSTAIN", "MISSING", "N/A", "—", "-"})
_VALID_ABSENCE_SUBSTR: frozenset[str] = frozenset({"ABSTAIN", "MISSING", "N/A"})

# V1 schema aliases (older CASE files used different column names).
# Maps V1 header name → canonical REQUIRED_COLS name.
_COL_ALIASES: dict[str, str] = {
    "f_n":         "fn",
    "lsr_pos_r":   "pos_r",
    "lsr_acc_r":   "acc_r",
    "lsr_global_r": "gLSR",
}

WINDOW_DAYS: int = 30


def _normalize_col(s: str) -> str:
    """Strip parenthetical annotation from header: 'px_avg (H+L+C)/3' → 'px_avg'."""
    return s.split("(")[0].strip()


def _is_valid(v) -> bool:
    """True if cell value is non-null and not an ABSTAIN-family marker."""
    if v is None:
        return False
    s = str(v).strip()
    if not s:
        return False
    # Exact match against all absence markers
    if s.upper() in _VALID_ABSENCE_EXACT:
        return False
    # Substring match only for multi-char absence words (avoids "-" matching "5e-05")
    if any(tok in s.upper() for tok in _VALID_ABSENCE_SUBSTR):
        return False
    try:
        fv = float(v)
        return not math.isnan(fv)
    except (ValueError, TypeError):
        return True  # non-numeric non-empty non-ABSTAIN string = valid


def _find_header_row(ws) -> tuple[int, dict[str, int]]:
    """Return (header_row_idx, {col_name: col_idx_1based}).

    Searches first 5 rows for a row containing 'date' (exact) or a cell whose
    normalized prefix is 'px_avg'. Normalizes headers by stripping parenthetical
    annotations ('px_avg (H+L+C)/3' → also stored as 'px_avg'). Applies V1
    schema aliases so 'lsr_pos_r' → also stored as 'pos_r', etc.

    Returns (0, {}) if headers not found.
    """
    for r in range(1, 6):
        row = ws[r]
        names: dict[str, int] = {}
        for i, cell in enumerate(row):
            if isinstance(cell, MergedCell) or cell.value is None:
                continue
            raw = str(cell.value)
            norm = _normalize_col(raw)
            names[raw] = i + 1
            if norm != raw:
                names[norm] = i + 1  # normalized alias (strips annotation)
        # Apply V1 schema aliases
        for v1_name, canonical in _COL_ALIASES.items():
            if v1_name in names and canonical not in names:
                names[canonical] = names[v1_name]

        if "date" in names or "px_avg" in names:
            return r, names
    return 0, {}


def validate_written_pack(
    xlsx_path: str | Path,
    *,
    window: int = WINDOW_DAYS,
    sheet: str = "DAILY",
) -> None:
    """Reload XLSX from disk and validate DAILY required columns.

    Raises RuntimeError on any failure. Caller is responsible for exit≠0 + alert.
    """
    path = Path(xlsx_path)
    if not path.exists():
        raise RuntimeError(f"validate_written_pack: file not found: {path}")

    wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    try:
        if sheet not in wb.sheetnames:
            raise RuntimeError(
                f"validate_written_pack: sheet '{sheet}' not found in {path.name}"
            )

        ws = wb[sheet]
        header_row_idx, headers = _find_header_row(ws)

        # Collect all non-empty data rows (skip header row, skip empty dates)
        data_rows: list[tuple] = []
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if r_idx <= header_row_idx:
                continue
            if row[0] not in (None, ""):
                data_rows.append(row)

        if not data_rows:
            raise RuntimeError(
                f"validate_written_pack: no data rows in {path.name} sheet {sheet}"
            )

        window_rows = data_rows[-window:] if len(data_rows) >= window else data_rows
        n = len(window_rows)
        n_cols = max(len(r) for r in window_rows) if window_rows else 0

        failures: list[str] = []

        for col_name in REQUIRED_COLS:
            col_idx_0 = None  # 0-based index into row tuple

            if col_name in headers:
                col_idx_0 = headers[col_name] - 1
            else:
                failures.append(f"{col_name}: column header NOT FOUND in {sheet} row 1")
                continue

            if col_idx_0 >= n_cols:
                failures.append(f"{col_name}: col index {col_idx_0} out of range (max {n_cols-1})")
                continue

            valid = sum(1 for row in window_rows if _is_valid(row[col_idx_0]))
            pct = valid / n * 100 if n > 0 else 0.0

            if pct < 50.0:
                failures.append(
                    f"{col_name}: {valid}/{n} non-null in last {n}d = {pct:.0f}% < 50%"
                )

            # Range check for taker_buy_pct: expect percentage [20,80], not fraction [0,1]
            if col_name == "taker_buy_pct" and valid > 0:
                num_vals: list[float] = []
                for row in window_rows:
                    cell_v = row[col_idx_0]
                    if _is_valid(cell_v):
                        try:
                            num_vals.append(float(cell_v))
                        except (TypeError, ValueError):
                            pass
                if num_vals:
                    _tk_max = max(num_vals)
                    _tk_min = min(num_vals)
                    if _tk_max <= 1.0:
                        failures.append(
                            f"taker_buy_pct: fraction scale (max={_tk_max:.4f} ≤ 1.0)"
                            f" — expected pct [20,80]; rebuild needed"
                        )
                    elif _tk_max == _tk_min:
                        failures.append(
                            f"taker_buy_pct: constant value={_tk_max:.2f} across {n}d"
                            f" — likely stale/zero fill"
                        )
    finally:
        wb.close()

    if failures:
        raise RuntimeError(
            f"validate_written_pack FAIL [{path.name}] — {len(failures)} column(s):\n"
            + "\n".join(f"  !! {f}" for f in failures)
        )

"""universe_master.py — Persistent append-only universe master list.

Schema: symbol, added_date, source, status, note, last_seen_exchangeinfo
  source : seed | exchangeinfo | manual
  status : active | delisted | excluded
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from whale_collector.config import DATA_DIR

MASTER_PATH: Path = DATA_DIR / "config" / "universe_master.csv"
BACKUP_DIR: Path = DATA_DIR / "config" / "backups"

MASTER_COLS = [
    "symbol",
    "added_date",
    "source",
    "status",
    "note",
    "last_seen_exchangeinfo",
]


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_master(path: Optional[Path] = None) -> pd.DataFrame:
    """Load universe_master.csv. Returns empty DataFrame with correct schema if absent."""
    p = path or MASTER_PATH
    if not p.exists():
        return pd.DataFrame(columns=MASTER_COLS)
    df = pd.read_csv(p, dtype=str).fillna("")
    for col in MASTER_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[MASTER_COLS].copy()


def save_master(df: pd.DataFrame, path: Optional[Path] = None) -> None:
    """Atomic write of universe_master.csv with daily backup."""
    p = path or MASTER_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if p.exists():
        today = _today()
        bk = BACKUP_DIR / f"universe_master_{today}.csv"
        if not bk.exists():
            shutil.copy2(p, bk)

    tmp = p.with_suffix(".tmp.csv")
    df[MASTER_COLS].to_csv(tmp, index=False)
    tmp.replace(p)


def get_active_symbols(df: pd.DataFrame) -> list[str]:
    """Return list of symbols where status == 'active'."""
    return df[df["status"] == "active"]["symbol"].tolist()


def append_new_symbols(
    master: pd.DataFrame,
    new_symbols: set[str],
    today: str,
    source: str,
    notes: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Append rows for symbols not yet in master. Returns updated DataFrame."""
    if not new_symbols:
        return master
    notes = notes or {}
    rows = []
    for sym in sorted(new_symbols):
        rows.append({
            "symbol": sym,
            "added_date": today,
            "source": source,
            "status": "active",
            "note": notes.get(sym, ""),
            "last_seen_exchangeinfo": today,
        })
    new_df = pd.DataFrame(rows, columns=MASTER_COLS)
    return pd.concat([master, new_df], ignore_index=True)


def apply_delisted_72h(
    master: pd.DataFrame,
    trading_syms: set[str],
    today: str,
) -> tuple[pd.DataFrame, set[str]]:
    """Update last_seen_exchangeinfo for active symbols present in exchangeInfo,
    then mark as delisted any active symbol unseen for >72h (3 days).

    Returns (updated_df, newly_delisted_set).
    """
    df = master.copy()
    newly_delisted: set[str] = set()

    for i, row in df.iterrows():
        if row["status"] != "active":
            continue
        sym = row["symbol"]
        if sym in trading_syms:
            df.at[i, "last_seen_exchangeinfo"] = today
        else:
            last_seen = row["last_seen_exchangeinfo"]
            if last_seen:
                try:
                    last_dt = datetime.fromisoformat(last_seen).date()
                    today_dt = datetime.fromisoformat(today).date()
                    if (today_dt - last_dt).days > 2:  # >72h = more than 2 full days
                        df.at[i, "status"] = "delisted"
                        newly_delisted.add(sym)
                except ValueError:
                    pass
            # If last_seen is empty, leave active (will be marked on next run if still absent)

    return df, newly_delisted


def reactivate_returned(
    master: pd.DataFrame,
    trading_syms: set[str],
    today: str,
) -> tuple[pd.DataFrame, set[str]]:
    """Reactivate symbols with status=delisted that reappear in exchangeInfo TRADING.

    Returns (updated_df, reactivated_set).
    """
    df = master.copy()
    reactivated: set[str] = set()

    for i, row in df.iterrows():
        if row["status"] == "delisted" and row["symbol"] in trading_syms:
            df.at[i, "status"] = "active"
            df.at[i, "last_seen_exchangeinfo"] = today
            reactivated.add(row["symbol"])

    return df, reactivated


def load_freshwatch_symbols(path: Optional[Path] = None) -> set[str]:
    """Load freshwatch_symbols.txt. Returns empty set if file absent (non-blocking)."""
    from whale_collector.config import FRESHWATCH_PATH
    p = path or FRESHWATCH_PATH
    if not p.exists():
        return set()
    with open(p, encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}

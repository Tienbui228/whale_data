"""adapter_h1_nansen.py — H1 KHO-STEP adapter reads bot Nansen snapshots RAW.

Per proposals/adapter_h1_spec_v0.1_20260824.md (SIGNED operator ĐIỂM DỪNG 1 24/08).

Semantics:
  - Input: D:/Check onchain fresh wallets/snapshots/YYYY-MM-DD.json (daily cron 01:00 UTC)
  - RAW field exchange_balance_tokens (MỨC balance level, T-1 UTC snapshot)
  - Token map: contract 0x canonical (L-51 SAFE)
  - No Telegram parse, no filter apply (bot threshold 1.0%/$200k = render filter, IRRELEVANT
    for H1 doctrine which computes |Δbalance|/balance ≥ 10% in ≤3d window trong runner)
  - Cột phụ [BOT-COMPUTED] copy-through: exchange_delta_usd, delta_pct_mcap (mcap FROM snapshot)
  - api_failed=true → N/A + [API-FAILED] flag (adapter KHÔNG retry, KHÔNG kích bot)

Output DataFrame columns:
  date, symbol, token_contract, exch_balance_level, kho_step_pct,
  delta_usd, delta_pct_mcap, flags, source_file, ingested_at
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import pandas as pd


# [H1-đường-(a) KÝ 28/08] Adapter đọc VPS-synced snapshot (VPS = đường chạy chính duy nhất).
# Local Windows Task Scheduler 01:10 UTC (post Nansen 01:00) rsync/scp local snapshots
# + last_run.json → VPS data/raw/nansen_snapshots/. Retention 30d rotate.
# Máy tắt/bot fail → H1=N/A ngày đó theo cờ adapter, không coi sự cố.
# Env-detect: posix (VPS) → VPS path; win32 (local dev) → local path fallback.
import os as _os_env
if _os_env.name == "posix" or _os_env.environ.get("ADAPTER_H1_VPS_MODE"):
    BOT_SNAPSHOTS = Path("/root/Data_back_test/whale_data/data/raw/nansen_snapshots")
    BOT_LAST_RUN = Path("/root/Data_back_test/whale_data/data/raw/nansen_snapshots/last_run.json")
else:
    BOT_SNAPSHOTS = Path(r"D:/Check onchain fresh wallets/snapshots")
    BOT_LAST_RUN = Path(r"D:/Check onchain fresh wallets/last_run.json")


def _load_snapshot(date_str: str) -> Optional[dict]:
    """Load bot snapshot JSON for a given ingest date. Returns None if missing."""
    p = BOT_SNAPSHOTS / f"{date_str}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _last_ingested_at() -> str:
    """Return last successful cron run timestamp (ISO UTC)."""
    if BOT_LAST_RUN.exists():
        try:
            d = json.loads(BOT_LAST_RUN.read_text(encoding="utf-8"))
            return d.get("last_success", "?")
        except Exception:
            return "?"
    return "?"


def _compute_pct_mcap(r: dict) -> Optional[float]:
    """Copy-through bot semantic: exchange_delta_usd / market_cap × 100. None if missing."""
    du = r.get("exchange_delta_usd")
    mc = r.get("market_cap")
    if du is None or mc is None or float(mc) <= 0:
        return None
    return float(du) / float(mc) * 100.0


def read_adapter_daily(ingest_date: str, last_seen_days: int = 2) -> pd.DataFrame:
    """Read H1 balance adapter for a given ingest date (bot filename date, UTC 00:00 next day).

    Semantics:
      - Snapshot ingest_date = filename YYYY-MM-DD.json (cron 01:00 UTC same day)
      - `exchange_balance_date` inside JSON = T-1 UTC (previous day midnight)
      - Fallback last-seen ≤last_seen_days if snapshot missing/api_failed for a token
      - No retry, no bot trigger

    Returns DataFrame with columns per adapter-H1-spec v0.1.
    """
    snap = _load_snapshot(ingest_date)
    if snap is None:
        return pd.DataFrame(columns=["date", "symbol", "token_contract",
                                     "exch_balance_level", "kho_step_pct",
                                     "delta_usd", "delta_pct_mcap",
                                     "flags", "source_file", "ingested_at"])

    ingested = _last_ingested_at()
    src_file = f"{ingest_date}.json"
    rows_out = []

    for r in snap.get("rows", []):
        sym = r.get("symbol", "")
        contract = r.get("token", "")
        api_failed = bool(r.get("api_failed", False))
        exch_api_failed = bool(r.get("exchange_api_failed", False))
        flags: list[str] = []

        # Token contract missing → L-51 flag
        if not contract or not contract.startswith("0x"):
            flags.append("[SYMBOL-MAP-UNVERIFIED]")

        # API failed → N/A + flag, KHÔNG retry
        if api_failed or exch_api_failed:
            flags.append("[API-FAILED]")
            rows_out.append({
                "date":               None,
                "symbol":             sym,
                "token_contract":     contract or None,
                "exch_balance_level": None,
                "kho_step_pct":       None,
                "delta_usd":          None,
                "delta_pct_mcap":     None,
                "flags":              " ".join(flags) if flags else "",
                "source_file":        src_file,
                "ingested_at":        ingested,
            })
            continue

        # Balance MỨC (T-1 UTC per bot snapshot)
        bal_tokens = r.get("exchange_balance_tokens")
        bal_date = r.get("exchange_balance_date")
        prev_tokens = r.get("exchange_prev_tokens")
        delta_pct = r.get("exchange_delta_pct")

        # Normalize date to YYYY-MM-DD
        if bal_date and "T" in str(bal_date):
            date_iso = str(bal_date).split("T")[0]
        else:
            date_iso = None

        # If bot didn't provide balance for this token today, fallback last-seen
        if bal_tokens is None:
            # Simple last-seen scan backward up to last_seen_days
            for lb in range(1, last_seen_days + 1):
                prev_date = (datetime.strptime(ingest_date, "%Y-%m-%d")
                             - pd.Timedelta(days=lb)).strftime("%Y-%m-%d")
                prev_snap = _load_snapshot(prev_date)
                if prev_snap is None:
                    continue
                match = next((rr for rr in prev_snap.get("rows", [])
                              if rr.get("token") == contract or rr.get("symbol") == sym),
                             None)
                if match and match.get("exchange_balance_tokens") is not None:
                    bal_tokens = match["exchange_balance_tokens"]
                    bal_date = match.get("exchange_balance_date")
                    prev_tokens = match.get("exchange_prev_tokens")
                    delta_pct = match.get("exchange_delta_pct")
                    date_iso = str(bal_date).split("T")[0] if bal_date else prev_date
                    flags.append(f"[LAST-SEEN-{lb}D]")
                    break
            else:
                flags.append("[MISSING-SNAPSHOT]")

        # kho_step_pct: bot delta_pct (fraction 0-1) → normalize as-is
        # Bot returns fraction (0.00656 = 0.656%). Adapter keeps fraction; runner applies threshold.
        kho_step_pct = delta_pct if delta_pct is not None else None
        # Fallback compute if delta_pct null but balance + prev available
        if kho_step_pct is None and bal_tokens is not None and prev_tokens is not None:
            if float(prev_tokens) > 0:
                kho_step_pct = (float(bal_tokens) - float(prev_tokens)) / float(prev_tokens)
            # prev=0 → N/A (chống chia-0 kiểu CAP listing 0→130M per spec)

        # Cột phụ [BOT-COMPUTED]
        delta_usd = r.get("exchange_delta_usd")
        pct_mcap = _compute_pct_mcap(r)

        rows_out.append({
            "date":               date_iso,
            "symbol":             sym,
            "token_contract":     contract or None,
            "exch_balance_level": float(bal_tokens) if bal_tokens is not None else None,
            "kho_step_pct":       float(kho_step_pct) if kho_step_pct is not None else None,
            "delta_usd":          float(delta_usd) if delta_usd is not None else None,
            "delta_pct_mcap":     float(pct_mcap) if pct_mcap is not None else None,
            "flags":              " ".join(flags) if flags else "",
            "source_file":        src_file,
            "ingested_at":        ingested,
        })

    return pd.DataFrame(rows_out)


def snapshot_md5(ingest_date: str) -> Optional[str]:
    """Return md5 of raw snapshot JSON for provenance."""
    p = BOT_SNAPSHOTS / f"{ingest_date}.json"
    if not p.exists():
        return None
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


if __name__ == "__main__":
    import sys, io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # Smoke: adapter output for 2026-08-22 (last known api_ok=138 per A1)
    df = read_adapter_daily("2026-08-22")
    print(f"[adapter_h1_nansen] 2026-08-22: {len(df)} rows")
    print(f"  snapshot_md5: {snapshot_md5('2026-08-22')}")
    print(f"  columns: {list(df.columns)}")
    if not df.empty:
        # Sample rows
        print(f"\n  sample rows:")
        for _, r in df.head(3).iterrows():
            print(f"    {r['date']} {r['symbol']:>10} contract={str(r['token_contract'])[:20]}... "
                  f"bal={r['exch_balance_level']} kho_step_pct={r['kho_step_pct']} "
                  f"flags={r['flags'] or '-'}")
        # Stats
        with_bal = df["exch_balance_level"].notna().sum()
        with_flags = (df["flags"] != "").sum()
        print(f"\n  Stats: {with_bal}/{len(df)} rows have balance · {with_flags} rows have flags")

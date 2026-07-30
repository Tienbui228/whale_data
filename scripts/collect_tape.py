#!/usr/bin/env python3
"""E4: Tape collector — daily aggregate per-symbol per-venue từ public trades.

Chức năng:
  - Đọc public trades từ Gate.io (hoặc Binance spot) cho mỗi symbol được bật
  - Tính daily aggregate: takerBUY%, CVD, size distribution (p50/p90/CV)
  - Snapshot bid_wall/ask_wall (order book ±5% tại thời điểm chạy)
  - Append vào spot_tape_1d store (parquet, date+venue partitioned)

Config: data/config/tape_targets.json
  [{"symbol": "BR", "venue": "gate", "pair": "BR_USDT", "enabled_date": "2026-07-30"}]

Forward-only: không fetch trước enabled_date. Ghi rõ ngày bật trong log.
BẬT ĐẦU TIÊN: BR@Gate (xem config mẫu bên dưới).

Storage schema (spot_tape_1d):
    symbol, venue, date_str,
    n_trades, total_usd, buy_usd, sell_usd,
    taker_buy_pct, cvd_usd,
    size_p50_usd, size_p90_usd, size_cv,
    bid_wall_px, bid_wall_usd, ask_wall_px, ask_wall_usd,
    book_snapshot_ts, fetched_at_ms, schema_version

Cron: 01:15 UTC daily (sau spot candle đóng + collect_spot_daily xong).

Usage:
    python scripts/collect_tape.py
    python scripts/collect_tape.py --date 2026-07-29
    python scripts/collect_tape.py --target BR@gate
    python scripts/collect_tape.py --dry-run
"""

from __future__ import annotations

import asyncio
import json
import statistics as st
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, date as date_type
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, RAW_DIR, SCHEMA_VERSION, COMPRESSION, COMPRESSION_LEVEL,
)
from whale_collector.timeutil import now_ms, ms_to_date_str
from whale_collector.storage.paths import spot_tape_partition_path

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

TAPE_CONFIG = RAW_DIR.parent / "config" / "tape_targets.json"
DAY_S = 86_400

# Đặc tả mẫu cho tape_targets.json (tự động tạo nếu chưa có)
_DEFAULT_CONFIG = [
    {
        "symbol": "BR",
        "venue": "gate",
        "pair": "BR_USDT",
        "enabled_date": "2026-07-30",
        "active": True,
    }
]

_TAPE_COLS = [
    "symbol", "venue", "date_str",
    "n_trades", "total_usd", "buy_usd", "sell_usd",
    "taker_buy_pct", "cvd_usd",
    "size_p50_usd", "size_p90_usd", "size_cv",
    "bid_wall_px", "bid_wall_usd", "ask_wall_px", "ask_wall_usd",
    "book_snapshot_ts", "fetched_at_ms", "schema_version",
]

_partition_locks: dict[str, asyncio.Lock] = {}


def _get_lock(path: Path) -> asyncio.Lock:
    key = str(path)
    if key not in _partition_locks:
        _partition_locks[key] = asyncio.Lock()
    return _partition_locks[key]


def _sync_append(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        df = pd.concat([existing, df], ignore_index=True)
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        path, compression=COMPRESSION, compression_level=COMPRESSION_LEVEL,
    )


async def _write_tape_partition(df: pd.DataFrame, venue: str, date_str: str) -> None:
    if df.empty:
        return
    path = spot_tape_partition_path(venue, date_str)
    lock = _get_lock(path)
    async with lock:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_append, df, path)


def _load_config() -> list[dict]:
    if not TAPE_CONFIG.exists():
        TAPE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        TAPE_CONFIG.write_text(json.dumps(_DEFAULT_CONFIG, indent=2), encoding="utf-8")
        log.info("tape_config_created", path=str(TAPE_CONFIG))
    with TAPE_CONFIG.open(encoding="utf-8") as f:
        return json.load(f)


# ─── Gate.io tape fetcher ─────────────────────────────────────────────────────

def _gate_get(path: str, params: dict, retries: int = 3) -> list:
    """Synchronous Gate API GET (runs in thread pool). Returns parsed JSON."""
    base = "https://api.gateio.ws/api/v4"
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base}{path}?{qs}" if qs else f"{base}{path}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "tape-collector/1.0"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code == 404:
                raise ValueError(f"Gate 404: {path} {params} → {body}")
            if attempt == retries - 1:
                raise RuntimeError(f"Gate HTTP {e.code}: {body}")
            time.sleep(1.5)
        except Exception as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Gate network error: {exc}") from exc
            time.sleep(1.5)
    return []


def _gate_pull_trades(pair: str, day_start_s: int, day_end_s: int) -> list[dict]:
    """Pull all public trades for [day_start_s, day_end_s) via last_id pagination."""
    all_trades: list[dict] = []
    last_id: Optional[str] = None
    LIMIT = 1000
    max_pages = 300  # 300k trades max — more than enough for any Gate pair

    for _page in range(max_pages):
        params: dict = {
            "currency_pair": pair,
            "limit": LIMIT,
            "from": day_start_s,
            "to": day_end_s,
        }
        if last_id is not None:
            params["last_id"] = last_id

        batch = _gate_get("/spot/trades", params)
        if not batch:
            break

        # Gate from/to is inclusive and approximate — filter strictly
        batch_ok = [
            t for t in batch
            if day_start_s <= int(float(t.get("create_time", 0))) < day_end_s
        ]
        all_trades.extend(batch_ok)

        if len(batch) < LIMIT:
            break

        # Cursor: smallest trade ID on this page = oldest = next page end boundary
        min_id = min(int(t["id"]) for t in batch)
        if last_id is not None and min_id >= int(last_id):
            break  # cursor not advancing — stop
        last_id = str(min_id - 1)
        time.sleep(0.06)
    else:
        log.warning("tape_gate_max_pages", pair=pair, max_pages=max_pages)

    return all_trades


def _gate_book_snapshot(pair: str, depth: int = 20) -> dict:
    """Return order book walls within ±5% of mid."""
    book = _gate_get("/spot/order_book", {"currency_pair": pair, "depth": depth, "with_id": "true"})
    bids = [(float(p), float(a)) for p, a in book.get("bids", [])]
    asks = [(float(p), float(a)) for p, a in book.get("asks", [])]
    if not bids or not asks:
        return {"bid_wall_px": None, "bid_wall_usd": None,
                "ask_wall_px": None, "ask_wall_usd": None}

    mid = (bids[0][0] + asks[0][0]) / 2
    lo5, hi5 = mid * 0.95, mid * 1.05
    bids_5 = [(p, a) for p, a in bids if p >= lo5]
    asks_5 = [(p, a) for p, a in asks if p <= hi5]

    # Wall = single order with largest USD value within ±5%
    bid_wall = max(bids_5, key=lambda x: x[0] * x[1]) if bids_5 else (None, None)
    ask_wall = max(asks_5, key=lambda x: x[0] * x[1]) if asks_5 else (None, None)

    return {
        "bid_wall_px":  bid_wall[0],
        "bid_wall_usd": bid_wall[0] * bid_wall[1] if bid_wall[0] else None,
        "ask_wall_px":  ask_wall[0],
        "ask_wall_usd": ask_wall[0] * ask_wall[1] if ask_wall[0] else None,
    }


def _aggregate_trades(trades: list[dict]) -> dict:
    """Compute takerBUY%, CVD, size p50/p90/CV from a list of Gate trade dicts."""
    if not trades:
        return {
            "n_trades": 0, "total_usd": 0.0, "buy_usd": 0.0, "sell_usd": 0.0,
            "taker_buy_pct": float("nan"), "cvd_usd": 0.0,
            "size_p50_usd": float("nan"), "size_p90_usd": float("nan"), "size_cv": float("nan"),
        }

    buy_usd = 0.0; sell_usd = 0.0; sizes = []
    for t in trades:
        amt = float(t.get("amount", 0))
        px  = float(t.get("price", 0))
        usd = amt * px
        sizes.append(usd)
        if t.get("side") == "buy":
            buy_usd += usd
        else:
            sell_usd += usd

    total = buy_usd + sell_usd
    sorted_s = sorted(sizes)
    n = len(sorted_s)
    p50 = sorted_s[n // 2] if n else float("nan")
    p90 = sorted_s[int(n * 0.9)] if n else float("nan")
    mean_s = st.mean(sizes) if sizes else 0
    std_s  = st.stdev(sizes) if len(sizes) > 1 else 0
    cv     = std_s / mean_s if mean_s > 0 else float("nan")

    return {
        "n_trades": len(trades),
        "total_usd": total,
        "buy_usd": buy_usd,
        "sell_usd": sell_usd,
        "taker_buy_pct": buy_usd / total if total > 0 else float("nan"),
        "cvd_usd": buy_usd - sell_usd,
        "size_p50_usd": p50,
        "size_p90_usd": p90,
        "size_cv": cv,
    }


# ─── Per-target collection ────────────────────────────────────────────────────

async def _collect_target(
    target: dict,
    date_str: str,
    day_start_s: int,
    day_end_s: int,
    fetched_at: int,
) -> tuple[str, bool, str]:
    """Run tape collection for one target. Returns (label, ok, msg)."""
    sym = target["symbol"]; venue = target["venue"]; pair = target["pair"]
    label = f"{sym}@{venue}"

    # Forward-only guard
    enabled_date = target.get("enabled_date", "2000-01-01")
    if date_str < enabled_date:
        msg = f"before enabled_date {enabled_date} — skipping (forward-only)"
        log.info("tape_forward_only_skip", target=label, date=date_str, enabled=enabled_date)
        return label, False, msg

    loop = asyncio.get_running_loop()

    try:
        if venue == "gate":
            trades = await loop.run_in_executor(
                None, _gate_pull_trades, pair, day_start_s, day_end_s
            )
            agg = _aggregate_trades(trades)
            book = await loop.run_in_executor(None, _gate_book_snapshot, pair)
        else:
            return label, False, f"unsupported venue: {venue}"
    except Exception as exc:
        log.error("tape_collect_error", target=label, date=date_str, error=str(exc))
        return label, False, str(exc)

    book_ts = int(time.time())
    row = {
        "symbol": sym, "venue": venue, "date_str": date_str,
        **agg, **book,
        "book_snapshot_ts": book_ts,
        "fetched_at_ms": fetched_at,
        "schema_version": SCHEMA_VERSION,
    }
    df = pd.DataFrame([row], columns=_TAPE_COLS)
    await _write_tape_partition(df, venue, date_str)

    log.info("tape_done",
             target=label, date=date_str,
             n_trades=agg["n_trades"],
             taker_buy_pct=f"{agg['taker_buy_pct']:.3f}" if agg["taker_buy_pct"] == agg["taker_buy_pct"] else "nan",
             cvd=f"{agg['cvd_usd']:+,.0f}")
    return label, True, "ok"


# ─── Main ─────────────────────────────────────────────────────────────────────

async def run_tape(
    *,
    target_date: Optional[str] = None,
    target_filter: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    now_utc = datetime.now(timezone.utc)
    now = now_ms()

    # Resolve date (default = yesterday UTC)
    if target_date:
        day_start_s = int(datetime.strptime(target_date, "%Y-%m-%d")
                          .replace(tzinfo=timezone.utc).timestamp())
        date_str = target_date
    else:
        day_start_s = (int(now / 1000) // DAY_S - 1) * DAY_S
        date_str = datetime.fromtimestamp(day_start_s, timezone.utc).strftime("%Y-%m-%d")

    day_end_s = day_start_s + DAY_S
    log.info("tape_start", date=date_str, utc=now_utc.strftime("%Y-%m-%d %H:%M"))

    targets = _load_config()
    if target_filter:
        sym_f, _, venue_f = target_filter.lower().partition("@")
        targets = [
            t for t in targets
            if t["symbol"].lower() == sym_f
            and (not venue_f or t["venue"].lower() == venue_f)
        ]

    active = [t for t in targets if t.get("active", True)]
    log.info("tape_targets", active=len(active))

    if dry_run:
        for t in active:
            log.info("dry_run_target", symbol=t["symbol"], venue=t["venue"],
                     pair=t["pair"], enabled=t.get("enabled_date", "—"))
        return 0

    results = await asyncio.gather(
        *[_collect_target(t, date_str, day_start_s, day_end_s, now) for t in active],
        return_exceptions=True,
    )

    ok_count = 0; err_count = 0
    for res in results:
        if isinstance(res, Exception):
            err_count += 1
            log.error("tape_task_exception", error=str(res))
        else:
            _, ok, _ = res
            if ok:
                ok_count += 1
            else:
                err_count += 1

    log.info("tape_complete", ok=ok_count, errors=err_count)
    return 0 if err_count == 0 else 1


@app.command()
def main(
    date: Optional[str] = typer.Option(None, help="Date YYYY-MM-DD (default=yesterday)"),
    target: Optional[str] = typer.Option(None, help="Filter target e.g. BR@gate"),
    dry_run: bool = typer.Option(False, help="Validate config — no API calls"),
) -> None:
    """E4: Collect daily tape aggregate per symbol/venue (takerBUY%, CVD, walls)."""
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ])
    exit_code = asyncio.run(run_tape(
        target_date=date,
        target_filter=target,
        dry_run=dry_run,
    ))
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()

"""Universe builder: all Binance USD-M Futures TRADING pairs; CoinGecko for mcap enrichment only."""

from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp
import pandas as pd
import structlog

from whale_collector.coingecko.universe import fetch_top_markets, build_symbol_to_mc_map
from whale_collector.timeutil import now_ms, ms_to_date_str
from whale_collector.config import (
    MAX_MC_USD, MIN_MC_USD, UNIVERSE_TOP_N,
    BINANCE_FUTURES_BASE, COINGECKO_API_KEY, EXCLUDED_SYMBOLS,
)

log = structlog.get_logger()

# MC tier boundaries from spec §2.3 — DO NOT change
MC_TIERS = [
    (25_000_000,    "1_nano"),
    (50_000_000,    "2_micro"),
    (100_000_000,   "3_small"),
    (200_000_000,   "4_mid_small"),
    (500_000_000,   "5_mid"),
    (1_000_000_000, "6_large"),
]

def assign_mc_tier(mc_usd: float) -> str:
    for threshold, tier in MC_TIERS:
        if mc_usd < threshold:
            return tier
    return "7_xlarge"


async def fetch_exchange_info(session: aiohttp.ClientSession) -> dict[str, dict]:
    """Fetch Binance USD-M Futures PERPETUAL USDT pairs. Returns {symbol: {status, onboard_ms}}."""
    url = f"{BINANCE_FUTURES_BASE}/fapi/v1/exchangeInfo"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        resp.raise_for_status()
        data = await resp.json()

    result: dict[str, dict] = {}
    for s in data.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            result[s["symbol"]] = {
                "status": s.get("status", ""),
                "onboard_ms": int(s.get("onboardDate", 0)),
            }
    log.info("exchange_info_fetched", futures_pairs=len(result))
    return result


async def select_universe(
    *,
    session: Optional[aiohttp.ClientSession] = None,
    require_status: str = "TRADING",
    coingecko_api_key: str = COINGECKO_API_KEY,
    cg_pages: int = 8,
    # Legacy params kept for call-site compat — no longer used for filtering
    max_mc_usd: int = MAX_MC_USD,
    min_mc_usd: int = MIN_MC_USD,
    top_n: int = UNIVERSE_TOP_N,
) -> tuple[pd.DataFrame, dict[str, dict]]:
    """Build today's universe = ALL exchangeInfo TRADING USDT-PERP pairs.

    CoinGecko is used ONLY for mcap enrichment (nullable, fail-tolerant).
    Cap/rank filters removed per W1 approval 2026-07-25.

    Returns (snapshot_df, exchange_info_raw).
    exchange_info_raw is the full {symbol: {status, onboard_ms}} dict — callers can
    reuse it for universe_master logic without a second HTTP call.
    """
    now = now_ms()
    today = ms_to_date_str(now)

    _own_session = session is None
    if _own_session:
        _session = aiohttp.ClientSession()
    else:
        _session = session

    try:
        binance_pairs = await fetch_exchange_info(_session)

        cg_mc_map: dict[str, dict] = {}
        try:
            cg_entries = await fetch_top_markets(_session, pages=cg_pages,
                                                  api_key=coingecko_api_key)
            # build_symbol_to_mc_map keys are uppercase CG ticker (e.g. "BTC")
            cg_mc_map = build_symbol_to_mc_map(cg_entries)
        except Exception as exc:
            log.warning("coingecko_enrichment_failed", error=str(exc))
    finally:
        if _own_session:
            await _session.close()

    rows: list[dict] = []

    for binance_sym, bi in binance_pairs.items():
        if bi["status"] != require_status:
            continue
        if binance_sym in EXCLUDED_SYMBOLS:
            continue

        onboard_ms = bi["onboard_ms"]
        days_listed = int((now - onboard_ms) / 86_400_000) if onboard_ms > 0 else 0

        # CG enrichment: strip USDT suffix to match CG symbol (heuristic, nullable)
        cg_sym = binance_sym.removesuffix("USDT")
        cg = cg_mc_map.get(cg_sym, {})
        mc = float(cg.get("market_cap_usd") or 0)

        rows.append({
            "as_of_date": today,
            "symbol": binance_sym,
            "coingecko_id": cg.get("id", "") or "",
            "coingecko_name": "",
            "market_cap_usd": int(mc) if mc > 0 else None,
            "mc_rank": int(cg.get("market_cap_rank") or 0) or None,
            "mc_tier": assign_mc_tier(mc) if mc > 0 else None,
            "binance_status": bi["status"],
            "binance_onboard_ms": int(onboard_ms),
            "days_since_listing": days_listed,
            "fetched_at_ms": int(now),
        })

    df = pd.DataFrame(rows)
    log.info("universe_selected", n=len(df), today=today)
    return df, binance_pairs

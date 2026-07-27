"""Async HTTP client for Binance Futures public endpoints."""

import asyncio
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional

import aiohttp
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

log = structlog.get_logger()


class RateLimiter:
    """Rolling 60-second window rate limiter for Binance Futures API weight budget."""

    def __init__(self, max_weight_per_min: int = 2000):
        self.max_weight = max_weight_per_min
        self._window: deque = deque()  # (monotonic_ts, weight)
        self._lock = asyncio.Lock()

    async def acquire(self, weight: int) -> None:
        """Block until 'weight' more units fit within the rolling 60s window."""
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._window and self._window[0][0] < now - 60.0:
                    self._window.popleft()

                current = sum(w for _, w in self._window)
                if current + weight <= self.max_weight:
                    self._window.append((time.monotonic(), weight))
                    return

                # Wait until the oldest entry expires
                sleep_for = (self._window[0][0] + 60.1) - now if self._window else 1.0
                sleep_for = max(0.05, sleep_for)
                self._lock.release()
                try:
                    await asyncio.sleep(sleep_for)
                finally:
                    await self._lock.acquire()


class FetchLogger:
    """Accumulates API call records in memory; flushes to parquet at run end."""

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def log_call(
        self,
        *,
        endpoint: str,
        symbol: Optional[str],
        params: dict,
        status: int,
        attempt_n: int,
        error_class: Optional[str],
        fetched_at_ms: int,
        rows_returned: int = 0,
    ) -> None:
        # Redact any key-like params
        safe_params = {k: v for k, v in params.items() if k.lower() not in ("apikey", "signature", "recvwindow", "timestamp")}
        self._rows.append({
            "endpoint": endpoint,
            "symbol": symbol or "",
            "params_json": str(safe_params),
            "status": status,
            "attempt_n": attempt_n,
            "error_class": error_class or "",
            "fetched_at_ms": fetched_at_ms,
            "rows_returned": rows_returned,
        })

    def flush(self, path: Path) -> None:
        if not self._rows:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        df_new = pd.DataFrame(self._rows)
        df_new["fetched_at_ms"] = df_new["fetched_at_ms"].astype("int64")

        if path.exists():
            df_existing = pd.read_parquet(path)
            df_new = pd.concat([df_existing, df_new], ignore_index=True)

        table = pa.Table.from_pandas(df_new, preserve_index=False)
        pq.write_table(table, path, compression="zstd", compression_level=3)
        self._rows = []


class BinanceClient:
    """Async HTTP client for Binance Futures public endpoints.

    Retry policy per spec §3.4:
      429 → sleep Retry-After (or 60s), retry up to 5x
      418 → raise RuntimeError immediately (IP ban)
      5xx → exponential backoff 2/4/8/16s, max 4 retries
      400 → raise ValueError (bad symbol/params — caller skips symbol)
      timeout (30s) → retry up to 3x with 10s sleep

    futures_data_limiter: separate budget for /futures/data/* pool (distinct from
    the general fapi pool). Pass a RateLimiter at ~500/min to avoid saturating the
    data-endpoint pool under high concurrency.
    """

    def __init__(
        self,
        rate_limiter: RateLimiter,
        fetch_logger: Optional[FetchLogger] = None,
        base_url: str = "https://fapi.binance.com",
        futures_data_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.rate_limiter = rate_limiter
        self.futures_data_limiter = futures_data_limiter
        self.fetch_logger = fetch_logger
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "BinanceClient":
        self._session = aiohttp.ClientSession(
            base_url=self.base_url,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "WhaleCollector/0.1"},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def get(self, path: str, params: dict, weight: int = 1) -> dict | list:
        """Fetch path with params. Blocks on rate limiter; retries per policy.

        Uses futures_data_limiter for /futures/data/* paths when set; otherwise
        falls back to rate_limiter.

        Raises:
            ValueError: on 400 Bad Request (bad symbol — caller should skip)
            RuntimeError: on 418 (IP ban) or exhausted retries
        """
        limiter = (
            self.futures_data_limiter
            if self.futures_data_limiter is not None and path.startswith("/futures/data/")
            else self.rate_limiter
        )
        await limiter.acquire(weight)
        fetched_at_ms = int(time.time() * 1000)

        timeout_retries = 0
        server_retries = 0
        rate_retries = 0

        for attempt in range(10):  # outer bound; logic drives breaks
            try:
                async with self._session.get(path, params=params) as resp:
                    status = resp.status

                    if status == 200:
                        data = await resp.json()
                        if self.fetch_logger:
                            n = len(data) if isinstance(data, list) else 1
                            self.fetch_logger.log_call(
                                endpoint=path, symbol=params.get("symbol"),
                                params=params, status=200, attempt_n=attempt,
                                error_class=None, fetched_at_ms=fetched_at_ms,
                                rows_returned=n,
                            )
                        return data

                    elif status == 429:
                        rate_retries += 1
                        if rate_retries > 5:
                            raise RuntimeError(f"Rate limited 5x on {path}")
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        log.warning("binance_rate_limited", path=path, retry_after=retry_after, attempt=attempt)
                        if self.fetch_logger:
                            self.fetch_logger.log_call(
                                endpoint=path, symbol=params.get("symbol"),
                                params=params, status=429, attempt_n=attempt,
                                error_class="RateLimit", fetched_at_ms=fetched_at_ms,
                            )
                        await asyncio.sleep(retry_after)
                        continue

                    elif status == 418:
                        log.error("binance_ip_banned", path=path)
                        if self.fetch_logger:
                            self.fetch_logger.log_call(
                                endpoint=path, symbol=params.get("symbol"),
                                params=params, status=418, attempt_n=attempt,
                                error_class="IPBan", fetched_at_ms=fetched_at_ms,
                            )
                        raise RuntimeError("Binance IP ban (418) — aborting run")

                    elif status == 400:
                        body = await resp.text()
                        log.warning("binance_bad_request", path=path, symbol=params.get("symbol"), body=body[:200])
                        if self.fetch_logger:
                            self.fetch_logger.log_call(
                                endpoint=path, symbol=params.get("symbol"),
                                params=params, status=400, attempt_n=attempt,
                                error_class="BadRequest", fetched_at_ms=fetched_at_ms,
                            )
                        raise ValueError(f"400 Bad Request: {body[:200]}")

                    elif status >= 500:
                        server_retries += 1
                        if server_retries > 4:
                            raise RuntimeError(f"Server errors (5xx) after 4 retries: {path}")
                        backoff = [2, 4, 8, 16][min(server_retries - 1, 3)]
                        log.warning("binance_server_error", path=path, status=status, backoff=backoff)
                        if self.fetch_logger:
                            self.fetch_logger.log_call(
                                endpoint=path, symbol=params.get("symbol"),
                                params=params, status=status, attempt_n=attempt,
                                error_class="ServerError", fetched_at_ms=fetched_at_ms,
                            )
                        await asyncio.sleep(backoff)
                        continue

                    else:
                        body = await resp.text()
                        raise RuntimeError(f"Unexpected HTTP {status}: {body[:100]}")

            except asyncio.TimeoutError as exc:
                timeout_retries += 1
                if timeout_retries > 3:
                    raise RuntimeError(f"Timeout after 3 retries: {path}") from exc
                log.warning("binance_timeout", path=path, attempt=attempt)
                if self.fetch_logger:
                    self.fetch_logger.log_call(
                        endpoint=path, symbol=params.get("symbol"),
                        params=params, status=0, attempt_n=attempt,
                        error_class="Timeout", fetched_at_ms=fetched_at_ms,
                    )
                await asyncio.sleep(10)
                continue

            except aiohttp.ClientError as exc:
                log.warning("binance_client_error", path=path, error=str(exc), attempt=attempt)
                if self.fetch_logger:
                    self.fetch_logger.log_call(
                        endpoint=path, symbol=params.get("symbol"),
                        params=params, status=0, attempt_n=attempt,
                        error_class=type(exc).__name__, fetched_at_ms=fetched_at_ms,
                    )
                if attempt < 2:
                    await asyncio.sleep(10)
                    continue
                raise RuntimeError(f"Network error after retries: {path}") from exc

            except (ValueError, RuntimeError):
                raise

        raise RuntimeError(f"Exhausted retry attempts for {path}")

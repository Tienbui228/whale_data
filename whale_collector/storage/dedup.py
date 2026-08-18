"""Canonical dedup key — MỘT NGUỒN cho writer & reader (chống fork key).

Verified by _probe_oi_dup_v1v2v3_20260818 (V1c):
  as_of_ts_ms là BAR-TIME (khớp ở dup rows); fetched_at_ms là FETCH-TIME (khác).
  Data fields IDENTICAL ở dup rows → drop_duplicates(keep="last") an toàn.

Schema check (V2) — cả 3 metric có cùng key:
  oi_hist_1h · taker_ratio_1h · klines_1h  đều có [symbol, as_of_ts_ms].

Editing this constant = phá cả write + read semantics.
"""

DEDUP_KEY: list[str] = ["symbol", "as_of_ts_ms"]

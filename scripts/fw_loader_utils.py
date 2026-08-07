"""Shared loader utilities for freshwatch CSV data.

Single source of truth for taker_buy_pct scale detection.
freshwatch stores taker as decimal fraction (0.47 = 47%).
signals.py and gom_scan expect percentage (47.0).
"""
from __future__ import annotations
import math
import sys
from typing import Iterable


def taker_scale_check(
    tok: str,
    raw_values: Iterable[float],
    *,
    log=None,
) -> float:
    """Inspect raw taker_buy_pct values; return scale factor (1.0 or 100.0).

    Rules:
    - max(raw) ≤ 1.0 → fraction format → return 100.0 + log WARNING
    - max(raw) > 1.0 and min(raw) > 1.0 → pct format → return 1.0 + log WARNING
    - mixed (max > 1.0 and min ≤ 1.0) → raise ValueError (cannot auto-correct)
    - empty → return 100.0 (freshwatch convention default)
    """
    vals = [v for v in raw_values if not (v != v)]  # drop NaN
    if not vals:
        return 100.0

    mx, mn = max(vals), min(vals)

    if mx > 1.0 and mn < 1.0:
        raise ValueError(
            f"TRIPWIRE [{tok}]: mixed taker_buy_pct scale "
            f"(min={mn:.4f}, max={mx:.4f}) — cannot auto-convert"
        )

    if mx > 1.0:
        msg = f"TRIPWIRE [{tok}]: taker max={mx:.2f} > 1 → already pct, no ×100"
        if log is not None:
            log.warning("taker_scale_pct_unexpected", token=tok,
                        max=round(mx, 2), hint="already pct — ×100 not applied")
        else:
            print(f"WARNING {msg}", file=sys.stderr)
        return 1.0

    msg = f"TRIPWIRE [{tok}]: taker max={mx:.4f} ≤ 1 → fraction, ×100 applied"
    if log is not None:
        log.warning("taker_scale_fraction_converted", token=tok,
                    max=round(mx, 4), hint="decimal→pct ×100 applied")
    else:
        print(f"WARNING {msg}", file=sys.stderr)
    return 100.0


def taker_scale_check_dict_rows(
    tok: str,
    rows: Iterable[dict],
    field: str = "taker_buy_pct",
    *,
    log=None,
) -> float:
    """Convenience wrapper: extract `field` from each row dict, then call taker_scale_check."""
    raw = []
    for row in rows:
        v = row.get(field, "")
        try:
            fv = float(v)
            if not math.isnan(fv):
                raw.append(fv)
        except (TypeError, ValueError):
            pass
    return taker_scale_check(tok, raw, log=log)

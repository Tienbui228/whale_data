#!/usr/bin/env python3
"""[F5(c)] vol_guard_daily.py — daily store-vs-fresh-k[7] ±2% guard.

Operator ký chat 21/08 (P0-STORE-VOL-DUP-20260821):
  "Guard hàng ngày store-vs-k[7] ±2% → Telegram + exit≠0 (đường độc lập L-28:
   k[7] raw ≠ đường aggregate)"

Chạy TRƯỚC scripts/post_export_csv_commit.sh mỗi ngày (before 01:20 UTC).
Cron entry đề xuất:
  15 1 * * * cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/vol_guard_daily.py \
             --date $(date -u -d yesterday +%%Y-%%m-%%d) >> data/logs/vol_guard.log 2>&1

Semantics:
  - Fetch fresh k[7] from fapi cho fw-139 universe (~12s)
  - So sánh store DEDUP sum(quote_volume) vs fresh k[7] cho date target
  - Nếu ratio ∈ [0.98, 1.02] → OK, exit 0
  - Nếu ANY symbol ngoài dải → Telegram alert + exit 1 (block downstream cron)

Đường raw fapi ĐỘC LẬP với đường store aggregate — L-28 luật hai-nguồn-độc-lập.
"""
from __future__ import annotations
import os, sys, json, argparse, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

# Local imports guarded (script chạy khi VPS có .venv)
try:
    from whale_collector.config import RAW_DIR
except ImportError:
    RAW_DIR = Path("/root/Data_back_test/whale_data/data/raw")

UNIVERSE_PATH = Path("/root/Data_back_test/whale_data/data/config/freshwatch_symbols.txt")
FAPI_KLINES = "https://fapi.binance.com/fapi/v1/klines"

RATIO_MIN = 0.98
RATIO_MAX = 1.02


def _midnight_ms(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _fetch_fresh_k7(symbol: str, date_str: str) -> float | None:
    """Fetch fresh k[7] quote_volume from fapi 1d klines."""
    start_ms = _midnight_ms(date_str)
    end_ms = start_ms + 86_400_000 - 1
    q = urllib.parse.urlencode({
        "symbol": symbol, "interval": "1d",
        "startTime": start_ms, "endTime": end_ms, "limit": 2,
    })
    url = f"{FAPI_KLINES}?{q}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        if not data:
            return None
        return float(data[0][7])
    except Exception:
        return None


def _store_dedup_sum(symbol: str, date_str: str) -> float | None:
    """Read klines_1h store partition for date, dedup, sum quote_volume."""
    p = RAW_DIR / "klines_1h" / f"date={date_str}" / "part-0.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df = df[df["symbol"] == symbol]
    if df.empty:
        return None
    df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="last")
    return float(df["quote_volume"].sum())


def _load_universe() -> list[str]:
    if not UNIVERSE_PATH.exists():
        return []
    return sorted({
        l.strip() for l in UNIVERSE_PATH.read_text().splitlines()
        if l.strip() and not l.startswith("#")
    })


def _send_telegram(text: str) -> bool:
    """Send Telegram message using env credentials."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("WARN: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skip send",
              file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text,
    }).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=10) as r:
            return r.status == 200
    except Exception as exc:
        print(f"TG send failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (yesterday UTC recommended)")
    ap.add_argument("--top-n", type=int, default=0,
                    help="Limit to top-N vol symbols (0 = all fw-139)")
    ap.add_argument("--ratio-min", type=float, default=RATIO_MIN)
    ap.add_argument("--ratio-max", type=float, default=RATIO_MAX)
    ap.add_argument("--dry-run", action="store_true",
                    help="Log only, no Telegram, no exit≠0")
    args = ap.parse_args()

    symbols = _load_universe()
    if not symbols:
        print(f"ERROR: universe empty at {UNIVERSE_PATH}", file=sys.stderr)
        return 2

    print(f"[VOL-GUARD] date={args.date} n_symbols={len(symbols)} "
          f"ratio_band=[{args.ratio_min:.3f}, {args.ratio_max:.3f}]")

    violations = []
    n_missing_store = 0
    n_missing_fresh = 0
    checked = 0

    for sym in symbols:
        store_v = _store_dedup_sum(sym, args.date)
        if store_v is None:
            n_missing_store += 1
            continue
        fresh_v = _fetch_fresh_k7(sym, args.date)
        if fresh_v is None:
            n_missing_fresh += 1
            continue
        if fresh_v <= 0:
            continue
        ratio = store_v / fresh_v
        checked += 1
        if ratio < args.ratio_min or ratio > args.ratio_max:
            violations.append({
                "sym": sym, "store": store_v, "fresh": fresh_v, "ratio": ratio,
            })

    print(f"[VOL-GUARD] checked={checked} violations={len(violations)} "
          f"missing_store={n_missing_store} missing_fresh={n_missing_fresh}")

    if not violations:
        print(f"[VOL-GUARD] OK — all {checked} symbols within ±{(1-args.ratio_min)*100:.1f}%")
        return 0

    # Format violation report
    lines = [
        f"🚨 [VOL-GUARD FAIL] {args.date} — {len(violations)} symbol(s) out of ±{(1-args.ratio_min)*100:.1f}% band",
        f"    (store DEDUP sum vs fapi k[7] fresh)",
        f"",
        f"{'sym':>16}  {'store':>18}  {'fresh':>18}  {'ratio':>8}",
    ]
    for v in sorted(violations, key=lambda x: abs(x["ratio"] - 1.0), reverse=True)[:20]:
        lines.append(f"{v['sym']:>16}  {v['store']:>18,.0f}  {v['fresh']:>18,.0f}  {v['ratio']:>8.4f}")
    if len(violations) > 20:
        lines.append(f"    ... +{len(violations)-20} more")
    lines.append(f"")
    lines.append(f"REF: docs/reports/_p0_store_vol_dup_forensics_20260821.md")
    lines.append(f"     Downstream cron BLOCKED (exit 1) — fix source hoặc rebuild trước khi ghi CSV.")

    msg = "\n".join(lines)
    print(msg)

    if args.dry_run:
        print(f"[VOL-GUARD] DRY-RUN mode: exit 0 (no Telegram, no block)")
        return 0

    sent = _send_telegram(msg)
    print(f"[VOL-GUARD] Telegram sent: {sent}")
    return 1   # block downstream cron


if __name__ == "__main__":
    sys.exit(main())

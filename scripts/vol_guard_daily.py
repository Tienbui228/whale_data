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

# [R5 F5c-ext-20260824] extended reconcile: pos_r, acc_r, gLSR, OI cạnh vol
# Tolerance relative 2% PROVISIONAL (đặt lại từ phân bố khi chạy lần đầu).
# Ref operator ký chat 24/08 ⑦: "guard reconcile hàng ngày thêm pos_r/acc_r/gLSR/OI
#   cạnh vol, tolerance relative 2% PROVISIONAL, lệch → Telegram + exit≠0."
LSR_OI_RATIO_MIN = 0.98
LSR_OI_RATIO_MAX = 1.02
LSR_OI_METRICS = ["lsr_pos", "lsr_acc", "lsr_global", "oi_hist"]

FAPI_TOP_POS = "https://fapi.binance.com/futures/data/topLongShortPositionRatio"
FAPI_TOP_ACCT = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
FAPI_RETAIL = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
FAPI_OI_HIST = "https://fapi.binance.com/futures/data/openInterestHist"


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


# [R5 F5c-ext-20260824] LSR + OI reconcile helpers
def _store_lsr_oi(symbol: str, date_str: str, metric: str) -> float | None:
    """Read 1d parquet for metric, return latest value for symbol on date_str.
    metric ∈ {"top_pos_1d","top_acct_1d","retail_global_1d","oi_hist_1d"}
    """
    p = RAW_DIR / metric / f"date={date_str}"
    if not p.exists():
        return None
    files = list(p.glob("*.parquet"))
    if not files: return None
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    if df.empty or "symbol" not in df.columns: return None
    df = df[df["symbol"] == symbol]
    if df.empty: return None
    # Prefer long_short_ratio (LSR metrics) or sum_open_interest_value (OI)
    for col in ("long_short_ratio", "sum_open_interest_value"):
        if col in df.columns:
            v = df[col].iloc[-1]
            try:
                fv = float(v)
                if fv == fv: return fv
            except: pass
    return None


def _fetch_fresh_lsr(url: str, symbol: str, date_str: str, field: str) -> float | None:
    """Fetch fresh 1d LSR/OI from fapi. Returns float or None."""
    start_ms = _midnight_ms(date_str)
    end_ms = start_ms + 86_400_000 - 1
    q = urllib.parse.urlencode({
        "symbol": symbol, "period": "1d",
        "startTime": start_ms, "endTime": end_ms, "limit": 2,
    })
    fetch_url = f"{url}?{q}"
    try:
        with urllib.request.urlopen(fetch_url, timeout=10) as r:
            data = json.loads(r.read())
        if not data: return None
        row = data[0]
        v = row.get(field)
        if v is None: return None
        return float(v)
    except Exception:
        return None


_FAPI_MAP = {
    "lsr_pos":    (FAPI_TOP_POS,   "longShortRatio", "top_pos_1d"),
    "lsr_acc":    (FAPI_TOP_ACCT,  "longShortRatio", "top_acct_1d"),
    "lsr_global": (FAPI_RETAIL,    "longShortRatio", "retail_global_1d"),
    "oi_hist":    (FAPI_OI_HIST,   "sumOpenInterestValue", "oi_hist_1d"),
}


def _reconcile_metric(symbol: str, date_str: str, metric: str) -> tuple[float, float, float] | None:
    """Return (store_v, fresh_v, ratio) or None if either missing."""
    fapi_url, field, store_partition = _FAPI_MAP[metric]
    store_v = _store_lsr_oi(symbol, date_str, store_partition)
    if store_v is None: return None
    fresh_v = _fetch_fresh_lsr(fapi_url, symbol, date_str, field)
    if fresh_v is None or fresh_v <= 0: return None
    return (store_v, fresh_v, store_v / fresh_v)


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
    ap.add_argument("--lsr-oi-ratio-min", type=float, default=LSR_OI_RATIO_MIN,
                    help="[R5 F5c-ext] LSR/OI ratio min PROVISIONAL 2%")
    ap.add_argument("--lsr-oi-ratio-max", type=float, default=LSR_OI_RATIO_MAX)
    ap.add_argument("--enable-lsr-oi", action="store_true",
                    help="[R5 F5c-ext] Enable LSR + OI reconcile (extended guard)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Log only, no Telegram, no exit≠0")
    args = ap.parse_args()

    symbols = _load_universe()
    if not symbols:
        print(f"ERROR: universe empty at {UNIVERSE_PATH}", file=sys.stderr)
        return 2

    print(f"[VOL-GUARD] date={args.date} n_symbols={len(symbols)} "
          f"ratio_band=[{args.ratio_min:.3f}, {args.ratio_max:.3f}]")
    if args.enable_lsr_oi:
        print(f"[VOL-GUARD R5 F5c-ext] LSR+OI reconcile ENABLED band=[{args.lsr_oi_ratio_min:.3f}, {args.lsr_oi_ratio_max:.3f}] PROVISIONAL")

    violations = []
    lsr_oi_violations = []   # [R5 F5c-ext]
    lsr_oi_distribution = {m: [] for m in LSR_OI_METRICS}   # collect first-run relative diffs
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

        # [R5 F5c-ext] LSR + OI reconcile per symbol (nếu --enable-lsr-oi)
        if args.enable_lsr_oi:
            for m in LSR_OI_METRICS:
                res = _reconcile_metric(sym, args.date, m)
                if res is None: continue
                s_v, f_v, r = res
                lsr_oi_distribution[m].append(abs(r - 1.0))
                if r < args.lsr_oi_ratio_min or r > args.lsr_oi_ratio_max:
                    lsr_oi_violations.append({
                        "sym": sym, "metric": m, "store": s_v, "fresh": f_v, "ratio": r,
                    })

    print(f"[VOL-GUARD] checked={checked} violations={len(violations)} "
          f"missing_store={n_missing_store} missing_fresh={n_missing_fresh}")
    if args.enable_lsr_oi:
        print(f"[VOL-GUARD R5] lsr_oi violations={len(lsr_oi_violations)}")
        for m in LSR_OI_METRICS:
            arr = sorted(lsr_oi_distribution[m])
            if arr:
                p50 = arr[len(arr)//2]
                p90 = arr[int(len(arr)*0.9)] if len(arr) > 10 else arr[-1]
                pmax = arr[-1]
                print(f"[VOL-GUARD R5]   {m}: n={len(arr)} p50={p50:.4f} p90={p90:.4f} max={pmax:.4f} "
                      f"(relative diff |r-1|); PROVISIONAL tol=±{(1-args.lsr_oi_ratio_min)*100:.1f}%")

    if not violations and not lsr_oi_violations:
        print(f"[VOL-GUARD] OK — all {checked} symbols within ±{(1-args.ratio_min)*100:.1f}% "
              f"(vol + LSR/OI extended)")
        return 0

    # Format violation report
    lines = [
        f"🚨 [VOL-GUARD FAIL] {args.date} — {len(violations)} vol + {len(lsr_oi_violations)} LSR/OI out of band",
        f"    (store DEDUP sum vs fapi fresh)",
        f"",
    ]
    if violations:
        lines.append(f"── VOL (k[7]) ±{(1-args.ratio_min)*100:.1f}% ──")
        lines.append(f"{'sym':>16}  {'store':>18}  {'fresh':>18}  {'ratio':>8}")
        for v in sorted(violations, key=lambda x: abs(x["ratio"] - 1.0), reverse=True)[:20]:
            lines.append(f"{v['sym']:>16}  {v['store']:>18,.0f}  {v['fresh']:>18,.0f}  {v['ratio']:>8.4f}")
        if len(violations) > 20:
            lines.append(f"    ... +{len(violations)-20} more")
    if lsr_oi_violations:
        lines.append(f"")
        lines.append(f"── LSR/OI ±{(1-args.lsr_oi_ratio_min)*100:.1f}% PROVISIONAL [R5 F5c-ext] ──")
        lines.append(f"{'sym':>16}  {'metric':>12}  {'store':>14}  {'fresh':>14}  {'ratio':>8}")
        for v in sorted(lsr_oi_violations, key=lambda x: abs(x["ratio"] - 1.0), reverse=True)[:15]:
            lines.append(f"{v['sym']:>16}  {v['metric']:>12}  {v['store']:>14.4f}  {v['fresh']:>14.4f}  {v['ratio']:>8.4f}")
        if len(lsr_oi_violations) > 15:
            lines.append(f"    ... +{len(lsr_oi_violations)-15} more")
    lines.append(f"")
    lines.append(f"REF: docs/reports/_p0_store_vol_dup_forensics_20260821.md")
    lines.append(f"     R5 F5c-ext-20260824: LSR/OI reconcile PROVISIONAL 2% (set from distribution after first run)")
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

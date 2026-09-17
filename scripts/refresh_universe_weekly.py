#!/usr/bin/env python3
"""REFRESH UNIVERSE WEEKLY · Monday 01:00 UTC · KÝ 17/09

Luật universe:
  · Trên Binance Alpha (có trong token-list endpoint) AND
  · Có perp trên Binance USDT-M (fapi exchangeInfo) AND
  · CẢ HAI listing > 14 ngày

Nguồn ngày (KHÔNG dùng proxy klines):
  · Alpha: https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list
    → field `listingTime` (ms since epoch)
  · Perp: https://fapi.binance.com/fapi/v1/exchangeInfo
    → per-symbol `onboardDate` (ms since epoch)

Behavior:
  · UNION APPEND-ONLY vào data/config/freshwatch_symbols.txt · chỉ THÊM, không xoá
  · Token rớt khỏi Alpha hoặc delist perp → GIỮ, ghi `src: stale` + date trong sidecar
  · Sidecar: data/config/freshwatch_source.json {sym: {src, date}}
  · Atomic write · .tmp rename
  · Log diff + md5 before/after
  · Telegram notify khi n_added > 0

FAIL-CLOSED:
  · Endpoint hỏng/rỗng/JSON lỗi → exit 1 · KHÔNG ghi file · alert
  · Rule không có bất kỳ token nào thoả → exit 2 · KHÔNG ghi

Cron: `0 1 * * 1 cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/refresh_universe_weekly.py >> data/logs/refresh_universe.log 2>&1`
Slot check: 01:00 UTC Monday · alpha collector 01:30 · drift guard 01:44 · master 01:46 · not overlap.
"""
from __future__ import annotations
import sys, os, json, urllib.request, urllib.parse, hashlib, tempfile
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
FW_PATH = REPO / "data/config/freshwatch_symbols.txt"
SIDECAR_PATH = REPO / "data/config/freshwatch_source.json"
LOG_PATH = REPO / "data/logs/refresh_universe.log"

ALPHA_URL = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
FAPI_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
UA = {"User-Agent": "Mozilla/5.0"}

TODAY = datetime.now(timezone.utc).date()


def _log(msg):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg, file=sys.stderr)


def _fetch(url, name):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            if not body:
                _log(f"[N/A-ERROR:{name}-EMPTY] empty response"); sys.exit(1)
            return json.loads(body)
    except json.JSONDecodeError as e:
        _log(f"[N/A-ERROR:{name}-JSON] {e}"); sys.exit(1)
    except Exception as e:
        _log(f"[N/A-ERROR:{name}-FETCH] {type(e).__name__}: {e}"); sys.exit(1)


def _load_sidecar():
    if not SIDECAR_PATH.exists(): return {}
    try:
        return json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        _log(f"[N/A-ERROR:SIDECAR-PARSE] {e}"); sys.exit(1)


def _load_freshwatch():
    if not FW_PATH.exists(): return []
    return [l.strip() for l in FW_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def _atomic_write(path, content):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    tmp.replace(path)


def _tg_notify(text):
    tok = os.getenv("TG_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TG_CHAT_ID_DAILY")
    if not tok or not chat: return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "disable_web_page_preview": "true"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            _log(f"[TG-NOTIFY] ok={r.status == 200}")
    except Exception as e:
        _log(f"[TG-NOTIFY-ERR] {type(e).__name__}: {e}")


def main():
    _log(f"─── refresh_universe_weekly start · {TODAY} ───")

    # Fetch Alpha token-list
    alpha_data = _fetch(ALPHA_URL, "ALPHA")
    alpha_toks = alpha_data if isinstance(alpha_data, list) else alpha_data.get("data", [])
    if not alpha_toks:
        _log("[N/A-ERROR:ALPHA-EMPTY] token-list empty"); sys.exit(1)

    alpha_listings = {}   # bare_sym → date
    for t in alpha_toks:
        sym = t.get("symbol")
        lt = t.get("listingTime")
        if sym and lt:
            try: alpha_listings[sym] = datetime.fromtimestamp(int(lt) / 1000, tz=timezone.utc).date()
            except: pass  # L-66-OK
    _log(f"[ALPHA] {len(alpha_toks)} tokens · {len(alpha_listings)} listings")

    # Fetch fapi exchangeInfo
    fapi_data = _fetch(FAPI_URL, "FAPI")
    fapi_syms = fapi_data.get("symbols", [])
    if not fapi_syms:
        _log("[N/A-ERROR:FAPI-EMPTY] exchangeInfo empty"); sys.exit(1)

    fapi_onboard = {}   # perpSymbol → date · e.g. BTCUSDT → 2019-09-08
    fapi_status = {}    # perpSymbol → status
    for s in fapi_syms:
        sym = s.get("symbol", "")
        ob = s.get("onboardDate")
        st = s.get("status", "")
        if sym and ob:
            try: fapi_onboard[sym] = datetime.fromtimestamp(int(ob) / 1000, tz=timezone.utc).date()
            except: pass  # L-66-OK
        fapi_status[sym] = st
    _log(f"[FAPI] {len(fapi_syms)} symbols · {len(fapi_onboard)} with onboardDate · TRADING: {sum(1 for s in fapi_status.values() if s == 'TRADING')}")

    # Compute candidates: alpha ∩ perp-TRADING ∩ (both >14d)
    candidates = []
    for bare_sym, alpha_ld in alpha_listings.items():
        perp_sym = f"{bare_sym}USDT"
        if fapi_status.get(perp_sym) != "TRADING": continue
        perp_ob = fapi_onboard.get(perp_sym)
        if not perp_ob: continue
        alpha_age = (TODAY - alpha_ld).days
        perp_age = (TODAY - perp_ob).days
        if alpha_age > 14 and perp_age > 14:
            candidates.append(perp_sym)
    _log(f"[CANDIDATES] {len(candidates)} qualify (alpha AND perp both >14d)")

    if not candidates:
        _log("[N/A-ERROR:NO-CANDIDATES] rule matched nothing"); sys.exit(2)

    # UNION append-only
    current_fw = _load_freshwatch()
    current_set = set(current_fw)
    sidecar = _load_sidecar()

    added = [s for s in candidates if s not in current_set]
    dropped = [s for s in current_set if s in sidecar and sidecar[s].get("src") == "auto"
               and s not in set(candidates)]

    # Update sidecar
    for s in added:
        sidecar[s] = {"src": "auto", "date": TODAY.isoformat()}
    for s in dropped:
        sidecar[s] = {"src": "stale", "date": TODAY.isoformat(),
                      "was": sidecar.get(s, {}).get("src", "?")}

    # Build new fw text
    new_fw = current_fw + [s for s in added]

    if not added and not dropped:
        _log(f"[NO-CHANGE] fw={len(current_fw)} · candidates={len(candidates)} · no add/drop")
        return 0

    # md5 before/after
    md5_before = hashlib.md5(FW_PATH.read_bytes()).hexdigest()[:12] if FW_PATH.exists() else "(none)"

    # Atomic write
    _atomic_write(FW_PATH, "\n".join(new_fw) + "\n")
    _atomic_write(SIDECAR_PATH, json.dumps(sidecar, ensure_ascii=False, sort_keys=True, indent=2))

    md5_after = hashlib.md5(FW_PATH.read_bytes()).hexdigest()[:12]
    _log(f"[APPEND] fw {len(current_fw)}→{len(new_fw)} · added={len(added)} · stale-tagged={len(dropped)}")
    _log(f"[MD5] before={md5_before} · after={md5_after}")
    _log(f"[ADDED] {added}")
    if dropped:
        _log(f"[STALE] {dropped}")

    # Telegram notify
    if added:
        msg = (f"[UNIVERSE-REFRESH] {TODAY}\n"
               f"added: {len(added)} tokens\n"
               f"total: {len(current_fw)} → {len(new_fw)}\n"
               f"md5: {md5_before} → {md5_after}\n"
               f"sample: {', '.join(added[:10])}")
        _tg_notify(msg)

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

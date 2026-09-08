"""LEDGER BACKFILL 30d v3.3 · KÝ 07/09 GATE-4 RECONCILE · key-norm + universe-filter + EPISODE×COVERAGE.

RULES V3.3 (added over V3.2):
  · KEY-NORM: bare-symbol (strip USDT) mọi source trước union
  · UNIVERSE-FILTER: load freshwatch_symbols.txt (139 u50 syms) · filter WL entries to u50
  · EPISODE×COVERAGE: gap-14d chỉ đếm trên NGÀY-CÓ-COVERAGE của source đó ·
    lookback 14d mà số ngày-có-mắt < k=10 → new-entry = UNKNOWN-EPISODE, KHÔNG seed
    Log coverage-gap · Unknown ≠ absent (coverage-law chiếu xuống episode)
  · p15 UNIVERSE-BOUND: n_unique mọi trục ≤ |universe| · vượt = FAIL

L-59 RECONCILE: bảng đọc lại từ file d0aa3a9d bằng đếm trực tiếp.
"""
from __future__ import annotations
import sys, os, re, json, hashlib, tempfile, argparse
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from collections import defaultdict

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (sys.stdout.reconfigure fallback for Python <3.7 · benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LEDGER_DIR = REPO / "data/logs/event_ledger"
SNAP_DIR = REPO / "data/raw/nansen_snapshots"
WL_STATE = REPO / "data/state"
GH_LOG = REPO / "data/logs/gom_h_daily.log"
RELAY_LOG = REPO / "data/logs/tg_relay.log"
DIGEST_LOG = REPO / "data/logs/digest_daily_vps.log"
WL_LOG = REPO / "data/export/watchlist_cron.log"
UNIVERSE_PATH = REPO / "data/config/freshwatch_symbols.txt"
LEDGER_DIR.mkdir(parents=True, exist_ok=True)

FRESH_DELTA_THRESH = 50_000
EXCH_USD_MIN = 200_000
EXCH_PCT_MIN = 1.0
EPISODE_GAP = 14
COVERAGE_LOOKBACK = 14  # days
COVERAGE_MIN_DAYS = 10  # k=10 · under → UNKNOWN-EPISODE


def _load_universe() -> set[str]:
    """Load u50 universe · bare symbols (strip USDT)."""
    if not UNIVERSE_PATH.exists(): return set()
    syms = set()
    for line in UNIVERSE_PATH.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"): continue
        # Strip USDT suffix if present
        base = s.replace("USDT", "") if s.endswith("USDT") else s
        syms.add(base)
    return syms


def _norm_symbol(sym: str) -> str:
    """KEY-NORM: bare-symbol · strip USDT."""
    if not sym: return ""
    return sym.replace("USDT", "") if sym.endswith("USDT") else sym


# cluster_episodes verbatim from prod (v3.2 unchanged)
def cluster_episodes(rows):
    """rows: [{symbol, date, ...}] · Return list of episodes."""
    by_sym = {}
    for r in rows: by_sym.setdefault(r["symbol"], []).append(r)
    episodes = []
    for sym in sorted(by_sym):
        srtd = sorted(by_sym[sym], key=lambda x: x["date"])
        cur = []; prev_date = None
        for r in srtd:
            cur_date = date.fromisoformat(r["date"])
            if prev_date is not None and (cur_date - prev_date).days >= EPISODE_GAP:
                if cur: episodes.append(cur); cur = []
            cur.append(r); prev_date = cur_date
        if cur: episodes.append(cur)
    return episodes


# Existing SENT-anchor helpers (v3.2 unchanged)
def _relay_sent_by_target(target: str) -> dict | None:
    if not RELAY_LOG.exists(): return None
    txt = RELAY_LOG.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if f"target_date={target}" in lines[i] and "[EXTRACT]" in lines[i]:
            for j in range(i, min(i + 10, len(lines))):
                if "[SENT]" in lines[j] and "all_ok=True" in lines[j]:
                    h_m = re.search(r"hash=([a-f0-9]+)", lines[j])
                    return {"hash": h_m.group(1) if h_m else "?"}
    return None


def _digest_sent_by_target(target: str) -> dict | None:
    if not DIGEST_LOG.exists(): return None
    txt = DIGEST_LOG.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    d = datetime.strptime(target, "%Y-%m-%d").date()
    send_day = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    fresh_ok = exch_ok = False; done_hash = None
    for i, line in enumerate(lines):
        if send_day in line and f"snapshot={target}.json" in line:
            for j in range(i, min(i + 15, len(lines))):
                if "[SENT] Fresh-Wallets" in lines[j] and "ok=True" in lines[j]: fresh_ok = True
                if "[SENT] EXCH-BAL" in lines[j] and "ok=True" in lines[j]: exch_ok = True
                if "[DIGEST-VPS DONE]" in lines[j]:
                    m = re.search(r"hash=([a-f0-9]+)", lines[j])
                    if m: done_hash = m.group(1)
                    break
    if fresh_ok or exch_ok:
        return {"fresh_ok": fresh_ok, "exch_ok": exch_ok, "hash": done_hash or "?"}
    return None


def _wl_sent_by_target(target: str) -> bool:
    if not WL_LOG.exists(): return False
    txt = WL_LOG.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"^INFO:\s+target_date={re.escape(target)}\s.*?INFO:\s+snapshot SAVED",
                  txt, re.MULTILINE | re.DOTALL)
    return bool(m)


def _load_snap(p: Path) -> dict:
    if not p.exists(): return {"rows": []}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {"rows": []}


def _fresh_delta_from_snap_pair(target: str, universe: set[str]) -> list[dict]:
    p = SNAP_DIR / f"{target}.json"
    if not p.exists(): return []
    snap = _load_snap(p)
    d = datetime.strptime(target, "%Y-%m-%d").date()
    prev = None
    for delta_d in range(1, 8):
        cand = SNAP_DIR / f"{(d - timedelta(days=delta_d)).strftime('%Y-%m-%d')}.json"
        if cand.exists():
            try: prev = _load_snap(cand); break
            except: continue
    prev_by = {_norm_symbol(r.get("symbol", "")): r for r in (prev.get("rows", []) if prev else [])}
    rows = []
    for r in snap.get("rows", []):
        sym = _norm_symbol(r.get("symbol", ""))
        if universe and sym not in universe: continue  # universe-filter
        cur = r.get("usd_1d"); pv = prev_by.get(sym, {}).get("usd_1d")
        if cur is None or pv is None: continue
        try:
            delta = float(cur) - float(pv)
            if delta >= FRESH_DELTA_THRESH:
                rows.append({"symbol": sym, "line": f"snap-pair Δ={delta:+.0f}"})
        except: pass  # L-66-OK (json parse fallback)
    return rows


def _exch_qualified_from_snap(target: str, universe: set[str]) -> list[dict]:
    p = SNAP_DIR / f"{target}.json"
    if not p.exists(): return []
    snap = _load_snap(p)
    rows = []
    for r in snap.get("rows", []):
        sym = _norm_symbol(r.get("symbol", ""))
        if universe and sym not in universe: continue
        du = r.get("exchange_delta_usd"); mc = r.get("market_cap")
        if du is None: continue
        pct = (float(du) / float(mc) * 100) if mc and float(mc) > 0 else None
        if abs(float(du)) >= EXCH_USD_MIN and pct is not None and abs(pct) >= EXCH_PCT_MIN:
            direction = "up" if float(du) > 0 else "dn"
            rows.append({"symbol": sym, "direction": direction,
                         "line": f"snap-exch Δ={float(du):+.0f} pct={pct:+.2f}%"})
    return rows


def _parse_gom_h_from_log(target: str, universe: set[str]) -> tuple[list, list]:
    if not GH_LOG.exists(): return ([], [])
    txt = GH_LOG.read_text(encoding="utf-8", errors="replace")
    dd_mm = f"{target[8:10]}/{target[5:7]}"
    marker = f"━━ CAMPAIGN-PRE · {dd_mm} · {target} ━━"
    idx = txt.rfind(marker)
    if idx < 0: return ([], [])
    end_pat = re.compile(r"════════", re.MULTILINE)
    m_end = end_pat.search(txt, pos=idx + 100)
    end_pos = m_end.start() if m_end else len(txt)
    block = txt[idx:end_pos]
    perp = []; kho = []
    in_g = in_r = False
    for line in block.split("\n"):
        if "🟢 GOM/STAGING" in line: in_g = True; in_r = False; continue
        if "🔴 KHO ĐỘNG GIỮA ĐẠP" in line: in_r = True; in_g = False; continue
        if line.startswith("🌊 ") or line.startswith("⏳ ") or line.startswith("👁 "):
            in_g = in_r = False; continue
        m = re.match(r"^\s+[🥇🥈🥉•⚪]\s+(\S+?)USDT?\s+\[([^\]]+)\]", line)
        if m:
            sym = _norm_symbol(m.group(1))
            if universe and sym not in universe: continue
            tag = m.group(2)
            lane = "perp" if "H2" in tag else "kho"
            if "H1" in tag and "H2" in tag: lane = "both"
            evt = {"symbol": sym, "lane": lane, "line": line.strip()}
            if in_g or in_r:
                if lane in ("perp", "both"): perp.append(evt)
                if lane in ("kho", "both"): kho.append(evt)
    return (perp, kho)


def build_wl_membership_history(window_start: date, window_end: date, universe: set[str]) -> tuple[list, dict, dict]:
    """Return (memberships, per_day_present, coverage_days).
    memberships: [{symbol, date}] per each token's day-in-list-B (u50 filtered).
    per_day_present: date → bool (WL state file exists)
    coverage_days: dict of dates present.
    """
    membership_start = window_start - timedelta(days=EPISODE_GAP + COVERAGE_LOOKBACK + 5)
    d = membership_start
    memberships = []
    per_day_present = {}
    while d <= window_end:
        d_str = d.strftime("%Y-%m-%d")
        p = WL_STATE / f"hedge_watchlist_{d_str}.json"
        if p.exists():
            per_day_present[d_str] = True
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for tok in data.get("list_b_tokens", []):
                    sym = _norm_symbol(tok)
                    if universe and sym not in universe: continue  # universe-filter
                    memberships.append({"symbol": sym, "date": d_str})
            except: pass  # L-66-OK (json parse fallback)
        else:
            per_day_present[d_str] = False
        d += timedelta(days=1)
    return (memberships, per_day_present, per_day_present)


def wl_episode_with_coverage_guard(memberships: list, per_day_present: dict, window_start: date, window_end: date) -> tuple[dict, dict]:
    """EPISODE×COVERAGE: episode-start CHỈ khi 14d lookback trước có ≥k=10 ngày coverage.
    Return (per_day_new_episode_syms, per_day_unknown_episode_syms).
    """
    # Compute episodes (unchanged)
    episodes = cluster_episodes(memberships)
    per_day_new = defaultdict(set)
    per_day_unknown = defaultdict(set)
    for ep in episodes:
        first = ep[0]
        ep_date_str = first["date"]
        ep_date = date.fromisoformat(ep_date_str)
        if not (window_start <= ep_date <= window_end): continue
        # COVERAGE guard: check lookback COVERAGE_LOOKBACK days before ep_date
        cov_days = 0
        for i in range(1, COVERAGE_LOOKBACK + 1):
            d_check = (ep_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if per_day_present.get(d_check, False):
                cov_days += 1
        if cov_days >= COVERAGE_MIN_DAYS:
            per_day_new[ep_date_str].add(first["symbol"])
        else:
            per_day_unknown[ep_date_str].add(first["symbol"])
    return (dict(per_day_new), dict(per_day_unknown))


def backfill_v3_3(target: str, window_days: int = 30) -> dict:
    universe = _load_universe()
    events = []
    per_src = defaultdict(int)
    per_src_unique = defaultdict(set)
    coverage = defaultdict(set)
    excluded = defaultdict(int)
    excluded_universe = defaultdict(int)

    end = datetime.strptime(target, "%Y-%m-%d").date()
    start = end - timedelta(days=window_days)

    # WL episodes with coverage guard
    memberships, per_day_present, _ = build_wl_membership_history(start, end, universe)
    wl_seeds, wl_unknown = wl_episode_with_coverage_guard(memberships, per_day_present, start, end)

    d = start
    while d <= end:
        d_str = d.strftime("%Y-%m-%d")

        # GOM-H
        relay_sent = _relay_sent_by_target(d_str)
        if relay_sent:
            perp, kho = _parse_gom_h_from_log(d_str, universe)
            coverage["PERP-gomh"].add(d_str); coverage["KHO-SAN-gomh"].add(d_str)
            for evt in perp:
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type": "FIRE-SENT",
                               "axis": "PERP", "symbol": evt["symbol"], "target_date": d_str,
                               "source": "gomh", "source_tag": "ᴳ",
                               "sent_hash": relay_sent["hash"], "source_line": evt["line"][:80]})
                per_src["gom_h_perp_SENT"] += 1
                per_src_unique["gom_h_perp_SENT"].add(evt["symbol"])
            for evt in kho:
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type": "FIRE-SENT",
                               "axis": "KHO-SAN", "symbol": evt["symbol"], "target_date": d_str,
                               "source": "gomh_h1", "source_tag": "ᴳ",
                               "sent_hash": relay_sent["hash"], "source_line": evt["line"][:80]})
                per_src["gom_h_kho_SENT"] += 1
                per_src_unique["gom_h_kho_SENT"].add(evt["symbol"])
        else:
            excluded["gom_h_NO-relay-SENT"] += 1

        # FRESH/EXCH
        digest_sent = _digest_sent_by_target(d_str)
        if digest_sent and digest_sent.get("fresh_ok"):
            coverage["FRESH-CHAIN"].add(d_str)
            for r in _fresh_delta_from_snap_pair(d_str, universe):
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type": "FRESH-DELTA-SENT",
                               "axis": "FRESH-CHAIN", "symbol": r["symbol"], "target_date": d_str,
                               "source": "fresh_digest", "source_tag": "ᶠ",
                               "sent_hash": digest_sent["hash"], "source_line": r["line"][:80]})
                per_src["fresh_delta_SENT"] += 1
                per_src_unique["fresh_delta_SENT"].add(r["symbol"])
        else:
            excluded["fresh_NO-digest-SENT"] += 1

        if digest_sent and digest_sent.get("exch_ok"):
            coverage["KHO-SAN-exch"].add(d_str)
            for r in _exch_qualified_from_snap(d_str, universe):
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type": "EXCH-QUALIFIED-SENT",
                               "axis": "KHO-SAN", "symbol": r["symbol"], "target_date": d_str,
                               "source": "exch_digest", "source_tag": "ᴱ",
                               "sent_hash": digest_sent["hash"], "source_line": r["line"][:80]})
                per_src["exch_qualified_SENT"] += 1
                per_src_unique["exch_qualified_SENT"].add(r["symbol"])
        else:
            excluded["exch_NO-digest-SENT"] += 1

        # WL EPISODE × COVERAGE
        if _wl_sent_by_target(d_str):
            coverage["WL"].add(d_str)
            for sym in wl_seeds.get(d_str, set()):
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type": "WATCHLIST-B-NEW-EPISODE",
                               "axis": "PERP", "symbol": sym, "target_date": d_str,
                               "source": "watchlist_episode", "source_tag": "ᵂ",
                               "sent_hash": "wl-sent",
                               "source_line": f"NEW-EPISODE (gap≥{EPISODE_GAP}d · coverage≥{COVERAGE_MIN_DAYS}d/14): {sym}"})
                per_src["watchlist_b_episode_SENT"] += 1
                per_src_unique["watchlist_b_episode_SENT"].add(sym)
            for sym in wl_unknown.get(d_str, set()):
                excluded["wl_UNKNOWN-EPISODE"] += 1

        d += timedelta(days=1)
    events.sort(key=lambda e: (e["ts_utc"], e["symbol"], e["axis"]))

    # p15 UNIVERSE-BOUND check
    per_axis_uniq = defaultdict(set)
    for e in events: per_axis_uniq[e["axis"]].add(e["symbol"])
    p15_violations = {}
    for ax, syms in per_axis_uniq.items():
        if universe and len(syms) > len(universe):
            p15_violations[ax] = f"n={len(syms)} > |universe|={len(universe)}"
        oob = syms - universe if universe else set()
        if oob:
            p15_violations[f"{ax}_out-of-bound"] = f"n_oob={len(oob)} · sample={sorted(oob)[:5]}"

    # Stars
    per_sym = defaultdict(lambda: {"axes": set(), "events": [], "latest": {}})
    for e in events:
        per_sym[e["symbol"]]["axes"].add(e["axis"])
        per_sym[e["symbol"]]["events"].append(e)
        cur = per_sym[e["symbol"]]["latest"].get(e["axis"])
        if cur is None or e["target_date"] > cur["target_date"]:
            per_sym[e["symbol"]]["latest"][e["axis"]] = e
    stars_all = [(s, info) for s, info in per_sym.items() if len(info["axes"]) >= 2]
    n_new_today = 0
    new_today_syms = []
    for sym, info in stars_all:
        events_today = [e for e in info["events"] if e["target_date"] == target]
        if not events_today: continue
        axes_before = {e["axis"] for e in info["events"] if e["target_date"] < target}
        if len(axes_before) < 2:
            n_new_today += 1
            new_today_syms.append(sym)
    n_total = len(stars_all); n_hanging = n_total - n_new_today
    stars_sorted = sorted(stars_all, key=lambda x: (-len(x[1]["axes"]), -len(x[1]["events"]), x[0]))

    return {
        "universe_size": len(universe),
        "events": events,
        "per_src": dict(per_src),
        "per_src_unique": {k: len(v) for k, v in per_src_unique.items()},
        "coverage_counts": {k: len(v) for k, v in coverage.items()},
        "excluded": dict(excluded),
        "wl_unknown_days": {k: sorted(v) for k, v in wl_unknown.items() if v},
        "p15_violations": p15_violations,
        "stars_total": n_total,
        "stars_hanging": n_hanging,
        "stars_new_today": n_new_today,
        "new_today_syms": new_today_syms,
        "stars_list": [(s, info["axes"], len(info["events"]), info["latest"]) for s, info in stars_sorted],
    }


def _write_atomic(p, content):
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "wb") as f: f.write(content)
        os.replace(tmp_name, p)
    except:
        try: os.unlink(tmp_name)
        except: pass  # L-66-OK (json parse fallback)
        raise
    return hashlib.md5(content).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--window", type=int, default=30)
    args = ap.parse_args()

    res = backfill_v3_3(args.target, args.window)
    print(f"[BACKFILL v3.3 KEY-NORM + UNIVERSE + EPISODE×COVERAGE] target={args.target}")
    print(f"|universe| (freshwatch_symbols.txt) = {res['universe_size']}")
    print()
    print("## 4 SỐ per source (V3.3 · universe-filtered)")
    print(f"{'source':<32} {'n_events':>10} {'n_unique':>10}")
    for src in sorted(res["per_src"].keys()):
        print(f"{src:<32} {res['per_src'][src]:>10} {res['per_src_unique'].get(src, 0):>10}")
    print(f"TOTAL: {sum(res['per_src'].values())} events · {len(set(e['symbol'] for e in res['events']))} unique")
    print()
    print("## EXCLUDED")
    for k, n in sorted(res["excluded"].items()):
        print(f"  {k:<32} = {n}")
    if res["wl_unknown_days"]:
        print(f"  UNKNOWN-EPISODE days ({sum(len(v) for v in res['wl_unknown_days'].values())} sym-days):")
        for d, syms in sorted(res["wl_unknown_days"].items())[:5]:
            print(f"    {d}: {sorted(syms)[:10]}")
    print()
    print("## COVERAGE-per-axis")
    for k, n in sorted(res["coverage_counts"].items()):
        print(f"  {k:<20} = {n}/{args.window+1}")
    print()
    per_axis = defaultdict(set)
    for e in res["events"]: per_axis[e["axis"]].add(e["symbol"])
    perp = per_axis.get("PERP", set()); kho = per_axis.get("KHO-SAN", set()); fresh = per_axis.get("FRESH-CHAIN", set())
    print(f"## Ma trận giao (unique · post universe-filter)")
    print(f"  n_perp={len(perp)} · n_kho={len(kho)} · n_fresh={len(fresh)} · vs |universe|={res['universe_size']}")
    print(f"  |PERP∩FRESH|={len(perp & fresh)} · |KHO∩FRESH|={len(kho & fresh)} · |PERP∩KHO|={len(perp & kho)} · |all|={len(perp & kho & fresh)}")
    print()
    print(f"## p15 UNIVERSE-BOUND CHECK")
    if not res["p15_violations"]:
        print(f"  ✅ all axes ≤ |universe|={res['universe_size']}")
    else:
        for k, v in res["p15_violations"].items():
            print(f"  ⚠ {k}: {v}")
    print()
    SOFT_CEILING = 15
    print(f"## DAO CHECK BỘ BA")
    print(f"  ⭐ đang-treo = {res['stars_hanging']}")
    print(f"  ⭐ mới-hôm-nay = {res['stars_new_today']} ({res['new_today_syms']})")
    print(f"  coverage-vector = perp-gomh={res['coverage_counts'].get('PERP-gomh',0)}/{args.window+1} · kho-exch={res['coverage_counts'].get('KHO-SAN-exch',0)}/{args.window+1} · fresh={res['coverage_counts'].get('FRESH-CHAIN',0)}/{args.window+1} · wl={res['coverage_counts'].get('WL',0)}/{args.window+1}")
    if res["stars_hanging"] > SOFT_CEILING:
        print(f"  ⚠ [STAR-ANOMALY] đang-treo={res['stars_hanging']} > ceiling={SOFT_CEILING} · caveat: coverage-vector above")
    else:
        print(f"  ✓ đang-treo trong ceiling={SOFT_CEILING}")
    print()
    print("## ⭐-LIST với SOURCE-TAG (top 20)")
    for sym, axes, n_ev, latest in res["stars_list"][:20]:
        parts = [f"{ax[:4]}={e['target_date'][5:]}{e.get('source_tag','?')}" for ax, e in latest.items()]
        new_flag = " [NEW]" if sym in res["new_today_syms"] else ""
        print(f"  {sym:<15} {len(axes)}-trục ({'+'.join(sorted(axes))}) {' · '.join(parts)}{new_flag}")

    p = LEDGER_DIR / f"events_{args.target}.jsonl"
    content = "\n".join(json.dumps(e, ensure_ascii=False) for e in res["events"]).encode("utf-8")
    md5 = _write_atomic(p, content)
    print(f"\n[WRITE-JSONL] {p} · md5={md5}")
    print(f"[L-59 RECONCILE-KEY] cite md5={md5} for all future reads · run vs file must match")


if __name__ == "__main__":
    main()

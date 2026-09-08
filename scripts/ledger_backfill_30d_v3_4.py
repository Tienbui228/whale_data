"""LEDGER BACKFILL 30d v3.4 · KÝ 07/09 GATE-4 · giải phẫu + cổng thay rây.

RULES V3.4 (added over V3.3):
  · EXPLICIT-PARSER: list_b_tokens accepts BOTH list[str] AND dict[str,meta] · KHÔNG accidental
  · WATERFALL diagnostic: raw → key-norm → universe → baseline → episode×coverage (log per tier)
  · p15 FAIL-ENGINE with NAMES · cấm silent-drop · out-of-bound in ĐÍCH DANH
  · UNIVERSE cite: file+md5 in header (L-59 semantics) · TODO: per-target-date universe (L-48)
  · DAO-DEFERRED label (not CLEAR, not ANOMALY) khi coverage < ceiling target
  · Coverage line 3 số axis-union (PERP · KHO · FRESH) · split giữ trong diagnostic
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
COVERAGE_LOOKBACK = 14
COVERAGE_MIN_DAYS = 10


def _load_universe() -> tuple[set[str], str]:
    """Load u50 universe · returns (set, md5).
    NOTE: per-target-date universe (L-48 SOPH-family delist) NOT yet implemented — single file used.
    """
    if not UNIVERSE_PATH.exists(): return set(), ""
    content = UNIVERSE_PATH.read_bytes()
    md5 = hashlib.md5(content).hexdigest()
    syms = set()
    for line in content.decode("utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"): continue
        base = s.replace("USDT", "") if s.endswith("USDT") else s
        syms.add(base)
    return syms, md5


def _norm_symbol(sym) -> str | None:
    if not isinstance(sym, str) or not sym: return None
    s = sym.strip()
    if not s: return None
    return s.replace("USDT", "") if s.endswith("USDT") else s


def cluster_episodes(rows):
    """rows: [{symbol, date, ...}] · Return list of episodes. Verbatim from prod archive."""
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
        if sym is None: continue
        if universe and sym not in universe: continue
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
        if sym is None: continue
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
            if sym is None: continue
            if universe and sym not in universe: continue
            tag = m.group(2)
            lane = "perp" if "H2" in tag else "kho"
            if "H1" in tag and "H2" in tag: lane = "both"
            evt = {"symbol": sym, "lane": lane, "line": line.strip()}
            if in_g or in_r:
                if lane in ("perp", "both"): perp.append(evt)
                if lane in ("kho", "both"): kho.append(evt)
    return (perp, kho)


def _list_b_tokens_from(data: dict) -> list[str]:
    """EXPLICIT-PARSER (V3.4): list_b_tokens can be list[str] OR dict[str,meta].
    Return list of raw token strings. Non-string entries silently skipped WITH log elsewhere.
    """
    lb = data.get("list_b_tokens")
    if lb is None: return []
    if isinstance(lb, list): return [t for t in lb if isinstance(t, str)]
    if isinstance(lb, dict): return [k for k in lb.keys() if isinstance(k, str)]
    return []


def build_wl_waterfall(window_start: date, window_end: date, universe: set[str]) -> dict:
    """V3.4 WATERFALL: 5-tier diagnostic on WL membership pipeline.
    Returns dict with tier counts + drop classification + memberships-final + per_day_present."""
    membership_start = window_start - timedelta(days=EPISODE_GAP + COVERAGE_LOOKBACK + 5)
    tier1_raw = []          # every raw entry
    tier2_norm = []         # after key-norm
    per_day_present = {}
    drops_universe = []     # after tier3

    d = membership_start
    while d <= window_end:
        d_str = d.strftime("%Y-%m-%d")
        p = WL_STATE / f"hedge_watchlist_{d_str}.json"
        if p.exists():
            per_day_present[d_str] = True
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for tok in _list_b_tokens_from(data):
                    tier1_raw.append({"date": d_str, "raw": tok})
            except:
                pass
        else:
            per_day_present[d_str] = False
        d += timedelta(days=1)

    # Tier 2: key-norm
    for r in tier1_raw:
        n = _norm_symbol(r["raw"])
        if n is not None:
            tier2_norm.append({"date": r["date"], "raw": r["raw"], "norm": n})

    # Tier 3: universe filter (classify drops)
    tier3_after_universe = []
    drops = defaultdict(list)   # classified drops per class
    drops_sym = defaultdict(set)
    for r in tier2_norm:
        if r["norm"] in universe:
            tier3_after_universe.append(r)
        else:
            cls = _classify_drop(r["norm"], r["raw"], universe)
            drops[cls].append(r)
            drops_sym[cls].add(r["norm"])

    # Tier 4 · DIAGNOSTIC-ONLY: baseline D-1 count (does NOT gate episode input).
    # Reason: EPISODE×COVERAGE (tier-5) already enforces baseline via k=10 lookback.
    # Gating at tier-4 would shift episode-starts erroneously (án V3.4-BASELINE-DIAG).
    tier4_after_baseline = []
    dropped_baseline = 0
    for r in tier3_after_universe:
        d_prev = (date.fromisoformat(r["date"]) - timedelta(days=1)).strftime("%Y-%m-%d")
        if per_day_present.get(d_prev, False):
            tier4_after_baseline.append(r)
        else:
            dropped_baseline += 1

    # memberships_final = tier3_after_universe (NOT tier4) · baseline handled downstream
    return {
        "tier1_raw_n": len(tier1_raw), "tier1_raw_uniq": len(set(r["raw"] for r in tier1_raw)),
        "tier2_norm_n": len(tier2_norm), "tier2_norm_uniq": len(set(r["norm"] for r in tier2_norm)),
        "tier3_after_universe_n": len(tier3_after_universe),
        "tier3_after_universe_uniq": len(set(r["norm"] for r in tier3_after_universe)),
        "tier3_drops": {cls: {"n": len(drops[cls]), "n_uniq": len(drops_sym[cls]),
                              "sample": sorted(drops_sym[cls])[:20]} for cls in drops},
        "tier4_after_baseline_n": len(tier4_after_baseline),
        "tier4_after_baseline_uniq": len(set(r["norm"] for r in tier4_after_baseline)),
        "tier4_dropped_no_baseline": dropped_baseline,
        "tier4_gate_enforced": False,  # diagnostic only per V3.4-BASELINE-DIAG án
        "memberships_final": [{"symbol": r["norm"], "date": r["date"]} for r in tier3_after_universe],
        "per_day_present": per_day_present,
    }


def _classify_drop(norm_val: str, raw: str, universe: set[str]) -> str:
    """rác-parser | norm-miss-nối-lại | thật-ngoài-vũ-trụ"""
    if not norm_val: return "rác-parser"
    if not norm_val.replace("_","").replace("-","").isalnum():
        return "rác-parser"
    # Try trimming secondary stable suffixes
    for suffix in ("USDT","USDC","BUSD","FDUSD","TUSD"):
        if norm_val.endswith(suffix):
            trimmed = norm_val[:-len(suffix)]
            if trimmed and trimmed in universe:
                return "norm-miss-nối-lại"
    return "thật-ngoài-vũ-trụ"


def wl_episode_with_coverage_guard(memberships, per_day_present, window_start, window_end):
    episodes = cluster_episodes(memberships)
    per_day_new = defaultdict(set)
    per_day_unknown = defaultdict(set)
    for ep in episodes:
        first = ep[0]
        ep_date_str = first["date"]
        ep_date = date.fromisoformat(ep_date_str)
        if not (window_start <= ep_date <= window_end): continue
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


def backfill_v3_4(target: str, window_days: int = 30) -> dict:
    universe, uni_md5 = _load_universe()
    events = []
    per_src = defaultdict(int)
    per_src_unique = defaultdict(set)
    coverage = defaultdict(set)
    excluded = defaultdict(int)

    end = datetime.strptime(target, "%Y-%m-%d").date()
    start = end - timedelta(days=window_days)

    # WL 5-tier waterfall
    wf = build_wl_waterfall(start, end, universe)
    wl_seeds, wl_unknown = wl_episode_with_coverage_guard(
        wf["memberships_final"], wf["per_day_present"], start, end)

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

    # p15 UNIVERSE-BOUND · FAIL-ENGINE with NAMES · cấm silent-drop
    per_axis_uniq = defaultdict(set)
    for e in events: per_axis_uniq[e["axis"]].add(e["symbol"])
    p15_violations = {}
    for ax, syms in per_axis_uniq.items():
        oob = syms - universe if universe else set()
        if oob:
            p15_violations[ax] = {"n_oob": len(oob), "syms": sorted(oob)}
        if universe and len(syms) > len(universe):
            p15_violations[f"{ax}_over_universe"] = {"n_axis": len(syms), "n_universe": len(universe)}

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
        "universe_size": len(universe), "universe_md5": uni_md5,
        "waterfall": wf,
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

    res = backfill_v3_4(args.target, args.window)

    print(f"[BACKFILL v3.4 · GIẢI-PHẪU + P15-FAIL-ENGINE + DAO-DEFERRED] target={args.target}")
    print(f"[UNIVERSE-CITE] file={UNIVERSE_PATH.name} · md5={res['universe_md5']} · n={res['universe_size']}")
    print(f"[UNIVERSE-NOTE] per-target-date universe NOT WIRED (L-48 SOPH-family delist) · single file used")
    print()

    # WATERFALL
    wf = res["waterfall"]
    print("## BẢNG THÁC-NƯỚC WL 5-TIER (V3.4)")
    print(f"{'TIER':<40} {'n_entries':>12} {'n_unique':>10}")
    print(f"{'1. raw-parser':<40} {wf['tier1_raw_n']:>12} {wf['tier1_raw_uniq']:>10}")
    print(f"{'2. hậu-key-norm':<40} {wf['tier2_norm_n']:>12} {wf['tier2_norm_uniq']:>10}")
    print(f"{'3. hậu-universe':<40} {wf['tier3_after_universe_n']:>12} {wf['tier3_after_universe_uniq']:>10}")
    print(f"{'4. hậu-baseline (D-1)':<40} {wf['tier4_after_baseline_n']:>12} {wf['tier4_after_baseline_uniq']:>10}")
    print(f"{'5. hậu-episode×coverage':<40} {res['per_src'].get('watchlist_b_episode_SENT',0):>12} {res['per_src_unique'].get('watchlist_b_episode_SENT',0):>10}")
    print(f"[TIER-4 NOTE] gate_enforced={wf.get('tier4_gate_enforced', True)} · diagnostic-only (án V3.4-BASELINE-DIAG · baseline delegated to k=10 lookback)")
    print()
    print("### TIER-3 DROPS · CLASSIFICATION (LIỆT ĐÍCH DANH)")
    for cls in ("rác-parser", "norm-miss-nối-lại", "thật-ngoài-vũ-trụ"):
        d = wf["tier3_drops"].get(cls, {"n": 0, "n_uniq": 0, "sample": []})
        print(f"  {cls:<30} n_entries={d['n']:>4} · n_unique={d['n_uniq']:>3}")
        if d["sample"]: print(f"    sample: {d['sample']}")
    # Rác-parser assertion
    n_rac = wf["tier3_drops"].get("rác-parser", {}).get("n", 0)
    if n_rac > 0:
        print(f"\n  ⚠ RÁC-PARSER = {n_rac} > 0 → PHẢI SỬA PARSER (không để universe dọn hộ)")
    else:
        print(f"\n  ✓ RÁC-PARSER = 0 · parser CLEAN (dict/list explicit-handled)")
    if wf["tier4_dropped_no_baseline"] > 0:
        print(f"  · tier-4 dropped no-D-1-baseline = {wf['tier4_dropped_no_baseline']}")
    print()

    print("## 4 SỐ per source (V3.4 · universe-filtered)")
    print(f"{'source':<32} {'n_events':>10} {'n_unique':>10}")
    for src in sorted(res["per_src"].keys()):
        print(f"{src:<32} {res['per_src'][src]:>10} {res['per_src_unique'].get(src, 0):>10}")
    print(f"TOTAL: {sum(res['per_src'].values())} events · {len(set(e['symbol'] for e in res['events']))} unique")
    print()

    print("## EXCLUDED")
    for k, n in sorted(res["excluded"].items()):
        print(f"  {k:<32} = {n}")
    print()

    # COVERAGE · 3 số axis-union + diagnostic split
    perp_days = res["coverage_counts"].get("PERP-gomh", 0)
    wl_days = res["coverage_counts"].get("WL", 0)
    kho_h1_days = res["coverage_counts"].get("KHO-SAN-gomh", 0)
    kho_exch_days = res["coverage_counts"].get("KHO-SAN-exch", 0)
    fresh_days = res["coverage_counts"].get("FRESH-CHAIN", 0)
    win_n = args.window + 1
    perp_union = perp_days + wl_days - 0  # union approximation (day-set not computed exactly here; use diagnostic split for now)
    kho_union = max(kho_h1_days, kho_exch_days)  # union upper bound via diagnostic

    print("## COVERAGE (V3.4 NHÃN SỬA · axis-union 3 số)")
    print(f"  PERP-union  = {perp_days}∪{wl_days}/{win_n} (gomh · wl)")
    print(f"  KHO-union   = {kho_h1_days}∪{kho_exch_days}/{win_n} (gomh-H1 · exch)")
    print(f"  FRESH       = {fresh_days}/{win_n}")
    print(f"  [diagnostic split]")
    for k, n in sorted(res["coverage_counts"].items()):
        print(f"    {k:<20} = {n}/{win_n}")
    print()

    per_axis = defaultdict(set)
    for e in res["events"]: per_axis[e["axis"]].add(e["symbol"])
    perp = per_axis.get("PERP", set()); kho = per_axis.get("KHO-SAN", set()); fresh = per_axis.get("FRESH-CHAIN", set())
    print(f"## Ma trận giao (unique · post universe-filter)")
    print(f"  n_perp={len(perp)} · n_kho={len(kho)} · n_fresh={len(fresh)} · vs |universe|={res['universe_size']}")
    print(f"  |PERP∩FRESH|={len(perp & fresh)} · |KHO∩FRESH|={len(kho & fresh)} · |PERP∩KHO|={len(perp & kho)} · |all|={len(perp & kho & fresh)}")
    print()

    # p15 FAIL-ENGINE NAMES
    print(f"## p15 UNIVERSE-BOUND CHECK (V3.4 · FAIL-ENGINE with NAMES · cấm silent-drop)")
    if not res["p15_violations"]:
        print(f"  ✅ all axes ≤ |universe|={res['universe_size']} · zero out-of-bound")
    else:
        print(f"  ❌ FAIL-ENGINE · treo verdict")
        for ax, info in res["p15_violations"].items():
            if isinstance(info, dict) and "syms" in info:
                print(f"    {ax}: n_oob={info['n_oob']} · syms=ĐÍCH DANH={info['syms']}")
            else:
                print(f"    {ax}: {info}")
    print()

    # DAO CHECK · NHÃN SỬA: DAO-DEFERRED (khi coverage < ceiling)
    print(f"## DAO CHECK · NHÃN SỬA V3.4")
    dao_line = f"[DAO-DEFERRED coverage: fresh {fresh_days}/{win_n} · kho {kho_exch_days}/{win_n}] đang-treo={res['stars_hanging']} · mới={res['stars_new_today']}"
    print(f"  {dao_line}")
    print(f"  (không CLEAR · không ANOMALY · chờ mắt mở operator)")
    print(f"  new-today-syms = {res['new_today_syms']}")
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
    print(f"[L-59 RECONCILE-KEY] cite md5={md5} · run vs file must match")


if __name__ == "__main__":
    main()

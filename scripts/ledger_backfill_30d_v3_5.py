"""LEDGER BACKFILL 30d v3.5 · KÝ 07/09 GATE-4 · TRỤC GIÁ + G1-G3 direction + b3-fix.

RULES V3.5 (added over V3.4):
  · BỘ-BA fixed semantics: treo = tổng-sống · mới ⊆ treo (không cộng)
  · COVERAGE axis-union thực (per-day-SET union) · 3 số PERP·KHO·FRESH
  · WL án-lệ stat: "44-unique / ~N ghế / 25 mắt · thác N→16"
  · PRICE-JOIN: từng dòng sổ mang {px@seed(PERP) · px_now · max20d} từ spot_klines_1d
      · fallback binance_alpha nếu spot no_spot · [PX-N/A] không silent · footer coverage
  · G1-G3 direction (PROVISIONAL · axis_map.yaml direction_eval)
      · G1 |ret_since_seed|≥30% → floor POST (cấm PRE)
      · G2 dd20≤-40% → POST-DUMP + XẢ-watch
      · G3 sticky 14d (🔴 ∨ WASH-CRASH ∨ S4/S5) → khóa ≤ XẢ-watch
  · Direction persisted per-star (direction · reason) → digest render + star_grades
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
AXIS_YAML = REPO / "data/config/axis_map.yaml"
KLINES_DIR = REPO / "data/raw/spot_klines_1d"
PHASE_MAP = REPO / "docs/case_files/case_state_map.md"
LEDGER_DIR.mkdir(parents=True, exist_ok=True)

FRESH_DELTA_THRESH = 50_000
EXCH_USD_MIN = 200_000
EXCH_PCT_MIN = 1.0
EPISODE_GAP = 14
COVERAGE_LOOKBACK = 14
COVERAGE_MIN_DAYS = 10


def _load_universe():
    if not UNIVERSE_PATH.exists(): return set(), ""
    content = UNIVERSE_PATH.read_bytes()
    md5 = hashlib.md5(content).hexdigest()
    syms = set()
    for line in content.decode("utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"): continue
        syms.add(s.replace("USDT","") if s.endswith("USDT") else s)
    return syms, md5


def _load_direction_yaml():
    """Load direction_eval block from axis_map.yaml (simple parse, no external deps)."""
    if not AXIS_YAML.exists():
        return {"status": "MISSING", "g1_ret_pct_floor": 30, "g2_dd20_pct_ceiling": -40,
                "g3_sticky_window_days": EPISODE_GAP, "g3_reversal_stable_days": 7}
    txt = AXIS_YAML.read_text(encoding="utf-8")
    cfg = {}
    in_block = False
    for line in txt.splitlines():
        if line.startswith("direction_eval:"):
            in_block = True; continue
        if in_block:
            if line and not line.startswith(" ") and not line.startswith("#"): break
            m = re.match(r"\s+(\w+):\s*(.+?)(\s*#.*)?$", line)
            if m:
                k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
                try: cfg[k] = int(v)
                except:
                    try: cfg[k] = float(v)
                    except: cfg[k] = v
    return cfg


def _norm_symbol(sym):
    if not isinstance(sym, str) or not sym: return None
    s = sym.strip()
    if not s: return None
    return s.replace("USDT","") if s.endswith("USDT") else s


def cluster_episodes(rows):
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


# ═════════ SENT anchors (v3.4 unchanged) ═════════
def _relay_sent_by_target(target):
    if not RELAY_LOG.exists(): return None
    txt = RELAY_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    for i in range(len(txt)-1,-1,-1):
        if f"target_date={target}" in txt[i] and "[EXTRACT]" in txt[i]:
            for j in range(i, min(i+10, len(txt))):
                if "[SENT]" in txt[j] and "all_ok=True" in txt[j]:
                    h = re.search(r"hash=([a-f0-9]+)", txt[j])
                    return {"hash": h.group(1) if h else "?"}
    return None


def _digest_sent_by_target(target):
    if not DIGEST_LOG.exists(): return None
    txt = DIGEST_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    d = datetime.strptime(target,"%Y-%m-%d").date()
    send_day = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    fresh_ok=exch_ok=False; done_hash=None
    for i,line in enumerate(txt):
        if send_day in line and f"snapshot={target}.json" in line:
            for j in range(i, min(i+15,len(txt))):
                if "[SENT] Fresh-Wallets" in txt[j] and "ok=True" in txt[j]: fresh_ok=True
                if "[SENT] EXCH-BAL" in txt[j] and "ok=True" in txt[j]: exch_ok=True
                if "[DIGEST-VPS DONE]" in txt[j]:
                    m = re.search(r"hash=([a-f0-9]+)", txt[j])
                    if m: done_hash = m.group(1)
                    break
    if fresh_ok or exch_ok: return {"fresh_ok":fresh_ok,"exch_ok":exch_ok,"hash":done_hash or "?"}
    return None


def _wl_sent_by_target(target):
    """V3.5d FIX: BLOCK-SCOPED (không DOTALL span across next target_date=).
    Regex cũ `.*?` với DOTALL nhảy qua target khác → overcount (25 vs 18 · án V3.5d forensic).
    """
    if not WL_LOG.exists(): return False
    txt = WL_LOG.read_text(encoding="utf-8", errors="replace")
    # Find our target block · scoped to next target_date= boundary
    m = re.search(rf"^INFO:\s+target_date={re.escape(target)}(.*?)(?=^INFO:\s+target_date=|\Z)",
                  txt, re.MULTILINE | re.DOTALL)
    if not m: return False
    return "snapshot SAVED" in m.group(1)


def _load_snap(p):
    if not p.exists(): return {"rows":[]}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {"rows":[]}


def _fresh_delta(target, universe, ngoai_so_sink=None):
    """V3.5d: strict-139 interim + [NGOÀI-SỔ] tracking.
    ngoai_so_sink: dict for tokens that pass Δ≥50k but out-of-universe (không seed, chỉ ghi)."""
    p = SNAP_DIR / f"{target}.json"
    if not p.exists(): return []
    snap = _load_snap(p)
    d = datetime.strptime(target,"%Y-%m-%d").date()
    prev = None
    for dd in range(1,8):
        cand = SNAP_DIR / f"{(d - timedelta(days=dd)).strftime('%Y-%m-%d')}.json"
        if cand.exists():
            try: prev = _load_snap(cand); break
            except: continue
    prev_by = {_norm_symbol(r.get("symbol","")):r for r in (prev.get("rows",[]) if prev else [])}
    rows = []
    for r in snap.get("rows",[]):
        sym = _norm_symbol(r.get("symbol",""))
        if sym is None: continue
        cur=r.get("usd_1d"); pv=prev_by.get(sym,{}).get("usd_1d")
        if cur is None or pv is None: continue
        try:
            delta = float(cur)-float(pv)
            if delta < FRESH_DELTA_THRESH: continue
            if universe and sym not in universe:
                # NGOÀI-SỔ: passes threshold but out-of-universe
                if ngoai_so_sink is not None:
                    ngoai_so_sink.setdefault(target, []).append({"symbol":sym, "delta":delta})
                continue
            rows.append({"symbol":sym,"line":f"snap-pair Δ={delta:+.0f}"})
        except: pass  # L-66-OK (json parse fallback)
    return rows


def _exch_qualified(target, universe):
    p = SNAP_DIR / f"{target}.json"
    if not p.exists(): return []
    snap = _load_snap(p)
    rows = []
    for r in snap.get("rows",[]):
        sym = _norm_symbol(r.get("symbol",""))
        if sym is None or (universe and sym not in universe): continue
        du = r.get("exchange_delta_usd"); mc = r.get("market_cap")
        if du is None: continue
        pct = (float(du)/float(mc)*100) if mc and float(mc)>0 else None
        if abs(float(du))>=EXCH_USD_MIN and pct is not None and abs(pct)>=EXCH_PCT_MIN:
            direction="up" if float(du)>0 else "dn"
            rows.append({"symbol":sym,"direction":direction,
                         "line":f"snap-exch Δ={float(du):+.0f} pct={pct:+.2f}%"})
    return rows


def _parse_gom_h(target, universe):
    """V3.5: keep v3.4 semantics (🔴 KHO still counted as kho events for parity).
    Sticky-🔴 detection is separate (_scan_sticky_events)."""
    if not GH_LOG.exists(): return ([],[])
    txt = GH_LOG.read_text(encoding="utf-8", errors="replace")
    dd_mm = f"{target[8:10]}/{target[5:7]}"
    marker = f"━━ CAMPAIGN-PRE · {dd_mm} · {target} ━━"
    idx = txt.rfind(marker)
    if idx<0: return ([],[])
    end_pat = re.compile(r"════════", re.MULTILINE)
    m_end = end_pat.search(txt, pos=idx+100)
    end_pos = m_end.start() if m_end else len(txt)
    block = txt[idx:end_pos]
    perp=[]; kho=[]
    in_g=in_r=False
    for line in block.split("\n"):
        if "🟢 GOM/STAGING" in line: in_g=True; in_r=False; continue
        if "🔴 KHO ĐỘNG GIỮA ĐẠP" in line: in_r=True; in_g=False; continue
        if line.startswith("🌊 ") or line.startswith("⏳ ") or line.startswith("👁 "):
            in_g=in_r=False; continue
        m = re.match(r"^\s+[🥇🥈🥉•⚪]\s+(\S+?)USDT?\s+\[([^\]]+)\]", line)
        if m:
            sym = _norm_symbol(m.group(1))
            if sym is None or (universe and sym not in universe): continue
            tag = m.group(2)
            lane = "perp" if "H2" in tag else "kho"
            if "H1" in tag and "H2" in tag: lane="both"
            evt = {"symbol":sym,"lane":lane,"line":line.strip()}
            if in_g or in_r:
                if lane in ("perp","both"): perp.append(evt)
                if lane in ("kho","both"): kho.append(evt)
    return (perp, kho)


# ═════════ V3.5b · G3 STICKY sources ĐÍCH DANH ═════════
# Rule V3.5b: match tag-name as-printed only:
#   {🔴-block · "WASH-CRASH" walletset · S4/S5 phase}
# CẤM match ¹-generic (quiet bị khóa oan). ¹-only tokens liệt DIFF.
def _scan_sticky_events(universe, window_days=90):
    """Return dict: symbol → [{date, source}] where source ∈ {🔴-block, WASH-CRASH}.
    Also emit sidecar: sticky_diff_only1_syms cho token vốn có ¹ mà không có tag-name."""
    if not GH_LOG.exists(): return {}, set()
    txt = GH_LOG.read_text(encoding="utf-8", errors="replace")
    sticky = defaultdict(list)
    only1_syms = set()   # sticky-vì-¹-only = QUIET bị khóa oan · thả
    # Pattern 1: 🔴 KHO ĐỘNG blocks (đích danh)
    for m in re.finditer(r"━━ CAMPAIGN-PRE · \d{2}/\d{2} · (\d{4}-\d{2}-\d{2}) ━━", txt):
        d_str = m.group(1)
        idx = m.end()
        end_next = txt.find("━━ CAMPAIGN-PRE", idx)
        block = txt[idx : end_next if end_next>0 else len(txt)]
        red_idx = block.find("🔴 KHO ĐỘNG GIỮA ĐẠP")
        if red_idx >= 0:
            end_idx = min([i for i in [block.find("🌊 ",red_idx), block.find("⏳ ",red_idx), block.find("👁 ",red_idx)] if i>0] + [len(block)])
            red_block = block[red_idx:end_idx]
            for lm in re.finditer(r"^\s+[🥇🥈🥉•⚪]\s+(\S+?)USDT?\s+\[", red_block, re.MULTILINE):
                sym = _norm_symbol(lm.group(1))
                if sym and (not universe or sym in universe):
                    sticky[sym].append({"date": d_str, "source": "🔴-block"})
    # Pattern 2: WASH-CRASH walletset tag (đích danh)
    for m in re.finditer(r"(\S+?)USDT?\s+.*?WALLETSET:\s*WASH-CRASH", txt):
        sym = _norm_symbol(m.group(1))
        if sym and (not universe or sym in universe):
            sticky[sym].append({"date": None, "source": "WASH-CRASH"})
    # Pattern 3: ¹-generic → DIFF list (tokens sticky-vì-¹-only, KHÔNG thêm vào sticky)
    only1_raw = set()
    for m in re.finditer(r"(\S+?)¹\s*\(ngày\s+\d+/\d+\)", txt):
        sym = _norm_symbol(m.group(1))
        if sym and (not universe or sym in universe):
            only1_raw.add(sym)
    # Subtract ones already sticky via 🔴/WASH-CRASH
    only1_syms = only1_raw - set(sticky.keys())
    return dict(sticky), only1_syms


def _load_phase_sticky(universe):
    """Read case_state_map.md for S4/S5 phase tokens · returns {sym: phase}."""
    if not PHASE_MAP.exists(): return {}
    txt = PHASE_MAP.read_text(encoding="utf-8", errors="replace")
    out = {}
    # md format: | SYM | S4-XA | ... |  (loose match, phase starting with S4 or S5)
    for m in re.finditer(r"\|\s*([A-Z0-9_龙虾]+)\s*\|\s*(S[45][A-Z0-9_-]*)", txt):
        sym = _norm_symbol(m.group(1))
        if sym and (not universe or sym in universe):
            out[sym] = m.group(2)
    return out


def _load_phase_map():
    """Read case_state_map.md · return {symbol: state}. S4/S5 = XẢ/DUMP phases."""
    if not PHASE_MAP.exists(): return {}
    txt = PHASE_MAP.read_text(encoding="utf-8", errors="replace")
    phases = {}
    for m in re.finditer(r"\|\s*(\w+)\s*\|\s*(S[0-9]+[A-Z_-]*)\s*\|", txt):
        phases[_norm_symbol(m.group(1))] = m.group(2)
    return phases


# ═════════ V3.5b · LATTICE severity ═════════
# Direction ordered by SEVERITY (worse = higher rank):
#   PRE (0) < POST-FLOOR (1) < POST-DUMP (2) < XẢ-WATCH (3) < XẢ (4)
# Sticky context = XẢ-WATCH (rank 3) — WORSE than mechanical POST-DUMP because
# it means "we know KHO is releasing, coming xả" vs "just price dumped".
# Directive V3.5b: max-severity{context, G1, G2, G3} = higher rank wins.
DIRECTION_RANK = {"PRE": 0, "POST-FLOOR": 1, "POST": 1, "POST-DUMP": 2, "XẢ-WATCH": 3, "XẢ": 4}


def _max_severity(*dirs):
    """Pick direction with highest rank."""
    best = "PRE"; best_rank = 0
    for d in dirs:
        if d is None: continue
        r = DIRECTION_RANK.get(d, 0)
        if r > best_rank:
            best = d; best_rank = r
    return best


# ═════════ V3.5 · PRICE-JOIN from spot_klines_1d ═════════
def _load_klines_for_date(d_str):
    """Return dict: bare_symbol → {close, high, low, venue}. Read parquet from partition."""
    p = KLINES_DIR / f"date={d_str}" / "part-0.parquet"
    if not p.exists(): return {}
    try:
        import pandas as pd
    except ImportError:
        return {}
    try:
        df = pd.read_parquet(p)
    except: return {}
    out = {}
    for _, row in df.iterrows():
        sym_raw = str(row.get("symbol",""))
        sym_norm = _norm_symbol(sym_raw)
        if sym_norm is None: continue
        venue = row.get("venue","")
        close = row.get("close")
        if close is None or (isinstance(close,float) and (close!=close)): continue  # NaN
        # If we already have a value, prefer spot > alpha > store
        cur = out.get(sym_norm)
        if cur is None or (venue=="binance_spot" and cur.get("venue")!="binance_spot"):
            out[sym_norm] = {"close": float(close),
                             "high": float(row.get("high",0.0) or 0.0),
                             "low":  float(row.get("low",0.0) or 0.0),
                             "venue": venue}
    return out


def price_join_symbol(sym, seed_date_str, target_date_str, klines_cache):
    """Return {px_at_seed, px_now, max20d, px_src, ret_pct, dd20_pct}.
    px_src ∈ {spot, alpha, store, N/A}. Missing → [PX-N/A]."""
    # px @ seed
    seed_row = klines_cache.get(seed_date_str, {}).get(sym)
    px_seed = seed_row["close"] if seed_row else None
    src_seed = seed_row["venue"] if seed_row else None
    # px_now (target)
    now_row = klines_cache.get(target_date_str, {}).get(sym)
    px_now = now_row["close"] if now_row else None
    src_now = now_row["venue"] if now_row else None
    # max 20d — scan back 20 days from target
    max_high = None
    end_d = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    for i in range(20):
        d = (end_d - timedelta(days=i)).strftime("%Y-%m-%d")
        row = klines_cache.get(d, {}).get(sym)
        if row and row.get("high"):
            if max_high is None or row["high"] > max_high: max_high = row["high"]
    # Compute ret_since_seed, dd20 (from max20d to px_now)
    ret_pct = None
    if px_seed and px_now:
        try: ret_pct = (px_now - px_seed) / px_seed * 100
        except: pass  # L-66-OK (json parse fallback)
    dd20_pct = None
    if max_high and px_now:
        try: dd20_pct = (px_now - max_high) / max_high * 100
        except: pass  # L-66-OK (json parse fallback)
    if px_now is None:
        px_src = "N/A"
    elif src_now == "binance_spot":
        px_src = "spot"
    elif src_now == "binance_alpha":
        px_src = "alpha"
    else:
        px_src = src_now or "N/A"
    return {"px_at_seed": px_seed, "px_now": px_now, "max20d": max_high,
            "src_seed": src_seed, "src_now": src_now, "px_src": px_src,
            "ret_pct": ret_pct, "dd20_pct": dd20_pct}


def _preload_klines_cache(target, window_days):
    """Load klines for target + 30d back."""
    cache = {}
    end = datetime.strptime(target,"%Y-%m-%d").date()
    for i in range(window_days + 25):  # extra 5 for max20d headroom
        d_str = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        cache[d_str] = _load_klines_for_date(d_str)
    return cache


# ═════════ V3.5b · G1-G3 direction gates · LATTICE max-severity ═════════
def apply_direction_gates(sym, per_axis_events, price_data, sticky_map, phase_map, dir_cfg):
    """V3.5b: direction = max-severity{context/G3, G1, G2}.
    Sticky context (G3-🔴/WASH-CRASH/S4-S5) = XẢ-WATCH (rank 3, WORSE than POST-DUMP).
    ¹-generic KHÔNG match (chỉ tag-name as-printed).
    Return {direction, reasons[], sticky, flags}."""
    g1_floor = dir_cfg.get("g1_ret_pct_floor", 30)
    g2_ceiling = dir_cfg.get("g2_dd20_pct_ceiling", -40)
    reasons = []; flags = []
    candidates = []  # (rank_source, direction)

    # G3 sticky ĐÍCH DANH — 🔴/WASH-CRASH/S4-S5 · V3.5c: flag mang source+date
    sticky = False; sticky_kinds = set(); sticky_tags = []
    for r in sticky_map.get(sym, []):
        src = r.get("source", "")
        if src == "🔴-block" and "🔴" not in sticky_kinds:
            d_iso = r.get("date","?")
            d_short = f"{d_iso[8:10]}/{d_iso[5:7]}" if d_iso and d_iso != "?" else "?"
            tag = f"STICKY-XẢ vì 🔴-{d_short}"
            reasons.append(f"G3-sticky: 🔴 {d_iso}")
            flags.append(tag); sticky_tags.append(tag); sticky_kinds.add("🔴"); sticky = True
        elif src == "WASH-CRASH" and "WC" not in sticky_kinds:
            tag = "STICKY-XẢ vì WASH-CRASH"
            reasons.append("G3-sticky: WASH-CRASH")
            flags.append(tag); sticky_tags.append(tag); sticky_kinds.add("WC"); sticky = True
    ph = phase_map.get(sym)
    if ph and (ph.startswith("S4") or ph.startswith("S5")):
        tag = f"STICKY-XẢ vì {ph}"
        reasons.append(f"G3-sticky: phase={ph}")
        flags.append(tag); sticky_tags.append(tag); sticky = True

    if sticky:
        candidates.append(("G3", "XẢ-WATCH"))

    # G2 dd20 ≤ -40%
    dd = price_data.get("dd20_pct")
    if dd is not None and dd <= g2_ceiling:
        reasons.append(f"G2: dd20={dd:.1f}%≤{g2_ceiling}%")
        flags.append(f"POST-DUMP-dd{dd:.0f}%")
        candidates.append(("G2", "POST-DUMP"))

    # G1 |ret| ≥ 30% → POST (floor)
    ret = price_data.get("ret_pct")
    if ret is not None and abs(ret) >= g1_floor:
        reasons.append(f"G1: |ret|={abs(ret):.1f}%≥{g1_floor}%")
        flags.append(f"G1-POST-FLOOR-ret{ret:+.0f}%")
        candidates.append(("G1", "POST"))

    if not candidates:
        direction = "PRE"
    else:
        direction = _max_severity(*(c[1] for c in candidates))

    return {"direction": direction, "reasons": reasons, "sticky": sticky, "flags": flags}


def backfill_v3_5(target, window_days=30):
    universe, uni_md5 = _load_universe()
    dir_cfg = _load_direction_yaml()
    events = []
    per_src = defaultdict(int); per_src_unique = defaultdict(set)
    coverage_days = defaultdict(set)  # axis → set(dates present)
    excluded = defaultdict(int)

    end = datetime.strptime(target,"%Y-%m-%d").date()
    start = end - timedelta(days=window_days)
    ngoai_so = {}  # V3.5d: {target_date: [{symbol, delta}]} for out-of-u50 fresh hits

    # Preload klines
    klines_cache = _preload_klines_cache(target, window_days)
    # Sticky map + only1 diff + phase map (V3.5b: named-only)
    sticky_map, only1_syms = _scan_sticky_events(universe)
    phase_map = _load_phase_map()

    # WL waterfall (v3.4)
    wf = build_wl_waterfall(start, end, universe)
    wl_seeds, wl_unknown = wl_episode_with_coverage_guard(
        wf["memberships_final"], wf["per_day_present"], start, end)

    d = start
    while d <= end:
        d_str = d.strftime("%Y-%m-%d")
        relay_sent = _relay_sent_by_target(d_str)
        if relay_sent:
            perp, kho = _parse_gom_h(d_str, universe)
            coverage_days["PERP-gomh"].add(d_str); coverage_days["KHO-SAN-gomh"].add(d_str)
            for evt in perp:
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type":"FIRE-SENT",
                    "axis":"PERP","symbol":evt["symbol"],"target_date":d_str,
                    "source":"gomh","source_tag":"ᴳ",
                    "sent_hash":relay_sent["hash"],"source_line":evt["line"][:80]})
                per_src["gom_h_perp_SENT"] += 1
                per_src_unique["gom_h_perp_SENT"].add(evt["symbol"])
            for evt in kho:
                events.append({"ts_utc": f"{d_str}T00:00:00Z", "event_type":"FIRE-SENT",
                    "axis":"KHO-SAN","symbol":evt["symbol"],"target_date":d_str,
                    "source":"gomh_h1","source_tag":"ᴳ",
                    "sent_hash":relay_sent["hash"],"source_line":evt["line"][:80]})
                per_src["gom_h_kho_SENT"] += 1
                per_src_unique["gom_h_kho_SENT"].add(evt["symbol"])
        else:
            excluded["gom_h_NO-relay-SENT"] += 1

        digest_sent = _digest_sent_by_target(d_str)
        if digest_sent and digest_sent.get("fresh_ok"):
            coverage_days["FRESH-CHAIN"].add(d_str)
            for r in _fresh_delta(d_str, universe, ngoai_so_sink=ngoai_so):
                events.append({"ts_utc":f"{d_str}T00:00:00Z","event_type":"FRESH-DELTA-SENT",
                    "axis":"FRESH-CHAIN","symbol":r["symbol"],"target_date":d_str,
                    "source":"fresh_digest","source_tag":"ᶠ",
                    "sent_hash":digest_sent["hash"],"source_line":r["line"][:80]})
                per_src["fresh_delta_SENT"] += 1
                per_src_unique["fresh_delta_SENT"].add(r["symbol"])
        else:
            excluded["fresh_NO-digest-SENT"] += 1

        if digest_sent and digest_sent.get("exch_ok"):
            coverage_days["KHO-SAN-exch"].add(d_str)
            for r in _exch_qualified(d_str, universe):
                events.append({"ts_utc":f"{d_str}T00:00:00Z","event_type":"EXCH-QUALIFIED-SENT",
                    "axis":"KHO-SAN","symbol":r["symbol"],"target_date":d_str,
                    "source":"exch_digest","source_tag":"ᴱ",
                    "sent_hash":digest_sent["hash"],"source_line":r["line"][:80]})
                per_src["exch_qualified_SENT"] += 1
                per_src_unique["exch_qualified_SENT"].add(r["symbol"])
        else:
            excluded["exch_NO-digest-SENT"] += 1

        if _wl_sent_by_target(d_str):
            coverage_days["WL"].add(d_str)
            for sym in wl_seeds.get(d_str, set()):
                events.append({"ts_utc":f"{d_str}T00:00:00Z","event_type":"WATCHLIST-B-NEW-EPISODE",
                    "axis":"PERP","symbol":sym,"target_date":d_str,
                    "source":"watchlist_episode","source_tag":"ᵂ",
                    "sent_hash":"wl-sent",
                    "source_line":f"NEW-EPISODE (gap≥{EPISODE_GAP}d · coverage≥{COVERAGE_MIN_DAYS}d/14): {sym}"})
                per_src["watchlist_b_episode_SENT"] += 1
                per_src_unique["watchlist_b_episode_SENT"].add(sym)
            for sym in wl_unknown.get(d_str, set()):
                excluded["wl_UNKNOWN-EPISODE"] += 1
        d += timedelta(days=1)
    events.sort(key=lambda e: (e["ts_utc"], e["symbol"], e["axis"]))

    # p15 UNIVERSE-BOUND
    per_axis_uniq = defaultdict(set)
    for e in events: per_axis_uniq[e["axis"]].add(e["symbol"])
    p15_violations = {}
    for ax, syms in per_axis_uniq.items():
        oob = syms - universe if universe else set()
        if oob: p15_violations[ax] = {"n_oob":len(oob),"syms":sorted(oob)}

    # STARS + G1-G3 direction
    per_sym = defaultdict(lambda: {"axes":set(),"events":[],"latest":{}})
    for e in events:
        per_sym[e["symbol"]]["axes"].add(e["axis"])
        per_sym[e["symbol"]]["events"].append(e)
        cur = per_sym[e["symbol"]]["latest"].get(e["axis"])
        if cur is None or e["target_date"] > cur["target_date"]:
            per_sym[e["symbol"]]["latest"][e["axis"]] = e
    stars_all = [(s,info) for s,info in per_sym.items() if len(info["axes"]) >= 2]
    px_stats = {"n_stars": len(stars_all), "n_pxok":0, "n_pxna":0}
    star_records = []
    for sym, info in stars_all:
        # V3.5b · G1-ANCHOR = FIRST-SEED-ANY-AXIS (earliest event across all axes)
        all_dates = [e["target_date"] for e in info["events"]]
        seed_date = min(all_dates) if all_dates else target
        seed_axis = None
        for e in info["events"]:
            if e["target_date"] == seed_date:
                seed_axis = e["axis"]; break
        pd_ = price_join_symbol(sym, seed_date, target, klines_cache)
        pd_["seed_date"] = seed_date; pd_["seed_axis"] = seed_axis
        if pd_["px_now"] is not None: px_stats["n_pxok"] += 1
        else: px_stats["n_pxna"] += 1
        gates = apply_direction_gates(sym, info["latest"], pd_, sticky_map, phase_map, dir_cfg)
        # Flag ¹-only-QUIET (thả từ sticky · ghi diff)
        if sym in only1_syms:
            gates["flags"].append("¹-ONLY-QUIET-RELEASED")
            gates["reasons"].append("V3.5b: ¹-only không match tag-name → thả khỏi sticky")
        star_records.append({"symbol":sym,"axes":sorted(info["axes"]),"latest":info["latest"],
                             "price":pd_,"direction":gates["direction"],
                             "reasons":gates["reasons"],"sticky":gates["sticky"],
                             "flags":gates["flags"]})

    # BỘ-BA fixed: treo = ALL stars-alive · mới ⊆ treo
    treo_total_alive = len(stars_all)
    new_today_syms = []
    for sr in star_records:
        events_today = [e for e in sr["latest"].values() if e["target_date"] == target]
        axes_before = {e["axis"] for e in per_sym[sr["symbol"]]["events"] if e["target_date"] < target}
        if events_today and len(axes_before) < 2:
            new_today_syms.append(sr["symbol"])

    # ghế min/max = List-B size min/max in window (independent from cluster_episodes count)
    listb_sizes = []
    d = start
    while d <= end:
        d_str = d.strftime("%Y-%m-%d")
        p = WL_STATE / f"hedge_watchlist_{d_str}.json"
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                listb_sizes.append((d_str, len(_list_b_tokens_from(data))))
            except: pass  # L-66-OK (json parse fallback)
        d += timedelta(days=1)
    ghe_stats = {"n_days_with_listb": len(listb_sizes),
                 "min_size": min(s for _,s in listb_sizes) if listb_sizes else 0,
                 "max_size": max(s for _,s in listb_sizes) if listb_sizes else 0,
                 "avg_size": sum(s for _,s in listb_sizes)/len(listb_sizes) if listb_sizes else 0}

    return {
        "universe_size": len(universe), "universe_md5": uni_md5,
        "dir_cfg": dir_cfg,
        "waterfall": wf,
        "events": events,
        "per_src": dict(per_src),
        "per_src_unique": {k:len(v) for k,v in per_src_unique.items()},
        "coverage_days": {k: sorted(v) for k,v in coverage_days.items()},
        "excluded": dict(excluded),
        "wl_unknown_days": {k:sorted(v) for k,v in wl_unknown.items() if v},
        "p15_violations": p15_violations,
        "treo_total_alive": treo_total_alive,
        "new_today_syms": new_today_syms,
        "star_records": star_records,
        "px_stats": px_stats,
        "ghe_stats": ghe_stats,
        "only1_syms": sorted(only1_syms),
        "ngoai_so_fresh": ngoai_so,
    }


# WATERFALL (v3.4 unchanged) ─────────────────
def _list_b_tokens_from(data):
    lb = data.get("list_b_tokens")
    if lb is None: return []
    if isinstance(lb, list): return [t for t in lb if isinstance(t,str)]
    if isinstance(lb, dict): return [k for k in lb.keys() if isinstance(k,str)]
    return []


def _classify_drop(norm_val, raw, universe):
    if not norm_val: return "rác-parser"
    if not norm_val.replace("_","").replace("-","").isalnum(): return "rác-parser"
    for suffix in ("USDT","USDC","BUSD","FDUSD","TUSD"):
        if norm_val.endswith(suffix):
            trimmed = norm_val[:-len(suffix)]
            if trimmed and trimmed in universe: return "norm-miss-nối-lại"
    return "thật-ngoài-vũ-trụ"


def build_wl_waterfall(window_start, window_end, universe):
    membership_start = window_start - timedelta(days=EPISODE_GAP + COVERAGE_LOOKBACK + 5)
    tier1_raw = []; tier2_norm = []
    per_day_present = {}
    d = membership_start
    while d <= window_end:
        d_str = d.strftime("%Y-%m-%d")
        p = WL_STATE / f"hedge_watchlist_{d_str}.json"
        if p.exists():
            per_day_present[d_str] = True
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for tok in _list_b_tokens_from(data):
                    tier1_raw.append({"date":d_str,"raw":tok})
            except: pass  # L-66-OK (json parse fallback)
        else:
            per_day_present[d_str] = False
        d += timedelta(days=1)
    for r in tier1_raw:
        n = _norm_symbol(r["raw"])
        if n is not None: tier2_norm.append({"date":r["date"],"raw":r["raw"],"norm":n})
    tier3 = []; drops=defaultdict(list); drops_sym=defaultdict(set)
    for r in tier2_norm:
        if r["norm"] in universe:
            tier3.append(r)
        else:
            cls = _classify_drop(r["norm"], r["raw"], universe)
            drops[cls].append(r); drops_sym[cls].add(r["norm"])
    tier4=[]; dropped_bl=0
    for r in tier3:
        d_prev=(date.fromisoformat(r["date"])-timedelta(days=1)).strftime("%Y-%m-%d")
        if per_day_present.get(d_prev, False): tier4.append(r)
        else: dropped_bl += 1
    # Ghế = episodes formed on tier3
    episodes = cluster_episodes([{"symbol":r["norm"],"date":r["date"]} for r in tier3])
    n_ghe = len(episodes)
    n_mat = sum(1 for v in per_day_present.values() if v and window_start <= date.fromisoformat([k for k,vv in per_day_present.items() if vv][0]) if False)
    # Simpler: mắt = days-present in window
    n_mat_window = sum(1 for k,v in per_day_present.items() if v and window_start <= date.fromisoformat(k) <= window_end)
    return {
        "tier1_raw_n": len(tier1_raw), "tier1_raw_uniq": len(set(r["raw"] for r in tier1_raw)),
        "tier2_norm_n": len(tier2_norm), "tier2_norm_uniq": len(set(r["norm"] for r in tier2_norm)),
        "tier3_after_universe_n": len(tier3), "tier3_after_universe_uniq": len(set(r["norm"] for r in tier3)),
        "tier3_drops": {cls:{"n":len(drops[cls]),"n_uniq":len(drops_sym[cls]),
                             "sample":sorted(drops_sym[cls])[:20]} for cls in drops},
        "tier4_after_baseline_n": len(tier4), "tier4_after_baseline_uniq": len(set(r["norm"] for r in tier4)),
        "tier4_dropped_no_baseline": dropped_bl, "tier4_gate_enforced": False,
        "n_ghe": n_ghe, "n_mat_window": n_mat_window,
        "memberships_final": [{"symbol":r["norm"],"date":r["date"]} for r in tier3],
        "per_day_present": per_day_present,
    }


def wl_episode_with_coverage_guard(memberships, per_day_present, ws, we):
    episodes = cluster_episodes(memberships)
    per_day_new = defaultdict(set); per_day_unknown = defaultdict(set)
    for ep in episodes:
        first = ep[0]; eds = first["date"]; ed = date.fromisoformat(eds)
        if not (ws <= ed <= we): continue
        cov = 0
        for i in range(1, COVERAGE_LOOKBACK+1):
            dc = (ed - timedelta(days=i)).strftime("%Y-%m-%d")
            if per_day_present.get(dc, False): cov += 1
        if cov >= COVERAGE_MIN_DAYS: per_day_new[eds].add(first["symbol"])
        else: per_day_unknown[eds].add(first["symbol"])
    return (dict(per_day_new), dict(per_day_unknown))


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

    res = backfill_v3_5(args.target, args.window)
    wf = res["waterfall"]
    dir_cfg = res["dir_cfg"]

    print(f"[BACKFILL v3.5 · TRỤC-GIÁ + G1-G3 + BỘ-BA-FIX] target={args.target}")
    print(f"[UNIVERSE-CITE] file={UNIVERSE_PATH.name} · md5={res['universe_md5']} · n={res['universe_size']}")
    print(f"[DIR-CFG] status={dir_cfg.get('status')} · G1={dir_cfg.get('g1_ret_pct_floor')}% · G2={dir_cfg.get('g2_dd20_pct_ceiling')}% · G3-window={dir_cfg.get('g3_sticky_window_days')}d")
    print()

    wl_cov_days = len(res["coverage_days"].get("WL", []))
    print("## WL WATERFALL 5-TIER (V3.5 · án-lệ mang số)")
    print(f"[stat] {wf['tier3_after_universe_uniq']}-unique-trong-vũ-trụ / {wf['n_ghe']} ghế / {wl_cov_days} ngày-mắt · thác {wf['tier4_after_baseline_n']}→{res['per_src'].get('watchlist_b_episode_SENT',0)}")
    print(f"[tier-3 drops] rác-parser={wf['tier3_drops'].get('rác-parser',{}).get('n',0)} · norm-miss={wf['tier3_drops'].get('norm-miss-nối-lại',{}).get('n',0)} · thật-ngoài={wf['tier3_drops'].get('thật-ngoài-vũ-trụ',{}).get('n',0)}")
    print()

    print("## 4 SỐ per source")
    for src in sorted(res["per_src"].keys()):
        print(f"  {src:<32} {res['per_src'][src]:>4} events · {res['per_src_unique'].get(src,0):>3} unique")
    print()

    # COVERAGE axis-union THẬT (per-day-set union)
    perp_set = res["coverage_days"].get("PERP-gomh",set()) if False else set(res["coverage_days"].get("PERP-gomh",[]))
    wl_set = set(res["coverage_days"].get("WL",[]))
    kho_g_set = set(res["coverage_days"].get("KHO-SAN-gomh",[]))
    kho_e_set = set(res["coverage_days"].get("KHO-SAN-exch",[]))
    fresh_set = set(res["coverage_days"].get("FRESH-CHAIN",[]))
    perp_union = perp_set | wl_set
    kho_union = kho_g_set | kho_e_set
    win_n = args.window + 1
    print("## COVERAGE (V3.5 axis-union THẬT · 3 số)")
    print(f"  PERP  = {len(perp_union)}/{win_n}  (union {len(perp_set)} gomh ∪ {len(wl_set)} wl)")
    print(f"  KHO   = {len(kho_union)}/{win_n}   (union {len(kho_g_set)} gomh-H1 ∪ {len(kho_e_set)} exch)")
    print(f"  FRESH = {len(fresh_set)}/{win_n}")
    print()

    per_axis = defaultdict(set)
    for e in res["events"]: per_axis[e["axis"]].add(e["symbol"])
    perp = per_axis.get("PERP",set()); kho = per_axis.get("KHO-SAN",set()); fresh = per_axis.get("FRESH-CHAIN",set())
    print(f"## Ma trận giao")
    print(f"  n_perp={len(perp)} · n_kho={len(kho)} · n_fresh={len(fresh)}")
    print(f"  |PERP∩FRESH|={len(perp&fresh)} · |KHO∩FRESH|={len(kho&fresh)} · |PERP∩KHO|={len(perp&kho)} · |all|={len(perp&kho&fresh)}")
    print()

    print(f"## p15 UNIVERSE-BOUND")
    if not res["p15_violations"]:
        print(f"  ✅ zero out-of-bound")
    else:
        for ax, info in res["p15_violations"].items():
            print(f"  ❌ {ax}: n_oob={info['n_oob']} · syms={info['syms']}")
    print()

    # BỘ-BA fixed semantics: treo=tổng-sống · mới⊆treo
    treo = res["treo_total_alive"]; new_syms = res["new_today_syms"]; n_new = len(new_syms)
    print(f"## DAO CHECK · BỘ-BA (V3.5 FIXED)")
    dao_line = f"[DAO-DEFERRED coverage: fresh {len(fresh_set)}/{win_n} · kho {len(kho_union)}/{win_n} · perp {len(perp_union)}/{win_n}] treo={treo}(tổng-sống) · mới={n_new}⊆treo"
    print(f"  {dao_line}")
    print(f"  new-syms = {new_syms}")
    print(f"  px-coverage = {res['px_stats']['n_pxok']}/{res['px_stats']['n_stars']} stars have px_now")
    print()

    # STAR-LIST with G1-G3 direction + px · 3 TẦNG (V3.5b render)
    print("## ⭐-LIST 3 TẦNG với DIRECTION V3.5b")
    star_records = sorted(res["star_records"], key=lambda r: (-len(r["axes"]), r["symbol"]))
    tier_pre = [sr for sr in star_records if sr["direction"] == "PRE"]
    tier_xa  = [sr for sr in star_records if sr["direction"] in ("XẢ-WATCH","XẢ")]
    tier_post = [sr for sr in star_records if sr["direction"] in ("POST-DUMP","POST","POST-FLOOR")]

    def _fmt_sr(sr):
        px = sr["price"]
        parts = [f"{ax[:4]}={e['target_date'][5:]}{e.get('source_tag','?')}" for ax, e in sr["latest"].items()]
        ret_str = f"ret{px['ret_pct']:+.1f}%" if px["ret_pct"] is not None else "ret[PX-N/A]"
        dd_str = f"dd{px['dd20_pct']:+.1f}%" if px["dd20_pct"] is not None else "dd[PX-N/A]"
        px_tag = f"[PX-SRC={px['px_src']}·seed={px['seed_date'][5:]}({px['seed_axis'][:4]})]"
        dir_reason = ",".join(sr["flags"]) if sr["flags"] else ""
        new_flag = " [NEW]" if sr["symbol"] in new_syms else ""
        return f"  {sr['symbol']:<15} {len(sr['axes'])}-trục ({'+'.join(sr['axes'])}) {' · '.join(parts)} · {ret_str} {dd_str} → {sr['direction']}[{dir_reason}] {px_tag}{new_flag}"

    print(f"\n─── TẦNG 1 · ⭐-PRE ({len(tier_pre)}) ───")
    for sr in tier_pre: print(_fmt_sr(sr))
    print(f"\n─── TẦNG 2 · 🔻 XẢ-WATCH+XẢ ({len(tier_xa)}) [câu-soi bộ XẢ: rút về đâu? ai nhận trong dump? dính CEX-list?] ───")
    for sr in tier_xa: print(_fmt_sr(sr))
    print(f"\n─── TẦNG 3 · POST-DUMP+🌊 ({len(tier_post)}) ───")
    for sr in tier_post: print(_fmt_sr(sr))

    # V3.5e NGOÀI-SỔ: fresh Δ≥50k tokens out-of-universe (strict-139 interim)
    # + per-token counter /30d + [ĐỀ-CỬ-UNIVERSE] rule cho token ≥3× (chờ chữ 27/09)
    if res.get("ngoai_so_fresh"):
        print(f"\n## [NGOÀI-SỔ] fresh Δ≥50k out-of-u50 (V3.5e strict-139 + counter)")
        from collections import defaultdict as _dd
        per_token_count = _dd(int)
        for d_str, hits in sorted(res["ngoai_so_fresh"].items()):
            hit_str = ", ".join(f"{h['symbol']} Δ={h['delta']:+.0f}" for h in hits)
            print(f"  [NGOÀI-SỔ: {d_str}] {hit_str}")
            for h in hits: per_token_count[h["symbol"]] += 1
        # ĐỀ-CỬ-UNIVERSE: token ≥3× trong window
        print(f"\n  Per-token counter (/{args.window}d window):")
        for tok, n in sorted(per_token_count.items(), key=lambda x: (-x[1], x[0])):
            marker = "  ⇒ [ĐỀ-CỬ-UNIVERSE]" if n >= 3 else ""
            print(f"    {tok}: {n}×{marker}")
        deexue = [t for t, n in per_token_count.items() if n >= 3]
        for tok in deexue:
            n = per_token_count[tok]
            print(f"\n  [ĐỀ-CỬ-UNIVERSE: {tok} {n}×/{args.window}d — chờ chữ 27/09]")
        if not deexue:
            print(f"\n  (không token nào đạt ngưỡng 3× · BEAT/ONE/B đếm tiếp không đề cử sớm)")

    # V3.5b sticky diff: ¹-only tokens released from lockup
    if res["only1_syms"]:
        print(f"\n## STICKY-DIFF V3.5b · ¹-ONLY-QUIET-RELEASED (n={len(res['only1_syms'])})")
        print(f"  tokens: {res['only1_syms']}")
        print(f"  → thả khỏi sticky lockup (KHÔNG match tag-name as-printed)")

    # V3.5b ghế artifact-based stat
    gs = res["ghe_stats"]
    print(f"\n## LIST-B GHẾ ARTIFACT-BASED (V3.5b nguồn độc lập)")
    print(f"  n_days_with_listb={gs['n_days_with_listb']} · min={gs['min_size']} · max={gs['max_size']} · avg={gs['avg_size']:.1f}")
    print(f"  → so với cluster_episodes count ({wf.get('n_ghe',0)}) · án-lệ sửa: List-B window sizes [{gs['min_size']},{gs['max_size']}]")

    # V3.5b PX 5-row sanity table
    print(f"\n## PX SANITY TABLE (V3.5b · 5 dòng · tay-tính đối chiếu)")
    print(f"{'sym':<10} {'seed':<12} {'src_seed':<8} {'px@seed':>10} {'px_now':>10} {'max20d':>10} {'ret%':>7} {'dd%':>7}")
    picks = ["COLLECT","MITO","CYS"]
    extras = [sr["symbol"] for sr in star_records if sr["symbol"] not in picks][:2]
    for name in picks + extras:
        sr = next((r for r in star_records if r["symbol"]==name), None)
        if not sr:
            print(f"{name:<10} [not-a-star]")
            continue
        p = sr["price"]
        s_ret = f"{p['ret_pct']:+.1f}" if p['ret_pct'] is not None else "[N/A]"
        s_dd  = f"{p['dd20_pct']:+.1f}" if p['dd20_pct'] is not None else "[N/A]"
        s_pxs = f"{p['px_at_seed']:.6f}" if p['px_at_seed'] is not None else "[N/A]"
        s_pxn = f"{p['px_now']:.6f}" if p['px_now'] is not None else "[N/A]"
        s_max = f"{p['max20d']:.6f}" if p['max20d'] is not None else "[N/A]"
        print(f"{name:<10} {p['seed_date']:<12} {(p['src_seed'] or '-'):<8} {s_pxs:>10} {s_pxn:>10} {s_max:>10} {s_ret:>7} {s_dd:>7}")

    p = LEDGER_DIR / f"events_{args.target}.jsonl"
    content = "\n".join(json.dumps(e, ensure_ascii=False) for e in res["events"]).encode("utf-8")
    md5 = _write_atomic(p, content)
    print(f"\n[WRITE-JSONL] {p} · md5={md5}")

    # Star records dump (V3.5b · includes seed_date/seed_axis)
    star_dump = LEDGER_DIR / f"stars_{args.target}.jsonl"
    sc = "\n".join(json.dumps({
        "symbol": sr["symbol"], "axes": sr["axes"],
        "direction": sr["direction"], "reasons": sr["reasons"], "flags": sr["flags"],
        "sticky": sr["sticky"], "px": {k:v for k,v in sr["price"].items()},
        "latest_dates": {ax: e["target_date"] for ax, e in sr["latest"].items()},
    }, ensure_ascii=False) for sr in star_records).encode("utf-8")
    md5_stars = _write_atomic(star_dump, sc)
    print(f"\n[WRITE-STARS] {star_dump} · md5={md5_stars}")


if __name__ == "__main__":
    main()

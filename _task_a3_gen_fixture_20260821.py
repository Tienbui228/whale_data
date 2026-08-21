#!/usr/bin/env python3
"""[A3] Generate L-58-draft conformance fixture — 5 tokens + case-gap GUA.

Runs BOTH consumers (registry via lib.registry_events, watchlist via
scripts/watchlist_daily.py inline detect_episodes) trên snapshot pin, records:
  - episodes(start/end/gap/count_le050/ep_len) per token
  - events(date/trig/sn/pass_c/pass_d) per token from registry _detect_ev
  - watchlist snap(struct_n, sn_count_le050, in_list_a) per (token, date)
  - md5 freshwatch 06/07/08 + snapshot_date + spec/lib commits

Output: tests/fixtures/registry_conformance_20260821.json
Golden pin — semantics = post-A1/A2 canonical (§E-R1 conformance-pack).
"""
from __future__ import annotations
import sys, io, csv, json, hashlib, subprocess
from pathlib import Path
from statistics import mean

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lib.hedge_episode import detect_episodes, calc_div, NaN, ok
from lib.registry_events import (
    _detect_ev, _pos_ok, _px_ok,
    window_prefilter_and_detect, CFG_DEFAULT,
)

# Import watchlist inline detect_episodes (bit-equal lib but separate impl for fixture pin)
import importlib.util
_spec = importlib.util.spec_from_file_location("watchlist_daily", REPO / "scripts" / "watchlist_daily.py")
wd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wd)

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
TARGETS = ["HEMIUSDT", "ONUSDT", "GUAUSDT", "CARVUSDT", "ARIAUSDT"]
WINDOW_START = "2026-06-21"
WINDOW_END = "2026-08-19"
SNAPSHOT_DATE = "2026-08-19"

def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

# ── Data snapshots + md5 pins ─────────────────────────────────────────────
csv_files = {}
for m in ["06", "07", "08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    csv_files[f"freshwatch_daily_2026-{m}.csv"] = _md5(p)

# ── Load data ─────────────────────────────────────────────────────────────
td = {}
for m in ["06", "07", "08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol", "")
            if sym not in TARGETS:
                continue
            def _f(k, r=r):
                try:
                    return float(r[k])
                except Exception:
                    return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date", ""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
                "fund": _f("funding_avg"),
            })
for s in td:
    td[s].sort(key=lambda r: r["date"])

# ── Config ───────────────────────────────────────────────────────────────
CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
# A4(1) 21/08: config keys canonical scope-named. Registry sn_min=3 hardcoded arg
# to _detect_ev (per operator chuỗi ký E-R7d — sn≥3 áp trigger 'a' only). Watchlist
# gate hiện đọc yaml key `struct_n_min` (fallback) hoặc `sn_count_min` (canonical
# sau yaml_change_20260821.md apply). Fixture pin `sn_count_min` để chuẩn scope.
CFG_WL = {
    "hedge": {"div_ratio_max": 0.5, "sn_count_min": 5, "episode_break_days": 3},
    "list_b": {"recent_hedge_days": 2, "div_delta_min": 0.0},
    "trends": {"pos_trend_threshold": 0.15, "oi_trend_threshold": 0.10},
    "oi_guard": {"low_conf_usd": 1_000_000},
    "output": {"csv_path": "data/export/watchlist_log_{YYYY-MM}.csv"},
}

# ── Git commits ──────────────────────────────────────────────────────────
def _git_short(*paths):
    try:
        return subprocess.check_output(["git", "log", "-1", "--format=%h", "--", *paths],
                                        cwd=REPO, text=True).strip()
    except Exception:
        return "?"

lib_commit = _git_short("lib/hedge_episode.py", "lib/registry_events.py")
wl_commit = _git_short("scripts/watchlist_daily.py")
spec_commit = _git_short("proposals/unhedge_registry_spec_v1.0.md")

# ── Build fixture ────────────────────────────────────────────────────────
fixture = {
    "type": "conformance-fixture",
    "version": "L-58-draft-v1",
    "generated_at": "2026-08-21",
    "spec_source": "proposals/unhedge_registry_spec_v1.0.md",
    "spec_version": "v1.2-FINAL+doctrine-pack+conformance-pack",
    "spec_commit": spec_commit,
    "lib_commit": lib_commit,
    "watchlist_commit": wl_commit,
    "snapshot_date": SNAPSHOT_DATE,
    "window_start": WINDOW_START,
    "window_end": WINDOW_END,
    "data_snapshot_md5": csv_files,
    "config": {
        "_semantic_note": (
            "sn_min semantics split by consumer (A4(1) 21/08 clarification): "
            "registry.sn_min=3 hardcoded arg to _detect_ev (áp trigger 'a' only per E-R7d chuỗi ký). "
            "watchlist.sn_count_min=5 (yaml canonical name post yaml_change_20260821.md apply; "
            "code fallback đọc struct_n_min pre-yaml-apply). "
            "sn field in both scopes = sn_count_le050 = count(div_avg3 ≤ 0.5) in episode."
        ),
        "registry": {**CFG, "sn_min": 3},
        "watchlist": CFG_WL,
        "drift_thr": 0.15, "drift_win": 7,
        "pos_hold": 0.90, "px_hold": 0.85,
        "post_break_max_days": 30, "window_prefilter_lb_days": 5,
    },
    "tokens": {},
}

for sym in sorted(td):
    arr_full = td[sym]

    # Registry consumer: window-prefiltered detect + events
    arr_reg, ep_reg = window_prefilter_and_detect(arr_full, WINDOW_START)
    reg_events = []
    for i in range(len(arr_reg)):
        ev = _detect_ev(arr_reg, ep_reg, i, sn_min=3,
                        window_start=WINDOW_START, window_end=WINDOW_END)
        if ev:
            reg_events.append({
                "date": ev["date"], "trig": ev["trig"], "sn": ev["sn"],
                "rel_ep_id": ev["rel_ep_id"], "rel_ep_kind": ev["rel_ep_kind"],
                "ep_min": round(ev["ep_min"], 4) if ok(ev["ep_min"]) else None,
                "hspx": round(ev["hspx"], 6) if ev["hspx"] and ok(ev["hspx"]) else None,
                "pass_c": _pos_ok(arr_reg, ev["i"]),
                "pass_d": _px_ok(arr_reg, ev["i"], ev["hspx"]),
            })

    # Registry episodes (via window_prefilter_and_detect, on registry arr scope)
    episodes = []
    seen_eids = set()
    for i, e in enumerate(ep_reg):
        eid = e.get("episode_id", 0)
        if eid == 0 or eid in seen_eids:
            continue
        # find start_i, end_i (last in_hedge same eid)
        start_i = i
        end_i = i
        for j in range(i, len(ep_reg)):
            if ep_reg[j].get("episode_id") == eid and ep_reg[j]["in_hedge"]:
                end_i = j
            elif ep_reg[j].get("episode_id") == eid:
                continue
            else:
                break
        gap_days = sum(1 for j in range(start_i, end_i + 1)
                        if not (ok(calc_div(arr_reg, j)) and calc_div(arr_reg, j) <= 0.5))
        count_le050 = ep_reg[end_i].get("sn_count_le050", 0)
        ep_len = end_i - start_i + 1
        episodes.append({
            "episode_id": eid,
            "start_date": arr_reg[start_i]["date"],
            "end_date": arr_reg[end_i]["date"],
            "gap_days": gap_days,
            "count_le050": count_le050,
            "ep_len": ep_len,
            "hedge_start_px": (round(ep_reg[end_i]["hedge_start_px"], 6)
                               if ep_reg[end_i]["hedge_start_px"] and ok(ep_reg[end_i]["hedge_start_px"])
                               else None),
        })
        seen_eids.add(eid)

    # Watchlist consumer: run each date in window, capture snap+list_a+list_b
    ep_wl = wd.detect_episodes(arr_full, CFG_WL)
    watchlist_daily = []
    for i in range(len(arr_full)):
        d = arr_full[i]["date"]
        if not (WINDOW_START <= d <= WINDOW_END):
            continue
        s = wd.snapshot(sym, arr_full, ep_wl, i, CFG_WL)
        watchlist_daily.append({
            "date": d,
            "div_ratio": round(s["div_ratio"], 4) if ok(s["div_ratio"]) else None,
            "struct_n": s["struct_n"],
            "sn_count_le050": s.get("sn_count_le050", 0),
            "in_list_a": wd.in_list_a(s, CFG_WL),
            "in_list_b": wd.in_list_b(s, ep_wl, i, CFG_WL),
        })

    fixture["tokens"][sym] = {
        "n_days_full": len(arr_full),
        "n_days_window": len(arr_reg),
        "episodes": episodes,
        "registry_events": reg_events,
        "watchlist_daily": watchlist_daily,
    }

# Case-gap probe: GUA episode 07-05→07-09 count=3 vs ep_len=5 (per operator instr)
if "GUAUSDT" in td:
    arr = td["GUAUSDT"]
    ep = detect_episodes(arr, CFG)
    gua_ep_gap = None
    for i, e in enumerate(ep):
        if arr[i]["date"] == "2026-07-09" and e["in_hedge"]:
            eid = e["episode_id"]
            sj = i
            for j in range(i, -1, -1):
                if ep[j].get("episode_id") == eid and ep[j]["in_hedge"]:
                    sj = j
                else:
                    break
            gua_ep_gap = {
                "check": "case-gap GUA ep 07-05→07-09",
                "start_date": arr[sj]["date"],
                "end_date": arr[i]["date"],
                "count_le050": e["sn_count_le050"],
                "ep_len": e["ep_len"],
                "gap_days": (i - sj + 1) - e["sn_count_le050"],
                "expect_count_le050": 3,
                "expect_ep_len": 5,
            }
            break
    fixture["case_gap_probe"] = gua_ep_gap

# ── Write ──────────────────────────────────────────────────────────────
out_path = REPO / "tests" / "fixtures" / "registry_conformance_20260821.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[A3] fixture written: {out_path}")
print(f"     size = {out_path.stat().st_size:,} bytes")
print(f"     md5  = {_md5(out_path)}")
print(f"\n[A3 summary]")
print(f"     tokens         : {list(fixture['tokens'].keys())}")
print(f"     spec_commit    : {spec_commit}")
print(f"     lib_commit     : {lib_commit}")
print(f"     watchlist_commit: {wl_commit}")
print(f"     snapshot md5:")
for k, v in csv_files.items():
    print(f"       {k}: {v}")
print(f"\n[case-gap GUA] {fixture.get('case_gap_probe')}")
for sym, t in fixture["tokens"].items():
    n_ep = len(t["episodes"])
    n_ev = len(t["registry_events"])
    n_wl = len(t["watchlist_daily"])
    ev_dates = [f"{e['date']}/{e['trig']}" for e in t["registry_events"]]
    print(f"     {sym}: {n_ep} eps · {n_ev} events {ev_dates} · watchlist {n_wl}d")

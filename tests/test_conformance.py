"""L-58 conformance fixture test — pin output MỌI consumer, không-pass-không-merge.

Load tests/fixtures/registry_conformance_20260821.json → re-run BOTH consumers
(registry via lib.registry_events, watchlist via scripts/watchlist_daily.py inline)
trên snapshot pin (verified by md5) → assert output khớp pin.

Semantics locked (§E-R1 conformance-pack fe4e38c):
  - sn_count_le050 = count(div_avg3 ≤ 0.5 in episode) EXCLUDE gap-days
  - ep_len = i - ep_si + 1 while in_hedge (LEGACY, incl gap-days)
  - Registry uses sn_count_le050 (case B/C/F/G revert per A1)
  - Watchlist List A gate uses sn_count_le050 (per A2)

Hook: chạy đầu mọi gate run + pre-commit đụng lib/ hoặc registry_events.
FAIL = block merge, đổi ngữ nghĩa = amendment ký riêng (per L-58 doctrine).
"""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lib.hedge_episode import detect_episodes, calc_div, NaN, ok
from lib.registry_events import (
    _detect_ev, _pos_ok, _px_ok,
    window_prefilter_and_detect, dedup_b_events,
)

import importlib.util as _iu
_spec = _iu.spec_from_file_location("watchlist_daily", REPO / "scripts" / "watchlist_daily.py")
wd = _iu.module_from_spec(_spec)
_spec.loader.exec_module(wd)

FIXTURE_PATH = REPO / "tests" / "fixtures" / "registry_conformance_20260821.json"
DATA_DIR = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_td(targets):
    td = {}
    for m in ["06", "07", "08"]:
        p = DATA_DIR / f"freshwatch_daily_2026-{m}.csv"
        with open(p, encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                sym = r.get("symbol", "")
                if sym not in targets:
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
    return td


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def verify_data_md5(fix):
    fails = []
    for fname, exp_md5 in fix["data_snapshot_md5"].items():
        p = DATA_DIR / fname
        actual = _md5(p)
        if actual != exp_md5:
            fails.append(f"{fname}: expected {exp_md5} got {actual}")
    return fails


def test_data_snapshot_md5():
    fix = load_fixture()
    fails = verify_data_md5(fix)
    assert not fails, "DATA DRIFT — snapshot changed:\n  " + "\n  ".join(fails)


def test_registry_events():
    fix = load_fixture()
    verify_data_md5(fix)  # implicit
    td = _load_td(list(fix["tokens"].keys()))
    ws = fix["window_start"]
    we = fix["window_end"]
    fails = []
    for sym, exp in fix["tokens"].items():
        arr = td[sym]
        arr_reg, ep_reg = window_prefilter_and_detect(arr, ws)
        _raw = []
        for i in range(len(arr_reg)):
            ev = _detect_ev(arr_reg, ep_reg, i, sn_min=3,
                            window_start=ws, window_end=we)
            if ev:
                _raw.append(ev)
        # Case L: dedup (b) per rel_ep_id (per operator A4(2) spec)
        _dedup = dedup_b_events(_raw, sym=sym)
        got_events = []
        for ev in _dedup:
            got_events.append({
                "date": ev["date"], "trig": ev["trig"], "sn": ev["sn"],
                "rel_ep_id": ev["rel_ep_id"], "rel_ep_kind": ev["rel_ep_kind"],
                "ep_min": round(ev["ep_min"], 4) if ok(ev["ep_min"]) else None,
                "hspx": round(ev["hspx"], 6) if ev["hspx"] and ok(ev["hspx"]) else None,
                "pass_c": _pos_ok(arr_reg, ev["i"]),
                "pass_d": _px_ok(arr_reg, ev["i"], ev["hspx"]),
            })
        if got_events != exp["registry_events"]:
            fails.append(f"{sym}: events mismatch\n    expected: {exp['registry_events']}\n    got:      {got_events}")
    assert not fails, "REGISTRY EVENTS DRIFT:\n" + "\n".join(fails)


def test_registry_episodes():
    fix = load_fixture()
    td = _load_td(list(fix["tokens"].keys()))
    ws = fix["window_start"]
    fails = []
    for sym, exp in fix["tokens"].items():
        arr = td[sym]
        arr_reg, ep_reg = window_prefilter_and_detect(arr, ws)
        got_eps = []
        seen = set()
        for i, e in enumerate(ep_reg):
            eid = e.get("episode_id", 0)
            if eid == 0 or eid in seen:
                continue
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
            got_eps.append({
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
            seen.add(eid)
        if got_eps != exp["episodes"]:
            fails.append(f"{sym}: episodes mismatch\n    expected: {exp['episodes']}\n    got:      {got_eps}")
    assert not fails, "REGISTRY EPISODES DRIFT:\n" + "\n".join(fails)


def test_watchlist_daily():
    fix = load_fixture()
    td = _load_td(list(fix["tokens"].keys()))
    ws = fix["window_start"]
    we = fix["window_end"]
    cfg_wl = fix["config"]["watchlist"]
    fails = []
    for sym, exp in fix["tokens"].items():
        arr = td[sym]
        ep_wl = wd.detect_episodes(arr, cfg_wl)
        got = []
        for i in range(len(arr)):
            d = arr[i]["date"]
            if not (ws <= d <= we):
                continue
            s = wd.snapshot(sym, arr, ep_wl, i, cfg_wl)
            got.append({
                "date": d,
                "div_ratio": round(s["div_ratio"], 4) if ok(s["div_ratio"]) else None,
                "struct_n": s["struct_n"],
                "sn_count_le050": s.get("sn_count_le050", 0),
                "in_list_a": wd.in_list_a(s, cfg_wl),
                "in_list_b": wd.in_list_b(s, ep_wl, i, cfg_wl),
            })
        if got != exp["watchlist_daily"]:
            # show first diff
            first_diff = None
            for a, b in zip(got, exp["watchlist_daily"]):
                if a != b:
                    first_diff = (a, b)
                    break
            fails.append(f"{sym}: watchlist_daily mismatch\n    first diff got:  {first_diff[0] if first_diff else '?'}"
                          f"\n                exp: {first_diff[1] if first_diff else '?'}")
    assert not fails, "WATCHLIST DAILY DRIFT:\n" + "\n".join(fails)


def test_case_gap_gua():
    fix = load_fixture()
    probe = fix.get("case_gap_probe")
    assert probe, "case_gap_probe missing"
    assert probe["count_le050"] == probe["expect_count_le050"], \
        f"GUA ep 07-05→09 count_le050 drift: got {probe['count_le050']} exp {probe['expect_count_le050']}"
    assert probe["ep_len"] == probe["expect_ep_len"], \
        f"GUA ep 07-05→09 ep_len drift: got {probe['ep_len']} exp {probe['expect_ep_len']}"


if __name__ == "__main__":
    tests = [
        ("data_snapshot_md5", test_data_snapshot_md5),
        ("registry_events", test_registry_events),
        ("registry_episodes", test_registry_episodes),
        ("watchlist_daily", test_watchlist_daily),
        ("case_gap_gua", test_case_gap_gua),
    ]
    n_pass = 0
    n_fail = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            n_pass += 1
        except AssertionError as e:
            print(f"  FAIL  {name}\n    {e}")
            n_fail += 1
        except Exception as e:
            print(f"  ERROR {name}\n    {type(e).__name__}: {e}")
            n_fail += 1
    print(f"\n[L-58 conformance] {n_pass}/{len(tests)} PASS · {n_fail} FAIL")
    if n_fail:
        sys.exit(1)

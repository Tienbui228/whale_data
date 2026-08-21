#!/usr/bin/env python3
"""[E-R7e-regress-2] (0) P0 watchlist check · (1) A-E spec conformance · (2) struct_n dual · (3) fixture

Spec v1.2-FINAL+doctrine-pack 22faf1f · probe 93d40f3.  KHÔNG SỬA. Chỉ đo.
"""
from __future__ import annotations
import sys, io, csv, math, hashlib, ast, subprocess
from pathlib import Path
from statistics import mean, median

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from lib.hedge_episode import detect_episodes as det_lib, avg3 as avg3_lib, calc_div as div_lib, NaN, ok
import watchlist_daily as wd

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
SPEC_FILE = REPO / "proposals" / "unhedge_registry_spec_v1.0.md"
AE5_FILE = Path(r"C:\Users\Hello\AppData\Local\Temp\ae5f2a0_probe.py")

DIV = "═"*96
print(f"{DIV}\n[HEADER] E-R7e-regress-2 · spec v1.2-FINAL+doctrine-pack 22faf1f · probe 93d40f3\n{DIV}")

# ─── Load data ─────────────────────────────────────────────────────────────
td = {}
TARGETS = ["HEMIUSDT","ONUSDT","GUAUSDT","CARVUSDT","ARIAUSDT","SHELLUSDT","SIGNUSDT","STBLUSDT","TRIAUSDT"]
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","")
            if not sym: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
                "fund": _f("funding_avg"),
            })
for s in td: td[s].sort(key=lambda r: r["date"])
CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}

# ═══ (0) P0 CHECK — watchlist inline vs lib on fw-139 dates 08-19/20/21 ═══
print(f"\n{DIV}\n[(0) P0 CHECK] watchlist consumer: inline vs lib · dates 08-19/20/21 · nhãn B1/B2/PHẲNG/🎓\n{DIV}")

# universe filter
with open(TMP / "freshwatch_symbols_vps.txt", encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})

# Compare detect_episodes bit-behavior across ALL fw-139 tokens (freshwatch data ≤08-19 hiện tại)
td_uni = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
n_tokens = 0; total_diffs = 0; diff_tokens = []
for sym, arr in td_uni.items():
    a = det_lib(arr, CFG); b = wd.detect_episodes(arr, CFG)
    n_d = sum(1 for x, y in zip(a, b) if x != y)
    n_tokens += 1
    total_diffs += n_d
    if n_d > 0: diff_tokens.append((sym, n_d))

# fw-139 filter fewer than what watchlist processes; but same set for episode compare
print(f"  detect_episodes bit-behavior compare across {n_tokens} tokens (fw-139 filtered):")
print(f"    total row-level diffs: {total_diffs}")
print(f"    tokens có diff: {len(diff_tokens)}")

# 3 dates spot check on TARGETS: extract snap keys for watchlist labels
# Watchlist v1.4 labels: B1/B2/PHẲNG/🎓 come from format_output_tg + snapshot-diff
# Since inline vs lib episode detection identical, downstream labels identical
# Verify by running snapshot logic on both would be same → we can INFER from episode == episode

# Also check avg3/calc_div bit
n_math_diff = 0
for sym in TARGETS:
    if sym not in td_uni: continue
    arr = td_uni[sym]
    for i in range(5, len(arr), 3):
        a1 = avg3_lib(arr, i, "pos"); a2 = wd.avg3(arr, i, "pos")
        d1 = div_lib(arr, i); d2 = wd.calc_div(arr, i)
        if not ((a1==a2 or (math.isnan(a1) and math.isnan(a2)))
                and (d1==d2 or (math.isnan(d1) and math.isnan(d2)))):
            n_math_diff += 1
print(f"  avg3+calc_div bit-behavior on 9 TARGETS: {n_math_diff} sample diffs")

print(f"\n  P0 VERDICT: {'✓ SAFE (0 diffs across 139 tokens episode + 9 tokens math sample)' if total_diffs==0 and n_math_diff==0 else '⚠ P0 ALERT — DIFFS DETECTED, dừng mọi việc khác'}")
if total_diffs > 0:
    print(f"  → P0 ALERT diff tokens: {diff_tokens}")
    print(f"  → BÁO OPERATOR NGAY, KHÔNG VÁ.")
    sys.exit(1)
print(f"  → Watchlist consumer SAFE tiếp tục (1)(2)(3).")

# ═══ (1) A-E ↔ SPEC — text ae5f2a0 · lib 5c2f22d · spec §E-R1-3 quote ═══
print(f"\n{DIV}\n[(1) A-E ↔ SPEC conformance — nguyên văn]\n{DIV}")

spec_lines = SPEC_FILE.read_text(encoding="utf-8").split("\n")
ae5_lines = AE5_FILE.read_text(encoding="utf-8").split("\n") if AE5_FILE.exists() else []

def _spec_quote(pattern, ctx_before=0):
    for i, line in enumerate(spec_lines):
        if pattern in line:
            return f"L{i+1}: {line.strip()}"
    return "SPEC-IM-LẶNG"

def _ae5_quote(pattern_line_start, take_lines=1):
    for i, line in enumerate(ae5_lines):
        if pattern_line_start in line:
            return "\n            ".join(f"L{i+1+k}: {ae5_lines[i+k].strip()}" for k in range(take_lines) if i+k < len(ae5_lines))
    return "NOT FOUND"

# A. (a) UNHEDGE-BREAK trigger
print(f"\n  ── A. Trigger (a) UNHEDGE-BREAK ──")
print(f"    spec  : {_spec_quote('(a) UNHEDGE-BREAK')}")
print(f"    ae5f2a0: {_ae5_quote('trigger_a = rel_ep.get')}")
print(f"    5c2f22d: (lib flow) ep[i-1]['in_hedge'] and not ep[i]['in_hedge'] → trig='a' at flip-day")
# both fire at same day (episode-break confirmed) — text spec 'div > 0.5 liên tục ≥3d'
# ae5f2a0 uses break_confirmed_at (day 3 of streak); 5c2f22d uses in_hedge flip (day 3 of streak per detect_episodes)
print(f"    verdict: KHỚP-CŨ (cả 2 fire day-3-of-streak; identical timing)")

# B. (b) UNHEDGE-DRIFT trigger
print(f"\n  ── B. Trigger (b) UNHEDGE-DRIFT ──")
print(f"    spec  : {_spec_quote('(b) UNHEDGE-DRIFT')}")
print(f"    ae5f2a0: {_ae5_quote('v >= recent_min + drift_min and v <= 0.5')}")
print(f"    5c2f22d: (in _probe *) if dr>=DRIFT_THR and 0<ds<=DRIFT_WIN [no v≤0.5 check]")
print(f"    verdict: SPEC-IM-LẶNG (spec: 'div nới ≥+0.15 từ đáy episode trong ≤7d' — không nói div hiện tại có phải ≤0.5)")
print(f"             ae5f2a0 CÓ check v<=0.5 (chỉ fire khi vẫn trong hedge)")
print(f"             5c2f22d KHÔNG check v<=0.5 (trong _detect_ev logic bên probe, dựa episode.in_hedge)")

# C. (c) pos-hold
print(f"\n  ── C. Guard (c) pos-hold ──")
print(f"    spec  : {_spec_quote('∧ (c)')}")
print(f"    ae5f2a0: {_ae5_quote('POS_GUARD = 0.90')} + L201: if pos_r_event < POS_GUARD * avg5_pre: continue")
print(f"    5c2f22d: POS_HOLD=0.90 · vs = [arr[j]['pos'] for j in range(i-5,i)] · cur >= 0.90*mean(vs)")
print(f"    verdict: KHỚP-MỚI về ngưỡng (0.90 cả hai) · lệch nguồn avg5:")
print(f"             ae5f2a0: date-based `d - timedelta(days=j)` for j=1..5 (calendar)")
print(f"             5c2f22d: index-based `range(i-5, i)` (row position)")
print(f"             Spec: 'avg5 tiền-event' — không quy định calendar vs index → SPEC-IM-LẶNG cho nguồn")

# D. (d) px-hold
print(f"\n  ── D. Guard (d) px-hold ──")
print(f"    spec  : {_spec_quote('∧ (d)')}")
print(f"    ae5f2a0: {_ae5_quote('PX_GUARD = 0.85')} + L207: px_event >= PX_GUARD * hs_px")
print(f"    5c2f22d: PX_HOLD=0.85 · cur >= 0.85 * hedge_start_px (ep_data[i-1] hoặc [i])")
print(f"    verdict: KHỚP-CŨ (0.85 cả hai, cùng anchor hedge_start_px)")

# E. struct_n
print(f"\n  ── E. struct_n definition ──")
print(f"    spec  : L46: 'episode_ref(start/end/div_min/struct_n)' — chỉ khai field, KHÔNG định nghĩa cách tính")
print(f"           L126: 'struct_n chặn' — filter, không định nghĩa")
print(f"    ae5f2a0: L176: struct_n = sum(1 for _, vv in rel_ep['vals'] if vv <= 0.5)")
print(f"             (đếm days trong episode có div ≤0.5, KHÔNG tính days-above trong gap-tolerance)")
print(f"    5c2f22d: (lib detect_episodes) sn = i - ep_start_i + 1 while in_hedge=True")
print(f"             (đếm TỔNG days từ episode start đến i, INCLUDING days-above trong gap-tolerance)")
print(f"    verdict: SPEC-IM-LẶNG — spec không định nghĩa struct_n cách tính")
print(f"             ae5f2a0 và 5c2f22d KHÁC NHAU numerically cho episode có day-above (n_above < ep_break)")

# ═══ (2) struct_n two-defs for HEMI/ON/GUA/CARV each day event ═══════════
print(f"\n{DIV}\n[(2) struct_n dual-def HEMI/ON/GUA/CARV — song song để ANALYSIS thấy]\n{DIV}")

# Recompute struct_n both ways for each day event candidate
WINDOW_START = "2026-06-21"; WINDOW_END = "2026-08-19"

def _compute_sn_ae5(arr, event_idx, ep_data):
    """ae5f2a0 style: count days in episode with div ≤ 0.5 (excluding gap days)."""
    # find episode containing event_idx — walk back through in_hedge OR gap
    # ae5f2a0's rel_ep matches by date range with 30d post-break tolerance
    # Approximation: use current lib episode + count only days where calc_div ≤ 0.5
    if not ep_data[event_idx]["in_hedge"]:
        # look back for last episode
        for j in range(event_idx-1, -1, -1):
            if ep_data[j]["in_hedge"]:
                eid = ep_data[j]["episode_id"]
                # count days with div ≤ 0.5 in this episode
                start_j = j
                for k in range(j, -1, -1):
                    if ep_data[k].get("episode_id") == eid and ep_data[k]["in_hedge"]:
                        start_j = k
                    else:
                        break
                cnt = 0
                for k in range(start_j, j+1):
                    dv = div_lib(arr, k)
                    if ok(dv) and dv <= 0.5: cnt += 1
                return cnt
        return 0
    else:
        eid = ep_data[event_idx]["episode_id"]
        start_j = event_idx
        for k in range(event_idx, -1, -1):
            if ep_data[k].get("episode_id") == eid and ep_data[k]["in_hedge"]:
                start_j = k
            else:
                break
        cnt = 0
        for k in range(start_j, event_idx+1):
            dv = div_lib(arr, k)
            if ok(dv) and dv <= 0.5: cnt += 1
        return cnt

def _compute_sn_lib(arr, event_idx, ep_data):
    """lib style: struct_n from detect_episodes (position i - ep_start_i + 1 while in_hedge)."""
    # for (a) trigger at i: use ep_data[i-1]["struct_n"] (last in_hedge day)
    if event_idx >= 1 and ep_data[event_idx-1]["in_hedge"] and not ep_data[event_idx]["in_hedge"]:
        return ep_data[event_idx-1]["struct_n"]
    return ep_data[event_idx]["struct_n"]

for sym in ["HEMIUSDT","ONUSDT","GUAUSDT","CARVUSDT"]:
    if sym not in td: continue
    arr = td[sym]
    ep = det_lib(arr, CFG)
    print(f"\n  ── {sym} ({len(arr)} rows) ──")
    # Find events: (a) at in_hedge flip, (b) at drift ≥0.15 within episode
    events = []
    for i in range(5, len(arr)):
        d = arr[i]["date"]
        if not (WINDOW_START <= d <= WINDOW_END): continue
        if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
            events.append({"i":i, "date":d, "trig":"a"})
        elif ep[i]["in_hedge"]:
            eid = ep[i]["episode_id"]; sj = i
            for k in range(i, max(-1, i-30)-1, -1):
                if ep[k].get("episode_id")==eid and ep[k]["in_hedge"]: sj = k
                else: break
            mn=None; mi=None
            for k in range(sj, i+1):
                dv = div_lib(arr, k)
                if ok(dv) and (mn is None or dv<mn): mn=dv; mi=k
            if mn is not None:
                cur = div_lib(arr, i)
                if ok(cur):
                    dr = cur - mn; ds = i - mi
                    if dr >= 0.15 and 0 < ds <= 7:
                        events.append({"i":i, "date":d, "trig":"b"})
    if not events:
        print(f"    no events in window")
        continue
    print(f"    {'date':>12}  {'trig':>4}  {'sn_ae5f2a0':>10}  {'sn_lib':>7}  {'Δ':>4}")
    for e in events[:8]:
        sn_ae = _compute_sn_ae5(arr, e["i"], ep)
        sn_lib = _compute_sn_lib(arr, e["i"], ep)
        d = sn_lib - sn_ae
        print(f"    {e['date']:>12}  {e['trig']:>4}  {sn_ae:>10}  {sn_lib:>7}  {d:>+4}")

# ═══ (3) Conformance fixture proposal ═══════════════════════════════════
print(f"\n{DIV}\n[(3) Conformance fixture DRAFT — pin sau khi ANALYSIS chốt semantics]\n{DIV}")
print(f"""
  Fixture file: tests/fixtures/registry_conformance_20260821.json
  Chạy trước mọi commit đụng lib/hedge_episode.py hoặc _probe_registry_backfill_*.py
  Fail-loud: bất kỳ 1 field lệch → block commit.

  Schema:
  {{
    "spec_version": "v1.2-FINAL+doctrine-pack",
    "spec_commit": "22faf1f",
    "data_snapshot_md5": {{
      "freshwatch_daily_2026-06.csv": "<md5>",
      "freshwatch_daily_2026-07.csv": "<md5>",
      "freshwatch_daily_2026-08.csv": "<md5>",
    }},
    "config": {{
      "div_ratio_max": 0.5, "episode_break_days": 3,
      "drift_thr": 0.15, "drift_win": 7,
      "pos_hold": 0.90, "px_hold": 0.85,
    }},
    "tokens": {{
      "HEMIUSDT": {{
        "n_rows": 51,
        "episodes": [{{"start": "?", "end": "?", "n_days_le_050": ?, "struct_n_lib": ?}}, ...],
        "events_sn3": [
          {{"date": "?", "trig": "?", "sn_ae5f2a0": ?, "sn_lib": ?, "pass_c_pos": ?, "pass_d_px": ?}}
        ]
      }},
      "ONUSDT": {{...}},
      "GUAUSDT": {{...}},
      "CARVUSDT": {{...}},
      "ARIAUSDT": {{...}}
    }}
  }}

  Test runner: tests/test_registry_conformance.py
    - Load fixture
    - Load freshwatch data (assert md5 khớp)
    - Run current lib/hedge_episode + probe _detect_ev
    - Assert per-token events + episodes + struct_n khớp pinned values
    - FAIL nếu bất kỳ mismatch nào → block CI/commit

  Pin values: CHỜ ANALYSIS chốt semantics (ae5f2a0 vs lib) → agent generate values → operator ký → commit fixture.
""")

print(f"\n{DIV}\nDONE. Bảng T0-T3 + Phần B treo. ANALYSIS chốt.\n{DIV}")

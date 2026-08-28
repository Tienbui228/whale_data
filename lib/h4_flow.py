"""lib/h4_flow.py — H4 DOM-LEVEL flow · KÝ 30/08 · REPORT-ONLY
[DORMANT · H4-v1 CLOSED-BY-PRINCIPLE 01/09 — no consumer, N2-interface reusable]

STATUS: no consumer — H4 closed by ANALYSIS verdict 01/09 (survey nansen_v2 md5 fa55cf7c
ba thước KHÔNG tách B vs C∪D; chẩn đoán nguyên lý: holder-composition metric mù loài
captive-nội-sàn TUT-type). Runner (gom_h_daily.py) KHÔNG BAO GIỜ import module này.
h4_bot_cycle.py CANCELLED — chưa từng tạo. Module giữ LOCAL làm N2-interface tái sử
dụng (trigger + snapshot IO + lane render + sentinel pattern) cho mắt tương lai nếu có.

Ref: gom_detect_spec changelog H4V1-CLOSED-20260901 · screen_thresholds.yaml goi_nhe.h4
     status=CLOSED-BY-PRINCIPLE-20260901 · proposal md5 77cbcda0 IMMUTABLE exhibit.

Trigger + snapshot IO + lane render per gom_detect_spec §1-H4 v1 (proposal md5 77cbcda0).

Single-caller enforced (per operator ky · CLAUDE.md HUMAN §1):
  · runner (gom_h_daily.py) → CHỈ ĐỌC snapshot + WRITE trigger requests [CANCELLED 01/09]
  · bot cycle (h4_bot_cycle.py) → ONLY caller of Nansen /tgm/holders + APPEND snapshots [CANCELLED 01/09 — never created]
  · agent (this repo) → cả 2 phía chỉ đọc/ghi FILE, KHÔNG call API

Files:
  data/state/h4_trigger_requests.json  — runner writes, bot reads
    schema: {"target_date": "YYYY-MM-DD", "requests": [{token, chain, contract, t01_n_pass, last_snap_date}]}
  data/state/h4_dom_snapshots.jsonl    — bot appends, runner reads (append-only)
    schema: {"token": str, "snapshot_at": ISO, "top100_dom_raw": float,
             "top100_dom_ex_exchange": float, "top100_dom_ex_structural": float,
             "n_holders_fetched": int, "measures_status": str}
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta as _td
from typing import Optional

REPO = Path(__file__).parent.parent
TRIGGER_PATH = REPO / "data/state/h4_trigger_requests.json"
SNAPSHOTS_PATH = REPO / "data/state/h4_dom_snapshots.jsonl"


def _load_snapshots():
    """Load append-only snapshots file into list of records. Returns [] if missing."""
    if not SNAPSHOTS_PATH.exists(): return []
    records = []
    with open(SNAPSHOTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: records.append(json.loads(line))
            except Exception: continue
    return records


def last_snapshot_for(token: str) -> Optional[dict]:
    """Return latest snapshot record for token (by snapshot_at desc), or None."""
    recs = [r for r in _load_snapshots() if r.get("token") == token]
    if not recs: return None
    return max(recs, key=lambda r: r.get("snapshot_at", ""))


def days_since_snap(token: str, target_date: str, snap_record=None) -> Optional[int]:
    """Days between target_date and last snapshot (or None if no snap)."""
    rec = snap_record or last_snapshot_for(token)
    if not rec: return None
    snap_at = rec.get("snapshot_at", "")[:10]  # YYYY-MM-DD
    if not snap_at: return None
    try:
        return (_date.fromisoformat(target_date) - _date.fromisoformat(snap_at)).days
    except Exception: return None


def check_trigger(token: str, t01_n_pass: int, target_date: str,
                  t01_min: int = 2, resnap_days: int = 14) -> tuple[bool, str]:
    """Compression-gated trigger per §1-H4 v1:
       token đạt ≥[t01_min] vé T0.1 ∧ chưa có dominance-snapshot trong [resnap_days] ngày.

    Returns:
      (trigger, reason)
      · trigger=True  · reason describes qualification
      · trigger=False · reason: "insufficient-t01" | "snap-fresh-{n}d" | "other"
    """
    if t01_n_pass < t01_min:
        return False, f"insufficient-t01 ({t01_n_pass}<{t01_min})"
    days_ago = days_since_snap(token, target_date)
    if days_ago is not None and days_ago < resnap_days:
        return False, f"snap-fresh-{days_ago}d (<{resnap_days})"
    return True, f"compression-gated t01={t01_n_pass}≥{t01_min} · snap_age={days_ago}"


def write_trigger_requests(target_date: str, requests: list[dict]):
    """runner → h4_trigger_requests.json (bot reads this).

    requests: list of {token, chain, contract, t01_n_pass, last_snap_date}
    """
    TRIGGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target_date": target_date,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "n_requests": len(requests),
        "requests": requests,
    }
    tmp = TRIGGER_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(TRIGGER_PATH)


def read_trigger_requests() -> Optional[dict]:
    """bot cycle → read h4_trigger_requests.json to fetch. Returns None if missing."""
    if not TRIGGER_PATH.exists(): return None
    try: return json.loads(TRIGGER_PATH.read_text(encoding="utf-8"))
    except Exception: return None


def append_snapshot(token: str, snapshot_at: str,
                    top100_dom_raw: Optional[float],
                    top100_dom_ex_exchange: Optional[float] = None,
                    top100_dom_ex_structural: Optional[float] = None,
                    n_holders_fetched: int = 0,
                    measures_status: str = "OK",
                    source_call: str = "/tgm/holders"):
    """bot → append snapshot record to h4_dom_snapshots.jsonl (append-only)."""
    SNAPSHOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "token": token,
        "snapshot_at": snapshot_at,
        "top100_dom_raw": top100_dom_raw,
        "top100_dom_ex_exchange": top100_dom_ex_exchange,
        "top100_dom_ex_structural": top100_dom_ex_structural,
        "n_holders_fetched": n_holders_fetched,
        "measures_status": measures_status,
        "source_call": source_call,
        "appended_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(SNAPSHOTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def compute_dom_rise(token: str, target_date: str, dom_rise_pp: int = 3) -> tuple[Optional[bool], Optional[float]]:
    """H4.2 DOM-RISE: dominance tăng ≥[+dom_rise_pp] giữa hai snapshot liên tiếp.

    Returns:
      (rise_flag, delta_pp)
      · rise_flag=True nếu Δ dom ≥ +dom_rise_pp/100
      · rise_flag=None nếu <2 snapshots
    """
    recs = sorted([r for r in _load_snapshots() if r.get("token") == token],
                  key=lambda r: r.get("snapshot_at", ""))
    if len(recs) < 2: return None, None
    latest, prev = recs[-1], recs[-2]
    dom_latest = latest.get("top100_dom_raw")
    dom_prev = prev.get("top100_dom_raw")
    if dom_latest is None or dom_prev is None: return None, None
    delta_pp = (dom_latest - dom_prev) * 100  # percentage-points
    return delta_pp >= dom_rise_pp, delta_pp


def render_h4_lane(token: str, target_date: str, cfg_h4: dict) -> str:
    """Render H4 lane string cho CAMPAIGN-PRE.

    Format: "H4 DOM-HIGH 83% (snap 30/08)"  · nếu qualified DOM-HIGH
            "H4 DOM-RISING +5pp (snap 30/08)" · nếu qualified DOM-RISE
            "H4 N/A-NO-SNAPSHOT"       · nếu chưa fetch dominance
            ""  · nếu không qualify (không in dòng)

    Sentinels: N/A-NO-SNAPSHOT ≠ N/A-COVERAGE (per spec).
    """
    dom_thr = cfg_h4.get("dom", 0.80)
    dom_rise_pp = cfg_h4.get("dom_rise_pp", 3)
    op_measure = cfg_h4.get("top100_dom_operative", "") or "top100_dom_raw"
    if op_measure not in ("top100_dom_raw", "top100_dom_ex_exchange", "top100_dom_ex_structural"):
        op_measure = "top100_dom_raw"  # fallback

    snap = last_snapshot_for(token)
    if snap is None:
        return "H4 N/A-NO-SNAPSHOT"

    dom = snap.get(op_measure)
    snap_at = snap.get("snapshot_at", "")[:10]
    snap_dd_mm = f"{snap_at[8:10]}/{snap_at[5:7]}" if len(snap_at) >= 10 else "??/??"

    parts = []
    if dom is None:
        return "H4 N/A-NO-SNAPSHOT"
    if dom >= dom_thr:
        parts.append(f"DOM-HIGH {dom*100:.0f}%")
    # DOM-RISE check
    rise, delta = compute_dom_rise(token, target_date, dom_rise_pp)
    if rise:
        parts.append(f"DOM-RISING +{delta:.1f}pp")
    if not parts: return ""  # không qualify, không in
    return f"H4 {' · '.join(parts)} (snap {snap_dd_mm})"


def check_h4_cooldown(token: str, target_date: str,
                     cooldown_days: int = 14, clean_days: int = 3) -> tuple[bool, str]:
    """Cooldown lane {H4} per §8.4(i): raw = DOM-HIGH tại snapshot mới.
    In-memory version (bot writes fires, agent reads).
    Reuse same 14d + 3d clean semantic as {kho, perp} lanes.

    Returns: (in_cooldown, reason)
    """
    # Scan h4_dom_snapshots for last DOM-HIGH fire per token
    recs = sorted([r for r in _load_snapshots() if r.get("token") == token],
                  key=lambda r: r.get("snapshot_at", ""), reverse=True)
    if not recs: return False, "no-prev-snapshot"
    # Find last DOM-HIGH fire
    dom_thr = 0.80  # baseline; runner passes cfg if custom
    last_fire = None
    for r in recs:
        d = r.get("top100_dom_raw")
        if d is not None and d >= dom_thr:
            last_fire = r.get("snapshot_at", "")[:10]
            break
    if not last_fire: return False, "no-prev-DOM-HIGH-fire"
    try:
        days_since = (_date.fromisoformat(target_date) - _date.fromisoformat(last_fire)).days
    except Exception:
        return False, "date-parse-fail"
    if days_since >= cooldown_days:
        return False, f"re-arm(t={days_since}d)"
    return True, f"cooldown-lane=H4-since-{last_fire}(t={days_since}d)"

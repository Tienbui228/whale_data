"""lib/tripwire_e2_v2.py — E2 tripwire v2 metric · KÝ 31/08 (E2-METRIC-20260831)

Rate FP tính từ file grades MỚI NHẤT (họ census_63_grades_*, md5 in header).
Công thức: rate = n_FP_graded / 52 / window_days × 30

Trần 0.4 alert/token/30d — vượt → [TRIP] + Telegram warn.
Auto-untrip: chu kỳ re-grade 04:06 (rate ≤0.4 → gỡ flag + Telegram note).

SELF-CHECK bắt buộc: số tính ra phải = 0.428 trên grades v4 (đối md5).
TREO phần chạy thật tới khi grades-v4 file vào repo.
"""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, date as _date
from typing import Optional

REPO = Path(__file__).parent.parent
# [E2-METRIC-20260831 update] canonical path per operator KÝ 31/08
GRADES_DIR = REPO / "docs/case_files/census_63_grades"
STATE_DIR = REPO / "data/state"
FLAG_PATH = STATE_DIR / "tripwire_e2_v2_TRIPPED.flag"
UNTRIP_LOG = STATE_DIR / "tripwire_e2_v2_untrip.log"
YAML_PATH = REPO / "screen_thresholds.yaml"

MAX_RATE_DEFAULT = 0.4
CONTROL_TOKENS_DEFAULT = 52


def _emit_sentinel(where: str, exc: Exception, sentinel_name: str) -> None:
    """[L-66 sentinel] emit N/A-ERROR:<name> to stderr, không nuốt lỗi."""
    print(f"[tripwire_e2_v2 N/A-ERROR:{sentinel_name}] {where}: {type(exc).__name__}: {exc}",
          file=sys.stderr)


def load_registered_generations() -> dict:
    """[UNREGISTERED-GRADES-FILE guard] Load census_generations block từ yaml.
    Returns {gen_name: {grades_file, md5, exposure_days, window, ...}}.
    """
    try:
        import yaml
    except ImportError as exc:
        _emit_sentinel("load_registered_generations", exc, "YAML-IMPORT")
        return {}
    if not YAML_PATH.exists(): return {}
    try:
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return (data.get("goi_nhe", {}).get("tripwire_e2", {}).get("census_generations") or {})
    except Exception as exc:
        _emit_sentinel("load_registered_generations", exc, "YAML-PARSE")
        return {}


def check_grades_registration(grades_file: Path,
                               registered: Optional[dict] = None) -> tuple[bool, Optional[str], Optional[dict]]:
    """[UNREGISTERED-GRADES-FILE guard · md5-gate NÓI] Check if grades_file matches
    any registered generation (basename + md5 phải khớp).

    Returns (is_registered, generation_name, generation_config).
    """
    if registered is None: registered = load_registered_generations()
    if not registered: return (False, None, None)
    try:
        actual_md5 = hashlib.md5(grades_file.read_bytes()).hexdigest()
    except Exception as exc:
        _emit_sentinel("check_grades_registration", exc, "MD5-COMPUTE")
        return (False, None, None)
    for gen_name, cfg in registered.items():
        reg_file = (cfg.get("grades_file") or "").strip()
        reg_md5 = (cfg.get("md5") or "").strip().lower()
        if grades_file.name == reg_file and actual_md5.lower() == reg_md5:
            return (True, gen_name, cfg)
    return (False, None, None)


def find_latest_grades_file(grades_dir=GRADES_DIR) -> Optional[Path]:
    """Return grades CSV with LATEST graded_at (not mtime).
    Pattern: census*grades*.csv per operator glob update 31/08.
    """
    files = list(grades_dir.glob("census*grades*.csv"))
    if not files: return None
    # Read graded_at from first data row of each; pick max
    def _read_graded_at(f):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                content = [line for line in fp if not line.startswith("#")]
            reader = csv.DictReader(content)
            for row in reader:
                ga = (row.get("graded_at") or "").strip()
                if ga: return ga
        except Exception as exc:
            _emit_sentinel(f"_read_graded_at({f.name})", exc, "READ-GRADED-AT")
        return ""
    files_dated = [(f, _read_graded_at(f)) for f in files]
    files_dated.sort(key=lambda x: x[1], reverse=True)
    return files_dated[0][0] if files_dated else None


def read_grades_header_md5(grades_file: Path) -> Optional[str]:
    """Parse md5 hash from header line of grades CSV (comment format)."""
    if not grades_file.exists(): return None
    with open(grades_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#"): break
            if "md5" in line.lower():
                # Extract md5-like hex string
                import re
                m = re.search(r"[a-f0-9]{32}", line.lower())
                if m: return m.group(0)
    return None


def read_grades_breakdown(grades_file: Path) -> dict:
    """[E2-METRIC-20260831 chốt-1 EXPOSURE] Read grades CSV → full breakdown +
    exposure window (min..max fire_date).

    Returns: {
        'n_fp': int, 'n_tp': int, 'n_pending': int, 'n_total': int,
        'exposure_min': str, 'exposure_max': str, 'exposure_days': int,
    }

    Schema: 'grade' column (FP/TP/PENDING) · 'date' column (fire_date).
    Backward-compat: also checks 'TP_FP' column (old v3 schema).
    """
    result = {"n_fp": 0, "n_tp": 0, "n_pending": 0, "n_total": 0,
              "exposure_min": None, "exposure_max": None, "exposure_days": None}
    if not grades_file.exists(): return result
    with open(grades_file, "r", encoding="utf-8") as f:
        content_lines = [line for line in f if not line.startswith("#")]
    if not content_lines: return result
    reader = csv.DictReader(content_lines)
    dates = []
    for row in reader:
        # v4 schema uses 'grade'; v3 uses 'TP_FP'
        g = (row.get("grade") or row.get("TP_FP") or "").strip().upper()
        result["n_total"] += 1
        if g == "FP": result["n_fp"] += 1
        elif g == "TP": result["n_tp"] += 1
        elif g == "PENDING" or g == "": result["n_pending"] += 1
        # else: other grade → count total but not breakdown
        d = (row.get("date") or "").strip()
        if d: dates.append(d)
    if dates:
        result["exposure_min"] = min(dates)
        result["exposure_max"] = max(dates)
        try:
            result["exposure_days"] = (_date.fromisoformat(result["exposure_max"])
                                      - _date.fromisoformat(result["exposure_min"])).days + 1
        except Exception as exc:
            _emit_sentinel("read_grades_breakdown.exposure_days", exc, "DATE-PARSE")
    return result


def compute_rate(n_fp: int, control_tokens: int = CONTROL_TOKENS_DEFAULT,
                 exposure_days: int = None) -> float:
    """[E2-METRIC-20260831 chốt-2] rate = n_FP × 30 / (control_tokens × exposure_days)

    Equivalent: n_fp / control_tokens / exposure_days * 30
    exposure_days = window fire_date từ census generation (CỐ ĐỊNH mọi chu kỳ re-grade).
    PENDING → chỉ đổi TỬ số (n_FP), thế hệ mới mang exposure riêng.
    """
    if control_tokens <= 0 or exposure_days is None or exposure_days <= 0: return 0.0
    return n_fp * 30 / (control_tokens * exposure_days)


def check_tripwire(grades_file: Path = None, max_rate: float = MAX_RATE_DEFAULT,
                   control_tokens: int = CONTROL_TOKENS_DEFAULT,
                   exposure_days_declared: int = None,
                   window_str: str = None,
                   expected_rate: Optional[float] = None,
                   expected_grades_md5: Optional[str] = None,
                   expected_breakdown: Optional[dict] = None,
                   override_generation_config: Optional[dict] = None) -> dict:
    """[E2-METRIC-20260831 · Resolution (b) 31/08] rate với EXPOSURE = DECLARED yaml.

    chốt-1 EXPOSURE: exposure_days_declared từ yaml single-source (KHÔNG min..max read).
      CỐ ĐỊNH mọi chu kỳ re-grade cùng thế hệ.
      Min..max in-file = sanity check phải ⊆ declared window.
      Fire NGOÀI declared window → status='OUT-OF-WINDOW' DỪNG thật.
    chốt-2 CÔNG THỨC: rate = n_FP × 30 / (control_tokens × exposure_days_declared)
    SELF-CHECK KÉP: md5 + rate + breakdown khớp expected.

    [UNREGISTERED-GRADES-FILE guard 01/09] Nếu grades_file KHÔNG khớp census_generations
    yaml (basename + md5) → return status='UNREGISTERED-GRADES-FILE' (không silent None).
    Bypass check bằng `override_generation_config` (dùng cho DRY-RUN e2e tests).

    Returns: dict với full breakdown + rate + status.
    """
    if grades_file is None:
        grades_file = find_latest_grades_file()
    if grades_file is None or not grades_file.exists():
        return {"status": "NO-GRADES-FILE", "trip": False, "context": "grades file not found"}

    md5_actual = hashlib.md5(grades_file.read_bytes()).hexdigest()

    # [UNREGISTERED-GRADES-FILE guard] · md5-gate NÓI, không câm
    if override_generation_config is None:
        is_reg, gen_name, gen_cfg = check_grades_registration(grades_file)
        if not is_reg:
            registered = load_registered_generations()
            reg_summary = ", ".join(f"{k}:{v.get('grades_file','?')}({(v.get('md5') or '')[:8]})"
                                    for k, v in registered.items()) or "no registered generations"
            return {
                "status": "UNREGISTERED-GRADES-FILE", "grades_file": str(grades_file),
                "grades_md5_actual": md5_actual, "trip": False,
                "context": f"file {grades_file.name} md5 {md5_actual[:12]} không khớp census_generations yaml · registered: {reg_summary}",
            }
        # Populate declared fields from yaml gen_cfg (yaml-single-source per Resolution b)
        if exposure_days_declared is None:
            exposure_days_declared = gen_cfg.get("exposure_days")
        if window_str is None:
            window_str = gen_cfg.get("window")
        if expected_rate is None:
            expected_rate = gen_cfg.get("expected_rate")
        if expected_grades_md5 is None:
            expected_grades_md5 = (gen_cfg.get("md5") or "").lower()
        if expected_breakdown is None:
            eb = gen_cfg.get("expected_breakdown") or {}
            expected_breakdown = {
                "n_fp": eb.get("n_FP"), "n_tp": eb.get("n_TP"), "n_pending": eb.get("n_PENDING")
            }
    else:
        # Override path (for DRY-RUN e2e): use passed gen_cfg fields
        gen_cfg = override_generation_config
        if exposure_days_declared is None:
            exposure_days_declared = gen_cfg.get("exposure_days")
        if window_str is None:
            window_str = gen_cfg.get("window")
        if expected_rate is None:
            expected_rate = gen_cfg.get("expected_rate")
        if expected_grades_md5 is None:
            expected_grades_md5 = (gen_cfg.get("md5") or "").lower() or None
        if expected_breakdown is None:
            eb = gen_cfg.get("expected_breakdown") or {}
            if eb:
                expected_breakdown = {
                    "n_fp": eb.get("n_FP"), "n_tp": eb.get("n_TP"), "n_pending": eb.get("n_PENDING")
                }

    breakdown = read_grades_breakdown(grades_file)
    n_fp = breakdown["n_fp"]
    n_tp = breakdown["n_tp"]
    n_pending = breakdown["n_pending"]
    n_total = breakdown["n_total"]
    read_min = breakdown["exposure_min"]
    read_max = breakdown["exposure_max"]
    read_days = breakdown["exposure_days"]

    # Sanity check: read range ⊆ declared window
    if window_str and read_min and read_max:
        try:
            w_start, w_end = window_str.split("..")
            if read_min < w_start or read_max > w_end:
                return {
                    "status": "OUT-OF-WINDOW", "grades_file": str(grades_file),
                    "grades_md5": md5_actual, "breakdown": breakdown,
                    "read_range": f"{read_min}..{read_max}",
                    "declared_window": window_str,
                    "trip": False,
                    "context": f"fire NGOÀI declared window · read {read_min}..{read_max} ⊄ {window_str}",
                }
        except Exception as exc:
            _emit_sentinel("check_tripwire.window_sanity", exc, "WINDOW-PARSE")

    # Use DECLARED exposure (Resolution (b))
    exposure_days = exposure_days_declared
    rate = compute_rate(n_fp, control_tokens, exposure_days) if exposure_days else 0.0
    trip = rate > max_rate

    # SELF-CHECK md5
    if expected_grades_md5 and md5_actual != expected_grades_md5:
        return {
            "status": "MD5-MISMATCH", "grades_file": str(grades_file),
            "grades_md5_actual": md5_actual, "grades_md5_expected": expected_grades_md5,
            "trip": False,
            "context": f"grades md5 mismatch (actual {md5_actual[:12]} ≠ expected {expected_grades_md5[:12]})",
        }
    # SELF-CHECK rate
    if expected_rate is not None and abs(rate - expected_rate) > 0.001:
        return {
            "status": "SELFCHECK-FAIL-RATE", "grades_file": str(grades_file),
            "grades_md5": md5_actual,
            "breakdown": breakdown,
            "rate_computed": rate, "rate_expected": expected_rate,
            "diff": rate - expected_rate, "trip": False,
            "context": f"rate {rate:.4f} ≠ expected {expected_rate:.4f} (diff {rate-expected_rate:+.4f})",
        }
    # SELF-CHECK breakdown
    if expected_breakdown is not None:
        for k in ["n_fp", "n_tp", "n_pending"]:
            if expected_breakdown.get(k) is not None and breakdown[k] != expected_breakdown[k]:
                return {
                    "status": "SELFCHECK-FAIL-BREAKDOWN", "grades_file": str(grades_file),
                    "grades_md5": md5_actual,
                    "breakdown_actual": breakdown, "breakdown_expected": expected_breakdown,
                    "diff_key": k, "diff_val": f"{breakdown[k]} ≠ {expected_breakdown[k]}",
                    "trip": False,
                    "context": f"breakdown {k}: {breakdown[k]} ≠ expected {expected_breakdown[k]}",
                }

    return {
        "grades_file": str(grades_file), "grades_md5": md5_actual,
        "breakdown": breakdown,
        "n_fp": n_fp, "n_tp": n_tp, "n_pending": n_pending, "n_total": n_total,
        "exposure_days_declared": exposure_days,
        "exposure_read_min": read_min, "exposure_read_max": read_max, "exposure_read_days": read_days,
        "declared_window": window_str,
        "rate": rate, "threshold": max_rate, "trip": trip,
        "status": "TRIP" if trip else "OK",
        "context": f"n_FP={n_fp}/n_TP={n_tp}/n_PEND={n_pending} · exposure={exposure_days}d declared ({window_str}) · read {read_min}..{read_max}={read_days}d",
    }


def format_output_pair(check_result: dict) -> str:
    """Format cặp output đêm: 'tripwire FP-rate=0.428 [TRIP] · raw=<x> (context)'.
    TP-note kèm nếu n_TP≥1: "N TP control-nhiễm (round-trip |ret|<30%) — loại khỏi tử"
    """
    status = check_result.get("status", "")
    if status.startswith("SELFCHECK-FAIL"):
        return f"tripwire SELF-CHECK-FAIL · {check_result.get('context', '')}"
    if status == "NO-GRADES-FILE":
        return "tripwire N/A-NO-GRADES-FILE"
    if status == "MD5-MISMATCH":
        return f"tripwire N/A-MD5-MISMATCH · expected {check_result.get('grades_md5_expected', '')[:8]}"
    if status == "UNREGISTERED-GRADES-FILE":
        return f"tripwire N/A-UNREGISTERED-GRADES-FILE · {check_result.get('context', '')}"
    if status == "OUT-OF-WINDOW":
        return f"tripwire N/A-OUT-OF-WINDOW · {check_result.get('context', '')}"
    rate = check_result.get("rate", 0)
    trip_flag = "[TRIP]" if check_result.get("trip") else "[OK]"
    context = check_result.get("context", "")
    n_tp = check_result.get("n_tp", 0)
    n_fp = check_result.get("n_fp", 0)
    lines = [f"tripwire FP-rate={rate:.3f} {trip_flag} · raw=n_FP={n_fp} ({context})"]
    if n_tp >= 1:
        lines.append(f"  ↳ {n_tp} TP control-nhiễm (round-trip |ret|<30%) — loại khỏi tử theo E2-metric 31/08")
    return "\n".join(lines)


def apply_trip_flag(check_result: dict):
    """Nếu TRIP → write flag file. Nếu OK và flag existed → auto-untrip (per 04:06 re-grade)."""
    if check_result.get("status") == "TRIP":
        FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLAG_PATH.write_text(json.dumps({
            "tripped_at": datetime.now(timezone.utc).isoformat(),
            "rate": check_result.get("rate"),
            "threshold": check_result.get("threshold"),
            "grades_md5": check_result.get("grades_md5"),
            "context": check_result.get("context"),
        }, indent=2), encoding="utf-8")
        return "TRIP-FLAGGED"
    else:
        # Auto-untrip if OK and flag existed
        if FLAG_PATH.exists():
            prev = None
            try: prev = json.loads(FLAG_PATH.read_text(encoding="utf-8"))
            except: pass
            FLAG_PATH.unlink()
            UNTRIP_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(UNTRIP_LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()}  auto-untrip · rate={check_result.get('rate', 0):.3f} ≤ {check_result.get('threshold', 0.4)}  previous_trip={prev}\n")
            return "AUTO-UNTRIPPED"
    return "NO-CHANGE"

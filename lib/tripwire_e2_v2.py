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
from pathlib import Path
from datetime import datetime, timezone, date as _date
from typing import Optional

REPO = Path(__file__).parent.parent
SCRATCH_DIR = REPO / "scratch"
STATE_DIR = REPO / "data/state"
FLAG_PATH = STATE_DIR / "tripwire_e2_v2_TRIPPED.flag"
UNTRIP_LOG = STATE_DIR / "tripwire_e2_v2_untrip.log"

TRAILING_DAYS_DEFAULT = 30
MAX_RATE_DEFAULT = 0.4
CONTROL_TOKENS_DEFAULT = 52


def find_latest_grades_file(scratch_dir=SCRATCH_DIR) -> Optional[Path]:
    """Return latest census_63_grades_*.csv by mtime."""
    files = sorted(scratch_dir.glob("census_63_grades_*.csv"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


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


def count_fp_from_grades(grades_file: Path) -> tuple[int, int]:
    """Read grades CSV → (n_FP, n_total_graded).
    Assumes column 'TP_FP' with values 'TP' | 'FP' | '' (empty/pending).
    """
    if not grades_file.exists(): return 0, 0
    n_fp = 0; n_total = 0
    with open(grades_file, "r", encoding="utf-8") as f:
        # Skip comment lines
        content_lines = [line for line in f if not line.startswith("#")]
    if not content_lines: return 0, 0
    reader = csv.DictReader(content_lines)
    for row in reader:
        grade = (row.get("TP_FP") or "").strip().upper()
        if grade in ("TP", "FP"):
            n_total += 1
            if grade == "FP": n_fp += 1
    return n_fp, n_total


def compute_rate(n_fp: int, control_tokens: int = CONTROL_TOKENS_DEFAULT,
                 window_days: int = None) -> float:
    """rate = n_FP / control_tokens / window_days × 30 (per token per 30d).
    Nếu window_days=None → 30 (rate directly per 30d)."""
    if control_tokens <= 0: return 0.0
    if window_days is None: window_days = 30
    return n_fp / control_tokens / window_days * 30


def check_tripwire(grades_file: Path = None, max_rate: float = MAX_RATE_DEFAULT,
                   control_tokens: int = CONTROL_TOKENS_DEFAULT,
                   window_days: int = 30,
                   expected_rate: Optional[float] = None,
                   expected_grades_md5: Optional[str] = None) -> dict:
    """Read grades file → compute rate → return status dict.

    SELF-CHECK: nếu expected_rate provided (e.g. 0.428 for grades v4),
      lệch >0.001 → status='SELFCHECK-FAIL', không paste output.

    Returns: {
        'grades_file': str, 'grades_md5': str, 'n_fp': int, 'n_total': int,
        'rate': float, 'threshold': float, 'trip': bool, 'status': str, 'context': str
    }
    """
    if grades_file is None:
        grades_file = find_latest_grades_file()
    if grades_file is None or not grades_file.exists():
        return {"status": "NO-GRADES-FILE", "trip": False, "context": "grades file not found"}

    md5 = read_grades_header_md5(grades_file)
    n_fp, n_total = count_fp_from_grades(grades_file)
    rate = compute_rate(n_fp, control_tokens, window_days)
    trip = rate > max_rate

    # SELF-CHECK
    if expected_rate is not None:
        if abs(rate - expected_rate) > 0.001:
            return {
                "status": "SELFCHECK-FAIL",
                "grades_file": str(grades_file),
                "grades_md5": md5,
                "n_fp": n_fp, "n_total": n_total,
                "rate_computed": rate,
                "rate_expected": expected_rate,
                "diff": rate - expected_rate,
                "trip": False,
                "context": f"SELF-CHECK FAIL: rate {rate:.3f} ≠ expected {expected_rate:.3f} (diff {rate-expected_rate:+.4f})",
            }
    if expected_grades_md5 and md5 and md5 != expected_grades_md5:
        return {
            "status": "MD5-MISMATCH",
            "grades_file": str(grades_file),
            "grades_md5_actual": md5,
            "grades_md5_expected": expected_grades_md5,
            "trip": False,
            "context": "grades file md5 mismatch — expected file not available",
        }

    return {
        "grades_file": str(grades_file),
        "grades_md5": md5,
        "n_fp": n_fp, "n_total": n_total,
        "rate": rate,
        "threshold": max_rate,
        "trip": trip,
        "status": "TRIP" if trip else "OK",
        "context": f"raw=n_FP={n_fp}/n_total={n_total}",
    }


def format_output_pair(check_result: dict) -> str:
    """Format cặp output đêm: 'tripwire FP-rate=0.428 [TRIP] · raw=<x> (context)'."""
    if check_result.get("status") == "SELFCHECK-FAIL":
        return f"tripwire SELF-CHECK-FAIL · {check_result.get('context', '')}"
    if check_result.get("status") == "NO-GRADES-FILE":
        return "tripwire N/A-NO-GRADES-FILE"
    if check_result.get("status") == "MD5-MISMATCH":
        return f"tripwire N/A-MD5-MISMATCH · expected {check_result.get('grades_md5_expected', '')[:8]}"
    rate = check_result.get("rate", 0)
    trip_flag = "[TRIP]" if check_result.get("trip") else "[OK]"
    context = check_result.get("context", "")
    return f"tripwire FP-rate={rate:.3f} {trip_flag} · {context}"


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

"""_task_apply_rev10 · V3.5j directive item 1 · L-72-76 khuôn.

LESSONS APPLY BẰNG SCRIPT (không chờ operator tay):
  1. Load CASE_INDEX.xlsx (md5 pre)
  2. Append REV10 amendments vào sheet LESSONS
  3. Save (md5 post)
  4. Regen lessons_learned.md view
  5. SCP mirror LESSONS view lên VPS + md5 chuỗi

Rows từ vé e171c341 (proposals/rev10_apply_20260908.md · 16 amendments).
"""
import os, sys, hashlib, subprocess, io
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 stdout on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"d:/Data back test/whale_data") if os.name == "nt" else Path("/root/Data_back_test/whale_data")
XLSX = REPO / "docs/case_files/CASE_INDEX.xlsx"
MD_VIEW = REPO / "docs/lessons_learned.md"
LOG = REPO / "data/logs/apply_rev10.log"


def _md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def _log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().isoformat(timespec="seconds")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}Z] {msg}\n")
    print(msg)


# Amendments per vé REV10 e171c341 · 16 rows
AMENDMENTS = [
    ("L-79", "BLOCKER-BỊA + DEMO-RUỘT", "REV10-e171c341",
     "Placeholder PENDING-<x> khi source artifact sẵn = bịa. Demo-ruột: preview phải kiểm ruột trước trình."),
    ("L-78-append", "vế-tồn-tại (EMPTY-GUARD)", "REV10-e171c341",
     "Bốn-vế: (1) độc-lập · (2) không cùng-object · (3) đẳng-thức bất-biến · (4) vế-tồn-tại (empty-guard)."),
    ("án-lệ-✓-suy", "phái sinh L-79", "REV10-e171c341",
     "Nhãn chưa seal → in [UNVERIFIED] · CẤM ✓ suy."),
    ("§B-v1.8", "cộng dồn V3.1-V3.5i", "REV10-e171c341",
     "SỔ-ĂN-SỰ-KIỆN · SENT-anchor · FRESH-Δ-only · EPISODE×COVERAGE · WATERFALL · strict-139/[NGOÀI-SỔ]/[≥3×]-đề-cử · LATTICE max-severity · STICKY-đích-danh · first-seed-any-axis · READ-BACK VERIFY · anchor-139."),
    ("p14-DẢI-KÉP", "PROVISIONAL control-27/09", "REV10-e171c341",
     "chân-a n_PRE∈[4,6] · chân-b n_treo≤15 ∧ coverage-sạch(all ≥15/31) · sort dải-a=star_birth DESC · sort dải-b=last-signal ASC · coverage thủng → CAVEAT án-ở-ống."),
    ("p15-semantics", "UNIVERSE-BOUND FAIL-ENGINE with NAMES", "REV10-e171c341",
     "n_unique mọi trục ≤ |universe|=139 · vi phạm = FAIL-ENGINE treo verdict · in ĐÍCH DANH oob syms · CẤM silent-drop · universe cite = file+md5."),
    ("PIN-TUYỂN-DỤNG", "14 pin distinct · 17 sabotage rows", "REV10-e171c341",
     "Mỗi pin ≥1 mutate thật · 4-field log (pin·mutate·verdict·revert-sha) · nhánh luật-chết viết lại trước · p2-p6 FAIL-VACUOUS · p15 FAIL-ENGINE-NAMED · sweep prefix-match."),
    ("KHÓA-ĐÍCH-DANH", "sticky tag in-message", "REV10-e171c341",
     "Sticky-source chỉ match {🔴-block · WASH-CRASH · S4/S5} · CẤM ¹-generic · tag `STICKY-XẢ vì <src>-<DD/MM>` in trên dòng ⭐."),
    ("WL-án-lệ", "18≡18 verbatim", "REV10-e171c341",
     "18≡18 đối-chứng-hai-nguồn · 44-unique · List-B[23,44]avg34.6 · thác 157→16 · thay vĩnh viễn mọi trích tiền-REV4."),
    ("star_birth-def", "trục-thứ-hai tới", "REV10-e171c341",
     "star_birth(token) := min{d : |{trục có event ≤ d}| ≥ 2}."),
    ("⭐-01-entry#1", "COLLECT bảng-chấm-⭐", "REV10-e171c341",
     "COLLECT direction=POST-DUMP · ret=-40.0% · dd=-53.6% · sổ chấm: 'máy fire trước sóng (TP-recall) · ledger gán chiều sai 4 ngày (FP-direction)'."),
    ("L-80-DRAFT", "regex block-scoped enforcement", "REV10-e171c341",
     "'Regex đọc log đa-target PHẢI block-scoped (anchor target → next-target/EOF); DOTALL-span = phantom-đếm.' Án lệ kép: forensic-25-phantom 07/09 · extractor-watchlist 62≠30. DRAFT-KHÔNG-KÍCH-HOẠT."),
    ("LABEL-CLAIMS-LINT", "án lệ #2 + #2b", "REV10-e171c341",
     "Grep nhãn CLAIM {sorted·sort:·✓·checked·verified·OK·PASS·đã-*} · hợp lệ khi bán kính k=5 có phép-kiểm hoặc cite [per <seal-id>]. Án lệ #2: '5/5 WIRED ✅' không biên lai orphan. Án lệ #2b: claim-✅-giả toàn phần (watchlist wire 0 dump_as_sent)."),
    ("SỔ-ĐỌC-ENFORCEMENT", "regex đa-target block-scoped", "REV10-e171c341",
     "Regex đọc log đa-target = block-scoped. Fix wired _wl_sent_by_target."),
    ("DOS-PACKAGE", "ghế 27/09", "REV10-e171c341",
     "Câu kiến trúc: 'exposure-declared-theo-thế-hệ tầng universe — đổi mẫu số tại ranh thế hệ'. DOS 4×/30d ĐỀ-CỬ-UNIVERSE bất động 27/09. BEAT/ONE/B đếm tiếp."),
    ("[SENT]-marker-chuẩn", "L-59 áp mọi sender", "REV10-e171c341",
     "Mọi sender in `[SENT] <kênh> ok=<bool> HTTP <code> hash=<h>`. Wired: gom_daily · phase_map · watchlist."),
]


def apply_lessons():
    try:
        import openpyxl
    except ImportError:
        _log("[N/A-ERROR:APPLY] openpyxl not installed")
        return False
    md5_pre = _md5(XLSX)
    _log(f"[PRE] CASE_INDEX.xlsx md5={md5_pre}")

    wb = openpyxl.load_workbook(XLSX)
    if "LESSONS" not in wb.sheetnames:
        _log(f"[N/A-ERROR:APPLY] LESSONS sheet not found · sheets={wb.sheetnames}")
        return False
    ws = wb["LESSONS"]

    # Check existing content to avoid dup
    existing_keys = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[0]:
            existing_keys.add(str(row[0]).strip())

    added = 0
    for lesson_id, title, source, body in AMENDMENTS:
        key = lesson_id
        if key in existing_keys:
            _log(f"[SKIP] {key} already in sheet")
            continue
        # Append: {lesson_id, title, source_ref, body} + amendment tag col
        ws.append([lesson_id, title, source, body, None, None, None, None, "REV10-APPLY"])
        added += 1
        _log(f"[APPEND] {lesson_id} · {title}")

    if added == 0:
        _log(f"[NO-CHANGE] all {len(AMENDMENTS)} amendments already applied · pre=post")
        return True

    wb.save(XLSX)
    md5_post = _md5(XLSX)
    _log(f"[POST] CASE_INDEX.xlsx md5={md5_post} · added {added} rows")
    return True


def regen_view():
    """Regen lessons_learned.md view từ LESSONS sheet."""
    try:
        import openpyxl
    except ImportError:
        _log("[N/A-ERROR:REGEN] openpyxl missing")
        return False
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["LESSONS"]
    lines = [
        "# LESSONS LEARNED · view sinh từ CASE_INDEX.xlsx sheet LESSONS (L-74)",
        "# Regen: python _task_apply_rev10_20260908.py",
        "# CẤM edit md trực tiếp · edit vào sheet · md chỉ regenerate.",
        "",
        f"# Regenerated: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
    ]
    rows = list(ws.iter_rows(values_only=True))
    if not rows: return False
    header = rows[0]
    # Print as markdown table (limit cols shown to first 5)
    cols_show = ["id", "title", "source", "body", "amendment"]
    lines.append("| " + " | ".join(cols_show) + " |")
    lines.append("|" + "|".join(["---"] * len(cols_show)) + "|")
    for row in rows[1:]:
        if not row or not row[0]: continue
        vals = [
            str(row[0] or "-"),
            str(row[1] or "-").replace("|", "\\|"),
            str(row[2] or "-"),
            (str(row[3] or "-").replace("|", "\\|").replace("\n", " "))[:300],
            str(row[8] or "-") if len(row) > 8 else "-",
        ]
        lines.append("| " + " | ".join(vals) + " |")

    content = "\n".join(lines) + "\n"
    MD_VIEW.write_text(content, encoding="utf-8")
    md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
    _log(f"[REGEN] {MD_VIEW} · md5={md5} · n_rows={len(rows)-1}")
    return True


def scp_mirror():
    """SCP lessons_learned.md → VPS · verify md5 khớp."""
    md5_local = _md5(MD_VIEW)
    try:
        r = subprocess.run(
            ["scp", str(MD_VIEW), "root@5.223.67.21:/root/Data_back_test/whale_data/docs/"],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            _log(f"[N/A-ERROR:SCP] returncode={r.returncode} · stderr={r.stderr[:200]}")
            return False
    except Exception as e:
        _log(f"[N/A-ERROR:SCP] {type(e).__name__}: {e}")
        return False
    try:
        v = subprocess.run(
            ["ssh", "root@5.223.67.21",
             "md5sum /root/Data_back_test/whale_data/docs/lessons_learned.md"],
            capture_output=True, text=True, timeout=15)
        md5_vps = v.stdout.split()[0] if v.returncode == 0 else "?"
    except Exception as e:
        _log(f"[N/A-ERROR:VERIFY] {type(e).__name__}: {e}")
        return False
    ok = md5_local == md5_vps
    _log(f"[SCP-MIRROR] local={md5_local} · vps={md5_vps} · match={ok}")
    return ok


def main():
    _log("─── _task_apply_rev10 V3.5j start ───")
    if not apply_lessons():
        _log("APPLY FAIL · abort")
        return 1
    if not regen_view():
        _log("REGEN FAIL · abort")
        return 1
    if not scp_mirror():
        _log("SCP-MIRROR FAIL · lessons applied local but VPS not mirrored")
        return 1
    _log("─── _task_apply_rev10 DONE ─── evidence: data/logs/apply_rev10.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())

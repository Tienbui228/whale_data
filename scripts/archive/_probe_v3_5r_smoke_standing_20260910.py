"""V3.5r smoke · standing check với fake KHÔNG-KÍCH verdict · 3 điều kiện readout.

Đọc code check_standing() từ scripts/master_preview_send.py · sandbox verdict-file
tạm thay bằng {verdict=KHÔNG-KÍCH · date=today · evidence_pointer=<smoke>}.
Restore verdict-file sau smoke.

Điều kiện standing (V3.5p thuần máy):
  1. verdict-file exists AND verdict == 'KHÔNG-KÍCH' AND has evidence_pointer
  2. demo5_sent.marker exists (HỒ-SƠ-LỊCH-SỬ bất biến · V3.5r)
  3. preview_veto.marker NOT exists
"""
from __future__ import annotations
import sys, os, json, shutil
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
STATE = REPO / "data/state"
VERDICT = STATE / "dem0_lan2_verdict.json"
DEMO5 = STATE / "demo5_sent.marker"
VETO = STATE / "preview_veto.marker"
BACKUP = STATE / "dem0_lan2_verdict.json.bak_smoke"

sys.path.insert(0, str(REPO / "scripts"))


def main():
    print("═" * 62)
    print("V3.5r SMOKE · standing check với fake KHÔNG-KÍCH verdict")
    print("═" * 62)

    # 1. Backup current verdict
    if VERDICT.exists():
        shutil.copy(VERDICT, BACKUP)
    original_verdict = VERDICT.read_text(encoding="utf-8") if VERDICT.exists() else None

    # 2. Write fake KHÔNG-KÍCH verdict for TODAY (within 2d)
    today = datetime.now(timezone.utc).date().isoformat()
    fake = {
        "verdict": "KHÔNG-KÍCH",
        "date": today,
        "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_pointer": "smoke sandbox · V3.5r item 1 · fake · not for prod",
        "n_full_pair": "6/6", "n_sent": "6/6",
    }
    VERDICT.write_text(json.dumps(fake, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. Show pre-state
    print(f"\n─── PRE-STATE ───")
    print(f"  verdict-file: exists={VERDICT.exists()} · verdict='KHÔNG-KÍCH' · date={today}")
    print(f"  demo5_sent.marker: exists={DEMO5.exists()}")
    if DEMO5.exists():
        print(f"    content preview: {DEMO5.read_text(encoding='utf-8').splitlines()[0]}")
    print(f"  preview_veto.marker: exists={VETO.exists()} (want: False)")

    # 4. Call check_standing() · fresh import
    for m in list(sys.modules.keys()):
        if "master_preview_send" in m: del sys.modules[m]
    from master_preview_send import check_standing
    ok, reason = check_standing()

    print(f"\n─── check_standing() result ───")
    mark = "✅" if ok else "❌"
    print(f"  {mark} ok={ok} · reason={reason}")

    # 5. Explicit 3-condition readout
    print(f"\n─── 3 điều kiện đọc lại đích danh ───")
    v = json.loads(VERDICT.read_text(encoding="utf-8"))
    c1 = v.get("verdict") == "KHÔNG-KÍCH" and bool(v.get("evidence_pointer"))
    c2 = DEMO5.exists()
    c3 = not VETO.exists()
    print(f"  · 1. verdict==KHÔNG-KÍCH ∧ evidence_pointer: {c1}")
    print(f"  · 2. demo5_sent.marker exists (HỒ-SƠ-LỊCH-SỬ V3.5r): {c2}")
    print(f"  · 3. preview_veto.marker NOT exists: {c3}")
    all_ok = c1 and c2 and c3
    print(f"\n  3/3 pass? {all_ok}")

    # 6. Restore original verdict
    if BACKUP.exists():
        shutil.move(BACKUP, VERDICT)
    print(f"\n─── POST-STATE · verdict restored ───")
    if VERDICT.exists():
        v = json.loads(VERDICT.read_text(encoding="utf-8"))
        print(f"  verdict restored: {v.get('verdict')} · date={v.get('date')}")

    overall = "PASS" if all_ok and ok else "FAIL"
    print(f"\n[SMOKE] standing 3/3: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

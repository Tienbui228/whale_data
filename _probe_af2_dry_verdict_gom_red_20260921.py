"""AF2 · dry verdict simulate gom_daily sent_ok=False cho target 09-20.

Loại bỏ TẠM entry gom_daily khỏi bell_journal + xoá dòng SENT trong gom_daily.log
· gọi compute_night_verdict(dry=True) · in verdict + standing · restore back.
KHÔNG chạm state (dùng đường U5 --dry + monkey-patch log paths).
"""
import sys, os, json, shutil, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

import master_preview_send as mps

TARGET = "2026-09-21"   # chưa có epoch · fresh compute · phản ánh cron đêm mới

# Backup 2 files
BELL = Path("/root/Data_back_test/whale_data/data/logs/bell_journal.jsonl")
GD_LOG = Path("/root/Data_back_test/whale_data/data/logs/gom_daily.log")

bak_bell = BELL.read_bytes()
bak_gd = GD_LOG.read_bytes()

try:
    # 1. Remove gom_daily entries for TARGET from bell_journal
    filtered = []
    removed_count = 0
    for line in bak_bell.decode("utf-8").splitlines():
        if not line.strip():
            filtered.append(line); continue
        try:
            e = json.loads(line)
            if e.get("renderer") == "gom_daily" and e.get("target_date") == TARGET:
                removed_count += 1; continue
        except Exception:
            pass
        filtered.append(line)
    BELL.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    print(f"[SETUP] removed {removed_count} gom_daily bell_journal entries for {TARGET}")

    # 2. Remove [SENT] gom_daily lines for TARGET from gom_daily.log
    kept_lines = []
    removed_log = 0
    for line in bak_gd.decode("utf-8", errors="replace").splitlines():
        if "[SENT] gom_daily ok=True" in line and f"target={TARGET}" in line:
            removed_log += 1; continue
        kept_lines.append(line)
    GD_LOG.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
    print(f"[SETUP] removed {removed_log} [SENT] gom_daily lines for {TARGET}")

    # 3. Dry compute
    print(f"\n═══ compute_night_verdict('{TARGET}', dry=True) SAU khi gom_daily red ═══")
    r = mps.compute_night_verdict(TARGET, dry=True)
    print(f"  verdict          : {r['verdict']}")
    print(f"  n_full_pair      : {r['n_full_pair']}")
    print(f"  n_sent           : {r['n_sent']}")
    print(f"  missing_legs     : {r['missing_legs']}")
    print(f"  unknown_sentinels: {r.get('unknown_sentinels', [])}")
    print(f"  pin_scan         : {r.get('pin_scan_p1_p22_bo_niem')}")
    for renderer in ["gom_daily", "watchlist", "phase_map"]:
        d = r["sent_leg_detail"].get(renderer, {})
        print(f"  {renderer:12s} : ok={d.get('ok')} source={d.get('source')}")

    print(f"\n═══ STANDING check ═══")
    ok, reason = mps.check_standing()
    print(f"  standing.ok = {ok}")
    print(f"  reason      = {reason}")

    print(f"\n═══ TÁC ĐỘNG CRON ═══")
    if ok:
        print(f"  standing PASS → cron PROCEED tới rebuild/render/send (bản tin gửi)")
    else:
        print(f"  standing FAIL → cron SKIP · KHÔNG rebuild ledger · KHÔNG render · KHÔNG send · KHÔNG journal")
finally:
    # Restore
    BELL.write_bytes(bak_bell)
    GD_LOG.write_bytes(bak_gd)
    print(f"\n[RESTORE] bell_journal + gom_daily.log restored")

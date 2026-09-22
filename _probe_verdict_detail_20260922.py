import sys
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK
from master_preview_send import compute_night_verdict

for t in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20","2026-09-21"]:
    v = compute_night_verdict(t, dry=True)
    print(f'{t} · verdict={v["verdict"]:>12s} · full={v["n_full_pair"]} · sent={v["n_sent"]} · '
          f'pin={v.get("pin_scan_p1_p22_bo_niem","?")} · unk={len(v.get("unknown_sentinels",[]))} · '
          f'missing={v["missing_legs"]}')

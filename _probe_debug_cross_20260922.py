import sys
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
import hedge_v2 as hv

# Check 09-20 target · which tokens are over 2× 60d
price_map = hv.load_daily_rows("2026-09-20")
print("── 09-20 luật-nền check ──")
for sym in ["CROSSUSDT","BTRUSDT","BULLAUSDT","KOMAUSDT","SKYAIUSDT","TAKEUSDT"]:
    over, kd = hv.luat_nen_2x_min60d(sym, "2026-09-20", price_map)
    print(f"  {sym:12s} over={over} kd={kd}")

# 09-18 target · original body was for this
price_map18 = hv.load_daily_rows("2026-09-18")
print("── 09-18 luật-nền check ──")
for sym in ["CROSSUSDT","BTRUSDT","BULLAUSDT","KOMAUSDT","SKYAIUSDT","TAKEUSDT"]:
    over, kd = hv.luat_nen_2x_min60d(sym, "2026-09-18", price_map18)
    print(f"  {sym:12s} over={over} kd={kd}")

# Check 09-20 body: CROSS event D_cross=?
_, meta = hv.compose_body("2026-09-20", report_only=True)
print()
print(f"09-20 meta n_luat_nen={meta['n_luat_nen']}")

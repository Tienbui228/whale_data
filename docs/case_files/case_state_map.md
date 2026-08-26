# case_state_map — VIEW SINH read-only từ `CASE_INDEX.xlsx` sheet INDEX

**Generated:** 2026-08-26 03:19 UTC  ·  **Source:** `docs/case_files/CASE_INDEX.xlsx`
**Nguyên tắc (spec PHASE-TAG v0.3 §2, D1 chốt v0.3 #19):**
- Operator ký state TRONG `CASE_INDEX.xlsx` (canonical). File này là ống dẫn read-only.
- Đọc map = đọc verdict người ký, KHÔNG phạm Δ5.
- `case_tracker.md` giữ nguyên (hành chính án OPEN/RESOLVED/BLOCKED — khác sổ).
- Agent regenerate khi CASE_INDEX đổi. CẤM edit trực tiếp file này.

---

| token | state_ký | ngày_ký | verdict_ref (loại) | action_class | MM_ID | file |
|---|---|---|---|---|---|---|
| TST | COLD_START — PENDING | 2026-08-08 | Alpha fullyDelisted, ATH=listing day, -94% drawdown. Massive vol spike 07/08 (+2 | COLD_START |  | CASE_TST.xlsx |
| BANK | TRACKING | 2026-07-29 | pump da chay tron (+6.8x) | WATCH-only | MM-BIDWALK-A | CASE_BANK.xlsx |
| TAG | OPEN — WATCH-nong | 2026-07-28 | pump vong 2 nghi an | WATCH | unknown | CASE_TAG.xlsx |
| BR | OPEN | 2026-07-29 | pump-to-distribute | STAND_ASIDE | MM-BAIT-B | CASE_BR.xlsx |
| IDOL | OPEN | 2026-08-03 | nghi relocation / pump-staging | WATCH | unknown | CASE_IDOL.xlsx |
| TUT | du kien CASE-04 | — | test duong concentration_shift | — | (xet) | (hang cho) |
| BTW | DISTRIBUTION-WATCH | — | ho so trap mau | — | MM-BAIT-B | (hang cho) |
| PARTI | du kien CASE-06 | — | cau truc dep gay (calib #13 NEG) | — | (xet) | (hang cho) |
| HUMA / AT | mo khi tell ban | — | cum van tay div~8 | — | MM-BIDWALK-A? | (hang cho) |
| HEI | COLD_START — PENDING | 2026-08-08 | cold-start perp+spot, spike events 05-29/08-05/08-06 | COLD_START | PENDING | CASE_HEI.xlsx |
| BANANAS31 | COLD_START — PENDING | 2026-08-07 | Alpha fullyDelisted, dump -80% ATH, pos_r~6.7 (BTW/phan phoi?) | COLD_START |  | CASE_BANANAS31.xlsx |
| AGT | COLD_START — PENDING | 2026-08-08 | Alaya Governance Token. Perp onboard 2025-05-20, ATH=2025-05-27 (0.034016). Draw | COLD_START |  | CASE_AGT.xlsx |
| FF | COLD_START — AUDIT PENDING | Bot báo gom ~$2M trên perp — tái lập số, ba phương pháp §3 độc lập | ALPHA_398 | 2026-08-08 |  | FFUSDT |
| COOKIE | OPEN — audit-collect complete, awaiting operator verdict | 2026-08-09 | GOM-C fire 08-03; pump pattern; ATH-97.9%; OI $1.1M | COLD_START |  | CASE_COOKIE.xlsx |
| BROCCOLIF3B | OPEN | 2026-08-10 | COLD_START | COLD_START |  | CASE_BROCCOLIF3B.xlsx |
| KOMA | OPEN | 2026-08-10 | GOM-C PROVISIONAL | COLD_START | ALPHA_1 | CASE_KOMA.xlsx |
| APR | DISTRIBUTION-WATCH | 2026-08-10 | GOM-C 22ngay PROVISIONAL | COLD_START | N/A (not Alpha) | CASE_APR.xlsx |
| BTW | DISTRIBUTION-WATCH | 2026-08-10 | BLOWOFF2.0 echo; 3-cond trigger 0/3; OI UNCALIBRATED; GOM-C 14d pre-cool | WATCH (án tích refresh) |  | CASE_BTW.xlsx |
| ON | DISTRIBUTION-WATCH · S2-leg3 | 2026-08-10 | DIST_WALL ATH-XẢ; 0 GOM-A; OI UNCALIBRATED; stage S3 xả-vùng-nhớ | WATCH (án mới, stage S3 pending confirmation) |  | CASE_ON.xlsx |
| GUA | S2-WATCH · DISTRIBUTION | 2026-08-10 | crowd-trap; div_avg3=0.41 BEAR; gLSR=2.87 VERY BULL; 0 GOM-A; OI calib $5.4M; AT | WATCH (án mới, pump in-progress → DỪNG chờ đọc) | ALPHA_483 | CASE_GUA.xlsx |
| CYS | COLD_START — PENDING | 2026-08-13 | GOM audit: gom thật vs staged-pump. Short squeeze Aug04-12 (+438% từ Jun trough) | COLD_START |  | CASE_CYS.xlsx |
| AIN | TRACKING-ACTIVE | 2026-08-13 | Deposit intel: 30M token ≈ $2.4M từ 04/08. GOM-D 4/4 PASS, GOM-E PASS 29d hedge. | COLD_START |  | CASE_AIN.xlsx |
| TRIA | TRACKING (cold-start Aug19) | ? |  |  |  |  |
| STBL | TRACKING (cold-start Aug19, contract UNVERIFIED) | ? |  |  |  |  |
| HEMI | TRACKING (cold-start Aug20, active campaign, contract UNVERIFIED) | ? |  |  |  |  |
| PUMPBTC | TRACKING (cold-start Aug20, hedge episode 51d ongoing, contract VERIFIED) | ? |  |  |  |  |
| AKE | COLD_START 21/08 (R2 nhịp 1) — DAILY populated, contract UNVERIFIED (nhịp 2) | ? |  |  |  |  |
| COLD_START | 2026-08-23 | ? | 23/08 fresh operator paste contract |  |  | CAP |

---

**Tổng:** 28 case

**Machine-readable JSON view (join-key cho phase_tag.py):**

```json
{
  "TST": {"state": "COLD_START — PENDING", "ngay_ky": "2026-08-08", "verdict_ref": "Alpha fullyDelisted, ATH=listing day, -94% drawdown. Massive"},
  "BANK": {"state": "TRACKING", "ngay_ky": "2026-07-29", "verdict_ref": "pump da chay tron (+6.8x)"},
  "TAG": {"state": "OPEN — WATCH-nong", "ngay_ky": "2026-07-28", "verdict_ref": "pump vong 2 nghi an"},
  "BR": {"state": "OPEN", "ngay_ky": "2026-07-29", "verdict_ref": "pump-to-distribute"},
  "IDOL": {"state": "OPEN", "ngay_ky": "2026-08-03", "verdict_ref": "nghi relocation / pump-staging"},
  "TUT": {"state": "du kien CASE-04", "ngay_ky": "—", "verdict_ref": "test duong concentration_shift"},
  "BTW": {"state": "DISTRIBUTION-WATCH", "ngay_ky": "—", "verdict_ref": "ho so trap mau"},
  "PARTI": {"state": "du kien CASE-06", "ngay_ky": "—", "verdict_ref": "cau truc dep gay (calib #13 NEG)"},
  "HUMA / AT": {"state": "mo khi tell ban", "ngay_ky": "—", "verdict_ref": "cum van tay div~8"},
  "HEI": {"state": "COLD_START — PENDING", "ngay_ky": "2026-08-08", "verdict_ref": "cold-start perp+spot, spike events 05-29/08-05/08-06"},
  "BANANAS31": {"state": "COLD_START — PENDING", "ngay_ky": "2026-08-07", "verdict_ref": "Alpha fullyDelisted, dump -80% ATH, pos_r~6.7 (BTW/phan phoi"},
  "AGT": {"state": "COLD_START — PENDING", "ngay_ky": "2026-08-08", "verdict_ref": "Alaya Governance Token. Perp onboard 2025-05-20, ATH=2025-05"},
  "FF": {"state": "COLD_START — AUDIT PENDING", "ngay_ky": "Bot báo gom ~$2M trên perp — tái lập số, ba phương pháp §3 độc lập", "verdict_ref": "ALPHA_398"},
  "COOKIE": {"state": "OPEN — audit-collect complete, awaiting operator verdict", "ngay_ky": "2026-08-09", "verdict_ref": "GOM-C fire 08-03; pump pattern; ATH-97.9%; OI $1.1M"},
  "BROCCOLIF3B": {"state": "OPEN", "ngay_ky": "2026-08-10", "verdict_ref": "COLD_START"},
  "KOMA": {"state": "OPEN", "ngay_ky": "2026-08-10", "verdict_ref": "GOM-C PROVISIONAL"},
  "APR": {"state": "DISTRIBUTION-WATCH", "ngay_ky": "2026-08-10", "verdict_ref": "GOM-C 22ngay PROVISIONAL"},
  "BTW": {"state": "DISTRIBUTION-WATCH", "ngay_ky": "2026-08-10", "verdict_ref": "BLOWOFF2.0 echo; 3-cond trigger 0/3; OI UNCALIBRATED; GOM-C "},
  "ON": {"state": "DISTRIBUTION-WATCH · S2-leg3", "ngay_ky": "2026-08-10", "verdict_ref": "DIST_WALL ATH-XẢ; 0 GOM-A; OI UNCALIBRATED; stage S3 xả-vùng"},
  "GUA": {"state": "S2-WATCH · DISTRIBUTION", "ngay_ky": "2026-08-10", "verdict_ref": "crowd-trap; div_avg3=0.41 BEAR; gLSR=2.87 VERY BULL; 0 GOM-A"},
  "CYS": {"state": "COLD_START — PENDING", "ngay_ky": "2026-08-13", "verdict_ref": "GOM audit: gom thật vs staged-pump. Short squeeze Aug04-12 ("},
  "AIN": {"state": "TRACKING-ACTIVE", "ngay_ky": "2026-08-13", "verdict_ref": "Deposit intel: 30M token ≈ $2.4M từ 04/08. GOM-D 4/4 PASS, G"},
  "TRIA": {"state": "TRACKING (cold-start Aug19)", "ngay_ky": "?", "verdict_ref": ""},
  "STBL": {"state": "TRACKING (cold-start Aug19, contract UNVERIFIED)", "ngay_ky": "?", "verdict_ref": ""},
  "HEMI": {"state": "TRACKING (cold-start Aug20, active campaign, contract UNVERIFIED)", "ngay_ky": "?", "verdict_ref": ""},
  "PUMPBTC": {"state": "TRACKING (cold-start Aug20, hedge episode 51d ongoing, contract VERIFIED)", "ngay_ky": "?", "verdict_ref": ""},
  "AKE": {"state": "COLD_START 21/08 (R2 nhịp 1) — DAILY populated, contract UNVERIFIED (nhịp 2)", "ngay_ky": "?", "verdict_ref": ""},
  "COLD_START": {"state": "2026-08-23", "ngay_ky": "?", "verdict_ref": "23/08 fresh operator paste contract"}
}
```

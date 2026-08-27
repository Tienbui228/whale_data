# G6 Report mẫu 2 đêm — Telegram khối CAMPAIGN-PRE post gói-nhẹ

**Status:** MẪU FORMAT · CHỜ cron 28/08 01:45 UTC + 29/08 01:45 UTC (2 nights official post rev3) để paste NGUYÊN VĂN.
**Snapshot pin:** spec bot-signals sha `490a8f49` · gate_defs md5 `f275c53c` · yaml md5 `b03420a8` (rev3 +verify_walletset).
- **Đêm-1 27/08 01:45 UTC target=2026-08-26** = archive-note pre-wire (code `e851db50` cũ, `conf=conf=` double + `[[suppressed:perp]]` không trailer + **ramp dead c509b264 lineage** · NameError `_os_env` nuốt bởi except-pass trong chuỗi 70678b7 → 531c4d1 → ec8782e → 0ef10f7; log H1 `n_eval=0 n_NA=139` confirming) — KHÔNG counted G6 official.
- **Đêm-2 28/08 01:45 UTC target=2026-08-27** = máy-final **rev4-FINAL** code md5 `f99ef3c8` (gom_h_daily.py) + `83d0e131` (tripwire_e2.py) + yaml `3820b87c` + counter `1c104491` — accumulates rev2 3-fix + rev3 VERIFY-WALLETSET + rev4 CONF-FIX + **rev4-FINAL v2.1-THẬT yaml obs_min single-source + WALLETSET 2×2 wire + os import fix**.
- **Đêm-3 29/08 01:45 UTC target=2026-08-28** = official #2 cùng rev4-FINAL.
- **rev3/rev4 conf-fix note:** display-family (không đổi compose).
- **compose-string VPS (freeze giữ):** yaml `gom_h.compose` VPS md5 `3820b87c` vẫn giữ wording cũ `"(H1 OR (H2 AND T0.1)) AND NOT gom_h_cooldown_14d"` — stale so với code rev4-FINAL. **Behavior đã chứng qua SELF-CHECK-COMPOSE 3-dòng (CYS 07-12 h2_status=T, BTR 07-28 ramp=15.04%, BANANAS31 dq skip)**. LOCAL yaml đã sửa reflect true `"h1_raw OR h2_raw · T0.1 → NHÃN CONF"`. SCP compose-fix vào yaml VPS **SAU đêm-3** (29/08 01:45 UTC), không đụng compose behavior.
- **H1 kho metric fix (α-3 KÝ 27/08 LOCAL only tới hết freeze):** adapter `_kho_step_3d_best` canonical 3d-best per spec §5 · conformance fixture PASS 4/4 (XAN 07-03=10.10%T · BTR 07-29=12.02%T · TUT 08-09=4.58%F · CAP 07-12 prev-0-edge bắt lb=3). SCP SAU đêm-3.
- **Tripwire trailing-30d hybrid kỷ nguyên (post SCP hậu-freeze):** counter đêm-4+ sẽ trộn kỷ-nguyên-1d (under-count trước fix) với 3d-best (post fix) → rate leo dần vài ngày đầu. Kỳ vọng hội tụ về ~**0.845 census baseline** (85 kept fires / 52 eligible × 30/58). 4.4 victims/day là số THÔ (258/58) — kept hậu-cooldown thấp hơn nhiều. Đọc số với chú thích, không hoảng.
- **✅ rev4-FINAL RAMP RESTORATION (operator ky 27/08 confirm accept):** `os as _os_env` import fix restore ramp compute (silent-fail 4 revs cũ). Đêm-2/3 official CÙNG BASELINE f99ef3c8 (ramp sống lần đầu trên cron từ 2026-08-28). yaml `goi_nhe.kho_ramp.provisional_30d_start=2026-08-28` ghi mốc L-28.
- **WALLETSET 2×2 wired** (KÝ 27/08 thresholds |Δbal|≥50% · |Δholders|≥5 abs · stress vol≥5× ∨ ret≤-8% OR) — 3 CSV cột + `[WALLETSET: <tag>]` trailer sau `[VERIFY-WALLETSET]`. Anchor SOPH.

## Format Telegram khối CAMPAIGN-PRE (post gói-nhẹ + rev2 3-fix KÝ 27/08)

```
CAMPAIGN-PRE <YYYY-MM-DD>: <N> fires (fw-<M>)
  <SYM1>USDT  [H2]  conf=<LEVEL> (<n_pass>/<n_eval>; N/A: <list>)  H3=<T|F|N/A>
  <SYM2>USDT  [H1]  conf=<LEVEL> (...)  H3=<T|F|N/A>                          # Δ≥+10% accumulation
  <SYM2b>USDT [H1-OUT -X.X%]  conf=<LEVEL> (...)  H3=<T|F|N/A>                # Δ≤-10% distribution (rev2 B2)
  <SYM2c>USDT [H1-OUT -X.X% + H2]  conf=<LEVEL> (...)  H3=<T|F|N/A>           # kho-out + perp-hit
  <SYM3>USDT  [[suppressed:perp]]  conf=<LEVEL> (...)  H3=<T|F|N/A>  [SUPPRESSED n/14 lane=perp]     # rev2 B1
  <SYM4>USDT  [[DQ-SERIAL blocked]]  conf=<LEVEL> (...)  H3=<T|F|N/A>  [DQ-SERIAL] <SYM4> lane=<kho|perp>
  <SYM5>USDT  [H1-OUT -X.X% + H2]  conf=<LEVEL> (...)  H3=<T|F|N/A>  [VERIFY-WALLETSET]              # rev3 |Δ|≥50%/1d kho-out

---
spec_version: v4.0-draft
amendments_applied: GOI-NHE-20260829, V④-RT-2CHỐT-ANALYSIS-20260828, ⑬-COLUMN-MANIFEST-20260826, GOM-RESTRUCT-20260824
cfg-provenance: yaml_md5=59aadeb9280...
  coverage T0.1: n_fire=<x> n_NA=<y> n_warmup=<z> n_eval=<w> / total=<T>
  coverage H1: n_fire=<x> n_NA=<y> n_warmup=<z> n_eval=<w> / total=<T>
  coverage H2: n_fire=<x> n_NA=<y> n_warmup=<z> n_eval=<w> / total=<T>
  coverage H3: n_fire=<x> n_NA=<y> n_warmup=<z> n_eval=<w> / total=<T>
basis: 14d (obs_min=14 signed operator ký 29/08)
vol_source: fapi_k7_fresh
```

## Đêm-1 (pre-wire archive-note) · 27/08 01:45 UTC target=2026-08-26

**Status:** ARCHIVE-ONLY code `e851db50` cũ · KHÔNG counted G6 official.
**Bug đã biết:** `conf=conf=MED (...)` double-prefix · `[[suppressed:perp]]` không có trailer `[SUPPRESSED n/14 lane=perp]`.
**Đã fix ở rev2 (KÝ 27/08):** áp dụng từ đêm-2 trở đi.

```
[MTIME] scratch/gom_h_daily_2026-08-26.csv: 2026-08-27 01:45 UTC
[TELEGRAM BLOCK NGUYÊN VĂN — PRE-WIRE, chấm archive]:
CAMPAIGN-PRE 2026-08-26: 14 fires (fw-139)
  0GUSDT  [H2]  conf=conf=MED (2/3; N/A: -)  H3=F       # bug: double conf=
  ...
  MIRAUSDT  [[suppressed:perp]]  conf=conf=MED (3/3; N/A: -)  H3=F   # bug: no trailer
```

## Đêm-2 (official #1 rev2) · 28/08 01:45 UTC target=2026-08-27

```
[MTIME] scratch/gom_h_daily_2026-08-27.csv: <chờ cron sáng 28>
[MTIME] data/logs/gom_h_daily.log: <chờ>
[CODE MD5] gom_h_daily.py=a260a8ca · tripwire_e2.py=83d0e131 · counter=1c104491 pre-fire
[TELEGRAM BLOCK NGUYÊN VĂN]: <paste khi cron xong>
```

## Đêm-3 (official #2 rev2) · 29/08 01:45 UTC target=2026-08-28

```
[MTIME] scratch/gom_h_daily_2026-08-28.csv: <chờ cron sáng 29>
[MTIME] data/logs/gom_h_daily.log: <chờ>
[CODE MD5] gom_h_daily.py=a260a8ca · tripwire_e2.py=83d0e131 (unchanged)
[TELEGRAM BLOCK NGUYÊN VĂN]: <paste khi cron xong>
```

## Sáng 28/08 verification checklist (đêm-2 rev2 official #1)

- [ ] Syslog `2026-08-28T01:45` có CRON CMD `scripts/gom_h_daily.py`
- [ ] `scratch/gom_h_daily_2026-08-27.csv` mtime = `Aug 28 01:45..01:46` UTC
- [ ] `data/logs/gom_h_daily.log` grew (last entry timestamp `2026-08-28T01:45..`)
- [ ] Telegram khối CAMPAIGN-PRE sent (nếu có fires) · log line `TG-SEND ok=True`
- [ ] Coverage per H match format · basis=14d in
- [ ] **Fix B1 verified:** MIRA-cooldown-hàng có trailer `[SUPPRESSED n/14 lane=perp]` sau `H3=<X>`
- [ ] **Fix B2 verified:** kho-fire hàng nào Δ<0 → `[H1-OUT -X.X%]`, Δ>0 → `[H1]`, CSV cột `h1_direction` in|out
- [ ] **Fix B3 verified:** `data/state/tripwire_e2_counter.json` mỗi token chỉ 1 entry cho 08-27 (không duplicate)
- [ ] **Guard rev3 verified:** kho-out |Δ|≥50%/1d → trailer `[VERIFY-WALLETSET]` (yaml min_abs_delta=0.50); CSV cột `verify_ws_note`
- [ ] **rev4 conf-fix verified:** mẫu số conf hiển thị /4 (không /3), obs_min=14 mọi rolling-vế; ví dụ fire nào full 4-vế pass = HIGH (4/4; N/A: -)
- [ ] **rev4-FINAL yaml single-source verified:** header in `obs_min=14 (source: yaml goi_nhe.obs_min)`
- [ ] **WALLETSET 2×2 wired:** `[WALLETSET: <CONCENTRATED|BROAD-QUIET|BROAD-STRESS>]` trailer sau `[VERIFY-WALLETSET]`; CSV cột `walletset_tag`, `wallet_delta_pct`, `wallet_delta_holders`, `wallet_stress_flag`
- [ ] **ramp-line đầu tiên (rev4-FINAL):** in ramp evaluated `n=?` + có token nào h1_ramp fire/gần-fire không? kỳ vọng ~18 tokens (từ smoke 08-25 h1_ramp_raw=True count)
- [ ] **walletset tag xuất hiện đúng ngưỡng ký:** trailer `[WALLETSET: <tag>]` cho token thỏa (|Δbal|≥50% + |Δholders|≥5) hoặc (stress vol≥5×/ret≤-8% OR); anchor SOPH KHÔNG tag 2×2 (holders Δ=1<5)
- [ ] **CODE-FREEZE VPS:** md5 gom_h_daily.py + yaml TRƯỚC/SAU cron identical (cấm SCP đến 29/08 01:45 UTC)
- [ ] Conf format: `conf=<LEVEL> (n_pass/n_eval; N/A: <list>)` — không double `conf=` prefix
- [ ] CSV md5 khớp log `[OUTPUT]` line

## Sáng 29/08 verification checklist (đêm-3 rev2 official #2)

Same as sáng 28/08 + target 2026-08-28. Verify tripwire counter accumulates purely (no dedup collisions across 2 days).

## KHỚP nghĩa với gate_defs §3 gói-nhẹ 5 điểm

1. **Compose OR** ✓ — code `h1_raw_gn OR h2_raw_gn` (không AND)
2. **H1 hai trigger** — step OK · ramp stub (h1_ramp_raw wire chưa xong, chờ balance[D-14] impl)
3. **Tripwire 0.4** — runtime check chưa wire, chờ regression cron
4. **TP-grading 50%** — giữ (§5 luật chấm)
5. **[6/8] chấm T-④ re-render** — verify G3 output = **8/9 PASS** (89%)

## Refs
- gate_defs md5 `f275c53c`
- bot-signals sha `490a8f49` (G1 spec merge)
- whale_data commit sequence:
  - `a62e194` G1-SPEC + G2-CODE (compose OR + conf-labeler + DQ-SERIAL)
  - G3-G4-G5 pending commit
- Registry wrapper day-27 EOD (r1/r2/r3-arm + er8-guards + state-store) commit `9c8df0f`
- Wrapper day-28 (Telegram + runner + fixture) — pending merge sau ANALYSIS ký

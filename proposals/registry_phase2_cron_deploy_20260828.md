# Registry Phase-2 Cron Deploy Plan — 5 dòng · [TRÌNH KÝ, KHÔNG CHẠY]

**Status:** DRAFT · CHỜ operator KÝ · phase-2 §E-R go-live registry (cost-of-delay BTR+HEMI).
**Ngày soạn:** 2026-08-28
**Ref:** `proposals/unhedge_registry_spec.md` §E-R8 falsifier forward (chấm 30d từ go-live) · `screen_thresholds.yaml` `unhedge_registry` block (E-R4b v1.1 signed 20/08).

## 5 DÒNG DEPLOY

```
GIỜ    : 50 01 * * *  (01:50 UTC daily; sau gom_h 01:45 + phase_tag 01:30 + freshwatch 01:20)
INPUT  : data/export/freshwatch_daily_<latest>.csv + data/state/hedge_watchlist_<target_D-1>.json
         + docs/proposals/unhedge_registry_spec.md §E-R triggers/gates YAML md5-pinned
OUTPUT : data/registry/unhedge_registry_<YYYYMM>.csv (append-only)
         + data/state/unhedge_registry_snapshot_<target_D-1>.json (state per token)
         + Telegram §E-R alert khối riêng "REGISTRY (un-hedge/re-arm/ignite)"
GUARD  : go-live ≠ verify: --dry-run default (in "SẼ open/close/re-arm N rows", KHÔNG ghi
         file, KHÔNG send Telegram); --live flag → verify §E-R8 falsifier forward guard:
           (a) reg%_weekpeak ≤25% (nếu >25% tuần bất kỳ 30d → auto-block Telegram, ANALYSIS-ONLY)
           (b) MFE_k7 ≥ +10% cho ≥50% wave-2+ alerts trong 30d (nếu <50% → auto-block)
           (c) alert E-R3 ≤40% tổng Telegram/tuần
ROLLBACK: (i) --live flag remove → chỉ dry-run; (ii) rollback file: keep 30d bản CSV/JSON
         cũ trong data/registry/archive/; (iii) nếu §E-R8 (a)/(c) trip → auto ANALYSIS-ONLY
         mode (in report, không send Telegram) 30d chờ operator ký resume; miss-audit ③
         pump ≥30%/2d không alert → autopsy ≤48h bắt buộc, log data/logs/registry_autopsy.log
```

## Semantic bổ sung (không phải "5 dòng" nhưng cần cho ký)

**Trigger E-R1** (open row):
- (a) UN-HEDGE-DRIFT: div_avg3 drift ≥+0.15 từ episode min trong ≤7d
- (b) POS-HOLD: pos_r ≥ 90% × avg5(pre-event)
- (c) PX-HOLD: px ≥ 85% × hedge_start_px

**Trigger E-R3** (IGNITE):
- OI +30%/2d ∧ vol ≥5×med14 ∧ breakout ≥15%/range14d

**Trigger E-R4b** (RE-ARM v1.1):
- r1: days_since_ignite ≥14
- r2: px_now/local_low ≥1.15
- r3: oi_now/oi_local_low ≥1.30

**Close E-R4:**
- RE-HEDGED: new episode div_avg3 ≤0.5 ≥5d
- EXPIRED: 90d không ignite

## Sign-off checklist

- [ ] Operator KÝ deploy plan (5 dòng + semantic recap)
- [ ] DEV viết `scripts/registry_daily.py` per skeleton (không có sẵn, cần task riêng)
- [ ] Smoke test dry-run trên VPS: expected "SẼ open X close Y re-arm Z", 0 file writes
- [ ] `--live` first run + verify §E-R8 guards trip check
- [ ] Cron install VPS: `crontab -e` append `50 1 * * *` line
- [ ] Miss-audit autopsy log path setup: `data/logs/registry_autopsy.log`
- [ ] Case BTR + HEMI review sau 30d forward (chấm §E-R8 falsifier)

## Cost-of-delay note

- **BTR** D0 08-26 (fresh): registry mở row lần đầu = 08-27 nếu cron go-live tối nay → miss wave-1 08-11 (đã qua) nhưng bắt được ignite forward.
- **HEMI** D0 08-15 (11d): registry có thể bắt được RE-ARM window (r1 ≥14d = 08-29) nếu deploy trước 08-29.
- Delay > 08-29 → miss HEMI r1 first cycle.

## Refs
- unhedge_registry_spec.md §E-R1..§E-R8 (SIGNED v1.0 + E-R4b v1.1 20/08)
- screen_thresholds.yaml `unhedge_registry` block (canonical params)
- L-53 captive-vùng-giữa doctrine (target loài)
- L-54 INTEL ≠ ENTRY (registry không override entry rules)

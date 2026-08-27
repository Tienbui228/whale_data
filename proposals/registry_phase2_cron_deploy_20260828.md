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

- [x] Operator KÝ deploy plan (5 dòng + semantic recap) — 28/08
- [x] Operator KÝ scope wrapper (i): lib engine only, wrapper 1.6d — 28/08
- [x] DEV extend lib r1/r2/r3-arm helpers (`lib/registry_events.py` commit b081480) — 26/08 EOD
- [x] DEV §E-R8 guards runtime (`lib/registry_er8_guards.py`) — day 27 EOD
- [x] DEV State store JSON (`lib/registry_state_store.py`) — day 27 EOD
- [ ] DEV Telegram module với assertion (per operator plan (b) 27/08) — day 28
- [ ] DEV runner glue `scripts/registry_daily.py` FULL (replace stub) — day 28
- [ ] DEV fixture L-58 5/5 wrapper — day 28
- [ ] Smoke test dry-run VPS: expected "SẼ open X close Y re-arm Z", 0 file writes — day 28
- [ ] `--live` first run + verify §E-R8 guards trip check — sáng 29/08
- [ ] Cron 50 01 UTC đã install (registry_daily.py stub) — 26/08
- [ ] Miss-audit autopsy log path setup: `data/logs/registry_autopsy.log`
- [ ] Case BTR + HEMI review sau 30d forward (chấm §E-R8 falsifier)

## [PLAN UPDATE 27/08 per operator (a)(b) — post FULL merge luật ANALYSIS]

### (a) TESTA expected TÍNH LẠI + snapshot pin

Khi wrapper FULL merge (`scripts/registry_daily.py` real + state store wire):
1. **TESTA expected phải TÍNH LẠI** trên wrapper trước khi gate chấm (not carry-forward
   từ pre-merge fixture)
2. **Cùng snapshot pin** với mọi row registry — KHÔNG nửa cũ nửa mới (luật ANALYSIS)
3. Fixture BTR-positive (đã có), TESTA-negative-post-wire (chờ), + PENDING-STATE-WIRE
   auto-flip PASS khi state store lands
4. Snapshot pin = single YAML md5 + single lib commit sha + single fixture md5 per gate run

### (b) Telegram module — assertion tầng-alert

Telegram module (day 28 build) BẮT BUỘC:
1. Assertion: `trigger event` ∧ `tg_send trace trong log` (log format: `[YYYY-MM-DDTHH:MM:SSZ]
   TG-SEND sym=<X> event=<E> ok=<True|False> reason=<err|OK>`)
2. Fixture kiểm được: mock TG endpoint → verify log line matches (trigger fire → send call)
3. Fail-loud: nếu trigger fire nhưng tg_send skip (env var missing / API fail) → log WARN
   + increment counter cho §E-R8 ③ miss-audit tracking
4. Test cases:
   - trigger + env set → tg_send True → log OK line
   - trigger + env missing → tg_send skip → log WARN
   - trigger + API 5xx → tg_send False → log WARN + counter++

## Cost-of-delay note

- **BTR** D0 08-26 (fresh): registry mở row lần đầu = 08-27 nếu cron go-live tối nay → miss wave-1 08-11 (đã qua) nhưng bắt được ignite forward.
- **HEMI** D0 08-15 (11d): registry có thể bắt được RE-ARM window (r1 ≥14d = 08-29) nếu deploy trước 08-29.
- Delay > 08-29 → miss HEMI r1 first cycle.

## Refs
- unhedge_registry_spec.md §E-R1..§E-R8 (SIGNED v1.0 + E-R4b v1.1 20/08)
- screen_thresholds.yaml `unhedge_registry` block (canonical params)
- L-53 captive-vùng-giữa doctrine (target loài)
- L-54 INTEL ≠ ENTRY (registry không override entry rules)

# Đêm-4 C Report · target=2026-08-29 · cron fire 2026-08-30 01:45 UTC + CATCH-UP nộp

**Nguồn:** VPS 5.223.67.21 · SSH pull 2026-08-30 10:56 UTC · Đêm-4 vẫn chạy CATCH-UP mode (laptop tắt lúc 08:00 VN 30/08 · relay Windows Task Scheduler miss).

---

## 5 MỐC

| # | mốc | giá trị |
|---|---|---|
| 1 | target_date | 2026-08-29 |
| 2 | n_symbols / store_rows | 139 / **41,520** |
| 3 | GOM-H FIRE count | **2 / 139** (PROVEUSDT [H2] MED · RESOLVUSDT [H2] MED) |
| 4 | yaml md5 VPS cron | `3d11e572d77a657a2e5638dd6027e3a8` (post batch-4 SCP) |
| 5 | CSV md5 | — (log trailing chưa flush · derive từ latest scratch/gom_h_daily_2026-08-29.csv) |
| 4b | CODE md5 gom_h_daily.py VPS | `ccf504df81c25a41bdcc0a3516a73d5b` (post WIRE-TRIPWIRE-V2 · = LOCAL ✓) |

Coverage (per-H):
- T0.1 = 8 / 0 / 139 / 139
- **H1 = 0 / 139 / 0 / 139** ← **ALL N/A theo hợp đồng** (snapshot 2026-08-30 MISSING · laptop tắt 01:00 UTC 30/08 · Windows Task Scheduler sync miss)
- H2 = 13 / 0 / 139 / 139
- H3 = 0 / 0 / 139 / 139

## Telegram nguyên văn (CAMPAIGN-PRE 2026-08-29 · 2 fires + suppressed context · SENT qua CATCH-UP)

```
CAMPAIGN-PRE 2026-08-29: 2 fires (fw-139)
  0GUSDT       [[suppressed:perp]]  conf=MED (3/4)  H3=F  [SUPPRESSED 3/14 lane=perp]
  BASUSDT      [[suppressed:perp]]  conf=MED (2/4)  H3=F  [SUPPRESSED 3/14 lane=perp]  [WALLETSET: BROAD-STRESS · ret=-17.7%]
  BTRUSDT      [[suppressed:perp]]  conf=LOW (0/4)  H3=F  [SUPPRESSED 2/14 lane=perp]  [WALLETSET: BROAD-STRESS · vol=164.5x]
  ERAUSDT      [[suppressed:perp]]  conf=HIGH (4/4) H3=F  [SUPPRESSED 3/14 lane=perp]
  FUSDT        [[suppressed:perp]]  conf=MED (2/4)  H3=F  [SUPPRESSED 3/14 lane=perp]
  HYPERUSDT    [[suppressed:perp]]  conf=HIGH (4/4) H3=F  [SUPPRESSED 1/14 lane=perp]
  LAUSDT       [[suppressed:perp]]  conf=HIGH (4/4) H3=F  [SUPPRESSED 4/14 lane=perp]
  OPNUSDT      [[suppressed:perp]]  conf=HIGH (4/4) H3=F  [SUPPRESSED 3/14 lane=perp]
  PROVEUSDT    [H2]  conf=MED (2/4)  H3=F   ← FIRE
  RESOLVUSDT   [H2]  conf=MED (3/4)  H3=F   ← FIRE
  SAHARAUSDT   [[suppressed:perp]]  conf=MED (2/4)  H3=F  [SUPPRESSED 3/14 lane=perp]
  SOPHUSDT     [[suppressed:perp]]  conf=MED (3/4)  H3=F  [SUPPRESSED 4/14 lane=perp]
  ZAMAUSDT     [[suppressed:perp]]  conf=LOW (1/4)  H3=F  [SUPPRESSED 3/14 lane=perp]

# [LEGACY-COUNTER · pre-compose sub-metric — Telegram FINAL fire count = canonical] (L-59)
tripwire FP-rate=0.428 [TRIP] · raw=n_FP=43 (n_FP=43/n_TP=7/n_PEND=35 · exposure=58d declared (2026-06-26..2026-08-22) · read 2026-06-26..2026-08-21=57d)
  ↳ 7 TP control-nhiễm (round-trip |ret|<30%) — loại khỏi tử theo E2-metric 31/08
# tripwire_v2 flag action: TRIP-FLAGGED
```

**Send status:** manual CATCH-UP 10:57 UTC 30/08 · HTTP 200 · 1 part · hash `9b1753c6deee` (idempotent-hash marked · run cron thật đêm nay sẽ SKIP không double).

---

## DIAG 3 dòng (ngày-laptop-tắt)

**(a) Snapshot ngày target = KHÔNG ẢNH HƯỞNG target=08-29** — snapshot `2026-08-29.json` mtime `Aug 29 01:01` ĐỦ · nhưng snapshot `2026-08-30.json` (D · cần cho H1 adapter ingest 2026-08-30 rows=0) **MISSING** · **H1 coverage = 0 fire / 139 N/A theo hợp đồng (KHÔNG sự cố)** · module vẫn chạy H2/H3 (13 H2 fires + 0 H3 fires per coverage).

**(b) Task Scheduler "Run task as soon as possible after missed":** kiểm ngay:
- `TgRelayGomH` : **ĐÃ BẬT** `StartWhenAvailable=True` ✓ (Set-ScheduledTask hoạt · UserId=Hello RunLevel=Limited)
- `nansen_sync_vps` : **ACCESS DENIED** khi Set-ScheduledTask (task ghi settings khóa · cần Admin PowerShell hoặc user re-register) — TG-RELAY-V2 VPS-native (điều khoản B mới) sẽ làm redundancy Windows-side
- `FreshWatch-SnapshotWriter` : `StartWhenAvailable=True` ✓ (đã có sẵn)

**(c) State/cooldown VPS KHÔNG ảnh hưởng:** `tripwire_e2_counter.json` mtime `Aug 30 01:45` (cron ghi state đúng · counter cập nhật per fire); `tripwire_e2_v2_TRIPPED.flag` mtime `Aug 30 01:45` (WIRE-V2 flag write đúng). Cron chạy sạch · state đúng · Đêm-4 verify WIRE-TRIPWIRE-V2 sống từ cron thật (trailing 3 dòng in đúng · # tripwire_v2 flag action: TRIP-FLAGGED).

---

## STALENESS-MAP · 3 đêm gần nhất (input gom_h)

| input | Đêm-2 (28/08) | Đêm-3 (29/08) | Đêm-4 (30/08) | mtime pattern |
|---|---|---|---|---|
| `nansen_snapshots/YYYY-MM-DD.json` | `08-28 01:00:18` | `08-29 01:01:35` | **MISSING** | Windows bot ~01:00-01:01 UTC · **laptop-dependent** |
| `data/export/freshwatch_daily_2026-08.csv` | — | — | `08-30 01:20:00` | cron 01:20 UTC (VPS post-export shell) · **stable** |
| `screen_thresholds.yaml` | — | `08-29 02:30:54` (SCP batch-4) | (unchanged) | LOCAL SCP · **stable post-SCP** |
| `data/logs/collect_daily_metrics.log` | — | — | `08-30 00:40:04` | cron 00:35 UTC · **stable** |
| `data/logs/collect_spot_daily.log` | — | — | `08-30 01:05:08` | cron 01:05 UTC (post batch-4 wire) · **stable** |
| `data/logs/collect_alpha_daily.log` | — | — | `08-30 02:01:11` | cron 02:00 UTC · **AFTER gom_h** (không blocking) |

### Latest-mtime input BEFORE gom_h 01:45 UTC
- freshwatch_daily CSV: `01:20` ← latest blocker
- watchlist_log: `01:40` (via cron 01:40 UTC)
- **Max blocker: 01:40 UTC** → gom_h slot HIỆN TẠI `01:45` = 5 phút buffer

### SHIFT proposal (Đêm-5)
Nếu **watchlist (01:40)** giữ slot cố định, có thể **shift gom_h → 01:26 UTC** (chuông về 08:26 VN):
- ĐK tiên quyết: watchlist cron dời trước gom_h · hoặc gom_h không phụ thuộc watchlist output
- Verify: grep `gom_h_daily.py` cho `watchlist_*` reads → nếu KHÔNG → shift được
- Nếu CÓ: phải dời watchlist trước · hoặc giữ 01:45

**⚠ CHECK cần trước SHIFT:** grep gom_h source deps để confirm không dùng watchlist output. Chưa làm turn này · để trước Đêm-5.

---

## Lịch DỜI (post directive TG-RELAY-V2 VPS-NATIVE 30/08)

**Đêm này = biến ops-level (TG-RELAY-V2 VPS port)** → shift 1 đêm mỗi biến sau:

| đêm | date cũ | date mới | biến |
|---|---|---|---|
| Đêm-4 (verify) | 30/08 01:45 UTC | 30/08 (đã chạy · CATCH-UP nộp) | v1 nguyên trạng ✓ |
| **Đêm ops** | (không có) | **30/08 hôm nay** | **TG-RELAY-V2 VPS-NATIVE port** |
| Đêm-5 (SHIFT) | 31/08 | **01/09** | STALENESS-MAP validate + gom_h shift 01:26 UTC (nếu deps OK) |
| Đêm-6 (RENDER-V2 deploy) | 01/09 | **02/09** | render-v2 code + R3 sort-RIPE + fixture F1 5-pin |
| Đêm-6+7 R4 verify | 01-02/09 | **02-03/09** | 2 đêm cron render-v2 |

Một-biến-một-đêm giữ.

---

## Relay --catch-up flag DIFF (~7 dòng · đã apply LOCAL Windows)

```diff
--- a/tg_relay_gom_h.py
+++ b/tg_relay_gom_h.py
@@ def main(test_mode: bool = False) -> int:
-def main(test_mode: bool = False) -> int:
-    _log(f"[TG-RELAY START] test_mode={test_mode} · config={dict((k,v) for k,v in cfg.items() if k != 'vps_host')}")
+def main(test_mode: bool = False, catch_up: bool = False) -> int:
+    _log(f"[TG-RELAY START] test_mode={test_mode} · catch_up={catch_up} · config={dict((k,v) for k,v in cfg.items() if k != 'vps_host')}")

@@ Guard (a) staleness
-    if not test_mode:
+    if not test_mode and not catch_up:
         stale_ok, stale_reason = check_staleness(meta_fetch, meta_extract)
         if not stale_ok:
             ...
             return 4
+    elif catch_up:
+        _log(f"[CATCH-UP] STALENESS-TARGET bypassed · manual override for missed schedule")

@@ Format message
-    prefix = "[TEST-3 · SMOKE BLOCK]\n" if test_mode else ""
+    if test_mode:
+        prefix = "[TEST-3 · SMOKE BLOCK]\n"
+    elif catch_up:
+        prefix = f"[CATCH-UP {meta_extract.get('target_date','?')}]\n"
+    else:
+        prefix = ""

@@ CLI entry
-    test = "--test" in sys.argv
-    sys.exit(main(test_mode=test))
+    test = "--test" in sys.argv
+    catch = "--catch-up" in sys.argv
+    sys.exit(main(test_mode=test, catch_up=catch))
```

Idempotent-hash flow GIỮ nguyên (mark_sent chỉ khi all_ok=True) · run cron thật đêm sau sẽ SKIP không double.

---

## (B) TG-RELAY-V2 VPS-NATIVE · THI HÀNH XONG ✓

**Token:** `/root/.env_tg` (chmod 600 · outside repo · gitignore verify passed) · bot Make Money With Crypto reuse từ bot-signals config.yaml (zero secret mới).

**Script:** `/root/Data_back_test/whale_data/scripts/tg_relay_gom_h.py` md5 `7b354f079b1c6d034999ffd66917a0fe` · port từ Windows f3ad4f10 + guard GIỮ NGUYÊN:
- STALENESS-TARGET (30min · target D-1)
- plain-text (không Markdown)
- split-ranh-dòng + BẤT BIẾN trailing-3-dòng-tin-cuối
- idempotent-hash full_text + mark_sent chỉ khi all_ok=True
- **raw-save response body → `data/logs/tg_relay_raw.log` (L-59)**
- --catch-up bypass staleness (manual)
- --test test mode
- **Read log LOCAL VPS file system** (không SSH · zero network overhead)

**Cron VPS installed:** `55 1 * * * cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/tg_relay_gom_h.py >> data/logs/tg_relay.log 2>&1` — Đêm-5 01:55 UTC first live run.

**[TEST-VPS] send:** target=2026-08-29 · has_tripwire=True · has_flag=True · HTTP 200 · resp_len=2432 · hash `9b1753c6deee` ✓

**SINGLE-SENDER (bài học NANSEN-SINGLE-CALLER) enforced:**
- Windows Task Scheduler `TgRelayGomH` state=**Disabled** ✓
- Windows script renamed `tg_relay_gom_h.py.DISABLED-20260830` (cold-backup)
- VPS cron = sole sender · state hash một chỗ (`/root/Data_back_test/whale_data/data/state/tg_relay_last.json`)

## Wait-state · sau report này
- **Đêm-5 (01/09) 01:55 UTC:** VPS cron TG-RELAY-V2 first live · sáng ~08:55 VN Telegram GOM-H đầu tiên qua VPS-native path
- Đêm-5 SHIFT deferred → **02/09** (STALENESS-MAP validate · gom_h shift 01:26 UTC nếu deps OK)
- Đêm-6 RENDER-V2 deploy → **03/09** · Đêm-6+7 R4 verify → **03-04/09**
- Follow-up (không chặn): nansen_sync_vps StartWhenAvailable=True (Admin PS · hoặc user re-register) — VPS-relay redundancy đã giải quyết pipe-level

**Idempotent guard:** cron VPS 01:55 tối nay sẽ SKIP block target=08-29 (hash `9b1753c6deee` đã mark bởi CATCH-UP + [TEST-VPS]). Đêm-6 sẽ là first real production run với target mới (08-30 hoặc 08-31 tùy khi user bật laptop lại cho snapshot sync).

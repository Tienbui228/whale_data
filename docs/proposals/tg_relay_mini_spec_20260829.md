# TG-RELAY mini-spec · CHỜ CHỮ operator "ok tg-relay" · KÝ 29/08 · zero-code-yet

**Status:** DRAFT-READY-FOR-SIGN · zero wire hiện tại · 5 dòng spec + điểm cắm cron.
**Rationale:** GOM-H sender UNWIRED-BY-OMISSION (ruling operator 29/08 · Đêm-3 diag). Đề xuất tái dùng đồ có sẵn Windows-side (không SCP secret mới lên VPS).

## 5 DÒNG SPEC

1. **Cron cắm Windows Task Scheduler 01:55 UTC daily** (sau gom_h VPS 01:45 UTC + 10 phút buffer cho log flush).
2. **Fetch:** SSH pull tail-N Telegram-block + trailing tripwire line từ VPS `/root/Data_back_test/whale_data/data/logs/gom_h_daily.log` — grep từ separator `[TELEGRAM BLOCK — CAMPAIGN-PRE ...]` cuối cùng đến separator kế tiếp.
3. **Send:** POST `https://api.telegram.org/bot<TOKEN>/sendMessage` dùng **bot-token watchlist sẵn có** (LOCAL `.env` Windows-side · zero secret mới trên VPS · zero secret mới trong repo).
4. **Fail semantics (L-66):** exit code ≠ 0 hoặc HTTP ≠ 200 → ghi `data/logs/tg_relay.log` một dòng lỗi + append dòng lỗi vào **chính report sáng** (Đêm-4 report header) — không im.
5. **Idempotent guard:** hash Telegram-block · nếu hash trùng lần gửi gần nhất trong `data/state/tg_relay_last.json` → SKIP (tránh double-send khi Task Scheduler retry).

## ĐIỂM CẮM CRON

Windows Task Scheduler entry (schtasks style):
```powershell
schtasks /Create /SC DAILY /TN "TgRelayGomH" /ST 01:55 /RL LIMITED /TR ^
  "python `"D:/Check onchain fresh wallets/tg_relay_gom_h.py`""
```

## LOCATION

- **Script:** `D:/Check onchain fresh wallets/tg_relay_gom_h.py` (local Windows · cùng nhà với Nansen bot Task Scheduler khác)
- **Env:** local `.env` — reuse `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` từ watchlist bot sẵn có
- **State:** local `data/state/tg_relay_last.json` (hash last-sent) + log `data/logs/tg_relay.log`
- **VPS side:** ZERO change (Windows chỉ ĐỌC log · không ghi lại VPS)

## FLOW

```
Windows 01:55 UTC → SSH pull tail gom_h_daily.log → extract Telegram block
   → hash check idempotent → POST bot API → success/log OR fail/log+alert next-report
```

## VERIFY POST-DEPLOY

- Đêm-4 (30/08 01:55 UTC) → Telegram channel nhận CAMPAIGN-PRE 2026-08-29 block
- `data/logs/tg_relay.log` mỗi ngày 1 dòng success/fail
- Nếu VPS SSH down 15s timeout → fail-log + notify Đêm-5 report header

## Ref cross-links

- Đêm-3 diag: [dem3_c_report_20260829.md](../handover/dem3_c_report_20260829.md) commit `f88bc5b`
- CLAUDE.md H1-đường-(a) doc-fix 29/08 (sync-time thực tế ~01:00 · last_run.json path fix)
- SCP-PLAN (đợt-1 batch) không phụ thuộc TG-RELAY · độc lập triển khai

## CHỜ CHỮ

Operator "ok tg-relay" → agent scaffold script per spec 5 dòng + cắm Task Scheduler local → verify Đêm-4.

**Không tự deploy · không tự tạo file script · không chạm secret · không SCP.** Draft này chỉ là spec-giấy chờ chữ.

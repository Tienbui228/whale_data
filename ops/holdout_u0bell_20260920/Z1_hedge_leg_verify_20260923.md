# Z1 · Chân HEDGE trong cổng 6/6 · IN từ CODE · KHÔNG kết luận

Luật DEV vòng 10: mọi mốc giờ/cửa sổ trong báo phải in TỪ CODE (print biến), không tính tay.
NGUỒN print variables: `_probe_z1_window_print_20260923.py`

Doctrine áp: #16 mọi bảng NGUỒN · #17 code identity kiểm bằng file:dòng.

---

## Z1.a · Master xác định chân "watchlist full/sent" bằng gì

### 1. full_pair check (`master_preview_send.py:322-329`)

```python
full_pair_status = {}
for r in renderers:
    txt = art_dir / f"tg_final_{r}_{target}.txt"
    jsonl = art_dir / f"tg_final_{r}_{target}.jsonl"
    if txt.exists() and jsonl.exists():
        n_rows = sum(1 for _ in open(jsonl, encoding="utf-8"))
        full_pair_status[r] = {"txt": txt.stat().st_size, "jsonl_rows": n_rows}
    ...
```

| item | value | NGUỒN |
|------|-------|-------|
| txt path | `data/artifacts/tg_final_watchlist_<T>.txt` | line 323 |
| jsonl path | `data/artifacts/tg_final_watchlist_<T>.jsonl` | line 324 |
| gate | BOTH exist → OK · either missing → `{"missing": True}` | line 325-337 |

### 2. sent priority-1 · bell_journal (`master_preview_send.py:342-349`)

```python
if bell.exists():
    for line in bell.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            if e.get("target_date") == target and e.get("ok") and e.get("renderer") in sent_leg:
                sent_leg[e["renderer"]] = {"ok": True, "source": "bell_journal", ...}
```

| item | value | NGUỒN |
|------|-------|-------|
| file đọc | `data/logs/bell_journal.jsonl` | line 342 |
| filter | `e["renderer"] == "watchlist" AND e["target_date"] == target AND e["ok"] == True` | line 346 |
| action | Set `sent_leg["watchlist"]["ok"] = True` với source="bell_journal" | line 347-350 |

### 3. sent priority-2 · log-grep fallback (`master_preview_send.py:362`)

```python
log_map = {
    ...
    "watchlist": (REPO / "data/export/watchlist_cron.log",
                   rf"\[SENT\] watchlist ok=True.*target={target}", "target"),
}
```

| item | value | NGUỒN |
|------|-------|-------|
| file đọc | `data/export/watchlist_cron.log` | line 362 |
| regex (target=09-22 example) | `'\\[SENT\\] watchlist ok=True.*target=2026-09-22'` | printed from code |
| mark_type | `"target"` · window window_hours=30 | line 375 |

## Z1.b · HEDGE v2 (HEDGE_V2=1) có sinh ĐÚNG thứ đó không

### Common tail (chạy CHUNG cho cả HEDGE_V2 và đường cũ) · `watchlist_daily.py:711-732`

```python
# Line 713-715
print(f"[SENT] watchlist ok={ok_tg} HTTP {'200' if ok_tg else 'X'} hash={_tg_hash} target={target}",
      file=sys.stderr)
# Line 716-719 · log_bell
_lb("watchlist", target, "old", ok_tg, 200 if ok_tg else 0, None, tg_out)
# Line 720-732 · dump_as_sent · CHỈ nếu ok_tg
if ok_tg:
    _das("watchlist", target, tg_out, channel="old")
```

### Sinh từng thứ (byte-format so đường cũ):

| item | file:dòng ghi | format · byte-identical đường cũ? |
|------|---------------|-----------------------------------|
| `[SENT] watchlist ok=... hash=... target=...` cron log | `watchlist_daily.py:713-715` (stderr → cron log) | **IDENTICAL** · common tail dùng chung |
| `bell_journal.jsonl` entry | `watchlist_daily.py:718` `log_bell(...)` | **IDENTICAL** · common tail dùng chung (renderer="watchlist" · channel="old" · body=tg_out) |
| `tg_final_watchlist_<T>.txt` + `.jsonl` | `watchlist_daily.py:725` `dump_as_sent(...)` | **IDENTICAL** · common tail dùng chung · CHỈ nếu ok_tg=True |
| **NEW** · `hedge_v2_journal.jsonl` entry | `watchlist_daily.py:686-688 or 697-699` → `hedge_v2.py:915-932` `write_hedge_journal` | **KHÔNG có bên đường cũ** · **master KHÔNG đọc file này** · CHỈ HEDGE_V2 path ghi |
| **NEW** · `hedge_registry_<T>.csv/.md5` | `hedge_v2.py:843-877` `write_audit_csv` | **KHÔNG có bên đường cũ** · master KHÔNG đọc |
| **NEW** · `hedge_v2_first_night.marker` (nếu ok_tg + errata) | `watchlist_daily.py:701-705` | **KHÔNG có bên đường cũ** · master KHÔNG đọc |

**So byte-format cụ thể · dòng [SENT] watchlist target 09-22 đêm 24 hôm nay 01:40 (đường cũ):**

```
[SENT] watchlist ok=True HTTP 200 hash=bb53293543ad target=2026-09-22
```

**Nếu HEDGE_V2=1 chạy đêm sau:** dùng CHÍNH lệnh print đó (line 713-715) → format identical, chỉ `hash` sẽ khác (hash md5 của body HEDGE khác body v1.4).

## Z1.c · Hai kịch bản (đọc code · không chạy)

### Scenario A · HEDGE v2 gửi OK

**Đường đi (watchlist_daily.py):**

| step | file:dòng | action |
|------|-----------|--------|
| 1. compose | `watchlist_daily.py:674-675` → `hedge_v2.py:668-822 compose_body` | body ← composed |
| 2. u7_gate | `watchlist_daily.py:683` → `hedge_v2.py:895-910` | `ok_u7=True` (n ≤ 4096) |
| 3. send | `watchlist_daily.py:693` → `send_telegram(tg_out)` | HTTP 200 → `ok_tg=True` |
| 4. hedge_v2_journal ghi ok=True | `watchlist_daily.py:697-699` → `hedge_v2.py:915-932` | `write_hedge_journal(ok=True)` |
| 5. marker ghi (nếu errata) | `watchlist_daily.py:701-705` | `_marker_p.write_text(target)` |
| 6. [SENT] marker stderr | `watchlist_daily.py:713-715` | `[SENT] watchlist ok=True hash=... target=...` |
| 7. log_bell → bell_journal | `watchlist_daily.py:718` | entry `renderer=watchlist target=T ok=True` |
| 8. dump_as_sent → artifacts | `watchlist_daily.py:725` | writes `tg_final_watchlist_<T>.txt/.jsonl` |

**Master reads (compute_night_verdict):**

| check | source | result |
|-------|--------|--------|
| full_pair `tg_final_watchlist_<T>.txt/.jsonl` | `master_preview_send.py:323-329` | **BOTH EXIST** (step 8) → `{"txt": size, "jsonl_rows": count}` ✓ |
| bell_journal `renderer=watchlist ok=True target=T` | `master_preview_send.py:346` | **MATCH** (step 7) → `sent_leg["watchlist"] = {"ok": True, "source": "bell_journal"}` ✓ |

→ **Chân watchlist FULL/SENT · full_pair OK · sent OK** · master đếm 6/6 chân · verdict = KHÔNG-KÍCH nếu unk_sent=0.

### Scenario B · HEDGE v2 gửi FAIL (TG-SEND-FAIL or U7-BLOCKED)

**B1 · U7 blocked (body > 4096):**

| step | file:dòng | action |
|------|-----------|--------|
| 1. compose | line 674-675 | body |
| 2. u7_gate | line 683 → hedge_v2.py:905-906 | `ok_u7=False · reason="U7-BLOCKED-LEN"` |
| 3. hedge_v2_journal ghi ok=False | line 686-688 → hedge_v2.py:915-932 | `write_hedge_journal(ok=False, fail_reason="U7-BLOCKED-...", leg_fail_label="KÍCH-vì-chân-HEDGE")` |
| 4. `[HEDGE_V2 U7-BLOCKED]` stderr | line 689 | log entry |
| 5. ok_tg=False | line 691 | KHÔNG gọi send_telegram |
| 6. [SENT] marker stderr | line 713-715 | `[SENT] watchlist ok=False hash=... target=...` |
| 7. log_bell ok=False | line 718 | entry `renderer=watchlist target=T ok=False` |
| 8. dump_as_sent | line 721 `if ok_tg:` | **SKIPPED** (ok_tg=False) |

**B2 · send_telegram trả False (TG API 400/500):**

| step | file:dòng | action |
|------|-----------|--------|
| 1-2. compose + u7_gate | | OK |
| 3. send_telegram | line 693 | `ok_tg=False` |
| 4. hedge_v2_journal ok=False | line 697-699 | `write_hedge_journal(ok=False, fail_reason="TG-SEND-FAIL", leg_fail_label="KÍCH-vì-chân-HEDGE")` |
| 5. marker | KHÔNG ghi (line 701 `if ok_tg and _errata:`) | |
| 6-7. common tail | line 713-718 | `[SENT] ok=False` + log_bell ok=False |
| 8. dump_as_sent | line 721 | **SKIPPED** |

**Master reads (cả B1 và B2 giống nhau):**

| check | source | result |
|-------|--------|--------|
| full_pair | line 323-329 | **artifacts MISSING** (dump_as_sent skipped) → `{"missing": True}` |
| bell_journal filter `e["ok"] == True` | line 346 | entry có ok=False → **KHÔNG MATCH** · sent_leg["watchlist"] giữ `{"ok": False}` |
| Log-grep `\[SENT\] watchlist ok=True.*target={target}` | line 362 | cron log có `ok=False` · KHÔNG có `ok=True` → **NO MATCH** · sent_leg unchanged |

→ **Chân watchlist MISSING** (`n_full=5/6`) và **sent_leg["watchlist"].ok=False** (`n_sent=5/6`)
→ `missing_legs=["watchlist"]` · verdict = **KÍCH**
→ Master SKIP standing bell · STUCK-BELL alert

**⚠ Label "KÍCH-vì-chân-HEDGE":**
- `hedge_v2.py:928` `leg_fail_label = "KÍCH-vì-chân-HEDGE"` GHI VÀO `hedge_v2_journal.jsonl` (line 913 path)
- **Master (`compute_night_verdict`) KHÔNG đọc `hedge_v2_journal.jsonl`** — chỉ đọc `bell_journal.jsonl` và `master_preview.log`
- Verdict-file `dem0_lan2_verdict.json` KHÔNG có label "KÍCH-vì-chân-HEDGE" · chỉ có `missing_legs=["watchlist"]`
- **Wire label vào verdict CHƯA IMPLEMENT** · nợ γ+ · fix sau khi HEDGE_V2 ổn định

## Cửa sổ mốc giờ (in từ code · Z1.a companion)

**NGUỒN:** `python3 _probe_z1_window_print_20260923.py` (chạy 23/09 UTC · md5=`(local file)`)

```
target=2026-09-21
  cron_close(T)      = 2026-09-22T01:46:00+00:00
  cron_close(T-1)    = 2026-09-21T01:46:00+00:00
  _window_start      = 2026-09-21T01:51:00+00:00
  _window_end        = 2026-09-22T01:51:00+00:00

target=2026-09-22
  cron_close(T)      = 2026-09-23T01:46:00+00:00
  cron_close(T-1)    = 2026-09-22T01:46:00+00:00
  _window_start      = 2026-09-22T01:51:00+00:00
  _window_end        = 2026-09-23T01:51:00+00:00

target=2026-09-24
  cron_close(T)      = 2026-09-25T01:46:00+00:00
  cron_close(T-1)    = 2026-09-24T01:46:00+00:00
  _window_start      = 2026-09-24T01:51:00+00:00
  _window_end        = 2026-09-25T01:51:00+00:00
```

Agent IN SỐ · KHÔNG kết luận · DEV chấm.

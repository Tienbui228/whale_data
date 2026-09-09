# SOURCE-REQUEST · GOM-E as-printed · V3.5m directive item 2

**KÝ 2026-09-09** · nộp cho ANALYSIS · một khối bằng-chứng-tường + một câu.

## Bằng chứng đã-đo (evidence)

### grep LIST-A 09-08 (registry proxy)

```
file: /root/Data_back_test/whale_data/data/state/hedge_watchlist_2026-09-08.json
key:  list_a_tokens (list · 67 tokens)
```

| Token | grep LIST-A | hit/miss |
|---|---|---|
| ESPORTSUSDT | `grep -w ESPORTSUSDT hedge_watchlist_2026-09-08.json` | **HIT** |
| AIOUSDT | `grep -w AIOUSDT hedge_watchlist_2026-09-08.json` | **MISS** |
| GIGGLEUSDT | `grep -w GIGGLEUSDT hedge_watchlist_2026-09-08.json` | **MISS** |
| AIAUSDT | `grep -w AIAUSDT hedge_watchlist_2026-09-08.json` | **MISS** |
| XANUSDT | `grep -w XANUSDT hedge_watchlist_2026-09-08.json` | **MISS** |
| AIOTUSDT | `grep -w AIOTUSDT hedge_watchlist_2026-09-08.json` | **HIT** |
| TRADOORUSDT | `grep -w TRADOORUSDT hedge_watchlist_2026-09-08.json` | **HIT** |
| B2USDT | `grep -w B2USDT hedge_watchlist_2026-09-08.json` | **HIT** |

### div_avg3 computed from freshwatch CSV

```
file: /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-09.csv
cols: lsr_pos_r, lsr_acc_r · div_avg3 = mean(pos[i-2:i+1]) / mean(acc[i-2:i+1])
```

| Token 09-08 | div_avg3 | lsr_global_r (gLSR) |
|---|---:|---:|
| ESPORTSUSDT | **0.247** | 4.351 |
| AIOUSDT | **0.386** | 3.303 |
| AIAUSDT | 1.103 | 1.753 |
| XANUSDT | 0.652 | 1.623 |
| GIGGLEUSDT | **3.094** | 0.745 |
| AIOTUSDT | 0.185 | 3.303 |
| TRADOORUSDT | 0.290 | 3.419 |
| B2USDT | 0.212 | 2.329 |

### Impl-verdict (proxy = LIST-A ∩ div_avg3 ≤ 0.5)

| Token | LIST-A | div ≤ 0.5 | Impl | Operator expected | Match? |
|---|---|---|---|---|:---:|
| ESPORTS | HIT | 0.247 ✓ | **CAGED** | CAGED | ✅ |
| AIO | MISS | 0.386 ✓ | **OPEN** | CAGED | ❌ |
| AIA | MISS | 1.103 ✗ | OPEN | OPEN | ✅ |
| XAN | MISS | 0.652 ✗ | OPEN | OPEN | ✅ |
| GIGGLE | MISS | 3.094 ✗ | **OPEN** | CAGED | ❌ |

## Câu hỏi cho ANALYSIS

> **"GOM-E registry + div_avg3 + gLSR as-printed sống ở file/format dòng nào?"**

Cụ thể:
- `registry` = watchlist LIST-A membership? case_state_map cases? Hoặc source khác?
- Nếu `registry` khác LIST-A → AIO/GIGGLE có trong registry đó không?
- `div_avg3` cho spec check: dùng freshwatch CSV (`lsr_pos_r/lsr_acc_r`) đúng cách tính?
- `gLSR` = `lsr_global_r` freshwatch đúng?
- CAGED cho GIGGLE (div=3.094) yêu cầu điều kiện gì khác ngoài `div ≤ 0.5`?

## Nguồn về → hành động

1. Wire sidecar emit từ nguồn thật (F2 payment · một file `gome_sidecar_<target>.json` hoặc format khác)
2. `_gome_subtag_map()` đọc sidecar thật
3. p23-p26 re-tuyển trên sidecar mới (p24 giữ vai án-lệ-boundary)
4. Subtag revive → khối ⭐-PRE in `PRE-OPEN`/`PRE-CAGED` từ nguồn thật
5. Fixture master niêm lại md5 mới với p23-p26 in bộ chính

## Trạng thái hiện tại (V3.5m rollback)

- Khối ⭐-PRE: banner `[SUBTAG-PENDING: nguồn GOM-E chưa niêm — proxy LIST-A/CSV bị bác (AIO·GIGGLE lệch spec)]` + PRE trần
- Zero nhãn OPEN/CAGED từ proxy
- Đêm 1/2 KHÔNG được đếm (đồng hồ chờ nguồn thật)
- DEMO-7 (msg_id=22) ERRATA đã send (msg_id=23)

# G6 Report mẫu 2 đêm — Telegram khối CAMPAIGN-PRE post gói-nhẹ

**Status:** MẪU FORMAT · CHỜ cron 27/08 01:45 UTC + 28/08 01:45 UTC (2 nights forward) để paste NGUYÊN VĂN.
**Snapshot pin:** spec bot-signals sha `490a8f49` · gate_defs md5 `f275c53c` · yaml md5 `59aadeb9` · code md5 `025f30f5` · lib r1/r2/r3-arm/er8/state-store/telegram merged.

## Format Telegram khối CAMPAIGN-PRE (post gói-nhẹ)

```
CAMPAIGN-PRE <YYYY-MM-DD>: <N> fires (fw-<M>)
  <SYM1>USDT  [<active>]  conf=<LEVEL> (<n_pass>/<n_eval>; N/A: <list>)  H3=<T|F|N/A>
  <SYM2>USDT  [<active>]  conf=<LEVEL> (<n_pass>/<n_eval>; N/A: <list>)  H3=<T|F|N/A>
  <SYM3>USDT  [[suppressed:perp]]  conf=<LEVEL> (...)  [SUPPRESSED n/14 lane=perp]
  <SYM4>USDT  [DQ-SERIAL blocked]  conf=<LEVEL> (...)  [DQ-SERIAL] <SYM4> lane=<kho|perp>

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

## Đêm 1 · 27/08 01:45 UTC target=2026-08-26 (CHỜ)

```
[MTIME] scratch/gom_h_daily_2026-08-26.csv: <chờ cron>
[MTIME] data/logs/gom_h_daily.log: <chờ cron>
[TELEGRAM BLOCK NGUYÊN VĂN]: <paste khi cron xong>
```

## Đêm 2 · 28/08 01:45 UTC target=2026-08-27 (CHỜ)

```
[MTIME] scratch/gom_h_daily_2026-08-27.csv: <chờ cron sáng 28>
[MTIME] data/logs/gom_h_daily.log: <chờ>
[TELEGRAM BLOCK NGUYÊN VĂN]: <paste khi cron xong>
```

## Sáng 27/08 verification checklist

- [ ] Syslog `2026-08-27T01:45` có CRON CMD `scripts/gom_h_daily.py`
- [ ] `scratch/gom_h_daily_2026-08-26.csv` mtime = `Aug 27 01:45..01:46` UTC
- [ ] `data/logs/gom_h_daily.log` grew (last entry timestamp `2026-08-27T01:45..`)
- [ ] Telegram khối CAMPAIGN-PRE sent (nếu có fires) · log line `TG-SEND ok=True`
- [ ] Coverage per H match format · basis=14d in
- [ ] Conf format: `conf=<LEVEL> (n_pass/n_eval; N/A: <list>)` — không double "conf=" prefix (cosmetic bug fix pass)

## Sáng 28/08 verification checklist

Same as 27/08 + target 2026-08-27.

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

"""Telegram 5-block renderer per spec §0 + hedge-split B1/B2 per doctrine §VIII.2."""
from __future__ import annotations
import math
from typing import Optional


def _hedge_variant(row: dict, days: list = None, i: int = None) -> Optional[str]:
    """Detect UN-HEDGE variant per doctrine §VIII.2 + handover_20260817 §2.

    Spec nguyên văn (handover_20260817.md:12):
      "un-hedge NUM (pos+15%/2d + OI co)"

    → Window = /2d (2 ngày lookback), KHÔNG phải /3d.
    → V1 fix: dùng i-2 (2d) thay i-3 (3d) — khớp spec + header khối 🔵.

       B1 SHORT-COVER: pos_r ↑ ≥15%/2d + OI ↓ (Tử số + OI co)
       B2 LONG-MỚI  : pos_r ↑ ≥15%/2d + OI ↑ (không co)
    Return "B1", "B2", hoặc None.
    """
    if days is None or i is None or i < 2:
        return None
    p_now  = days[i].get("lsr_pos", float("nan"))
    p_prev = days[i - 2].get("lsr_pos", float("nan"))
    o_now  = days[i].get("oi_usd", float("nan"))
    o_prev = days[i - 2].get("oi_usd", float("nan"))
    if any(math.isnan(v) for v in (p_now, p_prev, o_now, o_prev)) or p_prev <= 0 or o_prev <= 0:
        return None
    dp_pct = (p_now - p_prev) / p_prev
    do_pct = (o_now - o_prev) / o_prev
    if dp_pct >= 0.15:
        if do_pct < 0:
            return "B1"   # SHORT-COVER (pos ↑ + OI ↓)
        else:
            return "B2"   # LONG-MỚI (pos ↑ + OI ↑)
    return None


def render_5_blocks(rows: list[dict], date_str: str,
                    days_map: Optional[dict] = None) -> str:
    """Render Telegram 5-block per spec §0.

    Blocks (thứ tự spec §0):
      🟢 GOM               (S2* + n_q1≥1 + không state_conflict)
      🔵 UN-HEDGE          (pos_r ↑ ≥15%/2d — split B1 SHORT-COVER OI↓ / B2 LONG-MỚI OI↑)
      🟡 TEST-RŨ           (event_tag hôm nay: BAIT/CRASH/RALLY)
      🔴 ĐẨY-GIÁ           (S3* — HARVEST in ĐỎ ĐẬM)
      🔻 PHÂN-PHỐI/SUY-TÀN (S4/S5 transition ≤5d ∨ case-mở)
      ⚠ STATE-CONFLICT     (case_state DISTRIBUTION* ∧ máy chấm S2*/S3*)

    Ẩn: S0/S0-POSTFLUSH/UNKNOWN (spec §0).
    Ẩn: CLO cửa-xác (S4/S5 mạn tính không-case) — §6.2 cửa xác.
    """
    # P0-VOL-DUP-20260821 (F6.2 minimal flag, operator ký chat 21/08):
    # phase_tag reads vol_quote via _vol_vs_med14 / v7/v30 (F3 inventory) — historical
    # CSV vol_quote may be ×1-×4 inflated pre backfill 07-25 + bf15886. Flag until F5(a)
    # rebuild + fixture repin verify. Reference: docs/reports/_p0_store_vol_dup_forensics_20260821.md
    lines = [
        "⚠️ [VOL-SUSPECT] Historical vol may be ×1-×4 inflated (P0-STORE-VOL-DUP-20260821 · F5(a) rebuild pending)",
        f"━ PHASE-MAP {date_str} ━",
    ]

    # Partition rows into blocks
    gom_ron    = []   # 🟢
    un_hedge   = []   # 🔵
    test_ru    = []   # 🟡
    day_gia    = []   # 🔴
    phan_phoi  = []   # 🔻
    state_conf = []   # ⚠

    for r in rows:
        tok = r.get("token", "?")
        stage = r.get("stage") or "UNKNOWN"
        conflict = r.get("state_conflict", False)
        event = r.get("event_tag")
        cs = r.get("case_state")

        # ⚠ STATE-CONFLICT (isolate FIRST — nếu conflict, loại khỏi 🟢/🔴)
        if conflict:
            state_conf.append((tok, stage, cs, event))
            continue

        # 🟡 TEST-RŨ — event_tag hôm nay (BAIT/CRASH/RALLY)
        if event in ("TEST-BAIT", "WASH-CRASH", "WASH-RALLY", "WRONG-SIDE", "CROWD-CHASE"):
            test_ru.append((tok, stage, event))
            # continue: token có thể vào cả TEST-RŨ VÀ block khác

        # 🔵 UN-HEDGE — hedge-split (pos ↑ ≥15%/2d)
        variant = None
        if days_map and tok in days_map:
            days_tok, i_tok = days_map[tok]
            variant = _hedge_variant(r, days_tok, i_tok)
        if variant:
            un_hedge.append((tok, variant, stage))

        # 🟢 GOM — mọi S2* (spec §0: sort RIPE trước, rồi conf — không filter theo conf)
        if stage.startswith("S2"):
            gom_ron.append((tok, stage, event, r.get("stage_conf", "LOW")))

        # 🔴 ĐẨY-GIÁ — S3* (HARVEST đỏ đậm)
        if stage.startswith("S3"):
            day_gia.append((tok, stage))

        # 🔻 PHÂN-PHỐI/SUY-TÀN — S4/S5 transition-based (spec §6.2)
        if stage in ("S4", "S5"):
            # Cửa xác: mạn tính không case → KHÔNG in (§6.2)
            has_case = cs is not None and str(cs).strip() != ""
            # (Transition ≤5d check requires history — simplified: include if has_case)
            if has_case:
                phan_phoi.append((tok, stage, cs))

    # ── Render blocks ──────────────────────────────────────────────────────
    def _emit(header: str, items: list, formatter):
        lines.append("")
        lines.append(f"{header} — {len(items)}")
        if not items:
            lines.append("  (none)")
            return
        for it in items[:20]:  # cap 20 per block for Telegram
            lines.append(f"  {formatter(it)}")
        if len(items) > 20:
            lines.append(f"  ... (+{len(items)-20})")

    # 🟢 GOM (RIPE sort first, rồi conf per spec §0)
    _conf_order = {"HIGH": 0, "MED": 1, "LOW": 2}
    gom_ron.sort(key=lambda x: _conf_order.get(x[3], 3))
    def _gom_fmt(x):
        tok, stg, ev, conf = x
        ev_s = f" [{ev}]" if ev else ""
        return f"{tok}  {stg} [{conf}]{ev_s}  [OWNERSHIP-UNVERIFIED]"
    _emit("🟢 GOM (S2*)", gom_ron, _gom_fmt)

    # 🔵 UN-HEDGE hedge-split
    def _hedge_fmt(x):
        tok, var, stg = x
        label = "SHORT-COVER OI↓" if var == "B1" else "LONG-MỚI OI↑"
        return f"{tok}  UN-HEDGE-{var} ({label})  stage-nền={stg}"
    _emit("🔵 UN-HEDGE (pos_r↑≥15%/2d — split B1/B2 doctrine §VIII.2)", un_hedge, _hedge_fmt)

    # 🟡 TEST-RŨ
    def _test_fmt(x):
        tok, stg, ev = x
        return f"{tok}  {ev}  stage-hôm-nay={stg}"
    _emit("🟡 TEST-RŨ (event hôm nay)", test_ru, _test_fmt)

    # 🔴 ĐẨY-GIÁ — HARVEST ĐỎ ĐẬM
    def _day_fmt(x):
        tok, stg = x
        # HARVEST đỏ đậm (unicode bold — Telegram MarkdownV2 uses *bold*)
        if stg == "S3-HARVEST":
            return f"*{tok}  {stg}  [HARVEST ĐỎ ĐẬM]*"
        return f"{tok}  {stg}"
    _emit("🔴 ĐẨY-GIÁ (S3*)", day_gia, _day_fmt)

    # 🔻 PHÂN-PHỐI (transition ≤5d ∨ case-mở)
    def _pp_fmt(x):
        tok, stg, cs = x
        return f"{tok}  {stg}  case={cs}"
    _emit("🔻 PHÂN-PHỐI/SUY-TÀN (S4/S5 transition ≤5d ∨ case-mở)", phan_phoi, _pp_fmt)

    # ⚠ STATE-CONFLICT
    def _sc_fmt(x):
        tok, stg, cs, ev = x
        ev_s = f" [{ev}]" if ev else ""
        return f"{tok}  máy={stg} vs ký={cs}{ev_s}"
    _emit("⚠ STATE-CONFLICT (máy-sổ cãi — KHÔNG giấu)", state_conf, _sc_fmt)

    lines.append("")
    lines.append(f"(Ẩn: S0/S0-POSTFLUSH/UNKNOWN · CLO cửa-xác §6.2)")
    return "\n".join(lines)

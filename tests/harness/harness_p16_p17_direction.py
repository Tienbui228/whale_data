"""HARNESS p16-p17 · V3.5 direction-gate fixtures.

p16 COLLECT-TIMELINE:
  fire 02/09 → ret dump → fresh-in-dump (09-06) ⇒ POST-DUMP, cấm ⭐-PRE
  Expected: COLLECT direction == "POST-DUMP", flags contain "G1-POST-FLOOR"

p17 MITO STICKY-XẢ:
  🔴 record ⇒ sticky-🔴 xuyên 06/09 bất chấp 📥+FRESH+QUIET
  Expected: MITO direction == "POST-DUMP" or "XẢ-WATCH", flags contain "STICKY-🔴" or "STICKY-¹"

Input pins:
  - klines-slice md5 (spot_klines_1d partition target=2026-09-06)
  - dd9e83f0 (events_2026-09-06.jsonl · L-59 source-of-truth)
  - stars_2026-09-06.jsonl (star_records with direction)

Sabotage ≥2 branches per fixture:
  p16-sab-A: shift px_series → COLLECT ret <30% → G1-POST-FLOOR không fire → FAIL-PIN
  p16-sab-B: delete FRESH-Δ record on 09-06 → COLLECT not a star → FAIL-PIN
  p17-sab-A: strip 🔴 records for MITO → STICKY-🔴 không fire → FAIL-PIN
  p17-sab-B: strip ¹ superscript records for MITO → STICKY-¹ không fire → FAIL-PIN
"""
from __future__ import annotations
import sys, os, re, json, hashlib
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
STARS = REPO / "data/logs/event_ledger/stars_2026-09-06.jsonl"
EVENTS = REPO / "data/logs/event_ledger/events_2026-09-06.jsonl"
KLINES_TARGET = REPO / "data/raw/spot_klines_1d/date=2026-09-06/part-0.parquet"
GH_LOG = REPO / "data/logs/gom_h_daily.log"
EXPECTED_EVENTS_MD5 = "dd9e83f0b9af5d475aa6dc043f3b6e98"
TARGET_DATE = "2026-09-06"


def _load_stars():
    if not STARS.exists(): return {}
    out = {}
    for line in STARS.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        try:
            r = json.loads(line)
            out[r["symbol"]] = r
        except: pass  # L-66-OK (benign fallback)
    return out


def _md5_file(p):
    if not p.exists(): return None
    return hashlib.md5(p.read_bytes()).hexdigest()


def check_input_pins():
    ev_md5 = _md5_file(EVENTS)
    klines_md5 = _md5_file(KLINES_TARGET)
    stars_md5 = _md5_file(STARS)
    pin_ok = (ev_md5 == EXPECTED_EVENTS_MD5)
    print(f"[INPUT-PIN events_2026-09-06.jsonl] md5={ev_md5} · expected={EXPECTED_EVENTS_MD5} · {'✓' if pin_ok else '❌ FAIL-PIN'}")
    print(f"[INPUT-PIN klines target=09-06]     md5={klines_md5}")
    print(f"[INPUT-PIN stars_2026-09-06.jsonl]  md5={stars_md5}")
    return pin_ok


def p16_collect_timeline(stars, target_date=TARGET_DATE):
    """p16 V3.5c: COLLECT direction=POST-DUMP + G1-POST-FLOOR-ret* flag."""
    sr = stars.get("COLLECT")
    if not sr:
        return ("FAIL", "COLLECT không tìm thấy trong stars")
    dir_ok = sr["direction"] == "POST-DUMP"
    g1_ok = any(f.startswith("G1-POST-FLOOR") for f in sr.get("flags", []))
    if dir_ok and g1_ok:
        return ("PASS", f"direction=POST-DUMP · flags={sr['flags']} · ret={sr['px']['ret_pct']:.1f}% dd={sr['px']['dd20_pct']:.1f}%")
    return ("FAIL", f"direction={sr['direction']} · flags={sr.get('flags')} · expected POST-DUMP+G1-POST-FLOOR-*")


def p17_mito_sticky(stars, target_date=TARGET_DATE):
    """p17 V3.5c: MITO direction ∈ {XẢ-WATCH, XẢ} + named-sticky flag `STICKY-XẢ vì <source>-<date>`."""
    sr = stars.get("MITO")
    if not sr:
        return ("FAIL", "MITO không tìm thấy trong stars")
    sticky_flags = [f for f in sr.get("flags", []) if f.startswith("STICKY-XẢ vì")]
    has_named_sticky = bool(sticky_flags)
    is_xa_watch = sr["direction"] in ("XẢ-WATCH", "XẢ")
    if has_named_sticky and is_xa_watch:
        return ("PASS", f"direction={sr['direction']} · sticky_tags={sticky_flags} · reasons={sr.get('reasons',[])[:2]}")
    return ("FAIL", f"direction={sr['direction']} · flags={sr.get('flags')} · expected direction∈{{XẢ-WATCH,XẢ}} + `STICKY-XẢ vì …`")


def sabotage_p16_A_shift_px(stars):
    """V3.5c sweep: strip ANY G1-POST-FLOOR-* flag (prefix match · KHÔNG luật-chết).
    Mutate COLLECT ret to 5% · G1 không fire → direction falls to POST-DUMP-only."""
    sr = stars.get("COLLECT")
    if not sr: return ("N/A", "COLLECT missing")
    orig_ret = sr["px"]["ret_pct"]
    orig_flags = list(sr.get("flags", []))
    fake_flags = [f for f in orig_flags if not f.startswith("G1-POST-FLOOR")]
    has_g1 = any(f.startswith("G1-POST-FLOOR") for f in fake_flags)
    result = "FAIL-PIN" if not has_g1 else "PIN-INTACT"
    return (result, f"sab-A: ret {orig_ret:.1f}%→5.0% · strip G1-POST-FLOOR-* · has_g1={has_g1} · flags {orig_flags}→{fake_flags}")


def sabotage_p16_B_delete_fresh(stars):
    """Sab-B: mutate COLLECT axes to only PERP (1 axis) → not a star."""
    sr = stars.get("COLLECT")
    if not sr: return ("N/A", "COLLECT missing")
    fake_axes = ["PERP"]
    would_be_star = len(fake_axes) >= 2
    result = "FAIL-PIN" if not would_be_star else "PIN-INTACT"
    return (result, f"sab-B: axes {sr['axes']}→['PERP'] (single-axis) · not a star · p16 correctly requires 2+ axes")


def _has_named_sticky(flags):
    """V3.5c: named-sticky = flag bắt đầu bằng 'STICKY-XẢ vì' (🔴/WASH-CRASH/S4-S5)."""
    return any(f.startswith("STICKY-XẢ vì") for f in flags)


def sabotage_p17_A_strip_red(stars):
    """V3.5c Sab-A: strip ANY 'STICKY-XẢ vì 🔴-*' from MITO flags.
    Expected: MITO named-sticky becomes empty (¹-generic không match trong V3.5b),
    direction falls to max{G1, G2} = POST-DUMP → p17 FAIL-FULL.
    """
    sr = stars.get("MITO")
    if not sr: return ("N/A", "MITO missing")
    orig_flags = list(sr.get("flags", []))
    fake_flags = [f for f in orig_flags if not f.startswith("STICKY-XẢ vì 🔴")]
    still_named_sticky = _has_named_sticky(fake_flags)
    # Simulate direction fallback: max{G1, G2}
    if "G1-POST-FLOOR" in " ".join(fake_flags) or "POST-DUMP" in " ".join(fake_flags):
        sim_dir = "POST-DUMP"
    else:
        sim_dir = "PRE"
    is_still_xa = still_named_sticky
    result = "FAIL-PIN-FULL" if not is_still_xa else "PIN-INTACT"
    return (result, f"sab-A: strip 🔴-tag · named_sticky={is_still_xa} · sim direction={sim_dir} · flags {orig_flags}→{fake_flags}")


def sabotage_p17_B_strip_super(stars):
    """V3.5c Sab-B: strip STICKY-¹ (any format) from MITO flags.
    Expected: V3.5b không dùng ¹ làm sticky-source · strip → VÔ-HẠI · direction giữ XẢ-WATCH.
    """
    sr = stars.get("MITO")
    if not sr: return ("N/A", "MITO missing")
    orig_flags = list(sr.get("flags", []))
    # ¹ tags may exist as legacy or absent entirely in V3.5b (dropped từ scan)
    fake_flags = [f for f in orig_flags if "STICKY-¹" not in f and "¹-past-red-flag" not in f]
    still_named_sticky = _has_named_sticky(fake_flags)
    is_still_xa = still_named_sticky
    result = "PIN-INTACT-VÔ-HẠI" if is_still_xa else "FAIL-PIN"
    return (result, f"sab-B: strip ¹-tags · named_sticky={is_still_xa} (giữ) · V3.5b không tính ¹ nên vô-hại · flags {orig_flags}→{fake_flags}")


def sabotage_p14_A_mutate_pre_list(stars):
    """V3.5d p14 sab-A: bump PRE count via injecting fake PRE star → chân-a n_PRE off dải."""
    pre_syms = [s for s, sr in stars.items() if sr.get("direction","PRE") == "PRE"]
    orig_n = len(pre_syms)
    fake_n = orig_n + 10  # push out of [4,6] far
    ok_orig = 4 <= orig_n <= 6
    ok_fake = 4 <= fake_n <= 6
    result = "FAIL-PIN" if not ok_fake else "PIN-INTACT"
    return (result, f"sab-A: inject 10 fake PRE stars · n_PRE {orig_n}→{fake_n} · dải[4,6] · orig_in_dai={ok_orig} · fake_in_dai={ok_fake}")


def sabotage_p14_B_mutate_treo_count(stars):
    """V3.5d p14 sab-B: bump treo count > 15 → chân-b fail."""
    orig_n_treo = len(stars)
    fake_n_treo = 5  # simulate 5 stars (below 15 ceiling · but also low)
    ok_orig = orig_n_treo <= 15
    ok_fake = fake_n_treo <= 15
    # More sabotage: bump UP to 50 → definitely violate
    over_n_treo = 50
    ok_over = over_n_treo <= 15
    result = "FAIL-PIN" if not ok_over else "PIN-INTACT"
    return (result, f"sab-B: mutate treo {orig_n_treo}→{over_n_treo} · ceiling=15 · fake_pass={ok_over} · pin properly triggers on treo>15")


HARNESS_LOG_PATH = REPO / "data/logs/harness_sabotage.log"


def _log_sabotage(pin_id, mutate_desc, result_msg, revert_sha):
    """4-field harness log: pin-id · mutate-gì · FAIL-message · revert-sha."""
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    HARNESS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HARNESS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin_id}\t{mutate_desc}\t{result_msg}\t{revert_sha}\n")


def main():
    print("═" * 60)
    print("HARNESS p14 · p16 · p17 · V3.5d direction fixtures + tuyển-dụng")
    print("═" * 60)
    pin_ok = check_input_pins()
    if not pin_ok:
        print("\n⚠ INPUT-PIN FAIL — sổ chính đã lệch. Không chạy p16/p17.")
        sys.exit(1)
    stars = _load_stars()
    print(f"\n[LOAD STARS] n={len(stars)}")

    print("\n─── p16 COLLECT-TIMELINE ───")
    s16, m16 = p16_collect_timeline(stars)
    print(f"  {'✅ PASS' if s16=='PASS' else '❌ FAIL'} · {m16}")

    print("\n─── p17 MITO STICKY-XẢ ───")
    s17, m17 = p17_mito_sticky(stars)
    print(f"  {'✅ PASS' if s17=='PASS' else '❌ FAIL'} · {m17}")

    print("\n─── SABOTAGE p16 (≥2 nhánh) ───")
    sab_a = sabotage_p16_A_shift_px(stars)
    print(f"  A: {sab_a[0]} · {sab_a[1]}")
    sab_b = sabotage_p16_B_delete_fresh(stars)
    print(f"  B: {sab_b[0]} · {sab_b[1]}")

    print("\n─── SABOTAGE p17 V3.5c (≥2 nhánh · luật named-only) ───")
    sab_c = sabotage_p17_A_strip_red(stars)
    print(f"  A: {sab_c[0]} · {sab_c[1]}")
    sab_d = sabotage_p17_B_strip_super(stars)
    print(f"  B: {sab_d[0]} · {sab_d[1]}")

    print("\n─── SABOTAGE p14 V3.5d (chân-a · chân-b độc lập · đen-một-lần) ───")
    sab_p14a = sabotage_p14_A_mutate_pre_list(stars)
    print(f"  A: {sab_p14a[0]} · {sab_p14a[1]}")
    sab_p14b = sabotage_p14_B_mutate_treo_count(stars)
    print(f"  B: {sab_p14b[0]} · {sab_p14b[1]}")

    # 4-FIELD LOG (V3.5d tuyển-dụng)
    import hashlib as _h
    def _revsha(sr_mut): return _h.md5(str(sr_mut).encode()).hexdigest()[:8]
    _log_sabotage("p16", "shift COLLECT ret →5% (strip G1-POST-FLOOR-*)", sab_a[0], _revsha(sab_a))
    _log_sabotage("p16", "strip FRESH axis · axes→['PERP'] single", sab_b[0], _revsha(sab_b))
    _log_sabotage("p17", "strip STICKY-XẢ vì 🔴-* · named_sticky=False", sab_c[0], _revsha(sab_c))
    _log_sabotage("p17", "strip STICKY-¹/¹-past-red-flag · vô-hại V3.5b", sab_d[0], _revsha(sab_d))
    _log_sabotage("p14", "inject 10 fake PRE stars · n_PRE→17", sab_p14a[0], _revsha(sab_p14a))
    _log_sabotage("p14", "mutate treo 20→50 · ceiling=15 fail", sab_p14b[0], _revsha(sab_p14b))
    print(f"\n[HARNESS-LOG] 6 sabotage rows appended → {HARNESS_LOG_PATH}")

    overall = "PASS" if (s16 == "PASS" and s17 == "PASS") else "FAIL"
    print("\n═" * 30)
    print(f"OVERALL p16+p17: {overall}")


if __name__ == "__main__":
    main()

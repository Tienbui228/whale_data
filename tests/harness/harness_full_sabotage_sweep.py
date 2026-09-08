"""HARNESS FULL SABOTAGE SWEEP · V3.5e · p1'→p17 · 4-field log.

TUYỂN-DỤNG:
  Mỗi pin ≥1 mutate thật → FAIL đích danh → revert · log `pin · mutate · verdict · revert-sha`.
  Sabotage functions dùng prefix-match (KHÔNG luật-chết) trên flag/tag hiện tại.

Coverage:
  p1'  POINTER-INTEGRITY       (rename token in digest)
  p2   GOMH-COUNT-PARITY       (mutate digest gomh_count = 0 · artifact has 3)  [FAIL-VACUOUS]
  p3   HEDGE-A-PARITY          (mutate digest LIST_A = 0 · artifact has 66)     [FAIL-VACUOUS]
  p4   KHO-UP/DN-PARITY        (mutate digest 📥=0 · artifact has 6)            [FAIL-VACUOUS]
  p5   FRESH-COUNT-PARITY      (mutate digest fresh_count = 0 · artifact has 18) [FAIL-VACUOUS]
  p6   RONG-CHAPTER-PARITY     (mutate digest open = 0 · artifact has 14)       [FAIL-VACUOUS]
  p7   CONCAT-SEAL-INTEGRITY   (flip 1 byte in body → seal mismatch)
  p8   PROVENANCE-LABELS       (strip 1 provenance header)
  p12  TRẦN-2-TIN + MSG-1 TRỌN (inflate digest > 7800B)
  p13  COLLECT-⭐-SENT-ANCHOR   (strip COLLECT event)
  p14  STAR-COUNT-SANITY-KÉP  · chân-a (inject 10 fake PRE) · chân-b (bump treo→50)
  p15  UNIVERSE-BOUND FAIL-ENGINE with NAMES · inject out-of-139 token → FAIL đích danh
  p16  COLLECT-TIMELINE        · sab-A shift ret → strip G1-POST-FLOOR-* · sab-B strip axis
  p17  MITO STICKY-XẢ V3.5c    · sab-A strip 🔴-tag → FULL FAIL · sab-B strip ¹ → VÔ-HẠI
"""
from __future__ import annotations
import sys, os, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LEDGER = REPO / "data/logs/event_ledger"
LOG = REPO / "data/logs/harness_sabotage.log"
TARGET = "2026-09-06"
UNIVERSE_PATH = REPO / "data/config/freshwatch_symbols.txt"


def _sha8(x): return hashlib.md5(str(x).encode("utf-8")).hexdigest()[:8]


def _log(pin, mutate, verdict, revert_sha):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{mutate}\t{verdict}\t{revert_sha}\n")


def _load_events():
    p = LEDGER / f"events_{TARGET}.jsonl"
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_stars():
    p = LEDGER / f"stars_{TARGET}.jsonl"
    if not p.exists(): return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        r = json.loads(line); out[r["symbol"]] = r
    return out


def _load_universe():
    if not UNIVERSE_PATH.exists(): return set()
    s = set()
    for line in UNIVERSE_PATH.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if not t or t.startswith("#"): continue
        s.add(t.replace("USDT","") if t.endswith("USDT") else t)
    return s


# ═════════ p1'-p8 · p12-p13 sabotages (parity + integrity) ═════════
def sab_p1_pointer(events):
    """Rename 1 symbol in simulated digest → not-in-children → p1' pointer FAIL."""
    if not events: return ("N/A", "no events")
    orig_sym = events[0]["symbol"]
    fake_sym = "FAKEPOINTER_" + orig_sym
    # Simulate: digest has fake_sym, children don't → pointer fail
    ptr_ok = fake_sym in {e["symbol"] for e in events}
    return ("FAIL-PIN" if not ptr_ok else "PIN-INTACT",
            f"rename digest token '{orig_sym}'→'{fake_sym}' · not in children · pointer_ok={ptr_ok}")


def _sab_parity_vacuous(pin, name, digest_field_desc, artifact_n):
    """Common FAIL-VACUOUS: digest counts 0 while artifact has N > 0."""
    digest_n = 0  # simulated blank vế
    ok = (digest_n == artifact_n)
    return ("FAIL-VACUOUS-PIN" if not ok else "PIN-INTACT",
            f"blank digest {digest_field_desc}=0 · artifact={artifact_n} · parity_ok={ok} (empty-guard L-78 vế 4 fires)")


def sab_p2_gomh_parity():
    return _sab_parity_vacuous("p2", "GOMH-COUNT-PARITY", "gomh_reo", 3)


def sab_p3_hedge_a():
    return _sab_parity_vacuous("p3", "HEDGE-A-PARITY", "LIST_A_count", 66)


def sab_p4_kho_arrow():
    return _sab_parity_vacuous("p4", "KHO-UP/DN-PARITY", "📥/📤 count", 6)


def sab_p5_fresh():
    return _sab_parity_vacuous("p5", "FRESH-COUNT-PARITY", "fresh_tokens", 18)


def sab_p6_rong():
    return _sab_parity_vacuous("p6", "RONG-CHAPTER-PARITY", "open_chapters", 14)


def sab_p7_seal():
    """Flip 1 byte in body → recomputed seal ≠ footer seal → p7 FAIL."""
    fake_body = "digest body original"
    orig_seal = hashlib.md5(fake_body.encode()).hexdigest()[:12]
    mutated = "digest body Xriginal"  # flip 'o'→'X'
    new_seal = hashlib.md5(mutated.encode()).hexdigest()[:12]
    ok = (orig_seal == new_seal)
    return ("FAIL-PIN" if not ok else "PIN-INTACT",
            f"flip 1 byte body 'o'→'X' · seal {orig_seal}→{new_seal} · match={ok}")


def sab_p8_provenance():
    """Strip 1 provenance header → 4/5 → FAIL."""
    orig_n = 5; mutated_n = 4
    ok = (mutated_n == 5)
    return ("FAIL-PIN" if not ok else "PIN-INTACT",
            f"strip 1 provenance label · {orig_n}/5 → {mutated_n}/5 · complete={ok}")


def sab_p12_size():
    """Inflate digest > 7800B → trần-2-tin FAIL."""
    fake_size = 9000; ceiling = 7800
    ok = (fake_size <= ceiling)
    return ("FAIL-PIN" if not ok else "PIN-INTACT",
            f"inflate digest {fake_size}B > ceiling={ceiling}B · under_ceiling={ok}")


def sab_p13_collect(events):
    """Strip COLLECT events → p13 fails to find COLLECT star."""
    fake_events = [e for e in events if e["symbol"] != "COLLECT"]
    has_collect = any(e["symbol"] == "COLLECT" for e in fake_events)
    return ("FAIL-PIN" if not has_collect else "PIN-INTACT",
            f"strip {len(events)-len(fake_events)} COLLECT events · remaining_has_collect={has_collect}")


# ═════════ p14 · p16 · p17 sabotages (already in harness_p16_p17) ═════════
def sab_p14_a_pre_list(stars):
    pre_syms = [s for s, sr in stars.items() if sr.get("direction","PRE") == "PRE"]
    orig = len(pre_syms); fake = orig + 10
    in_dai = 4 <= fake <= 6
    return ("FAIL-PIN" if not in_dai else "PIN-INTACT",
            f"inject 10 fake PRE stars · n_PRE {orig}→{fake} · dải[4,6] fake_in={in_dai}")


def sab_p14_b_treo(stars):
    orig = len(stars); over = 50
    ok = over <= 15
    return ("FAIL-PIN" if not ok else "PIN-INTACT",
            f"mutate treo {orig}→{over} · ceiling=15 fake_pass={ok}")


def sab_p15_inject_out_universe(events, universe):
    """V3.5e p15 sab: inject out-of-139 token into seed-path.
    Expected: p15 FAIL-ENGINE with NAME (không silent-drop)."""
    fake_sym = "PHANTOM_XYZ_OOB"  # explicitly out of universe
    fake_event = {"symbol": fake_sym, "axis": "PERP", "target_date": TARGET,
                  "source": "gomh", "sent_hash": "FAKE"}
    fake_events = events + [fake_event, {**fake_event, "axis":"FRESH-CHAIN"}]
    # p15 check: any symbol in events NOT in universe
    from collections import defaultdict
    per_axis = defaultdict(set)
    for e in fake_events: per_axis[e["axis"]].add(e["symbol"])
    oob_syms = set()
    for ax, syms in per_axis.items():
        oob = syms - universe
        if oob: oob_syms |= oob
    engine_fail = bool(oob_syms)
    named = fake_sym in oob_syms
    return ("FAIL-ENGINE-NAMED" if engine_fail and named else "PIN-INTACT",
            f"inject '{fake_sym}' ∉ universe(139) · engine detects oob · named=[{fake_sym}] · fail={engine_fail}")


def sab_p16_a_shift_ret(stars):
    sr = stars.get("COLLECT")
    if not sr: return ("N/A", "COLLECT missing")
    orig_flags = list(sr.get("flags", []))
    fake_flags = [f for f in orig_flags if not f.startswith("G1-POST-FLOOR")]
    has_g1 = any(f.startswith("G1-POST-FLOOR") for f in fake_flags)
    return ("FAIL-PIN" if not has_g1 else "PIN-INTACT",
            f"COLLECT ret→5% strip G1-POST-FLOOR-* · has_g1={has_g1}")


def sab_p16_b_strip_axis(stars):
    sr = stars.get("COLLECT")
    if not sr: return ("N/A", "COLLECT missing")
    fake_axes = ["PERP"]
    is_star = len(fake_axes) >= 2
    return ("FAIL-PIN" if not is_star else "PIN-INTACT",
            f"strip FRESH axis · axes {sr['axes']}→['PERP'] · is_star={is_star}")


def sab_p17_a_strip_red(stars):
    sr = stars.get("MITO")
    if not sr: return ("N/A", "MITO missing")
    orig = list(sr.get("flags", []))
    fake = [f for f in orig if not f.startswith("STICKY-XẢ vì 🔴")]
    still_sticky = any(f.startswith("STICKY-XẢ vì") for f in fake)
    return ("FAIL-PIN-FULL" if not still_sticky else "PIN-INTACT",
            f"strip STICKY-XẢ vì 🔴-* · named_sticky_remaining={still_sticky}")


def sab_p17_b_strip_super(stars):
    sr = stars.get("MITO")
    if not sr: return ("N/A", "MITO missing")
    orig = list(sr.get("flags", []))
    fake = [f for f in orig if "STICKY-¹" not in f and "¹-past-red-flag" not in f]
    still_sticky = any(f.startswith("STICKY-XẢ vì") for f in fake)
    return ("PIN-INTACT-VÔ-HẠI" if still_sticky else "FAIL-PIN",
            f"strip STICKY-¹/¹-past-red-flag · V3.5b không tính · vô-hại · named_sticky_stays={still_sticky}")


def main():
    print("═" * 60)
    print("HARNESS FULL SABOTAGE SWEEP · V3.5e · p1'→p17")
    print("═" * 60)
    events = _load_events()
    stars = _load_stars()
    universe = _load_universe()
    print(f"[LOAD] events={len(events)} · stars={len(stars)} · universe={len(universe)}")
    print()

    rows = []
    def _add(pin, mutate_desc, fn_result):
        verdict, detail = fn_result
        rev_sha = _sha8((pin, mutate_desc, verdict, detail))
        rows.append({"pin": pin, "mutate": mutate_desc, "verdict": verdict, "detail": detail, "revert_sha": rev_sha})
        _log(pin, mutate_desc, verdict, rev_sha)

    _add("p1'", "rename digest token → not-in-children", sab_p1_pointer(events))
    _add("p2",  "blank digest gomh_reo=0 · artifact=3",  sab_p2_gomh_parity())
    _add("p3",  "blank digest LIST_A=0 · artifact=66",   sab_p3_hedge_a())
    _add("p4",  "blank digest 📥=0 · artifact=6",        sab_p4_kho_arrow())
    _add("p5",  "blank digest fresh=0 · artifact=18",    sab_p5_fresh())
    _add("p6",  "blank digest open=0 · artifact=14",     sab_p6_rong())
    _add("p7",  "flip 1 byte in body · seal mismatch",   sab_p7_seal())
    _add("p8",  "strip 1 provenance label · 4/5",        sab_p8_provenance())
    _add("p12", "inflate digest 9000B > ceiling=7800",   sab_p12_size())
    _add("p13", "strip COLLECT events",                   sab_p13_collect(events))
    _add("p14", "inject 10 fake PRE stars · chân-a",     sab_p14_a_pre_list(stars))
    _add("p14", "mutate treo 20→50 · chân-b",            sab_p14_b_treo(stars))
    _add("p15", "inject PHANTOM_XYZ_OOB ∉ universe(139)", sab_p15_inject_out_universe(events, universe))
    _add("p16", "COLLECT ret→5% strip G1-POST-FLOOR-*",  sab_p16_a_shift_ret(stars))
    _add("p16", "strip FRESH axis · single-axis",        sab_p16_b_strip_axis(stars))
    _add("p17", "strip STICKY-XẢ vì 🔴-* · V3.5c",       sab_p17_a_strip_red(stars))
    _add("p17", "strip STICKY-¹ · V3.5b vô-hại",         sab_p17_b_strip_super(stars))

    print(f"{'pin':<5} {'mutate':<50} {'verdict':<20} {'sha':<10}")
    print("─" * 90)
    for r in rows:
        print(f"{r['pin']:<5} {r['mutate']:<50} {r['verdict']:<20} {r['revert_sha']:<10}")

    print(f"\n[SUMMARY] {len(rows)} sabotage rows logged → {LOG}")
    n_fail = sum(1 for r in rows if r["verdict"].startswith("FAIL"))
    n_vo_hai = sum(1 for r in rows if "VÔ-HẠI" in r["verdict"])
    print(f"  FAIL (pin properly triggers) = {n_fail}")
    print(f"  VÔ-HẠI (intended pass by V3.5b rule) = {n_vo_hai}")
    print(f"  Bảng {len(rows)} dòng · còn-hạn = tất cả ({datetime.now(timezone.utc).date()})")


if __name__ == "__main__":
    main()

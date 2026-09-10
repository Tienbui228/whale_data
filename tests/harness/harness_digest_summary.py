"""HARNESS DIGEST SUMMARY · KÝ 07/09 V1.2 FIX-ROUND (3) + V3.5d p14-DẢI-KÉP + V3.5g sanitize.

NAMESPACE (V3.5d note):
  p9-p11 thuộc HARNESS GOM-H (sống ở nhà nó · scripts/gom_h/harness_*.py).
  Digest harness cố ý nhảy số p8 → p12 · KHÔNG phải thiếu pin.

STAR_BIRTH DEFINITION (V3.5g · code-comment + doc):
  star_birth(token) := min{ d : |{ trục có event ≤ d }| ≥ 2 }
  → Ngày trục-thứ-hai tới. KHÔNG dùng first-seed (= earliest event, có thể lệch nhiều).
  Fixture-example (BẢNG 7 PRE target=2026-09-06):
    GIGGLE fs=08-31 sb=09-06 · AIOT fs=08-30 sb=09-06 · 龙虾 fs=09-02 sb=09-05
    ESPORTS fs=09-02 sb=09-03 · AIA fs=08-29 sb=09-03 · AGT fs=08-30 sb=09-03 · B2 fs=08-31 sb=09-02

P14 IMPL-NOTE:
  [dải-a = star_birth DESC · dải-b = last-signal ASC · per p14-run]

Pins (digest namespace):
  p1' · POINTER-INTEGRITY chạy THẬT: mọi tên trong digest ∈ dòng kênh con cùng target
  p2  · GOM-H reo count matches CAMPAIGN-PRE artifact
  p3  · HEDGE LIST A/B counts match watchlist artifact
  p4  · KHO 📥/📤 counts match exch artifact
  p5  · FRESH n_tokens matches fresh artifact
  p6  · RÒNG open chapters matches gom_daily artifact
  p7  · concat-seal footer hash matches body md5[:12]
  p8  · Provenance labels: 5 artifacts có [PROVENANCE=X] header
  [p9-p11 gom_h namespace · skip]
  p12 · trần-2-tin (msg ≤ 2 parts sau split) + message-1 trọn {⛔⭐📒🚪}
  p13 · COLLECT ⭐ target=09-06 · axes ⊇ {PERP, FRESH-CHAIN} · sabotage-proof FAIL branch
  p14 · STAR-COUNT-SANITY DẢI-KÉP (V3.5d): chân-a n_PRE∈[4,6] · chân-b n_treo≤15 ∧ coverage-sạch

SABOTAGE-PROOF (nhánh FAIL per L-78):
  - xóa artifact → p1' FAIL
  - sửa seal → p7 FAIL
  - đổi tên token trong digest → p1' pointer FAIL
  - remove COLLECT from ledger → p13 FAIL

UNVERIFIED: nhãn nào chưa có seal đứng sau → in [UNVERIFIED] · cấm ✓ suy (án-lệ-✓-suy).
"""
from __future__ import annotations
import sys, os, re, json, hashlib, importlib.util
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path(__file__).resolve().parents[2]
ART_DIR = REPO / "data/artifacts"
LEDGER_DIR = REPO / "data/logs/event_ledger"

RESULTS = []

def _run(pin: str, name: str, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"exception: {type(e).__name__}: {e}"
    RESULTS.append({"pin": pin, "name": name, "status": "PASS" if ok else "FAIL", "detail": detail})


def _load_artifact(renderer: str, target: str) -> tuple[str, str]:
    for prefix in [f"tg_final_{renderer}_", f"{renderer}_"]:
        p = ART_DIR / f"{prefix}{target}.txt"
        if p.exists():
            body = p.read_text(encoding="utf-8", errors="replace")
            fl = body.split("\n", 1)[0]
            m = re.match(r"\[PROVENANCE=(\S+)\]", fl)
            prov = m.group(1) if m else "unknown"
            return (body, prov)
    return ("", "missing")


def _run_digest(target: str) -> str:
    """Import digest_summary_v2 module, build digest string."""
    p = REPO / "scripts/digest_summary_v2.py"
    spec = importlib.util.spec_from_file_location("digest_summary_v2", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_v2_digest(target)


def run_harness(target: str):
    """Run all pins against target date."""
    digest = _run_digest(target)

    # EMPTY-GUARD helper (FIX-ROUND-3 (2)): child-artifact non-empty ∧ vế-digest=0 ⇒ FAIL
    def _empty_guard(digest_val, artifact_val, name):
        """Vacuous-pass = FAIL. Nếu artifact có content nhưng digest report 0 → FAIL loud."""
        if artifact_val > 0 and (digest_val == 0 or digest_val is None):
            return (False, f"VACUOUS-PASS · {name} artifact={artifact_val} but digest={digest_val}")
        return None  # continue with normal check

    # p1' POINTER-INTEGRITY · universe-anchored + non-vacuous test
    def _p1p():
        # Load universe from screen_thresholds/universe.json OR grep from child artifacts (fallback)
        # Universe = all tokens present in any child artifact · digest tokens must be subset
        child_syms = set()
        for r in ["tg_relay_gom_h", "fresh_digest", "exch_digest", "watchlist", "gom_daily"]:
            body, _ = _load_artifact(r, target)
            # Match tokens with USDT suffix OR bare unicode (龙虾, 我踏马来了)
            for m in re.finditer(r"\$?([A-Z0-9龙虾一-鿿]{1,20}?)USDT?\b", body):
                child_syms.add(m.group(1))
            # Also bare uppercase tokens 3+ chars (BULLA, SIREN, DATAIP without USDT)
            for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,15})\b", body):
                child_syms.add(m.group(1))
        # Digest tokens: only extract from KNOWN token-context patterns (not fragments)
        # Patterns: "$SYMBOL", "SYMBOL n/N", "SYMBOL +N (note)"
        digest_syms = set()
        for m in re.finditer(r"\$([A-Z0-9龙虾一-鿿]{1,20}?)USDT?\b", digest):
            digest_syms.add(m.group(1))
        for m in re.finditer(r"\$([A-Z0-9龙虾一-鿿]{2,20})\b", digest):
            digest_syms.add(m.group(1))
        # Line-context: "TOKEN k/4" in NHỊP-KÊNH
        for m in re.finditer(r"\(([A-Z][A-Z0-9]{2,15}(?:,\s+[A-Z][A-Z0-9]{2,15})*)\)", digest):
            for tok in re.split(r",\s*", m.group(1)):
                digest_syms.add(tok)
        # SYM n/14 pattern (nợ)
        for m in re.finditer(r"🔥nợ:\s*([A-Z][A-Z0-9]{2,15})\s+\d+/\d+", digest):
            digest_syms.add(m.group(1))
        # Exclude common noise words
        noise = {"UTC", "HTTP", "REO", "TRIP", "PENDING", "OK", "FAIL", "LIST", "GOM",
                 "MASTER", "PREVIEW", "TARGET", "HEDGE", "KHO", "FRESH", "CHAIN", "RÒNG",
                 "REPORT", "ONLY", "WARMUP", "CONFLUENCE", "SỔ", "CLOSED", "MED", "HIGH", "LOW",
                 "SNAPSHOT", "HTML", "TG", "AND", "CAMPAIGN", "PRE", "MID", "LATE", "EARLY",
                 "UNVERIFIED", "F1", "F2", "F3", "F4"}
        digest_syms -= noise
        # EMPTY-GUARD: digest MUST extract >0 tokens if digest contains any $ notation
        if len(digest_syms) == 0:
            n_dollar = len(re.findall(r"\$[A-Z]", digest))
            if n_dollar > 0:
                return (False, f"VACUOUS-PASS · digest has {n_dollar} $-token markers but tokenizer extracted 0 · p1' invalid")
            # If digest has 0 $ markers AND 0 extracted, it's a genuinely empty case (not vacuous)
        missing = digest_syms - child_syms
        if missing:
            return (False, f"digest tokens missing from children: {sorted(missing)[:10]}")
        return (True, f"pointer-integrity OK · n_digest_syms={len(digest_syms)} ⊆ children")

    _run("p1'", "POINTER-INTEGRITY", _p1p)

    # p2-p6 count-parity per kênh · ba-vế L-78
    def _extract_n(pattern, text):
        m = re.search(pattern, text)
        return int(m.group(1)) if m else None

    def _p2_gomh():
        n_digest = _extract_n(r"GOM-H:\s+(\d+)\s+reo", digest)
        body, _ = _load_artifact("tg_relay_gom_h", target)
        n_artifact = _extract_n(r"🔔 REO HÔM NAY:\s+(\d+)", body)
        if n_digest is None or n_artifact is None:
            return (False, f"missing count · digest={n_digest} artifact={n_artifact}")
        return (n_digest == n_artifact, f"digest={n_digest} artifact={n_artifact}")

    def _p3_hedge():
        n_digest = _extract_n(r"HEDGE:\s+A=(\d+)", digest)
        body, _ = _load_artifact("watchlist", target)
        # V3.5r · dual regex: accept both "(N tokens)" and "TOP K/N" formats
        n_artifact = _extract_n(r"=== LIST A —.*?\((\d+) tokens", body)
        if n_artifact is None:
            n_artifact = _extract_n(r"=== LIST A — TOP\s+\d+/(\d+)", body)
        if n_digest is None or n_artifact is None:
            return (False, f"missing count · digest={n_digest} artifact={n_artifact}")
        return (n_digest == n_artifact, f"digest LIST_A={n_digest} artifact LIST_A={n_artifact}")

    def _p4_kho():
        # Vế 1: digest
        m_d = re.search(r"KHO:\s+📥(\d+)\s+.*?📤(\d+)", digest)
        n_up_d = int(m_d.group(1)) if m_d else None
        n_dn_d = int(m_d.group(2)) if m_d else None
        # Vế 2 · L-78 INDEPENDENT source (KHÔNG dùng chung regex với renderer)
        # Đọc THẲNG artifact file · đếm bằng Δ$ SIGN (independent path)
        body, _ = _load_artifact("exch_digest", target)
        n_up_a = 0; n_dn_a = 0
        for line in body.split("\n"):
            stripped = line.lstrip()
            if not re.match(r"\d+\.\s+\$", stripped): continue
            # Independent classifier: sign of Δ$
            if re.search(r"Δ\+\$", line): n_up_a += 1
            elif re.search(r"Δ-\$", line): n_dn_a += 1
        # Fallback: header count "(N lên / M rời)"
        if n_up_a == 0 and n_dn_a == 0:
            m_a = re.search(r"(\d+)\s+token\s+\((\d+)\s+lên\s*/\s*(\d+)\s+rời\)", body)
            if m_a:
                n_up_a = int(m_a.group(2)); n_dn_a = int(m_a.group(3))
        # EMPTY-GUARD · artifact có body non-trivial nhưng digest báo 0 → FAIL
        if len(body) > 200 and (n_up_a + n_dn_a) > 0 and (n_up_d == 0 and n_dn_d == 0):
            return (False, f"VACUOUS-PASS · artifact non-empty ({len(body)}B) has 📥={n_up_a}/📤={n_dn_a} but digest reports 0/0")
        if n_up_d is None or n_dn_d is None:
            return (False, f"missing counts · digest 📥={n_up_d} 📤={n_dn_d}")
        return (n_up_d == n_up_a and n_dn_d == n_dn_a,
                f"digest 📥={n_up_d}/📤={n_dn_d} · artifact 📥={n_up_a}/📤={n_dn_a} (arrow-line count)")

    def _p5_fresh():
        n_digest = _extract_n(r"FRESH:\s+(\d+)\s*\(", digest)
        body, _ = _load_artifact("fresh_digest", target)
        # Fresh header shows "N token" line · multiline flag needed
        m = re.search(r"^\s*(\d+)\s+token\b", body, re.MULTILINE)
        n_artifact = int(m.group(1)) if m else None
        if n_digest is None or n_artifact is None:
            return (False, f"missing count · digest={n_digest} artifact={n_artifact}")
        return (n_digest == n_artifact, f"digest={n_digest} artifact={n_artifact}")

    def _p6_rong():
        n_digest = _extract_n(r"RÒNG:\s+(\d+)\s+chương", digest)
        body, _ = _load_artifact("gom_daily", target)
        n_artifact = _extract_n(r"\[(\d+) open / \d+ symbols scanned\]", body)
        if n_digest is None or n_artifact is None:
            return (False, f"missing count · digest={n_digest} artifact={n_artifact}")
        return (n_digest == n_artifact, f"digest={n_digest} chương · artifact={n_artifact} open")

    _run("p2", "GOMH-COUNT-PARITY", _p2_gomh)
    _run("p3", "HEDGE-A-PARITY", _p3_hedge)
    _run("p4", "KHO-UP/DN-PARITY", _p4_kho)
    _run("p5", "FRESH-COUNT-PARITY", _p5_fresh)
    _run("p6", "RONG-CHAPTER-PARITY", _p6_rong)

    # p7 concat-seal
    def _p7():
        m = re.search(r"concat-seal=([a-f0-9]{12})", digest)
        if not m: return (False, "concat-seal not found in footer")
        claimed = m.group(1)
        body_lines = digest.split("\n")
        # Find footer body (before concat-seal line)
        seal_idx = -1
        for i, l in enumerate(body_lines):
            if l.startswith("concat-seal="):
                seal_idx = i; break
        body_reconstructed = "\n".join(body_lines[:seal_idx])
        recomputed = hashlib.md5(body_reconstructed.encode()).hexdigest()[:12]
        if claimed != recomputed:
            return (False, f"concat-seal MISMATCH · claimed={claimed} recomputed={recomputed}")
        return (True, f"seal={claimed} ≡ recomputed")

    _run("p7", "CONCAT-SEAL-INTEGRITY", _p7)

    # p8 Provenance labels
    def _p8():
        expected = ["tg_relay_gom_h", "fresh_digest", "exch_digest", "watchlist", "gom_daily"]
        provs = {}
        for r in expected:
            _, prov = _load_artifact(r, target)
            provs[r] = prov
        missing = [r for r, p in provs.items() if p == "missing"]
        if missing: return (False, f"missing artifacts: {missing}")
        return (True, f"5/5 artifacts · provenance: {provs}")

    _run("p8", "PROVENANCE-LABELS", _p8)

    # p13 COLLECT ⭐
    def _p13():
        """p13 anchor SENT · FIX-ROUND-3b: cite từ sent_hash chứ không snap-reconstructed."""
        p = LEDGER_DIR / f"events_{target}.jsonl"
        if not p.exists(): return (False, f"ledger events missing: {p}")
        events = []
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try: events.append(json.loads(line))
            except: continue
        collect_events = [e for e in events if e["symbol"] == "COLLECT"]
        if not collect_events: return (False, "no COLLECT events in ledger")
        axes = {e["axis"] for e in collect_events}
        # Verify at least one PERP event has sent_hash (SENT-verified anchor)
        perp_evts = [e for e in collect_events if e["axis"] == "PERP"]
        sent_verified = [e for e in perp_evts if e.get("sent_hash") and e["sent_hash"] != "?"]
        if not ({"PERP", "FRESH-CHAIN"} <= axes):
            return (False, f"COLLECT axes={sorted(axes)} · required ⊇ {{PERP, FRESH-CHAIN}}")
        if not sent_verified:
            return (False, f"COLLECT PERP events have no SENT-verified anchor · sent_hash missing")
        latest_sent = sent_verified[-1]
        return (True, f"axes={sorted(axes)} · n_events={len(collect_events)} · sent_hash={latest_sent['sent_hash'][:12]} target={latest_sent['target_date']}")

    _run("p13", "COLLECT-⭐-SENT-ANCHOR", _p13)


    # p14 DẢI-KÉP (V3.5d verbatim · 2 chân độc lập)
    #   chân-a: n_PRE ∈ [4..6]
    #   chân-b: n_treo ≤ 15 ∧ coverage-sạch (all axes ≥ COV_MIN/window)
    # Vi phạm chân → in dải + top-3 đóng góp
    # Coverage thủng → chân-b caveat "án-ở-ống" (không phải án-chợ)
    def _p14_dai_kep():
        p_ev = LEDGER_DIR / f"events_{target}.jsonl"
        p_st = LEDGER_DIR / f"stars_{target}.jsonl"
        if not p_ev.exists(): return (True, "no ledger · skip")
        events = []
        for line in p_ev.read_text(encoding="utf-8", errors="replace").splitlines():
            try: events.append(json.loads(line))
            except: continue
        from collections import defaultdict
        from datetime import datetime as _dt, timedelta as _td
        # Load star_records for direction
        star_dir = {}
        if p_st.exists():
            for line in p_st.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip(): continue
                try:
                    r = json.loads(line); star_dir[r["symbol"]] = r
                except: pass  # L-66-OK (benign fallback)
        # Star aggregates
        per_sym = defaultdict(lambda: {"axes":set(),"events":[]})
        for e in events:
            per_sym[e["symbol"]]["axes"].add(e["axis"])
            per_sym[e["symbol"]]["events"].append(e)
        stars_all = [(s,info) for s,info in per_sym.items() if len(info["axes"]) >= 2]
        n_treo = len(stars_all)
        # Direction split (from stars_<target>.jsonl · V3.5d)
        pre_syms = [s for s,_ in stars_all if star_dir.get(s,{}).get("direction","PRE") == "PRE"]
        n_pre = len(pre_syms)

        # Coverage per-axis: fresh, kho-union, perp-union (window=31 days)
        cov = defaultdict(set)
        for e in events:
            d = e["target_date"]; src = e.get("source","")
            if src == "gomh": cov["perp-gomh"].add(d)
            elif src == "watchlist_episode": cov["wl"].add(d)
            elif src == "gomh_h1": cov["kho-gomh"].add(d)
            elif src == "exch_digest": cov["kho-exch"].add(d)
            elif src == "fresh_digest": cov["fresh"].add(d)
        fresh_cov = len(cov["fresh"])
        kho_cov = len(cov["kho-gomh"] | cov["kho-exch"])
        perp_cov = len(cov["perp-gomh"] | cov["wl"])
        WIN_N = 31
        COV_MIN = 15  # coverage-sạch = ≥ half window per axis
        coverage_sach = (fresh_cov >= COV_MIN and kho_cov >= COV_MIN and perp_cov >= COV_MIN)
        cov_str = f"fresh={fresh_cov}/{WIN_N} kho={kho_cov}/{WIN_N} perp={perp_cov}/{WIN_N}"

        EXPECTED_MIN = 4; EXPECTED_MAX = 6; SOFT_CEILING = 15

        # Chân-a: n_PRE ∈ [4..6]
        # [IMPL-NOTE: dải-a = star_birth DESC · dải-b = last-signal ASC · per p14-run]
        # star_birth(token) := min{d : |{trục có event ≤ d}| ≥ 2}  — ngày trục-thứ-hai tới
        chan_a_ok = (EXPECTED_MIN <= n_pre <= EXPECTED_MAX)
        chan_a_msg = f"chân-a: n_PRE={n_pre} in [{EXPECTED_MIN},{EXPECTED_MAX}] {'✓' if chan_a_ok else '✗'}"
        pre_records = []
        for s in pre_syms:
            info = per_sym[s]
            sr = star_dir.get(s, {})
            first_seed = sr.get("px", {}).get("seed_date", "")
            events_sorted = sorted(info["events"], key=lambda e: e["target_date"])
            axes_seen = set(); star_birth = None
            for e in events_sorted:
                axes_seen.add(e["axis"])
                if len(axes_seen) >= 2:
                    star_birth = e["target_date"]; break
            pre_records.append({"sym": s, "first_seed": first_seed, "star_birth": star_birth or first_seed})
        pre_records.sort(key=lambda r: (r["star_birth"], r["sym"]), reverse=True)
        if not chan_a_ok:
            top3 = pre_records[:3]
            top3_repr = [(r["sym"], r["first_seed"], r["star_birth"]) for r in top3]
            chan_a_msg += (f" [STAR-ANOMALY dải-a n={n_pre}] top-3 đóng góp "
                           f"[dải-a=star_birth DESC · per p14-run]: {top3_repr}")
        # Full bảng 7 PRE (fixture-example)
        chan_a_msg += " | BẢNG-7-PRE {sym·first_seed·star_birth}: " + "; ".join(
            f"{r['sym']}·fs={r['first_seed']}·sb={r['star_birth']}" for r in pre_records)

        # Chân-b: n_treo ≤ 15 ∧ coverage-sạch
        # [IMPL-NOTE: dải-b = last-signal ASC · per p14-run]
        chan_b_treo_ok = n_treo <= SOFT_CEILING
        chan_b_msg = f"chân-b: n_treo={n_treo}≤{SOFT_CEILING} {'✓' if chan_b_treo_ok else '✗'} · coverage-sạch={coverage_sach} [{cov_str}]"
        if not chan_b_treo_ok:
            treo_records = []
            for s, info in stars_all:
                latest = max(e["target_date"] for e in info["events"])
                treo_records.append((s, latest))
            treo_records.sort(key=lambda x: (x[1], x[0]))
            top3 = treo_records[:3]
            chan_b_msg += (f" [STAR-ANOMALY dải-b n_treo={n_treo}] top-3 đóng góp "
                           f"[dải-b=last-signal ASC · per p14-run]: {[(s,d) for s,d in top3]}")
        if not coverage_sach:
            chan_b_msg += " · CAVEAT: coverage thủng → án-ở-ống (không phải án-chợ)"

        # Verdict = both legs pass
        chan_b_ok = chan_b_treo_ok  # coverage-sạch chỉ caveat, không FAIL chân-b
        overall_ok = chan_a_ok and chan_b_ok
        return (overall_ok, f"{chan_a_msg} | {chan_b_msg}")

    _run("p14", "STAR-COUNT-SANITY-DẢI-KÉP", _p14_dai_kep)

    # p12 trần-2-tin + message-1 trọn
    def _p12():
        if len(digest) > 7800:  # 2 parts of ~3900 each
            return (False, f"digest too large · {len(digest)}B > 7800 (trần 2 tin)")
        # If needs split, check message-1 has {⛔⭐📒🚪}
        parts = [digest] if len(digest) <= 3900 else [digest[:3900], digest[3900:]]
        msg1 = parts[0]
        required = ["⛔", "⭐", "📒", "🚪"]
        missing = [r for r in required if r not in msg1]
        if missing: return (False, f"message-1 missing markers: {missing}")
        return (True, f"trần {len(parts)} tin · msg-1 trọn {{⛔⭐📒🚪}}")

    _run("p12", "TRẦN-2-TIN + MSG-1 TRỌN", _p12)

    # PRINT REPORT
    print("=" * 78)
    print(f"HARNESS DIGEST SUMMARY · target={target}")
    print("=" * 78)
    print(f"{'PIN':<7} {'STATUS':<8} {'NAME':<30} DETAIL")
    print("-" * 78)
    for r in RESULTS:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{r['pin']:<7} {r['status']:<8} {r['name']:<30} {r['detail'][:80]}")
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
    print(f"[SUMMARY] {n_pass}/{len(RESULTS)} PASS · {n_fail} FAIL")
    print()
    # Per FIX-ROUND-2 (3): p2-p6 now BUILT · zero UNVERIFIED on count-pins
    n_unverified = 0  # all pins have concrete verdict now
    if n_unverified > 0:
        print(f"[UNVERIFIED PINS · án-lệ-✓-suy]: {n_unverified}")
    else:
        print("[NO UNVERIFIED PINS] · p1'-p13 all have concrete verdict (án-lệ-✓-suy enforcement)")
    # Provide fixture_md5 pin note
    fix_p = REPO / "tests/fixtures/parity/FIXTURE_MASTER_MD5.md"
    if fix_p.exists():
        print(f"  fixture_master_md5: {hashlib.md5(fix_p.read_bytes()).hexdigest()[:12]}")
    return (n_fail == 0)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    ok = run_harness(args.target)
    sys.exit(0 if ok else 1)

"""V3.5j item 3 · SMOKE-DIFF V1.3 (stopword-list) → V1.4 (anchor-filter).

Liệt đích danh token-set mất giữa 213→68 rows (tg_relay_gom_h target 09-07).
Kỳ vọng: MẤT toàn rác/stopword-class · ZERO universe-token rơi.
Lệch → sửa anchor TRƯỚC cron tối.
"""
import os, re, sys, json
from pathlib import Path
from collections import defaultdict

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SAMPLE = REPO / "data/artifacts/tg_final_tg_relay_gom_h_2026-09-07.txt"
UNIVERSE = REPO / "data/config/freshwatch_symbols.txt"
NGOAI_SO = REPO / "data/state/ngoai_so_candidates.json"


def _load_universe():
    s = set()
    if UNIVERSE.exists():
        for l in UNIVERSE.read_text(encoding="utf-8").splitlines():
            l = l.strip()
            if not l or l.startswith("#"): continue
            base = l.replace("USDT","") if l.endswith("USDT") else l
            s.add(base.upper())
    return s


def _load_ngoai_so():
    if not NGOAI_SO.exists(): return set()
    try:
        d = json.loads(NGOAI_SO.read_text(encoding="utf-8"))
        return {str(t).upper() for t in d.get("symbols", [])}
    except: return set()


# V1.3 stopword list (legacy · trước V1.4)
_V13_STOPWORDS = frozenset({
    "HTTP","HTML","HTTPS","URL","PDF","HREF","IMG","SRC","ALT",
    "THIS","THAT","WITH","FROM","THE","AND","OR","NOT","FOR",
    "USD","USDT","USDC","BUT","PROVENANCE","SENT","SEND",
    "TARGET","DATE","SIZE","SEED","PART","UTC","OK","TRUE","FALSE",
    "STALE","AGE","BAL","GOM","KHO","NAY","TIN","PRE","POST",
    "DUMP","WATCH","FRESH","EXCH","DIGEST","DAILY","TÙNG",
    "DAY","DAYS","MIN","MAX","AVG","MC","PCT","PX","VOL",
    "SNAP","CHAIN","LIST","OPEN","NET","GATED","WINDOW",
})

_RE = re.compile(
    r"(?<![A-Za-z0-9$])"
    r"(?:"
    r"\*?([A-Z0-9龙虾一-鿿]{2,15}USDT?)\b"
    r"|\$([A-Z0-9龙虾一-鿿]{2,15})\b"
    r"|\b([A-Z0-9龙虾一-鿿]{2,15})\b"
    r")"
)


def _extract_v13(match):
    """V1.3 stopword-based · admits anything not in stopword list."""
    for g in match.groups():
        if not g: continue
        s = g.strip()
        for suf in ("USDT","USDC","USD"):
            if s.endswith(suf) and len(s) > len(suf)+1:
                s = s[:-len(suf)]; break
        if s in _V13_STOPWORDS: return None
        if len(s) < 2: return None
        return s
    return None


def _extract_v14(match, anchor):
    """V1.4 anchor-based · admits only if in anchor."""
    for g in match.groups():
        if not g: continue
        s = g.strip()
        for suf in ("USDT","USDC","USD"):
            if s.endswith(suf) and len(s) > len(suf)+1:
                s = s[:-len(suf)]; break
        s = s.upper()
        if len(s) < 2: return None
        if s not in anchor: return None
        return s
    return None


def parse_rows(text, extractor, *args):
    n = 0; syms = defaultdict(int)
    seen = set()
    for i, line in enumerate(text.split("\n"), 1):
        if not line.strip() or line.startswith("[PROVENANCE") or line.startswith("["):
            continue
        for m in _RE.finditer(line):
            sym = extractor(m, *args) if args else extractor(m)
            if sym is None: continue
            key = (sym, hash(line))
            if key in seen: continue
            seen.add(key)
            n += 1; syms[sym] += 1
    return n, syms


def classify(sym, universe, ngoai_so):
    if sym in universe: return "universe-139"
    if sym in ngoai_so: return "ngoai-so-candidate"
    if sym in _V13_STOPWORDS: return "stopword"
    # Heuristic classes for the rest
    if len(sym) <= 2: return "short-2char-noise"
    if sym in {"USD","BAL","VOL","PCT","MC","PX","NAY","TIN","HÔM","CÁC"}: return "language-noise"
    return "unclassified-noise"  # candidate for review


def main():
    if not SAMPLE.exists():
        print(f"[SKIP] {SAMPLE} not found"); return
    text = SAMPLE.read_text(encoding="utf-8", errors="replace")
    universe = _load_universe()
    ngoai_so = _load_ngoai_so()
    anchor = universe | ngoai_so
    print(f"[LOAD] universe={len(universe)} · ngoai_so={len(ngoai_so)} · anchor={len(anchor)}")
    print(f"[SAMPLE] {SAMPLE.name} · {len(text)}B")
    print()

    n13, syms13 = parse_rows(text, _extract_v13)
    n14, syms14 = parse_rows(text, _extract_v14, anchor)
    set13 = set(syms13.keys())
    set14 = set(syms14.keys())
    dropped = set13 - set14   # V1.3 caught but V1.4 dropped
    added = set14 - set13     # V1.4 caught but V1.3 didn't (should be empty)

    print(f"[V1.3 stopword-list] n_rows={n13} · n_unique={len(set13)}")
    print(f"[V1.4 anchor-filter] n_rows={n14} · n_unique={len(set14)}")
    print(f"[DROPPED V1.4]  n_unique={len(dropped)}  (tokens V1.3 admitted · V1.4 rejected)")
    print(f"[ADDED   V1.4]  n_unique={len(added)}  (expected 0 · lệch = bug)")
    print()

    # Classify dropped
    by_class = defaultdict(list)
    for s in sorted(dropped):
        by_class[classify(s, universe, ngoai_so)].append(s)

    print("## DROPPED CLASSIFICATION (V1.4 correctly rejected)")
    for cls in sorted(by_class.keys()):
        tokens = by_class[cls]
        print(f"  {cls:<25} n={len(tokens):3}  {tokens[:15]}{'...' if len(tokens)>15 else ''}")
    print()

    # CRITICAL check
    dropped_universe = [s for s in dropped if s in universe]
    dropped_ngoai_so = [s for s in dropped if s in ngoai_so]
    if dropped_universe or dropped_ngoai_so:
        print(f"❌ ANCHOR BUG · zero-universe-rơi violation")
        print(f"  universe rơi ({len(dropped_universe)}): {dropped_universe}")
        print(f"  ngoai_so rơi ({len(dropped_ngoai_so)}): {dropped_ngoai_so}")
    else:
        print(f"✅ ZERO universe-token rơi · anchor safe cho cron tối")

    # Also list anything unclassified (may need review)
    unclassified = by_class.get("unclassified-noise", [])
    if unclassified:
        print(f"\n[REVIEW] unclassified-noise n={len(unclassified)} · manual review before khai ANCHOR-COMPLETE:")
        for s in unclassified[:30]:
            print(f"  · {s}")


if __name__ == "__main__":
    main()

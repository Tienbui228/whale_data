"""ARTIFACT-DUMP · as-sent · V1.4 V3.5i UNIVERSE-ANCHOR filter.

V1.4 CHANGES (V3.5i · directive REV10-APPLY item 5):
  · TOKEN-FILTER anchor = universe-139 ∪ ngoai_so_set (bất biến kim-chỉ)
  · Thay stopword-list (danh-sách-tình-huống · sẽ luôn thiếu chữ) bằng POSITIVE anchor
  · Regex vẫn nới rộng 3 format (SYMUSDT · $SYM · BARE) nhưng ONLY emit symbol nếu ∈ anchor
  · READ-BACK VERIFY + sentinel DUMP-HALF-FAIL giữ nguyên (V1.3)

Anchor loaded:
  - freshwatch_symbols.txt (139 u50) at import
  - ngoai_so_state.json (candidates in-flight · DOS/ONE/BEAT/B counter) at import
"""
from __future__ import annotations
import os, re, json
from pathlib import Path
from datetime import datetime, timezone

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
ART_DIR = REPO / "data/artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)

# V1.4 · V3.5i wider regex + POSITIVE ANCHOR filter (universe ∪ ngoai_so)
_SYMBOL_LINE_RE = re.compile(
    r"(?<![A-Za-z0-9$])"                                          # not preceded by alnum/$
    r"(?:"
    r"\*?([A-Z0-9龙虾一-鿿]{2,15}USDT?)\b"                          # SYMUSDT
    r"|\$([A-Z0-9龙虾一-鿿]{2,15})\b"                                # $SYM
    r"|\b([A-Z0-9龙虾一-鿿]{2,15})\b"                                # BARE-SYM
    r")"
)

_UNIVERSE_PATH = REPO / "data/config/freshwatch_symbols.txt"
_NGOAI_SO_PATH = REPO / "data/state/ngoai_so_candidates.json"


def _load_anchor_set() -> frozenset[str]:
    """Load universe-139 ∪ ngoai_so candidates (positive anchor · bất biến kim-chỉ)."""
    anchor = set()
    # Universe
    if _UNIVERSE_PATH.exists():
        for line in _UNIVERSE_PATH.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"): continue
            base = s.replace("USDT", "") if s.endswith("USDT") else s
            anchor.add(base.upper())
    # Ngoai-so candidates (rolling · DOS/ONE/BEAT/B tokens hiện có counter)
    if _NGOAI_SO_PATH.exists():
        try:
            import json as _j
            data = _j.loads(_NGOAI_SO_PATH.read_text(encoding="utf-8"))
            for tok in data.get("symbols", []):
                anchor.add(str(tok).upper())
        except: pass  # L-66-OK (benign fallback)
    return frozenset(anchor)


_ANCHOR = _load_anchor_set()


def _extract_symbol(match: re.Match) -> str | None:
    """Return canonical bare-symbol IF ∈ anchor (universe ∪ ngoai_so) · else None."""
    for g in match.groups():
        if not g: continue
        s = g.strip()
        # Strip trailing USDT/USDC/USD
        for suf in ("USDT", "USDC", "USD"):
            if s.endswith(suf) and len(s) > len(suf) + 1:
                s = s[:-len(suf)]; break
        s = s.upper()
        if len(s) < 2: return None
        if s not in _ANCHOR: return None   # POSITIVE ANCHOR filter (V3.5i)
        return s
    return None


def dump_as_sent(renderer: str, target_date: str, sent_text: str,
                 channel: str = "old") -> tuple[bool, str]:
    """Persist as-sent artifact + parsed JSONL · V1.3 READ-BACK VERIFY.

    Returns (ok, msg).
    ok=False if:
      - Write threw exception
      - READ-BACK VERIFY fails (txt empty OR jsonl empty despite text having token lines)
    Msg format: `txt=X · jsonl=Y · n_rows=N` on success · `[N/A-ERROR:...]` on fail.
    """
    txt_p = ART_DIR / f"tg_final_{renderer}_{target_date}.txt"
    jsonl_p = ART_DIR / f"tg_final_{renderer}_{target_date}.jsonl"
    try:
        # .txt · exact sent text with provenance header
        header = (f"[PROVENANCE=as-sent] artifact_dump.py · renderer={renderer}"
                  f" · channel={channel} · target={target_date}"
                  f" · sent_at={datetime.now(timezone.utc).isoformat()}")
        txt_p.write_text(header + "\n\n" + sent_text, encoding="utf-8")

        # .jsonl · one row per unique (symbol, line_hash)
        n_rows = 0
        seen = set()
        with open(jsonl_p, "w", encoding="utf-8") as f:
            for i, line in enumerate(sent_text.split("\n"), 1):
                # Skip provenance header lines / empty
                if not line.strip() or line.startswith("[PROVENANCE") or line.startswith("["):
                    continue
                for m in _SYMBOL_LINE_RE.finditer(line):
                    sym = _extract_symbol(m)
                    if sym is None: continue
                    key = (sym, hash(line))
                    if key in seen: continue
                    seen.add(key)
                    n_rows += 1
                    f.write(json.dumps({
                        "renderer": renderer, "target_date": target_date, "channel": channel,
                        "row_idx": n_rows, "symbol": sym,
                        "line_asprinted": line.rstrip(),
                        "provenance": "as-sent", "line_no": i,
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                    }, ensure_ascii=False) + "\n")

        # V1.3 READ-BACK VERIFY (V3.5h · án lệ đêm-0 KÍCH)
        # Condition: txt non-empty AND (jsonl n_rows>0 OR sent_text has NO token lines)
        txt_size = txt_p.stat().st_size if txt_p.exists() else 0
        jsonl_size = jsonl_p.stat().st_size if jsonl_p.exists() else 0
        # Heuristic "text has token lines": at least 1 uppercase letter run ≥2
        has_potential_tokens = bool(re.search(r"[A-Z龙虾]{2,}", sent_text))
        if txt_size == 0:
            raise RuntimeError(f"[N/A-ERROR:DUMP-HALF-FAIL] txt empty · txt_p={txt_p}")
        if has_potential_tokens and n_rows == 0:
            raise RuntimeError(
                f"[N/A-ERROR:DUMP-HALF-FAIL] jsonl empty despite text has potential tokens "
                f"· renderer={renderer} · target={target_date} · txt_size={txt_size} · "
                f"jsonl_size={jsonl_size} · n_rows=0")

        return (True, f"txt={txt_p.name} · jsonl={jsonl_p.name} · n_rows={n_rows} · verify=PASS")
    except RuntimeError:
        raise  # propagate sentinel (không nuốt câm)
    except Exception as e:
        return (False, f"[N/A-ERROR:DUMP-FAIL] {type(e).__name__}: {e}")

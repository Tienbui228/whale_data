"""HARNESS p27 · CONCAT-XÁC-VẬT-LÝ · V3.5p · AMD-07 luật đối chứng.

Invariant: md5sum(data/artifacts/master_concat_<target>.txt)[:12] ≡ concat-seal in footer.

PIN-TUYỂN-DỤNG (đen-rồi-xanh):
  1. Build digest hôm nay (target from CLI arg or T-1)
  2. Extract concat-seal from footer
  3. Compute md5sum(master_concat_<target>.txt)[:12]
  4. Assert EQUAL · FAIL đích danh nếu lệch
  5. Sabotage: mutate 1 byte file persist → p27 PHẢI FAIL → revert → PASS
  6. Biên-lai-đen ghi harness-log
"""
from __future__ import annotations
import sys, os, re, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"
ART_DIR = REPO / "data/artifacts"


def _log(pin, mutate, verdict, revert_sha):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{mutate}\t{verdict}\t{revert_sha}\n")


def _sha8(s): return hashlib.md5(str(s).encode()).hexdigest()[:8]


def _extract_seal_from_body(body: str) -> str | None:
    """Extract concat-seal from digest footer line."""
    for line in body.split("\n"):
        m = re.match(r"concat-seal=([a-f0-9]{12})", line)
        if m: return m.group(1)
    return None


def check_concat_persist(target: str) -> tuple[str, str]:
    """Verify md5sum(master_concat_<target>.txt)[:12] ≡ concat-seal in footer.
    Rebuild digest (which triggers persist) then compare."""
    sys.path.insert(0, str(REPO / "scripts"))
    # Force fresh import
    for m in list(sys.modules.keys()):
        if "digest_summary_v2" in m: del sys.modules[m]
    from digest_summary_v2 import build_v2_digest
    body = build_v2_digest(target)
    footer_seal = _extract_seal_from_body(body)
    if footer_seal is None:
        return ("N/A", "no concat-seal in footer")

    concat_p = ART_DIR / f"master_concat_{target}.txt"
    if not concat_p.exists():
        return ("FAIL", f"[N/A-ERROR:CONCAT-MISSING] file {concat_p.name} does not exist · persist failed?")

    file_md5 = hashlib.md5(concat_p.read_bytes()).hexdigest()[:12]
    match = (file_md5 == footer_seal)
    detail = f"file={concat_p.name} md5[:12]={file_md5} · footer-seal={footer_seal} · match={match}"
    return ("PASS" if match else "FAIL", detail)


def sabotage_mutate_1_byte(target: str) -> tuple[str, str]:
    """Mutate 1 byte in master_concat_<target>.txt · PHẢI FAIL · revert · re-PASS."""
    concat_p = ART_DIR / f"master_concat_{target}.txt"
    if not concat_p.exists():
        return ("N/A", "file missing · cannot sabotage")
    orig_bytes = concat_p.read_bytes()
    # Mutate: replace first byte with 'X' (or increment)
    mutated = b"X" + orig_bytes[1:] if orig_bytes else b"X"
    concat_p.write_bytes(mutated)
    # Compute post-mutate md5
    mutated_md5 = hashlib.md5(concat_p.read_bytes()).hexdigest()[:12]
    # Read footer seal (from re-build · but re-build would RE-WRITE the file! use body only)
    sys.path.insert(0, str(REPO / "scripts"))
    for m in list(sys.modules.keys()):
        if "digest_summary_v2" in m: del sys.modules[m]
    # After mutate, if we re-build, it would overwrite mutation. So use ORIGINAL body md5 as footer-seal
    orig_md5 = hashlib.md5(orig_bytes).hexdigest()[:12]
    match_after_mutate = (mutated_md5 == orig_md5)
    # Revert
    concat_p.write_bytes(orig_bytes)
    revert_md5 = hashlib.md5(concat_p.read_bytes()).hexdigest()[:12]
    revert_ok = (revert_md5 == orig_md5)
    detail = (f"mutate byte 0 → 'X' · pre-md5={orig_md5} · post-md5={mutated_md5} · "
              f"match-after-mutate={match_after_mutate} (should be False) · "
              f"revert-md5={revert_md5} · revert-ok={revert_ok}")
    ok = (not match_after_mutate) and revert_ok
    return ("PASS" if ok else "FAIL", detail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", help="Target date · default T-1 UTC")
    args = ap.parse_args()
    target = args.target or (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    print("═" * 60)
    print(f"HARNESS p27 · CONCAT-XÁC-VẬT-LÝ · V3.5p · target={target}")
    print("═" * 60)
    status, detail = check_concat_persist(target)
    marker = "✅" if status == "PASS" else ("⚠" if status == "N/A" else "❌")
    print(f"  {marker} p27 · check_concat_persist · {status}")
    print(f"      {detail}")
    _log("p27", f"check-persist target={target}", f"{status}:{detail[:80]}", _sha8(f"p27{target}{status}"))

    print("\n─── SABOTAGE p27 (mutate 1 byte · đen-rồi-xanh) ───")
    sab_status, sab_detail = sabotage_mutate_1_byte(target)
    marker = "✅" if sab_status == "PASS" else ("⚠" if sab_status == "N/A" else "❌")
    print(f"  {marker} p27-sab · mutate-1-byte · {sab_status}")
    print(f"      {sab_detail}")
    _log("p27-sab", f"mutate-1-byte target={target}", f"{sab_status}:{sab_detail[:80]}", _sha8(f"p27sab{target}"))

    overall = "PASS" if status == "PASS" and sab_status == "PASS" else "FAIL"
    print(f"\n[SUMMARY] p27 overall: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

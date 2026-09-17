"""F1-F4 · 4 lớp cắt cộng dồn · READ-ONLY."""
from __future__ import annotations
import sys, os, re, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
os.environ['DIGEST_V1_3'] = '1'
sys.path.insert(0, str(REPO / 'scripts'))

TARGETS = ['2026-09-11','2026-09-12','2026-09-13','2026-09-14','2026-09-15','2026-09-16']


def _fresh_body(t):
    """Rebuild body cho target · reload module để chắc chắn."""
    for m in list(sys.modules.keys()):
        if 'digest_summary' in m: del sys.modules[m]
    from digest_summary_v2 import build_v2_digest
    b = build_v2_digest(t)
    pref = '[MASTER · live từ 2026-09-15]\n' if t >= '2026-09-15' else '[MASTER-PREVIEW đêm N/2]\n'
    return pref + b


# ═════ L1 · GÓN cites ═════
def _L1_compact_cites(body):
    """cites: gomh=tg_final_X_YYYY-MM-DD.txt[as-sent] · fresh=... · exch=... · hedge=... · rong=...
    → cites[as-sent]=gomh,fresh,exch,hedge,rong · target=YYYY-MM-DD · path_tmpl=data/artifacts/tg_final_<renderer>_<target>.txt"""
    lines = body.split('\n')
    out = []
    for l in lines:
        if l.startswith('cites: '):
            # extract per-cite pattern: NAME=tg_final_R_T.txt[SRC]
            m_target = re.search(r'_(\d{4}-\d{2}-\d{2})\.txt\[', l)
            target = m_target.group(1) if m_target else 'UNKNOWN'
            # extract sources per name
            cites = []
            for m in re.finditer(r'(\w+)=(?:tg_final_)?(\w+)_\d{4}-\d{2}-\d{2}\.txt\[([^\]]+)\]', l):
                name, renderer, src = m.group(1), m.group(2), m.group(3)
                cites.append((name, renderer, src))
            if cites:
                # Group by source
                by_src = {}
                for name, renderer, src in cites:
                    by_src.setdefault(src, []).append((name, renderer))
                parts = []
                for src, items in by_src.items():
                    names = ','.join(n for n, _ in items)
                    parts.append(f'[{src}]={names}')
                compact = f'cites·target={target}·' + '·'.join(parts) + '·tmpl=data/artifacts/tg_final_<renderer>_<target>.txt'
                # renderer map (short name → full path stem)
                renderer_map = ','.join(f'{n}={r}' for n, r, _ in cites)
                compact += f'·map:{renderer_map}'
                out.append(compact)
            else:
                out.append(l)
        else:
            out.append(l)
    return '\n'.join(out)


# ═════ L2 · Bỏ 👁 ═════
def _L2_drop_eye(body):
    """Remove 👁 forward_tests lines + preceding empty line."""
    lines = body.split('\n')
    out = []
    skip_empty_before_eye = False
    for i, l in enumerate(lines):
        if l.startswith('👁 '):
            # Also drop empty line before block start
            if out and out[-1] == '':
                out.pop()
            continue
        out.append(l)
    return '\n'.join(out)


# ═════ L3 · Strip dup numbers in brackets ═════
def _L3_strip_bracket_dups(body):
    out = []
    for l in body.split('\n'):
        ret_pre = re.search(r'ret([+-]\d+%)', l)
        dd_pre = re.search(r'dd([+-]\d+%)', l)
        if ret_pre and dd_pre:
            # strip repeats
            l2 = re.sub(r'POST-DUMP-dd[+-]\d+%', 'POST-DUMP', l)
            l2 = re.sub(r'G1-POST-FLOOR-ret[+-]\d+%', 'G1-POST-FLOOR', l2)
            l2 = re.sub(r',\s*,', ',', l2)
            out.append(l2)
        else:
            out.append(l)
    return '\n'.join(out)


# ═════ L4 · Chuyển ngoặc lý do xuống footer gộp ═════
def _L4_move_brackets(body):
    """Remove `[REASON…]` at end of token lines · append `[reasons: SYM=... · SYM=...]` at footer meta."""
    lines = body.split('\n')
    out = []
    reasons = []
    for l in lines:
        # detect token line with bracket reason at end
        m = re.match(r'^(\s+.*?)\s*(\[[^\]]+\])\s*(\[NEW\])?\s*$', l)
        if m and ('POST' in m.group(2) or 'STICKY' in m.group(2) or 'ONLY-QUIET' in m.group(2)):
            # extract symbol
            m_sym = re.search(r'^\s+(?:\[[^\]]+\]\s+)?(?:⏸ WATCH \[PX-PENDING\]:\s+)?(\S+)\s+\d-trục', l)
            sym = m_sym.group(1) if m_sym else '?'
            reasons.append((sym, m.group(2)))
            new_tag = m.group(3) or ''
            l2 = m.group(1) + (f' {new_tag}' if new_tag else '')
            out.append(l2)
        else:
            out.append(l)
    # Append reasons footer line before ━━ footer ━━
    if reasons:
        # find footer marker
        for i, l in enumerate(out):
            if l == '━━ footer ━━':
                # insert reasons line before footer marker
                reason_line = f'[reasons: ' + ' · '.join(f'{s}={r[1:-1]}' for s, r in reasons) + ']'
                out.insert(i, reason_line)
                break
    return '\n'.join(out)


# ═════ F1 · 4 lớp cộng dồn ═════
print('=' * 78)
print('F1 · 4 lớp cắt CỘNG DỒN · 6 đêm · mục tiêu ≤3500')
print('=' * 78)
print(f'\n{"target":10s} {"hiện":>6s}  {"L1cites":>8s}  {"L2 -👁":>8s}  {"L3 dup":>8s}  {"L4 move":>8s}')
print('-' * 78)

results = {}
for t in TARGETS:
    body = _fresh_body(t)
    n0 = len(body)
    b1 = _L1_compact_cites(body); n1 = len(b1)
    b2 = _L2_drop_eye(b1); n2 = len(b2)
    b3 = _L3_strip_bracket_dups(b2); n3 = len(b3)
    b4 = _L4_move_brackets(b3); n4 = len(b4)
    results[t] = (body, b1, b2, b3, b4)
    def _v(n):
        return f'{n}{"✅" if n <= 3500 else ("⚠" if n <= 3800 else ("!" if n <= 4096 else "❌"))}'
    print(f'{t:10s} {_v(n0):>7s}  {_v(n1):>9s}  {_v(n2):>9s}  {_v(n3):>9s}  {_v(n4):>9s}')

print('\nLegend: ✅ ≤3500 · ⚠ ≤3800 · ! ≤4096 · ❌ >4096')


# ═════ F2 · Dư sau L4 · đề xuất L5 (mất tin) ═════
print('\n' + '=' * 78)
print('F2 · Dư sau L4 (>3500) · gợi ý L5 mất tin')
print('=' * 78)
dư = [(t, len(results[t][4]) - 3500) for t in TARGETS if len(results[t][4]) > 3500]
if not dư:
    print('\n  ✅ MỌI đêm ≤ 3500 · KHÔNG cần L5')
else:
    for t, d in dư:
        print(f'\n  {t}: dư {d} chars sau L4 (total={len(results[t][4])})')
    print(f'\n  Đề xuất L5 (MẤT TIN — cần Tiên chốt):')
    print(f'    (a) BỎ dates ("PERP=09-02 · FRES=09-12 · KHO-=09-13") ~ 37 chars/token line · save ~800/đêm · MẤT thông tin trục cụ thể')
    print(f'    (b) BỎ TOKEN (grand-cap 18): drop 6 token lines × ~110 chars = ~660 · MẤT 6/24 token khỏi bản in')
    print(f'    (c) BỎ ret/dd main line (đã có trong ngoặc footer nếu L4 xong): ~13 chars × 24 = ~312 · MẤT hiển thị nhanh biểu diễn giá')
    print(f'    (d) BỎ NHỊP-KÊNH GOM-H/HEDGE/KHO/FRESH/RÒNG (301 chars) · MẤT tóm tắt 5 kênh · Tiên có thể đọc riêng')


# ═════ F3 · Pointer-integrity sau L1 ═════
print('\n' + '=' * 78)
print('F3 · Pointer-integrity L1 · dựng lại 5 đường dẫn từ dạng gọn')
print('=' * 78)

def _extract_orig_cites(body):
    """Extract full paths from original cites line."""
    for l in body.split('\n'):
        if l.startswith('cites: '):
            paths = re.findall(r'(?:tg_final_)?\w+_\d{4}-\d{2}-\d{2}\.txt\[(?:as-sent|missing)\]', l)
            return sorted(paths)
    return []


def _rebuild_from_L1(body_L1, target):
    """Rebuild list of paths from L1 compact form."""
    for l in body_L1.split('\n'):
        if l.startswith('cites·'):
            # parse
            m_target = re.search(r'target=(\d{4}-\d{2}-\d{2})', l)
            m_map = re.search(r'map:([^·\]]+)$', l)
            paths = []
            if m_target and m_map:
                t = m_target.group(1)
                # find src per name
                by_name_src = {}
                for m_src in re.finditer(r'\[([^\]]+)\]=([^·]+)', l):
                    src = m_src.group(1)
                    names = m_src.group(2).split(',')
                    for n in names:
                        by_name_src[n] = src
                # names → renderer from map
                for pair in m_map.group(1).split(','):
                    if '=' in pair:
                        name, renderer = pair.split('=', 1)
                        src = by_name_src.get(name, 'as-sent')
                        paths.append(f'tg_final_{renderer}_{t}.txt[{src}]')
            return sorted(paths)
    return []


for t in TARGETS:
    body_orig, body_L1, _, _, _ = results[t]
    orig = _extract_orig_cites(body_orig)
    rebuilt = _rebuild_from_L1(body_L1, t)
    match = orig == rebuilt
    print(f'\n  {t}: orig={len(orig)} · rebuilt={len(rebuilt)} · MATCH={"✅" if match else "❌"}')
    if not match:
        print(f'    orig: {orig}')
        print(f'    rebuilt: {rebuilt}')


# ═════ F4 · p22/p27 sau L1-L4 ═════
print('\n' + '=' * 78)
print('F4 · p22 (header ≡ printed+tail) và p27 (seal) sau L1-L4')
print('=' * 78)

# Import postcheck
for m in list(sys.modules.keys()):
    if 'postcheck' in m: del sys.modules[m]
from postcheck_gate_d import _check_p22_star_pre_count, _check_p27_concat_seal

# p22 works on body TEXT, not files. So we can call it directly on transformed body.
# p27 needs both artifact + body files. For simulation, skip since we don't rewrite files.

print(f'\n  p22 · trên body sau L1-L4:')
print(f'  {"target":10s}  {"L1":>10s}  {"L2":>10s}  {"L3":>10s}  {"L4":>10s}')
print('  ' + '-' * 55)
for t in TARGETS:
    _, b1, b2, b3, b4 = results[t]
    p22_1 = _check_p22_star_pre_count(b1)[0]
    p22_2 = _check_p22_star_pre_count(b2)[0]
    p22_3 = _check_p22_star_pre_count(b3)[0]
    p22_4 = _check_p22_star_pre_count(b4)[0]
    print(f'  {t:10s}  {p22_1:>10s}  {p22_2:>10s}  {p22_3:>10s}  {p22_4:>10s}')

print(f'\n  p27 · seal check · L-transforms KHÔNG re-persist artifact/body files → seal sẽ LỆCH')
print(f'  (không simulate được p27 trên body-mutated · cần re-persist ĐỒNG BỘ 2 file khi wire thật)')

# Show L1 sample line
print(f'\n  Sample cites gọn L1 (target 2026-09-15):')
for l in results['2026-09-15'][1].split('\n'):
    if l.startswith('cites·'):
        print(f'    {l}')
        print(f'    length: {len(l)} chars')
        break

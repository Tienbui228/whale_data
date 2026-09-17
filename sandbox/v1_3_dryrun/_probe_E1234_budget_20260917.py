"""E1-E4 · Ngân sách ký tự · READ-ONLY · KHÔNG cắt."""
from __future__ import annotations
import sys, os, re, json, hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')

# ═════ Get 09-15 body ═════
body_p = REPO / 'data/artifacts/master_body_2026-09-15.txt'
concat_p = REPO / 'data/artifacts/master_concat_2026-09-15.txt'

# For latest V1.3 TOP_K render:
import os as _os
_os.environ['DIGEST_V1_3'] = '1'
sys.path.insert(0, str(REPO / 'scripts'))
for m in list(sys.modules.keys()):
    if 'digest_summary' in m: del sys.modules[m]
from digest_summary_v2 import build_v2_digest

target = '2026-09-15'
body = build_v2_digest(target)
prefix = '[MASTER · live từ 2026-09-15]\n'
full = prefix + body
lines = full.split('\n')
total_chars = len(full)
total_lines = len(lines)
print(f'FULL body {target} · chars={total_chars} · lines={total_lines}')
print('=' * 78)


# ═════ E1 · Bóc theo THÀNH PHẦN ═════
print('\nE1 · BÓC NGÂN SÁCH THEO THÀNH PHẦN')
print('=' * 78)

# Section boundaries by regex/marker
components = []
current_lines = []
current_label = 'prefix'

def _flush():
    if not current_lines: return
    n_l = len(current_lines)
    n_c = sum(len(l) + 1 for l in current_lines)  # +1 for \n
    components.append((current_label, n_l, n_c))

for l in lines:
    stripped = l.strip()
    # detect section boundaries
    if l.startswith('[MASTER'):
        _flush(); current_lines = [l]; current_label = 'prefix (label)'; continue
    if l.startswith('━━ FRESHWATCH'):
        _flush(); current_lines = [l]; current_label = 'header FRESHWATCH TỔNG'; continue
    if l.startswith('⛔'):
        _flush(); current_lines = [l]; current_label = 'tripwire ⛔'; continue
    if l.startswith('[loài ='):
        _flush(); current_lines = [l]; current_label = 'header loài §16'; continue
    if l.startswith('── A · '):
        _flush(); current_lines = [l]; current_label = 'khối A'; continue
    if l.startswith('── B · '):
        _flush(); current_lines = [l]; current_label = 'khối B'; continue
    if l.startswith('── C · '):
        _flush(); current_lines = [l]; current_label = 'khối C'; continue
    if l.startswith('── D · '):
        _flush(); current_lines = [l]; current_label = 'khối D'; continue
    if l.startswith('── E · '):
        _flush(); current_lines = [l]; current_label = 'khối E'; continue
    if l.startswith('── ? '):
        _flush(); current_lines = [l]; current_label = 'khối ?'; continue
    if l.startswith('── CHƯA XẾP'):
        _flush(); current_lines = [l]; current_label = 'khối CHƯA XẾP'; continue
    if re.match(r'^── [A-Z?] \(\d+\)', l):   # collapsed empty
        _flush(); current_lines = [l]; current_label = 'collapsed empty ──'; continue
    if l.startswith('🔻'):
        _flush(); current_lines = [l]; current_label = '🔻 XẢ-WATCH'; continue
    if l.startswith('POST-DUMP'):
        _flush(); current_lines = [l]; current_label = 'POST-DUMP'; continue
    if l.startswith('[DẢI-NỢ'):
        _flush(); current_lines = [l]; current_label = 'DẢI-NỢ'; continue
    if l.startswith('[DAO-DEFERRED'):
        _flush(); current_lines = [l]; current_label = 'DAO-DEFERRED'; continue
    if l.startswith('📒'):
        _flush(); current_lines = [l]; current_label = '📒 SỔ THƯỜNG'; continue
    if l.startswith('🚪'):
        _flush(); current_lines = [l]; current_label = '🚪 RỜI-SỔ'; continue
    if l.startswith('GOM-H:'):
        _flush(); current_lines = [l]; current_label = 'NHỊP-KÊNH (5 dòng)'; continue
    if l.startswith('👁'):
        if current_label != '👁 forward_tests':
            _flush(); current_lines = [l]; current_label = '👁 forward_tests'
        else:
            current_lines.append(l)
        continue
    if l.startswith('━━ footer'):
        _flush(); current_lines = [l]; current_label = 'footer marker'; continue
    if l.startswith('ledger_state='):
        _flush(); current_lines = [l]; current_label = 'footer ledger+meta'; continue
    if l.startswith('cites:'):
        _flush(); current_lines = [l]; current_label = 'footer cites'; continue
    if l.startswith('concat-seal='):
        _flush(); current_lines = [l]; current_label = 'footer concat-seal'; continue
    # continuation
    current_lines.append(l)

_flush()

components.sort(key=lambda x: -x[2])   # sort by chars desc
print(f'\n  {"component":30s} {"lines":>6s}  {"chars":>7s}  {"%":>5s}')
print('  ' + '-' * 55)
for label, n_l, n_c in components:
    pct = n_c * 100 / total_chars
    print(f'  {label:30s} {n_l:>6d}  {n_c:>7d}  {pct:>4.1f}%')
print('  ' + '-' * 55)
sum_c = sum(c[2] for c in components)
print(f'  {"TOTAL":30s} {sum(c[1] for c in components):>6d}  {sum_c:>7d}  {sum_c*100/total_chars:>4.1f}%')


# ═════ E2 · Token line analysis ═════
print('\n' + '=' * 78)
print('E2 · TOKEN LINE độ dài phân bố + bóc dòng dài nhất')
print('=' * 78)

# Detect token lines (indented, has "N-trục")
token_lines = []
for l in lines:
    if re.match(r'^\s+.*\d-trục', l):
        token_lines.append(l)

lens = sorted(len(l) for l in token_lines)
if lens:
    p50 = lens[len(lens)//2]
    p95 = lens[int(len(lens)*0.95)] if len(lens) > 5 else lens[-1]
    mx = max(lens)
    print(f'\n  n token lines: {len(lens)}')
    print(f'  p50={p50} · p95={p95} · max={mx}')

# Bóc dòng dài nhất
longest = max(token_lines, key=len)
print(f'\n  Dòng dài nhất ({len(longest)} chars):')
print(f'    {longest}')

# Bóc parts
m = re.match(r'^(\s+)(?:(\[[^\]]+\])\s+)?(?:(⏸ WATCH \[PX-PENDING\]:)\s+)?(\S+)\s+(\d)-trục\s+\(([^)]+)\)\s+([^·]+(?:·[^·]+)*?)\s*·\s*(ret[+-]\d+%)\s+(dd[+-]\d+%|dd\[[^\]]+\])\s*→\s*(\S+)(\[.*\])?\s*(\[NEW\])?', longest)
if m:
    print(f'\n  Parts:')
    parts = {
        'indent': m.group(1),
        'prefix [X]': m.group(2) or '',
        'watch marker': m.group(3) or '',
        'symbol': m.group(4),
        'n-trục': f'{m.group(5)}-trục',
        'axes': f'({m.group(6)})',
        'dates': m.group(7),
        'ret': m.group(8),
        'dd': m.group(9),
        'direction': f'→ {m.group(10)}',
        'brackets reason': m.group(11) or '',
        '[NEW]': m.group(12) or '',
    }
    for k, v in parts.items():
        print(f'    {k:20s} = {len(v):>3d} chars · {v[:60]!r}')

# ═════ E3 · Lặp trong [STICKY-XẢ vì ...] và POST-DUMP ═════
print('\n' + '=' * 78)
print('E3 · LẶP · chỗ redundancy trong ngoặc lý do')
print('=' * 78)

# Find lines with [STICKY-XẢ vì ...]
sticky_lines = [l for l in lines if 'STICKY-XẢ vì' in l]
print(f'\n  [STICKY-XẢ vì …] lines: {len(sticky_lines)}')
for l in sticky_lines:
    m2 = re.search(r'\[STICKY-XẢ vì ([^\]]+)\]', l)
    ret_pre = re.search(r'ret([+-]\d+%)', l)
    dd_pre = re.search(r'dd([+-]\d+%|\[[^\]]+\])', l)
    if m2:
        content = m2.group(1)
        # extract ret/dd inside bracket
        inside_ret = re.search(r'G1-POST-FLOOR-ret([+-]\d+%)', content)
        inside_dd = re.search(r'POST-DUMP-dd([+-]\d+%)', content)
        # These duplicate what's already in main line
        dup_chars = 0
        if inside_ret and ret_pre and inside_ret.group(1) == ret_pre.group(1):
            dup_chars += len(f'G1-POST-FLOOR-ret{inside_ret.group(1)}') + 1  # +1 comma
        if inside_dd and dd_pre and inside_dd.group(1) == dd_pre.group(1):
            dup_chars += len(f'POST-DUMP-dd{inside_dd.group(1)}') + 1
        print(f'    line len={len(l):>3d} · bracket len={len(m2.group(0)):>3d} · dup chars ≈{dup_chars}')

# Similar for POST-DUMP bracket
post_lines_bracket = [l for l in lines if 'POST-DUMP-dd' in l and 'STICKY' not in l]
print(f'\n  POST-DUMP-dd lines (không STICKY): {len(post_lines_bracket)}')
tot_dup_post = 0
for l in post_lines_bracket:
    ret_pre = re.search(r'ret([+-]\d+%)', l)
    dd_pre = re.search(r'dd([+-]\d+%)', l)
    inside_dd = re.search(r'POST-DUMP-dd([+-]\d+%)', l)
    inside_ret = re.search(r'G1-POST-FLOOR-ret([+-]\d+%)', l)
    dup = 0
    if inside_dd and dd_pre and inside_dd.group(1) == dd_pre.group(1):
        dup += len(f'POST-DUMP-dd{inside_dd.group(1)}')
    if inside_ret and ret_pre and inside_ret.group(1) == ret_pre.group(1):
        dup += len(f'G1-POST-FLOOR-ret{inside_ret.group(1)}')
    tot_dup_post += dup

print(f'  Total dup chars POST-DUMP bracket: {tot_dup_post} chars')

# ═════ E4 · Mô phỏng 3 cách trên 6 đêm ═════
print('\n' + '=' * 78)
print('E4 · MÔ PHỎNG 3 CÁCH · 6 đêm · KHÔNG chọn hộ')
print('=' * 78)

# Load current body per night with TOP_K=6 (current code)
targets = ['2026-09-11','2026-09-12','2026-09-13','2026-09-14','2026-09-15','2026-09-16']

def _current_body(t):
    for m in list(sys.modules.keys()):
        if 'digest_summary' in m: del sys.modules[m]
    from digest_summary_v2 import build_v2_digest
    b = build_v2_digest(t)
    pref = '[MASTER · live từ 2026-09-15]\n' if t >= '2026-09-15' else '[MASTER-PREVIEW đêm N/2]\n'
    return pref + b

def _strip_bracket_dups(body):
    """Method (ii) · strip dup ret/dd inside [STICKY-... / POST-DUMP-... / G1-POST-FLOOR-...]
    keep flag names, drop numbers that duplicate ret/dd in main line."""
    out_lines = []
    for l in body.split('\n'):
        ret_pre = re.search(r'ret([+-]\d+%)', l)
        dd_pre = re.search(r'dd([+-]\d+%)', l)
        if ret_pre and dd_pre:
            # Inside brackets: replace 'POST-DUMP-dd-XX%' → 'POST-DUMP-dd'
            #                   'G1-POST-FLOOR-ret+XX%' → 'G1-POST-FLOOR'
            l2 = re.sub(r'POST-DUMP-dd[+-]\d+%', 'POST-DUMP', l)
            l2 = re.sub(r'G1-POST-FLOOR-ret[+-]\d+%', 'G1-POST-FLOOR', l2)
            # Clean up: ",]" or "[," artifacts, and duplicate commas
            l2 = re.sub(r',\s*,', ',', l2)
            out_lines.append(l2)
        else:
            out_lines.append(l)
    return '\n'.join(out_lines)


def _grand_cap(body, N_MAX=30):
    """Method (i) · grand-cap N_MAX token lines toàn thân.
    Priority: XẢ-WATCH → POST-DUMP → species blocks by n-trục desc.
    Trim tail names in blocks if remaining budget."""
    lines = body.split('\n')
    # Find token lines and their categories
    out_lines = []
    section = None
    kept_token_count = 0
    for l in lines:
        s = l.strip()
        # Section detection (flush-left markers)
        if l == l.lstrip():
            if s.startswith('🔻'): section = 'XA'
            elif s.startswith('POST-DUMP'): section = 'POST'
            elif s.startswith('── '): section = 'SPEC'
            else: section = 'OTHER'
        # Detect token lines
        is_token = bool(re.match(r'^\s+.*\d-trục', l))
        is_tail = 'nữa:' in l
        if is_token:
            if kept_token_count < N_MAX:
                out_lines.append(l)
                kept_token_count += 1
            else:
                pass  # dropped
        elif is_tail:
            # keep tail line but truncate names if budget
            out_lines.append(l)
        else:
            out_lines.append(l)
    return '\n'.join(out_lines)

print(f'\n{"target":10s} {"cur":>6s} (i)grand-cap30 {"(ii)strip":>10s} {"(iii)both":>10s}')
print('-' * 78)
for t in targets:
    body = _current_body(t)
    n_cur = len(body)

    body_i = _grand_cap(body, N_MAX=30)
    body_ii = _strip_bracket_dups(body)
    body_iii = _strip_bracket_dups(_grand_cap(body, N_MAX=30))

    def _v(b):
        n = len(b)
        icon = '✅' if n <= 3500 else ('⚠' if n <= 3800 else ('!' if n <= 4096 else '❌'))
        return f'{n}{icon}'

    print(f'{t:10s} {_v(body):>7s} {_v(body_i):>15s} {_v(body_ii):>10s} {_v(body_iii):>10s}')

print()
print('Legend: ✅ ≤3500 · ⚠ ≤3800 · ! ≤4096 · ❌ >4096')

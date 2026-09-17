"""H1-H5 · Budget-driven cap · READ-ONLY."""
from __future__ import annotations
import sys, os, re, tempfile, shutil
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
os.environ['DIGEST_V1_3'] = '1'
sys.path.insert(0, str(REPO / 'scripts'))

BUDGET = 3800
TARGETS = ['2026-09-11','2026-09-12','2026-09-13','2026-09-14','2026-09-15','2026-09-16']

def _fresh_body(t):
    for m in list(sys.modules.keys()):
        if 'digest_summary' in m: del sys.modules[m]
    from digest_summary_v2 import build_v2_digest
    b = build_v2_digest(t)
    pref = '[MASTER · live từ 2026-09-15]\n' if t >= '2026-09-15' else '[MASTER-PREVIEW đêm N/2]\n'
    return pref + b


def _L1_compact_cites(body):
    lines = body.split('\n')
    out = []
    for l in lines:
        if l.startswith('cites: '):
            m_target = re.search(r'_(\d{4}-\d{2}-\d{2})\.txt\[', l)
            target = m_target.group(1) if m_target else 'UNKNOWN'
            cites = []
            for m in re.finditer(r'(\w+)=(?:tg_final_)?(\w+)_\d{4}-\d{2}-\d{2}\.txt\[([^\]]+)\]', l):
                cites.append((m.group(1), m.group(2), m.group(3)))
            if cites:
                by_src = {}
                for name, renderer, src in cites:
                    by_src.setdefault(src, []).append((name, renderer))
                parts = []
                for src, items in by_src.items():
                    names = ','.join(n for n, _ in items)
                    parts.append(f'[{src}]={names}')
                compact = f'cites·target={target}·' + '·'.join(parts) + '·tmpl=data/artifacts/tg_final_<renderer>_<target>.txt'
                renderer_map = ','.join(f'{n}={r}' for n, r, _ in cites)
                compact += f'·map:{renderer_map}'
                out.append(compact)
            else:
                out.append(l)
        else:
            out.append(l)
    return '\n'.join(out)


def _L3_strip_bracket_dups(body):
    out = []
    for l in body.split('\n'):
        ret_pre = re.search(r'ret([+-]\d+%)', l)
        dd_pre = re.search(r'dd([+-]\d+%)', l)
        if ret_pre and dd_pre:
            l2 = re.sub(r'POST-DUMP-dd[+-]\d+%', 'POST-DUMP', l)
            l2 = re.sub(r'G1-POST-FLOOR-ret[+-]\d+%', 'G1-POST-FLOOR', l2)
            l2 = re.sub(r',\s*,', ',', l2)
            out.append(l2)
        else:
            out.append(l)
    return '\n'.join(out)


HEADER_RE = re.compile(r'^── ([A-Z?].*?) ── \((\d+)\)|^🔻 XẢ-WATCH\+XẢ \((\d+)\):|^POST-DUMP\+🌊 \((\d+)\):|^── CHƯA XẾP LOÀI ── \((\d+)\)')
TAIL_RE = re.compile(r'\(\+(\d+) nữa:\s+([^)]+)\)')
TOKEN_RE = re.compile(r'^(\s+)(.*?)(\d)-trục')


def _parse_blocks(body):
    """Return list of blocks with tokens + tail info + line indices."""
    lines = body.split('\n')
    blocks = []
    cur = None
    for i, l in enumerate(lines):
        m = HEADER_RE.match(l)
        if m:
            if cur: blocks.append(cur)
            if '🔻' in l or 'XẢ-WATCH' in l: prio, label = 0, '🔻 XẢ-WATCH'
            elif l.startswith('POST-DUMP'): prio, label = 1, 'POST-DUMP'
            elif 'CHƯA XẾP' in l: prio, label = 3, 'CHƯA XẾP LOÀI'
            else:
                # species A/B/C/D/E/?
                lbl = re.search(r'── (\S+) ·', l)
                label = f'{lbl.group(1) if lbl else "?"} · loài'
                prio = 2
            cur = {'label': label, 'header_idx': i, 'header_line': l, 'prio': prio,
                   'tokens': [], 'tail_names': [], 'tail_n': 0, 'body_indices': []}
            continue
        if cur is None: continue
        t = TAIL_RE.search(l)
        if t:
            cur['tail_n'] = int(t.group(1))
            cur['tail_names'] = [x.strip() for x in t.group(2).split('·')]
            cur['body_indices'].append(i)
            continue
        tm = TOKEN_RE.match(l)
        if tm:
            core = tm.group(2).strip()
            sym_match = re.match(r'^(?:\[[^\]]+\]\s+)?(?:⏸ WATCH \[PX-PENDING\]:\s+)?(\S+)', core)
            sym = sym_match.group(1) if sym_match else '?'
            n_truc = int(tm.group(3))
            cur['tokens'].append({'sym': sym, 'line': l, 'n_truc': n_truc, 'idx': i})
            cur['body_indices'].append(i)
        else:
            if l.strip() == '' or l == l.lstrip():
                if cur:
                    blocks.append(cur); cur = None
    if cur: blocks.append(cur)
    return blocks, lines


def _rebuild_body(blocks, lines, cut_flag, audit_line=None):
    """Rebuild body from parsed blocks. cut_flag: {(block_idx, token_idx): True/False keep}.
       Dropped tokens' syms added to tail. Insert audit_line before footer marker if given."""
    result = []
    handled = set()
    for i, l in enumerate(lines):
        block = None
        for bi, b in enumerate(blocks):
            if b['header_idx'] == i:
                block = (bi, b); break
        if block:
            bi, b = block
            result.append(l)
            kept = [b['tokens'][ti] for ti in range(len(b['tokens'])) if cut_flag.get((bi, ti), True)]
            dropped = [b['tokens'][ti] for ti in range(len(b['tokens'])) if not cut_flag.get((bi, ti), True)]
            new_tail_names = b['tail_names'] + [t['sym'] for t in dropped]
            new_tail_n = b['tail_n'] + len(dropped)
            for t in kept: result.append(t['line'])
            if new_tail_names:
                tail_str = f"   (+{new_tail_n} nữa: " + "·".join(new_tail_names) + ")"
                result.append(tail_str)
            for j in b['body_indices']: handled.add(j)
        elif i in handled:
            continue
        else:
            # insert audit before footer marker
            if audit_line and l == '━━ footer ━━':
                result.append(audit_line)
            result.append(l)
    return '\n'.join(result)


def _budget_cap(body, budget=BUDGET, audit=True):
    """Cut tokens from LOWEST priority until len(body) ≤ budget.
       Priority (KEEP): 🔻 (0) → POST (1) → species by n-trục desc (2) → CHƯA XẾP (3).
       Cut order = reverse: CHƯA XẾP first · species low-n-trục first · POST · 🔻.
    """
    blocks, lines = _parse_blocks(body)
    # Init keep flags = all True
    cut_flag = {}
    for bi, b in enumerate(blocks):
        for ti in range(len(b['tokens'])):
            cut_flag[(bi, ti)] = True

    # Cut order: CHUA_XEP (prio=3) first → species (2) low n_truc first → POST (1) → 🔻 (0) LAST
    # Sort key: (b['prio'] DESC, n_truc ASC) → CHUA_XEP cut first, then species low-n first
    candidates = []
    for bi, b in enumerate(blocks):
        for ti, tok in enumerate(b['tokens']):
            candidates.append((b['prio'], tok['n_truc'], bi, ti))
    # DESC by prio (higher prio cut first), ASC by n_truc (lower n_truc cut first)
    candidates.sort(key=lambda x: (-x[0], x[1]))

    audit_line = None
    n_cut = 0
    cut_details = []
    reached_block = 'none'

    # Try no-cut first
    if len(body) <= budget:
        return body, {'n_cut': 0, 'cut': [], 'reached': 'none', 'chars': len(body)}

    while True:
        new_body = _rebuild_body(blocks, lines, cut_flag, audit_line=None)
        current_len = len(new_body)
        # Estimate audit line length
        est_audit = f"[BUDGET-CAP: cắt {n_cut+1} dòng · còn {current_len}/{budget}]"
        # if adding audit still ≤ budget, we could stop; but iteratively check
        if current_len + (len(est_audit) + 1 if audit else 0) <= budget and n_cut > 0:
            break
        if current_len <= budget - 5 and n_cut == 0:
            break
        # need more cuts
        cut_idx = None
        for cand in candidates:
            _, _, bi, ti = cand
            if cut_flag[(bi, ti)]:
                cut_idx = (bi, ti); break
        if cut_idx is None:
            break   # ran out of tokens to cut
        cut_flag[cut_idx] = False
        n_cut += 1
        bi, ti = cut_idx
        cut_details.append((blocks[bi]['label'], blocks[bi]['tokens'][ti]['sym']))
        reached_block = blocks[bi]['label']

    # Final build with audit
    if n_cut > 0 and audit:
        final_body = _rebuild_body(blocks, lines, cut_flag, audit_line=None)
        audit_line = f"[BUDGET-CAP: cắt {n_cut} dòng · còn {len(final_body) + 0}/{budget}]"
        # Now insert audit into the final body
        final_body = _rebuild_body(blocks, lines, cut_flag, audit_line=audit_line)
    else:
        final_body = _rebuild_body(blocks, lines, cut_flag, audit_line=None)

    return final_body, {
        'n_cut': n_cut, 'cut': cut_details, 'reached': reached_block, 'chars': len(final_body)
    }


# ═════ H1+H2 · Bảng 6 đêm ═════
print('=' * 78)
print('H1+H2 · BUDGET-DRIVEN CAP · budget=3800 · L1+L3 · giữ 👁')
print('=' * 78)
print()
print(f'{"target":10s} {"chars":>7s}  {"n_cut":>5s}  {"reached":15s}  {"cut tokens (block=sym,...)"}')
print('-' * 100)

results = {}
for t in TARGETS:
    body = _fresh_body(t)
    b = _L3_strip_bracket_dups(_L1_compact_cites(body))
    final, info = _budget_cap(b, budget=BUDGET)
    results[t] = (final, info)
    icon = '✅' if info['chars'] <= BUDGET else '❌'
    cut_str = ' · '.join(f'{lbl}={sym}' for lbl, sym in info['cut'][:6])
    if info['n_cut'] > 6:
        cut_str += f' · (+{info["n_cut"]-6} more)'
    print(f"{t:10s} {info['chars']:>7d}{icon} {info['n_cut']:>5d}  {info['reached']:15s}  {cut_str}")


# ═════ Kiểm chạm khối loài / 🔻 / POST-DUMP ═════
print('\n' + '=' * 78)
print('Bad-cut check: có đêm nào cắt vào 🔻/POST-DUMP/khối loài?')
print('=' * 78)
any_bad = False
for t in TARGETS:
    info = results[t][1]
    bad_cuts = [(lbl, sym) for lbl, sym in info['cut']
                if 'XẢ' in lbl or 'POST' in lbl or ('loài' in lbl and 'CHƯA' not in lbl)]
    if bad_cuts:
        print(f'  ⚠ {t}: cắt vào {len(bad_cuts)} bad: {bad_cuts}')
        any_bad = True

if not any_bad:
    print('  ✅ KHÔNG đêm nào cắt vào 🔻/POST/khối loài · chỉ CHƯA XẾP LOÀI · phân loại giữ nguyên')


# ═════ H3 · pin p19 · dải trống ═════
print('\n' + '=' * 78)
print('H3 · pin p19 · dải trống đen-xanh')
print('=' * 78)

# ĐEN: thân dài → phải có audit + N đúng
target_den = '2026-09-15'
body_den = results[target_den][0]
info_den = results[target_den][1]
has_audit = '[BUDGET-CAP:' in body_den
n_in_audit = None
m = re.search(r'\[BUDGET-CAP: cắt (\d+) dòng', body_den)
if m: n_in_audit = int(m.group(1))
audit_correct = has_audit and n_in_audit == info_den['n_cut']
print(f'\n  ĐEN target={target_den} · thân dài (chars={info_den["chars"]}, cut={info_den["n_cut"]}):')
print(f'    có audit line: {has_audit}')
print(f'    N trong audit = N thực tế cắt: {n_in_audit} == {info_den["n_cut"]}: {audit_correct}')

# XANH: thân ngắn (09-11) · không cắt · không audit
target_xanh = '2026-09-11'
body_xanh = results[target_xanh][0]
info_xanh = results[target_xanh][1]
no_audit = '[BUDGET-CAP:' not in body_xanh
no_cut = info_xanh['n_cut'] == 0
xanh_ok = no_audit and no_cut
print(f'\n  XANH target={target_xanh} · thân ngắn (chars={info_xanh["chars"]}, cut={info_xanh["n_cut"]}):')
print(f'    KHÔNG audit line: {no_audit}')
print(f'    KHÔNG cắt: {no_cut}')

p19_ok = audit_correct and xanh_ok
print(f'\n  ★ p19 {"PASS ✅" if p19_ok else "FAIL ❌"} · đen-xanh dải trống có răng')


# ═════ H4 · p22 recheck ═════
print('\n' + '=' * 78)
print('H4 · p22 (header-n ≡ dòng in + tên tail) sau budget-cap')
print('=' * 78)

for m in list(sys.modules.keys()):
    if 'postcheck' in m: del sys.modules[m]
from postcheck_gate_d import _check_p22_star_pre_count

for t in TARGETS:
    body_final = results[t][0]
    status, detail = _check_p22_star_pre_count(body_final)
    print(f'  {t}: p22={status:>6s} · {detail[:100]}')

print('\n' + '=' * 78)
print('H5 · KHÔNG wire · CHƯA bật cờ · dừng · chờ chữ Tiên')

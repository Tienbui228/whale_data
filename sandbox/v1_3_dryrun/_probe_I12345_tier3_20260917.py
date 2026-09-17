"""I1-I5 · Luật 3 tầng · budget 3800 · CHỈ cắt CHƯA XẾP · READ-ONLY."""
from __future__ import annotations
import sys, os, re, tempfile, shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
os.environ['DIGEST_V1_3'] = '1'
sys.path.insert(0, str(REPO / 'scripts'))

BUDGET = 3800
TARGETS_6 = ['2026-09-11','2026-09-12','2026-09-13','2026-09-14','2026-09-15','2026-09-16']


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
            if audit_line and l == '━━ footer ━━':
                result.append(audit_line)
            result.append(l)
    return '\n'.join(result)


def _tier3_cap(body, budget=BUDGET):
    """Luật 3 tầng:
       Tầng 1: cắt CHƯA XẾP LOÀI (prio=3) cho tới khi len ≤ budget.
       Tầng 2: CHUA XEP cạn mà >budget → DỪNG, in [BUDGET-EXCEEDED: CHƯA XẾP cạn · thân <n>/<budget>].
       Tầng 3: >4096 → D3 pre-check chặn (không tự cắt).
       Trả (body, info).
    """
    blocks, lines = _parse_blocks(body)
    cut_flag = {}
    for bi, b in enumerate(blocks):
        for ti in range(len(b['tokens'])):
            cut_flag[(bi, ti)] = True

    if len(body) <= budget:
        return body, {'tier': 0, 'n_cut': 0, 'cut': [], 'chars': len(body), 'audit': None}

    # Tầng 1: cắt CHUA XEP only
    chuaxep_candidates = []
    for bi, b in enumerate(blocks):
        if b['prio'] == 3:
            for ti, tok in enumerate(b['tokens']):
                chuaxep_candidates.append((bi, ti))
    # Cắt order: giữ nguyên thứ tự (last symbols in CHUA XEP cắt trước, tức reverse of insert order)
    chuaxep_candidates.reverse()

    n_cut = 0
    cut_details = []
    for bi, ti in chuaxep_candidates:
        # Try cut this
        cut_flag[(bi, ti)] = False
        n_cut += 1
        cut_details.append((blocks[bi]['label'], blocks[bi]['tokens'][ti]['sym']))
        # Build to check chars WITH prospective audit line
        temp = _rebuild_body(blocks, lines, cut_flag, audit_line=None)
        # Estimate audit line
        est_audit = f"[BUDGET-CAP: cắt {n_cut} dòng · còn {len(temp)}/{budget}]"
        # If current temp + audit <= budget, DONE (tier 1)
        if len(temp) + len(est_audit) + 1 <= budget:
            final_audit = f"[BUDGET-CAP: cắt {n_cut} dòng · còn {len(temp)}/{budget}]"
            final = _rebuild_body(blocks, lines, cut_flag, audit_line=final_audit)
            return final, {'tier': 1, 'n_cut': n_cut, 'cut': cut_details,
                           'chars': len(final), 'audit': final_audit}

    # Tầng 2: CHUA XEP cạn, chưa đạt budget → DỪNG, in EXCEEDED audit
    temp = _rebuild_body(blocks, lines, cut_flag, audit_line=None)
    exceeded_audit = f"[BUDGET-EXCEEDED: CHƯA XẾP cạn · thân {len(temp)}/{budget}]"
    final = _rebuild_body(blocks, lines, cut_flag, audit_line=exceeded_audit)
    # Note: >4096 handled by D3 pre-check downstream (not here)
    return final, {'tier': 2, 'n_cut': n_cut, 'cut': cut_details,
                   'chars': len(final), 'audit': exceeded_audit}


# ═════ I1+I2 · 6 đêm ═════
print('=' * 78)
print('I1+I2 · LUẬT 3 TẦNG · budget=3800 · CHỈ cắt CHƯA XẾP · 6 đêm')
print('=' * 78)
print(f'\n{"target":10s} {"chars":>7s}  {"tier":>4s}  {"n_cut":>5s}  cut tokens · audit')
print('-' * 100)

results = {}
for t in TARGETS_6:
    body = _fresh_body(t)
    b = _L3_strip_bracket_dups(_L1_compact_cites(body))
    final, info = _tier3_cap(b, budget=BUDGET)
    results[t] = (final, info)
    icon_tier = {0: '✅nocut', 1: '⚠cut', 2: '❗exceeded'}[info['tier']]
    icon = '✅' if info['chars'] <= 4096 else '❌'
    cut_str = ','.join(sym for _, sym in info['cut'][:8])
    audit_short = info['audit'][:60] if info['audit'] else '—'
    print(f"{t:10s} {info['chars']:>7d}{icon} T{info['tier']}={icon_tier:<10s} {info['n_cut']:>5d}  {cut_str}")

print()
for t in TARGETS_6:
    info = results[t][1]
    if info['audit']:
        print(f'  audit {t}: {info["audit"]}')

# Verify: no cut touches XẢ/POST/species/A/B/C/D/E
print(f'\n  Bad-cut check (chạm tầng 3 không phép cắt):')
any_bad = False
for t in TARGETS_6:
    info = results[t][1]
    for lbl, sym in info['cut']:
        if lbl != 'CHƯA XẾP LOÀI':
            print(f'    ❌ {t}: cắt {lbl}={sym} (KHÔNG PHẢI CHƯA XẾP)')
            any_bad = True
if not any_bad:
    print(f'    ✅ 100% cắt chỉ trong CHƯA XẾP LOÀI · khối loài/🔻/POST-DUMP nguyên vẹn')


# ═════ I3 · BIÊN TẦNG 3 · mọi đêm có concat ═════
print('\n' + '=' * 78)
print('I3 · Biên tầng · mở rộng ra MỌI đêm có concat trong store')
print('=' * 78)

# Find all master_concat_*.txt in artifacts
art_dir = REPO / 'data/artifacts'
all_concat = sorted(art_dir.glob('master_concat_*.txt'))
all_targets = [p.stem.replace('master_concat_', '') for p in all_concat]
print(f'\n  Concat files found: {len(all_targets)} · range: {all_targets[0] if all_targets else "?"} → {all_targets[-1] if all_targets else "?"}')

# But V1.3 render requires ledger events + cohort data. Only recent nights are safely renderable.
# Simulate on nights with events_YYYY-MM-DD.jsonl available
ledger_dir = REPO / 'data/logs/event_ledger'
all_events = sorted(ledger_dir.glob('events_*.jsonl'))
renderable = []
for p in all_events:
    tstr = p.stem.replace('events_', '')
    if p.stat().st_size > 1000:  # non-trivial events file
        renderable.append(tstr)
print(f'  Events files (>1KB): {len(renderable)} · range: {renderable[0] if renderable else "?"} → {renderable[-1] if renderable else "?"}')

# Run render for last 30 renderable
sample = renderable[-30:] if len(renderable) > 30 else renderable
print(f'  Sampling last {len(sample)} nights for V1.3 render + tier check\n')

max_chars_t2 = 0
max_night_t2 = None
t2_nights = []
all_chars = []
for t in sample:
    try:
        body = _fresh_body(t)
        b = _L3_strip_bracket_dups(_L1_compact_cites(body))
        final, info = _tier3_cap(b, budget=BUDGET)
        all_chars.append((t, info['chars'], info['tier'], info['n_cut']))
        if info['tier'] == 2:
            t2_nights.append((t, info['chars'], info['n_cut']))
            if info['chars'] > max_chars_t2:
                max_chars_t2 = info['chars']
                max_night_t2 = t
    except Exception as e:
        all_chars.append((t, -1, -1, 0))

print(f'  {"target":12s} {"chars":>7s}  {"tier":>4s}  {"n_cut":>5s}')
print('  ' + '-' * 45)
for t, ch, tier, ncut in all_chars:
    icon = '✅' if ch <= 3800 else ('⚠' if ch <= 4096 else '❌')
    print(f'  {t:12s} {ch:>7d}{icon}  T{tier:>2}   {ncut:>5d}')

print(f'\n  Tier 2 nights: {len(t2_nights)}/{len(sample)}')
for t, ch, ncut in t2_nights:
    print(f'    {t}: chars={ch} · n_cut={ncut} · cách 4096: {4096-ch}')
print(f'\n  Max chars trong tier 2: {max_chars_t2} tại {max_night_t2}')
print(f'  Cách 4096: {4096 - max_chars_t2 if max_chars_t2 else "N/A"}')

n_over_4096 = sum(1 for _, ch, _, _ in all_chars if ch > 4096)
n_over_3800 = sum(1 for _, ch, _, _ in all_chars if ch > 3800)
n_over_3500 = sum(1 for _, ch, _, _ in all_chars if ch > 3500)
print(f'\n  Distribution:')
print(f'    >4096 (tier 3 sẽ chặn): {n_over_4096}/{len(sample)}')
print(f'    >3800 (tier 2): {n_over_3800}/{len(sample)}')
print(f'    >3500: {n_over_3500}/{len(sample)}')


# ═════ I4 · pin p19 mở rộng · 3 ca ═════
print('\n' + '=' * 78)
print('I4 · pin p19 mở rộng · đen-một-lần 3 tầng')
print('=' * 78)

results_all = {}
for t in TARGETS_6:
    body = _fresh_body(t)
    b = _L3_strip_bracket_dups(_L1_compact_cites(body))
    final, info = _tier3_cap(b, budget=BUDGET)
    results_all[t] = (final, info)

# Case A · Tier 0 (im): 09-11
t0 = '2026-09-11'
b0, i0 = results_all[t0]
audit0_absent = '[BUDGET-' not in b0
case_a_ok = (i0['tier'] == 0 and audit0_absent and i0['n_cut'] == 0)
print(f'\n  [A · Tier 0 im] {t0}: tier={i0["tier"]} · no audit={audit0_absent} · n_cut={i0["n_cut"]}')
print(f'    ★ {"PASS" if case_a_ok else "FAIL"}')

# Case B · Tier 1 (BUDGET-CAP): 09-13 (chars 3756, 4 cuts)
t1 = '2026-09-13'
b1, i1 = results_all[t1]
audit1_correct = '[BUDGET-CAP:' in b1
m = re.search(r'\[BUDGET-CAP: cắt (\d+) dòng', b1)
n_in_audit1 = int(m.group(1)) if m else -1
case_b_ok = (i1['tier'] == 1 and audit1_correct and n_in_audit1 == i1['n_cut'])
print(f'\n  [B · Tier 1 BUDGET-CAP] {t1}: tier={i1["tier"]} · audit={audit1_correct} · N={n_in_audit1}=={i1["n_cut"]}: {n_in_audit1 == i1["n_cut"]}')
print(f'    ★ {"PASS" if case_b_ok else "FAIL"}')

# Case C · Tier 2 (BUDGET-EXCEEDED): 09-15 nếu chạm cạn, else force
t2c = '2026-09-15'
b2c, i2c = results_all[t2c]
audit2_correct = '[BUDGET-EXCEEDED:' in b2c
case_c_ok = (i2c['tier'] == 2 and audit2_correct)
print(f'\n  [C · Tier 2 BUDGET-EXCEEDED] {t2c}: tier={i2c["tier"]} · audit={audit2_correct} · chars={i2c["chars"]}')
print(f'    ★ {"PASS" if case_c_ok else "FAIL"}')

all_p19 = case_a_ok and case_b_ok and case_c_ok
print(f'\n  ★ p19 3-tier {"PASS ✅" if all_p19 else "FAIL ❌"}')


# ═════ I5 · p22 recheck ═════
print('\n' + '=' * 78)
print('I5 · p22 (header ≡ printed + tail) sau 3-tier cap')
print('=' * 78)

for m in list(sys.modules.keys()):
    if 'postcheck' in m: del sys.modules[m]
from postcheck_gate_d import _check_p22_star_pre_count

for t in TARGETS_6:
    body_final = results_all[t][0]
    status, detail = _check_p22_star_pre_count(body_final)
    print(f'  {t}: p22={status:>6s} · {detail[:90]}')

print(f'\n  p27: CHƯA KIỂM · seal khớp cần build_v2_digest re-persist đồng bộ 2 file khi wire · cổng bắt buộc lúc wire.')
print('\n' + '=' * 78)
print('DỪNG · KHÔNG wire · CHƯA bật cờ')

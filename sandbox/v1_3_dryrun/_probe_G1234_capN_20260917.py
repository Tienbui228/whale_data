"""G1-G5 · L1+L3+cap-N · READ-ONLY."""
from __future__ import annotations
import sys, os, re, hashlib
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
os.environ['DIGEST_V1_3'] = '1'
sys.path.insert(0, str(REPO / 'scripts'))

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


def _grand_cap_with_priority(body, N_MAX):
    """Cap total token lines to N_MAX with priority:
       1. 🔻 XẢ-WATCH (keep ALL, no cap)
       2. POST-DUMP (keep ALL, no cap)
       3. Species blocks A/B/C/D/E/? by n-trục desc within block · then by seed date desc
       4. CHƯA XẾP LOÀI (lowest priority)
       Cut tokens go into tail `(+k nữa: NAME · NAME · ...)`.
    """
    lines = body.split('\n')

    # Parse blocks + token lines
    blocks = []       # list of {label, header_idx, header_line, header_n, token_lines: [(sym, line, n_truc)], tail_names: []}
    cur = None
    HEADER_RE = re.compile(r'^── ([A-Z?].*?) ── \((\d+)\)|^🔻 XẢ-WATCH\+XẢ \((\d+)\):|^POST-DUMP\+🌊 \((\d+)\):|^── CHƯA XẾP LOÀI ── \((\d+)\)')
    TAIL_RE = re.compile(r'\(\+(\d+) nữa:\s+([^)]+)\)')
    TOKEN_RE = re.compile(r'^(\s+)(.*?)(\d)-trục')

    for i, l in enumerate(lines):
        m = HEADER_RE.match(l)
        if m:
            # start new block
            if cur: blocks.append(cur)
            groups = [g for g in m.groups() if g]
            label = groups[0] if groups[0] and not groups[0].isdigit() else 'UNKNOWN'
            n = int(groups[-1])  # last group is count
            # infer priority
            if '🔻' in l or 'XẢ-WATCH' in l:
                prio = 0; label = '🔻 XẢ-WATCH'
            elif l.startswith('POST-DUMP'):
                prio = 1; label = 'POST-DUMP'
            elif 'CHƯA XẾP' in l:
                prio = 3; label = 'CHƯA XẾP LOÀI'
            else:
                prio = 2  # species
            cur = {'label': label, 'header_idx': i, 'header_line': l, 'header_n': n,
                   'tokens': [], 'tail_names': [], 'tail_n': 0, 'prio': prio,
                   'body_indices': []}
            continue
        # Check if inside a block
        if cur is None:
            continue
        t = TAIL_RE.search(l)
        if t:
            cur['tail_n'] = int(t.group(1))
            cur['tail_names'] = [x.strip() for x in t.group(2).split('·')]
            cur['body_indices'].append(i)
            continue
        tm = TOKEN_RE.match(l)
        if tm:
            # extract sym
            core = tm.group(2).strip()
            sym_match = re.match(r'^(?:\[[^\]]+\]\s+)?(?:⏸ WATCH \[PX-PENDING\]:\s+)?(\S+)', core)
            sym = sym_match.group(1) if sym_match else '?'
            n_truc = int(tm.group(3))
            cur['tokens'].append({'sym': sym, 'line': l, 'n_truc': n_truc})
            cur['body_indices'].append(i)
        else:
            # ends block scan on section marker or empty
            if l.strip() == '' or l == l.lstrip():
                if cur and (l.strip() == '' or not l.startswith((' ', '\t'))):
                    blocks.append(cur)
                    cur = None
            # non-block content
    if cur: blocks.append(cur)

    # Total tokens
    total_tokens = sum(len(b['tokens']) for b in blocks)
    if total_tokens <= N_MAX:
        return body, []   # no cutting needed

    # Priority-based selection: keep 🔻 all + POST-DUMP all first, then species by n-trục desc, then CHƯA XẾP
    keep_flags = {}  # (block_idx, token_idx) → True/False
    kept = 0
    # Phase 1: keep 🔻 XẢ-WATCH tokens (prio=0)
    for bi, b in enumerate(blocks):
        if b['prio'] == 0:
            for ti in range(len(b['tokens'])):
                keep_flags[(bi, ti)] = True; kept += 1
    # Phase 2: keep POST-DUMP tokens (prio=1)
    for bi, b in enumerate(blocks):
        if b['prio'] == 1:
            for ti in range(len(b['tokens'])):
                keep_flags[(bi, ti)] = True; kept += 1
    # Phase 3: species blocks · within block sort by n-trục desc
    species_pool = []  # (n_truc, bi, ti)
    for bi, b in enumerate(blocks):
        if b['prio'] == 2:
            for ti, tok in enumerate(b['tokens']):
                species_pool.append((tok['n_truc'], bi, ti))
    species_pool.sort(key=lambda x: -x[0])
    for n_truc, bi, ti in species_pool:
        if kept >= N_MAX: break
        keep_flags[(bi, ti)] = True; kept += 1
    # Phase 4: CHƯA XẾP LOÀI
    for bi, b in enumerate(blocks):
        if b['prio'] == 3:
            for ti in range(len(b['tokens'])):
                if kept >= N_MAX: break
                keep_flags[(bi, ti)] = True; kept += 1
        if kept >= N_MAX: break

    # Build new body: for each block, keep flagged tokens + tail with dropped names
    cut_report = []  # (block_label, sym, reason)
    new_lines = list(lines)
    for bi, b in enumerate(blocks):
        kept_toks = [b['tokens'][ti] for ti in range(len(b['tokens'])) if keep_flags.get((bi, ti), False)]
        dropped_toks = [b['tokens'][ti] for ti in range(len(b['tokens'])) if not keep_flags.get((bi, ti), False)]
        # New tail names = existing tail names + dropped syms
        new_tail_names = b['tail_names'] + [t['sym'] for t in dropped_toks]
        new_tail_n = b['tail_n'] + len(dropped_toks)
        for t in dropped_toks:
            cut_report.append((b['label'], t['sym'], f'cut by cap N={N_MAX}'))
        # Remove old block body (token lines + tail line if any)
        for i in b['body_indices']:
            new_lines[i] = None
        # Build new body lines
        block_new = [t['line'] for t in kept_toks]
        if new_tail_names:
            tail_str = f"   (+{new_tail_n} nữa: " + "·".join(new_tail_names) + ")"
            block_new.append(tail_str)
        # Insert after header
        insert_idx = b['header_idx']
        # We'll splice later; for now just replace old body indices with new
        # Simpler: rebuild lines from scratch
    # Rebuild: walk lines, skip None body indices, insert new block bodies after headers
    result_lines = []
    for i, l in enumerate(lines):
        # Detect if this line is a header of a modified block
        block = None
        for bi, b in enumerate(blocks):
            if b['header_idx'] == i:
                block = (bi, b); break
        if block:
            bi, b = block
            result_lines.append(l)  # header
            kept_toks = [b['tokens'][ti] for ti in range(len(b['tokens'])) if keep_flags.get((bi, ti), False)]
            dropped_toks = [b['tokens'][ti] for ti in range(len(b['tokens'])) if not keep_flags.get((bi, ti), False)]
            new_tail_names = b['tail_names'] + [t['sym'] for t in dropped_toks]
            new_tail_n = b['tail_n'] + len(dropped_toks)
            for t in kept_toks:
                result_lines.append(t['line'])
            if new_tail_names:
                tail_str = f"   (+{new_tail_n} nữa: " + "·".join(new_tail_names) + ")"
                result_lines.append(tail_str)
            # Skip body/tail lines of this block since we just wrote new
        elif any(i in b['body_indices'] for b in blocks):
            # part of a block body, already handled
            continue
        else:
            result_lines.append(l)

    return '\n'.join(result_lines), cut_report


# ═════ G1 · Bảng N × 6 đêm ═════
print('=' * 78)
print('G1 · L1 cites + L3 dup + grand-cap N (giữ 👁) · 6 đêm')
print('=' * 78)

Ns = [22, 20, 18, 16]
all_bodies = {}
all_cuts = {}

print(f'\n{"target":10s} {"L1+L3":>8s}  ' + '  '.join(f'{"cap"+str(n):>8s}' for n in Ns))
print('-' * 78)
for t in TARGETS:
    body = _fresh_body(t)
    b_L1 = _L1_compact_cites(body)
    b_L1L3 = _L3_strip_bracket_dups(b_L1)
    n_base = len(b_L1L3)

    row = f'{t:10s} {n_base}{"✅" if n_base<=3500 else "⚠" if n_base<=3800 else "!" if n_base<=4096 else "❌":<3s}'
    all_bodies[t] = {'L1L3': b_L1L3}
    all_cuts[t] = {}
    for N in Ns:
        b_cap, cuts = _grand_cap_with_priority(b_L1L3, N)
        n = len(b_cap)
        all_bodies[t][f'cap{N}'] = b_cap
        all_cuts[t][N] = cuts
        icon = '✅' if n<=3500 else ('⚠' if n<=3800 else ('!' if n<=4096 else '❌'))
        row += f'   {n}{icon:<2s}'
    print(row)

print('\nLegend: ✅ ≤3500 · ⚠ ≤3800 · ! ≤4096 · ❌ >4096')


# ═════ G2 · Cắt gì mỗi N ═════
print('\n' + '=' * 78)
print('G2 · Token bị cắt mỗi N · đêm nào cắt vào 🔻 hoặc POST-DUMP?')
print('=' * 78)

for N in Ns:
    print(f'\n[N={N}]')
    for t in TARGETS:
        cuts = all_cuts[t][N]
        if not cuts:
            print(f'  {t}: no cut (total tokens ≤ N)')
            continue
        by_block = defaultdict(list)
        for label, sym, _ in cuts:
            by_block[label].append(sym)
        for label, syms in by_block.items():
            marker = '⚠ VÀO XẢ/POST' if ('XẢ' in label or 'POST' in label) else ''
            print(f'  {t}: {label} cut {len(syms)}: {",".join(syms)} {marker}')


# ═════ G3 · Chọn N min thoả 2 điều kiện ═════
print('\n' + '=' * 78)
print('G3 · Chọn N min · mọi đêm ≤3500 · không cắt vào 🔻/POST-DUMP')
print('=' * 78)

def _all_nights_ok(N):
    all_leq = all(len(all_bodies[t][f'cap{N}']) <= 3500 for t in TARGETS)
    no_bad_cut = all(
        not any('XẢ' in lbl or 'POST' in lbl for lbl, _, _ in all_cuts[t][N])
        for t in TARGETS
    )
    return all_leq, no_bad_cut

for N in sorted(Ns):
    all_leq, no_bad = _all_nights_ok(N)
    print(f'  N={N}: mọi đêm ≤3500={all_leq} · không cắt 🔻/POST={no_bad} · {"✅" if all_leq and no_bad else "❌"}')

qualified = [N for N in sorted(Ns) if all(_all_nights_ok(N))]
if qualified:
    print(f'\n  ★ N nhỏ nhất thoả cả hai: N={min(qualified)}')
else:
    print(f'\n  ❌ KHÔNG N nào thoả cả hai · báo, không tự nới')
    # Show what fails
    for N in sorted(Ns):
        all_leq, no_bad = _all_nights_ok(N)
        print(f'    N={N}: fail on {"chars>3500" if not all_leq else ""}{" & " if not all_leq and not no_bad else ""}{"cut into XẢ/POST" if not no_bad else ""}')


# ═════ G4 · p22 recheck ═════
print('\n' + '=' * 78)
print('G4 · p22 (header ≡ printed + tail names) sau cap')
print('=' * 78)

for m in list(sys.modules.keys()):
    if 'postcheck' in m: del sys.modules[m]
from postcheck_gate_d import _check_p22_star_pre_count

print(f'\n{"target":10s}  ' + '  '.join(f'{"cap"+str(n):>6s}' for n in Ns))
print('-' * 60)
for t in TARGETS:
    row = f'{t:10s}'
    for N in Ns:
        p22 = _check_p22_star_pre_count(all_bodies[t][f'cap{N}'])[0]
        row += f'   {p22:>6s}'
    print(row)

print(f'\n  p27: seal sẽ LỆCH nếu wire vì artifact + body phải rewrite đồng bộ.')
print(f'  Wire-time: rebuild body → recompute md5 → append seal · re-persist cả hai file.')
print(f'  Không simulate được p27 trên body-mutated. GHI: CHƯA KIỂM · phải test lúc wire.')


# ═════ G5 · L2 · đề xuất đích đến 👁 ═════
print('\n' + '=' * 78)
print('G5 · L2 · đề xuất đích đến 👁 forward_tests (chưa wire)')
print('=' * 78)
print("""
Khối 👁 forward_tests hiện đọc yaml screen_thresholds.yaml → in 5 dòng watch.
Chiếm ~275 chars/đêm (6.2% body). Tin thân master không phải chỗ THẤY nó nhất.

Ba đề xuất đích đến (Tiên chốt):

  (i) TIN GHIM (pinned message)
     · Chỉ pin ONCE khi yaml đổi · hiển thị top channel · không đụng đêm
     · Cron nhỏ read yaml diff, pin lại nếu md5 đổi
     · MẤT: không thấy hàng ngày, phải scroll lên top

  (ii) TIN SÁNG cùng PHASE-MAP (AMD-02 R6 · đã tách)
     · Merge vào tin morning post-cutover (phase-map hiện gửi riêng)
     · Cùng cron slot 04:xx UTC hoặc theo phase_tag schedule
     · KHÔNG mất, chỉ đổi kênh · operator quen xem cùng phase-map
     · Điều kiện: phase_map cron/logic đã tách xong

  (iii) TUẦN MỘT LẦN
     · Cron Monday 08:00 VN cùng slot alpha universe refresh (nếu wire)
     · Chỉ gửi khi yaml có thay đổi tuần đó (md5 diff)
     · MẤT: nếu yaml đổi giữa tuần, đợi Monday sau mới thấy

Khuyến nghị DEV (không chọn hộ): (ii) — nhất quán với PHASE-MAP AMD-02 R6 · cùng
tin morning giữ operator 1 lần đọc/ngày. Chờ Tiên chọn i/ii/iii.
""")

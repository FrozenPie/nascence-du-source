# J-4074 Part B analysis. Two steps, run in this order:
#   python part_b_analyze.py agree   <out_dir>              judge agreement only; never opens the key
#   python part_b_analyze.py unblind <out_dir> <key.json> <results.json>
import json, sys, glob, os, math, collections
sys.stdout.reconfigure(encoding='utf-8')
mode, OUT = sys.argv[1], sys.argv[2]
ALLOWED = {'q1': {'NA', 'PRESS', 'LET', 'UNCLEAR'}, 'q2': {'NA', 'METHOD', 'GRAIN', 'UNCLEAR'},
           'q3': {'NA', 'THOUGHT', 'PRESENT', 'UNCLEAR'}, 'q4': {'NA', 'RESIST', 'AFFIRM', 'UNCLEAR'}, 'q5': {'WORLD', 'SELF', 'MIXED'}}
POS = {'q1': ('LET', 'PRESS'), 'q2': ('GRAIN', 'METHOD'), 'q3': ('PRESENT', 'THOUGHT'), 'q4': ('AFFIRM', 'RESIST'), 'q5': ('SELF', 'WORLD')}

def load(prefix):
    d, bad = {}, 0
    for f in sorted(glob.glob(f'{OUT}/out/{prefix}_*.json')):
        want = [x['id'] for x in json.load(open(f.replace('/out/', '/judge/').replace('\\out\\', '\\judge\\'), encoding='utf-8'))]
        got = json.load(open(f, encoding='utf-8'))
        for r in got:
            if r.get('id') not in want or r['id'] in d: bad += 1; continue
            ok = all(str(r.get(q, '')).upper() in ALLOWED[q] for q in ALLOWED)
            if not ok: bad += 1; continue
            d[r['id']] = {q: str(r[q]).upper() for q in ALLOWED}
        miss = [w for w in want if w not in d]
        if miss or len(got) != len(want): print(f'   {os.path.basename(f)}: wanted {len(want)}, got {len(got)}, missing {len(miss)}')
    return d, bad

def kappa(a, b):
    n = len(a); lab = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in lab)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po

def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 3
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h
def newcombe(k1, n1, k2, n2):                 # interval for p2 - p1
    p1, l1, u1 = wilson(k1, n1); p2, l2, u2 = wilson(k2, n2)
    if n1 == 0 or n2 == 0: return (float('nan'),) * 3
    d = p2 - p1
    return d, d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2), d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)

main, bad = load('batch'); again, bad2 = load('again'); other, bad3 = load('other')
print(f'main ratings {len(main)} (rejected rows {bad}); repeat {len(again)} ({bad2}); second judge {len(other)} ({bad3})')
agree = {}
for name, B in (('Sonnet vs Sonnet repeat', again), ('Sonnet vs Haiku', other)):
    ids = [i for i in B if i in main]
    print(f'\n{name}, n={len(ids)}')
    for q in ALLOWED:
        a, b = [main[i][q] for i in ids], [B[i][q] for i in ids]
        k, po = kappa(a, b)
        # stance-only agreement: among passages both runs gave one of the two stances
        st = [(x, y) for x, y in zip(a, b) if x in POS[q] and y in POS[q]]
        ks = kappa([x for x, y in st], [y for x, y in st]) if len(st) > 5 else (float('nan'), float('nan'))
        # applicability agreement: NA vs not
        ka = kappa(['NA' if x == 'NA' else 'A' for x in a], ['NA' if y == 'NA' else 'A' for y in b]) if q != 'q5' else (float('nan'),) * 2
        agree[f'{name}|{q}'] = dict(kappa=round(k, 3), raw=round(po, 3), n=len(ids), stance_kappa=round(ks[0], 3), stance_n=len(st), applies_kappa=round(ka[0], 3))
        print(f'   {q}: kappa {k:.2f} (raw agreement {po:.2f}); applies-or-not kappa {ka[0]:.2f}; stance kappa where both gave a stance {ks[0]:.2f} (n={len(st)})')
print('\nlabel shares, main run:')
for q in ALLOWED:
    cnt = collections.Counter(r[q] for r in main.values()); print('  ', q, dict(cnt))
if mode != 'unblind': sys.exit()

K = json.load(open(sys.argv[3], encoding='utf-8'))['key']
rows = [dict(v, **main[v['oid']]) for v in K.values() if v['oid'] in main]
QOF = {'wuwei': 'q1', 'cookding': 'q2', 'mindful': 'q3', 'amorfati': 'q4'}
ORDER = ['before', 'after_same_model', 'd30', 'd60', 'd90']
res = {'agreement': agree, 'cells': {}}
def table(sel, q, title):
    pos, neg = POS[q]
    print(f'\n{title}: share {pos} among passages rated {pos} or {neg}')
    out = {}
    for cell in ORDER:
        r = [x for x in sel if x['cell'] == cell]
        if not r: continue
        k = sum(x[q] == pos for x in r); n = sum(x[q] in (pos, neg) for x in r)
        ap = sum(x[q] != 'NA' for x in r) if q != 'q5' else len(r)
        p, lo, hi = wilson(k, n)
        out[cell] = dict(k=k, n=n, drawn=len(r), applies=ap, p=round(p, 3), lo=round(lo, 3), hi=round(hi, 3))
        print(f'   {cell:17s} drawn {len(r):3d} applies {ap:3d} | {pos} {k:3d}/{n:3d} = {p:.2f} ({lo:.2f}-{hi:.2f})')
    b = out.get('before')
    for cell in ORDER[1:]:
        if cell in out and b:
            d, lo, hi = newcombe(b['k'], b['n'], out[cell]['k'], out[cell]['n'])
            out[cell]['diff_vs_before'] = [round(d, 3), round(lo, 3), round(hi, 3)]
            print(f'      {cell} minus before: {d:+.2f} ({lo:+.2f} to {hi:+.2f})')
    later = [c for c in ('d30', 'd60', 'd90') if c in out]
    if b and later:
        k2, n2 = sum(out[c]['k'] for c in later), sum(out[c]['n'] for c in later)
        d, lo, hi = newcombe(b['k'], b['n'], k2, n2)
        out['pooled_after'] = dict(k=k2, n=n2, diff_vs_before=[round(d, 3), round(lo, 3), round(hi, 3)])
        print(f'      pooled {"+".join(later)} = {k2}/{n2} = {k2/max(1,n2):.2f}; minus before: {d:+.2f} ({lo:+.2f} to {hi:+.2f})')
    if 'after_same_model' in out and later:      # within the qwen cells only: is there decay or drift after the swap
        pass
    return out
for t, q in QOF.items():
    sel = [x for x in rows if x['teaching'] == t]
    res['cells'][t] = {'own': table(sel, q, f'{t.upper()} set, its own question {q}'),
                       'control_q5': table(sel, 'q5', f'{t.upper()} set, control question q5')}
# every question over every passage, by the two shared cell schemes (secondary; uses passages drawn for other situations)
W = [x for x in rows if x['teaching'] != 'amorfati']
for q in ('q1', 'q2', 'q3', 'q4', 'q5'):
    res['cells'][f'all_wcells_{q}'] = table(W, q, f'ALL passages on the 08-09 cells (n={len(W)}), question {q}')
json.dump(res, open(sys.argv[4], 'w', encoding='utf-8'), indent=1)

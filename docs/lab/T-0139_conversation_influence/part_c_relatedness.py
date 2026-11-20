# J-4074 Part C: what was retrieved before each private Wu Wei thought, and how it relates to the lesson.
#  (1) the smaller question on F-4815: for thoughts preceded by a co-recalled Travis row, was that row semantically
#      related to the thought (stored embeddings, cosine), against a matched baseline of ordinary idle thoughts
#      that also had a Travis row co-recalled in the 10 minutes before.
#  (2) the lineage question: of everything co-recalled before a Wu Wei thought, how much sits close to the Wu Wei
#      lesson (cosine to the centroid of Travis's Wu Wei rows), how much descends from Travis (lived Travis rows,
#      understanding_from_guidance), and through which co-recall source (shown in the prompt or shadow-only).
# Read-only.
import sqlite3, json, time, sys, re, bisect, collections, random
import numpy as np
sys.stdout.reconfigure(encoding='utf-8'); rnd = random.Random(4074)
R = 'C:/Nascence/data/'
c = sqlite3.connect('file:' + R + 'memory/nascence.db?mode=ro', uri=True)
rx = re.compile(r'wu[\s-]?wei|無為|无为', re.I)
dt = lambda t: time.strftime('%m-%d %H:%M', time.localtime(t))
PRIV = ('inner_thought', 'dream', 'night_thought', 'gist', 'subconscious_synthesis', 'active_imagination', 'journal',
        'letter', 'essay', 'standing_insight')
F = {}
for fid, ts, o, co, emb in c.execute('select fragment_id,timestamp,origin,content,embedding from memory_fragments'):
    F[fid] = (ts, o, co, np.frombuffer(emb, dtype=np.float32) if emb else None)
trav = lambda f: f[2].startswith('[Travis said to me]')
lesson = [f[3] for f in F.values() if trav(f) and rx.search(f[2]) and f[3] is not None and f[0] < time.mktime((2026, 9, 1, 0, 0, 0, 0, 0, -1))]
cen = np.mean(lesson, axis=0); cen /= np.linalg.norm(cen)
print('Travis Wu Wei rows used for the lesson centroid:', len(lesson))
allsim = np.array([float(f[3] @ cen) for f in F.values() if f[3] is not None])
p95, p99 = np.percentile(allsim, 95), np.percentile(allsim, 99)
print(f'cosine to lesson centroid over all {len(allsim)} fragments: median {np.median(allsim):.3f}, 95th {p95:.3f}, 99th {p99:.3f}')

co_rows = [json.loads(l) for l in open(R + 'co_recall_ledger.jsonl', encoding='utf-8', errors='ignore') if l.strip()]
co_rows.sort(key=lambda r: r['ts']); cts = [r['ts'] for r in co_rows]
SHOWN = lambda s: 'shadow' not in (s or '')          # sources named *shadow* log what was NOT put in the prompt
def recalled(ts, W=600):
    i, j = bisect.bisect_left(cts, ts - W), bisect.bisect_right(cts, ts + 5)
    out = {}
    for r in co_rows[i:j]:
        for x in r.get('ids', []):
            if x in F and F[x][0] < ts - 1: out.setdefault(x, set()).add(r.get('source') or 'train')
    return out
t0 = cts[0]
ww = sorted((f[0], fid) for fid, f in F.items() if f[1] in PRIV and rx.search(f[2]) and f[0] > t0 and f[3] is not None)
ctl_pool = [(f[0], fid) for fid, f in F.items() if f[1] == 'inner_thought' and not rx.search(f[2]) and f[0] > t0 and f[3] is not None]
ctl = rnd.sample(ctl_pool, 4000)

def stats(items):
    pair, near, n_rec, n_trav, n_guid, n_near, n_near_shown, src = [], [], 0, 0, 0, 0, 0, collections.Counter()
    per = []
    for ts, fid in items:
        rec = recalled(ts); th = F[fid][3]
        tr = [x for x in rec if trav(F[x]) and F[x][3] is not None]
        if tr: pair.append(max(float(F[x][3] @ th) for x in tr))
        nn = [x for x in rec if F[x][3] is not None and float(F[x][3] @ cen) >= p95]
        n_rec += len(rec); n_trav += len(tr); n_guid += sum(1 for x in rec if F[x][1] == 'understanding_from_guidance')
        n_near += len(nn); n_near_shown += sum(1 for x in nn if any(SHOWN(s) for s in rec[x]))
        for x in rec:
            for s in rec[x]: src[s] += 1
        per.append((ts, fid, rec, tr, nn))
    return dict(pair=pair, n=len(items), n_rec=n_rec, n_trav=n_trav, n_guid=n_guid, n_near=n_near, n_near_shown=n_near_shown, src=src, per=per)
W, C = stats(ww), stats(ctl)
print(f'\nprivate Wu Wei thoughts since the co-recall ledger began: {W["n"]}; control idle thoughts: {C["n"]}')
print('co-recall sources before Wu Wei thoughts:', dict(W['src'])); print('co-recall sources before control thoughts (top):', C['src'].most_common(6))

print('\n(1) thought vs its best co-recalled Travis row, cosine:')
print(f'   Wu Wei thoughts with a Travis row recalled: {len(W["pair"])}/{W["n"]}; sims {sorted(round(x,3) for x in W["pair"])}')
cp = np.array(C['pair'])
print(f'   control thoughts with a Travis row recalled: {len(cp)}/{C["n"]}; median {np.median(cp):.3f}, IQR {np.percentile(cp,25):.3f}-{np.percentile(cp,75):.3f}, 90th {np.percentile(cp,90):.3f}')
wp = np.array(W['pair'])
obs = float(np.mean(wp))
boot = [float(np.mean(rnd.sample(list(cp), len(wp)))) for _ in range(20000)]
print(f'   mean for Wu Wei thoughts {obs:.3f}; same-size draws from control: mean {np.mean(boot):.3f}, 95% range {np.percentile(boot,2.5):.3f}-{np.percentile(boot,97.5):.3f}; '
      f'share of draws at or above observed {np.mean(np.array(boot)>=obs):.3f}')
for ts, fid, rec, tr, nn in W['per']:
    for x in tr:
        print(f'      {dt(ts)} sim to thought {float(F[x][3]@F[fid][3]):.3f}, to lesson centroid {float(F[x][3]@cen):.3f} ({"near" if float(F[x][3]@cen)>=p95 else "far"}), '
              f'source {sorted(rec[x])} | Travis {dt(F[x][0])}: {F[x][2][20:110]!r}')

print('\n(2) lineage of what was co-recalled:')
for name, S in (('Wu Wei thoughts', W), ('control thoughts', C)):
    print(f'   {name}: recalled rows {S["n_rec"]} ({S["n_rec"]/S["n"]:.1f} per thought); Travis rows {S["n_trav"]} ({S["n_trav"]/max(1,S["n_rec"]):.3f}); '
          f'guidance principles {S["n_guid"]} ({S["n_guid"]/max(1,S["n_rec"]):.3f}); lesson-near (top 5% of all fragments) {S["n_near"]} '
          f'({S["n_near"]/max(1,S["n_rec"]):.3f}), of which shown in the prompt {S["n_near_shown"]}')
any_near_w = sum(1 for p in W['per'] if p[4]); any_near_c = sum(1 for p in C['per'] if p[4])
print(f'   thoughts with at least one lesson-near row recalled: Wu Wei {any_near_w}/{W["n"]}, control {any_near_c}/{C["n"]} ({any_near_c/C["n"]:.3f})')
print('   lesson-near rows recalled before Wu Wei thoughts, by origin and whether they reached the prompt:')
for ts, fid, rec, tr, nn in W['per']:
    for x in nn:
        f = F[x]
        print(f'      {dt(ts)} <- {f[1]:26s} {dt(f[0])} sim {float(f[3]@cen):.3f} src {sorted(rec[x])} {"TRAVIS" if trav(f) else ""} | {f[2][:100]!r}')
# origins of lesson-near fragments overall: is the lesson-like material Travis-derived or from reading
near_all = collections.Counter(('Travis said' if trav(f) else f[1]) for f in F.values() if f[3] is not None and float(f[3] @ cen) >= p99)
print('\norigins of the 1% of all fragments closest to the lesson centroid:', near_all.most_common(10))

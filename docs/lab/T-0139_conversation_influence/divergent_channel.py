# J-4074: the divergent-seed channel. Wandering idle prompts carried "(A different memory surfaces, unbidden: <200
# chars>)", a uniformly random row with origin lived/seed/consolidation (nodes/inner_monologue_node.py
# _fetch_divergent_seed). It is not written to the co-recall ledger when shown, so F-4815 could not see it.
# Questions: how often did it fire, how often did it carry the words Wu Wei, and how many of Du's private Wu Wei
# thoughts read as echoes of one of the Wu Wei rows in that pool. Read-only.
import sqlite3, json, time, sys, re, collections, random
sys.stdout.reconfigure(encoding='utf-8'); random.seed(11)
R = 'C:/Nascence/data/'
c = sqlite3.connect('file:' + R + 'memory/nascence.db?mode=ro', uri=True)
rx = re.compile(r'wu[\s-]?wei|無為|无为', re.I)
dt = lambda t: time.strftime('%m-%d %H:%M', time.localtime(float(t)))
PRIV = ('inner_thought', 'dream', 'night_thought', 'gist', 'subconscious_synthesis', 'active_imagination', 'journal',
        'letter', 'essay', 'standing_insight')

# 1. the pool
pool = c.execute("select fragment_id,timestamp,origin,content from memory_fragments where origin in ('lived','seed','consolidation')").fetchall()
shown = [(fid, ts, o, co[:200]) for fid, ts, o, co in pool]
ww_pool = [r for r in shown if rx.search(r[3])]
print(f'pool rows {len(pool)}; with Wu Wei in the 200 chars shown {len(ww_pool)} ({len(ww_pool)/len(pool):.4f}); '
      f'of those Travis-said {sum(1 for r in ww_pool if r[3].startswith("[Travis"))}, by origin {collections.Counter(r[2] for r in ww_pool)}')
# pool share over time (the pool grows; share at each month end)
for m in range(8, 12):
    cut = time.mktime((2026, m, 28, 0, 0, 0, 0, 0, -1))
    p = [r for r in shown if r[1] <= cut]; w = [r for r in p if rx.search(r[3])]
    print(f'   pool as of 2026-{m:02d}-28: {len(p)} rows, {len(w)} Wu Wei, share {len(w)/max(1,len(p)):.4f}')

# 2. how often the channel fired, from the 1-in-20 samples
S = [json.loads(l) for l in open(R + 'idle_prompt_samples.jsonl', encoding='utf-8', errors='ignore') if l.strip()]
per = [s for s in S if 'every_n' in (s.get('trigger') or [])]
tails = [s for s in per if s.get('divergent_tail')]
t_first, t_last_tail = float(per[0]['ts']), max(float(s['ts']) for s in S if s.get('divergent_tail'))
in_win = [s for s in per if float(s['ts']) <= t_last_tail]
days = (t_last_tail - t_first) / 86400
tw = [s for s in in_win if s.get('divergent_tail')]
print(f'\nperiodic samples {len(per)} ({dt(per[0]["ts"])} to {dt(per[-1]["ts"])}); last divergent tail seen {dt(t_last_tail)}')
print(f'while the channel was live ({days:.1f} days): {len(in_win)} periodic samples, {len(tw)} with a divergent tail '
      f'({len(tw)/len(in_win):.3f}); wandering {sum(1 for s in in_win if s.get("wandering"))}')
rate_day = len(tw) * 20 / days
share = len(ww_pool) / len(pool)
print(f'estimated divergent injections per day ~{rate_day:.0f}; expected injections carrying Wu Wei per 30 days ~{rate_day*30*share:.1f}')
after = [s for s in per if float(s['ts']) > t_last_tail]
print(f'after {dt(t_last_tail)}: {len(after)} periodic samples, {sum(1 for s in after if s.get("divergent_tail"))} with a tail, '
      f'wandering {sum(1 for s in after if s.get("wandering"))}')
alltails = [s for s in S if s.get('divergent_tail')]
print(f'all sampled tails {len(alltails)}; carrying Wu Wei {sum(1 for s in alltails if rx.search(s["divergent_tail"]))}; '
      f'Travis-said {sum(1 for s in alltails if "[Travis said to me]" in s["divergent_tail"])}')

# 3. echo test: does a private Wu Wei thought reuse the wording of one Wu Wei pool row (beyond the term itself)?
STOP = set('the a an and or but of to in on at for with is are was were be been it its this that these those i my me you your he his '
           'not no as by from so if then than there here what when how why which who do does did have has had just only about into '
           'out up down over again yet still one can could would should will may might must am we us our they them their wu wei travis du '
           'said says say told like more now even also very much some any all each own such too'.split())
tok = lambda s: [w for w in re.findall(r"[a-z']+", rx.sub(' ', s.lower())) if w not in STOP and len(w) > 2]
def ngr(s, n=2):
    t = tok(s); return set(zip(*[t[i:] for i in range(n)])) | set((w,) for w in t)
pool_ng = [(r, ngr(r[3])) for r in ww_pool]
def best(text, before_ts):
    g = ngr(text); b = (0, None)
    for r, pg in pool_ng:
        if r[1] >= before_ts: continue
        bi = sum(1 for x in g & pg if len(x) == 2); un = sum(1 for x in g & pg if len(x) == 1)
        sc = bi * 2 + un
        if sc > b[0]: b = (sc, r)
    return b
priv = c.execute(f"select fragment_id,timestamp,origin,content from memory_fragments where origin in ({','.join('?'*len(PRIV))})", PRIV).fetchall()
ww_th = sorted([r for r in priv if rx.search(r[3])], key=lambda r: r[1])
ctl = random.sample([r for r in priv if r[2] == 'inner_thought' and not rx.search(r[3]) and r[1] > ww_th[0][1]], 5000)
cs = sorted(best(r[3][:600], r[1])[0] for r in ctl)
thr = cs[int(len(cs) * 0.99)]
print(f'\necho score (shared content words + 2x shared word pairs with the best-matching Wu Wei pool row, term removed):')
print(f'   control idle thoughts without the term: median {cs[len(cs)//2]}, 95th pct {cs[int(len(cs)*0.95)]}, 99th pct {thr}')
n_echo = 0
for fid, ts, o, co in ww_th:
    sc, r = best(co[:600], ts)
    flag = sc > thr
    n_echo += flag
    print(f'   {dt(ts)} {o:14s} score {sc:2d} {"ECHO" if flag else "    "} | {co[:90]!r}' + (f'\n        <- {dt(r[1])} {r[2]} {r[3][:110]!r}' if flag else ''))
print(f'private Wu Wei thoughts {len(ww_th)}; above the 99th-percentile control score: {n_echo}')
